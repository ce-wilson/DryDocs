"""Control-M inventory extractor — the lineage seed (re-homed, ADR 0002-C §4).

Reads a CSV export of ``psgmgr.CM_DEF_VJOB`` (the projection in the load side's
``controlm_jobs.sql``) and turns each current-version job into a
:class:`~drydocs_lineage.model.ProcessNode` carrying the authoritative
job/cmd/node_target/run_as/folder/application. It then parses each CMD_LINE — via the
SHARED core parser, ``drydocs_core.orchestration.controlm.parse_command`` (the depgraph fork is
gone; 0002-C §3/G8) — to find the *next lower dependency*, the script/executable the
job launches, and links it with an ``INVOKES`` rel (scheduler_invokes, prov:used). Shared
scripts invoked from multiple folders collapse to one child node with multiple
INVOKES — exactly the lineage we want.

CMD_LINE **file operations** (G14; the pure unix move/copy/gzip wrapper forms the
2026-07-15 gate caveat names) become ``READS_FROM``/``WRITES_TO`` candidates with
the JOB itself as the Activity — a CMD_LINE file op is performed by the job, no
Script hop exists, which is exactly the gate EDIT's file-ops case (``from_node:
ETLProcess | ControlMJob``), so the writer's G13 resolution passes them through
unchanged. Operand patterns become ``local_file`` DataAssets verbatim ({ODATE}
tokens and wildcards are curation material, not noise). Non-data-flow ops
(DELETE/MKDIR/TRANSFORM/OTHER — job mechanics) are skipped AND counted.

PRE/POST-EXECUTION SHELL TEXT (G60). CMD_LINE is not the only carrier of file
operations: the EMBEDDED_SHELL variables ``PRECMD`` / ``POSTCMD`` (and the
observed ``POSCMD`` typo — the spelling set is core's ``SHELL_VAR_NAMES``)
hold the same shell text, and production uses them for exactly the mv/backup
forms the CMD_LINE pass cannot see (parquet plus .tok moved to a backup
path). When a variables CSV is present (explicit ``variables_csv=`` or
discovered beside the jobs CSV), those values run through the SAME G14
file-op grammar with the SAME endpoints — job → local_file, READS_FROM /
WRITES_TO, NO new relationship types. Invocations found in pre/post text are
deliberately NOT emitted: that would be a new candidate class, outside G14's
signed endpoints. Coverage distinguishes the pre/post source from CMD_LINE so
the added yield is measurable, and unparseable values are counted, never
dropped (the house rule).

Division of labor preserved (0002-C §4): the Oracle pull + pydantic row models stay
in core/load; lineage consumes the CSV projection.

Column contract (CSV header == controlm_jobs.sql aliases):
    job_id, version_serial, folder_id, job_name, parent_table, application,
    owner, author, node_id, cmd_line, is_current_version, ...   (extras ignored)
Mapping → ProcessNode:
    node_id→node_target (POLYMORPHIC: host group OR hard-coded host — gate
    controlm-hosts-topology; resolved by the Epic P RUNS_ON pass, not here)
    owner→run_as   job_name→name   parent_table→folder
    application→application   cmd_line→command
Variables column contract (either header shape; read via ``_var``, so the
jobs-CSV drift guard's ``row.get`` scan stays scoped to the jobs loop):
    aliased (controlm_variables.sql): folder_id, job_id, job_name, var_name, var_value
    raw (CM_DEF_SETVAR export):       TABLE_NAME, JOB_ID, JOB_NAME, NAME, VALUE
"""

from __future__ import annotations

import csv
from dataclasses import asdict, dataclass
from pathlib import Path

from drydocs_core.orchestration.controlm import parse_command, pipeline_guid
from drydocs_core.orchestration.controlm.variables import SHELL_VAR_NAMES
from drydocs_core.orchestration.shell import dpl_properties as _dpl_properties

from ..model import DataAssetNode, LineageGraph, ProcessNode, asset_id, process_id

# header tokens that identify a Control-M jobs CSV when searching a directory
_JOBS_CSV_HINTS = ("job_name", "cmd_line", "node_id")

# header-token sets that identify a Control-M variables CSV — either the
# controlm_variables.sql aliased shape or the raw CM_DEF_SETVAR export shape
# (the bundled sample). A candidate matches when EITHER tuple is fully present.
_VARS_CSV_HINTS = (("var_name", "var_value"), ("table_name", "appl_type", "value"))

# aliased-header field -> raw-export synonym, for the variables CSV only
_VARS_RAW_SYNONYMS = {
    "folder_id": "TABLE_NAME",
    "job_id": "JOB_ID",
    "job_name": "JOB_NAME",
    "var_name": "NAME",
    "var_value": "VALUE",
}


