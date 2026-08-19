"""N6 — the operator surfaces are PROFILES of the one load sequence, not copies.

Two files tell an operator what to run: ``scripts/ingest.sh`` (scheduled,
unattended) and Appendix B of ``docs/design/drydocs-startup-refresh-runbook.md``
(a human cold start). Until N6 each carried its own ordered list, the two
disagreed by five steps, and nothing recorded whether that gap was a decision.

THAT AMBIGUITY WAS THE DEFECT, not the step counts. A deliberate subset and a
forgotten step look identical from outside, so no reader could tell which they
were looking at and no test could either. N6 ruled it: the scheduled profile is
deliberately shorter, every omission carries a written reason in
``cli.SCHEDULED_INGEST_EXCLUSIONS``, and both surfaces now derive from
``cli.CANONICAL_LOAD_SEQUENCE``.

``ingest.sh`` derives literally — it calls ``load_profile`` at run time and has
no list left. Appendix B is prose and can call nothing, so this module holds it
to the same answer.

THE GAP THIS ALSO CLOSES. The sibling guard's completeness half
(``test_loader_commands_are_sequenced_or_declared_ad_hoc``) walks
``COMMAND_LOADERS``, so it only ever reaches LOADER-backed verbs. Non-loader
verbs were invisible to it, which is how ``bootstrap-schema-graph`` ran in both
operator surfaces for months while missing from the declaration — the generated
load map published 15 steps while both real paths ran 16, and the count was
wrong in the one place readers trusted. ``test_every_verb_an_operator_surface_names_is_declared``
below is written from the other direction: it starts at the surfaces, so a verb
an operator actually runs cannot go undeclared regardless of whether a loader
sits behind it.
"""

from __future__ import annotations

import re
from pathlib import Path

from drydocs import cli

REPO_ROOT = Path(__file__).resolve().parents[2]
INGEST_SH = REPO_ROOT / "scripts" / "ingest.sh"
RUNBOOK = REPO_ROOT / "docs" / "design" / "drydocs-startup-refresh-runbook.md"

#: Verbs the runbook names that are NOT load-sequence steps. Reasons required —
#: the SOURCELESS_LOADERS idiom: an exemption without one is the silent omission
#: this family of guards exists to end.
NON_SEQUENCE_VERBS: dict[str, str] = {
    "sweep-removed": (
        "Rollback section, D7 retention: hard-deletes nodes soft-marked "
        "removed-from-source. Operator-judged and destructive, never part of a "
        "refresh — the load path only ever soft-marks"
    ),
    "reset": (
        "Rollback section, destructive last resort: DETACH DELETEs the whole "
        "graph. Its presence in a load sequence would be a defect"
    ),
}

_VERB = re.compile(r"poetry run drydocs ([a-z][a-z0-9-]+)")
_SH_VERB = re.compile(r'"\$\{DRYDOCS\[@\]\}"\s+([a-z][a-z0-9-]+)')
_APPENDIX_B = re.compile(
    r"\*\*B\. The full cold-start command sequence.*?```powershell\n(.*?)```", re.S
)


def _appendix_b_verbs() -> list[str]:
    text = RUNBOOK.read_text(encoding="utf-8")
    match = _APPENDIX_B.search(text)
    assert match, (
        "could not find Appendix B's powershell block in the runbook — the "
        "heading or the fence moved, and this guard silently stops guarding if "
        "it just returns nothing"
    )
    return _VERB.findall(match.group(1))


def _operator_surface_verbs() -> set[str]:
    """Every verb an operator surface really runs — from BOTH surfaces, and
    honest about how each one answers.

    N11, 2026-08-19. The runbook is prose and names its verbs literally, so a
    regex is the only way to read it. ``ingest.sh`` is the opposite case and
    scanning it was quietly meaningless: N6 made it derive the sequence at run
    time (``"${DRYDOCS[@]}" "$cmd"`` out of ``load_profile``), and the sibling
    guard ``test_ingest_sh_reads_the_declaration_instead_of_listing_steps``
    ENFORCES that it never grows a literal call back. So ``_SH_VERB`` over that
    file was guaranteed to return the empty set, and the caller unioned it in
    as if it were coverage.

    Nothing was being missed — a surface that reads ``CANONICAL_LOAD_SEQUENCE``
    cannot name a verb the declaration omits, which is a STRONGER guarantee
    than any regex over it. What was wrong is that the guard could not tell the
    two reasons for an empty result apart: "derives, so there is nothing to
    scan" and "the regex stopped matching". Assert the derivation instead, so
    the empty set has to earn its silence — that indistinguishability is the
    same shape as the defect this module exists for (N6's docstring: a
    deliberate subset and a forgotten step look identical from outside).
    """
    sh_text = INGEST_SH.read_text(encoding="utf-8")
    literal = set(_SH_VERB.findall(sh_text))
    if not literal:
        assert "load_profile" in sh_text, (
            "scripts/ingest.sh names no verb literally AND no longer derives "
            "from cli.load_profile — so this guard is reading an empty set as "
            "coverage of a surface it has in fact stopped checking. Either it "
            "derives (N6) or its verbs must be scannable by _SH_VERB; silently "
            "neither is how bootstrap-schema-graph stayed undeclared for months."
        )
    return literal | set(_VERB.findall(RUNBOOK.read_text(encoding="utf-8")))


