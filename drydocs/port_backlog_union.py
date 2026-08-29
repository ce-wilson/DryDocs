"""port_backlog_union.py — J42: prove a port dropped no backlog item.

PORT-MANIFEST.yaml has promised the union rule for the backlog since the file
existed — today at file grain, for ``docs/restructure/backlog/items/*.yaml``:
*"Never drop a file; never regress a status"* (F4 ruling 2026-08-20). Plenty
enforces the backlog's INTERNAL consistency — schema, roll-up arithmetic,
``next_ready``, unknown ``depends_on`` — but every one of those checks reads ONE
copy. The union is a claim about TWO copies and nothing compared them, so a port
that quietly under-delivered items left both sides internally consistent and
green. Textbook J26: a rule written in prose and enforced by nobody. The near
miss that makes it worse — the dependency guard would have caught a gap only if
a SURVIVING item happened to depend on a missing one, so whether the gap was
visible at all was luck rather than design.

WHICH TWO TREES, and it is deliberately asymmetric:

* **producer** — the backlog as it stood at the RECORDED PORT BASE, read from a
  git ref (the ``port-base-YYYYMMDD`` tag the reconcile skill insists on). Not
  ``HEAD``: producer HEAD moves while a company session reads it, and commits
  past the tag ride the NEXT port, so counting them as missing would fail a port
  for being correct.
* **consumer** — the POST-APPLY WORKING TREE. That is the operationally
  meaningful question: did *this* port, as applied, under-deliver? Pointing both
  sides at refs would compare two archives and never look at what landed.

THE VACUOUS-GREEN TRAP, which is why this module refuses a file path outright.
``docs/restructure/backlog.yaml`` is a TOMBSTONE (sharded 2026-08-20, Y2 /
ADR 0013) and carries no ``items`` key at all. A check aimed there would read
two empty sets, report "no difference" and pass FOR BEING WRONG — the very J26
class this exists to close. So: the id set is THE DIRECTORY LISTING (Clause 6:
the entry IS the file), both sides are read by the SAME reader —
``drydocs_core.backlog_store.load_items`` — and an absent or empty items
directory FAILS LOUD rather than reading as agreement. ``load_items`` also
rejects a filename whose stem disagrees with the ``id`` inside it, which matters
here beyond tidiness: under Clause 6 a mismatch means the set being diffed is
not the set that exists.

SCOPE FENCE: this owns the UNION half only — never-drop-an-entry. The
never-regress-a-status half of the same manifest row belongs to the J16 guard in
``tests/unit/test_port_reconcile_guards.py``, which reads the assembled tree
through ``backlog_store.dump_document()``. Nothing here compares a status, and
nothing here touches ``RECONCILE_BEFORE_DIR`` — this check takes explicit paths
and refs.

Pure functions take DIRECTORIES, never a repository; only
:func:`materialize_ref` and :func:`run_union_check` shell out (the
``port_preflight.py`` idiom, so the guards exercise the logic without a git
tree).
"""

from __future__ import annotations

import subprocess
import tarfile
from dataclasses import dataclass
from pathlib import Path

from drydocs_core.backlog_store import ITEMS_DIR, BacklogStoreError, load_items, natural_id_key

#: The backlog tree, relative to a repo root — the path materialized from a ref.
BACKLOG_PATH = "docs/restructure/backlog"
ITEMS_PATH = f"{BACKLOG_PATH}/{ITEMS_DIR}"

#: Ids the CONSUMER deliberately does not carry, each with its reason (the
#: ``SCHEDULED_INGEST_EXCLUSIONS`` idiom). Without this, "no difference" and "a
#: difference somebody accepted" both render as silence, and the second one
#: quietly becomes the first. An entry must name an id the PRODUCER has and the
#: CONSUMER does not — a stale or contradictory allowance fails the check rather
#: than excusing anything. Empty today: no port has yet ruled an item
#: producer-only.
UNION_EXCLUSIONS: dict[str, str] = {}


class BacklogUnionError(RuntimeError):
    """A side could not be read at all — never a silent empty set."""


@dataclass(frozen=True)
class UnionReport:
    """The answer, with accepted differences kept distinct from silence."""

    producer_ids: tuple[str, ...]
    consumer_ids: tuple[str, ...]
    #: producer-minus-consumer with NO written allowance — the failure
    missing: tuple[str, ...]
    #: producer-minus-consumer somebody ruled: (id, reason)
    accepted: tuple[tuple[str, str], ...]
    #: consumer-only ids — reported, never a failure (the company plans its own
    #: work in the same id space; the manifest's union rule is one-directional)
    consumer_only: tuple[str, ...]
    #: allow-list entries that do not describe reality: (id, what is wrong)
    stale_exclusions: tuple[tuple[str, str], ...]

    @property
    def passed(self) -> bool:
        return not self.missing and not self.stale_exclusions

    def render(self) -> str:
        """The port-report block. States the accepted differences even when the
        gap is empty — a ruled omission must never read the same as no omission."""
        lines = [
            "BACKLOG UNION CHECK (J42) -- producer base vs the applied consumer tree",
            f"  producer items: {len(self.producer_ids)}",
            f"  consumer items: {len(self.consumer_ids)}",
        ]
        if self.missing:
            lines.append(f"  MISSING FROM THE CONSUMER ({len(self.missing)}) -- the port dropped:")
            lines.extend(f"    - {item_id}" for item_id in self.missing)
        else:
            lines.append("  missing from the consumer: none")
        if self.accepted:
            lines.append(f"  accepted differences ({len(self.accepted)}) -- ruled, not dropped:")
            lines.extend(f"    - {item_id}: {reason}" for item_id, reason in self.accepted)
        else:
            lines.append("  accepted differences: none declared")
        if self.consumer_only:
            lines.append(
                f"  consumer-only ({len(self.consumer_only)}) -- the company's own work, "
                "not a gap: " + ", ".join(self.consumer_only)
            )
        if self.stale_exclusions:
            lines.append(f"  UNUSABLE ALLOW-LIST ENTRIES ({len(self.stale_exclusions)}):")
            lines.extend(f"    - {item_id}: {why}" for item_id, why in self.stale_exclusions)
        lines.append("  RESULT: " + ("PASS" if self.passed else "FAIL"))
        if not self.passed:
            lines.append(
                "  A dropped item is a port defect, not a consumer decision. Restore each "
                "file from the producer base, or add its id to "
                "drydocs.port_backlog_union.UNION_EXCLUSIONS with the reason it stays behind."
            )
        return "\n".join(lines)


