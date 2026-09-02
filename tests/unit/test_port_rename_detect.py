"""The rename detector catches the two traps it was written for (J72).

Both are reconstructed from the 2026-09-01 company apply. A detector that cannot
reproduce the defect it exists for proves nothing (the J26 idiom), and here there
are two real defects to reproduce rather than an injected one.

Pure text in, candidates out — no repository, so these run producer-side where no
consumer tree exists.
"""

from __future__ import annotations

from drydocs.port.port_rename_detect import (
    MAX_MATCHES_PER_ADD,
    SIMILARITY_FLOOR,
    compare,
    containment,
    discounted_pair,
    discriminating,
    id_set,
    jaccard,
    normalized_text,
    overlap,
    parse_git_renames,
    rename_candidates,
    render_git_renames,
    report,
    structural_candidates,
    text_similarity,
    vanished_twin_candidates,
)

# ---- trap 1: the vocabulary fragment split -----------------------------------
# 41-local-seal.yaml became 41-local-business-application.yaml + 52-local-human.yaml
# at gate vocabulary-domains-and-id-policy §A1/§A2. The new paths were clean-adds;
# their entries already existed. Cost: 16 duplicated ids, 62 failures, one revert.

COMPANY_SEAL_FRAGMENT = """
# 41-local-seal.yaml — the SEAL domain
local_relationships:
  - id:           seal_has_port
    neo4j_label:  HAS_PORT
    status:       active
  - id:           seal_owns_application
    neo4j_label:  OWNS
    status:       active
  - id:           seal_appuser_owned_by
    neo4j_label:  OWNED_BY
    status:       active
"""

PRODUCER_BUSINESS_APPLICATION_FRAGMENT = """
# 41-local-business-application.yaml — renamed from 41-local-seal at the gate
local_relationships:
  - id:           seal_has_port
    neo4j_label:  HAS_PORT
    status:       deprecated
    superseded_by: business_application_has_port
  - id:           seal_owns_application
    neo4j_label:  OWNS
    status:       active
  - id:           business_application_has_port
    neo4j_label:  HAS_PORT
    status:       active
"""


def test_the_fragment_rename_is_caught() -> None:
    """A clean-add by path whose ids already live under another filename."""
    candidates = rename_candidates(
        proposed={
            "vocab/41-local-business-application.yaml": PRODUCER_BUSINESS_APPLICATION_FRAGMENT
        },
        existing={"vocab/41-local-seal.yaml": COMPANY_SEAL_FRAGMENT},
    )
    assert len(candidates) == 1
    assert candidates[0].existing == "vocab/41-local-seal.yaml"
    assert candidates[0].score >= SIMILARITY_FLOOR


def test_the_id_measure_catches_a_split_the_text_measure_would_rank_lower() -> None:
    """This is why the id measure exists, and the case that justifies keeping it.

    A fragment SPLIT moves entries into a file whose prose shares almost nothing
    with the source — different header, different domain, different comments. The
    ids are the only thing that survives the move, so text similarity alone would
    score it lower. 52-local-human.yaml was exactly this: entries lifted out of
    41-local-seal.yaml and 42-local-catalog.yaml into a file that reads nothing
    like either.
    """
    source = """
local_relationships:
  - id: seal_appuser_owned_by
    domain: business_application
    note: the functional account ownership edge, filed with the SEAL batch family
  - id: seal_person_manages
    domain: business_application
    note: filed here because the SEAL extract is where the roster arrived
  - id: seal_person_reports_to
    domain: business_application
    note: the employee hierarchy edge, awaiting its own domain
"""
    split_out = """
local_relationships:
  - id: seal_appuser_owned_by
    domain: human
    prov_maps_to: prov:wasAttributedTo
  - id: seal_person_manages
    domain: human
    prov_maps_to: org:headOf
  - id: seal_person_reports_to
    domain: human
    prov_maps_to: org:reportsTo
"""
    text_only = text_similarity(normalized_text(split_out), normalized_text(source))
    id_score, basis = compare(split_out, source)
    assert basis == "id-set", "the ids are what survive a split"
    assert id_score == 1.0, "every entry moved intact"
    assert text_only < id_score, (
        "the text measure scores this pair lower than the id measure — remove the "
        "id measure and a split would rely on prose that a split rewrites"
    )


