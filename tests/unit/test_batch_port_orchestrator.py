"""Guards for the declared batch-port orchestrator migration (backlog C14).

Executes the C12 platforms-taxonomy sign-off: the SEAL-declared orchestrator
string lands on (:BusinessApplication)-[:USES_SOFTWARE {source: 'batch-port'}]->
(:SoftwareProduct) via the platforms.yaml seed-row crosswalk. These tests keep
the crosswalk honest (only gate-confirmed software_registry_ref links resolve),
the coverage policy honest (unmapped strings reported, never guessed), and the
source-value disambiguation honest (both USES_SOFTWARE writers key their MERGE
on source so the edges can never collide). Pure file/adapter checks — no Neo4j.
"""
from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parents[2]
APPS_FILE = REPO / "config" / "taxonomy" / "business-application.yaml"
PLATFORMS_FILE = REPO / "config" / "taxonomy" / "platforms.yaml"
CYPHER_FILE = REPO / "drydocs" / "loaders" / "cypher" / "batch_port_orchestrator.cypher"
REGISTRY_CYPHER_FILE = REPO / "drydocs" / "loaders" / "cypher" / "software_registry.cypher"


# ---- crosswalk --------------------------------------------------------------

def test_crosswalk_resolves_all_seed_row_spellings() -> None:
    from drydocs.loaders.batch_port_orchestrator import build_orchestrator_crosswalk

    xwalk = build_orchestrator_crosswalk(PLATFORMS_FILE)
    # Every seed row contributes id, scheduler_kind, and label — casefolded.
    for spelling, ref in (
        ("controlm", "controlm"),
        ("ControlM", "controlm"),
        ("BMC Control-M", "controlm"),
        ("autosys", "autosys"),
        ("Autosys", "autosys"),
        ("CA Autosys", "autosys"),
        ("airflow", "airflow"),
        ("Airflow", "airflow"),
        ("Apache Airflow", "airflow"),
    ):
        assert xwalk.get(spelling.strip().casefold()) == ref, (
            f"'{spelling}' should resolve to '{ref}'"
        )


def test_crosswalk_only_carries_gate_confirmed_refs() -> None:
    """Every crosswalk value must be a software_registry_ref present on a seed
    row — the crosswalk can never invent a product id."""
    from drydocs.loaders.batch_port_orchestrator import build_orchestrator_crosswalk

    doc = yaml.safe_load(PLATFORMS_FILE.read_text(encoding="utf-8"))
    declared_refs = {
        row["software_registry_ref"]
        for row in doc["platforms"]
        if row.get("software_registry_ref")
    }
    xwalk = build_orchestrator_crosswalk(PLATFORMS_FILE)
    assert set(xwalk.values()) <= declared_refs
    assert declared_refs == {"controlm", "autosys", "airflow"}


def test_crosswalk_ignores_rows_without_a_ref(tmp_path: Path) -> None:
    """A seed row with no software_registry_ref contributes nothing — no
    nearest-match guessing."""
    from drydocs.loaders.batch_port_orchestrator import build_orchestrator_crosswalk

    plat = tmp_path / "platforms.yaml"
    plat.write_text(
        "platforms:\n"
        "  - id: tws\n"
        "    label: IBM TWS\n"
        "    scheduler_kind: TWS\n",
        encoding="utf-8",
    )
    assert build_orchestrator_crosswalk(plat) == {}


# ---- adapter ----------------------------------------------------------------

def test_adapter_resolves_the_committed_capture() -> None:
    """Every declared orchestrator in the committed taxonomy capture must
    resolve — an unmapped string in the capture itself is config drift."""
    from drydocs.loaders.batch_port_orchestrator import BatchOrchestratorYamlAdapter
    from drydocs_core.models.registry import BatchPortOrchestratorRow

    doc = yaml.safe_load(APPS_FILE.read_text(encoding="utf-8"))
    declared = [
        a for a in doc["nodes"]["business_applications"] if a.get("batch_orchestrator")
    ]
    assert declared, "the committed capture should declare at least one orchestrator"

    with BatchOrchestratorYamlAdapter(APPS_FILE, PLATFORMS_FILE) as adapter:
        rows = list(adapter.rows())

    assert len(rows) == len(declared)
    assert adapter.unmapped == [], (
        f"committed capture carries unmapped orchestrator strings: {adapter.unmapped}"
    )
    for raw in rows:
        row = BatchPortOrchestratorRow.model_validate(raw)
        assert row.product_id in {"controlm", "autosys", "airflow"}
        assert row.orchestrator_raw


