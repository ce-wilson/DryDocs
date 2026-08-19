"""G102 — the three ADR 0011 clause-1 guards, landed BEFORE the fold.

Gate ``document-content-topology`` (SIGNED 32/32, 2026-08-18) accepted the
physics-to-discipline loss of folding the content topology to one database ON
THE PRECONDITION that these guards exist first. Post-fold, a bad write CANNOT
be stopped by a database wall — every protection here is a check that must run
and pass. That is the deal the gate signed, and this file is the discipline
half of it.

Guard (a): every ground-truth QuerySpec excludes ``:Uncertain`` — generated
STRUCTURALLY at registry build (riding the :SchemaMeta exclusion idiom), never
hand-edited into ~30 queries. These tests prove the transform landed.

Guard (b): the uncertain WRITE boundary. Only the allowlisted writers may apply
``:Uncertain``; ``drydocs_deepdoc`` may not MERGE/CREATE a node WITHOUT it.

Guard (c): the live audit spec exists and is shaped right — :Uncertain nodes
reachable from ground truth, expected 0, any hit is a promotion that skipped
the HITL gate.
"""

from __future__ import annotations

import re
from pathlib import Path

from drydocs_api.query_specs import QUERY_SPECS, is_watermarked

REPO = Path(__file__).resolve().parents[2]

#: The ONLY code allowed to apply :Uncertain (ADR 0011 clause 1 + its §118
#: rider: the AgentRun telemetry write is the R1 ruling's substance surviving
#: as the label, so it is a second authorized surface — an allowlist, not a
#: single module). Adding an entry here is a ruling, not a convenience.
UNCERTAIN_WRITERS = (
    "drydocs_deepdoc",
    "agents/common/agent_run_writer.py",
)

_SCHEMA_META_EXCL = re.compile(r"NOT\s+(\w+):SchemaMeta")
_UNCERTAIN_EXCL = re.compile(r"NOT\s+(\w+):SchemaMeta\s+AND\s+NOT\s+(\w+):Uncertain")


def _ground_truth_specs():
    return [s for s in QUERY_SPECS.values() if s.database == "drydocs" and not s.uncertain]


# ── guard (a): the structural exclusion ──────────────────────────────────────


def test_every_ground_truth_schema_meta_site_also_excludes_uncertain() -> None:
    """Each `NOT x:SchemaMeta` in a ground-truth spec carries `AND NOT x:Uncertain`.

    The transform piggybacks the exclusion idiom test_schema_meta_exclusion
    already forces onto every bound stamped-label var, so coverage here is
    exactly coverage there — one idiom, two realms.
    """
    failures: list[str] = []
    for spec in _ground_truth_specs():
        meta_sites = _SCHEMA_META_EXCL.findall(spec.cypher)
        paired = _UNCERTAIN_EXCL.findall(spec.cypher)
        if len(meta_sites) != len(paired):
            failures.append(f"{spec.id}: {len(meta_sites)} SchemaMeta sites, {len(paired)} paired")
        for a, b in paired:
            if a != b:
                failures.append(f"{spec.id}: exclusion pair binds different vars ({a} vs {b})")
    assert not failures, (
        "ground-truth specs whose :Uncertain exclusion did not land structurally:\n  "
        + "\n  ".join(failures)
        + "\nThe transform is _with_ground_truth_exclusion at registry build — if a new "
        "spec has no :SchemaMeta anchor for it to ride, give it one (the O33 idiom) "
        "rather than hand-writing the Uncertain clause."
    )


def test_ground_truth_specs_never_mention_uncertain_except_the_exclusion() -> None:
    """A ground-truth spec that MATCHES :Uncertain is reading the wrong realm."""
    offenders: list[str] = []
    for spec in _ground_truth_specs():
        stripped = _UNCERTAIN_EXCL.sub("", spec.cypher)
        if ":Uncertain" in stripped:
            offenders.append(spec.id)
    assert not offenders, (
        f"ground-truth specs touching :Uncertain outside the exclusion: {offenders} — "
        "either the spec belongs to the uncertain realm (declare uncertain=True, which "
        "also watermarks its exports) or the query is wrong."
    )


