"""Drift guard for web/src/generated/remediation-lookup.json (G85).

The artifact cites the corpus BY LINE, so this fails on a stale artifact, on a corpus
edit that moves or removes a cited line, and on a citation whose trust tier the cited
file's own provenance does not allow (requirement (a)).
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest
import yaml

from tests.source_scan import imported_modules, source_text

REPO = Path(__file__).resolve().parents[2]
RENDERER = REPO / "scripts" / "render_remediation_lookup.py"
BOARD = REPO / "scripts" / "render_board.py"
COMMITTED = REPO / "web" / "src" / "generated" / "remediation-lookup.json"
DIFF = REPO / "web" / "src" / "generated" / "remediation-diff.json"
PRECEDENCE = REPO / "config" / "precedence.yaml"


def _renderer():
    spec = importlib.util.spec_from_file_location("render_remediation_lookup", RENDERER)
    module = importlib.util.module_from_spec(spec)
    # @dataclass resolves its module through sys.modules; unregistered, it raises.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _committed() -> dict:
    return json.loads(COMMITTED.read_text(encoding="utf-8"))


def _citations(tier: str | None = None):
    for lookup in _committed()["lookups"]:
        for answer in lookup["answers"]:
            if tier is None or answer["tier"] == tier:
                yield from answer["citations"]


def test_committed_frame_matches_regeneration() -> None:
    fresh = _renderer().build_remediation_lookup()
    assert _committed() == fresh, (
        "web/src/generated/remediation-lookup.json is stale — re-run "
        "`python scripts/render_remediation_lookup.py` (or a default-paths "
        "render_board.py run) and commit the refresh"
    )


def test_every_change_in_the_diff_has_a_lookup() -> None:
    """It reviews a diff; a change the diff makes with no lookup beside it is the gap."""
    diff = json.loads(DIFF.read_text(encoding="utf-8"))
    assert [c["approval_id"] for c in diff["changes"]] == [
        lk["approval_id"] for lk in _committed()["lookups"]
    ]


def test_tiers_walk_the_ratified_precedence_order() -> None:
    precedence = yaml.safe_load(PRECEDENCE.read_text(encoding="utf-8"))
    authority = {a["id"]: a["authority"] for a in precedence["order"]}
    tiers = _committed()["tiers"]
    assert [t["id"] for t in tiers] == ["vendor", "standards", "team"]
    assert all(authority[t["authority_id"]] == t["authority"] for t in tiers)
    assert [t["authority"] for t in tiers] == sorted(t["authority"] for t in tiers)
    for lookup in _committed()["lookups"]:
        assert [a["tier"] for a in lookup["answers"]] == [t["id"] for t in tiers]


def test_every_citation_is_still_the_line_it_names() -> None:
    """Requirement (a): doc, line and trust on every row, and the line still says it."""
    renderer = _renderer()
    rows = list(_citations())
    assert rows, "a lookup with no citations demonstrates nothing"
    for c in rows:
        path = REPO / c["doc"]
        assert path.exists(), f"cites a missing file: {c['doc']}"
        assert c["trust"] and c["citable_as"], f"{c['doc']}:{c['line']} carries no trust"
        lines = path.read_text(encoding="utf-8").splitlines()
        assert 0 < c["line"] <= len(lines), f"{c['doc']}:{c['line']} is past the end of the file"
        assert (
            renderer._excerpt(lines[c["line"] - 1]) == c["excerpt"]
        ), f"{c['doc']}:{c['line']} no longer says what the lookup quotes; re-render"


def test_no_vendor_citation_is_synthesized_or_a_laundered_lead() -> None:
    renderer = _renderer()
    for c in _citations("vendor"):
        assert c["trust"] != "SYNTHESIZED", f"{c['doc']}:{c['line']} cites SYNTHESIZED as vendor"
        text = (REPO / c["doc"]).read_text(encoding="utf-8")
        if renderer.SNIPPETS_MARKER in text:
            assert (
                c["trust"] == "GROUNDED-snippets-only"
            ), f"{c['doc']} is a search-snippet capture but {c['line']} is cited as {c['trust']}"


def test_the_resolver_refuses_both_ways_trust_gets_laundered(tmp_path, monkeypatch) -> None:
    """Anti-vacuity: the rule above has no live snippets-only citation today, so prove
    the resolver's refusals directly rather than trusting a guard with nothing to see."""
    renderer = _renderer()
    with pytest.raises(ValueError, match="may not be cited"):
        renderer.resolve_vendor(renderer.Cite(renderer.VARIABLES_DOC, "Name cannot", "SYNTHESIZED"))

    monkeypatch.setattr(renderer, "REPO", tmp_path)
    (tmp_path / "stub.md").write_text(
        "# stub\n\nEverything here is [GROUNDED — search-result snippets only].\n\n"
        "- defjob reads an XML input file.\n",
        encoding="utf-8",
        newline="\n",
    )
    with pytest.raises(ValueError, match="search-snippet capture"):
        renderer.resolve_vendor(renderer.Cite("stub.md", "defjob reads", "GROUNDED"))
    lead = renderer.resolve_vendor(
        renderer.Cite("stub.md", "defjob reads", "GROUNDED-snippets-only")
    )
    assert lead["citable_as"].startswith("citable ONLY as a lead")


def test_every_tier_answers_or_says_why_not() -> None:
    for lookup in _committed()["lookups"]:
        for answer in lookup["answers"]:
            if answer["status"] == "gap":
                assert (
                    not answer["citations"] and answer["gaps"]
                ), f"{lookup['approval_id']}/{answer['tier']} is a gap with no reason given"
            for gap in answer["gaps"]:
                assert len(gap["reason"]) >= 40, f"a reason this short explains nothing: {gap}"
        team = next(a for a in lookup["answers"] if a["tier"] == "team")
        assert team["status"] == "gap", "ownership resolves company-side, never in this artifact"


def test_no_citation_reaches_into_internal() -> None:
    """The artifact is published with web/; internal/ is not."""
    offenders = [c["doc"] for c in _citations() if c["doc"].startswith("internal/")]
    assert not offenders, f"published artifact cites Internal material: {offenders}"


def test_the_renderer_writes_no_graph_and_calls_no_network() -> None:
    """Requirement (b): read-only, the remediation module's no-graph-write invariant."""
    modules = imported_modules(source_text(RENDERER))
    forbidden = ("neo4j", "drydocs_core.neo4j_client", "requests", "httpx", "urllib.request")
    hits = sorted(m for m in modules for f in forbidden if m == f or m.startswith(f + "."))
    assert not hits, f"the lookup renderer imports {hits}"


def test_the_render_rides_the_default_board_run() -> None:
    """An unregistered artifact silently drifts (the J20 incident)."""
    assert "render_remediation_lookup" in imported_modules(source_text(BOARD))
