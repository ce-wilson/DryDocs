"""G82 — the raw PAT team report -> the two dev-team loader files.

The loaders, their cypher, their row models and their registrations were all real
and green against a fixture; the INPUT PIPELINE one step upstream did not exist.
These cases pin the projection's contract: its output validates through the two
pydantic row models the loaders actually use (the same shape as the committed
fixtures), it refuses to guess a key header, it picks `Relationship Type` and
never the `Team Type Name` decoy, it counts everything it drops, and its header
map stays in agreement with the column ledger it is the source of.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from drydocs.loaders.catalog import DevTeamRow, PatProductMappingRow
from drydocs.pat_projection import (
    ACKNOWLEDGED_ABSENT,
    DEFAULT_HEADER_MAP,
    DEV_TEAMS_COLUMNS,
    DEV_TEAMS_FILE,
    KNOWN_DROPPED,
    PAT_PRODUCT_MAPPING_COLUMNS,
    PAT_PRODUCT_MAPPING_FILE,
    ProjectionError,
    load_header_map,
    project_rows,
    project_team_report,
)

REPO = Path(__file__).resolve().parents[2]
LEDGER = REPO / "config" / "source-mappings" / "pat-team-report.yaml"


def _recorded_headers() -> list[str]:
    """The 43 column names of the live export, in export order, READ from the
    column ledger — the recorded list (census closed 2026-08-29; re-confirmed
    2026-09-07 against the SME's transposed header sheet, transcribed under
    internal-local and cited from K30's close note). Never from DEFAULT_HEADER_MAP:
    K30 (d) exists because the fixture used to be typed in the same believed
    spellings the code looked for, so the two could be wrong together."""
    doc = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    (obj,) = doc["objects"]
    return [c["name"] for c in obj["columns"]]


# The fixture's header row IS the recorded list — every column of the real export,
# in its order, so the fixture exercises the decoy column, every known-dropped
# column and the absence of `JIRA Board` exactly as a real run would. Values are
# synthetic; SEAL ids sit in the reserved 70001-70099 block the fixtures use.
RAW_HEADERS = _recorded_headers()


def _row(**over: str) -> dict[str, str]:
    base = {h: "" for h in RAW_HEADERS}
    base.update(
        {
            "Team ID": "T0042",
            "Legacy Team ID": "0f0f0f0f-0000-0000-0000-000000000000",
            "Team Name": "CCB Auto Risk Pod",
            "Team LoB Name": "CCB",
            "Product Line Name": "Auto",
            "Product ID": "PROD_AUTO_05",
            "Product Name": "Auto Pricing",
            "Supporting Area Product ID": "AP_AUTO_PUB",
            "Seal IDs": "70051; 70052",
            "Relationship Type": "Dedicated",
            "Team Type Name": "Technology",
            "Team Status": "Active",
            "Agile Framework": "Scrum",
        }
    )
    base.update(over)
    return base


def test_projection_output_validates_through_both_loader_row_models():
    """The deliverable: rows the two loaders would accept, not rows that look right."""
    raw = [
        _row(),
        _row(
            **{
                "Team ID": "T0099",
                "Team Name": "CCB Auto Onboarding",
                "Product ID": "PROD_AUTO_07",
                "Supporting Area Product ID": "",
                "Seal IDs": "70053",
                "Relationship Type": "Aligned",
                "Sponsoring Product ID": "PROD_AUTO_05",
                "Sponsoring Area Product ID": "AP_AUTO_PUB",
            }
        ),
    ]
    teams, mappings, report = project_rows(raw, RAW_HEADERS)
    assert [tuple(t) for t in teams] == [DEV_TEAMS_COLUMNS] * 2
    assert [tuple(m) for m in mappings] == [PAT_PRODUCT_MAPPING_COLUMNS] * 2
    dev = [DevTeamRow.model_validate(t) for t in teams]
    pat = [PatProductMappingRow.model_validate(m) for m in mappings]
    assert [d.team_id for d in dev] == ["T0042", "T0099"]
    assert dev[0].parent_product_id == "PROD_AUTO_05"
    # the real export has no `JIRA Board` column (K30-c): acknowledged, empty, exit-0
    assert dev[0].jira_board_id == "" and report.acknowledged_absent == ("jira_board_id",)
    assert pat[0].seal_ids == "70051, 70052"  # the row model's ';' -> ',' normalisation
    assert pat[0].team_type == "dedicated" and pat[0].area_product_id == "AP_AUTO_PUB"
    assert pat[1].sponsored is True
    assert pat[1].sponsored_product_id == "PROD_AUTO_05"
    assert pat[1].sponsored_area_product_id == "AP_AUTO_PUB"
    assert pat[0].sponsored is False
    assert (report.raw_rows, report.dev_team_rows, report.mapping_rows) == (2, 2, 2)


def test_relationship_type_feeds_team_type_and_the_decoy_never_does():
    """The 2026-08-11 company-side mistake, pinned: Team Type Name is the
    discipline and must not reach team_type even when Relationship Type is
    blank."""
    _, mappings, report = project_rows([_row(**{"Relationship Type": ""})], RAW_HEADERS)
    assert mappings[0]["team_type"] == ""  # not "technology"
    assert report.unrecognised_team_type == 1
    assert "Team Type Name" in report.dropped_by_design
    assert "Team Type Name" in KNOWN_DROPPED


def test_the_seal_column_is_found_by_name_and_the_shape_decoy_never_wins():
    """CORE5 (e) — the SHAPE decoy, sibling of the discipline decoy above.

    `Team ID` is a dense integer surrogate key whose values are SEAL-SHAPED, and
    it is the FIRST column of the 43 while `Seal IDs` is 42 columns later. So any
    discovery of "the seal column" that matches on VALUE SHAPE instead of on
    header name picks `Team ID` before it ever reaches the real one — and writes
    team ids as application ids on the ACTIVE arch_develops edge, silently.
    Exact string membership in `project_rows` is what makes that impossible; this
    test is the reason it must keep being exact.

    The width widening in CORE5 is what makes the decoy worth pinning NOW: with
    the extractor's application-id class at the measured 4-to-7 digits, a
    dense-integer team key is inside the id shape at every width it occurs in.
    """
    # the hazard is positional as well as shaped — read from the recorded list
    assert RAW_HEADERS[0] == "Team ID"
    assert RAW_HEADERS.index("Seal IDs") > RAW_HEADERS.index("Team ID")

    raw = [_row(**{"Team ID": "700051", "Seal IDs": "70061; 70062"})]
    _, mappings, _ = project_rows(raw, RAW_HEADERS)
    pat = PatProductMappingRow.model_validate(mappings[0])

    # the SEAL ids came from `Seal IDs`, by name ...
    assert pat.seal_ids == "70061, 70062"
    # ... and the SEAL-shaped team key never leaked into them
    assert "700051" not in (pat.seal_ids or "")
    assert pat.team_id == "700051"


def test_missing_key_header_is_refused_not_guessed():
    headers = [h for h in RAW_HEADERS if h != "Product ID"]
    with pytest.raises(ProjectionError, match="product_id .*'Product ID'"):
        project_rows([_row()], headers)
    # a re-spelled export is pinned through the header map, not by editing code
    hmap = load_header_map(None)
    hmap["product_id"] = "Product Id"
    _, mappings, _ = project_rows(
        [{**_row(), "Product Id": "PROD_X"}], [*headers, "Product Id"], hmap
    )
    assert mappings[0]["product_id"] == "PROD_X"


def test_missing_optional_mapped_header_is_loud_not_silently_empty():
    """(K30-a) seal_ids is mapped but NOT in REQUIRED_FIELDS. Before K30 a raw
    report missing its header degraded to an empty seal_ids column on every
    row and still reported success — the real-world failure mode this item
    closes (an export with a differently-spelled SEAL-id column silently
    writes zero application edges). After K30 this is a hard, loud refusal,
    same as a required field, unless the field is in ACKNOWLEDGED_ABSENT."""
    assert "seal_ids" not in ACKNOWLEDGED_ABSENT
    headers = [h for h in RAW_HEADERS if h != "Seal IDs"]
    with pytest.raises(ProjectionError, match="seal_ids .*'Seal IDs'"):
        project_rows([_row()], headers)


def test_jira_board_id_is_acknowledged_absent_not_loud():
    """(K30-c) jira_board_id maps to 'JIRA Board', a header TEAM_DETAILS_REPORT
    does not actually carry (it lives in a sibling PAT export). It is kept in
    DEFAULT_HEADER_MAP but listed in ACKNOWLEDGED_ABSENT, so a normal run
    without that header stays exit-0 (not (a)'s new loudness rule) and the
    report names it explicitly rather than staying silent."""
    assert "jira_board_id" in ACKNOWLEDGED_ABSENT
    assert "JIRA Board" not in RAW_HEADERS  # the recorded list does not carry it
    teams, _, report = project_rows([_row()], RAW_HEADERS)
    assert teams[0]["jira_board_id"] == ""
    assert report.acknowledged_absent == ("jira_board_id",)
    assert "acknowledged-absent" in "\n".join(report.lines())
    # ...and when a sibling export's column IS joined in, the mapped field flows.
    joined = [*RAW_HEADERS, "JIRA Board"]
    teams, _, report = project_rows([_row(**{"JIRA Board": "JIRA-AUTO"})], joined)
    assert teams[0]["jira_board_id"] == "JIRA-AUTO"
    assert report.acknowledged_absent == ()


def test_header_map_override_rejects_unknown_logical_fields(tmp_path: Path):
    bad = tmp_path / "h.yaml"
    bad.write_text("nonsense_field: X\n", encoding="utf-8")
    with pytest.raises(ProjectionError, match="nonsense_field"):
        load_header_map(bad)
    good = tmp_path / "g.yaml"
    good.write_text("team_id: 'TeamId'\n", encoding="utf-8")
    assert load_header_map(good)["team_id"] == "TeamId"
    assert load_header_map(good)["product_id"] == DEFAULT_HEADER_MAP["product_id"]


def test_rows_without_a_key_are_skipped_and_counted_and_repeated_teams_collapse():
    raw = [_row(), _row(**{"Team ID": ""}), _row(**{"Product ID": ""}), _row()]
    teams, mappings, report = project_rows(raw, RAW_HEADERS)
    assert report.skipped_no_key == 2
    assert len(teams) == 1  # one DevTeam row per team id
    assert len(mappings) == 2  # the alignment rows are kept as emitted


def test_unknown_headers_are_reported_not_silently_ignored():
    _, _, report = project_rows(
        [{**_row(), "Brand New Column": "x"}], [*RAW_HEADERS, "Brand New Column"]
    )
    assert report.unknown_headers == ("Brand New Column",)
    assert "UNKNOWN headers" in "\n".join(report.lines())


def test_file_round_trip_writes_the_two_names_the_refresh_chain_reads(tmp_path: Path):
    """LOAD7: the committed fixture is read UNCONDITIONALLY, and a missing one fails.

    This used to skip when the fixture was absent, "because drydocs/data/ is
    gitignored" — a skip that can never fire, because the file is TRACKED and
    git's ignore rules do not apply to tracked files (there is no `!` carve-out
    for drydocs/data/samples/; the pattern still matches, the fourteen files are
    simply already in the index). So the assertion below was protected by
    nothing, the same fake-skip class CORE4 removed from the demo interlock.
    Absence has to be a FAILURE here in particular: the fixture path is
    NAME-terminated on PAT_PRODUCT_MAPPING_FILE so the constant cannot drift
    from the fixture, which only holds if a rename BREAKS this test rather than
    skipping it.
    """
    raw = tmp_path / "TEAM_DETAILS_REPORT.csv"
    with raw.open("w", encoding="utf-8", newline="") as fh:
        import csv

        w = csv.DictWriter(fh, fieldnames=RAW_HEADERS)
        w.writeheader()
        w.writerow(_row())
    out = tmp_path / "projected"
    report = project_team_report(raw, out)
    assert sorted(p.name for p in out.iterdir()) == sorted(
        [DEV_TEAMS_FILE, PAT_PRODUCT_MAPPING_FILE]
    )
    assert (out / DEV_TEAMS_FILE).read_text(encoding="utf-8").splitlines()[0] == ",".join(
        DEV_TEAMS_COLUMNS
    )
    assert (out / PAT_PRODUCT_MAPPING_FILE).read_text(encoding="utf-8").splitlines()[0] == ",".join(
        PAT_PRODUCT_MAPPING_COLUMNS
    )
    assert report.mapping_rows == 1
    # the committed fixtures and the projection share one header, so the
    # loaders cannot tell a projected file from a fixture — that is the point
    fixture = REPO / "drydocs" / "data" / "samples" / PAT_PRODUCT_MAPPING_FILE
    assert fixture.exists(), (
        f"{fixture} is missing. It is a TRACKED file, so this is a renamed or deleted "
        "fixture, not an absent local one — see this test's docstring."
    )
    assert fixture.read_text(encoding="utf-8").splitlines()[0] == ",".join(
        PAT_PRODUCT_MAPPING_COLUMNS
    )


def test_the_fixture_header_row_is_the_recorded_list_not_the_module_constant():
    """K30 (d). The fixture used to write its header row in the SAME believed
    spellings DEFAULT_HEADER_MAP looked for (it wrote "SEAL IDs"), so code and
    test could be wrong together and the suite could not tell — which is exactly
    what happened until the 2026-08-29 census. The structural fix: the fixture's
    header row is drawn from the ledger's recorded 43-column list and is checked
    here against three things the module constant cannot supply — the full
    column count, the export order, and the 35 columns the map never names."""
    doc = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    (obj,) = doc["objects"]
    assert obj["profile"]["census"] == "closed"
    recorded = [c["name"] for c in obj["columns"]]
    assert RAW_HEADERS == recorded
    assert len(RAW_HEADERS) == obj["profile"]["column_count"] == 43
    assert len(set(RAW_HEADERS)) == 43
    # Not derived from the module's own belief: the fixture carries columns the
    # header map never mentions (the dropped ones), and every header the map DOES
    # name for this report is a recorded column — the map is checked against the
    # fixture, never the other way round.
    believed = set(DEFAULT_HEADER_MAP.values())
    assert len(set(RAW_HEADERS) - believed) == 35
    assert believed - set(RAW_HEADERS) == {DEFAULT_HEADER_MAP["jira_board_id"]}
    # And the fixture row helper fills every recorded column, so a run over it
    # reports zero unknown headers — the shape a clean real run has.
    _, _, report = project_rows([_row()], RAW_HEADERS)
    assert report.unknown_headers == ()
    assert set(report.dropped_by_design) == set(KNOWN_DROPPED)


def test_the_ledger_is_authored_from_what_the_projection_reads():
    """Deliverable (4): locator.mapping stops being null, and the ledger's
    projected rows ARE the header map — drift either way fails here."""
    doc = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    assert doc["source"] == "pat:people-report"
    (obj,) = doc["objects"]
    projected = {c["name"] for c in obj["columns"] if c["disposition"] == "projected"}
    excluded = {c["name"] for c in obj["columns"] if c["disposition"] == "excluded"}
    # The ledger lists COLUMNS OF THE REPORT. `jira_board_id` is mapped but its
    # header is not one of them (K30; confirmed by the 2026-08-29 census), so it
    # is named in ACKNOWLEDGED_ABSENT and deliberately absent below — a mapping
    # belief is not a column, and only columns are counted in the census.
    mapped_to_real_columns = {
        header for field, header in DEFAULT_HEADER_MAP.items() if field not in ACKNOWLEDGED_ABSENT
    }
    assert projected == mapped_to_real_columns
    assert excluded == set(KNOWN_DROPPED)
    # The census closes only when every column of the export has a disposition.
    assert len(projected) + len(excluded) == obj["profile"]["column_count"] == 43
    assert not projected & excluded
    registry = yaml.safe_load(
        (REPO / "config" / "source-registry.yaml").read_text(encoding="utf-8")
    )
    row = next(d for d in registry["datasets"] if d["id"] == "pat:people-report")
    assert row["locator"]["mapping"] == "config/source-mappings/pat-team-report.yaml"
