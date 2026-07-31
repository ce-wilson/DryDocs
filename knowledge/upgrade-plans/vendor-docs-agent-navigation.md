# Loading the vendor-docs capture for AGENT navigation

**Status:** plan, not a decision. The layer-1 spine is buildable now; every
meaning edge in layer 2/3 is gate-bound and stays `status: planned` until an SME
signs it (CLAUDE.md §6 — ontology edges are not casual).
**Written:** 2026-07-31, at the `bmc-controlm-utilities` capture.
**Corpus:** `bmc-controlm-9.0.20-utilities` — 1,017 verbatim topics, out-of-repo
(`DRYDOCS_DATA_ROOT/vendor-docs/…`), registered in `config/doc-source-registry.yaml`
with `confirmed: false`.

---

## 1. Why this corpus is not "more bmc-docs"

The existing `bmc-docs` corpus is 26 files we WROTE — a lossy paraphrase, trust
`GROUNDED`, chunk tiers inferred by a heading heuristic because no better signal
exists. This capture is different in two ways that change the modelling:

| | `bmc-docs` (existing) | `bmc-controlm-utilities` (new) |
|---|---|---|
| Trust | `GROUNDED` (our paraphrase) | **`VERBATIM`** (vendor's words) |
| Tier signal | heuristic on headings | **not needed** — the whole corpus is one tier |
| Structure | flat file set | **real hierarchy** from the publisher's `toc.json` |
| Titles | our filenames | **vendor-canonical entity names** (`exportdefjob`) |

The last two are the opportunity. We are not guessing at structure: BMC ships
the breadcrumb (`Utilities > emdef utility for jobs > defjob > defjob XML file
rules`) and the page titles are exact utility names. That is a navigable spine
handed to us for free, and the current lexical shape throws it away.

---

## 2. What an agent actually needs — and where the current shape fails

Today's loaded shape is `(:Chunk)-[:PART_OF]->(:Document)` with
`FIRST_CHUNK`/`NEXT_CHUNK`. That is a good *retrieval* shape and a poor
*navigation* shape. Three concrete failures, each with a design response:

**(a) No named entry point.** The only way in is similarity search. But an agent
usually arrives already knowing the noun — "how do I use `exportdefjob`?" —
and a vector search for a known exact identifier is both slower and less
reliable than `MATCH (u:ControlMUtility {name:$name})`. *Response: first-class,
name-addressable entity nodes with a uniqueness constraint. Vector/full-text
becomes the fallback for "I don't know the name", not the primary path.*

**(b) No lateral movement.** `NEXT_CHUNK` only walks forward inside one
document. Getting from "defjob XML file rules" to "defjob XML file parameters"
requires a fresh search, even though the corpus itself groups them. *Response:
load the TOC hierarchy, and derive a `page_role` so the three-page pattern
(`rules` / `parameters` / `examples`) that repeats across the whole emdef family
becomes traversable in one hop from the utility node.*

**(c) No cheap triage.** To judge relevance the agent must pull chunks, which is
the expensive operation. *Response: a deterministic `abstract` (the topic's
first paragraph) and `page_role` on `:Document`, so an agent can rank candidates
before spending context on chunk text.*

A fourth requirement is correctness, not convenience, and this whole
conversation is the cautionary tale: **the capture is 9.0.20, the estate is
9.0.21.300.** That must be a property on every node, not a footnote in a README
— so any answer built from it can say so. See §5.

---

## 3. Proposed shape, in three layers

Deliberately mapped onto CLAUDE.md §1 so the gate boundary is obvious.

### Layer 1 — the document spine (TAXONOMY: pure classification, loadable now)

Nothing here asserts meaning; it transcribes the publisher's own structure.

```
(:Document {
    doc_id, title, breadcrumb, source_url, sha256, captured_at,
    abstract,            # first paragraph, deterministic
    page_role,           # overview | rules | parameters | examples | reference
    doc_version,         # "9.0.20"
    version_verified     # false until checked against 9.0.21
 })
(:Chunk)-[:PART_OF]->(:Document)          # existing shape, unchanged
(:Document)-[:IN_SECTION]->(:DocSection)  # the toc.json tree
(:DocSection)-[:SUBSECTION_OF]->(:DocSection)
```

`page_role` is derived by an explicit title rule (`"* XML file rules"` →
`rules`, etc.), not by an LLM — the same determinism discipline as the existing
tier classifier, and it must report how many pages it could NOT classify rather
than defaulting them silently.

### Layer 2 — the entity spine (ONTOLOGY: gate-bound)

```
(:ControlMUtility {name, family, kind})   # exportdefjob, ctmorder, defjob…
(:Document)-[:DOCUMENTS]->(:ControlMUtility)
(:Document)-[:SEE_ALSO]->(:Document)      # from in-page cross-links
```

This is the payoff layer and the one that needs a ruling. Open questions:

- Is `:ControlMUtility` a new label, or an instance of the existing
  software-registry model (`:SoftwareProduct` / the `etlprocess-kind-enum`
  family)? Inventing a label because it is convenient is exactly what §1 warns
  against.
- `DOCUMENTS` vs reusing `DESCRIBES` (already registered for
  `:Document -> :SoftwareProduct`). Reuse is probably right; confirm at the gate.
- `SEE_ALSO` is derived from parsed hyperlinks — is a vendor's own cross-link an
  assertion we are willing to carry as a graph edge, or is it presentation?

### Layer 3 — the join to the estate (blocked, and honestly so)

The prize is connecting documentation to the running estate: a job whose
`CMD_LINE` invokes `ctmorder` should reach the page describing it.

**This cannot be built yet, and not for want of effort.** Q8 established the
constraint the hard way: *a relationship cannot span Neo4j databases*, and its
close note records that ADR 0006 plans to re-target doc corpora to `dddocs`
while the software registry keeps writing `drydocs` — which would silently drop
every cross edge. **G32 is the open ruling** on document/content residency and
it gates this layer. Until it lands, layer 3 is a `planned` vocabulary entry and
nothing more.

---

## 4. Agent entry points (QuerySpecs, not raw Cypher)

The agent Q&A spoke already exists (R4 ephemeral specs, R5 `/ask` with citations
carrying trust + classification). So the deliverable is **QuerySpecs**, which
keeps agents off `/raw-cypher` and makes every answer citable:

| Spec | Question it answers | Shape |
|---|---|---|
| `docs.utility-lookup.v1` | "how do I use `exportdefjob`?" | exact name → utility → its docs grouped by `page_role` |
| `docs.section-browse.v1` | "what else is in the emdef family?" | section → siblings, one hop |
| `docs.role-siblings.v1` | "show me the *examples* for this" | doc → same-utility docs of another role |
| `docs.search.v1` | "…something about watching a file?" | full-text/vector **fallback** |

Design rules for all four: bounded expansion (no unbounded variable-length
traversal), every row carries `source_url` + `doc_version` + trust so R5's
citation surface renders provenance, and results are chunk-free by default —
the agent asks for chunk text as a second, deliberate step.

---

## 5. The version caveat as a first-class property

Every node carries `doc_version: "9.0.20"` while the estate runs 9.0.21.300, and
`version_verified: false` until a page is checked. This is not bookkeeping: it
is the difference between an agent answering "Control-M does X" and "the 9.0.20
documentation says X; your estate is 9.0.21.300 and this page has not been
verified against it." The second is the only honest answer this corpus can
support, and the graph should make it impossible to give the first.

A later `bmc-controlm-9.0.21-parameters` capture (already registered as a tree
in the scraper) can flip `version_verified` per topic where the two agree.

---

## 6. Sequencing

1. **Convert + load layer 1** — HTML→markdown against the existing H2 chunking
   contract, `page_role`/`abstract` derivation with an unclassified-count report,
   TOC hierarchy. No meaning edges. *No gate needed.*
2. **Draft the layer-2 gate prompt** — the four questions in §3. *SME session.*
3. **QuerySpecs** for §4 on layer 1 + whatever layer 2 confirms.
4. **Layer 3 after G32.**

Step 1 is genuinely useful alone: hierarchy + role + abstract already beats
similarity-search-only, and it is the half that needs no ruling.

---

## 7. What this unblocks beyond navigation

258 of the 1,017 pages are XML/export/import topics — "XML file rules",
"Creating an XML file", "XML file validation", and the emdef family each with
rules/parameters/examples. `drydocs_lineage/extractors/controlm_xml.py` currently
declares an **ASSUMED** XML contract defined only by synthetic fixtures, with
"XML schema docs are a known reference gap" written into its docstring. This
corpus is that gap closing — and `exportdefjob` is the likely producer of the
estate's own exports, which makes it the page that explains where our input
files come from.
