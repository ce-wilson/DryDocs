"""The binding table: how a registered source's carrier is REACHED (G125; ADR 0017).

WHY THIS MODULE EXISTS. Half the location problem was already solved well —
``acquisition.mode: manual`` rows name a ``drop_dir``, :mod:`landing_zones`
resolves it, and a guard enforces where it may live. The other half had no owner:
fifteen ``automated`` rows declared no binding at all, their system rows carrying
``locator.service: ~`` and a comment, and nothing resolves a comment. So
``drydocs landing-zones --check`` reported a clean run over the rows it knew about
and said nothing about the rows it did not. **A check that silently covers half
its subject reads as coverage** — that is the defect, not the count.

THE GRAIN IS THE CARRIER (ADR 0017 clause 2 as amended 2026-08-30). One profile
per connection carrier, inherited by every dataset beneath it. Not per origin:
``origin: controlm`` spans three systems, so a per-origin row cannot bind to one
connection, and ``system: psgmgr`` carries three origins, so keying per origin
re-fragments the connection the table exists to share.

THE REPORT IS TYPED, AND ITS SCOPE IS RULED (ADR 0017 clause 7). Three rules, each
closing a way this check could go back to lying:

1. **Configured on this machine only.** A binding whose variables are unset here
   is :data:`NOT_CONFIGURED_HERE` — a distinct verdict, never a failure. The two
   machines hold different subsets, so scoring the other machine's binding red
   would make the check noise, and noise is how the original coverage lie
   survived. Every report names the venue it was produced on (J18 as a return
   value rather than a footnote).
2. **It starts at the REGISTRATION, never on the config side of the wall.** Side
   (A) is ``.env``. Nothing here asserts a variable holds a *correct* host and
   nothing probes a credential. The walk begins at a registered row, side (B),
   and runs downstream to the configured points as defined.
3. **It stops at the first stage not yet built, and names it.**
   :data:`NOT_BUILT` is a third verdict class, distinct from both reachable and
   broken. Most of the registry is mid-lifecycle by design — N12 clause (f)
   already rules ``mode: manual`` is the expected first state and never a defect —
   so scoring unbuilt stages as failures would be wrong about the majority of
   rows.

Nothing here opens a socket. Reachability in this module means "every variable
this binding references resolves here", which is the strongest claim that can be
made without probing side (A). An actual dial-out belongs to the adapter that
owns the protocol, and it reports through the same :class:`BindingReport`.
"""

from __future__ import annotations

import platform
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from drydocs_core.env_refs import (
    EnvRefError,
    UnsetVariableError,
    expand,
    is_reference,
)
from drydocs_core.repo_paths import repo_root

_REPO_ROOT = repo_root(Path(__file__).resolve().parent.parent)

#: Verdicts. Deliberately not a bool: the whole point of ADR 0017 clause 7 is
#: that "not configured here" and "not built yet" are STATES, not failures, and a
#: boolean cannot say so.
CONFIGURED: Final = "configured"
NOT_CONFIGURED_HERE: Final = "not-configured-on-this-machine"
DECLARED_UNCONFIGURED: Final = "declared-no-variables"
NOT_BUILT: Final = "not-built-yet"
BROKEN: Final = "broken"
VERDICTS: Final = (CONFIGURED, NOT_CONFIGURED_HERE, DECLARED_UNCONFIGURED, NOT_BUILT, BROKEN)

#: The downstream walk, in order. The check starts at (B) `registered` and stops
#: at the first stage that is not built.
STAGES: Final = ("registered", "bound", "configured", "adapter", "loaded")


class BindingError(RuntimeError):
    """A binding declaration is malformed. Never raised for an UNSET variable."""


@dataclass(frozen=True)
class StageReport:
    """One stage of the downstream walk.

    ``mitigation`` exists because a report that says what failed and not what to
    do about it sends the reader back to the source. DataHub's
    ``CapabilityReport`` carries the same three fields for the same reason.
    """

    stage: str
    capable: bool
    detail: str = ""
    mitigation: str = ""


