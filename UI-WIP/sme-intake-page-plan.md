# SME Context-Intake page — plan (wf-sme-intake)

> 2026-08-06 · user direction, in-session. This page IS the "SME assignment surface"
> Q10 names as a later slice — the front door for the failure/activity email corpus
> (.msg + Copilot JSON) and, eventually, any unstructured context an SME wants to
> land against the structured graph. Plan only: build slices at the end, each with
> its gate boundary. Nothing on this page ever writes the graph directly.

## What the user asked for (verbatim shape, top to bottom)

1. **Area selector** — dropdowns for Product Line, Product, Area Product, and SEAL:
   "to give us an idea about where it might belong."
2. **Context type** — dropdown (job failure, missed data load or file, data issue);
   the list will grow as we refine it.
3. **Upload** — drag-and-drop for `.msg`, `.json`, `.txt` (TBD): the email, and when
   the Copilot prompt was used, the corresponding `.json` extract.
4. **Review for ontology** — a button, similar to the FCDO tool's review pass.
5. **Related nodes** — a Cypher query that finds related nodes in the structured data.
6. **Agent first-pass correlation** — for SME review, accept or modify.
7. **Confirmation** — sends the package to admin review for acceptance and graph load.

## Page anatomy

Route `/intake` (working name: **Context Intake**), rendered inside the standard
Shell. Persona: the mock-auth roster gains an `sme` persona (`?as=sme`) whose
`towerId` scopes the area selector's default filter, the same drill-your-own rule
the `user` persona already follows; `steward` and `admin` can open the page too
(admin additionally sees the review queue, section 7). One page, seven sections,
progressively enabled — each section unlocks when the one above has enough state.
The intake is a draft the whole way down; an SME can leave and resume.

### 1. Area selector (where might this belong)

Cascading dropdowns, all populated from the live graph via QuerySpecs (the O33
guard applies; read-only):

- **Product Line → Product → Area Product** — the PAT hierarchy already in the
  graph (`ProductLine` / `Product` / `AreaProduct` nodes). Each level filters the
  next; each is optional.
- **SEAL (BusinessApplication)** — searchable select keyed on SEALID + name.
  Selecting an application back-fills the PAT levels when the mapping exists
  (`product-has-application` / attribution edges) and flags a mismatch when the
  SME picks conflicting levels — flag, never block.
- **"Unknown" is a first-class answer** at every level. Q10's acceptance is
  explicit: an email whose folder/process is not extractable lands *unassigned*
  rather than rejected or guessed. The selector is a hint channel, not a gate.

New QuerySpecs: `intake.area_tree.v1` (one call returning the three-level PAT tree,
cacheable), reuse the existing application-lookup spec for SEAL. Identifiers render
as `IdChip` per ui-conventions §2.

### 2. Context-type selector (what kind of thing is this)

Dropdown fed by a **new taxonomy file** `config/taxonomy/context-types.yaml`
(schema `drydocs.context-types.v1`) — this is pure classification (layer 1), so
adding values is a config edit + SME nod, never an ontology gate. Seed values:

| id | label |
|---|---|
| `job-failure` | Job failure |
| `missed-data-load` | Missed data load |
| `missed-file` | Missed file |
| `data-issue` | Data issue |

Each entry: `id`, `label`, `description`, `status: active|retired` (the list grows;
nothing is deleted). A unit guard (`tests/unit/test_context_types.py`) pins the
schema and id uniqueness. Served to the UI through a generated artifact +
drift-test, the gates.json pattern — the page never hardcodes the list. The
dropdown carries an "Other / not listed" option that records free text into the
intake note and shows up in the admin queue as vocabulary-growth signal.

### 3. Evidence upload (.msg + .json, .txt TBD)

Drag-and-drop zone accepting `.msg`, `.json`, `.txt`; multiple files per intake.
The `.msg`/`.json` Copilot pair is auto-linked by basename and shown as one
evidence row with two format chips; unpaired files are legal.

