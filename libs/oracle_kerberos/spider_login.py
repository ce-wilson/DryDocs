#!/usr/bin/env python3
"""oracle_kerberos.spider_login — Oracle (Spider/PSGMGR) Kerberos login, standalone.

Logs into an Oracle RAC service using **Kerberos v5 external authentication**
(no username/password) via python-oracledb in **Thick mode**. Hands back a live
``oracledb.Connection``; you run your own SQL.

Drop-in: copy this one file (plus a filled ``oracle_kerberos_connection.txt``)
into any project. No DryDocs imports.

Design constraints baked in (each one cost real troubleshooting time):

1. DSN = the TNS **alias**, never a hand-built single-host descriptor. The
   service floats between RAC nodes; a pinned host intermittently fails with
   ORA-12514.
2. A **clean runtime sqlnet.ora** is generated into a temp TNS_ADMIN on every
   run. On-disk profile sqlnet.ora files with conflicting
   AUTHENTICATION_SERVICES lines crash the OCI client natively
   (exit -1073740791 / 0xC0000409, no Python traceback).
3. ``init_oracle_client()`` is called with ``lib_dir`` only — **no
   config_dir**. Passing config_dir makes OCI parse sqlnet.ora during init and
   (with MIT settings present) hang at "validating loaded library".
   TNS_ADMIN is exported *after* init, so Kerberos is negotiated only at
   ``connect()`` time.
4. Two credential-cache modes:
   - ``FILE:`` (default) — MIT cache produced by kinit / enterprise login.
     sqlnet gets KERBEROS5_CONF + KERBEROS5_CONF_MIT=TRUE + the FILE: path.
   - ``MSLSA:`` (opt-in) — Windows-native LSA cache. sqlnet gets ONLY
     SQLNET.KERBEROS5_CC_NAME=MSLSA: — no KERBEROS5_CONF, no CONF_MIT,
     because MIT-library validation against an MSLSA: cache is exactly the
     init-time hang described above.
5. Windows FILE: cache paths need the ``FILE:`` prefix or they are silently
   ignored (``normalize_krb5ccname``).

Config file (``oracle_kerberos_connection.txt``, ini-style ``key = value``,
no section header) — see the sample file for all keys. Discovery order:
``--config <path>`` / ``config_path=`` argument → $ORACLE_KERBEROS_CONFIG →
current working directory → this module's folder.
"""

from __future__ import annotations

import argparse
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from pathlib import Path

CONFIG_FILENAME = "oracle_kerberos_connection.txt"
CONFIG_ENV_VAR = "ORACLE_KERBEROS_CONFIG"

# Last-resort search location: a real (gitignored) config next to this module.
# A module-level name so tests can point it elsewhere — the discovery tests
# must not see a developer's real config.
_MODULE_DIR = Path(__file__).resolve().parent

# Keys understood in the config file (superset of the team's sample).
_KNOWN_KEYS = {
    "sid",
    "hostname",  # informational only — connection always goes through the alias
    "port_no",
    "servicename",  # treated as the TNS ALIAS (resolved via tnsnames.ora); deliberate
    "tns_admin",
    "oracle_client_path",
    "krb5_config",
    "kerberos5_cc_name",
    "dpi_debug_level",
    "tcp_connect_timeout",
    "call_timeout_ms",
}


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


def find_config(explicit: str | os.PathLike | None = None) -> Path:
    """Locate the connection config file. Raises FileNotFoundError with the search list."""
    candidates: list[Path] = []
    if explicit:
        candidates.append(Path(explicit))
    env = os.environ.get(CONFIG_ENV_VAR)
    if env:
        candidates.append(Path(env))
    candidates.append(Path.cwd() / CONFIG_FILENAME)
    candidates.append(_MODULE_DIR / CONFIG_FILENAME)
    for cand in candidates:
        if cand.is_file():
            return cand
    searched = "\n  ".join(str(c) for c in candidates)
    raise FileNotFoundError(
        f"No {CONFIG_FILENAME} found. Searched:\n  {searched}\n"
        f"Copy oracle_kerberos_connection.sample.txt to {CONFIG_FILENAME} and fill it in."
    )


