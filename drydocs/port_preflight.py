"""port_preflight.py — J41: certify a producer base BEFORE a company session starts.

``docs/port/port-prompt.md`` has carried a mandatory CLOSING sequence since J35 and
nothing at the front, so every port began on an uncertified base. On 2026-08-09
that cost a full cycle: a company session was handed a thorough 8-phase plan and
could not run it solo, because one phase asked it to edit ``PORT-MANIFEST.yaml``
— a ``canonical-producer`` file its own apply phase takes wholesale. No amount of
instruction detail fixes a phase undoable by its assignee. Two real failures rode
in the same offered range (a ``FORCE_COLOR`` colour-vs-behaviour test failure and
a duplicate ``Idea-101`` from a two-session id collision), both invisible until
after the apply, and both of which would have read as port-introduced.

This module is the opening sequence made executable, because prose alone is what
J35 exists to correct — three consecutive ports closed without their required
fields while the rule was only written down.

A seventh check joined on 2026-08-12 from a different failure with the same shape:
a doc branch idle since 07-21 merged textually clean, and its "Approved /
canonical" list still pointed at two brand marks main had deleted as rejected in
between (Idea-110). A merge validates text overlap, never whether the prose still
describes the tree, so :func:`unresolved_citations` resolves the paths a newly
added document cites before that document crosses the repo boundary.

Pure functions here take TEXT, COMMIT LISTS and DOCUMENT MAPS, never a repository,
so the guards can exercise them without one. Only :func:`run_checks` shells out.
"""

from __future__ import annotations

import re
import subprocess
from collections.abc import Callable, Container, Mapping
from dataclasses import dataclass
from pathlib import Path

from drydocs_core.repo_paths import repo_root

REPO_ROOT = repo_root(Path(__file__).resolve().parents[1])
PORT_PROMPT_PATH = REPO_ROOT / "docs" / "port" / "port-prompt.md"

#: The ledger's own header exempts these: "Grooms, claims, board/design renders
#: and depgraph snapshots in the range are ritual ... and get no step." Matched on
#: the commit SUBJECT, so a substantive commit can never hide behind a prefix.
RITUAL_SUBJECT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^chore\(backlog\):\s*groom\b", re.I),
    re.compile(r"^chore\(backlog\):\s*claim\b", re.I),
    re.compile(r"^chore\(depgraph\):\s*snapshot\b", re.I),
    re.compile(r"^chore\(render\):", re.I),
    re.compile(r"^chore\(board\):", re.I),
    # THE SUBJECT CONVENTIONS DRIFTED AWAY FROM THE FIVE PATTERNS ABOVE, and the
    # ledger header never changed: it still says "Grooms, claims, board/design
    # renders and depgraph snapshots in the range are ritual ... and get no step."
    # These four spell the SAME categories the way the repo actually writes them
    # now. Measured on port-base-20260826..HEAD (2026-08-29): they account for 18
    # of 132 uncited commits, every one a claim, a render or a snapshot the header
    # had already exempted in words. This is a bug fix -- the policy is unchanged,
    # only its spelling.
    #
    # DELIBERATELY NOT WIDENED: `chore(backlog): close ...`. A close is not in the
    # header's ritual list, and close notes in this range carry findings a consumer
    # must read (G114 clause (e), K30's blocked half). Exempting them would be a
    # policy change, not a spelling fix, and it is the user's to make.
    # `session` joined the scope list on 2026-09-01: the session-close snapshot is
    # now written `chore(session): depgraph snapshot at <sha>, taken after CI went
    # green`. Same category, third spelling. The subject must still SAY snapshot,
    # so a substantive `chore(session):` cannot inherit the exemption.
    re.compile(r"^chore\((?:snapshot|depgraph|session)\):.*\bsnapshot\b", re.I),
    re.compile(r"^chore\(plan\):\s*(?:re-)?render\b", re.I),
    # A claim scoped to the ITEM rather than to `backlog`: `chore(Z5): claim`,
    # `chore(O63): release claim`. Narrow on purpose -- the subject must OPEN with
    # claim or release claim, so substantive work cannot inherit the exemption.
    re.compile(r"^chore\([A-Za-z][A-Za-z0-9]*\):\s*(?:release\s+(?:the\s+)?)?claim\b", re.I),
    # The same claim under a `backlog(<ID>):` TYPE rather than a chore scope —
    # `backlog(G125): claim in_progress (desktop)`. Three commits in the
    # port-base-20260829 range. Still anchored on `claim` immediately after the
    # colon, so `backlog(O60): the BDAT layers become a second lane basis` stays
    # substantive, which it is.
    re.compile(r"^backlog\([A-Za-z][A-Za-z0-9]*\):\s*(?:release\s+(?:the\s+)?)?claim\b", re.I),
    #
    # DELIBERATELY NOT WIDENED (2026-09-01), for the same reason `close` is not:
    # `chore(<ID>): mint ...` and `feat(backlog): <ID> body ...`. A MINT is not in
    # the header's ritual list, and under I6 a mint stub carries the item's FINAL
    # TITLE and its render — content a consumer reads, not bookkeeping. Mints are
    # covered by CITATION in the ledger's coverage footnote instead, the same way
    # IDEAS.md captures are. Exempting them would be a policy change, and it is
    # the user's to make, not this module's.
    # The same claim spelled as the status it writes: `chore(backlog): O69 in_progress`.
    re.compile(r"^chore\(backlog\):\s*[A-Za-z]+[0-9]+\s+in_progress\b", re.I),
    # The ledger roll itself, and it is not a convenience exemption — without it
    # the check cannot terminate. The commit that WRITES the citations can never
    # be among them, so every roll would mint a fresh uncited commit and the next
    # roll would too. Found by running this module against its own repository.
    # Deliberately NARROW: only a roll or a step write, never `chore(port):` at
    # large, because retiring manifest rows is also a chore(port) and is
    # substantive work a consumer must be told about.
    re.compile(r"^chore\(port\):\s*(roll\b|ledger\b)", re.I),
)

