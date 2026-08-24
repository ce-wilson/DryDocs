"""G81 — every path is a DECLARED zone with a mode, and write never meets read.

THE INCIDENT (2026-08-11): an internal folder holding extracted CSV source data
was OVERWRITTEN. Recovered from backup, so nothing was permanently lost — but the
class fires again the moment the backup is restored to the same place, which is
why this is a guard and not a note. The reconstruction that produced the design
is ``docs/reviews/g81-data-path-reconstruction.md``.

THE INVARIANT: no write/scratch zone may EQUAL, CONTAIN, or BE CONTAINED BY a
read zone. Both directions — the acceptance named only "equal or contain", and
two of the four live findings ran the other way, so a one-directional check would
have reported all-clear on half of them.

PROVEN TO FAIL before it is trusted (J26): the injected-overlap tests below build
a fixture declaration containing each violation shape and assert the guard names
BOTH paths. A guard that only passes on a clean tree has proved nothing.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_core import data_zones as dz

REPO = Path(__file__).resolve().parents[2]


def _write_zones(tmp_path: Path, body: str) -> Path:
    path = tmp_path / "data-zones.yaml"
    path.write_text(f"schema: drydocs.data-zones.v1\nzones:\n{body}", encoding="utf-8")
    return path


def _zone(zid: str, mode: str, spec: str, root: Path) -> dz.DataZone:
    return dz.DataZone(
        id=zid,
        mode=mode,
        base=dz.BASE_DATA_ROOT,
        path_spec=spec,
        path=root / spec,
        helper=None,
        env=None,
        note="",
    )


# --------------------------------------------------------------------------- #
# the invariant, against the REAL declarations
# --------------------------------------------------------------------------- #
def test_no_write_zone_meets_a_read_zone() -> None:
    """THE GUARD. Runs against the committed config/data-zones.yaml joined with
    config/source-registry.yaml's acquisition rows."""
    violations = dz.overlaps()
    assert not violations, (
        "write/scratch zone(s) overlapping a read zone — this is the 2026-08-11 "
        "overwrite class, live:\n  " + "\n  ".join(violations)
    )


def test_the_real_declaration_loads_and_is_not_empty() -> None:
    """An empty or unreadable declaration would make the invariant vacuously
    true — the failure mode the whole item exists to close."""
    zones = dz.load_zones()
    assert len(zones) >= 5, "suspiciously few declared zones — is the file truncated?"
    assert {z.mode for z in zones} <= set(dz.MODES)


def test_every_data_root_helper_maps_to_a_declared_zone() -> None:
    """Clause (b): the declaration is the enumeration. A helper that resolves a
    path but appears in no zone row is exactly the unenumerable surface that hid
    the overlap — so a new helper fails here until it is declared."""
    import inspect

    from drydocs_core import data_root

    # A helper counts as declared either by NAME in data-zones.yaml, or by
    # RESOLVING to a dataset drop the source registry already declares — those
    # are deliberately not duplicated into the second file (that split is the
    # point). So the match is on both, and a helper matching neither is the
    # unenumerable surface this clause exists to end.
    by_name = {z.helper for z in dz.load_zones() if z.helper}
    registry_paths = {z.path.resolve() for z in dz.registry_read_zones()}
    undeclared = []
    for name, fn in vars(data_root).items():
        # source_dir is the general RESOLVER every named helper composes, not a
        # zone of its own; its create path is guarded at runtime instead
        # (test_creating_inside_a_read_zone_is_refused).
        if name == "source_dir":
            continue
        if not (callable(fn) and name.endswith("_dir") and not name.startswith("_")):
            continue
        if inspect.getmodule(fn) is not data_root:
            continue
        if name in by_name:
            continue
        try:
            resolved = fn().resolve()
        except TypeError:  # a helper needing arguments cannot be probed blind
            undeclared.append(name)
            continue
        if resolved not in registry_paths:
            undeclared.append(name)
    assert not undeclared, (
        f"data_root helper(s) with no zone row in config/data-zones.yaml: "
        f"{sorted(undeclared)} — declare each with a mode, or the system touches "
        "a path no reader can enumerate."
    )


