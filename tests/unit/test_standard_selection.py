"""G94 — the standard-selection tree, and the executable proof the DD digit never selects.

The guardrail test in clause (b) is the reason this file exists as much as the
tree is. Guidelines §7.5 and G84 clause (c) rule the ``DD`` digit a grammar
VERSION that MUST NOT select a template or a standard, and a rule that lives only
in a docstring is a rule the next person reaches past. Here it is asserted two
ways: STRUCTURALLY, because no version parameter exists to pass, and
FUNCTIONALLY, because the same job under ``DD1|`` and a hypothetical ``DD2|``
selects the same standard.
"""

from __future__ import annotations

import inspect

from drydocs_core.orchestration.controlm.description_tokens import (
    FOLDER_VARIABLES,
    TOKEN_REGISTRY,
    JobType,
    parse_description,
    required_tokens,
)
from drydocs_core.orchestration.controlm.standard_selection import (
    ENGINE_STANDARDS,
    ENGINE_TOKEN_SETS,
    REASON_ENGINE_UNCLASSIFIED,
    REASON_ENGINE_UNRULED,
    REASON_FILE_WATCHER,
    REASON_NO_EXECUTABLE,
    REASON_UNSELECTABLE,
    STANDARD_FILE_WATCHER,
    STANDARD_GENERIC,
    generic_required_tokens,
    select_standard,
    selection_coverage,
)

#: Real launcher spellings, taken from config/launcher-registry.yaml rather than
#: invented, so a registry edit that breaks classification breaks this too.
DPL_LAUNCHER = "dt-pipelines-launcher-1.2.jar"
ABINITIO_LAUNCHER = "air"
INFORMATICA_LAUNCHER = "pmcmd"


# ---------------------------------------------------------------------------
# (a) ONE FUNCTION, ONE ANSWER — the tree
# ---------------------------------------------------------------------------
def test_a_file_watcher_selects_the_file_watcher_standard() -> None:
    got = select_standard(JobType.FILE_WATCHER)
    assert got.standard_id == STANDARD_FILE_WATCHER
    assert got.branch == "file-watcher"
    assert got.reason == REASON_FILE_WATCHER
    assert got.required == required_tokens(JobType.FILE_WATCHER)
    assert got.engine is None, "a file watcher runs no ETL engine; the branch must not ask"


def test_a_command_job_selects_on_its_engine_first() -> None:
    """Engine FIRST, per the 2026-08-12 direction — before any role question."""
    for launcher, expected in (
        (DPL_LAUNCHER, "DPL"),
        (ABINITIO_LAUNCHER, "ABINITIO"),
        (INFORMATICA_LAUNCHER, "INFORMATICA"),
    ):
        got = select_standard(JobType.PUBLISHER, executable=launcher)
        assert got.engine == expected, f"{launcher!r} should classify as {expected}"
        assert got.standard_id == ENGINE_STANDARDS[expected]
        assert got.branch == "engine"
        assert got.classifier_rule, "the classifier rule is carried so a selection is traceable"


def test_the_engine_outranks_the_job_role() -> None:
    """'Selects on its ETL ENGINE FIRST' is an ordering claim, so assert the order."""
    got = select_standard(JobType.PUBLISHER, job_role="PLACEMENT", executable=DPL_LAUNCHER)
    assert got.branch == "engine"
    assert got.standard_id == ENGINE_STANDARDS["DPL"]
    assert got.job_role == "PLACEMENT", "the role is still reported, just not decisive"


def test_a_non_engine_launcher_falls_back_to_generic_and_says_why() -> None:
    got = select_standard(JobType.PUBLISHER, job_role="PUBLISHER", executable="java")
    assert got.standard_id == STANDARD_GENERIC
    assert got.reason == REASON_ENGINE_UNCLASSIFIED
    assert got.unselectable is False, "a classified-but-non-ETL launcher is not a gap"


def test_selection_is_separate_from_validation() -> None:
    """The parser must not acquire a policy opinion, and vice versa.

    ``validate`` still takes a ``JobType`` and knows nothing about standards;
    the selector returns an identity and never parses a description.
    """
    from drydocs_core.orchestration.controlm import description_tokens as dt

    assert "standard" not in inspect.signature(dt.validate).parameters
    assert "parsed" not in inspect.signature(select_standard).parameters


# ---------------------------------------------------------------------------
# (b) THE GUARDRAIL BECOMES A TEST — the DD digit never selects
# ---------------------------------------------------------------------------
def test_no_grammar_version_parameter_exists_to_pass() -> None:
    """Structural half: the digit is ABSENT from the signature, not merely unused.

    Unused is a convention; absent is enforcement. A future contributor reaching
    for the version slot as a selector has nowhere to put it.
    """
    params = set(inspect.signature(select_standard).parameters)
    for forbidden in ("version", "grammar_version", "sentinel", "dd", "description"):
        assert forbidden not in params, (
            f"select_standard grew a {forbidden!r} parameter. The DD digit is a grammar "
            "VERSION and MUST NOT select a standard (guidelines §7.5, G84 (c)); spending "
            "the version slot on selection leaves the first grammar change with no way to "
            "announce itself."
        )


