"""TEMPORARY CMD_LINE job-detail staging store (G39) + Python parse (G40).

**RETIREMENT NOTE — this store is a stand-in.** The G18→G22 rua/cmdline plan
assumed a company-side psgmgr ``CM_DEF_VJOB_DETAIL``-style table (job detail
split by task type: file_watcher, cmd_line, …) would exist. It was never
built (premise correction, user 2026-07-27). This module materializes the
same shape as a SQLite store so the G40 parse and the G22 gate clauses have
something to read — and it is DELETED the day a real detail table exists.
Loading the parser's output into that real table is the company-side
follow-up recorded in G40's backlog notes.

Two steps, two CLI verbs:

``drydocs export-cmdline-staging`` (G39)
    One row per loaded :ControlMJob — identity keys (folder_id, job_id,
    job_name, data_center), the task-type discriminator, and the VERBATIM
    cmd_line — sourced FROM THE GRAPH (``j.cmd_line`` is already loaded
    verbatim by ``controlm_jobs.cypher``). The equivalent psgmgr projection
    is documented below (:data:`PSGMGR_PROJECTION_SQL`) as the company-side
    source for the same shape.

    The variables caveat, precisely (amended 2026-07-28): folder/job
    VARIABLE columns stay out of scope — the variables pull into the graph
    is deferred exactly as the original G18→G22 plan sequenced it. RESOLVED
    command lines, however, are IN scope as an input: an internal
    (company-side) resolution query can substitute %%VARs and populate the
    nullable ``cmd_line_resolved`` column after export. This module NEVER
    resolves variables itself — ``cmd_line`` stays verbatim either way, and
    the resolved value rides beside it, origin-flagged by its own column
    (the O24 source-vs-derived discipline).

``drydocs parse-cmdline-staging`` (G40)
    Decomposes every stored cmd_line through the EXISTING machinery — the
    shared core parser (``parse_command``: G26 launcher registry, G15 DPL
    arg contract incl. the %%VAR-launcher GUID fallback, G16 values-decide)
    — into structured detail columns beside the G39 rows. Parses
    ``cmd_line_resolved`` when present, else the verbatim ``cmd_line``
    (the core parser is designed for resolved values — resolution improves
    coverage; which text was parsed is recorded per job in
    ``parse_quality.parsed_from``). Unparseable / partial rows go to the
    WARN stream and are COUNTED, never dropped; a parsed/partial/unparsed
    coverage line prints on every run.

NO GRAPH WRITES anywhere in this module — G22 stays the terminus gate for
anything entering Neo4j. The store lives under the G19 data root
(``DRYDOCS_DATA_ROOT`` — real command lines are Internal; NEVER in-repo)
and is deterministic: same graph → same rows (ordered by the node key; no
wall-clock values stored), mirroring the mapping-store contract.
"""
from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path

from drydocs_core.controlm.commands import dpl_properties, parse_command, pipeline_guid
from drydocs_core.data_root import source_dir

LOGGER = logging.getLogger("drydocs.cmdline_staging")

# v2 (2026-07-28): + job_detail.cmd_line_resolved (the internal resolution
# query's landing column) and parse_quality.parsed_from. The store is derived
# and rebuildable — a v1 file is refused by parse; re-run the export.
SCHEMA_VERSION = "drydocs.cmdline-staging.v2"
DB_FILENAME = "job_detail.db"

RETIREMENT_NOTE = (
    "TEMPORARY stand-in for the unbuilt psgmgr CM_DEF_VJOB_DETAIL-style table "
    "(premise correction 2026-07-27); delete this store the day a real "
    "job-detail table exists."
)

#: The company-side source for the SAME shape (documented beside the store —
#: G39 acceptance). folder_id/job_id aliases follow controlm_jobs.sql, whose
#: loader is where the graph's ``j.cmd_line`` comes from; the graph export
#: below is therefore this projection one hop later.
PSGMGR_PROJECTION_SQL = """\
-- company-side equivalent of the G39 graph export (same columns, same order)
-- psgmgr.CM_DEF_VJOB is the replicated copy of dtsremgr.DEF_VJOB
SELECT
    J.TABLE_ID           AS folder_id,
    J.JOB_ID             AS job_id,
    J.JOB_NAME           AS job_name,
    J.INSTANCE_NAME      AS data_center,
    J.TASK_TYPE          AS task_type,
    CASE WHEN J.IS_CURRENT_VERSION = 'Y' THEN 1 ELSE 0 END AS active,
    J.CMD_LINE           AS cmd_line,
    NULL                 AS cmd_line_resolved
    -- cmd_line_resolved: populated AFTERWARD by the internal %%VAR
    -- resolution query (company-side; runs against psgmgr internally).
    -- This projection never resolves — cmd_line stays verbatim, the
    -- resolved value lands beside it in its own column.
FROM psgmgr.CM_DEF_VJOB J
ORDER BY J.TABLE_ID, J.JOB_ID
"""

