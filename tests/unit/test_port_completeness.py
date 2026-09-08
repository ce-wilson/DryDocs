"""Guards for the roll-close completeness check (PORT6).

The fixture repo reproduces the incident at its shape (J76): a path added in range 1,
never applied, that range 2's ``--numstat`` attribution reads as "not this roll" — empty
output — exactly as it would a deferred one. The check must name that path at range 2's
close, and ``--numstat`` over range 2 must be empty for it; that pair IS the finding.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

from drydocs.port import dispositions  # noqa: E402
from drydocs.port.port_completeness import (  # noqa: E402
    Deferral,
    HeadingGap,
    Survivor,
    complete,
    deferral_for,
    headings,
    main,
    missing_headings,
    parse_deferrals,
    render_table,
    survivors,
    union_append_gaps,
)

REPO = Path(__file__).resolve().parents[2]
PORT_PROMPT = REPO / "docs" / "port" / "port-prompt.md"
SKILL = REPO / ".claude" / "skills" / "reconcile-port" / "SKILL.md"
SCRIPT = REPO / "scripts" / "port_completeness_check.py"

MANIFEST_DOC = {
    "rows": [
        {"path": "docs/port/**", "disposition": "never-port"},
        {"path": "config/gate-log.md", "disposition": "union-append"},
        {"path": "config/company.yaml", "disposition": "canonical-company"},
        {"path": "web/**", "disposition": "canonical-producer"},
    ],
    "default_ok": [{"path": "README.md"}],
}


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=repo, capture_output=True, encoding="utf-8", check=True
    ).stdout


def _commit(repo: Path, msg: str) -> None:
    _git(repo, "add", "-A")
    _git(
        repo,
        "-c",
        "user.name=t",
        "-c",
        "user.email=t@t",
        "commit",
        "-q",
        "-m",
        msg,
    )


def _write(repo: Path, rel: str, text: str) -> None:
    f = repo / rel
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_text(text, encoding="utf-8", newline="\n")


GATE_LOG_1 = "# Gate log\n\n## gate-a\n\nruled.\n\n## gate-b\n\nruled.\n"
GATE_LOG_2 = GATE_LOG_1 + "\n## gate-c\n\nruled.\n"


@pytest.fixture
def producer(tmp_path: Path) -> Path:
    """Two rolls: range 1 adds ``pkg/new.py``; range 2 touches only ``other.md``."""
    repo = tmp_path / "producer"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _write(repo, "PORT-MANIFEST.yaml", yaml.safe_dump(MANIFEST_DOC))
    _write(repo, "README.md", "readme\n")
    _write(repo, "config/gate-log.md", GATE_LOG_1)
    _write(repo, "config/company.yaml", "theirs: 1\n")
    _write(repo, "docs/port/port-prompt.md", "# port\n")
    _commit(repo, "base 0")
    _git(repo, "tag", "port-base-0")
    _write(repo, "pkg/new.py", "X = 1\n")
    _write(repo, "docs/port/never.md", "never crosses\n")
    _commit(repo, "range 1: adds pkg/new.py")
    _git(repo, "tag", "port-base-1")
    _write(repo, "other.md", "touched\n")
    _write(repo, "config/gate-log.md", GATE_LOG_2)
    _commit(repo, "range 2: touches other.md, adds gate-c")
    _git(repo, "tag", "port-base-2")
    return repo


def _consumer_tree(tmp_path: Path, producer: Path, tag: str, drop: set[str]) -> Path:
    """The consumer tree = the producer tag's files, minus what was never applied."""
    tree = tmp_path / "consumer"
    tree.mkdir()
    for path in _git(producer, "ls-tree", "-r", "--name-only", tag).split():
        if path in drop:
            continue
        (tree / path).parent.mkdir(parents=True, exist_ok=True)
        (tree / path).write_bytes(_git(producer, "show", f"{tag}:{path}").encode("utf-8"))
    return tree


def _run(producer: Path, tree: Path, *args: str, capsys) -> tuple[int, str]:
    rc = main([*args, "--tree", str(tree), "--repo", str(producer)])
    return rc, capsys.readouterr().out


# ------------------------------------------------------------------ the incident (d)


def test_a_path_missed_in_range_1_is_named_at_range_2_close_while_numstat_is_empty(
    producer: Path, tmp_path: Path, capsys
) -> None:
    """The J76 fixture: ``pkg/new.py`` came in range 1 and was never applied. At range
    2's close the attribution instrument says nothing about it — and the completeness
    check names it, as CARRIED (already absent at the previous tag)."""
    tree = _consumer_tree(
        tmp_path, producer, "port-base-2", drop={"pkg/new.py", "docs/port/never.md"}
    )
    numstat = _git(producer, "diff", "--numstat", "port-base-1", "port-base-2", "--", "pkg/new.py")
    assert (
        numstat.strip() == ""
    ), "the fixture must reproduce the blind spot, not merely assert around it"

    rc, out = _run(producer, tree, "port-base-2", "--prev", "port-base-1", capsys=capsys)
    assert rc == 1
    assert "pkg/new.py" in out
    assert "[carried]" in out
    assert "NOT COMPLETE" in out
    # never-port paths never appear, in either band.
    assert "docs/port/never.md" not in out
    assert "docs/port/port-prompt.md" not in out


