"""V1 — every module in the registry maps to exactly ONE runbook state.

The problem this closes: on 2026-08-04 the mapping-store runbook was found stale
in two directions at once — it had been missing K9's `app_code_mapping` table
since the day before, and S4 had just invalidated its "nothing here can lose
data" safety rule. Neither was caught by anything; both were caught by a person
asking "is the runbook current?". A question you have to remember to ask is not
a control.

So: `modules:` in backlog.yaml is the census, and every entry lands in exactly
one of three states, none silently absent.

* **COVERED** — a governed ``docs/design/*-runbook.md`` names the module in its
  front matter. Naming it in the FRONT MATTER (not inferred from the filename)
  is the point: coverage has to be a claim the document makes about itself, or
  a rename quietly breaks the map.
* **EXEMPT** — with a reason per entry. Work areas are exempt by rule: they are
  captures and registries, not operable components. Placeholders are exempt
  while they have nothing to operate — and that condition is re-checked here,
  not trusted (see the docmeta note below).
* **RUNBOOK_PENDING** — a real module awaiting authorship. Frozen and
  SHRINK-ONLY, the N2 ``LEDGER_PENDING`` idiom: a module that gains a runbook
  must leave this list, or the test fails. The list can only get smaller.

Runbooks get their own disposition map, because "operates part of a module" and
"IS the module's runbook" are different claims and conflating them is how a
module looks covered while most of it is undocumented.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

REPO_ROOT = Path(__file__).resolve().parents[2]
BACKLOG = REPO_ROOT / "docs" / "restructure" / "backlog.yaml"
DESIGN_DIR = REPO_ROOT / "docs" / "design"

pytestmark = pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")

#: Exempt from module-runbook coverage, with the reason. Ruled at V1, 2026-08-04.
MODULE_EXEMPT: dict[str, str] = {
    # ── Work areas, exempt BY RULE (V1 acceptance). These are captures,
    # registries and prose — there is no service to start, no chain to run, and
    # no failure mode an operator diagnoses at 3am. Their operating procedure is
    # CLAUDE.md and the skills, not a runbook.
    "reference": "work area — external vendor/standards captures, no operable component",
    "taxonomy": "work area — config/taxonomy/ captures, no operable component",
    "ontology": "work area — schema + vocabulary registries, no operable component",
    "config": "work area — precedence/registries/crosswalks, no operable component",
    "graph-infra": (
        "work area — Neo4j topology and provisioning. The operable half is covered by "
        "drydocs-startup-refresh-runbook.md (container, provisioning, ingest), which is "
        "SYSTEM-level rather than a module runbook — see RUNBOOK_DISPOSITION"
    ),
    "docs": "work area — plans, ADRs, process docs, rituals; no operable component",
    # ── Placeholders: nothing to operate yet. RE-CHECKED, not inherited —
    # drydocs-docmeta was on this list in V1's own acceptance and has since been
    # BUILT (Q6, ADR 0006: connectors, cleaner, manifest, policy, registry,
    # tokenizer + live CLI verbs), so it moved to RUNBOOK_PENDING below. That is
    # the "if still placeholder" clause doing its job.
    "drydocs-plan": (
        "placeholder — no package. The board renderer is scripts/render_board.py, "
        "operated by the CLAUDE.md §0 session ritual, not by a module runbook"
    ),
    "drydocs-deepdoc": (
        "placeholder — 3 files / ~86 lines of seed code, no CLI verb and no importer "
        "anywhere in drydocs/ or drydocs_core/, so there is no operable surface yet. "
        "Moves to RUNBOOK_PENDING the moment a verb reaches it"
    ),
}

#: Real modules awaiting a runbook. FROZEN + SHRINK-ONLY (N2 LEDGER_PENDING
#: idiom): gaining a runbook removes the entry; nothing may be added here
#: without a backlog item that says who writes it.
RUNBOOK_PENDING: frozenset[str] = frozenset(
    {
        "drydocs-core",  # V2
        "drydocs-load",  # V3 — must rule its overlap with the system-level startup runbook
        "drydocs-review",  # V4
        "drydocs-docgen",  # V5
        "drydocs-lineage",  # V6 — two chain-scoped runbooks exist; neither covers the module
        "drydocs-remediation",  # V7
        "drydocs-agents",  # V9
        "drydocs-docmeta",  # BUILT at Q6; no V-item yet, so this list is where it is visible
    }
)

#: What each existing runbook actually operates, and whether that SATISFIES a
#: module. Ruled at V1, 2026-08-04. `satisfies` is the module it covers whole;
#: None means it is narrower than its module and does not discharge coverage.
RUNBOOK_DISPOSITION: dict[str, tuple[str | None, str, str]] = {
    "drydocs-api-runbook.md": (
        "drydocs-api",
        "drydocs-api",
        "V8 ruled AUTHOR-DISTINCT over extending the mapping-store runbook: that one "
        "scopes HTTP serving out in its own words, and the demo runbook covers one route "
        "of twenty-two. Extending either would have produced a document whose title no "
        "longer described it",
    ),
    "drydocs-web-console-runbook.md": (
        "drydocs-web",
        "drydocs-web",
        "the console IS the module; V10 audits its currency post-O35-O41 separately",
    ),
    "drydocs-mapping-store-runbook.md": (
        None,
        "drydocs-core",
        "operates ONE artifact of core (var/mapping.db) and says so — it scopes HTTP "
        "serving out explicitly. Core's config/env roots, schema provisioning, "
        "vocabulary registry and run log are all outside it (V2's scope)",
    ),
    "drydocs-mapping-demo-runbook.md": (
        None,
        "drydocs-api",
        "operates the /demo page only -- one route of twenty-two -- not the mappings API, "
        "the draft/promote surfaces or the server itself. V8 RULED (2026-08-04): author "
        "drydocs-api-runbook.md distinct rather than widen this one or the mapping-store "
        "runbook; both stay deliberately narrower than the module",
    ),
    "drydocs-lineage-mac-runbook.md": (
        None,
        "drydocs-lineage",
        "CHAIN-scoped: one lineage chain (MAC), not the module's operate surface. V6 "
        "indexes it rather than being discharged by it",
    ),
    "drydocs-cmdline-resolution-runbook.md": (
        None,
        "drydocs-lineage",
        "CHAIN-scoped: the G46-G48 cmd-line resolution chain. Same ruling as lineage-mac",
    ),
    "drydocs-startup-refresh-runbook.md": (
        None,
        "drydocs-load",
        "SYSTEM-level: container, provisioning and sample ingest ACROSS modules. It is "
        "not drydocs-load's module runbook, and V3's own title says it must rule the "
        "overlap rather than inherit it",
    ),
}

_FRONT_MATTER_MODULE = re.compile(r"^-\s+\*\*Module:\*\*\s*`?([a-z0-9-]+)`?", re.M)


def _modules() -> list[str]:
    return yaml.safe_load(BACKLOG.read_text(encoding="utf-8"))["modules"]


def _runbooks() -> dict[str, str]:
    return {p.name: p.read_text(encoding="utf-8") for p in sorted(DESIGN_DIR.glob("*-runbook.md"))}


def _covered() -> dict[str, str]:
    """module -> runbook filename, read from each runbook's own front matter."""
    out: dict[str, str] = {}
    for name, text in _runbooks().items():
        m = _FRONT_MATTER_MODULE.search(text)
        if m:
            out[m.group(1)] = name
    return out


