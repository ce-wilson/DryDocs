"""G66 — the Control-M DESCRIPTION-field token parser.

Every case here pins one rule from the company description-token standards —
the C29 capture (Internal at
``internal/controlm-config/reference/controlm-job-metadata-standards-capture.md``,
sanitized mechanism in ``knowledge/standards/technology/description-field-metadata-plan.md``
§2b) and the C30 greenfield ruling
(``knowledge/standards/technology/controlm-greenfield-job-standard.md`` §5,
normative page ``controlm-guidelines-and-standards.md`` §7). The rules are not
stylistic: each one exists because the obvious implementation gets a real
production value wrong.

All values here are SYNTHETIC — addresses use ``example.invalid`` (RFC-reserved,
can never resolve), accounts, record ids and route ids are invented. The real
corpus is Internal.
"""

from __future__ import annotations

import re
from pathlib import Path

from drydocs_core.orchestration.controlm.description_tokens import (
    DELIVERY_MECHANISMS,
    FOLDER_VARIABLES,
    FTS_INSTANCES,
    GRAMMAR_SENTINEL,
    JOB_ROLES,
    TOKEN_REGISTRY,
    Carrier,
    DescriptionPopulation,
    JobType,
    TokenFindingKind,
    parse_description,
    required_tokens,
    sentinel_coverage,
    validate,
)

#: The pre-sentinel C29 estate shape — ENV + the route pair, no FTS_ID/REC_ID,
#: contacts still per-job. Deliberately kept as the LEGACY corpus: the
#: era-aware completeness check must hold it to the set it was authored to.
WATCHER = (
    "DELIVERY_MECHANISM: MFTS_AGENT | USER: svc_mfts_sample | ENV: FTS0 | "
    "INBOUND_ROUTE: MFTS_RT_IN_SAMPLE_001 | OUTBOUND_ROUTE: MFTS_RT_OUT_SAMPLE_001 | "
    "EMAIL_DL_L3: l3_sample@example.invalid; l3_other@example.invalid | "
    "EMAIL_DL_L2: l2_sample@example.invalid | "
    "SOURCE_CONTACT: source_owner@example.invalid; source_support@example.invalid"
)

PUBLISHER = (
    "JOB_ROLE: PUBLISHER | EMAIL_DL_L3: l3_sample@example.invalid | "
    "EMAIL_DL_L2: l2_sample@example.invalid | "
    "PDN_DL: consumer_a@example.invalid; consumer_b@example.invalid | "
    "PDN_SNOW_QUEUE: NULL"
)

#: The C30 greenfield watcher shape (standard §5.1) — the exact population the
#: G83 repro showed the old registry mis-reading as seven findings.
C30_WATCHER = (
    "DELIVERY_MECHANISM: MFTS_AGENT | USER: svc_mfts_sample | FTS_ID: FTS2 | "
    "REC_ID: 70012,70013 | SOURCE_CONTACT: source_owner@example.invalid"
)


# -- rule 1: pipe is the only delimiter; semicolons live INSIDE a value ----------------


def test_semicolons_stay_inside_one_token() -> None:
    """A multi-address DL is ONE token. Splitting on ';' would shred it into
    fragments that look like keyless segments."""
    parsed = parse_description(WATCHER)
    assert parsed.value("SOURCE_CONTACT") == (
        "source_owner@example.invalid; source_support@example.invalid"
    )
    # the inner separator is applied on request, not during the split
    assert parsed.values("SOURCE_CONTACT") == [
        "source_owner@example.invalid",
        "source_support@example.invalid",
    ]
    assert parsed.values("EMAIL_DL_L3") == [
        "l3_sample@example.invalid",
        "l3_other@example.invalid",
    ]


def test_rec_id_splits_on_comma_not_semicolon() -> None:
    """C30 §5.1: REC_ID is the one comma-separated token — a source-system
    reference list, explicitly not a route pair. The inner separator comes
    from the spec, not from a global constant."""
    parsed = parse_description(C30_WATCHER)
    assert parsed.value("REC_ID") == "70012,70013"
    assert parsed.values("REC_ID") == ["70012", "70013"]


