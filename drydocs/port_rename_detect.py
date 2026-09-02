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

#: Below this many distinct tokens on either side, CONTAINMENT abstains and only
#: Jaccard votes. Same shape as MIN_IDS_FOR_ID_MEASURE and the same reason: a
#: measure that divides by the smaller set becomes a boilerplate detector when the
#: smaller set IS boilerplate. Caught by an existing guard the moment containment
#: landed — a 4-token document whose tokens were `-`, `id:` and
#: `local_relationships:` scored 0.75 containment against an unrelated file, on
#: structure alone. The company said it first about Jaccard ("equal tiny sets make
#: it measure boilerplate, not content"); it is truer of containment. Set below the
#: 11 tokens of the real pair this measure exists for.
MIN_TOKENS_FOR_CONTAINMENT = 8

_COMMENT = re.compile(r"#.*$", re.M)
_WS = re.compile(r"\s+")
_PUNCT_ONLY = re.compile(r"[^\w]+")


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
    collapsed = _WS.sub(" ", _COMMENT.sub("", text)).strip().lower()
    # A bare `-` is a YAML list marker, not evidence. Dropping pure punctuation
    # costs nothing and stops the smallest documents scoring on structure alone.
    return " ".join(t for t in collapsed.split() if not _PUNCT_ONLY.fullmatch(t))


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


def containment(a: set[str], b: set[str]) -> float:
    """``|A n B| / min(|A|, |B|)`` — overlap as a fraction of the SMALLER set.

    CONTRIBUTED BY THE COMPANY SESSION (2026-09-01) after measuring that Jaccard
    collapses under SIZE ASYMMETRY, which is arithmetic rather than opinion. Their
    real pair: an 11-token producer stub against the 97-token company epic it was
    reduced from, sharing 8 tokens. Jaccard puts the union on the bottom and scores
    it 0.08 — rank 13 of 29, never near the floor. Containment divides by the
    smaller set and scores 0.73, rank 1 of 29.

    That asymmetry is the normal shape of a rename here, not an edge case: a
    producer file is regularly a reduction or an expansion of its consumer twin,
    and Jaccard reads the size difference as dissimilarity.

    IT OVER-FIRES ALONE, and the caveat came with the contribution — verified
    independently on the producer tree: `component-topology.yaml` at 428 tokens
    reaches containment 0.64 against an 11-token stub on Jaccard 0.02, purely by
    being large enough to contain it. So this is taken as ``max(jaccard,
    containment)`` and bounded by :data:`MAX_MATCHES_PER_ADD`. **Neither is
    sufficient alone** — containment finds the twin, the cap bounds its noise —
    and that composition is the finding, more than either half.
    """
    if not a or not b:
        return 0.0
    if min(len(a), len(b)) < MIN_TOKENS_FOR_CONTAINMENT:
        return 0.0  # too small to carry content; see MIN_TOKENS_FOR_CONTAINMENT
    return len(a & b) / min(len(a), len(b))


def overlap(a: set[str], b: set[str]) -> float:
    """The stronger of Jaccard and containment. See :func:`containment`."""
    return max(jaccard(a, b), containment(a, b))


