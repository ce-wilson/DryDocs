"""Enforce the doc-source registry ledger (Q5 / ADR 0006 — no Neo4j required).

Every DOCUMENT corpus must carry classification + connector + curation tier (the Q5
acceptance trio) plus the ADR 0006 field semantics: target_db restricted to
dddocs | ddcontext, the curation ladder fixed per tier, and the External ⇒
source_url + captured_at rule shared with test_classification.py. The backfill
guard pins the corpora known to be ingested — a new corpus loaded without a
registry entry should fail HERE, not be discovered in the graph.
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

pytestmark = pytest.mark.skipif(not _YAML_AVAILABLE, reason="PyYAML not installed")

CONFIG_DIR = Path(__file__).resolve().parents[2] / "config"
DOC_REGISTRY = CONFIG_DIR / "doc-source-registry.yaml"
CLASSIFICATION = CONFIG_DIR / "classification.yaml"

CONNECTORS = {"web", "filedrop", "confluence", "sharepoint", "teams", "email"}
TIERS = {"T1", "T2", "T3", "T4"}
TARGET_DBS = {"dddocs", "ddcontext"}  # ADR 0006 §2 — nothing else, ever
TRUSTS = {"VERBATIM", "GROUNDED", "SYNTHESIZED"}
_REFRESH = re.compile(r"^(manual|on-demand|scheduled\(.+\))$")

# ADR 0006 §4: the curation ladder is FIXED per tier, not chosen per entry.
CURATION_BY_TIER = {
    "T1": "none",
    "T2": "sme-confirm",
    "T3": "sme-confirm",
    "T4": "sme-confirm",  # J23: the +confidential rider retired with the Internal-Confidential tier collapse
}

# The corpora known to be ingested as of Q5 (the backfill guard). EXTEND this set
# when a new corpus loads — the ledger entry and this pin land in the same commit.
INGESTED_CORPORA = {"bmc-docs", "essential-graphrag", "jpmc-reports"}


def _registry() -> dict:
    return yaml.safe_load(DOC_REGISTRY.read_text(encoding="utf-8"))


def test_doc_registry_exists_with_schema() -> None:
    assert DOC_REGISTRY.exists(), f"Missing doc-source ledger: {DOC_REGISTRY}"
    assert _registry().get("schema") == "drydocs.doc-source-registry.v1"


def test_every_doc_source_fully_declared() -> None:
    """The Q5 acceptance trio (classification + connector + curation tier) plus the
    ADR 0006 vocabularies, on EVERY entry."""
    vocab = yaml.safe_load(CLASSIFICATION.read_text(encoding="utf-8"))
    valid_cls = {lvl["id"] for lvl in vocab["levels"]}

    failures: list[str] = []
    seen_ids: set[str] = set()
    for src in _registry().get("sources", []):
        sid = src.get("id", "<no-id>")
        if sid in seen_ids:
            failures.append(f"[{sid}] duplicate id")
        seen_ids.add(sid)

        if src.get("classification") not in valid_cls:
            failures.append(
                f"[{sid}] classification '{src.get('classification')}' not in {sorted(valid_cls)}"
            )
        if not src.get("source"):
            failures.append(f"[{sid}] missing required field 'source'")
        if src.get("connector") not in CONNECTORS:
            failures.append(
                f"[{sid}] connector '{src.get('connector')}' not in {sorted(CONNECTORS)}"
            )
        if src.get("tier") not in TIERS:
            failures.append(f"[{sid}] tier '{src.get('tier')}' not in {sorted(TIERS)}")
        if src.get("target_db") not in TARGET_DBS:
            failures.append(
                f"[{sid}] target_db '{src.get('target_db')}' not in {sorted(TARGET_DBS)} (ADR 0006)"
            )
        if src.get("trust_default") not in TRUSTS:
            failures.append(
                f"[{sid}] trust_default '{src.get('trust_default')}' not in {sorted(TRUSTS)}"
            )
        if not _REFRESH.match(str(src.get("refresh", ""))):
            failures.append(
                f"[{sid}] refresh '{src.get('refresh')}' not manual | on-demand | scheduled(...)"
            )
        if src.get("classification") == "External":
            for field in ("source_url", "captured_at"):
                if not src.get(field):
                    failures.append(f"[{sid}] External corpus missing '{field}'")

    assert not failures, f"{len(failures)} doc-registry error(s):\n" + "\n".join(failures)


def test_curation_matches_tier_ladder() -> None:
    """ADR 0006 §4: curation is derived from tier — an entry may not soften (or
    over-harden) its own gate."""
    failures = [
        f"[{src.get('id')}] tier {src.get('tier')} requires curation "
        f"'{CURATION_BY_TIER.get(src.get('tier'))}', got '{src.get('curation')}'"
        for src in _registry().get("sources", [])
        if src.get("curation") != CURATION_BY_TIER.get(src.get("tier"))
    ]
    assert not failures, "\n".join(failures)


def test_ingested_corpora_are_backfilled() -> None:
    """Zero unregistered corpora: everything known to be loaded traces to an entry."""
    ids = {src.get("id") for src in _registry().get("sources", [])}
    missing = INGESTED_CORPORA - ids
    assert not missing, f"ingested corpora missing from the doc-source ledger: {sorted(missing)}"
