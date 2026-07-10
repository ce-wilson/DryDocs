# oracle_kerberos — Spider/PSGMGR "SID login" (standalone)

A small, reusable Python module that logs into the Spider Oracle DB (schema
`PSGMGR`) using **Kerberos v5 external authentication** — no DB
username/password. It hands you a live `oracledb` connection; you run your own
SQL.

- **Drop-in:** copy `spider_login.py` (+ your filled config) into any project.
- **Two audiences:** DryDocs developers testing with their **own SID** locally,
  and the deployed pipeline running under a **functional ID (FID)** on Linux.
- **Sanitized:** everything identifying lives in the gitignored
  `oracle_kerberos_connection.txt`. This module and sample carry placeholders
  only (see `PUBLISH-BOUNDARY.md`).

> Provenance: mechanism reproduced from the team's verified working
> `PSGMGR_CONNECTION_GUIDE.md` recipe plus the 2026-07-02 troubleshooting
> session that isolated the MSLSA/MIT init hang. This file records the
> *mechanism*; real values travel only in the gitignored config.

---

## 1. Prerequisites (one-time per machine)

| Requirement | How to check |
|---|---|
| Oracle 19c full/instant client, **64-bit** | `<oracle_client_path>\oci.dll` exists |
| Python 3.9+ **64-bit** | `python -c "import struct;print(struct.calcsize('P')*8)"` → `64` |
| python-oracledb ≥ 2.5 | `python -c "import oracledb;print(oracledb.__version__)"` |
| Valid Kerberos ticket | `klist` (or check the FILE: cache exists) — renew via enterprise login / `kinit` |
| `tnsnames.ora` with the alias | must contain the alias you connect with, **2 ADDRESS_LISTs** |

## 2. Configure

```powershell
Copy-Item libs/oracle_kerberos/oracle_kerberos_connection.sample.txt `
          libs/oracle_kerberos/oracle_kerberos_connection.txt   # gitignored
# then edit and fill in your values
```

Config discovery order: `--config <path>` → `$ORACLE_KERBEROS_CONFIG` →
current working directory → the module's own folder.

## 3. Use it

```powershell
# local checks only — no network
python libs/oracle_kerberos/spider_login.py --preflight

# connect + identity self-test (SELECT USER FROM dual + all_objects probe)
python libs/oracle_kerberos/spider_login.py --verify

# with a hang watchdog (kills the child after 90 s and prints the likely cause)
python libs/oracle_kerberos/spider_login.py --verify --timeout 90

# ad-hoc SQL
python libs/oracle_kerberos/spider_login.py --query "SELECT SYSDATE FROM dual"
```

```python
from libs.oracle_kerberos import connect

with connect() as conn:            # or connect(sid="D000000") to override
    with conn.cursor() as cur:
        cur.execute("SELECT USER FROM dual")
        print(cur.fetchone())
