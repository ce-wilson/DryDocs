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


def test_the_canonical_load_sequence_is_a_code_resident_surface_that_renders_enforced():
    """O54. The load sequence, its profiles and the scheduled exclusions live in
    drydocs/cli_shared.py by design (every operator surface derives from them),
    and N3/N6 gave them real guard tests. Until O54 the renderer forced
    `unguarded` on ANY code-resident row, which conflated WHERE the config lives
    with WHETHER it is tested. Read from a fresh build, not the committed file:
    the committed artifact is Lane A's render and lags a renderer change until
    the next render_board.py run."""
    fresh = _generator().build_matrix()
    row = next(s for s in fresh["surfaces"] if s["id"] == "canonical-load-sequence")
    assert row["code_resident"] is True
    assert row["file"] == "drydocs/cli_shared.py"
    assert row["symbols"] == [
        "CANONICAL_LOAD_SEQUENCE",
        "LOAD_PROFILES",
        "SCHEDULED_INGEST_EXCLUSIONS",
    ]
    assert "test_load_sequence_surfaces.py" in row["guard_tests"]
    assert row["status"] == "enforced"


def test_a_code_resident_row_renders_its_declarations_not_its_module():
    """The content of a code-resident surface is the named symbols' source (with
    the comment block above each), never the whole module: cli_shared.py is
    hundreds of lines of CLI plumbing, and scanning it would report every env
    read in the CLI as if the load sequence referenced it."""
    fresh = _generator().build_matrix()
    row = next(s for s in fresh["surfaces"] if s["id"] == "canonical-load-sequence")
    content = row["content"]
    for name in row["symbols"]:
        assert f"{name}" in content, f"{name} not in the rendered declarations"
    assert "def " not in content, "a function body leaked into the declaration slice"
    assert len(content) < 12_000, "the slice is the declarations, not the module"
    assert row["files"] == ["drydocs/cli_shared.py"]


def test_status_is_decided_by_guards_and_pending_only():
    """The status function, on its own: residency never decides it."""
    mod = _generator()
    guarded = {"guard_tests": ["x.py"], "code_resident": True}
    unguarded = {"guard_tests": [], "code_resident": False}
    assert mod.surface_status(guarded, pending=0) == "enforced"
    assert mod.surface_status(guarded, pending=2) == "gate-pending"
    assert mod.surface_status(unguarded, pending=0) == "unguarded"
    assert mod.surface_status({**unguarded, "code_resident": True}, pending=0) == "unguarded"


def test_every_row_carries_the_residency_fact_beside_its_status():
    """`code_resident` and `symbols` are on every row (empty symbols for config
    files), so the page never has to infer residency from a path."""
    for row in _generator().build_matrix()["surfaces"]:
        assert isinstance(row["code_resident"], bool), row["id"]
        assert isinstance(row["symbols"], list), row["id"]
        if row["code_resident"]:
            assert row["symbols"], f"{row['id']}: a code-resident row must name its symbols"


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