def test_adapter_reports_unmapped_and_skips_undeclared(tmp_path: Path) -> None:
    """The coverage policy: an unmapped string yields product_id=None and is
    listed in adapter.unmapped (never guessed); an app without the field is
    skipped and counted."""
    from drydocs.loaders.batch_port_orchestrator import BatchOrchestratorYamlAdapter

    apps = tmp_path / "apps.yaml"
    apps.write_text(
        "nodes:\n"
        "  business_applications:\n"
        "    - sealid: 1\n"
        "      batch_orchestrator: ControlM\n"
        "    - sealid: 2\n"
        "      batch_orchestrator: IBM TWS\n"
        "    - sealid: 3\n",
        encoding="utf-8",
    )
    with BatchOrchestratorYamlAdapter(apps, PLATFORMS_FILE) as adapter:
        rows = list(adapter.rows())

    assert len(rows) == 2, "undeclared app must be skipped, not errored"
    assert adapter.apps_without_declaration == 1
    by_id = {r["seal_id"]: r for r in rows}
    assert by_id["1"]["product_id"] == "controlm"
    assert by_id["2"]["product_id"] is None
    assert adapter.unmapped == [{"seal_id": "2", "orchestrator_raw": "IBM TWS"}]


# ---- loader wiring ----------------------------------------------------------

def test_loader_class_wiring() -> None:
    from drydocs.loaders.batch_port_orchestrator import BatchPortOrchestratorLoader

    assert BatchPortOrchestratorLoader.cypher_path == CYPHER_FILE
    assert BatchPortOrchestratorLoader.cypher_path.exists()
    assert BatchPortOrchestratorLoader.row_model is not None
    assert BatchPortOrchestratorLoader.name == "batch_port_orchestrator.v1"


# ---- cypher invariants ------------------------------------------------------

def test_cypher_stamps_and_keys_the_batch_port_source() -> None:
    """The gate-ruled disambiguation: the edge MERGE must be KEYED on
    {source: 'batch-port'} — a bare USES_SOFTWARE MERGE would match (and
    silently reuse) a stack or detection edge between the same pair."""
    cypher = CYPHER_FILE.read_text(encoding="utf-8")
    assert "MERGE (a)-[u:USES_SOFTWARE {source: 'batch-port'}]->(sp)" in cypher
    assert "batch_orchestrator_unmapped" in cypher, "unmapped flag missing"


def test_cypher_never_creates_endpoints() -> None:
    """MATCH-only on both endpoints — apps come from seal_applications,
    products from load-software-registry; this pass creates neither."""
    cypher = CYPHER_FILE.read_text(encoding="utf-8")
    assert "MATCH (a:BusinessApplication" in cypher
    assert "MERGE (a:BusinessApplication" not in cypher
    assert "MERGE (sp:SoftwareProduct" not in cypher


def test_registry_cypher_keys_its_own_source() -> None:
    """The other USES_SOFTWARE writer must key on {source: 'registry'} for the
    same reason (C14 hardening) — two unkeyed writers would steal each other's
    edges on shared app/product pairs."""
    cypher = REGISTRY_CYPHER_FILE.read_text(encoding="utf-8")
    assert "MERGE (a)-[u:USES_SOFTWARE {source: 'registry'}]->(sp)" in cypher


def test_cypher_unmapped_flag_keys_on_the_crosswalk_not_the_node_lookup() -> None:
    """``batch_orchestrator_unmapped`` means "platforms.yaml had no
    software_registry_ref for this string" — a CONFIG gap. Keyed on ``sp`` (the
    node lookup) instead of ``row.product_id`` (the crosswalk result), an absent
    or incomplete registry relabels correctly-mapped apps as unmapped, writing
    the wrong diagnosis into the graph and contradicting the CLI coverage report
    on the very same run."""
    cypher = CYPHER_FILE.read_text(encoding="utf-8")
    assert (
        "a.batch_orchestrator_unmapped     = "
        "CASE WHEN row.product_id IS NULL THEN true ELSE null END" in cypher
    )
    assert "CASE WHEN sp IS NULL THEN true" not in cypher


