# Company-side prompt — the `envelope-property-terms` gate: status, vocabulary profile, ratification

> Producer-drafted 2026-08-07 for the company-side assistant. Paste or read whole.
> The producer gate signed 2026-08-04 (M4, 10/10), same session as audit-envelope-
> phase4 — run this one AFTER that prompt (the bindings assume the envelope rulings).
> The producer has NO RECORD of your side's status. Documentation-grade throughout:
> no graph write, no edge change, no rename of the frozen envelope property names.

Venue: company `<org>/DryDocs`, current `main`. Name the venue in every claim (J18).

## Step 1 — STATUS FIRST (answer before touching anything else)

What is this gate's status on YOUR side? Search your `config/gate-log.md` for any
`envelope-property-terms` entry (heading-named, J28 rule). Report ONE of:
- **RATIFIED** — quote the entry heading + date, report back, STOP.
- **NEVER RUN** — continue to step 2.

**BEFORE you may report RATIFIED, run the PROVENANCE CHECK. An entry existing is
NOT evidence that you ratified anything.** `config/gate-log.md` is `union-append`
in the port manifest, so producer entries land on your side BY DESIGN — and the
crosswalk yamls and `source-registry.yaml` `confirmed:` flags port too. All three
"corroborating signals" therefore corroborate each other and nothing else.

    git log --oneline -S "envelope-property-terms" -- config/gate-log.md

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

The bindings live in the vocabulary registry and are enforced by drift guards, so the
profile is about YOUR tree's state:
1. **Vocabulary state:** does your `drydocs_core/ontology/relationship_vocabulary/`
   carry the `property_terms` section (the "0b" block in the header fragment)? The
   port carried it — verify it survived your per-entry vocab merges. THE KNOWN TRAP
   (ledger step 72): the binding guard REDS a pre-0b vocabulary — if the section is
   missing, restore vocabulary + guard in ONE commit, never the guard alone.
2. **Namespace state:** `dct:` (http://purl.org/dc/terms/) registered in your
   namespaces module and expanding via `namespaces.expand()`; the
   `reference/standards/dcmi-terms/` stub present.
3. **Envelope-bearing surfaces:** which of your loaders/extracts actually stamp the
   four frozen properties today, and — the company-only part — whether any
   COMPANY-LOCAL envelope property exists beyond the frozen four (your nine
   company-only audit-fields entries are where one would appear). Each such property
   is unbound until step 3 binds it.

## Step 3 — the producer rulings, crafted to finish yours

Ratify per-item; union-append to YOUR gate-log; edits that change meaning are
registered divergences:
1. **A1** — the binding is documentation-grade (no graph write, no loader change).
2. **A2** — SOSA ruled OUT: authorship provenance is not observation; SOSA stays in
   the experimental context-graph layer.
3. **B1 the uncontested trio** — `source_created_by` → `dct:creator`,
   `source_created_at` → `dct:created`, `source_updated_at` → `dct:modified`.
4. **B2 the contested row** — `source_updated_by` → `dct:contributor`, with the
   imprecision RECORDED in the entry note (DCMI defines no "modifier"; nearest term,
   same vocabulary family). Ratifying means keeping the recorded imprecision, not
   silently upgrading the claim.
5. **C1 registry home** — the `property_terms` section in the relationship
   vocabulary (one file for the mapper agent and the drift guards); confirm your
   step-2(1) state matches.
6. **D1–D2 consequences** — namespace registration + dcmi-terms standards stub +
   the extended drift guards (every envelope property carries a binding; every
   binding CURIE expands).
7. **THE EXTENSION (yours alone):** any company-local envelope property found at
   step 2(3) gets a binding under the same rule — same-family term where one exists,
   recorded imprecision where it does not, never left unbound.

## Rules in force

1. Per-item outcomes in your gate-log entry — ratified / edited / refused; edits are
   registered divergences. 2. Mechanism-only report-back. 3. Venue every claim (J18).
4. One commit per concern. 5. Fix data, never test-edit — the binding guards are the
   contract, and the pre-0b trap in step 2(1) is the one place a guard failure means
   "restore the vocabulary", not "the guard is wrong".

## Close-out

Report back: the step-1 status, the step-2 vocabulary/namespace/surface findings,
per-item dispositions, and any company-local bindings minted — then stop.
