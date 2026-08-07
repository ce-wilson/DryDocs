"""Dead-script archival report (G58) — the §E3 use case with its safety bar.

Gate rua-load-shapes (SIGNED OFF 2026-08-07) named the usage axis's use case:
identifying unused, deprecated code for archival and removal. Because the
output drives DELETION, a false positive removes live code — so every safety
property the gate ruled is structural here, not advisory:

- **§E3 / §H1 — no axis proves absence.** Referenced / present-on-server /
  registry-active are POSITIVE-ONLY observations, each bounded by a different
  coverage limit. Every "absent" statement this report makes reads as "not
  observed by feed X", never "does not exist". Script-to-script calls are
  visible ONLY where the bundle carried the body, so the report states its
  body-copy coverage ON ITSELF — a metadata-only run says so in its own
  output, and its unreferenced rows say "no CMD_LINE reference", never
  "nothing calls it".
- **§E3 — three dispositions, not two.** Genuinely dead (archive and
  remove), MISDEPLOYED (relocate, never delete — §E1's caveat that a script
  may simply have been deployed to the wrong server), and
  unreferenced-but-dynamically-called (keep: a caller is visible in a
  captured script body even though no CMD_LINE names it).
- **§E1 + the D-amendment — the misdeployment finding is SCOPE-GATED.**
  Under shared storage every host sees ONE file and "deployed to the wrong
  server" is close to meaningless; under UNKNOWN scope (every bundle until
  G56 captures the mount table) the finding is SUPPRESSED AND COUNTED, never
  emitted on a guess.
- **Already-archived is a SHAPE, not a status (Idea-82 / §G1's move):** a
  script carrying a code-repo occurrence and NO current server-extract
  occurrence is already archived — the progress measure toward the estate
  target state. That is exactly G24's ``repo_only`` corroboration bucket, so
  it is CROSS-REFERENCED from the :class:`CorroborationReport`, never
  recomputed; the inverse (server occurrence, no repo occurrence) is the
  existing ``never_committed`` bucket, likewise passed through.
- **§H1(i) — the registry axis's unknowns ride along.** ``active_unknown``
  (unrecognized active-flag spellings, counted by the G25 extractor) appears
  in the report rather than being dropped; a run without the registry feed
  says "not observed", not zero.

Everything here reads STAGED candidates (the same :class:`LineageGraph` the
G23 load consumes) and writes nothing — findings are SME review material on
the lineage-review surface, reported and never auto-actioned (§H2/P5).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field

from .model import LineageGraph, ProcessNode
from .writer import normalize_script_path

_JOB_KIND = "controlm_job"

#: row reasons — worded per §H1: what a feed did not observe, never what does
#: not exist. The metadata-only variant names the blind spot explicitly.
_REASON_UNREFERENCED = (
    "no CMD_LINE reference observed, and no caller visible in the carried script bodies"
)
_REASON_UNREFERENCED_NO_BODIES = (
    "no CMD_LINE reference observed (no body copies on this run — "
    "script-to-script callers are invisible to this feed)"
)
_REASON_BODY_CALLED = "no CMD_LINE reference observed, but a captured script body invokes it — keep"


@dataclass
class ArchivalReport:
    """The dead-script report — every count and claim per the gate's wording."""

    # (a) coverage, stated on the report itself
    scripts_total: int = 0
    scripts_with_bodies: int = 0
    metadata_only: bool = False
    coverage_statement: str = ""
    # (b) the three dispositions — distinct buckets, separately counted
    dead: list[dict] = field(default_factory=list)  # archive and remove
    misdeployed: list[dict] = field(default_factory=list)  # relocate, never delete
    dynamically_called: list[dict] = field(default_factory=list)  # keep
    in_use: int = 0  # CMD_LINE-referenced scripts — not candidates at all
    # (c) the scope gate
    misdeployment_suppressed: int = 0  # would-be findings under non-local scope
    # (d) the archived-state cross-reference (G24 buckets, never recomputed)
    corroboration_run: bool = False
    already_archived: list[dict] = field(default_factory=list)  # repo_only, verbatim
    never_committed: int | None = None  # None = corroboration not run
    # (e) the registry axis
    active_unknown: int | None = None  # None = registry feed not observed

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        archived = (
            f"already_archived={len(self.already_archived)} never_committed={self.never_committed}"
            if self.corroboration_run
            else "archived-state not observed (corroboration not run)"
        )
        registry = (
            f"active_unknown={self.active_unknown}"
            if self.active_unknown is not None
            else "registry axis not observed on this run"
        )
        return (
            f"scripts={self.scripts_total} in_use={self.in_use} | "
            f"dead={len(self.dead)} misdeployed={len(self.misdeployed)} "
            f"dynamically_called={len(self.dynamically_called)} | "
            f"misdeployment_suppressed={self.misdeployment_suppressed} | "
            f"{archived} | {registry}"
        )


def _occurrence_records(node: ProcessNode) -> list[dict]:
    """The reified records (§D2); pre-fix graphs fall back to node props."""
    return node.occurrences or [dict(node.properties, path=node.path)]


def _host_spellings(occ: dict) -> set[str]:
    return {s for s in (occ.get("rua_host", ""), occ.get("rua_fqdn", "")) if s}