#: Every LIVE relay must declare where its claim comes from. Only the last of
#: these may assert company state — the distinction RELAY-5 lost when it told the
#: company "you already pushed a software-registry change with the internal URL",
#: which `git log --all -S "in-house"` company-side showed was never there. The
#: T-tracker has carried this caveat since T11; the RELAY section, added later as
#: J38, never inherited it.
BASIS_TAGS: tuple[str, ...] = (
    "[VERIFIED-PRODUCER]",
    "[SME-REPORTED]",
    "[COMPANY-CONFIRMED]",
)

#: Extensions worth resolving. Deliberately narrow, the same call
#: ``tests/unit/test_runbook_currency.py`` makes for its ``_PATH``: prose mentions
#: plenty of things that look path-like, and a guard with false positives gets
#: muted. Held as a separate literal rather than imported from that module because
#: this one's import profile is stdlib-only by design (MODULE_MAP: "so its guards
#: run without a repository"), and a component may not import a test.
_CITED_EXTENSIONS = "py|md|yaml|yml|cypher|sql|json|html|ps1|sh|csv|xlsx|ts|tsx|svg|png"
_CITED_PATH = re.compile(rf"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:{_CITED_EXTENSIONS}))`")

#: Directory prefixes whose documents cite paths in ANOTHER tree or in a past
#: session. Each carries its reason — the exemption IS the reason, the same idiom
#: ``test_runbook_currency`` uses for HISTORICAL_PATHS / FOREIGN_PATHS, and the
#: same call it already makes for the port-prompt ARCHIVE ("a record of steps 1-42
#: as they were written, so its paths are statements about the past by
#: construction"). Both entries were measured, not guessed: together they account
#: for every finding the check reports on the ``ae21ee4..HEAD`` range but one.
RECORD_PREFIXES: dict[str, str] = {
    "docs/reviews/": (
        "dated review and experiment captures. A capture's paths are facts about the "
        "session that produced it — the graph-vs-files runs name scripts their agents "
        "wrote inside worktrees and never committed (Idea-108), which is precisely what "
        "the record records, not a claim that the file is in this tree"
    ),
    "internal/controlm-config/reference/": (
        "VERBATIM captures of the company's own controlm_pipeline and XML-processor "
        "repositories. Every path in them is that tree's, not this one's — the same "
        "distinction FOREIGN_PATHS draws, applied to whole documents because these are "
        "foreign end to end rather than in a line or two"
    ),
}

#: A document may also declare itself a record in its own header, which beats a
#: table entry here on both counts that matter: the caveat is visible to whoever
#: READS the document, and it cannot rot out of sight inside a module nobody opens.
#: The convention comes from Idea-110 (2026-08-12) — the doc that motivated this
#: whole check was closed by annotating it as a record rather than by editing it.
_RECORD_MARKER = re.compile(r"^\s*status:\s*DATED RECORD\b", re.M | re.I)

