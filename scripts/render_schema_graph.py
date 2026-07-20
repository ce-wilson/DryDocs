"""render_schema_graph.py — render relationship_vocabulary.yaml to schema_graph.cypher.

Thin CLI entry point beside ``scripts/render_board.py`` (the same deterministic
committed-render-matches-source house pattern; backlog C8). The logic lives in
``drydocs_core.ontology.schema_graph``; the drift guard is
``tests/unit/test_schema_graph.py``. Run under the venv (CLAUDE.md ritual /
backlog J12): ``poetry run python scripts/render_schema_graph.py``.

Usage:
    poetry run python scripts/render_schema_graph.py
    poetry run python scripts/render_schema_graph.py --vocabulary path/to/vocab.yaml --out path/to/out.cypher
"""
from __future__ import annotations

import argparse
from pathlib import Path

from drydocs_core.ontology.schema_graph import (
    DEFAULT_OUTPUT_PATH,
    DEFAULT_VOCAB_PATH,
    write_schema_graph,
)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--vocabulary",
        type=Path,
        default=DEFAULT_VOCAB_PATH,
        help="path to relationship_vocabulary.yaml "
        "(default: drydocs_core/ontology/relationship_vocabulary.yaml)",
    )
    parser.add_argument(
        "--out",
        type=Path,
        default=DEFAULT_OUTPUT_PATH,
        help="path to write the rendered Cypher "
        "(default: drydocs_core/schema/schema_graph.cypher)",
    )
    args = parser.parse_args()

    out_path = write_schema_graph(args.vocabulary, args.out)
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