def test_the_same_job_selects_the_same_standard_under_dd1_and_dd2() -> None:
    """Functional half: parse under both sentinels, select, compare."""
    body = "JOB_ROLE:PLACEMENT|DevX-project:PROJ"
    v1 = parse_description(f"DD1|{body}")
    v2 = parse_description(f"DD2|{body}")
    assert v1.grammar_version == 1 and v2.grammar_version == 2, (
        "precondition: the two descriptions must actually differ in grammar version, "
        "or this test proves nothing"
    )

    picks = [
        select_standard(
            JobType.PUBLISHER,
            job_role=parsed.tokens.get("JOB_ROLE"),
            executable=DPL_LAUNCHER,
        )
        for parsed in (v1, v2)
    ]
    assert picks[0].standard_id == picks[1].standard_id
    assert picks[0].required == picks[1].required
    assert picks[0].reason == picks[1].reason


def test_the_version_does_not_change_selection_on_the_generic_branch_either() -> None:
    """The fence holds where there is no engine to dominate the answer."""
    picks = [
        select_standard(JobType.PUBLISHER, job_role=parse_description(text).tokens.get("JOB_ROLE"))
        for text in ("DD1|JOB_ROLE:TRUST_INGEST", "DD2|JOB_ROLE:TRUST_INGEST")
    ]
    assert picks[0].standard_id == picks[1].standard_id == STANDARD_GENERIC


# ---------------------------------------------------------------------------
# (c) THE ENGINE BRANCH IS DECLARED, NOT INVENTED
# ---------------------------------------------------------------------------
def test_engine_token_sets_are_empty_by_declaration() -> None:
    """Clause (c) puts the CONTENT of each engine's set outside this item.

    A populated entry here means someone invented per-engine required tokens,
    which the item fails on explicitly.
    """
    assert ENGINE_TOKEN_SETS == {}, (
        "an engine acquired a required-token set. The CONTENT of a per-engine "
        "standard is not ruled by G94 — an entry appears only when a ruling puts "
        "one there."
    )


def test_an_unruled_engine_inherits_generic_and_reports_that_it_did() -> None:
    """Visible, never silent — the difference between a gap and a decision."""
    got = select_standard(JobType.PUBLISHER, executable=DPL_LAUNCHER)
    assert got.inherited_generic is True
    assert got.required == generic_required_tokens()
    assert got.reason == REASON_ENGINE_UNRULED
    assert got.standard_id == ENGINE_STANDARDS["DPL"], (
        "the engine keeps its OWN identity even while inheriting the generic set — "
        "otherwise the day a set is ruled is an identity change, not a content change"
    )


def test_every_engine_branch_has_an_identity() -> None:
    assert set(ENGINE_STANDARDS) == {"DPL", "ABINITIO", "INFORMATICA"}
    assert len(set(ENGINE_STANDARDS.values())) == 3, "identities must be distinct"


# ---------------------------------------------------------------------------
# (d) THE GENERIC SET IS DERIVED, NOT RETYPED
# ---------------------------------------------------------------------------
def test_the_generic_set_is_exactly_what_the_direction_describes() -> None:
    """'the DevX project key, the EMAIL_DL contacts' — derived, and it lands there.

    This is the check that the derivation is RIGHT rather than merely automatic:
    the acceptance describes the generic standard in words, and the computed set
    matches those words without being typed out.
    """
    assert generic_required_tokens() == (
        "DevX-project",
        "EMAIL_DL_L2",
        "EMAIL_DL_L3",
        "EMAIL_DL_PDN",
    )


def test_the_generic_set_cannot_drift_from_the_register() -> None:
    """Recompute independently and compare — no literal list in the module."""
    expected = [
        s.key
        for s in TOKEN_REGISTRY.values()
        if s.job_type is JobType.BOTH and not s.retired_by and not s.optional
    ]
    renames = {"L2_EMAIL_DL_NM": "EMAIL_DL_L2", "L3_EMAIL_DL_NM": "EMAIL_DL_L3"}
    for spec in FOLDER_VARIABLES.values():
        if spec.retired_by or spec.optional:
            continue
        key = renames.get(spec.key, spec.key)
        if key not in expected:
            expected.append(key)
    assert generic_required_tokens() == tuple(expected)


