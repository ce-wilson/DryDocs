"""J42 — the backlog UNION rule, enforced: a port may never drop an item file.

PORT-MANIFEST.yaml promises it for ``docs/restructure/backlog/items/*.yaml``
("Never drop a file; never regress a status") and nothing compared the two
repos' id sets, so a port that under-delivered left both sides internally
consistent and green.

PROVEN TO FAIL ON AN INJECTED DEFECT before it is trusted (J26): the deletion
test below removes one item FILE from a consumer copy and asserts the check
names that id. The vacuous-green cases get the same treatment — a tombstone
file, an absent items directory and an empty one must each FAIL LOUD, because a
check that reads two empty sets and reports "no difference" is exactly the
failure this item exists to close.

Fixture-driven and repository-free: :func:`compare` takes two directories.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs.port_backlog_union import (
    UNION_EXCLUSIONS,
    BacklogUnionError,
    compare,
    item_ids,
)

pytest.importorskip("yaml")


def _write_item(items_dir: Path, item_id: str, *, inner_id: str | None = None) -> Path:
    """One minimal item file. `inner_id` overrides the `id:` key to force the
    filename-vs-inner-id disagreement Clause 6 makes load-bearing."""
    path = items_dir / f"{item_id}.yaml"
    path.write_text(
        f"id: {inner_id or item_id}\n"
        f"epic: test-epic\n"
        f"title: item {item_id}\n"
        "type: task\n"
        "status: todo\n",
        encoding="utf-8",
    )
    return path


def _tree(root: Path, ids: list[str]) -> Path:
    """A backlog tree with an items/ directory holding `ids`."""
    backlog = root
    (backlog / "items").mkdir(parents=True, exist_ok=True)
    for item_id in ids:
        _write_item(backlog / "items", item_id)
    return backlog


# --------------------------------------------------------------------------- #
# the union itself
# --------------------------------------------------------------------------- #
def test_identical_trees_pass_and_report_no_accepted_difference(tmp_path: Path) -> None:
    producer = _tree(tmp_path / "producer", ["A1", "A2", "B10"])
    consumer = _tree(tmp_path / "consumer", ["A1", "A2", "B10"])

    report = compare(producer, consumer, exclusions={})

    assert report.passed
    assert report.missing == ()
    assert report.accepted == ()
    assert "missing from the consumer: none" in report.render()


def test_an_injected_deletion_fails_naming_the_id(tmp_path: Path) -> None:
    """THE J26 PROOF. One item FILE removed from the consumer copy — the shape a
    port that quietly under-delivers actually produces."""
    producer = _tree(tmp_path / "producer", ["A1", "A2", "B10"])
    consumer = _tree(tmp_path / "consumer", ["A1", "A2", "B10"])
    (consumer / "items" / "A2.yaml").unlink()

    report = compare(producer, consumer, exclusions={})

    assert not report.passed
    assert report.missing == ("A2",)
    rendered = report.render()
    assert "A2" in rendered and "RESULT: FAIL" in rendered


def test_missing_ids_are_named_in_natural_order_not_counted(tmp_path: Path) -> None:
    producer = _tree(tmp_path / "producer", ["C2", "C10", "C1"])
    consumer = _tree(tmp_path / "consumer", ["C1"])

    report = compare(producer, consumer, exclusions={})

    assert report.missing == ("C2", "C10"), "C2 sorts before C10 — the store's natural key"
    assert "- C2" in report.render()


def test_consumer_only_ids_are_reported_but_never_a_failure(tmp_path: Path) -> None:
    """The company plans its own work in the same id space; the manifest's union
    rule is one-directional (producer -> consumer)."""
    producer = _tree(tmp_path / "producer", ["A1"])
    consumer = _tree(tmp_path / "consumer", ["A1", "COMPANY1"])

    report = compare(producer, consumer, exclusions={})

    assert report.passed
    assert report.consumer_only == ("COMPANY1",)
    assert "consumer-only" in report.render()


# --------------------------------------------------------------------------- #
# accepted differences are not silence
# --------------------------------------------------------------------------- #
def test_an_allowed_id_passes_and_prints_its_reason(tmp_path: Path) -> None:
    producer = _tree(tmp_path / "producer", ["A1", "A2"])
    consumer = _tree(tmp_path / "consumer", ["A1"])
    reason = "producer-only tooling the company repo has no equivalent for"

    report = compare(producer, consumer, exclusions={"A2": reason})

    assert report.passed
    assert report.accepted == (("A2", reason),)
    rendered = report.render()
    assert reason in rendered, "a ruled omission must not read like no omission"
    assert "accepted differences: none declared" not in rendered


def test_a_clean_union_says_no_difference_was_declared(tmp_path: Path) -> None:
    """The other half of the same distinction: silence must be stated, so the
    reader can tell 'nobody dropped anything' from 'somebody accepted a drop'."""
    producer = _tree(tmp_path / "producer", ["A1"])
    consumer = _tree(tmp_path / "consumer", ["A1"])

    assert (
        "accepted differences: none declared" in compare(producer, consumer, exclusions={}).render()
    )


def test_an_allowance_for_an_id_the_producer_never_had_is_stale(tmp_path: Path) -> None:
    producer = _tree(tmp_path / "producer", ["A1"])
    consumer = _tree(tmp_path / "consumer", ["A1"])

    report = compare(producer, consumer, exclusions={"GHOST9": "a reason of adequate length here"})

    assert not report.passed
    assert report.stale_exclusions[0][0] == "GHOST9"


def test_an_allowance_for_an_id_the_consumer_has_never_described_a_drop(tmp_path: Path) -> None:
    producer = _tree(tmp_path / "producer", ["A1", "A2"])
    consumer = _tree(tmp_path / "consumer", ["A1", "A2"])

    report = compare(producer, consumer, exclusions={"A2": "a reason of adequate length here"})

    assert not report.passed
    assert "never dropped" in report.stale_exclusions[0][1]


def test_a_token_reason_is_not_a_reason(tmp_path: Path) -> None:
    producer = _tree(tmp_path / "producer", ["A1", "A2"])
    consumer = _tree(tmp_path / "consumer", ["A1"])

    report = compare(producer, consumer, exclusions={"A2": "n/a"})

    assert not report.passed
    assert "sentence" in report.stale_exclusions[0][1]


def test_the_shipped_allow_list_is_usable_against_this_repo() -> None:
    """Hygiene on the real dict: entries are checked by compare() against real
    trees, so all this asserts is that each carries a written sentence — the
    stale/contradictory halves cannot be judged without a producer base."""
    for item_id, reason in UNION_EXCLUSIONS.items():
        assert len(str(reason).split()) >= 5, f"{item_id}: the reason must be a sentence"


# --------------------------------------------------------------------------- #
# the vacuous-green cases: an unreadable side FAILS, never "no difference"
# --------------------------------------------------------------------------- #
def test_the_tombstone_monolith_is_refused_before_it_is_read(tmp_path: Path) -> None:
    """docs/restructure/backlog.yaml has no items key: reading it would compare
    two empty sets and PASS for being wrong. That is the whole reason J42 was
    repointed at the sharded grain."""
    tombstone = tmp_path / "backlog.yaml"
    tombstone.write_text(
        "schema: drydocs.backlog.v3\n# sharded 2026-08-20 (Y2)\n", encoding="utf-8"
    )

    with pytest.raises(BacklogUnionError, match="tombstone"):
        item_ids(tombstone)


def test_an_absent_items_directory_fails_loud(tmp_path: Path) -> None:
    empty_tree = tmp_path / "no-items"
    empty_tree.mkdir()

    with pytest.raises(BacklogUnionError, match="unreadable backlog"):
        item_ids(empty_tree)


def test_an_empty_items_directory_fails_loud(tmp_path: Path) -> None:
    """An empty backlog is never silent — the store's own words."""
    tree = tmp_path / "empty"
    (tree / "items").mkdir(parents=True)

    with pytest.raises(BacklogUnionError, match="unreadable backlog"):
        item_ids(tree)