Handling rules (all inherited from Q10 + the publish boundary):

- Files stream to `DRYDOCS_DATA_ROOT/context-intake/<intake_id>/` via a new
  `drydocs_api` multipart endpoint — **never into the repo tree** (the
  gitignored-PDF / vendor-scrape precedent). The repo commits mechanism only.
- Every intake is stamped `classification: Internal` at creation — production
  failure email carries real names, folder names, incident detail; there is no
  unlabeled default (CLAUDE.md §3).
- Each file gets a `sha256` digest at upload (the doc-registry freshness idiom) so
  a re-upload of changed evidence re-queues review rather than silently replacing.
- Parse-preview per file: subject / sent_at / from for `.msg` (display only,
  MAPI parse best-effort), pretty-printed keys for `.json`. Parse failure is a
  warning chip, not a rejection — the file still lands.

**Thread reuse → ingest the diff (user direction 2026-08-06).** People reuse
old email threads: a "new" email is routinely a reply or forward carrying the
whole prior conversation as a quoted tail. Rule:

- **Detect thread identity at ingest**: conversation headers where the `.msg`
  carries them, normalized subject (Re:/FW: stripped), and quoted-content
  overlap against the digests/text of evidence already in the store. Matching
  is a flag, never an auto-decision.
- **The original file always lands whole** — evidence is never edited (the
  adhoc-sme-email rule: a trimmed copy of evidence is no longer evidence).
  What changes is the REVIEW PAYLOAD: when the upload continues a known
  thread, the payload offered to ontology review is the **delta** — the new
  content above the quoted tail — not the whole thread again.
- **The SME decides if the delta adds value**: the upload row shows
  "continues the thread of intake `<id>`" with an inline diff (new content
  highlighted against the prior evidence). Two actions: **Adds value** (the
  delta proceeds through sections 4–7 as this intake's content) or **No new
  value** (the intake records the thread linkage + the decision and STOPS —
  nothing proposed, nothing queued, but the record exists so the same thread
  bouncing back a third time shows both prior decisions).
- Why this matters downstream: without the delta rule, every reply re-proposes
  every entity in the thread, the ontology-review panel drowns in repeats, and
  the corpus (when Q10 loads it) would chunk the same paragraphs N times —
  thread-position would masquerade as corroboration.
- Registry note: the corpus entry itself is Q10's decision (extend
  `adhoc-sme-email` vs add a sibling — four properties differ; that ruling
  belongs to the Q10 build, not this page). The page writes intake records, not
  registry entries.

### 4. "Review for ontology" (the FCDO-style pass)

One button. The backend runs an extraction pass over the uploaded evidence and
returns a **proposed-bindings panel**, the same interaction the FCDO tool's
review gives content owners — machine proposes, human disposes:

- **Recognized entities**: Control-M folder/job names, dataset/table identifiers,
  SEAL ids, file paths, DL addresses — each shown as an `IdChip` with the ontology
  class it would bind to (`ControlMFolder`, `ControlMJob`, `Dataset`,
  `BusinessApplication`, …) and a match tier (exact id / name match / fuzzy).
- **Context-type check**: the extractor's guess vs the SME's section-2 pick;
  disagreement is shown, SME's pick wins.
- Every row is editable: confirm, retype (change the class), or discard. Nothing
  here is a graph write — the output is a *candidate-binding set* stored on the
  intake record with `status: proposed` per row.
- The panel is a governed-surface sibling of the gate pages (VERBATIM render
  discipline): what the SME confirmed is exactly what admin review later sees.

### 5. Related nodes in the structured graph

Below the bindings, a read-only results table driven by a parameterized QuerySpec
(`intake.related_nodes.v1`) — never free-text Cypher from the browser. Inputs:
the confirmed entities from section 4 plus the area selections from section 1.
Shape (illustrative):

