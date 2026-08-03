#!/usr/bin/env bash
#
# ingest.sh — load the Control-M knowledge graph into Neo4j.
#
# Operational entry point for scheduled ingestion (Control-M / cron). This is a
# THIN wrapper over the DryDocs Python CLI (`poetry run drydocs ...`) — it adds no
# logic of its own; it just runs the canonical bootstrap -> ingest -> verify chain
# in order and fails fast. Reads Neo4j connection settings from the repo-root
# `.env` (see .claude/skills/run-drydocs/SKILL.md).
#
# Any arguments passed to this script are forwarded to the `ingest-controlm` step,
# so scoped/Oracle runs work:
#   scripts/ingest.sh                                   # sample CSVs (default)
#   scripts/ingest.sh --use-oracle --folder "CCB_AUTO_%"
#
# Exit codes: non-zero if any stage fails (set -e).
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

DRYDOCS=(poetry run drydocs)

echo "[ingest] 1/6 check — verify Neo4j + APOC reachable"
"${DRYDOCS[@]}" check

echo "[ingest] 2/6 bootstrap — constraints + ontology seed"
"${DRYDOCS[@]}" bootstrap

# Targets ddschema, not the estate graph, so it is chain-independent of everything
# below. It runs here anyway because a wiped DBMS is exactly when the meta-graph is
# forgotten — and because this block and the runbook's Appendix B are meant to be the
# same sequence, not two sequences that drift.
echo "[ingest] 3/6 schema meta-graph — render + apply to ddschema"
"${DRYDOCS[@]}" bootstrap-schema-graph

echo "[ingest] 4/6 ontology supplements (ordered chain, verified, idempotent)"
"${DRYDOCS[@]}" apply-supplements

echo "[ingest] 5/6 ingest-controlm ${*:-(sample mode)}"
"${DRYDOCS[@]}" ingest-controlm "$@"

echo "[ingest] 6/6 verify M1 + M3 invariants"
"${DRYDOCS[@]}" m1-verify
"${DRYDOCS[@]}" m3-verify

echo "[ingest] done"