# ---- trap 2: the gate prompt twin --------------------------------------------
# legacy-crosswalk.yaml (company, DRAFT/unsigned) vs cdo-crosswalk.yaml (producer,
# SIGNED OFF 13 confirmations). Applying the producer's copy would have imported a
# signature the company deliberately withholds, into a canonical-company path.
# The headers differ most, which is why comments are stripped before comparing.

COMPANY_GATE_PROMPT = """
# SME gate-prompt spec — legacy vocabulary crosswalk.
# DRAFT cdo-crosswalk.yaml company-side — arrives UNSIGNED per the 2026-08-06 port
# ruling (producer gate-prompts land as drafts). A company gate session is pending.
id: legacy-crosswalk
title: the crosswalk gate
sections:
  - title: A. the framework rows
  - title: B. the vocabulary bindings
  - title: C. the fence
"""

PRODUCER_GATE_PROMPT = """
# SME gate-prompt spec — CDO vocabulary crosswalk (backlog W1).
# SIGNED OFF 2026-08-05 (gate-log; 13 confirmations ACCEPTED IN FULL, chad.wilson).
id: cdo-crosswalk
title: the crosswalk gate
sections:
  - title: A. the framework rows
  - title: B. the vocabulary bindings
  - title: C. the fence
"""


def test_the_gate_prompt_twin_is_caught() -> None:
    """The pair whose headers disagree about SIGNED vs DRAFT — the gate-state
    regression, and the more dangerous of the two traps."""
    candidates = rename_candidates(
        proposed={"config/gate-prompts/cdo-crosswalk.yaml": PRODUCER_GATE_PROMPT},
        existing={"config/gate-prompts/legacy-crosswalk.yaml": COMPANY_GATE_PROMPT},
    )
    assert len(candidates) == 1
    assert candidates[0].existing == "config/gate-prompts/legacy-crosswalk.yaml"


def test_the_gate_pair_would_be_missed_by_the_id_measure_alone() -> None:
    """The mirror of the split case, and why `compare` takes the stronger measure.

    Each prompt carries exactly one id, and the rename renamed it
    (`legacy-crosswalk` -> `cdo-crosswalk`), so the ids share nothing. If the id
    measure voted here it would score the pair 0.00 and silence the text measure
    that scores it 0.88 — the signal meant to help would be the one that hid the
    gate-state regression.
    """
    assert id_set(PRODUCER_GATE_PROMPT).isdisjoint(id_set(COMPANY_GATE_PROMPT))
    score, basis = compare(PRODUCER_GATE_PROMPT, COMPANY_GATE_PROMPT)
    assert basis == "normalized-text"
    assert score >= SIMILARITY_FLOOR


def test_normalization_removes_the_signed_vs_draft_header_difference() -> None:
    """The headers are where a rename differs MOST — one says SIGNED OFF with a
    name and 13 confirmations, the other DRAFT and UNSIGNED. Comparing raw text
    lets that difference argue these are different documents, when it is the
    single most important reason to look at them together."""
    assert "signed off" not in normalized_text(PRODUCER_GATE_PROMPT)
    assert "draft" not in normalized_text(COMPANY_GATE_PROMPT)
    assert "the crosswalk gate" in normalized_text(PRODUCER_GATE_PROMPT)


# ---- the boundaries ----------------------------------------------------------


def test_a_path_present_on_both_sides_is_never_a_rename() -> None:
    """That is a COLLISION, which the manifest already routes by disposition.
    Reporting it here would bury the real signal in rows nobody needs."""
    assert (
        rename_candidates(
            proposed={"config/a.yaml": COMPANY_SEAL_FRAGMENT},
            existing={"config/a.yaml": COMPANY_SEAL_FRAGMENT},
        )
        == []
    )


def test_unrelated_files_are_not_flagged() -> None:
    """The floor has to hold, or the check gets muted — which is how a noisy
    guard becomes no guard at all."""
    assert (
        rename_candidates(
            proposed={"config/new.yaml": "local_relationships:\n  - id: totally_unrelated_thing\n"},
            existing={"config/old.yaml": COMPANY_SEAL_FRAGMENT},
        )
        == []
    )