def test_cypher_header_documents_where_the_prereq_is_enforced() -> None:
    """The template cannot make the whole-registry check itself (it runs per
    BATCH), so its header must point at the loader method that does — otherwise
    the next person re-pointing this loader at another database re-opens the
    silent-success hole."""
    cypher = CYPHER_FILE.read_text(encoding="utf-8")
    assert "_assert_endpoint_registries_present" in cypher
    assert "cannot span databases" in cypher


# ---- prereq enforcement (Q8 family) -----------------------------------------


class _FakeAdapter:
    def __init__(self, rows: list[dict]) -> None:
        self._rows = rows

    def __enter__(self) -> _FakeAdapter:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        yield from self._rows


class _FakeClient:
    """Stands in for the graph: which apps and products actually exist.

    ``apps`` is the set of seal_ids a real (non-SchemaMeta) :BusinessApplication
    exists for; ``products`` likewise for :SoftwareProduct. Both start empty in
    a fresh database — which is exactly the pair of silent-success cases these
    tests pin down. The template's write behaviour is simulated from the flushed
    rows: an app is stamped only if it was matched, and the edge is written only
    if the row's product_id resolves.
    """

    def __init__(self, apps: set[str], products: set[str]) -> None:
        self.apps = apps
        self.products = products
        self.run_calls: list[tuple[str, dict]] = []
        self.run_script_calls: list[tuple[str, dict]] = []

    def run(self, cypher: str, params: dict | None = None, **kwargs) -> list[dict]:
        bind = {**(params or {}), **kwargs}
        self.run_calls.append((cypher, bind))
        if "AS found" in cypher:
            # The SchemaMeta exemplars are excluded by the query's own
            # NOT n:SchemaMeta predicate, so they never reach these counts.
            if "(n:BusinessApplication)" in cypher:
                return [{"found": len(self.apps)}]
            if "(n:SoftwareProduct)" in cypher:
                return [{"found": len(self.products)}]
            return [{"found": 0}]
        if "WITH sid, a WHERE a IS NULL" in cypher:
            return [
                {"seal_id": sid}
                for sid in sorted(bind.get("seal_ids", []))
                if sid not in self.apps
            ]
        if "WHERE NOT (a)-[:USES_SOFTWARE {source: 'batch-port'}]" in cypher:
            out = []
            for row in self.flushed_rows():
                if row["seal_id"] not in self.apps:
                    continue  # hard MATCH missed — nothing was stamped
                if row.get("product_id") in self.products:
                    continue  # edge written
                out.append(
                    {
                        "seal_id": row["seal_id"],
                        "orchestrator_raw": row.get("orchestrator_raw"),
                        "unmapped": True if row.get("product_id") is None else None,
                    }
                )
            return sorted(out, key=lambda r: r["seal_id"])
        if "SHOW INDEXES" in cypher:
            return []
        if "AS rows_changed" in cypher:
            return [{"rows_changed": 0}]
        return []

    def run_script(self, script: str, params: dict | None = None) -> None:
        self.run_script_calls.append((script, dict(params or {})))

    def flushed_rows(self) -> list[dict]:
        rows: list[dict] = []
        for _, bind in self.run_calls:
            rows.extend(bind.get("batch", []))
        for _, params in self.run_script_calls:
            rows.extend(params.get("batch", []))
        return rows


def _row(seal_id: str, raw: str = "ControlM", product_id: str | None = "controlm") -> dict:
    return {"seal_id": seal_id, "orchestrator_raw": raw, "product_id": product_id}


def _loader(client: _FakeClient, rows: list[dict]):
    from drydocs.loaders.batch_port_orchestrator import BatchPortOrchestratorLoader

    return BatchPortOrchestratorLoader(client, _FakeAdapter(rows), run_log=False)


def test_empty_app_registry_fails_loudly() -> None:
    """The hard-MATCH endpoint: ZERO :BusinessApplication means every row's
    MATCH fails and nothing is written — not even the raw string — while the
    run reports OK with rows_processed > 0."""
    client = _FakeClient(apps=set(), products={"controlm"})
    with pytest.raises(RuntimeError, match="no :BusinessApplication nodes are reachable"):
        _loader(client, [_row("1")]).load()


def test_empty_product_registry_fails_loudly() -> None:
    """The FOREACH-guard endpoint: ZERO :SoftwareProduct silently drops every
    USES_SOFTWARE edge (the defect Q8 closed in bmc_docs)."""
    client = _FakeClient(apps={"1"}, products=set())
    with pytest.raises(RuntimeError, match="no :SoftwareProduct nodes are reachable"):
        _loader(client, [_row("1")]).load()


