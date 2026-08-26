"""SEAL role vocabulary — the canonicalizer and what it must never do.

Written 2026-08-06 alongside the fix to the bare-Operate-Manager coercion
(gate G35 §A5). Until then `drydocs_core.models.seal` had NO tests at all,
which is how an alias that destroyed a real role holding lived in the tree
long enough to be found by reading rather than by failing.

The defect, in one sentence: `"operate manager"` was aliased to
`"L2 Operate Manager"`, so a source row that named no level was rewritten to
one that did. Because the same person routinely holds L1, L2 and the bare
role on one application, the rewritten row produced an ``attribution_id``
identical to that person's genuine L2 row — and seal_contacts.cypher MERGEs
on ``attribution_id``, so the two folded into a single node. Three source
holdings became two, with no flag, and which one survived depended on batch
order.

The tests below pin the fix and, more usefully, the INVARIANT behind it: an
alias may only resolve to a level it actually names.
"""

from __future__ import annotations

import pytest

from drydocs_core.models.seal import _ROLE_CANONICAL, SealContactRow, canonicalize_role
from drydocs_core.ontology.tom_role_vocabulary import load_vocabulary

# The three classes, per the SME ruling of 2026-08-05/06 (G35 §A5): separate
# role classes, holdable by three different people or by one.
OPERATE_MANAGER_CLASSES = ("L1 Operate Manager", "L2 Operate Manager", "Operate Manager")


# How seal_contacts.cypher:55 builds the key. Duplicated here deliberately —
# the point of these tests is the SHAPE of the key, and a test that imported
# the shape from the code under test could not detect a change to it.
def _attribution_id(app_id: str, role_name: str, sid: str) -> str:
    return f"{app_id}|SEAL|{role_name}|{sid}"


@pytest.mark.parametrize("name", OPERATE_MANAGER_CLASSES)
def test_each_operate_manager_class_is_admissible_in_its_own_right(name: str) -> None:
    assert canonicalize_role(name) == name
    assert load_vocabulary().concept_for(name) is not None


def test_the_three_operate_manager_classes_stay_three() -> None:
    """The regression. Before the fix this set had two members, not three."""
    assert len({canonicalize_role(n) for n in OPERATE_MANAGER_CLASSES}) == 3


def test_one_person_holding_all_three_keys_three_attributions() -> None:
    """The case that made the coercion lossy: same app, same person, three roles.

    config/gate-log.md:882 records it from the live registry, and the bundled
    taxonomy sample (application 70001, Agent Brown) reproduces it.
    """
    rows = [
        SealContactRow(app_id="70001", role_name=name, employee_sid="K456789")
        for name in OPERATE_MANAGER_CLASSES
    ]
    keys = {_attribution_id(r.app_id, r.role_name, r.employee_sid) for r in rows}
    assert len(keys) == 3, "a role holding was lost to a MERGE collision"
    # and since the §G9 split, the three resolve to three CONCEPTS too
    assert {r.tom_role_id for r in rows} == {
        "operate_manager_l1",
        "operate_manager_l2",
        "operate_manager",
    }


def test_a_bare_operate_manager_row_keeps_the_name_the_source_gave_it() -> None:
    row = SealContactRow(app_id="70001", role_name="Operate Manager", employee_sid="K456789")
    assert row.role_name == "Operate Manager"
    assert row.tom_role_id == "operate_manager"


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        ("l2 manager", "L2 Operate Manager"),  # names a level -> may assert one
        ("L2 Ops Manager", "L2 Operate Manager"),
        ("l1 ops manager", "L1 Operate Manager"),
        ("OPERATE MANAGER", "Operate Manager"),  # names none -> must not invent one
        ("  Operate Manager  ", "Operate Manager"),
    ],
)
def test_alias_tolerance_survives_the_fix(alias: str, expected: str) -> None:
    """Drift tolerance is a separate concern from vocabulary membership, and the
    fix must not have cost us any of it."""
    assert canonicalize_role(alias.strip()) == expected


def test_no_alias_invents_a_level_the_alias_does_not_name() -> None:
    """The general form of the defect, so the next one is caught by this file
    rather than by a data loss.

    An alias that says nothing about L1 or L2 may not resolve to a canonical
    name that does. Stated as an invariant over the whole table, not as a
    special case for the one entry that broke it.
    """
    offenders = {
        alias: canonical
        for alias, canonical in _ROLE_CANONICAL.items()
        if canonical.startswith(("L1 ", "L2 "))
        and not ("l1" in alias.lower() or "l2" in alias.lower())
    }
    assert offenders == {}, f"alias(es) assert a level the source never stated: {offenders}"


# ── G70: the admission gate retired (gate §A3/§F4, signed 2026-08-11) ────────
# The test that stood here pinned the pre-G70 refusal and said of itself
# "when that question is ruled, this test is the one that should change".
# It was ruled: admit flagged. These are its replacements.


