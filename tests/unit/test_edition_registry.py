"""CFG2 — the edition registry: a declared segment keyed to an Area Product.

Gate ontology-domain-registry-and-edition-grain §C1-§C4 (SIGNED 2026-09-02). The
file is config/taxonomy/editions.yaml, on the lob-product-team.yaml pattern —
Internal, a synthetic sample producer-side, real rows company-side, a per-entry
manifest row. These guards hold CFG2 (e): every code is unique, is never a module
series code, never a frozen letter series and never DD; producer-side every row is
a sample; a REAL row's area_product_id resolves against the loaded :AreaProduct set
where a graph is present and is skipped — said, not hidden — where it is not (J18).

The allocator's module series and frozen set are read from THEIR files
(modules.yaml through validate.py's own reader, FROZEN_SERIES from the allocator
module) and handed to the pure check — the check never hardcodes either.
"""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path

import pytest

from drydocs_core import edition_registry as er
from drydocs_core.edition_registry import (
    Edition,
    EditionRegistryError,
    code_collisions,
    load_registry,
    unresolved_area_products,
)

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "config" / "taxonomy" / "editions.yaml"

#: CFG1's synthetic edition code (tests/unit/test_domain_registry.py) — the sample
#: here carries it so the two fixtures agree.
SYNTHETIC_EDITION = "XMPL"


