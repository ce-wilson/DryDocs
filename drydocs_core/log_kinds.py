"""The declared log KINDS — what the system writes, where, how loud, how long.

G105, ADR 0014 clause 1 as amended at the 2026-08-25 ruling. Before this, `kind`
was a filename convention rather than a code concept: three sites minted one and
none agreed (``run_log`` hardcoded ``load.``, ``llm_ledger`` hardcoded
``qa.graph_qa``, ``sql_run_log`` took an unvalidated ``base_name`` and wrote
``oracle.<ts>.log`` with no kind at all). Nothing could be configured per kind
while no declaration said what the kinds ARE.

THE NAMING RULE IS DERIVED HERE, NOT ASSERTED. :func:`log_filename` builds
``<kind>.<name>.<stamp>.<ext>`` from the kind's own ``rotation`` and ``format``,
so the per-day ledger is CONFORMING rather than excepted — which is how the
drafted clause's self-flagged weakness ("one exception in a naming rule is how
naming rules die") stops being a weakness.

Reads ``config/log-kinds.yaml``. Pure resolution: nothing here creates, moves or
deletes a directory, and nothing here configures logging — :mod:`drydocs.cli`
owns that, from these values.
"""

from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from drydocs_core.repo_paths import repo_root

PER_RUN = "per-run"
PER_DAY = "per-day"
#: Rotation decides the STAMP GRANULARITY, which is the whole of the naming rule
#: that varies between kinds.
ROTATIONS = (PER_RUN, PER_DAY)
_STAMP_FORMAT = {PER_RUN: "%Y%m%d-%H%M%S", PER_DAY: "%Y%m%d"}

FORMATS = ("log", "jsonl")

BASE_HOME = "home"
BASES = (BASE_HOME,)

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)
KINDS_FILE = _REPO_ROOT / "config" / "log-kinds.yaml"


class LogKindError(RuntimeError):
    """A declaration that cannot be trusted — never a silent fallback."""


@dataclass(frozen=True)
class LogKind:
    """One declared kind, with every field resolved against the defaults."""

    id: str
    level: str
    retention_days: int
    rotation: str
    format: str
    dir: str | None
    writer: str
    status: str
    note: str

    @property
    def planned(self) -> bool:
        """True for a kind declared before its writer exists (``api``, at G105)."""
        return self.status == "planned"

    def path(self, root: Path | None = None) -> Path:
        """The directory this kind writes into — the root, or its subdirectory."""
        base = root if root is not None else resolve_root()
        return base / self.dir if self.dir else base


def _doc(path: Path | None = None) -> dict[str, Any]:
    import yaml

    target = path or KINDS_FILE
    if not target.is_file():
        raise LogKindError(
            f"the log-kind declaration is missing: {target}. Every log path and "
            "level derives from it, so a missing file is a configuration error "
            "rather than a reason to fall back to a guess."
        )
    doc = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    if not doc.get("kinds"):
        raise LogKindError(f"{target} declares no kinds — an empty log map is never what was meant")
    return doc


def resolve_env_override(env_name: str | None) -> Path | None:
    """``<env_name>``, resolved as a path, when it names a set-and-non-empty
    environment variable — ``None`` otherwise.

    This is the ONE check both :func:`resolve_root` (the log root) and
    :func:`drydocs_core.data_zones._resolve` (any zone declaring ``env:``) run
    before falling back to their own default, factored out here so the two
    resolvers cannot drift apart on what "set" means (blank/whitespace-only
    counts as unset in both places, per G111).
    """
    if env_name and os.environ.get(env_name, "").strip():
        return Path(os.environ[env_name].strip())
    return None