def test_the_ingest_sh_half_of_the_surface_scan_cannot_pass_by_being_empty():
    """The helper's own guard, exercised — a scan that returns nothing must
    prove the surface derives rather than banking the empty result (N11)."""
    verbs = _operator_surface_verbs()
    assert verbs, "the surface scan found no verbs at all — both readers are dead"

    sh_text = INGEST_SH.read_text(encoding="utf-8")
    assert not _SH_VERB.findall(sh_text), (
        "scripts/ingest.sh now names verbs literally, so _operator_surface_verbs "
        "takes its scanning branch — this test's premise (the derived branch) is "
        "stale and the derivation assertion above needs re-reading."
    )
    assert (
        "load_profile" in sh_text
    ), "the derived branch is the live one and its own precondition is false"


# ---- the profile declarations themselves -------------------------------------


def test_profiles_are_declared_with_reasons_and_are_all_used():
    for name, reason in cli.LOAD_PROFILES.items():
        assert isinstance(reason, str) and len(reason.strip()) >= 40, (
            f"LOAD_PROFILES[{name!r}] needs to say which file derives from it "
            f"and what it is for, not {reason!r}"
        )
        assert cli.load_profile(name), (
            f"profile {name!r} selects no steps — an empty profile means a "
            "surface runs nothing, which is never what was meant"
        )
    declared = set(cli.LOAD_PROFILES)
    for step in cli.CANONICAL_LOAD_SEQUENCE:
        unknown = set(step.profiles) - declared
        assert not unknown, (
            f"step {step.command!r} claims undeclared profile(s) {sorted(unknown)} — "
            f"declare them in LOAD_PROFILES: {sorted(declared)}"
        )


def test_load_profile_rejects_an_unknown_name():
    """A typo'd profile name must fail loudly. ingest.sh treats an empty result
    as fatal precisely because a silent no-op is the worst outcome for a
    scheduled job; this is the same rule one level down."""
    try:
        cli.load_profile("cold-strat")
    except KeyError:
        return
    raise AssertionError("load_profile accepted an undeclared profile name")


def test_every_standing_step_is_in_the_cold_start_profile():
    """A cold start runs everything standing — that is what `standing` means.

    This is the invariant Appendix B actually violated: `docs-verify` is a
    standing step and the block omitted it, so a freshly built container was
    never reconciled against the doc-source registry.
    """
    missing = [
        step.command
        for step in cli.CANONICAL_LOAD_SEQUENCE
        if step.mode == "standing" and "cold-start" not in step.profiles
    ]
    assert not missing, (
        f"standing step(s) absent from the cold-start profile: {missing} — either "
        "add them to the profile (and to Appendix B) or they are not standing."
    )


def test_scheduled_ingest_omissions_are_ruled_rather_than_forgotten():
    """N6's ruling, enforced: the scheduled profile MAY be a subset, but every
    standing step it drops has to say why."""
    unexplained = [
        step.command
        for step in cli.CANONICAL_LOAD_SEQUENCE
        if step.mode == "standing"
        and "scheduled-ingest" not in step.profiles
        and step.command not in cli.SCHEDULED_INGEST_EXCLUSIONS
    ]
    assert not unexplained, (
        f"standing step(s) missing from the scheduled-ingest profile with no "
        f"recorded reason: {unexplained} — add the step to the profile, or add a "
        "reason to cli.SCHEDULED_INGEST_EXCLUSIONS. An unexplained omission is "
        "indistinguishable from an oversight, which is the defect N6 closed."
    )


def test_scheduled_ingest_exclusions_are_current_and_carry_reasons():
    """Shrink-only, the N2 LEDGER_PENDING idiom: a reason for a step that is now
    IN the profile (or gone) outlives the decision it records."""
    by_command = {step.command: step for step in cli.CANONICAL_LOAD_SEQUENCE}
    for command, reason in cli.SCHEDULED_INGEST_EXCLUSIONS.items():
        assert command in by_command, (
            f"SCHEDULED_INGEST_EXCLUSIONS names {command!r}, which is not a "
            "sequence step at all — stale entry."
        )
        assert "scheduled-ingest" not in by_command[command].profiles, (
            f"{command!r} IS in the scheduled-ingest profile and also carries an "
            "exclusion reason — pick one."
        )
        assert isinstance(reason, str) and len(reason.strip()) >= 40, (
            f"SCHEDULED_INGEST_EXCLUSIONS[{command!r}] needs a written reason, " f"not {reason!r}"
        )


