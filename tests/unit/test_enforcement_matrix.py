"""O12 enforcement-matrix drift guard (wf-admin-config-01 (4)).

The matrix cannot drift from the repo: regenerating in-memory must equal the
committed web/src/generated/enforcement-matrix.json, every referenced
file/consumer/guard-test must exist (the generator fails closed on those),
and every top-level config/ entry must have a surface row.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent.parent
COMMITTED = REPO / "web" / "src" / "generated" / "enforcement-matrix.json"


def _generator():
    spec = importlib.util.spec_from_file_location(
        "render_enforcement_matrix", REPO / "scripts" / "render_enforcement_matrix.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_committed_matrix_matches_regeneration():
    """The committed artifact equals a fresh build — regen + commit on drift."""
    mod = _generator()
    fresh = mod.build_matrix()
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    assert committed == fresh, (
        "enforcement-matrix.json drifted from the repo — run: "
        "python scripts/render_enforcement_matrix.py and commit the result"
    )


def test_every_config_surface_has_a_row():
    """Generator-level completeness re-asserted here so a registry hole fails
    even if someone hand-edits the JSON to match."""
    mod = _generator()
    covered = set()
    for s in mod.SURFACES:
        parts = s["file"].split("/")
        if parts[0] == "config" and len(parts) > 1:
            covered.add(parts[1])
        for extra in s.get("extra_files", []):
            ep = extra.split("/")
            if ep[0] == "config" and len(ep) > 1:
                covered.add(ep[1])
    for entry in sorted(p.name for p in (REPO / "config").iterdir()):
        assert entry in covered or entry in mod.CONFIG_EXEMPT, (
            f"config/{entry} has no enforcement-matrix surface row — add it to "
            "scripts/render_enforcement_matrix.py SURFACES (or CONFIG_EXEMPT with a reason)"
        )


def test_referenced_paths_exist():
    mod = _generator()
    for s in mod.SURFACES:
        assert (REPO / s["file"].rstrip("/")).exists(), f"{s['id']}: missing {s['file']}"
        for c in s["consumers"]:
            assert (REPO / c.rstrip("/")).exists(), f"{s['id']}: missing consumer {c}"
        for t in s["guard_tests"]:
            assert (REPO / "tests" / "unit" / t).exists(), f"{s['id']}: missing guard test {t}"


def test_launcher_registry_migrated_to_a_guarded_config_surface():
    """G26 (2026-07-27) retired the code-resident unguarded example: the
    registry now lives at config/launcher-registry.yaml behind a schema
    guard, and the matrix must render it that way. (Until G26 this test
    asserted the INVERSE — the page's visible migration argument.)"""
    committed = json.loads(COMMITTED.read_text(encoding="utf-8"))
    row = next(s for s in committed["surfaces"] if s["id"] == "launcher-registry")
    assert row["code_resident"] is False
    assert row["file"] == "config/launcher-registry.yaml"
    assert "test_launcher_registry.py" in row["guard_tests"]
    assert row["status"] == "enforced"
