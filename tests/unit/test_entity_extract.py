"""MM3 — the shared entity/ID extractor: typed matches with spans, table-driven.

Every string here is synthetic. 5-digit ids sit in the reserved block
70001-70099 (test_publish_boundary_values sweeps every tracked file for any
other), domains are ``.invalid``, project keys and schema names are plain words.
"""

from __future__ import annotations

import pytest

from drydocs_core import entity_extract as ex
from drydocs_core.entity_extract import EntityMatch, extract_entities, values

_GUID = "3f2504e0-4f89-11d3-9a0c-0305e82c3301"
_FOLDER = "PRARAG-HLDM-70002-PEX-RFND-DLY"


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
        ("the DL is on the thread", []),
        # application id — exactly five digits, standalone
        ("seal 70004", [(ex.APPLICATION_ID, "70004")]),
        ("order 700041 rejected", []),
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
    )