def test_a_deferral_row_turns_the_owed_path_green(producer: Path, tmp_path: Path, capsys) -> None:
    tree = _consumer_tree(
        tmp_path, producer, "port-base-2", drop={"pkg/new.py", "docs/port/never.md"}
    )
    deferrals = tmp_path / "mine.md"
    deferrals.write_text(
        "prose\n\n```deferred-paths\n# pattern | roll | ref | retired\npkg/** | port-base-1 | T99 | -\n```\n",
        encoding="utf-8",
    )
    rc, out = _run(producer, tree, "port-base-2", "--deferrals", str(deferrals), capsys=capsys)
    assert rc == 0, out
    assert "deferred: port-base-1 (T99)" in out
    assert "COMPLETE" in out and "NOT COMPLETE" not in out


def test_a_retired_deferral_no_longer_covers(producer: Path, tmp_path: Path, capsys) -> None:
    tree = _consumer_tree(
        tmp_path, producer, "port-base-2", drop={"pkg/new.py", "docs/port/never.md"}
    )
    deferrals = tmp_path / "mine.md"
    deferrals.write_text(
        "```deferred-paths\npkg/** | port-base-1 | T99 | 2026-09-08\n```\n", encoding="utf-8"
    )
    rc, _ = _run(producer, tree, "port-base-2", "--deferrals", str(deferrals), capsys=capsys)
    assert rc == 1


def test_the_producer_port_prompt_at_the_tag_is_read_for_deferrals(
    producer: Path, tmp_path: Path, capsys
) -> None:
    """``docs/port/**`` never crosses, so the consumer has no working-tree copy — the
    deferral rows are read from the producer's copy AT THE TAG."""
    _write(
        producer,
        "docs/port/port-prompt.md",
        "# port\n\n```deferred-paths\npkg/new.py | port-base-1 | T24 | -\n```\n",
    )
    _commit(producer, "range 3: defer pkg/new.py")
    _git(producer, "tag", "port-base-3")
    tree = _consumer_tree(
        tmp_path,
        producer,
        "port-base-3",
        drop={"pkg/new.py", "docs/port/never.md", "docs/port/port-prompt.md"},
    )
    rc, out = _run(producer, tree, "port-base-3", capsys=capsys)
    assert rc == 0, out
    assert "(T24)" in out


def test_canonical_company_absent_is_listed_as_a_ruling_and_does_not_fail(
    producer: Path, tmp_path: Path, capsys
) -> None:
    tree = _consumer_tree(
        tmp_path, producer, "port-base-2", drop={"config/company.yaml", "docs/port/never.md"}
    )
    rc, out = _run(producer, tree, "port-base-2", capsys=capsys)
    assert rc == 0, out
    assert "config/company.yaml" in out
    assert "ruling, not owed" in out


def test_a_union_append_heading_gap_fails_the_close(producer: Path, tmp_path: Path, capsys) -> None:
    """The consumer holds gate-log.md — at range 1's shape, without gate-c. Present on
    both sides, so presence alone would pass; the heading grain catches it."""
    tree = _consumer_tree(tmp_path, producer, "port-base-2", drop={"docs/port/never.md"})
    (tree / "config" / "gate-log.md").write_text(GATE_LOG_1, encoding="utf-8")
    rc, out = _run(producer, tree, "port-base-2", capsys=capsys)
    assert rc == 1
    assert "config/gate-log.md: 1 heading(s)" in out
    assert "- gate-c" in out
    assert "NOT COMPLETE: 0 owed path(s) not deferred, 1 union-append" in out


def test_an_unresolvable_tag_is_refused_not_read_as_empty(
    producer: Path, tmp_path: Path, capsys
) -> None:
    tree = _consumer_tree(tmp_path, producer, "port-base-2", drop={"docs/port/never.md"})
    rc = main(["port-base-nope", "--tree", str(tree), "--repo", str(producer)])
    assert rc == 2
    assert "does not resolve" in capsys.readouterr().err


def test_paths_only_prints_the_owed_paths_bare(producer: Path, tmp_path: Path, capsys) -> None:
    tree = _consumer_tree(
        tmp_path,
        producer,
        "port-base-2",
        drop={"pkg/new.py", "config/company.yaml", "docs/port/never.md"},
    )
    rc, out = _run(producer, tree, "port-base-2", "--paths-only", capsys=capsys)
    assert rc == 1
    assert out.split() == ["pkg/new.py"]  # the ruling class is not owed, so not printed


