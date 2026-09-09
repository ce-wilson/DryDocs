"""J8 — skip-guard policy: tests reading assets ABSENT FROM A FRESH CLONE must SKIP, not fail.

The exact failure a prior port hit: a test referenced a local-only file under the
gitignored ``drydocs/data/`` tree, the consumer cloned without it, and the suite died
with FileNotFoundError instead of a skip (the guard had been lost in a merge). This
policy test makes that loss loud.

WHAT THE POLICY ASKS, AND WHAT IT USED TO ASK (CORE4, 2026-09-07). It used to ask
"does this file mention a path under ``drydocs/data/`` or ``internal-local/``?" and
call any such path a gitignored asset. That is the wrong question, because
``drydocs/data/`` is gitignored WHOLESALE while fourteen sample files under it are
FORCE-TRACKED — so a test reading a tracked sample was flagged exactly like a test
reading a machine-local extract. The cost was not a false alarm that someone argued
with; it was a real one that got *satisfied*: a skip guard written to quiet the
policy, standing where an assertion belonged, silently disabling a test's real
assertions if the file ever went missing (Z8, and see ``test_bundled_demo_interlock``).

So the question is now the one that actually matters — **is this path in a fresh
clone?** — and it is put to GIT rather than to the path's prefix:

* **tracked** → present in every clone. No guard needed, and none should be written:
  if a tracked file is missing the clone is broken, and the test should say so loudly.
* **untracked** → absent on a fresh clone. A guard is required. This is the port
  failure, and it is still caught exactly as before: ``controlm_variables__sample.csv``
  under the same ``drydocs/data/samples/`` prefix is untracked, and the two
  ``test_variable_*`` files that read it are held to their guards by this rule.
* **unresolvable** → the file builds a path this checker cannot name (a chain ending
  in an imported constant, say). A guard is required, because a policy that cannot
  name the file cannot clear it. Third outcome, deliberately: folding it into
  "tracked" would quietly excuse the one shape the checker is blindest to.

HOW A REFERENCE IS READ. Through ``ast``, not a regex over the source text, so a path
mentioned in a comment is invisible (it is not a read) and a multi-line ``/`` chain is
seen whole. Two shapes resolve:

* a lone string constant containing ``drydocs/data/`` or ``internal-local/``; and
* a ``Path`` division chain, anchored at the ``"drydocs" / "data"`` (or bare
  ``"data" / "samples"``) segments, with everything before the anchor ignored — it is
  some spelling of "the repo root" and does not change which file is named.

The GUARD MARKER is read the same way — as a CALL to ``skip`` / ``importorskip`` /
``skipif``, not as those words appearing in the text. See ``_GUARD_CALLS``: the regex
this replaced matched the prose of the very file it had just cleared (J66).

ONE module-level name hop is followed, so ``SAMPLES = REPO / "drydocs" / "data" /
"samples"`` followed by ``SAMPLES / "x.csv"`` resolves. Imports are not followed and
neither is anything else: the moment a chain reaches a name this module cannot see, the
reference is unresolvable and its file keeps its guard. That boundary is the point —
real dataflow analysis is how a policy test becomes a thing nobody can reason about.

Carve-outs, both older than this rewrite and both kept:

* Literals containing glob characters (``drydocs/data/**``) are manifest/pattern rows,
  not filesystem reads — and no glob is ever a path git can be asked about.
* A quoted literal containing whitespace is PROSE — a sentence that mentions a tree,
  not a path this file opens (added 2026-08-07 after ``test_runbook_currency.py`` was
  flagged for a HISTORICAL_PATHS explanation; a skip guard there would have been a lie).
  This repo's paths never contain spaces, so the port-failure shape is untouched.

The guard requirement stays FILE-level: one guard marker per referencing file. That is
the granularity the port failure had.
"""

from __future__ import annotations

import ast
import subprocess
from pathlib import Path

from tests.source_scan import called_names