```cypher
// resolve confirmed entity ids against the structured graph, one UNION per class
MATCH (f:ControlMFolder) WHERE f.folder_id IN $folder_ids
OPTIONAL MATCH (f)<-[:CONTAINS_FOLDER|CONTAINS_JOB*0..1]-(app)
RETURN 'folder' AS kind, f.folder_id AS id, app.SEALID AS seal, ...
UNION
MATCH (j:ControlMJob) WHERE j.job_name IN $job_names ...
```

Results render with `IdChip` + a compact neighborhood preview (the MiniDag reuse
pattern) so the SME sees *why* a node is related — the folder's application, the
job's folder, the dataset's writers. An advanced disclosure shows the actual
Cypher + parameters (read-only, copyable) for SMEs who want it — transparency,
not an editor.

### 6. Agent first-pass correlation

"Correlate" runs the ADK `graph_qa` agent (Epic R wiring; the Ask spoke's
infrastructure) over: the evidence text + confirmed bindings + related-nodes
result. It returns ranked **candidate assignments** — email → ControlMFolder /
process — each with a confidence band and an evidence chain ("subject names
P012-DLY-LOAD; job P012A01 failed 2026-08-02 in folder X; folder X belongs to
SEAL 88123"). SME action per candidate: **Accept** / **Modify** (pick a different
target from a scoped search) / **Reject all** (stays unassigned — always legal).

Failure posture: agent unavailable → section renders a skip chip and the SME can
assign manually or leave unassigned; the page never blocks on the agent.

### 7. Confirm → admin review → (gated) load

The confirmation writes ONE intake record to the **origin-flagged store** (the
O24 precedent; `origin: sme-intake`): area hints, context type, evidence
digests + paths, confirmed bindings, the accepted/modified assignment, SME
identity + timestamp. Status machine (StatusChip vocabulary, ui-conventions §1):

```
draft → ontology-reviewed → correlated → sme-confirmed
      → admin-accepted | admin-returned (with note, back to SME)
      → loaded            (only after the gates below)
```

Admin view: the same page with a queue rail (`?as=admin`), diff-style display of
what the SME confirmed vs what the extractor proposed, accept/return actions.

**Stepper component — decided 2026-08-06, no new library.** The status machine
renders through an `IntakeStepper` adapted from `LoadsTimeline` (ordered stage
array, one StatusChip per stage, ui-conventions tokens). Action buttons
(Accept / Send back / Reject) render from a **legal-transitions map the API
returns per record** — the server owns the machine, the UI never encodes it a
second time, and adding a hop later is a server-side change. No workflow
library (XState, flow builders): the registry discipline makes a new dependency
non-free, and the machine already has one home in the O46 store. `@xyflow/react`
is already in-stack if the flow ever wants drawing as a diagram.

**The load boundary is absolute and pre-ruled:**
- The corpus load (Document → Chunk) waits on Q10, which waits on G31 → G32
  (database topology ruling — target_db for unstructured content is exactly
  what G32 decides).
- The assignment edge (email Document → ControlMFolder/process) is NEW
  relationship semantics: registered `status: planned` in the vocabulary with a
  gate-prompt spec, loader-inert until the gate signs — Q10's own acceptance.
- Admin acceptance therefore parks records at `admin-accepted` until both gates
  clear; the queue shows a "waiting on gate" chip, honest about why.

### 8. Reviewer-quality signal + admin block (added 2026-08-06, user direction)

> User recall: "there was a backlog item that ranked a user's auto acceptance so
> we could flag poor quality work." Searched 2026-08-06 — no such item exists in
> backlog.yaml, IDEAS, the gate prompts, or git history; it may have been a
> company-side drydocs-review discussion. Captured HERE as the requirement's home
> so it cannot get lost again.

The intake flow is exactly where rubber-stamping would do damage: an SME who
accepts every agent candidate without reading is indistinguishable from a
careful one unless the system measures the difference. Mechanism:

