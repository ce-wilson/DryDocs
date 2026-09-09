"""A test that crosses may not pin a path that does not (PORT3).

The defect, twice in one week: a producer test asserted that a `docs/port/` file was
in the tree (test_markdown_fences.py, fixed at 20449d47) and a second keyed a
currency map on `docs/port/port-prompt.md` with no skip (test_runbook_currency.py,
fixed at 84ef2d97). Both tests cross to every consumer through `PORT-MANIFEST.yaml`;
`docs/port/**` is `never-port`. So by construction both failed on every consumer tree,
and nothing checked the join between a test's disposition and the dispositions of the
paths it cites. This is that check.

What it reads (J37/J66): the manifest through its importable loader, and each test's
CODE through the syntax tree - whole string constants that look like repo paths,
``/``-chains rooted at a module-level repo-root binding, skip CALLS, and the argument
list of a ``git ls-files`` call. Never the prose.

What it asks of a citation whose path classifies `never-port`:

- a GITIGNORED zone (`drydocs/data/**`, `internal-local/**`) is the J8/CORE4 skip
  policy's domain: the test must CALL a skip guard, the same call
  tests/unit/test_skip_guard_policy.py reads;
- a TRACKED zone (`docs/port/**`, `docs/company-prompts/**`, ...) exists on the producer
  and not on a consumer, so the test must probe TRACKED CONTENT - `git ls-files` - and
  skip on its absence. A directory probe is not one: a consumer's `docs/port/` exists,
  holding one gitignored file, so `is_dir()` answered "present" for a zone that never
  crossed (af9194c4). The guard reads the probe's argument list, never the directory;
- a FIXTURE literal - a synthetic doc, a manifest row string, a tmp_path write - is
  data, not a read of this tree; the test names it in ``FIXTURE_LITERALS`` with the
  reason, per path. Glob strings (`docs/port/**`) are manifest patterns and are never
  citations.

A test that is itself `never-port` may cite anything: it never crosses either.
"""

from __future__ import annotations

import ast
import re
import subprocess
from collections.abc import Callable
from pathlib import Path

from drydocs.port.dispositions import classify, load_manifest
from drydocs_core.repo_paths import repo_root
from tests.source_scan import called_names

REPO_ROOT = repo_root(Path(__file__).resolve().parents[2])
TESTS_DIR = Path(__file__).resolve().parent
MANIFEST = load_manifest(REPO_ROOT / "PORT-MANIFEST.yaml")

NEVER_PORT = "never-port"

#: The skip CALLS the J8/CORE4 policy recognises - shared with test_skip_guard_policy.
GUARD_CALLS = frozenset({"skip", "importorskip", "skipif"})

#: The subcommand a tracked-content probe runs. `git ls-files -- <zone>` is the one
#: question that separates "the zone crossed" from "a directory of that name exists".
#: Read as an argument list, not as a literal: `git ls-files "*.md"` ENUMERATES a tree
#: and answers nothing about a zone (the pre-fix test_markdown_fences.py ran exactly
#: that and would have passed a literal check).
TRACKED_PROBE = "ls-files"

_GLOB_CHARS = set("*?[")
#: Two or more `/`-joined segments, or one dotted file name (`PORT-MANIFEST.company.yaml`).
_PATH_RE = re.compile(r"^\.?[\w.@-]+(?:/[\w.@-]+)+/?$|^[\w-]+\.[\w.-]+$")

