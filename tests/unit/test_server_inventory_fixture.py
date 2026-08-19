"""The Z1 server-export fixture stays synthetic and stays on-contract.

Two jobs, both born from documented misses:

1. VALUE SWEEP. The publish-boundary guard's scan A covers config/taxonomy/,
   drydocs/data/samples/ and knowledge/ — tests/fixtures/ is OUTSIDE its sweep,
   so a real application id pasted into this CSV would ride a green suite
   straight to a public push. The lesson is J15's, twice-learned: sweep for the
   VALUE, not the field. Every business_application value here must fall in the
   reserved synthetic block 70001-70099.

2. CONTRACT PIN. The fixture's header is the executable form of the field
   contract in config/taxonomy/server-location.yaml (`fields:`). If either side
   drifts, this fails before the Z3 loader can be built against the wrong shape.

Plus the standing caution in test form: the export's data_center column is
PHYSICAL geography, so no value in it may parse as a Control-M scheduling DC
name (the T032-E0700-DMA grammar) — the two concepts never join by field name,
and a fixture value that matches the other grammar is how that join would start
looking plausible.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
FIXTURE = REPO / "tests" / "fixtures" / "server_inventory" / "synthetic-server-export.csv"
CAPTURE = REPO / "config" / "taxonomy" / "server-location.yaml"

SYNTHETIC_BLOCK = range(70001, 70100)

#: The Control-M scheduling-DC grammar (knowledge/standards/technology/
#: data-center-naming-convention.md) — the SAME regex the publish-boundary
#: guard scans with. A physical data_center value must never match it.
_CONTROLM_DC_NAME = re.compile(r"^[A-Z]\d{3}-E\d{4}-[A-Z]{2,3}$")


def _rows() -> list[dict[str, str]]:
    with FIXTURE.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def test_fixture_header_matches_the_taxonomy_field_contract() -> None:
    capture = yaml.safe_load(CAPTURE.read_text(encoding="utf-8"))
    contract = [f["name"] for f in capture["fields"]]
    with FIXTURE.open(newline="", encoding="utf-8") as fh:
        header = next(csv.reader(fh))
    assert header == contract, (
        "the synthetic export's columns and the server-location field contract "
        f"disagree:\n  fixture:  {header}\n  contract: {contract}"
    )


def test_every_application_id_is_in_the_synthetic_block() -> None:
    bad = [
        r["business_application"]
        for r in _rows()
        if not (
            r["business_application"].isdigit()
            and int(r["business_application"]) in SYNTHETIC_BLOCK
        )
    ]
    assert not bad, (
        f"business_application values outside the reserved synthetic block "
        f"70001-70099: {bad} — tests/fixtures/ is outside the publish-boundary "
        "guard's scan A, so this test IS the sweep for this file."
    )


def test_both_designations_appear_because_one_download_carries_both() -> None:
    """The acquisition contract: the prod filter selects APPLICATIONS, and each
    application's download then carries BOTH its prod and DR servers."""
    designations = {r["designation"] for r in _rows()}
    assert {"PROD", "DR"} <= designations, (
        f"fixture designations {sorted(designations)} — a per-application download "
        "carries both PROD and DR rows, and the fixture must model that grain"
    )


def test_one_application_per_file_is_the_download_grain() -> None:
    apps = {r["business_application"] for r in _rows()}
    assert len(apps) == 1, (
        f"fixture spans applications {sorted(apps)} — the export is pulled PER "
        "BUSINESS APPLICATION, one file each; a multi-app file misrepresents the "
        "acquisition grain (add sibling fixture files instead)"
    )


def test_no_data_center_value_parses_as_a_controlm_scheduling_dc() -> None:
    bad = [r["data_center"] for r in _rows() if _CONTROLM_DC_NAME.match(r["data_center"])]
    assert not bad, (
        f"data_center values matching the Control-M scheduling-DC grammar: {bad} — "
        "the export's data-center field is PHYSICAL geography and never joins the "
        "Control-M field of the same name (the Epic Z standing caution)"
    )
