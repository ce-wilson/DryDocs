"""LOAD13 — the base's finish line, as a test.

The sibling of ``test_e2e_load.py``, and a different question. That test proves
the CSV → Neo4j chain works against the BUNDLED SAMPLES. This one proves the
BASE is finished: from a clean clone, extract the synthetic stand-ins into a
data root, bootstrap, apply supplements, ingest in SOURCE mode off the landing
zones, verify, report coverage, and generate the run books — with **every step
either green or skipped carrying its reason**. No declared finish line existed
for the base before this test; this is it.

**Why a ledger and not seven asserts.** The point of a finish line is that
nothing in it is silent. A step that cannot run here must SAY why, in the
report, at a length that forces a reason rather than a shrug (J78; the forty
characters `drydocs_core.check_outcome` asks of a NOT_CHECKED reason is the
same bar, and the same argument). So the chain runs once into a ledger of
:class:`Step`, and the guards read the ledger. A step that were simply dropped
from the chain would fail :func:`test_the_chain_ran_every_step_it_declares`,
which is the failure mode a hand-written sequence of asserts cannot catch.

**SOURCE mode, not FIXTURE.** ``ingest-controlm`` decides its mode by whether a
samples directory is passed (``mode = "FIXTURE" if samples_dir is not None else
"SOURCE"``). Passing none is the whole point: the stand-ins have to arrive
through the landing zones a real drop lands in, or this proves nothing about
the base an operator runs.

**The data root is a tmp_path and DRYDOCS_DATA_ROOT is set to it.** Two
reasons, one of them measured. The obvious one: ``--extract`` writes source
drops, and a test must never write into the machine's real data root. The
measured one: ``--out-root`` does NOT make the variable optional — the
extraction resolves its landing zones through ``manual_zones()``, which calls
``resolve_data_root()`` regardless, so an unset variable raises
``DataRootNotSetError`` before ``--out-root`` is ever consulted (G81 removed
the default on purpose).

**ONE named residual: ``snow:cmdb-ci-classes``.** Its stand-in CSV extracts
with the rest, and no loader consumes it — ``config/source-descriptors.yaml``
declares ``wired: false`` with the reason "no loader is built; the class export
is a header-only sampled capture and no gate has ruled its meaning yet". That
is a SEMANTIC hold, not a wiring omission, and the ledger carries it as a
skipped step with that declared reason rather than leaving the class quietly
unmentioned. The reason is READ FROM THE CONFIG, never restated here, so the
day a gate rules its meaning this test starts failing until the step is built.

**Venue (J18).** An ephemeral Neo4j Enterprise container from testcontainers,
image declared in ``config/dev-environment.yaml`` — NOT either machine's local
``neo4jtest``. That is what makes the result reproducible from a clean clone
rather than a claim about one laptop.

Opt-in and Docker-gated exactly as the sibling: marked ``integration``,
deselected by default, and auto-SKIPPED (never failed) when Docker or the
tracked bundle is absent.

    poetry run pytest tests/integration/test_e2e_base_finish_line.py -m integration -q
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import pytest
import yaml

# The sibling owns the container image resolution and the raw client; sharing
# them is the precedent already set by test_code_snapshot_retraction.py. A
# second copy of either is a second thing to drift.
from tests.integration.test_e2e_load import NEO4J_IMAGE, _client, _docker_available

REPO_ROOT = Path(__file__).resolve().parents[2]
BUNDLE = REPO_ROOT / "drydocs" / "data" / "samples" / "synthetic-sources.json.gz"
DESCRIPTORS = REPO_ROOT / "config" / "source-descriptors.yaml"

#: The residual this test names in its docstring. Its reason is read from the
#: config below, never duplicated here.
SEMANTIC_HOLD = "snow:cmdb-ci-classes"

#: A skip reason has to be long enough to be a reason. Same bar as
#: drydocs_core.check_outcome.REASON_MIN, and the same argument for it: a bare
#: "skipped" is a fact with no owner.
REASON_MIN = 40

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(not _docker_available(), reason="Docker daemon unavailable"),
    pytest.mark.skipif(
        not BUNDLE.exists(),
        reason="the tracked synthetic-sources bundle is absent from this clone",
    ),
]


@dataclass
class Step:
    """One step of the chain, and what became of it.

    ``ran`` False REQUIRES a reason; the ledger guard enforces it. There is no
    third state on purpose — a step that errored is a failure, not a skip, and
    fails at the point it ran.
    """

    name: str
    ran: bool
    reason: str = ""
    detail: str = ""


@dataclass
class Ledger:
    steps: list[Step] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    data_root: Path | None = None
    coverage_output: str = ""

    def add(self, name: str, ran: bool, reason: str = "", detail: str = "") -> None:
        self.steps.append(Step(name, ran, reason, detail))

    def named(self, name: str) -> Step:
        for step in self.steps:
            if step.name == name:
                return step
        raise AssertionError(f"the chain never recorded a step named {name!r}")

    def report(self) -> str:
        """The finish line as a readable report — one line per step, in run order.

        This is the artifact the acceptance's "every step green or skipped with
        its reason" actually names. It exists so a failure prints WHAT THE CHAIN
        DID rather than only which assertion tripped: an operator reading a red
        build wants the ledger, not a boolean. Every guard below attaches it.
        """
        width = max(len(s.name) for s in self.steps) if self.steps else 0
        lines = []
        for step in self.steps:
            mark = "ok     " if step.ran else "SKIPPED"
            tail = step.detail if step.ran else step.reason
            lines.append(f"  {mark}  {step.name.ljust(width)}  {tail}")
        return "\n".join(lines)


#: Every step this finish line claims to cover. Declared UP FRONT so a step that
#: is deleted or never reached is a failure rather than an absence — the ledger
#: cannot quietly shrink.
DECLARED_STEPS = (
    "extract-stand-ins",
    "bootstrap",
    "apply-supplements",
    "ingest-controlm-source-mode",
    "m3-verify",
    "docs-coverage",
    "runbook-sdlc",
    "runbook-excel",
    SEMANTIC_HOLD,
)


def _wired_reason(source_id: str) -> str:
    """The declared reason a source is not wired, read from the config.

    Read rather than restated: this test asserts the residual is NAMED with the
    project's own reason, so the day that reason changes — or the source becomes
    wired — the assertion moves with it instead of preserving a stale copy.
    """
    block = yaml.safe_load(DESCRIPTORS.read_text(encoding="utf-8"))["wired"]
    entry = block[source_id]
    assert isinstance(entry, dict) and entry.get("value") is False, (
        f"{source_id} is no longer declared unwired in {DESCRIPTORS.name}; "
        "this test's named residual needs revisiting"
    )
    return str(entry["reason"])


def _run(env: dict, *args: str) -> tuple[int, str]:
    """Invoke the real CLI and RETURN its outcome rather than asserting on it.

    The sibling's ``_invoke`` asserts exit 0, which is right for a chain that
    must succeed. Here the outcome is data: a step records what happened and the
    ledger guards decide what is acceptable.
    """
    from typer.testing import CliRunner

    from drydocs.cli import app

    result = CliRunner().invoke(app, list(args), env=env)
    return result.exit_code, result.output


@pytest.fixture(scope="module")
def neo4j_env(tmp_path_factory):
    """A throwaway Enterprise Neo4j plus the env the CLI reads, data root included.

    ``DRYDOCS_DATA_ROOT`` points at a tmp directory for the reasons in the module
    docstring. It is part of the ENV DICT rather than the process environment so
    nothing here can leak into a later test module.
    """
    from testcontainers.neo4j import Neo4jContainer

    root = tmp_path_factory.mktemp("base_data_root")
    container = (
        Neo4jContainer(NEO4J_IMAGE)
        .with_env("NEO4J_PLUGINS", '["apoc"]')
        .with_env("NEO4J_ACCEPT_LICENSE_AGREEMENT", "eval")
    )
    with container as neo4j:
        yield {
            "NEO4J_URI": neo4j.get_connection_url(),
            "NEO4J_USER": neo4j.username,
            "NEO4J_PASSWORD": neo4j.password,
            "NEO4J_DATABASE": "neo4j",
            "DRYDOCS_DATA_ROOT": str(root),
        }


@pytest.fixture(scope="module")
def finish_line(neo4j_env) -> Ledger:
    """Run the whole chain once, into a ledger every guard below reads."""
    ledger = Ledger(env=neo4j_env, data_root=Path(neo4j_env["DRYDOCS_DATA_ROOT"]))
    root = ledger.data_root
    assert root is not None

    # 1. Extract the stand-ins into the landing zones a real drop lands in.
    #    Called in-process with the env patched, so the resolve_data_root() the
    #    extraction reaches through manual_zones() sees the tmp root.
    with pytest.MonkeyPatch().context() as mp:
        mp.setenv("DRYDOCS_DATA_ROOT", str(root))
        from scripts.build_synthetic_sources import main as build_main

        rc = build_main(["--extract", "--out-root", str(root)])
    extracted = sorted(p for p in root.rglob("*.csv"))
    ledger.add(
        "extract-stand-ins",
        rc == 0 and bool(extracted),
        detail=f"{len(extracted)} CSVs into {len({p.parent for p in extracted})} landing zones",
    )

    # 2-4. The operator chain, in SOURCE mode: no samples directory is passed,
    #      so ingest-controlm reads the landing zones written above.
    for name, args in (
        ("bootstrap", ("bootstrap",)),
        ("apply-supplements", ("apply-supplements", "--only", "base")),
        ("ingest-controlm-source-mode", ("ingest-controlm",)),
        ("m3-verify", ("m3-verify",)),
    ):
        code, out = _run(neo4j_env, *args)
        ledger.add(name, code == 0, detail=f"exit {code}")
        assert code == 0, f"chain step {name} exited {code}:\n{out}"

    # 5. The coverage report. Its exit code is a STATEMENT ABOUT THE WORLD — it
    #    exits non-zero on a broken corpus pointer or version drift, both of
    #    which are true things about the estate rather than failures of this
    #    chain. So a findings exit still counts as RAN. What does not is the
    #    verb failing to produce a report at all: recording that as green would
    #    be the exact silence this item exists to outlaw, so it is asserted like
    #    any other chain step.
    code, out = _run(neo4j_env, "docs-coverage")
    assert code in (0, 1), f"docs-coverage did not produce a report, exited {code}:\n{out}"
    assert out.strip(), "docs-coverage exited cleanly and printed nothing"
    ledger.add("docs-coverage", True, detail=f"exit {code}, {len(out.splitlines())} lines")
    ledger.coverage_output = out

    # 6. The run books. Each generator is probed DYNAMICALLY so the sibling item
    #    that builds one flips its step green without editing this file.
    _record_runbook_sdlc(ledger)
    _record_runbook_excel(ledger)

    # 7. The named residual.
    ledger.add(SEMANTIC_HOLD, False, reason=_wired_reason(SEMANTIC_HOLD))
    return ledger


def _skill_generator(skill: str) -> Path:
    return REPO_ROOT / ".claude" / "skills" / skill / "generate_runbook.py"


def _record_runbook_sdlc(ledger: Ledger) -> None:
    """L23's long-form generator, run against the graph this chain just loaded."""
    gen = _skill_generator("controlm-runbook-automation-SDLC")
    if not gen.exists():
        ledger.add(
            "runbook-sdlc",
            False,
            reason=(
                "the -SDLC long-form run book generator is not present in this "
                "clone, so the chain cannot produce the long-form document"
            ),
        )
        return
    folder = _first_loaded_folder(ledger)
    if folder is None:
        ledger.add(
            "runbook-sdlc",
            False,
            reason=(
                "the loaded graph holds no Control-M folder to generate a run "
                "book for, so the generator has nothing to be run against"
            ),
        )
        return
    module = _load_by_path(gen, "_load13_sdlc_generator")
    # THE GRAPH, not the bundled samples. Generating from samples would prove
    # the generator runs and say nothing about this chain — the whole claim here
    # is that the document comes off the stand-ins this test just loaded.
    with _client(ledger.env) as cli:
        facts = module.load_from_graph(cli, folder, "testcontainers Neo4j (LOAD13 e2e)")
    document = module.render(
        facts,
        module.load_spec(),
        {"generated": "LOAD13", "venue": "testcontainers", "folder": folder},
    )
    ledger.add("runbook-sdlc", True, detail=f"{len(document.splitlines())} lines for {folder}")


