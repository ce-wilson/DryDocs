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
from drydocs_core.orchestration.controlm.variables import SHELL_VAR_NAMES, classify_variable
from drydocs_core.orchestration.shell import NAMED_LAUNCHER_RULES
from drydocs_core.orchestration.shell import dpl_properties as _dpl_properties

from ..model import (
    ETL_PROCESS_KINDS,
    DataAssetNode,
    LineageGraph,
    ProcessNode,
    asset_id,
    process_id,
)

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


#: G97 — the launcher/payload split, and WHICH FACT SAYS WHICH. These are the
#: G16 FACT_REGISTRY canonical fact_types, reached through
#: ``classify_variable`` so the "aliases suggest, VALUES decide" contract
#: applies: a variable whose VALUE is a registered launcher is a launcher
#: reference whatever it is NAMED (the JAR_PATH -> dt-launcher.sh gotcha), and
#: a bare digest is a SHA, never a URI. The 2,384-variable gap analysis' one
#: durable finding is that names lie, so nothing below ever reads a name.
_PAYLOAD_FACT = "ARTIFACT_URI"
_LAUNCHER_FACT = "LAUNCHER_SCRIPT_PATH"

#: fact_type -> the :Script property it becomes. EXACTLY the set gate
#: cmdline-nfr-vetting SME-3 (2026-07-21) adopted with m7 — platform /
#: artifact_uri / artifact_kind / platform_flags / script_path. ARTIFACT_SHA is
#: deliberately NOT here: it is named by the acceptance as a DISCRIMINATOR (a
#: job carrying one has an artifact) and it is counted as such below, but SME-3
#: did not adopt it as a Script property and this build mints no property a
#: signed ruling did not name.
_ARTIFACT_PROPS = {
    "ETL_PLATFORM": "platform",
    "PLATFORM_FLAGS": "platform_flags",
    "ARTIFACT_KIND": "artifact_kind",
    _LAUNCHER_FACT: "script_path",
}

#: the kind for a payload Script minted from a variable rather than parsed out
#: of a command line. Deliberately OUTSIDE ``ETL_PROCESS_KINDS`` so the writer
#: resolves it to the :Script endpoint class — scheduler_uses_artifact's
#: to_node is `Script` (SME-2), not the Script|ETLProcess union INVOKES got.
_ARTIFACT_KIND = "etl_artifact"

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
    # -- the G97 launcher/payload split. Clause (e): every invocation lands in
    #    exactly one of classified-launcher / classified-payload / unclassified,
    #    and an unclassified one STAYS WHERE IT IS — never promoted on a guess.
    launchers_classified: int = 0  # cmdline nodes stamped script_role=launcher
    payloads_classified: int = 0  # USES_ARTIFACT candidates linked
    invocations_unclassified: int = 0  # cmdline nodes with neither role — unchanged
    payloads_migrated_off_invokes: int = 0  # payload that HAD an INVOKES edge; moved
    payloads_kept_on_invokes_etl: int = 0  # payload is an :ETLProcess — §B2 keeps it
    invocations_etl_process: int = 0  # cmdline node is an :ETLProcess (G12/§B2)
    artifact_rows_read: int = 0  # variable rows carrying an artifact/launcher fact
    artifact_jobs_unmatched: int = 0  # artifact fact whose job is not in this extract
    artifact_values_unresolved: int = 0  # value holds %%refs/whitespace — no node minted
    artifact_sha_seen: int = 0  # ARTIFACT_SHA discriminators observed (not a property)

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
            f"added={self.prepost_file_ops_added} | "
            f"roles: launcher={self.launchers_classified} "
            f"payload={self.payloads_classified} "
            f"unclassified={self.invocations_unclassified} "
            f"etl_process={self.invocations_etl_process} "
            f"(migrated={self.payloads_migrated_off_invokes} "
            f"etl_kept={self.payloads_kept_on_invokes_etl}) | "
            f"artifact-vars: rows={self.artifact_rows_read} "
            f"unmatched={self.artifact_jobs_unmatched} "
            f"unresolved={self.artifact_values_unresolved}"
        )


