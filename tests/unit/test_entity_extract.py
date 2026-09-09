"""MM3 — the shared entity/ID extractor: typed matches with spans, table-driven.

Every string here is synthetic. 5-digit ids sit in the reserved block
70001-70099 (test_publish_boundary_values sweeps every tracked file for any
other), domains are ``.invalid``, project keys and schema names are plain words.

CORE5 widened the class to the measured 4-to-7-digit range, and those widths have
no reserved block. The values below extend the same ``700`` prefix (``7001``,
``700011``, ``7000111``) so they still read as block-family. Which sweep can see
them: Scan A (bare 5-6 digit ids) is scoped to config/taxonomy, the sample CSVs
and knowledge/, so it does not reach this file at all; Scan B reads numeric
segments out of folder-shaped tokens in EVERY tracked file, so ``_FOLDER_WIDE``
below carries an allowlist row in test_publish_boundary_values.py with its reason.
"""

from __future__ import annotations

import pytest

from drydocs_core import entity_extract as ex
from drydocs_core.entity_extract import EntityMatch, extract_entities, values

_GUID = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
_FOLDER = "PRARAG-HLDM-70002-PEX-RFND-DLY"

# The measured widths the 70001-70099 block cannot express (see the docstring).
_ID_4 = "7001"
_ID_6 = "700011"
_ID_7 = "7000111"
#: The same folder shape carrying a SIX-digit id segment — an ordinary width in
#: the live population that the pre-CORE5 `len(seg) == 5` test dropped silently.
_FOLDER_WIDE = "PRARAG-HLDM-700011-PEX-RFND-DLY"
#: ... and a FOUR-digit segment, which stays out: this pass scans every segment
#: rather than reading position 3, so at four digits a segment is as likely a
#: year or a sequence number as an id.
_FOLDER_NARROW = "PRARAG-HLDM-7001-PEX-RFND-DLY"


def _kinds(text: str) -> list[tuple[str, str]]:
    return [(m.kind, m.value) for m in extract_entities(text)]


# ---- one class at a time ----------------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # guid — bare, and cued by the launcher flag spellings shell.py knows
        (f"id {_GUID} seen", [(ex.GUID, _GUID)]),
        (f"-pipeline {_GUID}", [(ex.GUID, _GUID)]),
        # issue key — project key upper-case, a number; lower-case is not a key
        ("fixed in AUTO-1234 yesterday", [(ex.ISSUE_KEY, "AUTO-1234")]),
        ("fixed in auto-1234 yesterday", []),
        ("DATA2-77 and DATA2-78", [(ex.ISSUE_KEY, "DATA2-77"), (ex.ISSUE_KEY, "DATA2-78")]),
        # table name — SCHEMA.OBJECT upper-case dotted pair; lower-case dotted
        # tokens (hosts, versions, module paths) are not
        ("loads STAGE.ORDERS_DAILY nightly", [(ex.TABLE_NAME, "STAGE.ORDERS_DAILY")]),
        ("see drydocs_core.run_log for it", []),
        ("host box.example.invalid", []),
        # distribution list — DL-prefixed, with or without the mailbox domain
        (
            "cc DL-Batch-Support@example.invalid.",
            [(ex.DISTRIBUTION_LIST, "DL-Batch-Support@example.invalid")],
        ),
        ("page DL_ops_tier2 first", [(ex.DISTRIBUTION_LIST, "DL_ops_tier2")]),
        # A bare `DL` is not a distribution list — the class needs the `DL-`/`DL_`/`DL.`
        # prefix shape. Since MM12 it IS an acronym candidate, which is the right
        # reading of it and does not weaken this case: the assertion is still that
        # nothing here is a DISTRIBUTION_LIST.
        ("the DL is on the thread", [(ex.ACRONYM, "DL")]),
        # application id — a standalone 4-to-7-digit run (CORE5), reported bare
        # only from 5 up. `700041` is an order number, not an id: at six digits
        # it IS a candidate and IS reported, uncued, for the caller to rank down.
        ("seal 70004", [(ex.APPLICATION_ID, "70004")]),
        ("order 700041 rejected", [(ex.APPLICATION_ID, "700041")]),
        ("run 4 of 12", []),
        # nothing at all
        ("", []),
        ("plain prose with no identifiers", []),
    ],
)
def test_each_class_on_its_own(text: str, expected: list[tuple[str, str]]) -> None:
    assert _kinds(text) == expected