def test_every_module_has_exactly_one_runbook_state() -> None:
    """The census. A module in two states is a contradiction; a module in none
    is the silent absence this test exists to make impossible."""
    covered = _covered()
    failures: list[str] = []
    for module in _modules():
        states = [
            name
            for name, hit in (
                ("COVERED", module in covered),
                ("EXEMPT", module in MODULE_EXEMPT),
                ("RUNBOOK_PENDING", module in RUNBOOK_PENDING),
            )
            if hit
        ]
        if len(states) != 1:
            failures.append(
                f"{module}: in {len(states)} states {states or '[]'} — expected exactly one. "
                "Add it to MODULE_EXEMPT with a reason, to RUNBOOK_PENDING with its V-item, "
                "or give a runbook a `- **Module:** <name>` front-matter line"
            )
    assert not failures, f"{len(failures)} module(s) unmapped:\n" + "\n".join(failures)


def test_exempt_entries_carry_a_reason() -> None:
    empty = [m for m, why in MODULE_EXEMPT.items() if not why.strip()]
    assert not empty, f"exempt without a reason (the reason IS the exemption): {empty}"


def test_pending_list_is_shrink_only() -> None:
    """N2's LEDGER_PENDING idiom: a module that gained a runbook must LEAVE the
    list. Without this the list becomes a place entries go to be forgotten."""
    covered = _covered()
    stale = sorted(RUNBOOK_PENDING & set(covered))
    assert not stale, (
        f"these modules now have a runbook and must be removed from RUNBOOK_PENDING: "
        f"{ {m: covered[m] for m in stale} }"
    )
    unknown = sorted(RUNBOOK_PENDING - set(_modules()))
    assert not unknown, f"RUNBOOK_PENDING names modules not in the registry: {unknown}"


def test_no_module_is_both_exempt_and_pending() -> None:
    overlap = sorted(set(MODULE_EXEMPT) & RUNBOOK_PENDING)
    assert not overlap, f"exempt AND pending is a contradiction: {overlap}"


def test_every_runbook_has_a_disposition() -> None:
    """A new runbook must be dispositioned, not silently assumed to cover
    something. This is the half that keeps the map honest as docs are added."""
    on_disk = set(_runbooks())
    undispositioned = sorted(on_disk - set(RUNBOOK_DISPOSITION))
    assert not undispositioned, (
        f"runbook(s) with no V1 disposition: {undispositioned} — record what each one "
        "operates and whether it SATISFIES a module or is narrower than one"
    )
    vanished = sorted(set(RUNBOOK_DISPOSITION) - on_disk)
    assert not vanished, f"disposition names a runbook that no longer exists: {vanished}"


def test_dispositions_agree_with_the_front_matter() -> None:
    """A runbook that SATISFIES a module must say so in its own front matter,
    and one that does not must not claim to."""
    failures: list[str] = []
    for name, text in _runbooks().items():
        satisfies, scope_module, _reason = RUNBOOK_DISPOSITION[name]
        declared = _FRONT_MATTER_MODULE.search(text)
        declared_module = declared.group(1) if declared else None
        if satisfies and declared_module != satisfies:
            failures.append(
                f"{name}: dispositioned as the runbook for {satisfies!r} but its front "
                f"matter declares {declared_module!r} — add `- **Module:** {satisfies}`"
            )
        if satisfies is None and declared_module is not None:
            failures.append(
                f"{name}: declares `Module: {declared_module}` but is dispositioned as "
                f"narrower than {scope_module!r} — a partial runbook must not claim module "
                "coverage (that is how a module looks covered while most of it is not)"
            )
        if scope_module not in _modules():
            failures.append(f"{name}: scoped to {scope_module!r}, not a registry module")
    assert not failures, "\n".join(failures)
