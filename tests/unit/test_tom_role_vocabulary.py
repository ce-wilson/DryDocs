"""G70 — the declared TOM role vocabulary, and the drift guards that keep the
four formerly-hardcoded surfaces deferring to it.

The gate's §A1b measured WHY the guards exist: the only pre-G70 YAML role
list was read by no code, and it drifted TWICE inside a single gate with the
full suite passing both times. A vocabulary nobody is forced to update rots
into fiction (the ui-components precedent) — so the supplement seed, the
alias table, the loader Cypher and the taxonomy sample are all tested against
the declaration here.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from drydocs_core.models.seal import _ROLE_CANONICAL, canonicalize_role
from drydocs_core.ontology.tom_role_vocabulary import (
    VOCABULARY_FILE,
    TomRoleVocabularyError,
    load_vocabulary,
)

REPO = Path(__file__).resolve().parents[2]
SUPPLEMENT = REPO / "drydocs_core" / "schema" / "seal_ontology_supplement.cypher"
CONTACTS_CYPHER = REPO / "drydocs" / "loaders" / "cypher" / "seal_contacts.cypher"
MIGRATION = REPO / "drydocs" / "loaders" / "cypher" / "migrate_tom_role_split_g70.cypher"
BIZAPP = REPO / "config" / "taxonomy" / "business-application.yaml"

#: the signed §G register's short list — seeded, not invented (acceptance (3))
G_REGISTER_REQUIRED = {
    "application_owner",
    "primary_information_owner",
    "backup_information_owner",
    "cto",
    "technology_risk_controls",
    "design_authority",
    "backup_application_owner",
}


# ── the declaration itself ───────────────────────────────────────────────────


def test_the_declaration_loads_with_sixteen_classes():
    vocab = load_vocabulary(reload=True)
    assert len(vocab.classes) == 16
    assert vocab.catalog_total_rows == 83  # corrected from "100+" (K21 §10.7)
    assert vocab.out_of_scope_families, "the catalog remainder is MARKED, not dropped"


def test_the_required_set_is_the_signed_g_register():
    vocab = load_vocabulary()
    assert set(vocab.required_ids()) == G_REGISTER_REQUIRED


def test_cardinality_is_recorded_once_on_the_scheme_not_per_class():
    """§B3: one-or-more everywhere is a property of the MODEL. A per-class
    cardinality field reappearing is the drift this test refuses."""
    vocab = load_vocabulary()
    assert vocab.cardinality == "one-or-more"
    doc = yaml.safe_load(VOCABULARY_FILE.read_text(encoding="utf-8"))
    assert all("cardinality" not in cls for cls in doc["classes"])


def test_both_sre_rows_are_seeded_each_with_its_own_scope():
    """Close-out 2026-08-11: which SRE shape a team uses is an implementation
    choice — a reorganisation moves DATA, not vocabulary. Both are derived
    (the G16 amendment) so G71's completeness report can exclude them."""
    vocab = load_vocabulary()
    individual = vocab.by_id("site_reliability_engineer")
    team = vocab.by_id("sre_devops_incident_resolver_team")
    assert (individual.scope, team.scope) == ("Individual", "Group")
    assert individual.derived and team.derived
    assert not individual.required and not team.required


def test_the_operate_manager_split_is_three_declared_classes():
    vocab = load_vocabulary()
    ids = {c.id for c in vocab.classes}
    assert {"operate_manager", "operate_manager_l1", "operate_manager_l2"} <= ids
    assert vocab.concept_for("L1 Operate Manager") == "operate_manager_l1"
    assert vocab.concept_for("L2 Operate Manager") == "operate_manager_l2"
    assert vocab.concept_for("Operate Manager") == "operate_manager"


def test_risk_manager_crosswalks_to_technology_risk_controls_and_stops():
    """§A2: one class, two names — and the close-out made it unconditional
    (Individual scope in the catalog; there is no group to map to)."""
    vocab = load_vocabulary()
    assert vocab.concept_for("Risk Manager") == "technology_risk_controls"
    cls = vocab.by_id("technology_risk_controls")
    assert cls.required and cls.scope == "Individual"


def test_every_class_declares_the_f6b_lifecycle_flag():
    vocab = load_vocabulary()
    assert all(isinstance(c.active, bool) for c in vocab.classes)
    assert all(c.active for c in vocab.classes), "nothing is retired today"


def test_a_retired_class_stops_resolving(tmp_path):
    """Retirement is a STATE WITH BEHAVIOUR: an inactive class's rows load
    flagged like any undeclared name — not silently kept live, not deleted."""
    doc = yaml.safe_load(VOCABULARY_FILE.read_text(encoding="utf-8"))
    for cls in doc["classes"]:
        if cls["id"] == "chief_business_technologist":
            cls["active"] = False
            cls["required"] = False
    target = tmp_path / "vocab.yaml"
    target.write_text(yaml.safe_dump(doc), encoding="utf-8")
    vocab = load_vocabulary(target, reload=True)
    assert vocab.concept_for("Chief Business Technologist") is None
    assert vocab.by_id("chief_business_technologist").active is False  # still declared


def test_the_declaration_refuses_a_required_derived_class(tmp_path):
    """The G16 amendment's whole point, enforced at load: a derived fact has
    no place in the required-contact register."""
    doc = yaml.safe_load(VOCABULARY_FILE.read_text(encoding="utf-8"))
    for cls in doc["classes"]:
        if cls["id"] == "site_reliability_engineer":
            cls["required"] = True
    target = tmp_path / "vocab.yaml"
    target.write_text(yaml.safe_dump(doc), encoding="utf-8")
    with pytest.raises(TomRoleVocabularyError, match="mutually exclusive"):
        load_vocabulary(target, reload=True)