def test_spans_index_the_text_they_matched() -> None:
    text = "cc DL-Batch-Support@example.invalid, key AUTO-1234, table STAGE.ORDERS_DAILY"
    for m in extract_entities(text):
        assert text[m.start : m.end] == m.value, m


# ---- the folder name, and the precedence it forces ----------------------------


def test_folder_name_is_decoded_positionally_and_its_id_segment_is_an_application_id() -> None:
    matches = extract_entities(f"folder {_FOLDER} failed")
    by_kind = {m.kind: m for m in matches}
    folder = by_kind[ex.FOLDER_NAME]
    assert folder.value == _FOLDER
    assert folder.attribute("environment_code") == "P"
    assert folder.attribute("lob_code") == "R"
    assert folder.attribute("app_code") == "ARA"
    assert folder.attribute("folder_type_code") == "G"
    assert folder.attribute("segments") == "HLDM-70002-PEX-RFND-DLY"
    app = by_kind[ex.APPLICATION_ID]
    assert (app.value, app.cued, app.attribute("cue")) == ("70002", True, "folder-segment")
    assert f"folder {_FOLDER} failed"[app.start : app.end] == "70002"


def test_the_folder_wins_over_the_issue_key_shape_inside_it() -> None:
    """``HLDM-70002`` has the exact shape of an issue key. The folder pass runs
    first and claims the whole span, so the key reading never fires — the
    collision the pass order exists for."""
    kinds = [m.kind for m in extract_entities(_FOLDER)]
    assert ex.ISSUE_KEY not in kinds
    assert kinds.count(ex.APPLICATION_ID) == 1  # from the folder pass, not the bare pass


def test_a_folder_shaped_token_the_decoder_does_not_recognise_is_not_a_folder() -> None:
    """Six letters and two segments is the SHAPE; the decode still has to
    recognise the environment position. `XYZABC` is no environment."""
    matches = extract_entities("XYZABC-HLDM-70003-DLY")
    assert ex.FOLDER_NAME not in {m.kind for m in matches}
    # An issue key is a standalone token: `HLDM-70003` glued into a dash-joined
    # token is not one, so nothing claims it — and the bare 5-digit pass then
    # reports the segment as an UNCUED application id (reported, not ranked).
    assert [(m.kind, m.value, m.cued) for m in matches] == [(ex.APPLICATION_ID, "70003", False)]


def test_pipeline_like_prose_does_not_pass_as_a_folder() -> None:
    """`parse_folder_name` alone accepts any >=6-char P/D/Q token; the shape
    gate in front of it is what keeps `PIPELINE-ID-1` out."""
    assert ex.FOLDER_NAME not in {m.kind for m in extract_entities("PIPELINE-ID-1 ran")}


# ---- application-id cues ------------------------------------------------------


@pytest.mark.parametrize(
    ("text", "cued", "cue"),
    [
        ("-seal 70005 -i", True, "keyword"),
        ("spark.kubernetes.seal=70005", True, "keyword"),
        ('"APP_ID": "70005"', True, "keyword"),
        ("application 70005", True, "keyword"),
        ("70005/raw/flow-name/x.csv", True, "landing-prefix"),
        ("70005 - Ingestion design", False, None),  # a page title: reported, not cued
    ],
)
def test_application_id_is_always_reported_and_marked_when_cued(
    text: str, cued: bool, cue: str | None
) -> None:
    apps = [m for m in extract_entities(text) if m.kind == ex.APPLICATION_ID]
    assert len(apps) == 1
    assert (apps[0].value, apps[0].cued, apps[0].attribute("cue")) == ("70005", cued, cue)


