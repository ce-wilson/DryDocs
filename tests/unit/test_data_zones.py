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


def test_each_zone_path_equals_what_its_helper_actually_resolves(monkeypatch, tmp_path) -> None:
    """THE DECLARED-EQUALS-RESOLVED GUARD, and it is the one that makes the dpl
    class impossible rather than merely fixed.

    `dpl:pipeline-registry` said `dpl/` while dpl_registry_dir() returned
    `dpl-registry/`, and the two had never agreed since N12 — an operator who
    followed the registry had files nothing read. That was caught by hand here;
    nothing would have caught it happening again INSIDE config/data-zones.yaml,
    and the consequence is worse than a stranded drop: both guard layers key on
    the DECLARATION, so a zone whose YAML path drifts from its helper leaves the
    static invariant checking a fiction while `read_zone_containing()` protects
    the declared directory as writes land in the real one. Drift here disarms the
    whole mechanism silently, which is exactly the class G81 exists to end.

    Matching by NAME is not enough — that only proves the helper is mentioned.

    WIDENED AT G111: this used to walk only zones carrying a `helper`, so a
    helper-less zone (`run-logs` has `helper: ~`) was unguarded — which is why
    `data_zones._resolve()` ignoring the `env:` field entirely survived both G81
    and G109. Every zone is now walked. A helper-less zone declaring `env:` is
    checked against an INDEPENDENT recomputation (never against `dz._resolve`
    itself — that would only prove the code agrees with itself) built by
    explicitly setting its env var to a known override directory and asserting
    the declared path follows it; a helper-less zone with no `env:` falls back to
    checking base + path directly, the same independence the helper branch gets
    from calling the real helper function.
    """
    from drydocs_core import data_root

    monkeypatch.setenv(data_root.DATA_ROOT_ENV, str(tmp_path))
    mismatches = []
    for zone in dz.load_zones():
        if zone.helper:
            fn = getattr(data_root, zone.helper, None)
            if fn is None:
                continue  # named by test_declared_helpers_exist
            resolved = fn()
        elif zone.env:
            # No helper to call — recompute independently by forcing the env
            # var to a known value and expecting the declaration to follow it.
            override_dir = tmp_path / f"env-override-{zone.id}"
            monkeypatch.setenv(zone.env, str(override_dir))
            resolved = override_dir
        else:
            # No helper and no env: the only independent check left is base +
            # path, computed here rather than by calling the code under test.
            if zone.base == dz.BASE_HOME:
                resolved = Path.home() / zone.path_spec
            elif zone.base == dz.BASE_REPO:
                # G126: the repo base recomputed from the module-level constant,
                # not from data_zones' own _REPO_ROOT — same independence rule.
                resolved = REPO / zone.path_spec
            else:
                resolved = data_root.resolve_data_root() / zone.path_spec

        declared = dz._resolve(zone.base, zone.path_spec, zone.env)
        if zone.env:
            monkeypatch.delenv(zone.env, raising=False)
        if resolved.resolve() != declared.resolve():
            source = f"{zone.helper}()" if zone.helper else "the independent recomputation"
            mismatches.append(f"{zone.id}: declares {declared} but {source} gives {resolved}")
    assert not mismatches, (
        "zone declaration(s) disagreeing with what actually resolves them:\n  "
        + "\n  ".join(mismatches)
        + "\nThe declaration is what both the invariant and the runtime refusal "
        "read, so a drift here protects the wrong directory while writes land in "
        "the real one."
    )


def test_resolve_honors_env_when_set_and_falls_back_when_empty_or_unset(
    monkeypatch, tmp_path
) -> None:
    """Clause (a) at the unit level, isolated from the zone walk above: an `env`
    that is unset, or set to an empty/whitespace-only string, is not "set" — the
    same rule `log_kinds.resolve_env_override` enforces for the log root, reused
    here rather than re-derived so the two cannot judge "set" differently."""
    monkeypatch.delenv("DRYDOCS_G111_PROBE", raising=False)
    fallback = dz._resolve(dz.BASE_HOME, "logs/DryDocs/", "DRYDOCS_G111_PROBE")
    assert fallback == Path.home() / "logs/DryDocs/"

    monkeypatch.setenv("DRYDOCS_G111_PROBE", "   ")
    assert dz._resolve(dz.BASE_HOME, "logs/DryDocs/", "DRYDOCS_G111_PROBE") == fallback

    override = tmp_path / "wherever"
    monkeypatch.setenv("DRYDOCS_G111_PROBE", str(override))
    assert dz._resolve(dz.BASE_HOME, "logs/DryDocs/", "DRYDOCS_G111_PROBE") == override

    assert dz._resolve(dz.BASE_HOME, "logs/DryDocs/", None) == fallback