def test_a_different_directory_is_skipped_by_default() -> None:
    """Both known traps were in-directory renames, and a whole-tree comparison is
    quadratic for a signal that would mostly be noise. Opt in deliberately."""
    proposed = {"a/41-local-business-application.yaml": PRODUCER_BUSINESS_APPLICATION_FRAGMENT}
    existing = {"b/41-local-seal.yaml": COMPANY_SEAL_FRAGMENT}
    assert rename_candidates(proposed, existing) == []
    assert rename_candidates(proposed, existing, same_directory_only=False)


def test_id_set_survives_a_file_that_does_not_parse() -> None:
    """A half-applied port is exactly when this is needed, so the scanner must not
    depend on the document loading — a YAML error would switch the check off at
    the moment it matters most."""
    assert id_set("local_relationships:\n  - id: kept\n  bad: [unclosed\n") == {"kept"}


def test_normalized_text_drops_comments_and_case() -> None:
    assert normalized_text("# HEADER\nTitle:  The Thing\n") == "title: the thing"


def test_the_report_says_it_is_not_a_verdict() -> None:
    """The output must not read as a decision. Every one of these pairs can
    legitimately be adopted, declined, or dismissed, and the port's failures came
    from acting without looking rather than from looking and choosing wrong."""
    candidates = rename_candidates(
        proposed={"config/gate-prompts/cdo-crosswalk.yaml": PRODUCER_GATE_PROMPT},
        existing={"config/gate-prompts/legacy-crosswalk.yaml": COMPANY_GATE_PROMPT},
    )
    text = report(candidates)
    assert "REPORT, not a verdict" in text
    assert "ADOPT" in text and "DECLINE" in text and "false positive" in text
    assert "canonical-company" in text, "the gate-state trap must be named in the output"
    assert "no proposed clean-add" in report([])


# ---- the two signals added AFTER the company measured the coverage ------------
# The content measures caught 3 of 8 real pairs. The one that mattered most,
# 41-local-business-application <-> 41-local-seal, scored 0.29 on a 0.35 floor —
# the trap that cost 62 failures, missed by the tool built for it. These two
# signals were contributed and motivated by that measurement.


def test_the_same_slot_signal_catches_what_the_content_measures_missed() -> None:
    """A numbered directory numbers its SLOTS, so same number + different stem is
    rename evidence needing no content at all.

    Reconstructed at the real scores: the content measures put this pair at 0.29,
    below the floor. The structural signal does not consult content, so the
    migration that moved entries AND renamed their ids cannot suppress it.
    """
    proposed = {
        "vocab/41-local-business-application.yaml": (
            "business_application_has_port owns_deployment qualified_attribution declared active"
        )
    }
    existing = {
        "vocab/41-local-seal.yaml": (
            "seal_requires_scheduler batch_window escalation_route controlm_folder legacy"
        )
    }
    assert (
        compare(*proposed.values(), *existing.values())[0] < SIMILARITY_FLOOR
    ), "the fixture must be BELOW the content floor, or this proves nothing"
    found = rename_candidates(proposed, existing)
    assert [c.basis for c in found] == ["same-slot-prefix"]
    assert found[0].existing == "vocab/41-local-seal.yaml"


def test_a_different_slot_is_not_a_slot_rename() -> None:
    """The signal must stay narrow: 52- and 41- are different slots and a match
    between them is a SPLIT, which the vanished-twin signal handles on a different
    basis. Widening this one would flag every file in a numbered directory."""
    assert not structural_candidates(
        {"vocab/52-local-human.yaml": "a"}, {"vocab/41-local-seal.yaml": "a"}
    )