# ---- the measured width, and the floor that keeps it precise (CORE5) ----------
#
# The width is the ledger's, not a guess: config/source-mappings/pat-team-report.yaml,
# the `Seal IDs` row — "token width is 4 to 7 digits, never assume 5 or 6"
# (profile SME-reported 2026-09-07, cited by the K30 close note). The rule the
# extractor implements on top of it is ONE sentence: the bare floor is five, and
# four digits are reported only when the text names the token. These cases are
# that sentence, both halves, because widening a bare-digit pattern buys false
# positives and the cue is the only thing that pays for them.


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # (b) four, six and seven digits carried through, cued by each cue shape
        (f"seal {_ID_4}", [_ID_4]),
        (f"-seal {_ID_6} -i", [_ID_6]),
        (f'"APP_ID": "{_ID_7}"', [_ID_7]),
        (f"application {_ID_6}", [_ID_6]),
        (f"{_ID_7}/raw/flow-name/x.csv", [_ID_7]),
        # ... and five, six and seven come through BARE as well — the page-title
        # signal the class exists for. Six is the width the old `\d{5}` dropped.
        ("70005 - Ingestion design", ["70005"]),
        (f"{_ID_6} - Ingestion design", [_ID_6]),
        (f"{_ID_7} - Ingestion design", [_ID_7]),
        # (b) the negative: what the wider pattern must NOT swallow. Every one is
        # four digits and uncued — a year, a row count, a port, a small count.
        # This is the entire cost of widening, and the floor is what avoids it.
        ("the 2026 refresh moved the window", []),
        ("processed 1200 rows", []),
        ("the dev server is listening on 5173", []),
        ("run 4 of 12", []),
        (f"{_ID_4} rows rejected", []),
        # ... and the consequence, asserted rather than left to be discovered: a
        # SIX-digit row count is a candidate and IS emitted, uncued. Above the
        # floor the cue is the only discriminator; suppressing it would hide a
        # real six-digit id behind the same shape. The caller ranks.
        ("processed 123456 rows", ["123456"]),
    ],
)
def test_the_measured_width_and_the_floor_that_keeps_it_precise(
    text: str, expected: list[str]
) -> None:
    assert [m.value for m in extract_entities(text) if m.kind == ex.APPLICATION_ID] == expected


def test_a_four_digit_id_needs_the_text_to_name_it() -> None:
    """The floor stated as the pair it is: same token, cue and no cue."""
    assert [m.value for m in extract_entities(f"seal {_ID_4}")] == [_ID_4]
    assert extract_entities(f"{_ID_4} - Ingestion design") == ()
    cued = extract_entities(f"seal {_ID_4}")[0]
    assert (cued.cued, cued.attribute("cue")) == (True, "keyword")


def test_a_wide_folder_segment_is_an_application_id_and_its_span_is_its_own_width() -> None:
    """The folder pass carried the same five-digit belief, plus a hard-coded
    ``offset + 5`` that would have mis-spanned any other width."""
    text = f"folder {_FOLDER_WIDE} failed"
    apps = [m for m in extract_entities(text) if m.kind == ex.APPLICATION_ID]
    assert [(m.value, m.cued, m.attribute("cue")) for m in apps] == [
        (_ID_6, True, "folder-segment")
    ]
    assert text[apps[0].start : apps[0].end] == _ID_6


def test_a_four_digit_folder_segment_is_not_read_as_an_application_id() -> None:
    """Position 3 is where the convention puts the id, and this pass does not
    check position — so four digits stays out here even though a cued four-digit
    token in prose comes through. Enforce the position and it can come back."""
    matches = extract_entities(f"folder {_FOLDER_NARROW} failed")
    assert ex.FOLDER_NAME in {m.kind for m in matches}
    assert ex.APPLICATION_ID not in {m.kind for m in matches}