def _record_runbook_excel(ledger: Ledger) -> None:
    """DOC12's two-tab workbook generator, run against this chain's own graph.

    Presence is NOT the test. An earlier version recorded "generator present"
    once the file existed, which would have reported the step green while the
    generator was incapable of producing anything — the same silence the ledger
    exists to remove, one level up. It generates, or it says why it could not.
    """
    gen = _skill_generator("controlm-runbook-automation-excel")
    if not gen.exists():
        ledger.add(
            "runbook-excel",
            False,
            reason=(
                "the -excel skill ships a TEMPLATE writer but no generate_runbook.py, "
                "so the two-tab workbook cannot yet be filled from the graph (DOC12)"
            ),
        )
        return
    folder = _first_loaded_folder(ledger)
    if folder is None:
        ledger.add(
            "runbook-excel",
            False,
            reason=(
                "the loaded graph holds no Control-M folder to fill a workbook for, "
                "so the generator has nothing to be run against"
            ),
        )
        return
    excel = _load_by_path(gen, "_load13_excel_generator")
    sdlc = _load_by_path(_skill_generator("controlm-runbook-automation-SDLC"), "_load13_sdlc_facts")
    with _client(ledger.env) as cli:
        facts = sdlc.load_from_graph(cli, folder, "testcontainers Neo4j (LOAD13 e2e)")
    run = excel.generate(folder, facts=facts, venue="testcontainers Neo4j (LOAD13 e2e)")
    reached = sum(t.filled for t in run.tallies.values())
    declared = sum(t.declared_graph for t in run.tallies.values())
    ledger.add(
        "runbook-excel",
        True,
        detail=f"{reached}/{declared} graph-declared fields filled across {len(run.tallies)} tabs",
    )


