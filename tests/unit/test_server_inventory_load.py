"""Z3 loader + resolution-pass guards (gate server-location-ontology, 12/12,
2026-08-19 — config/gate-log.md).

What is pinned here, and to which ruling:

* §A1 — the loader writes :Server (the inventory spine) and the identity join
  is an EDGE pass, never a merge: the resolution cypher must not contain a
  single MERGE on a node.
* §A3 — designation is validated to the ruled enum (PROD | DR) at the model.
* §B2 — location_grain is computed loader-side as the finest SUPPLIED level,
  never inferred.
* §C1 — the tier property values are EXACTLY the ruled enum (exact |
  normalized | dns-resolved); T2 carries the exactly-one-candidate ambiguity
  guard; T3 is deliberately absent until the Z4 collector.
* §C2 — the technology-port leg is MATCH-only on :BusinessApplication (apps
  are counted when absent, never minted), and the port MERGE carries the
  port_app_key composite (parent_app_id, kind='Technology').

The fixture is the same synthetic per-application export the publish-boundary
guard test pins (tests/fixtures/server_inventory/), so a drift in either
consumer surfaces in both.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest
from pydantic import ValidationError

from drydocs.loaders.server_inventory import COVERAGE_QUERY, ServerInventoryLoader
from drydocs.loaders.server_resolution import (
    CYPHER_PATH as RESOLUTION_CYPHER_PATH,
)
from drydocs.loaders.server_resolution import (
    ServerResolutionCoverage,
)
from drydocs_core.adapters import CsvAdapter
from drydocs_core.cypher_split import strip_comments
from drydocs_core.models import ServerInventoryRow

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "server_inventory" / "synthetic-server-export.csv"

LOADER_CYPHER = strip_comments(
    ServerInventoryLoader.cypher_path.read_text(encoding="utf-8")  # type: ignore[union-attr]
)
RESOLUTION_CYPHER = strip_comments(RESOLUTION_CYPHER_PATH.read_text(encoding="utf-8"))


# ---- in-memory fake (the test_base_loader_smoke idiom) ----------------------


class _FakeNeo4jClient:
    def __init__(self) -> None:
        self.run_calls: list[tuple[str, dict]] = []
        self.run_script_calls: list[tuple[str, dict]] = []

    def run(self, cypher: str, params: dict[str, Any] | None = None, **kwargs: Any) -> list[dict]:
        self.run_calls.append((cypher, {**(params or {}), **kwargs}))
        return []

    def run_script(self, script: str, params: dict[str, Any] | None = None) -> None:
        self.run_script_calls.append((script, dict(params or {})))


# ---- the model (§A3, §B2) ----------------------------------------------------


def test_designation_is_the_ruled_enum() -> None:
    row = ServerInventoryRow(server_name="s", designation="prod", business_application="70055")
    assert row.designation == "PROD"
    with pytest.raises(ValidationError):
        ServerInventoryRow(server_name="s", designation="STAGING", business_application="70055")


def test_location_grain_is_finest_supplied_never_inferred() -> None:
    base = {"server_name": "s", "designation": "DR", "business_application": "70055"}
    assert ServerInventoryRow(**base, data_center="B1", city="C").location_grain == "building"
    assert ServerInventoryRow(**base, city="C", country="X").location_grain == "city"
    assert ServerInventoryRow(**base, state="ST").location_grain == "state"
    assert ServerInventoryRow(**base, country="X").location_grain == "country"
    assert ServerInventoryRow(**base).location_grain is None


# ---- the loader over the real fixture (e2e staging; idempotency is the
# ---- integration half — tests/integration/test_server_inventory_e2e.py) -----


def test_fixture_loads_clean_and_carries_the_grain_declaration() -> None:
    client = _FakeNeo4jClient()
    with CsvAdapter(FIXTURE) as adapter:
        summary = ServerInventoryLoader(client, adapter, run_log=False).load()
    assert summary.status == "OK"
    assert summary.rows_processed == 5
    assert summary.rows_rejected == 0
    # Multi-statement template -> run_script; the batch carries the computed
    # §B2 declaration on every row (the fixture always supplies a building).
    (script, params) = next((s, p) for s, p in client.run_script_calls if "UNWIND $batch" in s)
    assert all(r["location_grain"] == "building" for r in params["batch"])
    assert {r["designation"] for r in params["batch"]} == {"PROD", "DR"}


def test_loader_declarations_pin_the_registry_row() -> None:
    assert ServerInventoryLoader.source_id == "infra:server-export"
    assert ServerInventoryLoader.source_label == "csv"
    # Per-application files: a full-extract sweep on one app's load would mark
    # every OTHER app's servers removed — the docstring records the reason.
    assert ServerInventoryLoader.sweep_label is None


# ---- the cypher shapes (§A1, §C2) --------------------------------------------


def test_app_leg_is_match_only_and_the_port_carries_the_composite_key() -> None:
    assert "MATCH (a:BusinessApplication" in LOADER_CYPHER
    assert "MERGE (a:BusinessApplication" not in LOADER_CYPHER
    # port_app_key is (parent_app_id, kind) — the MERGE must bind both.
    assert "parent_app_id: row.business_application" in LOADER_CYPHER
    assert "kind: 'Technology'" in LOADER_CYPHER
    assert "role: 'technology_port'" in LOADER_CYPHER


def test_resolution_pass_merges_edges_never_nodes() -> None:
    for line in RESOLUTION_CYPHER.splitlines():
        if "MERGE" in line:
            assert "-[" in line, f"resolution MERGE must be an edge, got: {line.strip()}"


def test_resolution_tiers_are_the_ruled_enum_and_t3_is_absent() -> None:
    assert "'exact'" in RESOLUTION_CYPHER
    assert "'normalized'" in RESOLUTION_CYPHER
    # T3 arrives with the Z4 collector — writing it here would fake evidence.
    assert "'dns-resolved'" not in RESOLUTION_CYPHER
    # The T2 ambiguity guard: exactly one candidate or no edge.
    assert "size(candidates) = 1" in RESOLUTION_CYPHER


def test_resolution_and_coverage_exclude_the_schema_exemplars() -> None:
    assert ":SchemaMeta" in RESOLUTION_CYPHER
    assert ":SchemaMeta" in COVERAGE_QUERY


# ---- the coverage invariant (§C1: visible, never dropped) ---------------------


def test_coverage_reconciles_and_reports_the_ambiguity_guard() -> None:
    cov = ServerResolutionCoverage(
        total_hosts=10,
        null_nodeid=1,
        matched_exact=4,
        matched_normalized=2,
        matched_dns_resolved=0,
        unmatched=3,
        ambiguous_short_name=2,
    )
    assert cov.reconciles()
    assert cov.as_dict()["ambiguous_short_name"] == 2
    cov.unmatched = 2  # a host went missing from the census
    assert not cov.reconciles()
