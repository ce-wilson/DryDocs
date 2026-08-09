# Company-side prompt — the `autosys-crosswalk` gate: status, estate profile, ratification

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer gate signed 2026-07-14 (F1, 13 confirmations, ACCEPTED IN FULL) and the
> crosswalk has ridden every port since — but the producer has NO RECORD of your side's
> status. This session establishes it, profiles what only your estate can show, and
> finishes the ratification the two-tier doctrine says is yours.

Venue: company `<org>/DryDocs`, current `main`. Name the venue in every claim (J18).

## Step 1 — STATUS FIRST (answer before touching anything else)

What is this gate's status on YOUR side? Search your `config/gate-log.md` for any
`autosys-crosswalk` entry (heading-named or cited), check your
`config/crosswalks/autosys-to-bmc.yaml` row statuses, and your source-registry
`autosys-export` row. Report ONE of:
- **RATIFIED** — an entry exists: quote its heading + date, report back, and STOP.
- **DIVERGED** — your crosswalk/registry rows differ from producer: name the rows, stop
  at a divergence report.
- **NEVER RUN** — no entry: continue to step 2.
- **NOT APPLICABLE** — no AutoSys estate exists or is planned on your side: record that
  in your gate-log as a dated disposition (the Q1-B pinned-divergence idiom), report
  back, and STOP. A crosswalk for an orchestrator you will never ingest needs a
  disposition, not a ratification.

**BEFORE you may report RATIFIED, run the PROVENANCE CHECK. An entry existing is
NOT evidence that you ratified anything.** `config/gate-log.md` is `union-append`
in the port manifest, so producer entries land on your side BY DESIGN — and the
crosswalk yamls and `source-registry.yaml` `confirmed:` flags port too. All three
"corroborating signals" therefore corroborate each other and nothing else.

    git log --oneline -S "AutoSys" -- config/gate-log.md

- The introducing commit is a **PORT commit** (subject starts `port(...)`, or it
  sits on a port branch) -> the entry ARRIVED FROM THE PRODUCER. Report **NEVER
  RUN**, not RATIFIED, and continue to step 2.
- The introducing commit is **company-authored and unrelated to any port** ->
  genuinely RATIFIED. Quote that commit id; it is what gets ledgered.

Quote the command's OUTPUT, not your reading of it.

THIS IS NOT HYPOTHETICAL. On 2026-08-09 the `airflow-crosswalk` check reported
RATIFIED on exactly these three signals; the provenance command returned one
commit, `80d0fc0e`, subject `port(cewilson): apply eeaffa2..f7970e5 (step 31 —
web console O2 + 2026-07-14 gate session) onto branch`. The producer's own F2
sign-off had ported across and was being read back as company confirmation. Note
the tells that were visible without the command: the heading cites a PRODUCER
backlog id (F1/F2/M3/M4/O20), the signer and date match the producer's exactly,
and the producer's `confirmed:` comment string is byte-identical to yours.

The strongest POSITIVE evidence is content the producer has never seen: an entry
that rules company-only rows cannot be a ported artifact.

## Step 2 — profile the internal datasets used (agent; read-only, zero graph writes)

Only your side can see the AutoSys estate. Profile what exists — real values stay
Internal on your side; counts and shapes come back here:
1. **Estate census:** any AutoSys/Broadcom WLA instances in scope — JIL export
   availability, object counts per type (job, box, machine, condition, calendar).
2. **Row-6 evidence (the polymorphism follow-up):** `insert_machine` definitions —
   how many `machine:` names are real hosts vs virtual/load-balancing machines? The
   producer ruling maps virtual → `ControlMHostGroup -[:CONTAINS_HOST]->` and real →
   1-hop `RUNS_ON {role: agent_host}`; the discrimination NEEDS these definitions.
3. **Row-9 evidence:** the authoritative job-status vocabulary from a live export —
   the producer ruled this unresolvable without one.
4. **Row-4 evidence:** `d(file)` dependency usage counts — does the estate use
   file-watch conditions enough that d(file) needs its own FileWatcher-job baseline
   mapping?

## Step 3 — the producer rulings, crafted to finish yours

Ratify per-item against the step-2 profile; union-append to YOUR gate-log; edits that
change meaning are registered divergences:
1. **§A registration:** SoftwareProduct `autosys` MADE_BY `broadcom` (today's brand per
   ADR 0004; the CA lineage is name history, not the vendor). Crosswalk-only scope,
   public JIL concepts, bmc-baseline stays authority 1.
2. **§B the 11 rows:** rows 1/3/7 exact; 2/4/5/6/8/9/11 approximate with accepted
   caveats. Row 6's group-match-wins resolution mirrors controlm-hosts-topology
   (signed 2026-07-09) — if you diverged on THAT gate (your cm_hosts hold), say how it
   lands here.
3. **The three open questions** (live in the crosswalk's `open_questions`) — rule them
   FROM your profile, or leave them open with the missing evidence named: row 6
   (virtual-vs-real discrimination), row 9 (status vocabulary), row 4 (d(file)).
4. **§C no-equivalents:** row 10 (global/box variables) stays unmapped; any
   variable-graph need routes through ontology-mapper. Nothing silently approximated.
5. **Loader discipline restated:** `confirmed: true` on the source row is crosswalk
   authority ONLY — a loader must be implemented and separately gated before any load.

## Rules in force

1. Per-item outcomes in your gate-log entry — ratified / edited / refused; edits are
   registered divergences. 2. Real instance names, hosts, and JIL content stay Internal;
   report-back is mechanism-only (counts, shapes, row dispositions). 3. Venue every
   claim (J18). 4. One commit per concern. 5. A ratified crosswalk is not a performed
   load — deferred means the word "deferred" in the durable note.

## Close-out

Report back: the step-1 status, the step-2 profile counts, per-item dispositions, and
anything the producer should ledger — then stop. Loader builds and ingestion scheduling
are the SME's decisions.
