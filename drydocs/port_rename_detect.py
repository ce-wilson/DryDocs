"""port_rename_detect.py — a rename reads as a CLEAN-ADD on the receiving side (J72).

THE DEFECT, MEASURED TWICE IN ONE SESSION (2026-09-01, company apply of
``port-base-20260901``). A port classifies each producer path against
``PORT-MANIFEST.yaml``, and a path that does not exist consumer-side is a
clean-add: apply untouched, no merge, no decision. That classification is correct
about the PATH and blind to the CONTENT.

  * ``41-local-business-application.yaml`` was a clean-add by path. Its entries
    already existed consumer-side under ``41-local-seal.yaml`` — the producer had
    renamed the fragment at gate ``vocabulary-domains-and-id-policy`` §A1/§A2.
    Applying it duplicated 16 vocabulary ids and cost 62 failures and a revert.
  * ``cdo-crosswalk.yaml`` was a clean-add by path. The consumer held the same gate
    under its retired-acronym name — and the producer's copy carries a SIGNED-OFF
    header while the consumer's says DRAFT, unsigned, session pending. Applying it
    would have imported a signature the consumer deliberately withholds, into a
    file class the manifest declares ``canonical-company``. That is a gate-state
    regression, and it is worse than a duplicate: a dropped field is absent, a
    fabricated sign-off is present and confident, and ``config/gate-log.md`` cites
    gate outcomes.

Both were renames. Neither was visible to a path comparison, and no amount of
care with the manifest would have caught either, because the manifest answers
"how do I merge this path" and the question here is "is this path new at all".

WHAT THIS DOES. For each proposed clean-add, compare its content against consumer
files that have a DIFFERENT name, and report the ones that look like the same
document. Two comparisons, because the two traps had different shapes:

  * ID-SET overlap, for registry-shaped documents (a vocabulary fragment, a
    source registry, a bindings file). Renaming a fragment moves entries; the ids
    are what survive the move, so they are what identifies the twin.
  * NORMALIZED-TEXT similarity, for prose-shaped documents (a gate prompt, a
    runbook). Comments, blank lines and case are stripped; a rename usually keeps
    most of the body.

IT REPORTS, IT DOES NOT DECIDE. A high-similarity pair may be a genuine rename to
adopt, a rename to decline, or two files that merely look alike. The output is
"stop and look at these two", which is exactly the step that was missing both
times. Deciding is the manifest's job and the SME's.

Pure functions take TEXT and PATH MAPS, never a repository — the same rule
``port_preflight`` follows and for the same reason: the guards run without a
consumer tree, which the producer does not have.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

#: Sequences whose entries carry an ``id``-ish key, and the key to read.
#: DELIBERATELY NOT section titles: "A. the framework rows" captures as "A." and
#: would match every gate prompt with an A section — a false-positive generator.
#: Prose-shaped documents fall to the text measure, which is what they need. A
#: registry-shaped document is identified by the ids it carries rather than by its
#: prose, so this is the strong signal when it applies.
ID_SEQUENCES: tuple[tuple[str, str], ...] = (
    ("local_relationships", "id"),
    ("node_classifications", "label"),
    ("sources", "id"),
    ("systems", "id"),
    ("datasets", "id"),
    ("profiles", "id"),
    ("classes", "id"),
    ("items", "id"),
)

#: Below this, two documents are not the same document under either measure.
#: Deliberately LOW: this check exists to make somebody look, and the cost of a
#: false positive is one diff while the cost of a false negative is a duplicated
#: vocabulary or an imported signature. Tuned on the two known traps, both of
#: which score far above it.
SIMILARITY_FLOOR = 0.35

#: Below this many ids on either side, the id measure ABSTAINS instead of
#: voting. A gate prompt carries one id, and a rename renames it — scoring that
#: pair 0.00 on a one-id-each miss would silence the text measure that catches it.
MIN_IDS_FOR_ID_MEASURE = 3

#: Matches reported per proposed add. A cap rather than a best-of, because the
#: true twin can score below a coincidence — but a file matching a dozen others
#: is noise, not evidence, and burying the signal is the failure at the other end.
MAX_MATCHES_PER_ADD = 3

_COMMENT = re.compile(r"#.*$", re.M)
_WS = re.compile(r"\s+")


@dataclass(frozen=True)
class RenameCandidate:
    """One proposed add that looks like an existing consumer file under another name."""

    proposed: str
    existing: str
    score: float
    basis: str  # "id-set" | "normalized-text"

    def __str__(self) -> str:
        return (
            f"{self.proposed}\n    looks like {self.existing}"
            f"  ({self.basis} similarity {self.score:.2f})"
        )


def normalized_text(text: str) -> str:
    """Comments stripped, whitespace collapsed, lowercased.

    Comments go because a rename usually rewrites the header while keeping the
    body — the crosswalk prompt and its retired-acronym twin differ most in their
    header, which is precisely the part that must not dominate the comparison.
    """
    return _WS.sub(" ", _COMMENT.sub("", text)).strip().lower()


def id_set(text: str) -> set[str]:
    """Every entry id in a registry-shaped document.

    Parsed with a line scanner rather than a YAML load, because this must work on
    a file that does not parse — a half-applied port is exactly when it is needed,
    and a YAML error would turn the check off at the moment it matters most.
    """
    keys = {key for _sequence, key in ID_SEQUENCES}
    pattern = re.compile(
        rf"^\s*-?\s*(?:{'|'.join(sorted(keys))}):\s*[\"']?([A-Za-z0-9_.:@-]+)", re.M
    )
    return {m.group(1) for m in pattern.finditer(text)}


def jaccard(a: set[str], b: set[str]) -> float:
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def text_similarity(a: str, b: str) -> float:
    """Token-level Jaccard over normalized text. Cheap and order-insensitive,
    which is right here: a rename that also reorders sections is still a rename."""
    return jaccard(set(a.split()), set(b.split()))


def compare(proposed_text: str, existing_text: str) -> tuple[float, str]:
    """``(score, basis)`` — the STRONGER of the two measures, with its name.

    Not "pick one measure": they detect different things and the union of their
    coverage is the point. Both known traps prove it.

    The gate prompts each carry exactly ONE id, and a rename renames the id too
    (the retired-acronym stem -> ``cdo-crosswalk``), so the id measure scores them 0.00
    — the signal meant to help is the one that zeroes them. Their bodies are 0.88
    similar. Conversely a fragment SPLIT moves entries into a file whose prose
    shares little with the source, and there the ids are the only thing that
    survives the move. Take the max and both are caught.

    ``MIN_IDS_FOR_ID_MEASURE`` is why the gate pair is not scored 0.00 on a
    one-id-each coincidence: below it, the id measure abstains rather than voting.
    """
    proposed_ids, existing_ids = id_set(proposed_text), id_set(existing_text)
    id_score = (
        jaccard(proposed_ids, existing_ids)
        if min(len(proposed_ids), len(existing_ids)) >= MIN_IDS_FOR_ID_MEASURE
        else 0.0
    )
    text_score = text_similarity(normalized_text(proposed_text), normalized_text(existing_text))
    if id_score >= text_score and id_score > 0.0:
        return id_score, "id-set"
    return text_score, "normalized-text"


#: A leading numeric slot, as the vocabulary fragment directory uses it
#: (``41-local-seal.yaml``). Where a directory numbers its files, the number IS the
#: slot and the stem is just its current name — so same number + different stem is
#: rename evidence that needs no content at all.
_NUMERIC_SLOT = re.compile(r"^(\d+)[-_]")


def slot_of(path: str) -> str | None:
    """The numeric slot of a filename, or None if it does not use one."""
    match = _NUMERIC_SLOT.match(Path(path).name)
    return match.group(1) if match else None


def structural_candidates(
    proposed: dict[str, str], existing: dict[str, str]
) -> list[RenameCandidate]:
    """Same directory, same numeric slot, different stem — a rename, content-free.

    CONTRIBUTED BY THE COMPANY SESSION (2026-09-01), and it exists because the
    content measures FAILED on the incident this tool was built for. Measured
    against the eight real pairs from that apply, the content check caught three:
    it scored ``41-local-business-application.yaml`` against ``41-local-seal.yaml``
    at **0.29** on a 0.35 floor — the pair that cost 62 failures.

    WHY BOTH MEASURES DEGRADED AT ONCE, which is the assumption that broke. The
    max-of-two design supposes id-overlap and text-similarity fail independently.
    In a SPLIT-PLUS-RENAME they do not: the entries were redistributed across
    files (text falls) in the same migration that renamed their ids (overlap
    falls). Two measures, one common cause.

    This signal shares no cause with either, because it reads no content at all.
    """
    out: list[RenameCandidate] = []
    for new_path in sorted(proposed):
        if new_path in existing:
            continue
        slot, new_dir = slot_of(new_path), str(Path(new_path).parent)
        if slot is None:
            continue
        for old_path in sorted(existing):
            if old_path == new_path or str(Path(old_path).parent) != new_dir:
                continue
            if slot_of(old_path) == slot:
                out.append(RenameCandidate(new_path, old_path, 1.0, "same-slot-prefix"))
    return out


#: A vanished twin's content had to go SOMEWHERE, so the prior is far higher than
#: for an arbitrary pair and the floor drops accordingly. Still a floor: a file the
#: producer genuinely deleted should not drag in every unrelated add.
VANISHED_TWIN_FLOOR = 0.15


def vanished_twin_candidates(
    proposed: dict[str, str],
    existing: dict[str, str],
    producer_paths: set[str],
    *,
    floor: float = VANISHED_TWIN_FLOOR,
) -> list[RenameCandidate]:
    """Consumer files the producer no longer has — find where their content went.

    THE CASE NEITHER OTHER SIGNAL REACHES: a SPLIT INTO A NEW SLOT.
    ``41-local-seal.yaml`` vanished and its entries went to TWO files, one of them
    ``52-local-human.yaml``. The slot differs (52 vs 41) so the structural signal
    cannot see it, and the content scored 0.30/0.28 because the same migration
    that moved the entries also renamed their ids.

    But a file that exists here and NOT on the producer side is a strong prior on
    its own: the producer renamed it, split it, or deleted it, and all three are
    decisions rather than defaults. So this searches the WHOLE proposed set
    (ignoring slot and directory) at a lower floor, because the question has
    already narrowed from "are these two files related" to "where did this
    specific file's content go".

    A genuine deletion reports nothing above the floor and says so, which is the
    correct answer and still worth confirming.
    """
    out: list[RenameCandidate] = []
    for old_path, old_text in sorted(existing.items()):
        if old_path in producer_paths:
            continue  # still there; not vanished
        for new_path, new_text in sorted(proposed.items()):
            score, _basis = compare(new_text, old_text)
            if score >= floor:
                out.append(RenameCandidate(new_path, old_path, score, "vanished-twin"))
    return out


def rename_candidates(
    proposed: dict[str, str],
    existing: dict[str, str],
    *,
    floor: float = SIMILARITY_FLOOR,
    same_directory_only: bool = True,
    producer_paths: set[str] | None = None,
) -> list[RenameCandidate]:
    """Clean-adds that resemble an existing consumer file under a different name.

    ``proposed`` and ``existing`` are ``{repo-relative path: file text}``. A path
    present in BOTH is skipped — that is a collision the manifest already routes,
    not a rename.

    ``same_directory_only`` because both known traps were in-directory renames and
    a whole-tree comparison is quadratic over thousands of files for a signal that
    would mostly be noise. Set it False for a deliberate wide sweep.
    """
    out: list[RenameCandidate] = []
    for new_path, new_text in sorted(proposed.items()):
        if new_path in existing:
            continue  # a collision, not a rename — the manifest routes it
        new_dir = str(Path(new_path).parent)
        matches: list[RenameCandidate] = []
        for old_path, old_text in existing.items():
            if old_path == new_path:
                continue
            if same_directory_only and str(Path(old_path).parent) != new_dir:
                continue
            score, basis = compare(new_text, old_text)
            if score >= floor:
                matches.append(RenameCandidate(new_path, old_path, score, basis))
        # EVERY match above the floor, not just the best one — capped, not filtered.
        #
        # Reporting only the winner HIDES THE TRUE TWIN behind a higher-scoring
        # coincidence, which is not hypothetical: the company sweep on 2026-09-01
        # found `cdo-alignment.yaml` reported against `ddlineage-retirement.yaml`
        # while its real twin, the retired-acronym `*-alignment.yaml` sitting in the
        # same directory, also cleared the floor and was silently dropped. A
        # best-match report is a RANKING presented as an identification, and the one
        # answer it suppresses is the one the reader needed.
        out.extend(sorted(matches, key=lambda c: -c.score)[:MAX_MATCHES_PER_ADD])

    # The structural signal is added rather than compared against: it reads no
    # content, so it cannot be outscored by a content measure and must not be
    # suppressed by one. A pair found both ways appears once, structural first,
    # because "same slot" is the stronger claim.
    seen = {(c.proposed, c.existing) for c in out}
    structural = structural_candidates(proposed, existing)
    vanished = (
        vanished_twin_candidates(proposed, existing, producer_paths)
        if producer_paths is not None
        else []
    )
    for candidate in [*structural, *vanished]:
        key = (candidate.proposed, candidate.existing)
        if key not in seen:
            out.append(candidate)
            seen.add(key)
    return sorted(out, key=lambda c: (c.proposed, -c.score))


#: Printed on a clean run, because the company session's measurement showed the
#: content check catching only three of eight real pairs. Exit 0 said "clean" while
#: the trap that cost 62 failures scored 0.29 on a 0.35 floor. The signals since
#: added close the known cases; the honest claim is still NECESSARY, NOT SUFFICIENT.
NOT_A_GUARANTEE = (
    "NOT A GUARANTEE. This is necessary, not sufficient: a clean run means no "
    "proposed add matched a KNOWN rename shape, not that the slice is safe. Every "
    "clean-add still deserves a content look. Measured 2026-09-01, the content "
    "measures alone caught 3 of 8 real pairs — the same-slot and vanished-twin "
    "signals were added because of that miss, and the next shape is not yet known."
)


def report(candidates: list[RenameCandidate]) -> str:
    if not candidates:
        clean = "no proposed clean-add resembles an existing file under another name."
        return clean + "\n\n" + NOT_A_GUARANTEE
    lines = [
        f"{len(candidates)} proposed clean-add(s) resemble an existing file under "
        "ANOTHER NAME — stop and look before applying:",
        "",
    ]
    lines += [f"  {candidate}" for candidate in candidates]
    lines += [
        "",
        "This is a REPORT, not a verdict. Each pair is one of:",
        "  * a rename to ADOPT      — take the new name, delete the old, migrate references",
        "  * a rename to DECLINE    — keep your name; the content may still need merging",
        "  * a false positive       — two files that merely look alike",
        "",
        "Check the CONTENT before choosing, and check the gate state: a gate prompt "
        "whose header says SIGNED where yours says DRAFT is a gate-state regression, "
        "not a content difference (config/gate-prompts/** is canonical-company).",
        "",
        NOT_A_GUARANTEE,
    ]
    return "\n".join(lines)