# -- rule 2: split on the FIRST colon only ---------------------------------------------


def test_value_may_contain_colons() -> None:
    """`SeriesSLA: 17:00 EST` is the standard's own example. Splitting on
    every colon truncates the value at the time separator. (Tagged: the
    grammar formally governs the sentinel population, and these keys are
    unregistered — untagged they would be prose.)"""
    parsed = parse_description("DD1|datasetSeriesName: SAMPLE SERIES |SeriesSLA: 17:00 EST")
    assert parsed.value("SeriesSLA") == "17:00 EST"
    assert parsed.value("datasetSeriesName") == "SAMPLE SERIES"


def test_a_url_valued_token_survives_the_split() -> None:
    parsed = parse_description("DD1|docLink: https://example.invalid/runbook#step:3")
    assert parsed.value("docLink") == "https://example.invalid/runbook#step:3"


# -- rule 3: whitespace tolerance on both sides ----------------------------------------


def test_both_spacings_parse_identically() -> None:
    """The wild carries `| USER: x` and `|USER:x`; the standard's own
    examples are inconsistent, so tolerance is not a nicety."""
    loose = parse_description("DELIVERY_MECHANISM:  MFTS_AGENT  |   USER:   svc_a  ")
    tight = parse_description("DELIVERY_MECHANISM:MFTS_AGENT|USER:svc_a")
    assert loose.tokens == tight.tokens == {
        "DELIVERY_MECHANISM": "MFTS_AGENT",
        "USER": "svc_a",
    }


def test_empty_segments_are_skipped_not_reported() -> None:
    parsed = parse_description("| JOB_ROLE: PUBLISHER ||  |")
    assert parsed.tokens == {"JOB_ROLE": "PUBLISHER"}
    assert parsed.findings == []


# -- rule 4: the literal NULL is 'deliberately unassigned', not 'absent' ---------------


def test_literal_null_becomes_none_and_is_distinct_from_a_missing_key() -> None:
    parsed = parse_description(PUBLISHER)
    assert parsed.value("PDN_SNOW_QUEUE") is None
    assert "PDN_SNOW_QUEUE" in parsed.tokens  # present, explicitly unassigned
    assert "SOURCE_CONTACT" not in parsed.tokens  # genuinely absent
    assert parsed.values("PDN_SNOW_QUEUE") == []


def test_an_explicit_null_route_satisfies_the_completeness_check() -> None:
    """Non-MFTS mechanisms still emit both route tokens carrying NULL, which
    is what makes the parse total — the key is always found. A C29-era
    description, so the legacy required set applies."""
    sftp = parse_description(
        "DELIVERY_MECHANISM: SFTP_DIRECT | USER: svc_sftp | ENV: PROD | "
        "INBOUND_ROUTE: NULL | OUTBOUND_ROUTE: NULL | "
        "EMAIL_DL_L3: l3@example.invalid | EMAIL_DL_L2: l2@example.invalid | "
        "SOURCE_CONTACT: owner@example.invalid"
    )
    assert sftp.value("INBOUND_ROUTE") is None
    assert not [f for f in validate(sftp, JobType.FILE_WATCHER)]


# -- rule 5: unknown keys are preserved, never dropped ---------------------------------


def test_unknown_keys_are_kept_verbatim_and_reported_informationally() -> None:
    """C16 makes a bare key a legal team-local annotation. Dropping it loses
    evidence; promoting it breaks the prefix governance."""
    parsed = parse_description("JOB_ROLE: PUBLISHER | runbookHint: see wiki | myNote: tbd")
    assert parsed.value("runbookHint") == "see wiki"
    assert sorted(parsed.unknown_keys) == ["myNote", "runbookHint"]
    kinds = {f.kind for f in parsed.findings}
    assert kinds == {TokenFindingKind.UNKNOWN_KEY}
    # unknown keys never reach the SQL column projection
    assert "runbookHint" not in parsed.as_columns()