def _load_by_path(path: Path, name: str):
    import importlib.util
    import sys

    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def _first_loaded_folder(ledger: Ledger) -> str | None:
    with _client(ledger.env) as cli:
        rows = cli.run(
            "MATCH (f:ControlMFolder) RETURN f.sched_table AS name ORDER BY name LIMIT 1"
        )
    return rows[0]["name"] if rows else None


# ---------------------------------------------------------------------------
# the guards
# ---------------------------------------------------------------------------


def test_the_chain_ran_every_step_it_declares(finish_line: Ledger) -> None:
    """A step that vanished from the chain is the failure this catches.

    Asserting on the SET, not the count: two sessions once agreed on a failing
    total when one failure was new (J57), and the same reasoning applies to a
    ledger — agreeing on how many steps ran is not agreeing on which.
    """
    recorded = {step.name for step in finish_line.steps}
    assert recorded == set(DECLARED_STEPS), (
        f"chain steps missing: {sorted(set(DECLARED_STEPS) - recorded)}; "
        f"undeclared: {sorted(recorded - set(DECLARED_STEPS))}\n"
        f"{finish_line.report()}"
    )


def test_every_step_is_green_or_carries_its_reason(finish_line: Ledger) -> None:
    """The finish line itself: nothing silent.

    A skipped step with no reason, or a reason short enough to be a shrug, is
    exactly the shape this item exists to outlaw.
    """
    for step in finish_line.steps:
        if step.ran:
            continue
        assert len(step.reason.strip()) >= REASON_MIN, (
            f"step {step.name!r} is skipped with a reason of "
            f"{len(step.reason.strip())} characters, under the {REASON_MIN} "
            f"a reason has to reach: {step.reason!r}\n"
            f"{finish_line.report()}"
        )


