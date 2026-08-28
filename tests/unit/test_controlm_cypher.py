"""Static checks on the M3 Control-M Cypher templates and SQL projections."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from drydocs_core.cypher_split import strip_comments

ROOT = Path(__file__).resolve().parent.parent.parent
CYPHER_DIR = ROOT / "drydocs" / "loaders" / "cypher"
SQL_DIR = ROOT / "drydocs" / "loaders" / "sql"
SCHEMA_DIR = ROOT / "drydocs_core" / "schema"


def _cypher_code(name: str) -> str:
    """A template's CODE — ``//`` and ``/* */`` comments stripped (J26).

    Negative assertions read this, never raw text: a raw-text ban forbids the
    file from DESCRIBING the very thing it deliberately omits, and this repo's
    doctrine is that the reasoning is the audit trail. Positive presence pins
    may keep reading raw text — a comment can only false-pass those.
    """
    return strip_comments((CYPHER_DIR / name).read_text(encoding="utf-8"))


def _sql_code(name: str) -> str:
    """SQL with ``--`` line-comment tails dropped (the same J26 rule)."""
    text = (SQL_DIR / name).read_text(encoding="utf-8")
    return "\n".join(line.split("--")[0] for line in text.splitlines())


ALL_CYPHERS = [
    "controlm_folders.cypher",
    "controlm_jobs.cypher",
    "controlm_conditions_in.cypher",
    "controlm_conditions_out.cypher",
    "controlm_dependencies_derived.cypher",
    "controlm_hosts.cypher",
]

ALL_SQL = [
    "controlm_folders.sql",
    "controlm_jobs.sql",
    "controlm_conditions_in.sql",
    "controlm_conditions_out.sql",
    "controlm_dependencies_recursive.sql",
    "controlm_hosts.sql",
]


# ---- Cypher --------------------------------------------------------------


@pytest.mark.parametrize("name", ALL_CYPHERS)
def test_cypher_exists(name: str) -> None:
    assert (CYPHER_DIR / name).exists()


@pytest.mark.parametrize("name", ALL_CYPHERS)
def test_cypher_uses_unwind_batch(name: str) -> None:
    text = (CYPHER_DIR / name).read_text(encoding="utf-8")
    assert "UNWIND $batch AS row" in text


@pytest.mark.parametrize("name", ALL_CYPHERS)
def test_cypher_idempotent_merge(name: str) -> None:
    text = (CYPHER_DIR / name).read_text(encoding="utf-8")
    body = "\n".join(
        line for line in text.splitlines() if line.strip() and not line.strip().startswith("//")
    )
    assert "MERGE" in body
    assert not re.findall(r"^\s*CREATE\s+\(", body, re.MULTILINE)


def test_folders_uses_sched_table_not_parent_table() -> None:
    text = _cypher_code("controlm_folders.cypher")
    assert "row.sched_table" in text
    # NO parent_table on the folder loader (that lives on the job side).
    assert "row.parent_table" not in text


def test_folders_creates_application_grouping() -> None:
    """The folder pass derives BOTH grouping labels (load-order definition,
    2026-07-07): DATA_CENTER -> :ControlMServer and the header-row APPLICATION
    -> :ControlMApplication with CONTAINS_FOLDER (gate controlm-q1q3-phase1)."""
    text = (CYPHER_DIR / "controlm_folders.cypher").read_text(encoding="utf-8")
    assert "MERGE (srv:ControlMServer:Platform {name: row.data_center})" in text
    assert "MERGE (app:ControlMApplication:Collection {name: row.application})" in text
    assert "CONTAINS_FOLDER" in text
    # Null guard: folders without a header row must not merge a null-keyed app.
    assert "row.application IS NOT NULL" in text


def test_folder_sql_joins_header_row_for_application() -> None:
    """APPLICATION comes from the folder header row (JOB_ID=1, SMART Table) —
    CM_DEF_VTAB has no APPLICATION column. LEFT JOIN so header-less folders load."""
    text = (SQL_DIR / "controlm_folders.sql").read_text(encoding="utf-8")
    # J39 (2026-08-26): alias H -> J, back-flowed from the company copy so the two
    # sides stop carrying a permanent cosmetic diff. The guard pins the JOIN, and
    # the alias letter only because the assertions must name it.
    assert "LEFT JOIN psgmgr.CM_DEF_VJOB J" in text
    assert "J.JOB_ID   = 1" in text or "J.JOB_ID = 1" in text
    assert "J.APPLICATION" in text
    assert "J.IS_CURRENT_VERSION = 'Y'" in text  # string literal, VARCHAR2(1); domain 'Y' (D4)


def test_ingest_chain_order_is_enforced() -> None:
    """The ingest-controlm chain order (nodes before relationships; both
    folder-pass grouping labels before jobs; dependencies in a separate pass):
    folders -> jobs -> conditions in/out -> derived dependencies.

    Since N3 the stages are module-level declarations the command body
    consumes (cli.CONTROLM_*_STAGES), so order is asserted on the
    declarations themselves rather than scanned out of the function text.
    """
    from drydocs import cli as drydocs_cli

    chain = [
        stage[0]
        for stage in (
            drydocs_cli.CONTROLM_NODE_STAGES
            + drydocs_cli.CONTROLM_PART2_STAGES
            + drydocs_cli.CONTROLM_REL_STAGES
        )
    ]
    assert chain == [
        "controlm_folders",
        "controlm_jobs",
        "controlm_conditions_in",
        "controlm_conditions_out",
        "controlm_hosts",
        "controlm_dependencies_derived",
    ], "ingest-controlm stage order drifted"
    # The dependency pass must be alone in the deferred relationships phase
    # (two-phase contract: cross-folder WAS_INFORMED_BY needs all nodes first).
    assert [s[0] for s in drydocs_cli.CONTROLM_REL_STAGES] == ["controlm_dependencies_derived"]
    # The derived RUNS_ON resolution pass runs after ALL staged loads —
    # it reads the graph, not staging, so it sits after the stage loop.
    # S8: ingest-controlm lives in the ingest command module, not the root
    cli_src = (ROOT / "drydocs" / "cli_ingest.py").read_text(encoding="utf-8")
    ingest = cli_src[cli_src.index("def ingest_controlm") :]
    assert ingest.index("runs_on_resolution") > ingest.index("for stage_name, cls,")


def test_constraints_cover_folder_pass_labels() -> None:
    """Constraints exist BEFORE import for every MERGE key the folder pass
    touches (import pre-flight rule: constraints back MERGE lookups)."""
    text = (SCHEMA_DIR / "constraints.cypher").read_text(encoding="utf-8")
    assert "controlm_server" in text
    assert "controlmfolder_id" in text
    assert "controlmapplication_name" in text


def test_jobs_keeps_parent_table_property() -> None:
    text = (CYPHER_DIR / "controlm_jobs.cypher").read_text(encoding="utf-8")
    assert "row.parent_table" in text
    assert "row.application" in text  # Control-M app code (NOT seal_id)
    assert "row.cmd_line" in text


def test_jobs_node_key_is_folder_id_job_id_only() -> None:
    """NODE KEY is (folder_id, job_id). version_serial is a property."""
    text = (CYPHER_DIR / "controlm_jobs.cypher").read_text(encoding="utf-8")
    # MERGE pattern: both folder_id and job_id in the key block
    merge_block_pattern = re.compile(
        r"MERGE\s*\(j:ControlMJob:Activity\s*\{[^}]*\}",
        re.MULTILINE | re.DOTALL,
    )
    m = merge_block_pattern.search(text)
    assert m, "ControlMJob MERGE block not found"
    merge_keys = m.group(0)
    assert "folder_id: row.folder_id" in merge_keys
    assert "job_id: row.job_id" in merge_keys
    # version_serial should NOT be in the MERGE key block
    assert "version_serial:" not in merge_keys
    # but should still be SET as a property elsewhere
    assert "j.version_serial" in text


def test_conditions_match_jobs_on_folder_id_job_id() -> None:
    """Conditions MATCH :ControlMJob on (folder_id, job_id) only."""
    for name in ("controlm_conditions_in.cypher", "controlm_conditions_out.cypher"):
        text = (CYPHER_DIR / name).read_text(encoding="utf-8")
        match_block_pattern = re.compile(
            r"MATCH\s*\(j:ControlMJob\s*\{[^}]*\}",
            re.MULTILINE | re.DOTALL,
        )
        m = match_block_pattern.search(text)
        assert m, f"{name} ControlMJob MATCH not found"
        match_keys = m.group(0)
        assert "folder_id: row.folder_id" in match_keys
        assert "job_id: row.job_id" in match_keys
        # version_serial must NOT be in the MATCH key block
        assert "version_serial:" not in match_keys, f"{name} should not key on version_serial"


def test_conditions_node_key_is_folder_id_name_only() -> None:
    """:Condition NODE KEY is (folder_id, name). version_serial is a property."""
    for name in ("controlm_conditions_in.cypher", "controlm_conditions_out.cypher"):
        text = (CYPHER_DIR / name).read_text(encoding="utf-8")
        merge_block_pattern = re.compile(
            r"MERGE\s*\(c:Condition:Entity\s*\{[^}]*\}",
            re.MULTILINE | re.DOTALL,
        )
        m = merge_block_pattern.search(text)
        assert m, f"{name} :Condition MERGE block not found"
        merge_keys = m.group(0)
        assert "folder_id: row.folder_id" in merge_keys
        assert "name: row.condition_name" in merge_keys
        assert "version_serial:" not in merge_keys
        # But the property should be SET elsewhere.
        assert "c.version_serial" in text


def test_dependencies_match_on_the_composite_node_key() -> None:
    """Endpoints resolve by splitting the ctlm_id composite on '.' — the
    (folder_id, job_id) NODE KEY in composite form (P2 gate §B; phased
    loader, ported 2026-07-23)."""
    text = (CYPHER_DIR / "controlm_dependencies_derived.cypher").read_text(encoding="utf-8")
    assert "split(row.in_table_job_id, '.')[0]" in text
    assert "split(row.in_table_job_id, '.')[1]" in text
    assert "split(row.out_table_job_id, '.')[0]" in text
    assert "split(row.out_table_job_id, '.')[1]" in text


def test_conditions_in_carries_boolean_expr_props() -> None:
    text = _cypher_code("controlm_conditions_in.cypher")
    for fragment in ["and_or", "parentheses", "order_"]:
        assert fragment in text, f"in.cypher missing {fragment}"
    # No SIGN on the IN side.
    assert "row.sign" not in text


def test_conditions_out_carries_sign() -> None:
    text = _cypher_code("controlm_conditions_out.cypher")
    assert "row.sign" in text
    assert "and_or" not in text


def test_conditions_share_composite_key() -> None:
    """Both IN and OUT loaders key :Condition the same way so the same node
    is shared when (folder_id, name) matches. version_serial was dropped
    from the key in the constraints correction (condition_key is now
    (folder_id, name) only — see constraints.cypher)."""
    for name in ("controlm_conditions_in.cypher", "controlm_conditions_out.cypher"):
        text = (CYPHER_DIR / name).read_text(encoding="utf-8")
        assert "folder_id: row.folder_id" in text
        assert "name: row.condition_name" in text


# ---- host topology (P3; gate controlm-hosts-topology 2026-07-09) ----------


def test_hosts_cypher_merges_the_gated_topology() -> None:
    """The hosts pass MERGEs exactly the three gated elements — group (keyed
    per DC), member host (keyed on nodeid alone), CONTAINS_HOST — and does
    NOT write DEFINED_ON (blocked on the DC value-domain probe + scope call)
    or RUNS_ON (the separate derived pass)."""
    text = (CYPHER_DIR / "controlm_hosts.cypher").read_text(encoding="utf-8")
    assert (
        "MERGE (g:ControlMHostGroup:Collection "
        "{data_center: row.data_center, name: row.grpname})" in text
    )
    assert "MERGE (h:ExecutionHost:Agent {nodeid: row.nodeid})" in text
    assert "CONTAINS_HOST" in text
    assert "m.participation_type = row.participation_type" in text
    assert "last_capture_date" in text
    body = "\n".join(
        line for line in text.splitlines() if line.strip() and not line.strip().startswith("//")
    )
    assert "DEFINED_ON" not in body
    assert "RUNS_ON" not in body


def test_runs_on_resolution_implements_group_wins() -> None:
    """The derived pass writes both roles, guards the 1-hop case on the
    ABSENCE of a same-named group (the signed §B group-wins precedence),
    marks edges derived, and MERGEs edges only — endpoints are MATCHed,
    never created (the WAS_INFORMED_BY derived-pass contract)."""
    text = (CYPHER_DIR / "runs_on_resolution.cypher").read_text(encoding="utf-8")
    assert "MERGE (j)-[r:RUNS_ON {role: 'host_group'}]->(g)" in text
    assert "MERGE (j)-[r:RUNS_ON {role: 'agent_host'}]->(h)" in text
    # the group-absence guard excludes the :SchemaMeta exemplar (O33): the
    # exemplar carries name='ControlMHostGroup', so an unguarded EXISTS would
    # treat the label string as a real group name
    assert (
        "NOT EXISTS { MATCH (g:ControlMHostGroup {name: j.node_id}) "
        "WHERE NOT g:SchemaMeta }" in text
    )
    # the guard must precede the agent_host MERGE (it scopes that statement)
    assert "NOT EXISTS" in text[: text.index("role: 'agent_host'")]
    assert "r.derived" in text
    assert "j.node_id IS NOT NULL AND j.node_id <> ''" in text
    # edges only: no node-creating MERGE (label after the opening paren)
    assert not re.findall(
        r"MERGE\s*\(\w+:\w+", text
    ), "resolution pass must MATCH endpoints, never MERGE them"


def test_constraints_cover_host_topology_labels() -> None:
    text = (SCHEMA_DIR / "constraints.cypher").read_text(encoding="utf-8")
    assert "controlmhostgroup_key" in text
    assert "executionhost_nodeid" in text


def test_hosts_sql_uses_its_own_scope_binds() -> None:
    """CM_HOSTS has no folder/owner/author grain — the extract binds
    :grpname_filter and :row_cap only, and the CLI binds grpname_filter NULL
    (see ingest_controlm's stage_scope special case)."""
    text = (SQL_DIR / "controlm_hosts.sql").read_text(encoding="utf-8")
    code = "\n".join(line for line in text.splitlines() if not line.strip().startswith("--"))
    assert ":grpname_filter" in code
    assert ":row_cap" in code
    # the folder-grained quartet does not apply at this grain (header comment
    # explains why — only code lines count here)
    assert ":folder_filter" not in code
    cli_src = (ROOT / "drydocs" / "cli_ingest.py").read_text(encoding="utf-8")  # S8
    assert '"grpname_filter": None' in cli_src


# ---- provenance-edge diet (doc 06 Phase 2, SME sign-off 2026-07-06) ------

PROVENANCE_GUARDED_CYPHERS = [
    "controlm_folders.cypher",
    "controlm_jobs.cypher",
    "controlm_conditions_in.cypher",
    "controlm_conditions_out.cypher",
]


@pytest.mark.parametrize("name", PROVENANCE_GUARDED_CYPHERS)
def test_was_generated_by_is_checksum_guarded(name: str) -> None:
    """WAS_GENERATED_BY may only be written inside a FOREACH-over-CASE guard
    keyed on a stored-vs-incoming row_checksum comparison — never
    unconditionally, which is what made :JobRun a supernode on every full
    refresh (persona review Issue 3)."""
    text = (CYPHER_DIR / name).read_text(encoding="utf-8")
    assert "row_checksum IS NULL OR" in text
    assert "<> row.row_checksum) AS row_changed" in text
    assert "FOREACH (_ IN CASE WHEN row_changed THEN [1] ELSE [] END |" in text

    foreach_start = text.index("FOREACH (_ IN CASE WHEN row_changed")
    close_match = re.search(r"^\)\s*$", text[foreach_start:], re.MULTILINE)
    assert close_match, f"{name}: FOREACH block has no standalone closing paren"
    foreach_end = foreach_start + close_match.end()

    # Exactly one WAS_GENERATED_BY MERGE (comments may still name the label
    # in prose; only count non-comment code lines), and it must live INSIDE
    # the FOREACH body (i.e. conditionally), not before/after it.
    code_lines = [
        line for line in text.splitlines() if line.strip() and not line.strip().startswith("//")
    ]
    code = "\n".join(code_lines)
    assert code.count("WAS_GENERATED_BY") == 1
    assert "WAS_GENERATED_BY" in text[foreach_start:foreach_end]


@pytest.mark.parametrize("name", PROVENANCE_GUARDED_CYPHERS)
def test_row_checksum_is_persisted_on_the_node(name: str) -> None:
    """Every guarded loader SETs n.row_checksum = row.row_checksum after the
    FOREACH so the next run's comparison is against this run's content."""
    text = (CYPHER_DIR / name).read_text(encoding="utf-8")
    assert re.search(
        r"SET \w\.row_checksum = row\.row_checksum", text
    ), f"{name}: missing row_checksum SET"


def test_folders_application_block_survives_the_provenance_guard() -> None:
    """The deliberate tail order in controlm_folders.cypher (provenance BEFORE
    the WHERE-guarded ControlMApplication block, because that WHERE drops
    header-less rows for the remainder of the statement) must be preserved:
    the app/CONTAINS_FOLDER block still executes for rows with an
    application value, after the checksum-guarded provenance section."""
    text = (CYPHER_DIR / "controlm_folders.cypher").read_text(encoding="utf-8")
    provenance_idx = text.index("AS row_changed")
    application_idx = text.index("MERGE (app:ControlMApplication:Collection", provenance_idx)
    where_idx = text.index("WHERE row.application IS NOT NULL", provenance_idx)
    contains_folder_idx = text.index("CONTAINS_FOLDER", application_idx)
    assert provenance_idx < where_idx < application_idx < contains_folder_idx


def test_dependencies_derived_has_no_was_generated_by() -> None:
    """controlm_dependencies_derived.cypher only MERGEs an edge between two
    already-loaded jobs — it creates no new node, so it never had (and still
    has no) a WAS_GENERATED_BY tail. Confirms this loader is out of scope for
    the checksum guard."""
    text = _cypher_code("controlm_dependencies_derived.cypher")
    assert "WAS_GENERATED_BY" not in text


def test_dependencies_materializes_derived_edge() -> None:
    text = _cypher_code("controlm_dependencies_derived.cypher")
    # the derived predecessor edge is :WAS_INFORMED_BY (PROV-O wasInformedBy),
    # not the earlier :DEPENDS_ON working name
    assert ":WAS_INFORMED_BY" in text
    assert "derived" in text
    assert "via_condition" in text
    # the stored-closure properties went with the recursive CTE (phased
    # loader, ported 2026-07-23) — transitive reach is a graph traversal
    assert "recursion_level" not in text
    assert "dependency_path" not in text


# ---- SQL projections ------------------------------------------------------


@pytest.mark.parametrize("name", ALL_SQL)
def test_sql_exists(name: str) -> None:
    assert (SQL_DIR / name).exists()


@pytest.mark.parametrize("name", ALL_SQL)
def test_sql_references_psgmgr(name: str) -> None:
    text = (SQL_DIR / name).read_text(encoding="utf-8")
    assert "psgmgr." in text


def test_folder_sql_uses_sched_table() -> None:
    text = _sql_code("controlm_folders.sql")
    assert "T.SCHED_TABLE" in text
    # Confirm NO is_current_version filter on the folder side (that column
    # doesn't exist on CM_DEF_VTAB).
    assert "T.IS_CURRENT_VERSION" not in text


def test_jobs_sql_projects_the_audit_envelope() -> None:
    """Doc 06 Phase 1: the envelope columns are PROJECTED, not filter-only
    (gate controlm-q1q3-phase1; mapping in config/audit-fields.yaml)."""
    text = (SQL_DIR / "controlm_jobs.sql").read_text(encoding="utf-8")
    for col in ("J.CREATION_USER", "J.CREATION_DATE", "J.CHANGE_USERID", "J.CHANGE_DATE"):
        assert f"{col} " in text or f"{col}\t" in text.replace(
            "  ", " "
        ), f"missing projection {col}"
    assert "AS creation_user" in text
    assert "AS change_date" in text


def test_jobs_sql_filters_current_version_as_string() -> None:
    text = (SQL_DIR / "controlm_jobs.sql").read_text(encoding="utf-8")
    # IS_CURRENT_VERSION is VARCHAR2(1); literal must be a string.
    assert "J.IS_CURRENT_VERSION = 'Y'" in text


def test_dependencies_sql_is_direct_only() -> None:
    """Phased-loader change (ported 2026-07-23): the SQL emits DIRECT
    predecessor pairs only — no recursive CTE, no stored closure, no cycle
    guard needed (nothing recurses). Transitive reach is a Neo4j traversal."""
    text = _sql_code("controlm_dependencies_recursive.sql")
    assert "RecursiveJobDependencies" not in text
    assert "UNION ALL" not in text
    for alias in ("AS in_table_job_id", "AS out_condition", "AS out_table_job_id"):
        assert alias in text, f"missing projection {alias}"


def test_recursive_sql_cyclic_type_disabled() -> None:
    """The canonical version intentionally disables CYCLIC_TYPE matching."""
    text = (SQL_DIR / "controlm_dependencies_recursive.sql").read_text(encoding="utf-8")
    # The disabling marker appears at the cyclic-type comparison sites.
    assert "intentionally disabled" in text


# ---- Ontology supplement -------------------------------------------------


def test_m3_supplement_wires_to_prov_anchors() -> None:
    # m3_ontology_supplement.cypher was renamed to ontology_supplement.cypher
    # in the schema consolidation (bootstrap step 3).
    text = (SCHEMA_DIR / "ontology_supplement.cypher").read_text(encoding="utf-8")
    assert "SUBCLASS_OF" in text
    assert "http://www.w3.org/ns/prov#Collection" in text
    assert "http://www.w3.org/ns/prov#Activity" in text


def test_run_as_bind_is_upper_cased_but_the_column_is_not() -> None:
    """psgmgr stores CM_DEF_VJOB.OWNER all-upper (SME 2026-08-12) and the SQL
    binds `J.OWNER = :run_as` as an exact match, so a lower-case --run-as
    silently matched nothing. The BIND VALUE is normalized; the COLUMN must stay
    bare so the predicate keeps using its index on a ~240k-row table."""
    from drydocs.cli import _scope_binds

    assert _scope_binds(run_as="a_lower_case_acct")["run_as"] == "A_LOWER_CASE_ACCT"
    assert _scope_binds(run_as="ALREADY_UPPER")["run_as"] == "ALREADY_UPPER"
    # None must survive as None — it means "no filter on this dimension", and
    # "".upper() would turn a missing filter into an empty-string match.
    assert _scope_binds(run_as=None)["run_as"] is None

    for sql_name in ("controlm_jobs.sql", "controlm_dependencies_recursive.sql"):
        code = "\n".join(
            line
            for line in (SQL_DIR / sql_name).read_text(encoding="utf-8").splitlines()
            if not line.strip().startswith("--")
        )
        assert ":run_as" in code, sql_name
        assert "UPPER(J.OWNER" not in code.upper().replace(" ", ""), (
            f"{sql_name}: the OWNER column must not be wrapped in UPPER() — it is "
            "already upper at rest, so the function is a no-op that costs the index"
        )


# ---- G115: the data-center scope bind ------------------------------------

#: The extract family the data-center bind joins (G115 clause a). Conditions
#: and the dependency anchor are deliberately not in this list — the item
#: scoped the bind to the five extracts named here.
DC_BOUND_SQL = [
    "controlm_folders.sql",
    "controlm_jobs.sql",
    "controlm_variables.sql",
    "controlm_hosts.sql",
    "controlm_avg_run.sql",
]


@pytest.mark.parametrize("name", DC_BOUND_SQL)
def test_data_center_bind_joins_the_extract_family(name: str) -> None:
    """Every extract in the family carries the optional :data_center_filter
    bind (G115), NULL-guarded exactly like the other scope binds so an absent
    value means all data centers. Code lines only — a header comment naming
    the bind must not false-pass this."""
    code = _sql_code(name)
    assert ":data_center_filter" in code, f"{name}: missing the data-center bind"
    assert re.search(
        r":data_center_filter\s+IS\s+NULL\s+OR\s+\w+\.DATA_CENTER\s+LIKE\s+:data_center_filter",
        code,
    ), f"{name}: the data-center predicate must be NULL-guarded (absent means all)"


def test_scope_binds_data_center_both_states() -> None:
    """The bind in both states (G115 clause d). Absent: None flows through so
    the SQL guard short-circuits and every data center is read — the state
    every pre-G115 invocation runs in. Set: the operator's LIKE pattern passes
    through untouched (same rule as folder_filter; the long-form spelling used
    here is the bundled hosts sample's own publishable value, so the fixture
    corpus and this contract stay on one spelling)."""
    import csv

    from drydocs.cli import DEFAULT_SAMPLES_DIR, _scope_binds

    absent = _scope_binds()
    assert absent["data_center_filter"] is None
    # the existing four dimensions are untouched by the fifth joining
    assert set(absent) == {
        "folder_filter",
        "run_as",
        "developer_sid",
        "row_cap",
        "data_center_filter",
    }

    dc = "T012-E0700-SYN"  # a data_center value carried by controlm_hosts__sample.csv
    scope = _scope_binds("CCB_AUTO_%", None, None, 100, data_center=dc)
    assert scope["data_center_filter"] == dc
    assert scope["folder_filter"] == "CCB_AUTO_%"
    # the bundled samples carry the dimension in both value states the bind
    # sees: the hosts sample holds long-form names, and a set filter selects
    # a strict subset of its rows while an absent one selects them all
    # resolved through the importable declaration, the same object fixture
    # mode itself reads (these samples are committed, not local-only assets)
    sample = DEFAULT_SAMPLES_DIR / "controlm_hosts__sample.csv"
    with sample.open(encoding="utf-8", newline="") as fh:
        rows = list(csv.DictReader(fh))
    assert rows, "hosts sample is empty"
    matched = [r for r in rows if r["data_center"] == dc]
    assert matched, "the tested pattern must select sample rows (set state)"
    assert len({r["data_center"] for r in rows}) >= 2, (
        "the hosts sample must span more than one data center so the set and "
        "absent states of the bind are distinguishable on the fixture corpus"
    )


def test_data_center_option_is_registered_on_the_commands() -> None:
    """J37: assert against the registered command objects, never `--help`.
    The option joins the scope quartet on the three Oracle-scoped verbs."""
    import inspect

    import typer

    from drydocs import cli

    def _params(command_name: str) -> dict[str, object]:
        info = next(
            i
            for i in cli.app.registered_commands
            if (i.name or i.callback.__name__.replace("_", "-")) == command_name
        )
        return {name: p.default for name, p in inspect.signature(info.callback).parameters.items()}

    for command_name in ("ingest-controlm", "analyze-variables", "normalize-variables"):
        params = _params(command_name)
        assert "data_center" in params, f"{command_name}: no data_center parameter"
        default = params["data_center"]
        assert isinstance(default, typer.models.OptionInfo), command_name
        assert "--data-center" in default.param_decls, command_name
        # optional and absent-means-all: the default is None, so every
        # existing invocation keeps its behavior
        assert default.default is None, command_name


def test_data_center_scoped_chain_is_a_partial_extract() -> None:
    """A data-center-scoped chain run must not run the removed-from-source
    mark pass (D7 extended by G115): marking the other data centers removed
    is the source-outage-looks-like-deletion trap. Pinned on the command
    source the same way the runs_on ordering pin reads it."""
    cli_src = (ROOT / "drydocs" / "cli_ingest.py").read_text(encoding="utf-8")
    ingest = cli_src[cli_src.index("def ingest_controlm") :]
    assert "full_extract=folder is None and data_center is None" in ingest
