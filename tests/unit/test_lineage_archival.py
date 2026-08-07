"""G58 — the dead-script archival report, one test per acceptance clause.

The gate context (rua-load-shapes, SIGNED OFF 2026-08-07): the report drives
DELETION, so a false positive removes live code — §E3's flagged-never-
auto-judged and §H1's no-axis-proves-absence are ACCEPTANCE clauses here, not
style. Fixtures are hand-staged LineageGraphs (the same candidate shapes the
G20/G21 extractors produce), synthetic values throughout.
"""

from __future__ import annotations

from drydocs_lineage.archival import ArchivalReport, archival_report
from drydocs_lineage.extractors.code_repo import CorroborationReport
from drydocs_lineage.model import LineageGraph, ProcessNode, process_id
from drydocs_lineage.review import to_html

FQDN1 = "vsi-synth-01.example.internal"
FQDN2 = "vsi-synth-02.example.internal"


def _script(
    graph: LineageGraph,
    path: str,
    *,
    hosts: tuple[tuple[str, str], ...] = (("vsi-synth-01", FQDN1),),
    storage_scope: str | None = None,
    body: bool = True,
) -> str:
    """Stage a rua_script with one §D2 occurrence record per host."""
    pid = process_id("rua_script", path)
    props = {"origin": "server-extract"}
    if body:
        props["rua_copy"] = f"scripts{path}"
    node = ProcessNode(
        node_id=pid,
        kind="rua_script",
        name=path.rsplit("/", 1)[-1],
        path=path,
        properties=props,
    )
    for host, fqdn in hosts:
        occ = {"origin": "server-extract", "path": path, "rua_host": host, "rua_fqdn": fqdn}
        if storage_scope:
            occ["storage_scope"] = storage_scope
        node.occurrences.append(occ)
    graph.add_process(node)
    return pid


def _job(graph: LineageGraph, key: str, *, node_target: str = "") -> str:
    jid = process_id("controlm_job", key)
    graph.add_process(
        ProcessNode(node_id=jid, kind="controlm_job", name=f"JOB_{key}", node_target=node_target)
    )
    return jid


def _cmd_target(graph: LineageGraph, path: str) -> str:
    """The CMD_LINE feed's own staged target node (a different id namespace
    than rua_script — the report joins the two on the §D1 normalized path)."""
    cid = process_id("shell_script", path)
    graph.add_process(
        ProcessNode(node_id=cid, kind="shell_script", name=path.rsplit("/", 1)[-1], path=path)
    )
    return cid


# --- (a) coverage stated on the report itself -----------------------------------------


def test_metadata_only_run_states_its_own_coverage() -> None:
    """A body-less fixture carries the coverage statement in its own output,
    and its unreferenced rows read 'no CMD_LINE reference' — never a claim
    that nothing calls the script."""
    g = LineageGraph()
    _script(g, "/opt/app/orphan.ksh", body=False)
    report = archival_report(g)

    assert report.metadata_only is True
    assert report.scripts_with_bodies == 0
    assert "METADATA-ONLY RUN" in report.coverage_statement
    assert "no CMD_LINE reference" in report.coverage_statement

    assert len(report.dead) == 1
    reason = report.dead[0]["reason"]
    assert "no CMD_LINE reference" in reason
    assert "nothing calls" not in reason  # the forbidden overclaim
    assert "invisible" in reason  # the blind spot is named, not implied away


def test_body_carrying_run_still_reads_as_not_observed() -> None:
    """§H1 even with bodies: 'absent' means 'not observed by that feed'."""
    g = LineageGraph()
    _script(g, "/opt/app/orphan.ksh", body=True)
    report = archival_report(g)
    assert report.metadata_only is False
    assert "not observed" in report.coverage_statement
    assert "no CMD_LINE reference" in report.dead[0]["reason"]
    assert "nothing calls" not in report.dead[0]["reason"]


# --- (b) three dispositions, distinct, nothing silently absent ------------------------