#: Header only. A marker has to be a DECLARATION about the document; a document
#: that merely quotes the phrase mid-body has declared nothing.
_RECORD_HEADER_LINES = 30

_SHA_IN_BACKTICKS = re.compile(r"`([0-9a-f]{7,40})`")
_RELAY_HEADING = re.compile(r"^\s*-\s+(~~)?\*\*RELAY-(\d+)\b")
_LEDGER_START = "STEP LEDGER"
_LEDGER_END = "ACCEPTANCE GATE"
_RELAY_START = "STANDING RELAYS"
_RELAY_END = "OWED COMPANY-SIDE:"


@dataclass(frozen=True)
class Commit:
    """One commit in the candidate range."""

    sha: str
    subject: str


@dataclass(frozen=True)
class CheckResult:
    name: str
    passed: bool
    detail: str


def is_ritual(subject: str) -> bool:
    """True when the ledger's own header says this commit gets no step."""
    return any(p.search(subject) for p in RITUAL_SUBJECT_PATTERNS)


def _section(text: str, start: str, end: str) -> str:
    """The slice of *text* between the *start* and *end* markers.

    Returns "" when *start* is absent — an absent section cites nothing, which is
    the honest answer and makes every commit read as uncited rather than as
    covered. Failing open here would reproduce the very defect this module exists
    to catch.
    """
    i = text.find(start)
    if i == -1:
        return ""
    j = text.find(end, i)
    return text[i:] if j == -1 else text[i:j]


def cited_shas(port_prompt_text: str) -> set[str]:
    """Every backticked SHA appearing in the STEP LEDGER section."""
    return set(_SHA_IN_BACKTICKS.findall(_section(port_prompt_text, _LEDGER_START, _LEDGER_END)))


def uncited_commits(commits: list[Commit], port_prompt_text: str) -> list[Commit]:
    """Non-ritual commits in the range that the step ledger never cites.

    Mechanises the ROLL-PROCEDURE RULE — "currency is verified by diffing the
    ledger's claimed coverage against ``git log <last-ported-head>..HEAD``
    COMMIT-BY-COMMIT, never by eyeballing back from the newest entry". Both
    historic coverage gaps were found by the consumer, not here.

    A citation matches on SHA PREFIX in either direction, because the ledger
    abbreviates to 7 characters while ``git`` may hand back 40.
    """
    cited = cited_shas(port_prompt_text)
    missing: list[Commit] = []
    for commit in commits:
        if is_ritual(commit.subject):
            continue
        if any(commit.sha.startswith(c) or c.startswith(commit.sha) for c in cited):
            continue
        missing.append(commit)
    return missing


def relays_missing_basis(port_prompt_text: str) -> list[str]:
    """Live relay ids whose block declares no basis tag.

    A STRUCK relay (``~~**RELAY-n``) is discharged and exempt — it is kept as an
    audit trail, not as an instruction.
    """
    section = _section(port_prompt_text, _RELAY_START, _RELAY_END)
    if not section:
        return []

    lines = section.splitlines()
    starts: list[tuple[int, str, bool]] = []
    for index, line in enumerate(lines):
        match = _RELAY_HEADING.match(line)
        if match:
            starts.append((index, match.group(2), bool(match.group(1))))

    missing: list[str] = []
    for position, (index, relay_id, struck) in enumerate(starts):
        if struck:
            continue
        stop = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        block = "\n".join(lines[index:stop])
        if not any(tag in block for tag in BASIS_TAGS):
            missing.append(f"RELAY-{relay_id}")
    return missing


def is_record_document(rel_path: str, text: str) -> bool:
    """True when this document's paths are not claims about the current tree."""
    if any(rel_path.startswith(prefix) for prefix in RECORD_PREFIXES):
        return True
    header = "\n".join(text.splitlines()[:_RECORD_HEADER_LINES])
    return bool(_RECORD_MARKER.search(header))


def is_suite_guarded(rel_path: str) -> bool:
    """True when ``tests/unit/test_runbook_currency.py`` already resolves this doc.

    Skipping those is not a hole: that guard runs inside the suite, so a stale path
    in a runbook or in ``port-prompt.md`` still fails this preflight — as "suite
    green" rather than here. What the skip buys is that one defect is reported once.
    A document leaving that guard's coverage falls back INTO this check, never out
    of both, because this list is the narrower of the two.
    """
    return rel_path == "docs/port/port-prompt.md" or (
        rel_path.startswith("docs/design/") and rel_path.endswith("-runbook.md")
    )


