"""LIN2 - ``drydocs lineage-load``: the thin verb over ``drydocs_lineage.writer``.

What the verb owns and this file proves (acceptance e): PLAN-ONLY IS THE DEFAULT and
needs no database (the unit conftest's non-terminal console); the newest artifact is
derived from the zone without opening a file; curation is the gate (no decisions file
-> the empty set, said out loud; a stale decisions file -> refused); the planned label's
refusal is PRINTED at --write, never swallowed; the extract's provenance (run id, code
commit, the dirty marker) is printed. The write path against a real database is the
integration test (``tests/integration/test_lineage_load_e2e.py``, J9) and the writer's
own mechanics are ``test_lineage_writer.py``.

Every run sets ``DRYDOCS_DATA_ROOT`` to a tmp directory. The ``--write`` runs here go
through a FAKE client patched onto ``drydocs.cli._client`` (the S8 seam), so no
connection is ever attempted.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from drydocs import cli as cli_mod
from drydocs_lineage.curation import DECISIONS_SCHEMA

runner = CliRunner()
_ANSI = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return re.sub(r"\s+", " ", _ANSI.sub("", text))


def _env(tmp_path: Path, monkeypatch) -> Path:
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "logs"))
    return tmp_path / "lineage" / "staged"


def _stage(tmp_path: Path, monkeypatch) -> Path:
    """One extract over the bundled samples; returns the artifact it wrote."""
    staged = _env(tmp_path, monkeypatch)
    result = runner.invoke(cli_mod.app, ["lineage-extract"])
    assert result.exit_code == 0, _plain(result.output)
    files = sorted(staged.glob("lineage-*.json"))
    assert len(files) == 1
    return files[0]


def _decisions(path: Path, rels: list[list[str]], decision: str = "confirmed") -> Path:
    out = path.parent / "decisions.json"
    out.write_text(
        json.dumps(
            {
                "schema": DECISIONS_SCHEMA,
                "doc": "test",
                "exported": "2026-09-04T00:00:00Z",
                "decisions": [
                    {"from": a, "type": t, "to": b, "decision": decision} for a, t, b in rels
                ],
            }
        ),
        encoding="utf-8",
    )
    return out


class _FakeClient:
    """A Neo4jClient bound to drydocs that records what it is asked to run."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict]] = []

    def __enter__(self) -> _FakeClient:
        return self

    def __exit__(self, *exc) -> None:
        return None

    def connection_info(self) -> dict:
        return {"uri": "bolt://synthetic", "user": "u", "database": "drydocs"}

    def run(self, cypher: str, params: dict | None = None, **kwargs) -> list[dict]:
        merged = {**(params or {}), **kwargs}
        self.calls.append((cypher, merged))
        if "RETURN count(r) AS written" in cypher:
            return [{"written": len(merged["rows"])}]
        return []


def test_no_artifact_in_the_zone_says_run_the_extract(tmp_path: Path, monkeypatch) -> None:
    _env(tmp_path, monkeypatch)
    result = runner.invoke(cli_mod.app, ["lineage-load"])
    assert result.exit_code == 2
    out = _plain(result.output)
    assert "no staged lineage artifact" in out and "lineage-extract" in out


def test_plan_only_is_the_default_and_needs_no_database(tmp_path: Path, monkeypatch) -> None:
    """The newest artifact is picked by name, the extract is named (run id, code commit,
    the sources block), and with no decisions file the confirmed set is EMPTY and the
    verb says so. Nothing is connected to: ``_client`` is patched to fail loudly."""
    artifact = _stage(tmp_path, monkeypatch)

    def _no_client(*a, **k):
        raise AssertionError("plan-only must not build a client")

    monkeypatch.setattr(cli_mod, "_client", _no_client)
    result = runner.invoke(cli_mod.app, ["lineage-load"])
    assert result.exit_code == 0, _plain(result.output)
    out = _plain(result.output)
    header = json.loads(artifact.read_text(encoding="utf-8"))
    assert artifact.name in out.replace(" ", "") or artifact.stem[:20] in out.replace(" ", "")
    assert header["run_id"] in out.replace(" ", "")
    assert header["code_commit"][:12] in out.replace(" ", "")
    assert "controlm present" in out
    assert "no --confirmed decisions file: the confirmed set is EMPTY" in out
    assert "rels: 0 confirmed" in out
    assert "plan only" in out and "--write" in out


