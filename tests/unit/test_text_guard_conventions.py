"""J26 — the text-guard convention, and the inventory of guards that read
committed files as TEXT.

THE FAMILY. A guard that asserts over the raw text of a committed file with a
bare substring match makes that file unable to describe its own mechanism —
and this repo's doctrine is that the reasoning IS the audit trail. Four
instances forced the sweep:

1. ``test_schema.py::test_constraint_count`` counted ``CREATE CONSTRAINT``
   anywhere, so documenting a DDL trap in a ``//`` comment inflated the count
   AND false-failed the idempotence check (S3 anchored both at line start,
   mirroring ``constraints.py::_DECLARATION_RE``).
2. ``test_database_names.py`` keyed on the exact identifier ``DATABASE`` and
   missed ``SCHEMA_GRAPH_DATABASE`` (G51 widened it to any ``*DATABASE*``
   constant).
3. ``test_databases_match_provisioning_script`` promised "exactly what the DDL
   creates" and asserted only a subset (made bidirectional at the G51 tail —
   the promise-vs-assertion sub-family: docstring says equality, code checks
   containment).
4. ``render_gates.py`` classified a gate prompt as handled when ANY log entry
   cited its file (J28: heading identity now decides; a citation never closes
   a gate).

THE CONVENTION (what a new text guard must do):
- A NEGATIVE assertion ("X must not appear") or a COUNT reads code, not raw
  text: strip comments first (``drydocs_core.cypher_split.strip_comments`` for
  Cypher, a ``--`` line filter for SQL, a line-start anchor where the grammar
  is line-oriented). Raw-text bans forbid the file from explaining what it
  deliberately omits.
- A POSITIVE presence pin may read raw text — a comment can only false-pass
  it, never block a comment — but pin code when the claim is about code
  (test_schema's label/supplement checks moved to stripped text at this
  sweep, closing the commented-out-MERGE false-pass, the G29 lesson).
- The assertion must not promise more than it checks: if the docstring says
  "exactly", the code compares both directions.

THE INVENTORY (2026-08-04 sweep; ~227 read_text sites in tests/unit, by
family — each family either structural or noted):

- YAML/JSON-parsed reads (backlog, vocabulary, registries, manifests, the
  gates/matrix/load-map drift guards' committed-vs-regenerated equality):
  STRUCTURAL by construction — the parser, not a substring, does the reading.
- AST-based scans (test_database_names constants, test_render_determinism
  Path-sort rule, test_module_boundary imports): STRUCTURAL.
- Line-anchored counts (test_schema constraint count/idempotence,
  constraints.py::_DECLARATION_RE, database_names' comment-stripped DDL scan):
  STRUCTURAL — pinned below.
- Comment-stripped Cypher/SQL reads (supplements.declared_terms since G29;
  test_schema label + supplement checks, test_catalog_keying, and every
  negative assertion in test_controlm_cypher since this sweep): STRUCTURAL —
  regression pinned in test_catalog_keying.
- PORT-MANIFEST walk (test_port_reconcile_guards): YAML rows + glob-to-regex
  path matching + a PREFIX (append-only) comparison — STRUCTURAL; paths are
  identifiers, not prose.
- Positive presence pins on committed PROSE (test_node_status_envelope's
  contract-doc check, test_depgraph_snapshots' README currency,
  test_controlm_cypher's remaining fragment pins): bare substring is CORRECT
  here — the assertion is "the documentation says this", prose is the subject,
  and a false-pass requires someone to write the pinned sentence, which IS the
  requirement.
- Negative substring on PROSE with an escape hatch (test_database_names'
  superseded-name scan: any line may name a dead database by saying
  "superseded"; test_depgraph's retired-flag ban): deliberate bans whose
  escape hatch is exactly the sentence a reader needs — noted, correct.

The two meta-tests below pin the shared mechanisms the families above lean on,
so the convention survives refactors of the individual guards.
"""

from __future__ import annotations

from drydocs_core.cypher_split import strip_comments
from drydocs_core.schema.constraints import _DECLARATION_RE


def test_a_comment_quoting_ddl_is_not_a_declaration() -> None:
    """The original instance, pinned at the SHARED regex: constraints.cypher
    documents its own re-declaration trap by quoting DDL in a comment, and the
    line-start anchor is what keeps that quote from counting."""
    live = "CREATE CONSTRAINT real_key IF NOT EXISTS\nFOR (n:Thing) REQUIRE n.id IS NODE KEY;\n"
    described = live + (
        "// trap note: re-declaring under the same name is a silent no-op —\n"
        "//   CREATE CONSTRAINT real_key IF NOT EXISTS (different key!) succeeds\n"
    )
    assert len(_DECLARATION_RE.findall(live)) == 1
    assert len(_DECLARATION_RE.findall(described)) == 1, (
        "a // comment quoting CREATE CONSTRAINT counted as a declaration — "
        "the S3 line-start anchor regressed"
    )


def test_strip_comments_lets_a_file_quote_its_own_defect_shape() -> None:
    """The class mechanism: strip_comments removes what a comment says while
    keeping the code and the line structure, so negative assertions built on it
    never gag the file. (The live application is pinned in
    test_catalog_keying.py::test_the_guards_survive_the_file_describing_its_own_mechanism.)"""
    cypher = (
        "MERGE (p:Product {product_id: row.product_id})\n"
        "// the old shape was: SET p.orphan = false ON CREATE — never do that\n"
        "SET p.name = coalesce(row.name, p.name);\n"
    )
    code = strip_comments(cypher)
    assert "never do that" not in code
    assert "SET p.orphan = false" not in code  # the quoted defect is gone
    assert "coalesce(row.name, p.name)" in code  # the code is untouched
    assert code.count("\n") == cypher.count("\n")  # line structure preserved