- **Per-SME quality signals**, derived from intake records the store already
  holds (no new data entry): submissions in a rolling window; **auto-accept
  rate** (agent candidates accepted with zero modification); **too-fast rate**
  (confirm faster than a floor per evidence size); **admin-return rate** (their
  submissions returned by admin — the strongest signal, because it is another
  human's judgment, not a heuristic).
- **Defined limits** live in `config/review-quality.yaml` (admin-editable via
  the AdminConfig surface, versioned in git like every config): window size,
  `auto_accept_rate_max`, `min_review_seconds`, `admin_return_rate_max`. The
  limits FLAG, they never act: crossing one puts the SME on the admin queue's
  quality rail with the metric that tripped (Meter + StatusChip idiom).
- **Admin block, human-decided**: once flagged, the admin can block the persona
  from submitting (their drafts survive; the block records who/when/why in the
  store and is reversible with a note). The machine measures, the human blocks —
  the same measure-then-decide posture as every HITL surface in this repo.
  No auto-block, ever: a threshold is a tripwire, not a judge.
- **Ranking view** for admins: per-user panel (submissions, auto-accept %,
  return %, median review time) using the StatTiles/Meter reuse patterns — the
  point is coaching and triage, not a leaderboard; visible to admins only.
- Downstream value: the quality signal is exactly what the future graph-write
  trust model needs (an SME's confirmation weight), so the store schema keeps
  the per-decision detail (what was accepted, modified fields, durations), not
  just the rollup.

## What can build now vs what waits

| Can build now (no graph writes) | Waits on |
|---|---|
| Route, sections 1–3 (selectors, taxonomy file, upload + staging endpoint) | — |
| Section 4 extraction + candidate-binding store rows | — |
| Section 5 QuerySpecs (read-only) | — |
| Section 6 agent wiring | R-series ADK smoke (R11) helps but mock-able |
| Section 7 store + admin queue | — (store is not the graph) |
| Corpus Document→Chunk load | **Q10 ← G31 ← G32** |
| Assignment-edge load | **Q10's HITL gate** (vocab entry `planned` first) |

## Proposed build slices (for grooming into backlog)

1. **O45** `config/taxonomy/context-types.yaml` + guard + generated artifact
   (taxonomy-importer agent; smallest slice, unblocks the dropdown).
2. **O46** Intake API: multipart upload → data-root staging, digests,
   classification stamp, intake-record store (`origin: sme-intake`, O24 shape).
3. **O47** The page shell: route, `sme` persona, sections 1–3 against O45/O46;
   area QuerySpecs.
4. **O48** Ontology-review pass (section 4): extractor + proposed-bindings panel.
5. **O49** Related-nodes QuerySpec + panel (section 5) and agent correlation
   (section 6; mock-able behind the same interface).
6. **O50** Admin queue + status machine (section 7) — ends at `admin-accepted`.
7. **O51** Reviewer-quality signals + admin block (section 8):
   `config/review-quality.yaml` + guard, the derived metrics over intake
   records, the quality rail + per-user panel, and the block/unblock action.
   Depends on O46 (the store) and O50 (the queue it renders into).
8. **Q10 (existing)** stays the load owner: registry ruling (extend-vs-add
   against `adhoc-sme-email`), Document→Chunk load, and the assignment-edge gate.

Numbering indicative — grooming assigns real ids and the epic split (O for the
console surface, Q10 keeps the corpus/load half).

## File storage — ruled 2026-08-06 (user direction + assessment)

The user's framing: local for testing, plan B is Linux server hosting — or does
it need something else? **Answer: it needs no new technology, but any home must
meet three requirements**, all derived from rulings already on the books:

1. **Backup obligation** — Q10's retention note: after Outlook purges (6–18
   months) the extract store is the ONLY copy; a system of record, not a cache.
2. **Access control matching `Internal`** — every intake is classification-
   stamped; the store's ACLs are part of honoring that stamp.
3. **Durable identity independent of location** — already designed in (O46):
   sha256 digests + store-referenced paths, so files can move without the
   records lying.

The staging plan, in order:

| Stage | Home | Status |
|---|---|---|
| Dev / testing | `DRYDOCS_DATA_ROOT/context-intake/` (this machine) | plan of record now |
| Hosted (plan B) | company-side **Linux file server share**, backed up | plan of record for deployment — meets all three requirements with no new tech |
| Eventual candidate | S3-compatible **object storage** (the estate already runs S3 for the DPL zones) | revisit when company-side lands; NOT a dependency |

**The design consequence, and it is the whole point:** storage lives behind ONE
configured base path (the `DRYDOCS_DATA_ROOT` idiom O46 already uses) plus the
digest identity — so local → Linux share → object store is a **config change,
never a code change**. O46 must not let a filesystem assumption leak above that
seam (no hardlinks, no path math in records beyond the relative key).

## Demo script — grounded in the sample estate (added 2026-08-06)

The bundled samples already load a complete synthetic estate on `neo4jtest`
(SEAL ids in the reserved 70001–70099 block; publish-boundary safe), so demo
sessions should run on exactly what the graph already holds — the demo *is*
the ontology working, not a mockup:

**Scenario 1 — job failure (the primary demo; exercises every section):**
- Synthetic `.msg` + Copilot `.json` pair: *"PARAD0060_PEX_EXPLOANRQTDTL_AWS_RFND
  failed 03:12 — refund file not produced"* (a real sample job in folder
  `PRARAG-HLDM-70002-PEX-RFND-DLY`).