def _is_resolved_literal(value: str) -> bool:
    """True when a variable value names a KNOWN artifact rather than a promise.

    An unresolved ``%%VAR`` reference and a multi-token command are both real
    and common (SME-1: "payloads are often variable-held/unresolvable"), and
    neither identifies an artifact — staging one would put a node named
    ``%%JAR_PATH`` in the graph, which reads as a real artifact forever after.
    Counted by the caller, never silently dropped."""
    stripped = value.strip()
    return bool(stripped) and "%%" not in stripped and not any(c.isspace() for c in stripped)


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
            # AFTER the CMD_LINE pass on purpose: the split reads the nodes that
            # pass already staged, so a payload it can match is MOVED off INVOKES
            # rather than duplicated beside it (clause d).
            self._artifact_pass(vars_path, into, coverage)
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
            # G97 clause (e), decided HERE because this is where the registry's
            # verdict is in hand. `script_role` is a ruled :Script property
            # (SME-3), so it belongs in this bag; the classifier RULE that
            # produced it does not — that bag is definition-level launcher
            # params and a test guards it against exactly this kind of drift.
            if kind in ETL_PROCESS_KINDS:
                # this node is an :ETLProcess, and script_role is a :Script
                # property (SME-3) — stamping it here would put a Script
                # refinement on a node that is not one. §B2 keeps these on
                # INVOKES anyway, so they are their own count, not "unclassified".
                coverage.invocations_etl_process += 1
            elif inv.classifier_rule in NAMED_LAUNCHER_RULES:
                props["script_role"] = "launcher"
                coverage.launchers_classified += 1
            else:
                coverage.invocations_unclassified += 1
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

    # -- G97: the launcher / payload split ---------------------------------------
    def _artifact_pass(self, csv_path: Path, into: LineageGraph, coverage: ExtractCoverage) -> None:
        """Artifact variables → USES_ARTIFACT payload candidates (G97).

        WHY THIS READS VARIABLES AND NOT THE COMMAND LINE. A command line names
        what was TYPED; the payload a launcher dispatches is usually held in a
        folder/job VARIABLE, which is why gate cmdline-nfr-vetting SME-1
        rejected the payload-sourced TRIGGERS variant ("payloads are often
        variable-held/unresolvable") and why the G97 acceptance names the G16
        FACT_REGISTRY canonicals as the discriminator. Classification runs
        through :func:`classify_variable`, so the value contract decides and the
        variable's NAME never does.

        Each payload becomes a :Script (SME-2 ruled the edge
        ControlMJob→Script{payload}) carrying script_role='payload' plus the
        SME-3 property set, joined to its job by USES_ARTIFACT. Where the
        CMD_LINE pass already staged that same artifact, the node is REUSED and
        its INVOKES edge is MOVED — that is the "payload invocations migrate out
        of the 1..n fold" both signed entries describe, and doing it here is
        what makes a payload on both labels impossible rather than merely
        unlikely (clause d).
        """
        by_name = self._job_name_index(into)
        # job -> {fact_type: value}; one job's artifact facts are only complete
        # once the whole file is read, so collect first and mint after
        facts: dict[str, dict[str, str]] = {}
        evidence: dict[str, list[str]] = {}
        with csv_path.open(newline="", encoding="utf-8-sig") as fh:
            for var_row in csv.DictReader(fh):
                name = _var(var_row, "var_name")
                value = _var(var_row, "var_value")
                if not name:
                    continue
                classified = classify_variable(name, value)
                fact = classified.fact_type
                if fact not in _ARTIFACT_PROPS and fact not in (_PAYLOAD_FACT, "ARTIFACT_SHA"):
                    continue
                coverage.artifact_rows_read += 1
                if fact == "ARTIFACT_SHA":
                    # a DISCRIMINATOR, not a property (see _ARTIFACT_PROPS):
                    # counted so "this job has an artifact" stays measurable
                    coverage.artifact_sha_seen += 1
                    continue
                jid = self._join_job(var_row, into, by_name)
                if not jid:
                    coverage.artifact_jobs_unmatched += 1
                    continue
                if not _is_resolved_literal(value):
                    # %%REF-bearing or multi-token: the artifact is not KNOWN
                    # here, and minting a node named after an unresolved
                    # reference would put a placeholder in the graph
                    coverage.artifact_values_unresolved += 1
                    continue
                facts.setdefault(jid, {})[fact] = value
                # §B3: the raw evidence string is kept VERBATIM, which under
                # §B2's union endpoints is the only way the class choice stays
                # re-checkable later
                evidence.setdefault(jid, []).append(f"{name}={value}")

        for jid, job_facts in sorted(facts.items()):
            uri = job_facts.get(_PAYLOAD_FACT)
            if not uri:
                continue  # launcher/platform facts alone name no payload
            self._stage_payload(jid, uri, job_facts, evidence.get(jid, []), into, coverage)

    def _stage_payload(
        self,
        jid: str,
        uri: str,
        job_facts: dict[str, str],
        evidence: list[str],
        into: LineageGraph,
        coverage: ExtractCoverage,
    ) -> None:
        """One job's payload artifact → a :Script + a USES_ARTIFACT candidate."""
        existing = self._script_node_at(into, uri)
        if existing is not None and into.processes[existing].kind in ETL_PROCESS_KINDS:
            # §B2 kept INVOKES on :ETLProcess deliberately (it would mean
            # re-modelling G12's working wrapper-payload expansion), and
            # scheduler_uses_artifact's to_node is Script. So this one STAYS
            # where it is and is counted — clause (e), on a ruling not a guess.
            coverage.payloads_kept_on_invokes_etl += 1
            return
        if existing is not None:
            pid = existing
            if (jid, "INVOKES", pid) in into.rels:
                into.rels.discard((jid, "INVOKES", pid))
                coverage.payloads_migrated_off_invokes += 1
        else:
            pid = process_id(_ARTIFACT_KIND, uri)
            into.add_process(
                ProcessNode(
                    node_id=pid,
                    kind=_ARTIFACT_KIND,
                    name=_basename(uri),
                    path=uri,
                )
            )
        node = into.processes[pid]
        node.properties["script_role"] = "payload"
        node.properties["artifact_uri"] = uri
        for fact, prop in _ARTIFACT_PROPS.items():
            if job_facts.get(fact):
                node.properties[prop] = job_facts[fact]
        if evidence:
            node.properties["evidence"] = "\n".join(evidence)
        into.add_rel(jid, "USES_ARTIFACT", pid)
        coverage.payloads_classified += 1

    # -- shared join helpers (the pre/post pass and the artifact pass agree) ------
    @staticmethod
    def _job_name_index(into: LineageGraph) -> dict[str, str | None]:
        """job name -> node id, or None where the name is AMBIGUOUS in this
        extract (a duplicate name resolves to nothing rather than to whichever
        row was read last)."""
        by_name: dict[str, str | None] = {}
        for node in into.processes.values():
            if node.kind == "controlm_job":
                by_name[node.name] = None if node.name in by_name else node.node_id
        return by_name

    @staticmethod
    def _join_job(var_row: dict, into: LineageGraph, by_name: dict[str, str | None]) -> str:
        """A variables-CSV row -> its job node id, by the (folder_id, job_id)
        node key, falling back to a UNIQUE job name. Empty string = unmatched,
        which every caller counts."""
        folder_id = _var(var_row, "folder_id")
        job_id = _var(var_row, "job_id")
        jid = process_id("controlm_job", f"{folder_id}.{job_id}") if folder_id and job_id else ""
        if jid not in into.processes:
            jid = by_name.get(_var(var_row, "job_name")) or ""
        return jid

    @staticmethod
    def _script_node_at(into: LineageGraph, path: str) -> str | None:
        """The already-staged process node whose Script key IS ``path``.

        The writer keys :Script on the node key, so matching on it here is what
        keeps one artifact ONE node: without this, a jar named both in a
        command line and in an ETL_ARTIFACT_URI variable would stage twice,
        MERGE onto the same :Script in the writer, and arrive carrying INVOKES
        and USES_ARTIFACT at once — the one outcome clause (d) forbids."""
        for node_id, node in into.processes.items():
            if node.kind == "controlm_job" or node.kind == _ARTIFACT_KIND:
                continue
            if node_id.split(":", 1)[-1] == path:
                return node_id
        return None

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