#: Graph projection — one row per loaded job, ordered on the NODE KEY so the
#: export is deterministic. data_center = j.instance_name (CM_DEF_VJOB
#: INSTANCE_NAME, the Control-M server/DC instance).
_GRAPH_EXPORT_CYPHER = """\
MATCH (j:ControlMJob)
RETURN j.folder_id     AS folder_id,
       j.job_id        AS job_id,
       j.job_name      AS job_name,
       j.instance_name AS data_center,
       j.task_type     AS task_type,
       j.active        AS active,
       j.cmd_line      AS cmd_line
ORDER BY j.folder_id, j.job_id
"""

_DDL = """
CREATE TABLE IF NOT EXISTS meta (
  key   TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- G39: one row per loaded job. VERBATIM cmd_line; variable COLUMNS out of
-- scope (the variables pull stays deferred, G18->G22) — but a RESOLVED
-- command line is welcome beside it: cmd_line_resolved is the landing
-- column for the internal %%VAR resolution query (company-side; never
-- populated by this module).
CREATE TABLE IF NOT EXISTS job_detail (
  folder_id         TEXT NOT NULL,
  job_id            TEXT NOT NULL,
  job_name          TEXT,
  data_center       TEXT,
  task_type         TEXT,       -- the job/task type discriminator
  active            INTEGER,    -- is_current_version = 'Y' (graph j.active)
  cmd_line          TEXT,       -- verbatim; NULL for jobs with none
  cmd_line_resolved TEXT,       -- %%VARs substituted; NULL until resolution runs
  PRIMARY KEY (folder_id, job_id)
);

-- G40: structured detail columns, one row per parsed invocation.
CREATE TABLE IF NOT EXISTS job_detail_parsed (
  folder_id       TEXT NOT NULL,
  job_id          TEXT NOT NULL,
  seq             INTEGER NOT NULL,
  invocation_type TEXT NOT NULL,   -- G26 launcher registry verdict
  classifier_rule TEXT,
  launcher        TEXT,            -- executable_path (may be a %%VAR ref)
  launch_mode     TEXT,            -- DPL -i/-t/-py (G15; property, never identity)
  script_path     TEXT,            -- the payload
  config_path     TEXT,
  artifact_kind   TEXT,            -- payload extension class (script/jar/pset/...)
  pipeline_guid   TEXT,            -- DPL GUID, both spellings (G15)
  props_json      TEXT,            -- remaining DPL definition-level props
  args_json       TEXT,            -- the argument map, verbatim tokens
  raw_command     TEXT,
  PRIMARY KEY (folder_id, job_id, seq),
  FOREIGN KEY (folder_id, job_id) REFERENCES job_detail (folder_id, job_id)
);

-- G40: per-job verdict — every row accounted for, never silently dropped.
CREATE TABLE IF NOT EXISTS parse_quality (
  folder_id           TEXT NOT NULL,
  job_id              TEXT NOT NULL,
  verdict             TEXT NOT NULL
      CHECK (verdict IN ('parsed','partial','unparsed','no_cmd_line')),
  parsed_from         TEXT
      CHECK (parsed_from IN ('resolved','raw') OR parsed_from IS NULL),
  invocations         INTEGER NOT NULL,
  file_ops            INTEGER NOT NULL,
  unknown_invocations INTEGER NOT NULL,
  unparsed_statements INTEGER NOT NULL,
  PRIMARY KEY (folder_id, job_id)
);
"""

#: payload extension → artifact kind (G40 "artifact kind" column). Unmapped
#: extensions keep the bare extension so nothing is silently lumped.
_ARTIFACT_KINDS = {
    ".sh": "shell-script", ".ksh": "shell-script", ".bash": "shell-script",
    ".py": "python-script", ".pl": "perl-script", ".sql": "sql-script",
    ".jar": "java-archive",
    ".pset": "abinitio-pset", ".m": "abinitio-graph",
    ".cfg": "config", ".ini": "config", ".json": "config",
}


class CmdlineStagingError(RuntimeError):
    """The store is missing/foreign, or a step's precondition fails — loudly."""


def default_db_path(*, create: bool = False) -> Path:
    """``<DRYDOCS_DATA_ROOT>/cmdline-staging/job_detail.db`` (G19 data root —
    real command lines are Internal and NEVER live in-repo)."""
    return source_dir("cmdline-staging", create=create) / DB_FILENAME


def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.executescript(_DDL)
    return conn


# ---------------------------------------------------------------------------
# G39 — export: graph → job_detail
# ---------------------------------------------------------------------------

