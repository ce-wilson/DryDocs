"""D5 — client-side Cypher statement splitting (drydocs_core.cypher_split).

The APOC landmine this guards: apoc.cypher.runMany splits on every ';' —
including inside comments — and Cypher 25 rejects the resulting empty
fragment (seen live at the first EE-container bootstrap, 2026-07-15).
run_script must therefore split CLIENT-SIDE, comment/string-aware, and
never hand the server an empty or comment-only fragment.
"""
from __future__ import annotations

from drydocs_core.cypher_split import (
    code_semicolon_positions,
    code_semicolons,
    has_code,
    split_statements,
    strip_comments,
)
from drydocs_core.neo4j_client import Neo4jClient

# The live-failure shape: an end-of-line ';' inside a // comment, a block
# comment, string literals carrying ';', and a trailing ';' + comment tail.
SCRIPT = """\
// audit envelope bookkeeping: last_seen_at;
CREATE CONSTRAINT thing_id IF NOT EXISTS FOR (n:Thing) REQUIRE n.id IS UNIQUE;

/* block; comment */
MERGE (n:Thing {id: 'a;b'})
  SET n.note = "semi; in \\"string\\"";
// trailing comment only — a naive splitter ships this as an empty statement
"""


def test_split_yields_every_real_statement_exactly_once_and_nothing_empty():
    statements = split_statements(SCRIPT)
    assert len(statements) == 2
    assert "CREATE CONSTRAINT thing_id" in statements[0]
    assert "MERGE (n:Thing" in statements[1]
    assert "'a;b'" in statements[1]  # string semicolons survive intact
    assert all(has_code(s) for s in statements)  # no empty/comment-only fragment


def test_comment_and_string_semicolons_are_not_split_points():
    # Only the two statement terminators count — not the comment or string ones.
    assert code_semicolons(SCRIPT) == 2
    positions = code_semicolon_positions(SCRIPT)
    assert [SCRIPT[:p].count("MERGE") for p in positions] == [0, 1]


def test_has_code_rejects_comment_only_fragments():
    assert not has_code("  \n// just; a comment\n/* and; a block */  ")
    assert not has_code("")
    assert has_code("RETURN 1")
    assert has_code("'a string is code'")


def test_unterminated_final_statement_is_kept():
    # No trailing ';' — the tail is still a real statement.
    assert split_statements("MATCH (n) RETURN n") == ["MATCH (n) RETURN n"]


# ---------------------------------------------------------------------------
# run_script executes per-statement through a duck-typed driver (no live DB)
# ---------------------------------------------------------------------------

class _FakeResult:
    def consume(self) -> None:
        return None


class _FakeSession:
    def __init__(self, log: list) -> None:
        self._log = log

    def __enter__(self) -> _FakeSession:
        return self

    def __exit__(self, *_: object) -> bool:
        return False

    def run(self, statement: str, params: dict) -> _FakeResult:
        self._log.append((statement, params))
        return _FakeResult()


class _FakeDriver:
    def __init__(self, log: list) -> None:
        self._log = log

    def session(self, database: str | None = None) -> _FakeSession:
        return _FakeSession(self._log)


def test_run_script_sends_each_statement_once_with_params():
    log: list = []
    client = Neo4jClient("bolt://fake", "u", "p")
    client._driver = _FakeDriver(log)

    client.run_script(SCRIPT, params={"x": 1})

    assert len(log) == 2  # two real statements, nothing sheared, nothing empty
    sent = [stmt for stmt, _ in log]
    assert sum("CREATE CONSTRAINT thing_id" in s for s in sent) == 1
    assert sum("MERGE (n:Thing" in s for s in sent) == 1
    assert all(params == {"x": 1} for _, params in log)
    assert all(has_code(s) for s in sent)


# ---- strip_comments (added G29 — the supplement IRI parser reads code only) ---

def test_strip_comments_removes_line_and_block_comments():
    src = (
        "// a leading note\n"
        "MERGE (n:Thing {id: 1})  // trailing note\n"
        "/* a block\n   over two lines */\n"
        "SET n.ok = true;\n"
    )
    out = strip_comments(src)
    assert "note" not in out and "block" not in out
    assert "MERGE (n:Thing {id: 1})" in out
    assert "SET n.ok = true;" in out


def test_strip_comments_keeps_string_literals_verbatim():
    # '//' inside an IRI is data; a '/*' inside a string must not open a comment.
    src = 'MERGE (n {iri: "http://www.w3.org/ns/prov#Entity", note: "a /* b"});'
    assert strip_comments(src) == src


def test_strip_comments_handles_escaped_quotes():
    src = r'MERGE (n {label: "say \" then // not a comment"});'
    assert strip_comments(src) == src


def test_strip_comments_leaves_a_comment_only_script_empty_of_code():
    assert not has_code(strip_comments("// only a comment\n/* and a block */\n"))
