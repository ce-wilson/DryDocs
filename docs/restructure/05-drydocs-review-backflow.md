# 05 — `drydocs-review` back-flow plan (company → producer)

> **Direction is REVERSE of the normal port.** The normal pipe is one-way
> producer → company ([`git-readme.md`](../../git-readme.md)). This plan covers the
> *exception*: a body of generic SME-review/HITL tooling that was authored
> **company-side** and should be reproduced **generically** in this public producer.
> It is re-implementation from descriptions/screenshots, **not** a code copy — company
> code never lands in the public repo (see [`PUBLISH-BOUNDARY.md`](../../PUBLISH-BOUNDARY.md)).

## Why this exists

The company added a coherent **`drydocs-review` component** — five modules, all
company-only, all *generic SME-workflow tooling* (not internal-data modules like
`locations.py` / `seal_deployments.py`). Origin: as the SME it was hard to **test**
what an agent loaded into the graph and **tell the agent what to change**. The
depgraph viewer helped; this toolkit + interactive "HITL prompt pages" were built to
close that review loop.

The producer committed to the HITL SME gate as a first-class concept but implemented
it **docs-only**. Present today: [`03-hitl-sme-flow.md`](03-hitl-sme-flow.md),
[`04-sme-checklist-and-load-plan.md`](04-sme-checklist-and-load-plan.md),
[`config/gate-log.md`](../../config/gate-log.md),
[`config/taxonomy-ontology-map.yaml`](../../config/taxonomy-ontology-map.yaml),
[`config/classification.yaml`](../../config/classification.yaml), and the depgraph
`viewer.html`. There is **no tooling**. This toolkit *is* the missing implementation
— the strongest back-flow candidate to date, and it serves the standalone-generalization
goal (any DryDocs adopter needs an SME review loop).

## The `drydocs-review` component (module inventory)

| Module | What it does | Reads / writes |
|---|---|---|
| `graph_review.py` | Renders live-graph rows → self-contained SME review HTML (one section per DATA label, provenance header, snake_case node cards, `hidden_props` stripped). **No Neo4j in the module** (CLI hands it rows) → offline unit-testable. | reads graph via CLI → writes HTML |
| `graph_verify.py` | Data-driven Cypher acceptance runner: loads YAML `TC-*` suites, runs each against the live graph, asserts `equals`/`empty`/`nonempty`, non-zero exit on failure. Loader + evaluate are pure/offline. | reads graph via CLI |
| `review_labels.py` | Typed accessor over `review-labels.yaml` — the shared spine mapping each ingestion *source* → the DATA labels it populates, in chain order + SME provenance. Consumed by both above. Pure config, no graph. | reads config |
| `sme_notes.py` | Harvester for owner-attributed `SME[SID]` inline notes across the repo (Python/YAML `#`, Cypher `//`), typed sub-tags routing to `$FR/$UC/$OQ/$NOTES`. Read-only; structured SME feedback back to the agent. | reads repo files |
| `drydocs/publishing/` | Confluence publish pipeline: authors XHTML fragments under `pages/`, assembles via template (`assembler`), validates XML + macro allow-list (`validator`), previews locally (`preview`), pushes via a Confluence-client wrapper. | reads docs/site → writes Confluence |

## HITL gate architecture (the target the generator produces)

From the company Confluence space **"DryDocs — SME Gate Prompts"**. Two-level structure:

- **Parent / index page** — the load pipeline top-to-bottom, the **authority hand-off**
  (PAT `lob-product-team` writes `:Application` fields as *placeholders* in Step 1b;
  when the SEAL load runs in Step 2a it becomes the higher authority and overwrites
  name/LoB/state), plus a "How to use a review page".
- **One child checklist page per load step**, generated from
  [`04-sme-checklist-and-load-plan.md`](04-sme-checklist-and-load-plan.md): 1a PAT
  org skeleton, 1b Product→Application + AreaProduct, 2a SEAL Application (source of
  record), 2b SEAL Contacts (18-Role), 2c SEAL Logical Deployments. All classified
  **Internal**.
- **Page anatomy:** header (step + classification) → "What this load does" → A Scope
  → B Mapping/Join → … → Sign-off. Ticks + free-text persist in browser localStorage.
- **The crucial principle — the repo is the system of record; browser ticks are a
  working aid.** Durable trio, all already present on the producer:
  `04-sme-checklist-and-load-plan.md` (plan) → interactive page (aid) → `gate-log.md`
  + `taxonomy-ontology-map.yaml` `status: confirmed` (record). No graph write until
  the mapping is confirmed in the repo.