def parse_config(text: str) -> dict[str, str]:
    """Parse ``key = value`` lines; '#'/';' comments and blank lines ignored."""
    cfg: dict[str, str] = {}
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(("#", ";")):
            continue
        if "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip().lower()
        value = value.strip().strip('"').strip("'")
        if key:
            cfg[key] = value
    return cfg


def load_config(config_path: str | os.PathLike | None = None, **overrides: str) -> dict[str, str]:
    path = find_config(config_path)
    cfg = parse_config(path.read_text(encoding="utf-8"))
    cfg["_config_path"] = str(path)
    for key, value in overrides.items():
        if value is not None:
            cfg[key.lower()] = str(value)
    unknown = set(cfg) - _KNOWN_KEYS - {"_config_path"}
    if unknown:
        print(f"[oracle_kerberos] ignoring unknown config keys: {sorted(unknown)}")
    return cfg


# ---------------------------------------------------------------------------
# Kerberos credential-cache handling
# ---------------------------------------------------------------------------


def default_file_cache(sid: str) -> str:
    """Default MIT FILE: cache path for a SID (Windows) or uid (POSIX)."""
    if platform.system() == "Windows":
        return rf"FILE:C:\Users\{sid}\krb5cc_{sid}"
    uid = os.getuid() if hasattr(os, "getuid") else 0
    return f"FILE:/tmp/krb5cc_{uid}"


def normalize_krb5ccname(value: str, sid: str = "") -> str:
    """Normalize the credential-cache name.

    - blank        -> env KRB5CCNAME if set, else the SID-derived FILE: default
    - 'MSLSA:'     -> passed through (Windows LSA cache mode)
    - bare path    -> 'FILE:' prefix added (a bare path is silently ignored on Windows)
    - 'FILE:path'  -> passed through
    """
    value = (value or "").strip()
    if not value:
        env = os.environ.get("KRB5CCNAME", "").strip()
        if env:
            return normalize_krb5ccname(env, sid)
        if not sid and platform.system() == "Windows":
            raise ValueError(
                "kerberos5_cc_name is blank and no sid is set — cannot derive the "
                "FILE: cache path. Set sid=<your SID> or kerberos5_cc_name explicitly."
            )
        return default_file_cache(sid)
    upper = value.upper()
    if upper.startswith(("MSLSA:", "FILE:", "API:", "OSCC:")):
        return value if not upper.startswith("FILE:") else "FILE:" + value[5:]
    return f"FILE:{value}"


def is_mslsa(cc_name: str) -> bool:
    return cc_name.strip().upper().startswith("MSLSA:")


def cache_file_path(cc_name: str) -> Path | None:
    """Filesystem path of a FILE: cache, else None."""
    if cc_name.upper().startswith("FILE:"):
        return Path(cc_name[5:])
    return None


# ---------------------------------------------------------------------------
# Runtime TNS_ADMIN (clean sqlnet.ora + copied tnsnames.ora)
# ---------------------------------------------------------------------------


def build_sqlnet_text(krb5_config: str, cc_name: str) -> str:
    """Render the minimal, clean sqlnet.ora for the chosen cache mode."""
    lines = [
        "SQLNET.AUTHENTICATION_SERVICES=(KERBEROS5)",
        "NAMES.DIRECTORY_PATH=(TNSNAMES,EZCONNECT)",
    ]
    if is_mslsa(cc_name):
        # MSLSA: must NOT carry MIT config lines — loading the MIT library
        # against the LSA cache hangs OCI at "validating loaded library".
        lines.append("SQLNET.KERBEROS5_CC_NAME=MSLSA:")
    else:
        lines.append(f"SQLNET.KERBEROS5_CONF={krb5_config}")
        lines.append("SQLNET.KERBEROS5_CONF_MIT=TRUE")
        lines.append(f"SQLNET.KERBEROS5_CC_NAME={cc_name}")
    return "\n".join(lines) + "\n"


