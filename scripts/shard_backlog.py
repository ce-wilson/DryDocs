"""shard_backlog.py — the one-shot splitter for docs/restructure/backlog.yaml (Y2, ADR 0013).

Reads the monolith, writes the sharded tree beside it, PROVES the tree assembles
back to the monolith entry-for-entry, and only then (``--tombstone``) replaces the
monolith with a short pointer file. It is idempotent on an already-sharded tree
and it ports AS CODE (ADR 0013 Clause 6): the company runs it on its OWN
per-entry-unioned monolith at the first port after Y2 — never receives the tree.

    poetry run python scripts/shard_backlog.py                 # write + prove
    poetry run python scripts/shard_backlog.py --prove-only    # proof against an existing tree
    poetry run python scripts/shard_backlog.py --tombstone     # write + prove + tombstone

What the proof checks (Clause 5, the S5 pattern at d84d86bc):
  * every item in the tree deep-equals its monolith entry, field for field, once
    the ONE additive field (``annotations``: harvested inline comments) is removed;
  * ``annotations`` equals exactly what was harvested — nothing invented;
  * ``plan`` and ``modules`` are identical; the item ID SET is identical;
  * the derived summary equals the monolith's stored ``summary`` counts and
    ``next_ready`` set (the only block that is not carried — it is re-derived).
Epic header comment blocks are attached to the epic of the first item that follows
them (Clause 2) and the block -> epic mapping is printed for review.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from drydocs_core.backlog_store import (
    ANNOTATIONS_FIELD,
    EPICS_DIR,
    ITEMS_DIR,
    MODULES_FILE,
    PLAN_FILE,
    SCHEMA,
    derive_summary,
    dump_yaml,
    load_backlog_document,
)

REPO = Path(__file__).resolve().parent.parent
MONOLITH = REPO / "docs" / "restructure" / "backlog.yaml"
TREE = REPO / "docs" / "restructure" / "backlog"

TOMBSTONE = """\
# TOMBSTONE — docs/restructure/backlog.yaml was sharded on {date} (Y2, ADR 0013).
#
# The backlog now lives in docs/restructure/backlog/ — one item per file under
# items/<id>.yaml, epics under epics/, plan.yaml + modules.yaml. Read it through
# drydocs_core.backlog_store.load_backlog_document(); roll-ups are DERIVED by
# render_board.py, never stored. A claim is a one-key edit of one item file.
#
# This file must never grow an `items:` key again (tests/unit/test_backlog.py).
schema: drydocs.backlog.tombstone
sharded_on: "{date}"
see: docs/decisions/0013-backlog-sharding.md
"""

# --- harvesting the monolith's comments -------------------------------------------

_ITEM_START = re.compile(r"^  - id: (\S+)\s*$")
_FIELD_INLINE = re.compile(r"^    ([a-z_]+): (.*?)\s+# (.*)$")
_LIST_INLINE = re.compile(r"^      - (.*?)\s+# (.*)$")
_BLOCK_COMMENT = re.compile(r"^  # ?(.*)$")


def harvest(monolith_text: str) -> tuple[dict[str, dict[str, Any]], list[tuple[str, str]]]:
    """Return (annotations per item id, [(first-following-item-id, header block text)])."""
    lines = monolith_text.split("\n")
    try:
        start = lines.index("items:")
    except ValueError as exc:
        raise SystemExit("monolith has no `items:` key — already sharded?") from exc

    annotations: dict[str, dict[str, Any]] = {}
    headers: list[tuple[str, str]] = []
    pending_block: list[str] = []
    current: str | None = None
    current_field: str | None = None
    for line in lines[start + 1 :]:
        if line.startswith("summary:"):
            break
        m = _ITEM_START.match(line)
        if m:
            current = m.group(1)
            current_field = None
            if pending_block:
                headers.append((current, "\n".join(pending_block).strip("\n")))
                pending_block = []
            continue
        bm = _BLOCK_COMMENT.match(line)
        if bm and not line.startswith("    "):
            pending_block.append(bm.group(1).rstrip())
            continue
        if line.strip() == "" and pending_block:
            pending_block.append("")
            continue
        if current is None:
            continue
        fm = _FIELD_INLINE.match(line)
        if fm and not fm.group(2).startswith(('"', "'")) and not fm.group(2).startswith(">"):
            current_field = fm.group(1)
            annotations.setdefault(current, {})[current_field] = fm.group(3).strip()
            continue
        if re.match(r"^    [a-z_]+:", line):
            current_field = line[4:].split(":", 1)[0]
            continue
        lm = _LIST_INLINE.match(line)
        if lm and current_field:
            key = f"{current_field}[]"
            annotations.setdefault(current, {}).setdefault(key, []).append(
                f"{lm.group(1).strip()} — {lm.group(2).strip()}"
            )
    return annotations, headers


# --- writing the tree ---------------------------------------------------------------


def epic_letter(items: list[dict[str, Any]]) -> str:
    letters = {re.match(r"^([A-Za-z]+)", str(i["id"])).group(1) for i in items}  # type: ignore[union-attr]
    return "/".join(sorted(letters))


def write_tree(
    doc: dict[str, Any], annotations: dict, headers: list[tuple[str, str]], date: str
) -> None:
    items = doc["items"]
    (TREE / ITEMS_DIR).mkdir(parents=True, exist_ok=True)
    (TREE / EPICS_DIR).mkdir(parents=True, exist_ok=True)

    # plan + modules
    plan_doc = {"schema": SCHEMA, "plan": doc["plan"]}
    (TREE / PLAN_FILE).write_text(dump_yaml(plan_doc), encoding="utf-8", newline="\n")
    (TREE / MODULES_FILE).write_text(
        dump_yaml({"modules": doc["modules"]}), encoding="utf-8", newline="\n"
    )

    # epics: first-appearance order; header blocks attach to the epic of the item that follows
    epic_first: dict[str, int] = {}
    epic_items: dict[str, list[dict[str, Any]]] = {}
    for idx, it in enumerate(items):
        epic_first.setdefault(it["epic"], idx)
        epic_items.setdefault(it["epic"], []).append(it)
    item_epic = {str(i["id"]): i["epic"] for i in items}
    groom_logs: dict[str, list[dict[str, str]]] = {}
    for item_id, block in headers:
        ep = item_epic[item_id]
        dm = re.search(r"(\d{4}-\d{2}-\d{2})", block)
        groom_logs.setdefault(ep, []).append(
            {"date": dm.group(1) if dm else "", "note": block, "attached_at": item_id}
        )
    title_re = re.compile(r"Epic [A-Z]+ — ([^—(\n]+?)\s*(?:\(|—|$)")
    for order, (ep, _) in enumerate(sorted(epic_first.items(), key=lambda kv: kv[1])):
        title = ep.replace("-", " ")
        for entry in groom_logs.get(ep, []):
            tm = title_re.search(entry["note"])
            if tm:
                title = tm.group(1).strip()
                break
        epic_doc: dict[str, Any] = {
            "id": ep,
            "letter": epic_letter(epic_items[ep]),
            "title": title,
            "order": order,
            "groom_log": groom_logs.get(ep, []),
        }
        (TREE / EPICS_DIR / f"{ep}.yaml").write_text(
            dump_yaml(epic_doc), encoding="utf-8", newline="\n"
        )

    # items
    for it in items:
        out = dict(it)
        ann = annotations.get(str(it["id"]))
        if ann:
            out[ANNOTATIONS_FIELD] = ann
        (TREE / ITEMS_DIR / f"{it['id']}.yaml").write_text(
            dump_yaml(out), encoding="utf-8", newline="\n"
        )

    readme = TREE / "README.md"
    if not readme.exists():
        readme.write_text(
            "# The sharded backlog (ADR 0013)\n\n"
            "One item per file under `items/<id>.yaml`; epics under `epics/`; `plan.yaml` and "
            "`modules.yaml` carry what the monolith held outside `items:`. Read it through "
            "`drydocs_core.backlog_store.load_backlog_document()`. Roll-ups (counts, "
            "`next_ready`) are derived by `scripts/render_board.py` and never stored.\n\n"
            "**Claiming work:** edit `status:` in the one item file, commit, push — before "
            "starting. Two machines claiming different items no longer touch a shared line; "
            "the same item is one small git conflict resolved by *status never regresses*. "
            "Across repos (a port) status is per-repo — see ADR 0013 Clause 4.\n\n"
            f"Sharded from `backlog.yaml` on {date} by `scripts/shard_backlog.py` "
            "(entry-level deep-equality proof run before the tombstone).\n",
            encoding="utf-8",
            newline="\n",
        )


# --- the proof -----------------------------------------------------------------------


def prove(monolith_doc: dict[str, Any], annotations: dict) -> list[str]:
    tree_doc = load_backlog_document(TREE)
    failures: list[str] = []
    mono_items = {str(i["id"]): i for i in monolith_doc["items"]}
    tree_items = {str(i["id"]): i for i in tree_doc["items"]}
    if set(mono_items) != set(tree_items):
        failures.append(
            f"id set differs: only-monolith={sorted(set(mono_items) - set(tree_items))} "
            f"only-tree={sorted(set(tree_items) - set(mono_items))}"
        )
    for iid, mi in mono_items.items():
        ti = dict(tree_items.get(iid) or {})
        ann = ti.pop(ANNOTATIONS_FIELD, None)
        if ti != mi:
            diff = {k for k in set(ti) | set(mi) if ti.get(k) != mi.get(k)}
            failures.append(f"{iid}: fields differ: {sorted(diff)}")
        if (ann or None) != (annotations.get(iid) or None):
            failures.append(f"{iid}: annotations do not equal the harvested comments")
    if tree_doc["plan"] != monolith_doc["plan"]:
        failures.append("plan differs")
    if tree_doc["modules"] != monolith_doc["modules"]:
        failures.append("modules differ")
    stored = monolith_doc.get("summary") or {}
    derived = derive_summary(tree_doc)
    for key in ("todo", "in_progress", "blocked", "done"):
        if key in stored and stored[key] != derived[key]:
            failures.append(f"summary.{key}: stored {stored[key]} vs derived {derived[key]}")
    if "next_ready" in stored and set(stored["next_ready"]) != set(derived["next_ready"]):
        failures.append(
            f"next_ready: stored-only={sorted(set(stored['next_ready']) - set(derived['next_ready']))} "
            f"derived-only={sorted(set(derived['next_ready']) - set(stored['next_ready']))}"
        )
    # every epic referenced has a file; every epic file has items
    tree_epics = {e["id"] for e in tree_doc["epics"]}
    used = {i["epic"] for i in tree_doc["items"]}
    if tree_epics != used:
        failures.append(f"epic files vs used: {sorted(tree_epics ^ used)}")
    return failures


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--monolith", type=Path, default=MONOLITH)
    ap.add_argument("--date", required=True, help="YYYY-MM-DD stamped in the epic files and README")
    ap.add_argument("--prove-only", action="store_true")
    ap.add_argument("--tombstone", action="store_true")
    args = ap.parse_args(argv)

    text = args.monolith.read_text(encoding="utf-8")
    if "schema: drydocs.backlog.tombstone" in text:
        print("monolith is already a tombstone — nothing to do")
        return 0
    monolith_doc = yaml.safe_load(text)
    annotations, headers = harvest(text)

    if not args.prove_only:
        write_tree(monolith_doc, annotations, headers, args.date)
        print(f"wrote {len(monolith_doc['items'])} items, {len(headers)} header blocks attached:")
        for iid, block in headers:
            first = block.strip().split("\n")[0][:70]
            print(f"  -> before {iid:6s} {first}")

    failures = prove(monolith_doc, annotations)
    if failures:
        print("PROOF FAILED:")
        for f in failures:
            print("  ", f)
        return 1
    n = len(monolith_doc["items"])
    print(f"PROOF OK: {n} items deep-equal; plan/modules identical; derived summary == stored")

    if args.tombstone:
        args.monolith.write_text(TOMBSTONE.format(date=args.date), encoding="utf-8", newline="\n")
        print(f"tombstoned {args.monolith}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
