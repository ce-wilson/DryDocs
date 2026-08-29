"""Declared data zones with a MODE — the G81 non-overlap invariant.

THE INCIDENT (2026-08-11): an internal folder holding extracted CSV source data
was OVERWRITTEN. Recovered from backup, so nothing was permanently lost, but the
class fires again the moment the backup is restored to the same place. Every
other failure that week was a wrong READ; this one destroyed a source, and that
irreversibility is the whole reason this module exists.

WHAT WAS WRONG, measured rather than assumed (the full walk is
``docs/reviews/g81-data-path-reconstruction.md``): a path was whatever one of
twelve helpers in :mod:`drydocs_core.data_root` returned. Nothing distinguished a
folder the system OWNS from one a human DROPS INTO — that distinction lived only
in docstrings — so an overlap between them was invisible until it destroyed
something. Four existed when this module was written, including a create-capable
helper aimed EXACTLY at a hand-drop folder, and the root itself reachable through
a public arbitrary-parts function.

THE INVARIANT, and it is the defect in one sentence: **no write-mode path may
equal, contain, or be contained by a read-mode path.** Both directions. The
acceptance named only "equal or contain", but two of the four live findings ran
the other way (a write area nested inside a declared drop zone), so a guard in
only the named direction would have missed half of them.

WHERE THE TWO HALVES LIVE, and why it is two files rather than one:

* **read zones that are dataset drops** are already declared —
  ``config/source-registry.yaml`` ``acquisition.drop_dir`` (N12), resolved by
  :mod:`drydocs_core.landing_zones`. Re-declaring them here would create the
  drift this repo keeps killing.
* **everything the system owns** (write/scratch), plus read zones that are NOT
  dataset drops, are declared in ``config/data-zones.yaml``.

:func:`overlaps` JOINS the two sets, which is what makes the invariant a check on
reality rather than on one file's self-consistency.

Pure resolution: nothing here creates, moves or deletes a directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from drydocs_core.data_root import resolve_data_root
from drydocs_core.log_kinds import resolve_env_override
from drydocs_core.repo_paths import repo_root

READ = "read"
WRITE = "write"
SCRATCH = "scratch"
#: A zone's mode. ``read`` = source data the system may NEVER write; ``write`` =
#: outputs it owns and may rebuild; ``scratch`` = disposable working space.
MODES = (READ, WRITE, SCRATCH)

BASE_DATA_ROOT = "data_root"
BASE_HOME = "home"
#: In the working tree. The spelling is ``landing_zones.BASE_REPO`` deliberately:
#: the two declarations join in :func:`overlaps`, so a base meaning "the repo" in
#: one file and nothing in the other is a seam waiting to be misread (G126 (b)).
BASE_REPO = "repo"
BASES = (BASE_DATA_ROOT, BASE_HOME, BASE_REPO)

#: Modes whose helper may call mkdir. G81 (e): any path a ``create=True`` helper
#: may build is write-mode BY CONSTRUCTION, so the converse is enforced — a
#: read-mode zone must be reachable only through a helper that cannot create.
CREATABLE_MODES = (WRITE, SCRATCH)

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
ZONES_FILE = _REPO_ROOT / "config" / "data-zones.yaml"


class DataZoneError(RuntimeError):
    """A zone declaration that cannot be trusted — never a silent fallback."""


@dataclass(frozen=True)
class DataZone:
    """One declared zone, resolved to a real path."""

    id: str
    mode: str
    base: str
    path_spec: str
    path: Path
    helper: str | None
    env: str | None
    note: str
    #: How an operator rebuilds this zone's contents from nothing, for a zone
    #: that ``git clean -fdx`` can reach. ``None`` means "does not need one" —
    #: either the zone is outside the tree, or its contents are tracked. G126
    #: makes this the price of an in-tree untracked zone: not a blanket
    #: exception, a stated recovery path, checked by the guard.
    rebuild: str | None = None

    @property
    def creatable(self) -> bool:
        return self.mode in CREATABLE_MODES

    @property
    def inside_repo(self) -> bool:
        """True when the resolved zone sits under the repo working tree.

        The same property ``landing_zones.LandingZone`` exposes, and for the same
        reason: a ``data_root`` zone is safe because it is OUTSIDE the tree, and
        ``DRYDOCS_DATA_ROOT`` is env-settable, so someone will eventually point it
        at the checkout. Asserted on the RESOLVED path, never inferred from
        ``base``.
        """
        try:
            self.path.resolve().relative_to(_REPO_ROOT)
        except (ValueError, OSError):
            return False
        return True


@dataclass(frozen=True)
class ZoneState:
    """What is actually in a declared zone right now. Read-only, never creates."""

    zone: DataZone
    exists: bool
    file_count: int

    @property
    def empty(self) -> bool:
        return self.exists and self.file_count == 0


def inventory(zones: tuple[DataZone, ...] | None = None) -> tuple[ZoneState, ...]:
    """Present-or-absent plus a file count per declared zone.

    The read surface G109 gives ``drydocs landing-zones``. Mirrors
    ``landing_zones.inventory`` deliberately rather than sharing an
    implementation: the two declarations stay separate files on purpose (see this
    module's docstring), and a shared walker would be the seam through which they
    quietly become one. Never creates a directory — a doctor that repairs the
    tree it is inspecting reports health on damage it just hid.
    """
    import os

    out: list[ZoneState] = []
    for zone in zones if zones is not None else all_zones():
        exists = zone.path.is_dir()
        count = 0
        if exists:
            for _, _, files in os.walk(zone.path):
                count += len(files)
        out.append(ZoneState(zone=zone, exists=exists, file_count=count))
    return tuple(out)


def _resolve(base: str, spec: str, env: str | None = None) -> Path:
    """``base`` + ``spec``, unless ``env`` names a set-and-non-empty variable.

    A zone declaring ``env:`` (``run-logs`` does, per the ``home`` idiom) is
    overridable at runtime the same way the log root is — through
    :func:`drydocs_core.log_kinds.resolve_env_override`, reused rather than
    re-derived so the two resolvers cannot disagree on what "set" means (G111).
    """
    override = resolve_env_override(env)
    if override is not None:
        return override
    if base == BASE_HOME:
        return Path.home() / spec
    if base == BASE_DATA_ROOT:
        return resolve_data_root() / spec
    if base == BASE_REPO:
        return _REPO_ROOT / spec
    raise DataZoneError(f"unknown base {base!r} — declared: {sorted(BASES)}")


def load_zones(path: Path | None = None) -> tuple[DataZone, ...]:
    """Every zone in ``config/data-zones.yaml``, resolved and validated.

    Validation is here rather than only in the test so a consumer repo declaring
    its own zones gets the same protection from its OWN file. A malformed
    declaration RAISES — a zone the system cannot describe is exactly the state
    that let an overlap hide.
    """
    import yaml

    src = path or ZONES_FILE
    if not src.is_file():
        raise DataZoneError(f"data-zone declaration missing: {src}")
    doc = yaml.safe_load(src.read_text(encoding="utf-8")) or {}
    rows = doc.get("zones")
    if not rows:
        raise DataZoneError(
            f"{src} declares no zones — an empty declaration would make the "
            "non-overlap invariant vacuously true, which is the failure mode "
            "this whole item exists to close."
        )
    zones: list[DataZone] = []
    seen: set[str] = set()
    for row in rows:
        zid = str(row.get("id") or "").strip()
        if not zid:
            raise DataZoneError(f"{src}: a zone with no id")
        if zid in seen:
            raise DataZoneError(f"{src}: duplicate zone id {zid!r}")
        seen.add(zid)
        mode = str(row.get("mode") or "").strip()
        if mode not in MODES:
            raise DataZoneError(f"{src}: zone {zid!r} mode {mode!r} not in {list(MODES)}")
        base = str(row.get("base") or "").strip()
        if base not in BASES:
            raise DataZoneError(f"{src}: zone {zid!r} base {base!r} not in {list(BASES)}")
        spec = str(row.get("path") or "").strip()
        if not spec:
            raise DataZoneError(f"{src}: zone {zid!r} declares no path")
        helper = row.get("helper")
        env = str(row["env"]).strip() if row.get("env") else None
        zones.append(
            DataZone(
                id=zid,
                mode=mode,
                base=base,
                path_spec=spec,
                path=_resolve(base, spec, env),
                helper=str(helper).strip() if helper else None,
                env=env,
                note=str(row.get("note") or "").strip(),
                rebuild=str(row["rebuild"]).strip() if row.get("rebuild") else None,
            )
        )
    return tuple(zones)


def registry_read_zones(registry_path: Path | None = None) -> tuple[DataZone, ...]:
    """Dataset drop folders, as READ zones — the other half of the invariant.

    Read from ``config/source-registry.yaml`` via :mod:`drydocs_core.landing_zones`
    rather than copied here (N12 owns that declaration). Repo-based zones are
    included: a write landing inside ``docs/design/`` would be just as much a
    violation as one inside a data-root drop.
    """
    from drydocs_core.landing_zones import BASE_DATA_ROOT as LZ_DATA_ROOT
    from drydocs_core.landing_zones import manual_zones

    out: list[DataZone] = []
    for zone in manual_zones(registry_path):
        if not zone.base or not zone.drop_dir:
            continue  # named by the landing-zone guard; not this invariant's business
        out.append(
            DataZone(
                id=zone.source_id,
                mode=READ,
                base=BASE_DATA_ROOT if zone.base == LZ_DATA_ROOT else zone.base,
                path_spec=zone.drop_dir,
                path=zone.path,
                helper=None,
                env=None,
                note="declared in config/source-registry.yaml (acquisition.drop_dir, N12)",
            )
        )
    return tuple(out)


def all_zones(
    zones_path: Path | None = None, registry_path: Path | None = None
) -> tuple[DataZone, ...]:
    """The joined picture: declared zones + dataset drop zones."""
    return load_zones(zones_path) + registry_read_zones(registry_path)


def _contains(outer: Path, inner: Path) -> bool:
    """True when ``inner`` is ``outer`` or sits beneath it."""
    try:
        Path(inner).resolve().relative_to(Path(outer).resolve())
    except (ValueError, OSError):
        return False
    return True


def overlaps(zones: tuple[DataZone, ...] | None = None) -> tuple[str, ...]:
    """Every violation of the non-overlap invariant, NAMING BOTH PATHS.

    A violation is any write/scratch zone that EQUALS, CONTAINS, or IS CONTAINED
    BY a read zone. Both directions on purpose — see the module docstring; the
    rua pair that motivated this ran in the direction the acceptance did not
    name, so a one-directional check would have reported all-clear on half the
    live findings.

    Returns human-readable lines rather than a bool: a guard that says only
    "something overlaps" leaves the reader exactly where the twelve helpers did.
    """
    zs = all_zones() if zones is None else zones
    reads = [z for z in zs if z.mode == READ]
    writes = [z for z in zs if z.mode in CREATABLE_MODES]
    found: list[str] = []
    for w in writes:
        for r in reads:
            wp, rp = w.path, r.path
            if wp.resolve() == rp.resolve():
                relation = "EQUALS"
            elif _contains(rp, wp):
                relation = "is INSIDE"
            elif _contains(wp, rp):
                relation = "CONTAINS"
            else:
                continue
            found.append(f"{w.mode} zone {w.id!r} ({wp}) {relation} read zone {r.id!r} ({rp})")
    return tuple(sorted(found))


def zone_by_helper(helper_name: str) -> DataZone | None:
    """The declared zone a ``data_root`` helper implements, if any."""
    for zone in load_zones():
        if zone.helper == helper_name:
            return zone
    return None


def read_zone_containing(target: Path) -> DataZone | None:
    """The read zone ``target`` falls inside, if any — the RUNTIME check.

    The static invariant compares DECLARATIONS; it cannot see a path handed in at
    call time (``_unpack(unpack_dir=...)`` is the live example, and it is how the
    incident could happen with every declaration correct). This is what a write
    site calls before it writes.
    """
    for zone in all_zones():
        if zone.mode == READ and _contains(zone.path, target):
            return zone
    return None
