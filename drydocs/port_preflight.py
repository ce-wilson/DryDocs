"""port_preflight.py — J41: certify a producer base BEFORE a company session starts.

``docs/port-prompt.md`` has carried a mandatory CLOSING sequence since J35 and
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

Pure functions here take TEXT and COMMIT LISTS, never a repository, so the guards
can exercise them without one. Only :func:`run_checks` shells out.
"""

from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
PORT_PROMPT_PATH = REPO_ROOT / "docs" / "port-prompt.md"

#: The ledger's own header exempts these: "Grooms, claims, board/design renders
#: and depgraph snapshots in the range are ritual ... and get no step." Matched on
#: the commit SUBJECT, so a substantive commit can never hide behind a prefix.
RITUAL_SUBJECT_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"^chore\(backlog\):\s*groom\b", re.I),
    re.compile(r"^chore\(backlog\):\s*claim\b", re.I),
    re.compile(r"^chore\(depgraph\):\s*snapshot\b", re.I),
    re.compile(r"^chore\(render\):", re.I),
    re.compile(r"^chore\(board\):", re.I),
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


def run_checks(
    base: str, *, skip_tests: bool = False, will_tag: bool = False
) -> list[CheckResult]:
    """The five structural checks plus the relay-basis check, in order.

    Ordered cheapest-first so a dirty tree fails in milliseconds rather than after
    a minute of pytest.

    ``will_tag`` exists to break a chicken-and-egg the first draft walked straight
    into: the tag check gates certification, but ``--tag`` is how the tag gets
    created, so an untagged HEAD could never become a certified one. When the
    caller is about to create the tag, the check reports intent instead of absence.
    """
    results: list[CheckResult] = []

    dirty = _git("status", "--porcelain")
    results.append(
        CheckResult("tree clean", not dirty, dirty or "nothing staged or modified")
    )

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
            or ("will be created on success (--tag)" if will_tag else
                "no port-base-* tag at HEAD — run with --tag"),
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