def test_three_dispositions_are_distinct_and_complete() -> None:
    g = LineageGraph()
    # in use: a job CMD_LINE invokes it (via the cmdline feed's own node)
    used = "/opt/app/used.ksh"
    _script(g, used)
    jid = _job(g, "161015.22", node_target=FQDN1)
    g.add_rel(jid, "INVOKES", _cmd_target(g, used))
    # dynamically called: no CMD_LINE ref, but a captured body invokes it
    dyn = "/opt/app/helper.ksh"
    _script(g, dyn)
    caller = _script(g, "/opt/app/caller.ksh")
    g.add_rel(jid, "INVOKES", _cmd_target(g, "/opt/app/caller.ksh"))
    g.add_rel(caller, "INVOKES", _cmd_target(g, dyn))
    # genuinely dead: present, referenced by nothing observed
    dead = "/opt/app/dead.ksh"
    _script(g, dead)
    # misdeployed: referenced on host 1, stray copy on host 2, scope LOCAL
    mis = "/opt/app/mis.ksh"
    _script(g, mis, hosts=(("vsi-synth-01", FQDN1), ("vsi-synth-02", FQDN2)), storage_scope="local")
    g.add_rel(jid, "INVOKES", _cmd_target(g, mis))

    report = archival_report(g)

    dead_paths = {r["path"] for r in report.dead}
    dyn_paths = {r["path"] for r in report.dynamically_called}
    mis_paths = {r["path"] for r in report.misdeployed}
    assert dead_paths == {dead}
    assert dyn_paths == {dyn}
    assert mis_paths == {mis}
    # distinct buckets — no overlap
    assert not (dead_paths & dyn_paths) and not (dead_paths & mis_paths)
    # nothing silently absent: every unreferenced candidate is in a bucket,
    # every referenced one is counted in_use ("caller" and "used" and "mis")
    assert report.in_use == 3
    assert report.scripts_total == 5


def test_dynamically_called_rows_say_keep() -> None:
    g = LineageGraph()
    dyn = "/opt/app/helper.ksh"
    _script(g, dyn)
    caller = _script(g, "/opt/app/caller.ksh")
    jid = _job(g, "161015.22")
    g.add_rel(jid, "INVOKES", _cmd_target(g, "/opt/app/caller.ksh"))
    g.add_rel(caller, "INVOKES", _cmd_target(g, dyn))
    report = archival_report(g)
    assert [r["path"] for r in report.dynamically_called] == [dyn]
    assert "keep" in report.dynamically_called[0]["reason"]


# --- (c) the misdeployment scope gate -------------------------------------------------


def test_misdeployment_emitted_only_under_local_scope() -> None:
    def build(scope: str | None) -> ArchivalReport:
        g = LineageGraph()
        mis = "/opt/app/mis.ksh"
        _script(
            g,
            mis,
            hosts=(("vsi-synth-01", FQDN1), ("vsi-synth-02", FQDN2)),
            storage_scope=scope,
        )
        jid = _job(g, "161015.22", node_target=FQDN1)
        g.add_rel(jid, "INVOKES", _cmd_target(g, mis))
        return archival_report(g)

    local = build("local")
    assert len(local.misdeployed) == 1
    assert local.misdeployment_suppressed == 0
    assert FQDN2 in local.misdeployed[0]["stray_hosts"]
    assert "never delete" in local.misdeployed[0]["reason"]

    # unknown scope (every bundle until G56): suppressed AND counted
    unknown = build(None)
    assert unknown.misdeployed == []
    assert unknown.misdeployment_suppressed == 1

    shared = build("shared")
    assert shared.misdeployed == []
    assert shared.misdeployment_suppressed == 1


# --- (d) already-archived is cross-referenced, never recomputed -----------------------


def test_archived_state_cross_references_the_g24_buckets() -> None:
    g = LineageGraph()
    _script(g, "/opt/app/live.ksh")
    corr = CorroborationReport(
        repo_only=[{"repo": "synth-repo", "repo_path": "app/retired.ksh"}],
        never_committed=[
            {"server_path": "/opt/app/live.ksh", "blob_sha": "x", "path_tail_hints": []}
        ],
    )
    report = archival_report(g, corroboration=corr)
    assert report.corroboration_run is True
    assert report.already_archived == [{"repo": "synth-repo", "repo_path": "app/retired.ksh"}]
    assert report.never_committed == 1
    assert "already_archived=1" in report.summary()


def test_without_corroboration_archived_state_is_not_observed() -> None:
    report = archival_report(LineageGraph())
    assert report.corroboration_run is False
    assert report.never_committed is None
    assert "not observed" in report.summary()


# --- (e) no axis proves absence: the registry unknowns ride along ---------------------


def test_active_unknown_appears_rather_than_being_dropped() -> None:
    g = LineageGraph()
    _script(g, "/opt/app/x.ksh")
    with_registry = archival_report(g, active_unknown=2)
    assert with_registry.active_unknown == 2
    assert "active_unknown=2" in with_registry.summary()

    without = archival_report(g)
    assert without.active_unknown is None
    assert "registry axis not observed" in without.summary()


# --- the review surface ----------------------------------------------------------------


def test_review_page_renders_the_archival_section() -> None:
    g = LineageGraph()
    _script(g, "/opt/app/dead.ksh", body=False)
    report = archival_report(g)
    page = to_html(g, generated_at="2026-08-07 00:00 UTC", archival=report)
    assert "Dead-script archival report" in page
    assert "METADATA-ONLY RUN" in page
    assert "misdeployment checks suppressed" in page
    assert "/opt/app/dead.ksh" in page
    # without a report the section stays out — the page is unchanged material
    assert "Dead-script archival report" not in to_html(g, generated_at="2026-08-07 00:00 UTC")
