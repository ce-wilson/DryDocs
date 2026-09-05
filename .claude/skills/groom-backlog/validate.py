"""Standalone backlog validator, and THE id allocator (I6).

Runs the same checks as tests/unit/test_backlog.py for environments where
poetry/pytest are not installed. If the two ever disagree, test_backlog.py wins.

Usage (from the repo root):
    python .claude/skills/groom-backlog/validate.py
    python .claude/skills/groom-backlog/validate.py --next-id --module drydocs-load
    python .claude/skills/groom-backlog/validate.py --next-id Idea
    python .claude/skills/groom-backlog/validate.py --next-id --module drydocs-load --edition XMPL
    python .claude/skills/groom-backlog/validate.py --show-ids --module drydocs-load

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

THE VENUE IS AN EDITION SEGMENT, NOT A NUMBER BAND (PLAN2, 2026-09-05; gate
ontology-domain-registry-and-edition-grain §C1/§C4 and its rider idea-series-grammar).
Until then the two REPOS were partitioned by NUMBER -- producer 1-9999, company
10000+ -- and the DD-series was the company's reserve. Both rules RETIRED
FORWARD-ONLY: they govern no new mint, and every id they produced stays exactly
where it is (ids are join keys; config/gate-log.md cites them inside signed
records). The grammar is now ``[<EDITION>-]<MODULE><n>`` and
``[<EDITION>-]Idea-<n>``, edition first, the BASE edition unprefixed, so every
existing id parses unchanged. Which edition a new id belongs to is DECLARED, never
inferred: ``config/dev-environment.yaml`` ``edition:`` says what venue this
checkout runs as (``base`` on the producer; the company's own code on the company,
minted at its own gate into ``config/taxonomy/editions.yaml``). ``.claude/**`` is
canonical-producer, so the company runs THIS file -- and once the band is gone
nothing but that key tells it which venue it is in. A venue that declares no
``edition:`` mints no ITEM id (the refusal names the key); it may still capture an
IDEA, band-shaped, until it declares (rider C1: a capture surface never refuses a
capture). ``--edition <code>`` overrides DOWNWARD only: a base may mint for an
edition it hosts; an instance never mints for its base or for a sibling.
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
#: The VENUE file (PLAN2 b): canonical-company in PORT-MANIFEST.yaml, so each side
#: holds its own copy and the `edition:` key is the one per-side fact the allocator
#: reads. The same file already carries `capability_assert` for the same reason.
DEV_ENVIRONMENT_REL = "config/dev-environment.yaml"
#: The edition registry (CFG2): the only place an edition SEGMENT is declared.
EDITIONS_REL = "config/taxonomy/editions.yaml"

#: THE ID GRAMMAR (gate ontology-domain-registry-and-edition-grain §C1, 2026-09-02, and
#: its rider idea-series-grammar §B1, 2026-09-05): ``[<EDITION>-]<MODULE><n>`` for an
#: item, ``[<EDITION>-]Idea-<n>`` for an inbox entry -- edition first, the BASE edition
#: unprefixed, so every id ever minted parses unchanged: G129, MM4, DD7, LOAD12,
#: XMPL-LOAD1. The segment is 2-5 uppercase letters (drydocs_core.edition_registry
#: CODE_RE) and is DECLARED in editions.yaml or it is a typo, never a tenant.
#: Duplicated in drydocs_core/backlog_store.py DELIBERATELY (core imports nothing from
#: under .claude/); tests/unit/test_backlog.py holds the two to one fixed parse list.
_EDITION_SEGMENT = r"(?:(?P<edition>[A-Z]{2,5})-)?"
_ID_RE = re.compile(rf"^{_EDITION_SEGMENT}(?P<series>[A-Z]+)(?P<number>\d+)$")
#: The same grammar as a FILENAME, for `git ls-tree` / `git log --name-only` output.
#: Anchored at a token boundary on the left: before PLAN2 the pattern matched `LOAD1`
#: INSIDE `XMPL-LOAD1.yaml` and silently dropped the segment (review F1).
_FILE_RE = re.compile(r"(?<![A-Za-z0-9-])(?P<id>(?:[A-Z]{2,5}-)?[A-Z]+\d+)\.yaml$")

#: An inbox id: ``- **`Idea-207a`** ·`` or ``- **`XMPL-Idea-3`** ·``. Same collision
#: problem, same fix, one command -- the inbox's own header table used to carry its
#: own wording for "next free", which is how two documents came to state one rule
#: differently. The optional letter suffix is a SPLIT (Idea-205a/205b), never a new
#: number, and an item id never carries one (the two-parser guard rules the suffix).
_IDEA_RE = re.compile(rf"^- \*\*`{_EDITION_SEGMENT}Idea-(?P<number>\d+)[a-z]?`\*\* ·", re.M)

#: The same header, UNANCHORED, for reading `git log -p` output -- every line
#: there carries a diff marker, so the anchored pattern above matches nothing
#: and the history term silently returned zero. Found by the source counts
#: printing `history=0` next to `local=224`, which is why they are printed.
_IDEA_IN_DIFF_RE = re.compile(rf"\*\*`{_EDITION_SEGMENT}Idea-(?P<number>\d+)[a-z]?`\*\*")

#: The pseudo-series that means the idea inbox rather than a backlog letter.
IDEA_SERIES = "IDEA"

#: The venue value that means "the base edition" -- ids carry no segment.
BASE_EDITION = "base"

#: THE DD-SERIES IS FROZEN, like the letters. It was the company's reserve under the
#: 2026-07-20 cross-repo convention (git-readme.md); that PARTITION rule retired
#: forward-only at gate ontology-domain-registry-and-edition-grain §C4 -- a venue is
#: named by its edition segment now -- and DD1-DD10 / DD10001-DD10003 stay readable
#: (FROZEN_BAND). The allocator still refuses it rather than leaving it to a reader.
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

#: THE COMPANY'S LEGACY BAND IDS ARE FROZEN AT THE BAND'S OWN MAX (PLAN3, 2026-09-02).
#: FROZEN_SERIES was measured on the PRODUCER's tree, refs and history - G tops out at
#: 136 here - but the company holds G10001-G10003 and DD10001-DD10003, minted under the
#: 10000+ band rule while it was in force (retired forward-only at gate
#: ontology-domain-registry-and-edition-grain). Read against FROZEN_SERIES alone those six
#: fail the freeze guard the day PLAN1 ports. So a band-shaped number (above
#: PRODUCER_BAND_CEILING) is judged against THIS table, not the letter's: frozen at the
#: highest the band ever took, per series, as a committed constant. The allocator never
#: mints into either table; this exists so the GUARD can read the company's ids as legacy
#: rather than as strays. Duplicated in tests/unit/test_backlog.py with the same agreement
#: guard the first table has.
FROZEN_BAND: dict[str, int] = {
    "G": 10003,
    "DD": 10003,
}

#: THE 10000 BAND, RETIRED FORWARD-ONLY (§C4, PLAN2). It was the number partition --
#: producer at or below this in EVERY series, company above -- and it governs no new
#: mint: the edition segment does that job. The constant stays because old ids must
#: still be READ by it (FROZEN_BAND is judged against it, the legacy guard in
#: tests/unit/test_backlog.py reads it) and because two shapes still key off it: the
#: BASE stays at or below it (a base id above it would be band-shaped, and the
#: allocator refuses that as the retired rule's shape), and an UNDECLARED venue's
#: ideas sit above it (rider C1). Duplicated from tests/unit/test_backlog.py
#: DELIBERATELY -- this script runs where pytest does not -- and a guard there
#: asserts the two agree.
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
def _git_run(*args: str) -> tuple[bool, str]:
    """``(ok, stdout)`` from git at the repo root. Never raises."""
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
        return False, ""
    return out.returncode == 0, out.stdout


def _git(*args: str) -> str:
    """Run git at the repo root. Returns "" on any failure, never raises.

    Silent failure is right HERE and nowhere else: this runs on a laptop with no
    network as readily as on one with a remote, and an allocator that crashed
    when a fetch failed would push people straight back to guessing -- which is
    the failure being fixed. The CALLER reports which sources answered, so a
    degraded run is visible rather than silent. The one command whose SUCCESS is
    the information -- the fetch -- goes through :func:`_git_run` instead, because
    "" is also what a successful ``fetch --quiet`` prints (review F12).
    """
    ok, out = _git_run(*args)
    return out if ok else ""


def fetch_remotes() -> bool:
    """``git fetch --all``; True when it succeeded.

    Reported rather than swallowed (review F12): the two warnings the report
    prints fire only when there are NO remote refs or NONE could be read. A failed
    fetch on a checkout that HAS refs is neither -- the stale refs read fine and
    the union is silently a day old, which is exactly the case the fetch exists to
    cover. So the fetch says whether it ran, and the caller prints a third warning.
    """
    ok, _ = _git_run("fetch", "--all", "--quiet")
    return ok


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


#: One allocated inbox id: ``(edition or None, number)``. The segment is part of
#: the identity -- ``XMPL-Idea-3`` and ``Idea-3`` are two ids in two inboxes.
IdeaId = tuple[str | None, int]


def _idea_numbers(text: str, pattern: re.Pattern[str] = _IDEA_RE) -> set[IdeaId]:
    return {(m.group("edition"), int(m.group("number"))) for m in pattern.finditer(text)}


def idea_ids() -> tuple[set[IdeaId], dict[str, int], list[str]]:
    """Every ``[<EDITION>-]Idea-<n>`` ever allocated -- local file, remote refs, history.

    Same three-term union as the backlog ids and for the same reason: the inbox
    is one file, so a remote branch that appended an entry is invisible to a
    local read, and an entry deleted in a merge is invisible to a tree read.
    """
    local_path = REPO_ROOT / IDEAS_REL
    local = _idea_numbers(local_path.read_text(encoding="utf-8")) if local_path.exists() else set()

    remote: set[IdeaId] = set()
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
    history = _idea_numbers(diff, _IDEA_IN_DIFF_RE)

    counts = {"local": len(local), "remote": len(remote), "history": len(history)}
    return local | remote | history, counts, read


# ---------------------------------------------------------------------------
# The venue: which edition a new id belongs to (PLAN2 b; rider C1).
# ---------------------------------------------------------------------------
#: Sentinel: the venue file declares no `edition:`. Distinct from None, which means
#: "the base edition" once a venue HAS declared.
UNDECLARED = "<undeclared>"


def venue_edition() -> str | None:
    """What this checkout RUNS AS: ``base``, a declared code, or None when undeclared.

    Read from config/dev-environment.yaml `edition:` and from nowhere else -- never a
    hostname, never a remote URL, never the band of the ids already in the tree (that
    inference is exactly what let a company session mint the producer's next number).
    ADR 0015 D3's "declared, not inferred", applied to the allocator's own venue.
    """
    path = REPO_ROOT / DEV_ENVIRONMENT_REL
    if not path.exists():
        return None
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    value = doc.get("edition") if isinstance(doc, dict) else None
    if value is None or str(value).strip() == "":
        return None
    value = str(value).strip()
    return BASE_EDITION if value.lower() == BASE_EDITION else value.upper()


def declared_editions() -> set[str]:
    """The codes editions.yaml declares (CFG2) -- the only legal segments."""
    path = REPO_ROOT / EDITIONS_REL
    if not path.exists():
        return set()
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    rows = doc.get("editions") if isinstance(doc, dict) else None
    return {
        str(r["code"]).strip().upper()
        for r in (rows or [])
        if isinstance(r, dict) and r.get("code") not in (None, "")
    }


def resolve_edition(
    requested: str | None,
    venue: str | None,
    *,
    kind: str,
    declared: set[str] | None = None,
) -> str | None:
    """The edition a new id is minted INTO: a code, None for the base, or UNDECLARED.

    ``venue`` is what the checkout runs as (:func:`venue_edition`); ``requested`` is
    the operator's ``--edition``, which overrides DOWNWARD only. ``kind`` is
    ``"item"`` or ``"idea"`` and differs in exactly one branch: an undeclared venue
    mints no item (PLAN2 d -- the refusal names the key) but may still capture an
    idea, band-shaped, until it declares (rider C1 -- a capture surface never
    refuses a capture). Every refusal is a SystemExit naming the replacement.
    """
    codes = declared if declared is not None else declared_editions()
    want = None if requested in (None, "") else str(requested).strip()
    if want is not None and want.lower() == BASE_EDITION:
        want = BASE_EDITION
    elif want is not None:
        want = want.upper()

    if venue is None:
        if kind != "idea":
            raise SystemExit(
                f"refused: this venue declares no `edition:` in {DEV_ENVIRONMENT_REL}, so it "
                "mints no item id. Set `edition: base` on the base, or the code your own "
                f"edition gate minted into {EDITIONS_REL} (CFG2). The 10000 band and the "
                "DD reserve retired forward-only (gate ontology-domain-registry-and-edition-"
                "grain §C4): a venue is named by its edition segment, never by its number, "
                "and the company mints nothing new until it has minted its code."
            )
        if want is not None:
            raise SystemExit(
                f"refused: --edition {want} from a venue that declares no `edition:` in "
                f"{DEV_ENVIRONMENT_REL}. An override is downward from a declared venue; an "
                "undeclared venue mints band-shaped `Idea-<n>` until it declares."
            )
        return UNDECLARED

    if venue != BASE_EDITION and venue not in codes:
        raise SystemExit(
            f"refused: {DEV_ENVIRONMENT_REL} declares `edition: {venue}` but {EDITIONS_REL} "
            f"does not declare that code (declared: {sorted(codes) or 'none'}). An undeclared "
            "segment is a typo, not a tenant (§C1) - mint the code at your edition gate first."
        )

    target = venue if want is None else want
    if target == BASE_EDITION:
        if venue != BASE_EDITION:
            raise SystemExit(
                f"refused: --edition base from venue {venue}. An instance never mints for its "
                "base; the override is downward only (a base may mint for an edition it hosts)."
            )
        return None
    if target not in codes:
        raise SystemExit(
            f"refused: edition {target!r} is not declared in {EDITIONS_REL}. An undeclared "
            f"segment is a typo, not a tenant (§C1). Declared: {sorted(codes) or 'none'}."
        )
    if venue != BASE_EDITION and target != venue:
        raise SystemExit(
            f"refused: --edition {target} from venue {venue}. An instance mints for itself "
            "only; a base may mint for any edition it hosts (downward only)."
        )
    return target


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


#: "Read the venue file" -- the default for the `venue=` parameters below, so a test
#: can hand in `base`, a code or None without touching config/dev-environment.yaml.
_READ_VENUE = "<read the venue file>"


def _venue(venue: str | None) -> str | None:
    return venue_edition() if venue == _READ_VENUE else venue


def next_id(
    series: str,
    taken: set[str] | None = None,
    *,
    edition: str | None = None,
    venue: str | None = _READ_VENUE,
) -> tuple[str, int]:
    """``(next_id, highest_taken)`` for ``series`` in the venue's edition.

    MAX+1 within the (edition, series) pair, never the lowest gap. The BASE edition
    is unprefixed and stays at or below PRODUCER_BAND_CEILING; an edition's ids carry
    its segment and count from 1 in their own inbox of numbers (`XMPL-LOAD1`).
    """
    series = series.strip().upper()
    if not series.isalpha():
        raise SystemExit(f"refused: {series!r} is not a series prefix (letters only)")
    if series in RESERVED_SERIES:
        raise SystemExit(
            f"refused: the {series}-series is FROZEN. It was the company-side reserve under "
            "the 2026-07-20 cross-repo convention; that partition rule retired forward-only at "
            "gate ontology-domain-registry-and-edition-grain §C4 (config/gate-log.md). A venue "
            "is named by its edition segment: validate.py --next-id --module <module> "
            "[--edition <code>]"
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
    target = resolve_edition(edition, _venue(venue), kind="item")
    pool = taken if taken is not None else known_ids()[0]
    numbers = [
        int(m.group("number"))
        for i in pool
        if (m := _ID_RE.match(i)) and m.group("series") == series and m.group("edition") == target
    ]
    highest = max(numbers, default=0)
    nxt = highest + 1
    if target is None and nxt > PRODUCER_BAND_CEILING:
        raise SystemExit(
            f"refused: {series}{nxt} is band-shaped (>{PRODUCER_BAND_CEILING}). The 10000 band "
            "retired forward-only (§C4) and the base stays below it; a venue is named by its "
            "edition segment, never by its number: --edition <code>."
        )
    prefix = "" if target is None else f"{target}-"
    return f"{prefix}{series}{nxt}", highest


def next_idea_id(
    numbers: set[IdeaId] | None = None,
    *,
    edition: str | None = None,
    venue: str | None = _READ_VENUE,
) -> tuple[str, int]:
    """``(next_idea_id, highest_taken)`` -- the Idea path, through the same three rules
    an item gets (rider D1): max+1 over local, every remote ref and history (never the
    lowest gap); the floor; the venue check of C1. ONE branch (C2):

    - a declared venue mints prefixed (`<code>-Idea-<n>`) or, for the base, unprefixed
      at or below PRODUCER_BAND_CEILING;
    - an undeclared venue mints band-shaped -- unprefixed, above the ceiling -- until it
      declares, and the id is stable from then on (never re-prefixed).
    """
    target = resolve_edition(edition, _venue(venue), kind="idea")
    pool = numbers if numbers is not None else idea_ids()[0]
    if target == UNDECLARED:
        band = [n for e, n in pool if e is None and n > PRODUCER_BAND_CEILING]
        highest = max(band, default=0)
        return f"Idea-{max(highest, PRODUCER_BAND_CEILING) + 1}", highest
    if target is None:
        base = [n for e, n in pool if e is None and n <= PRODUCER_BAND_CEILING]
        highest = max(base, default=0)
        nxt = highest + 1
        if nxt > PRODUCER_BAND_CEILING:
            raise SystemExit(
                f"refused: Idea-{nxt} is band-shaped (>{PRODUCER_BAND_CEILING}); the base inbox "
                "stays below the retired band (rider C1)."
            )
        return f"Idea-{nxt}", highest
    own = [n for e, n in pool if e == target]
    highest = max(own, default=0)
    return f"{target}-Idea-{highest + 1}", highest


def _report_allocation(series: str, show_all: bool, edition: str | None = None) -> int:
    # Fetch first: a stale remote-tracking ref is a ref that cannot see the id the
    # other machine pushed an hour ago, which is the whole failure.
    fetched = fetch_remotes()
    all_refs = remote_refs()
    venue = venue_edition()

    if series.strip().upper() == IDEA_SERIES:
        ideas, counts, refs = idea_ids()
        allocated, highest = next_idea_id(ideas, edition=edition, venue=venue)
        label = "Idea"
        target = allocated[: allocated.index("Idea")]  # "" or "<code>-"
        taken_in_series = sorted(n for e, n in ideas if (f"{e}-" if e else "") == target)
    else:
        taken, counts, refs = known_ids()
        allocated, highest = next_id(series, taken, edition=edition, venue=venue)
        label = series.strip().upper()
        target = allocated[: allocated.index(label)]  # "" or "<code>-"
        taken_in_series = sorted(
            int(m.group("number"))
            for i in taken
            if (m := _ID_RE.match(i))
            and m.group("series") == label
            and (f"{m.group('edition')}-" if m.group("edition") else "") == target
        )

    print(
        f"venue: {venue if venue is not None else 'UNDECLARED (no `edition:` in ' + DEV_ENVIRONMENT_REL + ')'}"
    )
    if not fetched:
        print(
            "WARNING: `git fetch --all` FAILED, so the remote-tracking refs below may be "
            "STALE -- the union can be a day old and look complete. Treat the number as "
            "provisional and re-check before you push the stub.",
            file=sys.stderr,
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
        f"  highest {label} taken: {target}{label}{'-' if label == 'Idea' else ''}{highest}"
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
        joined = ", ".join(f"{target}{label}{'-' if label == 'Idea' else ''}{n}" for n in gaps)
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
        rest = list(argv[1:])
        # `--edition <code>` anywhere after the mode: mint INTO that edition. Downward
        # only -- a base may mint for an edition it hosts; an instance may not mint for
        # its base or a sibling (PLAN2 b). Without it, the venue's own edition.
        edition: str | None = None
        if "--edition" in rest:
            at = rest.index("--edition")
            if at + 1 >= len(rest):
                raise SystemExit("usage: --edition <code>   (a code declared in editions.yaml)")
            edition = rest[at + 1]
            del rest[at : at + 2]
        if rest and rest[0] == "--module":
            # The series is DERIVED from the module (ruling 2026-09-02): the groomer
            # names the module the item belongs to - a field every item already
            # carries - and never picks a letter.
            codes = module_series()
            if len(rest) < 2 or rest[1] not in codes:
                known = ", ".join(sorted(codes))
                raise SystemExit(
                    f"usage: validate.py {argv[0]} --module <module> [--edition <code>]"
                    f"   modules: {known}"
                )
            return _report_allocation(codes[rest[1]], show_all=show, edition=edition)
        if not rest:
            raise SystemExit(
                f"usage: validate.py {argv[0]} --module <module> [--edition <code>]"
                "   (a backlog item)"
                + chr(10)
                + f"       validate.py {argv[0]} Idea [--edition <code>]"
                "                (the idea inbox)"
            )
        return _report_allocation(rest[0], show_all=show, edition=edition)
    return main()


if __name__ == "__main__":
    sys.exit(_cli(sys.argv[1:]))
