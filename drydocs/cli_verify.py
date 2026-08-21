"""Graph-invariant verification: verify-reference (m1-verify) and verify-controlm (m3-verify).

S8 (2026-08-21): split out of drydocs/cli.py. The root stays the composition
root and the only module that may wire other components; this module holds
one domain's verbs and registers them on its own Typer, which the root merges
FLAT so `drydocs --help` lists the same names as before. Shared state
(console, registries, gates, adapters) lives in the root and is imported
from it; ``_client`` is resolved THROUGH the root at call time so tests that
monkeypatch ``drydocs.cli._client`` keep working.
"""

from __future__ import annotations

import typer
from rich.table import Table

from drydocs import cli as _root  # the composition root; call-time lookups only
from drydocs.cli import (
    console,
)
from drydocs_core.neo4j_client import Neo4jClient

app = typer.Typer()


def _client(database: str | None = None) -> Neo4jClient:
    """Resolved through the root at call time (tests patch drydocs.cli._client)."""
    return _root._client(database)


@app.command(name="verify-reference")
@app.command(
    name="m1-verify",
    deprecated=True,
    help="Deprecated alias of `verify-reference` (S8: milestone-named verbs retired; the old name keeps working).",
)
def m1_verify() -> None:
    """Assert M1 invariants on the populated graph."""
    with _client() as cli:
        # G33 §F1 (gate self-documentation-code-graph): :CodeModule and
        # :SoftwareProduct are two kinds of 'software' in one database and must
        # never co-label a node. Neo4j cannot declare label mutual-exclusion,
        # so the invariant lives here as a graph-test (0 also passes on a graph
        # with no code snapshot loaded — vacuously true, deliberately).
        colabeled = cli.run("""
            MATCH (n:CodeModule:SoftwareProduct)
            RETURN count(n) AS n
        """)
        # Scoped to SEAL-loaded apps (a.source = 'SEAL'): port data comes from the
        # SEAL extract only. Anchor apps MERGEd by attribution edges (e.g. the C9
        # pat mapping's seal_ids, a.source = 'pat') are legitimately port-less
        # until the SEAL extract covers them.
        rows = cli.run("""
            MATCH (a:BusinessApplication) WHERE a.source = 'SEAL'
            OPTIONAL MATCH (a)-[:HAS_PORT]->(ep:EventProcessing)
            OPTIONAL MATCH (a)-[:HAS_PORT]->(bp:BatchProcessing)
            RETURN count(a) AS apps, count(ep) AS ep, count(bp) AS bp
        """)
        # C9 (gate 2026-07-18): the home-product SUPPORTS edge is fallback-only.
        # An unsponsored DevTeam->Product edge beside an unsponsored
        # DevTeam->AreaProduct alignment restates the row join (C5 rule) — the
        # loader never writes it and the migration removed the pre-C9 ones.
        restate = cli.run("""
            MATCH (dt:DevTeam)-[r:SUPPORTS]->(:Product)
            WHERE coalesce(r.sponsored, false) = false
              AND EXISTS {
                MATCH (dt)-[r2:SUPPORTS]->(:AreaProduct)
                WHERE coalesce(r2.sponsored, false) = false
              }
            RETURN count(r) AS n
        """)
    r = rows[0] if rows else {"apps": 0, "ep": 0, "bp": 0}
    ok = r["apps"] == r["ep"] == r["bp"]
    console.print(f"apps have both ports: {'yes' if ok else 'NO'} (apps={r['apps']})")
    n_restate = restate[0]["n"] if restate else 0
    ok2 = n_restate == 0
    console.print(
        f"no join-restating DevTeam->Product SUPPORTS: {'yes' if ok2 else 'NO'} (found={n_restate})"
    )
    n_colabeled = colabeled[0]["n"] if colabeled else 0
    ok3 = n_colabeled == 0
    console.print(
        f"no :CodeModule+:SoftwareProduct co-labeling (G33 §F1): "
        f"{'yes' if ok3 else 'NO'} (found={n_colabeled})"
    )
    if not (ok and ok2 and ok3):
        raise typer.Exit(1)


