# Adoption dossier 1 of 3 — remediation: the `detect.py` union (G68/G69)

**Hand-carried; never ports. Read the producer tree at tag `port-base-20260826`.**
This dossier documents intent so the adoption session does not reverse-engineer it
from diffs. It asks for nothing back: run it when scheduled, record the outcome in
your own adoption report and ledger. Sequenced FIRST of the three sessions because
the union plan is already written (your PORT-REPORT-e33f8d02 named it) and it is
the smallest — it rehearses the union discipline before the lineage and ontology
sessions need it.

## What this closes

Your `drydocs_remediation/detect.py` carries divergent DPL detectors and lacks
R41–R44; the producer's b26 increment dropped DPL handling and refactored
(+155/−90). Your report's plan is correct and is the mandate here: **union, not
take — keep your `detect_dpl_findings`, add R41–R44.** Taking either side
wholesale loses the other side's working half.

## The producer increment, by intent (commits `783f754d` G68, `49202a88` G69)

**G68 — the folder-set profile (`drydocs_remediation/profile.py`, new, plus a CLI
verb in `drydocs/cli.py`).** The READ half of the remediation loop. Five censuses
report what the export SAYS; a substitution-slot list names what it does NOT
carry. The division is the design: the machine reports what IS, the SME supplies
what is not there — that is what keeps profiling out of the guessing that
produced the drift C32 documents. Transport is a CLI verb writing a JSON artifact;
the verb sits in `cli.py` because a `cli_remediation` module would be a component
importing a component (the composition root is the only exempt module). Census (b)
reports `run_as` BY JOB TYPE deliberately: a FileWatcher on the platform account
beside payload jobs on the application account is the DESIGNED pattern, and
flattening it reads as "two accounts."

**G69 — R41–R44 registered and detected in the same change (`detect.py`,
`formats.py`, `xml_bridge.py`, registry).** The pairing is the point: the registry
is the single source for both gates, so a detector with no entry emits findings
nothing can rank or sign off on. The four rules, from the registry
(`internal/remediation/standards-rules-registry.md`, R41–R44 section, added
2026-08-25):

- **R41 — no duplicate declaration in one scope** (must-fix). The message names
  the ORDINAL ACCIDENT — which duplicate wins is position, not intent — and the
  detector walks the RAW layers; a test pins that `_declared` resolving into a
  dict would make the rule unable to fire.
- **R42 — one separator per folder set** (should-fix, cross-folder). Mixed
  separators do not make a split fail; they make it return a different field
  count, so a positional read silently lands on the wrong field. The finding
  names the parse consequence.
- **R43 — carrier collision: one name, two resolvers.** REGISTERED WITH NO
  DETECTOR, deliberately: nothing in the governance corpus rules
  shell-vs-Control-M ownership, and a detector firing against an undecided rule
  puts a finding in front of an SME with no defensible action. Its entry records
  what it is NOT (R33 is one FACT on two carriers; R43 is one NAME on two
  resolvers). If YOUR standards own the ownership answer, rule it your side and
  the detector is a small build.
- **R44 — stale authored provenance** (advisory, limit stated in the message).

## Union rules for this session

1. **Keep, verbatim:** your `detect_dpl_findings` and every company-only detector
   and value table. Producer rule VALUES never existed here — the
   `drydocs_remediation/**` manifest note has said all along that rule values and
   live corroboration stay company-side.
2. **Add:** the R41/R42/R44 detectors and the R43 registry entry, from the
   producer tree at the tag. The registry section is the authority for severity
   and message shape; do not soften severities during the merge.
3. **Adopt whole, not merged:** `profile.py` is producer-new (your port reverted
   it from an early batch rather than judging it) — there is no company half to
   union; take it and its CLI verb together, since the verb is its only caller.
4. **Do not re-decide during the union:** run_as-by-job-type reporting (the
   2026-08-19 SME evidence rider) and the composition-root placement of the CLI
   verb. Both were placed deliberately; both have their reasoning in the producer
   commit messages at the tag.

## Done means

- `tests/unit/test_remediation_conformance.py` (144 producer lines at the tag)
  and `tests/unit/test_remediation_profile.py` (238 lines) arrive and pass —
  these tests ship WITH the cluster, so "arrive and pass" is the criterion, not
  "go green" (they are not in your current failing set because they were
  deferred with the code).
- Your existing DPL detector tests still pass unmodified. If a producer test and
  a company detector genuinely conflict, that is a finding for your ledger, not
  a test to edit quietly.
- Zero deltas outside `drydocs_remediation/**`, the `cli.py` verb, the registry
  section, and the two test files.

## Out of scope for this session

The lineage and ontology clusters (dossiers 2 and 3). R43's carrier-ownership
ruling (yours, on your own gate cadence, whenever your standards side takes it
up). Any graph write — this cluster reads no graph and writes none.
