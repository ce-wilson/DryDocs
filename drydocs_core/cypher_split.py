"""Comment/string-aware Cypher statement scanning — the ONE shared helper (D5).

apoc.cypher.runMany splits scripts on every ``;`` it sees, including one inside
a ``//`` comment, and Cypher 25 rejects the resulting empty fragment (seen live
at the first EE-container bootstrap, 2026-07-15). The fix class is to never let
a server-side splitter see the script at all: callers split CLIENT-SIDE with
this scanner, which recognizes ``//`` line comments, ``/* */`` block comments,
and ``'``/``"`` string literals (with backslash escapes) and therefore only
honors semicolons that are real code.

Consumers:
- ``drydocs_core.neo4j_client.Neo4jClient.run_script`` — splits and executes
  per-statement (each in its own auto-commit transaction, so DDL and DML can
  coexist in one file).
- ``drydocs.loaders.base`` — counts code semicolons to choose the run()/
  run_script() dispatch for cypher templates.
- ``drydocs_core.schema.supplements.declared_terms`` — reads the :OntologyTerm
  IRIs a supplement MERGEs, via :func:`strip_comments`, so a commented-out
  MERGE is not mistaken for a term the graph must hold (G29).
"""

from __future__ import annotations


def code_semicolon_positions(cypher: str) -> list[int]:
    """Indexes of every ``;`` OUTSIDE comments and string literals."""
    positions: list[int] = []
    i, n = 0, len(cypher)
    while i < n:
        two = cypher[i : i + 2]
        ch = cypher[i]
        if two == "//":
            j = cypher.find("\n", i)
            i = n if j == -1 else j
        elif two == "/*":
            j = cypher.find("*/", i + 2)
            i = n if j == -1 else j + 2
        elif ch in ("'", '"'):
            quote = ch
            i += 1
            while i < n:
                if cypher[i] == "\\":
                    i += 2
                    continue
                if cypher[i] == quote:
                    i += 1
                    break
                i += 1
        else:
            if ch == ";":
                positions.append(i)
            i += 1
    return positions


def code_semicolons(cypher: str) -> int:
    """Count of semicolons outside comments and strings (the dispatch test)."""
    return len(code_semicolon_positions(cypher))


def has_code(fragment: str) -> bool:
    """Whether anything other than whitespace and comments remains."""
    i, n = 0, len(fragment)
    while i < n:
        two = fragment[i : i + 2]
        ch = fragment[i]
        if two == "//":
            j = fragment.find("\n", i)
            i = n if j == -1 else j
        elif two == "/*":
            j = fragment.find("*/", i + 2)
            i = n if j == -1 else j + 2
        elif not ch.isspace():
            return True
        else:
            i += 1
    return False


def strip_comments(cypher: str) -> str:
    """*cypher* with ``//`` and ``/* */`` comments removed, code untouched.

    String literals are copied verbatim — a ``//`` inside a quoted IRI is data,
    not a comment. Newlines that ended a line comment are kept so line-oriented
    reading of the result still lines up with the source.
    """
    out: list[str] = []
    i, n = 0, len(cypher)
    while i < n:
        two = cypher[i : i + 2]
        ch = cypher[i]
        if two == "//":
            j = cypher.find("\n", i)
            i = n if j == -1 else j
        elif two == "/*":
            j = cypher.find("*/", i + 2)
            i = n if j == -1 else j + 2
        elif ch in ("'", '"'):
            quote = ch
            out.append(ch)
            i += 1
            while i < n:
                if cypher[i] == "\\":
                    out.append(cypher[i : i + 2])
                    i += 2
                    continue
                out.append(cypher[i])
                if cypher[i] == quote:
                    i += 1
                    break
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


def split_statements(script: str) -> list[str]:
    """Split *script* on code semicolons into executable statements.

    Fragments that hold no code — pure whitespace, or comments only (e.g. the
    tail after a final ``;``, or a comment block that a naive splitter would
    have sheared off) — are dropped, so every returned statement is one the
    server can execute. Comments preceding a statement stay attached to it.
    """
    parts: list[str] = []
    start = 0
    for pos in code_semicolon_positions(script):
        parts.append(script[start:pos])
        start = pos + 1
    parts.append(script[start:])
    return [part for part in parts if has_code(part)]
