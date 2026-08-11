"""G66 — the Control-M DESCRIPTION-field token parser.

Every case here pins one rule from the company description-metadata standard
(captured Internal at
``internal/controlm-config/reference/controlm-job-metadata-standards-capture.md``,
sanitized mechanism in ``knowledge/standards/technology/description-field-metadata-plan.md``
§2b). The rules are not stylistic: each one exists because the obvious
implementation gets a real production value wrong.

All values here are SYNTHETIC — addresses use ``example.invalid`` (RFC-reserved,
can never resolve), accounts and route ids are invented. The real corpus is
Internal.
"""

from __future__ import annotations

from drydocs_core.orchestration.controlm.description_tokens import (
    DELIVERY_MECHANISMS,
    TOKEN_REGISTRY,
    Carrier,
    JobType,
    TokenFindingKind,
    parse_description,
    required_tokens,
    validate,
)

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


# -- rule 2: split on the FIRST colon only ---------------------------------------------


def test_value_may_contain_colons() -> None:
    """`SeriesSLA: 17:00 EST` is the standard's own example. Splitting on
    every colon truncates the value at the time separator."""
    parsed = parse_description("datasetSeriesName: SAMPLE SERIES |SeriesSLA: 17:00 EST")
    assert parsed.value("SeriesSLA") == "17:00 EST"
    assert parsed.value("datasetSeriesName") == "SAMPLE SERIES"


def test_a_url_valued_token_survives_the_split() -> None:
    parsed = parse_description("docLink: https://example.invalid/runbook#step:3")
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
    is what makes the parse total — the key is always found."""
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


# -- prose, boilerplate, and empty input ------------------------------------------------


def test_prose_yields_no_tokens_and_says_so() -> None:
    """The correct answer for most of the estate: the standard has not been
    adopted here. It must not raise and must not invent tokens."""
    parsed = parse_description("Contol-M File Watcher for TOK")
    assert parsed.tokens == {}
    assert not parsed.is_structured
    assert [f.kind for f in parsed.findings] == [TokenFindingKind.UNPARSEABLE_SEGMENT]


def test_the_generator_boilerplate_literal_is_prose() -> None:
    """The DPL stub stamps 'Generated Control-M Folder' verbatim, and the
    integration plan's item E1 keys machine-generated provenance on that
    exact match. It carries no tokens — which is precisely the collision
    recorded in the capture: adding a token block would break E1."""
    parsed = parse_description("Generated Control-M Folder")
    assert not parsed.is_structured


def test_empty_and_none_are_safe() -> None:
    for empty in (None, "", "   "):
        parsed = parse_description(empty)
        assert parsed.tokens == {} and parsed.findings == []


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


# -- completeness per job type ----------------------------------------------------------


def test_the_two_worked_examples_are_complete_for_their_job_types() -> None:
    assert validate(parse_description(WATCHER), JobType.FILE_WATCHER) == []
    assert validate(parse_description(PUBLISHER), JobType.PUBLISHER) == []


def test_missing_required_tokens_are_named() -> None:
    parsed = parse_description("JOB_ROLE: PUBLISHER")
    missing = {
        f.key for f in validate(parsed, JobType.PUBLISHER)
        if f.kind is TokenFindingKind.MISSING_REQUIRED_TOKEN
    }
    assert missing == {"PDN_DL", "PDN_SNOW_QUEUE", "EMAIL_DL_L3", "EMAIL_DL_L2"}


def test_shared_tokens_are_required_of_both_job_types() -> None:
    for job_type in (JobType.FILE_WATCHER, JobType.PUBLISHER):
        required = required_tokens(job_type)
        assert "EMAIL_DL_L2" in required and "EMAIL_DL_L3" in required
    assert "JOB_ROLE" not in required_tokens(JobType.FILE_WATCHER)
    assert "DELIVERY_MECHANISM" not in required_tokens(JobType.PUBLISHER)


# -- the registry is the shared contract with the published register --------------------


def test_every_registered_token_declares_a_landing_column_and_a_term() -> None:
    """The register in description-field-metadata-plan.md §2b is generated
    from these fields by hand; a spec missing either one would publish a
    blank cell."""
    for key, spec in TOKEN_REGISTRY.items():
        assert spec.key == key
        assert spec.sql_column, f"{key} has no SQL landing column"
        assert spec.ontology_term, f"{key} has no proposed ontology term"
        assert spec.carrier is Carrier.DESCRIPTION