@dataclass(frozen=True)
class ConnectionProfile:
    """A named connection, referenced by registry rows. Holds variable NAMES only."""

    id: str
    carrier: str
    platform: str
    classification: str
    env: dict[str, str]
    serves: int
    note: str
    status: str = ""

    @property
    def variables(self) -> tuple[str, ...]:
        """The variable names this profile references, in declaration order."""
        out: list[str] = []
        for ref in self.env.values():
            raw = ref.strip()
            if raw.startswith("${") and raw.endswith("}"):
                out.append(raw[2:-1])
        return tuple(out)


@dataclass(frozen=True)
class UnboundCarrier:
    """A carrier with no binding, and the declared reason it has none."""

    carrier: str
    reason: str


@dataclass(frozen=True)
class BindingReport:
    """What a binding can actually do, on THIS machine, right now."""

    carrier: str
    profile_id: str
    verdict: str
    venue: str
    stages: tuple[StageReport, ...]
    unset: tuple[str, ...] = ()
    datasets: int = 0

    @property
    def stopped_at(self) -> str:
        """The first stage that is not capable, or ``""`` when all are."""
        for stage in self.stages:
            if not stage.capable:
                return stage.stage
        return ""

    @property
    def is_failure(self) -> bool:
        """ONLY ``broken`` is a failure.

        Not-configured-here and not-built-yet are states. This property is what
        keeps ``--check`` from reporting the other machine's subset, and the
        registry's own mid-lifecycle majority, as defects.
        """
        return self.verdict == BROKEN


def venue() -> str:
    """The machine a report was produced on (J18 as a return value)."""
    return platform.node() or "unknown-host"


def _doc(path: Path | None = None) -> dict[str, Any]:
    import yaml

    target = path or (_REPO_ROOT / "config" / "source-bindings.yaml")
    return yaml.safe_load(target.read_text(encoding="utf-8")) or {}


def load_profiles(path: Path | None = None) -> tuple[ConnectionProfile, ...]:
    """Every declared profile, in file order.

    Raises :class:`BindingError` when an ``env:`` entry is not a bare ``${NAME}``
    reference — a literal value in a binding is the publish-boundary defect this
    file exists to prevent, so it fails at load rather than at use.
    """
    out: list[ConnectionProfile] = []
    for row in _doc(path).get("profiles") or []:
        env = dict(row.get("env") or {})
        pid = row.get("id", "<no-id>")
        for key, ref in env.items():
            if not is_reference(str(ref)):
                raise BindingError(
                    f"profile {pid!r} field {key!r}: {ref!r} is not a ${{NAME}} reference. "
                    "A binding names variables and never holds a host, service name, SID "
                    "or credential (CLAUDE.md §3, ADR 0017 clause 3)."
                )
        out.append(
            ConnectionProfile(
                id=pid,
                carrier=row.get("carrier", ""),
                platform=row.get("platform", ""),
                classification=row.get("classification", ""),
                env=env,
                serves=int(row.get("serves") or 0),
                note=(row.get("note") or "").strip(),
                status=row.get("status", "") or "",
            )
        )
    return tuple(out)


def load_unbound(path: Path | None = None) -> tuple[UnboundCarrier, ...]:
    """Every carrier declared to have no binding, with its reason."""
    return tuple(
        UnboundCarrier(carrier=row.get("carrier", ""), reason=(row.get("reason") or "").strip())
        for row in _doc(path).get("unbound") or []
    )


def profile_for(carrier: str, path: Path | None = None) -> ConnectionProfile | None:
    """The profile bound to ``carrier``, or ``None``."""
    for prof in load_profiles(path):
        if prof.carrier == carrier:
            return prof
    return None


def _dataset_counts(registry_path: Path | None = None) -> dict[str, int]:
    import yaml

    target = registry_path or (_REPO_ROOT / "config" / "source-registry.yaml")
    doc = yaml.safe_load(target.read_text(encoding="utf-8")) or {}
    counts: dict[str, int] = {}
    for row in doc.get("datasets") or []:
        if (row.get("acquisition") or {}).get("mode") == "automated":
            sid = row.get("system") or ""
            counts[sid] = counts.get(sid, 0) + 1
    return counts