def cited_paths(text: str, repo_roots: Container[str]) -> set[str]:
    """Backticked paths in *text* that CLAIM to name something in this tree.

    Two filters, both measured against the live range rather than guessed, because
    an unfiltered pass reports 112 paths and a check nobody can act on gets muted:

    * a citation with **no directory** (``drydocs-mark-mini.svg``) is a filename
      mention, not a repo-relative path — the same rule the currency guard uses;
    * a citation whose **first segment is not a top-level entry** of this repo
      (``results/GRADES.md``, ``jobs/base.py``, ``model/variable.py``) is relative
      to the document's own directory or to a foreign codebase, and was never a
      claim about this tree. That one discriminator removes 53 of the 59 findings
      on ``ae21ee4..HEAD``, and none of them were defects.
    """
    found: set[str] = set()
    for path in _CITED_PATH.findall(text):
        head, _, rest = path.partition("/")
        if not rest or head not in repo_roots:
            continue
        found.add(path)
    return found


def unresolved_citations(
    docs: Mapping[str, str],
    *,
    repo_roots: Container[str],
    exists: Callable[[str], bool],
) -> list[tuple[str, str]]:
    """``(document, path)`` for every cited path that resolves nowhere.

    Mechanises the standing check Idea-110 asked for on 2026-08-12: *resolve the
    paths a document cites before landing it*. That entry is the failure this
    exists to catch — ``docs/design/ui-exploration/claude-design-ui-prompt.md`` was authored on a
    branch on 07-21, listed two brand marks under *Approved / canonical*, main
    deleted both on 07-28 as rejected, and the branch merged clean on 08-12
    because **a merge validates text overlap, never whether the prose still
    describes the tree**. A designer following the doc's own reference list was
    sent to two files that were not there.

    Takes TEXT and a predicate, never a repository, so the guards exercise it
    without one — the same contract the rest of this module keeps.
    """
    findings: list[tuple[str, str]] = []
    for rel_path, text in sorted(docs.items()):
        if is_suite_guarded(rel_path) or is_record_document(rel_path, text):
            continue
        for path in sorted(cited_paths(text, repo_roots)):
            if not exists(path):
                findings.append((rel_path, path))
    return findings


def _git(*args: str, cwd: Path | None = None) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=str(cwd or REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    ).stdout.strip()


def range_commits(base: str, head: str = "HEAD", cwd: Path | None = None) -> list[Commit]:
    """``<base>..<head>`` as :class:`Commit` records, oldest first."""
    raw = _git("log", "--reverse", "--format=%h%x00%s", f"{base}..{head}", cwd=cwd)
    commits: list[Commit] = []
    for line in raw.splitlines():
        sha, _, subject = line.partition("\0")
        if sha:
            commits.append(Commit(sha=sha, subject=subject))
    return commits


def added_documents(base: str, head: str = "HEAD", cwd: Path | None = None) -> dict[str, str]:
    """The markdown files the range ADDS, keyed by repo-relative path.

    ADDED, not added-or-modified, and the distinction is the whole design rather
    than a convenience. A document MODIFIED in the range is mostly older prose
    whose citations are dated statements — on ``ae21ee4..HEAD`` the wider scope
    reports 59 paths, of which the great majority are gate-log history, IDEAS
    entries naming an absence deliberately, and pre-Phase-B review docs. A document
    ADDED in the range is a fresh claim about the tree as it stands at the base
    being certified, and it is exactly the shape Idea-110 describes: prose written
    weeks earlier on a branch, landing now, against a tree that moved underneath it.
    """
    root = cwd or REPO_ROOT
    raw = _git("diff", "--name-only", "--diff-filter=A", f"{base}..{head}", cwd=cwd)
    docs: dict[str, str] = {}
    for rel in raw.splitlines():
        if not rel.endswith(".md"):
            continue
        path = root / rel
        if path.exists():
            docs[rel] = path.read_text(encoding="utf-8", errors="replace")
    return docs


