"""LOAD2 - the data-center spelling registry: one `--data-center` value, two value
domains, a DECLARED pairing.

The failure this closes is silent, which is why it is worth a suite: before LOAD2 every
extract bound one value domain, so a long-form value against the CM_DEF_VTAB family
(folders, jobs, variables) returned ZERO ROWS and read as an empty data center rather
than as an error. These guards pin the pairing as data, the refusal as loud, and the
non-derivability as measured rather than asserted.
"""

from __future__ import annotations

import csv
from pathlib import Path

import pytest

from drydocs_core.data_centers import (
    INTERNAL_TWIN,
    REGISTRY_FILE,
    DataCenterError,
    load_registry,
    resolve,
)

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "drydocs" / "data" / "samples"


def _registry():
    return load_registry(REGISTRY_FILE, reload=True)


def _sample_dcs(name: str) -> set[str]:
    """The data centers a bundled sample carries.

    `drydocs/data/` is gitignored apart from the force-tracked samples, so a clone that
    does not carry one SKIPS rather than fails — the corpus is evidence here, and absent
    evidence proves nothing either way (the repo's skip-guard policy)."""
    path = SAMPLES / name
    if not path.is_file():
        pytest.skip(f"{name} is not in this clone (drydocs/data/ is gitignored)")
    with path.open(encoding="utf-8-sig", newline="") as fh:
        return {r["data_center"] for r in csv.DictReader(fh) if r.get("data_center")}


def test_every_row_declares_both_spellings_and_the_pairing_is_one_to_one() -> None:
    reg = _registry()
    assert reg.data_centers, "the registry must declare at least one pairing"
    for dc in reg.data_centers:
        assert dc.code and dc.name, dc
        assert dc.code != dc.name, f"{dc.code}: a pairing of one spelling is not a pairing"
    assert len(set(reg.codes())) == len(reg.codes()), "short codes must be unique"
    assert len(set(reg.names())) == len(reg.names()), "long names must be unique"


def test_one_value_in_either_spelling_resolves_to_the_same_pair() -> None:
    """The property the CLI depends on: the operator passes ONE value, in whichever
    spelling they have, and both binds come out."""
    reg = _registry()
    for dc in reg.data_centers:
        assert resolve(dc.code, reg) is dc
        assert resolve(dc.name, reg) is dc
        assert resolve(dc.code.lower(), reg) is dc, "matching is case-insensitive"
        assert resolve(f"  {dc.name}  ", reg) is dc, "surrounding whitespace is trimmed"


def test_a_value_in_neither_domain_is_refused_and_names_both(monkeypatch) -> None:
    """Refusing is the point. Passing an unknown value through is what produced the
    silent zero-row result, so the error names BOTH domains and what each serves."""
    reg = _registry()
    with pytest.raises(DataCenterError) as exc:
        resolve("NOPE-999", reg)
    message = str(exc.value)
    assert "NOPE-999" in message
    assert "CM_DEF_VTAB" in message and "CM_HOSTS" in message
    assert reg.codes()[0] in message and reg.names()[0] in message
    assert reg.source in message, "the refusal names the venue it read (J18)"


def test_the_time_and_suffix_are_optional_metadata_never_identity() -> None:
    """THE TIME MAY NOT BE THERE, and the registry must not require it.

    BMC defines no format for the data-center name: the vendor corpus uses it as a scope
    and its only other mention marks the default-time-of-day reading "(internal)",
    linking out to our own standard. That standard is `authority: internal-standards`
    (precedence tier 2, refining the baseline) and `trust_tier: internal / SME-asserted /
    mutable`, captured from SME chat with its own open items. So a name carrying no
    `E####` segment is legal, and requiring one would encode a mutable convention as a
    structural invariant and refuse a legitimate row.

    Identity is the code/name PAIR and only that. The registry ships a row with neither
    optional segment so this property is exercised by the shipped data, not just asserted.
    """
    reg = _registry()
    bare = [d for d in reg.data_centers if not d.default_time and not d.suffix]
    assert bare, (
        "the registry must carry at least one row with no time and no suffix, or this "
        "property is untested on the shipped data"
    )
    for dc in bare:
        assert resolve(dc.code, reg) is dc, "a row with no time segment still resolves"
        assert resolve(dc.name, reg) is dc