def test_the_vanished_twin_signal_catches_a_split_into_a_new_slot() -> None:
    """The case NEITHER other signal reaches, and the last of the eight real pairs.

    41-local-seal.yaml vanished; its entries went to two files, one of them
    52-local-human.yaml. Different slot, so the structural signal is blind; the
    same migration renamed the ids, so the content score fell to 0.30. But a file
    the producer no longer has is a strong prior on its own — it was renamed,
    split, or deleted, and all three are decisions.
    """
    proposed = {
        "vocab/52-local-human.yaml": """
local_relationships:
  - id: seal_appuser_owned_by
    status: deprecated
    superseded_by: human_appuser_owned_by
  - id: human_appuser_owned_by
  - id: human_reports_to
"""
    }
    existing = {
        "vocab/41-local-seal.yaml": """
local_relationships:
  - id: seal_appuser_owned_by
  - id: seal_has_port
  - id: seal_owns_application
"""
    }
    # The consumer file is absent from the producer tree — that is what "vanished"
    # means. The content floor is raised out of the way so ONLY the vanished-twin
    # signal can produce this pair: that independence is the property under test,
    # and the real pair scored 0.30 against a 0.35 floor for exactly this reason.
    found = rename_candidates(
        proposed, existing, floor=0.9, producer_paths={"vocab/52-local-human.yaml"}
    )
    assert [c.basis for c in found] == ["vanished-twin"]

    # WITHOUT the producer path set the signal cannot fire — it is opt-in, because
    # only the caller knows which consumer paths the producer still has.
    assert rename_candidates(proposed, existing, floor=0.9) == []


def test_a_consumer_file_the_producer_still_has_is_not_vanished() -> None:
    """The prior only holds for a file the producer DROPPED. A path present on both
    sides is an ordinary collision and must not drag every add into the report."""
    assert not vanished_twin_candidates(
        {"vocab/new.yaml": "local_relationships:\n  - id: shared\n"},
        {"vocab/kept.yaml": "local_relationships:\n  - id: shared\n"},
        producer_paths={"vocab/kept.yaml", "vocab/new.yaml"},
    )


def test_a_clean_run_says_it_is_not_a_guarantee() -> None:
    """Exit 0 meant "clean" while the 62-failure pair scored 0.29. The company's
    framing — necessary, not sufficient — belongs in the tool, not just in the
    session that discovered it, or the next reader trusts the exit code."""
    text = report([])
    assert "NOT A GUARANTEE" in text
    assert "necessary, not sufficient" in text
    assert "3 of 8" in text, "the measurement that motivated the extra signals is the evidence"


def test_the_true_twin_is_not_hidden_behind_a_higher_scoring_coincidence() -> None:
    """A best-match report is a RANKING presented as an IDENTIFICATION.

    THIS TEST'S ORIGINAL FIXTURE WAS BUILT TO CONFIRM A WRONG HYPOTHESIS, and that
    is worth more than the property it checks. It was written believing the real
    `cdo-alignment.yaml` twin cleared the floor and was dropped by the best-match
    rule — so the fixture was authored to put a second file above the floor, and it
    passed. The company then MEASURED the real pair: 0.08, rank 13 of 29, never
    near the floor. A fixture written to match a hypothesis proves the hypothesis,
    not the tree; the real pair needed :func:`containment`, not a bigger cap.

    The property below is still real and still worth guarding — two files above the
    floor must both be reported — so the test stays. Its claim is now scoped to
    what it actually demonstrates, and the case it was WRITTEN for is covered by
    `test_containment_finds_a_twin_that_jaccard_buries`.
    """
    proposed = {"epics/cdo-alignment.yaml": "alignment crosswalk rows framework bindings shared"}
    existing = {
        # scores higher by accident — more shared filler tokens
        "epics/ddlineage-retirement.yaml": (
            "alignment crosswalk rows framework bindings shared retirement ledger extra"
        ),
        # the REAL twin, above the floor but ranked second
        "epics/legacy-alignment.yaml": "alignment crosswalk rows framework bindings",
    }
    found = rename_candidates(proposed, existing)
    reported = {c.existing for c in found}
    assert "epics/legacy-alignment.yaml" in reported, (
        "the true twin cleared the floor and must be reported even when another " "file outranks it"
    )
    assert len(found) >= 2, "both above-floor matches are evidence; one is a guess"
    assert [c.score for c in found] == sorted(
        (c.score for c in found), reverse=True
    ), "still ranked — the cap is on how many, not on whether they are ordered"


