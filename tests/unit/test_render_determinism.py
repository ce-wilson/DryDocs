"""Committed renders must not depend on the OS that produced them.

WHY THIS EXISTS. CI was red from 2026-07-21 to 2026-07-31 — roughly 180 runs —
on a single assertion: ``test_committed_matrix_matches_regeneration`` claiming
``enforcement-matrix.json`` had drifted. It had not. The renderer sorted
``Path`` objects, and ``PurePath.__lt__`` compares ``_str_normcase``, which is
case-FOLDED on Windows and case-SENSITIVE on POSIX::

    sorted(Path objects) on Windows -> platforms.yaml, README.md, software-registry.yaml
    sorted(Path objects) on Linux   -> README.md, platforms.yaml, software-registry.yaml

So the matrix committed from a Windows session regenerated in a different order
on the Linux runner, and the drift guard fired forever. The existing guard could
not catch it before the push, because on the authoring machine the committed
output and the regeneration agreed — both were wrong in the same direction.

That is the real lesson, and it is why this file is separate: a drift guard that
compares a render against ITSELF only detects staleness, never
platform-dependence. These tests assert the ORDERING RULE directly, so they fail
on the machine that would introduce the bug rather than on the runner that
discovers it two commits later.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO / "scripts"

#: Renderers whose output is COMMITTED and drift-checked. A per-OS ordering
#: difference in any of these reds out CI on the other platform.
COMMITTED_RENDERERS = (
    "render_enforcement_matrix.py",
    "render_load_map.py",
    "render_gates.py",
    "render_software_registry.py",
    "render_board.py",
)


def test_path_object_sorting_really_is_platform_dependent() -> None:
    """Pin the underlying cause, so the rule below reads as fact not folklore.

    On Windows this ordering is case-folded; on POSIX it is byte-order. The
    assertion is written to hold on BOTH, which is the point — the two differ.
    """
    names = ["dir/README.md", "dir/platforms.yaml", "dir/software-registry.yaml"]
    by_path = [p.name for p in sorted(Path(n) for n in names)]
    by_string = [Path(n).name for n in sorted(names)]

    # by_string is the same everywhere; by_path is not.
    assert by_string == ["README.md", "platforms.yaml", "software-registry.yaml"]
    assert by_path in (
        ["README.md", "platforms.yaml", "software-registry.yaml"],          # POSIX
        ["platforms.yaml", "README.md", "software-registry.yaml"],          # Windows
    )


def _bare_path_sorts(source: str) -> list[str]:
    """Find `sorted(<expr>)` calls with no `key=` whose argument yields Paths.

    Deliberately conservative: it flags a call only when the expression clearly
    walks the filesystem (`.glob` / `.rglob` / `.iterdir`) and nothing pulls a
    string out of it (`.name` / `.stem` / `.as_posix()`). Those string forms are
    already platform-independent, which is why they are not findings.
    """
    tree = ast.parse(source)
    findings: list[str] = []
    for node in ast.walk(tree):
        if not (isinstance(node, ast.Call) and getattr(node.func, "id", None) == "sorted"):
            continue
        if any(kw.arg == "key" for kw in node.keywords):
            continue
        if not node.args:
            continue
        blob = ast.dump(node.args[0])
        walks = any(w in blob for w in ("'glob'", "'rglob'", "'iterdir'"))
        stringified = any(s in blob for s in ("'name'", "'stem'", "'as_posix'", "'relative_to'"))
        if walks and not stringified:
            findings.append(f"line {node.lineno}")
    return findings


def test_committed_renderers_never_sort_path_objects() -> None:
    """The rule: sort filesystem walks by string, never by Path.

    Fix a finding with `key=lambda p: p.as_posix()` (or sort the strings). Do
    NOT silence it by regenerating on the other OS — that just moves which
    platform is broken.
    """
    failures: list[str] = []
    for name in COMMITTED_RENDERERS:
        script = SCRIPTS / name
        assert script.exists(), f"{name} is in COMMITTED_RENDERERS but does not exist"
        for where in _bare_path_sorts(script.read_text(encoding="utf-8")):
            failures.append(f"{name}:{where} sorts Path objects with no key=")

    assert not failures, (
        "OS-dependent ordering in a committed render:\n  "
        + "\n  ".join(failures)
        + "\nsorted() over Path compares a case-folded key on Windows and a "
          "case-sensitive one on POSIX. Use key=lambda p: p.as_posix()."
    )


def test_the_matrix_renderer_orders_a_mixed_case_directory_by_string() -> None:
    """End-to-end on the exact directory that broke CI.

    `config/taxonomy/` holds README.md beside lowercase capture files — the mix
    that makes the two orderings diverge. Asserting byte-order here means a
    Windows machine now produces the same file list the Linux runner will.
    """
    taxonomy = REPO / "config" / "taxonomy"
    rendered = sorted(
        (p for p in taxonomy.rglob("*") if p.is_file()),
        key=lambda p: p.as_posix(),
    )
    names = [p.name for p in rendered]

    assert "README.md" in names, "expected the mixed-case file that exposed the bug"
    assert names == sorted(names), (
        "config/taxonomy/ did not come out in byte order — the matrix render "
        f"would differ per-OS again. Got: {names}"
    )
    # ...and byte order specifically means the capital-R file leads.
    assert names[0] == "README.md"