def archival_report(
    graph: LineageGraph,
    *,
    corroboration=None,
    active_unknown: int | None = None,
) -> ArchivalReport:
    """Build the report over staged candidates (PURE — no graph writes).

    ``corroboration`` is the G24 :class:`~.extractors.code_repo.
    CorroborationReport` where the repo seam ran — its ``repo_only`` /
    ``never_committed`` buckets are cross-referenced verbatim (clause d).
    ``active_unknown`` is the G25 registry counter
    (``RegistryCoverage.active_unknown``); ``None`` means the registry feed
    was not observed on this run — reported as such, never as zero (§H1).
    """
    from .extractors.rua_inventory import RUA_PROFILE_KIND, RUA_SCRIPT_KIND

    report = ArchivalReport(active_unknown=active_unknown)

    # -- reference evidence, split by WHO references (§E3's blind-spot split) --
    cmd_ref_paths: set[str] = set()  # dst of INVOKES/TRIGGERS from a Control-M job
    body_ref_paths: set[str] = set()  # dst of INVOKES from a captured script body
    ref_targets: dict[str, set[str]] = {}  # path → node_targets of referencing jobs
    for src, rel, dst in graph.rels:
        if rel not in ("INVOKES", "TRIGGERS"):
            continue
        src_node = graph.processes.get(src)
        dst_node = graph.processes.get(dst)
        if src_node is None or dst_node is None:
            continue
        norm = normalize_script_path(dst_node.path or "")
        if norm is None:
            continue
        if src_node.kind == _JOB_KIND:
            cmd_ref_paths.add(norm)
            if src_node.node_target:
                ref_targets.setdefault(norm, set()).add(src_node.node_target)
        elif src_node.kind in (RUA_SCRIPT_KIND, RUA_PROFILE_KIND):
            body_ref_paths.add(norm)

    # -- the candidates: rua-staged scripts and profiles ------------------------
    candidates: list[tuple[str, ProcessNode]] = []
    for nid in sorted(graph.processes):
        node = graph.processes[nid]
        if node.kind not in (RUA_SCRIPT_KIND, RUA_PROFILE_KIND):
            continue
        norm = normalize_script_path(node.path)
        if norm is None:
            continue  # counted at the G23 load; not re-counted here
        candidates.append((norm, node))
        if node.properties.get("rua_copy"):
            report.scripts_with_bodies += 1

    report.scripts_total = len(candidates)
    report.metadata_only = report.scripts_total > 0 and report.scripts_with_bodies == 0
    bodies = f"{report.scripts_with_bodies}/{report.scripts_total}"
    if report.metadata_only:
        report.coverage_statement = (
            f"body-copy coverage: {bodies} script(s) carried content — METADATA-ONLY RUN. "
            "Script-to-script calls are structurally invisible on this run, so "
            "'unreferenced' below means only 'no CMD_LINE reference'; it can NEVER "
            "establish that nothing calls a script. Deletion candidates from this run "
            "require corroboration from a body-carrying bundle first (gate "
            "rua-load-shapes §E3/§H2)."
        )
    else:
        report.coverage_statement = (
            f"body-copy coverage: {bodies} script(s) carried content. Callers are "
            "visible only within the carried bodies and the CMD_LINE feed; every "
            "'absent' below reads as 'not observed by that feed' (§H1 — no axis "
            "proves absence)."
        )

    # -- dispositions ----------------------------------------------------------
    for norm, node in candidates:
        records = _occurrence_records(node)
        server_records = [
            o for o in records if o.get("origin", "server-extract") == "server-extract"
        ]
        hosts = sorted({h for o in server_records for h in _host_spellings(o)})
        scopes = {o.get("storage_scope", "unknown") for o in server_records}
        row = {"path": norm, "hosts": hosts, "kind": node.kind}

        if norm in cmd_ref_paths:
            report.in_use += 1
            # §E1's stray-copy finding: a referenced script with a copy on a
            # host no referencing job targets. Emitted ONLY under local scope
            # (clause c); anything else is suppressed and counted.
            if len(hosts) > 1:
                targets = ref_targets.get(norm, set())
                stray = [
                    sorted(_host_spellings(o))
                    for o in server_records
                    if _host_spellings(o) and not (_host_spellings(o) & targets)
                ]
                if stray and scopes == {"local"}:
                    report.misdeployed.append(
                        {
                            **row,
                            "stray_hosts": [h for spellings in stray for h in spellings],
                            "referenced_node_targets": sorted(targets),
                            "reason": (
                                "referenced copies exist, but these hosts are targeted "
                                "by no referencing job — relocate, never delete (§E1). "
                                "node_target is polymorphic (host or host group) — "
                                "SME review required."
                            ),
                        }
                    )
                elif stray:
                    report.misdeployment_suppressed += 1
            continue

        if norm in body_ref_paths:
            report.dynamically_called.append({**row, "reason": _REASON_BODY_CALLED})
        else:
            reason = (
                _REASON_UNREFERENCED_NO_BODIES
                if report.metadata_only or not node.properties.get("rua_copy")
                else _REASON_UNREFERENCED
            )
            report.dead.append({**row, "reason": reason})

    # -- (d) archived state: G24's buckets, cross-referenced never recomputed ---
    if corroboration is not None:
        report.corroboration_run = True
        report.already_archived = [dict(r) for r in corroboration.repo_only]
        report.never_committed = len(corroboration.never_committed)

    return report