def test_a_filename_disagreeing_with_its_inner_id_fails_loud(tmp_path: Path) -> None:
    """Under Clause 6 the filename IS the id, so a mismatch means the set being
    diffed is not the set that exists."""
    tree = tmp_path / "mismatch"
    (tree / "items").mkdir(parents=True)
    _write_item(tree / "items", "A1", inner_id="A9")

    with pytest.raises(BacklogUnionError, match="does not match the filename"):
        item_ids(tree)


def test_an_unreadable_side_never_becomes_an_empty_comparison(tmp_path: Path) -> None:
    """compare() must propagate the failure rather than diff against nothing."""
    producer = _tree(tmp_path / "producer", ["A1", "A2"])
    broken = tmp_path / "broken"
    broken.mkdir()

    with pytest.raises(BacklogUnionError):
        compare(producer, broken, exclusions={})


# --------------------------------------------------------------------------- #
# this repo's own tree is readable through the check
# --------------------------------------------------------------------------- #
def test_this_repos_backlog_reads_as_a_non_empty_id_set() -> None:
    """Guards the wiring end-to-end: the real directory, the real reader, and a
    set big enough that an accidental empty read would be obvious."""
    repo = Path(__file__).resolve().parents[2]
    ids = item_ids(repo / "docs" / "restructure" / "backlog")

    assert len(ids) > 50, "the producer backlog should be large — an empty read is the J26 trap"
    assert len(set(ids)) == len(ids), "duplicate id from the directory listing"


def test_the_rendered_block_is_pure_ascii(tmp_path: Path) -> None:
    """The skill tells a company session to PASTE this block into the port report,
    and PowerShell 5.1 mojibakes non-ASCII in console output — the documented
    PORT-REPORT-ae21ee4 trap, two sections above the step that runs this check. A
    corrupted paste is a silently wrong port report, so the block stays ASCII."""
    producer = _tree(tmp_path / "producer", ["A1", "A2", "A3"])
    consumer = _tree(tmp_path / "consumer", ["A1"])

    rendered = compare(
        producer, consumer, exclusions={"A3": "a written reason of adequate length here"}
    ).render()

    rendered.encode("ascii")  # raises UnicodeEncodeError if a smart dash creeps back in