# -- rule 6: a bad value is a finding, never an exception ------------------------------


def test_value_outside_the_vocabulary_is_reported_and_still_captured() -> None:
    parsed = parse_description("DELIVERY_MECHANISM: CARRIER_PIGEON | USER: svc_a")
    assert parsed.value("DELIVERY_MECHANISM") == "CARRIER_PIGEON"  # captured, not coerced
    finding = next(f for f in parsed.findings if f.kind is TokenFindingKind.VALUE_NOT_IN_VOCABULARY)
    assert finding.key == "DELIVERY_MECHANISM"
    assert "CARRIER_PIGEON" in finding.detail


def test_every_registered_mechanism_passes_its_own_vocabulary() -> None:
    for mechanism in DELIVERY_MECHANISMS:
        parsed = parse_description(f"DELIVERY_MECHANISM: {mechanism}")
        assert not [
            f for f in parsed.findings if f.kind is TokenFindingKind.VALUE_NOT_IN_VOCABULARY
        ]


def test_fts_id_is_a_shape_not_a_closed_enum() -> None:
    """C30 §5.1: known members are documentation; the check is the shape
    ``FTS[A-Z]*[0-9]+`` because new instances appear — and FTSCAT1 already
    breaks a naive FTS<digit> pattern. A value that kept its version fragment
    ('ST 6.0 - FTS2') is the finding the author must fix."""
    for member in FTS_INSTANCES:
        assert parse_description(f"DD1|FTS_ID: {member}").findings == []
    unlisted_but_shaped = parse_description("DD1|FTS_ID: FTS9")
    assert unlisted_but_shaped.findings == []  # the shape decides, not the tuple
    versioned = parse_description("DD1|FTS_ID: ST 6.0 - FTS2")
    bad = [f for f in versioned.findings if f.kind is TokenFindingKind.VALUE_NOT_IN_VOCABULARY]
    assert [f.key for f in bad] == ["FTS_ID"]


def test_job_role_carries_the_c30_values_and_the_c29_one() -> None:
    """§7.2's whole set is PLACEMENT / TRUST_INGEST; PUBLISHER is the C29
    capture the estate still carries. Aliases suggest, values decide — all
    three stay legal."""
    assert set(JOB_ROLES) == {"PUBLISHER", "PLACEMENT", "TRUST_INGEST"}
    for role in JOB_ROLES:
        parsed = parse_description(f"DD1|JOB_ROLE: {role}")
        assert not [
            f for f in parsed.findings if f.kind is TokenFindingKind.VALUE_NOT_IN_VOCABULARY
        ]


# -- the DD1| sentinel and the three populations (§7.5) ---------------------------------


def test_the_sentinel_is_stripped_and_never_reported() -> None:
    """The marker itself never becomes a token and never becomes a finding —
    the parser must not report the one thing the standard makes mandatory as
    a defect."""
    parsed = parse_description("DD1|DELIVERY_MECHANISM: MFTS_AGENT | FTS_ID: FTS2")
    assert parsed.population is DescriptionPopulation.TAGGED
    assert parsed.grammar_version == 1
    assert set(parsed.tokens) == {"DELIVERY_MECHANISM", "FTS_ID"}
    assert parsed.findings == []


def test_legacy_prose_manufactures_no_tokens() -> None:
    """Waterfall prose that happens to contain colons must not come back as
    'tokens' with unknown-key findings — that made prose indistinguishable
    from a legitimate C16 team-local annotation. Untagged means unread."""
    parsed = parse_description("NOTE: rerun after 08:00 | contact: ops team")
    assert parsed.population is DescriptionPopulation.UNTAGGED
    assert parsed.tokens == {}
    assert parsed.findings == []


