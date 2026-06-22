"""Precedence resolver (D2) — the config layer's authority chain (no Neo4j).

Acceptance: *flipping `order:` in precedence.yaml changes RECONCILES_TO resolution
with no code edit.* The flip tests below change only a YAML file (loaded via
`from_yaml`) and assert the winner — and the catalog `:RECONCILES_TO` target — changes.
"""
from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml

    from drydocs.precedence import (
        Claim,
        PrecedenceResolver,
        UnknownAuthorityError,
        DEFAULT_PRECEDENCE_PATH,
    )
    from drydocs.loaders.catalog import CatalogLOBRow, resolve_lob_reconciliation

    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False

pytestmark = pytest.mark.skipif(not _AVAILABLE, reason="PyYAML not installed")

# Default chain (matches config/precedence.yaml): bmc(1) > internal(2) > lob(3).
_DEFAULT_ORDER = [
    {"id": "bmc-baseline", "authority": 1},
    {"id": "internal-standards", "authority": 2},
    {"id": "lob-product-team", "authority": 3},
]
# Same three authorities, lob promoted to the top — the ONLY change is config.
_FLIPPED_ORDER = [
    {"id": "lob-product-team", "authority": 1},
    {"id": "internal-standards", "authority": 2},
    {"id": "bmc-baseline", "authority": 3},
]


def _write_precedence(tmp_path: Path, order: list[dict], active: dict | None = None) -> Path:
    """Write a precedence.yaml the resolver loads via from_yaml — config, not code."""
    doc = {
        "schema": "drydocs.precedence.v1",
        "order": order,
        "active": active or {e["id"]: True for e in order},
        "conflict_policy": {"winner": "highest-authority", "loser_disposition": "alias"},
    }
    p = tmp_path / "precedence.yaml"
    p.write_text(yaml.safe_dump(doc), encoding="utf-8")
    return p


# --- core resolution ----------------------------------------------------------

def test_highest_authority_wins() -> None:
    r = PrecedenceResolver(_DEFAULT_ORDER)
    res = r.resolve([
        Claim("lob-product-team", "AWM", 0.5),
        Claim("internal-standards", "CIB", 0.9),
    ])
    assert res.value == "CIB"
    assert res.authority == "internal-standards"
    # The loser is kept, never dropped.
    assert res.has_conflict
    assert "lob-product-team:AWM@0.5" in res.alias_strings()


def test_flipping_order_flips_the_winner(tmp_path: Path) -> None:
    """The acceptance contract, at the resolver level: same claims + same code,
    only the YAML order changes -> the winner changes."""
    claims = [
        Claim("lob-product-team", "AWM", 0.5),
        Claim("internal-standards", "CIB", 0.9),
    ]
    default = PrecedenceResolver.from_yaml(_write_precedence(tmp_path, _DEFAULT_ORDER))
    flipped = PrecedenceResolver.from_yaml(_write_precedence(tmp_path, _FLIPPED_ORDER))

    assert default.resolve(claims).value == "CIB"           # internal-standards wins
    assert flipped.resolve(claims).value == "AWM"           # lob-product-team now wins


def test_reconciles_to_resolution_is_config_driven(tmp_path: Path) -> None:
    """The acceptance contract, on the actual RECONCILES_TO path: the catalog
    LOB's reconciled segment flips when only precedence.yaml#order flips."""
    model = CatalogLOBRow(lob_id="LOB002", code="AWMCIB", name="legacy",
                          reconciles_to_segment="AWM", reconcile_confidence=0.5)
    override = [Claim("internal-standards", "CIB", 0.9)]  # a more-authoritative crosswalk

    default = PrecedenceResolver.from_yaml(_write_precedence(tmp_path, _DEFAULT_ORDER))
    flipped = PrecedenceResolver.from_yaml(_write_precedence(tmp_path, _FLIPPED_ORDER))

    d = resolve_lob_reconciliation(model, default, extra_claims=override)
    f = resolve_lob_reconciliation(model, flipped, extra_claims=override)

    assert d["reconciles_to_segment"] == "CIB"
    assert d["reconcile_authority"] == "internal-standards"
    assert "lob-product-team:AWM@0.5" in d["reconcile_aliases"]

    assert f["reconciles_to_segment"] == "AWM"
    assert f["reconcile_authority"] == "lob-product-team"


# --- toggles & edge cases -----------------------------------------------------

def test_inactive_authority_is_skipped() -> None:
    r = PrecedenceResolver(_DEFAULT_ORDER, active={"internal-standards": False})
    res = r.resolve([
        Claim("lob-product-team", "AWM", 0.5),
        Claim("internal-standards", "CIB", 0.9),
    ])
    assert res.value == "AWM"            # winner toggled off -> next authority wins
    assert res.authority == "lob-product-team"


def test_abstaining_claim_has_no_opinion() -> None:
    r = PrecedenceResolver(_DEFAULT_ORDER)
    # A None/"" value means the authority abstains and cannot win.
    res = r.resolve([
        Claim("bmc-baseline", None),
        Claim("lob-product-team", "Corp", 1.0),
    ])
    assert res.value == "Corp"
    assert res.authority == "lob-product-team"


def test_no_eligible_claims_yields_empty() -> None:
    r = PrecedenceResolver(_DEFAULT_ORDER)
    res = r.resolve([Claim("bmc-baseline", ""), Claim("lob-product-team", None)])
    assert res.winner is None
    assert res.value is None
    assert not res.has_conflict


def test_same_authority_breaks_ties_on_confidence() -> None:
    r = PrecedenceResolver(_DEFAULT_ORDER)
    res = r.resolve([
        Claim("internal-standards", "low", 0.3),
        Claim("internal-standards", "high", 0.8),
    ])
    assert res.value == "high"


def test_unknown_authority_raises() -> None:
    r = PrecedenceResolver(_DEFAULT_ORDER)
    with pytest.raises(UnknownAuthorityError):
        r.rank("not-an-authority")


def test_position_used_when_authority_field_omitted() -> None:
    # No explicit authority: -> position decides (top = highest).
    r = PrecedenceResolver([{"id": "a"}, {"id": "b"}])
    assert r.rank("a") < r.rank("b")
    assert r.resolve([Claim("b", "B"), Claim("a", "A")]).value == "A"


# --- the shipped config is well-formed ---------------------------------------

def test_real_precedence_yaml_chain() -> None:
    r = PrecedenceResolver.from_yaml(DEFAULT_PRECEDENCE_PATH)
    assert r.rank("bmc-baseline") < r.rank("internal-standards") < r.rank("lob-product-team")
    for a in ("bmc-baseline", "internal-standards", "lob-product-team"):
        assert r.is_active(a)