@dataclass
class ExportReport:
    """Counts, always reported (the never-silent rule)."""

    jobs: int = 0
    with_cmd_line: int = 0
    active: int = 0
    by_task_type: dict[str, int] = field(default_factory=dict)

    def summary(self) -> str:
        types = ", ".join(f"{k or '(none)'}={v}"
                          for k, v in sorted(self.by_task_type.items(),
                                             key=lambda kv: (kv[0] or "")))
        return (
            f"jobs={self.jobs} with_cmd_line={self.with_cmd_line} "
            f"active={self.active} | task_type: {types or '(no rows)'}"
        )


def export_job_detail(client, db_path: str | Path) -> ExportReport:
    """Materialize the G39 store from the graph. All tables are REBUILT
    (dropped + recreated — the graph is the truth; the store is derived and
    rebuildable, and a schema-version bump lands cleanly on an old file).
    LOUD CAVEAT: that includes ``cmd_line_resolved`` — the internal
    resolution query re-runs AFTER each export; resolution work does not
    survive a re-export (the store is temporary plumbing, not a system of
    record)."""
    rows = client.run(_GRAPH_EXPORT_CYPHER)
    report = ExportReport()
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    try:
        conn.executescript(
            "DROP TABLE IF EXISTS job_detail_parsed;"
            "DROP TABLE IF EXISTS parse_quality;"
            "DROP TABLE IF EXISTS job_detail;"
            "DROP TABLE IF EXISTS meta;"
        )
        conn.executescript(_DDL)
        with conn:
            for row in rows:
                cmd = row.get("cmd_line")
                task_type = row.get("task_type")
                conn.execute(
                    "INSERT INTO job_detail (folder_id, job_id, job_name, "
                    "data_center, task_type, active, cmd_line, cmd_line_resolved) "
                    "VALUES (?, ?, ?, ?, ?, ?, ?, NULL)",
                    (row.get("folder_id"), row.get("job_id"), row.get("job_name"),
                     row.get("data_center"), task_type,
                     None if row.get("active") is None else int(bool(row.get("active"))),
                     cmd),
                )
                report.jobs += 1
                report.with_cmd_line += bool(cmd and str(cmd).strip())
                report.active += bool(row.get("active"))
                key = str(task_type) if task_type is not None else ""
                report.by_task_type[key] = report.by_task_type.get(key, 0) + 1
            conn.executemany(
                "INSERT INTO meta (key, value) VALUES (?, ?)",
                sorted({
                    "schema_version": SCHEMA_VERSION,
                    "retirement": RETIREMENT_NOTE,
                    "source": "graph::ControlMJob (loader controlm_jobs; "
                              "cmd_line verbatim)",
                    "psgmgr_projection": PSGMGR_PROJECTION_SQL,
                    "variables": "variable COLUMNS stay OUT OF SCOPE (the "
                                 "folder/job variables pull is deferred, "
                                 "G18->G22 plan) — but cmd_line_resolved is "
                                 "the landing column for the INTERNAL %%VAR "
                                 "resolution query (company-side); this "
                                 "module never resolves, and re-export "
                                 "clears the column (resolution re-runs "
                                 "after each export)",
                }.items()),
            )
    finally:
        conn.close()
    return report


# ---------------------------------------------------------------------------
# G40 — parse: job_detail.cmd_line → job_detail_parsed + parse_quality
# ---------------------------------------------------------------------------

@dataclass
class ParseCoverage:
    """The coverage line — printed on every run, every row accounted for."""

    parsed: int = 0
    partial: int = 0
    unparsed: int = 0
    no_cmd_line: int = 0
    invocations: int = 0
    file_ops: int = 0
    from_resolved: int = 0   # jobs parsed from cmd_line_resolved (not raw)

    @property
    def total(self) -> int:
        return self.parsed + self.partial + self.unparsed + self.no_cmd_line

    def summary(self) -> str:
        return (
            f"coverage: parsed={self.parsed} partial={self.partial} "
            f"unparsed={self.unparsed} no_cmd_line={self.no_cmd_line} "
            f"(of {self.total} jobs; {self.invocations} invocations, "
            f"{self.file_ops} file ops; {self.from_resolved} from resolved "
            "cmd lines)"
        )


def _artifact_kind(script_path: str | None) -> str | None:
    if not script_path:
        return None
    name = script_path.replace("\\", "/").rsplit("/", 1)[-1]
    dot = name.rfind(".")
    if dot <= 0:
        return None
    ext = name[dot:].lower()
    return _ARTIFACT_KINDS.get(ext, ext.lstrip("."))