def test_the_sentinel_only_counts_at_position_zero() -> None:
    """startswith, no strip, no substring search (§7.5): a description that
    QUOTES the convention in prose cannot false-positive, and the predicate
    stays the cheapest available to a SQL scan."""
    quoted = parse_description(f"authored descriptions start with {GRAMMAR_SENTINEL} per the standard")
    assert quoted.population is DescriptionPopulation.UNTAGGED
    padded = parse_description(" DD1|USER: svc_a")
    assert padded.population is DescriptionPopulation.UNTAGGED


def test_a_future_grammar_version_reads_side_by_side() -> None:
    """The digit is a VERSION, not a template id: DD2 must parse today so a
    grammar migration can announce itself. Template selection is TASKTYPE
    plus the registered JOB_ROLE token (§7.2), never the sentinel."""
    parsed = parse_description("DD2|USER: svc_a")
    assert parsed.population is DescriptionPopulation.TAGGED
    assert parsed.grammar_version == 2
    assert parsed.value("USER") == "svc_a"


def test_prose_yields_no_tokens_and_says_so() -> None:
    """The correct answer for most of the estate: the standard has not been
    adopted here. Not a defect — no findings, and validate() manufactures
    none either."""
    parsed = parse_description("Contol-M File Watcher for TOK")
    assert parsed.tokens == {} and parsed.findings == []
    assert not parsed.is_structured
    assert parsed.population is DescriptionPopulation.UNTAGGED
    assert validate(parsed, JobType.FILE_WATCHER) == []


def test_the_generator_boilerplate_literal_is_its_own_population() -> None:
    """The DPL stub stamps its literals verbatim via get_description(), and
    the integration plan's item E1 keys machine-generated provenance on that
    match. The sentinel PARTITIONS the field so the two readers never
    collide: the literal population yields nothing and is never a defect."""
    for literal in (
        "Generated Control-M Folder",
        "Generated job to trigger DPL transformation in AWS for dataset: sample_ds",
    ):
        parsed = parse_description(literal)
        assert parsed.population is DescriptionPopulation.GENERATOR_LITERAL
        assert parsed.tokens == {} and parsed.findings == []
        assert not parsed.is_structured
        assert validate(parsed, JobType.PUBLISHER) == []


def test_empty_and_none_are_safe() -> None:
    for empty in (None, "", "   "):
        parsed = parse_description(empty)
        assert parsed.tokens == {} and parsed.findings == []
        assert parsed.population is DescriptionPopulation.UNTAGGED


def test_sentinel_coverage_is_tagged_over_total() -> None:
    """Adoption, not compliance: tagged ÷ total grows; 'how much metadata is
    wrong' never closes. None (no description at all) counts as untagged."""
    cov = sentinel_coverage(
        ["DD1|USER: svc_a", "legacy prose", None, "Generated Control-M Folder"]
    )
    assert (cov.tagged, cov.total) == (1, 4)
    assert cov.ratio == 0.25
    assert sentinel_coverage([]).ratio == 0.0


# -- duplicate keys: first wins, matching the Oracle parse ------------------------------


def test_duplicate_key_keeps_the_first_and_reports_the_second() -> None:
    """The standard's Oracle statements use REGEXP_SUBSTR(..., 1, 1) — the
    first occurrence. A Python extract that took the last would silently
    disagree with the SQL extract of the same row."""
    parsed = parse_description("USER: first | USER: second")
    assert parsed.value("USER") == "first"
    assert [f.kind for f in parsed.findings] == [TokenFindingKind.DUPLICATE_KEY]


# -- the SQL projection: Python-side and SQL-side extracts must be comparable -----------


def test_registered_tokens_project_onto_their_oracle_columns() -> None:
    columns = parse_description(WATCHER).as_columns()
    assert columns["DELIVERY_MECHANISM"] == "MFTS_AGENT"
    assert columns["USER_ID"] == "svc_mfts_sample"
    assert columns["MFTS_INBOUND_ROUTE_ID"] == "MFTS_RT_IN_SAMPLE_001"
    assert columns["SOURCE_CONTACT"].startswith("source_owner@example.invalid")


