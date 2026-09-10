"""gate_log_redactions.py — the ONE legitimate in-place edit of signed gate-log text, declared.

The reconcile guard for ``config/gate-log.md`` is line-subsequence append-only: every
line of the before-snapshot must survive, in order, in the merged file. Insertions are
free (a dated POSTSCRIPT under a signed record, the other side's entries interleaved);
a missing or altered pre-merge line is the violation. That rule has exactly one
legitimate exception, and it is not a rider: a publish-boundary redaction (CLAUDE.md
section 3). A company-internal name quoted inside a signed record has to LEAVE the
tracked text, and a postscript cannot remove anything — so the line is changed in
place, the postscript says so, and the guard, correctly, fails on producer text at the
next roll (observed 2026-09-07, ``55c2a204``, clause C of the ADR 0007 record; the
consumer's hand prompt told it to stop and wait for this ruling).

The ruling (SME, 2026-09-08, RELAY-47): a section-3 redaction is declared, never
excused. ``config/gate-log-redactions.yaml`` carries one row per redacted line — the
redacting commit, the date, which signed record, the REPLACEMENT line as it now reads,
and the reason — and the guard reads that file: a pre-merge line that is missing where
a declared replacement stands is LISTED as ruled, never silence and never a failure
(the ``UNION_EXCLUSIONS`` shape from ``port_backlog_union``); a declared replacement
that is nowhere in the live file is a STALE declaration and FAILS, because the
redaction was reverted or the record reworded and the declaration now protects
nothing. The declaration holds the AFTER text only: the before line is the string the
redaction removed, and a registry that quoted it would put the name back.

Why a file and not an exemption in the guard: the consumer's before-snapshot still
carries the old string, so the consumer's guard is the one that fails, and the
consumer takes the guard as a fast-forward. A ruling inside the producer's test file
would reach them; a ruling inside the producer's side-local overlay would not. The
registry is canonical-producer and crosses whole (``PORT-MANIFEST.yaml``), so the
consumer's guard reads the same declaration the producer's does.

A REDACTION IS ONE VENUE'S ACT, AND THE ROW SAYS WHOSE (PORT11, 2026-09-10). The
first version of this registry left that unsaid, and the omission had a cost the
company named at the close of ``port-base-20260908``: a publish-boundary redaction
is a PRODUCER-venue action, because the producer publishes. Company-side there is
no publish boundary - the redacted string is a company-internal system name in a
private repo, which is exactly the venue allowed to hold it - so importing the
redaction removes a true name from the only tree entitled to keep it. Their choice
on the day was to adopt the producer's text anyway, because the alternative was a
declaration that reads STALE forever: the header rules a replacement missing from
the live file stale, and a consumer keeping the true name never has that line.

So each row declares its ``side``, and the stale check reads it: a declaration can
only go stale on the side that OWNS it. That check does not weaken - on the owning
side it is exactly as strict as before, which is the clause that makes the registry
safe to have. On the other side there is nothing to be stale about, because the row
describes an edit that side did not make and should not make.

WHICH SIDE THIS CHECKOUT IS, is DECLARED and never inferred (:func:`local_side`).
``config/dev-environment.yaml`` is canonical-company in the manifest and already
carries this exact class of per-side fact - ``edition``, ``capability_assert``, the
census counts - so the company's copy answers for the company and a port never
overwrites it. Inferring the side from the presence of an overlay file, from a
remote name or from a hostname is the failure mode ``edition:`` was made declared
to avoid. A checkout that has not answered yet is NOT CHECKED, never assumed
producer: assuming would re-create the very failure this item removes, on the tree
least able to notice.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml

from drydocs_core.check_outcome import CheckOutcome, checked_clean, findings, not_checked
from drydocs_core.repo_paths import repo_root

REPO_ROOT = repo_root(Path(__file__).resolve().parents[2])
REDACTIONS_FILE = REPO_ROOT / "config" / "gate-log-redactions.yaml"
DEV_ENVIRONMENT_FILE = REPO_ROOT / "config" / "dev-environment.yaml"
SCHEMA = "drydocs.gate-log-redactions.v1"
REQUIRED_FIELDS = ("commit", "date", "record", "replacement", "reason", "side")
REASONS = ("publish-boundary",)

#: The two venues of the one-way port (PORT-MANIFEST.yaml `direction:`). Closed, and
#: an undeclared value is refused rather than defaulted: a redaction whose owner is a
#: guess is a redaction whose stale check is a guess.
SIDES = ("producer", "company")


class RedactionDeclarationError(ValueError):
    """The registry is malformed — a declaration that cannot be read protects nothing."""


@dataclass(frozen=True)
class Redaction:
    commit: str
    date: str
    record: str
    replacement: str
    reason: str
    #: The venue whose publish boundary required the edit. Only this side's tree
    #: carries the replacement, and only this side's declaration can go stale.
    side: str


def parse_redactions(doc: object) -> list[Redaction]:
    """The rows of a loaded registry, validated; raises on any shape the guard cannot use."""
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA:
        raise RedactionDeclarationError(f"schema must be {SCHEMA!r}")
    rows = doc.get("redactions")
    if not isinstance(rows, list):
        raise RedactionDeclarationError("`redactions:` must be a list (empty is fine)")
    out: list[Redaction] = []
    for i, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise RedactionDeclarationError(f"redactions[{i}] is not a mapping")
        missing = [k for k in REQUIRED_FIELDS if not str(row.get(k, "")).strip()]
        if missing:
            raise RedactionDeclarationError(f"redactions[{i}] is missing {missing}")
        if row["reason"] not in REASONS:
            raise RedactionDeclarationError(
                f"redactions[{i}] reason {row['reason']!r} is not one of {list(REASONS)} — "
                "a redaction is a publish-boundary act; anything else is a rider (L25)"
            )
        if row["side"] not in SIDES:
            raise RedactionDeclarationError(
                f"redactions[{i}] side {row['side']!r} is not one of {list(SIDES)} — "
                "a publish-boundary redaction is ONE venue's act and the row says whose; "
                "an undeclared owner makes the stale check a guess on both sides"
            )
        replacement = str(row["replacement"]).rstrip("\r\n")
        if not replacement.strip():
            raise RedactionDeclarationError(f"redactions[{i}] replacement is blank")
        out.append(
            Redaction(
                commit=str(row["commit"]),
                date=str(row["date"]),
                record=str(row["record"]),
                replacement=replacement,
                reason=str(row["reason"]),
                side=str(row["side"]),
            )
        )
    return out


def load_redactions(path: Path = REDACTIONS_FILE) -> list[Redaction]:
    """The declared redactions, or an empty list when the registry does not exist yet.

    Absent is not an error: a consumer tree that predates the registry has declared
    nothing, and the guard then behaves exactly as before this file existed.
    """
    if not path.exists():
        return []
    return parse_redactions(yaml.safe_load(path.read_text(encoding="utf-8")))


@dataclass
class AppendOnlyResult:
    """What the append-only check found: the violation, if any, and the ruled redactions."""

    violation: str | None = None
    #: (pre-merge line number, replacement line) for each missing line a declaration covers.
    ruled: list[tuple[int, str]] = field(default_factory=list)

    def lines(self) -> list[str]:
        out = []
        if self.ruled:
            out.append("RULED REDACTIONS (config/gate-log-redactions.yaml) - listed, not failed:")
            out.extend(f"  pre-merge line {i} -> {rep!r}" for i, rep in self.ruled)
        if self.violation:
            out.append(self.violation)
        return out


def check_append_only(
    before_text: str, after_text: str, redactions: list[Redaction] | None = None
) -> AppendOnlyResult:
    """Line-subsequence append-only, with declared redactions ruled rather than failed.

    Every line of ``before_text`` must survive in ``after_text`` in order. A line that
    does not survive is ruled when the ``after`` line standing at its position is a
    declared replacement; otherwise it is the violation and the message names it.
    """
    result = AppendOnlyResult()
    if after_text.startswith(before_text):
        return result
    replacements = {r.replacement for r in redactions or ()}
    before = before_text.splitlines()
    after = after_text.splitlines()
    j = 0
    for i, line in enumerate(before, start=1):
        k = j
        while k < len(after) and after[k] != line:
            k += 1
        if k < len(after):
            j = k + 1
            continue
        if j < len(after) and after[j] in replacements:
            result.ruled.append((i, after[j]))
            j += 1
            continue
        result.violation = (
            f"append-only violated: pre-merge line {i} is missing or altered in the "
            f"merged file: {line!r} (every existing line must survive in order — "
            "dropping or editing either side's audit entries is an audit violation; "
            "inserting under a record, or between records, is not; a publish-boundary "
            "redaction is declared in config/gate-log-redactions.yaml, never excused)"
        )
        return result
    return result


def append_only_violation(
    before_text: str, after_text: str, redactions: list[Redaction] | None = None
) -> str | None:
    """None if append-only holds (declared redactions ruled), else the message."""
    return check_append_only(before_text, after_text, redactions).violation


def local_side(path: Path = DEV_ENVIRONMENT_FILE) -> str | None:
    """Which venue THIS checkout is, as declared - or ``None`` when it has not said.

    ``config/dev-environment.yaml`` is canonical-company in ``PORT-MANIFEST.yaml``,
    so each side's copy answers for itself and a port never overwrites the answer.
    ``None`` is a real state and not a failure: the key arrives with this item, and a
    tree that has not adopted it yet has declared nothing. Callers must treat that as
    NOT CHECKED rather than as either side - see :func:`stale_redaction_check`.

    An off-vocabulary value IS refused, because that is a wrong answer rather than a
    missing one.
    """
    if not path.exists():
        return None
    doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(doc, dict):
        raise RedactionDeclarationError(f"{path.name} is not a mapping")
    raw = doc.get("side")
    if raw is None:
        return None
    side = str(raw).strip()
    if side not in SIDES:
        raise RedactionDeclarationError(
            f"{path.name} declares side {side!r}, which is not one of {list(SIDES)}"
        )
    return side


def stale_redactions(
    live_text: str, redactions: list[Redaction], side: str | None
) -> list[Redaction]:
    """Declarations OWNED BY ``side`` whose replacement line is nowhere in the live file.

    A stale declaration means the redaction was reverted or the record reworded; either
    way the row now protects nothing and the guard says so — this clause is what makes
    the registry safe to have, and on the owning side it is exactly as strict as it was
    before ``side`` existed.

    A row owned by the OTHER venue is not stale here and never can be: it describes a
    publish-boundary edit that side made to its own tree, and this tree legitimately
    carries the unredacted line instead (PORT11). ``side=None`` returns nothing,
    because a checkout that has not declared cannot judge either way; the probe below
    is what says so out loud, and callers should prefer it.
    """
    if side is None:
        return []
    live = set(live_text.splitlines())
    return [r for r in redactions if r.side == side and r.replacement not in live]


def stale_redaction_check(
    live_text: str, redactions: list[Redaction], side: str | None
) -> CheckOutcome:
    """The stale check as a PROBE (ADR 0021): clean, findings, or not-checked-with-a-reason.

    Three answers, because there are three. An undeclared side is NOT the same as a
    clean registry, and rendering it as one would hide exactly the tree this item
    exists for: a consumer that took the roll, has not yet declared ``side:``, and
    would otherwise be told its declarations are fine.
    """
    if side is None:
        return not_checked(
            "config/dev-environment.yaml declares no `side:`, so this checkout cannot "
            "say which redactions are its own to keep current; declare producer or "
            "company there and the check runs (PORT11)"
        )
    owned = [r for r in redactions if r.side == side]
    stale = [r for r in owned if r.replacement not in set(live_text.splitlines())]
    subject = f"{len(owned)} {side}-owned redaction(s) of {len(redactions)} declared"
    if stale:
        return findings(stale, size=len(owned), subject=subject)
    return checked_clean(size=len(owned), subject=subject)
