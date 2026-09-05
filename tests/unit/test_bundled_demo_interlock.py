"""Z7 — the bundled samples must reference EACH OTHER, not merely be valid.

Every sample file in this repo was built correctly and, for a long time, built
alone. Run together they produced a flawless coverage report over an empty
world: the Control-M hosts matched no inventory server, no folder reached any
application's batch port, and the teams the PAT sample named owned applications
no folder had ever heard of. Nothing was broken — every loader reported its own
gap honestly — and the bundled demo, which is the only end-to-end thing anyone
gets without company data, exercised the reporting path and never the success
path.

Each test below pins ONE join the demo needs, at the file level, before any
graph is involved. They are cheap, and they fail with the name of the file that
drifted, which is the part a live run cannot tell you. The join from Control-M
host to inventory server is the fourth, and it lives with the export fixture it
constrains (tests/unit/test_server_inventory_fixture.py).

WHAT THESE DO NOT ASSERT is that every gap is closed. Coverage gaps are the
point of the coverage counters, and a demo with nothing unmatched would prove
less, not more: 7 of the 8 folders are deliberately unattributed and 2 of the 4
hosts deliberately unresolved. These tests assert that AT LEAST ONE path through
each join is whole.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SAMPLES = REPO / "drydocs" / "data" / "samples"
FOLDERS = SAMPLES / "controlm_folders__sample.csv"
JOBS = SAMPLES / "controlm_jobs__sample.csv"
PAT = SAMPLES / "pat_product_mapping__sample.csv"
FACTS = REPO / "tests" / "fixtures" / "attribution" / "stg_app_fact__bundled-samples.csv"
APPLICATIONS = REPO / "config" / "taxonomy" / "business-application.yaml"

#: Position 3 of a Control-M folder name is the application id it belongs to
#: (knowledge/standards/technology/folder-naming-convention.md). The K2 policy
#: reads the id from a normalized variable, not from this name — but the sample
#: folder names are where a reader sees which application a folder is for, and
#: they are what these tests read to say the two sides agree.
_FOLDER_APP_ID = re.compile(r"^[A-Z]+-[A-Z]+-(\d{5})-")


def _rows(path: Path) -> list[dict[str, str]]:
    """Read one sample, or skip if it is not in this clone.

    A real skip, not a formality for the J8 policy test: drydocs/data/ is
    gitignored wholesale and its tracked CSVs are grandfathered inside it, so
    today every path here is present and the skip never fires. Written per
    reader so a missing sample can only quiet the tests that actually need it.
    """
    if not path.exists():
        pytest.skip(f"{path.relative_to(REPO)} absent — this interlock has no other half")
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _folder_app_ids() -> dict[str, str]:
    """folder_id -> the application id its name carries."""
    out = {}
    for row in _rows(FOLDERS):
        match = _FOLDER_APP_ID.match(row["sched_table"].strip())
        if match:
            out[row["folder_id"].strip()] = match.group(1)
    return out


def _captured_app_ids() -> set[str]:
    """The synthetic applications, from the capture the SEAL samples derive FROM.

    Read here rather than from seal_application_data__sample.csv because that CSV
    is generated per machine and never committed (drydocs/seal_samples.py); the
    capture is the tracked source both it and this test can agree on. `sealid` is
    the capture's own field name for what the graph keys as app_id.
    """
    doc = yaml.safe_load(APPLICATIONS.read_text(encoding="utf-8"))
    return {str(a["sealid"]).strip() for a in doc["nodes"]["business_applications"]}


def test_the_fact_feed_names_jobs_the_controlm_sample_actually_has() -> None:
    """The fallback attributes a FOLDER by aggregating its JOBS' decisions.

    A fact row for a job the sample does not contain resolves to nothing and
    the folder stays unmatched — silently, because an absent job is exactly
    what an unmatched folder looks like from the coverage report.
    """
    jobs = {(r["folder_id"].strip(), r["job_id"].strip()) for r in _rows(JOBS)}
    orphans = [
        (r["folder_id"], r["job_id"])
        for r in _rows(FACTS)
        if (r["folder_id"].strip(), r["job_id"].strip()) not in jobs
    ]
    assert not orphans, (
        f"stg_app_fact rows naming (folder, job) pairs the Control-M sample does "
        f"not carry: {orphans}"
    )


def test_every_fact_folder_is_unanimous_because_the_fallback_requires_it() -> None:
    """K2 §B3: a folder attributes by fallback only if its jobs AGREE.

    A second, disagreeing SEAL added to a folder here would not fail any loader
    — it would land on the coverage report as a conflict and the folder would
    go quiet, which is correct behaviour and a broken demo.
    """
    by_folder: dict[str, set[str]] = {}
    for row in _rows(FACTS):
        if row["fact_type"].strip().upper() == "SEAL":
            by_folder.setdefault(row["folder_id"].strip(), set()).add(row["fact_value"].strip())
    split = {f: sorted(v) for f, v in by_folder.items() if len(v) > 1}
    assert not split, (
        f"folders whose sample SEAL facts disagree: {split} — the fallback needs "
        "unanimity, so these would surface as conflicts and attribute nothing"
    )


def test_the_fact_feed_points_at_an_application_the_capture_carries() -> None:
    """The attribution edge is MATCH-only onto the app's port: no node is made.

    So a fact naming an application the SEAL capture never declares resolves to
    a decision that writes nothing at all.
    """
    captured = _captured_app_ids()
    unknown = sorted(
        {
            r["fact_value"].strip()
            for r in _rows(FACTS)
            if r["fact_type"].strip().upper() == "SEAL" and r["fact_value"].strip() not in captured
        }
    )
    assert not unknown, (
        f"sample SEAL facts naming applications config/taxonomy/"
        f"business-application.yaml does not declare: {unknown} — the folder would "
        f"resolve and then write no edge. Declared: {sorted(captured)}"
    )


def test_at_least_one_team_owns_an_application_a_folder_runs_for() -> None:
    """The team dimension's whole chain hangs on this one overlap.

    map.team-locations.v1 walks team <- application -> port <- folder -> job ->
    host -> server -> data center, and the SAME application has to appear on
    both sides. Until Z7 the PAT sample's teams owned 70051-70053 and every
    folder name carried 70002 and its neighbours, so the query was correct and
    empty — the hardest kind of empty to notice.
    """
    team_apps: set[str] = set()
    for row in _rows(PAT):
        team_apps |= {v.strip() for v in row.get("seal_ids", "").split(";") if v.strip()}
    folder_apps = set(_folder_app_ids().values())
    overlap = team_apps & folder_apps
    assert overlap, (
        f"no application is both owned by a team and named by a folder — teams "
        f"{sorted(team_apps)} vs folders {sorted(folder_apps)}"
    )