def test_read_zone_helpers_cannot_create() -> None:
    """Clause (e), the converse: a read-mode zone must be reachable only through
    a helper that cannot create. `create=True` on a read helper would make it
    write-mode by construction."""
    import inspect

    from drydocs_core import data_root

    offenders = []
    for zone in dz.load_zones():
        if zone.mode != dz.READ or not zone.helper:
            continue
        fn = getattr(data_root, zone.helper, None)
        if fn is None:
            continue
        if "create" in inspect.signature(fn).parameters:
            offenders.append(f"{zone.helper} (zone {zone.id!r})")
    assert not offenders, (
        f"READ-zone helper(s) exposing `create`: {offenders} — any path a "
        "create-capable helper may build is write-mode BY CONSTRUCTION (G81 (e))."
    )


def test_declared_helpers_exist() -> None:
    """A zone naming a helper that does not exist is a stale declaration."""
    from drydocs_core import data_root

    missing = [
        f"{z.id}:{z.helper}"
        for z in dz.load_zones()
        if z.helper and not hasattr(data_root, z.helper)
    ]
    assert not missing, f"zone(s) naming a non-existent helper: {missing}"


def test_zone_paths_are_conventions_not_machine_paths() -> None:
    """The J15 shape rule, borrowed from the drop_dir guard: no absolute paths,
    drive letters, UNC or parent escapes — real paths live in the internal twin."""
    bad = []
    for zone in dz.load_zones():
        spec = zone.path_spec
        if (
            spec.startswith(("/", "\\"))
            or "\\" in spec
            or ".." in spec
            or (len(spec) > 1 and spec[1] == ":")
        ):
            bad.append(f"{zone.id}: {spec!r}")
    assert not bad, f"zone path(s) that look like real machine paths: {bad}"


def test_declared_zones_do_not_duplicate_a_dataset_drop() -> None:
    """Read zones that ARE dataset drops live in source-registry.yaml; declaring
    one in both files is the drift this split exists to avoid."""
    registry = {z.path.resolve() for z in dz.registry_read_zones()}
    dupes = [z.id for z in dz.load_zones() if z.path.resolve() in registry]
    assert not dupes, (
        f"zone(s) duplicating a source-registry acquisition.drop_dir: {dupes} — "
        "the registry owns dataset drops; data-zones.yaml owns the rest."
    )


# --------------------------------------------------------------------------- #
# PROOF OF FAIL — each violation shape, injected
# --------------------------------------------------------------------------- #
def test_an_equal_path_is_caught_and_names_both(tmp_path: Path) -> None:
    zones = (_zone("out", dz.WRITE, "shared", tmp_path), _zone("drop", dz.READ, "shared", tmp_path))
    found = dz.overlaps(zones)
    assert len(found) == 1
    assert "EQUALS" in found[0] and "out" in found[0] and "drop" in found[0]
    assert str(tmp_path / "shared") in found[0], "the failure must name the PATH, not just the id"


def test_a_write_inside_a_read_zone_is_caught(tmp_path: Path) -> None:
    """THE RUA SHAPE — the direction the acceptance did not name, and 2 of the 4
    live findings. rua/extracted/ (write) sat inside rua/ (read)."""
    zones = (
        _zone("extracted", dz.WRITE, "rua/extracted", tmp_path),
        _zone("bundles", dz.READ, "rua", tmp_path),
    )
    found = dz.overlaps(zones)
    assert len(found) == 1 and "is INSIDE" in found[0]


def test_a_write_containing_a_read_zone_is_caught(tmp_path: Path) -> None:
    """THE ROOT SHAPE — a create-capable helper at a level that contains drops."""
    zones = (
        _zone("everything", dz.WRITE, ".", tmp_path),
        _zone("drop", dz.READ, "pat", tmp_path),
    )
    found = dz.overlaps(zones)
    assert len(found) == 1 and "CONTAINS" in found[0]


def test_a_clean_set_reports_nothing(tmp_path: Path) -> None:
    zones = (
        _zone("extracted", dz.WRITE, "rua/extracted", tmp_path),
        _zone("bundles", dz.READ, "rua/incoming", tmp_path),
    )
    assert dz.overlaps(zones) == ()


