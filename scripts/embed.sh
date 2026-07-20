#!/usr/bin/env bash
#
# embed.sh — populate vector embeddings on :Searchable nodes (post-load pass).
#
# Operational entry point for the embedding/vector step that runs AFTER ingest.sh.
# By design the embedding pass is separate from bulk load so the MERGE-heavy
# ingest isn't taxed by vector-index writes (see knowledge/ARCHITECTURE.md, T7).
#
#   scripts/embed.sh            # embed all searchable entities
#
# NOTE — FORWARD-LOOKING: the underlying `drydocs embed` command ships with the
# GraphRAG / P0 vector work on branch `feat/llm-nav-p0-vector`. It is NOT present
# on this branch yet. The guard below detects that and exits cleanly with
# instructions rather than failing obscurely. Once that work lands, this wrapper
# works unchanged.
#
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$REPO_ROOT"

if ! poetry run drydocs --help 2>/dev/null | grep -qw embed; then
  echo "[embed] 'drydocs embed' is not available in this checkout yet." >&2
  echo "[embed] It ships with the P0 vector work (branch feat/llm-nav-p0-vector)." >&2
  echo "[embed] Merge or check out that branch, then re-run this wrapper." >&2
  exit 3
fi

echo "[embed] populating embeddings ${*:-(all searchable entities)}"
poetry run drydocs embed "$@"

echo "[embed] done"
