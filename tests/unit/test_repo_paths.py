"""A render run must write into the checkout the CALLER is in (Idea-109).

WHY THIS EXISTS. On 2026-08-11 two agents working in separate
``.claude/worktrees/`` trees each ran the CLAUDE.md §0 session-end render ritual and
each silently wrote part of its output into the MAIN repo. Both recovered; neither
tree showed anything wrong, which is the point — the worktree stayed clean and main
picked up an uncommitted render nobody in that session had authored.

The mechanism, in one line: ``drydocs`` is installed **editable** (a ``drydocs.pth``
pinned at the main tree), so a module that anchors its default paths on
``Path(__file__)`` names the main tree from anywhere. ``python scripts/render_board.py``
puts ``scripts/`` on ``sys.path[0]`` and never the cwd, so the worktree's own
``drydocs/`` is not shadowed in and the import falls through to that install.

What made it nasty was that it was PARTIAL. ``render_board.py`` invokes five sibling
scripts by bare name — those resolve out of the worktree's ``scripts/`` and anchor on
their own ``__file__``, so they wrote to the worktree correctly — while the three
outputs that route through the installed package went to main. One command, one torn
render, two trees.

So these tests assert the RULE, not a committed artifact: repo-*content* defaults
follow the caller's checkout, and the end-to-end case drives a real second worktree
and asserts the main tree came back untouched. A drift guard could never have caught
this — from the authoring machine the render is correct and the damage is in a
directory the test does not look at.
"""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from drydocs_core.repo_paths import repo_root

REPO = Path(__file__).resolve().parents[2]

#: Modules whose defaults point at repo CONTENT and must therefore follow the caller.
#: Each entry is (import path, constant name) and every constant is asserted to live
#: under the resolved root. Package-internal resources (``drydocs_core/schema/*.cypher``)
#: are deliberately absent: those travel with the package and keep the ``__file__``
#: anchor.
CONTENT_PATH_CONSTANTS: tuple[tuple[str, str], ...] = (
    ("drydocs.plan.plan_board", "DEFAULT_BACKLOG_PATH"),
    ("drydocs.plan.plan_board", "DEFAULT_BOARD_PATH"),
    ("drydocs.docgen.plan_ideas", "DEFAULT_IDEAS_PATH"),
    ("drydocs.docgen.plan_ideas", "DEFAULT_IDEAS_OUT_PATH"),
    ("drydocs.plan.plan_roadmap", "DEFAULT_ROADMAP_PATH"),
    ("drydocs.plan.plan_roadmap", "DEFAULT_ROADMAP_BACKLOG_PATH"),
    ("drydocs.plan.plan_roadmap", "DEFAULT_ROADMAP_OUT_PATH"),
    # ---- the 2026-08-12 residue sweep (Idea-109's own follow-up list) ----
    ("drydocs.review.gate_pages", "DEFAULT_GATE_PROMPTS_DIR"),
    ("drydocs.review.graph_verify", "DEFAULT_GRAPH_TESTS_DIR"),
    ("drydocs.review.review_labels", "DEFAULT_REVIEW_LABELS_PATH"),
    ("drydocs.review.source_mappings", "DEFAULT_SOURCE_MAPPINGS_DIR"),
    ("drydocs.seal_samples", "DEFAULT_CAPTURE_PATH"),
    # A build script's WRITE target, so it follows the caller — unlike
    # drydocs.cli.DEFAULT_SAMPLES_DIR, which names the same directory as a
    # runtime READ default and stays package-internal. Same path, opposite call.
    ("drydocs.seal_samples", "DEFAULT_SAMPLES_DIR"),
    ("drydocs.port.port_preflight", "PORT_PROMPT_PATH"),
    # S8 (2026-08-21): the docs verbs and their content defaults moved out of the root
    ("drydocs.cli_docs", "DOC_REGISTRY_PATH"),
    ("drydocs.cli_docs", "SOFTWARE_REGISTRY_PATH"),
    ("drydocs.cli_docs", "PLATFORMS_PATH"),
    ("drydocs.cli_docs", "SOURCE_REGISTRY_PATH"),
    ("drydocs.loaders.bmc_docs", "DEFAULT_CORPUS_DIR"),
    ("drydocs.loaders.doc_traceability", "DEFAULT_DESIGN_DIR"),
    ("drydocs.loaders.essential_graphrag", "DEFAULT_PDF"),
    ("drydocs.loaders.batch_port_orchestrator", "DEFAULT_APPS_PATH"),
    ("drydocs.loaders.batch_port_orchestrator", "DEFAULT_PLATFORMS_PATH"),
    ("drydocs.loaders.code_snapshot", "DEFAULT_SNAPSHOT_DIR"),
    ("drydocs.loaders.folder_attribution", "PLATFORM_CODES_PATH"),
    ("drydocs.loaders.software_registry", "DEFAULT_REGISTRY_PATH"),
    ("drydocs_core.precedence", "DEFAULT_PRECEDENCE_PATH"),
    ("drydocs_core.source_registry", "DEFAULT_REGISTRY_PATH"),
    ("drydocs_core.source_registry", "DEFAULT_DOC_REGISTRY_PATH"),
    ("drydocs_core.source_registry", "DEFAULT_OVERLAY_PATH"),
    ("drydocs_core.manual_mappings", "DEFAULT_MANIFEST_PATH"),
    ("drydocs_core.mapping_store", "DEFAULT_DB_PATH"),
    ("drydocs_core.mapping_store", "ONTOLOGY_MAP_PATH"),
    ("drydocs_core.mapping_store", "SEAL_CONTACT_OVERRIDES_PATH"),
    ("drydocs_core.mapping_store", "APP_CODE_MAPPINGS_PATH"),
    ("drydocs_core.orchestration.crosswalk", "DEFAULT_CROSSWALK_DIR"),
    ("drydocs_core.orchestration.shell", "DEFAULT_LAUNCHER_REGISTRY_PATH"),
    # NOT on Idea-109's list, found by the sweep — same defect, same install.
    ("drydocs_docmeta.registry", "DEFAULT_LEDGER_PATH"),
    ("drydocs_docmeta.policy", "DEFAULT_POLICY_PATH"),
    ("drydocs_api.intake", "_CONTEXT_TYPES_YAML"),
)