def build_runtime_tns_admin(cfg: dict[str, str], cc_name: str) -> Path:
    """Create a temp TNS_ADMIN with a copied tnsnames.ora and a generated sqlnet.ora."""
    src_tns_dir = Path(cfg["tns_admin"])
    src_tnsnames = src_tns_dir / "tnsnames.ora"
    if not src_tnsnames.is_file():
        # some profiles keep it upper-cased
        alt = src_tns_dir / "TNSNAMES.ora"
        if alt.is_file():
            src_tnsnames = alt
        else:
            raise FileNotFoundError(
                f"tnsnames.ora not found under tns_admin={src_tns_dir} — "
                "it must contain the alias you connect with."
            )
    runtime = Path(tempfile.mkdtemp(prefix="psgmgr_tns_"))
    shutil.copy2(src_tnsnames, runtime / "tnsnames.ora")
    (runtime / "sqlnet.ora").write_text(
        build_sqlnet_text(cfg.get("krb5_config", ""), cc_name), encoding="utf-8"
    )
    return runtime


def alias_address_list_count(tnsnames_text: str, alias: str) -> int:
    """Count ADDRESS_LIST entries inside the alias' descriptor (2 = RAC failover pair)."""
    lines = tnsnames_text.splitlines()
    alias_re = re.compile(rf"^\s*{re.escape(alias)}\s*=", re.IGNORECASE)
    # any other entry name at the start of a line ends the alias' block
    entry_re = re.compile(r"^[A-Za-z0-9_.$-]+\s*=")
    start = next((i for i, ln in enumerate(lines) if alias_re.match(ln)), None)
    if start is None:
        return -1
    block: list[str] = [lines[start]]
    for ln in lines[start + 1 :]:
        if entry_re.match(ln):
            break
        block.append(ln)
    return sum(1 for ln in block for _ in re.finditer(r"ADDRESS_LIST", ln, re.IGNORECASE))


# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------


def preflight(cfg: dict[str, str]) -> list[tuple[str, bool, str]]:
    """Cheap local checks before touching the network. Returns (check, ok, detail)."""
    results: list[tuple[str, bool, str]] = []

    bits = struct.calcsize("P") * 8
    results.append(("python-is-64bit", bits == 64, f"{bits}-bit interpreter"))

    try:
        import oracledb

        results.append(("oracledb-installed", True, f"version {oracledb.__version__}"))
    except ImportError as exc:
        results.append(("oracledb-installed", False, str(exc)))

    client = Path(cfg.get("oracle_client_path", ""))
    lib = client / ("oci.dll" if platform.system() == "Windows" else "libclntsh.so")
    results.append(
        ("oracle-client-present", lib.is_file(), f"{lib} {'found' if lib.is_file() else 'MISSING'}")
    )
    if platform.system() == "Windows" and "client_1920_32" in str(client).lower():
        results.append(
            ("client-bitness", False, "path looks like the 32-bit client — use the 64-bit one")
        )

    cc_name = normalize_krb5ccname(cfg.get("kerberos5_cc_name", ""), cfg.get("sid", ""))
    if is_mslsa(cc_name):
        try:
            out = subprocess.run(["klist"], capture_output=True, text=True, timeout=15).stdout
            has_tgt = "krbtgt" in out
            detail = (
                "krbtgt present in LSA cache"
                if has_tgt
                else "no krbtgt in klist — log in / klogin first"
            )
            results.append(("kerberos-ticket", has_tgt, detail))
        except OSError as exc:
            results.append(("kerberos-ticket", False, f"klist failed: {exc}"))
    else:
        cache = cache_file_path(cc_name)
        ok = cache is not None and cache.is_file() and cache.stat().st_size > 0
        state = "exists" if ok else "missing/empty — run kinit (or enterprise login) first"
        results.append(("kerberos-ticket", ok, f"cache {cache} {state}"))
        krb5_conf = Path(cfg.get("krb5_config", ""))
        conf_state = "found" if krb5_conf.is_file() else "MISSING"
        results.append(("krb5-conf-present", krb5_conf.is_file(), f"{krb5_conf} {conf_state}"))

    alias = cfg.get("servicename", "")
    tnsnames = Path(cfg.get("tns_admin", "")) / "tnsnames.ora"
    if tnsnames.is_file():
        text = tnsnames.read_text(encoding="utf-8", errors="replace")
        count = alias_address_list_count(text, alias)
        if count < 0:
            results.append(("tns-alias-resolves", False, f"alias {alias} not found in {tnsnames}"))
        elif count < 2:
            detail = (
                f"alias found but only {count} ADDRESS_LIST — "
                "single-host descriptor risks ORA-12514"
            )
            results.append(("tns-alias-resolves", True, detail))
        else:
            results.append(("tns-alias-resolves", True, f"alias found with {count} ADDRESS_LISTs"))
    else:
        results.append(("tns-alias-resolves", False, f"{tnsnames} not found"))

    return results


