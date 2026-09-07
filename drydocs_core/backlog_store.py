"""Y2 / ADR 0013 — the reader for the sharded backlog.

``docs/restructure/backlog.yaml`` (21k lines, 466 items) was the only claim channel
between two machines and, through the port, two repositories — and every claim
edited the same stored roll-up block at its foot. It is now a DIRECTORY::

    docs/restructure/backlog/
        plan.yaml          schema + plan.phases
        modules.yaml       the module census (test_runbook_coverage reads it)
        epics/<epic>.yaml  id, letter, title, order, groom_log[]  (Clause 2)
        items/<id>.yaml    one STANDALONE mapping per item       (Clause 1)

This module is the ONE reader. It assembles the same document shape the monolith
had (``schema`` / ``plan`` / ``modules`` / ``items`` — plus ``epics``) so every
consumer keeps reading a dict, and it derives the roll-ups (``derive_summary``)
that are no longer stored anywhere (Clause 3).

Order is a reader rule, not a storage fact (Clause 1): items come back sorted by
the epic's ``order`` then by NATURAL id (``C2`` before ``C10``), which is what the
board rendered from the monolith's append order.

Failure modes are loud, the L17 family and the S5 family:
- a missing directory, or one with no item files, raises — an empty backlog must
  never read as "no work, carry on";
- a duplicate mapping key inside any file raises (S5's loader — plain
  ``safe_load`` keeps the last duplicate silently);
- an item whose ``id`` differs from its filename raises — the path IS the identity;
- an item naming an epic with no ``epics/<epic>.yaml`` raises — a typo would
  otherwise mint a phantom epic on the board and in the graph (Y4).

Single FILES stay first-class inputs: ``load_backlog_document`` accepts a
monolith-shaped YAML file too, so tmp-path tests build one document and the
splitter's proof reads the retired monolith through the same call.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from drydocs_core.repo_paths import repo_root
from drydocs_core.yaml_fragments import _DuplicateKeySafeLoader

# Resolve the checkout the CALLER stands in, not the one this file was installed from
# (Idea-109): a worktree session must read ITS backlog and claim in ITS tree.
_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
DEFAULT_BACKLOG_DIR = _REPO_ROOT / "docs" / "restructure" / "backlog"

PLAN_FILE = "plan.yaml"
MODULES_FILE = "modules.yaml"
EPICS_DIR = "epics"
ITEMS_DIR = "items"

SCHEMA = "drydocs.backlog.v3"

#: Statuses the roll-up counts; the board's columns.
STATUSES: tuple[str, ...] = ("todo", "in_progress", "blocked", "done")

#: The one field the splitter ADDS to an item: inline YAML comments harvested from
#: the monolith (``status: done   # closed 2026-08-04 (desktop)`` and the like),
#: keyed by the field they annotated. Additive, informational, never required.
ANNOTATIONS_FIELD = "annotations"

#: The BLESSED HOLD (Y7, 2026-09-07; ADR 0013 Clause 3a). An optional ``hold:`` mapping
#: on an item says "the dependencies are done and you still may not pull this" - the
#: one thing ``depends_on`` cannot express, and the case it exists for (O26 was pulled
#: on 2026-09-02 because both its deps were done; the hold was in an annotation no
#: derivation read). The field is DECLARED so the guard tells a hold from a note
#: without reading English: ``since`` (the date it was placed) and ``reason`` (the
#: human's words, verbatim) are required; ``by`` (who placed it) and ``until`` (the
#: EVENT that releases it - a ruling, a session - never a date) are optional. A held
#: item stays ``todo`` (or ``blocked``): it is not blocked by a dependency and it is not
#: in progress, it is waiting on a human. Releasing a hold is DELETING the key, with
#: the ruling recorded in ``notes``.
#:
#: Deliberately NOT "block on any annotation" (Y7 b). Most annotations are notes, not
#: holds; a general rule would refuse items nobody meant to hold, and a false hold is
#: invisible in the other direction - an item that silently leaves the ready list
#: with no reason is worse than today. Only this key holds; ``annotations`` never does.
HOLD_FIELD = "hold"
HOLD_REQUIRED_KEYS: tuple[str, ...] = ("since", "reason")
HOLD_OPTIONAL_KEYS: tuple[str, ...] = ("by", "until")
#: A hold may sit on an item in exactly these statuses. On ``in_progress`` it means
#: somebody pulled past the hold; on ``done`` it is stale. Both are guard failures.
HOLD_ALLOWED_STATUSES: tuple[str, ...] = ("todo", "blocked")


def is_held(item: dict[str, Any]) -> bool:
    """True when the item carries a ``hold:`` mapping - the declared shape, nothing else.

    A ``hold: ~`` reads as no hold (the key was released in place); a hold that is not
    a mapping is malformed and :func:`hold_errors` reports it, but it still HOLDS - a
    malformed hold failing open would be the false-ready this field exists to close.
    """
    return item.get(HOLD_FIELD) is not None


def hold_errors(item: dict[str, Any]) -> list[str]:
    """Shape findings for one item's hold, empty when there is none or it is well-formed.

    One function for the validator and the unit guard, so the two cannot disagree on
    what a blessed hold looks like.
    """
    if not is_held(item):
        return []
    iid = str(item.get("id", "<no-id>"))
    hold = item[HOLD_FIELD]
    if not isinstance(hold, dict):
        return [f"[{iid}] hold must be a mapping with {'/'.join(HOLD_REQUIRED_KEYS)}"]
    errors: list[str] = []
    for key in HOLD_REQUIRED_KEYS:
        if hold.get(key) in (None, ""):
            errors.append(f"[{iid}] hold is missing `{key}`")
    unknown = sorted(set(hold) - set(HOLD_REQUIRED_KEYS) - set(HOLD_OPTIONAL_KEYS))
    if unknown:
        errors.append(f"[{iid}] hold carries unknown key(s) {unknown}")
    if str(item.get("status", "")) not in HOLD_ALLOWED_STATUSES:
        errors.append(
            f"[{iid}] hold on a {item.get('status')!r} item - "
            f"a hold sits only on {'/'.join(HOLD_ALLOWED_STATUSES)}"
        )
    return errors


class BacklogStoreError(RuntimeError):
    """The backlog directory is missing, malformed, or internally inconsistent."""


# --- parsing ----------------------------------------------------------------------


def _load_file(path: Path) -> Any:
    try:
        return yaml.load(path.read_text(encoding="utf-8"), Loader=_DuplicateKeySafeLoader)
    except yaml.YAMLError as exc:  # pragma: no cover - message path
        raise BacklogStoreError(f"{path}: {exc}") from exc
    except Exception as exc:  # FragmentSourceError on a duplicate key
        raise BacklogStoreError(f"{path}: {exc}") from exc


#: The id grammar, ``[<EDITION>-]<SERIES><n>`` (gate ontology-domain-registry-and-
#: edition-grain §C1; PLAN2): an optional 2-5 letter edition segment, the series, the
#: number. Uppercase only and NO letter suffix - the ``[a-z]`` split suffix is an
#: Idea-inbox shape and no item id has ever carried one (PLAN2 e ruled it). Duplicated
#: from the allocator (.claude/skills/groom-backlog/validate.py) DELIBERATELY: core
#: imports nothing from under .claude/, so tests/unit/test_backlog.py holds the two
#: parsers to one fixed list of ids that must parse identically.
_ID_RE = re.compile(r"^(?:(?P<edition>[A-Z]{2,5})-)?(?P<series>[A-Z]+)(?P<number>\d+)$")


def natural_id_key(item_id: str) -> tuple[str, str, int]:
    """``C2`` < ``C10``; base ids before edition ids; non-conforming ids after, by text.

    An id the grammar cannot parse sorts LAST as text, never silently among the
    conforming ones - before PLAN2 a segment id fell through here and sorted after
    every conforming id without anything saying so.
    """
    m = _ID_RE.match(str(item_id))
    if not m:
        return ("~", "~" + str(item_id), 0)
    return (m.group("edition") or "", m.group("series"), int(m.group("number")))


def item_paths(backlog_dir: Path) -> list[Path]:
    items_dir = backlog_dir / ITEMS_DIR
    if not items_dir.is_dir():
        raise BacklogStoreError(f"backlog items directory missing: {items_dir}")
    paths = sorted(items_dir.glob("*.yaml"))
    if not paths:
        raise BacklogStoreError(f"no item files in {items_dir} — an empty backlog is never silent")
    return paths


def load_epics(backlog_dir: Path) -> list[dict[str, Any]]:
    epics_dir = backlog_dir / EPICS_DIR
    if not epics_dir.is_dir():
        raise BacklogStoreError(f"backlog epics directory missing: {epics_dir}")
    epics: list[dict[str, Any]] = []
    for path in sorted(epics_dir.glob("*.yaml")):
        doc = _load_file(path)
        if not isinstance(doc, dict) or doc.get("id") != path.stem:
            raise BacklogStoreError(
                f"{path}: epic file must be a mapping whose `id` equals the filename"
            )
        epics.append(doc)
    epics.sort(key=lambda e: (int(e.get("order", 10**6)), str(e["id"])))
    return epics


def load_items(backlog_dir: Path, epic_order: dict[str, int] | None = None) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for path in item_paths(backlog_dir):
        doc = _load_file(path)
        if not isinstance(doc, dict) or "id" not in doc:
            raise BacklogStoreError(f"{path}: item file must be a mapping with an `id`")
        if str(doc["id"]) != path.stem:
            raise BacklogStoreError(
                f"{path}: `id: {doc['id']}` does not match the filename — the path is the identity"
            )
        if epic_order is not None and doc.get("epic") not in epic_order:
            raise BacklogStoreError(
                f"{path}: epic {doc.get('epic')!r} has no epics/<epic>.yaml — a typo would mint a phantom epic"
            )
        items.append(doc)
    if epic_order is None:
        items.sort(key=lambda i: natural_id_key(i["id"]))
    else:
        items.sort(key=lambda i: (epic_order[i["epic"]], natural_id_key(i["id"])))
    return items


def load_backlog_document(source: str | Path = DEFAULT_BACKLOG_DIR) -> dict[str, Any]:
    """The assembled document: ``schema`` / ``plan`` / ``modules`` / ``epics`` / ``items``.

    A FILE path is read as one monolith-shaped document (tests, the retired
    monolith under the splitter's proof). A DIRECTORY is assembled.
    """
    source = Path(source)
    if source.is_file():
        doc = _load_file(source)
        if not isinstance(doc, dict):
            raise BacklogStoreError(f"{source}: expected a mapping document")
        return doc
    if not source.is_dir():
        raise BacklogStoreError(f"backlog source not found: {source}")

    plan_path = source / PLAN_FILE
    modules_path = source / MODULES_FILE
    if not plan_path.is_file():
        raise BacklogStoreError(f"missing {plan_path}")
    if not modules_path.is_file():
        raise BacklogStoreError(f"missing {modules_path}")
    plan_doc = _load_file(plan_path) or {}
    modules_doc = _load_file(modules_path) or {}
    if not isinstance(plan_doc, dict) or "plan" not in plan_doc:
        raise BacklogStoreError(f"{plan_path}: expected `schema:` and `plan:`")
    if not isinstance(modules_doc, dict) or not isinstance(modules_doc.get("modules"), list):
        raise BacklogStoreError(f"{modules_path}: expected `modules:` list")

    epics = load_epics(source)
    epic_order = {str(e["id"]): idx for idx, e in enumerate(epics)}
    items = load_items(source, epic_order)

    doc: dict[str, Any] = {
        "schema": plan_doc.get("schema", SCHEMA),
        "plan": plan_doc["plan"],
        "modules": modules_doc["modules"],
        "epics": epics,
        "items": items,
    }
    for key in ("summary", "updated"):
        if key in plan_doc:
            raise BacklogStoreError(
                f"{plan_path}: `{key}:` is not stored any more (ADR 0013 Clause 3) — derive it"
            )
    return doc


# --- derived roll-ups (Clause 3) ----------------------------------------------------


def derive_summary(doc: dict[str, Any]) -> dict[str, Any]:
    """Counts per status + ``next_ready`` + ``held`` — computed, never stored.

    ``next_ready`` = every ``todo`` item whose every ``depends_on`` is ``done`` and
    that carries no ``hold:`` (Y7), in document order. ``held`` = every item that
    carries one, in document order - rendered, never dropped, because the point of a
    hold is that a human wrote down why. Prose preconditions in an item's notes or
    annotations are NOT consulted; only the blessed field holds.

    This is THE rule. The board, the validator and the lane-handoff script all call
    it, so the Ready-to-pull strip and the derived list cannot disagree.
    """
    items = doc.get("items") or []
    by_id = {str(i["id"]): i for i in items}
    counts = {s: 0 for s in STATUSES}
    for i in items:
        s = str(i.get("status", ""))
        if s in counts:
            counts[s] += 1
    next_ready = [
        str(i["id"])
        for i in items
        if i.get("status") == "todo"
        and not is_held(i)
        and all(by_id.get(str(d), {}).get("status") == "done" for d in (i.get("depends_on") or []))
    ]
    held = [str(i["id"]) for i in items if is_held(i)]
    return {**counts, "next_ready": next_ready, "held": held}


# --- a file-shaped view (the reconcile-port before/after snapshot) ------------------


class _Dumper(yaml.SafeDumper):
    pass


def _str_presenter(dumper: yaml.SafeDumper, data: str):
    if "\n" in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


_Dumper.add_representer(str, _str_presenter)


def dump_yaml(obj: Any) -> str:
    """Deterministic YAML: insertion order kept, multi-line strings as literal blocks."""
    return yaml.dump(
        obj,
        Dumper=_Dumper,
        sort_keys=False,
        allow_unicode=True,
        width=100,
        default_flow_style=False,
    )


def dump_document(source: str | Path = DEFAULT_BACKLOG_DIR) -> str:
    """The assembled document as one YAML text — what the reconcile-port step snapshots
    to ``<before-dir>/backlog.yaml`` so the status-regression guard stays file-shaped
    (the S5 precedent: the merged document is what the guard compares)."""
    return dump_yaml(load_backlog_document(source))
