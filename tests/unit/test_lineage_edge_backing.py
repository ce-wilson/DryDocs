"""The swimlane's READS/WRITES edges must match what the vocabulary rules (O60).

WHY THIS GUARD EXISTS, and it is not the obvious reason. O60's acceptance said
the two data edges render dashed and marked planned "for as long as
``m3_reads_from`` / ``m3_writes_to`` carry status: planned". At build they carried
``deprecated``, superseded by ``scheduler_reads_from`` / ``scheduler_writes_to``,
and BOTH SUCCESSORS ARE ACTIVE — so the condition was false and the edges render
SOLID. The wireframe's own WF-DFL-14/15 labels still read "(planned)" and are
stale for the same reason.

That is the third time in one session an item's wording was overtaken by its
dependency (Idea-230's class). What makes this one different is that O60 phrased
the rule as a CONDITION ON THE DATA rather than as a flat instruction, so the
build could resolve it correctly instead of following stale wording. This guard
is what keeps that resolution honest afterwards: if the vocabulary ever changes
its mind, the view is wrong and this fails, naming the surface to fix.

WHAT IT DOES NOT DO: assert a loader writes these edges. Vocabulary status is a
RULING about whether the relationship is confirmed; whether any row exists is a
different question, answered by the load map and the graph. The swimlane draws
synthesized data, so what its solid strokes assert is that the relationship is
RULED — which is exactly what an active entry means.
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parents[2]
VOCAB_DIR = REPO / "drydocs_core" / "ontology" / "relationship_vocabulary"
DEMO = REPO / "web" / "src" / "lineage" / "demoSwimlane.ts"

#: The entries the surface names as its backing, and the status it claims for
#: each. Read from the view's own text below, so the two cannot disagree.
CLAIMED = {"scheduler_reads_from": "active", "scheduler_writes_to": "active"}

#: The superseded pair the acceptance's condition named. Kept here so the guard
#: fails loudly if either is ever revived rather than left deprecated.
SUPERSEDED = {"m3_reads_from", "m3_writes_to"}


def _entries() -> dict[str, dict]:
    """Every vocabulary entry with an id, flattened across the fragments."""
    found: dict[str, dict] = {}

    def walk(node: object) -> None:
        if isinstance(node, dict):
            entry_id = node.get("id")
            if isinstance(entry_id, str) and "status" in node:
                found[entry_id] = node
            for value in node.values():
                walk(value)
        elif isinstance(node, list):
            for value in node:
                walk(value)

    for path in VOCAB_DIR.glob("*.yaml"):
        walk(yaml.safe_load(path.read_text(encoding="utf-8")))
    return found


def test_the_entries_the_surface_names_exist_and_are_active() -> None:
    entries = _entries()
    for entry_id, expected in CLAIMED.items():
        assert entry_id in entries, (
            f"the swimlane cites vocabulary entry '{entry_id}', which no fragment declares — "
            "either the entry was renamed or the surface is citing something that never existed"
        )
        actual = entries[entry_id].get("status")
        assert actual == expected, (
            f"'{entry_id}' is now '{actual}', not '{expected}'. The /lineage swimlane draws this "
            "edge SOLID because the entry is active; if the ruling changed, the stroke and the "
            "caption in web/src/lineage/demoSwimlane.ts must change with it."
        )


def test_the_superseded_pair_is_still_superseded() -> None:
    """If m3_* were ever revived, the acceptance's original condition would be
    live again and the view's reasoning would need re-reading — not silently
    kept."""
    entries = _entries()
    for entry_id in SUPERSEDED:
        assert entries[entry_id].get("status") == "deprecated", (
            f"'{entry_id}' is no longer deprecated — O60's acceptance made the dashed/planned "
            "rendering conditional on this pair, so a change here reopens that decision"
        )


def test_the_surface_quotes_the_entry_ids_it_relies_on() -> None:
    """The claim is checkable by a reader only if the ids are on the page.

    Reads the demo module's EDGE_BACKING text; a surface that stopped naming its
    backing would leave the solid strokes unexplained.
    """
    text = DEMO.read_text(encoding="utf-8")
    for entry_id in CLAIMED:
        assert entry_id in text, f"the surface no longer names '{entry_id}' as its backing"
