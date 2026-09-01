"""Guard for PORT-MANIFEST.yaml — the machine-readable port-disposition ledger
(docs/reviews/tech-debt-port-boundary.md Phase 1, 2026-07-09).

The manifest is the authority the consumer-side reconcile-port run reads
mechanically; these checks keep it well-formed and pin the rows whose loss
would be catastrophic (a blind checkout of drydocs/publishing/** destroys the
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
        "drydocs/publishing/**": "canonical-company",
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
