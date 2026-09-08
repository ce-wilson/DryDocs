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
less, not more. These tests assert that AT LEAST ONE path through each join is
whole.

WHICH GAPS ARE DELIBERATE, corrected 2026-09-07 (LOAD4). This paragraph used to
say "7 of the 8 folders are deliberately unattributed and 2 of the 4 hosts
deliberately unresolved", and only the second half was ever true. The folder
number was a rationalization of a defect: the SEAL capture declared 70001-70003
while the folder names carried 70002, 70011, 70012, 70021, 70022, 70031 and
70041, so six folders could not have attributed whatever the evidence said. The
ids were authored apart, nobody chose that, and calling it deliberate is how it
survived. Corrected by growing the capture (see its own header for why that
direction) and extending the fact feed. What is deliberate now, each named where
a guard can see it:

* folder 161020 has an application the capture DOES carry (70012) and no fact
  rows at all — the "no evidence" unmatched case;
* folder 161999 is retired and names 70041, which the capture deliberately does
  not carry — the "application no longer in the registry" unmatched case, pinned
  by ``DELIBERATE_GAPS`` below;
* 2 of the 4 hosts stay unresolved (tests/unit/test_server_inventory_fixture.py),
  untouched by LOAD4.
"""

from __future__ import annotations

import csv
import re
from pathlib import Path

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
#:
#: THE `\d{5}` HERE IS THE SYNTHETIC WIDTH, NOT A CLAIM ABOUT THE REAL ONE, and
#: it is deliberately left at five (CORE5, 2026-09-07). The demo folder names are
#: built from the reserved block 70001-70099, which is five digits by
#: construction, so this pattern is exact for its subject and widening it would
#: only let a non-block value through unnoticed. The LIVE population is 4 to 7
#: digits (config/source-mappings/pat-team-report.yaml, the `Seal IDs` row) —
#: which is why the prose extractor and the publish-boundary scans DID widen, and
#: why this comment exists: the same five-digit belief was written in four places
#: and only one of them was ever right. If the demo ever mints an id outside the
#: block, this is the line that has to move with it.
_FOLDER_APP_ID = re.compile(r"^[A-Z]+-[A-Z]+-(\d{5})-")


def _rows(path: Path) -> list[dict[str, str]]:
    """Read one sample. Absence is a FAILURE here, not a skip (CORE4, 2026-09-07).

    This used to be a ``pytest.skip``, and its own docstring said why that was
    wrong while defending it: "drydocs/data/ is gitignored wholesale and its
    tracked CSVs are grandfathered inside it, so today every path here is present
    and the skip never fires". A guard that never fires is not protecting the
    suite from anything — it was written to satisfy the J8 skip-guard policy,
    which at the time called any drydocs/data/ path a gitignored asset and could
    not see that these four are force-tracked.

    Every path this reads is in git, so a fresh clone HAS it. If one is missing
    the clone is broken, not incomplete, and the right behaviour is to say so
    loudly — the cost of the old skip was that a genuinely missing sample would
    have quietly disabled this interlock's real assertions instead.

    The policy now asks git rather than the path prefix, so this file needs no
    guard at all and carries none.
    """
    assert path.exists(), (
        f"{path.relative_to(REPO)} is TRACKED and absent — this clone is broken, "
        "not incomplete. The bundled samples ship with the repo; restore them "
        "rather than skipping the interlock that reads them."
    )
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


# ---- LOAD4: the join the other four assumed and nobody checked -----------------

#: folder_id -> the application id its name carries, for folders the capture
#: deliberately does NOT declare. ONE entry, and it has to stay that way for the
#: guard to mean anything: 161999 is status=R with an empty user_daily, and a
#: retired folder naming an application the registry no longer carries is the
#: unattributed case the demo should show. Every OTHER folder must resolve — that
#: is the whole point, because before LOAD4 six of them silently could not, and
#: the coverage report read that as a finding rather than as a fixture defect.
DELIBERATE_GAPS = {"161999": "70041"}


def test_every_folder_names_an_application_the_capture_carries() -> None:
    """LOAD4 (d). The fixture's two halves were authored apart: folder names on
    one side, the SEAL capture on the other, and nothing compared them. Six
    folders named applications that did not exist, so no evidence could ever have
    attributed them."""
    captured = _captured_app_ids()
    missing = {
        folder_id: app_id
        for folder_id, app_id in _folder_app_ids().items()
        if app_id not in captured
    }
    assert missing == DELIBERATE_GAPS, (
        f"folder-name application ids that config/taxonomy/business-application.yaml "
        f"does not declare: {missing}. Expected exactly the deliberate gap "
        f"{DELIBERATE_GAPS}. Declare the id in the capture, or add it here WITH ITS "
        f"REASON — a gap that is merely tolerated is how the last one lasted."
    )


def test_the_bundled_demo_attributes_most_of_its_folders_and_says_why_the_rest_do_not() -> None:
    """LOAD4 (c) — the coverage claim, made sample-reproducible (J18).

    "Attribution works on the samples" was a thing said about a machine. This
    runs the real resolver over the committed fixtures, in-process and with no
    Neo4j, so the numbers below are reproducible in any clone. Before LOAD4 they
    were 1 attributed and 7 unmatched, and six of those seven could not have been
    fixed by any amount of evidence.
    """
    from drydocs.loaders.folder_attribution import FolderAttributionAdapter
    from drydocs_core.adapters import CsvAdapter
    from drydocs_core.models import FolderAttributionRow

    # folder -> app_code, the fan-out index: the demo has no authored app-code
    # store (config/overrides/app-code-mappings.csv is header-only), so every
    # attribution below comes from the K2 job-grain fallback.
    folder_codes: dict[str, str | None] = {row["folder_id"].strip(): None for row in _rows(FOLDERS)}
    for row in _rows(JOBS):
        folder_codes[row["folder_id"].strip()] = (row.get("application") or "").strip() or None

    adapter = FolderAttributionAdapter([], folder_codes, fact_source=CsvAdapter(FACTS))
    with adapter:
        rows = [FolderAttributionRow.model_validate(r) for r in adapter.rows()]
    coverage = adapter.coverage
    assert coverage is not None and coverage.reconciles()

    attributed = {r.folder_id: r.app_id for r in rows}
    assert attributed == {
        "161014": "70002",
        "161015": "70011",
        "161016": "70011",
        "160500": "70021",
        "160501": "70022",
        "162001": "70031",
    }
    assert (coverage.eligible_folders, coverage.attributed, coverage.unmatched) == (8, 6, 2)
    assert not coverage.conflicts

    # the two unmatched are the two named in the module docstring, for two
    # different reasons — a demo that shows only one kind of gap shows less
    unmatched = set(folder_codes) - set(attributed)
    assert unmatched == {"161020", "161999"}
