"""Per-run loader log — the SqlRunLog contract generalized to EVERY loader.

Requirement (user directive, 2026-07-22, from the company XML-loader first run):
all extractors/loaders write a per-run log with a **configurable log path**, a
**shared naming convention**, and a **header/meta block from the process** —
instead of streaming hundreds of per-row WARNINGs (the ``description_tokens``
flood) to the console with no durable record.

The contract mirrors :mod:`drydocs_core.adapters.sql_run_log` deliberately —
one log family, two producers:

    header (run metadata) -> captured log stream + reject detail -> footer
    (summary counts)

Configuration (one knob for the whole family):

    DRYDOCS_LOGDIR   log directory for ALL run logs; falls back to
                     SPIDERP_LOGDIR (the Oracle path's original name, kept so
                     company-side inspection snippets work unchanged), then to
                     ``~/logs/DryDocs`` — deliberately outside the repo.
    DRYDOCS_CALLER   the ``script:`` stamp; falls back to SPIDERP_CALLER, then
                     to ``drydocs <argv>``.

Naming convention (shared): ``<kind>.<name>.<YYYYmmdd-HHMMSS>[-N].log`` —
loader runs use kind ``load`` (e.g. ``load.controlm_jobs.v1.20260722-125345.log``);
the SQL extract logs keep their statement base names.

A log may contain real source values (job names, rejected rows) — logs live
outside the repo and are never committed. Writing is best-effort after open:
the log is an audit trail, never the reason a load fails.
"""
from __future__ import annotations

import getpass
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping

DEFAULT_LOGDIR = Path.home() / "logs" / "DryDocs"
LOGDIR_ENV = "DRYDOCS_LOGDIR"
LEGACY_LOGDIR_ENV = "SPIDERP_LOGDIR"
CALLER_ENV = "DRYDOCS_CALLER"
LEGACY_CALLER_ENV = "SPIDERP_CALLER"

_RULE = "=" * 66
_THIN_RULE = "-" * 66

#: logger namespaces the capture handler tees into the run log. Both package
#: roots — the WARN streams live under either (e.g. drydocs.loaders.base,
#: drydocs_core.controlm.* company-side).
CAPTURE_NAMESPACES = ("drydocs", "drydocs_core")


def resolve_log_dir() -> Path:
    """The configurable log path: DRYDOCS_LOGDIR > SPIDERP_LOGDIR > default."""
    for env in (LOGDIR_ENV, LEGACY_LOGDIR_ENV):
        raw = os.environ.get(env, "").strip()
        if raw:
            return Path(raw)
    return DEFAULT_LOGDIR


def caller_stamp() -> str:
    """The ``script:`` header value — how this process was invoked."""
    for env in (CALLER_ENV, LEGACY_CALLER_ENV):
        stamp = os.environ.get(env, "").strip()
        if stamp:
            return stamp
    return "drydocs " + " ".join(sys.argv[1:])


def claim_log_path(base_name: str) -> Path:
    """Claim a log file under the shared naming convention, creating the dir."""
    log_dir = resolve_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    path = log_dir / f"{base_name}.{stamp}.log"
    seq = 1
    while path.exists():  # same base within one second (tests, retries)
        seq += 1
        path = log_dir / f"{base_name}.{stamp}-{seq}.log"
    return path


class _CaptureHandler(logging.Handler):
    """Tees log records into the run-log file (console config untouched)."""

    def __init__(self, run_log: "LoaderRunLog", level: int) -> None:
        super().__init__(level=level)
        self._run_log = run_log
        self.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._run_log._write(self.format(record) + "\n")
            if record.levelno >= logging.WARNING:
                self._run_log._warnings += 1
        except Exception:  # noqa: BLE001 — audit trail, never the failure
            pass


class LoaderRunLog:
    """One self-contained log per loader run.

    Drive it in order: :meth:`open` -> :meth:`attach` -> (stream: captured
    log records via the handler, :meth:`reject` per rejected row) ->
    :meth:`close`. Every method is a no-op after close, and any OSError while
    writing is swallowed after ``open`` succeeds.
    """

    def __init__(
        self,
        loader_name: str,
        run_id: str,
        *,
        source: str = "",
        target: str = "",
        meta: Mapping[str, Any] | None = None,
    ) -> None:
        self.loader_name = loader_name
        self.run_id = run_id
        self.source = source
        self.target = target
        self.meta = dict(meta or {})
        self.path: Path | None = None
        self._fh = None
        self._handler: _CaptureHandler | None = None
        self._rejects = 0
        self._warnings = 0
        self._started = time.monotonic()

    # -- lifecycle ---------------------------------------------------------

    def open(self) -> Path:
        """Claim the file and write the header/meta block from the process."""
        path = claim_log_path(f"load.{self.loader_name}")
        self._fh = path.open("w", encoding="utf-8", newline="")
        self.path = path
        self._started = time.monotonic()
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        try:
            os_user = getpass.getuser()
        except Exception:  # noqa: BLE001 — some CI environments have no user
            os_user = ""
        lines = [
            _RULE,
            f"date       : {now}",
            f"script     : {caller_stamp()}",
            f"loader     : {self.loader_name}",
            f"run id     : {self.run_id}",
            f"source     : {self.source}",
            f"target     : {self.target}",
            f"os user    : {os_user}",
        ]
        for key, value in self.meta.items():
            lines.append(f"{key:<11}: {value}")
        lines.append(_RULE)
        self._write("\n".join(lines) + "\n")
        return path

    def attach(self, level: int = logging.INFO) -> None:
        """Tee ``drydocs*`` log records (the WARN streams) into this file."""
        if self._fh is None or self._handler is not None:
            return
        self._handler = _CaptureHandler(self, level)
        for namespace in CAPTURE_NAMESPACES:
            logging.getLogger(namespace).addHandler(self._handler)

    def reject(self, row_index: int, errors: Any) -> None:
        """Record one rejected row — the FULL stream lands here, uncapped
        (the in-memory summary keeps only ``max_rejects_kept``)."""
        self._rejects += 1
        self._write(f"{_THIN_RULE}\nREJECT row {row_index}: {errors}\n")

    def close(
        self,
        summary: Mapping[str, Any] | None = None,
        error: BaseException | None = None,
    ) -> None:
        if self._handler is not None:
            for namespace in CAPTURE_NAMESPACES:
                logging.getLogger(namespace).removeHandler(self._handler)
            self._handler = None
        if self._fh is None:
            return
        elapsed_ms = int((time.monotonic() - self._started) * 1000)
        if error is not None:
            self._write(f"\nFAILED: {error}\n")
        self._write(f"\n{_THIN_RULE}\n-- summary --\n")
        for key, value in (summary or {}).items():
            self._write(f"{key:<21}: {value}\n")
        self._write(
            f"warnings captured    : {self._warnings}\n"
            f"rejects logged       : {self._rejects}\n"
            f"Done in {elapsed_ms} ms.\n"
        )
        try:
            self._fh.close()
        except OSError:
            pass
        self._fh = None

    # -- internal ----------------------------------------------------------

    def _write(self, text: str) -> None:
        if self._fh is None:
            return
        try:
            self._fh.write(text)
        except OSError:
            pass
