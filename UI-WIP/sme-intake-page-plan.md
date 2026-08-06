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

**The load boundary is absolute and pre-ruled:**
- The corpus load (Document → Chunk) waits on Q10, which waits on G31 → G32
  (database topology ruling — target_db for unstructured content is exactly
  what G32 decides).
- The assignment edge (email Document → ControlMFolder/process) is NEW
  relationship semantics: registered `status: planned` in the vocabulary with a
  gate-prompt spec, loader-inert until the gate signs — Q10's own acceptance.
- Admin acceptance therefore parks records at `admin-accepted` until both gates
  clear; the queue shows a "waiting on gate" chip, honest about why.

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
7. **Q10 (existing)** stays the load owner: registry ruling (extend-vs-add
   against `adhoc-sme-email`), Document→Chunk load, and the assignment-edge gate.

Numbering indicative — grooming assigns real ids and the epic split (O for the
console surface, Q10 keeps the corpus/load half).

## Open questions (for the SME, not guessed here)

- `.txt` handling: same evidence class as `.msg`, or a separate "note" kind?
- Does the area hint ever OVERRIDE an extractable assignment, or is it always
  the weaker signal? (Recommended: hint only; extraction + SME beat it.)
- Retention surfacing: should the page show Q10's retention note ("file server
  becomes system of record after Outlook purge") per intake, or per corpus?
- Is the FCDO-style review panel worth generalizing into a shared component with
  the gate pages now, or after the first build proves the shape?