def test_guid_carries_the_flag_that_named_it() -> None:
    m = extract_entities(f"launch -pipeline {_GUID} -dataset {_GUID}")
    assert [(x.cued, x.attribute("cue")) for x in m] == [(True, "pipeline"), (True, "dataset")]
    bare = extract_entities(f"guid {_GUID}")[0]
    assert (bare.cued, bare.attribute("cue")) == (False, None)


# ---- a mixed line, and the references-out contract --------------------------------


def test_a_mixed_line_reports_every_class_in_text_order() -> None:
    text = (
        f"{_FOLDER}: -seal 70002 -pipeline {_GUID} wrote STAGE.ORDERS_DAILY; "
        f"see AUTO-1234, cc DL-Batch-Support@example.invalid"
    )
    kinds = [m.kind for m in extract_entities(text)]
    assert kinds == [
        ex.FOLDER_NAME,
        ex.APPLICATION_ID,  # the folder segment
        ex.APPLICATION_ID,  # the -seal cue
        ex.GUID,
        ex.TABLE_NAME,
        ex.ISSUE_KEY,
        ex.DISTRIBUTION_LIST,
    ]
    starts = [m.start for m in extract_entities(text)]
    assert starts == sorted(starts)


def test_values_are_distinct_in_first_seen_order_and_filter_by_kind() -> None:
    text = "AUTO-1234 then AUTO-1234 again, seal 70006, DATA2-77"
    matches = extract_entities(text)
    assert values(matches) == ("AUTO-1234", "70006", "DATA2-77")
    assert values(matches, ex.ISSUE_KEY) == ("AUTO-1234", "DATA2-77")
    assert values(matches, ex.APPLICATION_ID, ex.ISSUE_KEY) == ("AUTO-1234", "70006", "DATA2-77")
    assert values(()) == ()


def test_matches_are_hashable_value_objects() -> None:
    a = EntityMatch(ex.ISSUE_KEY, "AUTO-1", 0, 6, attributes=(("project", "AUTO"),))
    assert a == EntityMatch(ex.ISSUE_KEY, "AUTO-1", 0, 6, attributes=(("project", "AUTO"),))
    assert len({a, a}) == 1
    assert a.span == (0, 6)
    assert a.attribute("missing") is None


def test_the_pass_order_is_the_declared_precedence() -> None:
    assert ex.KINDS == (
        ex.GUID,
        ex.FOLDER_NAME,
        ex.ISSUE_KEY,
        ex.TABLE_NAME,
        ex.DISTRIBUTION_LIST,
        ex.APPLICATION_ID,
        ex.ACRONYM,
    )


# ---- the acronym class (MM12) -----------------------------------------------


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        # the plain shapes: letters, and letters with the digits vendors use
        ("the ETL job failed", [(ex.ACRONYM, "ETL")]),
        ("staged into S3 overnight", [(ex.ACRONYM, "S3")]),
        ("runs on EC2 in the east", [(ex.ACRONYM, "EC2")]),
        ("escalate to L2 first", [(ex.ACRONYM, "L2")]),
        # six is the ceiling, seven is a word in caps rather than an acronym
        ("the SIXCHR code", [(ex.ACRONYM, "SIXCHR")]),
        ("the SEVENCH code", []),
        # one character cannot be an acronym, and neither can pure digits: the
        # shape needs two characters and at least one letter, so a bare 4-digit
        # run is left to the application-id floor, which drops it uncued
        ("drive X now", []),
        ("count 4321 rows", []),
        # a lower-case word is not one, and a mixed-case product name is not one
        ("the etl job", []),
        ("uses PowerShell here", []),
    ],
)
def test_acronym_shapes(text: str, expected: list[tuple[str, str]]) -> None:
    assert _kinds(text) == expected


