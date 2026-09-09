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

4.  **PUBLISH BOUNDARY.** Every application id the generator emits must sit
    inside the reserved synthetic block 70001-70099. The sweep is over the
    VALUE, not the field: the ids that survived an earlier cleanup were embedded
    inside folder-name strings, and a generated run book prints folder names
    everywhere.
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


@pytest.fixture(scope="module")
def clone_samples(tmp_path_factory) -> Path:
    """A samples directory holding ONLY the tracked CSVs — a fresh clone's view."""
    target = tmp_path_factory.mktemp("clone_samples")
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


def test_every_na_section_carries_a_reason(spec: dict) -> None:
    """`N/A` on its own is an omission; `N/A — <reason>` is an answer."""
    for section in spec["sections"]:
        if section.get("na_for_batch"):
            assert section.get("na_reason"), f"{section['anchor']} is N/A with no reason"


# --------------------------------------------------------------------------
# 4 — publish boundary
# --------------------------------------------------------------------------


_FIVE_PLUS_DIGITS = re.compile(r"(?<![0-9])\d{5,7}(?![0-9])")


def test_no_generated_document_carries_an_id_outside_the_reserved_block(
    generator, clone_samples: Path
) -> None:
    """Sweep the VALUE, not the field — ids hide inside folder-name strings."""
    offenders: list[str] = []
    for name in _sample_folder_names(clone_samples):
        document = generator.render(
            generator.load_from_samples(name, samples_dir=clone_samples),
            generator.load_spec(),
            _meta(),
        )
        for token in _FIVE_PLUS_DIGITS.findall(document):
            if int(token) not in SYNTHETIC_BLOCK:
                offenders.append(f"{name}: {token}")
    assert offenders == [], (
        "a generated document carries a numeric id outside the reserved synthetic "
        f"block 70001-70099: {sorted(set(offenders))}"
    )


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