#: Never-port literals that are DATA in the test that carries them - never a read of
#: this tree - keyed by test file, then by the path as the syntax tree resolves it.
#: The reason is the exemption: an entry a reader cannot check is a silenced failure.
FIXTURE_LITERALS: dict[str, dict[str, str]] = {
    "test_port_completeness.py": {
        "docs/port/never.md": "synthetic ls-tree listing; classified, never opened",
        "docs/port/port-prompt.md": "synthetic ls-tree listing; classified, never opened",
        "docs/port/x.md": "synthetic ls-tree listing; classified, never opened",
    },
    "test_port_dispositions.py": {
        "docs/port/port-prompt.md": "input to classify(); the row match is the subject",
    },
    "test_port_drops.py": {
        "PORT-MANIFEST.company.yaml": "written under tmp_path; the overlay slot under test",
        "PORT-MANIFEST.producer.yaml": "written under tmp_path; the overlay slot under test",
    },
    "test_port_manifest.py": {
        "tests/unit/test_lane_handoff.py": (
            "the skill/test pairing under test; the path is compared against manifest "
            "rows, never opened"
        ),
    },
    "test_port_preflight.py": {
        "docs/port/port-prompt.md": (
            "a key in a synthetic doc map with an injected exists=; never opened"
        ),
    },
    "test_port_reconcile_guards.py": {
        "PORT-MANIFEST.company.yaml": "overlay fixture written under tmp_path",
        "PORT-MANIFEST.producer.yaml": "overlay fixture written under tmp_path",
        "knowledge/depgraph-snapshots/drydocs-20260727.json": (
            "a path classified through the manifest to prove the glob row matches it"
        ),
    },
    "test_skip_guard_policy.py": {
        "internal-local/archive/x.csv": "the policy's own fixture string; never opened",
        "drydocs/data/": "the policy's _LOCAL_TREES prefix; a filter, never opened",
        "drydocs/data/samples/controlm_variables__sample.csv": (
            "the policy's own fixture string - the port failure shape it must still flag"
        ),
    },
    "test_runbook_currency.py": {
        "docs/company-prompts/port-fix-a14a8028-company-prompt.md": (
            "a HISTORICAL_PATHS key: a statement about the past, exempted from the "
            "existence check by its own table"
        ),
        "docs/port/port-dispositions.md": (
            "a GENERATED_PATHS key: regenerated per apply and gitignored, exempted from "
            "the existence check by its own table"
        ),
    },
}


# ---- reading the citations out of the syntax tree -----------------------------------


def _const_str(node: ast.AST) -> str | None:
    return node.value if isinstance(node, ast.Constant) and isinstance(node.value, str) else None


def _div_operands(node: ast.AST) -> list[ast.AST] | None:
    """Flatten ``a / b / c`` to ``[a, b, c]``; None if this is not a division chain."""
    if not isinstance(node, ast.BinOp) or not isinstance(node.op, ast.Div):
        return None
    left = _div_operands(node.left) or [node.left]
    return [*left, node.right]


def _is_root_expr(node: ast.AST) -> bool:
    """A spelling of the repo root: an expression anchored on ``__file__``
    (`Path(__file__).resolve().parents[2]`) or a call to ``repo_root``. A bare Name is
    resolved by the caller against the module's own root bindings; a constant never
    is; any other call (`re.compile(...)`) binds no root."""
    for sub in ast.walk(node):
        if isinstance(sub, ast.Name) and sub.id == "__file__":
            return True
        if (
            isinstance(sub, ast.Call)
            and isinstance(sub.func, ast.Name)
            and sub.func.id == "repo_root"
        ):
            return True
    return False


def _root_bindings(tree: ast.Module) -> dict[str, list[str]]:
    """Module-level ``NAME = <root> / "a" / "b"`` bindings, as their segments after the
    root. ``REPO = repo_root(...)`` binds to ``[]``; ``DOCS = REPO / "docs"`` to
    ``["docs"]``. Resolved in order, so a binding may build on an earlier one."""
    roots: dict[str, list[str]] = {}
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        operands = _div_operands(node.value) or [node.value]
        head, *tail = operands
        if isinstance(head, ast.Name) and head.id in roots:
            base = roots[head.id]
        elif _is_root_expr(head):
            base = []
        else:
            continue
        segments = [_const_str(o) for o in tail]
        if any(s is None for s in segments):
            continue
        roots[target.id] = [*base, *(s for s in segments if s)]
    return roots


def _looks_like_path(literal: str) -> bool:
    return bool(_PATH_RE.match(literal)) and not _GLOB_CHARS.intersection(literal)


