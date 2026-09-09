"""Guards for the `-SDLC` long-form run book generator (L23).

The generator lives at `.claude/skills/controlm-runbook-automation-SDLC/`, where no
package guard reaches it — `test_module_boundary.py` walks `PKG_ROOTS` only, and
`.claude` is not one. That is why this file exists and why it is broad: it is the
only thing standing between the skill and silent drift.

Four classes of guard here, in the order they matter:

1.  **CONFORMANCE, the acceptance itself** — a document generated for a bundled
    sample folder passes `sdlc-app-runbook.outline.yaml` validation with no hand
    editing. Run for EVERY sample folder, including the retired one with zero
    jobs, because a generator that only works on the folder its author picked is
    a demo, not a generator.

2.  **CLONE REPRODUCIBILITY.** The two `seal_*__sample.csv` files are UNTRACKED —
    `.gitignore` ignores `drydocs/data/` and the sample files that ship are
    force-added exceptions, which those two are not. So the conformance tests run
    against a directory holding only the TRACKED inputs. Without this the suite
    would pass on the machine that generated the SEAL samples and fail on a fresh
    clone and in CI, which is the worst available outcome: green where it is
    wrong, red where it is right.

3.  **SPEC-VS-OUTLINE DRIFT, both directions.** The outline owns the section set;
    the spec owns provenance per section. A section added to one and not the
    other is exactly the kind of quiet gap this repo keeps paying for, so the
    anchor sets must be equal, every `fill:` must resolve to a renderer, and
    every renderer must be reachable from the spec.

4.  **PUBLISH BOUNDARY**, two identifier classes and two rules. An APPLICATION id
    must sit inside the reserved synthetic block 70001-70099; the sweep is over
    the VALUE, not the field, because the ids that survived an earlier cleanup
    were embedded inside folder-name strings and a run book prints folder names
    everywhere. A PERSON identifier has no range to check, so its rule is
    provenance: every employee SID in the output must be one the fixture put in
    the input. Echoing an input is the job; emitting one from anywhere else is
    the thing worth catching.

    That second rule needed the fixture to grow. The SEAL sample pair is
    untracked, so a clone-faithful fixture has no contacts at all — and with no
    contacts the ownership and escalation renderers, the ONLY two that emit a
    person, are never reached. The sweep was passing without rendering a single
    one. The fixture now WRITES its own tiny synthetic SEAL bundle (still no
    machine dependency), and a control test asserts the sweep actually sees a
    person with it and none without it. A guard whose reach is not itself tested
    is a guard that reports on the code it happens to touch.
"""

from __future__ import annotations

import importlib.util
import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from drydocs.docgen.doc_outline import load_outline, validate_paths

REPO_ROOT = Path(__file__).resolve().parents[2]
SKILL_DIR = REPO_ROOT / ".claude" / "skills" / "controlm-runbook-automation-SDLC"
SPEC_PATH = SKILL_DIR / "section-spec.yaml"
SKILL_MD = SKILL_DIR / "SKILL.md"
OUTLINE_PATH = REPO_ROOT / "docs" / "design" / "templates" / "sdlc-app-runbook.outline.yaml"

#: The `-excel` sibling's vocabulary, which this skill shares by ruling rather
#: than inventing a second one. Adding a fourth value here is a decision about
#: BOTH skills and belongs in both specs.
SOURCE_VALUES = {"graph", "graph-partial", "manual"}

#: The reserved synthetic block. SEAL does not issue ids in this range, which is
#: why the sanitized samples use it.
SYNTHETIC_BLOCK = range(70001, 70100)


def _load_generator():
    """Import the skill's generator by path — it is not on any package path."""
    spec = importlib.util.spec_from_file_location(
        "_sdlc_runbook_generator", SKILL_DIR / "generate_runbook.py"
    )
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture(scope="module")
def generator():
    return _load_generator()


@pytest.fixture(scope="module")
def spec() -> dict:
    return yaml.safe_load(SPEC_PATH.read_text(encoding="utf-8"))