def resolve_root(path: Path | None = None, *, default: Path | None = None) -> Path:
    """The one place the log root is resolved.

    ``DRYDOCS_LOGDIR`` wins, the legacy ``SPIDERP_LOGDIR`` still resolves for one
    deprecation cycle WITH A WARNING, and the declared default is the fallback —
    the exact order ``run_log`` has always used, preserved rather than replaced.

    One place, but not the only CALLER of the order: ``config/data-zones.yaml``'s
    ``run-logs`` zone also declares ``env: DRYDOCS_LOGDIR``, and
    ``data_zones._resolve()`` honors it (G111) by calling
    :func:`resolve_env_override` — the same primary-env check this function runs
    — rather than re-deriving it, so the log root and the ``run-logs`` zone
    cannot again report two different directories.
    """
    doc = _doc(path)
    root = doc.get("root") or {}
    env_name = root.get("env") or ""
    legacy = root.get("legacy_env") or ""

    override = resolve_env_override(env_name)
    if override is not None:
        return override
    if legacy and os.environ.get(legacy, "").strip():
        warnings.warn(
            f"{legacy} is deprecated and is honored for one more cycle — set "
            f"{env_name} instead (ADR 0014 clause 1; the removal trigger is the "
            "next port after that ADR was accepted).",
            DeprecationWarning,
            stacklevel=2,
        )
        return Path(os.environ[legacy].strip())

    if default is not None:
        # The caller's own default wins the LAST branch only. run_log passes
        # DEFAULT_LOGDIR, which is the identical path in production
        # (Path.home()/"logs"/"DryDocs" both ways) and is the seam the unit
        # conftest patches to keep the suite out of the developer's real log
        # directory. Resolving the declaration's literal here instead would send
        # every test that writes a run log into ~/logs/DryDocs -- the same class
        # of defect as a test resolving the real data root.
        return default
    base = root.get("base") or ""
    if base not in BASES:
        raise LogKindError(f"unknown root base {base!r} — declared: {sorted(BASES)}")
    return Path.home() / (root.get("path") or "")


def load_kinds(path: Path | None = None) -> tuple[LogKind, ...]:
    """Every declared kind, with defaults applied and the declaration validated.

    Validated here rather than only in the test so a consumer repo declaring its
    own kinds gets the same refusal — the ``data_zones.load_zones`` idiom.
    """
    doc = _doc(path)
    defaults = doc.get("defaults") or {}
    seen: set[str] = set()
    out: list[LogKind] = []
    for raw in doc["kinds"]:
        kind_id = str(raw.get("id") or "").strip()
        if not kind_id:
            raise LogKindError("a kind with no id — the id IS the filename segment")
        if kind_id in seen:
            raise LogKindError(f"duplicate kind id {kind_id!r}: two kinds cannot share a segment")
        seen.add(kind_id)

        merged = {**defaults, **{k: v for k, v in raw.items() if v is not None}}
        rotation = str(merged.get("rotation"))
        fmt = str(merged.get("format"))
        if rotation not in ROTATIONS:
            raise LogKindError(f"{kind_id}: unknown rotation {rotation!r} — declared: {ROTATIONS}")
        if fmt not in FORMATS:
            raise LogKindError(f"{kind_id}: unknown format {fmt!r} — declared: {FORMATS}")
        try:
            retention = int(merged.get("retention_days"))
        except (TypeError, ValueError) as exc:
            raise LogKindError(
                f"{kind_id}: retention_days must be a whole number of days, "
                f"got {merged.get('retention_days')!r}"
            ) from exc

        out.append(
            LogKind(
                id=kind_id,
                level=str(merged.get("level") or "INFO").upper(),
                retention_days=retention,
                rotation=rotation,
                format=fmt,
                dir=(str(merged["dir"]) if merged.get("dir") else None),
                writer=str(raw.get("writer") or ""),
                status=str(raw.get("status") or "active"),
                note=str(raw.get("note") or ""),
            )
        )
    return tuple(out)


def kind(kind_id: str, path: Path | None = None) -> LogKind:
    """One declared kind by id, or a refusal naming what IS declared.

    Never invents a kind from defaults: a writer using an undeclared id is the
    pre-G105 state (three sites, three conventions, nothing checkable), and
    quietly accepting it would restore exactly that.
    """
    for candidate in load_kinds(path):
        if candidate.id == kind_id:
            return candidate
    declared = sorted(k.id for k in load_kinds(path))
    raise LogKindError(
        f"undeclared log kind {kind_id!r} — declared: {declared}. Add it to "
        "config/log-kinds.yaml; a kind that exists only in code is the state G105 removed."
    )


def stamp_for(rotation: str, now: datetime | None = None) -> str:
    """The timestamp segment for a rotation — the only part of the rule that varies."""
    if rotation not in ROTATIONS:
        raise LogKindError(f"unknown rotation {rotation!r} — declared: {ROTATIONS}")
    return (now or datetime.now()).strftime(_STAMP_FORMAT[rotation])


def log_filename(
    kind_id: str, name: str, *, now: datetime | None = None, path: Path | None = None
) -> str:
    """``<kind>.<name>.<stamp>.<ext>``, DERIVED from the kind's declaration.

    ``name`` is free-form on purpose: ``code_snapshot.v1`` carries its own version
    segment, and a rule that spelled out the shape of ``name`` matched only 5 of
    86 real files.
    """
    declared = kind(kind_id, path)
    return f"{kind_id}.{name}.{stamp_for(declared.rotation, now)}.{declared.format}"