So the "HITL prompt-page generator" is **a renderer** over
`04-sme-checklist-and-load-plan.md` + `taxonomy-ontology-map.yaml` +
`classification.yaml` that emits the interactive checklist pages, which `publishing/`
then pushes. The producer already owns the input doc, the config, and the record —
only the renderer is missing.

## Sanitization rule — mechanism, not instance

Reproduce the **tooling**; never bring the **artifacts it produced**.

| Bring (generic mechanism) | Leave / abstract (internal instance) |
|---|---|
| `graph_review` renderer, `graph_verify` YAML runner, `review_labels` accessor, `sme_notes` harvester | Real `SME[SID]` values; real `review-labels.yaml` content if it names internal sources |
| The publishing *pipeline* (assembler / validator / preview) | `toby_publish_confluence` (internal wrapper) → a generic pluggable publisher; Confluence space coordinates |
| The HITL prompt-page **generator** (interactive checklist, localStorage, "no write until confirmed", logs to `gate-log.md`) | The produced pages — the real SME gate pages are `CLASSIFICATION: INTERNAL-CONFIDENTIAL` (real LoB/Sub-LoB/Product-Line, row counts, `business_segment_code`) |

Seed every generator example from the synthesized `vendor-bmc` corpus, never real data.

## Boundary-guard fix (part of this epic)

`tests/unit/test_module_boundary.py` is currently an **allow-list**: a module in
neither `CORE_PREFIXES` nor a component group is skipped by *both* tests → silently
unguarded. Today the only unclassified `.py` under the scanned roots is
`drydocs/__init__.py`. Two changes:

1. **Add a `review` component group** to `COMPONENT_GROUPS` + `MODULE_MAP.md` rows,
   once the modules physically land here (SME review + graph acceptance + docs publish;
   all own a run cadence or do external I/O → none are core; `review_labels` is
   borderline → park in the component, promote to `drydocs_core.config` only if a
   second consumer appears).
2. **Flip the guard to default-deny** — add a test asserting every scanned module
   resolves to exactly one bucket (core or a component group), failing with the list
   of stragglers (exempt package `__init__.py`). This closes the blind spot
   *structurally* — the next unclassified module trips it, no enumeration required —
   and it means the company side does its own enumeration where its modules live.

## Sequencing (by sanitization-risk + testability)

1. `graph_verify` + `review_labels` — the offline spine (loader + evaluate pure).
2. `graph_review` — pure HTML renderer, offline-testable.
3. `sme_notes` — generic harvester, strip real SIDs.
4. HITL prompt-page **generator** — renderer over the three inputs above; own thread.
5. `drydocs/publishing/` — last; needs the Confluence adapter abstracted.

Then land the `review` group in `MODULE_MAP.md` + the guard, plus the default-deny backstop.

## Back-flow reconciliation direction (READ THIS before the next port)

Once these modules exist on **both** sides, they become **collisions** on the next
producer → company port — and the resolution is the **reverse** of most rows:

> **Canonical-COMPANY.** For every `drydocs-review` path
> (`graph_review.py`, `graph_verify.py`, `review_labels.py`, `sme_notes.py`,
> `drydocs/publishing/**`, `review-labels.yaml`, the HITL page generator), **keep the
> company version.** The producer's copy is the sanitized *public template*; it must
> **not** overwrite the company's originals, which carry the real Confluence wiring,
> the real publisher, and the real `review-labels.yaml`. Do not hand-merge — take
> company wholesale.

This rule is mirrored in [`git-readme.md`](../../git-readme.md) (the port guide the
company reads) and [`docs/port-prompt.md`](../port-prompt.md), and in the
`reconcile-port` skill's divergence ledger.

## Status

Tracked as **Epic H** in [`backlog.yaml`](backlog.yaml).

- **H1 — done (2026-07-01).** The offline spine: [`drydocs/review_labels.py`](../../drydocs/review_labels.py)
  (typed accessor over [`config/review-labels.yaml`](../../config/review-labels.yaml)) +
  [`drydocs/graph_verify.py`](../../drydocs/graph_verify.py) (pure `load`/`evaluate`; `run_*`
  takes a duck-typed `GraphRunner`, so the module never imports Neo4j and is fully offline).
  Example suite [`graph-tests/vendor-bmc-smoke.yaml`](../../graph-tests/vendor-bmc-smoke.yaml).
  27 unit tests; both YAML seeds `classification: Internal-Public`.