def _tracked_sample_csvs() -> list[Path]:
    out = subprocess.run(
        ["git", "ls-files", "drydocs/data/samples/*.csv"],
        cwd=REPO_ROOT,
        capture_output=True,
        encoding="utf-8",
        check=True,
    ).stdout
    return [REPO_ROOT / line for line in out.splitlines() if line.endswith(".csv")]


#: A tiny SEAL bundle written by the fixture, NOT copied from the machine.
#:
#: The real `seal_*__sample.csv` files are untracked and rebuilt per machine, so
#: a clone has neither. Copying them would make the suite machine-dependent — the
#: exact failure the clone fixture exists to prevent. But WITHOUT them,
#: `facts.contacts` is always empty, and the two renderers that emit a person
#: identifier (the ownership table and the escalation contact list) are never
#: reached. The publish-boundary sweep would then be green because it never
#: renders the values most worth sweeping, which is a guard lying to itself.
#:
#: So the fixture writes its own, inside the synthetic universe, and the sweep
#: reaches the escalation rows. Two apps: 70002 (which a bundled folder name
#: carries) and 70003 (which no folder does, so it never appears in output).
_SEAL_APPS = (
    "app_id,name,app_short_name,app_state,app_lob,info_classification,"
    "app_owner_sid,app_owner_name,chief_tech_officer_sid,chief_tech_officer_name,"
    "info_owner_sid,info_owner_name\n"
    "70002,Fixture Reporting App,FIX-RPT,Operate,CCB,Internal,"
    "K900001,Ada Fixture,K900002,Bo Fixture,K900003,Cy Fixture\n"
    "70003,Fixture Unused App,FIX-UNU,Operate,CCB,Internal,"
    "K900004,Di Fixture,K900004,Di Fixture,K900004,Di Fixture\n"
)
_SEAL_CONTACTS = (
    "app_id,role_name,employee_sid,employee_name,employee_email\n"
    "70002,L1 Operate Manager,K900001,Ada Fixture,ada.fixture@example.invalid\n"
    "70002,L2 Operate Manager,K900002,Bo Fixture,bo.fixture@example.invalid\n"
    "70002,Design Authority,K900003,Cy Fixture,cy.fixture@example.invalid\n"
    "70003,L1 Operate Manager,K900004,Di Fixture,di.fixture@example.invalid\n"
)

#: Every employee identifier the fixture puts in reach of the renderers. The
#: sweep asserts the generator emits NO person identifier that is not one of
#: these — it may echo its input, never invent.
_FIXTURE_SIDS = {"K900001", "K900002", "K900003", "K900004"}


@pytest.fixture(scope="module")
def clone_samples(tmp_path_factory) -> Path:
    """The tracked CSVs plus a synthetic SEAL bundle — a clone's view, plus reach.

    Tracked files are copied; the SEAL pair is WRITTEN here (see `_SEAL_APPS`)
    rather than copied from the machine, so the directory is identical on every
    checkout and the ownership and escalation renderers are actually exercised.
    """
    target = tmp_path_factory.mktemp("clone_samples")
    for path in _tracked_sample_csvs():
        shutil.copy(path, target / path.name)
    (target / "seal_application_data__sample.csv").write_text(
        _SEAL_APPS, encoding="utf-8", newline="\n"
    )
    (target / "seal_contact_data__sample.csv").write_text(
        _SEAL_CONTACTS, encoding="utf-8", newline="\n"
    )
    return target


@pytest.fixture(scope="module")
def tracked_only_samples(tmp_path_factory) -> Path:
    """The tracked CSVs and nothing else — a fresh clone exactly as it arrives."""
    target = tmp_path_factory.mktemp("tracked_only")
    for path in _tracked_sample_csvs():
        shutil.copy(path, target / path.name)
    return target


# --------------------------------------------------------------------------
# 1 + 2 — conformance, against a clone's view of the samples
# --------------------------------------------------------------------------


def _sample_folder_names(clone_samples: Path) -> list[str]:
    text = (clone_samples / "controlm_folders__sample.csv").read_text(encoding="utf-8")
    header, *rows = (line for line in text.splitlines() if line.strip())
    index = header.split(",").index("sched_table")
    return [row.split(",")[index] for row in rows]