# -- completeness per job type: era-aware (G83) -----------------------------------------


def test_the_two_worked_examples_are_complete_for_their_job_types() -> None:
    """The C29 corpus validates clean against the era it was authored to —
    the greenfield standard governs what gets AUTHORED next; it cannot
    retroactively unwrite the deployed estate."""
    assert validate(parse_description(WATCHER), JobType.FILE_WATCHER) == []
    assert validate(parse_description(PUBLISHER), JobType.PUBLISHER) == []


def test_the_c30_watcher_description_validates_clean() -> None:
    """THE G83 REPRO, inverted. Before the registry caught up with C30 this
    exact shape came back with SEVEN findings — unknown_key on FTS_ID and
    REC_ID, missing_required_token on ENV, INBOUND_ROUTE, OUTBOUND_ROUTE,
    EMAIL_DL_L3 and EMAIL_DL_L2 — on a description that is exactly what the
    ruled standard requires."""
    parsed = parse_description(C30_WATCHER)
    assert parsed.unknown_keys == []
    assert validate(parsed, JobType.FILE_WATCHER) == []
    tagged = parse_description(GRAMMAR_SENTINEL + C30_WATCHER)
    assert validate(tagged, JobType.FILE_WATCHER) == []


def test_a_tagged_c30_command_job_validates_clean() -> None:
    """§5.2: 'that is the whole set' — JOB_ROLE alone, with the sentinel."""
    for role in ("PLACEMENT", "TRUST_INGEST"):
        parsed = parse_description(f"DD1|JOB_ROLE: {role}")
        assert validate(parsed, JobType.PUBLISHER) == []


def test_missing_required_tokens_are_named() -> None:
    parsed = parse_description("JOB_ROLE: PUBLISHER")
    missing = {
        f.key for f in validate(parsed, JobType.PUBLISHER)
        if f.kind is TokenFindingKind.MISSING_REQUIRED_TOKEN
    }
    assert missing == {"PDN_DL", "PDN_SNOW_QUEUE", "EMAIL_DL_L3", "EMAIL_DL_L2"}


def test_retired_tokens_parse_as_known_not_unregistered() -> None:
    """Retire-in-place, never delete: the estate still carries these, and
    deleting an entry would silently reclassify real estate data as somebody's
    private C16 annotation — the one reading governance cannot afford."""
    parsed = parse_description(WATCHER)
    assert "ENV" in parsed.tokens
    assert "ENV" not in parsed.unknown_keys
    for key in (
        "ENV",
        "INBOUND_ROUTE",
        "OUTBOUND_ROUTE",
        "PDN_SNOW_QUEUE",
        "PDN_DL",
        "EMAIL_DL_L2",
        "EMAIL_DL_L3",
    ):
        assert TOKEN_REGISTRY[key].retired_by, f"{key} must name the ruling that retired it"


def test_required_tokens_never_demand_a_retired_token() -> None:
    """G83 clause (c): a job authored to C30 validates clean without the
    retired set. The exported required_tokens() IS the current-era set."""
    for job_type in (JobType.FILE_WATCHER, JobType.PUBLISHER):
        for key in required_tokens(job_type):
            assert not TOKEN_REGISTRY[key].retired_by
    assert set(required_tokens(JobType.FILE_WATCHER)) == {
        "DELIVERY_MECHANISM",
        "USER",
        "FTS_ID",
        "REC_ID",
        "SOURCE_CONTACT",
    }
    assert set(required_tokens(JobType.PUBLISHER)) == {"JOB_ROLE"}


def test_contact_tokens_left_the_per_job_required_sets() -> None:
    """C30 §5.3: contacts are folder-scope documentation — the per-job
    EMAIL_DL_* tokens duplicated a folder fact per job and left with the
    ruling. The per-type discriminators stay put."""
    for job_type in (JobType.FILE_WATCHER, JobType.PUBLISHER):
        required = required_tokens(job_type)
        assert "EMAIL_DL_L2" not in required and "EMAIL_DL_L3" not in required
    assert "JOB_ROLE" not in required_tokens(JobType.FILE_WATCHER)
    assert "DELIVERY_MECHANISM" not in required_tokens(JobType.PUBLISHER)


