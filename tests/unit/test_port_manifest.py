"""Guard for PORT-MANIFEST.yaml — the machine-readable port-disposition ledger
(docs/reviews/tech-debt-port-boundary.md Phase 1, 2026-07-09).

The manifest is the authority the consumer-side reconcile-port run reads
mechanically; these checks keep it well-formed and pin the rows whose loss
would be catastrophic (a blind checkout of drydocs/review/publishing/** destroys the
consumer's wired Confluence originals). Pure YAML — no git, no Neo4j.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

REPO = Path(__file__).resolve().parents[2]
MANIFEST = REPO / "PORT-MANIFEST.yaml"

VALID_DISPOSITIONS = {
    "clean-add",
    "canonical-producer",
    "canonical-company",
    "union-append",
    "per-entry",
    "evaluate",
    "never-port",
    # J43 (2026-08-26): a DETERMINISTIC RENDER — take neither side's copy,
    # REGENERATE from the reconciled tree. Added for the whole derived family at
    # once (board/roadmap/ideas/load-map + the design-doc renders); the roadmap
    # row had inboxed exactly this naming gap after the company's send-back.
    "derived",
}


@pytest.fixture(scope="module")
def manifest() -> dict:
    return yaml.safe_load(MANIFEST.read_text(encoding="utf-8"))


def test_schema_and_header(manifest: dict) -> None:
    assert manifest["schema"] == "drydocs.port-manifest.v1"
    assert manifest["classification"] == "Internal-Public"
    assert manifest.get("default"), "the no-row default must be stated"


def test_paths_unique(manifest: dict) -> None:
    paths = [r["path"] for r in manifest["rows"]]
    dupes = [p for p, n in Counter(paths).items() if n > 1]
    assert not dupes, f"duplicate manifest paths: {dupes}"


def test_dispositions_valid(manifest: dict) -> None:
    bad = [
        (r["path"], r.get("disposition"))
        for r in manifest["rows"]
        if r.get("disposition") not in VALID_DISPOSITIONS
    ]
    assert not bad, f"invalid dispositions: {bad}"


def test_per_entry_rows_carry_an_entry_rule(manifest: dict) -> None:
    missing = [
        r["path"]
        for r in manifest["rows"]
        if r["disposition"] == "per-entry" and not r.get("entry_rule")
    ]
    assert not missing, f"per-entry rows without entry_rule: {missing}"


def test_protective_rows_carry_a_note(manifest: dict) -> None:
    """canonical-company and never-port rows exist to STOP someone — the note
    is the one-line why that stops them."""
    missing = [
        r["path"]
        for r in manifest["rows"]
        # J43: `derived` joins the note-required set — a derived row's note must
        # name what regenerates it, or "regenerate" is an instruction with no verb.
        if r["disposition"] in ("canonical-company", "never-port", "derived") and not r.get("note")
    ]
    assert not missing, f"protective rows without a note: {missing}"


def test_critical_rows_are_pinned(manifest: dict) -> None:
    """Regression pins for the rows whose loss caused (or nearly caused) real
    damage: the back-flow stream, the append-only audit log, the per-entry
    ontology files, and the port-frozen adapter."""
    by_path = {r["path"]: r["disposition"] for r in manifest["rows"]}
    expected = {
        "drydocs/review/publishing/**": "canonical-company",
        "config/gate-prompts/**": "canonical-company",
        "drydocs_core/adapters/oracle_adapter.py": "canonical-company",
        "config/gate-log.md": "union-append",
        "drydocs_core/ontology/relationship_vocabulary/**": "per-entry",
        "config/taxonomy-ontology-map/**": "per-entry",
        "drydocs/data/**": "never-port",
    }
    for path, disposition in expected.items():
        assert (
            by_path.get(path) == disposition
        ), f"{path}: expected {disposition}, manifest says {by_path.get(path)}"


def _is_glob(path: str) -> bool:
    return any(c in path for c in "*?[")


def _probe_for(path: str) -> str:
    """A concrete path a row governs: itself for a literal row, a representative
    expansion for a glob row (`**` -> two segments, `*` -> one token)."""
    return path.replace("**", "zz/zz").replace("*", "zz")


def shadowed_rows(rows: list[dict]) -> list[tuple[str, str]]:
    """J47 (b): (row, earlier glob) pairs where an EARLIER glob row already
    matches the row's path — first match wins, so the later, more specific row
    can never fire. Derived from the rows themselves; no hardcoded override list."""
    from tests.unit.test_port_reconcile_guards import glob_to_regex

    paths = [r["path"] for r in rows]
    out: list[tuple[str, str]] = []
    for i, path in enumerate(paths):
        probe = _probe_for(path)
        for earlier in paths[:i]:
            if _is_glob(earlier) and earlier != path and glob_to_regex(earlier).match(probe):
                out.append((path, earlier))
                break
    return out


def test_no_row_is_shadowed_by_an_earlier_glob(manifest: dict) -> None:
    """First match wins — a specific override (config/gate-log.md) must appear
    BEFORE the broad glob that would otherwise swallow it (config/**). J47
    (2026-08-21): DERIVED for every row rather than a hand-typed list of four
    overrides against config/**, which is what let a fifth override drift
    unchecked. Proven to fail on an injected defect below (J26)."""
    paths = [r["path"] for r in manifest["rows"]]
    shadowed = shadowed_rows(manifest["rows"])
    assert not shadowed, (
        "rows that can never fire (an earlier glob already matches them):\n  "
        + "\n  ".join(f"{row}  <- shadowed by earlier {glob}" for row, glob in shadowed)
    )
    # same shape for the drydocs/ tree: the frozen adapter + review modules are
    # file-specific rows, and no broad drydocs/** row may exist at all
    assert "drydocs/**" not in paths, "no blanket drydocs/** row — keep dispositions explicit"


def test_shadow_detector_catches_a_misordered_override() -> None:
    """J26: the derived guard is watched to fail on the defect it replaces the
    list for — the override AFTER its broad glob."""
    bad = [{"path": "config/**"}, {"path": "config/gate-log.md"}, {"path": "docs/x.md"}]
    assert shadowed_rows(bad) == [("config/gate-log.md", "config/**")]
    good = [{"path": "config/gate-log.md"}, {"path": "config/**"}, {"path": "docs/x.md"}]
    assert shadowed_rows(good) == []
    # a later glob narrower than an earlier one is shadowed too
    nested = [{"path": "docs/**"}, {"path": "docs/plan/*.html"}]
    assert shadowed_rows(nested) == [("docs/plan/*.html", "docs/**")]


def test_pyproject_row_pins_the_version_string_rule(manifest: dict) -> None:
    """J7 rule (3): the pyproject.toml row is per-entry and its entry_rule keeps
    the CONSUMER's version string (per-repo release cadence) — a port must never
    carry the producer's version or its v* release tags across."""
    row = next(r for r in manifest["rows"] if r["path"] == "pyproject.toml")
    assert row["disposition"] == "per-entry"
    rule = row["entry_rule"].lower()
    assert "version string" in rule and "consumer" in rule, rule
    assert "tags never cherry-pick" in rule, rule


# ---- J68: a declaration and its guard must find each other -------------------
# A DECLARATION file (MODULE_MAP.md, source-registry.yaml, 01_databases.cypher)
# and the GUARD that reads it encode ONE fact in two languages. Take one without
# the other and the guard enforces rows the declaration no longer carries.
#
# The rule is deliberately NOT "both must share a disposition". The
# test_database_names.py row is a worked counter-example: its guard is per-entry
# because SCANNED_PACKAGES is extensible, while the cypher it reads is
# canonical-producer because the TOPOLOGY is a signed gate's ruling. That split is
# correct and reasoned, and a same-disposition rule would break it.
#
# What must hold is weaker and sufficient: THE COUPLING IS NAMED IN THE MANIFEST,
# so a port session resolving either file reads about the other. That is exactly
# what the test_database_names.py note does ("MOVES WITH ... ALWAYS") and exactly
# what MODULE_MAP.md did not do — which is how a wholesale take of MODULE_MAP.md
# dropped six company-only module families on 2026-09-01 while its per-entry guard
# went on enforcing them.

#: (declaration, guard, why the two are one fact). Hand-declared, because which
#: guard reads which file is not derivable from paths — and a typed list is what
#: forces a human look when a new pair appears.
DECLARATION_GUARD_PAIRS: tuple[tuple[str, str, str], ...] = (
    (
        "MODULE_MAP.md",
        "tests/unit/test_module_boundary.py",
        "the map classifies every module; the guard is default-deny over that "
        "classification, so a module the map loses is a module the guard rejects",
    ),
    (
        "drydocs_core/component_map.py",
        "tests/unit/test_module_boundary.py",
        "since ADR 0018 D1 the groups the guard enforces live in this file and the "
        "guard imports them; the third member of the pair above, born 2026-09-02 "
        "without a row and found by the company's chunk-5 apply of port-base-20260902",
    ),
    (
        "drydocs_core/component_map.py",
        "MODULE_MAP.md",
        "the map's component tables are RENDERED from the declaration; a merge that "
        "moves one without re-rendering the other is two classifications",
    ),
    (
        "config/source-registry.yaml",
        "tests/unit/test_source_registry.py",
        "the registry declares the systems and datasets; the guard validates them, "
        "so a row the registry loses is a guard failure and not a silent absence",
    ),
    (
        "drydocs_core/schema/provisioning/01_databases.cypher",
        "tests/unit/test_database_names.py",
        "the cypher provisions the databases and the guard parses it back — one "
        "topology ruling in two languages (document-content-topology, 32/32)",
    ),
)


def _row_for(rows: list[dict], path: str) -> dict | None:
    """The row governing ``path`` — first match wins, literal or glob."""
    from tests.unit.test_port_reconcile_guards import glob_to_regex

    for row in rows:
        pattern = row["path"]
        if pattern == path or glob_to_regex(pattern).match(path):
            return row
    return None


def _row_text(row: dict | None) -> str:
    return "" if row is None else f"{row.get('entry_rule', '')}\n{row.get('note', '')}"


def uncoupled_pairs(
    rows: list[dict], pairs: tuple[tuple[str, str, str], ...]
) -> list[tuple[str, str]]:
    """Pairs where NEITHER governing row names the other half.

    Naming either direction is enough: a session resolving the declaration finds
    the guard, or a session resolving the guard finds the declaration. Naming
    neither is the case that fails.
    """
    out: list[tuple[str, str]] = []
    for declaration, guard, _why in pairs:
        declaration_text = _row_text(_row_for(rows, declaration))
        guard_text = _row_text(_row_for(rows, guard))
        if guard not in declaration_text and declaration not in guard_text:
            out.append((declaration, guard))
    return out


def test_every_declaration_names_the_guard_that_reads_it(manifest: dict) -> None:
    """J68 (c). Measured, not theorised: on 2026-09-01 a company apply took
    MODULE_MAP.md wholesale (canonical-producer) while its guard stayed per-entry,
    dropping drydocs.scrapers.*, drydocs.docmeta.* and drydocs.seal_projection —
    six module families the guard then rejected. The manifest already carried the
    coupling for ONE pair, in the test_database_names.py note; this makes it a
    property of every declared pair instead of one row's good manners."""
    gaps = uncoupled_pairs(manifest["rows"], DECLARATION_GUARD_PAIRS)
    assert not gaps, (
        "declaration/guard pairs where neither row names the other — a port "
        "session resolving one will not learn about the other:\n  "
        + "\n  ".join(f"{d}  <->  {g}" for d, g in gaps)
    )


def test_the_coupling_detector_catches_an_uncoupled_pair() -> None:
    """The guard is watched to fail on the defect it exists for (the J26 idiom) —
    otherwise a detector that silently matches nothing reads as a passing suite."""
    pair = (("MODULE_MAP.md", "tests/unit/test_module_boundary.py", "why"),)
    uncoupled = [
        {"path": "MODULE_MAP.md", "disposition": "canonical-producer"},
        {"path": "tests/unit/test_module_boundary.py", "entry_rule": "groups union"},
    ]
    assert uncoupled_pairs(uncoupled, pair) == [
        ("MODULE_MAP.md", "tests/unit/test_module_boundary.py")
    ]
    # naming it from EITHER side closes the gap
    from_declaration = [
        {"path": "MODULE_MAP.md", "note": "moves with tests/unit/test_module_boundary.py"},
        {"path": "tests/unit/test_module_boundary.py", "entry_rule": "groups union"},
    ]
    assert uncoupled_pairs(from_declaration, pair) == []
    from_guard = [
        {"path": "MODULE_MAP.md", "disposition": "canonical-producer"},
        {"path": "tests/unit/test_module_boundary.py", "note": "reads MODULE_MAP.md"},
    ]
    assert uncoupled_pairs(from_guard, pair) == []


# ---- J71: a per-entry merge rule must be TOTAL ------------------------------
# A rule that ENUMERATES fields has a hole in it the moment a field is added, and
# enumerating harder does not close it — the next field reopens it. Measured on
# 2026-09-01, from a real drop: config/source-bindings.yaml's rule named six
# producer-owned fields and two company-owned ones, `twin` and `reason` were in
# neither, and the company port carried none of `1bd29b42` because a per-entry
# merge with no instruction for a field has no defensible move.
#
# So the property is TOTALITY, not completeness. Name what you want to name, then
# declare what happens to everything else. "Is this rule total" is decidable;
# "is this rule complete enough" is not, which is why the second cannot be guarded.

#: The literal that makes a rule total. Deliberately a marker rather than a prose
#: match: "producer owns the rest" and "the rest is producer-owned" and a dozen
#: other spellings all mean the same thing, and a guard that accepts any of them
#: also accepts a sentence that merely sounds like a default.
DEFAULT_MARKER = "UNNAMED FIELDS:"

#: Per-entry rows whose governed file is a YAML document of list entries, with the
#: top-level sequences whose entries carry the fields. Hand-declared: which
#: sequences hold entries is not derivable (a `counts:` block is a mapping, not
#: entries), and a typed list forces a human look when a new per-entry file appears.
ENTRY_FILES: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("config/source-bindings.yaml", ("profiles", "unbound")),
    ("config/doc-source-registry.yaml", ("sources",)),
    ("config/source-registry.yaml", ("systems", "datasets")),
    ("config/audit-fields.yaml", ("envelope", "sources")),
    ("config/taxonomy/domains.yaml", ("domains",)),
    ("config/taxonomy/editions.yaml", ("editions",)),
)


def entry_fields(path: str, sequences: tuple[str, ...]) -> set[str]:
    """Every field name appearing on an entry under ``sequences``.

    Parsed, never grepped. A regex over raw YAML matches prose inside `notes:`
    blocks — the first version of this check reported `session`, `prose` and
    `anyway` as fields across the backlog items, which is the J66 lesson (a guard
    reads code, not the prose around it) arriving in a config file.
    """
    import yaml as _yaml

    doc = _yaml.safe_load((REPO / path).read_text(encoding="utf-8"))
    fields: set[str] = set()
    for sequence in sequences:
        for entry in doc.get(sequence) or []:
            if isinstance(entry, dict):
                fields |= set(entry)
    return fields


def incomplete_rules(rows: list[dict]) -> list[tuple[str, list[str]]]:
    """(path, unclassified fields) for every per-entry rule that is not total."""
    by_path = {row["path"]: row for row in rows}
    out: list[tuple[str, list[str]]] = []
    for path, sequences in ENTRY_FILES:
        row = by_path.get(path)
        if not row or row.get("disposition") != "per-entry":
            continue
        rule = row.get("entry_rule") or ""
        if DEFAULT_MARKER in rule:
            continue  # total by declaration — unnamed fields have an answer
        unnamed = sorted(f for f in entry_fields(path, sequences) if f not in rule)
        if unnamed:
            out.append((path, unnamed))
    return out


def test_every_per_entry_rule_is_total(manifest: dict) -> None:
    """J71 (c). The failure this prevents is silent by construction: a dropped
    field leaves no conflict, no red test and no diff on either side — it is simply
    absent, and stays absent until somebody happens to look for it, which on
    2026-09-01 took two days and an SME reading a console table."""
    gaps = incomplete_rules(manifest["rows"])
    assert not gaps, (
        "per-entry rules that do not say what happens to every field in their file. "
        f"Name the field, or add a `{DEFAULT_MARKER}` clause saying which side owns "
        "everything not listed:\n  " + "\n  ".join(f"{path}: {fields}" for path, fields in gaps)
    )


def test_the_totality_detector_catches_an_injected_hole() -> None:
    """The J26 idiom: a detector that silently matches nothing reads as a pass."""
    if not (REPO / "config" / "source-bindings.yaml").is_file():
        # A consumer mid-apply holds the manifest before it holds every per-entry
        # subject (the company's chunk-2 take on 2026-09-03 hit FileNotFoundError
        # here). The detector above already ran on the rows that exist; this
        # companion only needs a subject to inject a hole into, and it names one.
        pytest.skip(
            "companion needs config/source-bindings.yaml to inject its hole into; the "
            "file is absent on this tree (a consumer before its per-entry class lands)"
        )
    rows = [
        {
            "path": "config/source-bindings.yaml",
            "disposition": "per-entry",
            "entry_rule": "producer owns id and carrier",
        }
    ]
    gaps = incomplete_rules(rows)
    assert gaps and gaps[0][0] == "config/source-bindings.yaml"
    assert "twin" in gaps[0][1], "the field the real drop turned on must be reported"
    # the marker closes it without naming anything further
    rows[0]["entry_rule"] += f" {DEFAULT_MARKER} producer-owned."
    assert incomplete_rules(rows) == []