def test_the_acronym_carries_the_sentence_it_was_found_in() -> None:
    """MM12 clause (b), the whole reason this class differs from the other six."""
    text = "The load ran twice. SNOW is ServiceNow and explicitly NOT Snowflake. Then it cleared."
    (snow,) = (m for m in extract_entities(text) if m.kind == ex.ACRONYM and m.value == "SNOW")
    assert snow.attribute("evidence") == (
        "SNOW is ServiceNow and explicitly NOT Snowflake."
    ), "the evidence must be the sentence, not the whole document and not the token"


def test_an_ambiguous_acronym_keeps_two_distinct_evidence_spans() -> None:
    """The acceptance's named case. Two documents say SNOW and mean different
    systems; collapsing them to one reading would destroy the finding, which is
    that they disagree."""
    text = (
        "In the incident notes SNOW (ServiceNow) is where the ticket lives. "
        "In the platform notes SNOW (Snowflake) is where the warehouse lives."
    )
    snow = [m for m in extract_entities(text) if m.kind == ex.ACRONYM and m.value == "SNOW"]
    assert len(snow) == 2
    assert {m.attribute("gloss") for m in snow} == {"ServiceNow", "Snowflake"}
    assert len({m.attribute("evidence") for m in snow}) == 2
    assert len({m.span for m in snow}) == 2


@pytest.mark.parametrize(
    ("text", "gloss"),
    [
        ("we raise it in ServiceNow (SNOW) today", "ServiceNow"),
        ("we raise it in SNOW (ServiceNow) today", "ServiceNow"),
        ("SNOW stands for ServiceNow here", None),
        ("SNOW means ServiceNow here", None),
        ("SNOW is short for ServiceNow", None),
    ],
)
def test_a_glossed_acronym_is_cued_and_records_what_the_gloss_said(
    text: str, gloss: str | None
) -> None:
    """A parenthetical either way round, or a naming verb. The verb forms mark
    the token glossed without capturing an expansion — the sentence carries the
    meaning, and inventing a span for it would be the guessing this module
    refuses."""
    (snow,) = (m for m in extract_entities(text) if m.kind == ex.ACRONYM)
    assert snow.cued is True
    assert snow.attribute("gloss") == gloss


def test_an_unglossed_acronym_is_a_candidate_but_is_not_cued() -> None:
    (etl,) = (m for m in extract_entities("the ETL job failed") if m.kind == ex.ACRONYM)
    assert etl.cued is False and etl.attribute("gloss") is None


def test_the_function_word_floor_drops_emphasis_caps_unless_they_are_glossed() -> None:
    """The 4-digit floor's rule, at the other class. A closed class of function
    words in caps for emphasis carries no information; glossed, it is emitted
    anyway, so the floor cannot hide a real acronym that happens to collide."""
    assert _kinds("THE ONLY thing that MUST NEVER happen is a silent write") == []
    (nb,) = (
        m for m in extract_entities("NO (Norwegian Ordering) is the feed") if m.kind == ex.ACRONYM
    )
    assert (nb.value, nb.cued, nb.attribute("gloss")) == ("NO", True, "Norwegian Ordering")


def test_every_narrower_class_claims_its_span_before_the_acronym_pass_runs() -> None:
    """The precedence the pass order exists for, at the widest shape. HLDM is a
    project key, PSGMGR a schema, PRARAG a folder prefix — none of them may be
    read a second time as an acronym."""
    text = f"{_FOLDER} raised HLDM-4021; query PSGMGR.CMS_JOBS and page DL-ops@example.invalid"
    acronyms = {m.value for m in extract_entities(text) if m.kind == ex.ACRONYM}
    assert (
        acronyms == set()
    ), f"the acronym pass claimed {sorted(acronyms)} out of spans an earlier pass owned"


def test_the_acronym_pass_reads_a_token_no_other_class_wanted() -> None:
    """The other half of the same design: what is left over IS the class's job."""
    text = "MFT moved the file to PSGMGR.CMS_JOBS overnight"
    kinds = _kinds(text)
    assert (ex.TABLE_NAME, "PSGMGR.CMS_JOBS") in kinds
    assert (ex.ACRONYM, "MFT") in kinds