def test_refusal_writes_nothing_not_even_the_job_run() -> None:
    """Refusal follows the _preflight_indexes convention — it lands before
    _open_run, so a refused load leaves no :JobRun behind to look successful."""
    client = _FakeClient(apps=set(), products=set())
    with pytest.raises(RuntimeError):
        _loader(client, [_row("1")]).load()
    assert not client.flushed_rows()
    assert not [c for c, _ in client.run_calls if "MERGE (run:JobRun" in c]


def test_schema_meta_exemplars_alone_do_not_satisfy_the_prereqs() -> None:
    """schema_graph.cypher MERGEs :SchemaMeta:<Label> exemplars carrying the
    REAL label with no key property. A bare count() would see them and wave both
    empty registries straight through, so both probes must exclude them."""
    client = _FakeClient(apps=set(), products=set())
    with pytest.raises(RuntimeError):
        _loader(client, [_row("1")]).load()

    probes = [c for c, _ in client.run_calls if "AS found" in c]
    assert probes, "no endpoint-presence probe was issued"
    for probe in probes:
        assert "NOT n:SchemaMeta" in probe, (
            "endpoint probes must use the rename-proof label predicate"
        )
        assert "IS NOT NULL" in probe, "keyless stubs must not satisfy the probe"


def test_healthy_load_reports_no_misses() -> None:
    client = _FakeClient(apps={"1", "2"}, products={"controlm", "autosys"})
    loader = _loader(client, [_row("1"), _row("2", "Autosys", "autosys")])
    summary = loader.load()

    assert summary.status == "OK"
    assert summary.rows_processed == 2
    assert loader.apps_not_in_graph == []
    assert loader.apps_without_edge == []


def test_row_whose_app_is_absent_is_named_not_silently_dropped() -> None:
    """A hard-MATCH miss leaves NO trace in the graph, so it cannot be found by
    asking what this run touched — the loader must remember what it sent. The
    CLI coverage report counts crosswalk hits on the SOURCE side and would read
    "2/2 mapped" while one row landed nowhere at all."""
    client = _FakeClient(apps={"1"}, products={"controlm"})
    loader = _loader(client, [_row("1"), _row("9999")])
    loader.load()

    assert loader.seal_ids_sent == {"1", "9999"}
    assert loader.apps_not_in_graph == ["9999"]


def test_product_missing_from_registry_is_reported_as_a_load_gap() -> None:
    """The crosswalk resolved, but that product is not in the registry. The
    whole-registry refusal cannot see this — the registry is present, just
    incomplete — so it has to surface here, flagged as a LOAD gap (unmapped
    falsy) rather than a platforms.yaml config gap."""
    client = _FakeClient(apps={"1"}, products={"controlm"})
    loader = _loader(client, [_row("1", "Airflow", "airflow")])
    loader.load()

    assert loader.apps_without_edge == [
        {"seal_id": "1", "orchestrator_raw": "Airflow", "unmapped": None}
    ]


def test_unmapped_string_is_reported_as_a_config_gap() -> None:
    """product_id=None is the platforms.yaml gap the C12 gate ruled on: flagged
    on the node, no edge, reported — and distinguished from the load gap above,
    because the two need different fixes."""
    client = _FakeClient(apps={"1"}, products={"controlm"})
    loader = _loader(client, [_row("1", "IBM TWS", None)])
    loader.load()

    assert loader.apps_without_edge == [
        {"seal_id": "1", "orchestrator_raw": "IBM TWS", "unmapped": True}
    ]


def test_missing_edge_probe_is_scoped_to_this_run() -> None:
    """The probe must key on batch_orchestrator_last_run_id — an unscoped sweep
    would report apps from earlier runs as this run's misses."""
    client = _FakeClient(apps={"1"}, products={"controlm"})
    loader = _loader(client, [_row("1")])
    loader.load()

    probe = [
        (c, b) for c, b in client.run_calls
        if "WHERE NOT (a)-[:USES_SOFTWARE {source: 'batch-port'}]" in c
    ]
    assert probe, "no missing-edge probe was issued"
    cypher, bind = probe[0]
    assert "batch_orchestrator_last_run_id: $run_id" in cypher
    assert bind["run_id"] == loader.run_id
