"""Guards for DOC12 — the 2-tab Excel run book filled from the graph.

The generator lives at `.claude/skills/controlm-runbook-automation-excel/`,
where no package guard reaches it, which is why this file exists and why it is
broad. It is the sibling of `test_sdlc_runbook_generator.py` and shares its
reasoning; what it adds is the clause the two skills exist to protect.

FOUR THINGS ARE GUARDED HERE.

1.  **THE SHARED-QUERY CLAUSE, which is the acceptance's own failure mode.**
    "Two skills disagreeing about the same runbook fact" is what the L23 clause
    names, so this generator must READ the -SDLC generator's facts rather than
    ask the graph itself. The guard reads CODE, not the prose around it (J66):
    the module docstring says the word "Cypher" while explaining why there is
    none, and a substring test over raw source would fail on the explanation.

2.  **THE THIRD OUTCOME.** A field the template declares `source: graph` that
    the generator cannot fill must not come out blank — blank is
    indistinguishable from "this folder genuinely has no value here". It gets a
    marker and a count, and that count is the honest measure of how much of the
    template the graph actually reaches today.

3.  **RECONCILIATION.** Every field lands in exactly one of four outcomes, and
    the per-source totals match what the spec declares. A generator that
    silently dropped a field would still produce a plausible workbook.

4.  **PUBLISH BOUNDARY.** Committed files stay mechanism-only; a FILLED workbook
    is Internal. The sweep is over the VALUE, not the field name, for the reason
    the -SDLC sibling records: real ids once survived a cleanup by hiding inside
    folder-name strings.
"""

from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

import pytest
import yaml

from tests.source_scan import called_names, imported_modules, source_text

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "controlm-runbook-automation-excel"
GENERATOR = SKILL_DIR / "generate_runbook.py"
SPEC_PATH = SKILL_DIR / "template-spec.yaml"

#: The reserved synthetic block, as the -SDLC sibling defines it.
SYNTHETIC_BLOCK = range(70001, 70100)

#: A folder every bundled sample set carries, and the retired zero-job one.
SAMPLE_FOLDER = "PRARAG-HLDM-70002-PEX-RFND-DLY"
EMPTY_FOLDER = "PRRPDG-RPD-70041-RISK-RETIRED"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load("_doc12_generator", GENERATOR)


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def run(generator):
    return generator.generate(SAMPLE_FOLDER)


# --- 1. the shared-query clause ------------------------------------------------


def test_this_generator_issues_no_cypher_of_its_own(generator) -> None:
    """The clause the two skills exist to protect, asserted against CODE.

    The module docstring uses the word "Cypher" to explain why none is here, so
    a raw-source substring test would fail on its own explanation — the J66
    disease exactly. `code_only` strips comments and string literals, which is
    what makes this guard read the program rather than its commentary.
    """
    source = source_text(GENERATOR)
    # CASE-SENSITIVE, and shaped: `MATCH (` is Cypher and nothing else, whereas an
    # upper-cased search for RETURN matches every Python `return` in the file —
    # measured, on the first version of this guard. The subject here is the
    # literal query text a second implementation would embed, so this reads the
    # whole source rather than `code_only`, which strips exactly the string
    # literals a query would hide in.
    for shape in (r"MATCH\s*\(", r"MERGE\s*\(", r"OPTIONAL\s+MATCH"):
        assert not re.search(shape, source), (
            f"{GENERATOR.name} embeds Cypher matching {shape!r}. The runbook queries "
            "are SHARED with the -SDLC generator; a second copy is the "
            "two-skills-disagree failure the L23 acceptance names."
        )
    # And the execution seam: a module that never runs a query cannot issue one.
    # Through `called_names`, NOT a substring test over `code_only` — that helper
    # normalises `client.run(` to `CLIENT . RUN (`, so a search for ".run(" can
    # never match and the guard would have been inert. Measured against the
    # -SDLC generator, which does call it: `called_names` reports {'run'} there
    # and nothing here, so this half of the guard is known to discriminate.
    assert "run" not in called_names(source), (
        f"{GENERATOR.name} calls a client's run() — it must read the -SDLC "
        "generator's facts, never execute a query itself"
    )


def test_the_facts_come_from_the_sdlc_sibling(generator) -> None:
    """Shared, and shared FROM the one place that owns the folder query."""
    source = source_text(GENERATOR)
    assert (
        "controlm-runbook-automation-SDLC" in source
    ), "the generator must load the -SDLC sibling's facts rather than its own"
    assert "neo4j" not in {
        m.split(".")[0] for m in imported_modules(source)
    }, "this module must not construct a graph client; the caller injects facts"


# --- 2. the third outcome ------------------------------------------------------


