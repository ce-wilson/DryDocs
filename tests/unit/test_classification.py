"""Enforce the sensitivity-classification axis (no Neo4j required).

Every ingested source must carry a `classification` from the controlled vocabulary
in config/classification.yaml plus a `source`; External sources must additionally
cite `source_url` + `captured_at`. This is the publish-boundary safety net — it fails
CI if a source is registered without a sensitivity label.
"""

from __future__ import annotations

from pathlib import Path

import pytest

try:
    import yaml

    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
CLASSIFICATION = CONFIG_DIR / "classification.yaml"
SOURCE_REGISTRY = CONFIG_DIR / "source-registry.yaml"
REFERENCE_REGISTRY = Path(__file__).resolve().parents[2] / "reference" / "REGISTRY.yaml"


def test_classification_file_exists() -> None:
    assert CLASSIFICATION.exists(), f"Missing controlled vocabulary: {CLASSIFICATION}"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_classification_vocabulary_shape() -> None:
    doc = yaml.safe_load(CLASSIFICATION.read_text(encoding="utf-8"))
    ids = {lvl["id"] for lvl in doc.get("levels", [])}
    assert ids == {
        "External",
        "Internal-Public",
        "Internal",
    }, (  # J23: Internal absorbs the former Internal-Confidential
        f"classification levels drifted: {ids}"
    )
    # publishable must be a bool on every level
    for lvl in doc["levels"]:
        assert isinstance(lvl.get("publishable"), bool), f"{lvl['id']} missing publishable bool"


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_every_source_is_classified() -> None:
    """v2 registry (gate source-registry-v2): every SYSTEM row carries a valid
    classification + name + the standing seal_id PLACEHOLDER (D1 amendment);
    every DATASET row joins to a classified system and names its artifact —
    the publish-boundary axis attaches at the system, datasets inherit.
    External systems additionally carry source_url + captured_at."""
    if not SOURCE_REGISTRY.exists():
        pytest.skip("source-registry.yaml not present")

    vocab = yaml.safe_load(CLASSIFICATION.read_text(encoding="utf-8"))
    valid = {lvl["id"] for lvl in vocab["levels"]}

    reg = yaml.safe_load(SOURCE_REGISTRY.read_text(encoding="utf-8"))
    failures: list[str] = []

    systems = {s.get("id"): s for s in reg.get("systems", [])}
    for sid, sys_row in systems.items():
        cls = sys_row.get("classification")
        if cls not in valid:
            failures.append(f"[system {sid}] classification '{cls}' not in {sorted(valid)}")
            continue
        if not sys_row.get("name"):
            failures.append(f"[system {sid}] missing required field 'name'")
        if "seal_id" not in sys_row:
            failures.append(
                f"[system {sid}] missing the standing seal_id PLACEHOLDER "
                "(D1 amendment — present on every committed system row)"
            )
        if cls == "External":
            for field in ("source_url", "captured_at"):
                if not sys_row.get(field):
                    failures.append(f"[system {sid}] External system missing '{field}'")

    for ds in reg.get("datasets", []):
        did = ds.get("id", "<no-id>")
        if ds.get("system") not in systems:
            failures.append(
                f"[dataset {did}] system '{ds.get('system')}' does not resolve "
                "to a registered system row (classification would be undefined)"
            )
        if not ds.get("artifact"):
            failures.append(f"[dataset {did}] missing required field 'artifact'")

    assert not failures, f"{len(failures)} classification error(s):\n" + "\n".join(failures)


@pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")
def test_reference_registry_is_external() -> None:
    """All Tier-1 reference material is External by definition — the registry must
    declare it, so the publish boundary can treat reference/ as publishable."""
    if not REFERENCE_REGISTRY.exists():
        pytest.skip("reference/REGISTRY.yaml not present")
    reg = yaml.safe_load(REFERENCE_REGISTRY.read_text(encoding="utf-8"))
    assert (
        reg.get("classification") == "External"
    ), "reference/REGISTRY.yaml must declare top-level `classification: External`"


# --------------------------------------------------------------------------- #
# J24 — the retired-tier regression guard
#
# `Internal-Confidential` was retired into `Internal` on 2026-07-31 (J23). Two
# things let it survive that collapse for a day, and both are guarded here:
#
#   1. drydocs_api holds its OWN copy of the vocabulary (the API is pure and
#      does not read config/ at import). Nothing compared the two, so the API
#      kept offering a level the config no longer defined — and two registered
#      specs kept carrying it, meaning a real export wrote a file prefixed
#      INTERNAL-CONFIDENTIAL__ with a banner naming a nonexistent tier.
#   2. Forward-looking specs (the UI type union, skill routing tables, gate
#      prompts) are read by humans and agents to decide what tier something
#      GETS, so a stale value there re-enters real code later.
#
# The token scan names its own scope ON PURPOSE. History legitimately records
# the retired tier — config/gate-log.md, signed-off gate prompts, `done`
# backlog close-notes, SDLC-Docs/extracted/, IDEAS.md's audit trail — and a
# repo-wide scan would either fail forever or force someone to rewrite history
# to make it pass. An explicit list can only ever be too small, which shows up
# as a missed sweep rather than as pressure to falsify the record.
# --------------------------------------------------------------------------- #

