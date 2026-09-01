"""The rename detector catches the two traps it was written for (J72).

Both are reconstructed from the 2026-09-01 company apply. A detector that cannot
reproduce the defect it exists for proves nothing (the J26 idiom), and here there
are two real defects to reproduce rather than an injected one.

Pure text in, candidates out — no repository, so these run producer-side where no
consumer tree exists.
"""

from __future__ import annotations

from drydocs.port_rename_detect import (
    SIMILARITY_FLOOR,
    compare,
    id_set,
    normalized_text,
    rename_candidates,
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