# ---- surface 1: scripts/ingest.sh --------------------------------------------


def test_ingest_sh_reads_the_declaration_instead_of_listing_steps():
    text = INGEST_SH.read_text(encoding="utf-8")
    assert "load_profile" in text and "scheduled-ingest" in text, (
        "scripts/ingest.sh no longer reads cli.load_profile('scheduled-ingest') "
        "— the whole point of N6 is that it has no sequence of its own."
    )
    hardcoded = sorted(set(_SH_VERB.findall(text)))
    assert not hardcoded, (
        f"scripts/ingest.sh invokes verb(s) literally: {hardcoded} — the loop runs "
        '"${DRYDOCS[@]}" "$cmd" from the derived profile. A literal call is a '
        "second sequence growing back."
    )


def test_ingest_sh_treats_an_empty_profile_as_fatal():
    """`set -e` does not fire for a failure inside process substitution, so a
    broken venv or a renamed profile would otherwise exit 0 having loaded
    nothing. For a Control-M-scheduled job that reads as a clean run."""
    text = INGEST_SH.read_text(encoding="utf-8")
    assert '"${#STEP_CMDS[@]}" -eq 0' in text and "exit 1" in text, (
        "scripts/ingest.sh lost its empty-profile guard — a scheduled ingest that "
        "silently does nothing and exits 0 is worse than one that fails."
    )


def test_ingest_sh_forwards_arguments_only_to_ingest_controlm():
    """The documented contract: `scripts/ingest.sh --use-oracle --folder X%`
    scopes the Control-M extract and nothing else. Passing "$@" to every step
    would break `check` and both verifies."""
    text = INGEST_SH.read_text(encoding="utf-8")
    assert '[ "$cmd" = "ingest-controlm" ]' in text, (
        "the argument-forwarding condition in scripts/ingest.sh changed — "
        "arguments must reach ingest-controlm and no other step."
    )


# ---- surface 2: the runbook's Appendix B -------------------------------------


def test_appendix_b_is_exactly_the_cold_start_profile():
    expected = [step.command for step in cli.load_profile("cold-start")]
    found = _appendix_b_verbs()
    assert found == expected, (
        "the runbook's Appendix B has drifted from the cold-start profile.\n"
        f"  Appendix B: {found}\n"
        f"  declared  : {expected}\n"
        "Appendix B is prose and cannot derive itself, so this test IS its "
        "derivation — fix the block, or change the declaration and the block "
        "together (and bump the runbook Rev; it is a governed render)."
    )


def test_every_verb_an_operator_surface_names_is_declared():
    """Written from the SURFACES inward, which is the direction that catches
    what the loader-side completeness check cannot: a non-loader verb an
    operator really runs, missing from the declaration
    (`bootstrap-schema-graph`, found 2026-08-04)."""
    sequenced = {step.command for step in cli.CANONICAL_LOAD_SEQUENCE}
    named = _operator_surface_verbs()
    undeclared = sorted(
        verb
        for verb in named
        if verb not in sequenced
        and verb not in NON_SEQUENCE_VERBS
        and verb not in cli.AD_HOC_COMMANDS
    )
    assert not undeclared, (
        f"operator surface(s) run verb(s) the load sequence does not declare: "
        f"{undeclared} — add them to cli.CANONICAL_LOAD_SEQUENCE, or to "
        "NON_SEQUENCE_VERBS with the reason they are not load steps."
    )


def test_non_sequence_exemptions_are_current_and_carry_reasons():
    """Shrink-only again: an exemption for a verb the runbook stopped naming is
    dead weight, and one for a verb that has since JOINED the sequence is a
    contradiction."""
    sequenced = {step.command for step in cli.CANONICAL_LOAD_SEQUENCE}
    named = set(_VERB.findall(RUNBOOK.read_text(encoding="utf-8")))
    for verb, reason in NON_SEQUENCE_VERBS.items():
        assert (
            isinstance(reason, str) and len(reason.strip()) >= 40
        ), f"NON_SEQUENCE_VERBS[{verb!r}] needs a written reason, not {reason!r}"
        assert verb not in sequenced, (
            f"{verb!r} is exempted as a non-sequence verb AND declared in "
            "CANONICAL_LOAD_SEQUENCE — pick one."
        )
        assert verb in named, (
            f"NON_SEQUENCE_VERBS exempts {verb!r}, which the runbook no longer "
            "names — remove the exemption."
        )