```

## 4. How it avoids the known failure modes

| # | Failure | What this module does |
|---|---|---|
| 1 | `ORA-12514` from a pinned single host (service floats between RAC nodes) | DSN = the **TNS alias**, resolved from your `tnsnames.ora` with both `ADDRESS_LIST`s; preflight warns if the alias has < 2 |
| 2 | Native crash `0xC0000409` / exit `-1073740791` (conflicting on-disk `sqlnet.ora`) | Generates a **clean runtime `sqlnet.ora`** in a temp `TNS_ADMIN` every run; never reads the profile's |
| 3 | `ORA-01017` (Thin mode can't do Kerberos) | Always **Thick mode**: `init_oracle_client(lib_dir=…)` |
| 4 | 32-bit DLLs on `PATH` | `lib_dir` passed explicitly; preflight checks interpreter bitness and flags `client_1920_32` paths |
| 5 | Bare cache path silently ignored on Windows | `normalize_krb5ccname()` adds the `FILE:` prefix |
| 6 | `dpi_debug_level=64` floods stderr and hides real errors | default `0`; opt-in only |
| 7 | `ORA-03156` / `DPY-4024` on the expensive `CM_HIST_VW` mistaken for a connection failure | `--verify` probes **`all_objects`** instead; sets `call_timeout` on every connection |
| 8 | No/expired ticket → nothing works | preflight checks the cache (FILE: exists / `klist` krbtgt) before connecting |
| 9 | **Init-time hang at `validating loaded library`** (MSLSA: cache + MIT settings) | `init_oracle_client()` gets **no `config_dir`** (TNS_ADMIN exported only after init, so Kerberos negotiates at `connect()`), and in MSLSA: mode the generated `sqlnet.ora` carries **only** `KERBEROS5_CC_NAME=MSLSA:` — no `KERBEROS5_CONF`, no `CONF_MIT` |

### The two credential-cache modes

- **FILE: (default, recommended)** — the MIT cache your `kinit` / enterprise
  login writes (`C:\Users\<SID>\krb5cc_<SID>`). Same flow you already use for
  SQL Developer. `sqlnet.ora` gets `KERBEROS5_CONF` + `CONF_MIT=TRUE` + the
  `FILE:` path. This is the configuration verified working end-to-end.
- **MSLSA: (opt-in)** — the Windows-native LSA cache (pre-populated by domain
  logon, has the cross-realm TGTs). Set `kerberos5_cc_name = MSLSA:`. The
  module then omits every MIT line from `sqlnet.ora`, because MIT-library
  validation against an LSA cache is exactly the init-time hang in row 9.

## 5. Linux VSI / functional ID (FID)

Same module; differences are all environmental:

```bash
kinit -kt /path/to/<FID>.keytab <FID>@<REALM>     # non-interactive ticket
klist                                             # confirm principal + validity
export LD_LIBRARY_PATH=/path/to/oracle/client/lib:$LD_LIBRARY_PATH   # BEFORE python starts
export ORACLE_KERBEROS_CONFIG=/path/to/oracle_kerberos_connection.txt
python spider_login.py --verify
```

- `oracle_client_path` → the dir containing `libclntsh.so`.
- `kerberos5_cc_name` blank → `$KRB5CCNAME`, else `FILE:/tmp/krb5cc_<uid>`.
- Cache file must be **owned/readable by the FID's runtime user** (a cache
  created by another account → `ORA-12641`).
- Tickets expire — schedule `kinit -kt` renewal in the job wrapper
  (Control-M pre-command), and re-run on `ORA-12641`/no-ticket.
- MSLSA:/`FILE:`-prefix quirks are Windows-only.

## 6. Quick error → cause map

| Symptom | Likely cause | Action |
|---|---|---|
| exit `-1073740791` / `0xC0000409`, no traceback | bad on-disk `sqlnet.ora` picked up | this module generates its own; check nothing else sets `TNS_ADMIN` first |
| hang at `validating loaded library` | MIT settings + MSLSA: cache | FILE: mode, or MSLSA: via this module (row 9 above) |
| `ORA-12514` | single-host descriptor, service on other node | use the TNS alias DSN |
| `ORA-01017` | Thin mode / SSO not negotiated | Thick mode + `AUTHENTICATION_SERVICES=(KERBEROS5)` |
| `ORA-12641` | Kerberos init failed | krb5.conf path, cache path/ownership, valid `klist` |
| `ORA-03156` / `DPY-4024` | query too slow (heavy view) | bound the query, raise `call_timeout_ms` — not connectivity |
| `ORA-12154` / `DPY-4000` | alias not resolvable | `TNS_ADMIN` folder must hold `tnsnames.ora` with the alias |
| no ticket in `klist` | missing/expired | enterprise login / `kinit -kt` |

## 7. Relationship to the DryDocs pipeline

This module is deliberately **outside** `drydocs/` — `drydocs_core/adapters/
oracle_adapter.py` is port-frozen (company Kerberos divergence) and must not
be touched. Company-side, the ingestion loaders can import `connect()` from
this module (or the company's own `libs/oracle_kerberos`) without any adapter
change.