def test_the_match_list_is_capped_so_a_common_file_cannot_bury_the_signal() -> None:
    """The failure at the other end: reporting everything makes a boilerplate-heavy
    file match a dozen others and drowns the pair that matters.

    FOUR files, deliberately below MIN_CORPUS_FOR_IDF. Above it, idf strips the
    shared tokens and NOTHING matches — which is idf doing the same job better. The
    cap is what protects a directory too small for document frequency to mean
    anything, and the two cover different regimes rather than overlapping.
    """
    shared = "alignment crosswalk rows framework bindings"
    existing = {f"epics/other-{n}.yaml": shared for n in range(4)}
    found = rename_candidates({"epics/new.yaml": shared}, existing)
    assert len(found) == MAX_MATCHES_PER_ADD

    # AND THE GUARANTEE THE REGRESSION DEMANDED: idf can never strip a pair to
    # nothing. Six identical files means EVERY token is boilerplate, so the discount
    # would leave zero — at which point the stub veto fires and the comparison runs
    # raw. The report stays bounded by the cap rather than going silently empty,
    # because an empty report on a directory that contains a rename is the one
    # output a reviewer acts on without looking.
    long_shared = " ".join(f"boiler{i}" for i in range(30))
    big = {f"epics/other-{n}.yaml": long_shared for n in range(6)}
    still_found = rename_candidates({"epics/new.yaml": long_shared}, big)
    assert len(still_found) == MAX_MATCHES_PER_ADD, "bounded by the cap, never silenced"


def test_containment_finds_a_twin_that_jaccard_buries() -> None:
    """The real pair, at the real sizes, contributed by the company session.

    An 11-token producer stub against the 97-token company epic it was reduced
    from, sharing 8 tokens. Jaccard puts the UNION on the bottom — 8/100 — and
    scores 0.08, rank 13 of 29, nowhere near the floor. Containment divides by the
    SMALLER set — 8/11 — and scores 0.73, rank 1.

    This is arithmetic, not tuning: a producer file is regularly a reduction or an
    expansion of its consumer twin, so Jaccard reads the normal shape of a rename
    as dissimilarity.
    """
    shared = [f"tok{n}" for n in range(8)]
    stub = " ".join([*shared, "stubonly1", "stubonly2", "stubonly3"])  # 11
    epic = " ".join([*shared, *(f"epiconly{n}" for n in range(89))])  # 97
    a, b = set(stub.split()), set(epic.split())
    assert len(a) == 11 and len(b) == 97 and len(a & b) == 8

    assert jaccard(a, b) < SIMILARITY_FLOOR, "Jaccard buries it below the floor"
    assert containment(a, b) >= SIMILARITY_FLOOR, "containment clears it"
    assert overlap(a, b) == containment(a, b), "the stronger measure wins"

    found = rename_candidates(
        {"epics/cdo-alignment.yaml": stub}, {"epics/legacy-alignment.yaml": epic}
    )
    assert [c.existing for c in found] == ["epics/legacy-alignment.yaml"]


def test_containment_over_fires_alone_which_is_why_the_cap_is_load_bearing() -> None:
    """The caveat shipped WITH the contribution, and verified independently on the
    producer tree: `component-topology.yaml` at 428 tokens reaches containment 0.64
    against an 11-token stub on Jaccard 0.02 — purely by being large enough to
    contain it.

    So containment is not adopted alone. It surfaces the twin the union-denominator
    buried; the cap keeps its size-driven false positives from burying it again.
    Neither half is sufficient, which is the finding.
    """
    stub = set("a b c d e f g h i j k".split())
    big = stub | {f"unrelated{n}" for n in range(400)}
    assert containment(stub, big) == 1.0, "a big file trivially contains a small one"
    assert jaccard(stub, big) < 0.05, "and Jaccard correctly calls it dissimilar"
    # the cap is what keeps a directory full of large files from drowning the report
    # FOUR files, below MIN_CORPUS_FOR_IDF: idf abstains, so the cap is the only
    # thing standing between the reader and a page of matches. That is the regime
    # this test is about — in a larger directory idf removes the shared tokens first.
    existing = {f"epics/big-{n}.yaml": " ".join(big) for n in range(4)}
    assert (
        len(rename_candidates({"epics/stub.yaml": " ".join(stub)}, existing)) == MAX_MATCHES_PER_ADD
    )


