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
    """Counts per status + ``next_ready`` — computed, never stored.

    ``next_ready`` = every ``todo`` item whose every ``depends_on`` is ``done``,
    in document order. Prose preconditions in an item's notes are NOT consulted;
    the claim commit is where a human reads them.
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
        and all(by_id.get(str(d), {}).get("status") == "done" for d in (i.get("depends_on") or []))
    ]
    return {**counts, "next_ready": next_ready}


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