#: Every package the editable install puts on ``sys.path`` from the main tree —
#: i.e. every package whose ``__file__`` lies about which checkout it is in.
#: ``agents/``, ``scripts/`` and ``libs/`` are deliberately absent: they are not
#: installed, so they import out of the caller's own tree and were never affected.
INSTALLED_PACKAGES: tuple[str, ...] = (
    "drydocs",
    "drydocs_core",
    "drydocs_remediation",
    "drydocs_lineage",
    "drydocs_deepdoc",
    "drydocs_docmeta",
    "drydocs_api",
)

#: ``__file__``-anchored expressions that climb to the repo root and are RIGHT to.
#: Each needs its reason; the module comment carries the long form.
ROOT_ANCHOR_EXEMPT: dict[str, str] = {
    "drydocs_core/config.py": (
        ".env is untracked machine-local credentials. A git worktree gets the tracked "
        "tree and NOT this file, so following the caller would find no .env at all and "
        "lose the database settings — an untracked local secret is not repo content"
    ),
}


def _make_fake_checkout(root: Path) -> Path:
    """Build the minimum tree ``repo_paths`` recognizes as a DryDocs checkout."""
    root.mkdir(parents=True, exist_ok=True)
    (root / ".git").write_text("gitdir: /elsewhere\n", encoding="utf-8")
    (root / "pyproject.toml").write_text("[tool.poetry]\nname='drydocs'\n", encoding="utf-8")
    (root / "drydocs").mkdir(exist_ok=True)
    (root / "drydocs" / "__init__.py").write_text("", encoding="utf-8")
    return root


# --------------------------------------------------------------------------- unit


def test_resolves_to_the_checkout_containing_the_cwd(tmp_path, monkeypatch):
    """The whole bug in one assertion: cwd in tree B, anchor in tree A -> B wins."""
    installed = _make_fake_checkout(tmp_path / "main-tree")
    caller = _make_fake_checkout(tmp_path / "worktree")

    monkeypatch.chdir(caller)
    assert repo_root(installed / "drydocs") == caller.resolve()


def test_resolves_from_a_subdirectory_of_the_checkout(tmp_path, monkeypatch):
    """Renders are run from anywhere in the tree, not only its root."""
    installed = _make_fake_checkout(tmp_path / "main-tree")
    caller = _make_fake_checkout(tmp_path / "worktree")
    deep = caller / "docs" / "plan"
    deep.mkdir(parents=True)

    monkeypatch.chdir(deep)
    assert repo_root(installed / "drydocs") == caller.resolve()


