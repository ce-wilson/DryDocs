"""NFR-REM-1 — no graph write, ever (TDD §5): the STRUCTURAL half.

Walks the drydocs_remediation package AST and asserts (1) no write-transaction marker
is ever referenced, and (2) the package does not touch the Neo4j driver at all yet —
corroboration reads (0002-B §2 step 5) have not landed. When they do, tighten (2) to
"read-only sessions via drydocs_core.Neo4jClient" and add the runtime mock-client half
of this gate; do not delete it.
"""
from __future__ import annotations

import ast
from pathlib import Path

PKG = Path(__file__).resolve().parents[2] / "drydocs_remediation"

WRITE_MARKERS = {"execute_write", "write_transaction", "begin_transaction"}


def _walk_files():
    return sorted(PKG.rglob("*.py"))


def test_no_write_transaction_markers() -> None:
    hits: list[str] = []
    for path in _walk_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            name = None
            if isinstance(node, ast.Attribute):
                name = node.attr
            elif isinstance(node, ast.Name):
                name = node.id
            if name in WRITE_MARKERS:
                hits.append(f"{path.name}:{node.lineno} -> {name}")
    assert not hits, "graph-write marker referenced in the no-graph-write component:\n" + "\n".join(hits)


def test_no_neo4j_driver_usage_yet() -> None:
    hits: list[str] = []
    for path in _walk_files():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                mod = getattr(node, "module", "") or ""
                names = ", ".join(a.name for a in node.names)
                if "neo4j" in mod.lower() or "neo4j" in names.lower():
                    hits.append(f"{path.name}:{node.lineno} -> {mod or names}")
    assert not hits, (
        "drydocs_remediation touches the Neo4j driver — corroboration must be "
        "read-only via drydocs_core and this test tightened deliberately:\n"
        + "\n".join(hits)
    )
