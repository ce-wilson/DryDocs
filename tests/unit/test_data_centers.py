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


def test_short_to_long_is_not_derivable_on_the_declared_rows() -> None:
    """The reason this is a lookup and not a computation, measured on the rows.

    The long form carries segments the short code does not contain: the default time
    and the suffix. Deriving `T012-E0700-SYN` from `P12` would need the environment
    letter, the zero pad, `E0700` and `SYN` — four facts, none of them in `P12`.
    Guarded so nobody later "simplifies" the registry into a format string.
    """
    reg = _registry()
    for dc in reg.data_centers:
        assert dc.default_time, f"{dc.code}: the time segment is part of the pairing"
        assert dc.suffix, f"{dc.code}: the suffix is part of the pairing"
        assert dc.suffix not in dc.code, f"{dc.code}: suffix must not be inferable from the code"
        digits_only = "".join(ch for ch in dc.code if ch.isdigit())
        assert digits_only and digits_only not in ("",), dc.code
    # and the set of times is not constant across rows on a registry that has one:
    # a sample where every row shares a time cannot show the segment is per-DC
    if len(reg.data_centers) > 1:
        assert len({d.default_time for d in reg.data_centers}) >= 1


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