def parse_job_detail(db_path: str | Path) -> ParseCoverage:
    """Decompose every stored cmd_line into detail columns (G40).

    Reuses the shared core parser end to end: the G26 launcher registry
    classifies, the G15 DPL contract yields GUID + launch_mode + props (the
    %%VAR-launcher fallback fires inside ``parse_command``), and the G16
    values-decide rule holds because classification keys on TOKEN VALUES,
    never on a variable's name. Parses ``cmd_line_resolved`` when the
    internal resolution query has populated it, else the verbatim
    ``cmd_line`` (the core parser is designed for resolved values);
    ``parse_quality.parsed_from`` records which. NO graph writes.
    """
    db_path = Path(db_path)
    if not db_path.exists():
        raise CmdlineStagingError(
            f"staging store not found: {db_path} — run "
            "`drydocs export-cmdline-staging` first (G39)"
        )
    conn = _connect(db_path)
    coverage = ParseCoverage()
    try:
        stored = conn.execute(
            "SELECT value FROM meta WHERE key = 'schema_version'"
        ).fetchone()
        if stored is None or stored[0] != SCHEMA_VERSION:
            raise CmdlineStagingError(
                f"{db_path}: not a {SCHEMA_VERSION} store "
                f"(schema_version={stored[0] if stored else 'MISSING'})"
            )
        rows = conn.execute(
            "SELECT folder_id, job_id, cmd_line, cmd_line_resolved "
            "FROM job_detail ORDER BY folder_id, job_id"
        ).fetchall()
        with conn:
            conn.execute("DELETE FROM job_detail_parsed")
            conn.execute("DELETE FROM parse_quality")
            for folder_id, job_id, cmd, resolved in rows:
                _parse_one(conn, folder_id, job_id, cmd, resolved, coverage)
    finally:
        conn.close()
    return coverage


def _parse_one(conn, folder_id, job_id, cmd, resolved, coverage: ParseCoverage) -> None:
    where = f"job {folder_id}.{job_id}"
    # prefer the internal resolution query's output — the core parser is
    # designed for resolved values; the raw cmd_line stays untouched beside it
    use_resolved = bool(resolved and str(resolved).strip())
    text = resolved if use_resolved else cmd
    if not text or not str(text).strip():
        coverage.no_cmd_line += 1
        _quality(conn, folder_id, job_id, "no_cmd_line", None, 0, 0, 0, 0)
        return
    parsed_from = "resolved" if use_resolved else "raw"
    coverage.from_resolved += use_resolved

    parsed = parse_command(str(text))
    unknown = 0
    for seq, inv in enumerate(parsed.invocations, start=1):
        props = dpl_properties(inv.args) if inv.invocation_type == "DPL" else {}
        launch_mode = props.pop("launch_mode", None)
        conn.execute(
            "INSERT INTO job_detail_parsed (folder_id, job_id, seq, "
            "invocation_type, classifier_rule, launcher, launch_mode, "
            "script_path, config_path, artifact_kind, pipeline_guid, "
            "props_json, args_json, raw_command) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (folder_id, job_id, seq,
             inv.invocation_type, inv.classifier_rule,
             inv.executable_path, launch_mode,
             inv.script_path, inv.config_path,
             _artifact_kind(inv.script_path),
             pipeline_guid(inv.args),
             json.dumps(props, sort_keys=True) if props else None,
             json.dumps(list(inv.args)) if inv.args else None,
             inv.raw_command),
        )
        unknown += inv.invocation_type == "UNKNOWN"

    n_inv = len(parsed.invocations)
    n_fop = len(parsed.file_ops)
    n_unparsed = len(parsed.unparsed)
    coverage.invocations += n_inv
    coverage.file_ops += n_fop

    if n_inv == 0 and n_fop == 0:
        verdict = "unparsed"
        coverage.unparsed += 1
        LOGGER.warning("%s: cmd_line (%s) yielded no invocation and no file "
                       "op (unparsed): %.120s", where, parsed_from, text)
    elif unknown or n_unparsed:
        verdict = "partial"
        coverage.partial += 1
        LOGGER.warning("%s: partial parse (%s) — %d UNKNOWN invocation(s), "
                       "%d unparsed statement(s)", where, parsed_from,
                       unknown, n_unparsed)
    else:
        verdict = "parsed"
        coverage.parsed += 1
    _quality(conn, folder_id, job_id, verdict, parsed_from,
             n_inv, n_fop, unknown, n_unparsed)


def _quality(conn, folder_id, job_id, verdict, parsed_from,
             inv, fop, unknown, unparsed) -> None:
    conn.execute(
        "INSERT INTO parse_quality (folder_id, job_id, verdict, parsed_from, "
        "invocations, file_ops, unknown_invocations, unparsed_statements) "
        "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (folder_id, job_id, verdict, parsed_from, inv, fop, unknown, unparsed),
    )