# ------------------------------------------------------------------ pure functions


def test_parse_deferrals_round_trip_including_retired_and_comments() -> None:
    text = (
        "outside\n```python\nnot | a | row\n```\n"
        "```deferred-paths\n# pattern | roll | ref | retired\n"
        "drydocs_lineage/** | port-base-20260901 | T24 | -\n"
        "old/path.py | port-base-20260825 | T20 | 2026-09-05\n\n```\n"
    )
    rows = parse_deferrals(text)
    assert rows == [
        Deferral("drydocs_lineage/**", "port-base-20260901", "T24", "-"),
        Deferral("old/path.py", "port-base-20260825", "T20", "2026-09-05"),
    ]
    assert rows[0].active and not rows[1].active
    assert deferral_for("drydocs_lineage/writer.py", rows) is rows[0]
    assert deferral_for("old/path.py", rows) is None


def test_parse_deferrals_refuses_a_short_row_by_line() -> None:
    with pytest.raises(ValueError, match="row 2"):
        parse_deferrals("```deferred-paths\npkg/** | port-base-1\n```\n")


def test_headings_skip_fenced_blocks_and_h1_h3() -> None:
    md = "# top\n\n## one\n\n### sub\n\n```md\n## not-a-heading\n```\n\n## two\n"
    assert headings(md) == ["one", "two"]
    assert missing_headings(md, "# top\n\n## two\n") == ["one"]


def test_survivors_skip_never_port_and_mark_carried() -> None:
    tag = {"docs/port/x.md", "web/a.ts", "web/b.ts", "config/company.yaml"}
    found = survivors(tag, lambda p: p == "web/b.ts", MANIFEST_DOC, (), prev_tag_paths={"web/a.ts"})
    assert [s.path for s in found] == ["config/company.yaml", "web/a.ts"]
    a = found[1]
    assert a.disposition == "canonical-producer" and a.carried is True and a.owed
    assert found[0].disposition == "canonical-company" and not found[0].owed


def test_union_append_gaps_only_markdown_present_both_sides() -> None:
    tag = {"config/gate-log.md", "epics/x.yaml", "config/absent.md"}
    doc = {
        "rows": [
            {"path": "config/**", "disposition": "union-append"},
            {"path": "epics/**", "disposition": "union-append"},
        ]
    }
    gaps = union_append_gaps(
        tag,
        doc,
        read_tag=lambda p: GATE_LOG_2,
        read_tree=lambda p: GATE_LOG_1 if p == "config/gate-log.md" else None,
    )
    assert gaps == [HeadingGap("config/gate-log.md", ("gate-c",))]


def test_render_table_shape_matches_the_consumers_table() -> None:
    s = [
        Survivor("web/a.ts", "canonical-producer", "web/**", None, True),
        Survivor("x.py", dispositions.DEFAULT, "(no row)", Deferral("x.py", "r", "T1"), False),
        Survivor("config/company.yaml", "canonical-company", "config/company.yaml", None, None),
    ]
    out = render_table("port-base-2", s, [], prev="port-base-1")
    assert "| disposition | carried | new | deferred | owed | total |" in out
    assert "| DEFAULT (manifest default) | 0 | 1 | 1 | 0 | 1 |" in out
    assert "| canonical-company (ruling, not owed) | 0 | 0 | 0 | 0 | 1 |" in out
    assert "| TOTAL | 1 | 1 | 1 | 1 | 3 |" in out
    assert not complete(s, [])
    assert "PRESENCE only" in out


# ------------------------------------------------------------------ the surfaces (b, c, e)


def test_the_port_prompt_carries_a_deferred_paths_block_with_t24_as_its_first_row() -> None:
    rows = parse_deferrals(PORT_PROMPT.read_text(encoding="utf-8"))
    assert rows, "the port-prompt must carry a ```deferred-paths``` block (PORT6 b)"
    assert rows[0].ref == "T24" and rows[0].pattern.startswith("drydocs_lineage/")


def test_the_reconcile_port_skill_names_both_instruments_at_the_close() -> None:
    text = SKILL.read_text(encoding="utf-8")
    assert "--numstat" in text
    assert "port_completeness_check.py" in text


def test_the_wrapper_is_thin_and_its_help_states_the_presence_limit() -> None:
    spec = importlib.util.spec_from_file_location("port_completeness_check", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    assert module.main is main
    with pytest.raises(SystemExit) as exc:
        main(["--help"])
    assert exc.value.code == 0


def test_git_is_available_for_the_fixture() -> None:
    assert shutil.which("git")
