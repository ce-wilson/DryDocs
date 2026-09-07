"""CFG1 — the domain registry is DATA, and the vocabulary's domain axis reads it.

Gate ontology-domain-registry-and-edition-grain §B1-§B3 (SIGNED 2026-09-02). Until
CFG1 the 13 domains were a comment block in 00-header.yaml and a closed enum in
config/schemas/relationship-vocabulary.schema.json; nothing joined the two, and
"registered" meant somebody edited the comment. These guards make the file
config/taxonomy/domains.yaml the one surface the others defer to (J37: the
importable object, never the comment):

- every vocabulary entry's `domain:` is a registered, ACTIVE row, and it sits in
  THAT row's fragment (the partition IS the file — §B3);
- every registered fragment exists on disk and every fragment on disk is
  registered (a bijection, so an unregistered fragment cannot appear);
- the schema's enum EQUALS the registry's ids (the enum is a render of the file,
  kept for editor-time checks; it is never the source);
- the header comment points at the file and no longer carries the closed list;
- every `authority` resolves in config/gate-log.md, and a `pending` one has NOT
  been signed (a signed record with a pending row means flip the row);
- the base-owned rule (§B5 rider) fires on a synthetic edition row — a guard with
  no positive case in this repo would first run unobserved at the company
  (review F7; the test_port_manifest.py detector-and-companion idiom).
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from drydocs_core import yaml_fragments
from drydocs_core.ontology import domain_registry as dr
from drydocs_core.ontology.domain_registry import (
    Domain,
    DomainRegistryError,
    load_registry,
    validate_rows,
)

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
REGISTRY = REPO / "config" / "taxonomy" / "domains.yaml"
VOCAB_DIR = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary"
HEADER = VOCAB_DIR / "00-header.yaml"
VOCAB_SCHEMA = REPO / "config" / "schemas" / "relationship-vocabulary.schema.json"
GATE_LOG = REPO / "config" / "gate-log.md"

#: The 13 as seeded — pinned so a silent drop of a row is a red test, not a diff
#: nobody reads. Growing the list is ONT1/ONT2's mint through §B2; add here too.
SEEDED = frozenset(
    {
        "scheduler",
        "business_application",
        "catalog",
        "architecture",
        "registry",
        "docs",
        "all",
        "context",
        "quality",
        "corporate",
        "itsm",
        "infrastructure",
        "human",
    }
)

#: A synthetic edition code for the §B5 fixture. Deliberately NOT a real code:
#: the producer never names the company's (CFG2 c), and CFG2's synthetic sample
#: adopts this one so the two fixtures agree.
SYNTHETIC_EDITION = "XMPL"


def _registry():
    return load_registry(REGISTRY, reload=True)


def _fragment_entries(path: Path) -> list[dict]:
    """The entries one fragment holds. The first fragment opens the
    `local_relationships:` key and the rest continue it as bare lists, so a
    fragment parses as either shape (yaml_fragments' contract)."""
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if isinstance(doc, dict):
        return list(doc.get("local_relationships") or [])
    return list(doc or [])


# --------------------------------------------------------------------------- #
# the file loads, and it is the 13 as ruled
# --------------------------------------------------------------------------- #


def test_the_registry_loads_with_the_thirteen_seeded_domains() -> None:
    reg = _registry()
    assert set(reg.ids()) == SEEDED
    assert set(reg.active_ids()) == SEEDED, "nothing is deprecated at mint"
    assert all(d.is_base for d in reg.domains), "no edition row exists in this repo (CFG2 c)"
    assert all(d.minted_by == "producer" for d in reg.domains)


def test_every_row_cites_a_fragment_that_exists_and_every_fragment_is_registered() -> None:
    """§B3 both ways: a domain is a partition of the vocabulary and nothing else,
    and a fragment with no registry row is a domain nobody minted."""
    reg = _registry()
    registered = {d.vocabulary_fragment for d in reg.domains}
    on_disk = {p.name for p in VOCAB_DIR.glob("*-local-*.yaml")}
    assert registered == on_disk, (
        f"registry vs disk: unregistered fragments {sorted(on_disk - registered)}; "
        f"rows whose fragment is missing {sorted(registered - on_disk)}"
    )
    assert len(registered) == len(reg.domains), "two domains cannot share a fragment"


# --------------------------------------------------------------------------- #
# the vocabulary defers to the registry
# --------------------------------------------------------------------------- #


def test_every_vocabulary_entry_names_a_registered_active_domain() -> None:
    reg = _registry()
    active = set(reg.active_ids())
    vocab = yaml_fragments.load_yaml_source(VOCAB_DIR)
    bad = [
        (rel.get("id"), rel.get("domain"))
        for rel in vocab.get("local_relationships", [])
        if rel.get("domain") not in active
    ]
    assert not bad, f"entries whose domain is not a registered ACTIVE row: {bad}"


def test_every_entry_sits_in_its_own_domains_fragment() -> None:
    """The partition IS the file (§B3). Measured true at mint for all 175
    entries; an entry filed in another domain's fragment is a domain nobody
    minted, hiding in one that was."""
    reg = _registry()
    misfiled: list[tuple[str, str, str]] = []
    for d in reg.domains:
        for rel in _fragment_entries(reg.fragment_for(d.id)):
            if rel.get("domain") != d.id:
                misfiled.append((rel.get("id"), rel.get("domain"), d.vocabulary_fragment))
    assert not misfiled, f"(entry, its domain, the fragment it sits in): {misfiled}"


def test_the_schema_enum_is_a_render_of_the_registry() -> None:
    """S6 keeps the closed enum for editor-time checking. It is the RENDER, the
    registry is the source: they must be equal, and a domain minted in one place
    only is a red test here, never a silent divergence."""
    reg = _registry()
    schema = json.loads(VOCAB_SCHEMA.read_text(encoding="utf-8"))
    enum = schema["$defs"]["local_relationship"]["properties"]["domain"]["enum"]
    assert set(enum) == set(reg.ids()), (
        f"schema enum vs registry: only in schema {sorted(set(enum) - set(reg.ids()))}; "
        f"only in registry {sorted(set(reg.ids()) - set(enum))}"
    )
    assert len(enum) == len(set(enum)), "duplicate in the schema enum"


def test_the_header_comment_is_a_pointer_not_the_list() -> None:
    """(c): the header's domain block says where the registry is and no longer
    carries the closed list — a list in two places is the state CFG1 removed."""
    text = HEADER.read_text(encoding="utf-8")
    assert "config/taxonomy/domains.yaml" in text
    # the old comment enumerated the 13 with pipes; the pointer does not
    assert not re.search(
        r"itsm\s*\|\s*infrastructure", text
    ), "00-header.yaml still enumerates the closed domain list — it is a pointer now"


# --------------------------------------------------------------------------- #
# every authority is a real ruling
# --------------------------------------------------------------------------- #


def _signed_gate_headings(log_text: str) -> set[str]:
    """Gate ids that appear in a SIGNED OFF heading of the log."""
    out: set[str] = set()
    for line in log_text.splitlines():
        if not line.startswith("## ") or "SIGNED OFF" not in line:
            continue
        m = re.search(r"GATE:\s*`?([a-z0-9-]+)`?", line)
        if m:
            out.add(m.group(1))
    return out


def test_every_authority_resolves_in_the_gate_log() -> None:
    """Nothing invented (acceptance b): a signed authority is a SIGNED OFF gate
    heading; a pending one names a gate the log has NOT signed — if it has, the
    row is stale and says pending about a ruling that exists."""
    reg = _registry()
    signed = _signed_gate_headings(GATE_LOG.read_text(encoding="utf-8"))
    problems: list[str] = []
    for d in reg.domains:
        if d.authority_status == "signed" and d.authority not in signed:
            problems.append(f"{d.id}: authority {d.authority!r} is not a SIGNED OFF gate heading")
        if d.authority_status == "pending" and d.authority in signed:
            problems.append(f"{d.id}: authority {d.authority!r} IS signed — flip authority_status")
    assert not problems, "\n".join(problems)


def test_the_pending_authority_is_the_one_known_case() -> None:
    """`itsm` was registered on SME direction (G100, 2026-08-18) ahead of its
    gate; recorded as pending rather than as a ruling that does not exist. When
    the gate signs, this test and the row flip together."""
    reg = _registry()
    pending = sorted(d.id for d in reg.domains if d.authority_status == "pending")
    assert pending == ["itsm"], pending


# --------------------------------------------------------------------------- #
# the reader refuses what the gate forbade
# --------------------------------------------------------------------------- #


def _row(**over) -> Domain:
    base = dict(
        id="scheduler",
        title="Scheduler",
        vocabulary_fragment="40-local-scheduler.yaml",
        minted_by="producer",
        registered_at="2026-08-12",
        authority="vocabulary-domains-and-id-policy",
        status="active",
    )
    base.update(over)
    return Domain(**base)


def test_a_row_without_a_fragment_is_refused(tmp_path: Path) -> None:
    """§B3: vocabulary_fragment is REQUIRED — the fragment-less domain the
    2026-09-01 design allowed has no consumer after PLAN1 and is not permitted."""
    doc = {
        "schema": dr.SCHEMA,
        "classification": "Internal-Public",
        "updated": "2026-09-04",
        "domains": [
            {
                "id": "topic",
                "title": "A backlog topic",
                "minted_by": "producer",
                "registered_at": "2026-09-04",
                "authority": "vocabulary-domains-and-id-policy",
                "status": "active",
            }
        ],
    }
    path = tmp_path / "domains.yaml"
    path.write_text(yaml.safe_dump(doc), encoding="utf-8")
    with pytest.raises(DomainRegistryError, match="vocabulary_fragment.*required"):
        load_registry(path, reload=True)


def test_a_deprecated_row_names_its_successor() -> None:
    with pytest.raises(DomainRegistryError, match="superseded_by"):
        dr._row(
            {
                "id": "old",
                "title": "Old",
                "vocabulary_fragment": "99-local-old.yaml",
                "minted_by": "producer",
                "registered_at": "2026-09-04",
                "authority": "x",
                "status": "deprecated",
            }
        )


def test_an_edition_may_extend_the_registry_with_its_own_id() -> None:
    """The positive case, so the two refusals below are refusals of something
    specific: an edition row with a NEW id, minted by the edition, passes."""
    rows = [
        _row(),
        _row(
            id="xmpl_billing",
            title="Billing (edition-owned)",
            vocabulary_fragment="60-local-xmpl-billing.yaml",
            minted_by=SYNTHETIC_EDITION,
            authority="xmpl-billing-ontology",
        ),
    ]
    validate_rows(rows)  # no raise
    assert not rows[1].is_base


def test_an_edition_row_may_not_reuse_a_base_id() -> None:
    """§B5 rider, first half: the ontology is common and base-owned; an edition
    extends, never overrides. Proven on the synthetic edition (review F7)."""
    rows = [_row(), _row(minted_by=SYNTHETIC_EDITION, authority="xmpl-scheduler-override")]
    with pytest.raises(DomainRegistryError, match="reuses a BASE id"):
        validate_rows(rows)


def test_a_base_row_is_never_deprecated_by_an_edition() -> None:
    """§B5 rider, second half: a base row's successor is a base row."""
    rows = [
        _row(status="deprecated", superseded_by="xmpl_sched"),
        _row(
            id="xmpl_sched",
            title="Scheduling (edition)",
            vocabulary_fragment="60-local-xmpl-sched.yaml",
            minted_by=SYNTHETIC_EDITION,
            authority="xmpl-sched-ontology",
        ),
    ]
    with pytest.raises(DomainRegistryError, match="never deprecated by an edition"):
        validate_rows(rows)


def test_a_missing_registry_is_loud(tmp_path: Path) -> None:
    with pytest.raises(DomainRegistryError, match="missing"):
        load_registry(tmp_path / "nope.yaml", reload=True)