def test_the_control_m_sample_inputs_the_generator_needs_are_all_tracked() -> None:
    """The conformance proof is only worth anything if its inputs ship.

    Stated as a guard rather than a comment because the failure it prevents is
    invisible locally: the two SEAL files exist on a machine that ran
    `scripts/build_seal_samples.py` and nowhere else.
    """
    tracked = {p.name for p in _tracked_sample_csvs()}
    required = {
        "controlm_folders__sample.csv",
        "controlm_jobs__sample.csv",
        "controlm_conditions_in__sample.csv",
        "controlm_conditions_out__sample.csv",
    }
    assert required <= tracked, f"the generator's required inputs are not all tracked: {tracked}"
    assert "seal_application_data__sample.csv" not in tracked, (
        "the SEAL sample became tracked — good news, but this test and the "
        "generator's OPTIONAL_SAMPLES note both describe it as absent from a "
        "clone, and both need updating"
    )


def test_every_sample_folder_generates_a_conformant_document(
    generator, clone_samples: Path, tmp_path: Path
) -> None:
    """The acceptance clause: generated, not hand-edited, and it validates.

    Every folder, not one: the sample set deliberately includes a retired folder
    with zero jobs and folders with no conditions at all, and a run book that
    renders only for the rich folder is not a generator.
    """
    names = _sample_folder_names(clone_samples)
    assert len(names) >= 8, f"expected the bundled folder set, saw {len(names)}"
    for name in names:
        facts = generator.load_from_samples(name, samples_dir=clone_samples)
        document = generator.render(facts, generator.load_spec(), _meta())
        out = tmp_path / f"{name}.md"
        out.write_text(document, encoding="utf-8", newline="\n")
        problems = validate_paths(OUTLINE_PATH, out)
        assert problems == [], f"{name} does not conform:\n  " + "\n  ".join(problems)


def test_generation_is_deterministic(generator, clone_samples: Path) -> None:
    """Two runs over one bundle are byte-identical.

    Nothing in the generator reads a clock: the cover's date is the newest
    capture date in the folder's own data. A generated artifact that changes
    because it was generated twice cannot be reviewed or diffed.
    """
    name = "PRARAG-HLDM-70011-PEX-TRUST-DLY"
    first = generator.render(
        generator.load_from_samples(name, samples_dir=clone_samples), generator.load_spec(), _meta()
    )
    second = generator.render(
        generator.load_from_samples(name, samples_dir=clone_samples), generator.load_spec(), _meta()
    )
    assert first == second
    assert "\r" not in first, "the rendered document carries CR — it must be LF-only"


def _meta() -> dict:
    return {
        "project": "",
        "version": "0.1-generated",
        "reflects": "",
        "classification": "Internal",
    }


# --------------------------------------------------------------------------
# 3 — spec/outline/renderer drift, all three directions
# --------------------------------------------------------------------------


def test_the_spec_covers_exactly_the_outline_sections(spec: dict) -> None:
    outline = load_outline(OUTLINE_PATH)
    spec_anchors = {section["anchor"] for section in spec["sections"]}
    assert spec_anchors == outline.all_anchors(), (
        "section-spec.yaml and the outline disagree.\n"
        f"  only in the outline: {sorted(outline.all_anchors() - spec_anchors)}\n"
        f"  only in the spec:    {sorted(spec_anchors - outline.all_anchors())}"
    )


def test_every_spec_section_has_a_renderer_and_every_renderer_is_reachable(
    generator, spec: dict
) -> None:
    used = {section["fill"] for section in spec["sections"]}
    defined = set(generator.RENDERERS)
    assert used <= defined, f"spec names renderers that do not exist: {sorted(used - defined)}"
    assert defined <= used, f"renderers nothing reaches: {sorted(defined - used)}"


def test_every_source_value_is_the_excel_siblings_vocabulary(spec: dict) -> None:
    """One concept, one vocabulary across the two runbook skills."""
    seen = {section["source"] for section in spec["sections"]}
    assert seen <= SOURCE_VALUES, f"unknown source values: {sorted(seen - SOURCE_VALUES)}"


