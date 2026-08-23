# Business-layer location experiment — GraphRAG search of the annual report, ORG + location ontology applied

**Date:** 2026-08-08 · **Directive:** user (desktop chat) — "graph rag search of the annual
report; if it's not loaded into the context graph, apply org and location ontology, determine
if any locations are referenced and the business context … a real test of the concept without
needing the technical layer … a business layer view."
**Classification:** Internal (strategy analysis; the quoted source material itself is public —
SEC-filed annual report + a public GlobalData profile page).

---

## 1. The GraphRAG search verdict: registered, not loaded (this venue)

- The corpus **exists in the registry**: `config/doc-source-registry.yaml` id `jpmc-reports`
  (classification External, `target_db: ddcontext`, captured 2026-06-30, trust VERBATIM).
  It was the FIRST ddcontext doc ingestion — annual-report sections as `:DataAsset` slices
  seeding effective-dated BusinessSegment context — **not** the lexical Document→Chunk backbone,
  and `confirmed: false` (no active loader binds; reshaping is a P4+ decision).
- **Live check (desktop, `neo4jtest`, `ddcontext` — J18 venue): the database is EMPTY.**
  Zero nodes, zero relationships. The June ingestion either ran against the retired
  `neo4j-drydocs-ee` container or was never re-provisioned here (Idea-49's open question).
- The ingest script was removed 2026-07-22 (`5eb68bc`); the PDFs are still local-only at the
  repo root — five of them, including the **2025 and 2026 editions**, which are NEWER than
  the registry's `captured_at: 2026-06-30`. The registry entry describes a 2024-edition run.
- **Conclusion:** a true GraphRAG search (vector retrieval over chunks) is not possible today
  for two independent reasons — nothing is loaded in this venue, and even the registered
  shape is `:DataAsset` slices, not the retrievable lexical backbone. So the concept test below
  is the experiment the directive anticipated: apply the ontology by hand to what the report
  says, and see whether the business layer stands on its own.

## 2. What the sources actually say (VERBATIM, with page cites)

Source A — `jpmorgan-chase-annualreport-2026.pdf` (public SEC-filed annual report, 372 pp):

| Cite | Statement (condensed) |
|---|---|
| p10 | "On-ground presence in **177 locations in the U.S., 60+ countries internationally** and serving clients in **100+ markets**" |
| p6 | Moves "over $10 trillion in **120+ currencies** and more than **160 countries**"; safeguards $35T in assets |
| p59, p63 | **New global headquarters in New York City**, opening later this year |
| p80 | The national bank subsidiary is "headquartered in **Columbus**" [Ohio] |
| p80 | U.K.: "**more than 22,000 employees** … regional headquarters in **London**, a new technology center in **Glasgow**, and a significant footprint in **Bournemouth** and **Edinburgh**" |
| p104 | "The Firm is **managed on an LOB basis**. Effective in the second quarter of 2024, the Firm reorganized its reportable business segments by combining the former Corporate & Investment Bank and Commercial Banking … to form … the Commercial & Investment Bank ('CIB'). … the Firm has **three reportable business segments** – Consumer & Community Banking, Commercial & Investment Bank, and Asset & Wealth Management – with the remaining activities in **Corporate**." |

Source B — GlobalData company-profile locations page (public, paywalled beyond the free tier;
fetched 2026-08-08): head office **270 Park Avenue, New York, NY 10017, USA**; listed
subsidiaries with countries — J.P. Morgan Europe Ltd (UK), J.P. Morgan Bank Luxembourg SA
(Luxembourg), J.P. Morgan Bank Canada (Canada), J.P. Morgan Personal Investing Ltd (UK),
InstaMed Communications LLC (US), Chase Bankcard Services Inc (US), Banc One Equity Capital
II LLC (US), J.P. Morgan Overseas Capital Corp (UK, inactive).

## 3. The ontology application — W3C ORG + location, business layer only

No technical layer touched: no servers, no Control-M, no racks. Every row below is derivable
from the two public sources alone.

| Fact from the source | ORG / location term | Notes |
|---|---|---|
| JPMorganChase, the Firm | `org:FormalOrganization` | The anchor node |
| CCB, CIB, AWM, Corporate | `org:OrganizationalUnit` + `org:unitOf` → Firm | "Managed on an LOB basis" — these ARE the LOB layer of our LOB→Product→Team taxonomy, straight from the source |
| 2Q2024 segment reorg (CIB = former CIB + Commercial Banking) | `org:ChangeEvent` with `org:originalOrganization` (×2) and `org:resultingOrganization` | An **effective-dated org fact** — exactly the "effective-dated BusinessSegment context" the jpmc-reports registry entry was created to seed. The business layer produces temporal structure on its own |
| New global HQ, NYC (270 Park Ave per GlobalData) | `org:hasPrimarySite` → `org:Site` + `org:siteAddress` (city New York, state NY, country US) | Two sources corroborate: report names the city, GlobalData supplies the street address |
| Regional HQ, London | `org:hasSite` with a role qualifier (regional-hq) | Site ROLE is a modeling decision the Z2 gate must take anyway — business layer surfaces it first |
| Technology center, Glasgow | `org:hasSite` (role: technology-center) | City-grain only — no street, no state |
| Footprint: Bournemouth, Edinburgh | `org:hasSite` (role unstated) | Weakest grain: named city, undefined function |
| Bank subsidiary HQ, Columbus [OH] | `org:hasSubOrganization` → JPMorgan Chase Bank, N.A. + its own `org:hasPrimarySite` | The Firm ≠ the bank — the ORG ontology forces the legal-entity distinction the prose blurs |
| GlobalData subsidiaries (8) | `org:hasSubOrganization`, each with country-grain location | Country-only grain; one carries a lifecycle state (inactive) — a status property, not a deletion |
| "177 locations in the U.S., 60+ countries" | **NOT** `org:Site` instances | An aggregate presence CLAIM. There is no enumerable site list behind it in the source — modeling it as 177 site nodes would fabricate data. It is a measurement about the org, trust GROUNDED, not VERBATIM structure |
| "serving clients in 100+ markets", "160 countries" (payments reach) | Market/operational-reach assertions | Business context, not org structure: these describe the RELATIONSHIP to markets, which is context-graph material (layer 4), not ontology-layer structure |

**The grain finding (feeds Z2 directly):** locations arrive at MIXED grain — street address
(NYC), city+implied state (Columbus), city only (Glasgow, Bournemouth), country only
(Luxembourg subsidiaries). The location ontology cannot assume uniform depth; it needs a
city→state→country hierarchy with partial fills, and a rule for which grain each source is
trusted to assert. The Z2 gate's geography-grain question now has business-layer evidence,
not just the infrastructure export's schema.

**The claim-vs-site finding:** the single most important epistemic line in the exercise is
the one between an enumerable `org:Site` (London regional HQ) and an aggregate presence claim
("177 locations"). The first is graph structure; the second is a measurement that must never
be exploded into fake structure. Any future loader for this corpus needs that rule written
down — it is the business-layer twin of the load-map's "unmatched is reported, not dropped."

## 4. Business context determined

- **Locations referenced: yes** — and they cluster into exactly three business meanings:
  (1) **corporate structure** (global HQ NYC, bank HQ Columbus, regional HQ London,
  subsidiary domiciles), (2) **capability placement** (Glasgow technology center — a
  location chosen FOR a function; Bournemouth/Edinburgh as operational mass), and
  (3) **market reach** (177 U.S. locations, 60+ countries, 100+ markets — presence claims
  that describe scale, not sites).
- **The segment story is location-aware**: the U.K. narrative ties 22,000 employees and four
  named cities to a growth thesis. Location in the annual report is never neutral geography —
  it always carries business intent, which is what makes the business layer worth modeling
  separately from the technical layer.
- **The LOB bridge is real**: "managed on an LOB basis" is the company's own language for the
  hierarchy DryDocs already models as LOB→Product→Team. The business layer of the graph does
  not need inventing — the source hands it over.

## 5. What the experiment proves, and what it queues

**Proved:** the ORG + location ontology produces a coherent business-layer view from public
sources alone — org structure, effective-dated change, sited presence at mixed grain, and a
clean boundary against presence claims — with zero dependence on the technical layer. The Z5
map module's contract ("a node label that has a location") is satisfiable by this layer
alone: Firm → sites in New York, Columbus, London, Glasgow, Bournemouth, Edinburgh renders on
a world map today, with `org:OrganizationalUnit` and person/team relationships as the
dropdown dimension.

**Queued (inbox capture, next groom):**
1. The jpmc-reports corpus needs a decision: reshape onto the lexical Document→Chunk backbone
   (making real GraphRAG possible) or keep the `:DataAsset`-slice shape — the registry's
   named P4+ decision, now with a concrete consumer (this experiment) asking for it. The
   2025/2026 editions sitting at the repo root are newer than `captured_at` and should ride
   whichever re-ingest is ruled.
2. The ORG mappings in §3 are gate material: they are proposals (`status: planned` shapes),
   not rulings. The Z2 gate can adopt the grain + claim-vs-site findings; the org-structure
   shapes (`org:ChangeEvent`, site roles, sub-organization distinction) belong to a
   business-layer gate of their own or an E-epic (context-graph) item.
3. `ddcontext` on this desktop is empty — whatever re-ingest is ruled must follow the
   provisioning check first (Idea-49's container question).
