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
import uuid
from collections.abc import Callable, Iterator, Mapping
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any

LOGGER = logging.getLogger(__name__)

DEFAULT_LOGDIR = Path.home() / "logs" / "DryDocs"
LOGDIR_ENV = "DRYDOCS_LOGDIR"
LEGACY_LOGDIR_ENV = "SPIDERP_LOGDIR"
CALLER_ENV = "DRYDOCS_CALLER"
LEGACY_CALLER_ENV = "SPIDERP_CALLER"

_RULE = "=" * 66
_THIN_RULE = "-" * 66

#: logger namespaces the capture handler tees into the run log. Both package
#: roots — the WARN streams live under either (e.g. drydocs.loaders.base,
#: drydocs_core.orchestration.controlm.* company-side).
CAPTURE_NAMESPACES = ("drydocs", "drydocs_core")


def resolve_log_dir() -> Path:
    """The configurable log path: DRYDOCS_LOGDIR > SPIDERP_LOGDIR > default.

    G105: the ORDER is unchanged and is now resolved in ONE place —
    :func:`drydocs_core.log_kinds.resolve_root`, reading ``config/log-kinds.yaml``
    — so the log root has a declaration like every other configured path instead
    of living in three module constants. The legacy variable now emits a
    DeprecationWarning when it is the one that resolved; it still resolves.

    Falls back to the module constants if the declaration cannot be read. That is
    deliberate and narrow: a run log must never be the reason a load fails, and
    this function is called from inside ``open()``.
    """
    try:
        from drydocs_core.log_kinds import resolve_root

        return resolve_root(default=DEFAULT_LOGDIR)
    except Exception:  # — a broken declaration must not take the loaders with it
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


def claim_log_path(base_name: str, *, now: Callable[[], datetime] = datetime.now) -> Path:
    """Claim a log file under the shared naming convention, creating the dir.

    ``now`` is injectable (J46): the collision suffix is decided by the second
    stamp, so a test that wants a collision must hold the clock still rather
    than hope two calls land inside the same wall-clock second.
    """
    log_dir = resolve_log_dir()
    log_dir.mkdir(parents=True, exist_ok=True)

    # G105: the stamp granularity and the extension are DERIVED from the declared
    # kind — ``base_name`` is ``<kind>.<name>``, and the kind is what says whether
    # this rotates per run or per day and whether it is .log or .jsonl. Every
    # caller funnels through here, which is what makes `kind` a real thing rather
    # than a prefix three sites happened to agree on for `load` and not for `sql`.
    kind_id, _, name = base_name.partition(".")
    try:
        from drydocs_core.log_kinds import kind as declared_kind
        from drydocs_core.log_kinds import stamp_for

        spec = declared_kind(kind_id)
        stamp = stamp_for(spec.rotation, now())
        suffix = spec.format
    except Exception:  # — an unreadable declaration falls back to the old shape
        stamp = now().strftime("%Y%m%d-%H%M%S")
        suffix = "log"

    path = log_dir / f"{base_name}.{stamp}.{suffix}"
    seq = 1
    while path.exists():  # same base within one stamp (tests, retries, per-day)
        seq += 1
        path = log_dir / f"{base_name}.{stamp}-{seq}.{suffix}"
    return path


class _CaptureHandler(logging.Handler):
    """Tees log records into the run-log file (console config untouched)."""

    def __init__(self, run_log: LoaderRunLog, level: int) -> None:
        super().__init__(level=level)
        self._run_log = run_log
        self.setFormatter(logging.Formatter("%(levelname)s %(name)s: %(message)s"))

    def emit(self, record: logging.LogRecord) -> None:
        try:
            self._run_log._write(self.format(record) + "\n")
            if record.levelno >= logging.WARNING:
                self._run_log._warnings += 1
        except Exception:  # — audit trail, never the failure
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
        except Exception:  # — some CI environments have no user
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


@contextmanager
def batch_run_log(
    name: str,
    *,
    run_id: str | None = None,
    source: str = "",
    target: str = "",
    meta: Mapping[str, Any] | None = None,
) -> Iterator[dict[str, Any]]:
    """Open a :class:`LoaderRunLog` for one COMPONENT batch and close it on both paths.

    G107. ``drydocs/loaders/base.py`` has always done this correctly — open,
    capture the exception, re-raise, close in ``finally`` — but it did it inline,
    so the four components that run their own cadences had no way to get the same
    behaviour without copying the block. Copying it four times is precisely the
    drift G107 exists to prevent: four components, four almost-identical shapes,
    and no single place to fix the one that is subtly wrong. This is that block,
    once.

    Yields a mutable ``summary`` dict. Fill it during the batch; whatever it holds
    at exit becomes the log's summary block. The batch's OWN return value is
    untouched — this records a run, it does not wrap one.

    ``OSError`` while claiming the file is swallowed and the batch runs WITHOUT a
    log, matching ``base.py._open_run_log``: a run log is an audit trail and must
    never be the reason a batch fails. An exception inside the batch is recorded
    and re-raised unchanged.

        with batch_run_log("lineage.curated", target="drydocs") as summary:
            written = do_the_work()
            summary["rels written"] = written
    """
    log = LoaderRunLog(
        name,
        run_id or str(uuid.uuid4()),
        source=source,
        target=target,
        meta=meta,
    )
    summary: dict[str, Any] = {}
    try:
        path = log.open()
    except OSError as exc:  # — unwritable log dir: record nothing, run anyway
        LOGGER.warning("%s: run log unavailable (%s) — continuing without", name, exc)
        yield summary
        return
    log.attach()
    LOGGER.info("[run-log] %s", path)
    error: BaseException | None = None
    try:
        yield summary
    except BaseException as exc:
        error = exc
        raise
    finally:
        log.close(summary, error=error)