def _var(var_row: dict, field: str) -> str:
    """Read a variables-CSV field under either header shape."""
    value = var_row.get(field) or var_row.get(_VARS_RAW_SYNONYMS[field]) or ""
    return value.strip()


#: file-op types that carry data flow (src read, tgt written) — the unix
#: move/copy/gzip wrapper forms named in the 2026-07-15 gate caveat (G14).
#: DELETE/MKDIR/TRANSFORM/OTHER are job mechanics, not lineage flow — skipped
#: and counted, never silent.
_DATAFLOW_FILE_OPS = {"MOVE", "COPY", "COMPRESS"}
#: DataAsset kind for unix file-op operands (the D1 proxy shape)
_FILE_OP_ASSET_KIND = "local_file"

#: every CSV header this extractor consumes (the column contract). Guarded by
#: tests/unit/test_source_mapping_drift.py (N2): each name must remain an alias
#: in controlm_jobs.sql's SELECT list, and this tuple must match the row.get()
#: keys in the code — a renamed alias fails the guard instead of silently
#: dropping the column (the G9 tech-debt finding #2).
CSV_CONTRACT = (
    "application",
    "cmd_line",
    "folder_id",
    "is_current_version",
    "job_id",
    "job_name",
    "node_id",
    "owner",
    "parent_table",
)


@dataclass
class ExtractCoverage:
    """Per-run accounting — every skip is counted BY REASON, never silent
    (the STG_PARSE_QUALITY / UNMATCHED house rule applied to the candidate side).
    """

    rows_read: int = 0
    jobs_added: int = 0  # distinct current-version job nodes
    skipped_stale_version: int = 0  # is_current_version present and not current ('Y')
    skipped_nameless: int = 0  # row with no job_name
    commands_empty: int = 0  # job kept, but cmd_line blank — no candidate
    commands_unparsed: int = 0  # job kept, cmd_line present but 0 invocations AND 0 file ops
    invocations_added: int = 0  # INVOKES candidates linked
    invocations_unresolved: int = 0  # added but kind UNKNOWN (review page warns)
    invocations_no_target: int = 0  # parsed invocation without a resolvable target
    file_ops_added: int = 0  # READS_FROM/WRITES_TO candidates linked (G14) — CMD_LINE source
    file_ops_skipped_non_dataflow: int = 0  # op parsed, but not a data-flow op (DELETE/MKDIR/...)
    file_ops_no_operand: int = 0  # data-flow op missing a usable src/tgt
    # -- pre/post-execution shell text (G60) — counted apart from CMD_LINE so
    #    the added yield is measurable, never folded into the counters above
    prepost_rows_read: int = 0  # PRECMD/POSTCMD/POSCMD variable rows seen
    prepost_jobs_unmatched: int = 0  # shell text whose job is not in this extract
    prepost_commands_empty: int = 0  # shell variable present, value blank
    prepost_commands_unparsed: int = 0  # value present but 0 invocations AND 0 file ops
    prepost_file_ops_added: int = 0  # READS_FROM/WRITES_TO candidates from pre/post text

    def as_dict(self) -> dict[str, int]:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"rows={self.rows_read} jobs={self.jobs_added} "
            f"invocations={self.invocations_added} "
            f"(unresolved={self.invocations_unresolved}) | skipped: "
            f"stale={self.skipped_stale_version} nameless={self.skipped_nameless} "
            f"no_target={self.invocations_no_target} | commands: "
            f"empty={self.commands_empty} unparsed={self.commands_unparsed} | "
            f"file-ops: added={self.file_ops_added} "
            f"non_dataflow={self.file_ops_skipped_non_dataflow} "
            f"no_operand={self.file_ops_no_operand} | "
            f"prepost: rows={self.prepost_rows_read} "
            f"unmatched={self.prepost_jobs_unmatched} "
            f"empty={self.prepost_commands_empty} "
            f"unparsed={self.prepost_commands_unparsed} "
            f"added={self.prepost_file_ops_added}"
        )


def _stable_invocation_key(inv, target: str) -> str:
    """Env-stable identity token for an invoked artifact (SME session
    2026-07-16, gate-log ``cmdline-lineage-review``): a DPL launch is keyed by
    its pipeline GUID — BOTH observed spellings, single-dash ``-pipeline``
    (launcher grammar) and ``--pipeline-id`` (on-prem argument contract; G15)
    — the jar path is shared tooling, the GUID names the workload. An
    Ab Initio pset/graph is keyed by basename (sandbox mount paths vary
    dev/uat/prod for the same graph). Everything else keeps the full target;
    full paths stay on ProcessNode.path either way. Scripts stay PATH-keyed
    on purpose — same-basename multi-mount Script duplicates surface in
    lineage-review for SME merge, never auto-merged."""
    if inv.invocation_type == "DPL":
        guid = pipeline_guid(inv.args)
        if guid:
            return guid
    if inv.invocation_type == "ABINITIO" and target.endswith((".pset", ".m")):
        return _basename(target)
    return target