def text_similarity(a: str, b: str) -> float:
    """Token-level overlap over normalized text. Cheap and order-insensitive,
    which is right here: a rename that also reorders sections is still a rename."""
    return overlap(set(a.split()), set(b.split()))


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
        overlap(proposed_ids, existing_ids)
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
        # CORRECTION, 2026-09-01: an earlier version of this comment said the true
        # twin "also cleared the floor and was silently dropped" by the best-match
        # rule. THAT WAS WRONG, and measured wrong by the company session: on their
        # tree the twin scored 0.08 and ranked 13 of 29 — it never came near the
        # floor, so no change to the cap could have surfaced it. The cap is still
        # right (a best-match report is a RANKING presented as an IDENTIFICATION),
        # but it was not the fix for that pair; :func:`containment` is. Left here as
        # a correction rather than an edit, because the wrong reason was load-bearing
        # for a whole round of work.
        #
        # The two compose and neither is sufficient: containment surfaces a twin the
        # union-denominator buried, and the cap keeps containment's size-driven
        # false positives from burying it again.
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
    by_key = {(c.proposed, c.existing): c for c in out}
    for candidate in [*structural, *vanished]:
        key = (candidate.proposed, candidate.existing)
        existing_claim = by_key.get(key)
        if existing_claim is None:
            by_key[key] = candidate
        elif candidate.basis == "same-slot-prefix":
            # THE STRONGEST CLAIM WINS A DUPLICATE, and the naive dedup had this
            # backwards. `41-local-business-application` <- `41-local-seal` reported
            # as normalized-text 0.57 because the content pass reached it first and
            # the structural pass was then skipped as "already seen" — losing the
            # 1.00 same-slot claim, which is the one a reader should act on. Order of
            # discovery is not evidence of strength.
            by_key[key] = candidate
    out = list(by_key.values())
    del seen

    # THE CAP IS PER PROPOSED FILE, ACROSS ALL SIGNALS — not per signal.
    #
    # Containment is deliberately permissive (it has to be, to surface a twin the
    # union-denominator buried), so three signals each capped at three produced
    # TWENTY rows for six files on the real vocabulary sweep. That is the failure
    # the company named about a different symptom, and it applies here exactly:
    # three unrelated files at a similar score are "a strong invitation to dismiss
    # the whole flag as noise, which is the failure the detector exists to prevent."
    #
    # Structural first, because "same slot" is the strongest claim available, then
    # by score — so whatever survives the cap leads with the likeliest twin.
    ranked: dict[str, list[RenameCandidate]] = {}
    for candidate in out:
        ranked.setdefault(candidate.proposed, []).append(candidate)
    capped: list[RenameCandidate] = []
    for proposed_path in sorted(ranked):
        best_first = sorted(
            ranked[proposed_path],
            key=lambda c: (c.basis != "same-slot-prefix", -c.score),
        )
        capped.extend(best_first[:MAX_MATCHES_PER_ADD])
    return capped


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


def parse_git_renames(name_status: str) -> list[tuple[str, str, int]]:
    """``(old, new, similarity%)`` from ``git diff -M --diff-filter=R --name-status``.

    GIT ALREADY KNOWS, and the port was throwing it away. A port classifies each
    producer path against the manifest and asks "does the consumer have this path" —
    a question that discards the rename metadata sitting in the commit that made it.
    Measured on ``port-base-20260826..HEAD``: **18 renames**, every one of the
    2026-09-01 traps among them, with similarity scores attached —
    ``40-local-controlm -> 40-local-scheduler`` at R097,
    ``41-local-seal -> 41-local-business-application`` at R095, the crosswalk prompt
    twin at R075, its test at R088, and ``drydocs/docs_verify.py ->
    drydocs_core/docs_verify.py`` at R090, which is the shadow-definition trap.

    This is EXACT where the similarity measures are heuristic, so it is reported
    first and separately. It does not replace them, for two reasons:

    * **Git's rename detection is 1:1.** A SPLIT gets one match and the rest are
      plain adds — ``41-local-seal`` matched ``41-local-business-application`` and
      ``52-local-human`` came back as an add, which is precisely the pair
      :func:`containment` recovers at 0.71.
    * It has a similarity threshold and a rename limit, so a heavily-edited rename
      can fall out of the list entirely.

    Parsing is separated from running git so the guards need no repository.
    """
    out: list[tuple[str, str, int]] = []
    for line in name_status.splitlines():
        parts = line.split("	")
        if len(parts) != 3 or not parts[0].startswith("R"):
            continue
        score = parts[0][1:]
        out.append((parts[1], parts[2], int(score) if score.isdigit() else 0))
    return out


def render_git_renames(renames: list[tuple[str, str, int]]) -> str:
    if not renames:
        return "git detected no renames in this range."
    lines = [
        f"{len(renames)} RENAME(S) GIT DETECTED IN THIS RANGE — exact, not inferred.",
        "",
        "A path on the right may look like a clean-add here while the path on the",
        "left is a file you already hold. Resolve each as a rename before applying:",
        "",
    ]
    lines += [f"  R{score:03d}  {old}\n        -> {new}" for old, new, score in renames]
    lines += [
        "",
        "Git's detection is 1:1, so a SPLIT shows one rename and the other targets as",
        "plain adds. The similarity candidates below cover that case.",
    ]
    return "\n".join(lines)


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