def test_the_stand_ins_arrived_through_the_landing_zones(finish_line: Ledger) -> None:
    """SOURCE mode read a drop, not the tracked fixture directory."""
    step = finish_line.named("extract-stand-ins")
    assert step.ran, f"the stand-ins did not extract: {step.reason}"
    root = finish_line.data_root
    assert root is not None and (root / "psgmgr-mirror").is_dir(), (
        "the Control-M landing zone is absent, so ingest-controlm cannot have " "read a source drop"
    )


def test_the_loaded_graph_holds_the_stand_in_population(finish_line: Ledger) -> None:
    """The chain's actual product: a populated graph, from the stand-ins."""
    with _client(finish_line.env) as cli:
        rows = cli.run(
            "MATCH (f:ControlMFolder) WITH count(f) AS folders "
            "MATCH (j:ControlMJob) RETURN folders, count(j) AS jobs"
        )
    assert rows, "the graph answered no counts at all after the chain"
    assert (
        rows[0]["folders"] > 0 and rows[0]["jobs"] > 0
    ), f"the chain completed but loaded nothing: {rows[0]}"


def test_the_semantic_hold_is_named_with_the_projects_own_reason(finish_line: Ledger) -> None:
    """The one named residual, carrying the config's reason rather than a copy."""
    step = finish_line.named(SEMANTIC_HOLD)
    assert not step.ran, (
        f"{SEMANTIC_HOLD} now loads; the finish line's named residual is stale "
        "and this test should assert the loaded classes instead"
    )
    assert step.reason == _wired_reason(
        SEMANTIC_HOLD
    ), "the residual's reason has drifted from config/source-descriptors.yaml"


def test_the_excel_runbook_step_reports_its_state_either_way(finish_line: Ledger) -> None:
    """DOC12's generator: green when it is here, a reasoned skip when it is not.

    Written for BOTH worlds deliberately. The first version asserted only the
    skip and failed the moment DOC12 landed — a correct tripwire and a wrong
    permanent guard, because the batch that adds the generator then has to edit
    a test belonging to another item to get green, and it found out at the merge
    rather than at the build. What has to hold in either world is the property
    this whole file is about: the step reports its state and never goes silent.
    """
    step = finish_line.named("runbook-excel")
    if step.ran:
        assert step.detail.strip(), (
            "a green step must say what it produced; 'it ran' with no detail is "
            "the silence this ledger exists to remove"
        )
        assert "/" in step.detail, (
            "the workbook step reports how much of the template it filled, so a "
            f"reader sees reach rather than a bare success: {step.detail!r}"
        )
    else:
        assert "DOC12" in step.reason, (
            "the skip should name the item that resolves it, so a reader knows "
            f"where the work is: {step.reason!r}"
        )


def test_the_sdlc_runbook_generates_off_this_chain(finish_line: Ledger) -> None:
    """L23's generator, proven against a graph this test loaded from stand-ins."""
    step = finish_line.named("runbook-sdlc")
    assert step.ran, f"the long-form run book did not generate: {step.reason}"
    assert "lines" in step.detail
