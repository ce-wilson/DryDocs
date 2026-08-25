"""G105 — the log KINDS are declared, and the naming rule derives from them.

Before this, `kind` was a filename convention rather than a code concept. Three
sites minted one and none agreed: `run_log` hardcoded the `load.` prefix,
`llm_ledger` hardcoded `qa.graph_qa`, and `sql_run_log` took a caller-supplied
`base_name` with no prefix enforcement and wrote `oracle.<ts>.log` — no kind
segment at all. Nothing could be configured per kind while no declaration said
what the kinds ARE.

The rule these tests protect is that THE FILENAME IS DERIVED, not asserted
alongside the code. ADR 0014 clause 3 as drafted asserted
`<kind>.<name>.<YYYYmmdd-HHMMSS>` and called the per-day ledger the one exception
to it; measured, that rule matched 5 of 86 real files. Deriving stamp granularity
from `rotation` and the extension from `format` makes the ledger conforming AND
the 79 `.v1` loader logs conforming, with no exception left to defend.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from drydocs_core import log_kinds as lk

_AT = datetime(2026, 8, 25, 14, 30, 15)

_MINIMAL = """
schema: drydocs.log-kinds.v1
root:
  base: home
  path: logs/DryDocs/
  env: DRYDOCS_LOGDIR
  legacy_env: SPIDERP_LOGDIR
defaults:
  level: INFO
  retention_days: 90
  rotation: per-run
  format: log
  dir: ~
kinds:
  - id: load
    note: a note
"""


def _write(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "log-kinds.yaml"
    path.write_text(body, encoding="utf-8")
    return path


# ---- the shipped declaration ------------------------------------------------


def test_the_real_declaration_loads_and_every_kind_is_complete():
    kinds = lk.load_kinds()
    assert kinds, "config/log-kinds.yaml declares nothing"
    for k in kinds:
        assert k.rotation in lk.ROTATIONS
        assert k.format in lk.FORMATS
        assert k.retention_days > 0, f"{k.id}: retention {k.retention_days} sweeps immediately"
        assert k.note.strip(), f"{k.id}: a kind with no note is a row nobody can review"


def test_the_three_families_that_disagreed_are_all_declared_now():
    """The point of the item, stated as an assertion: every writer that mints a
    filename has a row, including the SQL family that had no kind segment."""
    declared = {k.id for k in lk.load_kinds()}
    assert {"load", "qa", "sql"} <= declared


def test_a_planned_kind_is_marked_rather_than_silently_absent():
    """`api` is declared before its writer exists (G108), so the kind is real the
    moment the writer lands instead of being invented by it."""
    planned = {k.id for k in lk.load_kinds() if k.planned}
    assert "api" in planned
    assert all(k.writer for k in lk.load_kinds() if not k.planned), (
        "an ACTIVE kind must name the writer that mints it — that is the link "
        "which makes the declaration checkable rather than decorative"
    )


# ---- the derived naming rule ------------------------------------------------


def test_a_per_run_kind_stamps_to_the_second():
    assert lk.log_filename("load", "code_snapshot.v1", now=_AT) == (
        "load.code_snapshot.v1.20260825-143015.log"
    )


def test_the_per_day_ledger_is_conforming_not_excepted():
    """The clause-3 amendment, as a test. Same grammar, different rotation."""
    assert lk.log_filename("qa", "graph_qa", now=_AT) == "qa.graph_qa.20260825.jsonl"


def test_the_sql_family_gains_the_kind_segment_it_never_had():
    assert lk.log_filename("sql", "oracle", now=_AT) == "sql.oracle.20260825-143015.log"


def test_name_stays_free_form_which_is_what_makes_the_v1_files_conform():
    """The drafted rule matched 5 of 86 files because it did not know the loader
    version sits INSIDE <name>. Pinned so a future tightening cannot re-break it."""
    assert lk.log_filename("load", "a.b.c", now=_AT).startswith("load.a.b.c.")


# ---- refusals ---------------------------------------------------------------


def test_an_undeclared_kind_is_refused_and_the_message_names_what_is_declared():
    with pytest.raises(lk.LogKindError, match="undeclared log kind"):
        lk.kind("nope")


def test_a_missing_declaration_raises_rather_than_guessing(tmp_path):
    with pytest.raises(lk.LogKindError, match="missing"):
        lk.load_kinds(tmp_path / "absent.yaml")


def test_an_empty_declaration_raises(tmp_path):
    with pytest.raises(lk.LogKindError, match="declares no kinds"):
        lk.load_kinds(_write(tmp_path, "schema: drydocs.log-kinds.v1\nkinds: []\n"))


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("rotation", "hourly", "unknown rotation"),
        ("format", "txt", "unknown format"),
        ("retention_days", "forever", "whole number of days"),
    ],
)
def test_a_malformed_kind_raises_naming_the_field(tmp_path, field, value, match):
    body = _MINIMAL.replace("    note: a note", f"    note: a note\n    {field}: {value}")
    with pytest.raises(lk.LogKindError, match=match):
        lk.load_kinds(_write(tmp_path, body))


def test_two_kinds_cannot_share_an_id(tmp_path):
    body = _MINIMAL + "  - id: load\n    note: the collision\n"
    with pytest.raises(lk.LogKindError, match="duplicate kind id"):
        lk.load_kinds(_write(tmp_path, body))


# ---- root resolution --------------------------------------------------------


def test_the_generic_variable_wins_over_the_legacy_one(tmp_path, monkeypatch):
    decl = _write(tmp_path, _MINIMAL)
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path / "legacy"))
    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "generic"))
    assert lk.resolve_root(decl) == tmp_path / "generic"


def test_the_legacy_variable_still_resolves_but_warns(tmp_path, monkeypatch):
    """One more cycle, with a warning — "one cycle" with no event attached is how
    a deprecation becomes permanent, so the warning is the event's reminder."""
    decl = _write(tmp_path, _MINIMAL)
    monkeypatch.delenv("DRYDOCS_LOGDIR", raising=False)
    monkeypatch.setenv("SPIDERP_LOGDIR", str(tmp_path / "legacy"))
    with pytest.warns(DeprecationWarning, match="SPIDERP_LOGDIR"):
        assert lk.resolve_root(decl) == tmp_path / "legacy"