def test_every_declared_column_still_appears_in_its_outline_guidance(spec: dict) -> None:
    """The outline's `Columns exactly: ...` prose is the authority; the spec copies it.

    Copying is right — parsing the guidance sentence would break the first time
    someone rewords it — but a copy needs a guard, or a reworded outline drifts
    silently away from the table the generator emits. This is that guard: it
    checks the copy still occurs in the source, without parsing the source.
    """
    raw = yaml.safe_load(OUTLINE_PATH.read_text(encoding="utf-8"))
    guidance: dict[str, str] = {}
    for section in raw["sections"]:
        guidance[section["anchor"]] = section.get("guidance", "") or ""
        for sub in section.get("subsections") or []:
            guidance[sub["anchor"]] = sub.get("guidance", "") or ""

    problems = []
    for section in spec["sections"]:
        text = guidance.get(section["anchor"], "")
        for key in ("columns", "header_rows", "task_columns", "inventory_columns"):
            for column in section.get(key) or []:
                if _squash(column) not in _squash(text):
                    problems.append(f"{section['anchor']}.{key}: {column!r} is not in the guidance")
    assert problems == [], "spec columns drifted from the outline guidance:\n  " + "\n  ".join(
        problems
    )


def _squash(text: str) -> str:
    """Whitespace removed entirely, case folded — the comparison the sources need.

    Two measured reasons, both from the real files rather than imagined:
    the outline's folded YAML scalars WRAP inside a column name (`Event Wait
    Trigger Files/` then `Dependencies` on the next line), so collapsing runs of
    whitespace to one space is not enough; and the guidance writes some column
    names in running prose (`Script Name | vault function call`) where the
    rendered header capitalizes (`Vault function call`). Neither is drift, and a
    guard that called them drift would be trained out of the tree within a week.
    """
    return re.sub(r"\s+", "", text).casefold()


def test_the_skill_md_coverage_sentence_matches_the_spec(spec: dict) -> None:
    """SKILL.md states 4 / 11 / 26 / 10. The spec is the authority; keep them equal.

    This guard READS PROSE on purpose, which is normally the wrong thing to do —
    the rule is to read the importable object, not the human-facing render. The
    exception is a guard whose SUBJECT is the prose, and this is one: the claim
    under test is the sentence itself. A number quoted in a document nothing
    checks is a number that rots, and this repo has paid for that more than once.
    Edit the spec and this test tells you which sentence to update.
    """
    counts = {value: 0 for value in SOURCE_VALUES}
    for section in spec["sections"]:
        counts[section["source"]] += 1
    na = sum(1 for section in spec["sections"] if section.get("na_for_batch"))
    na_in_manual = sum(
        1
        for section in spec["sections"]
        if section.get("na_for_batch") and section["source"] == "manual"
    )
    assert na == na_in_manual, (
        "an N/A section is labeled something other than `manual`, so the SKILL.md "
        "sentence '10 of the 26 are N/A' would be counting across two buckets"
    )

    text = SKILL_MD.read_text(encoding="utf-8")
    stated = re.search(
        r"(\d+) sections? `graph`, (\d+) `graph-partial`, (\d+)\s*\n?`manual`.*?"
        r"\((\d+) in all.*?(\d+) of the \d+ are N/A",
        text,
        re.S,
    )
    assert stated, "SKILL.md's coverage sentence changed shape — update this guard with it"
    graph, partial, manual, total, stated_na = (int(g) for g in stated.groups())
    assert (graph, partial, manual) == (
        counts["graph"],
        counts["graph-partial"],
        counts["manual"],
    ), (
        f"SKILL.md says {graph}/{partial}/{manual}; the spec has "
        f"{counts['graph']}/{counts['graph-partial']}/{counts['manual']}"
    )
    assert total == len(
        spec["sections"]
    ), f"SKILL.md says {total} sections, spec has {len(spec['sections'])}"
    assert stated_na == na, f"SKILL.md says {stated_na} N/A sections, the spec has {na}"


