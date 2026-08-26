"""Runtime consumer for ``config/crosswalks/*.yaml`` — native term -> baseline concept.

ADR 0008 rule 3, and the reason this module exists at all: the crosswalks were
GATE-CONFIRMED data (autosys-crosswalk / airflow-crosswalk, both signed off
2026-07-14) **with no runtime reader**. A ``fidelity: no-equivalent`` row was a
warning in prose that nothing could enforce, which is precisely the drift
``external/orchestration/autosys/README.md`` warns about: a second orchestrator
arrives, an unmapped concept gets quietly rendered as the nearest Control-M
label, and the graph now asserts something no gate ruled.

So :func:`resolve` REFUSES rather than approximates. Three outcomes, and the
middle one is the point:

  ``fidelity: exact``        -> resolves; the baseline concept is the same thing
  ``fidelity: approximate``  -> resolves, and the caller is TOLD it is lossy via
                               ``Mapping.fidelity``; it is never silently exact
  ``fidelity: no-equivalent``-> raises :class:`NoEquivalentError`. There is no
                               "closest match" fallback, deliberately — the
                               concept routes to ``ontology-mapper`` and the
                               HITL gate, which is a human decision, not a
                               default this module may pick.

Pure config layer: no Neo4j, no graph writes, no I/O beyond reading the
committed YAML. Loading is memoized per path so the parse cost is paid once.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import yaml

from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parents[2])
DEFAULT_CROSSWALK_DIR = _REPO_ROOT / "config" / "crosswalks"

SCHEMA_ID = "drydocs.crosswalk.v1"

#: Sibling crosswalk kinds that share ``config/crosswalks/`` but are NOT
#: orchestrator crosswalks — e.g. the CDO vocabulary crosswalk (backlog W1),
#: which maps ontology terms to standard vocabularies and has its own guards.
#: The directory scan skips these deliberately; any OTHER schema id still
#: fails loudly, so a typo'd orchestrator crosswalk cannot vanish silently.
SIBLING_SCHEMA_IDS: frozenset[str] = frozenset({"drydocs.vocab-crosswalk.v1"})

#: The fidelity vocabulary. A row carrying anything else is a malformed file,
#: not a new tier — adding one is a gate decision, so it fails loudly here.
FIDELITIES: frozenset[str] = frozenset({"exact", "approximate", "no-equivalent"})

#: Fidelities a caller may act on. ``no-equivalent`` is deliberately absent.
RESOLVABLE: frozenset[str] = frozenset({"exact", "approximate"})


class CrosswalkError(RuntimeError):
    """A crosswalk file is malformed, or names an unknown fidelity."""


class UnknownOrchestratorError(KeyError):
    """No confirmed crosswalk is registered for that orchestrator."""


class UnknownConceptError(KeyError):
    """The orchestrator has a crosswalk, but no row for that native term."""


class NoEquivalentError(RuntimeError):
    """The row exists and says the baseline has NO equivalent.

    Raised rather than returned so a caller cannot treat it as a mapping by
    forgetting to check a flag. Route the concept to ``ontology-mapper`` and the
    HITL gate; do not pick the nearest label.
    """


@dataclass(frozen=True)
class Mapping:
    """One resolved native -> baseline row."""

    orchestrator: str
    native: str
    baseline: str
    node: str | None
    fidelity: str
    status: str
    note: str | None = None

    @property
    def is_lossy(self) -> bool:
        """True when the mapping holds but loses information (``approximate``)."""
        return self.fidelity == "approximate"


@dataclass(frozen=True)
class Crosswalk:
    """One orchestrator's confirmed crosswalk to the BMC Control-M baseline."""

    id: str
    orchestrator: str
    baseline: str
    status: str
    rows: tuple[Mapping, ...]
    path: Path | None = None

    @property
    def confirmed(self) -> bool:
        return self.status == "confirmed"

    def fidelity_counts(self) -> dict[str, int]:
        counts = {f: 0 for f in sorted(FIDELITIES)}
        for row in self.rows:
            counts[row.fidelity] += 1
        return counts

    def no_equivalents(self) -> tuple[Mapping, ...]:
        """Rows the baseline cannot express — the ontology-mapper queue."""
        return tuple(r for r in self.rows if r.fidelity == "no-equivalent")


def _parse(doc: dict, path: Path | None) -> Crosswalk:
    where = path.name if path else "<dict>"
    if doc.get("schema") != SCHEMA_ID:
        raise CrosswalkError(f"{where}: schema must be {SCHEMA_ID!r}, got {doc.get('schema')!r}")
    orchestrator = doc.get("orchestrator")
    if not orchestrator:
        raise CrosswalkError(f"{where}: must declare an `orchestrator:`")
    raw_rows = doc.get("rows")
    if not isinstance(raw_rows, list) or not raw_rows:
        raise CrosswalkError(f"{where}: must contain a non-empty `rows:` list")

    rows: list[Mapping] = []
    seen: set[str] = set()
    for raw in raw_rows:
        if not isinstance(raw, dict):
            raise CrosswalkError(f"{where}: malformed row entry: {raw!r}")
        native = raw.get("native")
        if not native:
            raise CrosswalkError(f"{where}: row {raw.get('n')} has no `native:` term")
        fidelity = raw.get("fidelity")
        if fidelity not in FIDELITIES:
            raise CrosswalkError(
                f"{where}: row {raw.get('n')} fidelity {fidelity!r} is not one of "
                f"{sorted(FIDELITIES)} — a new tier is a gate decision, not a typo"
            )
        key = _key(native)
        if key in seen:
            raise CrosswalkError(f"{where}: duplicate native term {native!r}")
        seen.add(key)
        rows.append(
            Mapping(
                orchestrator=orchestrator,
                native=native,
                baseline=raw.get("baseline") or "",
                node=raw.get("node"),
                fidelity=fidelity,
                status=raw.get("status") or "proposed",
                note=raw.get("note"),
            )
        )
    return Crosswalk(
        id=doc.get("id") or where,
        orchestrator=orchestrator,
        baseline=doc.get("baseline") or "bmc-controlm",
        status=doc.get("status") or "proposed",
        rows=tuple(rows),
        path=path,
    )


