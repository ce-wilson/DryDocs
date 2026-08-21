"""Resolve a load chain's inputs BEFORE the first write — explicit path or fail (G78).

THE DEFECT THIS CLOSES. A chain step whose input file was absent logged
"No sample for <step>; skipping" and the run reported SUCCESS; and the chain's
only input option defaulted to the bundled FIXTURE directory, so a run with no
arguments loaded synthetic rows into a real graph and called it done. Together:
not a failed load, a load that succeeded with the wrong data. Reproduced on both
sides (producer: the two SEAL fixtures the reference chain expects are GENERATED
per machine and were absent; company, 2026-08-11: the dev-team step dropped and
a real-data run loaded fixtures instead).

THE CONTRACT, copied up from the single-loader verb that already had it right
(``drydocs load <name> --csv <path>``: arbitrary path, no convention, no fixture
default, exit 2 rather than guess):

* (a) a missing REQUIRED input FAILS the chain, naming the file and the path
  searched — and it fails BEFORE any step writes, so a half-loaded chain cannot
  happen. A step is optional only when it is written down as such, never
  because its file happens to be absent.
* (b) two explicit modes, no default. FIXTURE mode (``--samples-dir``) reads the
  bundled ``<step>__sample.csv`` names from a directory the operator named.
  SOURCE mode (``--source <id>``) resolves the source's declared landing zone
  (``config/source-registry.yaml`` ``acquisition.drop_dir`` under
  ``DRYDOCS_DATA_ROOT`` — ADR 0012 / N12) and reads ``<step>.csv`` from it, so
  production data never has to be called ``*__sample.csv`` in a directory
  called ``samples``. A step whose effective source was not selected is
  reported as NOT SELECTED — a written-down skip the operator asked for, which
  is a different thing from a missing file.
* (c) the run summary states, per step, WHICH path it read and how many rows
  it loaded, so "it succeeded" is falsifiable at a glance.

Pure path resolution: nothing here opens a database.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path

from drydocs_core.landing_zones import LandingZone, manual_zones
from drydocs_core.source_registry import SourceRegistry

FIXTURE = "fixture"
SOURCE = "source"


@dataclass(frozen=True)
class ChainStep:
    """One step of a sequenced chain: (cli name, loader class, fixture file)."""

    name: str
    loader: type
    fixture_file: str
    #: written-down optionality (a). Default False: absence is a failure.
    optional: bool = False

    @property
    def source_file(self) -> str:
        """The file name a SOURCE-mode run reads from the landing zone."""
        return f"{self.name}.csv"


@dataclass(frozen=True)
class ResolvedInput:
    step: ChainStep
    mode: str  # FIXTURE | SOURCE
    path: Path
    source_id: str | None = None


@dataclass(frozen=True)
class SkippedStep:
    step: ChainStep
    reason: str


@dataclass
class ChainPlan:
    inputs: list[ResolvedInput] = field(default_factory=list)
    skipped: list[SkippedStep] = field(default_factory=list)


class MissingChainInputError(RuntimeError):
    """Raised BEFORE any write, naming every missing file and where it was sought."""

    def __init__(self, missing: Sequence[tuple[ChainStep, Path, str]]) -> None:
        self.missing = tuple(missing)
        lines = [
            f"  {step.name}: {path.name} not found — searched {path.parent} ({mode} mode)"
            for step, path, mode in missing
        ]
        super().__init__(
            "chain input(s) missing; nothing was loaded:\n"
            + "\n".join(lines)
            + "\nA required step never skips. Name the right --samples-dir (fixtures) or put the "
            "file in the source's declared landing zone (--source, config/source-registry.yaml "
            "acquisition.drop_dir). SEAL fixtures are generated per machine: "
            "scripts/build_seal_samples.py."
        )


class ChainModeError(RuntimeError):
    """No mode, or both modes, given — the chain refuses to guess."""


def _zone_index(registry_path: Path | None = None) -> dict[str, LandingZone]:
    return {z.source_id: z for z in manual_zones(registry_path)}


def resolve_chain_inputs(
    chain: Iterable[ChainStep],
    *,
    samples_dir: Path | None,
    sources: Sequence[str],
    registry: SourceRegistry,
    registry_path: Path | None = None,
) -> ChainPlan:
    """Decide every step's input up front. Raises :class:`ChainModeError` when
    the operator named no mode (or both), :class:`MissingChainInputError` when
    any required file is absent. Never touches the graph."""
    if samples_dir is None and not sources:
        raise ChainModeError(
            "no input named: pass --samples-dir <dir> for a FIXTURE run, or --source <id> "
            "(repeatable) for a run against declared landing zones. There is no default — a "
            "default would load fixtures into a real graph and report success."
        )
    if samples_dir is not None and sources:
        raise ChainModeError(
            "--samples-dir and --source are exclusive: fixtures or sources, not both"
        )

    plan = ChainPlan()
    missing: list[tuple[ChainStep, Path, str]] = []
    if samples_dir is not None:
        for step in chain:
            path = Path(samples_dir) / step.fixture_file
            if path.exists():
                plan.inputs.append(ResolvedInput(step, FIXTURE, path))
            elif step.optional:
                plan.skipped.append(
                    SkippedStep(step, f"optional; {path.name} absent in {path.parent}")
                )
            else:
                missing.append((step, path, FIXTURE))
    else:
        zones = _zone_index(registry_path)
        unknown = [s for s in sources if s not in zones]
        if unknown:
            raise ChainModeError(
                f"--source {unknown} is not a manual-acquisition dataset in the source registry "
                f"(declared zones: {sorted(zones)})"
            )
        wanted = set(sources)
        for step in chain:
            effective = registry.effective_source_id(step.loader.name, step.loader.source_id)
            if effective not in wanted:
                plan.skipped.append(
                    SkippedStep(step, f"not selected (binds to {effective or '<no source>'})")
                )
                continue
            path = zones[effective].path / step.source_file
            if path.exists():
                plan.inputs.append(ResolvedInput(step, SOURCE, path, source_id=effective))
            elif step.optional:
                plan.skipped.append(
                    SkippedStep(step, f"optional; {path.name} absent in {path.parent}")
                )
            else:
                missing.append((step, path, SOURCE))
    if missing:
        raise MissingChainInputError(missing)
    return plan


@dataclass
class StepResult:
    """(c) what one step actually read and loaded — the falsifiable line."""

    step: str
    mode: str
    path: str
    rows: int
    rejected: int
    source_id: str | None = None

    def as_row(self) -> tuple[str, ...]:
        return (
            self.step,
            self.mode if not self.source_id else f"{self.mode}:{self.source_id}",
            self.path,
            str(self.rows),
            str(self.rejected),
        )


def summary_lines(results: Sequence[StepResult], skipped: Sequence[SkippedStep]) -> list[str]:
    out = ["step | mode | path read | rows | rejected"]
    out += [" | ".join(r.as_row()) for r in results]
    out += [f"{s.step.name} | — | NOT LOADED: {s.reason} | 0 | 0" for s in skipped]
    return out