- **H2 — done (2026-07-01).** [`drydocs/graph_review.py`](../../drydocs/graph_review.py): pure
  `render_review({label: [props]})` → self-contained HTML, `hidden_props` + `_`-keys stripped, review-spine
  provenance on each section header. 6 unit tests.
- **H3 — done (2026-07-01).** [`drydocs/sme_notes.py`](../../drydocs/sme_notes.py): `SME[sid] $FR/$UC/$OQ/$NOTES`
  harvester (read-only `harvest_tree`/`route`, excludes `data/`). 5 unit tests, synthetic SIDs.
- **H4 — done (2026-07-01).** [`drydocs/gate_pages.py`](../../drydocs/gate_pages.py): `render_gate_page(spec)`
  → self-contained interactive HTML (checkbox per confirmation, localStorage persistence, progress bar,
  classification badge, mapping table, "no graph write until confirmed" banner). Example
  [`config/gate-prompts/vendor-bmc-example.yaml`](../../config/gate-prompts/vendor-bmc-example.yaml). 6 unit tests.
- **H5 — done (2026-07-01).** [`drydocs/publishing/`](../../drydocs/publishing/__init__.py): `assemble` +
  validator (well-formed XML + macro allow-list) + `write_preview` + `Publisher` Protocol
  (Noop/Local; Confluence push abstracted — no `toby_publish_confluence`, no space coords). 10 unit tests.
- **H6 — done (2026-07-01).** Boundary guard closed: `review` component group +
  `test_every_module_is_classified` (default-deny). Boundary guard 3 passed; Track-1 92 passed / 0 failed.

**Epic H offline scope is complete** — all six review modules reproduced generically (241 unit tests pass).
What remains is HITL/company-gated or an architecture decision (below).

## Deferred / gated — the to-do list (NOT built today)

Everything below either needs the **HITL SME gate** or an **architecture decision**, so
per scope it is documented here rather than built:

1. **Real internal review spine (HITL-gated).** The committed `review-labels.yaml` is the
   vendor-BMC generic seed. The real internal source→label chains (SEAL / PAT sources) are
   `Internal`/`Internal-Confidential`, live in a gitignored twin, and must be confirmed
   through the gate ([`03-hitl-sme-flow.md`](03-hitl-sme-flow.md), logged to
   [`gate-log.md`](../../config/gate-log.md)) before they drive any load. Never commit here.
2. **Real acceptance suites (HITL-gated).** `graph-tests/vendor-bmc-smoke.yaml` asserts only
   shape/consistency. Suites that assert real counts/IDs are `Internal` and depend on a
   *confirmed* load — those go in the gitignored twin, gated the same way.
3. **CLI wiring of review commands — RESOLVED (option A, entrypoint exemption).** Wiring
   `graph-verify` / `graph-review` / `sme-notes` / `docs-*` into `cli.py` makes it import the
   `drydocs-review` component. The CLI is the composition root, so it is **exempt** from the
   components-don't-import-each-other rule via `ENTRYPOINT_MODULES` in
   [`tests/unit/test_module_boundary.py`](../../tests/unit/test_module_boundary.py) (still
   default-deny classified in `load`). **This is the canonical answer to the port-side A/B/C
   question: option A.** A company port whose `cli.py` owns the review commands passes the guard
   unchanged — do NOT extract a `review_cli.py` sub-app (option B), which creates a company-only
   structure the producer lacks and re-collides on every future port.
4. **Running against a live graph.** `run_suite` reads a real Neo4j graph; it writes no meaning
   edges (read-only), so *running* it is not HITL-gated — but it needs a provisioned graph
   (Epic G) to exercise beyond the offline unit tests.
5. **Real gate pages (HITL-gated).** `gate_pages.render_gate_page` renders any spec; the committed
   example is vendor-BMC. Pages for real PAT/SEAL load steps encode `Internal-Confidential` data
   (real LoB/Sub-LoB/Product-Line, SEAL ids) — those specs + rendered pages live in a gitignored
   twin and are produced as part of a gated load run, never committed here.
6. **Real `ConfluencePublisher` (company-gated).** The publishing pipeline ships offline publishers
   only (`Noop`/`Local`). A real Confluence push (space coordinates, auth, the internal
   `toby_publish_confluence` wrapper) is a company-side implementation of the `Publisher` Protocol in
   the gitignored twin — deliberately absent from this public template.