# ---------------------------------------------------------------------------
# Connect
# ---------------------------------------------------------------------------

_client_initialized = False


def init_client(cfg: dict[str, str]) -> None:
    """Thick-mode init. lib_dir only — no config_dir (see module docstring, point 3)."""
    global _client_initialized
    if _client_initialized:
        return
    import oracledb

    dpi = cfg.get("dpi_debug_level", "0").strip() or "0"
    if dpi != "0":
        os.environ["DPI_DEBUG_LEVEL"] = dpi
    oracledb.init_oracle_client(lib_dir=cfg["oracle_client_path"])
    _client_initialized = True


def connect(
    config_path: str | os.PathLike | None = None,
    sid: str | None = None,
    **overrides: str,
):
    """Open a Kerberos-authenticated connection. Returns an oracledb.Connection.

    ``sid`` (or any config key passed as a keyword) overrides the config file —
    e.g. a teammate porting this into their project: ``connect(sid="D000000")``.
    """
    import oracledb

    if sid is not None:
        overrides["sid"] = sid
    cfg = load_config(config_path, **overrides)

    cc_name = normalize_krb5ccname(cfg.get("kerberos5_cc_name", ""), cfg.get("sid", ""))
    runtime = build_runtime_tns_admin(cfg, cc_name)

    # Init BEFORE exporting TNS_ADMIN so OCI does not parse sqlnet.ora at init
    # time; Kerberos is negotiated only inside connect().
    init_client(cfg)

    os.environ["TNS_ADMIN"] = str(runtime)
    if not is_mslsa(cc_name):
        os.environ["KRB5_CONFIG"] = cfg.get("krb5_config", "")
        os.environ["KRB5CCNAME"] = cc_name

    alias = cfg["servicename"]
    tcp_timeout = int(cfg.get("tcp_connect_timeout", "15") or "15")
    conn = oracledb.connect(dsn=alias, externalauth=True, tcp_connect_timeout=tcp_timeout)
    call_timeout = int(cfg.get("call_timeout_ms", "30000") or "30000")
    conn.call_timeout = call_timeout
    return conn


def verify(config_path: str | os.PathLike | None = None, **overrides: str) -> dict[str, str]:
    """Connect and prove identity + schema visibility with cheap dictionary queries only.

    Deliberately does NOT touch PSGMGR.CM_HIST_VW — it is an expensive view and
    times out even on ROWNUM<=1 probes; that is a workload problem, not a
    connectivity problem.
    """
    conn = connect(config_path, **overrides)
    out: dict[str, str] = {}
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT USER FROM dual")
            out["authenticated_as"] = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM all_objects WHERE owner = 'PSGMGR'")
            out["psgmgr_objects_visible"] = str(cur.fetchone()[0])
        out["oracle_version"] = conn.version
    finally:
        conn.close()
    return out


# ---------------------------------------------------------------------------
# Error → cause map
# ---------------------------------------------------------------------------