def test_command_facts_come_from_the_shared_parser_at_production_shapes(
    generator, clone_samples: Path
) -> None:
    """The anti-duplication clause, made testable at values the samples do not have.

    Every bundled `cmd_line` is a bare path with no arguments, so a string slice
    and the shared parser agree on all of them — which is exactly why a guard
    built only on the samples would never notice the difference. These two shapes
    are the ones production uses (a wrapper script with arguments, and the
    `dt-launcher` jar the sibling's own spec uses as its example), and on them a
    slice gets four things wrong at once.
    """
    facts = generator.load_from_samples("PRARAG-HLDM-70002-PEX-RFND-DLY", samples_dir=clone_samples)
    facts.jobs[0]["cmd_line"] = "sh /home/ops/scripts/run_wrapper.ksh job_a.pset {ODATE},1,Y,NO"
    facts.jobs[1]["cmd_line"] = (
        "java -jar /apps/etl/dt-accelerators/dt-launcher-current.jar "
        "-c /apps/etl/tenants/cfg/70004-epv-conf.json"
    )

    by_target = {fact.target: fact for fact in facts.commands()}
    # 1 — the script is the SCRIPT, not the whole argv
    assert "/home/ops/scripts/run_wrapper.ksh" in by_target
    # 2 — the jar is the target; the java verb is not
    assert "/apps/etl/dt-accelerators/dt-launcher-current.jar" in by_target
    # 3 — the parameter file lands in the field named for it, from either shape
    assert by_target["/home/ops/scripts/run_wrapper.ksh"].config_path == "job_a.pset"
    assert (
        by_target["/apps/etl/dt-accelerators/dt-launcher-current.jar"].config_path
        == "/apps/etl/tenants/cfg/70004-epv-conf.json"
    )
    # 4 — the directory is the artifact's, never the shell verb's, and never the
    #     config's for a jar launch
    assert facts.script_directories() == [
        "/apps/etl/dt-accelerators",
        "/home/ops/scripts",
    ]
    # and the kinds come from the parser, not from a suffix test
    assert by_target["/home/ops/scripts/run_wrapper.ksh"].kind == "SHELL_SCRIPT"
    assert [fact.target for fact in facts.shell_scripts()] == ["/home/ops/scripts/run_wrapper.ksh"]


def test_one_script_invoked_by_two_jobs_is_one_row_with_two_callers(
    generator, clone_samples: Path
) -> None:
    """The fan-out the folder-set profiler measures, not two look-alike scripts."""
    facts = generator.load_from_samples("PRARAG-HLDM-70002-PEX-RFND-DLY", samples_dir=clone_samples)
    shared = "/home/ops/scripts/run_wrapper.ksh"
    facts.jobs[0]["cmd_line"] = f"{shared} first.pset"
    facts.jobs[1]["cmd_line"] = f"{shared} second.pset"
    scripts = facts.shell_scripts()
    assert len(scripts) == 1, f"one wrapper, two argument sets, {len(scripts)} rows"
    assert len(scripts[0].jobs) == 2, "both invoking jobs must be named on the row"


def test_a_condition_with_two_emitters_names_both(generator, clone_samples: Path) -> None:
    """Naming only the first sends a reader chasing a late upstream to the wrong job.

    The bundled estate has this case for real: one condition name is raised from
    two different folders.
    """
    facts = generator.load_from_samples("PRARAG-HLDM-70002-PEX-RFND-DLY", samples_dir=clone_samples)
    multi = [name for name, raising in facts.emitters.items() if len(raising) > 1]
    assert multi, "the bundled estate is expected to contain a multi-emitter condition"
    rendered = facts.emitted_by(multi[0])
    assert " or " in rendered, f"only one emitter named for {multi[0]}: {rendered}"


def test_every_declared_header_row_has_a_value_the_renderer_can_supply(
    generator, spec: dict, clone_samples: Path
) -> None:
    """`header_rows` is spec DATA; the values are code. Keep them in step.

    Adding a row through the documented change path — edit the outline, edit the
    spec — used to crash the renderer with a `KeyError` while the column-drift
    guard passed, because that guard compares a column against the outline's
    guidance and has nothing to say about the renderer's dict. The renderer now
    falls back to the unknown token, and this pins the gap so it is reported here
    rather than discovered at render time.
    """
    facts = generator.load_from_samples("PRARAG-HLDM-70002-PEX-RFND-DLY", samples_dir=clone_samples)
    supplied = set(generator.etl_header_values(facts, facts.jobs[0]))
    declared = {row for section in spec["sections"] for row in (section.get("header_rows") or [])}
    assert declared <= supplied, (
        "section-spec.yaml declares per-workflow header rows the renderer has no "
        f"value for: {sorted(declared - supplied)}"
    )


