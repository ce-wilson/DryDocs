# Company-side prompt — the `cmdline-nfr-vetting` company gate

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer sign-off entry (2026-07-21, 4/4) closes with: "COMPANY runs its own
> gate on the draft NFR — this sign-off is producer-side only." **This session IS
> that gate.** The draft standards NFR is YOUR document; the producer rulings below
> are reference positions to ratify, edit, or diverge from — not a decided outcome.

Venue: company `<org>/DryDocs`, current `main` (the producer rulings ported long ago
— verify the m3/m7 vocabulary notes are present before starting). Name the venue in
every claim (J18).

## What this session is (and is not)

The producer gate `cmdline-nfr-vetting` was SIGNED OFF 2026-07-21, 4/4 (SME
chad.wilson; producer `config/gate-log.md`; the flow-doc §5–§6 hold the
comparison + proposal). Under the two-tier doctrine that is NOT your sign-off.
This session gates the **company draft NFR itself** (canonical Control-M variables
+ command-line structure + its ontology section) against your live evidence,
union-appends the entry to YOUR `config/gate-log.md`, and decides what the NFR
publishes as. An edit that changes meaning is a **registered divergence**.

## The producer positions you are ratifying (the gate-log entry is authority)

- **SME-1 — TRIGGERS from-node = the invoked wrapper/LAUNCHER Script**
  (`m3_triggers` unchanged). The NFR's payload-sourced variant was REJECTED:
  the `-pipeline` GUID literal rides the launcher's CMD_LINE (the extractor's
  parse surface) and payloads are often variable-held/unresolvable.
- **SME-2 — `m7_uses_artifact` registered** (ControlMJob→Script{payload},
  prov:used, `status: planned`) — a distinct label per the documented
  RUNS_ON-overload risk. Payload invocations migrate out of the `m3_invokes`
  1..n fold at the m7 build.
- **SME-3 — `:Script` refinements adopted** (with m7): `script_role`
  {launcher, payload} + platform / artifact_uri / artifact_kind /
  platform_flags / script_path properties (+ the 4 Informatica identifiers);
  Script identity stays PATH-keyed.
- **SME-4 — variable-standard deltas adopted, all 7:** ETL_* prefix wins over
  the gap-analysis CTM_* spelling; NEW `ETL_ARTIFACT_SHA` canonical (digests
  are not URIs); the **aliases-suggest-VALUES-DECIDE** contract (a variable
  holding a registered launcher is a launcher ref regardless of name);
  alias-map completion from the 2,384-variable evidence; TWO platform axes
  (`%%ETL_PLATFORM` = execution tech, extended with emr + reserved snowflake;
  `ETLProcess.kind` stays a separate launcher-derived graph axis — the
  perceived enum mismatch dissolves); FACT_REGISTRY migration including the
  IMAGE → ARTIFACT_URI clean break; mode flags stay CMD_LINE literals (only
  `-py` rides `ETL_PLATFORM_FLAGS`).

Launcher-registry verdict on record: value-based classification design
CONFIRMED correct; open gaps at signing = `dpl_spark_processor` (G15, since
built producer-side), `ICDW_etl_run_interface.ksh` (G16, since built),
`ecosystem_execution_engine.sh` + the template ingestion jar (await samples).

## What the producer could NOT decide for you — rule these yourself

1. **Each of the four positions against YOUR current evidence.** The
   2,384-variable gap analysis was your data at a point in time — re-check the
   alias map and the VALUES-DECIDE contract against the current variable
   population before ratifying SME-4.
2. **The sample-blocked launcher gaps.** Do samples now exist for
   `ecosystem_execution_engine.sh` and the template ingestion jar? If yes,
   classify them at this gate; if no, record "awaiting samples" in words.
3. **Verify G15/G16 against live CMD_LINEs.** The DPL launcher arg contract
   (both GUID spellings, %%VAR-launcher fallback, launch_mode + props) and the
   ICDW ksh launcher rule were built from your traces — confirm a current
   extraction run reproduces them (venue the run).
4. **FACT_REGISTRY migration scheduling** (ETL_* canonicals, alias rollups,
   IMAGE → ARTIFACT_URI) is a company operational decision — schedule it or
   defer it in words.
5. **NFR publication** — whether and where the vetted NFR publishes to your
   standards channel is yours alone.

## Rules in force

1. Per-item outcomes in your gate-log entry (SME-1..4 + the five rulings
   above) — ratified / edited / refused, edits registered as divergences.
2. Fix data/code, never test-edit; producer guards are the contract.
3. Real variable values, SIDs, server names stay Internal on your side;
   anything reported back to the producer is mechanism-only.
4. Venue every claim (J18).
5. A green suite is not a performed migration — deferred means the word
   "deferred" in the durable note.

## Close-out

- Gate-log entry appended; the NFR's status decided (published / revised /
  held); sample-gap and migration decisions recorded in words.
- Report back: per-item edits/divergences, the sample-gap status, and anything
  the producer should ledger — mechanism-only.
- Then stop.
