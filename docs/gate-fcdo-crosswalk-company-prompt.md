# Company-side prompt — the `fcdo-crosswalk` ratification + recapture scrape

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The crosswalk artifacts (`config/crosswalks/fcdo-vocabulary.yaml`, 8 rows) landed
> in your tree with the a14a8028 port — this session can run now. The scrape it
> unblocks is **company-network-only**: nothing can be captured from the producer
> machine, which is why row 5 waits on you.

Venue: company `<org>/DryDocs`, current `main`. Name the venue in every claim (J18).

## What this session is (and is not)

The producer gate `fcdo-crosswalk` was SIGNED OFF 2026-08-05, **13/13** (SME
chad.wilson; producer `config/gate-log.md`; spec
`config/gate-prompts/fcdo-crosswalk.yaml`), and the `fcdo-frameworks` corpus was
ACTIVATED the same day by user ruling — a separate registry decision, not a gate
outcome. Under the two-tier doctrine neither is your sign-off. This session runs
the company ratification, decides YOUR corpus activation, and schedules the
recapture scrape. Union-append the entry to YOUR `config/gate-log.md`; an edit
that changes meaning is a **registered divergence**.

FCDO is YOUR governance group. Where the crosswalk misstates their published
framework, the correction is a company-side edit with the page as evidence — you
hold the authoritative source, the producer holds a capture.

## The producer ruling you are ratifying (summary — the gate-log entry is authority)

- **A1–A4 scope** — review-only; mechanism-only surfaces (standard CURIEs, no
  internal names); nothing new minted; the ALIGNMENT-PLAN skip list is binding.
- **B1** rows 1/2/3/7 exact: ControlMJob↔OL Job · JobRun/ControlMJobRun↔OL Run ·
  DataAsset↔Dataset · SUBCLASS_OF/MAPS_TO↔rdfs bridging.
- **B2** row 2 scope note — name conformance only, no run-event-ingestion mandate.
- **B3** row 4 grain split — their grain is the Run, ours the definition
  (ETLProcess | ControlMJob); both grains recorded; future run-grain lineage
  lands on ControlMJobRun without displacing definition-grain edges.
- **B4** row 6 documentation-only — the adms:status reading is a translation
  aid; the proposed→confirmed→applied HITL machinery changes in no way.
- **B5** row 8 carrier difference — RECONCILES_TO {confidence} carries
  skos:closeMatch semantics on an edge property, not an RDF mapping resource.
- **C1** row 5 BLOCKED — stays OPEN, signed neither way, until the registered
  `fcdo-frameworks` scrape recaptures the Descriptive Metadata Framework.
- **C2** — transcript absence is never treated as absence from their standard.
- **D1–D2** — rows 1–4, 6–8 flipped proposed → confirmed; row 5
  `blocked-on-recapture`; guard test moved in the same commit (F1/F2 precedent).

Corpus activation record (producer side): `config/doc-source-registry.yaml`
`confirmed: true`; activation proceeds INDEPENDENTLY of the row-5 recapture;
T4 `sme-confirm` per-page curation still applies; `target_db: ddcontext` keeps
the corpus out of ground truth.

## What the producer could NOT decide for you — rule these yourself

1. **Ratify the 8 rows against the live source.** You can open the actual
   framework pages; the producer worked from captures. Any row the live page
   contradicts is an edit with the page cited.
2. **YOUR corpus activation.** The producer flip does not activate your
   registry. Decide it, and record whether T4 per-page curation and the
   ddcontext isolation carry over unchanged.
3. **Run the recapture scrape** (Confluence connector, company network). The
   Descriptive Metadata Framework is the first-priority target — activation is
   the path that PRODUCES the row-5 evidence.
4. **The row-5 ruling** once the recapture lands: map the Descriptive Metadata
   Framework row, or rule it unmappable with reason. This is a gate ruling —
   either side may draft the session, both sides record it. Until then row 5
   stays `blocked-on-recapture` in both logs; a completed scrape is not a
   completed ruling.

## Rules in force

1. Per-item outcomes in your gate-log entry (A, B1–B5, C1–C2, D1–D2 + the four
   rulings above) — ratified / edited / refused, edits registered as divergences.
2. Fix data/code, never test-edit; producer guards are the contract.
3. Scraped page content and internal framework names stay Internal on your
   side; anything reported back to the producer is mechanism-only (standard
   CURIEs are fine — that is the crosswalk's own surface rule).
4. Venue every claim (J18).
5. Deferred means the word "deferred" in the durable note.

## Close-out

- Gate-log entry appended; your activation decision recorded; the scrape run or
  scheduled in words; row-5 status restated.
- Report back: per-item edits/divergences, activation outcome, recapture status
  — mechanism-only.
- Then stop.
