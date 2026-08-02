"""The crosswalk runtime consumer (S2 / ADR 0008 rule 3) — no Neo4j required.

`config/crosswalks/*.yaml` was gate-confirmed data with NO runtime reader, so a
`fidelity: no-equivalent` row was a warning in prose that nothing could enforce.
These guards pin the behaviour that replaces the prose:

- an unmappable concept RAISES rather than resolving to a near-miss;
- an `approximate` mapping resolves but announces that it is lossy;
- a `status: proposed` crosswalk is refused at runtime by default;
- the committed crosswalks both parse, and their no-equivalent rows are the
  ontology-mapper queue rather than a silent gap.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_core.orchestration.crosswalk import (
    DEFAULT_CROSSWALK_DIR,
    FIDELITIES,
    SCHEMA_ID,
    CrosswalkError,
    NoEquivalentError,
    UnknownConceptError,
    UnknownOrchestratorError,
    load_crosswalk,
    load_crosswalks,
    orchestrators,
    resolve,
    unmappable,
)

_CONFIRMED = ("autosys", "airflow")


# --- the committed crosswalks -------------------------------------------------
def test_committed_crosswalks_load_and_are_confirmed() -> None:
    walks = load_crosswalks()
    assert {cw.orchestrator for cw in walks} == set(_CONFIRMED)
    for cw in walks:
        assert cw.confirmed, f"{cw.id}: status {cw.status!r} — a gate signed these off"
        assert cw.baseline == "bmc-controlm"
        assert cw.rows, f"{cw.id}: no rows"


def test_every_row_carries_a_known_fidelity() -> None:
    """A new tier is a gate decision, so an unknown value must fail loudly."""
    for cw in load_crosswalks():
        for row in cw.rows:
            assert row.fidelity in FIDELITIES, f"{cw.id} row {row.native!r}: {row.fidelity!r}"


def test_orchestrators_are_discoverable() -> None:
    assert orchestrators() == tuple(sorted(_CONFIRMED))


# --- the ruling: no-equivalent REFUSES ----------------------------------------
def test_no_equivalent_raises_rather_than_approximating() -> None:
    """ADR 0008 rule 3. The failure this prevents is silent: an unmapped concept
    rendered as the nearest Control-M label puts an unruled assertion in the graph."""
    gaps = unmappable("airflow")
    assert gaps, "airflow's crosswalk records no-equivalent rows; the fixture is stale"
    with pytest.raises(NoEquivalentError):
        resolve(gaps[0].native, "airflow")


def test_every_no_equivalent_row_refuses() -> None:
    for cw in load_crosswalks():
        for row in cw.no_equivalents():
            with pytest.raises(NoEquivalentError):
                resolve(row.native, cw.orchestrator)


def test_no_equivalent_message_routes_to_the_gate() -> None:
    row = unmappable("airflow")[0]
    with pytest.raises(NoEquivalentError, match="ontology-mapper"):
        resolve(row.native, "airflow")


# --- resolution ----------------------------------------------------------------
def test_exact_row_resolves_to_the_baseline_concept() -> None:
    m = resolve("Task", "airflow")
    assert m.baseline == "Job"
    assert m.node == "ControlMJob"
    assert m.fidelity == "exact"
    assert not m.is_lossy


def test_approximate_resolves_but_announces_the_loss() -> None:
    """The middle tier is the point: it must not read as `exact` to a caller."""
    m = resolve("DAG", "airflow")
    assert m.fidelity == "approximate"
    assert m.is_lossy


def test_match_ignores_the_syntax_parenthetical() -> None:
    """Rows read `Job (\\`insert_job: ...\\`)`; callers hold the label."""
    assert resolve("job", "autosys").baseline == "Job"
    assert resolve("  JOB  ", "autosys").baseline == "Job"


def test_unknown_orchestrator_and_concept_raise_distinctly() -> None:
    with pytest.raises(UnknownOrchestratorError):
        resolve("Task", "dollar-universe")
    with pytest.raises(UnknownConceptError):
        resolve("Kubernetes CronJob", "autosys")


# --- malformed input fails loudly ---------------------------------------------
def _write(tmp_path: Path, body: str) -> Path:
    p = tmp_path / "probe-to-bmc.yaml"
    p.write_text(body, encoding="utf-8")
    return p


def test_wrong_schema_is_refused(tmp_path: Path) -> None:
    p = _write(tmp_path, "schema: drydocs.something-else\norchestrator: probe\nrows: [{n: 1}]\n")
    with pytest.raises(CrosswalkError, match="schema"):
        load_crosswalk(p)


def test_unknown_fidelity_is_refused(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        f"schema: {SCHEMA_ID}\norchestrator: probe\nrows:\n"
        "  - {n: 1, native: Job, baseline: Job, fidelity: probably}\n",
    )
    with pytest.raises(CrosswalkError, match="not one of"):
        load_crosswalk(p)


def test_duplicate_native_term_is_refused(tmp_path: Path) -> None:
    p = _write(
        tmp_path,
        f"schema: {SCHEMA_ID}\norchestrator: probe\nrows:\n"
        "  - {n: 1, native: Job, baseline: Job, fidelity: exact}\n"
        "  - {n: 2, native: Job, baseline: Folder, fidelity: exact}\n",
    )
    with pytest.raises(CrosswalkError, match="duplicate"):
        load_crosswalk(p)


def test_empty_rows_is_refused(tmp_path: Path) -> None:
    p = _write(tmp_path, f"schema: {SCHEMA_ID}\norchestrator: probe\nrows: []\n")
    with pytest.raises(CrosswalkError, match="non-empty"):
        load_crosswalk(p)


def test_proposed_crosswalk_is_not_a_runtime_mapping(tmp_path: Path) -> None:
    """A proposed crosswalk is a gate's INPUT. Runtime use needs the opt-out."""
    (tmp_path / "probe-to-bmc.yaml").write_text(
        f"schema: {SCHEMA_ID}\nid: probe\norchestrator: probe\nstatus: proposed\nrows:\n"
        "  - {n: 1, native: Job, baseline: Job, node: ControlMJob, fidelity: exact}\n",
        encoding="utf-8",
    )
    with pytest.raises(CrosswalkError, match="proposed"):
        resolve("Job", "probe", directory=tmp_path)
    m = resolve("Job", "probe", directory=tmp_path, require_confirmed=False)
    assert m.node == "ControlMJob"


def test_default_directory_is_the_committed_one() -> None:
    assert DEFAULT_CROSSWALK_DIR.is_dir()
    assert DEFAULT_CROSSWALK_DIR.name == "crosswalks"