- Walk: SME picks SEAL **70002** → PAT levels back-fill from the sample catalog
  (LOB → Product → Area Product, `catalog_lobs`/`pat_product_mapping` samples);
  context type `job-failure`; upload the pair; ontology review recognizes the
  JOB name, the FOLDER (PRAOCG-coded name), and the SEAL id — three entity
  classes, three match tiers; related nodes show folder → its 5 sample jobs →
  the application → its dev team (`CONTAINS_JOB`, attribution, `dev_teams`
  sample); the agent proposes the folder with the evidence chain; admin
  accepts → **parks on the waiting-on-gate chip** (the honest ending is part
  of the demo).
- Why this one first: it lights up the largest confirmed-ontology surface —
  containment, SEAL attribution, PAT hierarchy — with zero new data.

**Scenario 2 — missed file (conditions traversal):**
- Email: an upstream file never arrived, a downstream job sat waiting. The
  sample conditions (`controlm_conditions_in/out`, dependencies) let related
  nodes walk the WAS_INFORMED_BY/condition chain — the demo shows the graph
  answering "what was this job waiting on" from the email's job name alone.
  Context type `missed-file`.

**Scenario 3 — the quality rail (O51):**
- A scripted persona rapid-accepts scenario-1 candidates without modification;
  the auto-accept + too-fast limits trip; the admin queue shows the flag; the
  admin blocks, the persona's next submit is refused with the recorded reason,
  unblock with note. Thirty seconds, and it demonstrates the measure-then-
  human-decides posture end to end.

**Fixture rule:** demo evidence files are SYNTHETIC, live in
`tests/fixtures/intake/` (committed — they reference only reserved-block ids
and sample names), and double as the O46/O48 unit-test fixtures — one corpus
of truth for tests and demos, the bundled-samples precedent.

## Open questions (for the SME, not guessed here)

- `.txt` handling: same evidence class as `.msg`, or a separate "note" kind?
- Does the area hint ever OVERRIDE an extractable assignment, or is it always
  the weaker signal? (Recommended: hint only; extraction + SME beat it.)
- Retention surfacing: should the page show Q10's retention note ("file server
  becomes system of record after Outlook purge") per intake, or per corpus?
- Is the FCDO-style review panel worth generalizing into a shared component with
  the gate pages now, or after the first build proves the shape?