REPO = Path(__file__).resolve().parents[2]
RETIRED_TIER = "internal-confidential"

# Live surfaces that ASSIGN or IMPLEMENT a classification. Add a row here when
# a new surface starts making classification decisions.
LIVE_VOCABULARY_SURFACES = (
    "drydocs_api/query_specs.py",
    "drydocs_api/exports.py",
    "drydocs_api/ephemeral_specs.py",
    "web/src/explorer/SpecGrid.tsx",
    "web/src/routes/AskRoute.tsx",
    "UI-WIP/site-plan.md",
    "UI-WIP/wf-admin-config-01.md",
    ".claude/skills/data-context-extractor/references/platforms.md",
    ".claude/skills/controlm-runbook-automation/references/fix-package.md",
    "config/taxonomy/business-application.yaml",
    "config/taxonomy/lob-product-team.yaml",
    "config/taxonomy/oracle-schemas.yaml",
    "config/taxonomy-ontology-map.yaml",
)


def test_the_api_vocabulary_agrees_with_the_config_vocabulary() -> None:
    """The root cause, guarded: two copies that nothing joined.

    Asserting agreement rather than scanning for a token is what makes this
    guard survive the NEXT vocabulary change as well as this one.
    """
    pytest.importorskip("yaml", reason="PyYAML not installed")
    from drydocs_api.query_specs import CLASSIFICATIONS

    doc = yaml.safe_load(CLASSIFICATION.read_text(encoding="utf-8"))
    from_config = {lvl["id"].lower() for lvl in doc["levels"]}
    assert CLASSIFICATIONS == from_config, (
        "drydocs_api.query_specs.CLASSIFICATIONS has drifted from "
        f"config/classification.yaml: api={sorted(CLASSIFICATIONS)} "
        f"config={sorted(from_config)}"
    )


def test_every_registered_spec_carries_a_live_classification() -> None:
    """A spec may only be stamped with a level the config still defines."""
    pytest.importorskip("yaml", reason="PyYAML not installed")
    from drydocs_api.query_specs import QUERY_SPECS

    doc = yaml.safe_load(CLASSIFICATION.read_text(encoding="utf-8"))
    valid = {lvl["id"].lower() for lvl in doc["levels"]}
    bad = {s.id: s.classification for s in QUERY_SPECS.values() if s.classification not in valid}
    assert not bad, f"spec(s) carrying a retired/unknown classification: {bad}"


def test_the_ephemeral_ceiling_is_a_live_level() -> None:
    """The fail-closed ceiling must RE-POINT, never rot or be deleted.

    It is the only classification decision made without human review — the
    Cypher is LLM-authored at runtime — so it has to name a level that exists
    and it has to be the most restrictive one.
    """
    pytest.importorskip("yaml", reason="PyYAML not installed")
    from drydocs_api.ephemeral_specs import EPHEMERAL_CLASSIFICATION

    doc = yaml.safe_load(CLASSIFICATION.read_text(encoding="utf-8"))
    unpublishable = {lvl["id"].lower() for lvl in doc["levels"] if not lvl["publishable"]}
    assert EPHEMERAL_CLASSIFICATION in unpublishable, (
        f"the ephemeral ceiling '{EPHEMERAL_CLASSIFICATION}' is not an "
        f"unpublishable level in config/classification.yaml {sorted(unpublishable)} — "
        "un-reviewed Cypher would export below the boundary"
    )


def test_the_retired_tier_is_gone_from_every_live_vocabulary_surface() -> None:
    """Scoped by the explicit list above — history is never swept in."""
    offenders = []
    for rel in LIVE_VOCABULARY_SURFACES:
        path = REPO / rel
        assert path.exists(), f"guard names a missing file: {rel} (update the list)"
        for n, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if RETIRED_TIER in line.lower() and "J23" not in line and "J24" not in line:
                offenders.append(f"{rel}:{n}: {line.strip()[:100]}")
    assert not offenders, (
        f"{len(offenders)} live surface line(s) still name the retired "
        "Internal-Confidential tier (a line may cite it if it also names the "
        "J23/J24 decision that retired it):\n" + "\n".join(offenders)
    )
