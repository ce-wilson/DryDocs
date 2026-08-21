"""U7 — the depgraph capability probe behind `snapshot.ps1`.

The probe exists because a sibling-repo checkout silently decided what a
snapshot could see. These tests pin the *decision logic* with injected fakes
(so they run anywhere), plus one live check against the real configured
instrument that skips when the sibling repo is absent.
"""

from __future__ import annotations

import importlib.util
import json
import sys
import types
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parents[2]
PROBE_PATH = REPO_ROOT / "knowledge" / "depgraph-snapshots" / "probe_instrument.py"


def _main_worktree() -> Path:
    """The MAIN checkout — parent of the shared .git — from a worktree or the
    checkout itself (U26). Falls back to this file's repo root when git is
    unavailable, which is the pre-U26 behaviour and correct from the checkout."""
    import subprocess

    try:
        out = subprocess.run(
            ["git", "rev-parse", "--path-format=absolute", "--git-common-dir"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
            timeout=20,
            check=True,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return REPO_ROOT
    return Path(out).parent if out else REPO_ROOT


DEV_ENV = REPO_ROOT / "config" / "dev-environment.yaml"


def _load_probe() -> types.ModuleType:
    spec = importlib.util.spec_from_file_location("probe_instrument", PROBE_PATH)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


probe_mod = _load_probe()


def _fake_importer(modules: dict[str, types.ModuleType | Exception]):
    def _import(name: str):
        got = modules.get(name)
        if got is None:
            raise ModuleNotFoundError(name)
        if isinstance(got, Exception):
            raise got
        return got

    return _import


def _extractor_module(*, with_extract_many: bool) -> types.ModuleType:
    mod = types.ModuleType("depgraph.extractors.python_imports")

    class PythonImportExtractor:
        def extract(self, *a, **k):  # the isolated-root entry point, always present
            ...

    if with_extract_many:
        PythonImportExtractor.extract_many = lambda self, *a, **k: None
    mod.PythonImportExtractor = PythonImportExtractor
    return mod


def _cli_module(*, help_text: str) -> types.ModuleType:
    mod = types.ModuleType("depgraph.cli")

    def main(argv=None):
        print(help_text)
        raise SystemExit(0)

    mod.main = main
    return mod


# --- multi_root --------------------------------------------------------------


def test_multi_root_true_when_extract_many_present():
    made = _extractor_module(with_extract_many=True)
    imp = _fake_importer({"depgraph.extractors.python_imports": made})
    assert probe_mod._probe_multi_root(imp) is True


def test_multi_root_false_when_only_isolated_extract():
    """The exact 2026-07-28 regression: importable, looks fine, resolves nothing."""
    made = _extractor_module(with_extract_many=False)
    imp = _fake_importer({"depgraph.extractors.python_imports": made})
    assert probe_mod._probe_multi_root(imp) is False


def test_multi_root_false_when_module_missing():
    assert probe_mod._probe_multi_root(_fake_importer({})) is False


def test_multi_root_false_when_import_raises_non_import_error():
    imp = _fake_importer({"depgraph.extractors.python_imports": RuntimeError("boom")})
    assert probe_mod._probe_multi_root(imp) is False


# --- tree --------------------------------------------------------------------


def test_tree_true_when_cli_advertises_the_flag():
    made = _cli_module(help_text="usage: depgraph scan\n  --tree  walk files")
    imp = _fake_importer({"depgraph.cli": made})
    assert probe_mod._probe_tree(imp) is True


def test_tree_false_when_flag_absent_from_help():
    """controlm-lineage: the CLI works, it just has no --tree."""
    made = _cli_module(help_text="usage: depgraph scan\n  --project NAME")
    imp = _fake_importer({"depgraph.cli": made})
    assert probe_mod._probe_tree(imp) is False


def test_tree_false_when_cli_missing():
    assert probe_mod._probe_tree(_fake_importer({})) is False


def test_tree_survives_a_cli_that_raises():
    mod = types.ModuleType("depgraph.cli")

    def main(argv=None):
        raise RuntimeError("parser exploded")

    mod.main = main
    assert probe_mod._probe_tree(_fake_importer({"depgraph.cli": mod})) is False


def test_tree_probe_does_not_leak_help_text_to_stdout(capsys):
    """--help writes to the real stdout unless captured; the probe must swallow it."""
    imp = _fake_importer({"depgraph.cli": _cli_module(help_text="NOISE --tree")})
    probe_mod._probe_tree(imp)
    assert capsys.readouterr().out == ""


# --- ts_imports --------------------------------------------------------------


def _extractors_module(default_names):
    mod = types.ModuleType("depgraph.extractors")

    class _E:
        def __init__(self, name):
            self.name = name

    mod.default_extractors = lambda: [_E(n) for n in default_names]
    return mod


def test_ts_imports_true_when_default_extractors_carry_it():
    imp = _fake_importer(
        {"depgraph.extractors": _extractors_module(["python-imports", "ts-imports"])}
    )
    assert probe_mod._probe_ts_imports(imp) is True


def test_ts_imports_false_when_absent_or_opt_in():
    """An extractor that exists but is not in default_extractors() still leaves
    a plain snapshot without front-end edges — membership is what scan() consults."""
    imp = _fake_importer({"depgraph.extractors": _extractors_module(["python-imports"])})
    assert probe_mod._probe_ts_imports(imp) is False


def test_ts_imports_false_when_module_missing():
    assert probe_mod._probe_ts_imports(_fake_importer({})) is False


# --- reporting / policy ------------------------------------------------------


def test_missing_reports_only_unmet_requirements():
    caps = {"multi_root": True, "tree": False}
    assert probe_mod.missing(caps, ["multi_root"]) == []
    assert probe_mod.missing(caps, ["multi_root", "tree"]) == ["tree"]


def test_probe_reports_not_importable_without_depgraph():
    caps = probe_mod.probe(_fake_importer({}))
    assert caps == {
        "multi_root": False,
        "tree": False,
        "ts_imports": False,
        "version": None,
        "importable": False,
    }


def test_main_emits_json_and_exits_zero_by_default(capsys, monkeypatch):
    """Report-don't-decide: a missing capability is still exit 0 without --require."""
    monkeypatch.setattr(probe_mod, "probe", lambda: {"multi_root": False, "tree": False})
    assert probe_mod.main([]) == 0
    assert json.loads(capsys.readouterr().out) == {"multi_root": False, "tree": False}


def test_main_exits_nonzero_when_a_required_capability_is_missing(capsys, monkeypatch):
    monkeypatch.setattr(probe_mod, "probe", lambda: {"multi_root": False, "tree": True})
    assert probe_mod.main(["--require", "multi_root"]) == 1
    capsys.readouterr()


def test_every_capability_has_a_stated_reason():
    """The refusal message quotes these; an unreasoned capability is unexplainable."""
    assert set(probe_mod.CAPABILITY_REASONS) == {"multi_root", "tree", "ts_imports"}
    assert all(v.strip() for v in probe_mod.CAPABILITY_REASONS.values())


# --- the live instrument -----------------------------------------------------


def _configured_instrument() -> dict:
    return yaml.safe_load(DEV_ENV.read_text(encoding="utf-8"))["depgraph"]


def test_dev_environment_records_the_expected_instrument():
    dep = _configured_instrument()
    assert dep["repo"], "the sibling checkout path must be recorded"
    assert dep["expected_branch"] and dep["expected_commit"]
    assert isinstance(dep["capability_assert"], bool), (
        "capability_assert must be an explicit bool — a missing key would silently "
        "decide whether the live check asserts or skips"
    )
    assert "multi_root" in dep["requires"]["scan"]
    assert "tree" in dep["requires"]["tree"]
    # every required capability must be one the probe actually knows how to test
    for names in dep["requires"].values():
        assert set(names) <= set(probe_mod.CAPABILITY_REASONS)


def test_live_instrument_satisfies_the_capabilities_snapshot_requires():
    """The check that was missing on 2026-07-28.

    Two ways this legitimately does not run, and they are different:

    * the sibling repo is not checked out — this repo must stay clonable and
      testable on its own;
    * ``depgraph.capability_assert`` is false — the deployment's scanner is
      separately owned, so a missing capability is an owed action elsewhere
      rather than a defect here. The consumer hit exactly this: its depgraph
      fork lacks the U6 resolver and the producer remote is unreachable from
      it, so the port could not remediate (PORT-REPORT-94132c80 / 48e).

    The second gate is config, not an env var, so this file stays identical on
    both sides and there is nothing to reconcile at the next port.
    """
    dep = _configured_instrument()
    if not dep["capability_assert"]:
        pytest.skip(
            "config/dev-environment.yaml sets depgraph.capability_assert: false — "
            "the configured scanner is separately owned; its capability gap is an "
            "owed action there, not a failure here"
        )
    # U26: the sibling sits beside the MAIN checkout. From a git worktree this
    # file's parents[2] is the worktree, and resolving `../depgraph` from there
    # named a path that never existed — the test skipped with the same wrong
    # location snapshot.ps1 died on, so the two agreed while both were wrong.
    dep_path = (_main_worktree() / dep["repo"]).resolve()
    if not (dep_path / "depgraph").is_dir():
        pytest.skip(
            f"depgraph sibling checkout absent at {dep_path} (resolved beside the main "
            "working tree via git rev-parse --git-common-dir)"
        )
    sys.path.insert(0, str(dep_path))
    try:
        for name in [m for m in sys.modules if m == "depgraph" or m.startswith("depgraph.")]:
            del sys.modules[name]
        caps = probe_mod.probe()
    finally:
        sys.path.remove(str(dep_path))
    assert caps["multi_root"], (
        f"the depgraph checkout at {dep_path} cannot resolve multi-root imports — "
        "a snapshot taken now would undercount edges (see U6/U7)"
    )