TESTS_DIR = Path(__file__).resolve().parent
REPO = TESTS_DIR.parents[1]

#: What a guard IS, as calls rather than as text (J66). It was
#: ``re.compile(r"skipif|importorskip|pytest\.skip")`` over raw source until
#: CORE4, and the rewrite tripped it immediately: this module's own prose now
#: explains why a file no longer needs a guard, the words "pytest.skip" appear in
#: that explanation, and the regex read the explanation as the guard. That is
#: J66's failure exactly — a guard that fails on the sentence describing it —
#: caught here by the very edit it would have punished.
_GUARD_CALLS = frozenset({"skip", "importorskip", "skipif"})
#: The two trees whose contents are not guaranteed to be in a clone.
_LOCAL_TREES = ("drydocs/data/", "internal-local/")
_GLOB_CHARS = set("*?[")


def _tracked() -> frozenset[str]:
    """Every path git tracks, forward-slashed — i.e. exactly what a fresh clone has.

    Same idiom as test_publish_boundary_values.py::_tracked_files. On failure this
    returns EMPTY, which makes every reference untracked and every referencing file
    an offender: the conservative direction, since the alternative is a policy that
    passes because it could not ask.
    """
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO,
            capture_output=True,
            encoding="utf-8",
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        return frozenset()
    return frozenset(line.strip() for line in out.splitlines() if line.strip())


TRACKED = _tracked()


def _normalize(path: str) -> str:
    return path.replace("\\", "/").lstrip("./")


def _in_local_tree(path: str) -> bool:
    return any(marker in path for marker in _LOCAL_TREES)


def _is_prose(literal: str) -> bool:
    """A quoted literal that MENTIONS a tree in a sentence rather than naming a path.

    Whitespace is the discriminator because this repo's paths never contain spaces.
    """
    return any(ch.isspace() for ch in literal)


def _is_tracked(path: str) -> bool:
    """True if a fresh clone has this path — as a file, or as a directory with
    tracked content under it (a prefix used for filtering is not a read of a file,
    but the directory is still there)."""
    path = _normalize(path)
    if path in TRACKED:
        return True
    prefix = path if path.endswith("/") else path + "/"
    return any(t.startswith(prefix) for t in TRACKED)


# ---- resolving references out of the syntax tree -------------------------------


def _div_operands(node: ast.AST) -> list[ast.AST] | None:
    """Flatten ``a / b / c`` to ``[a, b, c]``; None if this is not a division chain."""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
        return None
    left = _div_operands(node.left) or [node.left]
    return [*left, node.right]


def _anchor(segments: list[str | None]) -> list[str] | None:
    """The path segments from the local-tree anchor onward, or None if not anchored.

    ``None`` inside ``segments`` marks an operand that is not a string constant.
    Anything BEFORE the anchor is some spelling of the repo root and is dropped;
    anything unresolvable AT or AFTER it makes the whole reference unresolvable,
    which the caller sees as an empty list.
    """
    for i, seg in enumerate(segments):
        rest = segments[i:]
        if seg == "drydocs" and len(rest) > 1 and rest[1] == "data":
            head: list[str] = []
        elif seg == "data" and len(rest) > 1 and rest[1] == "samples":
            head = ["drydocs"]  # the bare `"data" / "samples"` spelling
        elif seg == "internal-local":
            head = []
        else:
            continue
        out = list(head)
        for part in rest:
            if part is None:
                return []  # anchored, but the tail cannot be named
            out.append(part)
        return out
    return None


def _module_dirs(tree: ast.Module) -> dict[str, list[str]]:
    """Module-level ``NAME = <chain>`` bindings that resolve into a local tree.

    The one hop this checker follows, and the only one: it is what turns
    ``SAMPLES = REPO / "drydocs" / "data" / "samples"`` plus ``SAMPLES / "x.csv"``
    into a path git can be asked about.
    """
    out: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        operands = _div_operands(node.value)
        if not isinstance(target, ast.Name) or operands is None:
            continue
        segments = _anchor([_const_str(o) for o in operands])
        if segments:
            out[target.id] = segments
    return out