def test_the_strongest_claim_wins_a_duplicate_not_the_first_one_found() -> None:
    """Order of discovery is not evidence of strength.

    The content pass runs before the structural pass, so a pair both find was
    reported on the WEAKER basis: `41-local-business-application` <- `41-local-seal`
    came back as normalized-text 0.57 while the same-slot claim of 1.00 was dropped
    as "already seen". A reader acts on the basis, so reporting the weaker one is a
    downgrade disguised as deduplication.
    """
    proposed = {"vocab/41-local-business-application.yaml": "alpha beta gamma delta epsilon zeta"}
    existing = {"vocab/41-local-seal.yaml": "alpha beta gamma delta epsilon eta"}
    found = rename_candidates(proposed, existing)
    pair = [c for c in found if c.existing == "vocab/41-local-seal.yaml"]
    assert len(pair) == 1, "one row per pair, not one per signal"
    assert pair[0].basis == "same-slot-prefix"
    assert pair[0].score == 1.0


def test_the_cap_is_per_file_across_signals_not_per_signal() -> None:
    """Three signals each capped at three is a cap of nine, which on the real
    vocabulary sweep produced twenty rows for six files — the noise that invites a
    reader to dismiss the whole report."""
    shared = " ".join(f"tok{n}" for n in range(20))
    proposed = {"vocab/41-local-new.yaml": shared}
    # Four, not eight: above MIN_CORPUS_FOR_IDF the shared tokens are stripped as
    # directory boilerplate and nothing matches at all — which is idf working.
    existing = {f"vocab/41-local-old{n}.yaml": shared for n in range(4)}
    found = rename_candidates(proposed, existing, producer_paths={"vocab/41-local-new.yaml"})
    assert len(found) == MAX_MATCHES_PER_ADD
    assert all(c.proposed == "vocab/41-local-new.yaml" for c in found)


# ---- git already knew (2026-09-01) -------------------------------------------
# The SME asked whether the commit ritual should go per-module to prevent this.
# It would not have: the vocabulary rename was ALREADY a 6-file, ontology-scoped
# commit. Nothing was missing from the commit — the rename metadata was missing
# from the PORT, which classifies by path and never reads history.


def test_git_rename_output_is_parsed_exactly() -> None:
    """`git diff -M --diff-filter=R --name-status` is authoritative where the
    similarity measures are heuristic. Measured on the real consumer range: 18
    renames, every 2026-09-01 trap among them."""
    sample = "\n".join(
        [
            "R097\tvocab/40-local-controlm.yaml\tvocab/40-local-scheduler.yaml",
            "R075\tconfig/gate-prompts/legacy-crosswalk.yaml\tconfig/gate-prompts/cdo-crosswalk.yaml",
            "R090\tdrydocs/docs_verify.py\tdrydocs_core/docs_verify.py",
            "M\tsome/edited/file.py",  # not a rename; must be ignored
            "A\tsome/added/file.py",
        ]
    )
    parsed = parse_git_renames(sample)
    assert len(parsed) == 3
    assert parsed[0] == ("vocab/40-local-controlm.yaml", "vocab/40-local-scheduler.yaml", 97)
    # the cross-DIRECTORY move is in the list — the same-directory heuristic skips it
    assert ("drydocs/docs_verify.py", "drydocs_core/docs_verify.py", 90) in parsed


def test_the_git_report_states_its_one_to_one_limit() -> None:
    """Git matches one old path to one new path, so a SPLIT reports one rename and
    the other targets as plain adds — which is exactly the pair containment
    recovers. A reader who does not know that will trust the exact list as complete."""
    text = render_git_renames([("a/old.yaml", "a/new.yaml", 97)])
    assert "exact, not inferred" in text
    assert "1:1" in text and "SPLIT" in text
    assert "R097" in text
    assert "git detected no renames" in render_git_renames([])