def _key(native: str) -> str:
    """Match key for a native term.

    Rows read like ``Job (`insert_job: <name> job_type: c`)`` — a human label
    plus its literal syntax. Callers hold the label, so the key is the text
    before the parenthetical, lowercased.
    """
    head = native.split("(", 1)[0]
    return " ".join(head.split()).strip().lower()


def load_crosswalk(path: str | Path) -> Crosswalk:
    """Load and validate one crosswalk file at an explicit path."""
    path = Path(path)
    if not path.exists():
        raise CrosswalkError(f"crosswalk file not found: {path}")
    return _parse(yaml.safe_load(path.read_text(encoding="utf-8")) or {}, path)


def load_crosswalks(directory: str | Path = DEFAULT_CROSSWALK_DIR) -> tuple[Crosswalk, ...]:
    """Every orchestrator crosswalk in *directory*, in sorted filename order.

    Files declaring a recognized sibling schema (:data:`SIBLING_SCHEMA_IDS`)
    are skipped — they are not orchestrator crosswalks and have their own
    consumers/guards. An unknown schema still raises via :func:`_parse`.
    """
    directory = Path(directory)
    if not directory.is_dir():
        raise CrosswalkError(f"crosswalk directory not found: {directory}")
    walks: list[Crosswalk] = []
    for p in sorted(directory.glob("*.yaml")):
        doc = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
        if doc.get("schema") in SIBLING_SCHEMA_IDS:
            continue
        walks.append(_parse(doc, p))
    return tuple(walks)


@lru_cache(maxsize=8)
def _registry(directory: str) -> dict[str, Crosswalk]:
    return {cw.orchestrator: cw for cw in load_crosswalks(directory)}


def orchestrators(directory: str | Path = DEFAULT_CROSSWALK_DIR) -> tuple[str, ...]:
    """Orchestrators with a crosswalk on disk, confirmed or not."""
    return tuple(sorted(_registry(str(directory))))


def resolve(
    native: str,
    orchestrator: str,
    *,
    directory: str | Path = DEFAULT_CROSSWALK_DIR,
    require_confirmed: bool = True,
) -> Mapping:
    """Resolve a native term to its baseline concept.

    Raises :class:`NoEquivalentError` when the crosswalk says the baseline cannot
    express the concept — never a nearest-match fallback (ADR 0008 rule 3).
    ``require_confirmed`` keeps a ``status: proposed`` crosswalk out of runtime
    use: proposed rows are a gate's INPUT, not a mapping anything may act on.
    """
    registry = _registry(str(directory))
    cw = registry.get(orchestrator)
    if cw is None:
        raise UnknownOrchestratorError(
            f"no crosswalk for orchestrator {orchestrator!r} "
            f"(have: {', '.join(sorted(registry)) or 'none'})"
        )
    if require_confirmed and not cw.confirmed:
        raise CrosswalkError(
            f"crosswalk {cw.id!r} is status {cw.status!r} — a proposed crosswalk is a "
            "gate's input, not a runtime mapping. Pass require_confirmed=False only "
            "for gate tooling that is reviewing it."
        )
    key = _key(native)
    for row in cw.rows:
        if _key(row.native) == key:
            if row.fidelity == "no-equivalent":
                raise NoEquivalentError(
                    f"{orchestrator}: {native!r} has NO baseline equivalent "
                    f"({row.note or 'see the crosswalk row'}). Route it to "
                    "ontology-mapper and the HITL gate — do not map it to the "
                    "nearest Control-M label."
                )
            return row
    raise UnknownConceptError(f"{orchestrator}: no crosswalk row for native term {native!r}")


def unmappable(
    orchestrator: str,
    *,
    directory: str | Path = DEFAULT_CROSSWALK_DIR,
) -> tuple[Mapping, ...]:
    """The orchestrator's ``no-equivalent`` rows — the ontology-mapper queue."""
    registry = _registry(str(directory))
    cw = registry.get(orchestrator)
    if cw is None:
        raise UnknownOrchestratorError(f"no crosswalk for orchestrator {orchestrator!r}")
    return cw.no_equivalents()


def iter_mappings(
    directory: str | Path = DEFAULT_CROSSWALK_DIR,
) -> Iterable[Mapping]:
    """Every row across every crosswalk, for reporting and guards."""
    for cw in load_crosswalks(directory):
        yield from cw.rows