def _const_str(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def references(source: str) -> tuple[list[str], list[str]]:
    """``(resolved_paths, unresolvable_descriptions)`` for one module's source.

    Only references INTO a local tree are returned; everything else is not this
    policy's business.
    """
    tree = ast.parse(source)
    dirs = _module_dirs(tree)
    resolved: list[str] = []
    unresolvable: list[str] = []

    for node in ast.walk(tree):
        operands = _div_operands(node)
        if operands is not None:
            segments = [_const_str(o) for o in operands]
            # a chain rooted at a module-level directory name: substitute it in
            first = operands[0]
            if isinstance(first, ast.Name) and first.id in dirs:
                segments = [*dirs[first.id], *segments[1:]]
                anchored: list[str] | None = (
                    [] if any(s is None for s in segments) else [s for s in segments if s]
                )
            else:
                anchored = _anchor(segments)
            if anchored is None:
                continue  # a division that has nothing to do with these trees
            if not anchored:
                unresolvable.append(ast.unparse(node))
            else:
                resolved.append("/".join(anchored))
            continue

        literal = _const_str(node)
        if literal is None or not _in_local_tree(_normalize(literal)):
            continue
        if _GLOB_CHARS.intersection(literal):
            continue  # manifest/pattern row, not a filesystem read
        if _is_prose(literal):
            continue  # a sentence that MENTIONS the tree, not a path opened here
        resolved.append(_normalize(literal))

    return resolved, unresolvable


def needs_guard(source: str) -> tuple[list[str], list[str]]:
    """``(untracked, unresolvable)`` — the two reasons a file must carry a guard."""
    resolved, unresolvable = references(source)
    return [p for p in resolved if not _is_tracked(p)], unresolvable


def _has_guard(source: str) -> bool:
    """Does this module CALL a skip guard — `pytest.skip`, `importorskip`, or a
    `skipif` marker? Read as calls, never as text (J66): see `_GUARD_CALLS`."""
    return bool(_GUARD_CALLS & called_names(source))


# ---- the policy ----------------------------------------------------------------

#: Files that QUOTE the local-tree paths they police - as fixture strings and
#: exemption keys, never as reads - and so cannot be read by this policy as tests
#: that open them. This file, and the PORT3 never-port citation guard that applies
#: the same reading across the manifest's every never-port row.
_QUOTES_THE_PATTERNS = frozenset({Path(__file__).name, "test_never_port_citations.py"})


def test_gitignored_asset_references_carry_a_skip_guard() -> None:
    untracked_offenders: list[str] = []
    unresolvable_offenders: list[str] = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        if path.name in _QUOTES_THE_PATTERNS:
            continue
        text = path.read_text(encoding="utf-8")
        if _has_guard(text):
            continue
        untracked, unresolvable = needs_guard(text)
        if untracked:
            untracked_offenders.append(f"{path.name}: {sorted(set(untracked))}")
        if unresolvable:
            unresolvable_offenders.append(f"{path.name}: {sorted(set(unresolvable))}")

    assert not (untracked_offenders or unresolvable_offenders), (
        "Test files that must carry a skipif/importorskip/pytest.skip guard and do "
        "not. The two cases are different problems with different fixes:\n\n"
        "UNTRACKED — the path is real and git does not track it, so a fresh clone "
        "does not have it and this test FAILS there instead of skipping. Add the "
        f"guard:\n  {chr(10) + '  '.join(untracked_offenders) or '(none)'}\n\n"
        "UNRESOLVABLE — the path is built from something this checker cannot name "
        "(a chain ending in an imported constant, say), so the policy cannot tell "
        "whether a fresh clone has it. Either name the path so it resolves, or keep "
        f"a guard:\n  {chr(10) + '  '.join(unresolvable_offenders) or '(none)'}\n\n"
        "A path git DOES track needs no guard at all — writing one there disables "
        "the test's real assertions the day the file goes missing (CORE4)."
    )


def test_policy_checker_catches_the_port_failure_shape() -> None:
    """The checker itself. The port failure still flags; a tracked sample does not."""
    # the shape the policy exists for: a real, untracked, machine-local asset
    unguarded = 'sample = Path("drydocs/data/samples/controlm_variables__sample.csv")\n'
    assert needs_guard(unguarded) == (["drydocs/data/samples/controlm_variables__sample.csv"], [])
    assert not _has_guard(unguarded)
    assert _has_guard(unguarded + 'pytest.skip("sample absent")\n')
    assert _has_guard('m = pytest.mark.skipif(cond, reason="x")\n')
    assert _has_guard('mod = pytest.importorskip("google.adk")\n')

    # J66: a guard is a CALL, not a word. A docstring explaining why this file
    # needs no guard mentions `pytest.skip` and must not thereby become guarded —
    # the regex this replaced did exactly that, on this module's own prose.
    explained = unguarded + '"""This used to be a pytest.skip; see CORE4."""\n'
    assert not _has_guard(explained)

    # ... and the same prefix, but a FORCE-TRACKED file: no guard required (CORE4)
    tracked = 'sample = Path("drydocs/data/samples/controlm_jobs__sample.csv")\n'
    assert needs_guard(tracked) == ([], [])

    # a multi-line chain resolves whole, and one module-level name hop is followed
    chained = 'SAMPLE = ROOT / "drydocs" / "data" / "samples" / "controlm_variables__sample.csv"\n'
    assert needs_guard(chained)[0] == ["drydocs/data/samples/controlm_variables__sample.csv"]
    hopped = 'SAMPLES = ROOT / "drydocs" / "data" / "samples"\nF = SAMPLES / "controlm_jobs__sample.csv"\n'
    assert needs_guard(hopped) == ([], [])

    # ... but a chain the checker cannot name is the THIRD outcome, not a pass
    opaque = 'fixture = ROOT / "drydocs" / "data" / "samples" / SOME_IMPORTED_NAME\n'
    untracked, unresolvable = needs_guard(opaque)
    assert untracked == [] and len(unresolvable) == 1

    manifest_row = '{"drydocs/data/**": "never-port"}\n'
    assert needs_guard(manifest_row) == ([], [])

    clean = 'FIXTURE = Path("tests/fixtures/lineage/jobs.csv")\n'
    assert needs_guard(clean) == ([], [])

    # A reason-string that MENTIONS the tree is not a read (the 2026-08-07 carve-out;
    # the real shape came from test_runbook_currency.py's HISTORICAL_PATHS note).
    prose = '"the pack retired to internal-local/archive/company-prompts/ at cleanup"\n'
    assert needs_guard(prose) == ([], [])

    # ...but the carve-out must not swallow the failure the policy exists for: a
    # spaceless path literal is still an offense even inside a prose-heavy file.
    prose_plus_real = prose + 'sample = Path("internal-local/archive/x.csv")\n'
    assert needs_guard(prose_plus_real)[0] == ["internal-local/archive/x.csv"]

    # a path mentioned in a COMMENT is not a read at all — ast never sees it (J66)
    commented = "# reads drydocs/data/samples/controlm_variables__sample.csv one day\nx = 1\n"
    assert needs_guard(commented) == ([], [])


def test_the_tracked_listing_is_real_and_carries_the_force_tracked_samples() -> None:
    """The instrument, checked before the subject (J76): this policy is only as good
    as the listing it asks. `drydocs/data/` is gitignored wholesale, so these two
    facts together ARE the defect CORE4 fixes — same directory, opposite answers."""
    assert "drydocs/data/samples/controlm_jobs__sample.csv" in TRACKED
    assert "drydocs/data/samples/controlm_variables__sample.csv" not in TRACKED