def test_the_row_counter_charges_a_table_for_its_own_header_only(generator) -> None:
    """A label-less header must not cost a real row its place in the count.

    The cover's carrying/total figure is the number SKILL.md tells a reader to
    trust over the section labels, so the way it is counted is a contract. Two
    shapes pin it, and the first is the one that was wrong: the per-workflow
    block renders a two-column table whose header is `|  |  |`, which carries
    nothing, while the counter discounted one header per table in aggregate —
    so every such table silently ate a genuine row. The second shape pins the
    rule the counter was rewritten FOR: a row of nothing but unknown tokens is
    not a row the bundle filled.
    """
    unknown = generator.UNKNOWN
    label_less = "\n".join(["|  |  |", "|---|---|", f"| **Folder name** | `{'F1'}` |"])
    assert generator._row_counts(label_less) == (
        1,
        1,
    ), "a label-less header is not a carrying row and must not be discounted as one"

    all_unknown = "\n".join(
        ["| Item | A | B |", "|---|---|---|", f"| Session log files | {unknown} | {unknown} |"]
    )
    assert generator._row_counts(all_unknown) == (
        0,
        1,
    ), "a row whose every value cell is the unknown token carries nothing"


def test_a_job_waiting_only_on_other_folders_is_not_called_a_successor(
    generator, spec: dict, clone_samples: Path
) -> None:
    """Run-order roles are derived from THIS folder's edges, not from `end_folder`.

    An engineer restarting mid-batch reads this column to decide what has to be
    back up first. Calling every non-terminal job "intermediate" told them a job
    follows the row above it, which for a folder of independent jobs is false and
    expensive at 03:00. Both branches are live in the bundled estate, so both are
    asserted here rather than one being taken on faith: the refund folder's jobs
    wait only on OTHER folders, and the trust folder genuinely chains internally.
    """

    fill = "end_to_end_process"
    section = next(s for s in spec["sections"] if s.get("fill") == fill)

    def roles_for(folder: str) -> str:
        facts = generator.load_from_samples(folder, samples_dir=clone_samples)
        return generator.RENDERERS[fill](section, facts, {})

    independent = roles_for("PRARAG-HLDM-70002-PEX-RFND-DLY")
    assert (
        "parallel — waits only on other folders" in independent
    ), "a job waiting only on other folders must not be presented as following the row above it"
    assert (
        "follows a job in this folder" not in independent
    ), "the refund folder chains nothing internally; claiming it does invents a predecessor"

    chained = roles_for("PRARAG-HLDM-70011-PEX-TRUST-DLY")
    assert (
        "follows a job in this folder" in chained
    ), "the trust folder does chain internally — a real successor must still be named one"


def test_every_na_section_carries_a_reason(spec: dict) -> None:
    """`N/A` on its own is an omission; `N/A — <reason>` is an answer."""
    for section in spec["sections"]:
        if section.get("na_for_batch"):
            assert section.get("na_reason"), f"{section['anchor']} is N/A with no reason"


# --------------------------------------------------------------------------
# 4 — publish boundary
# --------------------------------------------------------------------------


#: An application id. The negative lookbehind excludes a digit AND a `K`, so an
#: employee SID is not read as an application id — they are different things with
#: the same digit width and they get different rules below.
_FIVE_PLUS_DIGITS = re.compile(r"(?<![0-9K])\d{5,7}(?![0-9])")

#: A person. The one identifier class a generated run book must never invent.
_EMPLOYEE_SID = re.compile(r"\bK\d{5,7}\b")


