"""G72 — the three-valued attribution-surface discriminator + the SS-D4 order
(gate tom-roles-enumeration-and-cardinality, signed 2026-08-11).

What SS-D1 found: SEAL's own contacts view and the ServiceNow TOM view return
different counts for the same application, and nothing recorded which surface
an attribution came from — `Attribution.source` was the literal 'SEAL' at both
loader sites regardless. The fix declares the three surfaces IN the existing
precedence chain (config/precedence.yaml — SS-D4: "this is the order
config/precedence.yaml gains"), with the stamp each surface writes, so surface
identity and precedence live in ONE place and the existing resolver settles a
roster disagreement with no new mechanism.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_core.precedence import Claim, PrecedenceResolver, UnknownAuthorityError

REPO_ROOT = Path(__file__).resolve().parents[2]
CYPHER = REPO_ROOT / "drydocs" / "loaders" / "cypher"

HAND_VERIFIED = "hand-verified-crosswalk"
SERVICENOW = "servicenow-tom"
SEAL_EXTRACT = "seal-contact-extract"


@pytest.fixture(scope="module")
def resolver() -> PrecedenceResolver:
    return PrecedenceResolver.from_yaml()


def test_the_three_surfaces_are_declared_in_the_ruled_order(resolver) -> None:
    """SS-D4: hand-verified > ServiceNow TOM > SEAL extract. Human verification
    outranks both automated surfaces; the operating-model source outranks the
    contact extract."""
    assert resolver.surface_ids() == (HAND_VERIFIED, SERVICENOW, SEAL_EXTRACT)
    assert resolver.rank(HAND_VERIFIED) < resolver.rank(SERVICENOW) < resolver.rank(SEAL_EXTRACT)


def test_stamps_are_unique_and_seal_matches_every_loaded_graph(resolver) -> None:
    """The SEAL stamp is deliberately the literal every already-loaded graph
    carries and the pinned attribution_id embeds (app_id|SEAL|role|sid) —
    declaring the existing value costs zero migration."""
    stamps = [resolver.stamp_for(sid) for sid in resolver.surface_ids()]
    assert len(stamps) == len(set(stamps)) == 3
    assert resolver.stamp_for(SEAL_EXTRACT) == "SEAL"
    assert resolver.authority_for_stamp("SEAL") == SEAL_EXTRACT
    # a non-surface chain entry has no stamp; an unknown id raises
    assert resolver.stamp_for("bmc-baseline") is None
    with pytest.raises(UnknownAuthorityError):
        resolver.stamp_for("not-an-authority")


def test_both_loader_sites_stamp_the_declared_seal_surface(resolver) -> None:
    """SS-D1's defect site, tied to the declaration: the two SEAL loader cypher
    files must stamp exactly the declared stamp — change the declaration, not
    the cypher. (The PAT team-role attributions are a different fact family
    and already stamp 'pat'.)"""
    stamp = resolver.stamp_for(SEAL_EXTRACT)
    contacts = (CYPHER / "seal_contacts.cypher").read_text(encoding="utf-8")
    applications = (CYPHER / "seal_applications.cypher").read_text(encoding="utf-8")
    assert f"m.source     = '{stamp}'" in contacts
    for site in ("m1.source", "m2.source"):
        assert f"{site}     = '{stamp}'" in applications, site


def test_a_roster_disagreement_resolves_per_the_ruling(resolver) -> None:
    """SS-D4 in executable form: two ingested surfaces that disagree with no
    rule is the one outcome SS-D4 refuses. The existing resolver IS the rule."""
    seal_says = Claim(SEAL_EXTRACT, "SID-A")
    tom_says = Claim(SERVICENOW, "SID-B")
    hand_says = Claim(HAND_VERIFIED, "SID-C")

    res = resolver.resolve([seal_says, tom_says])
    assert res.authority == SERVICENOW  # operating-model source beats the extract
    assert res.has_conflict  # the loser is an alias, never silently dropped

    res = resolver.resolve([seal_says, tom_says, hand_says])
    assert res.authority == HAND_VERIFIED  # human verification beats both
    assert {c.authority for c in res.aliases} == {SEAL_EXTRACT, SERVICENOW}
