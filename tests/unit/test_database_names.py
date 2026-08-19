"""Every database name the code names must be one provisioning actually creates.

The drift this closes (backlog G28, found 2026-07-25): ``drydocs_deepdoc.DATABASE``
was ``"drydocs_context"`` — a database
``drydocs_core/schema/provisioning/01_databases.cypher`` never creates. At the time it
created ``drydocs`` / ``ddlineage`` / ``ddcontext`` / ``ddall`` (the set has since
gained ``ddschema`` at G51 and retired ``ddlineage`` at X1). ADR 0002's original
``drydocs_context`` / ``drydocs_all`` names were superseded by the G6/G7 deploy, and
that supersession is on the record in ADR 0006 §1 ("the plan's working name predates
the deploy") plus the gate-log dd*-convention entry — so provisioning is not a
unilateral winner here, it is the ruled convention.

What made it survive: ``test_lineage_deepdoc_scaffold.py`` asserted the stale value,
so the suite PROTECTED the wrong name instead of catching it. A test that pins a
constant to itself proves nothing; this one pins it to the provisioning DDL, which is
the only thing that decides whether a database exists.

The second drift this closes (backlog G51, found 2026-08-02): the guard below keyed
on the EXACT identifier ``DATABASE``, so ``SCHEMA_GRAPH_DATABASE = "ddschema"``
walked straight past it while ``01_databases.cypher`` created no such database —
a shipped verb (``bootstrap-schema-graph``) targeting a name provisioning never
makes. A guard whose docstring promises more than its pattern matches is the J26
family; the match is now "any module-level constant whose name contains
``DATABASE``", so the next differently-named constant is caught whatever it is
called.

Pure stdlib + a regex over the DDL — no Neo4j, no driver, no live connection.
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
PROVISIONING = REPO_ROOT / "drydocs_core" / "schema" / "provisioning" / "01_databases.cypher"

#: Packages whose string constants must only ever name a provisioned database.
SCANNED_PACKAGES: tuple[str, ...] = (
    "drydocs",
    "drydocs_core",
    "drydocs_api",
    "drydocs_lineage",
    "drydocs_deepdoc",
    "drydocs_remediation",
)

#: Database names that were REAL once and are not any more. Naming one in source is
#: the drift G28 closed. A deliberately small, explicit set beats a clever pattern:
#: the first version of this test used a generic `drydocs_*|dd*` regex and flagged the
#: CSS colour `#ddd` and the column `drydocs_application_id`.
SUPERSEDED_NAMES: frozenset[str] = frozenset(
    {
        "drydocs_context",  # -> ddcontext   (ADR 0002 original; superseded at the G6/G7 deploy)
        "drydocs_all",  # -> ddall       (same)
        "drydocs_docs",  # -> dddocs      (docmeta plan working name; ADR 0006 §1 renamed it)
        "ddlineage",  # retired outright 2026-08-04 (ADR 0002 X1 amendment; no successor)
        "ddcontext",  # folded 2026-08-18 (G32/G102): the uncertain realm is the :Uncertain LABEL in the one database
        "ddall",  # retired 2026-08-18 with its second constituent (G32/G102); joined here at the G38 close
    }
)

#: A line may name a superseded database ONLY if it says so. This is the escape hatch
#: for supersession notes and history, and it is deliberately the *only* one — you can
#: mention the old name, but you have to admit it is old. ("retire" joined at X2 —
#: ddlineage has no successor name, so "superseded" would be the wrong admission;
#: "was `" widened from the double-backtick form for markdown-style comments.)
_ALLOWED_IN_LINE = re.compile(r"supersed|renamed|retire|was\s+`|historical", re.IGNORECASE)

_CREATE_DB = re.compile(
    r"CREATE\s+(?:COMPOSITE\s+)?DATABASE\s+([A-Za-z_][A-Za-z0-9_]*)", re.IGNORECASE
)


def _provisioned() -> set[str]:
    text = PROVISIONING.read_text(encoding="utf-8")
    # Strip // comments so a commented-out CREATE never counts as provisioned.
    live = "\n".join(line.split("//")[0] for line in text.splitlines())
    return set(_CREATE_DB.findall(live))


def _python_files() -> list[Path]:
    files: list[Path] = []
    for pkg in SCANNED_PACKAGES:
        root = REPO_ROOT / pkg
        if root.is_dir():
            files.extend(p for p in root.rglob("*.py") if ".venv" not in p.parts)
    return files


def _names_a_database(identifier: str) -> bool:
    """A constant participates in the guard if its NAME says it holds a database.

    Widened from ``identifier == "DATABASE"`` at G51: the exact-match version let
    ``SCHEMA_GRAPH_DATABASE`` ship an unprovisioned name through a green suite.
    Identifier-based on purpose — value-based guessing is what flagged the CSS
    colour ``#ddd`` in this file's first draft (see SUPERSEDED_NAMES note).
    """
    return "DATABASE" in identifier


def test_provisioning_creates_the_expected_topology() -> None:
    """Anchor the other tests: ADR 0002 (+ 0006 §1 renames, + the amendments).

    5 -> 4 names at X2 (``ddlineage`` retired, 2026-08-04); 4 -> 2 at G102
    (2026-08-18): gate document-content-topology folded the content topology to
    ONE database — ``ddcontext`` folded (the realm is the :Uncertain label) and
    ``ddall`` retired with its second constituent. ``ddschema`` stays: G51, and
    keeping it out is what stops ADR 0011 clause 2 from ever firing.
    """
    assert _provisioned() == {"drydocs", "ddschema"}


def test_module_level_database_constants_are_provisioned() -> None:
    """Any module exposing a DATABASE constant must name a real database."""
    offenders: list[str] = []
    provisioned = _provisioned()
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
            named = [t for t in targets if _names_a_database(t)]
            if not named:
                continue
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                if node.value.value not in provisioned:
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(
                        f"{rel}: {named[0]} = {node.value.value!r}, "
                        f"not created by provisioning ({sorted(provisioned)})"
                    )
    assert not offenders, "database constant names an unprovisioned database:\n" + "\n".join(
        offenders
    )


def test_no_source_file_names_a_superseded_database() -> None:
    """Catch the drift in docstrings and comments too — that is where it spread.

    A docstring naming a dead database is how the next reader learns the wrong name,
    so prose is in scope. The only way past this test is to say the name is
    superseded, which is exactly the sentence a reader needs anyway.
    """
    offenders: list[str] = []
    for path in _python_files():
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if _ALLOWED_IN_LINE.search(line):
                continue
            for stale in SUPERSEDED_NAMES:
                if stale in line:
                    rel = path.relative_to(REPO_ROOT)
                    offenders.append(f"{rel}:{lineno}: names superseded database {stale!r}")
    assert not offenders, (
        "source names a database that no longer exists (say 'superseded' on the line if "
        "the mention is deliberately historical):\n" + "\n".join(offenders)
    )


def test_read_targets_and_write_targets_agree() -> None:
    """No query spec may read a database that nothing writes (backlog G30).

    The drift this closes: four ``drydocs_api`` specs declared
    ``database="ddlineage"`` while ``drydocs_lineage.writer`` pinned ``"drydocs"``
    and refused anything else. Both sides were internally consistent and cited a
    source — the specs followed G1 provisioning, the writer followed ADR 0002
    D1/D2 — so neither looked wrong on its own. It stayed invisible because the
    writer is gate-bound, so the specs returned zero rows for a *plausible*
    reason. G30 ruled for ADR 0002 (see its "Residency clarification"); this test
    is what makes the two halves impossible to separate again.

    ``ddlineage`` remained provisioned-but-excluded until it was retired outright
    (ADR 0002 X1 amendment, 2026-08-04) — "provisioned" was deliberately never
    the test. Having a writer is.
    """
    from drydocs_api.query_specs import QUERY_SPECS, SPEC_DATABASES

    written = _write_targets()
    # (pre-G102 a `composite = {"ddall"}` carve-out lived here — the composite
    # stored nothing and federated written constituents. Retired with ddall.)
    unwritten = SPEC_DATABASES - written
    assert not unwritten, (
        f"SPEC_DATABASES allows {sorted(unwritten)}, which no module writes — a spec "
        f"pointed there reads an empty database forever. Written: {sorted(written)}"
    )

    offenders = [
        f"{s.id}: reads {s.database!r}, which nothing writes"
        for s in QUERY_SPECS.values()
        if s.database not in written
    ]
    assert not offenders, "query spec reads a database nothing writes:\n" + "\n".join(offenders)


def _write_targets() -> set[str]:
    """Every database some module declares itself the writer of.

    ``drydocs`` is included unconditionally: it is the main load's target, and the
    load reads it from configuration (``NEO4J_DATABASE``) rather than a module
    constant, so the AST scan below cannot see it.
    """
    targets = {"drydocs"}
    for path in _python_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in tree.body:
            if not isinstance(node, ast.Assign):
                continue
            if not any(isinstance(t, ast.Name) and _names_a_database(t.id) for t in node.targets):
                continue
            if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
                targets.add(node.value.value)
    return targets


def test_the_lineage_writer_still_targets_the_ruled_database() -> None:
    """G30's ruling, pinned at the writer end as well as the reader end.

    Flipping this constant is a legitimate future decision — the ADR names the
    trigger — but it is an ADR amendment through the SME gate, not an edit. If it
    moves, the specs and this test move with it, together.
    """
    from drydocs_api.query_specs import query_spec
    from drydocs_lineage.writer import DATABASE as LINEAGE_DATABASE

    assert LINEAGE_DATABASE == "drydocs"
    for spec_id in (
        "lineage.hops.v1",
        "lineage.data-assets.v1",
        "lineage.schema-definition.v1",
        "runbooks.series.v1",
    ):
        assert (
            query_spec(spec_id).database == LINEAGE_DATABASE
        ), f"{spec_id} reads a different database than drydocs-lineage writes"


def test_superseded_names_are_really_superseded() -> None:
    """A name may only be called superseded while provisioning does NOT create it.

    If someone re-provisions ``drydocs_context``, the supersession claim becomes false
    and every "superseded" note in the tree becomes a lie — this fails first.
    """
    overlap = SUPERSEDED_NAMES & _provisioned()
    assert not overlap, (
        f"provisioning creates {sorted(overlap)}, which this test calls superseded — "
        "one of the two is wrong"
    )
