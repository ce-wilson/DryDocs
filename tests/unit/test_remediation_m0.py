"""M0 PoC slice behavior (ADR 0002-B gates 1/2/4, mechanized).

Reproduces the M0 worked example's mechanism on SYNTHETIC data (real values are
Internal and live under internal/remediation/ only): the transcript loads (gate 1),
the classifier-backed detector flags dot-smuggling (gate 2), the legacy template
resolves to a clean baseline, and the modern-style rewrite DIVERGES under the current
resolver (gate 4 — the headline M0 finding; adjudication = ground truth A3 / the
var.text rule B1, deliberately NOT resolved in code).
"""
from __future__ import annotations

from pathlib import Path

from drydocs_remediation.detect import DOT_SMUGGLING_RULE_ID, detect_findings
from drydocs_remediation.equivalence import prove_equivalence, resolved_watch
from drydocs_remediation.formats import TranscriptDefinitionFormat

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures" / "remediation"
LEGACY = FIXTURES / "synthetic-legacy-transcript.yaml"
MODERN = FIXTURES / "synthetic-modern-transcript.yaml"


def _load(path: Path):
    return TranscriptDefinitionFormat().load(path)


def test_transcript_loads_gate1() -> None:
    ds = _load(LEGACY)
    assert ds.folders[0].name == "FOLDER-SYNTH-SAMPLE-DLY"
    assert len(ds.jobs) == 1
    job = ds.jobs[0]
    assert job.job_type == "FileWatcher"
    assert job.variables[0] == ("%%DIR_A", "/data/sample/in/")
    assert job.watch_template.startswith("%%DIR_A.")


def test_transcript_round_trips(tmp_path: Path) -> None:
    ds = _load(LEGACY)
    out = TranscriptDefinitionFormat().dump(ds, tmp_path / "again.yaml")
    ds2 = _load(out)
    assert ds2.jobs[0].variables == ds.jobs[0].variables
    assert ds2.jobs[0].watch_template == ds.jobs[0].watch_template


def test_detect_flags_dot_smuggling_gate2() -> None:
    findings = detect_findings(_load(LEGACY))
    assert len(findings) == 1
    f = findings[0]
    assert f.rule_id == DOT_SMUGGLING_RULE_ID
    assert f.target == "JOB0001_SAMPLE_DAILY_INDICATOR_TOK_FW:SUFX"
    assert f.ratified is False  # registry ratification is gate territory (M1)
    # the clean modern shape has nothing to flag
    assert detect_findings(_load(MODERN)) == []


def test_legacy_baseline_resolves_clean() -> None:
    ds = _load(LEGACY)
    watch = resolved_watch(ds.folder_variables(), ds.jobs[0])
    # every '.' between %%refs is consumed as the concatenation delimiter; the only
    # surviving dot is the smuggled SUFX='.'; %%$ODATE canonicalizes to {ODATE}
    assert watch == "/data/sample/in/Sample_File_{ODATE}.tok"


def test_equivalence_reproduces_the_m0_divergence_gate4() -> None:
    report = prove_equivalence(_load(LEGACY), _load(MODERN))
    assert report.compared_jobs == 1
    assert report.equivalent is False
    (div,) = report.divergences
    # the modern %%var.text shape gains a '.' after the dir and keeps the template
    # dots under the current resolver — the B1 question, pending ground truth (A3)
    assert "'/data/sample/in/Sample_File_{ODATE}.tok'" in div
    assert "'/data/sample/in/.Sample_File_.{ODATE}.tok'" in div


def test_equivalence_passes_on_identical_behavior() -> None:
    report = prove_equivalence(_load(LEGACY), _load(LEGACY))
    assert report.equivalent is True
    assert report.compared_jobs == 1
    assert report.divergences == []
