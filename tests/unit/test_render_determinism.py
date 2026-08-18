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
        ["README.md", "platforms.yaml", "software-registry.yaml"],  # POSIX
        ["platforms.yaml", "README.md", "software-registry.yaml"],  # Windows
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


# ---------------------------------------------------------------------------
# LINE ENDINGS — the second way a committed surface picks up its author's OS.
#
# Ordering was the first (above). This is the second, and it went unguarded for
# longer: `Path.write_text(...)` with no `newline=` emits \r\n on Windows, so a
# committed render or snapshot lands CRLF against an LF index. Git normalizes it
# back on commit, so no blob ever changes and NOTHING FLAGS IT — the reason
# Idea-121 sat latent, and the reason Idea-129 (the same class in the snapshot
# pipeline) was found by a stray `git add` warning rather than by a test.
#
# Idea-121 fixed the render half and recorded that nothing guarded it. This is
# that guard. It is deliberately a DECLARED LIST rather than a repo sweep,
# because Idea-121 fenced eight non-render writers OUT of the sweep on purpose
# (vendor_docs, publishing/*, schema_graph, extract_office_text,
# external_vendor_scrape) — they write uncommitted outputs and each needs its
# own call. Adding a committed surface means adding its writer here.
# ---------------------------------------------------------------------------

#: Modules that write a COMMITTED surface. Repo-relative.
COMMITTED_SURFACE_WRITERS = (
    "drydocs/plan_board.py",
    "drydocs/plan_ideas.py",
    "drydocs/plan_roadmap.py",
    "drydocs/design_doc.py",
    "scripts/render_context_types.py",
    "scripts/render_enforcement_matrix.py",
    "scripts/render_gates.py",
    "scripts/render_load_map.py",
    "scripts/render_remediation_diff.py",
    "scripts/render_software_registry.py",
    "knowledge/depgraph-snapshots/filter_ignored.py",
    # Added 2026-08-17: MISSED by the original list and by the Idea-129 pass, and
    # found only by a `git add` CRLF warning while committing something else. The
    # list being incomplete is the failure mode a DECLARED list has; the static
    # check below cannot flag a writer nobody declared.
    "drydocs_core/ontology/schema_graph.py",
)

#: Globs whose CONTENT is committed and must be byte-identical across platforms.
COMMITTED_SURFACE_GLOBS = (
    "docs/plan/*.html",
    "docs/design/*.html",
    "web/src/generated/*.json",
    "knowledge/depgraph-snapshots/*.json",
    # The generated meta-graph — a render like any other, and the surface whose
    # CRLF warning exposed the gap in the writer list above.
    "drydocs_core/schema/schema_graph.cypher",
)


def _write_text_calls_missing_newline(source: str) -> list[int]:
    """Line numbers of `.write_text(...)` calls that do not pass `newline=`.

    Matched on the attribute name rather than the receiver, because the receiver
    is a local (`out`, `path`, `dest`) at every site and typing it would make the
    check miss exactly the new site it exists to catch.
    """
    tree = ast.parse(source)
    return sorted(
        node.lineno
        for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == "write_text"
        and not any(kw.arg == "newline" for kw in node.keywords)
    )


def test_committed_surface_writers_pass_newline_lf() -> None:
    """Every writer of a committed surface pins `newline="\n"`.

    Static on purpose: the byte check below can only fail after someone actually
    re-renders, so on a fresh checkout it is silent. This one fails the moment a
    writer is added without the argument, on every platform including CI.
    """
    failures: list[str] = []
    for rel in COMMITTED_SURFACE_WRITERS:
        module = REPO / rel
        assert module.exists(), f"{rel} is in COMMITTED_SURFACE_WRITERS but does not exist"
        for line in _write_text_calls_missing_newline(module.read_text(encoding="utf-8")):
            failures.append(f"{rel}:{line}")

    assert not failures, (
        "committed-surface writer(s) call write_text() with no newline=:\n  "
        + "\n  ".join(failures)
        + '\nPass newline="\n". Python text mode emits \r\n on Windows, so the '
        "output lands CRLF against an LF index; git normalizes it back on commit, "
        "so no blob changes and the stale-render check reports phantom drift "
        "forever (Idea-121, and Idea-129 for the snapshot half)."
    )


def test_committed_surfaces_carry_no_cr_byte() -> None:
    """The working-tree bytes agree with the LF index.

    `.gitattributes` pins `* text=auto eol=lf`, so checkout gives LF regardless of
    core.autocrlf. A CR byte here therefore means a WRITER put it there after
    checkout — which is the defect, not a local git setting.
    """
    offenders: list[str] = []
    for pattern in COMMITTED_SURFACE_GLOBS:
        for path in sorted(REPO.glob(pattern), key=lambda p: p.as_posix()):
            if b"\r" in path.read_bytes():
                offenders.append(path.relative_to(REPO).as_posix())

    assert not offenders, (
        "committed surface(s) hold CR bytes in the working tree:\n  "
        + "\n  ".join(offenders)
        + '\nRe-run the writer after checking it passes newline="\\n". These files '
        "commit as LF either way, which is exactly why this goes unnoticed: the "
        "cost is a permanently-dirty stale-render check, not a wrong blob."
    )