def test_retirement_is_carrier_scoped_and_the_generic_set_honors_that() -> None:
    """C30 retired the JOB-level contacts and kept the FOLDER-level ones.

    ``EMAIL_DL_L2`` is retired in ``TOKEN_REGISTRY`` (a description token) and
    live in ``FOLDER_VARIABLES`` (a folder variable) — the same spelling under
    two carriers, which is precisely what :class:`Carrier` exists to keep apart.
    A naive "never require a retired key" rule would therefore drop a LIVE folder
    variable, so the real rule is per-table: a key contributed by a table must
    not be retired IN THAT TABLE.
    """
    retired_as_token = {s.key for s in TOKEN_REGISTRY.values() if s.retired_by}
    assert "EMAIL_DL_L2" in retired_as_token, "precondition: the job-level twin is retired"
    assert not FOLDER_VARIABLES["EMAIL_DL_L2"].retired_by, "and the folder-level one is not"

    got = set(generic_required_tokens())
    # nothing arrives from TOKEN_REGISTRY while retired there
    from_tokens = {
        s.key
        for s in TOKEN_REGISTRY.values()
        if s.job_type is JobType.BOTH and not s.retired_by and not s.optional
    }
    assert got & retired_as_token <= set(FOLDER_VARIABLES), (
        "a key required while retired as a description token must be justified by a "
        "LIVE folder variable of the same spelling — otherwise the set is holding "
        "greenfield jobs to a retired standard"
    )
    assert from_tokens <= got


def test_the_pre_rename_folder_spellings_are_not_required_twice() -> None:
    """C30 §5.3 renamed two folder variables; both still PARSE, one is REQUIRED."""
    got = set(generic_required_tokens())
    assert "EMAIL_DL_L2" in got and "L2_EMAIL_DL_NM" not in got
    assert "EMAIL_DL_L3" in got and "L3_EMAIL_DL_NM" not in got
    assert "L2_EMAIL_DL_NM" in FOLDER_VARIABLES, "the twin stays REGISTERED so extracts resolve"


# ---------------------------------------------------------------------------
# (e) UNSELECTABLE IS AN ANSWER
# ---------------------------------------------------------------------------
def test_unselectable_returns_the_generic_standard_with_a_reason() -> None:
    got = select_standard(JobType.PUBLISHER)
    assert got.unselectable is True
    assert got.standard_id == STANDARD_GENERIC
    assert got.reason == REASON_UNSELECTABLE
    assert got.required == generic_required_tokens(), "an answer, not an error"


def test_a_job_role_without_an_executable_is_selectable() -> None:
    """Having a role is enough to not be a gap, and the reason distinguishes it."""
    got = select_standard(JobType.PUBLISHER, job_role="TRUST_INGEST")
    assert got.unselectable is False
    assert got.reason == REASON_NO_EXECUTABLE


def test_coverage_counts_the_reasons() -> None:
    """The adoption-not-compliance measure G84 established."""
    population = [
        select_standard(JobType.FILE_WATCHER),
        select_standard(JobType.PUBLISHER, executable=DPL_LAUNCHER),
        select_standard(JobType.PUBLISHER, executable=ABINITIO_LAUNCHER),
        select_standard(JobType.PUBLISHER, job_role="PLACEMENT"),
        select_standard(JobType.PUBLISHER),
    ]
    cov = selection_coverage(population)
    assert cov.total == 5
    assert cov.unselectable == 1
    assert cov.inherited_generic == 2
    assert cov.by_standard[STANDARD_FILE_WATCHER] == 1
    assert sum(cov.by_reason.values()) == 5
    assert cov.selectable_ratio == 0.8


def test_unselectable_is_reported_apart_from_generic() -> None:
    """'We chose generic' and 'we could not choose' are different findings."""
    cov = selection_coverage(
        [
            select_standard(JobType.PUBLISHER, job_role="PLACEMENT"),
            select_standard(JobType.PUBLISHER),
        ]
    )
    assert cov.by_standard[STANDARD_GENERIC] == 2
    assert cov.unselectable == 1


# ---------------------------------------------------------------------------
# scope fences — zero writes, no carrier, nothing ratified
# ---------------------------------------------------------------------------
def test_selection_does_not_mutate_the_register() -> None:
    before = dict(TOKEN_REGISTRY), dict(FOLDER_VARIABLES)
    select_standard(JobType.PUBLISHER, executable=DPL_LAUNCHER)
    generic_required_tokens()
    assert (dict(TOKEN_REGISTRY), dict(FOLDER_VARIABLES)) == before


def test_the_module_creates_no_carrier() -> None:
    """G95 §E2: G94 may return interim identities; it may NOT invent the carrier.

    Storage is inside G95's scope, so this module must not read or write a
    config family, a database or a file.
    """
    from drydocs_core.orchestration.controlm import standard_selection as mod

    source = inspect.getsource(mod)
    for forbidden in ("open(", "yaml.safe_load", "sqlite3", "Path(", "read_text"):
        assert forbidden not in source, (
            f"standard_selection.py contains {forbidden!r} — storage for a standard "
            "identity is G95's subject, and inventing the carrier here is what its "
            "clause E2 forbids."
        )