@pytest.mark.parametrize(
    "name",
    [
        "Deployment Owner",
        "Deployment Information Owner",
        "Application Module Owner",
        "Site Reliability Engineer",
    ],
)
def test_the_four_classes_the_old_gate_rejected_now_load(name: str) -> None:
    """§A1d measured the cost of the enum gate: four of the SME's thirteen
    classes could not be loaded at all. They load now, each to its own
    declared concept."""
    row = SealContactRow(app_id="70001", role_name=name, employee_sid="K789012")
    assert row.role_name == name
    assert row.tom_role_id is not None
    assert not row.tom_role_id.startswith("operate_manager")


def test_an_undeclared_name_loads_flagged_never_dies() -> None:
    """§A3/§F4: an unrecognised name is ADMITTED with tom_role_id None — the
    loader flags unmapped_role from exactly that — instead of the row dying
    at validation where no review surface ever sees it."""
    row = SealContactRow(app_id="70001", role_name="Grand Vizier", employee_sid="K789012")
    assert row.role_name == "Grand Vizier"  # the source's term is kept (§B2)
    assert row.role_source_name == "Grand Vizier"
    assert row.tom_role_id is None


def test_the_raw_source_string_survives_alongside_the_canonical() -> None:
    """§A4b: verbatim means VERBATIM. The field ledger promised the raw string
    and the old model discarded it at validation — canonicalized 'l2 ops
    manager' reached the graph as 'L2 Operate Manager' and the source's own
    spelling was unrecoverable. Both survive now, in different fields."""
    row = SealContactRow(app_id="70001", role_name="l2 ops manager", employee_sid="K456789")
    assert row.role_name == "L2 Operate Manager"  # canonical — keys the attribution_id
    assert row.role_source_name == "l2 ops manager"  # raw — lands on the Attribution
    assert row.tom_role_id == "operate_manager_l2"


def test_tech_partner_and_cto_are_distinguishable_again() -> None:
    """§A6c's accepted risk, no longer taken: the alias made the two terms
    indistinguishable downstream. The alias still resolves — but the raw
    term now survives, so the graph can answer which one the source used."""
    tech = SealContactRow(app_id="70001", role_name="Tech Partner", employee_sid="K345678")
    cto = SealContactRow(app_id="70001", role_name="CTO", employee_sid="K345678")
    assert tech.role_name == cto.role_name == "CTO"
    assert tech.role_source_name == "Tech Partner"
    assert cto.role_source_name == "CTO"


def test_every_pre_g70_canonical_spelling_is_frozen() -> None:
    """THE NO-RE-KEY PIN (§H5 / identity gate §D2): attribution_id embeds the
    canonical spelling, so a 'tidy the canonical' edit re-keys every loaded
    Attribution for that class and orphans the old nodes. Every spelling the
    pre-G70 model could emit must come out of the reshaped model
    BYTE-IDENTICAL — this is what makes G70 a migration-free change for
    already-loadable rows, and it is why the migration script touches
    concepts only."""
    pre_g70_canonicals = [
        "Application Owner",
        "Primary Information Owner",
        "Backup Information Owner",
        "CTO",
        "Design Authority",
        "Chief Business Technologist",
        "L1 Operate Manager",
        "L2 Operate Manager",
        "Operate Manager",
        "Backup Application Owner",
        "Risk Manager",
    ]
    for name in pre_g70_canonicals:
        row = SealContactRow(app_id="70001", role_name=name, employee_sid="K000000")
        assert row.role_name == name, f"canonical spelling drifted: {name!r} -> {row.role_name!r}"
        assert _attribution_id("70001", row.role_name, "K000000") == f"70001|SEAL|{name}|K000000"


def test_normalization_resolves_the_abbrev_convention_without_new_aliases() -> None:
    """§A3b's second question, answered as the gate suggested: normalise
    punctuation/whitespace before lookup rather than growing an alias per
    typographic variant. 'Chief Technology Officer(CTO)' is the SME's own
    worked example — it used to die at validation without ever reaching the
    loader's flag."""
    assert canonicalize_role("Chief Technology Officer(CTO)") == "CTO"
    assert canonicalize_role("Application  Owner") == "Application Owner"
    assert canonicalize_role("Site Reliability Engineer (SRE)") == "Site Reliability Engineer"


def test_the_level_invariant_extends_to_normalization() -> None:
    """The 2026-08-06 defect class, both directions, on the NEW path: a raw
    string naming a level may only resolve to that level, and normalization
    stripping a parenthetical may not silently discard the level it stated —
    'Operate Manager (L2)' returns None (loads flagged) rather than becoming
    the bare class."""
    assert canonicalize_role("Operate Manager (L2)") is None
    assert canonicalize_role("L2 Operate Manager (ops)") == "L2 Operate Manager"
    row = SealContactRow(app_id="70001", role_name="Operate Manager (L2)", employee_sid="K1")
    assert row.tom_role_id is None  # flagged for review, the level question intact
    assert row.role_source_name == "Operate Manager (L2)"
