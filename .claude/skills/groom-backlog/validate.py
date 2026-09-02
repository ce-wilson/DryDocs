"""Standalone backlog validator, and THE id allocator (I6).

Runs the same checks as tests/unit/test_backlog.py for environments where
poetry/pytest are not installed. If the two ever disagree, test_backlog.py wins.

Usage (from the repo root):
    python .claude/skills/groom-backlog/validate.py
    python .claude/skills/groom-backlog/validate.py --next-id G
    python .claude/skills/groom-backlog/validate.py --next-id Idea
    python .claude/skills/groom-backlog/validate.py --show-ids G

WHY THE ALLOCATOR LIVES HERE (I6). "Next free number in the matching epic's
letter" was a SENTENCE IN A SKILL FILE, and a sentence cannot look anywhere. It
has failed six times. The most recent: on 2026-08-29 one machine's O69 was
already pushed on a feature branch when the other minted its own -- and the
second machine never looked past its own working tree, because the rule never
said to. Free in MY tree is not free.

WHAT "FREE" MEANS HERE, and it is a UNION of three sources because no single one
of them is complete:

1. the local ``items/`` directory -- what this checkout holds;
2. every REMOTE REF's tree listing -- ``git ls-tree`` per ref, listing only, no
   checkout, cheap. This is the source the O69 collision needed and nobody read;
3. every id ever ADDED under ``items/`` across all refs in history -- so an id
   that was minted and later renumbered stays BURNED. G70 and G71 were forced to
   G75/G76 because ``config/gate-log.md`` cites ids inside SIGNED records; handing
   G70 out again would re-point a citation inside a signed-off gate.

Each source is genuinely load-bearing, which is not an assumption -- it was
measured while building this. O79 and O80 exist in the working tree and appear in
NEITHER history listing (they arrived through a re-mint rename), and burned ids
appear in history and in no tree at all. Any one source alone hands out a taken
number.

IT ANSWERS FOR THE IDEA INBOX TOO (``--next-id Idea``). Same collision, same
three-term union, and it is here rather than in a second place because the
inbox's own header table used to carry its own wording for "next free" -- which
is how one rule came to be written down in three documents with three shapes.

THE NUMBER IS MAX+1 AND NEVER THE LOWEST GAP. A gap is not evidence that a number
is free; it is usually evidence that a number was BURNED. Filling gaps is how a
signed gate record starts pointing at somebody else's item.

WHAT THIS DOES NOT CHANGE: the allocator BANDS (producer 1-9999, company 10000+,
tests/unit/test_backlog.py). Bands separate the two REPOS and always did their
job; they say nothing about two producer machines minting the same number in the
same band, which is exactly the gap this closes. The band guard is untouched.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
BACKLOG = REPO_ROOT / "docs" / "restructure" / "backlog"  # the sharded tree (ADR 0013)
AGENTS_DIR = REPO_ROOT / ".claude" / "agents"
ITEMS_REL = "docs/restructure/backlog/items"
IDEAS_REL = "docs/restructure/IDEAS.md"
MODULES_REL = "docs/restructure/backlog/modules.yaml"

#: An item id is an uppercase series prefix and a number: G129, MM4, DD7.
_ID_RE = re.compile(r"^(?P<series>[A-Z]+)(?P<number>\d+)$")
_FILE_RE = re.compile(r"(?P<id>[A-Z]+\d+)\.yaml$")

#: An inbox id: ``- **`Idea-207a`** ·``. Same collision problem, same fix, one
#: command -- the inbox's own header table used to carry its own wording for
#: "next free", which is how two documents came to state one rule differently.
#: The optional letter suffix is a SPLIT (Idea-205a/205b) and never a new number.
_IDEA_RE = re.compile(r"^- \*\*`Idea-(?P<number>\d+)[a-z]?`\*\* ·", re.M)

#: The same header, UNANCHORED, for reading `git log -p` output -- every line
#: there carries a diff marker, so the anchored pattern above matches nothing
#: and the history term silently returned zero. Found by the source counts
#: printing `history=0` next to `local=224`, which is why they are printed.
_IDEA_IN_DIFF_RE = re.compile(r"\*\*`Idea-(?P<number>\d+)[a-z]?`\*\*")

#: The pseudo-series that means the idea inbox rather than a backlog letter.
IDEA_SERIES = "IDEA"

#: Reserved for company-side-only items (cross-repo convention 2026-07-20,
#: git-readme.md). The allocator refuses it rather than leaving it to a reader.
RESERVED_SERIES = frozenset({"DD"})

#: THE LEGACY SERIES ARE FROZEN (ruling 2026-09-02, config/gate-log.md). The letter
#: was an epoch tag - it recorded WHEN a phase opened, not what an item is about -
#: and G alone had absorbed 136 items across six epics. Each series is frozen at
#: the highest number it had ever taken across local, every remote ref and history,
#: measured the day of the ruling; that number is a COMMITTED CONSTANT, never the
#: current max, because a computed floor rises with every new id and silently
#: re-legalizes the series (the band guard's own rule). No id moves: ids are join
#: keys and config/gate-log.md cites them inside signed records. New ids take the
#: MODULE code from modules.yaml `series:` - ``--next-id --module <module>``.
#: Duplicated in tests/unit/test_backlog.py DELIBERATELY, with a guard that the two
#: agree; the test wins if they ever differ.
FROZEN_ON = "2026-09-02"
FROZEN_SERIES: dict[str, int] = {
    "A": 4,
    "B": 5,
    "C": 44,
    "D": 11,
    "E": 2,
    "F": 2,
    "G": 136,
    "GN": 2,
    "H": 8,
    "I": 8,
    "J": 78,
    "K": 30,
    "L": 29,
    "M": 4,
    "MM": 14,
    "N": 28,
    "O": 92,
    "P": 6,
    "Q": 28,
    "R": 23,
    "S": 16,
    "U": 27,
    "V": 11,
    "W": 3,
    "X": 4,
    "Y": 7,
    "Z": 9,
}

#: Producer allocates at or below this in EVERY series; company is above it.
#: Duplicated from tests/unit/test_backlog.py DELIBERATELY -- this script runs
#: where pytest does not, which is its whole reason to exist. The test wins if
#: they ever disagree, and a guard there asserts the two agree.
PRODUCER_BAND_CEILING = 9999

STATUSES = {"todo", "in_progress", "blocked", "done"}
TYPES = {"requirement", "task", "chore", "bug"}
PRIORITIES = {"p0", "p1", "p2", "p3"}
MODELS = {"haiku", "sonnet", "opus", "fable"}  # keep in sync with test_backlog.py (it wins)
REQUIRED = (
    "id",
    "title",
    "type",
    "module",
    "phase",
    "epic",
    "agent",
    "model",
    "priority",
    "status",
    "depends_on",
    "acceptance",
)


# ---------------------------------------------------------------------------
# The allocator (I6).
# ---------------------------------------------------------------------------
def _git(*args: str) -> str:
    """Run git at the repo root. Returns "" on any failure, never raises.

    Silent failure is right HERE and nowhere else: this runs on a laptop with no
    network as readily as on one with a remote, and an allocator that crashed
    when a fetch failed would push people straight back to guessing -- which is
    the failure being fixed. The CALLER reports which sources answered, so a
    degraded run is visible rather than silent.
    """
    try:
        out = subprocess.run(
            ["git", *args],
            cwd=str(REPO_ROOT),
            capture_output=True,
            # UTF-8 EXPLICITLY, not text=True. text=True decodes with the LOCALE
            # codec, which on this desktop is cp1252 -- and every item file holds
            # em dashes, so `git show` of one raised UnicodeDecodeError inside a
            # reader thread. Found while building this, and it would have made the
            # allocator crash on the first non-ASCII item it read.
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
    except (OSError, subprocess.SubprocessError):
        return ""
    return out.stdout if out.returncode == 0 else ""


def _ids_from_names(blob: str) -> set[str]:
    return {m.group("id") for line in blob.splitlines() if (m := _FILE_RE.search(line.strip()))}


def local_ids() -> set[str]:
    """Ids in this checkout."""
    return {p.stem for p in (BACKLOG / "items").glob("*.yaml") if _ID_RE.match(p.stem)}


def remote_refs() -> list[str]:
    return [
        r.strip()
        for r in _git("for-each-ref", "--format=%(refname)", "refs/remotes/").splitlines()
        if r.strip()
    ]


def remote_ids(refs: list[str] | None = None) -> tuple[set[str], list[str]]:
    """``(ids, refs_read)`` from a TREE LISTING per remote ref -- no checkout.

    This is the source the O69 collision needed: the other machine's id was
    pushed on a feature branch, and nothing local could see it.
    """
    found: set[str] = set()
    read: list[str] = []
    for ref in refs if refs is not None else remote_refs():
        listing = _git("ls-tree", "-r", "--name-only", ref, "--", ITEMS_REL)
        if listing:
            found |= _ids_from_names(listing)
            read.append(ref)
    return found, read


def historical_ids() -> set[str]:
    """Every id ever ADDED under items/ on any ref -- the BURNED set.

    ``--no-renames`` on purpose: with rename detection a re-mint reports as R and
    the new id never appears as an add. It is still not complete on its own (O79
    and O80 are in the tree and in neither listing), which is why this is one
    term of a union and not the answer.
    """
    return _ids_from_names(
        _git(
            "log",
            "--all",
            "--no-renames",
            "--diff-filter=A",
            "--name-only",
            "--format=",
            "--",
            ITEMS_REL,
        )
    )


def _idea_numbers(text: str) -> set[int]:
    return {int(m.group("number")) for m in _IDEA_RE.finditer(text)}


def idea_ids() -> tuple[set[int], dict[str, int], list[str]]:
    """Every ``Idea-<n>`` ever allocated -- local file, remote refs, and history.

    Same three-term union as the backlog ids and for the same reason: the inbox
    is one file, so a remote branch that appended an entry is invisible to a
    local read, and an entry deleted in a merge is invisible to a tree read.
    """
    local_path = REPO_ROOT / IDEAS_REL
    local = _idea_numbers(local_path.read_text(encoding="utf-8")) if local_path.exists() else set()

    remote: set[int] = set()
    read: list[str] = []
    for ref in remote_refs():
        blob = _git("show", f"{ref}:{IDEAS_REL}")
        if blob:
            remote |= _idea_numbers(blob)
            read.append(ref)

    # Every revision of the file on any ref. One `git log -p` rather than a
    # rev-list plus a show per commit -- the inbox has hundreds of revisions and
    # a subprocess each would make the allocator too slow to bother running.
    diff = _git("log", "--all", "-p", "--format=", "--", IDEAS_REL)
    history = {int(m.group("number")) for m in _IDEA_IN_DIFF_RE.finditer(diff)}

    counts = {"local": len(local), "remote": len(remote), "history": len(history)}
    return local | remote | history, counts, read


def known_ids() -> tuple[set[str], dict[str, int], list[str]]:
    """``(ids, per_source_counts, refs_read)`` -- the union that defines "taken"."""
    local = local_ids()
    remote, refs = remote_ids()
    history = historical_ids()
    counts = {"local": len(local), "remote": len(remote), "history": len(history)}
    return local | remote | history, counts, refs


def module_series() -> dict[str, str]:
    """``module -> SERIES`` from modules.yaml ``series:`` - the ONLY source of a new series.

    Read from the file rather than embedded here so that registering a module and
    registering its series is one edit in one place, and the guard in
    tests/unit/test_backlog.py holds both to the same shape.
    """
    doc = yaml.safe_load((REPO_ROOT / MODULES_REL).read_text(encoding="utf-8")) or {}
    series = doc.get("series") or {}
    return {str(k): str(v).strip().upper() for k, v in series.items()}


def next_id(series: str, taken: set[str] | None = None) -> tuple[str, int]:
    """``(next_id, highest_taken)`` for ``series``. MAX+1, never the lowest gap."""
    series = series.strip().upper()
    if not series.isalpha():
        raise SystemExit(f"refused: {series!r} is not a series prefix (letters only)")
    if series in RESERVED_SERIES:
        raise SystemExit(
            f"refused: the {series}-series is reserved for company-side-only items "
            "(cross-repo convention 2026-07-20, git-readme.md)"
        )
    if series in FROZEN_SERIES:
        raise SystemExit(
            f"refused: the {series}-series was FROZEN on {FROZEN_ON} at "
            f"{series}{FROZEN_SERIES[series]} (config/gate-log.md). The letter was an epoch "
            "tag, not a topic. New ids take the module code: "
            "validate.py --next-id --module <module>"
        )
    codes = module_series()
    if series != IDEA_SERIES and series not in set(codes.values()):
        registered = ", ".join(f"{m}={c}" for m, c in sorted(codes.items()))
        raise SystemExit(
            f"refused: {series!r} is not a registered module series. A series comes from "
            f"docs/restructure/backlog/modules.yaml `series:`, never from a letter somebody "
            f"picks. Registered: {registered}"
        )
    pool = taken if taken is not None else known_ids()[0]
    numbers = [
        int(m.group("number"))
        for i in pool
        if (m := _ID_RE.match(i)) and m.group("series") == series
    ]
    highest = max(numbers, default=0)
    nxt = highest + 1
    if nxt > PRODUCER_BAND_CEILING:
        raise SystemExit(
            f"refused: {series}{nxt} is in the COMPANY band (>{PRODUCER_BAND_CEILING}). "
            "Producer allocates 1-9999 in every series."
        )
    return f"{series}{nxt}", highest


def _report_allocation(series: str, show_all: bool) -> int:
    # Fetch first: a stale remote-tracking ref is a ref that cannot see the id the
    # other machine pushed an hour ago, which is the whole failure.
    _git("fetch", "--all", "--quiet")
    all_refs = remote_refs()

    if series.strip().upper() == IDEA_SERIES:
        numbers, counts, refs = idea_ids()
        highest = max(numbers, default=0)
        label, allocated = "Idea", f"Idea-{highest + 1}"
        taken_in_series = sorted(numbers)
    else:
        taken, counts, refs = known_ids()
        allocated, highest = next_id(series, taken)
        label = series.strip().upper()
        taken_in_series = sorted(
            int(m.group("number"))
            for i in taken
            if (m := _ID_RE.match(i)) and m.group("series") == label
        )

    if not all_refs:
        print(
            "WARNING: this checkout has NO remote-tracking refs, so the answer below is "
            "LOCAL + HISTORY only -- the exact blind spot that produced the duplicate "
            "O69. Add a remote, or treat this number as provisional and re-check before "
            "you push the stub.",
            file=sys.stderr,
        )
    elif not refs:
        print(
            f"WARNING: {len(all_refs)} remote ref(s) exist and none could be read for "
            f"{label}. Either the fetch failed or every ref predates this surface; the "
            "answer below is local + history only.",
            file=sys.stderr,
        )

    print(f"next free: {allocated}")
    print(
        f"  highest {label} taken: {label}{'-' if label == 'Idea' else ''}{highest}"
        if highest
        else f"  no {label} id has ever been allocated"
    )
    print(
        f"  sources: local={counts['local']} remote={counts['remote']} "
        f"history={counts['history']}"
    )
    skipped = [r for r in all_refs if r not in refs]
    print(
        f"  remote refs read ({len(refs)} of {len(all_refs)}): "
        f"{', '.join(refs) if refs else 'NONE'}"
    )
    if skipped:
        print(f"  refs with nothing to read: {', '.join(skipped)}")
    print(
        "  MINT IT THE WAY A PULL IS CLAIMED: write the stub, commit and PUSH it, "
        "then write the body. An id that exists only in your tree is an id the other "
        "machine will mint too."
    )
    if show_all:
        gaps = [n for n in range(1, highest) if n not in set(taken_in_series)]
        print(f"  {label} allocated: {len(taken_in_series)}")
        joined = ", ".join(f"{label}{'-' if label == 'Idea' else ''}{n}" for n in gaps)
        print(f"  gaps (NOT free -- a gap is usually a BURNED id): {joined or 'none'}")
    return 0


def main() -> int:
    fails: list[str] = []
    sys.path.insert(0, str(REPO_ROOT))
    from drydocs_core.backlog_store import derive_summary, load_backlog_document

    doc = load_backlog_document(BACKLOG)

    if doc.get("schema") != "drydocs.backlog.v3":
        fails.append(f"schema drifted: {doc.get('schema')!r}")

    phases = doc.get("plan", {}).get("phases", [])
    pids: set[int] = set()
    for ph in phases:
        pid = ph.get("id")
        if not isinstance(pid, int) or pid in pids:
            fails.append(f"phase id problem: {pid!r}")
        pids.add(pid)
        for f in ("title", "goal"):
            if not ph.get(f):
                fails.append(f"phase {pid} missing {f}")
        if ph.get("status") not in STATUSES:
            fails.append(f"phase {pid} bad status {ph.get('status')!r}")

    modules = doc.get("modules", [])
    if not modules or len(modules) != len(set(modules)):
        fails.append("modules registry empty or has duplicates")

    agents = {p.stem for p in AGENTS_DIR.glob("*.md")} | {"main"}

    items = doc.get("items", [])
    by_id: dict[str, dict] = {}
    for it in items:
        iid = it.get("id", "<no-id>")
        if iid in by_id:
            fails.append(f"[{iid}] duplicate id")
        by_id[iid] = it
        for f in REQUIRED:
            if f not in it or it[f] in (None, ""):
                fails.append(f"[{iid}] missing required field '{f}'")
        for ok, msg in (
            (it.get("status") in STATUSES, f"status {it.get('status')!r}"),
            (it.get("type") in TYPES, f"type {it.get('type')!r}"),
            (it.get("priority") in PRIORITIES, f"priority {it.get('priority')!r}"),
            (it.get("model") in MODELS, f"model {it.get('model')!r}"),
            (it.get("agent") in agents, f"agent {it.get('agent')!r}"),
            (it.get("module") in set(modules), f"module {it.get('module')!r}"),
            (it.get("phase") in pids, f"phase {it.get('phase')!r}"),
            (isinstance(it.get("depends_on"), list), "depends_on (must be a list)"),
        ):
            if not ok:
                fails.append(f"[{iid}] bad {msg}")

    for iid, it in by_id.items():
        for dep in it.get("depends_on", []):
            if dep == iid or dep not in by_id:
                fails.append(f"[{iid}] bad dep {dep!r}")

    # cycle detection (DFS, three-color)
    white, gray, black = 0, 1, 2
    color = dict.fromkeys(by_id, white)

    def visit(node: str, path: list[str]) -> None:
        color[node] = gray
        for dep in by_id[node].get("depends_on", []):
            if color.get(dep) == gray:
                fails.append(f"dependency cycle: {' -> '.join([*path, node, dep])}")
            elif color.get(dep) == white:
                visit(dep, [*path, node])
        color[node] = black

    for iid in by_id:
        if color[iid] == white:
            visit(iid, [])

    # ADR 0013 Clause 3: nothing stores a roll-up; the derived one is printed so the
    # groomer can read next_ready without opening the board.
    derived = derive_summary(doc)
    for path in sorted(BACKLOG.rglob("*.yaml")):
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for key in ("summary", "next_ready", "updated"):
            if isinstance(d, dict) and key in d:
                fails.append(f"{path.name}: stored `{key}:` — roll-ups are derived, never stored")
    for path in (BACKLOG / "items").glob("*.yaml"):
        d = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        if d.get("id") != path.stem:
            fails.append(f"{path.name}: id {d.get('id')!r} != filename")
    print(
        "derived: "
        + " ".join(f"{k}={derived[k]}" for k in ("todo", "in_progress", "blocked", "done"))
        + f" next_ready={len(derived['next_ready'])}"
    )

    print(f"items={len(items)} phases={len(phases)} modules={len(modules)}")
    if fails:
        print(f"FAIL ({len(fails)}):")
        for f in fails:
            print(" -", f)
        return 1
    print("ALL CHECKS PASS")
    return 0


def _cli(argv: list[str]) -> int:
    if argv and argv[0] in ("--next-id", "--show-ids"):
        show = argv[0] == "--show-ids"
        rest = argv[1:]
        if rest and rest[0] == "--module":
            # The series is DERIVED from the module (ruling 2026-09-02): the groomer
            # names the module the item belongs to - a field every item already
            # carries - and never picks a letter.
            codes = module_series()
            if len(rest) < 2 or rest[1] not in codes:
                known = ", ".join(sorted(codes))
                raise SystemExit(
                    f"usage: validate.py {argv[0]} --module <module>   modules: {known}"
                )
            return _report_allocation(codes[rest[1]], show_all=show)
        if not rest:
            raise SystemExit(
                f"usage: validate.py {argv[0]} --module <module>   (a backlog item)"
                + chr(10)
                + f"       validate.py {argv[0]} Idea                (the idea inbox)"
            )
        return _report_allocation(rest[0], show_all=show)
    return main()


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