def test_landing_zones_reports_both_declarations_not_just_the_registry(
    monkeypatch, tmp_path
) -> None:
    """G109 (a): the read surface must cover BOTH declarations.

    `drydocs landing-zones` read only `config/source-registry.yaml`'s manual rows,
    so every zone `config/data-zones.yaml` declares — including read zones holding
    real source data — was invisible to the one command whose purpose is that "my
    extracts are gone" is a one-command answer. A check that silently covers half
    the zones reads as coverage, and that is the defect rather than the count.

    Asserted against the JSON surface because that IS the contract here (J37: a
    guard may read CLI output when the output is the contract, and JSON is machine
    output rather than a render that reflows).
    """
    import json

    from typer.testing import CliRunner

    from drydocs import cli
    from drydocs_core import data_zones as dz
    from drydocs_core import landing_zones as lz

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    result = CliRunner().invoke(cli.app, ["landing-zones", "--json"])
    assert result.exit_code == 0, result.output

    payload = json.loads(result.stdout)
    assert set(payload) == {
        "manual_zones",
        "declared_zones",
        # G125: the third and fourth keys. The automated half of the registry
        # declared no binding at all, so this command reported a clean run over
        # the filesystem zones and said nothing about fifteen datasets — the same
        # coverage defect G109 fixed one level narrower.
        "bindings",
        "unbound_carriers",
    }, (
        "the JSON surface must stay ONE document with every half in it — two "
        "printed arrays do not parse, which would break the machine-readable "
        "contract. A new declaration is a new KEY, never a second print_json."
    )

    reported = {row["zone_id"] for row in payload["declared_zones"]}
    expected = {zone.id for zone in dz.load_zones()}
    assert (
        reported == expected
    ), f"declared zones missing from the read surface: {sorted(expected - reported)}"

    manual = {row["source_id"] for row in payload["manual_zones"]}
    assert manual == {
        z.source_id for z in lz.manual_zones()
    }, "widening the command must not drop the registry half it already covered"
    assert reported, "no declared zones reported at all — the join is dead"

    # G126: the hazard and its recovery travel in the same row. A machine reader
    # that can see `inside_repo` but not `rebuild` knows a zone is deletable and
    # nothing about getting it back.
    in_tree = [row for row in payload["declared_zones"] if row["base"] == dz.BASE_REPO]
    assert in_tree, "the in-tree zone vanished from the machine surface"
    for row in in_tree:
        assert row["rebuild"], f"in-tree zone {row['zone_id']} reports no rebuild path"


def test_check_fails_on_an_empty_read_zone_but_not_an_empty_write_zone(
    monkeypatch, tmp_path
) -> None:
    """G109 (a): mode decides what EMPTY means, which is why --check is mode-aware.

    An empty READ zone is the signature this command exists to surface — source
    data that was there and is not. An empty WRITE zone is an output directory the
    system rebuilds on demand, so failing on it would train the operator to ignore
    the exit code, which costs more than the check is worth.
    """
    from typer.testing import CliRunner

    from drydocs import cli
    from drydocs_core import data_zones as dz

    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    zones = dz.load_zones()
    write_zone = next(z for z in zones if z.mode == dz.WRITE and z.base == dz.BASE_DATA_ROOT)
    read_zone = next(z for z in zones if z.mode == dz.READ and z.base == dz.BASE_DATA_ROOT)

    write_zone.path.mkdir(parents=True, exist_ok=True)
    assert (
        CliRunner().invoke(cli.app, ["landing-zones", "--check"]).exit_code == 0
    ), "an empty WRITE zone must not fail --check"

    read_zone.path.mkdir(parents=True, exist_ok=True)
    assert (
        CliRunner().invoke(cli.app, ["landing-zones", "--check"]).exit_code == 1
    ), "an empty READ zone must fail --check — it is the missing-source signature"


# --------------------------------------------------------------------------- #
# G126 — the in-tree zone, its price, and the code that owns its path
# --------------------------------------------------------------------------- #
IN_TREE_ZONES = {"console-credentials"}
"""Every zone deliberately declared inside the working tree.

An explicit set rather than a computed one, because the point is the TRIPWIRE: a
new in-tree zone is a decision someone has to make on purpose, and G109 found two
zones nobody had declared precisely because nothing forced that moment. Adding an
id here is the moment.
"""


def test_in_tree_zones_are_the_ones_we_meant() -> None:
    """A repo-based zone is reachable by ``git clean -fdx`` whatever .gitignore
    says, so arriving at one by accident is the failure this pins down."""
    actual = {z.id for z in dz.load_zones() if z.base == dz.BASE_REPO}
    assert actual == IN_TREE_ZONES, (
        f"in-tree zone set changed: {actual ^ IN_TREE_ZONES}. A repo-based zone "
        "sits where `git clean -fdx` can delete it. If that is intended, add the "
        "id to IN_TREE_ZONES and give the zone a `rebuild:`."
    )


