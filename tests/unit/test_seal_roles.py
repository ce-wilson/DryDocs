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
from pydantic import ValidationError

from drydocs_core.models.seal import _ROLE_CANONICAL, SealContactRow, SealRole, canonicalize_role

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
    assert SealRole(name).value == name


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
    keys = {_attribution_id(r.app_id, r.role_name.value, r.employee_sid) for r in rows}
    assert len(keys) == 3, "a role holding was lost to a MERGE collision"


def test_a_bare_operate_manager_row_keeps_the_name_the_source_gave_it() -> None:
    row = SealContactRow(app_id="70001", role_name="Operate Manager", employee_sid="K456789")
    assert row.role_name is SealRole.OPERATE_MANAGER
    assert row.role_name.value == "Operate Manager"


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


def test_an_unknown_role_name_is_still_refused_at_validation() -> None:
    """Pinning current behaviour, NOT endorsing it. G35 §A3 asks whether an
    unrecognised name should be refused like this or admitted and flagged; the
    SME's 2026-08-06 list contains four classes that hit this path today. When
    that question is ruled, this test is the one that should change."""
    with pytest.raises(ValidationError, match="unrecognised SEAL role"):
        SealContactRow(
            app_id="70001", role_name="Site Reliability Engineer", employee_sid="K789012"
        )