def venue_line() -> str:
    """The J18 stamp: an acceptance figure without its venue reads as a defect.

    The two machines hold independent graphs and differ in the two dimensions that
    move the count — whether the production CSV is present, and whether
    ``RECONCILE_BEFORE_DIR`` is set — which is exactly why the ledger's own chain
    records ``1539 -> 1551`` as NOT a ``+12`` delta.
    """
    import os
    import platform

    csv_present = (REPO_ROOT / "drydocs" / "data" / "samples").exists()
    reconcile = "set" if os.environ.get("RECONCILE_BEFORE_DIR") else "unset"
    force_color = os.environ.get("FORCE_COLOR")
    extra = f", FORCE_COLOR={force_color}" if force_color else ""
    return (
        f"venue: {platform.node()}, samples-dir {'present' if csv_present else 'absent'}, "
        f"RECONCILE_BEFORE_DIR {reconcile}{extra}"
    )


def run_checks(base: str, *, skip_tests: bool = False, will_tag: bool = False) -> list[CheckResult]:
    """The five structural checks plus the relay-basis and cited-path checks.

    Ordered cheapest-first so a dirty tree fails in milliseconds rather than after
    a minute of pytest.

    ``will_tag`` exists to break a chicken-and-egg the first draft walked straight
    into: the tag check gates certification, but ``--tag`` is how the tag gets
    created, so an untagged HEAD could never become a certified one. When the
    caller is about to create the tag, the check reports intent instead of absence.
    """
    results: list[CheckResult] = []

    dirty = _git("status", "--porcelain")
    results.append(CheckResult("tree clean", not dirty, dirty or "nothing staged or modified"))

    text = PORT_PROMPT_PATH.read_text(encoding="utf-8")

    missing_relays = relays_missing_basis(text)
    results.append(
        CheckResult(
            "relay basis tags",
            not missing_relays,
            ", ".join(missing_relays) or "every live relay declares its basis",
        )
    )

    commits = range_commits(base)
    uncited = uncited_commits(commits, text)
    results.append(
        CheckResult(
            "ledger coverage",
            not uncited,
            "\n".join(f"    UNCITED {c.sha} {c.subject}" for c in uncited)
            or f"all {len(commits)} commits in {base}..HEAD are cited or ritual",
        )
    )

    docs = added_documents(base)
    unresolved = unresolved_citations(
        docs,
        repo_roots={entry.name for entry in REPO_ROOT.iterdir()},
        exists=lambda rel: (REPO_ROOT / rel).exists(),
    )
    results.append(
        CheckResult(
            "cited paths resolve",
            not unresolved,
            "\n".join(f"    UNRESOLVED {doc}: `{path}`" for doc, path in unresolved)
            or f"every path cited by the {len(docs)} document(s) this range adds resolves",
        )
    )

    render = subprocess.run(
        ["poetry", "run", "python", "scripts/render_board.py"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    drift = _git("status", "--porcelain") if render.returncode == 0 else ""
    results.append(
        CheckResult(
            "renders current",
            render.returncode == 0 and not drift,
            drift or ("renderer failed" if render.returncode else "no drift after re-render"),
        )
    )

    if skip_tests:
        results.append(CheckResult("suite green", False, "SKIPPED — not a certification"))
    else:
        suite = subprocess.run(
            ["poetry", "run", "pytest", "tests/unit", "-q"],
            cwd=str(REPO_ROOT),
            capture_output=True,
            text=True,
            check=False,
        )
        tail = [ln for ln in suite.stdout.splitlines() if ln.strip()]
        results.append(
            CheckResult(
                "suite green",
                suite.returncode == 0,
                f"{tail[-1] if tail else 'no output'} ({venue_line()})",
            )
        )

    tags = _git("tag", "--points-at", "HEAD").splitlines()
    base_tags = [t for t in tags if t.startswith("port-base-")]
    results.append(
        CheckResult(
            "certified base tag",
            bool(base_tags) or will_tag,
            ", ".join(base_tags)
            or (
                "will be created on success (--tag)"
                if will_tag
                else "no port-base-* tag at HEAD — run with --tag"
            ),
        )
    )

    return results


def next_base_tag(existing: list[str], today: str) -> str:
    """``port-base-<today>``, suffixed a/b/c… when that name is taken.

    Same convention the company already uses for its backup tags, so a second
    certification on one day reads the way the other side's tags already do.
    """
    stem = f"port-base-{today}"
    if stem not in existing:
        return stem
    for suffix in "bcdefghijklmnopqrstuvwxyz":
        candidate = f"{stem}{suffix}"
        if candidate not in existing:
            return candidate
    raise ValueError(f"no free suffix for {stem}")