def test_idf_drops_a_directory_schema_that_every_file_shares() -> None:
    """Contributed by the company session after measuring the cost of recall.

    Backlog items share a schema, so nearly every proposed item matched several
    others at 0.40-0.60 on `id:` / `epic:` / `status:` alone — 252 pairs in one
    directory for roughly two real ones. Structure survives a rename and so does
    content; only CONTENT identifies.

    This matters as much as recall for a reason measured twice this session: a
    reviewer handed 252 pairs will skim, and skimming is how the twin got taken in
    the first place. A report nobody reads is the same outcome as no report.
    """
    schema = "id: epic: status: acceptance: notes: type: module: phase: agent: model:"

    def item(tag: str) -> str:
        # long enough that the discount leaves more than MIN_TOKENS_FOR_CONTAINMENT,
        # or the stub veto fires and this would be testing the veto, not idf
        return schema + " " + " ".join(f"{tag}{i}" for i in range(12))

    existing = {f"items/{n}.yaml": item(n) for n in ("A1", "B2", "C3", "D4", "E5")}
    existing["items/OLD.yaml"] = item("zeta")
    proposed = {"items/NEW.yaml": item("zeta")}  # schema shared with all; content with one

    found = rename_candidates(proposed, existing)
    assert [c.existing for c in found] == ["items/OLD.yaml"], (
        "only the file sharing distinctive content is a candidate; the five sharing "
        "only the directory's schema are not"
    )


def test_idf_abstains_in_a_directory_too_small_to_measure() -> None:
    """In a three-file directory every shared token trivially exceeds any ceiling,
    so document frequency is noise. Small directories keep the unfiltered
    comparison — where the pair count is small enough to read anyway."""
    freq = {"shared": 3}
    assert discriminating("shared unique", freq, 3) == "shared unique"
    # above the threshold the same token is dropped as boilerplate
    assert discriminating("shared unique", {"shared": 5}, 5) == "unique"


def test_the_idf_discount_never_switches_containment_off() -> None:
    """THE STUB VETO — the regression that produced a FALSE ALL-CLEAR.

    Reconstructed from the real incident. A ten-token stub whose tokens ARE the
    directory's shared scaffolding, against the larger twin it was reduced from. The
    discount leaves the stub FIVE tokens — below MIN_TOKENS_FOR_CONTAINMENT — so
    containment abstains, Jaccard alone scores 0.09 against a 0.35 floor, and the
    pair vanishes. idf does not out-score containment here; it switches it off.

    That is the worst output this tool can produce: a directory containing a real
    rename reporting "no proposed clean-add resembles an existing file", which is
    the one result a reviewer acts on without looking.
    """
    scaffold = "id: title: order: letter: groom_log: epic alignment status"
    stub = f"{scaffold} distinctive_marker"
    twin = stub + " " + " ".join(f"detail{i} expanded prose retained" for i in range(20))
    # a directory whose files all share the scaffold — so the discount targets it
    corpus = {f"epics/other-{n}.yaml": f"{scaffold} filler{n}" for n in range(8)}
    corpus["epics/legacy-alignment.yaml"] = twin

    found = rename_candidates({"epics/cdo-alignment.yaml": stub}, corpus)
    assert any(c.existing == "epics/legacy-alignment.yaml" for c in found), (
        "the known-real pair must survive the idf discount — losing it is a false "
        "all-clear on a directory that contains a rename"
    )


def test_the_veto_is_decided_per_pair_not_per_file() -> None:
    """Discounting one side and not the other is worse than either.

    The stub's tokens would survive on the stub and be stripped from the twin, so the
    overlap goes to zero and the pair is lost just as surely. If the discount would
    gut EITHER side, both are compared raw.
    """
    freq = {"shared": 20, "rare": 1}
    corpus_size = 20
    short = "shared shared rare"
    long = " ".join(["shared"] + [f"uniq{i}" for i in range(20)])
    a, b = discounted_pair(short, long, freq, corpus_size)
    assert set(a.split()) == set(normalized_text(short).split()), "short side kept raw"
    assert set(b.split()) == set(normalized_text(long).split()), "so is its partner"
