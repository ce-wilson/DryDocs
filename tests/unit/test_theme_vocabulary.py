"""G77 — one theme vocabulary, two corpora.

The folder-scope ``THEME`` description token and the docmeta capture
envelope's ``themes`` field classify against the SAME lob-product-team
skos:ConceptScheme and resolve to the SAME concept IRIs. Every case here pins
one clause of the item: resolution by IRI never by label (d), unrecognised
values returned not raised (a), the token never joins a job-level required set
(a), the three-way unclassified / out-of-scope split reported apart (c), and
zero graph writes throughout.
"""

from __future__ import annotations

import json
from pathlib import Path

from drydocs_core.ontology.concept_scheme import (
    LOB_PRODUCT_TEAM_SCHEME,
    ThemeStatus,
    load_concept_scheme,
    theme_status,
)
from drydocs_core.orchestration.controlm.description_tokens import (
    TOKEN_REGISTRY,
    JobType,
    TokenFindingKind,
    parse_description,
    required_tokens,
    theme_coverage,
    validate,
)
from drydocs_docmeta.connectors.base import RawPage
from drydocs_docmeta.manifest import CaptureManifest

SCHEME = load_concept_scheme()
CCB = f"{LOB_PRODUCT_TEAM_SCHEME}#CCB"
PL_AUTO = f"{LOB_PRODUCT_TEAM_SCHEME}#PL_AUTO"


# -- the scheme reader --------------------------------------------------------


def test_concept_iri_is_scheme_hash_notation_and_broader_is_the_parent_link():
    """Gate §A2's IRI form; skos:broader is the parent_* link read as SKOS."""
    assert SCHEME.uri == LOB_PRODUCT_TEAM_SCHEME
    assert SCHEME.resolve("PL_AUTO") == PL_AUTO
    assert SCHEME.broader_closure(PL_AUTO) == (PL_AUTO, CCB)
    assert SCHEME.concepts[CCB].broader is None


def test_labels_never_resolve_only_notations_and_iris_do():
    """(d) joined by CONCEPT IRI, never by label — label drift between corpora
    cannot fork the join because a label is not a valid value anywhere."""
    assert SCHEME.resolve("Auto") is None
    assert SCHEME.resolve("Consumer & Community Banking") is None
    assert SCHEME.resolve(CCB) == CCB
    assert SCHEME.resolve("CCB") == CCB
    res = SCHEME.resolve_all(["CCB", "Auto", PL_AUTO, "CCB"])
    assert res.iris == (CCB, PL_AUTO)  # deduplicated, order kept
    assert res.unrecognised == ("Auto",)  # returned, never raised


def test_dev_teams_are_not_concepts():
    """The scheme declares not_concepts: [dev_teams] — an org unit is never a
    subject, so a team id must not resolve."""
    assert all(c.tier != "dev_teams" for c in SCHEME.concepts.values())


# -- (a) the Control-M folder-block token --------------------------------------


def test_theme_token_resolves_notations_and_iris_inside_the_tagged_block():
    parsed = parse_description(f"DD1|THEME: CCB; {PL_AUTO}")
    assert parsed.population.value == "tagged"
    assert parsed.values("THEME") == ["CCB", PL_AUTO]
    assert parsed.theme_iris(SCHEME) == (CCB, PL_AUTO)
    assert parsed.findings == []


def test_unrecognised_theme_value_is_a_finding_not_an_exception():
    """Aliases suggest, values decide: the label 'Auto' is reported and the
    rest of the block still parses."""
    parsed = parse_description("DD1|THEME: Auto; CCB | OWNER: team-x")
    kinds = [(f.kind, f.key) for f in parsed.findings]
    assert (TokenFindingKind.VALUE_NOT_IN_VOCABULARY, "THEME") in kinds
    assert parsed.theme_iris(SCHEME) == (CCB,)
    assert "Auto" in next(f.detail for f in parsed.findings if f.key == "THEME")


def test_theme_is_folder_scope_and_never_required_of_any_job_type():
    """JobType.FOLDER keeps the token out of both job-level required sets, so
    the registry-vs-greenfield-standard agreement test is untouched and no
    watcher or publisher ever gets a MISSING_REQUIRED_TOKEN for THEME."""
    spec = TOKEN_REGISTRY["THEME"]
    assert spec.job_type is JobType.FOLDER
    assert spec.optional is True
    assert spec.concept_scheme == LOB_PRODUCT_TEAM_SCHEME
    assert "THEME" not in required_tokens(JobType.FILE_WATCHER)
    assert "THEME" not in required_tokens(JobType.PUBLISHER)
    # coverage, not compliance: a tagged folder without THEME is not a defect
    assert required_tokens(JobType.FOLDER) == ()
    parsed = parse_description("DD1|OWNER: team-x")
    assert not [f for f in validate(parsed, JobType.FOLDER) if f.key == "THEME"]