def report(
    profile: ConnectionProfile,
    *,
    datasets: int = 0,
    adapter_built: bool = True,
    loaded: bool = False,
) -> BindingReport:
    """Walk one binding downstream and report how far it reaches.

    The walk STARTS at ``registered`` — side (B) — and never inspects side (A).
    ``adapter_built`` and ``loaded`` are supplied by the caller because they are
    facts about the pipeline rather than about the binding; the load state is the
    one the load-map surface already renders, so the check and the rendered view
    answer with the same fact rather than two.
    """
    stages: list[StageReport] = [
        StageReport("registered", True, f"{datasets} automated dataset(s) on this carrier")
    ]
    stages.append(StageReport("bound", True, f"profile {profile.id!r}"))

    if not profile.env:
        stages.append(
            StageReport(
                "configured",
                False,
                "the profile declares no variables yet",
                "declare an env: block here when an account exists on this machine",
            )
        )
        return BindingReport(
            carrier=profile.carrier,
            profile_id=profile.id,
            verdict=DECLARED_UNCONFIGURED,
            venue=venue(),
            stages=tuple(stages),
            datasets=datasets,
        )

    unset: list[str] = []
    broken: list[str] = []
    for key, ref in profile.env.items():
        try:
            expand(str(ref), where=f"profile {profile.id!r} field {key!r}")
        except UnsetVariableError:
            unset.append(str(ref).strip()[2:-1])
        except EnvRefError as exc:
            broken.append(str(exc))

    if broken:
        stages.append(StageReport("configured", False, "; ".join(broken), "fix the declaration"))
        return BindingReport(
            carrier=profile.carrier,
            profile_id=profile.id,
            verdict=BROKEN,
            venue=venue(),
            stages=tuple(stages),
            unset=tuple(unset),
            datasets=datasets,
        )

    if unset:
        stages.append(
            StageReport(
                "configured",
                False,
                f"unset here: {', '.join(unset)}",
                "set them in your machine-local .env, or ignore this row -- a binding "
                "the other machine configures is not a defect here",
            )
        )
        return BindingReport(
            carrier=profile.carrier,
            profile_id=profile.id,
            verdict=NOT_CONFIGURED_HERE,
            venue=venue(),
            stages=tuple(stages),
            unset=tuple(unset),
            datasets=datasets,
        )

    stages.append(
        StageReport("configured", True, f"{len(profile.env)} variable(s) resolve on this machine")
    )
    if not adapter_built:
        stages.append(
            StageReport("adapter", False, "no adapter reads this carrier yet", "build the adapter")
        )
        return BindingReport(
            carrier=profile.carrier,
            profile_id=profile.id,
            verdict=NOT_BUILT,
            venue=venue(),
            stages=tuple(stages),
            datasets=datasets,
        )
    stages.append(StageReport("adapter", True))
    if not loaded:
        stages.append(
            StageReport("loaded", False, "nothing has loaded from this carrier yet", "run the load")
        )
        return BindingReport(
            carrier=profile.carrier,
            profile_id=profile.id,
            verdict=NOT_BUILT,
            venue=venue(),
            stages=tuple(stages),
            datasets=datasets,
        )
    stages.append(StageReport("loaded", True))
    return BindingReport(
        carrier=profile.carrier,
        profile_id=profile.id,
        verdict=CONFIGURED,
        venue=venue(),
        stages=tuple(stages),
        datasets=datasets,
    )


def reports(
    profiles: Iterable[ConnectionProfile] | None = None,
    registry_path: Path | None = None,
) -> tuple[BindingReport, ...]:
    """One report per declared profile, in file order."""
    counts = _dataset_counts(registry_path)
    return tuple(
        report(p, datasets=counts.get(p.carrier, 0))
        for p in (profiles if profiles is not None else load_profiles())
    )