def test_uncertain_specs_are_watermarked() -> None:
    """The durable watermark trigger is the spec's own declaration (ADR 0011 §117)."""
    for spec in QUERY_SPECS.values():
        if spec.uncertain:
            assert is_watermarked(spec), f"{spec.id}: uncertain=True but not watermarked"


# ── guard (b): the write boundary ────────────────────────────────────────────


def _is_allowlisted(path: Path) -> bool:
    rel = path.relative_to(REPO).as_posix()
    return any(rel == w or rel.startswith(w + "/") for w in UNCERTAIN_WRITERS)


def test_no_code_outside_the_allowlist_applies_uncertain() -> None:
    """Applying :Uncertain is the uncertain write boundary — two surfaces, ruled.

    Scans every loader cypher, schema cypher and first-party python write
    surface for the label being APPLIED (in a MERGE/CREATE node pattern or a
    SET label). Reading the label (WHERE NOT x:Uncertain, MATCH for audits) is
    everyone's right and is not flagged.
    """
    apply_re = re.compile(r"(?:MERGE|CREATE)\s*\([^)]*:Uncertain|SET\s+\w+\s*:\s*Uncertain")
    roots = [
        REPO / "drydocs" / "loaders",
        REPO / "drydocs_core" / "schema",
        REPO / "drydocs_api",
        REPO / "drydocs_lineage",
        REPO / "drydocs_remediation",
        REPO / "drydocs_deepdoc",
        REPO / "agents" / "common",
    ]
    offenders: list[str] = []
    for root in roots:
        if not root.exists():
            continue
        for path in sorted(root.rglob("*")):
            if path.suffix not in {".py", ".cypher"} or "__pycache__" in path.parts:
                continue
            if not apply_re.search(path.read_text(encoding="utf-8", errors="ignore")):
                continue
            if not _is_allowlisted(path):
                offenders.append(path.relative_to(REPO).as_posix())
    assert not offenders, (
        ":Uncertain applied outside the ruled write boundary:\n  "
        + "\n  ".join(offenders)
        + f"\nThe allowlist is {UNCERTAIN_WRITERS} — extending it is a ruling "
        "(gate document-content-topology §F / ADR 0011 clause 1), not an edit."
    )


def test_deepdoc_never_writes_without_the_label() -> None:
    """drydocs_deepdoc may not MERGE/CREATE a node pattern that lacks :Uncertain.

    The writer is a stub today, which is exactly why this guard lands NOW: the
    discipline is built in before the first uncertain write ever happens — the
    gate's 'nearly free' timing argument, made enforceable.
    """
    node_write = re.compile(r"(?:MERGE|CREATE)\s*\(\s*\w*\s*:([A-Za-z:]+)")
    offenders: list[str] = []
    root = REPO / "drydocs_deepdoc"
    for path in sorted(root.rglob("*")):
        if path.suffix not in {".py", ".cypher"} or "__pycache__" in path.parts:
            continue
        for labels in node_write.findall(path.read_text(encoding="utf-8", errors="ignore")):
            if "Uncertain" not in labels.split(":"):
                offenders.append(f"{path.relative_to(REPO).as_posix()}: :{labels}")
    assert not offenders, "drydocs_deepdoc node writes missing :Uncertain:\n  " + "\n  ".join(
        offenders
    )


# ── guard (c): the live audit spec ───────────────────────────────────────────


def test_the_audit_spec_is_registered_and_shaped_right() -> None:
    spec = QUERY_SPECS["audit.uncertain-reachable.v1"]
    assert spec.uncertain, "the audit spec reads the uncertain realm by design"
    assert spec.database == "drydocs"
    assert "breaching" in [c.name for c in spec.columns]
    assert "NOT g:Uncertain" in spec.cypher and "NOT g:SchemaMeta" in spec.cypher
    # Expected-0 is the CONTRACT: the description must say so, because the spec
    # is the alarm and an alarm whose threshold lives only in a chat is no alarm.
    assert "EXPECTED 0" in spec.description