def test_no_generated_document_carries_an_id_outside_the_reserved_block(
    generator, clone_samples: Path
) -> None:
    """Sweep the VALUE, not the field — ids hide inside folder-name strings.

    Two rules, because there are two identifier classes and only one of them has
    a reserved range. An APPLICATION id must sit inside 70001-70099. A PERSON
    identifier has no range to check, so the rule is provenance instead: every
    SID in the output must be one the fixture put in the input. A generator that
    echoes its input is doing its job; one that emits a SID from anywhere else is
    the thing this guard exists to catch.
    """
    app_offenders: list[str] = []
    sid_offenders: list[str] = []
    for name in _sample_folder_names(clone_samples):
        document = generator.render(
            generator.load_from_samples(name, samples_dir=clone_samples),
            generator.load_spec(),
            _meta(),
        )
        for token in _FIVE_PLUS_DIGITS.findall(document):
            if int(token) not in SYNTHETIC_BLOCK:
                app_offenders.append(f"{name}: {token}")
        for sid in _EMPLOYEE_SID.findall(document):
            if sid not in _FIXTURE_SIDS:
                sid_offenders.append(f"{name}: {sid}")
    assert app_offenders == [], (
        "a generated document carries a numeric id outside the reserved synthetic "
        f"block 70001-70099: {sorted(set(app_offenders))}"
    )
    assert sid_offenders == [], (
        f"a generated document carries an employee SID that was not in its input: "
        f"{sorted(set(sid_offenders))}"
    )


def test_the_sweep_actually_reaches_the_rows_that_carry_people(
    generator, clone_samples: Path, tracked_only_samples: Path
) -> None:
    """The guard above is worthless unless the ownership rows are in its reach.

    This is the control for it. With the fixture's SEAL bundle the escalation
    table has rows and the sweep sees SIDs; with a bare clone it has none, which
    is correct behaviour and also why the previous version of the boundary sweep
    was green for the wrong reason — it never rendered a single contact.
    """
    name = "PRARAG-HLDM-70002-PEX-RFND-DLY"
    with_seal = generator.render(
        generator.load_from_samples(name, samples_dir=clone_samples), generator.load_spec(), _meta()
    )
    assert _EMPLOYEE_SID.findall(with_seal), (
        "the fixture's SEAL bundle did not reach the rendered document — the "
        "publish-boundary sweep would be passing without ever seeing a person"
    )
    assert set(_EMPLOYEE_SID.findall(with_seal)) <= _FIXTURE_SIDS

    bare = generator.render(
        generator.load_from_samples(name, samples_dir=tracked_only_samples),
        generator.load_spec(),
        _meta(),
    )
    assert not _EMPLOYEE_SID.findall(
        bare
    ), "a clone with no SEAL samples produced a person identifier from somewhere"


def test_the_committed_skill_files_carry_no_real_looking_ids() -> None:
    """The same sweep over what is COMMITTED, which is the half that publishes."""
    offenders = []
    for path in sorted(SKILL_DIR.rglob("*")):
        if not path.is_file() or path.suffix not in {".md", ".yaml", ".py"}:
            continue
        for token in _FIVE_PLUS_DIGITS.findall(path.read_text(encoding="utf-8")):
            if int(token) not in SYNTHETIC_BLOCK:
                offenders.append(f"{path.name}: {token}")
    assert offenders == [], f"committed skill files carry non-synthetic ids: {offenders}"


# --------------------------------------------------------------------------
# the sibling contract
# --------------------------------------------------------------------------


def test_the_excel_sibling_no_longer_calls_this_skill_future(spec: dict) -> None:
    """L23's last acceptance clause: the forward reference resolves once this lands."""
    excel = REPO_ROOT / ".claude" / "skills" / "controlm-runbook-automation-excel" / "SKILL.md"
    text = excel.read_text(encoding="utf-8")
    for stale in ("a future -SDLC sibling", "planned `-SDLC` generator sibling"):
        assert stale not in text, f"the -excel SKILL.md still says {stale!r}"
    assert (
        "controlm-runbook-automation-SDLC" in text
    ), "the -excel SKILL.md should name the sibling now that it exists"


def test_the_skill_declares_its_identity_header(spec: dict) -> None:
    """The spec is skill-owned governed data, so it carries the identity header."""
    assert spec["schema"] == "drydocs.sdlc-runbook-section-spec.v1"
    assert spec["classification"] in {"External", "Internal-Public", "Internal"}
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(spec["updated"]))
    assert SKILL_MD.exists(), "every skill directory carries a SKILL.md"