def test_the_declared_default_is_the_pre_g105_path(tmp_path, monkeypatch):
    """DEFAULTS UNCHANGED, proven rather than asserted (the acceptance's words).

    With the environment cleared, the declaration resolves to exactly where
    `run_log.DEFAULT_LOGDIR` pointed before this item existed.
    """
    decl = _write(tmp_path, _MINIMAL)
    monkeypatch.delenv("DRYDOCS_LOGDIR", raising=False)
    monkeypatch.delenv("SPIDERP_LOGDIR", raising=False)
    assert lk.resolve_root(decl) == Path.home() / "logs" / "DryDocs"


def test_a_caller_default_wins_only_the_last_branch(tmp_path, monkeypatch):
    """`run_log` passes DEFAULT_LOGDIR so the unit conftest's hermetic seam keeps
    working. It must NOT outrank the environment — a set DRYDOCS_LOGDIR is an
    operator's explicit choice and a caller default is a fallback."""
    decl = _write(tmp_path, _MINIMAL)
    monkeypatch.delenv("SPIDERP_LOGDIR", raising=False)
    monkeypatch.delenv("DRYDOCS_LOGDIR", raising=False)
    assert lk.resolve_root(decl, default=tmp_path / "injected") == tmp_path / "injected"

    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path / "generic"))
    assert lk.resolve_root(decl, default=tmp_path / "injected") == tmp_path / "generic"


# ---- clause 2: stdlib only, and the run-log contract is untouched -----------


def test_dictconfig_added_no_runtime_dependency():
    """ADR 0014 clause 2 is stdlib-only, asserted rather than trusted. A logging
    library is the easiest dependency in the world to reach for, and this item is
    the moment it would have happened."""
    import tomllib

    pyproject = tomllib.loads(
        (Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8")
    )
    deps = {name.lower() for name in pyproject["tool"]["poetry"]["dependencies"]}
    for banned in ("loguru", "structlog", "python-json-logger", "colorlog"):
        assert banned not in deps, f"clause 2 says stdlib only; {banned} is a runtime dep"


def test_the_run_log_header_and_summary_contract_is_unchanged(tmp_path, monkeypatch):
    """G105 changed WHERE the filename comes from, not what the file says.

    The header/summary block is a contract with readers (and with sql_run_log,
    which mirrors it deliberately), so the fields are pinned here rather than left
    to be noticed missing.
    """
    from drydocs_core.run_log import LoaderRunLog

    monkeypatch.setenv("DRYDOCS_LOGDIR", str(tmp_path))
    log = LoaderRunLog("probe.v1", "run-1", source="src", target="drydocs")
    path = log.open()
    log.close({"rows": 2})

    body = path.read_text(encoding="utf-8")
    for field in ("date", "script", "loader", "run id", "source", "target", "os user"):
        assert f"{field}" in body, f"the header lost its {field!r} line"
    assert "-- summary --" in body
    assert "warnings captured" in body and "rejects logged" in body
    assert "Done in" in body
    # and the filename now DERIVES, which is the only thing that changed
    assert path.name.startswith("load.probe.v1."), path.name
    assert path.name.endswith(".log")