def test_one_spelling_cannot_admit_into_two_classes(tmp_path):
    doc = yaml.safe_load(VOCABULARY_FILE.read_text(encoding="utf-8"))
    doc["classes"][0]["source_names"].append("Design Authority")
    target = tmp_path / "vocab.yaml"
    target.write_text(yaml.safe_dump(doc), encoding="utf-8")
    with pytest.raises(TomRoleVocabularyError, match="two classes"):
        load_vocabulary(target, reload=True)


# ── drift guard 1: the supplement's scheme seed ──────────────────────────────


def _supplement_seeds() -> dict[str, dict[str, str]]:
    """Parse the TOMRole MERGEs out of the seal supplement — the declared_terms()
    idiom: the .cypher is a source artifact, and the guard reads it so the seed
    cannot drift from the declaration without a test noticing (§A1b)."""
    text = SUPPLEMENT.read_text(encoding="utf-8")
    seeds: dict[str, dict[str, str]] = {}
    pattern = re.compile(
        r'MERGE \(c\d+:TOMRole \{id: "([a-z0-9_]+)"\}\)(.*?)(?=MERGE \(|WITH 1)', re.DOTALL
    )
    for cid, body in pattern.findall(text):
        flat: dict[str, str] = {}
        for key, quoted, bare in re.findall(r'c\d+\.(\w+) = (?:"([^"]*)"|(true|false))', body):
            flat[key] = quoted if quoted else bare
        seeds[cid] = flat
    return seeds


def test_the_supplement_seed_matches_the_declaration():
    vocab = load_vocabulary(reload=True)
    seeds = _supplement_seeds()
    assert set(seeds) == {c.id for c in vocab.classes}, (
        "the supplement's tom_roles seed and config/taxonomy/tom-role-vocabulary.yaml "
        "disagree about which classes exist — amend BOTH in one commit (§H3's one-unit rule)"
    )
    for cls in vocab.classes:
        seed = seeds[cls.id]
        assert seed.get("pref_label") == cls.pref_label, f"{cls.id}: pref_label drifted"
        assert seed.get("required") == str(cls.required).lower(), f"{cls.id}: required drifted"
        assert seed.get("scope") == cls.scope, f"{cls.id}: scope drifted"
        if cls.derived:
            assert seed.get("derived") == "true", f"{cls.id}: derived marker missing in seed"


def test_the_supplement_records_cardinality_once_on_the_scheme():
    text = SUPPLEMENT.read_text(encoding="utf-8")
    assert 's.cardinality = "one-or-more"' in text
    assert "levels" not in _supplement_seeds().get(
        "operate_manager", {}
    ), "c7.levels retired with the §G9 split"


# ── drift guard 2: the loader defers, it does not list ───────────────────────


def test_the_loader_cypher_carries_no_role_crosswalk():
    """§A8 surface (iii): the 4-branch CASE is gone, and this test is what
    stops a hurried fix from quietly reintroducing a hardcoded role list."""
    text = CONTACTS_CYPHER.read_text(encoding="utf-8")
    assert "CASE row.role_name" not in text
    assert "row.tom_role_id" in text
    assert "row.role_source_name" in text
    for literal in ("'backup_information_owner'", "'operate_manager'", "'L1'"):
        assert literal not in text, f"hardcoded role literal back in the loader: {literal}"


# ── drift guard 3: the alias table resolves INTO the declaration ─────────────


def test_every_alias_resolves_to_a_declared_source_name():
    vocab = load_vocabulary()
    declared = {n.casefold() for c in vocab.classes for n in c.source_names}
    strays = {a: c for a, c in _ROLE_CANONICAL.items() if c.casefold() not in declared}
    assert strays == {}, f"alias(es) resolve outside the declared vocabulary: {strays}"


# ── drift guard 4: the taxonomy capture ──────────────────────────────────────


def test_the_business_application_capture_no_longer_carries_a_role_register():
    """Acceptance (2): the `roles:` list is DELETED, not reinterpreted —
    leaving both surfaces was §F3's one outcome to refuse."""
    doc = yaml.safe_load(BIZAPP.read_text(encoding="utf-8"))
    assert "roles" not in (doc.get("nodes") or {}), (
        "config/taxonomy/business-application.yaml grew a role register again — "
        "the declared vocabulary is config/taxonomy/tom-role-vocabulary.yaml (G70 §F3)"
    )


def test_every_membership_role_name_canonicalizes_into_the_declaration():
    """The memberships REMAIN (they are the gate walk's sample — §H4), and this
    replaces the derivation the deleted list depended on: the sample can never
    quietly grow a name the register does not carry."""
    vocab = load_vocabulary()
    doc = yaml.safe_load(BIZAPP.read_text(encoding="utf-8"))
    names = {entry["role"] for block in doc["nodes"]["memberships"] for entry in block["roles"]}
    unresolved = {name for name in names if vocab.concept_for(canonicalize_role(name)) is None}
    assert (
        unresolved == set()
    ), f"membership role name(s) outside the declared vocabulary: {unresolved}"


# ── the migration (§H5) ──────────────────────────────────────────────────────


def test_the_migration_exists_and_moves_exactly_the_three_populations():
    text = MIGRATION.read_text(encoding="utf-8")
    assert "operate_manager_l1" in text and "operate_manager_l2" in text
    assert "technology_risk_controls" in text and "chief_business_technologist" in text
    assert "REMOVE m.level" in text and "REMOVE c.levels" in text
    # restricted: it re-points concepts; no executable line may touch an
    # attribution_id (the §H5 hazard the migration exists to NOT need)
    executable = [line for line in text.splitlines() if not line.strip().startswith("//")]
    assert all("attribution_id" not in line for line in executable)
