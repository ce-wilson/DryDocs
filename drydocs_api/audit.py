"""API audit logging — the `api` and `api-debug` kinds (G108, ADR 0014 clause 6).

The component logged NOTHING before this: no record existed of who asked the
graph for what through the API. This module writes that record — one line per
audited request — as TWO DECLARED KINDS (config/log-kinds.yaml, ruled
2026-08-25):

- ``api`` — the AUDIT record: lean, per-day, 90-day retention (a metrics window
  on what is searched, not an audit relic). It NEVER carries Cypher text or
  result values; it is an access record, not a data copy.
- ``api-debug`` — the trace tier: per-run, short retention, and it DOES carry
  Cypher text and request detail. Enabled by the kind's own declared
  ``level: DEBUG`` — settings-level, never per request, because an HTTP request
  has no ``--verbose`` and a per-request header would let an untrusted caller
  turn on verbose capture of their own traffic. Whether this text is ever
  DISPLAYED anywhere is held for SME review; this module writes it and nothing
  surfaces it.

THE ENUMERATION (the G108 deliverable: found by reading app.py's routes, not
from memory). The audited set is every route that EXECUTES CYPHER or WRITES —
the scope the 2026-08-25 ruling widened from Cypher-only, because intake.py
writes to the data root and would otherwise be the one filesystem-touching
surface with no trail. Twelve routes:

  Cypher-executing (5):
    POST /query/{query_id}        runs a named view query
    POST /raw-cypher              admin-gated raw Cypher
    POST /specs/{spec_id}/run     registered + ephemeral QuerySpecs
    POST /specs/{spec_id}/export  spec run streamed to a download; the record
                                  lands at job creation with rows null — row
                                  counts for a stream belong to the export
                                  manifest, which registers on completion
    POST /specs/ephemeral         registers Cypher for later execution — the
                                  Cypher ENTERS the system here, and it is the
                                  route the QA agent's run_id arrives on
  Writes (7):
    POST /intake                          record to the data root
    POST /intake/{id}/evidence            files to the data root
    POST /intake/{id}/transition          status machine write
    POST /intake/{id}/thread-decision     decision write
    POST /mappings/overrides/draft        rows into var/mapping.db
    POST /mappings/drafts/{id}/promote    draft status flip in var/mapping.db
    POST /mappings/app-code/draft         rows into var/mapping.db

  Deliberately NOT audited, and why:
    /health /queries GET /specs GET /demo         static reads, no Cypher
    /login /logout                                touch only the in-memory
                                                  session store; company-side
                                                  OIDC replaces them wholesale
    POST /mappings/changeset                      returns a change artifact and
                                                  persists NOTHING server-side
                                                  (the O13 "only write is the
                                                  returned artifact" contract)
    GET /exports/{id}/manifest, GET /intake*,     reads over local stores,
    GET /mappings/*                               no Cypher, no writes
  A request rejected before a bearer token exists (401 missing header) is not
  audited — there is no actor to record; everything from token extraction on
  is, including invalid-token and forbidden outcomes with the ORIGINAL error
  class (never the mapped HTTPException).

THE ACTOR IS ALWAYS HASHED — sha256 hexdigest of the bearer token, the same
function the :AgentRun writer applies to caller identity (a known-value test
pins the equivalence rather than asserting it). A raw actor value never lands,
so the record stays publishable under the §3 sensitivity rules and cannot
become the place a real identity leaks.

THE CORRELATION ID (ruling D) is what joins this record to the QA ledger: the
ledger holds the question text keyed by ``run_id``, this record holds route and
outcome, and without a shared key "what is searched" has half its answer in
each file. Where the caller supplies an agent run id (``X-DryDocs-Run-Id``,
sent by agents/common/ephemeral_client since G108) that is the correlation id;
otherwise it falls back to the hashed session token — the same value
control.py already passes as the owner token. ``correlation_source`` says
which one won.

Sink and naming follow G105 exactly, the way the ``qa`` kind already does for
jsonl: filenames DERIVED via ``log_kinds.log_filename`` in the directory
``run_log.resolve_log_dir`` resolves (the RuntimeSettings log directory). No
second logging mechanism — the declaration in config/log-kinds.yaml IS the
mechanism, and this writer is the one it names. Writing is best-effort after
the G105 amendment's idiom: telemetry never turns a good answer into an error,
and a permanently broken sink warns once instead of passing silently.
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

from drydocs_core.log_kinds import kind, log_filename
from drydocs_core.run_log import resolve_log_dir

AUDIT_KIND = "api"
DEBUG_KIND = "api-debug"
#: the free-form <name> segment both kinds share: api.access.<day>.jsonl and
#: api-debug.access.<run-stamp>.jsonl pair up in a directory listing.
AUDIT_NAME = "access"

#: the debug tier's Cypher size bound — stated here and in the kind's declared
#: note, per the acceptance's "whoever records query text states its bound".
#: 20k chars holds every repo-declared spec with an order of magnitude to
#: spare; a longer text is truncated and flagged, never dropped.
CYPHER_TEXT_BOUND = 20_000

#: X-DryDocs-Run-Id is untrusted caller input headed for a 90-day record:
#: bound its length and shape so it cannot become a log-bloat channel. A value
#: failing the shape is dropped (the correlation falls back to the session
#: hash) rather than sanitized — a mangled key joins nothing anyway.
RUN_ID_BOUND = 128

_LOGGER = logging.getLogger(__name__)


def actor_hash(value: str) -> str:
    """sha256 hexdigest of the utf-8 text — the :AgentRun caller-identity
    function (agents/common/agent_run_writer._sha256), reimplemented here
    because the agents tree is a separate venv, and pinned equivalent by a
    known-value test."""
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def clean_run_id(value: str | None) -> str | None:
    """The supplied correlation run id, or None when it fails the shape."""
    if not value:
        return None
    value = value.strip()
    if not value or len(value) > RUN_ID_BOUND or not value.isprintable():
        return None
    return value


@dataclass
class AuditRecord:
    """One audited request, mutable while the route fills it in.

    ``cypher``/``params`` are DEBUG-TIER fields: the api-kind line is built by
    an explicit allowlist that can never include them (tested structurally),
    so setting them on the record is always safe for the route to do.
    """

    route: str
    actor_sha256: str | None = None
    run_id: str | None = None
    query_id: str | None = None
    spec_id: str | None = None
    database: str | None = None
    rows: int | None = None
    error_class: str | None = None
    elapsed_ms: int | None = None
    detail: dict[str, object] = field(default_factory=dict)
    # debug tier only — never in the api-kind line
    cypher: str | None = None
    params: dict[str, object] | None = None

    @property
    def correlation(self) -> tuple[str | None, str | None]:
        """(correlation_id, correlation_source): the agent run id where one was
        supplied, else the hashed session token (ruling D)."""
        if self.run_id:
            return self.run_id, "run_id"
        if self.actor_sha256:
            return self.actor_sha256, "session"
        return None, None


class ApiAuditLog:
    """Append-only JSONL writer for the two api kinds.

    Opened per append like the ledger (concurrent workers interleave lines
    instead of clobbering a handle). ``log_dir``/``kinds_path`` are injectable
    for tests; the defaults are the resolved log root and the repo
    declaration. The api-debug filename's per-run stamp is FROZEN at
    construction — one server process, one trace file — while the per-day
    audit filename re-derives on every append so day rollover just works.
    """

    def __init__(self, log_dir: Path | None = None, kinds_path: Path | None = None) -> None:
        self._log_dir = log_dir
        self._kinds_path = kinds_path
        self._warned = False
        self._debug_enabled = False
        self._debug_filename: str | None = None
        try:
            debug_kind = kind(DEBUG_KIND, kinds_path)
            self._debug_enabled = debug_kind.level == "DEBUG"
            if self._debug_enabled:
                self._debug_filename = log_filename(DEBUG_KIND, AUDIT_NAME, path=kinds_path)
        except Exception:
            # an unreadable declaration disables the DEBUG tier only; the
            # audit tier still tries per append and warns once if it cannot
            _LOGGER.warning("api-debug kind unreadable; debug tier disabled", exc_info=True)

    @property
    def debug_enabled(self) -> bool:
        return self._debug_enabled

    @contextmanager
    def observe(self, route: str, *, token: str | None = None, run_id: str | None = None):
        """Audit one request: yields the record for the route to fill, writes
        it on the way out — INCLUDING when the block raises, so a route dying
        mid-query still leaves a line carrying the original error class."""
        record = AuditRecord(route=route)
        record.actor_sha256 = actor_hash(token) if token else None
        record.run_id = clean_run_id(run_id)
        started = time.perf_counter()
        try:
            yield record
        except BaseException as exc:
            record.error_class = type(exc).__name__
            raise
        finally:
            record.elapsed_ms = int((time.perf_counter() - started) * 1000)
            self.write(record)

    def write(self, record: AuditRecord) -> None:
        """One api-kind line (allowlisted fields), plus the api-debug line when
        the declaration enables it. Best-effort: never raises."""
        correlation_id, correlation_source = record.correlation
        line: dict[str, object] = {
            "ts": datetime.now(UTC).isoformat(timespec="seconds"),
            "route": record.route,
            "actor_sha256": record.actor_sha256,
            "correlation_id": correlation_id,
            "correlation_source": correlation_source,
            "run_id": record.run_id,
            "query_id": record.query_id,
            "spec_id": record.spec_id,
            "database": record.database,
            "outcome": "error" if record.error_class else "ok",
            "error_class": record.error_class,
            "rows": record.rows,
            "elapsed_ms": record.elapsed_ms,
        }
        if record.detail:
            line["detail"] = dict(record.detail)
        self._append(AUDIT_KIND, line)
        if self._debug_enabled:
            debug_line = dict(line)
            if record.cypher is not None:
                truncated = len(record.cypher) > CYPHER_TEXT_BOUND
                debug_line["cypher"] = record.cypher[:CYPHER_TEXT_BOUND]
                debug_line["cypher_truncated"] = truncated
            if record.params is not None:
                debug_line["params"] = record.params
            self._append(DEBUG_KIND, debug_line)

    # ── mechanics ────────────────────────────────────────────────────────────

    def _path(self, kind_id: str) -> Path:
        log_dir = self._log_dir or resolve_log_dir()
        if kind_id == DEBUG_KIND and self._debug_filename:
            return log_dir / self._debug_filename
        return log_dir / log_filename(kind_id, AUDIT_NAME, path=self._kinds_path)

    def _append(self, kind_id: str, line: dict[str, object]) -> None:
        try:
            path = self._path(kind_id)
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as fh:
                fh.write(json.dumps(line, default=str) + "\n")
        except Exception:
            if not self._warned:  # say so ONCE, then stay quiet — G105's amendment
                self._warned = True
                _LOGGER.warning("api audit write failed; requests continue", exc_info=True)
