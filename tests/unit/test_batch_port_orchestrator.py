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