def test_the_newest_artifact_wins_by_name(tmp_path: Path, monkeypatch) -> None:
    artifact = _stage(tmp_path, monkeypatch)
    older = artifact.parent / "lineage-20250101T000000Z-older.json"
    older.write_text(artifact.read_text(encoding="utf-8"), encoding="utf-8")
    result = runner.invoke(cli_mod.app, ["lineage-load"])
    assert result.exit_code == 0, _plain(result.output)
    assert "older" not in _plain(result.output)


def test_confirmed_decisions_shape_the_plan_and_rejected_ones_stay_out(
    tmp_path: Path, monkeypatch
) -> None:
    artifact = _stage(tmp_path, monkeypatch)
    rels = json.loads(artifact.read_text(encoding="utf-8"))["graph"]["rels"]
    invokes = [r for r in rels if r[1] == "INVOKES"]
    assert len(invokes) >= 3
    confirmed = _decisions(artifact, invokes[:-1])
    doc = json.loads(confirmed.read_text(encoding="utf-8"))
    a, t, b = invokes[-1]
    doc["decisions"].append({"from": a, "type": t, "to": b, "decision": "rejected"})
    confirmed.write_text(json.dumps(doc), encoding="utf-8")

    result = runner.invoke(
        cli_mod.app, ["lineage-load", str(artifact), "--confirmed", str(confirmed)]
    )
    assert result.exit_code == 0, _plain(result.output)
    out = _plain(result.output)
    assert f"{len(invokes) - 1} confirmed, 1 rejected, 0 undecided" in out
    assert f"rels: {len(invokes) - 1} confirmed, {len(invokes) - 1} INVOKES" in out
    assert "Script" in out and "ETLProcess" in out
    assert "plan only" in out


def test_a_decisions_file_from_another_extract_is_refused(tmp_path: Path, monkeypatch) -> None:
    """Curation out of sync: a decision naming a rel this artifact does not carry."""
    artifact = _stage(tmp_path, monkeypatch)
    stale = _decisions(
        artifact, [["proc#controlm_job:1.1", "INVOKES", "proc#shell_script:/nowhere.ksh"]]
    )
    result = runner.invoke(cli_mod.app, ["lineage-load", str(artifact), "--confirmed", str(stale)])
    assert result.exit_code == 2
    out = _plain(result.output)
    assert "does not carry" in out and "re-render lineage-review" in out


def test_a_bad_decisions_file_is_refused_with_the_readers_message(
    tmp_path: Path, monkeypatch
) -> None:
    artifact = _stage(tmp_path, monkeypatch)
    bad = artifact.parent / "bad.json"
    bad.write_text(json.dumps({"schema": "nope", "decisions": []}), encoding="utf-8")
    result = runner.invoke(cli_mod.app, ["lineage-load", str(artifact), "--confirmed", str(bad)])
    assert result.exit_code == 2
    assert "not a lineage decisions file" in _plain(result.output)


