"""The file-level port drop check and its accepted-drop seam (PORT4).

Three states, none of them silence: an UNRULED drop is a finding; a RULED drop is
listed under its own heading and passes; a STALE ruling (the path is back, or nothing
ever dropped it) fails. The block lives in the SIDE-LOCAL overlay and is never one of
the manifest blocks the reconcile guards union.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
import yaml

from drydocs.port import port_drops
from drydocs.port.dispositions import load_manifest
from drydocs.port.port_drops import (
    ACCEPTED_DROPS_BLOCK,
    AcceptedDrop,
    AcceptedDropError,
    check_drops,
    git_dropped_paths,
    git_tracked_paths,
    load_accepted_drops,
    parse_accepted_drops,
)
from drydocs_core.repo_paths import repo_root

REPO = repo_root(Path(__file__).resolve().parents[2])

MANIFEST_DOC = {
    "schema": "drydocs.port-manifest.v1",
    "rows": [
        {"path": "drydocs/**", "disposition": "canonical-producer"},
        {"path": "config/company.yaml", "disposition": "canonical-company"},
        {"path": "PORT-MANIFEST.*.yaml", "disposition": "never-port"},
    ],
    "default_ok": [{"path": "README.md"}],
    "overlay": {
        "files": [
            {"path": "PORT-MANIFEST.company.yaml", "side": "company"},
            {"path": "PORT-MANIFEST.producer.yaml", "side": "producer"},
        ]
    },
}

RULING = {
    "path": "drydocs/old.py",
    "report": "PORT-REPORT-70001",
    "date": "2026-09-04",
    "reason": "retired at the producer; the consumer holds no local edits to it",
}


def _ruling(**over: str) -> AcceptedDrop:
    return AcceptedDrop(**{**RULING, **over})


# ------------------------------------------------------------------ the three states


def test_an_unruled_drop_is_a_finding_and_fails():
    report = check_drops(
        dropped={"drydocs/old.py"}, present={"README.md"}, accepted=[], manifest_doc=MANIFEST_DOC
    )
    assert report.findings == (("drydocs/old.py", "canonical-producer"),)
    assert not report.accepted and not report.stale
    assert not report.passed
    text = report.render()
    assert "DROPPED, UNRULED (1)" in text
    assert "drydocs/old.py  [canonical-producer]" in text
    assert "RESULT: FAIL" in text


def test_a_ruled_drop_is_listed_under_its_own_heading_and_passes():
    report = check_drops(
        dropped={"drydocs/old.py"},
        present={"README.md"},
        accepted=[_ruling()],
        manifest_doc=MANIFEST_DOC,
    )
    assert report.passed
    assert not report.findings
    assert [(p, d) for p, d, _ in report.accepted] == [("drydocs/old.py", "canonical-producer")]
    text = report.render()
    # Listed, never silence: the ruled path, its report and its date are all in the render.
    assert "accepted drops (1) -- ruled, not findings" in text
    assert "drydocs/old.py" in text and "PORT-REPORT-70001 2026-09-04" in text
    assert "dropped, unruled: none" in text
    assert "RESULT: PASS" in text


def test_a_stale_ruling_fails_when_the_path_exists_again():
    report = check_drops(
        dropped=set(),
        present={"README.md", "drydocs/old.py"},
        accepted=[_ruling()],
        manifest_doc=MANIFEST_DOC,
    )
    assert not report.passed
    assert not report.findings and not report.accepted
    (ruling, why), *_ = report.stale
    assert ruling.path == "drydocs/old.py" and "exists again" in why
    assert "STALE ACCEPTED-DROP ROWS (1)" in report.render()


def test_a_stale_ruling_fails_when_nothing_ever_dropped_the_path():
    report = check_drops(
        dropped=set(), present={"README.md"}, accepted=[_ruling()], manifest_doc=MANIFEST_DOC
    )
    assert not report.passed
    (_, why), *_ = report.stale
    assert "nothing dropped this path" in why


def test_a_ruling_never_hides_a_different_unruled_drop():
    """One ruling covers ONE path; every other drop stays a finding."""
    report = check_drops(
        dropped={"drydocs/old.py", "config/company.yaml"},
        present=set(),
        accepted=[_ruling()],
        manifest_doc=MANIFEST_DOC,
    )
    assert report.findings == (("config/company.yaml", "canonical-company"),)
    assert len(report.accepted) == 1
    assert not report.passed


def test_the_render_states_ruled_drops_even_with_no_findings_and_no_rulings():
    """A clean run still says what it looked at — 'none declared' is a statement,
    not silence."""
    report = check_drops(dropped=set(), present=set(), accepted=[], manifest_doc=MANIFEST_DOC)
    assert report.passed
    assert "accepted drops: none declared" in report.render()


# ------------------------------------------------------------------ parsing the block


def test_an_overlay_without_the_block_rules_nothing():
    assert parse_accepted_drops({"default_ok": [{"path": "x"}]}) == []
    assert parse_accepted_drops(None) == []


def test_a_well_formed_block_parses_with_its_provenance():
    rows = parse_accepted_drops(
        {ACCEPTED_DROPS_BLOCK: [RULING]}, source="PORT-MANIFEST.company.yaml"
    )
    assert rows == [_ruling(source="PORT-MANIFEST.company.yaml")]


@pytest.mark.parametrize("missing", ["path", "report", "date", "reason"])
def test_a_row_missing_provenance_is_refused(missing: str):
    row = {k: v for k, v in RULING.items() if k != missing}
    with pytest.raises(AcceptedDropError, match=missing):
        parse_accepted_drops({ACCEPTED_DROPS_BLOCK: [row]})


def test_a_duplicate_path_is_refused():
    with pytest.raises(AcceptedDropError, match="ruled twice"):
        parse_accepted_drops({ACCEPTED_DROPS_BLOCK: [RULING, dict(RULING)]})


def test_a_glob_is_refused_because_a_ruling_names_one_path():
    with pytest.raises(AcceptedDropError, match="glob"):
        parse_accepted_drops({ACCEPTED_DROPS_BLOCK: [{**RULING, "path": "drydocs/*.py"}]})


def test_a_block_that_is_not_a_list_is_refused():
    with pytest.raises(AcceptedDropError, match="must be a list"):
        parse_accepted_drops({ACCEPTED_DROPS_BLOCK: {"path": "x"}})


def test_load_reads_only_the_overlays_the_manifest_declares(tmp_path: Path):
    """The declared, EXISTING overlays contribute; an absent slot contributes nothing;
    an undeclared PORT-MANIFEST.*.yaml is not read at all."""
    (tmp_path / "PORT-MANIFEST.company.yaml").write_text(
        yaml.safe_dump({ACCEPTED_DROPS_BLOCK: [RULING]}), encoding="utf-8"
    )
    (tmp_path / "PORT-MANIFEST.stray.yaml").write_text(
        yaml.safe_dump({ACCEPTED_DROPS_BLOCK: [{**RULING, "path": "drydocs/stray.py"}]}),
        encoding="utf-8",
    )
    rows = load_accepted_drops(MANIFEST_DOC, tmp_path)
    assert [r.path for r in rows] == ["drydocs/old.py"]
    assert rows[0].source == "PORT-MANIFEST.company.yaml"


def test_load_refuses_a_path_ruled_in_two_overlays(tmp_path: Path):
    for name in ("PORT-MANIFEST.company.yaml", "PORT-MANIFEST.producer.yaml"):
        (tmp_path / name).write_text(
            yaml.safe_dump({ACCEPTED_DROPS_BLOCK: [RULING]}), encoding="utf-8"
        )
    with pytest.raises(AcceptedDropError, match="more than one overlay"):
        load_accepted_drops(MANIFEST_DOC, tmp_path)


# ------------------------------------------------------------------ the live tree


def test_the_live_manifests_accepted_drops_are_well_formed():
    """Producer-side both overlay slots are normally absent, so this is usually the
    empty list — the point is that whatever IS declared parses."""
    rows = load_accepted_drops(load_manifest(REPO / "PORT-MANIFEST.yaml"), REPO)
    assert all(r.path and r.report and r.date and r.reason for r in rows)


def test_the_block_is_side_local_and_never_unioned():
    """``accepted_drops`` records one side's rulings about its own tree (J34). It
    declares no disposition and adds no coverage, so the reconcile guards must not
    union it into the manifest view — only this check reads it."""
    from tests.unit.test_port_reconcile_guards import UNIONED_BLOCKS

    assert ACCEPTED_DROPS_BLOCK not in UNIONED_BLOCKS


def test_the_entry_script_is_an_entry_point_only():
    src = (REPO / "scripts" / "port_drop_check.py").read_text(encoding="utf-8")
    assert "from drydocs.port.port_drops import main" in src


# ------------------------------------------------------------------ the git half


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, encoding="utf-8", check=True
    ).stdout


def _commit(repo: Path, msg: str) -> None:
    _git(repo, "add", "-A")
    _git(repo, "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", msg)


@pytest.fixture
def consumer(tmp_path: Path) -> Path:
    """A pre-port tag holding two files; the apply then deletes one of them."""
    repo = tmp_path / "consumer"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / "PORT-MANIFEST.yaml").write_text(yaml.safe_dump(MANIFEST_DOC), encoding="utf-8")
    (repo / "README.md").write_text("readme\n", encoding="utf-8")
    (repo / "drydocs").mkdir()
    (repo / "drydocs" / "old.py").write_text("X = 1\n", encoding="utf-8")
    _commit(repo, "pre-port")
    _git(repo, "tag", "port-base-0")
    (repo / "drydocs" / "old.py").unlink()
    _commit(repo, "apply: retires drydocs/old.py")
    return repo


def test_git_dropped_paths_is_the_cumulative_delete_set(consumer: Path):
    assert git_dropped_paths(consumer, "port-base-0") == {"drydocs/old.py"}
    assert "drydocs/old.py" not in git_tracked_paths(consumer)
    assert "README.md" in git_tracked_paths(consumer)


def test_main_reports_the_unruled_drop_then_passes_once_ruled(consumer: Path, capsys):
    rc = port_drops.main(["port-base-0", "--repo", str(consumer)])
    assert rc == 1
    assert "DROPPED, UNRULED (1)" in capsys.readouterr().out

    (consumer / "PORT-MANIFEST.company.yaml").write_text(
        yaml.safe_dump({ACCEPTED_DROPS_BLOCK: [RULING]}), encoding="utf-8"
    )
    rc = port_drops.main(["port-base-0", "--repo", str(consumer)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "accepted drops (1) -- ruled, not findings" in out and "drydocs/old.py" in out


def test_main_fails_on_a_stale_ruling_when_the_path_is_restored(consumer: Path, capsys):
    (consumer / "PORT-MANIFEST.company.yaml").write_text(
        yaml.safe_dump({ACCEPTED_DROPS_BLOCK: [RULING]}), encoding="utf-8"
    )
    (consumer / "drydocs" / "old.py").write_text("X = 2\n", encoding="utf-8")
    _commit(consumer, "restore")
    rc = port_drops.main(["port-base-0", "--repo", str(consumer)])
    assert rc == 1
    assert "STALE ACCEPTED-DROP ROWS (1)" in capsys.readouterr().out


def test_main_refuses_a_ref_that_does_not_resolve(consumer: Path, capsys):
    assert port_drops.main(["no-such-tag", "--repo", str(consumer)]) == 2
    assert "does not resolve" in capsys.readouterr().err