# The DPL launcher argument contract (G15) is PROMOTED to the shared core
# parser — drydocs_core.orchestration.shell.dpl_properties — so the load
# component's cmdline staging parser (G40) and these extractors read ONE
# contract (imported above as _dpl_properties; rua_code_ops imports it from
# here, unchanged).


def _basename(path: str) -> str:
    return path.replace("\\", "/").rstrip("/").split("/")[-1] or path


class ControlMInventoryExtractor:
    """CSV export → ProcessNodes + INVOKES candidates (curation decides the rest)."""

    name = "controlm-inventory"

    def extract(
        self,
        source: str | Path,
        into: LineageGraph,
        *,
        variables_csv: str | Path | None = None,
    ) -> ExtractCoverage:
        """``source`` is the jobs CSV (preferred) or a directory to search.

        ``variables_csv`` names the variables export carrying the
        PRECMD/POSTCMD shell text (G60); when omitted and ``source`` is a
        directory, one is discovered beside the jobs CSV by header hints.

        Returns the run's :class:`ExtractCoverage` so callers can report what
        was read, added, and skipped (by reason) — nothing drops silently.
        """
        coverage = ExtractCoverage()
        csv_path = self._resolve_csv(Path(source))
        if csv_path is None:
            return coverage  # nothing to do — no Control-M export present
        with csv_path.open(newline="", encoding="utf-8-sig") as fh:
            for row in csv.DictReader(fh):
                coverage.rows_read += 1
                self._row(row, into, coverage)
        vars_path = self._resolve_variables_csv(
            Path(variables_csv) if variables_csv is not None else Path(source)
        )
        if vars_path is not None:
            self._prepost_pass(vars_path, into, coverage)
        return coverage

    # -- internals --------------------------------------------------------------
    def _resolve_csv(self, root: Path) -> Path | None:
        if root.is_file() and root.suffix.lower() == ".csv":
            return root
        if root.is_dir():
            for cand in sorted(root.glob("*.csv")):
                try:
                    header = cand.open(encoding="utf-8-sig").readline().lower()
                except OSError:
                    continue
                if all(h in header for h in _JOBS_CSV_HINTS):
                    return cand
        return None

    def _resolve_variables_csv(self, root: Path) -> Path | None:
        # header-verified in BOTH shapes — an explicit path that is not a
        # variables CSV (e.g. the jobs CSV itself) resolves to None rather
        # than feeding job rows through the shell-variable pass.
        if root.is_file():
            candidates = [root]
        elif root.is_dir():
            candidates = sorted(root.glob("*.csv"))
        else:
            return None
        for cand in candidates:
            if cand.suffix.lower() != ".csv":
                continue
            try:
                header = cand.open(encoding="utf-8-sig").readline().lower()
            except OSError:
                continue
            if any(all(h in header for h in hints) for hints in _VARS_CSV_HINTS):
                return cand
        return None

    def _row(self, row: dict, into: LineageGraph, coverage: ExtractCoverage) -> None:
        # only current-version definitions (CSV may already be filtered)
        icv = (row.get("is_current_version") or "").strip()
        # live domain is 'Y' (D4, 2026-07-15); '1' tolerated for legacy synthetic CSVs
        if icv and icv not in ("Y", "1"):
            coverage.skipped_stale_version += 1
            return
        job_name = (row.get("job_name") or "").strip()
        if not job_name:
            coverage.skipped_nameless += 1
            return
        folder = (row.get("parent_table") or row.get("folder_id") or "").strip()
        folder_id = (row.get("folder_id") or "").strip()
        job_id = (row.get("job_id") or "").strip()
        cmd = (row.get("cmd_line") or "").strip()

        # stable identity = the graph's ControlMJob NODE KEY composite
        # (folder_id, job_id); fall back to folder/job_name for hand-made CSVs.
        key = f"{folder_id}.{job_id}" if (folder_id and job_id) else f"{folder}/{job_name}"
        jid = process_id("controlm_job", key)
        if jid not in into.processes:
            coverage.jobs_added += 1
        into.add_process(
            ProcessNode(
                node_id=jid,
                kind="controlm_job",
                name=job_name,
                command=cmd,
                node_target=(row.get("node_id") or "").strip(),
                run_as=(row.get("owner") or "").strip(),
                folder=folder,
                application=(row.get("application") or "").strip(),
            )
        )

        if not cmd:
            coverage.commands_empty += 1
            return
        parsed = parse_command(cmd)
        for fop in parsed.file_ops:
            self._file_op(jid, fop, into, coverage)
        invocations = parsed.invocations
        if not invocations:
            if not parsed.file_ops:
                coverage.commands_unparsed += 1
            return
        for inv in invocations:
            target = inv.target
            if not target:
                coverage.invocations_no_target += 1
                continue
            kind = inv.invocation_type.lower()
            cid = process_id(kind, _stable_invocation_key(inv, target))
            props = _dpl_properties(inv.args) if kind == "dpl" else {}
            into.add_process(
                ProcessNode(
                    node_id=cid,
                    kind=kind,
                    name=_basename(target),
                    path=inv.script_path or inv.executable_path or "",
                    dataflow=props.pop("dataflow", ""),
                    config_path=props.pop("config_path", "") or (inv.config_path or ""),
                    properties=props,
                )
            )
            into.add_rel(jid, "INVOKES", cid)
            coverage.invocations_added += 1
            if kind == "unknown":
                coverage.invocations_unresolved += 1

    def _prepost_pass(self, csv_path: Path, into: LineageGraph, coverage: ExtractCoverage) -> None:
        """PRECMD/POSTCMD shell text → the SAME G14 file-op feed (G60).

        Joins each EMBEDDED_SHELL variable row (spellings per core's
        ``SHELL_VAR_NAMES``, which carries the observed ``POSCMD`` typo) to
        its job by the (folder_id, job_id) node key, falling back to a UNIQUE
        job name; an unmatched row is counted, never dropped. Invocations
        parsed out of pre/post text are deliberately not emitted — file-op
        candidates only, inside G14's signed endpoints.
        """
        by_name: dict[str, str | None] = {}
        for node in into.processes.values():
            if node.kind == "controlm_job":
                by_name[node.name] = None if node.name in by_name else node.node_id
        with csv_path.open(newline="", encoding="utf-8-sig") as fh:
            for var_row in csv.DictReader(fh):
                bare = _var(var_row, "var_name").removeprefix("%%").strip().upper()
                if bare not in SHELL_VAR_NAMES:
                    continue
                coverage.prepost_rows_read += 1
                folder_id = _var(var_row, "folder_id")
                job_id = _var(var_row, "job_id")
                jid = (
                    process_id("controlm_job", f"{folder_id}.{job_id}")
                    if folder_id and job_id
                    else ""
                )
                if jid not in into.processes:
                    jid = by_name.get(_var(var_row, "job_name")) or ""
                if not jid:
                    coverage.prepost_jobs_unmatched += 1
                    continue
                value = _var(var_row, "var_value")
                if not value:
                    coverage.prepost_commands_empty += 1
                    continue
                parsed = parse_command(value)
                for fop in parsed.file_ops:
                    self._file_op(jid, fop, into, coverage, prepost=True)
                if not parsed.file_ops and not parsed.invocations:
                    coverage.prepost_commands_unparsed += 1

    def _file_op(
        self,
        jid: str,
        fop,
        into: LineageGraph,
        coverage: ExtractCoverage,
        *,
        prepost: bool = False,
    ) -> None:
        """One parsed file op → READS_FROM/WRITES_TO candidates (G14).

        The src endpoint is the JOB itself — a CMD_LINE or PRECMD/POSTCMD
        file op is performed by the job with no Script hop, the gate EDIT's
        file-ops case (from_node: ControlMJob), so the writer's G13 resolution
        passes these through unchanged. Same endpoints for both sources; only
        the COUNTER differs (``prepost``), so the pre/post yield is
        measurable. Every skip is counted by reason (the house rule).
        """
        if fop.op_type not in _DATAFLOW_FILE_OPS:
            coverage.file_ops_skipped_non_dataflow += 1
            return
        src, tgt = fop.src_pattern, fop.tgt_pattern
        if not src or not tgt:
            coverage.file_ops_no_operand += 1
            return
        for location, rel_type in ((src, "READS_FROM"), (tgt, "WRITES_TO")):
            aid = asset_id(_FILE_OP_ASSET_KIND, location)
            into.add_data_asset(
                DataAssetNode(
                    node_id=aid,
                    kind=_FILE_OP_ASSET_KIND,
                    location=location,
                )
            )
            into.add_rel(jid, rel_type, aid)
            if prepost:
                coverage.prepost_file_ops_added += 1
            else:
                coverage.file_ops_added += 1