def item_ids(backlog_dir: Path) -> tuple[str, ...]:
    """Every item id in ONE backlog tree, from the directory listing.

    ``backlog_dir`` is the ``docs/restructure/backlog`` DIRECTORY. A file path is
    refused before anything is read: the only file anyone would plausibly pass is
    the tombstone monolith, and reading it would produce the empty set that
    passes for being wrong.

    Reads through :func:`drydocs_core.backlog_store.load_items`, which is where
    the fail-loud behavior this check depends on already lives — missing items
    directory, empty items directory, and a filename whose stem disagrees with
    the ``id`` inside it are all errors there, and are re-raised here as
    :class:`BacklogUnionError` naming the side that could not be read.
    """
    if backlog_dir.is_file():
        raise BacklogUnionError(
            f"{backlog_dir} is a FILE — the backlog is sharded (ADR 0013 Clause 6: the "
            "entry is the file), so this check takes the backlog DIRECTORY. "
            "docs/restructure/backlog.yaml is a tombstone with no items key: reading it "
            "would compare two empty sets and pass for being wrong (J26)."
        )
    try:
        # epic_order=None: ids only, so an epic file the other side has not got
        # must not fail the union check — that is a different rule's business.
        items = load_items(backlog_dir, epic_order=None)
    except BacklogStoreError as exc:
        raise BacklogUnionError(f"unreadable backlog at {backlog_dir}: {exc}") from exc
    return tuple(str(item["id"]) for item in items)


def compare(
    producer_dir: Path,
    consumer_dir: Path,
    exclusions: dict[str, str] | None = None,
) -> UnionReport:
    """Diff two backlog trees' id sets. Pure: two directories, no repository."""
    allowed = UNION_EXCLUSIONS if exclusions is None else exclusions
    producer = item_ids(producer_dir)
    consumer = item_ids(consumer_dir)
    producer_set, consumer_set = set(producer), set(consumer)

    gap = producer_set - consumer_set
    missing = sorted(gap - set(allowed), key=natural_id_key)
    accepted = sorted(
        ((item_id, allowed[item_id]) for item_id in gap & set(allowed)),
        key=lambda pair: natural_id_key(pair[0]),
    )

    # Allow-list hygiene, checked HERE rather than in a test, so a consumer repo
    # gets it from its own trees: an allowance for an id the producer never had
    # is stale, and one for an id the consumer DOES have never described a drop.
    stale: list[tuple[str, str]] = []
    for item_id, reason in sorted(allowed.items(), key=lambda pair: natural_id_key(pair[0])):
        if item_id not in producer_set:
            stale.append((item_id, "the producer base has no such item — stale allowance"))
        elif item_id in consumer_set:
            stale.append((item_id, "the consumer HAS this item — it was never dropped"))
        elif len(str(reason).split()) < 5:
            stale.append((item_id, f"the reason must be a sentence, not {reason!r}"))

    return UnionReport(
        producer_ids=producer,
        consumer_ids=consumer,
        missing=tuple(missing),
        accepted=tuple(accepted),
        consumer_only=tuple(sorted(consumer_set - producer_set, key=natural_id_key)),
        stale_exclusions=tuple(stale),
    )


def materialize_ref(ref: str, dest: Path, *, repo: Path, path: str = BACKLOG_PATH) -> Path:
    """Extract ``path`` at ``ref`` into ``dest``; return the extracted directory.

    ``git archive`` rather than a checkout, so the producer side is read WITHOUT
    touching the consumer's working tree mid-reconcile. A ref that does not carry
    the path makes git fail, and that failure is surfaced: it is the absent-tree
    FAIL case arriving through git, and swallowing it into an empty set is the
    vacuous green this module exists to prevent.
    """
    dest.mkdir(parents=True, exist_ok=True)
    archive = dest / "_backlog.tar"
    result = subprocess.run(
        ["git", "archive", "--format=tar", "-o", str(archive), ref, "--", path],
        cwd=str(repo),
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise BacklogUnionError(
            f"could not read {path!r} at ref {ref!r} in {repo}: "
            f"{(result.stderr or result.stdout).strip()} — an unreadable producer side is a "
            "FAILURE, never an empty set (fetch the producer remote and name the "
            "port-base tag, not HEAD)."
        )
    with tarfile.open(archive) as tar:
        tar.extractall(dest)
    archive.unlink()
    extracted = dest / path
    if not extracted.is_dir():
        raise BacklogUnionError(
            f"ref {ref!r} produced no {path!r} directory — the producer base has no backlog "
            "tree to union against."
        )
    return extracted


def run_union_check(
    *,
    producer_ref: str,
    consumer_dir: Path,
    workdir: Path,
    repo: Path,
) -> UnionReport:
    """Materialize the producer base, then compare it with the applied tree."""
    producer_dir = materialize_ref(producer_ref, workdir, repo=repo)
    return compare(producer_dir, consumer_dir)