def test_falls_back_when_the_cwd_is_outside_any_repo(tmp_path, monkeypatch):
    """An installed-package consumer keeps the old behaviour exactly."""
    installed = _make_fake_checkout(tmp_path / "main-tree")
    outside = tmp_path / "somewhere-else"
    outside.mkdir()

    monkeypatch.chdir(outside)
    anchor = installed / "drydocs"
    assert repo_root(anchor) == anchor.resolve()


def test_a_foreign_repo_never_captures_the_paths(tmp_path, monkeypatch):
    """cwd inside the ``depgraph`` sibling must NOT redirect DryDocs' own defaults."""
    installed = _make_fake_checkout(tmp_path / "main-tree")
    foreign = tmp_path / "depgraph"
    foreign.mkdir()
    (foreign / ".git").mkdir()
    (foreign / "pyproject.toml").write_text("[project]\nname='depgraph'\n", encoding="utf-8")

    monkeypatch.chdir(foreign)
    anchor = installed / "drydocs"
    assert repo_root(anchor) == anchor.resolve()


def test_a_parent_repo_never_captures_the_paths(tmp_path, monkeypatch):
    """The climb stops at the nearest ``.git``; it does not keep going up to find a match."""
    outer = _make_fake_checkout(tmp_path / "outer-drydocs")
    inner = outer / "vendored"
    inner.mkdir()
    (inner / ".git").mkdir()
    (inner / "pyproject.toml").write_text("[project]\nname='other'\n", encoding="utf-8")

    monkeypatch.chdir(inner)
    anchor = tmp_path / "main-tree" / "drydocs"
    assert repo_root(anchor) == anchor.resolve()


#: The root constant each swept module exposes. Three spellings are in use and
#: renaming 24 modules to agree would be churn for its own sake.
_ROOT_ATTRS = ("_REPO_ROOT", "REPO_ROOT", "_REPO")


def _module_root(module) -> Path:
    for attr in _ROOT_ATTRS:
        if isinstance(getattr(module, attr, None), Path):
            return getattr(module, attr)
    raise AssertionError(f"{module.__name__} exposes no root constant from {_ROOT_ATTRS}")


@pytest.mark.parametrize(("module_path", "constant"), CONTENT_PATH_CONSTANTS)
def test_content_defaults_live_under_the_resolved_root(module_path, constant):
    """Every repo-content default must sit inside the checkout, wherever that is.

    Guards the adoption, not the helper: a new default added with a bare
    ``Path(__file__)`` anchor is exactly the regression, and adding its constant here
    is the one-line cost of the fix staying applied.
    """
    module = __import__(module_path, fromlist=[constant])
    value = getattr(module, constant)
    root = _module_root(module)
    assert value.is_relative_to(root), f"{module_path}.{constant} escapes the root"
    assert root == REPO, "the test suite runs from the main checkout"


# ------------------------------------------------------------------ default-deny


def _dunder_file_anchor(node: ast.AST) -> str | None:
    """``__file__`` -> "", ``pkg.sub.__file__`` -> "pkg.sub", else None."""
    if isinstance(node, ast.Name) and node.id == "__file__":
        return ""
    if isinstance(node, ast.Attribute) and node.attr == "__file__":
        parts = []
        cur: ast.AST = node.value
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            return ".".join(reversed(parts))
    return None


def _climb_chain(node: ast.AST) -> tuple[int, str] | None:
    """``Path(<x>.__file__).resolve().parents[2]`` -> ``(3, anchor)``; else None.

    Counts how far the expression climbs: each ``.parent`` is one level and
    ``.parents[i]`` is ``i + 1``.
    """
    climbs = 0
    cur = node
    while True:
        if isinstance(cur, ast.Attribute) and cur.attr == "parent":
            climbs += 1
            cur = cur.value
        elif (
            isinstance(cur, ast.Subscript)
            and isinstance(cur.value, ast.Attribute)
            and cur.value.attr == "parents"
            and isinstance(cur.slice, ast.Constant)
            and isinstance(cur.slice.value, int)
        ):
            climbs += cur.slice.value + 1
            cur = cur.value.value
        elif (
            isinstance(cur, ast.Call)
            and isinstance(cur.func, ast.Attribute)
            and cur.func.attr == "resolve"
        ):
            cur = cur.func.value
        else:
            break

    func = getattr(cur, "func", None)
    name = getattr(func, "id", None) or getattr(func, "attr", None)
    if isinstance(cur, ast.Call) and name == "Path" and cur.args:
        anchor = _dunder_file_anchor(cur.args[0])
        if anchor is not None:
            return climbs, anchor
    return None


