# Company-side prompt — the `rua-load-shapes` ratification gate (G22)

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> **Staged for the NEXT port:** the sign-off (2026-08-07) post-dates the a14a8028
> range, so the gate-log entry, the vocabulary consequences (G55), and the
> source-registry flips arrive with the next port. Do not run this session until
> that port lands — verify the producer entry "GATE: rua-load-shapes (G22) —
> SIGNED OFF, 28/28" is present in the ported `config/gate-log.md` first.

Venue: company `<org>/DryDocs`, the next port branch or `main` after its merge —
name which in every claim (J18).

## What this session is (and is not)

The producer gate `rua-load-shapes` was SIGNED OFF 2026-08-07, **28/28** (SME
chad.wilson; spec `config/gate-prompts/rua-load-shapes.yaml`; nine RECORD entries
precede the sign-off and remain accurate — the sign-off closes them, supersedes
none). It is the terminus of the G18–G21/G24/G25 candidate chain: five staging
seams, two real production bundles on YOUR side, **zero graph writes** — and that
last fact must still be true when you start. Under the two-tier doctrine this is
not your sign-off. Ratify per-item, union-append to YOUR `config/gate-log.md`;
an edit that changes meaning is a **registered divergence**.

## The producer ruling you are ratifying (summary — the gate-log entry is authority)

- **A1 HELD** behind K17 — `m3_delegates_to` may not activate while `:AppUser`
  has no agreed key. **A2 DECLINED** (redundant — ETL placement = job
  placement). **A3/A4/A5 ACTIVATE** — `m3_invokes` (endpoint widened per B2),
  `m7_uses_artifact` (deliberately in the same breath), `m3_reads_from` /
  `m3_writes_to` with the restriction restated. **A6** — anything unticked
  stays planned and candidate-side.
- **B2 CHOSEN** (not B1) · **B3 CONFIRMED**.
- **C1–C3 RULED** — all three land `status: planned`; C3's `.ksh` adapter added
  in-session. **C1 cannot be built before K17 signs.**
- **D1–D4 RULED** — normalized absolute path · reified occurrence nodes · three
  parts · stub.
- **E1–E3 CONFIRMED** — E1 with the SME caveat that retires "latest code that
  actually runs".
- **F1 RULED** the confidential set · **F2 CONFIRMED** (a filesystem path is
  not confidential; the URN survives).
- **G1 RULED** both-not-either · **G2 CONFIRMED**, scoped to scripts.
- **H1–H3 CONFIRMED** (H3 added in-session on SME evidence) ·
  **I1–I3 CONFIRMED** (I2 corrected, I3 materially amended).

Three preconditions found during the walk (ratify these too — they are rulings):
1. **Audit-fields: three stubs, three DIFFERENT reasons.**
   `bitbucket:repo-objects-manifest` — `commit_date` is the ref-TIP's date, not
   the file's; writing it as `source_updated_at` is the mtime error in a
   different column; out-of-reach-not-absent, revisit trigger = the manifest
   contract. `dpl:pipeline-registry` / `dpl:dataset-registry` — the field
   contract is ASSUMED, never validated (tracker **T13**); claiming an envelope
   or its absence would be a guess until a real export parses.
2. **Lifecycle: `deprecated`, not `removed`** — a signed-gate precedent (K7 §C2
   "never gated, never loaded") already answers the §I1 question; nothing in
   the registry is `removed`; the fix was the gloss in `00-header.yaml`,
   comment-only.
3. **Source-registry flips:** four dataset rows go `confirmed: true`
   (`exec-hosts:rua-bundle`, `bitbucket:repo-objects-manifest`,
   `dpl:pipeline-registry`, `dpl:dataset-registry`), each `adapter: ~` —
   **authority to load, not a loader** (the autosys/airflow precedent).

Follow-ups carried out of the gate (they ride the same port): **G55** vocabulary
consequences; **G23** curated rua load (carrying the §D2 extractor fix — second
arrival of a staged id currently drops); **G56** collector mount capture
(schema v3); **G57** `rua_*` → `bkup_*` rename. The lineage-writer guard
(`test_live_load_is_gate_bound_against_the_real_registry`) INVERTS at G55 — it
retires deliberately, never by deleting the raises-check.

## What the producer could NOT decide for you — rule these yourself

1. **The two production bundles are YOURS.** Re-verify the ruled shapes (D1
   path normalization, D2 occurrence grain, the D-amendment's shared-storage
   finding) against your real bundles before ratifying — the producer walked
   samples plus your two bundles as captured; the live population may have
   grown.
2. **T13 — validate the DPL registry field contract.** Parse a REAL export from
   your per-SEAL registry DB; that run decides whether createdBy/lastModifiedBy
   exist and closes (or re-scopes) the two dpl audit stubs. Venue the run.
3. **F1 — the confidential set** was ruled on producer-visible paths. Sweep
   your real path population against it before any load; additions are
   company-side edits, Internal.
4. **K17 discipline.** `fid-identity-and-scope` is UNSIGNED on both sides —
   A1 and C1 stay held on yours too. Do not green them, and flag any code that
   assumes the `:AppUser` key early.
5. **G23 scheduling** — the curated load (and with it the first actual rua
   graph write) is a company operational decision: schedule it or defer it in
   words. A ratified gate is not a performed load.

## Rules in force

1. Per-item outcomes in your gate-log entry (A1–A6, B2–B3, C1–C3, D1–D4,
   E1–E3, F1–F2, G1–G2, H1–H3, I1–I3 + the three preconditions) — ratified /
   edited / refused, edits registered as divergences.
2. Fix data/code, never test-edit; producer guards are the contract; the G55
   guard inversion is the one deliberate exception, done as its own commit
   citing this gate.
3. Real hostnames, mount paths, SEAL ids stay Internal on your side; anything
   reported back to the producer is mechanism-only.
4. Venue every claim (J18).
5. One commit per concern; quote the suite delta in each report-back message.
6. A green suite is not a performed load — deferred means the word "deferred"
   in the durable note.

## Close-out

- Gate-log entry appended; the four registry flips ratified-or-diverged; T13
  status recorded; K17 holds restated; G23 scheduled or deferred in words.
- Report back: per-item edits/divergences, the T13 result, the F1 sweep
  outcome (count only), and anything the producer should ledger —
  mechanism-only.
- Then stop. Loader builds (G23) and the port merge are the SME's decisions.
