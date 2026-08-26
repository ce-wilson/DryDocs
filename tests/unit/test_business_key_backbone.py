"""G31 — the D1 business-key backbone, guarded within the one database.

The item's original acceptance was written against the pre-G32 multi-database
future: proxy keys mirrored into every database so the composite could join
across the wall. G32 ruled the FOLD, so the cross-database premise died — but
the D1 discipline it protected did not: **identity is always a business key**
(ADR 0001), because that is what lets a corpus rebuild and re-link under
truncate-and-reload, and what graph-seeded retrieval cites back to.

The surviving, enforceable form: every label a shipped loader uses as a
MATCH-only JOIN TARGET must carry a uniqueness / node-key constraint on the
matched property. A join target without a constrained key is how you get a
green load that wrote nothing — the MATCH silently misses, the edge is never
created, and no error fires anywhere (the Q8 class: "silently drops every
DESCRIBES edge").

Deliberately conservative, the _bare_path_sorts idiom: only clear single-label
``MATCH (x:Label {prop: ...})`` patterns count. Multi-label alternations,
path patterns and WHERE-clause joins are out of scope — a guard with false
positives gets muted.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
CYPHER_DIR = REPO / "drydocs" / "loaders" / "cypher"
CONSTRAINTS = REPO / "drydocs_core" / "schema" / "constraints.cypher"
SCHEMA_DIR = REPO / "drydocs_core" / "schema"

#: MATCH (var:Label {prop: — the join-target shape. OPTIONAL MATCH included:
#: an optional join without a key misses just as silently.
_MATCH_TARGET = re.compile(r"MATCH\s*\(\s*\w+\s*:\s*([A-Za-z]\w*)\s*\{\s*(\w+)\s*:")
_MERGE_LABEL = re.compile(r"MERGE\s*\(\s*\w*\s*:\s*([A-Za-z]\w*)")
_UNIQUE = re.compile(
    r"FOR\s*\(\s*\w+\s*:\s*(\w+)\s*\)\s*REQUIRE\s*(?:\w+\.(\w+)\s+IS\s+UNIQUE"
    r"|\(\s*([^)]+?)\s*\)\s+IS\s+NODE\s+KEY)"
)

#: (Label, prop) join targets that are DELIBERATELY unconstrained, each with the
#: ruling that owns it. Adding a row here is a decision, not a convenience —
#: empty is the expected state.
EXEMPT: dict[tuple[str, str], str] = {
    ("ControlMJob", "node_id"): (
        "patch_window.cypher:140 — a FILTER, not an identity join: it selects ALL "
        "jobs whose raw node_id names the target host (the fallback for jobs whose "
        "RUNS_ON edge was not resolved at load). One-to-many by design; zero rows is "
        "a meaningful answer, so the silent-miss class does not apply. Classified at "
        "the guard's first run, G31 2026-08-18; indexing it is a perf question, not "
        "an identity one."
    ),
    ("Attribution", "role_source_name"): (
        "migrate_tom_role_split_g70.cypher — a one-shot migration selecting a "
        "POPULATION by role class (every L1/L2/bare-OM/Risk-Manager/CBT "
        "Attribution), not an identity join: one-to-many by design, zero rows "
        "means 'already migrated' (it is idempotent), so the Q8 silent-miss "
        "class does not apply. The loaders never join on this property — its "
        "identity key stays attribution_id, which IS constrained."
    ),
}


def _constrained_pairs() -> set[tuple[str, str]]:
    """Every (label, property) protected by UNIQUE or NODE KEY, from every
    committed schema file — constraints.cypher plus the supplements (some keys,
    like schemameta_name, deliberately live with their subsystem)."""
    pairs: set[tuple[str, str]] = set()
    for path in sorted(SCHEMA_DIR.rglob("*.cypher"), key=lambda p: p.as_posix()):
        for label, uniq, node_key in _UNIQUE.findall(path.read_text(encoding="utf-8")):
            if uniq:
                pairs.add((label, uniq))
            elif node_key:
                for part in node_key.split(","):
                    prop = part.strip().split(".")[-1]
                    pairs.add((label, prop))
    return pairs


def _join_targets() -> dict[tuple[str, str], list[str]]:
    """(label, prop) pairs each loader MATCHes without MERGEing that label —
    the cross-loader joins the backbone exists for."""
    targets: dict[tuple[str, str], list[str]] = {}
    for path in sorted(CYPHER_DIR.glob("*.cypher"), key=lambda p: p.as_posix()):
        text = path.read_text(encoding="utf-8")
        merged = set(_MERGE_LABEL.findall(text))
        for label, prop in _MATCH_TARGET.findall(text):
            if label in merged or label == "SchemaMeta":
                continue
            targets.setdefault((label, prop), []).append(path.name)
    return targets


def test_every_loader_join_target_has_a_constrained_business_key() -> None:
    constrained = _constrained_pairs()
    failures = [
        f"({label}.{prop}) matched by {sorted(set(files))} — no UNIQUE/NODE KEY found"
        for (label, prop), files in sorted(_join_targets().items())
        if (label, prop) not in constrained and (label, prop) not in EXEMPT
    ]
    assert not failures, (
        "loader join targets without a constrained business key:\n  "
        + "\n  ".join(failures)
        + "\nA MATCH-only join on an unconstrained property is a silent-miss defect "
        "(the Q8 class) AND an unindexed scan. Add the key to constraints.cypher, or "
        "add an EXEMPT row with the ruling that owns the exception."
    )


def test_the_d1_backbone_keys_are_home_in_constraints() -> None:
    """The two keys the retired proxy file carried, plus the four the G31
    measurement found missing (they arrived between the measurement and the
    fold): all six live in the committed schema, one home."""
    constrained = _constrained_pairs()
    for pair in [
        ("DataAsset", "assetId"),
        ("ControlMJob", "folder_id"),
        ("ControlMJob", "job_id"),
        ("SoftwareProduct", "product_id"),
        ("Vendor", "vendor_id"),
        ("Document", "doc_id"),
        ("ControlMFolder", "folder_id"),
    ]:
        assert pair in constrained, f"D1 backbone key missing from the schema: {pair}"


def test_the_proxy_file_stays_a_tombstone() -> None:
    """02_proxy_constraints.cypher retired at G31 — it must never regrow CREATE
    statements, because a key created only there runs against no database (the
    provisioner no longer invokes it) and silently protects nothing."""
    text = (SCHEMA_DIR / "provisioning" / "02_proxy_constraints.cypher").read_text(encoding="utf-8")
    assert "RETIRED" in text
    assert "CREATE CONSTRAINT" not in text.replace("// ", ""), (
        "the tombstone regrew a CREATE CONSTRAINT — keys belong in "
        "constraints.cypher, the one home"
    )