def test_a_graph_field_the_generator_cannot_fill_is_never_blank(generator, run) -> None:
    """Blank would read as 'this folder has no value here'. It does not mean that.

    It means the template claims the graph holds the field and no feed reaches
    it, which is a statement about the PROJECT, not about the folder — and the
    two must not look identical on a support engineer's screen.
    """
    assert run.tallies, "the run reported no tabs at all"
    unreached = sum(t.unreached for t in run.tallies.values())
    assert unreached > 0, (
        "no field landed in the third state; if the graph now reaches every "
        "declared field this guard should assert that instead"
    )
    resolved = generator._resolve("a field nothing supplies", "graph", {})
    assert resolved.outcome == generator.UNREACHED
    assert resolved.value.strip(), "the third state must carry a marker, not an empty string"
    assert resolved.fill is not None, "it must be tinted so a reader sees it"


def test_a_known_hold_names_its_reason_from_config(generator) -> None:
    """Where the cause is declared, the cell cites it instead of shrugging.

    Read from config/source-descriptors.yaml rather than restated, so the day the
    dataset is wired the note stops being produced rather than going stale.
    """
    assert generator.KNOWN_HOLDS, "no known holds declared"
    for field_name, dataset_id in generator.KNOWN_HOLDS.items():
        reason = generator._wired_reason(dataset_id)
        assert reason, (
            f"{field_name} claims {dataset_id} holds it, but that dataset is not "
            "declared unwired in config/source-descriptors.yaml"
        )
        cell = generator._resolve(field_name, "graph", {})
        assert dataset_id in cell.value and reason in cell.value


# --- 3. reconciliation ---------------------------------------------------------


def test_every_field_lands_in_exactly_one_outcome(run, spec) -> None:
    """A dropped field would still produce a plausible workbook. This catches it."""
    declared = {}
    for tab in spec["tabs"]:
        items = tab["rows"] if tab["layout"] == "rows" else tab["columns"]
        declared[tab["name"]] = len(items)
    assert set(run.tallies) == set(declared), "the run covered a different tab set"
    for name, tally in run.tallies.items():
        assert tally.total == declared[name], (
            f"{name}: the run accounted for {tally.total} fields, the spec declares "
            f"{declared[name]}"
        )


def test_the_capture_counts_match_what_the_spec_declares(run, spec) -> None:
    """partial and manual are the template's own numbers, not the generator's."""
    for tab in spec["tabs"]:
        items = tab["rows"] if tab["layout"] == "rows" else tab["columns"]
        tally = run.tallies[tab["name"]]
        assert tally.manual == sum(1 for i in items if i["source"] == "manual")
        assert tally.partial == sum(1 for i in items if i["source"] == "graph-partial")
        assert tally.declared_graph == sum(1 for i in items if i["source"] == "graph")


def test_a_folder_with_no_jobs_still_reports_its_shape(generator, spec) -> None:
    """The retired folder: zero jobs is not zero fields.

    A generator that only works on the folder its author picked is a demo, and
    the job tab is where that shows: with no rows to write, the columns still
    have to be counted or the tab silently reports nothing.
    """
    empty = generator.generate(EMPTY_FOLDER)
    jobs_tab = next(t for t in spec["tabs"] if t["layout"] != "rows")
    tally = empty.tallies[jobs_tab["name"]]
    assert tally.total == len(jobs_tab["columns"])
    assert tally.filled == 0, "a folder with no jobs can fill no per-job column"


def test_the_workbook_writes_and_reads_back(generator, tmp_path, spec) -> None:
    """It has to be a real workbook, not a report about one."""
    out = tmp_path / "runbook.xlsx"
    generator.generate(SAMPLE_FOLDER, out=out)
    openpyxl = pytest.importorskip("openpyxl")
    wb = openpyxl.load_workbook(out)
    assert wb.sheetnames == [t["name"] for t in spec["tabs"]]
    technical = wb[spec["tabs"][0]["name"]]
    values = {row[0]: row[1] for row in technical.iter_rows(min_row=3, max_col=2, values_only=True)}
    assert values.get("Control-M Folder name") == SAMPLE_FOLDER
    assert all(v is not None and str(v).strip() for v in values.values()), (
        "every Technical_Details cell carries something — blank is the state this "
        "generator exists to remove"
    )


# --- 4. publish boundary -------------------------------------------------------


def test_the_committed_generator_carries_no_real_looking_ids() -> None:
    """Mechanism only. A FILLED workbook is Internal and lives elsewhere."""
    text = GENERATOR.read_text(encoding="utf-8")
    for match in re.findall(r"\b(\d{5})\b", text):
        assert int(match) in SYNTHETIC_BLOCK, (
            f"{GENERATOR.name} carries the five-digit id {match}, which is outside the "
            "reserved synthetic block 70001-70099"
        )
    assert "K9" not in text.replace("K9 recovery", ""), "no employee SID shapes in committed files"


def test_no_generated_value_carries_an_id_outside_the_reserved_block(run, generator) -> None:
    """The sweep is over the VALUE, not the field: ids have hidden in names before."""
    rendered = run.render()
    for match in re.findall(r"\b(\d{5})\b", rendered):
        assert (
            int(match) in SYNTHETIC_BLOCK
        ), f"the run report carries {match}, outside the reserved synthetic block"