def test_an_in_tree_zone_declares_how_it_is_rebuilt() -> None:
    """THE PRICE OF THE EXCEPTION, and what keeps it from being a blanket.

    A landing zone earns its in-tree place by holding TRACKED files
    (``test_landing_zones.py``). ``internal-local/`` can never be tracked —
    PUBLISH-BOUNDARY.md forbids committing credential material, permanently — so
    it earns its place the other way: by saying, in the declaration, how an
    operator recreates THE SYSTEM'S PAYLOAD there from nothing. G109 (e) ruled the
    Confluence capture OUT of the tree because its exception could never expire
    and it had no rebuild short of a company-side re-scrape. This one has a
    one-command rebuild, and that difference is the whole argument, so it is
    checked rather than asserted in prose.

    THE FIELD IS SCOPED AND THE GUARD DOES NOT OVERSTATE IT: a `rebuild:` covers
    what DryDocs put in the zone, never everything an operator keeps beside it.
    ``internal-local/`` holds 200-plus files this command cannot restore, so the
    zone is declared to keep the SYSTEM out, not to mark the directory
    disposable. A guard that read `rebuild:` as "safe to delete" would be worse
    than no guard.
    """
    missing = [z.id for z in dz.load_zones() if z.base == dz.BASE_REPO and not z.rebuild]
    assert not missing, (
        f"in-tree zone(s) with no `rebuild:` — {missing}. Declare the command "
        "that recreates the contents, or move the zone out of the tree."
    )


def test_the_credential_path_the_code_uses_falls_inside_its_declared_zone(monkeypatch) -> None:
    """The declaration cannot drift from the module that owns the path.

    ``credentials_path()`` is the authority on where the file lives; the zone is
    the declaration of where the system may not write. This is the G81
    helper-agreement idiom applied to a path whose owner is not a ``data_root``
    helper. The variable is cleared first: with it SET the operator has moved the
    file outside the declaration's reach on purpose, which the zone's note records
    as a limit rather than pretending to follow.
    """
    from drydocs_api.credentials import PATH_ENV_VAR, credentials_path

    monkeypatch.delenv(PATH_ENV_VAR, raising=False)
    zone = next(z for z in dz.load_zones() if z.id == "console-credentials")
    assert dz._contains(zone.path, credentials_path()), (
        f"credentials_path() resolves to {credentials_path()}, which is outside "
        f"the declared zone {zone.path} — one of the two moved and the other did not."
    )


def test_the_credential_zone_is_read_so_nothing_may_create_under_it(monkeypatch) -> None:
    """READ means the SYSTEM may never write, and the operator's hand is not the
    system. Proven against the create-capable public helper, the one G81's
    reconstruction found aimed at a hand-drop folder."""
    from drydocs_core import data_root

    zone = next(z for z in dz.load_zones() if z.id == "console-credentials")
    assert zone.mode == dz.READ
    assert zone.creatable is False
    # The runtime refusal — the leg that sees a path handed in at call time,
    # which is how the incident happened with every declaration correct.
    hit = dz.read_zone_containing(zone.path / "console-credentials.json")
    assert hit is not None and hit.id == zone.id
    nested = dz.read_zone_containing(zone.path / "deepdoc" / "anything")
    assert nested is not None and nested.id == zone.id
    # And the runtime refusal every write site calls names it rather than
    # failing anonymously — the G81 (c) rule that a violation names both ends.
    with pytest.raises(Exception, match="console-credentials"):
        data_root.refuse_write_into_read_zone(zone.path / "out", action="create")


def test_a_write_inside_the_in_tree_read_zone_is_caught(tmp_path: Path) -> None:
    """PROOF OF FAIL for the new base: the invariant is not base-aware, and it
    must not become so — a repo-based read zone protects exactly as much as a
    data_root one.

    The fixture path is deliberately NOT the real zone's name. A synthetic
    declaration under tmp_path proves the shape without writing a literal that
    ``test_skip_guard_policy.py`` reads as a real gitignored asset this file
    opens — and that policy is right to flag it, because a skip guard here would
    be a lie that let these assertions silently vanish on a fresh clone.
    """
    read = dz.DataZone(
        id="machine-local",
        mode=dz.READ,
        base=dz.BASE_REPO,
        path_spec="machine-local/",
        path=tmp_path / "machine-local",
        helper=None,
        env=None,
        note="",
        rebuild="a command",
    )
    write = dz.DataZone(
        id="output",
        mode=dz.WRITE,
        base=dz.BASE_REPO,
        path_spec="machine-local/out/",
        path=tmp_path / "machine-local" / "out",
        helper=None,
        env=None,
        note="",
    )
    found = dz.overlaps((write, read))
    assert len(found) == 1
    assert "is INSIDE" in found[0]
    assert str(read.path) in found[0] and str(write.path) in found[0]