def _allocator():
    path = REPO / ".claude" / "skills" / "groom-backlog" / "validate.py"
    spec = importlib.util.spec_from_file_location("groom_validate_for_editions", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _registry():
    return load_registry(REGISTRY, reload=True)


def _row(**over) -> Edition:
    base = dict(
        code="XMPL",
        title="Example",
        area_product_id="AP_SAMPLE_001",
        minted_by="producer",
        registered_at="2026-09-04",
        authority="ontology-domain-registry-and-edition-grain",
        sample=True,
    )
    base.update(over)
    return Edition(**base)


# --------------------------------------------------------------------------- #
# the file: Internal, synthetic, and carrying CFG1's fixture code
# --------------------------------------------------------------------------- #


def test_the_sample_loads_and_every_row_is_synthetic() -> None:
    """(a)/(c): the producer ships the sample only — a real row here would name
    an Area Product, and the company's code is the company's to mint."""
    reg = _registry()
    assert reg.codes(), "the sample is not empty"
    assert all(e.sample for e in reg.editions), "a non-sample row in the producer's file"
    assert reg.real() == ()
    assert SYNTHETIC_EDITION in reg.codes(), "CFG1's base-owned fixture code is in the sample"
    doc = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert doc["classification"] == "Internal"
    assert doc["classification_only"] is True


def test_the_two_registries_never_share() -> None:
    """§A2: a domain id never looks like an edition code and vice versa — one is
    lowercase snake_case, the other 2-5 uppercase letters — and neither file
    carries the other's key."""
    from drydocs_core.ontology.domain_registry import load_registry as load_domains

    editions = _registry()
    domains = load_domains(reload=True)
    assert not set(editions.codes()) & set(domains.ids())
    doc = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    assert "domains" not in doc and "vocabulary_fragment" not in str(doc.get("editions"))


# --------------------------------------------------------------------------- #
# (e): every code is clear of the module series, the frozen letters and DD
# --------------------------------------------------------------------------- #


def test_every_code_is_clear_of_module_series_frozen_letters_and_dd() -> None:
    allocator = _allocator()
    reg = _registry()
    problems = code_collisions(
        reg.editions,
        module_series=allocator.module_series(),
        frozen_series=allocator.FROZEN_SERIES,
    )
    assert not problems, "\n".join(problems)


def test_the_collision_check_catches_each_kind() -> None:
    """The J26 idiom: a detector that silently matches nothing reads as a pass."""
    allocator = _allocator()
    modules = allocator.module_series()
    a_module_code = next(iter(modules.values()))
    rows = [
        _row(),
        _row(code=a_module_code),  # a module's series
        _row(code="G"),  # a frozen letter (bypassing the 2-letter floor on purpose: G is frozen)
        _row(code="MM"),  # a frozen two-letter series
    ]
    problems = code_collisions(rows, module_series=modules, frozen_series=allocator.FROZEN_SERIES)
    assert any("series code of module" in p for p in problems), problems
    assert sum("FROZEN" in p for p in problems) == 2, problems
    dup = code_collisions([_row(), _row()])
    assert dup == ["XMPL: declared twice"]


def test_dd_is_refused_at_load(tmp_path: Path) -> None:
    doc = {
        "schema": er.SCHEMA,
        "classification": "Internal",
        "updated": "2026-09-04",
        "editions": [
            {
                "code": "DD",
                "title": "x",
                "area_product_id": "AP",
                "minted_by": "company",
                "registered_at": "2026-09-04",
                "authority": "x",
            }
        ],
    }
    path = tmp_path / "editions.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    with pytest.raises(EditionRegistryError, match="reserved"):
        load_registry(path, reload=True)


@pytest.mark.parametrize("bad", ["x", "TOOLONG", "Ab", "A-B", ""])
def test_a_code_is_two_to_five_uppercase_letters(bad: str) -> None:
    with pytest.raises(EditionRegistryError):
        er._row(
            {
                "code": bad,
                "title": "x",
                "area_product_id": "AP",
                "minted_by": "producer",
                "registered_at": "2026-09-04",
                "authority": "x",
            }
        )


def test_an_edition_is_declared_by_a_base_never_by_an_instance() -> None:
    """§B2: a base mints, an instance requests — `minted_by` on an edition row is
    the base that declared it, never another edition."""
    with pytest.raises(EditionRegistryError, match="declared by a BASE"):
        er._row(
            {
                "code": "NEWE",
                "title": "x",
                "area_product_id": "AP",
                "minted_by": "XMPL",
                "registered_at": "2026-09-04",
                "authority": "x",
            }
        )


# --------------------------------------------------------------------------- #
# (e), second half: a REAL row's Area Product resolves in the graph — J18
# --------------------------------------------------------------------------- #


def test_the_resolution_check_ignores_samples_and_reports_real_misses() -> None:
    rows = [
        _row(),  # sample: never checked, its id is invented
        _row(code="REAL", area_product_id="AP_REAL", sample=False),
    ]
    assert unresolved_area_products(rows, loaded_ids=set()) == [("REAL", "AP_REAL")]
    assert unresolved_area_products(rows, loaded_ids={"AP_REAL"}) == []


def test_real_rows_resolve_against_the_loaded_area_products() -> None:
    """Runs for real only where real rows live (the company). Here the sample has
    no real row, so there is nothing to look up and the test SAYS so rather than
    passing quietly; with real rows and no reachable graph it skips (J18 — a
    venue that cannot answer is not a venue that answered yes)."""
    reg = _registry()
    real = reg.real()
    if not real:
        pytest.skip("no real edition rows in this tree (the producer ships the sample only)")
    if not os.environ.get("NEO4J_URI") and not (REPO / ".env").is_file():
        pytest.skip(
            "no graph settings on this machine — the check needs the loaded :AreaProduct set"
        )
    from drydocs_core.config import Neo4jSettings
    from drydocs_core.neo4j_client import Neo4jClient

    settings = Neo4jSettings()
    try:
        with Neo4jClient(
            settings.uri, settings.user, settings.password.get_secret_value(), database="drydocs"
        ) as client:
            rows = client.run("MATCH (ap:AreaProduct) RETURN ap.area_product_id AS id")
            loaded = {r["id"] for r in rows}
    except Exception as exc:  # unreachable is a skip, never a pass
        pytest.skip(f"graph unreachable: {exc}")
    missing = unresolved_area_products(real, loaded)
    assert (
        not missing
    ), f"real edition rows whose area_product_id is not a loaded :AreaProduct: {missing}"
