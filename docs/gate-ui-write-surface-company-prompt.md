# Company-side prompt — the `ui-write-surface` gate: status, console profile, ratification

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer gate signed 2026-07-21 (O20, 4/4) and ruled the write boundary for the
> ENTIRE web console; the console has ported to you repeatedly since, and YOUR
> deployment runs against real data — but the producer has NO RECORD of your side's
> status on the boundary itself. One producer-side hold matters here: the
> override-vs-graph PRECEDENCE question was left as an OPEN future gate on both sides.

Venue: company `<org>/DryDocs`, current `main` + your deployed console. Name the venue
in every claim (J18).

## Step 1 — STATUS FIRST (answer before touching anything else)

What is this gate's status on YOUR side? Search your `config/gate-log.md` for any
`ui-write-surface` entry (heading-named, J28 rule). Report ONE of:
- **RATIFIED** — quote the entry heading + date, report back, STOP.
- **NEVER RUN** — continue to step 2.
- **PARTIAL** — console rulings exist under other headings (your K7–K15 web holds,
  the AppCodeCascadePane reversal): list them, then continue — this session
  consolidates the boundary, it does not reopen the holds.

**BEFORE you may report RATIFIED, run the PROVENANCE CHECK. An entry existing is
NOT evidence that you ratified anything.** `config/gate-log.md` is `union-append`
in the port manifest, so producer entries land on your side BY DESIGN — and the
crosswalk yamls and `source-registry.yaml` `confirmed:` flags port too. All three
"corroborating signals" therefore corroborate each other and nothing else.

    git log --oneline -S "ui-write-surface" -- config/gate-log.md

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

The boundary is only as real as the deployment. Profile YOUR console's write paths —
real row contents stay Internal, counts and shapes come back here:
1. **M2 origin-flagged store:** your mapping-store table — override/user-mapping row
   counts by origin flag (source vs user), first instance = the SEAL-contacts
   override list. Verify the origin flag is populated on every row (an unflagged row
   is the drift the ruling exists to prevent).
2. **M1 gate-drafting:** whether the rendered gate pages' draft-assembly affordance
   is in use on your side (browser-local ticks, zero server surface) — used / unused
   is a fact worth recording either way.
3. **Write-path census:** every console/api route on your deployment that persists
   ANYTHING, classified against the ruled tiers (M1 artifact / M2 non-graph store /
   refused M3 direct-graph-write). Company-local extensions count — the census is
   exactly where an accidental M3 would surface.
4. **Precedence exposure:** any code or query that already ASSUMES override-beats-
   graph or graph-beats-override when the M2 store and the graph disagree — the open
   future-gate question. Findings are flags, not fixes.

## Step 3 — the producer rulings, crafted to finish yours

Ratify per-item; union-append to YOUR gate-log; edits that change meaning are
registered divergences:
1. **SME-1 doctrine:** the loader remains the ONLY graph writer; M3 (direct graph
   write from any console action) is REFUSED as a standing rule — any future
   exception is its own gate. drydocs-api stays read + artifact + derived-non-graph-
   store only. Admin config edits NEVER from the console. A super-user page is
   EXPECTED in the SaaS idiom — expectation recorded, scoping is follow-on backlog.
2. **SME-2 (M1):** gate pages assemble the gate-log entry snippet from ticked
   confirmations for the SME to review + commit; ticks stay browser-local; zero
   server surface; upgradeable to M2 only by its own decision.
3. **SME-3 (M2):** SME annotations/user mappings persist in the mapping-store TABLE
   with the origin flag always visible, exported as artifacts/reports; if notes ever
   become graph content, that shape routes through its own ontology gate first.
4. **SME-4:** server-side git (branch/PR creation) stays DEFERRED — overrides exit
   as downloads + source-corrections reports for the system owners (the
   fix-the-source doctrine); revisit waits on your GHE posture + its own security
   review. YOUR side owns that revisit decision — defer it in words or scope it.
5. **The step-2(3) census verdict:** every write path lands in a ruled tier, or is
   named as a divergence with its own disposition. An M3-shaped path found in the
   census is a defect report, not a ratification edit.
6. **The precedence question STAYS OPEN** — record it as open on your side too;
   anything found at step 2(4) is flagged against the future gate, not resolved here.

## Rules in force

1. Per-item outcomes in your gate-log entry — ratified / edited / refused; edits are
   registered divergences. 2. Real override rows, SIDs, and contact values stay
   Internal; report-back is mechanism-only (counts, tiers, flags). 3. Venue every
   claim (J18). 4. One commit per concern. 5. This gate ruled console affordances,
   not graph semantics — no vocabulary or map changes ride with it.

## Close-out

Report back: the step-1 status, the step-2 census (store counts by origin, write-path
tier table, precedence flags), per-item dispositions — then stop. The K7–K15 web
holds and the precedence future gate remain exactly as held.