def test_scratch_counts_as_a_write_for_the_invariant(tmp_path: Path) -> None:
    """Scratch is disposable — it may be CLEANED, which is worse than written."""
    zones = (_zone("tmp", dz.SCRATCH, "work", tmp_path), _zone("drop", dz.READ, "work", tmp_path))
    assert len(dz.overlaps(zones)) == 1


# --------------------------------------------------------------------------- #
# a declaration that cannot be trusted FAILS — never a silent default
# --------------------------------------------------------------------------- #
def test_a_missing_declaration_raises(tmp_path: Path) -> None:
    with pytest.raises(dz.DataZoneError, match="missing"):
        dz.load_zones(tmp_path / "nope.yaml")


def test_an_empty_declaration_raises(tmp_path: Path) -> None:
    path = tmp_path / "data-zones.yaml"
    path.write_text("schema: drydocs.data-zones.v1\nzones: []\n", encoding="utf-8")
    with pytest.raises(dz.DataZoneError, match="no zones"):
        dz.load_zones(path)


@pytest.mark.parametrize(
    ("body", "match"),
    [
        ("  - id: a\n    mode: sideways\n    base: data_root\n    path: a/\n", "mode"),
        ("  - id: a\n    mode: read\n    base: elsewhere\n    path: a/\n", "base"),
        ("  - id: a\n    mode: read\n    base: data_root\n    path: ''\n", "no path"),
        (
            "  - id: a\n    mode: read\n    base: data_root\n    path: a/\n"
            "  - id: a\n    mode: write\n    base: data_root\n    path: b/\n",
            "duplicate",
        ),
    ],
)
def test_a_malformed_zone_raises(tmp_path: Path, body: str, match: str) -> None:
    with pytest.raises(dz.DataZoneError, match=match):
        dz.load_zones(_write_zones(tmp_path, body))


# --------------------------------------------------------------------------- #
# the RUNTIME half: a write aimed at a read zone is refused
# --------------------------------------------------------------------------- #
def test_creating_inside_a_read_zone_is_refused(monkeypatch, tmp_path: Path) -> None:
    """The static invariant compares DECLARATIONS and cannot see a path handed in
    at call time — which is how the incident could happen with every declaration
    correct. This is the check at the write site."""
    from drydocs_core import data_root

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    with pytest.raises(data_root.ReadZoneWriteError) as info:
        data_root.source_dir("remediation", "incoming", "sneaky", create=True)
    message = str(info.value)
    assert "remediation-incoming" in message, "the refusal must name the ZONE"
    assert "sneaky" in message, "the refusal must name the TARGET"
    assert not (
        tmp_path / "remediation" / "incoming" / "sneaky"
    ).exists(), "the directory was created despite the refusal"


def test_creating_in_a_write_zone_still_works(monkeypatch, tmp_path: Path) -> None:
    """The guard must not make the system unable to do its job."""
    from drydocs_core import data_root

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    made = data_root.rua_extracted_dir("bundle-1", create=True)
    assert made.is_dir()


def test_read_zone_containing_finds_the_zone(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    hit = dz.read_zone_containing(tmp_path / "remediation" / "incoming" / "x" / "y.xml")
    assert hit is not None and hit.id == "remediation-incoming"
    assert dz.read_zone_containing(tmp_path / "rua" / "extracted" / "b") is None


def test_the_console_script_renders_config_errors_not_tracebacks() -> None:
    """G81's errors are OPERATOR CONFIGURATION errors, and the command most
    likely to meet one is `landing-zones` — whose whole reason for existing is
    that "my extracts are gone" should be a one-command answer. A stack trace
    there defeats the command at the moment it matters, so pyproject points at
    run(), which renders the message and exits 2 (the repo's operator-error
    code). Guarded because an entry-point revert is silent and untested."""
    import tomllib

    from drydocs import cli

    assert hasattr(cli, "run"), "drydocs.cli.run() is the console-script entry point"
    pyproject = tomllib.loads((REPO / "pyproject.toml").read_text(encoding="utf-8"))
    entry = pyproject["tool"]["poetry"]["scripts"]["drydocs"]
    assert entry.startswith("drydocs.cli:run"), (
        f"the console script points at {entry!r}, not drydocs.cli:run — an "
        "unset DRYDOCS_DATA_ROOT would render as a traceback again."
    )