_ERROR_MAP: list[tuple[str, str]] = [
    (
        "ORA-12514",
        "Listener does not know the service — single-host descriptor or wrong node. "
        "Use the TNS alias DSN (both ADDRESS_LISTs).",
    ),
    (
        "ORA-01017",
        "Kerberos SSO not negotiated — Thick mode missing or "
        "AUTHENTICATION_SERVICES not (KERBEROS5).",
    ),
    (
        "ORA-12641",
        "Kerberos auth service failed to init — check krb5.conf path, cache "
        "path/ownership, and that the ticket is valid (klist).",
    ),
    (
        "ORA-12154",
        "Alias not resolvable — TNS_ADMIN folder must contain tnsnames.ora with the alias.",
    ),
    (
        "DPY-4000",
        "Alias not resolvable — TNS_ADMIN folder must contain tnsnames.ora with the alias.",
    ),
    (
        "ORA-03156",
        "Query too slow (heavy view?) — bound the query and raise call_timeout; "
        "NOT a connectivity problem.",
    ),
    (
        "DPY-4024",
        "call_timeout exceeded — heavy view or unindexed predicate; NOT a connectivity problem.",
    ),
    (
        "DPI-1047",
        "Oracle client library could not be loaded — check oracle_client_path "
        "and 64-bit vs 32-bit.",
    ),
]


def explain(exc: BaseException) -> str | None:
    """Map a driver exception onto the known cause table (None if unknown)."""
    text = str(exc)
    for code, cause in _ERROR_MAP:
        if code in text:
            return f"{code}: {cause}"
    return None


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _run_with_watchdog(argv: list[str], timeout_s: int) -> int:
    """Re-invoke this script in a child process and kill it on timeout.

    A hung OCI call cannot be interrupted from Python threads; a child process
    is the only reliable guard. Exit 124 on timeout (like GNU timeout).
    """
    child_args = [sys.executable, str(Path(__file__).resolve()), *argv]
    try:
        proc = subprocess.run(child_args, timeout=timeout_s)
        return proc.returncode
    except subprocess.TimeoutExpired:
        print(
            f"\n[oracle_kerberos] TIMED OUT after {timeout_s}s. If it hung at "
            "'validating loaded library' the sqlnet.ora carried MIT settings with an "
            "MSLSA: cache; if it hung during connect, check network/ticket (klist)."
        )
        return 124


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="spider_login",
        description="Oracle (Spider/PSGMGR) Kerberos external-auth login.",
    )
    parser.add_argument("--config", help=f"path to {CONFIG_FILENAME}")
    parser.add_argument("--sid", help="override sid from the config file")
    parser.add_argument(
        "--preflight", action="store_true", help="run local checks only, no connection"
    )
    parser.add_argument(
        "--verify", action="store_true", help="connect and run the identity self-test"
    )
    parser.add_argument("--query", help="connect and run one SQL statement, print rows")
    parser.add_argument(
        "--timeout",
        type=int,
        help="watchdog seconds — run in a child process and kill it if it hangs",
    )
    args = parser.parse_args(argv)

    if args.timeout:
        argv_full = list(sys.argv[1:] if argv is None else argv)
        child = [
            a
            for i, a in enumerate(argv_full)
            if not a.startswith("--timeout") and (i == 0 or argv_full[i - 1] != "--timeout")
        ]
        return _run_with_watchdog(child, args.timeout)

    overrides: dict[str, str] = {}
    if args.sid:
        overrides["sid"] = args.sid

    if args.preflight or args.verify or args.query:
        cfg = load_config(args.config, **overrides)
        print(f"[oracle_kerberos] config: {cfg['_config_path']}")
        checks = preflight(cfg)
        width = max(len(name) for name, _, _ in checks)
        failed = False
        for name, ok, detail in checks:
            print(f"  {'OK ' if ok else 'FAIL'}  {name.ljust(width)}  {detail}")
            failed = failed or not ok
        if args.preflight:
            return 1 if failed else 0
        if failed:
            print("[oracle_kerberos] preflight failures above — attempting connection anyway")

    try:
        if args.verify:
            result = verify(args.config, **overrides)
            for key, value in result.items():
                print(f"  {key} = {value}")
            return 0
        if args.query:
            conn = connect(args.config, **overrides)
            try:
                with conn.cursor() as cur:
                    cur.execute(args.query)
                    if cur.description:
                        for row in cur:
                            print(row)
            finally:
                conn.close()
            return 0
    except Exception as exc:  # — CLI boundary: map + report every failure
        cause = explain(exc)
        print(f"[oracle_kerberos] FAILED: {exc}")
        if cause:
            print(f"[oracle_kerberos] likely cause — {cause}")
        return 1

    parser.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