def citations(source: str) -> set[str]:
    """Every repo-relative path ``source`` cites in CODE: whole string constants that
    look like paths (glob patterns and prose excluded), and ``/``-chains rooted at a
    repo-root spelling or a module-level binding of one. A chain rooted at a
    function-local name (``tmp_path / "docs"``) is not a read of this tree."""
    tree = ast.parse(source)
    roots = _root_bindings(tree)
    found: set[str] = set()
    docstrings = {
        id(stmt.value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        for stmt in node.body[:1]
        if isinstance(stmt, ast.Expr) and _const_str(stmt.value) is not None
    }

    def visit(node: ast.AST) -> None:
        operands = _div_operands(node)
        if operands is not None:
            # the OUTERMOST chain is the citation; its inner chains and constant
            # operands are its parts, not further citations
            head, *tail = operands
            if isinstance(head, ast.Name) and head.id in roots:
                base: list[str] | None = roots[head.id]
            elif _is_root_expr(head):
                base = []
            else:
                base = None
            segments = [_const_str(o) for o in tail]
            if base is not None and segments and all(s is not None for s in segments):
                found.add("/".join([*base, *segments]))
            for operand in operands:
                if _const_str(operand) is None:
                    visit(operand)
            return
        literal = _const_str(node)
        if literal is not None:
            if id(node) not in docstrings and _looks_like_path(literal):
                found.add(literal.lstrip("./"))
            return
        for child in ast.iter_child_nodes(node):
            visit(child)

    visit(tree)
    return found


# ---- the mechanism a citation must carry ----------------------------------------------


def _git_ignored(path: str) -> bool:
    """Is ``path`` in a gitignored ZONE here? The zone kind decides which mechanism
    applies. ``--no-index`` asks about the rules, not the index: fourteen bundled samples
    under `drydocs/data/` are force-tracked (grandfathered, per the port ledger), and a
    tracked file is still a file in a zone the port never carries."""
    result = subprocess.run(
        ["git", "check-ignore", "-q", "--no-index", "--", path],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.returncode == 0


def _root_commit() -> str:
    return subprocess.run(
        ["git", "rev-list", "--max-parents=0", "HEAD"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=True,
    ).stdout.split()[0]


def _git_seeded(path: str) -> bool:
    """Was ``path`` in this history's root commit? A never-port file that was in the
    seed is on every consumer cut from it - the port never carries a CHANGE to it,
    but the file is there. The bundled demo samples from the 2026-07-20 initial import
    are the case (tests/unit/test_bundled_demo_interlock.py reads three of them and
    fails, by CORE4, rather than skips); a sample added later is not seeded and its
    test skips (controlm_hosts__sample.csv, absent company-side per the port ledger)."""
    result = subprocess.run(
        ["git", "cat-file", "-e", f"{_root_commit()}:{path}"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return result.returncode == 0


def _is_tracked_content_probe(tree: ast.AST) -> bool:
    """Does the code run ``git ls-files`` over a SPECIFIC pathspec? The pathspec is what
    makes it a probe: a name (``zone``) or a glob-free constant asks "does this zone
    have tracked content"; a glob (``"*.md"``) or no pathspec at all lists the tree."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.List | ast.Tuple):
            continue
        words = [_const_str(e) for e in node.elts]
        if "git" not in words or TRACKED_PROBE not in words:
            continue
        after = node.elts[words.index(TRACKED_PROBE) + 1 :]
        for elt in after:
            word = _const_str(elt)
            if word is None:
                return True  # a name or expression: a path the test computed
            if word.startswith("-"):
                continue  # a flag, `--` included
            if word and not _GLOB_CHARS.intersection(word):
                return True
    return False


def findings(
    source: str,
    *,
    manifest: dict = MANIFEST,
    fixtures: dict[str, str] | None = None,
    is_ignored: Callable[[str], bool] = _git_ignored,
    is_seeded: Callable[[str], bool] = _git_seeded,
) -> list[str]:
    """The never-port citations in ``source`` that carry no allowance. Empty is clean.

    The allowances, in order: a FIXTURE literal; a SEEDED path (in the root commit, so
    on every consumer); a GITIGNORED-zone path with a skip call; a TRACKED-zone path
    with a tracked-content probe."""
    fixtures = fixtures or {}
    cited = sorted(p for p in citations(source) if classify(p, manifest)[0] == NEVER_PORT)
    if not cited:
        return []
    has_skip = bool(GUARD_CALLS & called_names(source))
    has_probe = _is_tracked_content_probe(ast.parse(source))
    out: list[str] = []
    for path in cited:
        if path in fixtures or is_seeded(path):
            continue
        if is_ignored(path):
            if not has_skip:
                out.append(
                    f"{path}: a gitignored never-port path and no skip guard is called "
                    f"({sorted(GUARD_CALLS)}; the J8/CORE4 policy)"
                )
        elif not has_probe:
            out.append(
                f"{path}: a tracked never-port path and no tracked-content probe "
                f"(`git {TRACKED_PROBE} -- <zone>`) - a consumer tree has no such content; "
                "a directory probe (is_dir()/exists()) is not one, the directory can exist "
                "empty or holding only gitignored state (af9194c4)"
            )
    return out


# ---- the guard ------------------------------------------------------------------------


def _crossing_tests() -> list[Path]:
    """Every unit test the manifest lets cross - anything but never-port. This file
    quotes the shapes it polices and is excluded by name, as test_skip_guard_policy is."""
    out = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        if path.name == Path(__file__).name:
            continue
        rel = path.relative_to(REPO_ROOT).as_posix()
        if classify(rel, MANIFEST)[0] != NEVER_PORT:
            out.append(path)
    return out


def test_no_crossing_test_pins_a_never_port_path_without_an_allowance() -> None:
    offenders: list[str] = []
    for path in _crossing_tests():
        source = path.read_text(encoding="utf-8")
        for line in findings(source, fixtures=FIXTURE_LITERALS.get(path.name)):
            offenders.append(f"{path.name}: {line}")
    assert not offenders, (
        "Tests that cross to every consumer (PORT-MANIFEST disposition other than "
        "never-port) and cite a never-port path with no way to skip its absence. On a "
        "consumer tree these fail by construction. Fix one of three ways:\n  "
        + "\n  ".join(offenders)
        + "\n\nTRACKED zone (docs/port/**, docs/company-prompts/**, ...): probe tracked "
        "content with `git ls-files -- <zone>` and skip the entry when it is empty "
        "(test_runbook_currency.NEVER_PORT_ZONE_OF is the shape). GITIGNORED zone "
        "(drydocs/data/**, internal-local/**): call pytest.skip/importorskip/skipif. "
        "FIXTURE literal (data, never a read of this tree): add it to FIXTURE_LITERALS "
        "here with the reason."
    )


def test_every_fixture_literal_is_still_cited_by_its_test() -> None:
    """A stale exemption is a silenced failure in waiting: each entry names a test that
    exists, crosses, and still cites that path."""
    stale: list[str] = []
    for name, paths in FIXTURE_LITERALS.items():
        path = TESTS_DIR / name
        if not path.is_file():
            stale.append(f"{name}: no such test")
            continue
        cited = citations(path.read_text(encoding="utf-8"))
        for p, reason in paths.items():
            assert reason.strip(), f"{name}: {p!r} carries no reason"
            if p not in cited:
                stale.append(f"{name}: {p!r} is no longer cited - retire the entry")
    assert not stale, "\n".join(stale)


# ---- the incident shapes are the fixtures ---------------------------------------------

_FENCES_PRE_FIX = (
    "from pathlib import Path\n"
    "import subprocess\n"
    'DOCS_ROOT = Path(__file__).resolve().parents[2] / "docs"\n'
    "def test_x():\n"
    "    found = set(DOCS_ROOT.rglob('*.md'))\n"
    '    assert (DOCS_ROOT / "port" / "port-prompt.md") in found\n'
    "def test_y():\n"
    '    subprocess.run(["git", "ls-files", "*.md"], cwd=DOCS_ROOT.parent)\n'
)
_FENCES_POST_FIX = _FENCES_PRE_FIX.replace(
    '"port" / "port-prompt.md"', '"style" / "us-business-english.md"'
)

_RUNBOOK_PRE_FIX = (
    "EXTRA_DOCS = {\n"
    '    "docs/port/port-prompt.md": "the port ledger",\n'
    '    "docs/style/us-business-english.md": "the style guide",\n'
    "}\n"
    "def test_x():\n"
    "    for rel in EXTRA_DOCS:\n"
    "        assert (REPO_ROOT / rel).exists()\n"
)
_RUNBOOK_POST_FIX = _RUNBOOK_PRE_FIX + (
    "import subprocess\n"
    'NEVER_PORT_ZONE_OF = {"docs/port/port-prompt.md": "docs/port"}\n'
    "def _zone_has_tracked_content(zone):\n"
    '    r = subprocess.run(["git", "ls-files", "--", zone], capture_output=True)\n'
    "    return bool(r.stdout.strip())\n"
)
_RUNBOOK_DIR_PROBE = _RUNBOOK_PRE_FIX + (
    'NEVER_PORT_ZONE_OF = {"docs/port/port-prompt.md": "docs/port"}\n'
    "def _zone_present(zone):\n"
    "    return (REPO_ROOT / zone).is_dir()\n"
)


def _ignored_zone(path: str) -> bool:
    """The injected zone rule for the fixtures: samples are ignored, docs/port is tracked."""
    return path.startswith("drydocs/data/")


def _never_seeded(path: str) -> bool:
    return False


def test_the_fences_canary_fails_pre_fix_and_passes_post_fix() -> None:
    """20449d47: a root-anchored `/`-chain into docs/port, asserted present - in a file
    that also ran `git ls-files "*.md"` to ENUMERATE, which is not a zone probe."""
    assert "docs/port/port-prompt.md" in citations(_FENCES_PRE_FIX)
    (line,) = findings(_FENCES_PRE_FIX, is_ignored=_ignored_zone, is_seeded=_never_seeded)
    assert line.startswith("docs/port/port-prompt.md: a tracked never-port path")
    assert findings(_FENCES_POST_FIX, is_ignored=_ignored_zone, is_seeded=_never_seeded) == []


def test_the_runbook_map_fails_without_a_probe_and_passes_with_ls_files() -> None:
    """84ef2d97: a map keyed on the path with no skip; the fix probes tracked content."""
    (line,) = findings(_RUNBOOK_PRE_FIX, is_ignored=_ignored_zone, is_seeded=_never_seeded)
    assert "docs/port/port-prompt.md" in line and "ls-files" in line
    assert findings(_RUNBOOK_POST_FIX, is_ignored=_ignored_zone, is_seeded=_never_seeded) == []


def test_the_probe_is_read_as_an_argument_list_not_a_literal() -> None:
    tree = ast.parse
    assert _is_tracked_content_probe(tree('subprocess.run(["git", "ls-files", "--", zone])'))
    assert _is_tracked_content_probe(tree('subprocess.run(["git", "ls-files", "docs/port"])'))
    assert not _is_tracked_content_probe(tree('subprocess.run(["git", "ls-files", "*.md"])'))
    assert not _is_tracked_content_probe(tree('subprocess.run(["git", "ls-files"])'))
    assert not _is_tracked_content_probe(tree('X = "ls-files"'))


def test_a_directory_probe_is_not_a_tracked_content_probe() -> None:
    """af9194c4: `is_dir()` said "present" for a consumer's docs/port/ holding one
    gitignored file. The guard reads the probe's literal, so this shape still fails."""
    (line,) = findings(_RUNBOOK_DIR_PROBE, is_ignored=_ignored_zone, is_seeded=_never_seeded)
    assert "is_dir()" in line


def test_a_gitignored_zone_needs_a_skip_call_not_a_probe() -> None:
    src = (
        "REPO = repo_root(Path(__file__).resolve().parents[2])\n"
        'SAMPLE = REPO / "drydocs" / "data" / "samples" / "x.csv"\n'
    )
    (line,) = findings(src, is_ignored=_ignored_zone, is_seeded=_never_seeded)
    assert "gitignored never-port path and no skip guard" in line
    assert (
        findings(src + 'pytest.skip("absent")\n', is_ignored=_ignored_zone, is_seeded=_never_seeded)
        == []
    )


def test_a_fixture_allowance_covers_exactly_its_path() -> None:
    src = 'rows = ["docs/port/port-prompt.md", "docs/port/other.md"]\n'
    allowed = {"docs/port/port-prompt.md": "a synthetic listing"}
    (line,) = findings(src, fixtures=allowed, is_ignored=_ignored_zone, is_seeded=_never_seeded)
    assert line.startswith("docs/port/other.md")


def test_glob_patterns_prose_docstrings_and_local_chains_are_not_citations() -> None:
    src = (
        '"""The docs/port/port-prompt.md ledger."""\n'
        'PATTERN = "docs/port/**"\n'
        'NOTE = "see docs/port/port-prompt.md for the ledger"\n'
        "def test_x(tmp_path):\n"
        '    (tmp_path / "docs" / "port").mkdir(parents=True)\n'
    )
    assert citations(src) == set()


def test_a_seeded_path_needs_no_mechanism_and_a_later_one_does() -> None:
    src = (
        "REPO = repo_root(Path(__file__).resolve().parents[2])\n"
        'A = REPO / "drydocs" / "data" / "samples" / "seeded.csv"\n'
        'B = REPO / "drydocs" / "data" / "samples" / "later.csv"\n'
    )
    (line,) = findings(src, is_ignored=_ignored_zone, is_seeded=lambda p: p.endswith("seeded.csv"))
    assert line.startswith("drydocs/data/samples/later.csv")


def test_the_live_seed_holds_the_demo_samples_and_not_the_later_host_sample() -> None:
    """The mechanism against this history: the samples the demo interlock reads without
    a skip are in the root commit; the hosts sample (2026-07-27) is not, and its test
    skips."""
    assert _git_seeded("drydocs/data/samples/controlm_jobs__sample.csv")
    assert not _git_seeded("drydocs/data/samples/controlm_hosts__sample.csv")


def test_the_guard_reads_a_tracked_zone_as_tracked_here() -> None:
    """The live half of the mechanism split: on the producer, docs/port is tracked and
    not ignored; the samples zone is ignored. A consumer is not asserted about."""
    assert not _git_ignored("docs/port/port-prompt.md")
    assert _git_ignored("internal-local/anything.md")
    # force-tracked, and still in the ignored zone: the skip call is the mechanism
    assert _git_ignored("drydocs/data/samples/controlm_jobs__sample.csv")
