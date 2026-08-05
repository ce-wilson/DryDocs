#!/usr/bin/env bash
#
# ingest.sh — load the Control-M knowledge graph into Neo4j.
#
# Operational entry point for scheduled ingestion (Control-M / cron). This is a
# THIN wrapper over the DryDocs Python CLI (`poetry run drydocs ...`) — it adds no
# logic of its own. Reads Neo4j connection settings from the repo-root `.env`
# (see .claude/skills/run-drydocs/SKILL.md).
#
# THE SEQUENCE IS NOT WRITTEN HERE (N6, 2026-08-04). It is READ at run time from
# the one declaration — drydocs.cli.CANONICAL_LOAD_SEQUENCE — filtered to the
# `scheduled-ingest` profile. There is no list in this file to fall out of step
# with, which is the point: until N6 this script and the startup runbook's
# Appendix B each carried their own copy, they disagreed by five steps, and
# nothing recorded whether that was a decision or an oversight.
#
# WHAT THIS PROFILE DELIBERATELY SKIPS. A scheduled Control-M ingest is NOT a
# full refresh. `refresh-reference` is a weekly chain on a different cadence;
# `load-software-registry` and `load-bmc-docs` are repo-triggered corpora that
# change when the repo does, not when the batch estate does; and `docs-verify`
# would fail here BY DESIGN, since this path loads no doc corpora and `set -e`
# would abort the ingest over a reconciliation that was never meant to hold.
# Each of those four carries its reason in cli.SCHEDULED_INGEST_EXCLUSIONS, and
# tests/unit/test_load_sequence_surfaces.py fails if a standing step is dropped
# from this profile without one. To see exactly what will run:
#
#   poetry run python -c "from drydocs.cli import load_profile; \
#     print(*[s.command for s in load_profile('scheduled-ingest')], sep='\n')"
#
# Any arguments passed to this script are forwarded to the `ingest-controlm`
# step, so scoped/Oracle runs work:
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
PROFILE="scheduled-ingest"

# command<TAB>first sentence of the declared note, one line per step, in order.
_emit_profile() {
  poetry run python - "$PROFILE" <<'PY'
import sys

from drydocs.cli import load_profile

for step in load_profile(sys.argv[1]):
    print(f"{step.command}\t{step.note.split('. ')[0].strip()}")
PY
}

STEP_CMDS=()
STEP_NOTES=()
while IFS=$'\t' read -r cmd note; do
  STEP_CMDS+=("$cmd")
  STEP_NOTES+=("$note")
done < <(_emit_profile)

# `set -e` does NOT fire for a failure inside process substitution, so an import
# error or a renamed profile would otherwise sail through as "nothing to run"
# and exit 0 — a silent no-op is the worst possible outcome for a scheduled job.
if [ "${#STEP_CMDS[@]}" -eq 0 ]; then
  echo "[ingest] FATAL: profile '$PROFILE' produced no steps — the declaration" \
       "could not be read (bad checkout, broken venv, or a renamed profile)." >&2
  exit 1
fi

TOTAL="${#STEP_CMDS[@]}"
for i in "${!STEP_CMDS[@]}"; do
  cmd="${STEP_CMDS[$i]}"
  printf '[ingest] %d/%d %s - %s\n' "$((i + 1))" "$TOTAL" "$cmd" "${STEP_NOTES[$i]}"
  # Only ingest-controlm takes the caller's arguments (scope binds / --use-oracle).
  if [ "$cmd" = "ingest-controlm" ] && [ "$#" -gt 0 ]; then
    "${DRYDOCS[@]}" "$cmd" "$@"
  else
    "${DRYDOCS[@]}" "$cmd"
  fi
done

echo "[ingest] done"
