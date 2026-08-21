"""rua code-operations pass (G21) — captured content through the ontology mappers.

Runs over the script and profile CONTENT a rua bundle carried back (the
``rua_copy`` copies :class:`~drydocs_lineage.extractors.rua_inventory.
RuaInventoryExtractor` staged) and maps what it finds onto the EXISTING
software-ontology surfaces — reusing, never duplicating, the G14/G15/G16
machinery:

(a) launcher/interpreter invocations found inside SCRIPTS classify via the
    shared ``LAUNCHER_REGISTRY`` (``drydocs_core.orchestration.controlm.parse_command``);
    a DPL launch keeps its pipeline-GUID identity (G15) via the same
    ``_stable_invocation_key`` the CMD_LINE extractor uses. They become
    INVOKES candidates from the ``rua_script`` node — scheduler_invokes is
    registered vocabulary; candidates, not writes.
(b) variable ASSIGNMENTS (``NAME=value`` / ``export NAME=value``) classify
    via the FACT_REGISTRY ETL_* canonicals with the G16 value contracts —
    values decide, names only suggest; name/value mismatches and alias
    spellings ride the WARN counters, and every fact lands in the result's
    ``facts`` list for curation.
(c) FILE OPERATIONS (move/copy/gzip and kin) in scripts emit READS_FROM /
    WRITES_TO candidates with endpoints exactly per the 2026-07-15 gate
    EDIT — the acting artifact is the staged script node, the operands are
    ``local_file`` DataAssets (the G14 CMD_LINE idiom, one level down). No
    new relationship types; every m3_*/m7 status is untouched.
(d) PROFILE parsing captures PATH mutations and sourced/invoked scripts as
    script-to-script DEPENDENCY CANDIDATES, flagged ``needs_vocabulary`` —
    a profile is environment inclusion, not a gated Activity, so the edge
    MEANING is the G22 gate's and profiles stage NO rels here. (``source``
    lines inside scripts are the same inclusion semantics and join the
    same candidate list.)
(e) every skipped or unparseable construct is COUNTED by reason — static
    analysis of shell text is best-effort by design, and the counters make
    the miss rate visible instead of implying completeness.

Run AFTER :class:`RuaInventoryExtractor` on the same :class:`LineageGraph`
and the same bundle directory.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

from drydocs_core.orchestration.controlm import classify_variable, parse_command

from ..model import DataAssetNode, LineageGraph, ProcessNode, asset_id, process_id
from .controlm_inventory import (
    _DATAFLOW_FILE_OPS,
    _FILE_OP_ASSET_KIND,
    _basename,
    _dpl_properties,
    _stable_invocation_key,
)
from .rua_inventory import RUA_PROFILE_KIND, RUA_SCRIPT_KIND, RuaInventoryExtractor

#: shell inclusion verbs — environment/source semantics, never an invocation
_SOURCE_VERBS = {".", "source"}

#: a leading NAME=value token (assignment scan; export/typeset prefixes dropped)
_ASSIGN_RE = re.compile(r"^([A-Za-z_][A-Za-z0-9_]*)=(.*)$", re.DOTALL)
_ASSIGN_PREFIXES = {"export", "typeset", "readonly", "set"}


@dataclass
class RuaCodeOpsCoverage:
    """Per-run accounting — every skip/miss counted BY REASON, never silent."""

    scripts_seen: int = 0
    scripts_parsed: int = 0
    scripts_no_copy: int = 0  # staged listing, but no carried-back content
    scripts_unreadable: int = 0
    profiles_seen: int = 0
    profiles_parsed: int = 0
    profiles_no_copy: int = 0
    profiles_unreadable: int = 0
    lines_read: int = 0
    lines_blank: int = 0
    lines_comment: int = 0
    lines_continuation_joined: int = 0
    assignments_classified: int = 0
    facts_classified: int = 0  # FACT_REGISTRY / value-contract hits
    fact_name_mismatches: int = 0  # G16 WARN: name suggested, value decided
    fact_alias_renames: int = 0  # G16 WARN: non-canonical ETL_* spelling
    invocations_added: int = 0  # INVOKES candidates (scripts only)
    invocations_unresolved: int = 0  # added but classified UNKNOWN
    invocations_no_target: int = 0
    file_ops_added: int = 0  # READS_FROM/WRITES_TO candidates (scripts)
    file_ops_skipped_non_dataflow: int = 0
    file_ops_no_operand: int = 0
    profile_file_ops_skipped: int = 0  # profiles stage no rels — counted, not staged
    statements_unparsed: int = 0  # parse_command could not classify
    path_mutations: int = 0
    dependency_candidates: int = 0  # source/invocation inclusions (needs vocabulary)

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"scripts={self.scripts_parsed}/{self.scripts_seen} "
            f"profiles={self.profiles_parsed}/{self.profiles_seen} | "
            f"invocations={self.invocations_added} "
            f"(unresolved={self.invocations_unresolved} "
            f"no_target={self.invocations_no_target}) "
            f"file_ops={self.file_ops_added} "
            f"(non_dataflow={self.file_ops_skipped_non_dataflow} "
            f"no_operand={self.file_ops_no_operand} "
            f"profile_skipped={self.profile_file_ops_skipped}) | "
            f"facts={self.facts_classified}/{self.assignments_classified} "
            f"(mismatch={self.fact_name_mismatches} alias={self.fact_alias_renames}) | "
            f"deps={self.dependency_candidates} path_mut={self.path_mutations} | "
            f"missing: copy={self.scripts_no_copy}+{self.profiles_no_copy} "
            f"unreadable={self.scripts_unreadable}+{self.profiles_unreadable} "
            f"unparsed={self.statements_unparsed}"
        )


@dataclass
class RuaCodeOps:
    """The pass result: counters plus the candidate material curation reads.

    ``dependency_candidates`` entries carry ``needs_vocabulary: True`` on
    purpose — script-to-script inclusion has NO registered relationship type,
    and minting one is the G22 gate's call, never this pass's.
    """

    coverage: RuaCodeOpsCoverage = field(default_factory=RuaCodeOpsCoverage)
    facts: list[dict] = field(default_factory=list)
    path_mutations: list[dict] = field(default_factory=list)
    dependency_candidates: list[dict] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "coverage": self.coverage.as_dict(),
            "facts": self.facts,
            "path_mutations": self.path_mutations,
            "dependency_candidates": self.dependency_candidates,
        }


def _logical_lines(text: str, coverage: RuaCodeOpsCoverage) -> list[str]:
    """Physical lines → logical lines: backslash continuations joined, blank
    and full-line-comment lines counted and dropped."""
    out: list[str] = []
    pending = ""
    for raw in text.splitlines():
        coverage.lines_read += 1
        line = pending + raw
        if line.rstrip().endswith("\\"):
            pending = line.rstrip()[:-1] + " "
            coverage.lines_continuation_joined += 1
            continue
        pending = ""
        stripped = line.strip()
        if not stripped:
            coverage.lines_blank += 1
            continue
        if stripped.startswith("#"):
            coverage.lines_comment += 1
            continue
        out.append(stripped)
    if pending.strip():
        out.append(pending.strip())
    return out


def _split_leading_assignments(line: str) -> tuple[list[tuple[str, str]], str]:
    """Peel ``export``/``typeset`` prefixes and leading NAME=value tokens off a
    logical line. Returns (assignments, remainder-statement)."""
    tokens = line.split()
    assigns: list[tuple[str, str]] = []
    i = 0
    while i < len(tokens):
        tok = tokens[i]
        if tok in _ASSIGN_PREFIXES and not _ASSIGN_RE.match(tok):
            i += 1
            continue
        m = _ASSIGN_RE.match(tok)
        if m is None:
            break
        name, value = m.group(1), m.group(2)
        # a quoted value with spaces was split by .split(); re-join until the
        # quote closes (best-effort — shell text, not a grammar)
        if value[:1] in "'\"" and not value.endswith(value[0]):
            quote = value[0]
            while i + 1 < len(tokens) and not tokens[i].endswith(quote):
                i += 1
                value += " " + tokens[i]
        assigns.append((name, value.strip("'\"")))
        i += 1
    return assigns, " ".join(tokens[i:])


class RuaCodeOpsExtractor:
    """Bundle content → software-ontology candidates (G21; candidate side only)."""

    name = "rua-code-ops"

    def extract(self, source: str | Path, into: LineageGraph) -> RuaCodeOps:
        """``source`` is the extracted bundle dir (the same one the inventory
        pass read); ``into`` is the SAME graph, already holding the staged
        ``rua_script`` / ``rua_profile`` nodes with their ``rua_copy``
        pointers. Returns the pass result; callers report it."""
        bundle_dir = RuaInventoryExtractor()._resolve_bundle_dir(Path(source))
        result = RuaCodeOps()
        cov = result.coverage
        for node in list(into.processes.values()):
            if node.kind == RUA_SCRIPT_KIND:
                cov.scripts_seen += 1
                self._artifact(node, bundle_dir, into, result, is_script=True)
            elif node.kind == RUA_PROFILE_KIND:
                cov.profiles_seen += 1
                self._artifact(node, bundle_dir, into, result, is_script=False)
        return result

    # -- one artifact ---------------------------------------------------------
    def _artifact(
        self,
        node: ProcessNode,
        bundle_dir: Path,
        graph: LineageGraph,
        result: RuaCodeOps,
        *,
        is_script: bool,
    ) -> None:
        cov = result.coverage
        copy_rel = node.properties.get("rua_copy", "")
        if not copy_rel:
            if is_script:
                cov.scripts_no_copy += 1
            else:
                cov.profiles_no_copy += 1
            return
        try:
            text = (bundle_dir / copy_rel.lstrip("/")).read_text(encoding="utf-8", errors="replace")
        except OSError:
            if is_script:
                cov.scripts_unreadable += 1
            else:
                cov.profiles_unreadable += 1
            return
        if is_script:
            cov.scripts_parsed += 1
        else:
            cov.profiles_parsed += 1

        for line in _logical_lines(text, cov):
            self._line(line, node, graph, result, is_script=is_script)

    # -- one logical line -------------------------------------------------------
    def _line(
        self,
        line: str,
        node: ProcessNode,
        graph: LineageGraph,
        result: RuaCodeOps,
        *,
        is_script: bool,
    ) -> None:
        cov = result.coverage
        first = line.split(None, 1)[0] if line.split() else ""

        # (d) inclusion semantics: `. /path` / `source /path` — a dependency
        # CANDIDATE (needs vocabulary), in scripts and profiles alike.
        if first in _SOURCE_VERBS:
            target = next((t for t in line.split()[1:] if not t.startswith("-")), None)
            if target:
                result.dependency_candidates.append(
                    {
                        "src_kind": node.kind,
                        "src_path": node.path,
                        "target": target,
                        "via": "source",
                        "needs_vocabulary": True,
                    }
                )
                cov.dependency_candidates += 1
            return

        assigns, remainder = _split_leading_assignments(line)
        for name, value in assigns:
            cov.assignments_classified += 1
            if name == "PATH" and not is_script:
                result.path_mutations.append(
                    {
                        "profile_path": node.path,
                        "value": value,
                    }
                )
                cov.path_mutations += 1
                continue
            cv = classify_variable(name, value)
            if cv.fact_type is not None:
                cov.facts_classified += 1
                if cv.fact_name_mismatch:
                    cov.fact_name_mismatches += 1
                if cv.fact_alias_of:
                    cov.fact_alias_renames += 1
                result.facts.append(
                    {
                        "artifact_kind": node.kind,
                        "artifact_path": node.path,
                        "name": name,
                        "value": value,
                        "fact_type": cv.fact_type,
                        "fact_name_mismatch": cv.fact_name_mismatch,
                        "fact_alias_of": cv.fact_alias_of,
                    }
                )
        if not remainder:
            return

        parsed = parse_command(remainder)
        for fop in parsed.file_ops:
            self._file_op(node, fop, graph, cov, is_script=is_script)
        for inv in parsed.invocations:
            self._invocation(node, inv, graph, result, is_script=is_script)
        cov.statements_unparsed += len(parsed.unparsed)

    # -- (c) file ops → READS_FROM / WRITES_TO candidates -------------------------
    def _file_op(
        self,
        node: ProcessNode,
        fop,
        graph: LineageGraph,
        cov: RuaCodeOpsCoverage,
        *,
        is_script: bool,
    ) -> None:
        """Mirrors the G14 CMD_LINE idiom one level down: the acting artifact
        is the staged script node; endpoints per the 2026-07-15 gate EDIT.
        Profiles stage NO rels (their edge meaning is G22's) — counted."""
        if not is_script:
            cov.profile_file_ops_skipped += 1
            return
        if fop.op_type not in _DATAFLOW_FILE_OPS:
            cov.file_ops_skipped_non_dataflow += 1
            return
        src, tgt = fop.src_pattern, fop.tgt_pattern
        if not src or not tgt:
            cov.file_ops_no_operand += 1
            return
        for location, rel_type in ((src, "READS_FROM"), (tgt, "WRITES_TO")):
            aid = asset_id(_FILE_OP_ASSET_KIND, location)
            graph.add_data_asset(
                DataAssetNode(
                    node_id=aid,
                    kind=_FILE_OP_ASSET_KIND,
                    location=location,
                )
            )
            graph.add_rel(node.node_id, rel_type, aid)
            cov.file_ops_added += 1

    # -- (a) invocations → INVOKES candidates (scripts) / dep candidates (profiles)
    def _invocation(
        self,
        node: ProcessNode,
        inv,
        graph: LineageGraph,
        result: RuaCodeOps,
        *,
        is_script: bool,
    ) -> None:
        cov = result.coverage
        target = inv.target
        if not target:
            cov.invocations_no_target += 1
            return
        if not is_script:
            # (d) a profile invoking a script is inclusion, not a gated
            # Activity edge — dependency candidate, no rel.
            result.dependency_candidates.append(
                {
                    "src_kind": node.kind,
                    "src_path": node.path,
                    "target": target,
                    "via": "invocation",
                    "invocation_type": inv.invocation_type,
                    "needs_vocabulary": True,
                }
            )
            cov.dependency_candidates += 1
            return
        kind = inv.invocation_type.lower()
        cid = process_id(kind, _stable_invocation_key(inv, target))
        props = _dpl_properties(inv.args) if kind == "dpl" else {}
        graph.add_process(
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
        graph.add_rel(node.node_id, "INVOKES", cid)
        cov.invocations_added += 1
        if kind == "unknown":
            cov.invocations_unresolved += 1