def test_the_planned_label_is_named_in_the_plan_and_refused_at_write(
    tmp_path: Path, monkeypatch
) -> None:
    """scheduler_triggers is still ``planned``: the plan print names the gate-bound label
    with no database at all, and --write surfaces the writer's GateBoundVocabularyError
    as a printed REFUSED line and exit 2 - never swallowed. The fake client proves no
    statement ran."""
    artifact = _stage(tmp_path, monkeypatch)
    data = json.loads(artifact.read_text(encoding="utf-8"))
    jobs = [p["node_id"] for p in data["graph"]["processes"] if p["kind"] == "controlm_job"]
    trig = [jobs[0], "TRIGGERS", jobs[1]]
    data["graph"]["rels"].append(trig)
    data["graph"]["stats"]["rels"] += 1
    artifact.write_text(json.dumps(data), encoding="utf-8")
    confirmed = _decisions(artifact, [trig])

    result = runner.invoke(
        cli_mod.app, ["lineage-load", str(artifact), "--confirmed", str(confirmed)]
    )
    assert result.exit_code == 0, _plain(result.output)
    assert "GATE-BOUND: TRIGGERS (scheduler_triggers) is planned" in _plain(result.output)

    fake = _FakeClient()
    monkeypatch.setattr(cli_mod, "_client", lambda database=None: fake)
    result = runner.invoke(
        cli_mod.app, ["lineage-load", str(artifact), "--confirmed", str(confirmed), "--write"]
    )
    assert result.exit_code == 2
    out = _plain(result.output)
    assert "REFUSED" in out and "scheduler_triggers=planned" in out
    assert fake.calls == [], "the gate refuses before any statement runs"


def test_write_runs_the_stamped_plan_through_the_drydocs_client(
    tmp_path: Path, monkeypatch
) -> None:
    """--write asks for the drydocs-bound client and runs the plan: the :JobRun opens
    with the artifact's run id and sources block, every node/rel row carries the
    extract's run id and code commit, and the summary names both runs."""
    artifact = _stage(tmp_path, monkeypatch)
    data = json.loads(artifact.read_text(encoding="utf-8"))
    invokes = [r for r in data["graph"]["rels"] if r[1] == "INVOKES"]
    confirmed = _decisions(artifact, invokes)
    fake = _FakeClient()
    asked: list[str | None] = []

    def _client(database=None):
        asked.append(database)
        return fake

    monkeypatch.setattr(cli_mod, "_client", _client)
    result = runner.invoke(
        cli_mod.app, ["lineage-load", str(artifact), "--confirmed", str(confirmed), "--write"]
    )
    assert result.exit_code == 0, _plain(result.output)
    assert asked == ["drydocs"]
    out = _plain(result.output)
    assert f"wrote {len(invokes)} rel(s) to drydocs" in out
    assert data["run_id"] in out.replace(" ", "")
    opened = [p for c, p in fake.calls if "MERGE (run:JobRun" in c]
    assert len(opened) == 1
    assert opened[0]["extract_run_id"] == data["run_id"]
    assert opened[0]["extract_code_commit"] == data["code_commit"]
    assert [json.loads(s)["hop"] for s in opened[0]["sources"]] == [
        s["hop"] for s in data["sources"]
    ]
    assert all(
        p["extract_run_id"] == data["run_id"] for c, p in fake.calls if "rows" in p
    ), "every MERGE row batch carries the extract's run id"
    closed = [c for c, _ in fake.calls if "COMPLETED" in c]
    assert len(closed) == 1 and "COMPLETED" in fake.calls[-1][0]


def test_write_with_nothing_confirmed_writes_nothing(tmp_path: Path, monkeypatch) -> None:
    artifact = _stage(tmp_path, monkeypatch)
    fake = _FakeClient()
    monkeypatch.setattr(cli_mod, "_client", lambda database=None: fake)
    result = runner.invoke(cli_mod.app, ["lineage-load", str(artifact), "--write"])
    assert result.exit_code == 0, _plain(result.output)
    assert "nothing confirmed - nothing to write" in _plain(result.output)
    assert fake.calls == []


def test_a_dirty_extract_is_flagged_on_the_load(tmp_path: Path, monkeypatch) -> None:
    """The LIN1 follow-up at load time: an artifact staged from uncommitted code says so
    where the load reads it."""
    artifact = _stage(tmp_path, monkeypatch)
    data = json.loads(artifact.read_text(encoding="utf-8"))
    data["code_commit"] = "0123456789abcdef0123456789abcdef01234567-dirty"
    artifact.write_text(json.dumps(data), encoding="utf-8")
    result = runner.invoke(cli_mod.app, ["lineage-load", str(artifact)])
    assert result.exit_code == 0, _plain(result.output)
    assert "DIRTY TREE" in _plain(result.output)