def test_no_module_anchors_repo_content_on_dunder_file() -> None:
    """DEFAULT-DENY: an expression that climbs to the REPO ROOT must go through
    ``repo_root()``, in every package the editable install serves from the main tree.

    This is the half the ledger above cannot cover. The parametrized test proves the
    constants we KNOW about resolve correctly; it can say nothing about a module
    added next month with a fresh ``Path(__file__).resolve().parents[2]`` — which is
    exactly how all 24 of these got here, and this guard found the last of them (a
    ``_repo_relative`` helper buried in a function body) after the sweep had already
    read every file on Idea-109's list. Landing at the repo root is the whole signal:
    a chain that stops INSIDE its own package is a package-internal resource and
    rightly keeps the ``__file__`` anchor (``drydocs_core/schema/*.cypher``,
    ``drydocs/loaders/cypher/``, the bundled sample CSVs).
    """
    offenders: list[str] = []
    for package in INSTALLED_PACKAGES:
        for path in sorted((REPO / package).rglob("*.py")):
            rel = path.relative_to(REPO).as_posix()
            if rel in ROOT_ANCHOR_EXEMPT:
                continue
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)

            wrapped = {
                id(arg)
                for node in ast.walk(tree)
                if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "repo_root"
                for arg in node.args
            }
            for node in ast.walk(tree):
                chain = _climb_chain(node)
                if chain is None or id(node) in wrapped:
                    continue
                climbs, anchor = chain
                # Depth of the file the anchor names, in components from the repo root.
                depth = len(anchor.split(".")) + 1 if anchor else len(path.relative_to(REPO).parts)
                if depth - climbs == 0:
                    offenders.append(f"{rel}:{node.lineno} climbs to the repo root")

    assert not offenders, (
        f"{len(offenders)} __file__ anchor(s) resolve REPO CONTENT without repo_root() "
        "(Idea-109). Wrap the anchor in repo_root(...) if the path is repo content, or "
        "add the file to ROOT_ANCHOR_EXEMPT with the reason it must follow the "
        "install instead:\n  " + "\n  ".join(offenders)
    )


def test_every_root_anchor_exemption_names_a_real_file_and_a_reason() -> None:
    """Shrink-only: an exemption for a file that moved is dead weight, and one
    without a reason has outlived whoever knew why."""
    for rel, why in ROOT_ANCHOR_EXEMPT.items():
        assert (REPO / rel).is_file(), f"ROOT_ANCHOR_EXEMPT names a missing file: {rel}"
        assert len(why.strip()) >= 40, f"ROOT_ANCHOR_EXEMPT[{rel!r}] needs a reason"


# ---------------------------------------------------------------------- end-to-end


#: Printed by the probe below, one per line, as ``<label>\t<resolved path>``. Spans all
#: four installed packages the sweep touched, plus the one constant that must NOT move.
_PROBE = """\
import drydocs.review.gate_pages, drydocs.port.port_preflight, drydocs.seal_samples
import drydocs.cli, drydocs_core.precedence, drydocs_core.mapping_store
import drydocs.loaders.code_snapshot, drydocs_docmeta.registry, drydocs_api.intake
for label, value in [
    ("content:gate_pages", drydocs.review.gate_pages.DEFAULT_GATE_PROMPTS_DIR),
    ("content:port_preflight", drydocs.port.port_preflight.PORT_PROMPT_PATH),
    ("content:seal_samples", drydocs.seal_samples.DEFAULT_SAMPLES_DIR),
    ("content:precedence", drydocs_core.precedence.DEFAULT_PRECEDENCE_PATH),
    ("content:mapping_store_db", drydocs_core.mapping_store.DEFAULT_DB_PATH),
    ("content:code_snapshot", drydocs.loaders.code_snapshot.DEFAULT_SNAPSHOT_DIR),
    ("content:docmeta_registry", drydocs_docmeta.registry.DEFAULT_LEDGER_PATH),
    ("content:api_intake", drydocs_api.intake._CONTEXT_TYPES_YAML),
    ("package:cli_samples", drydocs.cli.DEFAULT_SAMPLES_DIR),
]:
    print(f"{label}\\t{value}")
"""


@pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")
def test_swept_defaults_resolve_inside_a_real_worktree(tmp_path):
    """J48 clause (b): drive a REAL worktree and prove the sweep took.

    The parametrized ledger runs from the main checkout, where a swept constant and an
    unswept one resolve to the SAME path — it cannot tell them apart. Only a second
    checkout can, which is why this spends a real ``git worktree``: it is the one place
    the defect is observable at all.

    ``package:cli_samples`` is the control. It names the same directory as
    ``content:seal_samples`` and must stay pinned at the install, so a blanket
    search-and-replace of every ``__file__`` anchor fails this test rather than passing
    it — which is what makes this a check on the JUDGEMENT and not just on the edit.

    THE PROBE RUNS AS A FILE OUTSIDE THE WORKTREE, and that is load-bearing rather than
    tidy. ``python -c`` puts the CWD on ``sys.path``, so the worktree's own ``drydocs/``
    shadows the editable install and every import — swept or not — comes back
    worktree-relative: the control passes for the wrong reason and the test proves
    nothing. Running a file reproduces the incident's actual conditions, where
    ``sys.path[0]`` is the SCRIPT's directory and the cwd is never on the path. The
    first draft used ``-c`` and failed exactly here, which is how this got written down.
    """
    worktree = tmp_path / "wt"
    probe = tmp_path / "probe.py"  # NOT inside the worktree — see the docstring
    probe.write_text(_PROBE, encoding="utf-8")
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    try:
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        result = subprocess.run(
            [sys.executable, str(probe)],
            cwd=worktree,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"probe failed:\n{result.stdout}\n{result.stderr}"

        resolved = dict(line.split("\t", 1) for line in result.stdout.splitlines() if "\t" in line)
        assert len(resolved) == 9, f"probe printed {len(resolved)} rows, expected 9"

        for label, value in sorted(resolved.items()):
            path = Path(value)
            if label.startswith("content:"):
                assert path.is_relative_to(
                    worktree
                ), f"{label} resolved OUTSIDE the caller's worktree: {value}"
            else:
                assert path.is_relative_to(REPO) and not path.is_relative_to(
                    worktree
                ), f"{label} is package-internal and must stay with the install: {value}"
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=REPO,
            check=False,
            capture_output=True,
        )


@pytest.mark.skipif(shutil.which("git") is None, reason="git not on PATH")
def test_a_worktree_render_does_not_touch_the_main_tree(tmp_path):
    """The original incident, reproduced and asserted against.

    Drives a REAL ``git worktree`` and a REAL ``scripts/render_board.py`` run, then
    asserts the main tree's committed renders are byte-for-byte unchanged. Before the
    fix this failed on ``board.html``: the render succeeded, the worktree looked clean,
    and main quietly acquired three regenerated files.
    """
    watched = (
        REPO / "docs" / "plan" / "board.html",
        REPO / "docs" / "plan" / "ideas.html",
        REPO / "docs" / "plan" / "roadmap.html",
    )
    before = {p: p.read_bytes() for p in watched if p.is_file()}
    if not before:  # pragma: no cover - the renders are committed
        pytest.skip("no committed renders present to protect")

    worktree = tmp_path / "wt"
    subprocess.run(
        ["git", "worktree", "add", "--detach", str(worktree), "HEAD"],
        cwd=REPO,
        check=True,
        capture_output=True,
    )
    try:
        # Strip PYTHONPATH so nothing re-injects the main tree ahead of the discovery.
        env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
        result = subprocess.run(
            [sys.executable, str(worktree / "scripts" / "render_board.py")],
            cwd=worktree,
            capture_output=True,
            text=True,
            env=env,
        )
        assert result.returncode == 0, f"render failed:\n{result.stdout}\n{result.stderr}"

        # The worktree is where the output belongs...
        assert (worktree / "docs" / "plan" / "board.html").is_file()
        # ...and every path the run printed must be inside it, not in main.
        for line in result.stdout.splitlines():
            if line.startswith("wrote "):
                assert (
                    str(REPO) not in line or str(worktree) in line
                ), f"render wrote outside the caller's worktree: {line}"

        after = {p: p.read_bytes() for p in before}
        assert after == before, "a worktree render modified the MAIN tree (Idea-109)"
    finally:
        subprocess.run(
            ["git", "worktree", "remove", "--force", str(worktree)],
            cwd=REPO,
            check=False,
            capture_output=True,
        )