# -- contacts changed carrier, they did not vanish (G83 clause d) -----------------------


def test_folder_contacts_registered_under_both_spellings() -> None:
    """The three C30 folder-scope contacts, plus the pre-rename twins, so a
    live extract authored either way still resolves. EMAIL_DL_PDN has no
    twin — the folder-variable table never carried a PDN member before C30."""
    for key in (
        "EMAIL_DL_L2",
        "EMAIL_DL_L3",
        "EMAIL_DL_PDN",
        "L2_EMAIL_DL_NM",
        "L3_EMAIL_DL_NM",
    ):
        assert key in FOLDER_VARIABLES, f"{key} missing from the folder register"
        assert FOLDER_VARIABLES[key].carrier is Carrier.FOLDER_VARIABLE


def test_the_two_contact_kinds_are_never_collapsed() -> None:
    """Same carrier, same prefix, different audience: L2/L3 are internal
    support tiers, PDN is downstream BUSINESS users told a delay affects
    them. Different ontology role — the register must never collapse them."""
    assert FOLDER_VARIABLES["EMAIL_DL_L2"].ontology_term == "ex:supportContact"
    assert FOLDER_VARIABLES["EMAIL_DL_L3"].ontology_term == "ex:supportContact"
    assert FOLDER_VARIABLES["EMAIL_DL_PDN"].ontology_term == "ex:consumerContact"


# -- the registry is the shared contract with the published register --------------------


def test_every_registered_token_declares_a_landing_column_and_a_term() -> None:
    """The register in the standards pages is generated from these fields by
    hand; a spec missing either one would publish a blank cell."""
    for key, spec in TOKEN_REGISTRY.items():
        assert spec.key == key
        assert spec.sql_column, f"{key} has no SQL landing column"
        assert spec.ontology_term, f"{key} has no proposed ontology term"
        assert spec.carrier is Carrier.DESCRIPTION


# -- the registry-vs-standard agreement test (the G83 deliverable) ----------------------

_GREENFIELD_STANDARD = (
    Path(__file__).resolve().parents[2]
    / "knowledge"
    / "standards"
    / "technology"
    / "controlm-greenfield-job-standard.md"
)


def _example_block(text: str, section: str, next_section: str) -> str:
    start = text.index(section)
    end = text.index(next_section, start)
    fence = re.search(r"```\n(.*?)```", text[start:end], re.DOTALL)
    assert fence is not None, f"no fenced example under {section}"
    return fence.group(1)


def _example_keys(block: str) -> set[str]:
    return set(re.findall(r"([A-Z][A-Z0-9_]*):", block))


def test_the_registry_and_the_greenfield_standard_agree() -> None:
    """G83 clause (e), the deliverable: the next ruling cannot land in prose
    alone. The standard's own §5.1/§5.2 worked examples ARE the per-job-type
    token sets — parse them and hold required_tokens() to them, so an edit to
    either side without the other fails here."""
    text = _GREENFIELD_STANDARD.read_text(encoding="utf-8")
    watcher = _example_keys(_example_block(text, "### 5.1", "### 5.2"))
    publisher = _example_keys(_example_block(text, "### 5.2", "### 5.3"))
    assert watcher == set(required_tokens(JobType.FILE_WATCHER))
    assert publisher == set(required_tokens(JobType.PUBLISHER))
    retired = {key for key, spec in TOKEN_REGISTRY.items() if spec.retired_by}
    assert not retired & (watcher | publisher), "a retired token reappeared in the standard"
    roles = set(
        re.findall(r"JOB_ROLE:\s*([A-Z_]+)", _example_block(text, "### 5.2", "### 5.3"))
    )
    assert roles <= set(JOB_ROLES)