def test_theme_coverage_reports_unread_apart_from_unclassified():
    cov = theme_coverage(
        [
            "DD1|THEME: CCB",  # classified
            "DD1|OWNER: team-x",  # tagged, no theme -> unclassified (pending)
            "legacy prose about nothing",  # untagged -> unread, not pending
            None,
        ],
        SCHEME,
    )
    assert (cov.classified, cov.unclassified, cov.unread) == (1, 1, 2)
    assert cov.ratio == 0.5  # classified ÷ tagged, never ÷ total


# -- (b)/(c) the scraped-document envelope -------------------------------------


def _pages() -> list[RawPage]:
    return [
        RawPage(location="https://x.invalid/a", body=b"alpha"),
        RawPage(location="https://x.invalid/b", body=b"beta"),
        RawPage(location="https://x.invalid/c", body=b"gamma"),
    ]


def _build(classification: str, themes: dict | None) -> CaptureManifest:
    return CaptureManifest.build(
        source_id="s",
        connector="web",
        captured_at="2026-08-21T00:00:00Z",
        corpus_id="a-corpus",
        classification=classification,
        pages=_pages(),
        themes=themes,
        scheme=SCHEME,
    )


def test_envelope_carries_the_same_iris_the_token_resolves_to():
    """(b) the same field, the same vocabulary, the same IRI — the join key
    shared with the folder block. Labels are dropped and surfaced as findings."""
    themes = {"https://x.invalid/a": ["CCB", "Auto"], "https://x.invalid/b": [PL_AUTO]}
    m = _build("Internal", themes)
    by_loc = {p.location: p for p in m.pages}
    assert by_loc["https://x.invalid/a"].themes == (CCB,)
    assert by_loc["https://x.invalid/b"].themes == (PL_AUTO,)
    assert (
        by_loc["https://x.invalid/a"].themes[0]
        == parse_description("DD1|THEME: CCB").theme_iris(SCHEME)[0]
    )
    findings = CaptureManifest.theme_findings(themes, SCHEME)
    assert [(f.location, f.value) for f in findings] == [("https://x.invalid/a", "Auto")]


def test_unclassified_and_out_of_scope_are_different_values_and_counted_apart():
    """(c) C34's split implemented where it bites: an External source is out of
    scope PERMANENTLY (never pending), an internal page without a theme is
    pending. Coverage reports the two apart and the ratio excludes scope."""
    internal = _build("Internal", {"https://x.invalid/a": ["CCB"]})
    cov = internal.theme_coverage()
    assert (cov.classified, cov.unclassified, cov.out_of_scope) == (1, 2, 0)
    assert cov.ratio == 1 / 3

    external = _build("External", {"https://x.invalid/a": ["CCB"]})
    assert {p.theme_status for p in external.pages} == {ThemeStatus.OUT_OF_SCOPE.value}
    assert all(p.themes == () for p in external.pages)  # out of scope carries no theme
    cov = external.theme_coverage()
    assert (cov.classified, cov.unclassified, cov.out_of_scope) == (0, 0, 3)
    assert cov.ratio == 0.0 and cov.in_scope == 0

    assert theme_status("External", None) is ThemeStatus.OUT_OF_SCOPE
    assert theme_status("Internal-Public", None) is ThemeStatus.UNCLASSIFIED


def test_theme_fields_round_trip_and_pre_g77_manifests_read_as_unclassified(tmp_path: Path):
    m = _build("Internal", {"https://x.invalid/a": ["CCB"]})
    m.write(tmp_path)
    back = CaptureManifest.read(tmp_path)
    assert back == m
    # an older manifest with no theme keys at all
    raw = json.loads((tmp_path / "capture-manifest.json").read_text(encoding="utf-8"))
    for p in raw["pages"]:
        p.pop("themes")
        p.pop("theme_status")
    (tmp_path / "capture-manifest.json").write_text(json.dumps(raw), encoding="utf-8")
    old = CaptureManifest.read(tmp_path)
    assert all(p.themes == () and p.theme_status == "unclassified" for p in old.pages)


def test_zero_graph_writes():
    """The field, its validation and the split — no Cypher anywhere near it."""
    for module in ("drydocs_core/ontology/concept_scheme.py", "drydocs_docmeta/manifest.py"):
        text = Path(module).read_text(encoding="utf-8")
        assert "MERGE" not in text and "CREATE" not in text, module