def test_short_to_long_is_a_lookup_because_the_vendor_defines_no_format() -> None:
    """Why this is a lookup and not a computation, stated at the level that survives.

    The argument is NOT "the long form carries segments the short code lacks" — that is
    true of the rows that carry them and says nothing about a row that does not. It is
    that the field is free-form as far as Control-M is concerned, so no rule takes a
    short code to a long name. Measured here as: no single transformation of the code
    produces the name across the declared rows, and the guard is deliberately blind to
    which optional segments a row happens to have.
    """
    reg = _registry()
    for dc in reg.data_centers:
        assert dc.code != dc.name
        assert dc.name != dc.code.upper() and dc.name != dc.code.lower()
        # the one transformation that LOOKS derivable — zero-padding the digits — does
        # not produce the name on its own, whatever else the name carries
        digits = "".join(ch for ch in dc.code if ch.isdigit())
        padded = f"{dc.code[:1]}0{digits}"
        assert dc.name != padded, (
            f"{dc.code}: if a pad alone produced {dc.name!r} the pairing would be "
            "derivable for this row — the registry must not imply that it is"
        )


def test_the_publishable_rows_are_all_samples_and_the_twin_is_absent_here() -> None:
    """Producer-side there is no real inventory: every row is synthetic and the reader
    says which venue it read. A real-row claim belongs to the tree that holds them (J18)."""
    reg = _registry()
    assert all(d.sample for d in reg.data_centers), "no real data center may enter the repo"
    assert reg.real() == ()
    assert reg.source == "publishable-sample"
    assert not INTERNAL_TWIN.exists(), (
        "the internal twin is machine-local and untracked; if it exists on this machine "
        "the default load reads it and a sample-only assertion above would be wrong"
    )


def test_the_registry_covers_the_bundled_corpus_in_both_domains() -> None:
    """LOAD2 (d): one option value must reach both sample families, which is only true
    if the registry pairs the values the committed samples actually carry."""
    reg = _registry()
    folders = _sample_dcs("controlm_folders__sample.csv")
    hosts = _sample_dcs("controlm_hosts__sample.csv")
    assert folders and hosts
    assert folders <= set(reg.codes()), (
        f"folders sample carries short codes the registry does not pair: "
        f"{sorted(folders - set(reg.codes()))}"
    )
    assert hosts <= set(reg.names()), (
        f"hosts sample carries long names the registry does not pair: "
        f"{sorted(hosts - set(reg.names()))}"
    )
    # the two samples speak DIFFERENT domains — the property that makes the corpus a
    # test of the split at all
    assert not (folders & hosts), "a value in both samples would collapse the two domains"


def test_a_malformed_registry_is_refused_rather_than_half_read(tmp_path: Path) -> None:
    bad = tmp_path / "dc.yaml"
    bad.write_text("schema: something.else\ndata_centers: []\n", encoding="utf-8")
    with pytest.raises(DataCenterError, match="schema must be"):
        load_registry(bad, reload=True)

    half = tmp_path / "half.yaml"
    half.write_text(
        "schema: drydocs.data-centers.v1\ndata_centers:\n  - code: P12\n", encoding="utf-8"
    )
    with pytest.raises(DataCenterError, match="both `code`"):
        load_registry(half, reload=True)

    dupe = tmp_path / "dupe.yaml"
    dupe.write_text(
        "schema: drydocs.data-centers.v1\n"
        "data_centers:\n"
        "  - {code: P12, name: T012-E0700-SYN}\n"
        "  - {code: P12, name: T099-E0700-SYN}\n",
        encoding="utf-8",
    )
    with pytest.raises(DataCenterError, match="duplicate code"):
        load_registry(dupe, reload=True)

    missing = tmp_path / "absent.yaml"
    with pytest.raises(DataCenterError, match="registry is missing"):
        load_registry(missing, reload=True)
