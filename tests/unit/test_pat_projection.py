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

# A synthetic report in the DEFAULT spellings, with the decoy column present and
# every known-dropped column beside the ones we read. Ids are synthetic; SEAL ids
# sit in the reserved 70001-70099 block the fixtures use.
RAW_HEADERS = [
    "Team ID",
    "Legacy Team ID",
    "Team Name",
    "LOB",
    "Product Line",
    "Product ID",
    "Product Name",
    "Supporting Area Product ID",
    "Supporting Area Product Name",
    "Sponsoring Product ID",
    "Sponsoring Product Name",
    "Sponsoring Area Product ID",
    "Sponsoring Area Product Name",
    "Sponsoring Product Line",
    "SEAL IDs",
    "Relationship Type",
    "Team Type Name",
    "JIRA Instance",
    "JIRA Board",
    "Status",
    "Agile Framework",
]


def _row(**over: str) -> dict[str, str]:
    base = {h: "" for h in RAW_HEADERS}
    base.update(
        {
            "Team ID": "T0042",
            "Legacy Team ID": "0f0f0f0f-0000-0000-0000-000000000000",
            "Team Name": "CCB Auto Risk Pod",
            "LOB": "CCB",
            "Product Line": "Auto",
            "Product ID": "PROD_AUTO_05",
            "Product Name": "Auto Pricing",
            "Supporting Area Product ID": "AP_AUTO_PUB",
            "SEAL IDs": "70051; 70052",
            "Relationship Type": "Dedicated",
            "Team Type Name": "Technology",
            "JIRA Board": "JIRA-AUTO",
            "Status": "Active",
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
                "SEAL IDs": "70053",
                "Relationship Type": "Aligned",
                "JIRA Board": "JIRA-ONBOARD",
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
    assert dev[0].parent_product_id == "PROD_AUTO_05" and dev[0].jira_board_id == "JIRA-AUTO"
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
    if not fixture.exists():
        pytest.skip("sample fixture absent on this machine (drydocs/data/ is gitignored)")
    assert fixture.read_text(encoding="utf-8").splitlines()[0] == ",".join(
        PAT_PRODUCT_MAPPING_COLUMNS
    )


def test_the_ledger_is_authored_from_what_the_projection_reads():
    """Deliverable (4): locator.mapping stops being null, and the ledger's
    projected rows ARE the header map — drift either way fails here."""
    doc = yaml.safe_load(LEDGER.read_text(encoding="utf-8"))
    assert doc["source"] == "pat:people-report"
    (obj,) = doc["objects"]
    projected = {c["name"] for c in obj["columns"] if c["disposition"] == "projected"}
    excluded = {c["name"] for c in obj["columns"] if c["disposition"] == "excluded"}
    assert projected == set(DEFAULT_HEADER_MAP.values())
    assert excluded == set(KNOWN_DROPPED)
    assert not projected & excluded
    registry = yaml.safe_load(
        (REPO / "config" / "source-registry.yaml").read_text(encoding="utf-8")
    )
    row = next(d for d in registry["datasets"] if d["id"] == "pat:people-report")
    assert row["locator"]["mapping"] == "config/source-mappings/pat-team-report.yaml"