# --- ontology supplements (G29: one data-driven chain) ------------------------


@app.command(name="verify-controlm")
@app.command(
    name="m3-verify",
    deprecated=True,
    help="Deprecated alias of `verify-controlm` (S8: milestone-named verbs retired; the old name keeps working).",
)
def m3_verify() -> None:
    """Assert M3 (part 1) invariants on the populated graph."""
    checks = []
    with _client() as cli:
        # Every folder has a server.
        rows = cli.run("""
            MATCH (f:ControlMFolder)
            OPTIONAL MATCH (f)-[:SCHEDULED_ON]->(srv:ControlMServer)
            WITH count(f) AS folders, count(srv) AS srv_links
            RETURN folders, srv_links
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "every folder has a server",
                    r["folders"] == r["srv_links"],
                    f"folders={r['folders']} srv_links={r['srv_links']}",
                )
            )

        # Every application grouping contains at least one folder (no orphan
        # :ControlMApplication nodes — they only exist via the header-row join).
        rows = cli.run("""
            MATCH (a:ControlMApplication)
            OPTIONAL MATCH (a)-[:CONTAINS_FOLDER]->(f:ControlMFolder)
            WITH count(DISTINCT a) AS apps, count(DISTINCT CASE WHEN f IS NOT NULL THEN a END) AS with_folder
            RETURN apps, with_folder
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "every ControlMApplication contains a folder",
                    r["apps"] == r["with_folder"],
                    f"apps={r['apps']} with_folder={r['with_folder']}",
                )
            )

        # C5 (gate 2026-07-18): no direct edge between the two row-derived
        # satellites of the folder header row. App and server both hang off the
        # folder (star-on-folder); "which servers run this app's work" is the
        # per-folder traversal CONTAINS_FOLDER + SCHEDULED_ON — a stored
        # shortcut would flatten a many-to-many that changes as folders
        # migrate, restating the row join with no provenance of its own.
        rows = cli.run("""
            MATCH (app:ControlMApplication)-[r]-(srv:ControlMServer)
            RETURN count(r) AS direct_edges
        """)
        if rows:
            checks.append(
                (
                    "no direct ControlMApplication<->ControlMServer edge",
                    rows[0]["direct_edges"] == 0,
                    f"direct_edges={rows[0]['direct_edges']}",
                )
            )

        # Every job has a folder.
        rows = cli.run("""
            MATCH (j:ControlMJob)
            OPTIONAL MATCH (f:ControlMFolder)-[:CONTAINS_JOB]->(j)
            WITH count(j) AS jobs, count(f) AS with_folder
            RETURN jobs, with_folder
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "every job has a folder",
                    r["jobs"] == r["with_folder"],
                    f"jobs={r['jobs']} with_folder={r['with_folder']}",
                )
            )

        # Composite key sanity — no duplicate (folder_id, job_id): the NODE KEY.
        # JOB_ID alone is folder-scoped in BMC (the same JOB_ID legitimately
        # appears in multiple folders, e.g. a DLY/CYC promoted pair) — grouping
        # without folder_id was a stale pre-composite-key check (caught by the
        # J9 e2e run against the bundled sample, which carries such a pair).
        rows = cli.run("""
            MATCH (j:ControlMJob)
            WITH j.folder_id AS fid, j.job_id AS jid, count(*) AS n
            WHERE n > 1
            RETURN count(*) AS dupes
        """)
        if rows:
            checks.append(
                (
                    "no duplicate (folder_id, job_id)",
                    rows[0]["dupes"] == 0,
                    f"dupes={rows[0]['dupes']}",
                )
            )

        # The "ControlM SchedulerKind seeded" check retired with the seeds
        # (C12 platforms-taxonomy gate 2026-07-21): fresh bootstraps no longer
        # create :SchedulerKind nodes, and old graphs that still hold them are
        # harmless. The orchestrator fact is verified via the software registry
        # (USES_SOFTWARE {source:'batch-port'} — loader migration C14).

        # ---- doc-06 Phase 3 invariants (M2, 2026-07-21) ------------------
        # Post-migration shape: no blanket provenance from pre-diet runs, the
        # raw-named folder audit props retired, and node pull-provenance uses
        # first_seen_at (created_at survives ONLY on the snapshot version
        # labels — the snapshot writer's own vocabulary).
        rows = cli.run("""
            MATCH (run:JobRun {kind:'load', status:'OK'})
            WHERE run.rows_changed IS NULL
            OPTIONAL MATCH ()-[r:WAS_GENERATED_BY]->(run)
            RETURN count(r) AS blanket
        """)
        if rows:
            checks.append(
                (
                    "no blanket WAS_GENERATED_BY from pre-diet runs",
                    rows[0]["blanket"] == 0,
                    f"blanket={rows[0]['blanket']} (pre-diet load detected — rebuild from bootstrap; the one-time 20260721 migration was removed 2026-07-23)",
                )
            )

        rows = cli.run("""
            MATCH (f:ControlMFolder)
            WHERE f.last_updated IS NOT NULL OR f.last_updated_user IS NOT NULL
            RETURN count(f) AS raw_props
        """)
        if rows:
            checks.append(
                (
                    "raw-named folder audit props retired",
                    rows[0]["raw_props"] == 0,
                    f"raw_props={rows[0]['raw_props']} (envelope pair is the record)",
                )
            )

        rows = cli.run("""
            MATCH (n)
            WHERE n.created_at IS NOT NULL
              AND NOT n:ApplicationSnapshot AND NOT n:ProductSnapshot
              AND NOT n:CatalogLOBSnapshot
            RETURN count(n) AS legacy_created_at
        """)
        if rows:
            checks.append(
                (
                    "loader nodes use first_seen_at (created_at renamed)",
                    rows[0]["legacy_created_at"] == 0,
                    f"legacy_created_at={rows[0]['legacy_created_at']}",
                )
            )

        # Local-namespace anchor terms present (post supplement).
        # Parentheses around the OR group — without them, AND binds tighter
        # and the IRI-prefix filter only constrains the ControlMFolder branch.
        rows = cli.run("""
            MATCH (n:OntologyTerm:LocalClass)
            WHERE n.iri STARTS WITH 'https://drydocs.local/ontology#'
              AND (n.iri ENDS WITH 'ControlMFolder'
                   OR n.iri ENDS WITH 'ControlMJob'
                   OR n.iri ENDS WITH 'ControlMServer')
            RETURN count(DISTINCT n) AS n
        """)
        if rows:
            checks.append(
                (
                    "M3 local anchor terms seeded",
                    rows[0]["n"] >= 3,
                    f"n={rows[0]['n']} (expect >= 3 after apply-ontology-supplement)",
                )
            )

        # Every active folder has at least one active job (sample-friendly bound).
        rows = cli.run("""
            MATCH (f:ControlMFolder {active: true})
            OPTIONAL MATCH (f)-[:CONTAINS_JOB]->(j:ControlMJob)
            WITH f, count(j) AS jc
            RETURN sum(CASE WHEN jc = 0 THEN 1 ELSE 0 END) AS empty_folders,
                   count(f) AS total
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "active folders contain at least one job",
                    r["empty_folders"] == 0,
                    f"empty={r['empty_folders']} total={r['total']}",
                )
            )

        # Every :Condition has at least one job referencing it (IN or OUT).
        # Orphans would mean a condition definition without a producer or
        # consumer — meaningless and almost certainly a load bug.
        rows = cli.run("""
            MATCH (c:Condition)
            OPTIONAL MATCH (c)<-[:REQUIRES_IN_CONDITION|EMITS_OUT_CONDITION]-(:ControlMJob)
            WITH c, count(*) AS refs
            RETURN sum(CASE WHEN refs = 0 THEN 1 ELSE 0 END) AS orphan,
                   count(c) AS total
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "no orphan conditions",
                    r["orphan"] == 0,
                    f"orphan={r['orphan']} total={r['total']}",
                )
            )

        # Every derived :WAS_INFORMED_BY edge must carry via_condition — the
        # linking condition is the edge's identity discriminator. The old
        # level/path checks went with the stored closure (phased-loader
        # change 2026-07-23: direct edges only; transitive reach is a
        # graph traversal).
        rows = cli.run("""
            MATCH ()-[r:WAS_INFORMED_BY]->()
            WHERE r.derived = true
            RETURN count(r) AS total,
                   sum(CASE WHEN r.via_condition IS NULL THEN 1 ELSE 0 END) AS missing_condition
        """)
        if rows:
            r = rows[0]
            checks.append(
                (
                    "WAS_INFORMED_BY edges carry via_condition",
                    r["missing_condition"] == 0,
                    f"total={r['total']} missing_condition={r['missing_condition']}",
                )
            )

        # CORPORATE BACKBONE — the §B2 agreement check (gate
        # corporate-backbone-vocabulary, SIGNED 19/19, 2026-08-17). NOT an M3
        # invariant: it rides here because m3-verify is the only graph-assertion
        # surface in the CLI and there is no m0/ontology equivalent. Naming
        # inboxed rather than silently widened.
        #
        # §B1 ruled TWO edge types over one date-discriminated type, so currency
        # is encoded TWICE — in the type NAME and in effective_to — and the two
        # can disagree. The SME ruled a GRAPH-TEST rather than a constraint on
        # the TOM-roles-singleton precedent: Neo4j cannot express "this type
        # implies this property is null". Harmless today because ontology.cypher
        # is the only writer and it writes both correctly; this exists for the
        # first loader that writes these edges.
        # COUNT{} subqueries, NOT chained MATCHes. The first draft of this check
        # was `MATCH ... WITH count(r) ... MATCH ... RETURN` and returned NO ROWS
        # on a clean graph, because a second MATCH that finds nothing eliminates
        # the row — so `if rows:` skipped the check entirely and m3-verify
        # reported a silent pass. Caught by running it live (laptop, neo4jtest,
        # drydocs DB) rather than by reading it. A check that vanishes precisely
        # when there is nothing to report is indistinguishable from one that
        # vanishes when there is.
        rows = cli.run("""
            RETURN
              COUNT {
                MATCH (:Company)-[r:HAS_BUSINESS_SEGMENT]->(:BusinessSegment)
                WHERE r.effective_to IS NOT NULL
              } AS current_but_dated,
              COUNT {
                MATCH (:Company)-[h:HAS_BUSINESS_SEGMENT_HISTORICAL]->(:BusinessSegment)
                WHERE h.effective_to IS NULL
              } AS historical_but_open
        """)
        if rows:
            r = rows[0]
            disagreements = r["current_but_dated"] + r["historical_but_open"]
            checks.append(
                (
                    "segment edge type agrees with effective_to",
                    disagreements == 0,
                    f"current_but_dated={r['current_but_dated']} "
                    f"historical_but_open={r['historical_but_open']}",
                )
            )

    t = Table(title="M3 (part 1 + part 2) invariants")
    t.add_column("Check")
    t.add_column("OK", justify="center")
    t.add_column("Detail")
    failed = 0
    for name, ok, detail in checks:
        t.add_row(name, "yes" if ok else "NO", detail)
        if not ok:
            failed += 1
    console.print(t)
    if failed:
        console.print(f"[red]{failed} invariant(s) failed.[/]")
        raise typer.Exit(1)
    console.print("[green]All M3 (part 1) invariants passed.[/]")
