# IDEAS — the idea board (inbox)

Low-friction capture. Jot anything here from any surface — a "what if", a bug you spotted,
a doc that needs writing, a future source to ingest. **No schema required.** Messy is fine.

This is the **inbox**, not the backlog. Nothing here is committed to until it is *groomed*
into [`backlog.yaml`](backlog.yaml) with an id, owner agent, inputs, and an acceptance test.

## How this feeds the backlog

```
capture here (any surface)  ──groom──▶  backlog.yaml item  ──▶  agent pulls it
```

**Grooming ritual** (you, or an Opus `main` session, ~weekly): read this list top to bottom;
for each idea either (a) promote it to a `backlog.yaml` item, (b) merge it into an existing
item, or (c) drop it. Strike through or delete what's been groomed so the inbox stays short.

## Capture format (loose)

`- [tag] one line. (optional: why / where you saw it)`

Tags help grooming: `idea` · `bug` · `doc` · `source` (new data source) · `question` · `chore`.

### Entry header (added 2026-08-05, user direction — the inbox needed identity, state and priority)

Every inbox entry carries a one-line header, then its body:

```
- **`Idea-N`** · 2026-07-22 · `[idea]` · **open** · prio? **Med** —
  <the entry text>
```

The header and the body render as ONE line (the Epic L markdown renderer has no hard
break), which is why the header ends in `—`: it reads as a prefix, the same shape the
file already used (`2026-08-05 — [bug] **Title**`), just carrying identity and state.

| Field | Rule |
|---|---|
| **id** | `Idea-<n>`, assigned in CAPTURE order — oldest is `Idea-1`. Ids are **stable references**: never renumber, never reuse. A new capture takes the next free number wherever it sits in the file (new entries still go at the TOP; position is chronology, the id is identity). **This side allocates 1–9999** — see the allocator bands below. |
| **split** | A big entry whose parts have DIFFERENT dispositions splits into `Idea-Na`, `Idea-Nb`, … Split only when the parts would carry different **status or priority or target item** — not merely because an entry is long. |
| **date** | Capture date. Unchanged by later edits; a later finding is a `KEPT-UPDATED <date>` line in the body. |
| **tag** | `idea` · `bug` · `doc` · `source` · `question` · `chore` — as before. |
| **status** | `open` (needs a decision or a groom) · `parked → <trigger>` (deliberately waiting on a NAMED trigger) · `groomed → <ids>` (produced backlog items) · `merged → <id>` (folded into an existing item's acceptance or notes) · `closed` (resolved, kept for the record). |
| **prio** | **the user's** call: `High` · `Med` · `Low` · `Deferred`. Written `prio?` while the value is **proposed by the agent and not yet confirmed**; written `prio` once the user has ruled it. Confirming is a one-character delete, which is the point. |

### Allocator bands — which side minted this id (added 2026-08-18)

**Producer allocates `1–9999`. Company allocates `10000+`.** Same rule in every series — here and
in `backlog.yaml`'s letter series. The grammar does not change, so `Idea-10012` and `G10604` parse
with every existing regex and no historical id moves.

**Read it by length:** *five digits or more → company; four or fewer → producer.* There is no
boundary number to remember, which is the point — `G604` and `G60` differ by one glyph and sit in
the same visual class, while `G10604` cannot be mistaken for anything producer-side.

**Why the bands exist.** Three allocators mint from one counter with no lock — producer-desktop,
producer-laptop, company. Git serializes the first two only *after* both have pushed, which is
exactly when it is too late, and never serializes the third. This file is `union-append` at port
time (`PORT-MANIFEST.yaml`), so two sides' entries merge and a shared number becomes two different
ideas. It has already happened at every level: `backlog.yaml` carried **two different G70 and two
different G71** after a concurrent push, and the desktop pair had to be renumbered to G75/G76
because `config/gate-log.md` cited G73/G74 inside a SIGNED-OFF record and *a sign-off citation must
not be falsified to settle a numbering clash* (`docs/port-prompt.md`). `PORT-MANIFEST.yaml` records
the same hazard for `backlog.yaml` ("both sides run their own plan against OVERLAPPING ids") and
again for ADRs ("both sides may hold the same ADR number for different decisions").

**Forward-only.** The bands govern the NEXT id each side allocates; nothing historical is
renumbered, because ids are join keys and renaming one in place re-points every citation of it
(the G87 ruling). So a low number means "allocated before the partition", NOT "producer" — that
residual ambiguity is frozen on the day this rule landed and shrinks in relevance from there.

Enforced by `tests/unit/test_plan_ideas.py::test_new_idea_ids_stay_in_this_sides_band` and the
matching backlog guard. The grandfather line is a committed constant, never "the current max" —
a computed floor rises with every new id and silently re-legalizes the band.

**Why `merged` exists, and why it is the most useful status.** Most inbox entries are not
new work — they are a fact that belongs INSIDE work already scheduled. Filing those as new
items inflates the backlog and splits one change across two owners; leaving them in the inbox
loses them. `merged → C25` says the finding now rides that item's acceptance, so whoever
picks it up gets the finding for free.

**Why marked rather than moved.** The groom ritual says a groomed line moves to the audit
trail at the bottom of this file. That works when an entry maps 1:1 to an item. It does not
when one entry carries several findings and only part of it is actionable — moving the whole
line files the open findings under "recently groomed", where nobody looks for open work.
So: **fully consumed → move to the audit trail; partially consumed → mark in place and say
what stays open.** Either way the inbox itself answers "was this groomed?", which is the
question a 1,000-line file with the trail at the bottom could not answer.

## Inbox

<!-- add new ideas at the top -->

- **`Idea-136`** · 2026-08-19 · `[bug]` · **open** · prio? **Low** —
  **`snapshot.ps1`'s RED warn line prints `System.Object[]` where the conclusion belongs.**
  Observed at the 2026-08-19 snapshot: `ci: System.Object[] AT HEAD e0ae9ba - main is RED...`
  — the `-f` arg `$mine[0].conclusion.ToUpper()` (line ~136) stringified as an array, so the
  warn names no conclusion. Cosmetic only (warn-only by design, the RED itself was the known
  billing block: jobs "fail" in 3-5s with no logs), but the line exists so a human reads WHY
  main is red, and right now it can't say. Likely PS 5.1 member-enumeration on `$mine[0]`
  when `gh run list --json` yields nested arrays — pin with `@($mine)[0]` or select the
  property explicitly, then re-run the snapshot to confirm the text.

- **`Idea-132`** · 2026-08-18 · `[source]` · **open** · prio? **Med** —
  **The ServiceNow extracts are being re-sourced INTERNALLY: hand-pulled CSV/YAML → SQL
  against the Snowflake replica views. SME note 2026-08-18.** Today every ServiceNow-derived
  load is a hand pull exported to CSV/YAML and then loaded; nothing queries the replica
  directly. That is changing company-side — each hand-built extract becomes a SQL file, the
  loader's `source_label` flips `csv`/`yaml` → `snowflake`, and an overlay rebinds each
  dataset onto the replica.
  **NOTHING IS OWED PRODUCER-SIDE TODAY** — there are no `snow_*` loaders here and the only
  registered ServiceNow datasets are `snow:cmdb-ci-classes` and the `snowflake:` placeholder.
  This is recorded because it changes what a FUTURE producer-side build should target, and
  because two of the pieces are already scheduled: [[G100]] (the ITSM technician-group gate)
  must build its lookup against the sourced feed, not against a CSV shape that is being
  retired underneath it.
  **THE GRAMMAR IS ALREADY RULED AND SHOULD NOT BE RE-DERIVED.** `config/source-registry.yaml`
  (the `snow` system row) states it: ServiceNow → Snowflake replica → `snow@[db].[schema].<table>`,
  origin stays `snow` with Snowflake as the CARRIER — the same shape as Control-M read from the
  Oracle replica. And the naming rule is explicit: **name the dataset for the ServiceNow TABLE,
  never for the `V_`-prefixed view wrapper.** The replica host, database and schema are Internal
  and stay company-side.
  **WHAT IS AND IS NOT A MODEL CHANGE:** the row models are unchanged — the SQL aliases columns
  onto the existing field names — so this is a SOURCE swap, not a re-shape. Two areas ARE
  net-new and have never been built: per-CI TOM responsibilities (a scoped-app extension table
  resolved to application/deployment) and incidents. Each is a new graph shape and needs its own
  HITL gate before any load, not a loader bolted onto this swap.
  **ONE KNOCK-ON WORTH DECIDING WITH IT:** `source_label: snowflake` would be another value
  outside the declared `'csv' | 'oracle' | 'agent' | 'human'` enum in `drydocs/loaders/base.py`
  — 12 of 28 loaders are already outside it and nothing enforces it. Re-sourcing is the natural
  moment to rule what that field means rather than adding a thirteenth exception.
  **KEPT-UPDATED 2026-08-18:** the ACQUISITION half of this entry now has an owner — Idea-133 groomed to [[N12]] (a declared `acquisition:` block per registry dataset row, so this swap becomes a `mode: manual` → `automated` flip rather than prose in `notes:`) and [[N13]] (the gate prompt ruling that flip once, with O24/K9's override→source-corrected flip). The `source_label` enum question is UNTOUCHED and stays open here.

- **`Idea-130`** · 2026-08-17 · `[idea]` · **open** · prio? **Med** —
  **`jpmc-reports` is an External-PUBLIC corpus, so it is the safest first docmeta
  ingestion — SME direction 2026-08-17.** The annual-report / 10-K MD&A source is
  already registered and classified: `config/doc-source-registry.yaml#jpmc-reports`,
  `classification: External` ("public SEC filings / investor-relations PDFs"),
  `source_url` present, `trust_default: VERBATIM`. **Why it is a good candidate
  specifically:** an External corpus carries no publish-boundary risk, so the P4 load
  path can be exercised end-to-end — chunker, embeddings, trust provenance, the
  `:Uncertain` routing — without any of the redaction care an Internal corpus forces.
  The P4 revision (`knowledge/upgrade-plans/docmeta-p4-revision-single-db.md`)
  currently names only the BMC corpus for the end-to-end local load; this is a second
  External candidate for that slot, and it is gate-bound like the rest of P4.
  **Three facts that change the work, all in the registry entry:** (1) it is
  `confirmed: false`, which is the flag N9 says a future loader gates on; (2) its
  current shape is `:DataAsset` slices, **NOT** the lexical `Document→Chunk` shape —
  reshaping is the P4+ decision, not a load; (3) **the ingest path is gone** —
  `scripts/ingest_jpmc_reports.py` was REMOVED 2026-07-22 (recover via git history)
  and the two PDFs were never committed (root `/*.pdf` gitignore precedent), so
  "publishable" describes the DATA, not a runnable pipeline. Re-running it means
  re-fetching the PDFs and writing a loader against the current module shape.
  Related: this corpus seeded the effective-dated `Company`/`BusinessSegment` context
  whose vocabulary registration is the gap in [[Idea-131]].

- **`Idea-131`** · 2026-08-17 · `[bug]` · **open** · prio? **Med** —
  **`:Company` and both `HAS_BUSINESS_SEGMENT*` edges execute but were NEVER
  registered in the relationship vocabulary — and no guard can see it.** The
  corporate backbone `(:Company {name:"JPMC"})-[:HAS_BUSINESS_SEGMENT]->(:BusinessSegment)`
  is MERGEd by `drydocs_core/schema/ontology.cypher:205-232`, constrained by
  `constraints.cypher:29` (`company_name` uniqueness), documented as *the* corporate
  hierarchy across four `.claude/skills/data-context-extractor/` files, and live in the
  graph (verified: laptop, `neo4jtest`, `drydocs` DB — 4 current + 4 historical edges).
  But `10-node-classifications.yaml` registers `BusinessSegment` and `CatalogLOB` and
  **not `Company`** (57 labels, absent), and no fragment registers either
  `HAS_BUSINESS_SEGMENT` or `HAS_BUSINESS_SEGMENT_HISTORICAL` — only `RECONCILES_TO`
  (`42-local-catalog.yaml`). **NOT a regression:** `git log -S "Company"` over the
  vocabulary returns nothing, so it was never there and there is no ruling to find —
  it is an M0 seed that predates the registry and never got back-registered.
  **WHY NOTHING CAUGHT IT, which is the reusable half:**
  `test_taxonomy_ontology_map.py:134` checks label UNIQUENESS and
  `test_yaml_fragments.py:83` checks fragment KEYS — **nothing cross-checks an edge's
  `from_node`/`to_node` against the registered label set**, so a wholly absent endpoint
  raises no guard. `RECONCILES_TO` passes only because its endpoint happens to be
  registered. That endpoint cross-check is a cheap guard and is the part worth building
  first; it generalizes past this one backbone. This is the exact shape closed for
  `ControlMApplication` (2026-07-09) and deliberately avoided for the `:Port` →
  `:DistributionList` edge, where the node class shipped WITH the edge for this reason.
  **Registering the label + two edges is gate territory** per `docs/RELATIONSHIP_GUIDE.md`
  (`status: planned` first), not a quiet add — but the guard is not.

- **`Idea-129`** · 2026-08-17 · `[bug]` · **closed 2026-08-17** · prio? **Low** —
  **The depgraph snapshot JSON was written CRLF — the surface Idea-121 did not reach.
  FIXED, and the guard Idea-121 asked for now exists.** Measured before:
  **31,505 CRLF / 0 bare LF**; after: **0 / 31,505**.
  **THE FIRST DIAGNOSIS WAS WRONG AND THE EVIDENCE CORRECTED IT.** This entry
  originally blamed `snapshot.ps1:391`. The real culprit on the ritual path is
  `filter_ignored.py:100` — `write_text(...)` with no `newline=`, the *exact*
  Idea-121 defect in a file that sweep never looked at. The tell was in the original
  measurement: **0 bare LF** means one uniform writer produced every line, and
  `snapshot.ps1` injects its meta line with a bare `` `n `` — so had the PowerShell
  been last, the file would have held at least one. `filter_ignored.py` rewrites the
  file after it and decides the committed bytes.
  **BOTH sites are fixed, and that is not belt-and-braces:** `filter_ignored.py`
  early-returns without rewriting when nothing is dropped, and a `-CodeOnly` run never
  calls it at all, so `snapshot.ps1` normalizing `$new` to `\n` is the only guarantee
  on those two paths. Safe as a byte replace — JSON forbids unescaped control
  characters in strings, so every CRLF there is structural.
  **The guard is the durable half.** Idea-121 recorded "nothing guards this yet, so it
  can regress", and Idea-129 IS that regression, found by a stray `git add` warning
  rather than a test. `tests/unit/test_render_determinism.py` now carries two:
  a STATIC check that every declared committed-surface writer passes `newline="\n"`
  (fails on CI, on any platform, the moment a writer is added without it) and a byte
  check that no committed surface holds a CR. Verified RED on
  `drydocs-20260817.json` before the fix, green after. The writer list is DECLARED,
  not swept, because Idea-121 fenced eight non-render writers out on purpose —
  adding a committed surface means adding its writer to that tuple.
  **Left open deliberately:** whether the sibling depgraph repo should emit LF at
  source (Idea-126 territory) — we normalize on arrival either way.

- **`Idea-127`** · 2026-08-14 · `[idea]` · **open** · prio? **Low** —
  **Read-time staleness hint on estate queries and snapshot HTML.** R4 of the GitNexus
  comparison: surface "indexed at commit X / loaded at T; HEAD is Y / now is T+n" in
  query answers and the depgraph html view — the GitNexus `staleness.ts` contract. Our
  snapshot meta header already pins provenance harder (U7/U15); this is the missing
  *read-time* half. Small; depgraph html profile + `drydocs_api`.

- **`Idea-126`** · 2026-08-14 · `[idea]` · **open** · prio? **Med** —
  **Declared-deps extractor DAG in depgraph (sibling-repo item).** R3 of the GitNexus
  comparison: before the lineage forks multiply extractors, adopt the GitNexus runner
  pattern — extractors/profiles declare `deps`, Kahn-validated, runner passes each one
  only its declared upstream outputs (hidden coupling becomes an error, cycle diagnosis
  prints the concrete path), per-phase timing. Lands in `../depgraph`, not DryDocs;
  captured here because grooming happens here.

- **`Idea-125`** · 2026-08-14 · `[idea]` · **open** · prio? **Med** —
  **Named agent verbs over QuerySpecs (impact/context/trace analogs).** R2 of the
  GitNexus comparison: expose reviewed `drydocs_api` QuerySpecs as purpose-built MCP
  tools — `impact` (blast radius over job chains/conditions), `context` (one
  job/asset/series: owners, schedule, upstream/downstream), `trace` (path between two
  estate nodes) — so agents call named verbs instead of composing raw Cypher against
  the generic neo4j-drydocs server. GitNexus evidence: the verb surface, not the graph,
  is what makes agents actually use it. Pairs with Idea-124 (the verbs carry the
  epistemic field).

- **`Idea-124`** · 2026-08-14 · `[idea]` · **open** · prio? **High** —
  **Epistemic labeling on query answers: `exact` vs `lower-bound` + causes.** R1 of
  [`docs/reviews/gitnexus-depgraph-comparison.md`](../reviews/gitnexus-depgraph-comparison.md):
  lineage/impact-style QuerySpec responses (and depgraph's JSON assertions) declare
  whether the answer is complete — `epistemic: exact|lower-bound` plus a
  machine-readable `causes` split (unparsed `cmd_line`s, unresolved invocations,
  gate-pending edges). Extends the trust axis from the *graph* to the *answer*;
  GitNexus doctrine: an empty result set is not evidence of absence when the causes
  say the walk couldn't see. Ontology-cheap — a property on responses, not the graph.

- **`Idea-121`** · 2026-08-13 · `[bug]` · **open** · prio? **Med** —
  **RENDER HALF FIXED 2026-08-13; the remaining writers stay open, so this entry stays
  open too.** all 11 `write_text(` sites in
  `plan_board` / `plan_ideas` / `plan_roadmap` / `design_doc` and the six
  `scripts/render_*.py` now pass `newline="\n"`. Verified by re-rendering EVERY surface
  — board, the six generated JSON, roadmap, ideas, load-map and all 16 design docs —
  and getting a clean tree: **25 dirtied files down to 0**. Suite 2150 passed; both
  ruff gates exit 0 (the added argument pushed five lines over the limit, so
  `ruff format` rewrapped them in the same commit). **What stays open:** the other
  eight `write_text(` sites — `vendor_docs` (2), `publishing/publisher`,
  `publishing/preview`, `schema_graph`, `extract_office_text`,
  `external_vendor_scrape` — which this entry deliberately fenced OUT of the sweep.
  They write non-render outputs and each needs its own call, not a blanket change.
  Also still open: whether a guard should pin this (a test asserting no committed
  render surface contains a CR byte would stop it regressing; nothing enforces it
  today). The original finding follows.
  **The renderers write CRLF on Windows, so every render run dirties the committed
  renders with line-ending-only churn.** Found the same day the LF policy landed
  (`fcc8afa` .editorconfig, `b348b0c` `* text=auto eol=lf`): running
  `render_board.py` + `render_ideas.py` left TEN files modified in `git status`, of
  which exactly ONE — `ideas.html` — had a content change. The other nine
  (`board.html`, `roadmap.html`, `load-map.html`, and six `web/src/generated/*.json`)
  differed only in line endings. Mechanism: the writers call
  `Path.write_text(..., encoding="utf-8")` with no `newline=`, so Python text mode
  translates `\n` to `\r\n` on Windows; git normalizes it straight back to LF on
  commit, which is why no blob ever changed and nobody noticed. **Correctness is not
  at stake — legibility is.** The session ritual's stale-render check reads
  `git status` / `git diff --quiet` after a re-render, and a step that reports ten
  changed files when one changed is a step whose signal is buried in noise. That is
  the Idea-111 failure shape (a gate nobody reads) arriving by a different route, and
  it is exactly the "phantom CRLF-vs-LF noise in tools that read the working tree"
  the `.editorconfig` commit named the same morning. Fix: pass `newline="\n"` —
  available since Python 3.10, and the project is `^3.11` (verified present on
  3.12.10). Nineteen `write_text(` sites repo-wide lack it; roughly ten produce
  committed render surfaces (`plan_board` / `plan_ideas` / `plan_roadmap` /
  `design_doc` plus the six `scripts/render_*.py` JSON generators). Sweep the
  render/generated-surface writers as one unit; the remaining writers
  (`vendor_docs`, `publishing/*`, `schema_graph`, the `scripts/` scrapers) are a
  separate call, not automatic. Idea-120's proposed metrics JSONL writer should be
  born with `newline="\n"` rather than added to the queue.
  **KEPT-UPDATED 2026-08-13 — it is not cosmetic after all: it poisons a committed
  provenance field, and the LF refresh is what started it.** The session-end
  `snapshot.ps1` renders the board and the design docs BEFORE it scans, so those
  renders dirty 25 tracked files and the scan then records `meta.git.dirty: true`.
  That field has one job, stated in the script's own comment: *"does the commit in
  this header actually describe the code that was measured?"* Here the answer is yes
  and the header says no — a reader is told the opposite of the truth, which is the
  exact failure U15 split the field to prevent (the 20260805 snapshot, where the
  "dirt" was three untracked paths). Same false alarm, new cause. The two snapshots
  taken either side of the refresh prove the causation: `bb9788b6` at 02:20 recorded
  `dirty: false`, `7d885c9` at 13:45 recorded `dirty: true`, same script and a clean
  tree both times. Before the refresh the working tree held CRLF and the renderers
  wrote CRLF, so a render changed nothing; afterwards the tree is LF and every render
  dirties its output. So **every snapshot taken on Windows from now on carries a false
  `dirty: true`** until the writers pass `newline="\n"`, and `drydocs-20260813-1344.json`
  is the first one — committed knowingly, recorded here rather than silently. This
  raises the priority question: the fix is ten call sites, and the thing it protects
  is the provenance header of the whole snapshot series.

- **`Idea-120`** · 2026-08-13 · `[chore]` · **open** · prio? **Med** —
  **Debt metrics have no machine-readable history, so "is it getting better" is
  unanswerable.** Newest-only snapshot retention (U12) is right for snapshots, but it
  leaves the tech-debt skill's hand-typed prose as the ONLY trend record for A3/A4/A5.
  That prose has been wrong twice in the direction that hides work — `drydocs_api` at
  the U2 census, then `drydocs_docmeta` invisible to A3/A4/A5 for five days after
  `d647171` — and on 2026-08-13 it blocked attribution of an A5 move from 29 to 31,
  because there is no prior snapshot on disk to diff against. Proposed: `snapshot.ps1`
  appends one row per run to a metrics JSONL beside the snapshot it just wrote (date,
  commit, A3 top module + count, A4 package + first-party counts, A5 count, live
  `IMPORTS` edge count). Append-only and cheap, and it turns every future `/tech-debt`
  run into a diff instead of a re-derivation. U12 stays intact — a metrics ledger is
  not a retained snapshot. Pairs with Idea-119, whose +2 this would have explained.

- **`Idea-115`** · 2026-08-12 · `[chore]` · **open** · prio? **Med** —
  **The rua bundle's script-copy path is a CONVENTION the extractor re-derives, not a
  column the collector declares — so if the two ever disagree, the pipeline reports an
  empty bundle rather than a broken contract.** `drydocs_lineage/extractors/rua_inventory.py:384`
  builds it by hand — `copy_rel = f"scripts{row['path']}"  # the collector mirrors the abs tree` —
  and `scripts.tsv` carries no copy-path column to check it against: the collector writes
  the header `path owner group perms size mtime sha256`
  (`drydocs_lineage/collect/rua_inventory.sh:296`) and mirrors matched files under
  `scripts/` separately. Both downstream consumers then read that derived path —
  G21 `rua_code_ops.py:236` (`read_text` → parse code operations) and G24
  `code_repo.py:235` (`read_bytes` → git blob sha1 → server-vs-repo corroboration).
  **Why it is worth a line rather than a shrug:** the failure is SILENT and reads as the
  wrong thing. Both extractors already handle a missing copy gracefully and correctly —
  `scripts_unreadable` / `scripts_no_copy` in G21, `server_uncomputable` in G24 — because
  an over-cap file is *listed but not copied* by design (`SCRIPT_COPY_MAX_BYTES`, default
  1 MiB). That is the right behavior for the case it was built for, and it is exactly what
  absorbs a layout change: every counter lands in the "too big to copy" bucket, the run
  succeeds, and "the collector's mirror layout changed" is indistinguishable from "this
  estate has large scripts". Nothing errors. Found 2026-08-12 tracing G24 end to end at the
  user's ask; **nothing is wrong today** — the chain is correctly wired and this is a latent
  coupling, not a live defect.
  **The fix is not free, and the tension is the interesting part.** The obvious move — add a
  `copy_path` column to `scripts.tsv` so the location is declared rather than guessed — is a
  **bundle schema change**, and the collector stamps `COLLECTOR_VERSION=rua-inventory/v2`
  precisely so consumers can version-detect. The script's own header already rules that an
  extractor "must treat `scripts.tsv` and the `sha256` columns as OPTIONAL" so v1 bundles
  stay ingestible; a new column means v3 and the same optional-column discipline again, for
  a field every current bundle can already derive. **The cheaper candidate:** leave the wire
  format alone and pin the CONVENTION with a guard — one test that builds a small bundle
  (or uses a fixture) and asserts a `-n`-captured file is readable at
  `scripts{path}` from the extractor's side, so a collector-side layout change reds a test
  instead of quietly zeroing the counters. That is the S10/derived-coverage idiom the repo
  already uses elsewhere. **Decide which**, or rule it accepted-as-is with the reason
  recorded — all three are legitimate; what is not legitimate is the current state, where
  the contract exists only as a comment on one line.

- **`Idea-111`** · 2026-08-12 · `[bug]` · **closed — both CI ruff gates exit 0 again; only the process question is left, and it is the user's** · prio? **High** —
  **SWEPT AND GREEN 2026-08-12 (this desktop).** `ruff check .` and `ruff format --check .`
  both exit **0** — the first time since 2026-08-05. 35 findings and 31 unformatted files
  to zero. The user's deferral was only ever about not racing the concurrent remediation
  session; that session closed (G60/G83/G84 `done`), so the sweep ran the same evening.
  **Fixed, not ignored (the default):** 10 auto-fixable; a 31-file `ruff format`; the 6
  **N818** exception renames in `xml_io.py` at the user's explicit call —
  `UnsupportedEncoding`→`…Error` and its five siblings, **54 references across 5 files**,
  every name verified standalone first so a word-boundary rename could not clobber a longer
  one; **RUF007** ×2 → `itertools.pairwise` (clearer and equivalent); **N802** ×1, a test
  name of this session's own.
  **Two things RULED as keepers rather than fixed, because ruff's suggestion was wrong —
  not merely unnecessary.** This is the half worth reading:
  - **RUF002/RUF003** (14, prose only) now ignored globally with the reason inline.
    `defect A′` / `defect B′` are established identifiers carried in commit subjects
    (`3ebb66d`, `d40c9cb`) and throughout `drydocs_remediation`; ruff proposes a BACKTICK,
    which yields ``defect A` `` — nonsense, and CLAUDE.md is explicit that a style pass
    never renames identifiers. `⊆`/`∪` are set notation in a comment *about* set semantics
    ("emitted tokens ⊆ before ∪ introduced"); ruff proposes capital `U`, which reads as a
    word. **RUF001 stays ENFORCED** and is the one that matters — ambiguous characters in
    IDENTIFIERS are a hazard, in prose they are typography. Same split
    `docs/ruff-format-convergence.md` already drew for RUF001/2/3.
  - **RUF009** ×2 per-file-ignored on `xml_io.py`: the rule catches a shared MUTABLE
    default, and `Span` is `@dataclass(frozen=True)`, so one shared immutable instance is
    correct. Ruff does not special-case frozen dataclasses.
  Suite 2110 passed / 8 skipped; renders verified non-drifting.
  **STILL OPEN, and the only thing left here: the process question below.** A blocking gate
  that nobody read for a week is the actual defect; the lint was just its symptom.
  <!-- original entry, kept for the trail: -->

  **CI has been RED on `main` since 2026-08-05 and nobody noticed for a week.** Last green
  run `2026-08-05T06:10` (`test(currency): bring port-prompt under the currency guard`);
  every one of the 100+ runs since has failed, including four pushed today before this was
  checked. The failure is narrow and always the same: `ruff check` fails, so `ruff format
  --check` never even runs. **Everything else is green** — unit suite, CLI imports, CLI
  help, publish-boundary guard, schema/vocabulary guard. That is why it was survivable and
  also why it was invisible: the job that matters most passes, and only the last two steps
  red out.
  **This is J10 stage 5 working as designed and then being ignored.** Stage 5 (`1fcbf63`,
  2026-08-01) made both ruff gates blocking on purpose, after stages 1-4 cleared 362
  findings and formatted the whole tree at the pinned ruff **0.5.7**
  (`docs/ruff-format-convergence.md`). The debt then re-accumulated over eleven days of
  agent-authored code that never went through the pinned formatter: **48 findings / 44
  unformatted files** as measured 2026-08-12.
  **A hypothesis worth killing before someone re-derives it:** the drift is NOT two ruff
  versions disagreeing. There is exactly one ruff here — 0.5.7 in `pyproject.toml`,
  `poetry.lock` and the installed binary, with no ruff on PATH, no pipx ruff and no
  VS Code/Cursor bundled extension. New code is simply hand-written in the modern
  `assert x, (msg)` shape that 0.5.7 rewrites to its own older style. One formatter, an
  unformatted tail.
  **FIXED TODAY — the gate's SCOPE, not the code.** `pyproject.toml` `extend-exclude` now
  carries the two graph-vs-files capture directories (13 `.py` files, nothing imports them,
  verified before excluding). They are agent scratch scripts kept verbatim as the record of
  each track, and the repo already ruled this class once: *"fixing somebody else's capture
  to satisfy a guard is a provenance call, not a formatting one"* (ledger step 123, which
  inboxed the question as `Idea-103` rather than editing them). Same reasoning as the
  vendored `.claude/skills` block. **48 -> 35 findings, 44 -> 32 files.**
  **STILL OPEN — the sweep, deliberately deferred by the user.** ~1 hour: 10 auto-fixable
  plus a 32-file mechanical format (+452/-320), then ~25 needing judgement — 14
  `RUF002/003` (one character each, ambiguous Unicode in prose), 6 `N818`, 2 `RUF009`, 2
  `RUF007`, 1 `N802`. **Sequencing matters: 22 of the 35 are in `drydocs_remediation`,
  where a concurrent session is working right now** — including all 6 `N818`, which are
  exception-class renames in `xml_io.py` (`MalformedXml`, `LocatorNotFound`,
  `SelfCheckFailed`…) and therefore an API change, not a lint tidy. That session is already
  fixing its own ruff findings, so the sweep should follow their work, not race it. Outside
  their module only **13** remain: 8 `tests`, 2 `scripts`, 2 `drydocs`, 1 `drydocs_lineage`.
  **The process question is the durable half, and it is the user's:** a blocking gate that
  goes unwatched for a week is worth less than an advisory one that gets read. Options are
  a notification on red, a session-ritual step that checks `gh run list` before pushing, or
  accepting red-until-swept as a known state with an owner and a date.

- **`Idea-110`** · 2026-08-12 · `[doc]` · **closed — reclassified as a dated record, same day** · prio? **Low** —
  **CLOSED 2026-08-12.** User ruled option (c): the file is a dated RECORD of the
  2026-07-21 issue, not a usable starting prompt. Its header now says exactly that — a
  `status: DATED RECORD` block with the capture and landing dates, an explicit "do not
  paste as-is", and the reason it is kept anyway (it is the clearest single statement of
  the approved design direction: Kept Orbit brand rules, locked stack, token palette,
  layout anatomy — all of which still hold). The known drift is named in the header rather
  than left for the next reader to chase: the two marks are gone, the final mark is
  UNSETTLED, and mark references in the body are to be read as intent, not as pointers to
  assets. The body is deliberately NOT rewritten — annotating a record beats editing one,
  and the §2/§6 wording is part of what the record records. Two caveats added while there:
  the 33-path check is stamped point-in-time rather than offered as a guarantee, and §7
  ("what actually needs design work") is flagged as the most likely stale section, being a
  2026-07-21 to-do list. `kept-orbit-brand-sheet.png` + `kept-orbit-philosophy.md` remain
  the brand authority and are present. The general hazard below stands and is the residue
  worth keeping.
  **THE RESIDUE IS NOW MECHANISED, same day.** The "cheap standing check" below is a
  seventh port-preflight check, `cited paths resolve`: `drydocs.port_preflight` resolves
  every backticked repo-relative path cited by each document the range **ADDS**, and
  refuses to certify the base on any that resolve nowhere. Run against
  `UI-WIP/claude-design-ui-prompt.md` **as it stood at its merge `429d829`** it returns
  exactly `UI-WIP/drydocs-mark.svg` — the miss, reproduced. Two filters keep it actionable
  and both were measured rather than guessed: a citation with no directory is a filename
  mention (so `drydocs-mark-mini.svg` is deliberately NOT caught — the same line
  `test_runbook_currency` draws), and a citation whose first segment is not a top-level
  entry of this repo is relative to its own document or to a foreign codebase. ADDED-only
  is the other half: added-or-modified reports **59** paths on `ae21ee4..HEAD`, nearly all
  gate-log history and IDEAS entries naming an absence on purpose, while added-only reports
  **1** — this one. Exemptions follow the existing idiom: `RECORD_PREFIXES`
  (`docs/reviews/`, `internal/controlm-config/reference/`) each with its reason, plus
  self-declaration — a header carrying `status: DATED RECORD` exempts its own document,
  which is why the (c) ruling above ALSO closed the check's only live finding. Guards in
  `tests/unit/test_port_preflight.py`, each of the six mechanisms proven to fail on an
  injected defect before being trusted (J26). Documents already covered by
  `test_runbook_currency` are skipped — not to save work, but so that one defect is not
  reported under two check names.
  **`UI-WIP/claude-design-ui-prompt.md` cites two canonical brand assets that main deleted
  as REJECTED two and a half weeks before the doc was merged.** The doc names
  `UI-WIP/drydocs-mark.svg` + `drydocs-mark-mini.svg` as "final vector marks" under
  *Approved / canonical*; `d6022c3` (2026-07-28, "drop three rejected marks") removed both
  from main, and nothing on any branch has replaced them — they resolve nowhere in the tree
  and are not gitignored. A designer following the doc's own reference list is sent to two
  files that do not exist, listed under the heading that says they are approved.
  **How it got here, which is the part worth keeping:** the doc was authored 2026-07-21
  (`d9a2eac`) on a local branch, the marks were dropped from main 2026-07-28, and the branch
  was merged 2026-08-12 (`429d829`). The merge was textually conflict-free — one new file,
  no collision — so nothing flagged that its CONTENT referenced files main had since
  removed. That is the general hazard: merging a long-idle branch validates text overlap,
  never whether the prose still describes the tree. Cheap standing check before landing an
  idle doc branch — resolve the paths it cites.
  **Scope check done, so this is not vaguer than it is:** 33 of the doc's referenced paths
  resolve fine, including `kept-orbit-brand-sheet.png`, `kept-orbit-philosophy.md`,
  `web/src/layout/shellConfig.ts`, `components/ui/EmptyState.tsx`,
  `routes/ModuleTemplate.tsx` and the `drydocs-icons/` registry. The mark pair is the only
  genuine miss. The rest of the doc is a 2026-07-21 snapshot of the console and reads as
  accurate.
  **Decide:** (a) re-point the two lines at whatever the current mark is, if one exists
  outside the tree; (b) mark the brand-asset bullet superseded and say the mark is unsettled;
  or (c) leave it and reclassify the whole file as a dated record rather than a usable
  starting prompt — in which case its header should say so, since it currently reads as
  live instructions ("Copy everything below the line into Claude Design UI").

- **`Idea-109`** · 2026-08-12 · `[bug]` · **closed — fix landed at 841dc6e5, residue swept as J48 the same day** · prio? **Low** —
  **RESIDUE SWEPT 2026-08-12 (this desktop) — J48 `done`, and this entry closes.** 27
  sites judged: 24 modules now route through `repo_root()`, and three were RULED and left
  as written, which is the judgement this entry said each one needed — recorded at the
  site, because "skipping a site is not a disposition": `ontology/schema_graph.py`
  (vocabulary fragments + generated `.cypher` are package resources),
  `scripts/external_vendor_scrape.py` (not an installed package, so `__file__` already
  names the caller's tree — and it *cannot* adopt: those two lines put the root on
  `sys.path` **before** `drydocs_core` is importable), and `drydocs_core/config.py`, the
  one place where following the caller would be a **regression** — `.env` is untracked
  machine-local credentials that a worktree never receives, so a worktree run would find
  no `.env` at all. The mixed case came out repo-content: `var/mapping.db` is derived FROM
  the committed YAML/CSV beside it, so a worktree reading its own `config/` and writing
  main's `var/` is exactly the torn split this entry describes. Gitignored ≠ shared.
  **This entry's own list was short by four**, all the same defect in the same editable
  install: `drydocs_docmeta/registry.py`, `drydocs_docmeta/policy.py`,
  `drydocs_api/intake.py`, and a `_repo_relative()` helper buried INSIDE a function body in
  `drydocs_api/mappings.py` — found by the new derived guard *after* every listed file had
  already been read by hand, which is the case for deriving rather than enumerating in one
  incident.
  **One mechanism finding worth keeping.** The worktree proof's first draft ran its probe
  with `python -c`, which puts the CWD on `sys.path` — so the worktree's own `drydocs/`
  shadowed the editable install, every import came back worktree-relative, and the control
  passed for the wrong reason. The test now runs a probe FILE outside the worktree,
  reproducing the incident's real condition (`sys.path[0]` is the script's directory, never
  the cwd). That is the same asymmetry the original bug turned on, met from the other side.
  **Verified live** (desktop, no database, no company data — re-runs anywhere): a real
  `git worktree`, nine constants across four packages resolving inside it, and
  `cli.DEFAULT_SAMPLES_DIR` correctly staying pinned at the install. A blanket
  search-and-replace of every `__file__` anchor FAILS that test, so it checks the judgement
  and not just the edit. Suite 2092 passed / 8 skipped.
  **FIX 2026-08-12 (this desktop).** New `drydocs_core/repo_paths.py` — `repo_root(fallback)`
  climbs from the cwd to the nearest enclosing `.git` (an `.exists()` test, because a
  worktree root carries a `.git` *file*, not a directory), validates it as a DryDocs
  checkout via `drydocs/__init__.py` + `pyproject.toml`, and otherwise returns the caller's
  old `__file__` anchor. It stops at the first `.git` whether or not that repo validates,
  so neither the `depgraph` sibling nor an unrelated parent repo can capture the paths, and
  installed-package consumers outside any checkout behave exactly as before. Adopted in
  `plan_board`, `plan_ideas`, `plan_roadmap` — the three that route through the installed
  package. Guard: `tests/unit/test_repo_paths.py`, 13 tests, including one that drives a
  **real** `git worktree` through a **real** `scripts/render_board.py` and asserts main
  comes back byte-identical; **verified to fail without the fix** with exactly the original
  symptom (`wrote C:\coding\projects\DryDocs\docs\plan\board.html` from a worktree cwd).
  Suite 1961 passed / 5 skipped. **What the fix also corrected in the diagnosis below:** the
  damage was never "everything goes to main", it was a **torn render** — the five sibling
  scripts `render_board.py` invokes (`render_gates`, `render_enforcement_matrix`,
  `render_load_map`, `render_software_registry`, `render_context_types`) resolve out of the
  worktree's own `scripts/` and anchor on their own `__file__`, so *those* were always
  correct; only the three package-routed outputs went to main. Half the render in each tree
  is why nobody noticed. **RESIDUE, still open:** ~17 other `_REPO_ROOT`/`REPO_ROOT` sites
  share the raw `Path(__file__)` pattern (`gate_pages`, `graph_verify`, `review_labels`,
  `source_mappings`, `seal_samples`, `port_preflight`, the four `drydocs/loaders/*`,
  `drydocs_core` `precedence`/`source_registry`/`manual_mappings`/`mapping_store`,
  `orchestration/crosswalk`+`shell`, `ontology/schema_graph`). They are NOT all bugs — the
  rule is that repo-*content* paths follow the caller while package-*internal* resources
  (e.g. `drydocs_core/schema/*.cypher`) rightly follow `__file__` — so each needs that
  one-line judgement, which is why this was scoped to the ritual rather than swept.
  *(Swept as J48 later the same day — see the top of this entry. The real count was 27, not
  17, and the rule held: 24 adopted, 3 ruled package-internal or install-anchored.)*

  <!-- original diagnosis, kept for the trail: -->

  **A worktree-isolated agent that runs the session-end render ritual writes its output
  into the MAIN repo, not its own worktree.** Both `results-sonnet` tracks hit this
  independently within the same half hour on 2026-08-11 and both recovered, which is why
  the sonnet `RUN-LOG.md` calls it out as adoptable "independent of the graph-vs-files
  question". Mechanism, re-verified on this desktop 2026-08-12: `drydocs` is installed
  **editable** into `.venv` via a `drydocs.pth` pinned at the main tree, and
  `drydocs/plan_board.py:34` sets `_REPO_ROOT = Path(__file__).resolve().parent.parent` —
  so the defaults are anchored to *where the package file lives*, never to the cwd or to
  the worktree the caller is standing in. Running `python scripts/render_board.py` puts
  `scripts/` on `sys.path[0]` and does **not** put the cwd on the path, so the worktree's
  own `drydocs/` is never shadowed in: the import falls through to the editable install.
  Reproduced with cwd set to `.claude/worktrees/agent-a6fcf6daf8af92ce7` — `p.__file__`
  and `DEFAULT_BOARD_PATH` both resolve under `C:\coding\projects\DryDocs\`, the main
  tree. No database and no company data, so it re-runs anywhere (J18). It is silent: the
  render succeeds, the worktree stays clean, and the main tree acquires an uncommitted
  board/design-doc render nobody in that session wrote. `DEFAULT_BACKLOG_PATH` has the
  same anchor, so the agent also *reads* main's backlog, not its own. Blast radius is
  every `scripts/render_*.py` plus `snapshot.ps1`, which drives them — i.e. the whole
  CLAUDE.md §0 session-end ritual, exactly the step an agent is most likely to run
  unprompted. Candidate fixes, not yet ruled: derive `_REPO_ROOT` from `git rev-parse
  --show-toplevel` at call time; or have the render scripts pass explicit paths resolved
  from their own `__file__`; or refuse to write outside the caller's worktree. Related to
  `Idea-108`, which is the wreckage this behaviour left behind.

- **`Idea-108`** · 2026-08-12 · `[chore]` · **closed — salvaged, then pruned under user ruling, same day** · prio? **Low** —
  **CLOSED 2026-08-12.** User ruled "prune worktrees + branches" once the salvage below
  made it safe. Executed on this desktop after a final re-verification that all four
  untracked files were byte-identical to their committed captures and all four branches
  were ancestors of `main`: both `.claude/worktrees/agent-*` trees removed,
  `git worktree prune` run, and all four `worktree-agent-*` branches deleted
  (`6c24963` ×2, `23e14bb` ×2). `git worktree list` now reports only the main checkout and
  no `worktree-agent-*` branch remains. Nothing unique was lost — the content lives in
  `o31-ALPHA.diff` / `o31-BETA.diff`, committed and pushed first.
  **UPDATE 2026-08-12 (this desktop): the "both directions are destructive" dilemma is
  resolved, because there was a third, non-destructive direction — finish the capture.**
  The two worktrees are the ALPHA/BETA tracks of the `results-sonnet` O31 coding
  comparison (`docs/reviews/graph-vs-files-experiment/`), whose protocol told each agent
  to write a `<run>.diff` back to the main tree and **commit nothing**. Checking the two
  captures against their live worktrees showed they were **not captured to the same
  standard**: `agent-aa168e5039f906d30` = ALPHA, whose `o31-ALPHA.diff` is a structured
  file (`=== git diff (tracked files) ===` / `=== NEW FILE: … ===` / `=== git status
  --porcelain ===`) that **embeds both untracked files in full** — that worktree was
  already 100% redundant. `agent-a6fcf6daf8af92ce7` = BETA, whose `o31-BETA.diff` was a
  plain `git diff` plus a porcelain listing: it **named** `scripts/render_underhood_benchmark.py`
  and `tests/unit/test_underhood_benchmark.py` as `??` but carried **none of their
  content**, and BETA's report only describes the script. So 737 lines — the *core
  deliverable* of half the comparison — existed nowhere but that dirty worktree, and the
  prune this entry was raised to authorize would have destroyed it while the diff on disk
  looked complete. **Done:** `o31-BETA.diff` rewritten into ALPHA's format with both files
  embedded verbatim — **744 insertions, 0 deletions**, every pre-existing byte verified
  byte-identical in place and both embedded files verified exact against the worktree.
  **What is left is only the prune**, and it is now genuinely safe: both worktrees are
  fully represented in tracked files, and all four `worktree-agent-*` branches are already
  ancestors of `main`. Still the user's call because `git worktree prune` / branch deletion
  is irreversible and touches another stream's trees. The separate render-path finding
  these two runs surfaced is now filed as `Idea-109`. Sibling of `Idea-17` (post-squash
  relic cleanup).

  <!-- superseded framing, kept for the trail: -->
  **Two abandoned agent worktrees are holding UNCOMMITTED work that no branch and no
  `git log` will ever show.** Found at the 2026-08-12 groom, verified on this desktop:
  `git worktree list` reports `.claude/worktrees/agent-a6fcf6daf8af92ce7` and
  `.claude/worktrees/agent-aa168e5039f906d30`, both pinned at `6c24963` (2026-08-11)
  while `main` is at `887a0e7`, and BOTH TREES ARE DIRTY — 6 and 8 changed paths
  respectively, including an untracked new file `scripts/render_underhood_benchmark.py`
  and modifications to `docs/restructure/backlog.yaml`, `docs/plan/board.html`,
  `docs/plan/roadmap.html`, `tests/unit/test_render_determinism.py`, `CHANGELOG.md`
  and two `web/src/underhood/` sources. All four `worktree-agent-*` branches are
  ancestors of `main` (`git branch --merged main` lists every one), so the BRANCHES
  carry no unique commits: the only unique content in the repo is that uncommitted
  working-tree state. Two of the four branches have no worktree directory left at all.
  Why it is worth a decision rather than a sweep: a `git worktree prune` or a routine
  branch cleanup erases the untracked script silently, and the standing concurrent-sessions
  rule is that no session touches another stream's uncommitted work — which is exactly why
  the groom looked and did NOT act. What the user rules: is this a superseded
  `render_underhood_benchmark.py` experiment that can go, or unlanded work to commit onto
  a branch first? Sibling of `Idea-17` (post-squash relic cleanup), which this groom
  narrowed the same day.

- **`Idea-104`** · 2026-08-11 · `[question]` · **open** · prio? **Med** —
  **The MFT route id changed shape between the field observation and the standard, and
  nobody has said which is real.** The 2026-06-11 production capture
  (`internal/standards/technology/description-field-metadata-plan.md`) records one
  numeric key, `ROUTE_ID: 372399`. The 2026-08-11 standards capture records a
  *directional pair* of *string* ids, `INBOUND_ROUTE: MFTS_RT_IN_…` /
  `OUTBOUND_ROUTE: MFTS_RT_OUT_…`, each modeled as a `dprod:DataProductPort`. Three
  readings and they lead different places: the strings are documentation placeholders
  and the real ids are numeric; the route-id format genuinely changed; or the numeric id
  was only ever one leg of a pair nobody had split yet. It matters because C16's prefix
  governance assigns a SINGLE target (`mfts.routeId`) that a directional pair does not
  fit, and because a `dprod` port needs a stable key. Same capture, same class of
  problem, worth ruling together: `SourceSnowQueue` (the *source system's* queue,
  populated in production) and `PDN_SNOW_QUEUE` (the *downstream consumer's* queue,
  `NULL` in the standard) are DIFFERENT SUBJECTS that a naive key mapping would merge.
  **CHECKED AT THE 2026-08-11 GROOM — still open, and now half-answered.** C30 (done, 2026-08-11) retires the INBOUND/OUTBOUND route pair ON WATCHERS, because a watcher is inherently inbound, and drops `PDN_SNOW_QUEUE` from the job token set — so the directional-pair half and the two-queues half both narrow. What C30 did NOT rule, and what still needs the SME, is the one this entry was raised for: whether the real route id is the numeric `372399` or the `MFTS_RT_*` string, which decides both what C16's single `mfts.routeId` prefix target points at and what a `dprod:DataProductPort` is keyed on. NOT groomed into an item, deliberately: the two readings lead to different prefix governance and a different port key, and a groom cannot pick between them.
  **RE-CHECKED AT THE 2026-08-12 GROOM — still the SME's, and now explicitly PROTECTED in an item rather than only in this file.** G83 applies C30's ruling to the parse contract, which means it touches exactly the two entries that carry this question. Its acceptance therefore says in writing that marking the route pair retired is NOT an answer to which route-id shape is real, and that whichever entry survives must keep the note recording the two unreconciled forms — so the evidence cannot be tidied away with the tokens. The question itself is unchanged and unowned.

- **`Idea-93`** · 2026-08-08 · `[chore]` · **groomed → executed IN PLACE at the 2026-08-09 groom (14 stale `inputs:` fixed in backlog.yaml) + merged → L19 (the design-doc half); the E1 status question STAYS OPEN — user call** · prio? **High** —
  **next_ready needs a re-groom: 9 of 62 items carry stale `inputs:`** (persona Run 2,
  U-pm: `docs/reviews/persona-project-manager-2026-08.md`). Six causes: (1) the S5
  2026-08-06 split of `config/taxonomy-ontology-map.yaml` and
  `drydocs_core/ontology/relationship_vocabulary.yaml` into fragment DIRECTORIES —
  stales Q14, G34, U10, U11 (and one traceability-matrix Component ref, per U-tw —
  re-point it in the same pass); (2) `web/src/routes/ask/` never existed — the ask
  module is `web/src/ask/` + `routes/AskRoute.tsx` (Q15, R11, R12); (3) U10 cites the
  retention-deleted `drydocs-20260802.json` — rule of thumb: cite the snapshot
  DIRECTORY, never a dated file, retention makes dated cites self-staling; (4) R9 has a
  filename typo (`persona-architect-…` → `persona-python-architect-…`); (5) V4 cites
  `drydocs/review/`, which is flat files not a directory; (6) status hygiene — E1 has
  worn `in_progress` since 2026-06-22 while actually waiting on gate scheduling;
  consider `blocked`. Done-claims audit itself: 271 claims, ZERO false — the ledger
  holds.
  **GROOM 2026-08-09 — what was executed, and what is left.** Fourteen (not nine)
  non-`done` items carried a stale `inputs:` path, and all fourteen were corrected in
  `backlog.yaml` at this groom rather than promoted, because `backlog.yaml` is the file a
  groom owns: `E1`, `Q10`, `Q11`, `Q14`, `G34`, `G44`, `U10`, `U11` re-pointed at the S5
  fragment DIRECTORIES (`drydocs_core/ontology/relationship_vocabulary/`,
  `config/taxonomy-ontology-map/`); `E2` likewise; `Q15`, `R11`, `R12` re-pointed at
  `web/src/ask/` + `web/src/routes/AskRoute.tsx`; `U10` also dropped the retention-deleted
  dated snapshot for the snapshot DIRECTORY (the rule of thumb this entry proposed, now
  applied); `R9` fixed to `persona-python-architect-2026-07.md`; `V4` re-pointed at the five
  flat drydocs-review files plus `drydocs/publishing/`. `done` items were deliberately NOT
  touched — their `inputs:` were true when the work ran, and rewriting them edits the record
  rather than the work queue. STILL OPEN, and the reason this entry stays in the inbox: the
  **E1 status question** (in_progress since 2026-06-22, actually waiting on gate scheduling —
  `blocked` may be the honest value). A groom does not move an item's status: status is the
  claim channel between the two machines, so that one is the user's call. The design-doc and
  traceability-matrix half of this entry rides L19 clause (f).
  **RE-AUDITED 2026-08-12 (groom) — the 08-09 sweep has held, and the two new stale paths
  found were fixed in place.** The check re-run across all 112 non-`done` items (leading path
  token of every `inputs:` entry, existence-tested against the tree) returns THREE refs, down
  from fourteen: `G63` and `G64` both cite `config/audit-fields/` as a DIRECTORY when the
  ledger is the file `config/audit-fields.yaml` — every one of the other twelve references in
  `backlog.yaml` spells it correctly, so this is a typo and not a planned split; both corrected
  at this groom with the reason in a trailing comment. The third, `Y4`'s `backlog/items/`, is
  NOT stale: it is the sharded directory `Y2`/`Y3` create, and an input that names a
  deliberate future output is the one legitimate form of a non-existent path. Worth keeping as
  a standing groom check — it is cheap, it caught two, and `L27`'s enforcement mechanism does
  not cover `backlog.yaml` inputs. The E1 status question is untouched and still the user's.

- **`Idea-89`** · 2026-08-07 · `[bug]` · **closed → fixed in place 2026-08-07 (SME ruling); no item minted** · prio **Med** —
  **`OverviewRoute` renders ALL modules unfiltered — the Overview pick-list offers
  routes the persona will bounce off.** `OverviewRoute.tsx:94` maps `MODULES` with no
  `canAccessModule` filter, while `Aside.tsx:50` does filter
  (`MODULES.filter((m) => canAccessModule(m.access, persona.role))`). So for the `user`
  persona the Overview "What do you want to look at?" list shows `gates`,
  `underhood` and now `software` — all `access: 'sme'` — and clicking any of them
  hits the App.tsx role guard and redirects to `/`. The fix is one `.filter(...)`,
  but it CHANGES BEHAVIOUR for modules that predate `/software`, so it wants its own
  item with a test rather than a drive-by edit inside another item's commit. Worth
  deciding at the same time: whether an inaccessible module should vanish or render
  disabled-with-a-reason (vanishing is what the aside already does, so consistency
  argues for the filter). (Found at the /software build, 2026-08-07, laptop —
  `/software` inherited the defect rather than causing it.)
  **RULED 2026-08-07 (SME): VANISH, matching what the aside already does.** The
  disabled-with-a-reason alternative is DECLINED — *"I don't want to overcomplicate
  the UI; we are still in proof-of-concept early stages, authentication will be
  added later if needed."* That reason is the durable half: a second access idiom
  is complexity bought against a decision NOT YET MADE, and the moment real
  authentication lands the whole affordance gets re-decided anyway. One idiom, one
  place. FIXED IN PLACE rather than promoted: with the behaviour question ruled,
  what remained was a one-line `.filter(...)` making the pick-list agree with the
  aside — minting an item to close it the same minute is ceremony, not audit. The
  groom was right to flag the disagreement; the ruling is what dissolved it.

- **`Idea-86`** · 2026-08-07 · `[source]` · **parked → G32 rules `target_db`** · prio? **Med** —
  **Register the internal MWAA documentation as a doc corpus — blocked on `target_db`,
  which G32 owns.** The internal MWAA implementation-docs locator saved this session
  (`internal/airflow-reference/mwaa-internal-docs.md`, hung off the `airflow` system
  row's `locator.internal_docs` in `config/source-registry.yaml`, id
  `airflow:internal-implementation-docs`) has NO entry in
  `config/doc-source-registry.yaml`, so `drydocs docs-coverage` reports Airflow as
  `no-corpus` — a true statement, and the exact row the Q16 report exists to print.
  Registering one requires `target_db`, and `tests/unit/test_doc_registry.py` admits
  only `{dddocs, ddcontext}` with no "pending" value — a field G32 is actively
  deciding. **User ruling 2026-08-07: WAIT for G32** rather than declare a value that
  the ruling may reverse. When it unparks, the entry is tier **T2** (internal
  platform), connector **web**, curation **sme-confirm** (fixed per tier), and
  classification **Internal**.
  TRIGGER RE-CHECKED 2026-08-12 (groom) — **NOT fired.** G32 is still `in_progress` (a drafted,
  unsigned gate awaiting the SME), so `target_db` has no ruled value and the user's WAIT ruling
  stands. Worth noting for whoever schedules that gate: the residency question now has a THIRD
  waiting consumer — C34 §(b1) blocks its cross-corpus half on the same constraint (a Neo4j
  relationship cannot span databases), alongside this entry and `Idea-88`. Three parked items on
  one unsigned gate is the argument for scheduling it, not for pre-empting it.

- **`Idea-74`** · 2026-08-05 · `[source]` · **open — user decision, blocks O44 column 3** · prio? **Med** —
  **Does DryDocs ingest the ServiceNow queue/assignment-group export, and
  producer-side or company-side?** O44's third column wants the SNOW queues that
  match an application and the technician roles inside them. `snow:cmdb-ci-classes`
  is registered (Q4 ruling, 2026-07-31) but `confirmed: false`, `adapter: ~`, and
  it captures CMDB **classes** — not queues, not assignment groups, not people.
  The concept is real and evidenced in prose only: the runbook skill's
  template-spec cites AO (L3) and RE/RRT (L2) Snow queues with a `Technician`
  role, and `internal/remediation/governance/critical-batch-and-self-heal.md`
  names a SNOW technician group plus a CTASK peer-review task. So the shape is
  known and no dataset carries it. Decide (a) register a second SNOW dataset for
  the queue/group export and build it here, (b) company-side only, in which case
  O44 column 3 is permanently empty and its acceptance should say so, or (c) defer.
  Note this is ALSO the other half of G35 §D — the ServiceNow TOM Accountable view
  is the surface whose counts disagree with SEAL's, and neither is ingested today.

- **`Idea-70`** · 2026-08-05 · `[decision]` · **closed — RULED same day, no item** · prio? **Med** —
  **`fcdo-frameworks` corpus activation — SME "under consideration" at the
  fcdo-crosswalk sign-off (gate-log 2026-08-05).** RULED in-chat the same
  session ("flip to activate. I want to settle our ontology with what they
  published"): (a) `confirmed: true` flipped in
  `config/doc-source-registry.yaml` with a gate-log RECORD entry; (b) the
  flip proceeds INDEPENDENTLY of the row-5 recapture — activation is the
  path that produces the recapture evidence. Test moved with the flip.
  No backlog item needed; the executed-pre-groom pattern.
  ORIGINAL ENTRY: the gate confirmed the vocabulary crosswalk (rows 1-4/6-8)
  and the SME remarked on §A that activating the corpus is under
  consideration, since the alignment check it was waiting on has passed.
  Sub-decisions: (a) the activation flip itself (producer-side registry
  state; the actual Confluence scrape stays company-side/on-network), and
  (b) wait for the row-5 recapture or proceed independently.

- **`Idea-63a`** · 2026-08-05 · `[question]` · **closed — answered; the cardinality question is settled** · prio? **Med** —
  **Control-M app code → SEAL cardinality — CORRECTED 2026-08-05: `uniq -d`
  tests the registry key, NOT the tier, and is necessary but NOT sufficient.** `AOC` and `DCL` are each
  a UNIQUE row in the file and still 1:many in reality (see the tier-1-shaped-CSV entry above). K8
  authors one steward row per app code and fans it out to folders (§B1), while
  `graph-tests/folder-attribution-coverage.yaml` enforces folder→application **1:1**. **Many codes →
  one SEAL is SAFE and already exercised** — SEAL 35806 (a reporting engine) registered ONE CODE PER
  SCHEMA, and two distinct codes carry SEAL 111809. **One code → many CONSUMERS is real and is tier 2**,
  handled by K7's surfacing rule rather than by the cardinality of the file. Still worth running
  `awk -F, 'NR>1{print $1}' <file> | sort | uniq -d` — a duplicated code would ALSO make the K9 manual
  tier-5 pins ambiguous (they were rekeyed to `app_code=<CODE>` and are hand-authored) — but an empty
  result proves only that the registry is a function, not that any code is tier 1. *(Split 2026-08-05:
  the `descr` half became `Idea-63b` — different disposition, since the cardinality question has an
  answer and the review queue is unbuilt work.)*

- **`Idea-61`** · 2026-08-05 · `[source]` · **parked → AutoSys ingestion work resumes (row 12 is a crosswalk amendment gate; checked at the 2026-08-07 groom — no active AutoSys stream to hang it on)** · prio? **Med** —
  **AutoSys attributes at a NAME-PREFIX grain, not a folder grain — crosswalk
  row 12, needs a gate amendment.** Placeholder captured in
  [`external/orchestration/autosys/README.md`](../../external/orchestration/autosys/README.md); the
  `autosys-crosswalk` gate is SIGNED (11 rows, 2026-07-14) so this cannot be appended to
  `config/crosswalks/autosys-to-bmc.yaml` silently. Observed: the AutoSys code registry maps a code to
  a LIST of instance-qualified name prefixes (`t08.x; u08.x; l08.x`), and a job name is a dotted
  namespace `<instance>.<lob>.<app>.<name>.<type>` — so attribution is a prefix MATCH, not a container
  lookup, and the environment lives in the instance prefix (the FID-name env-triplet convention one
  level up). Two load traps to handle before, not during, a load: a SENTINEL SEAL id whose row says
  the code must not be used (needs an explicit reject list — a lookup miss is not the same thing), and
  lifecycle state ("SEAL Decommissioned NO New EDIT ACCESS Permitted") trapped in a free-text info
  column beside a date.

- **`Idea-60`** · 2026-08-04 · `[source]` · **groomed → C25** · prio? **Med** —
  *(the gate SESSION is now a backlog item; the rest of this entry
  stays open — the sub-application USES_SOFTWARE source and the two missing product rows are not
  in C25)* —
  2026-08-04 — [source] **Software VERSION as graph context, from an adhoc evidence email — two gates
  drafted, both awaiting SME.** An SME email compiled for a version-readiness review lists install
  paths per functional id for one ETL product. Opening proposal was
  `(:BusinessApplication)-[:USES_SOFTWARE {version}]->(:SoftwareProduct)-[:documented_by]->(email)`;
  two defects named in the draft: (1) Neo4j cannot hang a relationship off a relationship, so the
  evidence attaches by property pointer / node-grain edge / reified assertion — not as drawn; (2) the
  rows are **(fid-name, install-path)** rows, not (application, product) rows — the same app appears
  many times with different versions and is reached only through a MUTABLE ownership join, so writing
  the app-level edge directly bakes a time-varying derivation into a fact. Gate
  `software-version-context` proposes: load at the AppUser grain (new vocab entry
  `reg_appuser_uses_software`, same label, C8-clean), MERGE keyed `{source, install_path}` (NOT
  `{source}` — C14's key assumes one fact per pair and this source asserts several), version parsed
  from the path via a pattern table shaped like `invocation_patterns`, observed versions NEVER
  auto-appended to the curated `software-registry.yaml` product row, evidence attached by
  `evidence_doc_id` pointer with reification as the named upgrade path. Corpus `adhoc-sme-email`
  registered (`confirmed: false`, citation-only, connector `email`). App-level rollup deliberately
  BLOCKED on the FID gate. **Groom both gates + the doc-09 phases into backlog items once signed.**

- **`Idea-57`** · 2026-08-05 · `[bug]` · **merged → J35 (2026-08-07, the SHA-citation half); the company-side credential fix stays open, company's hand** · prio? **High** —
  **The company side cannot fetch the producer, and has been answering
  from a cached ref without knowing it was one.** A company session reported "producer repo
  not reachable — private or removed" and fell back to `cewilson/main @ 5f79d145`. The repo
  is neither private-to-them-by-design nor removed: `gh repo view ce-wilson/DryDocs` from
  the producer returns `PRIVATE` and healthy with a current `pushedAt`. So it is an ACCESS
  failure — expired PAT, lapsed SSO authorization on the token, or a proxy — and all three
  are indistinguishable from `git fetch`. Blocks guardrail 1 outright ("read at producer
  HEAD, not the ref you last fetched"). Warning added at the top of `port-prompt.md`
  §"Last completed port", but the fix is company-side credential work. **The design question
  worth grooming:** a cached-ref read is currently indistinguishable from a live one to the
  reader of the answer — should the port prompt require every producer-tree citation to
  quote the SHA it was read at, so a stale read announces itself?

- **`Idea-50`** · 2026-08-04 · `[source]` · **parked → the internal DPL build starts landing** · prio? **Med** —
  **`controlm-pipeline-stub` captured + integration plan written (internal).**
  The internal DPL Control-M XML builder/validator package (config → generate → validate →
  upload → runtime, 14/14 green) is captured VERBATIM at
  `internal/controlm-config/reference/controlm-pipeline-stub-capture.md`, and the
  work order for the internal Opus 4.8 agent is
  `internal/controlm-config/controlm-pipeline-stub-integration-plan.md` (items X1-X3 XML-seam
  supplement, W1-W4 greenfield emitter for the fix module, V1-V2 CR### rules, E1-E4
  classifier/gate enrichment, F1 fixture factory). Producer-side grooming trigger: the
  producer-TWIN items (E2 job-name grammar mechanism, F1 sanitized fixtures, W1 if promoted
  to drydocs_core) groom into backlog.yaml when the internal build starts landing — epic
  placement (G-series vs new) is a user call at that groom. Notables the capture settles:
  the stub IS the vendor-schema acquisition remediation XML I/O was parked on
  (Folder.xsd + full attribute reference), and the DPL job-name grammar closes half the
  "job naming standard = outstanding gap" memory (folder grammar corroborates PRAOCG).
  TRIGGER CHECKED 2026-08-04 (weekly groom) — **NOT fired, stays parked.** Both capture
  files verified present (`internal/controlm-config/reference/controlm-pipeline-stub-capture.md`
  and `internal/controlm-config/controlm-pipeline-stub-integration-plan.md`), but the stated
  trigger is the INTERNAL build starting to land, and nothing from X1-X3 / W1-W4 / V1-V2 /
  E1-E4 / F1 has landed yet. The entry's own terms also make this un-groomable today even if
  it had: epic placement for the producer twins (G-series vs a new epic) is explicitly a user
  call at that groom, so promoting now would be inventing the answer.

- **`Idea-49`** · 2026-08-04 · `[question]` · **parked → user ruling: recreate the desktop container, or re-point the version fact** · prio? **Med** —
  venue divergence (J18): the DESKTOP `neo4jtest` reports server
  5.26.27, while `config/dev-environment.yaml` + runbook Appendix A say 2026.05.0 EE —
  and its `ddschema` was missing today despite G51 (provisioned 2026-08-03, desktop),
  i.e. the topology state postdating the wipe did not survive to today. Likely the
  desktop container predates/rolled back from the 2026-07-28 plugin-volume recreation.
  Ties into G50 (desktop rollback-copy question, open). Re-provisioned + fully reloaded
  today; decide whether to recreate the desktop container on the pinned image or re-point
  the config's version fact with a venue note. (desktop)
  KEPT-UPDATED 2026-08-04 (weekly groom) — **still the user's decision, and now confirmed
  DESKTOP-ONLY.** Verified at this groom from the laptop (J18 venue: laptop, `neo4jtest`,
  `drydocs` DB): this machine runs the pinned 2026.05.0 Enterprise with `ddschema` present
  and six user databases online, so the config's version fact matches reality here and the
  divergence is not a repo-wide drift. That narrows the choice rather than making it — the
  question is unchanged (recreate the desktop container on the pinned image, or re-point the
  config's version fact with a venue note), and it stays parked because either answer is a
  ruling, not a default. Worth noting for whoever rules it: nothing currently DETECTS this.
  `tests/unit/test_dev_environment.py` pins the provisioning command to the config file, but
  no check compares a RUNNING server's reported version against the pinned one, which is why
  the desktop drifted silently. If the ruling is "re-point with a venue note", that gap is
  the thing worth an item.

- **`Idea-44`** · 2026-07-31 · `[source]` · **parked → company network access** · prio? **Med** —
  **fcdo-frameworks live Confluence scrape (company-side).**
  Registered on-demand in `config/doc-source-registry.yaml` (connector: confluence, T4,
  ddcontext); page-ID target list in `internal/fcdo-reference/README.md`. Priority
  recapture: Descriptive Metadata, Data Quality, Data Contracts (DPROD), Taxonomy
  Framework property tables — the capture holes that block crosswalk sign-off. Needs the
  docmeta confluence connector (or an interim company-side capture) — company network only.

- **`Idea-41`** · 2026-07-28 · `[question]` · **merged → J34 (2026-08-07 pm — the overlay grammar must be able to express a producer-LOCAL file); the disposition ruling itself stays the user's** · prio? **Med** —
  **`config/dev-environment.yaml` under a `canonical-producer` row —
  decide the disposition producer-side too, not just company-side.** Step 48 raises this for the
  consumer, but the asymmetry is ours: `config/**` is `canonical-producer`, and U7 has just made
  that file *producer-local infrastructure* (sibling repo path, expected instrument commit, on
  top of the pre-existing container name + host ports). A port applies it wholesale, and the L16
  runbook's Appendix A is a **render** of it — so a producer value propagates into consumer
  documentation, which is exactly the drift Appendix A was restated to prevent. Options: a
  per-entry row (which keys? the file has no id-keyed grain — probably section-level: `neo4j:`
  and `depgraph:` are environment-specific, `services:` ports arguably shared), a
  canonical-company row, or split the file into a portable contract + a local overlay. The last
  is the cleanest and the most work. Left deliberately un-made by the 2026-07-28 session, per
  J16's own rule that a disposition is a decision, not a default. ~~Fork merge~~ — **RESOLVED
  2026-07-28**: both branches merged into depgraph `main` (`5006567`) and DELETED, local and
  remote; `main` now carries every capability (probe reports `multi_root` AND `tree` true for
  the first time, `-Tree` works). Semantic merge details in DryDocs `8a82e3b` and the depgraph
  merge commit; the `add_rel` signature/shape collision and three regions git auto-merged that
  should have conflicted are the parts worth re-reading if that code is touched again.

- **`Idea-37`** · 2026-07-25 · `[idea]` · **parked → the SME convenes the supplement-shape gate** · prio? **Low** —
  **Supplement shape C — registration-vs-instance-seed re-slice** (the
  parked sibling of shape A, now groomed as **G29**). Re-sliced so that registering an
  ontology term and seeding an instance of it are separate operations rather than two halves
  of one supplement file. Explicitly **gate-worthy, not a refactor** — it changes what a
  supplement MEANS, so it routes through the HITL gate rather than a build item. Groom when
  the SME convenes it; G29 deliberately does not touch it.

- **`Idea-36`** · 2026-07-25 · `[source]` · **closed — cited, no item of its own (confirmed at the 2026-07-25 groom)** · prio? **Low** —
  **Databricks Unity Catalog researched — full notes at
  [`reference/research/databricks-unity-catalog.md`](../../reference/research/databricks-unity-catalog.md)
  (SME saw "Unity Catalog works so well in Databricks" and asked what it captures).** Public
  vendor build of the layer `docs/patterns/data-catalog/` models. Headline: its four semantic
  features land almost exactly on node types we already define — Domains → `CatalogDataDomain`,
  Glossary → `CatalogBusinessTerm`, governed tags → `CatalogTag` / `CatalogClassifier`, data
  classification → `config/classification.yaml`. Independent convergence, worth citing rather
  than re-deriving. **Three things to actually use:** (1) *lineage derived from Spark execution
  plans, never declared* — a clean public demonstration of the GROUNDED-over-SYNTHESIZED
  principle, and the argument for deriving Control-M dependencies from definitions rather than
  documentation; (2) *a controlled vocabulary needs an enforcement point or it rots* — their
  governed tags only work because a **tag policy** is attached, which is our classification-test
  rule generalized to any glossary we build; (3) their glossary ships "terms that link to each
  other," i.e. a concept scheme, which is external evidence for the acronym-catalog idea below.
  **Don't over-borrow:** "Genie Ontology" is a learned context layer, **not** an ontology in the
  PROV-O/ORG sense — cite as *catalog* precedent only, same tool-pattern-not-standard verdict as
  NeoCarta. It also has no orchestration model, so it answers a different question than we do.
  **Latent option (not proposed):** if the company runs Databricks, `system.access.table_lineage`
  and per-catalog `information_schema` are privilege-filtered and SQL-queryable — a legitimate
  future ingest source, necessarily Internal-classified. Groom: probably no backlog item of its
  own; fold the citations into the acronym-catalog item and any data-catalog ADR that revisits
  glossary/tag enforcement.
  KEPT-UPDATED 2026-07-25 groom — **the first citation has been consumed**: ADR 0010 §4.2
  (`app_id` + `id_authority`, groomed as **S3**) applies the governed-namespace lesson inward —
  the value of a governed namespace is that *the identifier itself carries its authority*, which
  is exactly what `id_authority: "SEAL"` encodes. Still parked: the *tag-policy-as-enforcement*
  and *glossary-as-concept-scheme* citations, which wait on the acronym-catalog line below and
  on a data-catalog ADR that neither exists nor is scheduled. No item of its own — confirmed.
  (Correction 2026-07-27: `id_authority` was WITHDRAWN at the identity gate's §B0 sign-off —
  SEAL stays the single issuing registry, so the property encoded a fact that cannot vary. The
  governed-namespace citation stands; its worked example moved to the source-field ledger shape
  instead.)

- **`Idea-35`** · 2026-07-25 · `[idea]` · **merged → G34 (content inside its scaffold); parked → the gate-log Q6 ruling** · prio? **Med** —
  **Acronym catalog scoped by domain — so agents and humans stop colliding
  on the same three letters (SME, chat).** Direct fallout of the Q6 reopen below: `Ais` cost
  real time because two readings are both plausible — "as-is" (the standard architecture
  modeling idiom) and "Application Integration Streaming" (an org platform family) — and
  nothing in the repo adjudicated between them. Today
  `config/taxonomy/software-registry.yaml#acronyms` is a one-key section with no scope
  dimension, so it can record *expansions* but not **collisions**, and collisions are the
  failure mode that actually bites. **Shape:** key by acronym, carry *many* senses, tag each
  sense with its domain scope — `area` (which part of the org/platform), `business-domain`,
  `technical-domain`, `industry` (what an outsider would assume it means) — plus, wherever a
  misreading is known to have happened, an explicit **does-NOT-mean** note. AIS is the worked
  example: industry/modeling sense "as-is", org sense "Application Integration Streaming", and
  the note that our `:AisTool` label meant neither. **Modeling hook:** this is a SKOS job
  (`prefLabel` / `altLabel` / `definition` / `scopeNote`, senses as concepts in a scheme) —
  SKOS is already registered in `reference/standards/README.md` (namespace + "concept
  reconciliation") but has **no fetched local copy** yet, unlike prov-o/w3c-org/dprod-ekgf/
  sosa-ssn; fetching it would be part of this. **Boundary caveat (decide at grooming):**
  industry acronyms are External and publishable, org-internal ones are not automatically —
  needs per-entry `classification` or an `internal/` split, same rule as any other source.
  **Consumers:** agents reading CLAUDE.md and gate prompts; L5/L6 SME review, where an
  unglossed acronym stalls a page; a whitepaper/website glossary. Groom **after** the Q6
  ruling — Q6 decides whether `#acronyms` survives at all, and this is the shape it would grow
  into if it does. (Note: "Q6" here is the **gate-log** question, not the backlog item Q6,
  which is the unrelated docmeta Port A.)
  KEPT-UPDATED 2026-07-25 groom — **independent corroboration from the pre-UI structure
  review**: its §4.2 arrives at the same home from a different direction, ruling that where
  "SEAL", "PAT" and "AIS" need to be *defined* rather than *encoded*, the carrier is a
  `CatalogBusinessTerm`-shaped glossary (`docs/patterns/data-catalog/enterprise-data-catalog-ontology.md`)
  — not a property, not a label. That is this line's shape, reached by the identity question
  instead of the collision question. Still parked on the same trigger (the gate-log Q6 ruling);
  what changed is that two threads now converge on it, so it is likelier to be worth building.
  KEPT-UPDATED 2026-07-27 groom: the landing zone now EXISTS as a backlog item — **G34**
  (raised at the identity-gate sign-off) reserves `CatalogBusinessTerm` + its three edges as
  `planned`, schema public / definitions internal, deliberately defining NO terms. When Q6 is
  ruled and this line grooms, it becomes content INSIDE G34's scaffold (senses, scopes,
  does-NOT-mean notes as SKOS), not a new home.

- **`Idea-34`** · 2026-07-25 · `[question]` · **open — SME rules** · prio? **Low** —
  **Q6 REOPENED: is the AIS acronym entry worth keeping at all?**
  (SME, chat). C12/Q6 ruled the expansion "Application Integration Streaming" survives as
  `config/taxonomy/software-registry.yaml#acronyms` — the durable "what did that name mean"
  home. The SME now reports the premise was wrong: they read `Ais` as **"as-is"**, never as
  an acronym, so the label was never a considered modeling choice on our side. The record
  corroborates — `761a201` (2026-07-09) introduced it as `:AiTool` (**no "s"**), attributed
  to in-chat direction and flagged "not yet defined in the ontology"; it stayed spelled two
  ways for twelve days across backlog/IDEAS/port-archive; the 2026-07-21 "correction" to
  `AisTool` matched the C11 screenshot rather than decoding it; the expansion landed only at
  Q6 that afternoon. **Counterweight (don't skip it):** their docs portal root
  `/docs/ais/{orchestration,etl,file-transfer}/` is independent corroboration that AIS is a
  real org term — two separate questions (is the acronym real? = yes / was `:AisTool` a
  considered choice? = no), and Q6 answered the first as if it settled the second.
  **Options:** (a) drop `#acronyms` entirely — `config/gate-log.md` already carries the
  expansion verbatim, append-only, so nothing is lost and a one-key config section created
  to hold a dead string goes away; (b) keep it but rewrite as a **disambiguation** —
  "does NOT mean 'as-is'" is the protective sentence, not the expansion, since as-is/to-be
  is a standard modeling idiom and that misreading imports a false meaning (and "Streaming"
  was already ruled a misnomer at Q6). Producer-side recommendation: (b), worded as
  disambiguation. **Hold DISCHARGED 2026-07-27:** the hold was that
  `docs/port-T12-ais-excision-company-prompt.md` step 2b deferred the acronym rather than
  sweeping it, so no company session could harden a ruling still under review. T12 has since
  ruled (SUPERSEDE, 2026-07-21) and the excision is applied company-side, so that prompt is
  spent and was retired from the tree — the acronym question is now free-standing and no
  longer gated by a pending session. Still open, still the SME's: groom when they rule — a
  Q6 amendment entry in `gate-log.md`, not a new gate.

- **`Idea-33`** · 2026-07-24 · `[bug]` · **open — needs the user to point at the exact spot** · prio? **Low** —
  **Unlocated user-reported typo: "apply-catalog … at the bottom says
  apply ontology" (chat).** Searched cli.py docstrings/messages, runbook .md/.html both revs,
  run-drydocs skill, RELATIONSHIP_GUIDE, repo-README, feedback html, gate docs — no such
  string exists. Best guess: startup-refresh runbook step 3 says "the three domain
  supplements" and Appendix B omits `apply-registry-supplement` while running
  `load-software-registry` — a genuine Rev 3 gap that should ride the L5/L6 SME feedback
  loop (doc is mid-review; do not hot-edit). Re-check with the user for the exact spot.
  KEPT-UPDATED 2026-07-25 groom: **G29** (the `apply-supplements` consolidation) rewrites the
  exact verb set Appendix B lists, so its acceptance carries a rider to fold this check into
  the runbook update — which resolves the best-guess half without hot-editing a doc that is
  mid-SME-review. The *unlocated* half still needs the user to point at the exact spot.
  KEPT-UPDATED 2026-07-26 (G29 done): the rider was executed and turned up a NEW, closer
  candidate — not in the runbook at all, but in `.claude/skills/run-drydocs/SKILL.md`, whose
  chain block annotated `apply-catalog-supplement` with `# Catalog **ontology**` (and listed
  catalog BEFORE seal, which is the wrong order). "apply-catalog … says … ontology" is a
  fair description of that line. Both are now fixed — the block is one `apply-supplements`
  call and the order is enforced in code. Offered as the likely origin, NOT declared closed:
  if the user meant somewhere else, the report is still open. The runbook itself stays
  untouched and its three owed edits are the separate 2026-07-26 [doc] entry above.

- **`Idea-32`** · 2026-07-23 · `[idea]` · **open — user/SME ruling: which scope (the controlm_jobs.sql direct pull vs the remediation staging reads); re-checked at the 2026-08-07 pm groom** · prio? **Med** —
  **Oracle connection for the lineage/remediation path (user note,
  chat pm).** The lineage jobs step still stages a CSV by hand through a JDBC client;
  the Oracle connection is planned — and the user's note ties it to the REMEDIATION
  context ("switch to the remediation since this last update was related"). Candidate
  shape: a direct pull of the `controlm_jobs.sql` projection (the same file
  `ingest-controlm --use-oracle` runs — runbook Rev 2 records the equivalence) plus
  the remediation-side staging reads (STG_APP_FACT-family fact tables per the
  company-side greenfield docs). Clarify scope with the SME before building.

- **`Idea-31`** · 2026-07-23 · `[source]` · **parked → the remediation M2 generalization opens** · prio? **Med** —
  **Company-side greenfield remediation standards not yet
  producer-modeled.** Two docs live in the company `drydocs_remediation` path (seen in
  review 2026-07-23): (1) the Control-M file-name component standard — FileName
  decomposed into FilePrefix / FileBusinessDate / FileSequence / FileExtension /
  FileCompression / FileSuffix + the FilePattern FileWatcher glob, DistributionRole
  derived from extension, a `CM_JOB_FILE_NAME_STANDARD` Oracle column standard, and
  dcat:Distribution ontology mappings; (2) the cmd-job ontology variable mapping
  (`%%ETL_PLATFORM`, `%%LAUNCHER_SCRIPT_PATH`, `%%ETL_ARTIFACT_URI`… →
  STG_APP_FACT fact_type → :Script nodes / INVOKES / USES_ARTIFACT). Producer-side
  `drydocs_remediation` models FileWatcher (`job_type`, `watch_template`, resolved-watch
  equivalence) and job variables (ordered defs, scope chain, canonical rename,
  dot-smuggling detect, corroborate) GENERICALLY — but has no filename-component
  standard and `transform.py` still notes the canonical variable map is "a company-side
  ratified value". Candidate: bring both docs in as the ratified maps when the
  remediation M2 generalization opens (FR-REM-5's schedule/command/conditions slice).

- **`Idea-30a`** · 2026-07-22 · `[idea]` · **parked → cm_avg_run + calendar projection land** · prio? **Med** —
  **PDN trigger design: milestone/SLA grain + graph-computed slack,
  not per-job failure mail (SME, chat pm).** Current state: dev teams default ON/DO-MAIL
  + SHOUT to L2-on-failure → hundreds of ignored mails daily (alert fatigue — the
  motivating stat for the notification model). SME ruling direction: a failure must NOT
  trigger a PDN (potential delay notification) by itself; the trigger belongs at the END
  of the work stream with remaining recovery time calculated. Options mapped: (1)
  vendor-native = Control-M SLA Management / BIM job type at stream end — deadline-aware,
  projects completion from averages, alerts only on projected breach [MODEL KNOWLEDGE,
  not in corpus; licensed add-on — add "is BIM installed?" to the OQ-1-style company
  probe list]; (2) no-license fallback = terminal Dummy milestone job + time-based SHOUT
  WHEN-lateness variants instead of ON-NOTOK [SHOUT corpus-grounded via ctmdefine; the
  WHEN variants need verification]; (3) Confirm attribute = manual-approval GATE
  (corpus-grounded), not a notifier — usable as a HITL pause at recovery-decision
  points, wrong tool at stream end; (4) fatigue fix independent of all: demote
  failure-mail to MAXRERUN-exhausted only. DryDocs' role: the TRUE trigger condition is
  deadline − (now + remaining critical-path runtime) < 0 — the CPM-not-path-sum ruling
  from the cm_avg_run gate + calendar-projection plan; graph decides, milestone job
  delivers, DL from the email-dl-contact-point NOTIFIES mapping receives. Feeds: the DL
  gate B2 grain question (stream/milestone grain confirms folder-preference), the
  runbook module ETA logic, and the company-side probe list.

- **`Idea-30b`** · 2026-07-23 · `[idea]` · **parked → cm_avg_run + calendar projection land** · prio? **Med** —
  **Deadline-calibration audit — the SAME slack computation that gates a PDN also tells you
  whether a deadline is honest.** *(Split from `Idea-30a` 2026-08-05: 30a designs the trigger,
  30b audits the one that already exists — different deliverables, same feed.)*
  KEPT-UPDATED 2026-07-23 (SME, chat): the BIM install probe is ANSWERED — one
  production SLA/BIM job exists (SEAL 90489) — but it fires near-DAILY and is ignored:
  mechanism right, calibration wrong. Cause candidates (distinguishable): (1) deadline
  tighter than the stream's actual completion distribution [most common]; (2) stale/
  unrepresentative averages after the chain changed shape; (3) alert scope includes
  per-job failures, re-inheriting the noise it was meant to replace; (4) stream is
  genuinely chronically at-risk but the alert carries no slack/recovery content, so
  it's untriageable. DryDocs diagnostic play (once cm_avg_run + calendar projection
  land): take the 90489 BIM service's job membership, compute observed critical-path
  completion distribution, compare to the configured deadline → move deadline /
  refresh scope / re-engineer. Same slack computation that gates a PDN also VALIDATES
  whether a deadline is honest — deadline-calibration audit = a runbook/notification
  module feature, and the worked example for it. Principle for the notification model
  (gate-worthy): an alert channel earns attention only with a low base rate AND
  actionable content (remaining slack + recovery action) — any mechanism without
  calibrated thresholds degrades to ignored noise.

- **`Idea-29`** · 2026-07-22 · `[idea]` · **parked → gate email-dl-contact-point signs** · prio? **Med** —
  *(KEPT-UPDATED 2026-07-26: distinct from **Q10**, the email BODY as a
  document corpus. This entry is about DL MEMBERSHIP as an ontology mapping — the two touch
  the same source and must not be merged.)* **Email DLs need an ontology mapping (user, chat pm).** DL = the
  contact/notification channel for an app/team; only configured in Outlook (no feed,
  can't fix), witnessed in runbooks, extractable from emails; membership/usage are
  context-graph (layer 4) material. DRAFTED STRAIGHT TO GATE same session: gate prompt
  `config/gate-prompts/email-dl-contact-point.yaml` (class options vcard:Group vs
  prov:Agent; HAS_CONTACT_POINT dcat:contactPoint edge; store-as-source per the O24
  pattern; extraction-proposes-steward-disposes; layer-4 membership boundary) + map
  entry `dl-contact-point` (proposed). Grooming disposition: tracked at the gate —
  build items groomed on sign-off; nothing further parked here.
  AMENDED same day (SME follow-up, chat): the downstream-notification AUTHORING
  landscape added as gate section C — greenfield intent was the job Description
  field; better candidate = escalation DB special-instructions VARCHAR2(4000) in
  psgmgr (EJOBNAME/ECOMPONENT joins, support-editable = fixable source →
  override-until-fixed, not store-as-source, for the NOTIFIES leg); de facto truth =
  runbooks / Jira sign-offs / email threads (brownfield bootstrap, rejected as end
  state). C2 keyed convention must SHARE the description-metadata plan's template
  phase (two 4000-char conventions must not fork).

- **`Idea-28`** · 2026-07-22 · `[source]` · **open — SME data entry, not a backlog item** · prio? **High** —
  **Tier-1/tier-2 app-code rows: the SME still owes the enumeration.**
  (Re-inboxed slim 2026-08-04 from the groomed defined-mapping mega-entry — everything else
  in it was resolved by the K7 sign-off 2026-08-03 and the K9 build; see the audit trail.)
  Declared tier-1 examples so far: ARA=70002 (CMH Advice R&A), SRV=70003 (HL Servicing R&A).
  Tier-2 platform codes (e.g. DPL) map to MANY AreaProducts and the enumeration is OPEN.
  The landing zone now EXISTS: rows in `config/overrides/app-code-mappings.csv`, authored
  either directly or via the K11 steward screen once built — this is DATA ENTRY awaiting the
  SME, not a backlog item. Reminder riding with it: AreaProduct has ZERO rows in the sample
  taxonomy (lob-product-team.yaml OQ `area-product-missing`) — tier 2 makes that layer
  load-bearing, so the two OQs converge when the SME supplies the list.

- **`Idea-27`** · 2026-07-22 · `[idea]` · **parked → an env-toggle item exists to attach to** · prio? **Low** —
  **Env toggle = one canonical node identity, never per-env node
  identities.** When the header env toggle [Prod|UAT|Dev] gets built, it must re-scope
  DATA under one canonical node, not split identities (`job-dev`/`job-prod`
  anti-pattern). (Backstage assessment T8, UI-WIP/backstage-catalog-assessment.md §3;
  design constraint for the shell — attach to the env-toggle item when one exists.)
  TRIGGER RE-CHECKED 2026-08-12 (groom) — **NOT fired, and the check is worth recording because
  the toggle superficially looks built.** `O2` (done) shipped a **cosmetic** Prod|UAT|Dev toggle
  in the console shell; it re-scopes nothing, so there is still no item that would decide node
  identity, which is the only thing this entry constrains. Attaching the constraint to O2 now
  would file it against a done item where no one implementing the real re-scope will read it.

- **`Idea-25`** · 2026-07-22 · `[idea]` · **parked → a producer extractor starts consuming a temporal field** · prio? **Low** —
  **Control-M compact-timestamp normalization (mechanism, from the
  company XML-loader's second timestamp bug).** Control-M XML exports carry compact
  timestamps `yyyyMMddHHmmss` + literal `UTC` suffix (invented example: `20250101093000UTC`);
  fed raw into Cypher `datetime()` they throw `CypherSyntaxError` — not ISO 8601, and
  `UTC` is not a valid zone designator (`Z`/`+00:00`). Fix mechanism when the XML loader
  back-flows (and for any future producer temporal field): (1) normalize in PYTHON at the
  row-model layer (the C3 "Python owns normalization" precedent) — one canonical
  `parse_controlm_timestamp()` pydantic validator emitting tz-aware `datetime`, driver
  converts natively, `datetime()` string-parsing never appears in Cypher; (2) two bugs in
  the same family = scattered parsing, consolidate + unit-test the compact-UTC, date-only,
  and empty forms; (3) unparseable value → row to `rows_rejected` + WARN (G16
  values-decide pattern), never a batch abort at `_flush`. **FIXED company-side same day
  (as-built mechanism, supersedes the proposal above for back-flow):** a `_ts()`
  normalizer in the XML extractor emits the ISO *string* the loaders' existing Cypher
  `datetime(replace(x, ' ', 'T'))` contract expects (one temporal contract shared with
  the Oracle path — better than forking to native datetimes); zone token `UTC`/`Z` → `Z`,
  numeric offsets kept; 8-digit date-only → midnight; empty/None → None so the null-guard
  drops the row (fixes the batch abort). Residual gaps flagged to the company agent:
  unknown non-compact forms pass through to `datetime()` (docstring claims None) and 14
  valid digits aren't validated as a real date (`strptime` beats `isdigit`+len) — carry
  both hardenings into the back-flowed version.
  KEPT-UPDATED 2026-07-31 (weekly groom) — **trigger CHECKED and NOT fired, but the
  landing site now has a name.** A producer-side XML seam DOES exist as of 2026-07-29
  (**G47**, `drydocs_lineage/extractors/controlm_xml.py`), which looked like the
  back-flow trigger — but the file consumes **no temporal fields at all**: its declared
  contract is folders, jobs, and ordered variables only, and a search of it for
  timestamp/datetime handling returns nothing. So there is still no producer surface
  where a compact `yyyyMMddHHmmssUTC` value could arrive, and nothing to normalize. Stays
  parked, with the trigger sharpened: this grooms when the XML seam (or any producer
  extractor) starts consuming a temporal field — at which point the normalizer belongs in
  the EXTRACTOR emitting the ISO string the loaders' existing
  `datetime(replace(x, ' ', 'T'))` Cypher contract expects (the as-built company `_ts()`
  shape, which deliberately shares one temporal contract with the Oracle path rather than
  forking to native datetimes), plus the two hardenings above.
  Trigger re-checked 2026-08-04 (Control-M inbox groom): `controlm_xml.py` still consumes
  no temporal fields — stays parked.
  Trigger re-checked 2026-08-12 (groom): still NOT fired, and this check covers new ground —
  the extractor was rewritten at **G66** (2026-08-11) to stage folder and job DESCRIPTIONS, so
  it is no longer the same file that was checked in August. A search of it for timestamp /
  datetime handling still returns nothing: the fields it consumes are folders, jobs, ordered
  variables and now descriptions. Stays parked on the unchanged trigger.

- **`Idea-22`** · 2026-07-21 · `[idea]` · **parked → the public site starts** · prio? **Low** —
  **Public marketing-site brand kit** captured in
  `UI-WIP/WEBSITE-IDEAS.MD` (3 logo directions incl. the core+orbit modernization, secondary
  palette, hero/feature/architecture landing structure). This is the PUBLIC SITE
  (website-and-backstory workstream, 'overnight ledger' editorial identity — site not
  started, domain unresolved), NOT the console — deliberately left out of the 2026-07-21
  Epic O extension groom. Groom when the public site starts; the icon/logo direction
  should stay consistent with the O22 console glyph set.

- **`Idea-20`** · 2026-07-21 · `[source]` · **groomed → G60 (2026-08-07 pm) — clause (c) ONLY; clauses (a) and (d) re-read 2026-08-12 as PARKED, not open: (a) parked → a real CMD_LINE sample containing the `ingestion-launcher` jar, (d) parked → layer-4 context-graph work starts** · prio? **Med** —
  **DPL ingestion leg + AWS zone model traced** (company ingestion
  template; mechanism-only — values stay company-side). Upstream of the launcher spine:
  FM drop of a `.dat` + `.tok` landing pair → Control-M file-watcher condition grammar
  (`TOK-IN-COND…` / `FW_DAT#DAT-IN-COND…`, FW-OK-on-FAIL) → a **separate
  `ingestion-launcher` jar** publishes to S3 RAW via HTTP-PUT publish API (dataset
  identity = GUID + version, zone-scoped publish role) → **each zone hop
  RAW→TRUSTED→REFINED is its own DPL pipeline** (own `--pipeline-id`) → PROVISIONING
  DB-load lands the consumption target (Provisioned ≠ an S3 prefix). One bucket with
  zone prefixes; per-zone Glue databases + tables (partition keys at onboarding,
  `--odate` = partition value). Legacy `dataset_flow.json` FILE→CONFORMED ≈ the
  RAW→TRUSTED hop. UPDATE same day (prod CMD_LINE samples): the ingestion TRIGGER jobs
  use the SAME dt-launcher.sh (`-i` mode) — that grammar merged into G15. Still open
  here: (a) the template's `ingestion-launcher*.jar` was NOT observed in any sampled
  CMD_LINE (placement jobs?) — classifier entry waits on a real sample; (b) ~~DataAsset
  zone/glue-table shapes for the MAC enrichment feed~~ RESOLVED at the G17 build
  (same day): candidate shape = `dpl_dataset` DataAsset keyed by dataset GUID
  alone, version/zone/name as PROPERTIES (glue db/table can join later as more
  properties); version-as-identity deferred to G22 clause f; (c) Pre/Post-execution command fields carry mv/backup file ops
  (parquet + .tok → backup) — a G14-shaped surface G14 doesn't read (it parses
  CMD_LINE only); (d) cross-job `%%\\JOB\VAR` runtime threading (run GUIDs, record
  counts passed between jobs) — context-graph flavored, definition-level no-op.
  RE-READ 2026-08-12 (groom) — **neither remaining clause is an open question; both are
  waits, and saying so is the whole edit.** Clause (a) cannot be groomed into an item
  because the item would have no input: a repo-wide search finds `ingestion-launcher`
  ONLY in this entry and in the backlog text quoting it — no sample, no classifier row, no
  fixture. It is parked on evidence arriving (a real `CMD_LINE` sample carrying that jar),
  and the classifier entry is a ten-minute edit the day one does. Clause (d) is parked on
  SCOPE, not evidence: cross-job runtime threading is layer-4 context-graph material by the
  CLAUDE.md §1 split, and layer 4 has no owner agent and no phase work started, so an item
  raised now would sit unstartable and distort `next_ready`. Marked so a future reader stops
  re-litigating two lines that are each waiting on something nameable.

- **`Idea-17`** · 2026-07-20 · `[chore]` · **open — NARROWED 2026-08-12: the REMOTE half is discharged (both branches are already gone from origin) and the stash is gone; only two this-machine-local relics remain, still the user's destructive call** · prio? **Low** —
  **Post-squash ref cleanup (user decision, destructive)**: origin still
  carries two pre-squash-history branches — `feat/mapping-store` (SUPERSEDED: the Initial-import
  squash absorbed its content and main then evolved past it; its only unique file was the
  regenerable web-console `.print.html`, since retired by L13) and
  `feature/provenance-audit-fields-plan` (status unreviewed). Local relics on the producer
  machine: branch `backup/ui-dark-local-3`, the stale stash noted at the 07-20 groom, and the
  new safety tag `archive/old-history-2026-07-20` (this machine's pre-squash history; the other
  machine has `archive/full-history`). Deleting the remote branches is the user's call.
  RE-CHECKED 2026-08-12 (groom, desktop) — **most of this entry has already been executed,
  and nobody recorded it.** `git ls-remote --heads origin` returns exactly two refs, `main`
  and `feat/external-vendor-scraper`: BOTH pre-squash-history branches (`feat/mapping-store`,
  `feature/provenance-audit-fields-plan`) are already gone from origin, so the destructive
  remote decision this entry was raised for no longer exists. `git stash list` is EMPTY, so
  the stale stash is gone too. What actually remains is two local relics on this desktop and
  nothing else: the branch `backup/ui-dark-local-3` and the safety tag
  `archive/old-history-2026-07-20`. Both are still the user's call — deleting the tag drops
  this machine's only pointer to pre-squash history (the other machine holds
  `archive/full-history`), which is precisely the kind of thing a groom must not decide.
  Related finding from the same check, filed separately because it is live rather than
  historical: `Idea-108`, four merged `worktree-agent-*` branches and two dirty worktrees.

- **`Idea-16`** · 2026-07-20 · `[chore]` · **open — USER MANUAL STEP** · prio? **Med** —
  **USER MANUAL STEP: add the SNYK_TOKEN repo secret** so the new CI
  snyk job (44523ab) runs for real — token from app.snyk.io (Account settings → API
  token) → repo Settings → Secrets and variables → Actions. Until then every scan step
  skips cleanly by design. After the first green scan: triage `snyk code` advisory
  findings and decide whether to gate it (the ruff-idiom follow-up).
  RE-VERIFIED 2026-08-12 (groom) — **the entry still stands exactly as written, and it is
  still the user's hand.** `.github/workflows/ci.yml` still carries the `snyk` job (the
  `snyk/actions/setup` step, `snyk test --all-projects --severity-threshold=high`, and the
  advisory `snyk code test`), and the file's own comment still names the missing repo secret
  as a USER MANUAL STEP. Nothing in the repo can discharge this: no agent can set a GitHub
  repo secret, so it neither grooms into an item nor closes itself. Checked because an open
  entry that has quietly become obsolete is worse than one that is merely waiting.

- **`Idea-15`** · 2026-07-20 · `[idea]` · **parked → ONE user decision (display-label scope); the placement blocker is DISCHARGED — epic `generic-naming` now exists** · prio? **Med** —
  **Replace SEAL/PAT naming with industry-standard, SaaS-configurable
  terminology** (user request; web research DONE same day →
  `knowledge/upgrade-plans/generic-terminology-research.md`). Candidates validated:
  SEAL → **Application Portfolio** holding **Business Application**s (ServiceNow
  CSDM/APM — our K4 node label independently confirmed); PAT → **Product Taxonomy** /
  **Product Portfolio** (product-operating-model literature; AreaProduct is the least
  standard term). Mechanism = the Salesforce "Rename Tabs and Labels" pattern: canonical
  concept ids stay generic and stable, tenant display/source names become config
  (source-registry `display_name` fields; O12/O13 console surfaces render them).
  PARKED pending user decisions recorded in the note's §Decision surface: (1) scope —
  display-label config only vs also renaming `seal_*` vocab ids/domains (ADR-scale, the
  ADR 0004 precedent); (2) placement — productization has NO epic/phase, so promoting
  this is a PLAN CHANGE (new epic proposal → user); (3) `SEALID` → generic identity
  property (gate discipline). Related: [[SaaS scaffold research line — the
  template-play/whitespace finding, 2026-07-17]].
  KEPT-UPDATED 2026-07-20 groom: **C10 landed same day** (ServiceNow CMDB/CSDM doc-set
  mined, 54ccf63) — the CSDM service/service-offering layer this line called its missing
  piece is now in reference/. The decision surface is fully fed; still PARKED on the three
  §Decision user calls above (scope / placement-as-plan-change / SEALID property).
  KEPT-UPDATED 2026-07-27 groom: **§Decision item 3 is RESOLVED** — the
  business-application-identity gate (SIGNED OFF 2026-07-27) ruled `SEALID` → generic
  `app_id` on the canonical node, with the per-source field-name ledger
  (`config/source-mappings/seal-extract.yaml`) carrying what each source CALLS it; build = S3.
  Decisions 1 (display-label scope) and 2 (placement/plan-change) remain the parked user calls.
  KEPT-UPDATED 2026-08-12 (groom): **§Decision item 2 is DISCHARGED — this entry now has ONE
  open question, not two.** Promoting it was blocked because "productization has NO epic/phase",
  so any promotion was a plan change only the user could make. That is no longer true: epic
  **`generic-naming`** was created 2026-08-11 on SME direction and **GN1 is DONE** — ADR 0012
  names loaders, commands and sources by the DATA rather than the tool, on exactly this
  entry's warrant ("company jargon entered a repo that was meant to be generic from the start —
  seal, pat, m1/m3 — this is the standalone-generalization goal, not cosmetics"). So the
  landing zone exists and the plan-change question is answered. What ADR 0012 does NOT cover is
  this entry's subject: the DISPLAY layer (tenant-configurable labels over stable concept ids,
  the Salesforce rename-tabs pattern) and the node-label/vocab-id question. Decision 1 — display
  labels only, or also renaming `seal_*` vocabulary ids and domains, which is ADR-scale — is the
  single remaining user call, and it is a genuine fork: one is config, the other rewrites the
  ontology's identifiers. ADR 0012 §(f) is the warning worth reading before ruling it: source
  registry ids are COMPANY-CANONICAL, so renaming `pat:*` is a cross-repo reconciliation minting
  retired-id entries, not an edit.

- **`Idea-14`** · 2026-07-19 · `[idea]` · **parked → depgraph work resumes** · prio? **Low** —
  **depgraph metric extensions (codeflow takeaways — ideas, not code)**:
  compute codeflow's three genuinely useful metrics ON TOP of our existing ast-accurate
  graph, in the depgraph sibling repo (stdlib, deterministic, rides the snapshot JSON,
  flows into Neo4j at Fork 3): (1) **blast radius** — reverse transitive reachability per
  file ("what breaks if this changes"; the same what-depends-on-it question DryDocs asks
  of batch jobs, turned inward); (2) **dead-file candidates** — zero inbound edges and not
  an entrypoint; (3) **coupling/health trend** — fan-in/fan-out per file plus a metric-delta
  summary across the committed snapshot series (codeflow's card-history pattern, free from
  our existing time series). Deep-dive verdict 2026-07-19: codeflow itself REJECTED as a
  ritual component (browser-only app, regex-heuristic edges vs our ast, Node-vm headless
  hack, no Neo4j path) — take the ideas only.

- **`Idea-13`** · 2026-07-18 · `[idea]` · **parked → a catalog/domain owner asks for it** · prio? **Low** —
  **ETL-tooling inventory as a DryDocs domain** (re-inboxed slim from the
  groomed mapping-store line): a gap no catalog covers — DataHub/OpenMetadata inventory data
  assets, not the tooling estate. DryDocs should own it. Context in the mapping-store plan §5
  (internal DataHub adoption).

- **`Idea-11`** · 2026-07-17 · `[idea]` · **closed — research; whitespace confirmed, no item** · prio? **Low** —
  **SaaS knowledge-graph scaffold research (chat)**: no drop-in template exists
  for what DryDocs is. Candidates assessed: Neo4j Labs `create-context-graph` (Apache-2.0 scaffolder,
  FastAPI+Next.js+Chakra — stack mismatch vs ReUI decision, auto-extract-by-default = anti-HITL, no
  lineage/batch-job domains → pattern quarry only: its "one domain YAML drives the whole generated
  app" validates our registry-driven module/QuerySpec design); OpenMetadata (real HITL prior art —
  draft→reviewer→approve glossary/governance workflows — but deliberately NO graph DB, would replace
  the Neo4j core, no Control-M connector); DataHub (Neo4j-backed graph layer architecturally closest,
  but Kafka+ES+MySQL+Neo4j footprint, approval flows largely Cloud-tier, no Control-M). Whitespace
  confirmed: Control-M/batch-orchestration knowledge graph + HITL-gated ontology is uncovered — keep
  building; future options = "publish to catalog" export target (OpenMetadata/DataHub ingestion APIs,
  fits QuerySpec export) and DryDocs-as-template play à la create-context-graph ("pick your
  orchestrator, get a scaffolded support graph") for the standalone-generalization goal.

- **`Idea-10`** · 2026-07-14 · `[source]` · **merged → K16, K17 (the FID half); the ALIAS tier re-read 2026-08-12 as PARKED → a company-side alias table (or a producer-side substitute) actually exists** · prio? **Med** —
  **K2 FID / ALIAS reconciliation tables are company-side unblocks.**
  The attribution loader's TierReconcilers seam ships empty for FID and ALIAS (facts stay
  unresolved, counted in coverage) — tier 2 needs a FID -> seal_id source and tier 4 an
  alias table before those tiers resolve anything. APP_NAME reconciles today from the
  loaded SEAL reference (exact normalized match; ambiguous names excluded).
  CANDIDATE SOURCE added 2026-07-16 (cmdline-lineage-review side finding): FID + SEAL
  are co-located in Control-M FOLDER VARIABLES (env-suffixed FID_D/Q/P alongside a SEAL
  value; the SEAL is also embedded in folder names) — a FID→seal_id pairing may be
  derivable from the already-ingested variables, not only from company tables.
  RE-READ 2026-08-12 (groom) — **the ALIAS half is a wait, not an open question, and the
  FID half has moved a long way since this was written.** Tier 4 resolves nothing until an
  alias table exists to reconcile against; no such source is registered, so there is no item
  to write and nothing for a groom to decide — parked on the source existing. The FID half
  is live and has narrowed twice this week: `K16` (census) and `K17` (the gate) own it, and
  the 2026-08-12 SME answers moved the join off the functional id entirely
  (`UPPER(HR_PHONE_EXP.EMP_LAST_NAME) = CM_DEF_VJOB.OWNER`, directory side normalized only),
  which is a stronger result than the "candidate source" note above anticipated.

- **`Idea-9`** · 2026-07-12 · `[idea]` · **parked → website work starts** · prio? **Low** —
  **dry-docs.com site visual language**: seed from the whitepaper's
  "overnight ledger" identity (greenbar/banner-page/mono-display; canonical source stays
  docs/whitepaper/drydocs-whitepaper.md). Parked until website work starts — the site is
  not started and the domain's availability is unresolved. (Re-inboxed slim at the
  2026-07-13 groom from the artifact-design-review line, sub-item 3.)

- **`Idea-7`** · 2026-07-11 · `[idea]` · **parked → the SME schedules the lineage gate** · prio? **Med** —
  **Lineage live-load gate session** (captured at the G9 close). The Fork-3
  writer is built and REFUSES by design: the four vocabulary entries (m3_invokes / m3_triggers /
  m3_reads_from / m3_writes_to) are `status: planned`, so `write_curated` raises
  GateBoundVocabularyError until the HITL gate flips them active. When the SME schedules that
  gate: review a `plan_curated` output + the lineage-review page for a real extract, confirm
  the vocabulary (and the writer's Script.path key + DataAsset URN mapping), flip statuses,
  first live curated write. HITL-dependent — groom into an item when the gate is scheduled.
  Refs: 0002-C §4/§7, drydocs_lineage/writer.py, tests/unit/test_lineage_writer.py (the gate
  test flips deliberately at activation).

- **`Idea-6`** · 2026-07-10 · `[idea]` · **parked → the remediation gates open (TDD §6/§7 is the tracking surface)** · prio? **Low** —
  **Remediation next slices — tracked in the TDD, not itemized here**
  (captured at the G3 close, same day). What remains after G3/0002-B closed: the Tier-2
  agentic lane (FR-REM-4 — gated on OQ-2 registry shape + OQ-4 agent runtime, both open
  HITL questions), XML I/O (gated on the vendor schema acquisition — company-side .dtd /
  exportdeftable, corpus stub has the fetch list), and the A3 ground-truth watched filename
  + B1 var.text rule (company-side; adjudicates the real M0 unit's equivalence verdict —
  the resolver stays untouched until then). Groom into items only when their gates open;
  `docs/design/drydocs-remediation-tdd.md` §6/§7 is the tracking surface.

- **`Idea-5`** · 2026-07-10 · `[idea]` · **parked → Phase C proper** · prio? **Low** —
  **Phase C packaging (deferred by ADR 0002-A-1 at the G2 relocate)**: the
  pieces deliberately NOT executed in Phase B — (a) make `drydocs-core` independently
  installable (packaging-only commit: per-package pyprojects + path deps, NO file moves),
  (b) the remainder's 4-way component split (load/review/plan/docgen as real packages) and
  load's final name. UPDATED at the G3 close (same day): G3 completed IN-MONOREPO, so
  trigger (a) expired unfired — no early promotion needed; the whole line now waits for
  Phase C proper. Refs: ADR 0002-A-1 §Consequences, PORT-MANIFEST header sequencing note.

- **`Idea-4`** · 2026-07-09 · `[idea]` · **parked → BMC EPD entitlement, or OQ-1 closes company-side** · prio? **Low** —
  **Control-M Workbench as the remediation greenfield test bed — PARKED**
  (user call, 2026-07-09). The Workbench Docker image (dev Control-M, plain `docker run`, no
  Kubernetes/Helm) would let fix packages be DEPLOYED + EXECUTED against a disposable env
  before the Jira handoff — stronger than the offline equivalence proof, still SoD-safe.
  Blocked here: image lives on distribution.bmc.com (not Docker Hub; pull attempt 401) and
  needs an EPD-entitled account + identity token — an entitlement/machine-boundary question,
  not a technical one. Ports 8443/7005 verified free on this box. Revisit when OQ-1 closes
  company-side or entitlement is resolved. Refs: `controlm-api-installation.md` (corpus,
  §Workbench + SYNTHESIZED notes), `drydocs-remediation-tdd.md` §HITL OQ-1. (Control-M for
  Kubernetes / Helm-chart offering deliberately SKIPPED — different product, agents-in-K8s,
  no current use case.)

- **`Idea-3`** · 2026-07-08 · `[doc]` · **parked → the BRD shape settles upstream** · prio? **Low** —
  **BRD outline (Epic L, deferred)** — the third canonical doc type after
  TDD (L1) and Runbook (L8). Parked, not promoted: the BRD is a work-in-progress upstream and
  the user flagged it as "definitely a later phase", so there is no stable outline to write an
  acceptance test against yet. When the BRD shape settles, promote as `docs/design/templates/
  brd.outline.yaml` (reuse the `drydocs.doc-outline.v1` schema + traceability spine) into Epic L.
  Seed from the corpus: `SDLC-Docs/BRD - Table of Contents.docx`, `business requirements document
  template 31.docx`, `Business Requirements Template - FULL CDI Version.docx`.

## Recently groomed (audit trail)

- **FILED 2026-08-18 (desktop, second pass — the whole consumed tail, per the user's “clear the rest”)** — **Promoted 0, inboxed 0, merged 0, parked 0. Twenty-two entries moved, seven deliberately left behind.** After the morning's seven-entry filing the inbox still held **79 entries, 29 of them already marked `groomed →` or `merged →`** — dispositioned work that a reader scanning for open items had to re-read and re-dismiss on every pass. This clears that tail. **Moved (22):** `Idea-113` (→ G93), `Idea-83` (→ J33), `Idea-81` (→ N10), `Idea-77` (→ O53), `Idea-75` (→ K20), `Idea-72` (→ L25), `Idea-71` (→ O52), `Idea-69` (→ K18), `Idea-68` (→ K18), `Idea-64` (→ D9), `Idea-63b` (→ K18), `Idea-62` (→ J32), `Idea-135` (→ K16+K17, filed as `Idea-59` and renumbered later the same day), `Idea-58` (→ U15), `Idea-56` (→ J35), `Idea-53` (→ S10), `Idea-46` (→ C22+C26), `Idea-45` (→ C26+C27), `Idea-39` (→ C26+C27), `Idea-38` (→ J13), `Idea-12` (→ the provenance-audit-fields plan, docs 06/06a), `Idea-2` (→ Q4+Q5+Q6). **THE SEVEN THAT STAY, and why — this is the half worth reading.** The ritual says *fully consumed → move; partially consumed → mark in place and say what stays open*, so a `groomed →` header is NOT by itself a licence to file. Each of these carries a live remainder in its own header: `Idea-93` (L19 took the design-doc half; **the E1 status question stays open — user call**), `Idea-60` (**C25 took the gate SESSION only**; the sub-application USES_SOFTWARE source and the two missing product rows are explicitly not in it), `Idea-57` (J35 took the SHA-citation half; **the company-side credential fix is the company's hand**), `Idea-41` (J34 took the overlay-grammar requirement; **the disposition ruling itself stays the user's**), `Idea-35` (G34 took the content; **the rest parks on the gate-log Q6 ruling**), `Idea-20` (**clause (c) ONLY** to G60 — (a) and (d) re-read 2026-08-12 as parked, not open), `Idea-10` (K16/K17 took the FID half; **the ALIAS tier parks until a company-side alias table exists**). Filing any of those seven would bury an open user decision under a heading nobody reads for open work — the precise failure the mark-in-place rule exists to prevent. **Four judgement calls made explicit so they can be reversed.** `Idea-69`'s body says “WHAT SURVIVES” and reads like residue; it is not — the survivor is the narrow code-level platform declaration, and that is exactly what K18 (done) was groomed to carry. `Idea-135` (`Idea-59` when filed) carries “six open questions [that] need the directory owner”; they ride K16 (blocked) and K17 (todo), which is tracking, not inbox work. `Idea-45` and `Idea-39` both contain the word *parked* about a DIFFERENT entry's trigger — the company catalog gate — and `Idea-39` states in its own header that nothing stays open as inbox work. `Idea-12` merged into a PLAN document rather than a backlog item, and `Idea-2` left P4–P7 plan-tracked; both are dispositioned elsewhere, which is consumption, not residue. **Result: the inbox drops 79 → 57 and now holds open work, parked work and closed-for-the-record only — no entry whose disposition is already complete.** Verified by census rather than assertion: 57 inbox + 79 trail = 136 entries, the same 136 as before the pass, with zero duplicated and zero lost.

- **`Idea-113`** · 2026-08-12 · `[idea]` · **groomed → G93 (2026-08-12)** · prio? **Med** —
  **Coverage counts belong in the Jira fix-package explanation.** User direction
  2026-08-12: the per-run counters the extractors already emit (`ExtractCoverage.summary()`
  with the new `prepost_*` source split, `XmlDefsCoverage`, the conformance finding counts
  by rule) are the model for what a remediation batch should LOG when it is done — the
  counts go into the Jira explanation of the fix package (the runbook-automation support→dev
  handoff), carried through the run-log contract (`drydocs_core/run_log.py`) rather than
  console output, so the explanation is generated from the same numbers the run recorded.

- **`Idea-83`** · 2026-08-07 · `[bug]` · **groomed → J33 (2026-08-07)** · prio? **Low** —
  **Three standing rich-ANSI test failures on this desktop, pre-existing (not
  G55).** `test_supplements.py::test_chain_applies_in_registry_order` +
  `::test_unknown_only_name_exits_2_without_touching_the_graph` and
  `test_bootstrap_guard.py::test_bootstrap_reports_the_declared_count_on_success`
  all assert plain substrings against CLI output that arrives with ANSI color
  codes interleaved on this machine (`\x1b[1;31m` inside the matched phrase) —
  fails under both `python -m pytest` and `poetry run pytest`, fails identically
  on a stashed clean tree, `NO_COLOR=1` does not help (rich force-colors the
  captured stream). Likely a rich/typer version or console-detection difference
  on this desktop. Fix direction: strip ANSI in the assertions or force
  `Console(force_terminal=False)` under pytest — do NOT loosen the messages.
  (Found during the G55 close, 2026-08-07.)

- **`Idea-81`** · 2026-08-07 · `[idea]` · **groomed → N10 (2026-08-07, the gate-prompt draft; schema change waits on the gate)** · prio? **Med** —
  **Split wiring readiness out of the registry `confirmed` flag.** The a14a8028
  fix session (company, 2026-08-06) surfaced a semantics drift: producer uses
  `confirmed` for SEMANTIC confirmation (gate-signed; the class that transfers per
  Q6), while the company additionally encodes PIPELINE-WIRING readiness in the same
  flag (`cm_hosts` stays `false` because their P3 host stage isn't wired, despite the
  transferable gate). Company suggestion, endorsed at the fix session's Q1-B ruling:
  a separate `wired`/`ready` field on registry entries rather than overloading
  `confirmed` — then a divergence like T15/P3 is expressible as
  `confirmed: true, wired: false` instead of a pinned-guard standing divergence.
  Registry schema change → gate territory; groom toward the config layer.
  (Source: company `gate-log.md` standing-divergence entry + PORT-REPORT-a14a8028
  fix close-out, ledgered in docs/port-prompt.md.)

- **`Idea-77`** · 2026-08-06 · `[chore]` · **groomed → O53 (2026-08-07, default remove)** · prio? **Low** —
  **`web/src/components/HeroArt.tsx` is an orphan — the code graph's first
  front-end finding.** The O42 TS import edges went live (226 edges, depgraph
  `a56d2fc`) and the very first orphan query returned exactly one component:
  nothing imports HeroArt and it imports nothing first-party. The repo's own
  comments corroborate — `OverviewRoute.tsx:16` says the radial hub was
  "DEMOTED to a small decorative mark", and only a css comment still cites the
  file. Decide: delete it (with the index.css hero block that styles it), or
  re-wire it in. Either way, remove-or-use — a knowingly dead component defeats
  the inventory drift guard's purpose. *(Found at the O42 close, desktop; the
  query is `MATCH (m:CodeModule) WHERE m.extension IN ['.ts','.tsx'] AND NOT
  (m)-[:IMPORTS]-() ...` — vite.config.ts is the other hit and is legitimately
  edge-less.)*

- **`Idea-75`** · 2026-08-06 · `[bug]` · **groomed → K20 (2026-08-07, the amendment-gate DRAFT — K5 stays signed until sign-off)** · prio? **High** —
  **`tech_partner` is scoped to a node class that has no rows and no loader, and
  the SME says it belongs one level up.** SME, in-chat 2026-08-06: *"in the catalog
  there is a role hierarchy ProductCatalog-Product with role 'Tech Partner'"* — i.e.
  Tech Partner attaches at the **Product** level. The signed K5 gate
  (product-cabinet-attribution, 2026-07-20) ruled the opposite: §B118 records
  *"tech_partner ALSO attaches ONLY to :AreaProduct"*, and
  `catalog_ontology_supplement.cypher:373-374` seeds it `scope = "AreaProduct"`.
  **The repo's own company role doc agrees with the SME, not with the gate.**
  `docs/Product/technology_roles_and_responsibilities.md` defines Tech Partner as
  *"accountable technology leader **for a product**"* and lists **Area Tech
  Partner** as a SEPARATE role (*"owns the technical strategy for the domain"*),
  noting a Tech Partner *"may also assume Area Tech Partner responsibilities based
  on product size"* — which is exactly the kind of overlap that makes two roles look
  like one. K5's stated basis for the AreaProduct scope was *"the rename history
  naming it the area-product role"*, so the likeliest reading is that the two roles
  were conflated at the gate.
  **Two consequences, both measurable now.** (1) `area_products: 0` in
  `config/taxonomy/lob-product-team.yaml` and `catalog_has_area_product` is still
  `status: planned` — so `tech_partner` is scoped exclusively to a node class with
  zero instances and no loader, making it **a signed concept nothing can write**.
  That is precisely the `technology_risk_controls` failure mode (G35 §A2) reproduced
  on the catalog side, and it went unnoticed for the same reason: nothing tests that
  a seeded concept is reachable. (2) If Tech Partner is product-level, then **Area
  Tech Partner has no concept at all** in a scheme K5 fixed at exactly 7 — the first
  worked example on this side of what a FIXED scheme costs.
  **Do NOT fix by editing the supplement.** K5 is signed; per CLAUDE.md a signed
  ruling is re-opened through a gate. Needs a K5-amendment gate on the G35 model
  (G35 amends the 2026-07-10 §B the same way). Note G35's scope fence explicitly
  declines to reopen K5, so this cannot be folded into that walk.
  *Adjacent but separate:* the SME also ruled 2026-08-06 that the SEAL-side
  `"tech partner" -> "CTO"` alias STAYS (G35 §A6). That is about a contact-extract
  NAME; this is about which catalog node the ProductRole attaches to. Both true at
  once — but if Tech Partner is product-level, K5's change_note (*"this area-product
  role was formerly named 'CTO' in SEAL; SEAL's CTO now denotes the product-level
  role"*) needs re-reading at the same gate, because its two halves may have been
  describing the same level.

- **`Idea-72`** · 2026-08-05 · `[doc]` · **groomed → L25 (2026-08-07, rider default per the step-83 precedent)** · prio? **Low** —
  **A SIGNED gate page cites line numbers that have since moved.** The
  business-application-identity gate's §D2 (signed 2026-07-27) names its four
  `attribution_id` sites as `seal_applications.cypher:124,147,170` and
  `seal_contacts.cypher:53`. They are now `152,175,198` and `55`. The FILES and
  the FACT are still right — only the line numbers drifted — but §D2's whole
  point was that the site count had been wrong once already, so it is the one
  clause where a reader is most likely to check the citation and conclude the
  page is stale. Found while drafting the G35 gate prompt, which cites the same
  four sites. Question this raises beyond the fix: gate pages are governed
  surfaces and a signed one is a historical record — is a line number ever
  correctable in place, or does a drifted citation get a rider (the step-83
  precedent) rather than an edit? Cheap either way; the RULE is the valuable part,
  because L19's doc-drift sweep will hit the same question at scale.

- **`Idea-71`** · 2026-08-05 · `[bug]` · **groomed → O52 (2026-08-07; the J26-class question rides the item's notes)** · prio? **Med** —
  **`ownership.attributions.v1` returns a column that is always null.** The
  QuerySpec ends `... e.sid AS holder_sid` (`drydocs_api/query_specs.py:451`),
  but `:Employee` is keyed and written as `employee_id` at every site
  (`seal_contacts.cypher:31`, `seal_applications.cypher:145,169,192`) and nothing
  in the repo ever sets `.sid`. So the Holder SID column of the K4 attribution
  review surface is empty for every row. Its sibling spec
  `mappings.seal-contact-roles.v1` gets it right (`e.employee_id AS holder_sid`,
  line 258), which is what makes this a typo rather than a design difference.
  One-word fix; the reason it is worth an entry is the CLASS — a QuerySpec that
  names a property no loader writes is green in every unit test, because the
  guards check spec shape and not whether the property exists in the schema. That
  is the same promise-vs-assertion family as J26. Found while reading the
  attribution surfaces for the G35 gate prompt; not fixed there because G35 is an
  `ontology`-layer item and this is `drydocs-api`.

- **`Idea-69`** · 2026-08-05 · `[bug]` · **groomed → K18** · prio? **High** —
  **CORRECTED SAME DAY — the claim below was WRONG in its headline and is kept
  only for the narrow residue.** I reported that "every code authored through the K11 steward screen
  is tier-1 by construction". It is not.
  [`AppCodeCascadePane.tsx:288`](../../web/src/routes/AppCodeCascadePane.tsx) has a three-value tier
  selector — `seal-born | platform | dual-coded` — and `tier === 'platform'` authors **per-folder**
  rows (`app_code + folder_id + app_id`), which the loader indexes into `by_folder` and resolves per
  folder. That IS K7 §B2's "resolves per folder", built and wired end to end. The screen handles
  platform codes correctly. WHAT SURVIVES, and it is much smaller: the **code-level platform
  DECLARATION** — the empty-app_id row whose only job is to mark a code so its *unresolved* folders
  surface as `platform-unresolved` instead of falling through to the K2 fuzzy fallback — cannot be
  authored through the store. Consequence is bounded to folders under a platform code that the
  steward has not yet resolved per-folder: they get a fuzzy match instead of surfacing to a human.
  Worth closing, not urgent, and NOT the silent fan-out I described. ALSO REVISED (user,
  2026-08-05): platform app codes DO carry a SEAL — the platform's own — so "declare by absence of
  app_id" was always the wrong encoding; an explicit row kind is the fix, and the store's
  app_id-required check is correct as it stands.
  ORIGINAL ENTRY, for the record: **K9/K11 cannot author a tier-2 platform declaration — the store
  requires the exact field the loader requires to be empty.** Found reviewing the K series (user request).
  [`drydocs_api/mappings.py:413`](../../drydocs_api/mappings.py) refuses a changeset entry unless
  BOTH `app_code` and `app_id` are present ("app_code and app_id are both required — authoring is per
  app code (K7 §B1)"), and the same requirement repeats in the second validator (~:541). But
  [`folder_attribution.py:216-224`](../../drydocs/loaders/folder_attribution.py) uses an **empty
  `app_id`** as the SOLE mechanism to mark a code as a declared platform code — a populated app_id is
  read as a tier-1 code-level attribution and fans out to every folder under the code. **Consequence:
  every code authored through the K11 steward screen is tier-1 BY CONSTRUCTION**, and a platform code
  can only be declared by hand-writing an authored row that bypasses the store. This is the same
  silent fan-out logged against the app-code CSV, reached by a second independent route — so the fix
  cannot be "sanitize the CSV". FIX SHAPE: the store needs an explicit platform-declaration entry kind
  (app_code + no target + rationale), not a relaxation of the app_id check — the check is right for
  tier-1 rows and dropping it would let a blank target through as an ordinary attribution. Severity:
  the loader is correct, the gate is correct, the WRITE PATH is the gap; nothing is mis-written today
  because no producer-side platform code has been authored yet.

- **`Idea-68`** · 2026-08-05 · `[question]` · **merged → K18** · prio? **Low** —
  **"tier" names three different things — but the VALUE SPACES do not
  collide, so this is naming hygiene, not the ambiguity I first claimed (corrected same day).** The
  K7 row-kind tier is a STRING enum (`seal-born | platform | dual-coded`, `AppCodeCascadePane.tsx`);
  the K2 match-precedence tier is an INT (1 SEAL … 5 manual); `drydocs_api/mappings.py` stamps the
  int form on SUPPORTED_SHAPE definitions. `folder_attribution.py` writes the STRING onto the
  BELONGS_TO_APPLICATION edge, so a `tier` edge property is not ambiguous in practice — I said a
  `tier=2` edge could mean "platform" or "matched by FID"; it cannot, because the edge carries the
  string. Still worth a rename (`row_kind` vs `match_tier`) for readers, and worth doing before
  either surfaces in a QuerySpec, but it is cosmetic rather than a correctness risk.

- **`Idea-64`** · 2026-08-05 · `[chore]` · **groomed → D9 (2026-08-07; the ordering decision routes through the gate)** · prio? **High** —
  **`refines:` in the standards frontmatter is a CHAIN, not a flag — and
  `config/precedence.yaml` cannot express two internal tiers.** SME framing: Vendor → Company/Platform
  team → Lower support group. Concretely: BMC baseline ← DAT SRE standard (platform team,
  framework-coded) ← HLT standard (support group, application-coded). Both internal levels sit at
  precedence tier 2 today, so where the two internal standards DIFFER — and they do, in folder
  grammar, in what position 6 means, and in whether the app code carries the SEAL — nothing records
  which wins. Also corrected a real defect in the publishable standard: "frequency at position 6 =
  legacy" is true only of the DAT standard; under HLT a frequency letter at position 6 is CURRENT.

- **`Idea-63b`** · 2026-08-05 · `[question]` · **merged → K18** · prio? **Med** —
  **The app-code CSV's `descr` column is a corroboration signal, never a validity
  test (user, 2026-08-05).**
  `descr` leads with the seal id on MOST rows but not all, so column 2 vs the head of column 3 is a
  CORROBORATION signal with a known-imperfect base rate — never a pass/fail check and never a
  derivation source. `seal_id` is the field; `descr` is prose about it. A majority-correct column is
  the dangerous kind: it survives spot-checks and fails silently in the tail. Use the comparison only
  to produce a REVIEW QUEUE of disagreeing rows (candidate stale renames / decommissioned SEALs /
  copy-paste), each ruled by a human — same disposition as the §G5 disagreement classes.

- **`Idea-62`** · 2026-08-05 · `[idea]` · **groomed → J32** · prio? **High** —
  **Generalize the registration/routing/attribution rule — three instances in two
  days.** (1) A FID is REGISTERED to the platform app while its jobs are ATTRIBUTED elsewhere
  (`fid-identity-and-scope` §G). (2) An AutoSys failure alert carries TWO SEAL ids as escalation
  ROUTING (`SEAL=<a>_<b>` in the incident payload) — ingested naively that manufactures a job
  belonging to two applications. (3) The Control-M escalation DB routes by SEAL for the same reason.
  Candidate standing rule for `docs/RELATIONSHIP_GUIDE.md` or a knowledge/standards note: **a SEAL id
  appearing in a field is not an attribution claim unless that field's job is to attribute** —
  ownership, routing, and attribution are three different facts that all serialize as a SEAL id, and
  the graph has exactly one place (the confirmed app-code mapping) where the third is authored.

- **`Idea-135`** · 2026-08-04 · `[source]` · **groomed → K16, K17** · prio? **High** — *(RENUMBERED 2026-08-18 from `Idea-59` at the allocator-band change: the company side holds a DIFFERENT `Idea-59` (snow_tom_responsibilities), this file is `union-append`, and a port would have merged both into one number. Producer's was the uncited side — no hit in backlog.yaml, config/gate-log.md, docs/ or any tracker row at the time of the grep — so per the G75/G76 precedent producer's moved. One citation appeared later the same day: `docs/port-prompt.md` RELAY-11, an outbound relay telling the company how to repair their lost `Idea-50..75` block. That is a live relay, not an append-only signed record, so it was amended in the same change (RELAY-11 RIDER 2) rather than pinning the id — the G75/G76 constraint is that a SIGN-OFF citation must not be falsified, and this is not one. Keeps its 2026-08-04 capture date: the id is identity, the date is chronology.)* —
  *(census then gate session; the §G registration-vs-attribution
  finding and the six directory-owner questions ride the gate page, not this entry)* —
  2026-08-04 — [source] **The FID directory is the K2 tier-2 unblock — it was never a side quest.**
  `TierReconcilers.fid` has been an empty dict since the K2 build ("no producer-side reconciliation
  source yet"), while the signed match policy orders SEAL > **FID** > APP_NAME > ALIAS. The firm's ID
  directory is that table, and it is ingestible (UI, export, audit columns, application assignment) —
  unlike the outlook-dl case. Gate `fid-identity-and-scope` + [doc 09](09-fid-identity-and-scope.md)
  drafted: `:AppUser` keyed on the directory **id** (not the name — a renameable key silently splits a
  node) with `fid_name` + an explicit crosswalk on the hot path, since every source we hold joins by
  NAME; `BELONGS_TO_APPLICATION {role:'service_account', as_of}` to `:BusinessApplication`; ownership
  is an **as-of assertion**, transfers are normal not drift, and **transfer detection requires
  snapshot diffing** — a single extract can never reveal one, so dated retained snapshots or the
  `as_of` stamp is decoration. Scope answered by MEASUREMENT not judgment: demand-driven pull list
  (run-as owners ∪ unresolved FID facts ∪ evidence rows), preceded by a one-application census that
  turns "about 200 accounts" into "N of ~200, and here is what the rest are". Retired accounts stay in
  scope (historical jobs reference them); contact columns defer to `email-dl-contact-point`.
  Six open questions need the directory owner — name reuse after retirement is the one that decides
  whether every historical join by name is ambiguous.

- **`Idea-58`** · 2026-08-05 · `[bug]` · **groomed → U15 (2026-08-07; the whole-meta-header pass stays a candidate in its notes)** · prio? **Med** —
  **`meta.depgraph.dirty` conflates "untracked files present" with "the
  instrument differs from its pin".** The 20260805 snapshot records `depgraph.commit:
  773fb1e, dirty: true` — but the sibling is at EXACTLY the pin, and the dirt is three
  untracked paths (`.claude/`, two screenshots), no modified tracked source. A reader of
  that header reasonably concludes the snapshot was produced by modified instrument code,
  which would make it unusable for comparison. Fix is small: compute the flag from tracked
  changes only (`git status --porcelain --untracked-files=no`), or split it into
  `dirty_tracked` / `untracked_present`. Third finding in the instrument-provenance class
  (see the two inboxed 2026-08-04), which is starting to argue for one grooming pass over
  the whole `meta` header rather than another point fix.

- **`Idea-56`** · 2026-08-05 · `[chore]` · **merged → J35 (2026-08-07, with Idea-76)** · prio? **High** —
  **The port ledger is being reconstructed after the fact, not rolled
  at the port.** Rolling it today found TWO unrecorded ports (`6713c142`, `5f79d145`) while
  the section still named `40c35724`; the `40c35724` entry itself admits the same thing
  happened to `f71967db`. Three in a row. Consequence: range, port commit, backup tag and
  acceptance numbers are simply unknown for both new entries and cannot be recovered
  retroactively. Worth a real fix rather than more diligence — either the company report
  lands in the producer repo as an artifact, or the roll becomes a step in the port prompt's
  own closing sequence.

- **`Idea-53`** · 2026-08-04 · `[bug]` · **groomed → S10 (BUILT 2026-08-05)** · prio? **High** —
  *(the missing loader guard is now an item and was BUILT the same
  day; the tracker-row half was not groomed — it was DONE in the same commit, T23's row now carries
  the firing as direct evidence. Nothing here stays open.)* —
  2026-08-04 — [bug] **T23 FIRED company-side, exactly as its own row predicted — the tracker
  status should stop saying "pending (producer belief)".** The company ran
  `drydocs load seal_applications` against a graph that took the S3 CODE but never the S3
  re-key, and got `Neo.ClientError.Schema.ConstraintValidationFailed: Node(97) already exists
  with label 'BusinessApplication'`. Mechanism confirmed against producer source: pre-S3 nodes
  carry `seal_id` and NO `app_id`; `MERGE (a:BusinessApplication {app_id: row.app_id})` cannot
  match them because a uniqueness constraint IGNORES NULLS, so it mints a second node, and the
  next line `SET a.seal_id = row.app_id` then collides with the original's `seal_id` (both
  properties are separately unique-constrained, constraints.cypher:43-44). T23's row already
  says "all 8 key-bearing sites cut over in ONE apply or the constraint's null-tolerance
  silently doubles canonical nodes" — this is that sentence happening. Fix relayed: backfill
  `app_id = seal_id` on pre-S3 nodes BEFORE re-running, after checking whether the partial run
  (batches commit per flush) already doubled any. Producer action: T23's status cell reads
  "pending (producer belief, as of 2026-08-03)" and there is now direct evidence — update it
  at the next port roll, and consider whether the loader should FAIL LOUDLY on a
  `:BusinessApplication` with a null app_id rather than silently creating its twin, which is
  the guard the null-tolerance argument implies but nothing implements.

- **`Idea-46`** · 2026-08-01 · `[source]` · **merged → C22 (bug half) + C26 (back-flow half)** · prio? **Med** —
  **Company catalog-loader review (screenshots, same day as C17) — three
  back-flow candidates and one confirmation.** CONFIRMS C17 §a from the other side: the company's
  `product_lines.cypher` takes `product_line_id` + `parent_lob_id` + `parent_sub_lob_id` and keys
  on ids throughout, i.e. the id-carrying extract the ruling assumed is not hypothetical — it is
  what they load. NEW producer-side gaps, none of which exist here: (a) `pat_app_links.cypher` —
  the product-scoped Product→BusinessApplication loader C9 §c said `catalog_has_application` was
  waiting for, complete with STUB GOVERNANCE worth copying (`is_stub: true`, `source: 'pat-stub'`,
  placeholder attrs filled ONLY while stub, cleared once the real SEAL load lands); (b)
  `pat_product_owners.cypher` — `:Product` ownership enrichment (`product_owner_*`,
  `tech_partner_*`, sids as join keys for a later employee-hierarchy load), MATCH-only so it never
  mints products; (c) `products.cypher` step-2a supplement fields (`description`, `alias`,
  `product_orientation`, `references[]`), each coalesced so a sparse refresh cannot blank an
  enrichment. Also a straight producer BUG the comparison exposed: our `product_lines.cypher` and
  `area_products.cypher` do `SET name = row.name` unconditionally, so a sparse refresh BLANKS the
  name — the company's `coalesce(row.name, p.name)` is the right idiom and we should adopt it
  (their `product_lines` has our bug, their `products` does not; the inconsistency is theirs,
  the bug is ours in both). Company-side findings recorded as tracker T20 in `docs/port-prompt.md`.
  KEPT-UPDATED 2026-08-02 (weekly groom) — **the bug half is groomed, the back-flow half stays
  parked.** The `SET name = row.name` finding went to **C22** together with the [bug] parent-join
  line (same three files, one sweep); the groom verified it and found the blanking SET in
  `products.cypher` too, so C22 covers three loaders rather than the two named here. What remains
  parked HERE are the three producer-side GAPS — `pat_app_links` with its stub governance,
  `pat_product_owners`, and the `products` step-2a supplement fields — because those are back-flow
  and ride the same trigger as the 2026-07-27 company-catalog line below: the COMPANY gate's own
  sign-off. Do not open a second back-flow item for them.
  **GROOMED 2026-08-05 → C26** *(the parked half only)*: those three gaps are now named in C26's
  notes as absorbed, so they ride C26/C27's trigger inside the backlog rather than in this file.
  Nothing about this entry stays open — the bug half went to C22 in the 2026-08-02 groom.

- **`Idea-45`** · 2026-08-01 · `[question]` · **groomed → C26, C27** · prio? **Med** —
  *(absorbed into the company-catalog pair exactly as this
  entry's own last line instructed — the Sub-LoB grain and the `:LOB`-vs-`:CatalogLOB` label
  ruling are C27's §(a) and §(b), settled in ONE pass; the invisible-flattening argument is
  recorded in C27's notes as the reason it is gate-worthy rather than shruggable.)* —
  2026-08-01 — [question] **We model no Sub-LoB, and the SME fact that closed C17 says it is a
  real grain with its own numeric id. CONFIRMED BUILT company-side the same day** — their
  `product_lines.cypher` carries `parent_sub_lob_id` and anchors the line under
  `MERGE (sl:SubLOB {sub_lob_id: …})` when it is populated, falling back to `:LOB {lob_id}`
  otherwise, both via `HAS_PRODUCT_LINE`. So this is no longer "should we model it" but "adopt
  which shape" — and the label ruling (`:LOB` vs our `:CatalogLOB`) has to be settled in the same
  pass, since their fallback branch and our `catalog_lobs.cypher` write DIFFERENT labels for the
  same thing. Original note follows. The catalog hierarchy runs
  `BusinessSegment → CatalogLOB → ProductLine → Product → AreaProduct`; the source runs
  `LoB → Sub-LoB → Product Line → …`, so our chain silently flattens one level. Corroborated
  three ways: the SME statement (2026-08-01), the FCDO capture's "5-level hierarchy … native
  IDs at each level", and the company's own catalog gate page which already introduces
  `:SubLOB` + `HAS_SUB_LOB` ("only CIB and AWM have them") and widens `HAS_PRODUCT_LINE` to
  `(:SubLOB|:LOB)`. NOT built at C17 on purpose — a new node label + relationship is an
  ontology decision, and this is the same divergence the parked 2026-07-27 company-catalog
  back-flow note already owns (its trigger is the COMPANY gate's sign-off). Worth noting the
  flattening is currently INVISIBLE rather than merely absent: `parent_lob_id` on a product
  line will carry whatever the extract puts there, so a sub-LoB id would land in a
  `:CatalogLOB`-keyed field and MERGE a phantom LOB. Fold into that back-flow item when its
  trigger fires; do not open a second one.

- **`Idea-39`** · 2026-07-27 · `[idea]` · **groomed → C26, C27** · prio? **Med** —
  *(the whole entry is now covered: C26 writes the divergence
  down and reserves the four shapes as `planned` — actionable NOW, no trigger; C27 is the
  adoption gate that still waits on the COMPANY gate's sign-off. The two sibling entries that
  said "fold into that back-flow item; do not open a second one" — the 2026-08-01 Sub-LoB line
  and the parked half of the 2026-08-02 catalog-comparison line — are absorbed into the same
  pair. Nothing here stays open as inbox work.)* —
  2026-07-27 — [idea] **Company catalog gate (`internal/org/catalog/`, page dated 2026-06-25) has
  drifted ahead of the producer catalog ontology — back-flow / divergence-ledger candidate.**
  Screenshot review of `_catalog_gate_page.html` ("SME Gate Prompt — PAT Catalog Loader", step 1
  of 3; sibling `_product_application_gate_page.html` likely steps 2–3): introduces `:SubLOB` +
  `HAS_SUB_LOB` (LOB→SubLOB, "only CIB and AWM have them"), widens HAS_PRODUCT_LINE to
  `(:SubLOB|:LOB)`, uses label `:LOB {lob_id, name}` vs our `:CatalogLOB {lob_id, code, name}`,
  expects map ids `sub-lob-org-unit` + `catalog-lob-reconciles-segment` (ours:
  `lob-has-product-line` / `lob-reconciles-to-segment`, confirmed 2026-06-21), and ingests a
  5-field `pat_lob_sublob_productline.csv` (164 rows; Sub-LoB Name column our
  `lob-product-team.yaml` capture lacks). None of it exists here, even as `status: planned`.
  Gate MECHANICS all match the gate_pages.py design (localStorage ticks, no-write-until-confirmed,
  `{confidence, authority, aliases}` on RECONCILES_TO, skos:closeMatch aliases, precedence winner
  `lob-product-team`) — content drifted, mechanism didn't. Page date 2026-06-25 PRE-DATES the G2
  Phase-B relocate (2026-07-10), so its `drydocs/schema/ontology.cypher` path was period-correct,
  not a bug — refresh it if the prompt is revised. Real page bug to fix before signoff:
  functional-org target "Corporate" is ambiguous vs our seeded `:BusinessSegment {code:"Corp",
  name:"Corporate"}` — written as a code it MERGEs a phantom segment. Useful real-data signal:
  CIB + AWM appear as SEPARATE LoBs with 1.0 exact matches → resolves the LOB002 AWMCIB (legacy,
  0.5) open question in `lob-product-team.yaml`. If the company gate signs off: mechanism-only
  back-port (vocab entries as `planned`, map entries, 5-field taxonomy capture, LOB-vs-CatalogLOB
  label ruling) or an explicit port-prompt divergence-ledger entry. ~~COORDINATE FIRST: a laptop
  session (unpushed as of 2026-07-27) is re-working BusinessApplication mapping — don't touch
  catalog/SEAL map entries until it lands.~~
  KEPT-UPDATED 2026-07-27 groom: the laptop session LANDED same day (business-application-identity
  gate SIGNED OFF `fc15191`; the build = S3, `seal_id` → `app_id` on the canonical node) — the
  coordinate-first constraint is lifted. New wrinkle for the eventual back-port: the comparison
  now also crosses the app_id rename (the company page pre-dates it), so the label ruling
  (LOB vs CatalogLOB) and the key ruling (app_id) should be settled in the same pass. Still
  parked on its original trigger: the COMPANY gate's own sign-off.

- **`Idea-38`** · 2026-07-27 · `[question]` · **merged → J13** · prio? **High** —
  **Internal platform vocabulary in the sample corpus — ruling
  needed.** Residual from the groomed J14/J15 publish-boundary pair: the samples still carry
  real-looking internal platform tokens (`HLDM`, `PRARAG`, `svc.hldm`, `/opt/scripts/hldm/`,
  `host-hldm-01`, datacenter codes) — a different value class from SEALIDs, deliberately left
  untouched by the 2026-07-27 sweep and not ruled on. Is platform vocabulary publishable
  mechanism (like the naming grammar) or a value class to synthesize? User/SME call; once
  ruled, J15's value-shape guard test can grow a rule for it.
  KEPT-UPDATED 2026-07-27 (J14 close): two more members of the same identifier class found at
  the build — (a) the escalation-table schema identifiers (`psgmgr` / `cm_escalation_db` /
  `EJOBNAME` / `ECOMPONENT`) generalized out of the two J14 files but still present in 6+
  tracked files (controlm-db skill, gate prompts, taxonomy-ontology map, remediation TDD);
  (b) `knowledge/standards/technology/data-center-naming-convention.md` carries real DC codes
  and a real app code — same class, same sibling directory, untouched by J14 by scope. The
  ruling should cover: platform tokens, DC codes, schema/table/column identifiers, and
  synthetic-sample product NAMES that echo real ones ("Home Lending Servicing" in
  lob-product-team.yaml, paired only with synthetic ids).
  KEPT-UPDATED 2026-08-12 (groom) — **ONE OF THE FOUR CLASSES IS NOW CLOSED, three remain.**
  Class (1), the platform tokens this entry led with, was RULED by the SME on 2026-08-11:
  `PRARAG`/`HLDM` are AUTHORED FIXTURE NAMES, not captured values, so no sweep is owed and the
  proposed one was stopped (`PRARAG` sits in ~36 files including the bundled sample corpus, the
  lineage fixtures and five tests that assert on it literally, so removing an authored name
  would have rewritten the corpus and broken the parser's own pins). The ruling is recorded
  where realness decisions live — beside the J15 realness table in
  `internal/standards/technology/folder-naming-convention.md` — because that table replaced the
  NUMERIC segments inside those folder names, and reading it alone makes the surviving tokens
  look like an oversight. J13's notes already carry the closure. Classes (2) DC codes,
  (3) schema/table/column identifiers and (4) the echoing product names are UNCHANGED and still
  user-gated; the ruling deliberately did not dispose of them, and the DC-codes file is the live
  one (it carries real DC codes AND a real app code, out of J14's scope by accident of scoping).

- **`Idea-12`** · 2026-07-18 · `[idea]` · **merged → the provenance-audit-fields plan (docs 06/06a), at its next touch** · prio? **Low** —
  JobRun.started_at/status indexes (GraphAcademy advisor residual) — fold
  into the provenance-audit-fields plan (docs 06/06a) at its next touch, not standalone.

- **`Idea-2`** · 2026-07-06 · `[idea]` · **groomed → Q4, Q5, Q6 (P1–P3); P4–P7 stay plan-tracked** · prio? **Med** —
  **`drydocs-docmeta` component plan written** — full plan in
  `knowledge/upgrade-plans/docmeta-component.md`: component boundary (new `docmeta`
  COMPONENT_GROUP, imports core only, CLI via entrypoint exemption), config
  `doc-source-registry.yaml` + test guard, `drydocs_docs` DB + composite delta, phases
  P0 (benchmark) → P7 (T4 connectors), Port A inventory (bkup scraper → producer:
  carry cleaner/tokenizer/manifest, adapt registry/confluence-interface, drop migrate),
  Port B git-readme §6 (clean-adds / Canonical-COMPANY connector wiring / company
  supplements: blocked vendor fetches, Graph-API creds, Enterprise multi-DB target).
  Heads-up bullet added to git-readme.md. Groom phases P1–P3 to backlog after the P0
  benchmark verdict (**landing zone since 2026-07-16: phase 14 / Epic Q** — created at the
  Essential-GraphRAG groom). **TRIGGER FIRED 2026-07-16 pm: the P0 WRITTEN verdict landed**
  (knowledge/upgrade-plans/docmeta-p0-verdict.md, Q3 — recommendation: BUILD) → **P1–P3 are
  now groomable into Epic Q at the next groom**; the docmeta ADR is the P1 gate output — **number correction 2026-07-16**:
  the plan reserved "ADR 0004" (2026-07-06) but 0004 was minted the next day for the
  software-registry terminology ADR (accepted 2026-07-07); the docmeta ADR takes the next
  free number at authoring (plan doc's 3 refs annotated same day). The four T1–T4 tier lines were folded
  INTO this sequenced plan (P0→P7) and moved to the audit trail (2026-07-09). P0's corpus
  load is already substantially executed: the bmc-docs lexical loader (Document→Chunk,
  llm-graph-builder pattern) shipped and gate `bmc-docs-lexical-load` was ACCEPTED 13/13,
  LOADED LIVE (commits 12423f4/24d6a4b) — the WRITTEN benchmark verdict (traversal vs
  manifest-routed markdown vs vector RAG) + the docmeta ADR still remain before P1–P3 promote.
  **GROOMED 2026-07-18: P1–P3 promoted → Q4 (gate + ADR) / Q5 (registry ledger) / Q6 (Port A;
  module drydocs-docmeta registered as working name — final at the Q4 gate).** P4–P7 stay
  plan-tracked until Q4–Q6 land. NEW RIDER (GraphAcademy advisor, 2026-07-17): when the docmeta
  loaders land, add existence constraints on `Document.trust_default` / `Chunk.tier_rule`
  (silent null = provenance undercount).

- **FILED 2026-08-18 (desktop — `Idea-114` + `Idea-112`, the 2026-08-12 pair whose lines never moved)** — **Promoted 0, inboxed 0, merged 0, parked 0: this run dispositions nothing.** Both entries were already groomed on 2026-08-12 and the trail already carries that run (**GROOM 2026-08-12, targeted — `Idea-112`, `Idea-113`, `Idea-114`**, below); what never happened is the second half of the ritual, the MOVE. They sat in the inbox marked `groomed →` for six days, which is exactly the state the “fully consumed → move to the audit trail” rule exists to prevent — a reader scanning the inbox for open work had to read and dismiss them each pass. Filed together at the user's grouping because they came out of ONE session (working through the G60 result) and split into work that still has to agree: `Idea-112` → **G92** (p2, `drydocs-lineage`, phase 6) resolves `%%` variables BEFORE the file-op parse so a variable path and its resolved twin stop planning two `DataAsset` nodes for one file; `Idea-114` → **G94** (p2, `drydocs-core`, phase 6, deps G84) the standard-selection decision tree **+ G95** (p3, `config`, dependency-free) the gate prompt for standard identity and its carrier. **All three items are still `todo`, so nothing here is retrospective** — the filing is bookkeeping, and the open work is in the backlog where it belongs. Guardrail restated because it survives the move: §7.5/G84 rule the DD digit a grammar VERSION that must never select a template or standard, so a standard id needs its own carrier and never the sentinel digit.

- **`Idea-114`** · 2026-08-12 · `[idea]` · **groomed → G94 (the selection decision tree, buildable now) + G95 (the gate prompt for standard identity + per-team carrier — the contract change goes to the SME first, 2026-08-12)** · prio? **Med** —
  **DD1 standard selection is a decision tree, and standards need identity.** User
  direction at the 2026-08-12 session: under the `DD1|` tag, a FileWatcher job validates
  against the FW standard; a CMD job selects by ETL engine FIRST (DPL, Ab Initio,
  Informatica — the launcher classification already names these), then falls back to a
  generic standard that carries SOME shared tokens (DevX key, the EMAIL_DL contacts) but
  not all. The standard itself then needs identity and storage: a config table (SQLite?)
  keyed by a standard id, so a validation profile can be stored BY TEAM, with a
  platform/product hierarchy later. Guardrail to carry into the groom: §7.5/G84 rule the
  DD digit a grammar VERSION that MUST NOT select a template or standard — selection rides
  TASKTYPE + JOB_ROLE + the launcher classification, so a standard id needs its OWN
  carrier (the config table keyed by team/engine, or a registered token), never the
  sentinel digit. Today the per-job-type sets live in code-as-data (`TOKEN_REGISTRY`, the
  parse contract, guarded by the registry-vs-standard agreement test) — externalizing
  them into a per-team registry is a contract change and gate-relevant. Relates: G77
  (THEME token inside the DD1 block), the etlprocess-kind-enum rider (engine vocabulary).

- **`Idea-112`** · 2026-08-12 · `[idea]` · **groomed → G92 (2026-08-12)** · prio? **Med** —
  **Resolve `%%` variables in PRECMD/POSTCMD (and CMD_LINE) before the G14 file-op
  parse.** The G60 feed stages operands verbatim, so candidates carry unresolved names
  (`%%R_PATH/...`, `%%$ODATE`) that cannot merge with their resolved twins. The one
  resolver (`drydocs_core/orchestration/controlm/resolver.py` — "no caller may
  re-implement substitution") already does everything needed: PRECMD/POSTCMD are
  themselves SETVAR definitions, so `resolve_layers()` over the folder→job scope chain
  returns each row's `resolved_value` in place — parse THAT instead of the raw value, keep
  raw verbatim beside it (the G46 derived-fact shape), and `{ODATE}`-class canonical
  tokens remain as expected symbolic residue in the operand. The SAME variables CSV
  carries both the shell text and its bindings (`var_scope` splits FOLDER from JOB in the
  aliased shape; the raw export's folder rows are the header row where JOB_NAME equals the
  folder name). Count resolution quality per the `ResolveCoverage` precedent
  (`drydocs/cmdline_staging.py`). Raised working through the G60 result with the user.

- **FILED 2026-08-18 (desktop — `Idea-79` + `Idea-76`, the port-mechanics pair; both items shipped)** — **Promoted 0, inboxed 0, merged 0, parked 0.** Neither entry had a trail record at all: they were dispositioned on 2026-08-07 in a session that filed no groom entry (the only 2026-08-07 entry below is the laptop's Q16-session gaps run, which covers different ids), so this filing is also the retro-record. Grouped because they are one subject seen from two ends — what the port CARRIES and what the port has REACHED. `Idea-79` → **J34** (p2, `docs`, phase 8, **done**): the `PORT-MANIFEST.yaml` company-row overlay seam, raised after a clobber audit quantified **89 company-only paths** falling through `default:` and out of their own J16 guard. `Idea-76` → **J35** (p2, `docs`, phase 8, **done**, merged with `Idea-56`): the port ledger stopping at step 101 / `a14a802` with ten commits behind it, which J35 turned from a catch-up into a structural roll. **Both done, so the entries are fully consumed with no residue** — the reason they move rather than getting marked in place.

- **`Idea-79`** · 2026-08-06 · `[idea]` · **groomed → J34 (2026-08-07)** · prio? **Med** —
  **`PORT-MANIFEST.yaml` needs a company-row overlay seam — ports keep clobbering
  company-only tracked-path rows.** PORT-REPORT-a14a8028's clobber audit found the take
  dropped the company's `default_ok` section — quantified at the 2026-08-06 root-cause
  run as **89 company-only paths** falling through `default:` (canonical-producer
  disposition means the producer file wins verbatim), so company-only tracked paths fell
  through their own J16 guard (`test_no_tracked_path_falls_through_silently`, the one
  conscious deferral in that report). The company session re-adds the rows by
  hand this time; the structural fix is a D2-registry-style overlay: producer manifest
  stays canonical, company rows live in a separate company-side include the guard unions,
  and a port can no longer delete them. Needs a small grammar decision (include file vs.
  marked section), then a manifest + guard change on both sides.

- **`Idea-76`** · 2026-08-06 · `[chore]` · **merged → J35 (2026-08-07, with Idea-56)** · prio? **Med** —
  **The port ledger stops at step 101 / `a14a802`, and ten commits have landed
  since — including the whole G22 gate session.** The internal port that started
  2026-08-06 classified the range ending at `a14a802`, so everything after it is
  outside what the company side has seen: `180f4ae` (the SEAL sample generator —
  already flagged as owed step 102), the five G22 gate commits, the desktop's two
  code-graph asset-skip rulings, and the `.ksh` → SWO binding in
  `code_snapshot.py`. Two of those are code changes, not just gate prose. Roll the
  ledger before the next port so the company side is classifying a range that ends
  somewhere deliberate. *(Noticed at the G22 session close, laptop.)*

- **FILED 2026-08-18 (desktop — `Idea-67` + `Idea-66` + `Idea-65`, the Control-M app-code cluster; all three items shipped)** — **Promoted 0, inboxed 0, merged 0, parked 0.** All three were dispositioned on 2026-08-05, before this trail's earliest entry, so they have never had a record here; this filing supplies it. Grouped because they are three readings of ONE identifier problem — a 3-character Control-M app code asked to carry more meaning than it can hold. **`Idea-66` → K18** (p1, `drydocs-load`, phase 9, **done**): the app-code CSV is tier-1-shaped, so a straight conversion would fan a PLATFORM code's own SEAL onto every consumer folder beneath it — silent, and it looks correct, because `AOC→110777` is a true statement about the platform and a false one about the folders. Unblocked the same day when the SME supplied the closed six-code platform list, turning a steward capture exercise into a name parse. **`Idea-67` → K19** (p2, `drydocs-load`, phase 9, **done**, deps K18): the same code is not DURABLE — a scarce 3-char namespace gets retired and reissued (`DDC` is the documented case), so a code→application mapping is an as-of assertion, not a fact, and a reused code can silently inherit its predecessor's mapping. **`Idea-65` → merged into C25** (p2, `ontology`, phase 2, **done**): the SUB-APPLICATION field is a standards-backed at-scale statement of app→platform — and the entry is worth keeping for its own CORRECTION, which the user made the same day: it was first overclaimed as a better USES_SOFTWARE source than the version email, and it answers no versioning question at all. PRODUCT and VERSION are two facts, not two sources for one. **All three items done; no residue, so all three move.**

- **`Idea-67`** · 2026-08-05 · `[question]` · **groomed → K19** · prio? **Med** —
  **A Control-M app code is NOT a durable identifier — the 3-char limit
  forces reuse (user, 2026-08-05).** Codes are a scarce namespace, so they get retired and reissued
  with a different meaning; `DDC` is the documented case (created for the PySpark conversion,
  repurposed, nothing PySpark now). CONSEQUENCE for the K9 store, which is about to be hand-keyed:
  a code→application mapping is an **as-of assertion**, not a fact — the same shape as the FID→SEAL
  registration ruled in `fid-identity-and-scope` §B1, and the third current-state-only identifier
  found this week. `authored_on` already gives the store an as_of; what nothing prevents is a REUSED
  code silently inheriting its predecessor's mapping, and folders authored under the old meaning
  keeping an attribution that is now wrong. Wants: effective dating on the mapping, or at minimum a
  reuse detection that surfaces "this code's mapping predates folders that appeared under it".

- **`Idea-66`** · 2026-08-05 · `[bug]` · **groomed → K18** · prio? **High** —
  **The app-code CSV is TIER-1-SHAPED, and loading it as authored rows would
  silently fan a platform code's own SEAL onto every consumer folder under it.** THE MECHANISM (built,
  [`folder_attribution.py:216-224`](../../drydocs/loaders/folder_attribution.py)): the ONLY way to
  declare a tier-2 platform code is an authored row with **`app_id` EMPTY** — a populated app_id is
  read as a code-level tier-1 attribution and fans out. `internal/orchestration/controlm-app-codes-with-seal.csv`
  (company-side) populates `seal_id` on every row, including the platform codes, so a straight
  CSV→authored-rows conversion can NEVER produce a platform declaration. Confirmed real by the user
  2026-08-05: `AOC` (registered to the CCB Cloud Data Processing Platform SEAL, the datalake seal for
  Ab Initio) and `DCL` (the DPL launcher spine, registered to a consumer app) are both shared platform
  codes whose folders serve many consuming applications. K7 ALREADY RULED THIS — tier 2, "e.g. the DPL
  launcher spine", folders SURFACE for steward completion, never auto-picked
  ([`k7-folder-mapping-decisions.md:14`](k7-folder-mapping-decisions.md)) — so the 1:1 graph-test does
  NOT red; the defect is upstream, at tier assignment. FIX SHAPE: an explicit platform-code list
  applied BEFORE conversion, dropping `seal_id` for those codes rather than carrying it. The failure is
  silent and looks correct — `AOC→110777` is a true statement about the PLATFORM, just not about the
  consumer folders it would be stamped on. The only in-file hint of platform-ness is the word
  "Platform" in `descr`, which is the untrustworthy column (below). **UNBLOCKED SAME DAY:** the SME
  supplied the DAT SRE standard's Framework → APPCODE table — the platform list is CLOSED AT SIX
  codes (values in `internal/standards/technology/folder-naming-convention.md`), and tier is
  MECHANICALLY DERIVABLE from the folder name: prefix positions 3–5 ∈ platform list → tier 2, else
  tier 1. So the fix is a six-row list plus a name parse, NOT a steward capture exercise — and the
  tier-2 resolving SEAL is a token inside the folder name, so per-folder resolution is derivable for
  the common case too. Mechanism written up in
  [`knowledge/standards/technology/folder-naming-convention.md`](../../knowledge/standards/technology/folder-naming-convention.md).

- **`Idea-65`** · 2026-08-05 · `[source]` · **merged → C25** · prio? **Med** —
  **The Control-M SUB-APPLICATION field declares WHICH PLATFORM an application
  runs on — a first-pass C1 source, NOT a replacement for the version email.** ~~a far better
  USES_SOFTWARE source than the adhoc version email~~ — **CORRECTED SAME DAY (user):** that
  overclaimed it on both axes. Under the HLT standard the framework does not vanish when the app code
  is application-tied; it moves to a sub-application `PR<Appcode>-<Platform App Code>`. **Documenting
  the platform IS the intent of the naming standard** — so the field is a faithful, standards-backed,
  at-scale statement of *app → platform*, and that is genuinely useful. What it is not:
  - **It answers no versioning question.** `ABI` says Ab Initio, never `v4-3-2-2`. The version email
    and this field are not two sources for one fact; they are two different facts (PRODUCT vs
    VERSION), and only the email carries the one the readiness review actually asked for. Treating
    this as "the better source" would have left the gate's whole subject unsourced.
  - **Mapping it at sub-application grain manufactures a super node.** An app has MANY
    sub-applications, all naming the same platform — fan every one into `:SoftwareProduct {abinitio}`
    and that single node collects an edge per sub-application per app across the estate, which is a
    traversal hazard, not just noise. If this is loaded, the edge is **one per (application, product),
    deduped at app grain**, with the sub-application rows as supporting evidence rather than as edges.
  Standing use: **fine for a first-pass C1 (container) diagram** — which apps sit on which ETL
  platform, at estate scale, for free. Anything finer waits for a real source.
  PREREQUISITE either way: two of the six framework codes have no
  `config/taxonomy/software-registry.yaml` product row — DPL (the standing gap `invocation_patterns`
  already records, now with a name and a framework table behind it) and Snowflake ETL. Register those
  products first. *[Corrected 2026-08-05 (user): AWS Snowflake is a TARGET DB platform (S3/Glue/
  Iceberg family), not an ETL product — the second row registers `snowflake` the data platform, not
  a "Snowflake ETL" tool. Recorded in C25's notes and both folder-naming twins.]*

- **GROOM 2026-08-18 (targeted — Idea-134 only, the mechanics the signed gate authorized; SME context supplied at dispatch)** — **Promoted 2: `Idea-134` → `N14` + `N15`** (both epic N / phase 11 / **p1** — SME-confirmed at dispatch, not proposed — agent `main`, sonnet, todo, `depends_on: [N12, N13, O24]`, all three done, so **both enter `next_ready` on arrival**). **Inboxed 0, merged 0, parked-as-question 0.** **TWO items rather than one because the gate's two authorized builds land in different modules:** N14 is a report/export surface (`drydocs-api`, the O24 report family) and N15 is loader-side detection (`drydocs-load`, which owns a run cadence — the MODULE_MAP placement test). They are independent; neither blocks the other. **N14 — the UNION REPORT:** one report class over BOTH domains (§A1's single `pending_source_correction` vocabulary — active `seal_contact_override` rows plus every registry dataset row still at `acquisition.mode: manual`), ordered by AGE with the age BASIS made explicit because it is asymmetric (override rows carry `authored_on`; a manual registry row carries no dated field today, so the build picks and documents one basis). The gate's fences are written into the ACCEPTANCE, not the notes: no deadline, SLA, alerting or per-row `review_by` (§C2 — per-row clocks were offered and declined); it never gates a load, blocks CI or fails a test (§C3); and per N12 clause (f) no column, wording or styling may present `manual` as a defect. The K7 §E2 exemption is ENFORCED rather than documented — a test asserts an `app_code_mapping` row can never appear (§D1), and the report reads each store's DECLARED pending-vs-permanent property (§D2) instead of hardcoding the one exemption. **N15 — AGREEMENT-CANDIDATE DETECTION:** `seal_contacts` + the O24 override store named as the first concrete surface; when a loaded SEAL holder equals the override's corrected holder the override becomes a retirement CANDIDATE. **Two hands made structural, not aspirational:** it rides the EXISTING draft mechanism (`add_draft` / the commit-by-replace override draft path), so an unattended run can only leave an open draft — a test asserts a detection run leaves every `seal_contact_override.status` untouched (§B2/§B3; auto-retire was offered at the gate and declined). Confirming archives the row dated with its agreement evidence, history kept (§B4) — which is what extends today's `('active','corrected-in-seal')` CHECK. **Nothing graph-side in either item (§A3):** pending-ness lives in config and stores only; a graph-side flag would be a new RELATIONSHIP_GUIDE proposal and its own gate. **No new gate is created and none is needed** — the lifecycle was SIGNED 12/12 the same day and these two implement it. Sonnet on both, recorded deliberately in N15's notes: it does change a store schema, but the gate already made that decision, so the schema-touch alone must not re-tier it to fable. Verified at the groom rather than recalled: the gate clause anchors come from `config/gate-log.md`, and the `v_source_corrections` view, the `app_code_mapping` DDL comment, the status CHECK and the thin `seal_contacts` loader were read out of the tree.

- **`Idea-134`** · 2026-08-18 · `[idea]` · **groomed → N14 + N15 (2026-08-18)** · prio **High** —
  **The pending-source-correction MECHANICS — the two builds the signed gate authorized
  but did not build.** Gate `pending-source-correction` SIGNED 12/12 (2026-08-18, N13).
  Ruled, now buildable: (1) the UNION REPORT — one report class listing every live
  placeholder across both domains (override rows awaiting source correction + manual
  acquisition rows awaiting automation), ordered by AGE, no deadline, never gating
  anything (§C1-§C3); (2) AGREEMENT-CANDIDATE DETECTION — the load that consumes a
  source carrying an overridden value surfaces override == source as a retirement
  CANDIDATE for steward confirmation (§B2, two hands; an unattended job may propose,
  never perform, §B3). Both flips keep history per §B4. The K7 §E2 permanent-by-nature
  domains are exempt and must not appear in the report (§D1); new stores declare
  pending-vs-permanent at creation (§D2).

- **GROOM 2026-08-18 (targeted — Idea-133 only, with SME context supplied in-session)** — **Promoted 2: `Idea-133` → `N12` + `N13`** (both epic N / module `config` / phase 11 / p2 / todo, dependency-free, so both enter `next_ready` on arrival). **Inboxed 0, merged 0, parked-as-question 0.** N12 is the BUILD: a first-class `acquisition:` block on every dataset row of `config/source-registry.yaml` (`mode: manual | automated`; manual names `format: csv | ascii | json` + a landing-zone-relative `drop_dir`, automated names `via: api | db` with the pull's coordinates by reference), declared in the JSON Schema and ENFORCED in `tests/unit/test_source_registry.py` — the schema is shape-only (S6, no `additionalProperties: false`), so a block added to the YAML alone would validate silently. **The SME's exploratory-phase framing is written into the ACCEPTANCE, not just the notes:** `mode: manual` is the EXPECTED FIRST STATE of every source (profiling → ontology → mapping → trial loads, with a .csv/.json file as the natural manual Neo4j loader), never a defect — no test or render may present it as a violation. Fences kept from the entry: no watcher/mover is built, no real path is committed, and the doc-corpus ledger is out of scope. **N13 is the SIBLING the SME's second half asked for:** the acquisition manual→automated flip and the O24 override→source-corrected flip are ONE lifecycle shape, and K9 §E2 deferred that flip to "the domains where permanence is temporary" with NO item owning it — so N13 drafts one gate prompt covering both (drafting decides nothing; G27/W1/U11/N10 precedent) and nothing changes until the gate signs. Raised as a sibling rather than folded into N12 as a clause on purpose: folding it would make a buildable config item undeliverable without an SME session. Coordination recorded, not invented: N10's proposed wired/ready flag and `acquisition.mode` are DIFFERENT axes that compose on the same row, and Idea-132's `source_label` enum question stays open in the inbox.

- **`Idea-133`** · 2026-08-18 · `[idea]` · **groomed → N12 + N13 (2026-08-18)** · prio? **Med** —
  **Give every registry source a declared ACQUISITION PATH: manual sources name their
  drop directory (CSV/ASCII, real path in the internal twin), automated sources name
  their API/db pull.** SME ask 2026-08-18. Today the acquisition mode is smeared across
  three half-fields that do not compose into an answer: `adapter` (csv/oracle/yaml/
  markdown/json — 8 sources carry `~`), `connector` (only the doc corpora use it), and
  `locator` (free-shape: `extract: ~`, `data_root:`, `mapping:` — each source invents
  its own key). Nothing states the split the SME names: is this source a MANUAL drop
  (someone exports a file into a directory) or AUTOMATED (an API call or a db pull the
  pipeline runs)?
  **THE SHAPE TO CONSIDER:** a first-class `acquisition:` block per dataset —
  `mode: manual | automated`; for manual, `format: csv | ascii` plus `drop_dir:` where
  the COMMITTED value is the landing-zone convention (`DRYDOCS_DATA_ROOT`-relative, the
  `controlm-xml/` precedent, resolver in `drydocs_core/data_root.py`) and the REAL
  internal path lives only in the internal twin (the `locator.extract: ~` discipline,
  unchanged); for automated, `via: api | db` plus the pull's coordinates by reference
  (the source's own dataset id already names the db object; the API case names the
  call surface, e.g. the G96 framework for Control-M).
  **WHY IT EARNS A FIELD RATHER THAN A CONVENTION:** Idea-115 already caught this class
  once — the rua copy path existed only as a derived expression, and the fix was to
  make both ends name each other. Idea-132 is the live driver: the ServiceNow extracts
  are moving manual→automated (hand-pulled CSV → SQL over the replica), and TODAY that
  transition has no field to flip — it shows up only as prose in `notes:`. A declared
  `acquisition.mode` makes "what is still hand-fed?" a query instead of an audit, gives
  the load-map/console an honest manual-vs-automated lens, and gives the
  `source_label` enum question (Idea-132's knock-on) the axis it is actually trying to
  encode — acquisition mode is a SOURCE fact and belongs on the registry row, not on
  the loader class.
  **FENCES:** schema change to `drydocs.source-registry.v2` rows + its JSON Schema +
  `test_source_registry.py`, so it is a groomable item, not a quick edit; no real paths
  ever committed (Scan D/J27 class); and it RECORDS mode per source — it does not build
  any mover/watcher for the drop directories.

- **GROOM 2026-08-17 (desktop, targeted — the UI / UI-WIP inbox entries only, per the run's focus: console work that does not touch what other sessions hold)** — the three entries the 2026-08-13 groom explicitly left for a console-epic run ("UI-view work and belong with the console epic") are that run's whole scope, and all three promoted. **Promoted 3: `Idea-116` → `O60`, `Idea-122` → `O61`, `Idea-123` → `O62`** (all p2 task, `drydocs-web`, phase 12, epic web-console, sonnet) — all three dependency-free, so all three enter `next_ready` on arrival. **Inboxed 0, merged 0, parked-as-question 0, closed 0.** Verified against the tree at the groom rather than taken from the entries: `web/src/lineage/` + `routes/LineageRoute.tsx` exist (O60's landing), `UI-WIP/wireframes/wireframes.json` carries WF-DFL-01..17 + the `FB-2026-08-13-01` feedback record and `out/dataflow.svg` is present, `web/src/ownership/` + `MiniDag.tsx` exist and the module registry's own tagline for /ownership is "SEAL → PAT → team rollup" — the exact chain Idea-122 draws (O61's landing), and `web/src/ask/` + `routes/AskRoute.tsx` + `drydocs_api/query_specs.py` exist (O62's landing). **The O60/O62 pairing is kept explicit in both items** — one job → pipeline → asset chain, swimlane form vs report form. **Nothing here decides an ontology question, and two caveats are written into acceptances rather than left in this file:** O60 renders READS/WRITES dashed-and-labelled-planned for as long as `m3_reads_from`/`m3_writes_to` stay `status: planned` (drawing skips no gate), and O61's dotted "aligns to platform" cross-branch edge renders as a visually distinct annotation because no confirmed graph relationship backs it. **The sensitivity boundary is in every acceptance:** all three SME-supplied examples live machine-local under `internal-local/` with real SEAL ids/hosts/org values; the committed fixtures are SYNTHESIZED twins of shape only. Ties recorded as ties, not dependencies: O61 ↔ G94 (renders the roll-up, does not consume the selector), O62 ↔ Idea-125 (whether the report also becomes an Ask-agent named-verb answer stays open in the inbox). No existing item's status, id, or text was touched — additive only, by the run's own no-impact constraint.

- **`Idea-123`** · 2026-08-13 · `[idea]` · **groomed → O62 (2026-08-17)** · prio? **Med** —
  **Web UI example output: the "Ask the knowledge graph" file-name search report.**
  SME supplied a real captured example (screenshot machine-local at
  `internal-local/ui-examples/dd-ui-wip-user-query-for-file-name-result.png`,
  transcribed — real SEAL ids/hosts/repo URLs — at
  `internal-local/ui-examples/dd-ui-ask-graph-file-search-transcription-20260813.md`).
  The use case: user searches a FILE NAME (or table) to find the business
  application and process associated with it; the result points to a
  file-transfer process fed by an event-based application, and the generated
  "report" shows the code repos and development teams for BOTH processes so
  support can escalate. Mechanism: a shortest-path traversal from an
  Application anchor filtered on a fileName property (~22-node result spanning
  application / product / dev-team / scheduler folder+job / file-transfer
  route / pipeline / repo labels), plus a source→node-label legend table the
  report view would carry. This is the concrete output target for the Ask
  route — pairs with the Idea-116 swimlane view (same job→pipeline→asset
  chain, report form instead of diagram form).

- **`Idea-122`** · 2026-08-13 · `[idea]` · **groomed → O61 (2026-08-17)** · prio? **Med** —
  **Web UI example view: the product roll-up flow — which area a job/folder
  supports and how it rolls up through the product catalog.** SME supplied a
  rendered mermaid example (screenshot machine-local at
  `internal-local/ui-examples/dd-ui-wip-user-view-product-mermaid.png`,
  transcribed — real org-taxonomy values — at
  `internal-local/ui-examples/dd-ui-product-rollup-mermaid-transcription-20260813.md`).
  The view: folder token = PAT AreaProduct, rolling up AreaProduct → Product →
  ProductLine → LOB, with the TWO roll-up shapes side by side — framework
  applications (no direct SEAL; the AreaProduct token is the join) vs app-tied
  applications (carry SEAL; the Control-M sub-application is the join) — the
  folder-name grammar as the leaf, data classification beneath, and a dotted
  cross-branch "aligns to platform" edge. Candidate UI shape: a mermaid/MiniDag
  flow on the product page; ties to the PRAOCG folder grammar and the G94
  standard-selection decision tree.

- **`Idea-116`** · 2026-08-13 · `[idea]` · **groomed → O60 (2026-08-17)** · prio? **Med** —
  **Web UI: a swimlane data-flow layout for the lineage module — lanes Control-M |
  Data Layer | File Server / Database.** Captured from SME chat while testing the
  wireframe feedback loop (recorded as `FB-2026-08-13-01` in
  `UI-WIP/wireframes/wireframes.json`); the idea traces to the user's original Full
  Circle Docs document-portal concept, §7 Business Flow Diagrams (transcribed
  machine-local at `internal-local/fullcircle-docs-scan-20260813.md`). The wireframe
  half is DONE at capture time: `UI-WIP/wireframes/out/dataflow.svg` (keys
  WF-DFL-01..17; the renderer gained `lane` + `arrow` primitives, spec v2). What
  remains is the React build: a swimlane layout for `/lineage` (proposed
  `lineage/SwimlaneView.tsx`) rendering job → pipeline → asset per data series —
  FW job "detected by" join, launcher→pipeline token join (G15 contract),
  condition edges per the BMC baseline — with READS/WRITES rendered dashed while
  `m3_reads_from`/`m3_writes_to` stay `status: planned` (no gate is skipped by
  drawing them). Wireframe-first is the point: SME feedback cites WF-DFL keys
  before any component exists.

- **GROOM 2026-08-14 (desktop, targeted — `Idea-128` only)** — closed `Idea-128` as **evaluated**: the producer-side GitNexus trial it proposed RAN on 2026-08-14 (desktop) and the entry's own body carries the full verdict, so the groom's whole job was the disposition. Mechanics all passed (clean global install, Windows worker pool fine, ~30s index of the DryDocs repo, working tree untouched so the publish boundary held, `.gitnexus/` a local cache) — but method-grain impact returned `epistemic: "exact"` while missing real receiver-annotated production call sites that plain grep finds, and a tool whose `exact` can be false cannot gate edits; **verdict: do NOT adopt as edit discipline.** **Promoted 0, inboxed 0, merged 0, closed 1.** No backlog item minted — module-boundary tests + grep remain the edit discipline on this codebase, and the entry's cleanup residue (disposable `.gitnexus/` caches, optional `npm uninstall -g gitnexus`) is delete-at-will hygiene, not an item. `Idea-124` (epistemic labeling as a CONCEPT) is explicitly unaffected by this close and stays open — ours must census its blind spots better than this implementation did. `backlog.yaml` is untouched, so `summary:` and `next_ready:` are unchanged by construction; the validator was still run. Nothing here decides an ontology question — the trial never touched the estate graph.

- **`Idea-128`** · 2026-08-14 · `[idea]` · **closed — evaluated at the 2026-08-14 groom: trial ran, verdict recorded in the body, do NOT adopt, no item minted** · prio? **Low** —
  **Producer-side GitNexus trial on the DryDocs repo itself (dev tooling only).**
  R5 of [`docs/reviews/gitnexus-depgraph-comparison.md`](../reviews/gitnexus-depgraph-comparison.md):
  index the DryDocs repo with GitNexus (supports Python; clone at `sandbox/GitNexus`),
  wire its MCP server, and evaluate `impact`/`detect_changes` before `drydocs_core`
  refactors — symbol-grain impact analysis beside (not replacing) the depgraph drift
  ritual. Check in the trial: Windows worker-pool behavior, index time, and that
  `.gitnexus/` stays out of git (their analyzer edits `.gitignore` itself — publish
  boundary). Never touches the estate graph or ontology.
  **TRIAL RUN 2026-08-14 (desktop) — verdict: do NOT adopt as edit discipline; grooming
  should close this as evaluated.** Mechanics all passed: global install clean (gitnexus
  1.6.9; npm 11 allow-scripts gate skipped postinstalls but prebuilt binaries cover it),
  Windows worker pool fine, DryDocs indexed in ~30s via `analyze --index-only` (16,737
  nodes / 27,077 edges), working tree untouched (publish boundary safe), `.gitnexus/`
  ~240 MB local cache. Quality on OUR Python is where it failed: class-grain
  `impact Neo4jClient` was reasonable (48 impacted, import-grain), and the
  ambiguous-name handling (`run_script` → 10 candidates, risk UNKNOWN until
  disambiguated) is genuinely good design — but method-grain impact on the
  disambiguated `Neo4jClient.run_script` returned impactedCount=1 labeled
  `epistemic: "exact"` while missing real receiver-annotated production call sites
  (`drydocs/loaders/base.py:442` `self.client.run_script(...)`, client: Neo4jClient;
  ditto `runs_on_resolution.py`) that plain grep finds. The honesty mechanism we most
  wanted (Idea-124's model) under-reports on Python receiver typing — "exact" was
  false. `trace main → Neo4jClient` found no path (breaks at CLI dispatch, our
  dominant pattern); `detect-changes` mixes markdown Section "symbols" into a
  risk=high verdict (noisy); FTS/BM25 unavailable offline (LadybugDB extension wants
  network). Net: for this codebase, module-boundary tests + grep remain stronger than
  its method-grain graph, and a tool whose `exact` can be wrong cannot gate edits.
  Idea-124 (epistemic labeling as a CONCEPT) is unaffected — ours must census its
  blind spots better than this implementation did. Cleanup: `.gitnexus/` dirs in
  DryDocs (~240 MB) and sandbox/GitNexus (~358 MB) are disposable caches; delete at
  will, plus `npm uninstall -g gitnexus` if not wanted.

- **GROOM 2026-08-13 (desktop, targeted — "the open inbox entries that would impact or change the established node labels and the Cypher loaders")** — the filter was applied to the WHOLE open and parked tail, not only the new captures, and every claim below was re-verified against the tree at the groom rather than taken from the entry. **Promoted 5: `U21`, `U22`, `U23`, `G97`, `Q18`. Merged 1. Inboxed 0. Parked as a question 0.** Four of the five are dependency-free and enter `next_ready` on arrival; `Q18` deliberately does not. **`Idea-118` → `U21`** (p1 bug, `drydocs-load`, phase 16): the code-snapshot load sweeps NODES and never EDGES, so `IMPORTS` only grows — `seal_attribution.py` still carries an edge to `loaders/base.py` that survived a full re-load, against a file with zero occurrences of the string and a snapshot that records no such edge (985 live vs 982 in the snapshot; fan-in 32 where the tree says 31). Written as a PER-SOURCE retraction with the over-reach guard as its own test, because the graph holds edges other loaders wrote; the mark-vs-delete call is left to the item but must be RECORDED, and if edges are marked then the read paths filter them the way U13 made node queries filter. Verified at the groom: `stale_edge_cleanup.cypher` is the repo's only edge-retraction precedent and has NO live caller in the tracked tree, so the pattern exists as a file rather than as a mechanism. **`Idea-117` → `U22`** (p2 bug, `graph-infra`, phase 16): every `:CodeModule` carried one Aug-2 `last_seen_at` for eleven days and the session read A3's fan-in as the Aug-2 value believing it current — the G78 class, a read that SUCCEEDED with the wrong data. The entry explicitly handed the warn-vs-fail call to the groom: **RULED WARN**, on the same argument CLAUDE.md already makes for `snapshot.ps1`'s CI check (recording structure and passing a gate are unrelated jobs, and the check must not red a suite on a machine with no container). What is unit-testable is the COMPARISON over fixtures — fresh / stale / no snapshot / empty graph / database-unreachable, that last one a DISTINCT verdict and never "fresh" — so the mechanism is guarded with no database. Priority dropped to p2 from the entry's High with the reason in the notes: one existing command repairs it and did, so what is missing is detection. `module: graph-infra` chosen on SUBJECT (the loaded graph's currency, U15/U19's family) over `docs` (the review-plan file, U13/U20's) and the choice is recorded in the item, because both were plausible. **`Idea-47` → `U23`** (p3 task, `ontology`, phase 16, `fable`, `ontology-mapper`): the `.cypher` files are `:CodeModule` nodes with zero edges while each loader names its Cypher as a literal path — promoted as a **gate-rider DRAFT and only a draft**, on the G27 / N10 / G95 precedent, because a new relationship type is an ontology decision. Its clause (c) is what stops a signed rider with no path to a first row: the depgraph scanner does not emit the edge, so the prompt must say where it would come from and what an instrument change costs. Clause (d) fences it against gate `self-documentation-code-graph` §H5 — a loader→cypher edge is the FIRST half of the "which module loads this job" join and not the join. **`Idea-23` → `G97`** (p2 task, `drydocs-lineage`, phase 6): the parked trigger has FIRED and the entry was out of date — `m7_uses_artifact` has been `status: active` since 2026-08-07 (gate `rua-load-shapes` §A4, applied at G55), not `planned`, and `writer.py` MERGEs `:ETLProcess` on its token. G16's own notes name this item by description. NO gate is opened: `cmdline-nfr-vetting` ruled the distinct label and the `:Script` refinements, `rua-load-shapes` activated both entries together precisely so the launcher/payload split is right from first load. Verified ABSENT at the groom so this is a real build — the writer emits no `USES_ARTIFACT` edge and stamps `script_role` only for the rua profile case. **`Idea-88` → `Q18`** (p2 task, `drydocs-load`, phase 14) — **the parking is PRESERVED, not overridden**: the entry was parked behind two open rulings, and the item reproduces that as `depends_on: [G32, Q14]`, so it stays out of `next_ready` until both rule while the work becomes visible in the database instead of living only in this file. Its acceptance says in writing that the edge TERM is Q14's and residency is G32's, and it carries Q16's unshipped clause (b). **Merged 1: `Idea-119` → `G78` clause (d) + a rider note on `G79`** — the five loaders with no direct test import (`business_segments`, `controlm`, `controlm_dependencies_derived`, `controlm_hosts`, `seal_contacts`) ride the fix that touches them, which is the entry's own proposed disposition; A5 is named in the clause as a DIRECT-IMPORT proxy so the ask is an import-bearing test, not proof of total absence. `G79`'s note names the two the split re-homes, verified at the groom (`seal_contacts` is a `REFRESH_REFERENCE_CHAIN` member and `business_segments` is refreshed inside the same command, ahead of the chain tuple). **Deliberately NOT promoted, each for a stated reason:** `Idea-86` and the residency half of `Idea-88` stay behind `G32`, which is still `in_progress` (an unsigned drafted gate) — three parked consumers on one gate is an argument for scheduling it, not for pre-empting it; `Idea-7` (flipping the four `m3_*` lineage entries active) and `Idea-37` are HITL-scheduled by their own terms; `Idea-104` (which MFT route-id shape is real) and `Idea-34` (whether the AIS acronym entry survives, and what `:AisTool` ever meant) are label/identifier questions that only the SME can answer; `Idea-15`'s remaining call — display labels only, or renaming the `seal_*` vocabulary ids and domains — is ADR-scale and the user's; `Idea-25`, `Idea-27`, `Idea-31` and `Idea-61` were re-read and their triggers are still unfired. `Idea-122` and `Idea-123`, both captured the same day, DESCRIBE label chains rather than change them — they are UI-view work and belong with the console epic, so this run left them. **Nothing here decides an ontology question:** `U23` is a prompt that registers nothing, `G97` builds inside two signed gates and flips no entry, and `Q18` routes both of its open questions back to `Q14` and `G32` by dependency.

- **GROOM 2026-08-12 (desktop, targeted — `Idea-112`, `Idea-113`, `Idea-114` only, not the open tail)** — three entries captured the same day from live work, all three actionable, so this run promoted rather than parked. **Promoted 4: `G92`, `G93`, `G94`, `G95`** — all four dependency-satisfied and in `next_ready` on arrival. **Inboxed 0, merged 0, parked-as-question 0.** Every claim below was re-verified against the tree at the groom rather than taken from the entry, and all of it is sample-reproducible with no database and no company data (J18). **`Idea-112` → `G92`** (p2 task, `drydocs-lineage`, phase 6, deps G14/G46/G60 all done): the entry's premise holds exactly — `_prepost_pass` in `drydocs_lineage/extractors/controlm_inventory.py` calls `parse_command(value)` on the RAW variables-CSV `var_value`, and `_file_op` keys the asset off that verbatim operand, so `%%R_PATH/out.dat` and `/data/r/out.dat` plan edges to two `DataAsset` nodes for one file; the CMD_LINE pass shares the defect, pre/post merely concentrates it. Written as a FEED change, not a new parser and not a new resolver: `resolve_layers` / `resolve_command_line` (G46, done) already return each definition's `resolved_value` with substitution provenance, and PRECMD/POSTCMD are themselves SETVAR definitions, so the chain that resolves the rest of the job resolves them in place. The acceptance carries the four things that make it reviewable — raw stays beside resolved (the G46 derived-fact shape), `{ODATE}`-class residue counted as EXPECTED and kept distinct from an unresolved user variable, `ResolveCoverage`-style per-run counters on the existing `ExtractCoverage` summary line, and both variables-CSV shapes feeding the scope chain (`var_scope` in the aliased projection; the `JOB_NAME == folder name` header rule in the raw export, per `drydocs/staging.py`). Endpoints unchanged, no new relationship type, `m3_reads_from` / `m3_writes_to` stay planned — no gate. `module: drydocs-lineage` recorded in the item: the change point is the extractor's pass, core's resolver is CALLED not modified. **`Idea-113` → `G93`** (p2 task, `drydocs-remediation`, phase 6, dependency-free): `render_handoff()` in `drydocs_remediation/jira.py` emits Findings / Scope / Change / Equivalence / Acceptance / Rollback and not one count of what the run processed, so the ticket carries no denominator — while the extractors already model exactly this (`ExtractCoverage.summary()` with the G60 `prepost_*` split, `XmlDefsCoverage`, findings by rule). Also verified: NOTHING under `drydocs_remediation/` imports `run_log` today (`drydocs/cli.py` is the only `LoaderRunLog` caller), so the batch-side run log is IN the item rather than assumed. Acceptance pins the five things that keep it honest — counts ride the run log not the console, they are recorded not recomputed at render time (proven by a test where the renderer gets a filtered finding list), skips counted with reasons, absence rendered as *not recorded* rather than omitted, and the equivalence proof NOT restated so a big denominator cannot read as evidence. **`Idea-114` → `G94` + `G95`, split on buildability.** `G94` (p2 task, `drydocs-core`, phase 6, deps G84 done) is the decision tree, and it is buildable now because the repo already has both inputs: `config/launcher-registry.yaml` classifies DPL / ABINITIO / INFORMATICA through `classify_executable()`, and `JOB_ROLES` is already the C30 discriminator set — the gap is that `required_tokens()` keys on `JobType` alone. Its most durable clause is the guardrail-as-test: §7.5 and G84(c) rule the DD digit a grammar VERSION that must not select a standard, so a test asserts the same job under `DD1|` and a hypothetical `DD2|` selects the SAME standard, and the per-engine token CONTENT is explicitly out of scope (an unruled engine inherits the generic set and REPORTS that it did). `G95` (p3 task, `config`, phase 6, `fable`, dependency-free) is the other half as a DRAFTED GATE PROMPT on the G27 / W1 / N10 / G61 precedent — drafting decides nothing — because standard identity and its carrier are a contract change to `TOKEN_REGISTRY`, whose docstring calls itself the single source parser and register both read from, guarded by the registry-vs-standard agreement test. The prompt puts four questions and pre-picks none: identity shape, carrier (versioned YAML under `config/` on the launcher-registry precedent vs. the SQLite table the user floated), ratifying the DD-digit fence explicitly *because a per-team registry is the exact pressure that would break it*, and whether a team profile may RELAX a company-required token or only add. `module: config` recorded in the item — the artifact under discussion is a registry/profile store and `config/` is the declared home for registries; the prompt DESCRIBES a change to a `drydocs-core` module without making one. **Nothing was parked as a question** — no `module` or `phase` was genuinely two-way, and the one decision the user has not made (where a standard lives) is routed to the SME as `G95` rather than guessed. **Left for the user/SME: unchanged from the third pass**, plus the `G95` gate itself.

- **GROOM 2026-08-12 (desktop, third pass — the two entries captured after the second pass)** — the inbox gained exactly two entries since the morning runs, `Idea-110` and `Idea-109`, and they needed opposite dispositions. **Promoted 1: `J48`** (p2 chore, `drydocs-core`, phase 8, dependency-free) from `Idea-109`'s RESIDUE. The reported bug — a worktree-isolated agent running the session-end render ritual writes `board.html` / `ideas.html` / `roadmap.html` into the MAIN tree — was already FIXED the same day at `841dc6e5` (`drydocs_core/repo_paths.py`, adopted in `plan_board`/`plan_ideas`/`plan_roadmap`, 13 tests including one that drives a real `git worktree` through a real `render_board.py`), so what was left was never groomed into anything: **seventeen** other modules still anchor a default path on a raw `Path(__file__)` repo root. Re-counted at this groom rather than taken from the entry — a `grep` for `REPO_ROOT =` across `drydocs/`, `drydocs_core/` and `scripts/` returns 21 sites, of which 3 have adopted `repo_root()` and 1 is the docstring example in `repo_paths.py` itself, leaving 17 (plus `ontology/schema_graph.py`, which uses `Path(__file__)` without a `REPO_ROOT` name and is in the item's inputs for that reason). Evidence is re-runnable with no database and no company data (J18). The item is written as a **sweep with a judgement, not a mechanical replace**, because the entry is explicit that these are not all bugs: repo-*content* defaults follow the caller's checkout, package-*internal* resources rightly keep `__file__`, and each site gets that one-line ruling — with "correct as written" recorded as a package-internal disposition rather than a skip, plus a derived coverage test (the S10 precedent) so a NEW un-ruled site reds instead of passing by omission. Likely dispositions are written into the notes as NON-binding, so the sweep is not re-derived from scratch. `module: drydocs-core` chosen and recorded in the item: the convention, its one implementation and its guard all live in `drydocs_core/`, even though the sites span three trees. **Inboxed 0, merged 0.** `Idea-110` needed nothing — it was captured AND closed the same day (`b268cd36` reclassified `UI-WIP/claude-design-ui-prompt.md` as a dated record), and its residue is a standing habit ("resolve the paths a doc cites before landing an idle branch"), not an item. **Left for the user/SME: 9, unchanged from the second pass** — `Idea-104`, `Idea-74`, `Idea-34`, `Idea-33`, `Idea-32`, `Idea-28`, `Idea-17` (the two machine-local relics), `Idea-16` (the SNYK repo secret), and the `E1` status question inside `Idea-93`; all were re-verified against the tree hours earlier at the second pass, so this run did not re-walk them. Nothing here touches edge semantics: J48 is path resolution only — no graph write, no vocabulary entry, no gate.

- **GROOM 2026-08-12 (desktop, second pass — "finish any non-HITL open items")** — the inbox had NO new captures (the 08-11 weekly pass consumed Idea-96..Idea-107 and the earlier 08-12 pass worked the tail), so this run did the one thing left that is not the user's: walk every OPEN and residual-clause entry, verify its state against the tree, and either finish it or say precisely what it waits on. **Promoted 1, and it did not come from the inbox:** **K24** (p2 bug) — the `fid-identity-and-scope` gate page carries TWO questions numbered **Q6**, the SME answer landed 2026-08-12 by `887a0e7` and an older, still-open application-roll-up question that was never renumbered when the new one was appended, while FOUR other files cite "Q6" by number (`config/source-mappings/psgmgr.yaml`, `config/source-registry.yaml`, `docs/k16-fid-census-company-prompt.md`, and K16's own "RUN Q6 FIRST" line). Reproduced at the groom with a scan of every file in `config/gate-prompts/` — exactly one collision in the whole tree — so the evidence is re-runnable with no database and no company data (J18). It renumbers only the entry nobody cites and adds the duplicate-id guard to `tests/unit/test_gates_json.py`; it answers nothing, which matters because K17 is the next gate walked on that page. **Fixed in place, 2 stale `inputs:` paths** (the `Idea-93` class, re-audited across all 112 non-`done` items): `G63` and `G64` cited `config/audit-fields/` as a directory when the ledger is the file `config/audit-fields.yaml`. Three refs flagged, two were typos, one (`Y4`'s `backlog/items/`) is a legitimate future output — down from fourteen at the 08-09 sweep. **Two open entries narrowed by verification rather than by a ruling:** `Idea-17` — both pre-squash branches are ALREADY GONE from origin and the stash is empty, so the destructive REMOTE decision it was raised for no longer exists; two this-machine-local relics remain. `Idea-16` — re-verified the `snyk` job is still in `ci.yml` and still gated on the missing repo secret, so it is unchanged and undischargeable by any agent. **Three residual clauses re-read as PARKED with named triggers, not open:** `Idea-20`(a) → a real `CMD_LINE` sample carrying the `ingestion-launcher` jar (a repo-wide search finds that string only in this file and the backlog text quoting it, so an item today would have no input), `Idea-20`(d) → layer-4 context-graph work starting, `Idea-10`'s ALIAS tier → an alias source existing at all. **Inboxed 1:** `Idea-108` — two abandoned agent worktrees pinned at `6c24963` are holding UNCOMMITTED work (6 and 8 changed paths, including the untracked `scripts/render_underhood_benchmark.py`), while all four `worktree-agent-*` branches are already ancestors of `main`; parked rather than swept because the standing rule is that no session touches another stream's uncommitted work, and both salvage and prune are irreversible in one direction. **Left for the user/SME: 9, unchanged** — `Idea-104`, `Idea-74`, `Idea-34`, `Idea-33`, `Idea-32`, `Idea-28`, `Idea-17` (local half), `Idea-16`, the `E1` status question in `Idea-93` — plus `Idea-108` new. Nothing here decides an ontology question: K24 is identifier hygiene on a gate page and explicitly rules nothing the gate owns.

- **GROOM 2026-08-12 (desktop)** — a SMALL groom by design: the 2026-08-11 weekly pass consumed every new capture (Idea-96..Idea-107), and nothing has been captured since, so this pass worked the OPEN and PARKED tail plus one cross-check the inbox could not have produced. **Promoted 2:** both from the Control-M `DESCRIPTION` seam, both reproduced at the groom with a sample and no database (J18) so anyone can re-run the evidence. **G83** (p1 bug) — C30 ruled the description token set on 2026-08-11 and only the standards page moved: parsing a fully C30-conformant watcher description returns SEVEN findings (`FTS_ID` and `REC_ID` as unknown keys, `ENV` + both route ids + both `EMAIL_DL`s reported missing), and `G67`'s own conformance fixtures already emit `FTS_ID: FTS2`. The judgment call is written into the acceptance rather than left open: retired tokens are MARKED, never deleted, because the deployed estate still carries them and a greenfield standard cannot retroactively unwrite ~240K descriptions. **G84** — the `DD1|` sentinel from `Idea-105`'s SME resolution: today the parser reports the compliant marker itself as an `unparseable_segment`, and legacy prose containing a colon manufactures pseudo-tokens indistinguishable from a C16 team-local annotation. Fenced: a READ gate only, ratifying nothing, with the marker in ONE constant because gate `email-dl-contact-point` §G6 still rules it. **Merged 1:** `Idea-73` (the employee hierarchy) → **G74**, which was raised 2026-08-11 asking the same question from the other end; three findings ride across — O44 column 1 is a second waiting consumer, `pat:people-report` carries teams not reporting lines so it is NOT the source, and the 2026-07-23 HR-hierarchy direction was written for the COMPANY gate, which is why nothing landed here. **One dependency added:** `G77` now depends on `G84` as well as `C34` — its clause (a) registers a THEME token *inside* the `DD1|` block, and without the link two sessions implement the same sentinel differently in one file. **Left for the user/SME: 9** — `Idea-104` (which MFT route-id shape is real; G83 was written NOT to answer it), `Idea-74` (does DryDocs ingest the ServiceNow queue export, and on which side), `Idea-34`, `Idea-33`, `Idea-32`, `Idea-28`, `Idea-17`, `Idea-16`, and the `E1` status question inside `Idea-93`. **Four parked entries re-checked, none fired,** and two of them narrowed: `Idea-15`'s placement blocker is DISCHARGED (the `generic-naming` epic now exists), leaving one open user call instead of two; `Idea-38`'s class (1) is CLOSED by the 2026-08-11 authored-fixture ruling, leaving three; `Idea-25` and `Idea-27` re-verified unfired against the current tree. Nothing raised here decides an ontology question: both new items are pure-parse, zero graph writes, every token stays `proposed`.

- **`Idea-119`** · 2026-08-13 · `[chore]` · **merged → G78 clause (d) + a rider note on G79 (2026-08-13) — the five untested loaders ride the fix that touches them, exactly as this entry proposed** · prio? **Med** —
  **31 package modules have no direct test import, and five of them are loaders G78 is
  about to change.** A5 measured 2026-08-13 at `bb9788b6`: 31, against the skill's 29
  baseline at `2d104ef` (08-09). By package: `drydocs_core` 14, `drydocs` 10,
  `drydocs_lineage` 4, `drydocs_docmeta` 2, `drydocs_api` 1. The pointed five are
  `business_segments.py`, `controlm.py`, `controlm_dependencies_derived.py`,
  `controlm_hosts.py` and `seal_contacts.py` — untested loaders, while G78 (p0) fixes a
  chain step that silently skips a missing input and reports success. Highest
  single-leverage gap: `drydocs_lineage/extractors/rua_inventory.py`, fan-in 5, no test
  import. Two caveats ride with the number: A5 is a DIRECT-IMPORT proxy, so fixtures and
  subprocess coverage do not show; and the +2 could not be attributed (see Idea-120).
  Proposed disposition on groom: **merge the five loaders into G78/G79's acceptance**
  rather than filing a coverage sweep — the tests belong with the fix that touches them.

- **`Idea-118`** · 2026-08-13 · `[bug]` · **groomed → U21 (2026-08-13)** · prio? **High** —
  **`IMPORTS` edges are never retracted, so fan-in inflates permanently and test debt
  under-reports.** Found while cross-checking the freshly reloaded graph against the
  snapshot it was loaded from. `drydocs/loaders/seal_attribution.py` still carries an
  `IMPORTS` edge to `drydocs/loaders/base.py`; the file contains ZERO occurrences of the
  string "base" (K8 removed it at `4df4df2`), and today's snapshot records no such edge.
  **The edge survived a full `load-code-snapshot` re-run** — so this is not the staleness
  in Idea-117 and a refresh does not fix it. The D7 sweep tombstones removed MODULES;
  nothing sweeps removed EDGES, so the import graph only grows. Size today: 985 live
  `IMPORTS` edges in the graph vs 982 in the snapshot — 3 ghosts, one of which put
  `loaders/base.py` at fan_in 32 where the tree says 31, distorting the repo's #1
  change-risk metric. **A5 is affected in the dangerous direction**: a module whose test
  import was DELETED keeps the ghost edge and still counts as tested, so test debt reads
  better than it is. Fix shape: retract edges absent from the loaded snapshot for any
  module that snapshot DID include — a per-source sweep, never a global delete, since the
  graph holds edges other loaders wrote.

- **`Idea-117`** · 2026-08-13 · `[bug]` · **groomed → U22 (2026-08-13; the warn-vs-fail call this entry left to the groom is RULED WARN in the item's clause (b))** · prio? **High** —
  **The code graph can go stale for weeks and nothing says so.** Found by `/tech-debt`
  2026-08-13 (desktop, `neo4jtest`, `drydocs` DB): every `:CodeModule` carried
  `last_seen_at = 2026-08-02T23:06:42Z` from ONE run id — loaded once on Aug 2 and never
  refreshed, 11 days. The session first read A3's top fan-in as 28, which is the Aug-2
  value (the skill's own baselines run 28 → 29 on 08-04 → 31 on 08-09); it looked current
  and would have been reported as current. Same class as G78 — not a failed read, a read
  that SUCCEEDED with the wrong data, and it sits underneath every architecture and debt
  decision. `drydocs load-code-snapshot` repairs it in one command (run 2026-08-13; graph
  now 1697 modules, 164 tombstones), but nothing compares `max(m.last_seen_at)` against
  the newest snapshot's `meta.captured_at`. Proposed: a freshness assertion in
  `tests/unit/test_code_graph_review_plan.py`, which already fails when the typed package
  allow-list and `pyproject.toml` disagree — the shape exists, this is one more check in
  it. Warn-vs-fail is a real call for the groom: the snapshot ritual's CI check is
  warn-only on the argument that recording structure and passing a gate are different
  jobs, and the same argument applies here.

- **`Idea-88`** · 2026-08-07 · `[idea]` · **groomed → Q18 (2026-08-13), with the parking PRESERVED as `depends_on: [G32, Q14]` rather than overridden** · prio? **Med** —
  **The only loaded software↔docs edge has NO registry declaration behind it — close
  the gap with a `describes_product:` field.** The 27 live
  `(:Document)-[:DESCRIBES]->(:SoftwareProduct)` edges for `controlm` are asserted by a
  hardcoded Python constant — `drydocs/loaders/bmc_docs.py`
  `SUBJECT_PRODUCT_ID = "controlm"` — and the corpus's `doc-source-registry.yaml` entry
  carries only `taxonomy_path`, which NO file maps to a product id. So the one working
  traversal in the estate is unreproducible from the ledger, and a report cannot
  honestly infer the declaration (the /software page refuses to, deliberately — O56
  honesty rule 4). Fix direction: a `describes_product:` field on doc-source-registry
  entries, with the loader READING the registry instead of carrying the constant, plus
  a guard that the id resolves to a real software-registry product. Parked rather than
  groomed because it touches a loader AND a gated corpus behind two open rulings — G32
  (which database corpora live in) and Q14 (which term carries the edge) — and this is
  also where Q16's unshipped clause (b) will land. (Found at the Q16 close, 2026-08-07.)

- **`Idea-47`** · 2026-08-02 · `[idea]` · **groomed → U23 (2026-08-13) — the gate-rider DRAFT only; the edge stays unregistered until the SME signs, and the emitter question rides the prompt** · prio? **Low** —
  **The 45 `.cypher` files are now nodes with zero edges — nothing joins a
  loader to the Cypher it executes**, even though the path is a literal in the `.py`
  (`CYPHER_DIR / "code_snapshot.cypher"`). `drydocs/loaders/` holds 32 `.cypher` + 24 `.py` +
  15 `.sql` side by side, unconnected. depgraph does not emit the edge and the loader could not
  load it if it did (new edge type → gate). This is gate §H5's named future item, now with the
  nodes already in place — the remaining work is the edge, not the corpus.

- **`Idea-23`** · 2026-07-21 · `[idea]` · **groomed → G97 (2026-08-13) — TRIGGER FIRED: `m7_uses_artifact` has been `status: active` since 2026-08-07 (gate rua-load-shapes §A4, applied at G55), not `planned` as this entry recorded, and the writer MERGEs :ETLProcess on its token** · prio? **Med** —
  **m7 build follow-up** (from gate `cmdline-nfr-vetting`): migrate
  payload invocations out of the m3_invokes 1..n fold onto the registered `USES_ARTIFACT`
  edge + stamp `script_role` {launcher, payload} and the artifact_* properties on :Script.
  Feed now EXISTS (G16 value-contract facts + G15 launcher properties); groom once the
  writer's ETLProcess endpoint work makes the edge landable — the vocab entry
  `m7_uses_artifact` stays `planned` until that build's own flip.

- **`Idea-105`** · 2026-08-11 · `[question]` · **groomed → G84 (2026-08-12, the READ gate only — the ruling itself stays the gate's, rider §G6)** · prio? **High** —
  **Two things claim the same 4000-char Control-M `DESCRIPTION` field on generated
  objects, and they cannot both hold.** The DPL generator stamps two literal strings
  (`Generated Control-M Folder`, `Generated job to trigger DPL …`), and
  `internal/controlm-config/controlm-pipeline-stub-integration-plan.md` item **E1** keys
  machine-generated provenance on an EXACT match of those literals. The company
  description-metadata standard captured at C29
  (`internal/controlm-config/reference/controlm-job-metadata-standards-capture.md`)
  fills the same field with pipe-delimited `key: value` tokens. Add a token block and
  E1's literal match breaks; require the literal and the token block has nowhere to go.
  Neither document mentions the other. Three exits: (a) exempt generated objects from
  the token standard — cheapest, but generated objects are the majority of the estate
  and the metadata is most valuable exactly where nobody hand-authored anything;
  (b) fold the literal in as one token (`GENERATED_BY: <generator>`) — keeps both, but
  changes E1 from a string compare to a parse and invalidates the discriminator on every
  object already generated; (c) move the discriminator off `DESCRIPTION` to something
  else the generator also stamps. DECIDE with whichever item lands E1; raised as gate
  rider `email-dl-contact-point` §G6 so a section-C ruling cannot presume an exit
  silently. Sibling finding: REQ-3 in the same capture reintroduces the dot-smuggling
  pattern (`…%%$NEXT..tok`) that the description-metadata plan §3 lists as hazard #1 —
  so the practice is not extinct in the *standards*, not just in the legacy estate.
  **CHECKED AT THE 2026-08-11 GROOM — still open, and already carried in two places, which is why no item was minted.** C29's notes record the collision verbatim, and it rides `config/gate-prompts/email-dl-contact-point.yaml` as rider §G6 so a section-C ruling cannot presume an exit silently. There is still NO backlog item landing the stub plan's E1, so there is nothing to merge into; the three exits (exempt generated objects, fold the literal in as a `GENERATED_BY:` token, or move the discriminator off `DESCRIPTION`) have materially different costs on an estate that is mostly generated objects, so this is a user/SME ruling at that gate rather than a groom decision.
  **RESOLVED 2026-08-11 (SME design session) — EXIT (d), which none of the three recorded
  exits describes: a VERSIONED SENTINEL PREFIX partitions the field, so both claims hold
  unchanged and nothing already deployed migrates.** A description that begins `DD1|` is
  authored to the token standard; one that does not is either the generator's literal or
  legacy filler. E1 keeps its exact-match discriminator because generated descriptions
  never carry the tag; the token parser never sees a generated object it would choke on;
  and legacy waterfall prose becomes a third, correctly-ignored class. Cheaper than all
  three recorded exits: (a) loses the metadata where the estate is densest, (b)
  invalidates E1 on every object already generated, (c) needs a new carrier the generator
  stamps — (d) costs one prefix and zero migrations. It also RETIRES C29's proposed
  `GENERATED_BY` token: absence of the tag on a literal-match description already is the
  provenance signal, so a token asserting it is a second carrier for one fact.
  THE DESIGN THAT RIDES WITH IT, all SME-ruled the same session:
  (1) the digit is a VERSION, not a template id — `DD1|` / `DD2|` parse side by side
  through a grammar migration, and template selection is `TASKTYPE` (derived) plus the
  already-registered `JOB_ROLE` token (declared), never the sentinel;
  (2) anchored at position 0, so the check is `startswith` — the cheapest possible SQL
  predicate at ~240K jobs, and prose that quotes the convention cannot false-positive;
  (3) FOLDER SCOPE is preferred, because `get_description()` is generator-owned and a
  tagged block on a generated JOB is overwritten at the next regeneration;
  (4) the compliance objection dissolves rather than being solved — untagged means
  unread, so multi-team inconsistency costs COVERAGE (a number that grows) instead of
  corrupting data (a number that never closes). Under 10 folders carry the standard
  today, which is a sample size, not a weakness: what is being proven is that the round
  trip is lossless and the vocabulary holds WHEN the field is filled, never that teams
  will comply.
  Recorded at the gate as rider §G6 exit (d) and specified in
  `knowledge/standards/technology/controlm-guidelines-and-standards.md` §7.5. The gate
  still RULES it — this entry stops being an open question and becomes a recommendation
  with a written warrant. NOTE for the company side: their copy of the gate prompt is
  canonical-company and did not take the producer edits, so RELAY-7 carries this across.


- **`Idea-73`** · 2026-08-05 · `[source]` · **merged → G74 (2026-08-12) — the item that owns the :Employee spine now carries the source question, the O44 column-1 consumer and the company-side reading** · prio? **High** —
  **Where does the employee hierarchy come from, and does it live producer-side at
  all?** Established while drafting G35: `:Employee` is a node class (`prov:Agent`)
  with **no Employee-to-Employee edge anywhere** in the relationship vocabulary —
  no `REPORTS_TO`, no manager edge, no source feeding one, no backlog item that
  would create one. Two separate SME directions now depend on it: G35 §B7 ("if a
  person is in the role, create the relationship to the employee hierarchy in a
  later pass") and O44's first column, whose manager filter is its whole point.
  The 2026-07-23 producer-session HR-hierarchy direction — single `:Employee`
  spine, two-scope HR supplement, two-pass loader, `REPORTS_TO` current-state
  sweep — was written for the **company** `hr-emp-hierarchy` gate, which is
  probably why nothing landed here. Decide whether the producer repo gets a
  hierarchy at all (with what source — `pat:people-report` carries teams, not
  reporting lines), or whether both directions are company-side and the producer
  records that explicitly. Marked High because two committed directions currently
  defer to something that does not exist, and a deferral pointing at nothing is an
  omission with better wording.


- **GROOM 2026-08-11 (desktop, weekly)** — worked the eleven ungroomed 2026-08-09..08-11 captures plus one misfiled entry found at the bottom of this file. **Promoted 10:** `Idea-96`→**J42** (the backlog union rule has no guard — a port-time id-set diff), `Idea-100`→**J43** (a `gate_bound:` precondition key on PORT-MANIFEST rows), `Idea-103`→**J44** (where the unclosed-fence guard's boundary sits for captured and vendored markdown), `Idea-99`→**J45** (the owed DPL/Snowflake port relay), `Idea-106`→**J46** (the clock-racing run-log collision test), `Idea-107`→**J47** (no guard asserts a PORT-MANIFEST path exists; the ordering check is hardcoded), `Idea-98`→**C33** (the adhoc Ab Initio version loader C25 authorized), `Idea-97`→**U20** (the review plan's six-scan-roots baseline, two package generations stale), `Idea-102`→**K22** + **K23** (the Deployment Module CI class via the gate, and the KB-article grain check). **Merged 2:** `Idea-101` into **J43** as clause (b) — same file, same vocabulary, same reviewer, so the derived-render disposition is decided in the same pass; `Idea-102`'s register-line finding into **G70**'s notes rather than its acceptance, because that acceptance mirrors a SIGNED gate register and a groom does not edit one. **Left open as questions for the user/SME: 2** — `Idea-104` (which MFT route-id shape is real, updated with what C30 did and did not settle) and `Idea-105` (the two claimants on the 4000-char `DESCRIPTION` field; three exits, already carried as gate rider §G6 and in C29's notes, with no item landing E1 to merge into). **One id repaired:** the 2026-08-11 manifest-guard capture had been filed as a second `Idea-86` and appended BELOW this audit trail — renumbered `Idea-107`, tagged `[bug]` instead of the non-vocabulary `[guard]`, and groomed. Every item raised here is dependency-free, so all ten enter `next_ready` on arrival; nothing raised decides an ontology question — K22 and K23 both register `planned` and route via the gate.

- **`Idea-96`** · 2026-08-09 · `[chore]` · **groomed → J42** · prio? **High** —
  **The backlog union rule has no guard: nothing asserts that after a port the consumer's
  item-id set is a superset of the producer's at the port base.** `PORT-MANIFEST.yaml`
  states the rule unconditionally for `docs/restructure/backlog.yaml` — *"Union the items;
  NEVER regress a status … or drop an entry"* — and `tests/unit/test_backlog.py` enforces
  plenty about the file (schema, roll-up arithmetic, `next_ready`, unknown `depends_on`),
  but every one of those checks looks at ONE copy in isolation. The union is a claim about
  TWO copies, and no check ever compares them, so a port that quietly under-delivers items
  leaves both sides internally consistent and passing. Textbook J26: a rule written in
  prose and enforced by nobody, which is exactly the shape that survives unnoticed —
  surfaced during a reconcile, where items present in the producer at the port base turned
  out to be absent downstream and neither side's suite had anything to say about it. Note
  the near-miss that makes this worse than it sounds: the dependency guard would have
  caught it *if* any surviving item had depended on a missing one, so whether the gap is
  visible at all is luck, not design. Shape of the fix: a port-time check (not a unit test
  — the producer tree cannot see the consumer's) that diffs the two id sets at the recorded
  port base and fails the port report on a non-empty producer-minus-consumer difference,
  with a named allow-list for ids deliberately not carried. Cheap, and it converts the
  union rule from a promise into an assertion. Mechanism only — the numbers and ids from
  the occurrence stay in the port report, not here.

- **`Idea-97`** · 2026-08-09 · `[bug]` · **groomed → U20** · prio? **Low** —
  **The review plan's doc-coverage baseline is two package generations stale — same disease
  U18 just fixed one table over.** `docs/reviews/code-graph-review-plan.md` Phase 3 unit 3
  still reads *"Six scan roots × DesignDoc coverage"* with per-root counts (`tests` 85,
  `drydocs` 41, `drydocs_core` 35, `lineage` 12, `remediation` 7, `deepdoc` 3) that predate
  BOTH `drydocs_api` and `drydocs_docmeta`. U18 widened the A1–A6 metric scope to eight
  package roots and guarded the typed list against `pyproject.toml`, but that guard is
  anchored on the `$packages` literal and this unit hard-codes its own root list in prose,
  so it was out of the guard's reach and out of U18's stated surface. Left deliberately
  rather than swept in. Fix is small: restate the unit on eight roots, re-measure the
  per-root doc coverage, and decide whether the count belongs in prose at all or should be
  derived like the metric scope now is — the third hand-typed root list in the same
  document is the argument for deriving.

- **`Idea-98`** · 2026-08-09 · `[chore]` · **groomed → C33** · prio? **Med** —
  **The adhoc Ab Initio version loader — the build C25 authorized and deliberately did not do.**
  Gate `software-version-context` signed the shape and nothing else:
  `reg_appuser_uses_software` is registered `status: planned`, no loader exists, and the
  `adhoc-sme-email` corpus stays `confirmed: false` for that reason alone. The build is:
  the loader itself (MERGE key `{source, install_path}`, edge properties per §B3, `as_of`
  from the email's sent date), the `:Document` minted from a hand-recorded citation, the
  `evidence:` block's `as_of` filled in on the `abinitio` product row, registration in
  `config/manual-loads/manifest.yaml` per §E4, and the §C1 install-path pattern rows in the
  `invocation_patterns` shape. **Settle §Q3 before writing the MERGE key, not after** —
  the gate deferred it with the consequence stated: if the estate re-points installs by
  symlink, `install_path` is a poor key and identity moves to `(fid, version)`, which is a
  re-key rather than an edit. Two things this build must NOT do: write the §F
  application-level rollup (blocked on K17, and not behind a flag), and auto-append observed
  versions to the curated `versions:` list (§C2).

- **`Idea-99`** · 2026-08-09 · `[chore]` · **groomed → J45** · prio? **Med** —
  **Port relay owed: the producer is now canonical for the DPL and Snowflake registry
  entries.** C25 registered the `dpl` and `snowflake` product rows, the `in-house` vendor
  (no `publisher_url`, guard narrowed to third-party vendors), and the acronym
  `DPL: "Data Pipeline Library"`. The SME began the same expansion company-side on
  2026-08-07 and **stopped so the two copies would match** — so this is a deliberate
  producer-first divergence with a waiting consumer, exactly the shape of the standing AIS
  acronym relay (R1), whose lesson applies here too: that expansion had to be carried
  ACROSS FILES rather than same-file overwritten, and this one may as well. Deliberately
  NOT written into `docs/port-prompt.md` at the time it arose, because a port was in flight
  against a fetched head and that file is a hand-merge surface — a relay added mid-port
  lands in someone's conflict resolution instead of their checklist. **Add it once that
  port merges**, together with the other post-port items (the staged clean-add rows, the
  ledger roll, striking R4).

- **`Idea-100`** · 2026-08-09 · `[bug]` · **groomed → J43** · prio? **High** —
  **The manifest has no way to say "gate-bound" — and that gap nearly shipped an unsigned
  gate's ontology.** The best finding in PORT-REPORT-0d3761a9, caught company-side by their
  own re-check rather than by any guard: their initial vocabulary reconcile ACTIVATED the
  G55 `rua-load-shapes` lineage flips, because K8 (`seal-app-ref-edge-reshape`) *is* signed
  company-side and the files looked takeable. `rua-load-shapes` is a DIFFERENT gate and is
  still unsigned there. They reverted all three vocab fragments; the G23/rua code ported
  inert because it is gate-bound and refuses `planned` labels — so the code's own guard
  caught what the manifest did not. **The rule they wrote down is the one this repo should
  encode: "identical to base" and "per-entry equivalent" are BOTH insufficient tests for a
  gate-bound file.** A producer vocabulary or test file can be byte-identical to the port
  base and still assume an active gate the consumer has not signed — status/id-set parity is
  not field-and-gate parity. Today `PORT-MANIFEST.yaml` expresses disposition (who wins) but
  nothing about PRECONDITION (what must be signed first), so
  `drydocs_core/ontology/relationship_vocabulary/**` carries a disposition that is right
  whenever the gates agree and dangerous exactly when they do not. Shape of the fix: a
  `gate_bound:` key on those rows naming the gate id, and a reconcile-time check that
  refuses to activate an entry whose gate is unsigned on the RECEIVING side. Note the near
  miss honestly — this was caught by a human re-reading their own work, which is not a
  control.

- **`Idea-101`** · 2026-08-09 · `[question]` · **merged → J43 (clause b — the derived-render disposition, decided across every derived row in one pass)** · prio? **Low** —
  **Does the manifest vocabulary need a `derived` disposition?** Raised by the company's
  send-back on the two roadmap rows and deliberately not settled unilaterally. Derived
  renders — `docs/plan/board.html`, `docs/plan/roadmap.html`, the design-doc `.html` — all
  carry `disposition: canonical-company`, which is a poor fit: there is no authored consumer
  content to be canonical about, and the actual instruction in every one of their notes is
  REGENERATE from the reconciled tree. `canonical-company` and "regenerate" differ in a way
  that matters — the first says *keep what you have*, and keeping a stale render is as wrong
  as taking the producer's. The `roadmap.yaml` row had the same class of defect and was a
  clear enough case to fix outright (`evaluate` → `per-entry`, since its note already
  prescribed a deterministic rule); this one is not, because splitting a single row away
  from the board.html precedent would create a worse inconsistency than the imprecision.
  Decide it across all the derived rows at once, or leave it and say why in the manifest.

- **`Idea-102`** · 2026-08-09 · `[question]` · **groomed → K22 (the CI class, via the gate) + K23 (the KB-article thread); merged → G70 (the shared-subject finding for §G13/G14/G15)** · prio? **High** —
  **The deployment grain has an SME-confirmed cardinality and no home — DryDocs has one
  concept where the source has two.** K21 found `u_seal_deployment_id` sitting beside
  `u_seal_application_id` on the CSDM Application Service row (`cmdb_ci_service_discovered`),
  never on `cmdb_ci_business_app`. The SME then confirmed it directly: **one application,
  multiple deployments is correct**, with the identifier reading as
  `app_id(seal_id):deployment_id`. That closes the condition C10's gate-bound candidate #1 was
  deferred on ("only when an environment-level use case lands"). **THE SAME SESSION ALSO SUPPLIED
  THE CAVEAT THAT SHRINKS IT, and the caveat is the more valuable half:** *everything we map is
  off the **application**; modules are referenced by default for changes but in practice are not
  used as intended.* So the grain is ruled — attribution stays on the application,
  `seal-tom-attribution-reshape`'s subject does NOT move, and `:BusinessApplication` is correct
  as-is. What survives is much smaller than it first looked: **capture an identifier the source
  carries and we discard**, not re-home attribution. Worth writing down precisely because the
  expensive reading was the plausible one — this repo's grain corrections (K1/K2, and the
  2026-07-22 move of SEAL attribution from job level to the folder→batch `:Port`) are exactly the
  shape this looked like for about an hour. **What is left.** (1) **The key, and it still
  blocks.** If the deployment id is scoped under the application id, a bare `deployment_id` is
  NOT a business key and a loader keying on it alone MERGEs distinct deployments together — the
  identity-gate §D2 / §C3 failure on a new axis. **UPDATED 2026-08-10 — the SME supplied the CI
  topology and it answers the key question and renames the thing.** The CI class is the
  **Deployment Module**: `Business Application [Instantiates] Deployment Module`, inverse
  `[Instance of]`, and above it `[Contained by] area product`. Each Deployment Module carries its
  OWN unique CI id, so the CI id is the key and `app_id:deployment_id` is the human-readable name
  — which is itself the proof the deployment id is scoped, since a globally unique id would not
  need the application in its name. **"Deployment" and "module" are ONE thing**, which means G35's
  G13 (Deployment Owner), G14 (Deployment Information Owner) and G15 (Application Module Owner)
  plausibly share ONE subject and could resolve together rather than one register line at a time.
  **A CORRECTION THIS ENTRY MUST CARRY, because its first version had it backwards:** the module
  reference being a form default applies to TRANSACTIONAL records — a Change, an Incident or a KB
  article must name a deployment module, ServiceNow defaults it, and people accept the default. The
  Deployment Module CI ITSELF is real, with its own id, its own place in the chain, and KB articles
  attached. So the grain is sound and only the *counting of transactions per module* is not; the
  earlier conclusion that §G15 needed no grain would have discarded a real CI class on the strength
  of a defaulted foreign key. (2) **The label**, if we capture it: C10's standing advice holds —
  adopt the CONCEPT, pick our own stable name, since the vendor's own label moved (Application
  Service → Service Instance at Yokohama), and this instance's own inverse label (`Instance of`)
  already differs from the one public material uses (`Instantiated by`). (3) **A rider on an
  existing gate, not its own gate** — nothing changes an attribution subject. **AND A SEPARATE
  THREAD WORTH ITS OWN ITEM:** KB articles link at Deployment Module grain and the SME called them
  "more meaningful." A documented fix attached to the deployment that has the incident is squarely
  what a production-support knowledge graph is for; it would promote the `kb_*` family from ring 3
  to a real candidate. Check first whether the KB→module link is asserted or defaulted, since the
  defect above would hit it identically. Evidence, and open questions 8 + 9:
  `knowledge/upgrade-plans/servicenow-replica-evidence.md`.

- **`Idea-103`** · 2026-08-10 · `[bug]` · **groomed → J44** · prio? **Low** —
  **Five more unclosed markdown fences live outside the `docs/**` guard, in files this
  repo did not author.** The J41 sweep that found the `port-prompt.md` defect
  (`84ed7e3`, live five days and four ports) scanned all 507 tracked `.md` files and
  found six. One was ours and is fixed (`docs/decisions/0002` carried an orphan trailing
  fence). `tests/unit/test_markdown_fences.py` now guards `docs/**`. The rest were left
  DELIBERATELY, and the reason is the interesting part: `internal/fcdo-reference/`
  CONFLUENCE-TRANSCRIPT.md (opens 5140 of 5355) and TRANSCRIPT-1-ONTOLOGY.md (419 of
  568) are CAPTURED transcripts, and `.claude/skills/data-context-extractor/references/`
  is vendored skill material — editing either to satisfy a guard means editing somebody
  else's capture, which is a provenance decision rather than a formatting one.
  `SDLC-Docs/extracted/issue-driven-capture-loop.md` (181 of 181) is a trailing orphan
  and probably safe. DECIDE: widen the guard with an explicit capture carve-out, or
  leave captures unguarded and say so where the boundary lives.

- **`Idea-106`** · 2026-08-11 · `[bug]` · **groomed → J46** · prio? **Low** —
  **`test_loader_run_log.py::test_naming_convention_and_collision_suffix` is clock-flaky.**
  It calls `claim_log_path()` twice and asserts the second gets the `-2` collision
  suffix — but the suffix only appears when both calls land in the SAME second, since
  the name is stamped `YYYYMMDD-HHMMSS`. If the clock ticks between the two statements
  the second call gets a fresh timestamp and no suffix, and the assertion fails.
  Observed failing once and passing on the immediately following identical run
  (2026-08-11, desktop, during the C30/G67 close-out). Fix: freeze the clock for the
  two calls rather than racing it — the collision behaviour is what is under test, not
  the timestamp.

- **`Idea-107`** · 2026-08-11 · `[bug]` · **groomed → J47** · prio? **Med** —
  **No guard asserts that a `PORT-MANIFEST.yaml` path still exists.**
  Found at G75: the row `drydocs_core/controlm/**` pointed at a path that has not
  existed since the S2 / ADR 0008 relocate under `orchestration/`, so every module in
  the Control-M package was silently falling through to the generic
  `drydocs_core/**` evaluate-on-collision row instead of the canonical-producer row it
  was written for. Nothing failed, because `tests/unit/test_port_manifest.py` checks
  uniqueness, dispositions, notes and pins — never existence.
  `test_runbook_currency.py::test_every_path_a_document_names_exists` already does
  exactly this job for DOCUMENTS, and its FOREIGN_PATHS / HISTORICAL_PATHS escape
  hatches are the right shape here too: a manifest legitimately names company-only
  paths (`drydocs/docmeta/**`, `drydocs/scrapers/**`) and glob rows that match nothing
  producer-side. So the guard is "every non-glob row resolves, every glob row matches
  at least one path, unless allowlisted with a reason".
  Second half, same family: `test_overrides_precede_their_broader_glob` only checks a
  HARDCODED list of four overrides against `config/**`. A new specific row placed after
  its broader glob passes today — verified at G75, where the ordering had to be fixed by
  hand. Derive the pairs instead: any row whose path is a strict prefix-match of a later
  glob row is an ordering defect.
  RENUMBERED AT THE 2026-08-11 GROOM: captured as `Idea-86`, an id the 2026-08-07
  `[source]` entry already held — the second two-session id collision in this file after
  the duplicate `Idea-101` that J41 records. The older entry keeps the id; commit
  `d05811a`'s message is the only surface carrying the short-lived spelling. It also
  landed BELOW the audit trail rather than at the top of the inbox, and its `[guard]`
  tag is not one of the six — both corrected here.


- **GROOM 2026-08-09 (desktop, weekly)** — worked the six 2026-08-08 persona Run-2 captures plus the two `open` chores the 2026-08-07 pm groom left standing. **Promoted 11:** `Idea-91`→U18, `Idea-92`→U19, `Idea-94`(mechanism half)→L27, `Idea-95`(c)→V11, `Idea-85`→**G62/G63/G64/G65** (one item per gate session — the four post-G22 data-profile prompts were drafted 2026-08-07 and had no id, so the pull loop could not see them), `Idea-87`→J40, `Idea-90`→C28 + Q17. **Merged 3:** `Idea-94` and `Idea-95`(a,b) into **L19** (second filing — the sweep never ran and the drift got worse, so L19 was raised p3→p2 and re-stated with Run-2 numbers, and clause (f) now covers the S5 fragment-split re-cites); `Idea-90`’s location findings into **Z2** (mixed grain + the enumerable-site-vs-aggregate-claim line, as required confirmations). **Executed in place 1:** `Idea-93` — fourteen stale `inputs:` corrected directly in `backlog.yaml`; its E1 status question stays open and the entry stays in the inbox, marked. **Parked as a question: 0.** Two HITL-safe drafts, deciding nothing: C28 (business-layer ORG prompt, `status: planned` terms only, sign-off a separate session) and Q17 (a PROPOSED decision record the user rules) — the G27/W1/U16 precedent.

- **`Idea-95`** · 2026-08-08 · `[doc]` · **merged → L19 (clauses a+b, the second filing) + groomed → V11 (clause c, 2026-08-09)** · prio? **Med** —
  **Doc-drift second filings + one new gap** (persona Run 2, U-tw). (a)
  `drydocs_lineage/model.py` still cited by no traceability component — fan-in has
  grown 9 → 24 and it is the G22-reshape fan-out surface (`base.py` DID get its cite,
  so the Run-1 line half-landed). (b) `sdlc-neo4j-schema.md` §DEP: all three Run-1 rows
  still stale, and the vocabulary row is now TWO moves behind (G2 re-home, then the S5
  fragment split); the file gets additive edits (a C23 note landed 08-03) but no
  verification sweeps — regenerate §DEP from the tree. (c) NEW: `drydocs_docmeta`
  (10 modules) has no design doc or runbook — the same growth stage that produced the
  core-runbook after Run 1 flagged drydocs_core.

- **`Idea-94`** · 2026-08-08 · `[doc]` · **merged → L19 (the sweep) + groomed → L27 (the enforcement mechanism, 2026-08-09)** · prio? **High** —
  **Design-doc re-cite sweep, SECOND filing — now with a mechanism ask** (persona Run 2,
  U-tw: `docs/reviews/persona-tech-writer-2026-08.md`). The Run-1 sweep never ran: all
  five pre-squash cites unchanged (`807e050`, `ac2ea2e`, `97ee81c`, `24d6a4b`,
  `0e036ff`); `drydocs-startup-refresh-runbook` reached Rev 10 (seven bumps since
  Run 1) still citing squash-day `a135a6d`; `drydocs-mapping-store-runbook` took two
  bumps on `22d1a39`; `drydocs-mapping-demo-runbook` still has no `commit:` at all;
  `drydocs-project-tdd` was edited 08-06 on a dangling cite. The pattern is behavioral —
  rev bumps happen, cite refreshes don't — so beyond the one-time sweep, add
  enforcement: the design-doc renderer or a unit test should fail on a `commit:` that
  is unreachable from HEAD.

- **`Idea-92`** · 2026-08-08 · `[bug]` · **groomed → U19 (2026-08-09)** · prio? **Med** —
  **Depgraph scanner blind spot: imports rooted off the repo root never resolve**
  (persona Run 2, U-arch F1). `scripts/render_board.py:56-62` imports seven sibling
  scripts by bare name — zero `scripts→scripts` edges in the graph; `agents/` modules
  import `common.*`/`graph_qa.*` against the `agents/` sys.path root — zero
  `agents→agents` edges. Absolute imports from the same files DO resolve, so the U6 fix
  is fine; what is missing is per-directory sys.path roots (or an alias map) in the
  extractor. Until fixed, the 23-item first-party orphan queue is mostly false positives
  and only the package-scope metrics are trustworthy.

- **`Idea-91`** · 2026-08-08 · `[bug]` · **groomed → U18 (2026-08-09)** · prio? **Med** —
  **U14 `$packages` allow-list is missing `drydocs_docmeta`** (persona Run 2, U-arch F4:
  `docs/reviews/persona-python-architect-2026-08.md`). The package was born 2026-08-04
  (`d647171`) — the same day the U14 baselines were measured — and has a MODULE_MAP row
  and a `test_module_boundary.py` entry, but the tech-debt skill's A1–A6 pack and the
  review plan still scope metrics to seven roots, so all 10 docmeta modules are invisible
  to A3/A4/A5. Fix: add the eighth root in both places, re-baseline A3/A5, and note the
  two untested connectors (`connectors/filedrop.py`, `connectors/web.py`) while there.
  Same failure shape as Run 1's `drydocs_api` census miss, one package generation later.

- **`Idea-90`** · 2026-08-08 · `[idea]` · **groomed → Q17 (corpus reshape) + C28 (org-structure gate DRAFT); merged → Z2 (the location grain + claim-vs-site findings) — 2026-08-09** · prio? **Med** —
  **Business-layer location experiment ran (annual report + ORG/location ontology) —
  three decisions queued.** Full write-up:
  `internal/context-graph-analysis/business-layer-location-experiment.md`. The GraphRAG
  search verdict: the `jpmc-reports` corpus is registered (External, `target_db:
  ddcontext`, `:DataAsset`-slice shape, `confirmed: false`) but `ddcontext` is EMPTY on
  the desktop (`neo4jtest`, probed 2026-08-08) and the registered shape is not the
  lexical spine, so no vector retrieval is possible either way. The hand-applied ORG +
  location pass over the public sources produced a coherent business layer regardless:
  org units = the LOB layer verbatim ("managed on an LOB basis"), an effective-dated
  `org:ChangeEvent` (the 2Q2024 segment merge), sites at MIXED grain (street → city →
  country), and a hard epistemic line between an enumerable `org:Site` and an aggregate
  presence claim ("177 locations") that must never be exploded into fake site nodes.
  Queued: (1) the corpus's named P4+ reshape decision now has a real consumer — lexical
  spine vs slice shape, and the newer 2025/2026 editions at the repo root should ride the
  re-ingest; (2) the §3 ORG mappings are gate material (`status: planned` proposals) —
  grain + claim-vs-site findings feed Z2, the org-structure shapes want a business-layer
  gate or E-epic item; (3) any re-ingest gates on the desktop ddcontext provisioning
  check (`Idea-49`). Also proves the Z5 map contract is satisfiable from the business
  layer alone — a located-nodes world map needs no technical layer.

- **`Idea-87`** · 2026-08-07 · `[chore]` · **groomed → J40 (2026-08-09)** · prio? **High** —
  **Company docmeta has diverged and is AHEAD — exactly the class a port silently
  clobbers.** Port A landed on the company side and then moved: their ADR is
  `0005-docmeta-document-ingestion.md` where the producer has docmeta at **ADR 0006**
  (`0006-docmeta-component-and-doc-graph.md`, and producer 0005 is the browser↔Neo4j
  access path — so the numbers COLLIDE with different subjects); their package is
  `drydocs.docmeta` (`drydocs/docmeta/`) where the producer has top-level
  `drydocs_docmeta/`; and they carry `prompts.py` and `pipeline.py`, which the producer
  does not have at all. A straight producer→company port take would overwrite the
  package path, renumber-or-duplicate the ADR, and drop two files that only exist over
  there. Needs a deliberate reconcile decision before the next docmeta port — at
  minimum: which ADR number is canonical on each side, whether the package paths
  converge or stay deliberately divergent with a recorded reason, and whether
  `prompts.py`/`pipeline.py` back-flow to the producer. Relates to `Idea-79`/J34
  (the PORT-MANIFEST company-overlay seam) — same failure mode, different artifact.

- **`Idea-85`** · 2026-08-07 · `[chore]` · **groomed → G62, G63, G64, G65 (2026-08-09 — one item per gate session, as the entry asked)** · prio? **Med** —
  **Backlog ids + scheduling for the four post-G22 data-profile gate prompts**
  (drafted 2026-08-07, unsigned): `rua-bundle-data-profile`,
  `repo-manifest-data-profile`, `dpl-pipeline-registry-contract`,
  `dpl-dataset-registry-contract` in `config/gate-prompts/`. Each has the same
  two-step shape per SME direction: §A HITL identify-the-source-data (Internal)
  → §B agent profiles the existing data → §C rulings. The dpl pair discharges
  T13; repo-manifest is the trusted_ref blessing venue; rua-bundle gates any
  load population beyond the G22-walked bundles. Promote with ids + agent/model
  at next groom; sessions are company-side (real data lives there).


- **GROOM 2026-08-07 (laptop, Q16-session gaps)** — source was the session, not this file, so no inbox line moved; recorded here because the ids are new. **Closed:** `Q16` → `done` as an explicit PARTIAL close (clause (a) shipped at b297268 / 9b4cf59 / 0ddf880; clause (b), the pointer reaching the graph, is NOT done and stays blocked behind Q14, which is behind G32 — said in the close note rather than implied by the status). **Promoted 3, all epic web-console:** `O56` (the `/software` page, groomed `done` — it was BUILT at 9b4cf59 before any item claimed it, so the ledger was carrying an invisible surface), `O57` (a console page for the load-map content no web/ code reads — 28 pipeline sources, 15 systems, 17 retired ids, 17 sequence steps; N5 chose the print surface, so the JSON's console consumer was never scoped), `O58` (a docs-verify surface, `fable` because its transport choice can change the drydocs_api read-path boundary — the sweep is multi-database and a QuerySpec carries exactly one `database:`). **Inboxed 4, none promoted:** `Idea-86` (MWAA corpus, parked on G32 per the user's ruling), `Idea-87` (company docmeta divergence — ADR number AND package path, port-clobber class), `Idea-88` (the undeclared bmc-docs→controlm link; also where Q16's clause (b) lands), `Idea-89` (OverviewRoute renders all modules unfiltered). **Merged 0.**

- **GROOMED TOGETHER 2026-08-07 (pm)** — the OLD OPEN TAIL. The morning groom cleared the fresh Idea-56..84 cohort; this run worked the entries that had been sitting `open` since 2026-07-03 through 2026-08-04, and promoted 15 of them: `Idea-84`→J36, `Idea-54`→J37, `Idea-18`+`Idea-24`+`Idea-26`→**J38** (one item, because the three share a defect rather than content — the inbox is not a channel the other repo reads), `Idea-19`→J39, `Idea-52`→G59, `Idea-20`(c)→G60, `Idea-21`→G61, `Idea-51`→N11, `Idea-43`→D10, `Idea-42`→U16, `Idea-48`→U17, `Idea-55`→O54, `Idea-40`→O55, `Idea-8`→L26, `Idea-1`→R14. Two HITL-safe drafts, not decisions: D10 (the XML-vs-replica precedence prompt) and G61 (the two provenance gap classes) both DRAFT and rule nothing, per the standing G27/W1/N10 precedent. `Idea-41` merged into J34 and `Idea-20` marked partial — both stay in the inbox. Left open on purpose, and named in the groom report: `Idea-73`/`Idea-74` (user decisions blocking O44), `Idea-32` (SME scope call), `Idea-34`/`Idea-33`/`Idea-28`/`Idea-16`/`Idea-17` (SME rulings, user manual steps, destructive ref deletion — none of them a groom's to make).

- **`Idea-84`** · 2026-08-07 · `[bug]` · **groomed → J36 (2026-08-07 pm)** · prio? **Low** —
  **Testcontainers integration tests on this desktop need
  `TESTCONTAINERS_RYUK_DISABLED=true`.** At the G23 e2e build, container startup
  failed with "Port mapping ... port 8080 is not available" for the ryuk reaper —
  reproduced identically on an existing J9 test, so pre-existing environment
  trouble, not the new test. Workaround (remove stale ryuk containers, then set
  the env var) ran the new e2e green in 22s. Decide: pin the env var for this
  machine class (integration-test docs or conftest), or fix the underlying port
  conflict. (Found at the G23 close, desktop, 2026-08-07.)


- **`Idea-55`** · 2026-08-04 · `[idea]` · **groomed → O54 (2026-08-07 pm; the "registry must accept a module path" blocker was checked at the groom and is NOT the blocker)** · prio? **Low** —
  **The load sequence is config-living-in-code and now guarded — it may
  deserve an enforcement-matrix row.** `render_enforcement_matrix.py`'s own docstring calls
  `code_resident` "config living in code, the page's KPI example", and `cli.CANONICAL_LOAD_SEQUENCE`
  (with `LOAD_PROFILES` / `SCHEDULED_INGEST_EXCLUSIONS`) is exactly that — except it now has
  guards, so it would land `enforced` rather than `unguarded`. Blocked on a small design
  question rather than effort: every SURFACES row today has a `file:` under `config/`, so a
  code-resident row needs the registry to accept a module path. (Noticed at N6; deliberately
  NOT done there — the matrix is an O12/admin surface, not N6's scope.)

- **`Idea-54`** · 2026-08-04 · `[bug]` · **groomed → J37 (2026-08-07 pm)** · prio? **Med** —
  **A guard written on one machine had never actually executed on the
  other, and passed by accident when it did.** `test_runbook_currency.py::_cli_verbs` shelled
  out to `drydocs --help` and parsed it. On the laptop that failed twice at once: `text=True`
  decodes with cp1252, which cannot decode the `┐` in Typer's rich box (`0x90`), so `stdout`
  came back `None`; and the rows start with `│`, not `|`, so the pattern would have matched
  nothing anyway — which makes EVERY documented verb look unregistered. Fixed at N6 by
  reading `app.registered_commands` instead of parsing a rendered table. The general question
  worth grooming: how many other guards shell out and parse human-facing output, and is
  "never parse a render when the object is importable" worth writing down as a standard?

- **`Idea-52`** · 2026-08-04 · `[question]` · **groomed → G59 (2026-08-07 pm; the company-side relay was already made)** · prio? **Med** —
  **`apply-supplements` would silently skip the company's two local
  supplements — the exact defect G29 was built to remove.** Producer's chain is the ONE ordered
  list `base -> seal -> catalog -> registry` (+ opt-in sosa) in
  `drydocs_core/schema/supplements.py`. The company additionally runs
  `apply-resource-pools-supplement` (Control-M QUANTITATIVE resource pools, feeds
  `controlm_quantitatives.py`) and `apply-platforms-supplement` (now a documented SUPERSEDED
  no-op, T12) — verified 2026-08-04 that NEITHER verb nor supplement file exists producer-side,
  so they are genuinely company-local, not producer staleness. Consequence: if the company
  adopts `apply-supplements` as its one chain, resource-pools is omitted and whatever MATCHes
  its terms goes quiet — which is precisely how the pre-G29 three-verb block omitted `registry`
  and left `load-software-registry` MATCHing terms nothing had seeded. Relayed as "add your two
  to your own SUPPLEMENTS list before switching". Open producer-side question: should
  `apply-supplements` VERIFY that every supplement file present on disk is in the chain, so a
  local addition cannot be silently skipped? That guard would be portable and would have caught
  this class on either side.

- **`Idea-51`** · 2026-08-04 · `[bug]` · **groomed → N11 (2026-08-07 pm; the divergence half closed with N6 on 2026-08-04)** · prio? **Med** —
  **N6 is now the only thing keeping three load sequences honest, and it is
  ready.** Asked to confirm the load sequence, a check of all three surfaces found them agreeing
  on the shape and disagreeing on membership. `bootstrap-schema-graph` was in BOTH operator
  surfaces (`scripts/ingest.sh` step 3/6, the startup runbook's Appendix B) and missing ONLY from
  `cli.CANONICAL_LOAD_SEQUENCE`, so the generated load-map published 15 steps while both real
  paths ran 16 — FIXED same session (declaration corrected, load-map regenerated at 17). What is
  NOT fixed is why nothing caught it: `test_load_map_declarations.py` checks that every declared
  step is a real command and that every LOADER-backed command is sequenced, but
  `bootstrap-schema-graph` is a schema command, so the completeness check never reaches it — the
  guard is one-directional for non-loader verbs. ingest.sh's own comment already says this block
  and Appendix B "are meant to be the same sequence, not two sequences that drift", which is
  exactly N6's acceptance ("a guard proves they agree"). Remaining divergence for N6 to absorb:
  ingest.sh omits refresh-reference, load-software-registry, load-bmc-docs, load-doc-traceability
  and docs-verify that the runbook and the declaration carry — deliberate for a scheduled
  Control-M ingest, but nothing records that it is deliberate, so it reads identically to drift.

- **`Idea-48`** · 2026-08-02 · `[question]` · **groomed → U17 (2026-08-07 pm)** · prio? **Low** —
  **`DesignDoc.commit` is an author's claim, not a git fact — decide
  whether the writer persona's staleness ranking should use it.** `drydocs-startup-refresh-runbook`
  carries `a135a6d` (2026-07-20, from the doc's own "reflected commit" prose) while the file's
  last touch is `554a4e8` (2026-07-31, Rev 5). Both readings are defensible — "what the author says
  it reflects" vs "when it was edited" — but the plan doesn't say which, so the ranking is undefined.

- **`Idea-43`** · 2026-07-29 · `[question]` · **groomed → D10 (2026-08-07 pm, the gate-prompt DRAFT — the ruling stays the SME's)** · prio? **High** —
  **psgmgr replica vs Control-M XML export: which source wins per
  object when they disagree?** (Guardrail 3 of the XML-fed cmd-line resolution idea → G46/
  G47/G48; the build fills a nullable derived column and decides NO source-of-truth
  question.) Needs a config/precedence.yaml ruling + a named owner-and-sunset for the dual
  definition path (the context-graph dual-ingestion tale's rule of thumb) — e.g. "XML
  export is the definition SoR; the Oracle replica remains the runtime/stats feed", or
  whatever is actually intended. Also touches T16: if XML becomes the standing feed, the
  CM_DEF_VJOB_DETAIL retirement note gains a second path. HITL — user/SME rules this,
  never a groom.

- **`Idea-42`** · 2026-07-28 · `[question]` · **groomed → U16 (2026-08-07 pm, the sizing record — the call stays the user's)** · prio? **Med** —
  **Retire the `depgraph` sibling repo entirely by bringing the SCANNER
  in-house?** The user's reaction to the fork merge was *"I didn't realize it was still used
  after we made it a module"* — and that instinct was half right in a way worth acting on. ADR
  0002-C absorbed depgraph's **lineage** assets into drydocs-core, but the **scanner** never
  moved: `snapshot.ps1` shells out to `../depgraph` every session, which is precisely why a
  months-old sibling checkout could write a 105-edge undercount (→ U7). The whole *class* of
  defect — instrument revision decided by a checkout nobody looks at, capability split across
  branches, `dirty:true` in every meta block — exists only because the tool lives outside this
  repo's history. In-housing it (`drydocs_core/codegraph/`, or a thin vendored package) would
  delete that class outright: one `poetry run` invocation, pinned by `poetry.lock`, versioned
  with the code it measures, no probe needed because the tool and the caller ship together.
  Against: depgraph is deliberately stdlib-only and general-purpose (it scans any project, not
  just this one), it has its own Control-M/RUA/html-review surfaces DryDocs does not use, and
  0002-C consciously chose absorb-the-assets-not-the-tool. So this is a real trade, not a
  cleanup — size it before committing. Precondition now satisfied either way: the fork is
  consolidated (depgraph `5006567`, one branch), so there is a single revision to vendor from.
  KEPT-UPDATED 2026-08-02 (weekly groom) — still the user's call, but the argument moved: **U9
  added a THIRD producer-side post-processing step wrapped around the sibling tool** (git-ignore
  filtering, after U7's capability probe and U8's abs_path strip). None of the three could live
  in depgraph, because each encodes something about THIS repo rather than about scanning — which
  is a point for the fork ("the general instrument stays general") and against it at the same
  time ("the wrapper is now bigger than the seam it wraps"). Worth deciding before a fourth step
  appears. What has NOT changed: no scan capability was missing this time — `main` already
  reported `tree: true`, so the sibling checkout was not the constraint.
- **`Idea-40`** · 2026-07-28 · `[chore]` · **groomed → O55 (2026-08-07 pm; migrate OR record a waiver, both allowed)** · prio? **Med** —
  **react-router high advisory (GHSA-qwww-vcr4-c8h2, RSC-mode CSRF) cannot
  clear without the v7→v8 major migration** — v8 absorbs `react-router-dom` (its latest is
  still 7.18.1, inside the vulnerable 7.12.0–8.2.0 range), so `npm audit fix` is a no-op and
  the fix means rewriting the router imports against `react-router@8.3.0`. Escalated from O34
  per its stop clause (postcss/nanoid patches applied there); a UI-workstream decision, and
  likely moot in practice — the console is a Vite SPA, no RSC actions — but the audit stays
  red until ruled. Pairs with the code-splitting design call O34 also parked.

- **`Idea-26`** · 2026-07-22 · `[chore]` · **groomed → J38 (2026-08-07 pm, with Idea-18 and Idea-24)** · prio? **Low** —
  **Company adoption: route the XML run's WARN flood through the new
  loader run logs (next port).** Producer BUILT the generalized run-log family same day
  (user directive after the first company XML run flooded the console with per-row
  `description_tokens` WARNINGs): `drydocs_core/run_log.py` + `BaseLoader` wiring —
  configurable path (`DRYDOCS_LOGDIR` → `SPIDERP_LOGDIR` fallback → `~/logs/DryDocs`),
  shared naming (`load.<loader>.<stamp>.log`), header/meta from the process, WARN-stream
  tee + uncapped reject detail, summary footer, best-effort contract. When ported,
  company-side should ALSO (a) attach the tee in the XML *extractor* stage (the
  description_tokens flood happens pre-loader, in the adapter), and (b) consider raising
  the console handler to WARNING-summary-only once the stream lands in the file — the
  file is the review surface, the console shows counts.

- **`Idea-24`** · 2026-07-21 · `[chore]` · **groomed → J38 (2026-08-07 pm, with Idea-18 and Idea-26)** · prio? **Low** —
  **Next cross-repo port: carry the AIS acronym expansion across
  files.** Producer's authoritative home is `software-registry.yaml#acronyms`; the company's
  PROVISIONAL gloss sits on their `source-registry.yaml` docs-source entry with a
  PORT-MANIFEST canonical-producer row expecting the producer expansion at next cherrypick —
  different files, so the port must transplant the value, not same-file overwrite. Also
  still open company-side: no 06-29 gate-log entry (their audit gap; backfill offered).

- **`Idea-21`** · 2026-07-21 · `[idea]` · **groomed → G61 (2026-08-07 pm, the provenance gate DRAFT)** · prio? **Med** —
  **FW-really-API confirmed live** — the greenfield-provenance use case
  for the fix module: a file-watcher-shaped job's `.tok` is produced by an UPSTREAM API-call
  job writing the file locally, no external push exists — the name/type lies. Already
  codified as the `_FW`-really-API anti-pattern + design principle 8 (intent from resolved
  flow, flag name-token disagreement) in
  `internal/remediation/governance/nfr-consistency-and-greenfield.md`; the description-field
  metadata plan is the declared-provenance carrier. Two NEW provenance gap classes from the
  live case: (a) payload script deployed on the exec host but ABSENT from SCM (code search
  finds only the XML variable reference) → *artifact-not-in-SCM* flag on :Script; (b)
  pipeline-id-keyed code discovery has NO key for non-DPL python jobs → PATH-keyed Script
  identity is the fallback, and the GUID-vs-path boundary is the kind discriminator.
- **`Idea-19`** · 2026-07-21 · `[idea]` · **groomed → J39 (2026-08-07 pm)** · prio? **Med** —
  **Back-flow the company's un-back-flowed advances (bd7952f follow-up 3).**
  The 2026-07-20 bundle port went bidirectional (+288 producer / +148 company) precisely
  because these never came back; reproduce mechanism-only via the screenshot/describe
  channel: snow-support schema supplements (`hpsm_queue_key`/`sn_group_name` constraint
  pair + a `snow-snowflake-itsm` source stub), the `drydocs_remediation` DPL-watch-drift
  rule + tests (pairs with the DPL runtime-trace inbox entry below), the `graph_verify`
  Assertion refactor, the docgen deviations vs the finalized company TDD, the
  `CONFLUENCE_BASE_URL` config seam (mechanism: base-URL as config; the value stays
  company-side), and the `controlm_folders.sql` `J` table alias. Ties into the
  drydocs-review back-flow epic. Until these land, every future port repeats the
  squash-reconcile instead of a clean linear apply.

- **`Idea-18`** · 2026-07-21 · `[chore]` · **groomed → J38 (2026-08-07 pm, with Idea-24 and Idea-26; every relay is RE-VERIFIED before it is written down)** · prio? **Low** —
  **Company-side heads-ups from the port-report gap review** (their
  tracker — recorded here so they aren't lost; relay next company session): (a) the
  `test_schema_graph.py` drift-guard sequencing conflict — see the new reconcile-port
  skill ledger note (re-add only after their doc-vocab gate); (b) confirm
  `docs/restructure/internal-backlog.yaml` was deleted after the DD-series merge
  (bd7952f follow-up 2 — 388a30d shows the merge happened, not the deletion); (c) the
  company is producer commits behind past `7e8df54` (L7 gate sign-off + live loader,
  G14 lineage file-ops pass, the hermetic oracle-kerberos test fix that retires the
  standing known-failure note, DPL inbox, port-gap fixes) — **and their tooling can't
  see it**: the 07-21 company-side "identify unported commits" search concluded "fully
  ported, nothing outstanding" from a FROZEN `cewilson/main` ref (`git fetch cewilson`
  404s company-side; likely the stale pre-rename remote URL — the live repo is
  `https://github.com/ce-wilson/DryDocs.git`, pushed 07-21). First company action:
  `git remote set-url` + re-auth, re-fetch, then re-run their own re-verify
  (`git log <last-ported>..cewilson/main`). Silver lining from that search: the L7
  port branch IS merged to company main (`373e993`→`c8cf9f0`), closing the
  "NOT merged" state in 5eba0c3, and the historical port reports (0eb1a8d, aa049d3,
  e6f8cca, e418258, eeaffa2, f7970e5) all exist as files company-side.

- **`Idea-8`** · 2026-07-12 · `[doc]` · **groomed → L26 (2026-08-07 pm; the Epic L outline half deliberately excluded)** · prio? **Low** —
  **/documentation skill has NO white-paper guideline** (types: README, API,
  runbook, architecture, onboarding). Wrote docs/whitepaper/drydocs-whitepaper.md deriving
  structure from the architecture-doc type + white-paper conventions; if white papers recur,
  add a "White paper" type to the skill (exec summary → problem → approach → architecture →
  governance → roadmap) and consider an Epic L outline for it (whitepaper.outline.yaml).

- **`Idea-1`** · 2026-07-03 · `[chore]` · **groomed → R14 (2026-08-07 pm)** · prio? **Low** —
  `common/` shows up in ADK `/list-apps` (it's a shared-tools package, not
  an app). Cosmetic; hide or restructure later.

- **GROOMED TOGETHER 2026-08-07** (user instruction): `Idea-80` + `Idea-82` produced **G58** (the dead-script archival report — three dispositions, a stated coverage precondition, the already-archived count) and **L24** (state the target state as a goal in the executive overview). One report item rather than two because both entries turn on the SAME argument: an absence observed by one feed is not an absence in the world. The one fragment NOT made an item — what to CALL the estate-level end state — rides G58's notes as a question the build surfaces, because nothing needs a formal term yet.

- **`Idea-82`** · 2026-08-07 · `[idea]` · **groomed → G58 + L24 (2026-08-07, same day as capture)** · prio? **Med** —
  **Name the estate-level TARGET STATE: "the production server holds only actively
  used code" — and carry it into the executive overview as a stated goal.** User
  direction, 2026-08-07, in the question that closed the G22 sign-off session.
  **THE GAP:** DryDocs can already name every ARTIFACT-level state involved, but has
  no name for the ESTATE-level condition they add up to. Artifact side is covered:
  a tombstone (`removed_from_source_at`, the D7 sweep ruled at U13) is the existing
  word for *was here, isn't now, history kept*, and after G22 §D2 the `:Script` case
  needs no new flag at all — it falls out of the occurrence shape (code-repo
  occurrence + no current server-extract occurrence = archived; server occurrence +
  no repo occurrence = G24's existing `never_committed` bucket). That keeps
  "archived" DERIVED FROM EVIDENCE rather than declared, the same move §G1 made when
  it put identity in the business key and made the URN a render. What has no name is
  the goal: an estate where the two sets have converged.
  **WHY IT IS NOT A LABEL CHOICE:** the state is a property of the ESTATE, not of any
  node, so it is a real vocabulary decision and rides the HITL gate rather than being
  picked at a groom. Do NOT reach for the `00-header.yaml` lifecycle
  (`planned|active|deprecated|removed`) — that enum governs relationship-vocabulary
  ENTRIES (edge meanings, i.e. schema), and a script on a server is an INSTANCE.
  Reusing the four words for both would put `removed` = "we deleted an edge
  definition" and `removed` = "we deleted a file off a server" in one repo: the exact
  two-things-one-spelling collision §A2 caught on `group` and J32 made a standing rule.
  **THE PRECONDITION THAT MUST RIDE ANY WORK HERE (§H1):** absence of a server
  occurrence is NOT proof of removal. All three usage axes are positive-only, and
  present-on-server is bounded by `scan_roots`, so "not in the bundle" only ever means
  "not observed by that feed". A tombstone must therefore be set from a SWEEP-SCOPED
  absence — within roots actually scanned, on a bundle that actually parsed — or a
  collector that skipped a mount tombstones live code. Since §E3's use case is
  DELETION, that false positive deletes something running. §E3's three dispositions
  stay distinct for the same reason: genuinely dead (archive and remove), misdeployed
  (relocate, never delete), unreferenced-but-dynamically-called (keep).
  **THE SECOND HALF OF THE ASK — the executive overview.** The user asked for this to
  appear in `docs/overview/drydocs-executive-overview.html` as a stated **target-state
  goal**, not only as a backlog item. Two things a groomer needs to know before
  touching it: (1) that file is **hand-authored HTML and its own SINGLE SOURCE** —
  there is NO `.md` twin (unlike `docs/whitepaper/`), it is not renderer output, and
  `render_design_doc.py` does not cover `docs/overview/`, so it is edited directly;
  (2) it is a **non-governed outward-facing doc** (CLAUDE.md §6), so editorial and
  design treatment DO apply there — the publish-VERBATIM rule binds the design
  renders, gate pages and the board, not this file. Nearest existing homes are "The
  loop that makes it a system, not an inventory" (the operational-outcome section) and
  "Honest about the gaps"; there is no target-state section today.
  **RELATED:** §E3 (the archival/removal use case and its three dispositions), G23
  (curated rua load), Idea-80 (dead-script report coverage precondition — same
  coverage argument, and these two should probably groom together).

- **`Idea-80`** · 2026-08-06 · `[idea]` · **groomed → G58 (2026-08-07, once G22 signed as its own status line required)** · prio? **High** —
  **The dead-script report drives DELETION, so it needs a coverage precondition and
  three dispositions, not two.** G22 §E3 named the use case: identifying unused,
  deprecated code for archival and removal. That raises the bar on the report the
  usage axis feeds. (a) **Body-copy coverage is a precondition, not a footnote** —
  script-to-script invocation is visible only where the bundle carried the script
  BODY, and the metadata-only listings ship none, so on those bundles
  "unreferenced" means "no CMD_LINE reference", never "nothing calls it"; a report
  that omits its coverage will propose deleting leaf scripts it was structurally
  unable to see callers for. (b) **Three dispositions** — genuinely dead (remove),
  MISDEPLOYED (relocate; §E1's caveat that a script may have been deployed to the
  wrong server), and unreferenced-but-dynamically-called (keep). (c) The
  misdeployment case is only valid where `storage_scope` is local — under shared
  storage every host sees one file. *(From the G22 §E session, laptop.)*

- **`Idea-78`** · 2026-08-06 · `[feature]` · **groomed → O45–O51 (2026-08-06, same day as capture)** · prio? **High** —
  **SME Context-Intake page: the front door for the unstructured email corpus
  (the Q10 "SME assignment surface"), planned end-to-end.** User direction
  in-session; full plan at `UI-WIP/sme-intake-page-plan.md`. Seven sections top
  to bottom: PAT + SEAL area cascade (hint channel, "unknown" first-class) →
  context-type dropdown from a NEW `config/taxonomy/context-types.yaml`
  (job-failure, missed-data-load, missed-file, data-issue — growing, taxonomy
  layer so growth is not a gate) → drag-drop upload for .msg + Copilot .json
  pairs (.txt TBD; data-root staging, Internal stamp, sha256, never the repo) →
  FCDO-style "review for ontology" pass (proposed bindings, SME confirms) →
  read-only related-nodes QuerySpec over the structured graph → ADK agent
  first-pass correlation (accept / modify / stay-unassigned) → confirm into the
  O24 origin-flagged store (`origin: sme-intake`) and an ADMIN review queue.
  Nothing writes the graph: corpus load waits on Q10←G31←G32, the assignment
  edge is gate-registered `planned` per Q10's own acceptance; admin-accepted
  records park on a "waiting on gate" chip. Seven proposed build slices
  (O45–O51 indicative) + open questions are in the plan. *(Grooming: the
  console slices join Epic O; Q10 keeps the corpus/load half.)* AMENDED
  same day (user): §8 **reviewer-quality signal + admin block** — per-SME
  auto-accept rate / too-fast rate / admin-return rate over a rolling window,
  limits in `config/review-quality.yaml`; crossing a limit FLAGS the SME on
  the admin queue's quality rail, and the admin (never the machine) can block
  the persona from submitting — reversible, recorded who/when/why. The user
  recalled a backlog item ranking auto-acceptance to flag poor-quality work;
  searched 2026-08-06 — no such item exists in backlog/IDEAS/gates/history
  (possibly company-side drydocs-review), so this entry is now that
  requirement's home.

- 2026-08-05 (desktop, user directive: number the inbox, add status + priority, and
  "extend or supplement existing backlog items with the ideas… I don't want every idea
  moved, but they do need to be reviewed again") — **all 69 inbox entries reviewed and
  headered.** Ids assigned in CAPTURE order (`Idea-1` oldest, `Idea-69` newest), so a new
  capture at the top never renumbers anything below it. Three entries SPLIT because their
  halves had different dispositions, which is the only reason to split: `Idea-63a` (the
  cardinality question — answered, closed) vs `63b` (the `descr` review queue — unbuilt,
  merged into K18); `Idea-30a` (design the PDN trigger) vs `30b` (audit the deadline of the
  BIM job that already exists).
  **Outcome of the review — the point of it was NOT to promote everything.** 3 promoted
  (**K18** derive the tier from the folder name + give the store a platform-declaration row
  kind; **K19** app-code mapping as an as-of assertion, reuse detection; **J32** write down
  the registration/routing/attribution rule). 5 MERGED into items that already exist, which
  is the disposition this pass was really for — **J13** absorbed the platform-vocabulary
  ruling (`Idea-38`: it is the same user-gated decision J13 already waits on, now with four
  value classes named), **C25** absorbed the two missing software-registry product rows
  (`Idea-65`) as a prerequisite, **G34** absorbed the acronym-catalog CONTENT shape
  (`Idea-35`) into its scaffold, and `Idea-68`/`Idea-63b` ride K18 as clauses. The rest
  carry a status and a proposed priority and STAY here: 22 `parked` with a named trigger,
  28 `open`, 3 `closed`. (71 headers over 69 ids — the two splits account for the difference.)
  Every priority carries a trailing `*` — proposed by the agent, not confirmed by the user.
  Clearing the star is the review pass this file now supports and could not before.

- 2026-08-05 (desktop, user directive "groom them into backlog items") — the two HITL gates
  drafted the same day → **C25** (run the `software-version-context` gate — epic
  ontology-mapping, phase 2, beside its C12/C14 USES_SOFTWARE siblings) and **K17** (run the
  `fid-identity-and-scope` gate — epic seal-attribution, phase 9, the K2 tier-2 unblock),
  plus **K16** (the doc-09 Phase-0 FID census). K17 depends on K16 BY DESIGN: the census
  produces the §Q0 disagreement breakdown the gate cannot sign without, so grooming the gate
  alone would have scheduled a session that cannot reach a ruling. Both gates were already
  documented as artifacts — committed prompts, `status: open` rows in `gates.json`, format
  guard passing — but had NO backlog item, so `unblocks: []` and nothing would ever pull
  them. That gap is what this groom closes. The IDEAS entries themselves STAY in the inbox
  (they carry findings wider than the gates: the app-code cardinality question, the
  registration/routing/attribution rule, the sub-application USES_SOFTWARE source, the
  tier-naming split) — only the gate-session work was promoted.
- 2026-08-04 (desktop, user directive) — [idea] the backlog-sharding EPIC entry (2026-08-03;
  kept-parked at the same day's weekly groom) → **UN-PARKED and groomed as Epic Y: Y1 the
  sharding ADR ruling session, Y2 the shard build, Y3 the :BacklogItem/DEPENDS_ON vocabulary
  via the gate, Y4 the query surface.** Phase 1's guard had already shipped (`c5b689e`, port
  step 55) and stays outside the epic. The park condition travels with Y2 as a prose
  precondition (in-flight port PORT-REPORT review first). Fresh exhibit recorded at the groom:
  the three same-afternoon roll-up rebase conflicts of 2026-08-04 (X1-claim/V8, X2-close/V2,
  X3-close/V3), all in the stored summary/next_ready block Y2 derives away.

- 2026-08-04 (session close, laptop) — [question] "nothing compares the checkout against
  `expected_commit`" → **RULED AND BUILT SAME SESSION (user: "warn in snapshot.ps1"), no
  backlog id.** `snapshot.ps1` now reads the pin, compares against the revision it records
  (`$depFull`, not a fresh HEAD), and warns with a drift classification that says what to do:
  *ahead* → the pin is the stale side, bump it; *behind* → this scan is stale and not
  comparable, `pull --ff-only`; *diverged* → the fork shape behind the 105-edge undercount,
  resolve first; *unknown* → the pinned commit is absent, fetch. An explicit "currency
  UNCHECKED" warning fires when the pin cannot be read, so a silent no-op is never mistaken
  for a clean check. WARN and not refuse was the ruled point: a sibling ahead of the pin is
  how a bump starts, so refusing would block the fix. All six paths exercised by executing
  the block extracted from the real file against synthetic states.
  Two defects found while building it, both worth remembering. (1) The classifier first
  compared against a fresh `HEAD` rather than the captured `$depFull` — identical in a normal
  run, so only the test matrix caught it, and it misreported *behind* as *ahead*, the one
  direction that matters. (2) The advice strings were first written with em dashes and BROKE
  THE SCRIPT: the file is UTF-8 without a BOM, PS 5.1 therefore decodes it as CP1252, and a
  UTF-8 em dash arrives ending in a smart quote that PowerShell honours as a string
  delimiter — the string closed early and the whole file failed to parse (confirmed with
  `Parser::ParseFile` on the real file). Em dashes in comments and here-strings are harmless
  and stay. A repo-wide guard now reds on non-ASCII inside a single-line quoted string in any
  BOM-less `.ps1`, proven red on a probe before being kept. Note J29's encoding standard
  covers `.cypher`/`.sql`/`.csv` and deliberately not `.ps1`, so this is a neighbouring rule,
  not a J29 gap. Also removed: the capability refusal's hardcoded `depgraph 5006567`, stale
  since the morning's bump — it quotes the configured pin now.

- 2026-08-04 (session close, laptop) — [bug]×2 the instrument-drift pair → **BOTH RESOLVED
  SAME SESSION on user direction ("pull the depgraph sibling and bump the pin"), no backlog
  id.** (a) Sibling fast-forwarded 5006567 → 773fb1e (clean descendant: `9c663ca` RUA
  inventory ingestion + script-op analyzer, then the merge), `expected_commit` bumped, probe
  re-run the way `snapshot.ps1` runs it (PYTHONPATH=. inside the sibling — a bare run from
  the DryDocs venv reports everything false and is NOT a valid probe) → importable,
  multi_root, tree all true. (b) The dead-SHA snapshot header is gone: the re-run replaced
  `drydocs-20260804.json` (which cited the rewritten-away `63adc2b`) with
  `drydocs-20260804-1548.json` at the live `299af39`.
  **One claim in the original entry was WRONG and the correction is worth keeping:** it said
  scanning from the stale revision "would emit a snapshot missing three relationship types".
  Measured after the bump, that is false for this repo — DryDocs scans emit exactly ONE
  relationship type, CONTAINS (1772), with TRANSFERS and RUNS_ON at zero in both the old and
  new snapshots and an identical 526 edges. Those types come from depgraph's Control-M / RUA
  lineage extractors, which a Python-tree scan never exercises. The bump was still right —
  two machines on different instruments cannot be compared, and the pin named a revision main
  had moved past — but the justification was comparability and currency, not lost output. The
  inferred consequence had been stated as fact without measuring it. Lesson recorded in the
  config comment: treat a REL_TYPES change as a reason to re-measure, not as proof of an
  undercount. Residual (the missing DETECTION) re-inboxed as a [question].

- 2026-08-04 (weekly groom, laptop) — [bug] `provision.ps1` shells out to host-PATH
  `cypher-shell` → **G54**. Verified at the groom: the REQUIRES block (`:6`) presents host
  cypher-shell as satisfied by "bundled in the Neo4j Docker image", but the runner (`:57`)
  invokes the bare binary, which a Docker-only host does not have. Acceptance forces one of
  two resolutions (exec-aware script preferred over a header-only fix) and carries the J29
  PS 5.1 trap into the header, since the workaround shape and the encoding standard are one
  lesson. The BOM half of the report was already resolved by J29 and is recorded as wrong.
- 2026-08-04 (weekly groom, laptop) — [bug] the two catalog loaders C22's file set excluded
  → **C24**. Verified statically: `catalog_lobs.cypher:28-29` blanks TODAY (CatalogLOBRow's
  code/name are already Optional), while `dev_teams.cypher:16` is the latent whole-row-reject
  case (DevTeamRow.name is required) — so they fail differently and C22's row-model half has
  to move with the Cypher half. Depends on C22 (done), so it enters next_ready.
- 2026-08-04 (weekly groom, laptop) — [chore] branch `wip/k9-laptop` → **J30 + J31**, split
  deliberately. J30 is the one-off disposition (per-file comparison, lift what is worth
  keeping, then delete local and remote with the tip SHA in the close note); J31 is the rule
  the collision exposed — the pull rule makes the CLAIM visible but not the WORK, so a
  session that dies looks identical to one that never started. J31 extends J19's pushed-claim
  discipline rather than proposing a new direction, which is why it is a chore and not a gate
  item; its wording is confirmed with the user at build. Second occurrence of the C19 class,
  and the two failed differently — C19 was two unclaimed sessions, K9 was a pushed claim that
  went dark while the work existed locally.
- 2026-08-04 (weekly groom, laptop) — [chore] `reference/REGISTRY.yaml`'s dcat `docs:` path
  resolves to nothing → **A4**. Verified: no `reference/standards/dcat/` directory exists.
  Two allowed resolutions (write the dcmi-terms-pattern stub, or re-point at the standards
  README like skos), the choice recorded in the close note; rides A1's registry-path audit if
  that is picked up first.
- 2026-08-04 (weekly groom, laptop) — [idea] the `controlm-runbook-automation-SDLC` skill →
  **L23**. Promoted rather than parked because it is not a speculative shape: the shipped
  `-excel` skill's own frontmatter already names "a future -SDLC sibling", and the doc type,
  worked example and outline tests all landed at `995eb9a`. Acceptance keys on the validation
  that already exists (a generated doc validates against the outline unedited) and forbids
  re-writing queries the `-excel` skill owns — two skills disagreeing about the same runbook
  fact is the failure it exists to prevent. Filed under Epic L: the outline system lives
  there, and this is a doc GENERATOR, distinct from drydocs-docmeta which ingests.
- 2026-08-04 (weekly groom, laptop) — [doc] `sdlc-neo4j-schema.md`'s stale HAS_APPLICATION
  loader-inventory row → **MERGED into L19** as clause (e), no new item. The line's own
  instruction was "fix it in the stream that owns that doc, not piecemeal", and L19 is
  already the doc-drift sweep over `docs/reviews/sdlc-*.md`. Verified both halves: `:553`
  still carries the claim, `pat_product_mapping.cypher:39` says C9 removed the write in
  2026-07-18. Restated to the K13 support reading so the correction lands once.
- 2026-08-04 (weekly groom, laptop) — two entries KEPT PARKED with triggers re-checked and
  NOT fired: the **controlm-pipeline-stub** twins (capture files present, but no internal
  build has landed, and epic placement is explicitly a user call at that groom) and the
  **desktop venue divergence** (a user ruling either way; the laptop was verified on the
  pinned 2026.05.0 with `ddschema` present, so the drift is desktop-only — and the groom
  noted that nothing currently detects a running server's version against the pinned one).

- 2026-08-04 (Control-M groom) — [chore] the legacy /mappings job-application pane (coverage
  grid + assign flow still on the retired job-grain edge, found at K11) → **K15** (type bug —
  the surface actively misreports; retire-or-re-bind, direction confirmed with the user at
  build).
- 2026-08-04 (Control-M groom) — [idea] the 2026-07-14 ctlm_id ripple → **CONSUMED**: (1) the
  which-other-CM_-views census is internal-side (docs/next-internal-session.md item 4, needs
  Oracle — K14's notes keep it separate on purpose); (2) the K2 manual-CSV `ctlm_id=` shorthand
  is moot — K9 rekeyed the template to app_code; (3) company-side alignment rides port step 62
  (the composite-key-serialization standard, ctlm_id dot form ruled 2026-08-03).
- 2026-08-04 (weekly groom) — [bug] review-plan seed queries missing the D7 tombstone filter
  → **U13** (the A3 dead-`__init__.py` ranking is the proof case; fix the query pack, not the
  sweep).
- 2026-08-04 (weekly groom) — [bug] 63 vendored `.claude/skills` scripts polluting the
  architect-persona metrics → **U14**. Fix placed in the QUERIES (region allow-list), not the
  scan — the U9 whole-tree shape is the ruled intent; the metrics mis-scope it.
- 2026-08-04 (weekly groom) — [chore] the G51-tail retrospective close → **MERGED into J26** as
  the second family instance (promise-vs-assertion: `test_databases_match_provisioning_script`
  docstring promised equality, asserted subset; made bidirectional at `aa0a0eb` and failed on
  `['ddschema']` before the config fix). Both company consequences were ALREADY ledgered before
  this groom: port-prompt step 59 carries the schema_meta caution verbatim, and the standing
  divergences carry the Rev 5 rev-pin note — no tracker row owed.
- 2026-08-04 (weekly groom) — [question] composite-key grammar → **RESOLVED + BUILT 2026-08-03**
  (two SME rulings: ctlm_id dot composite is THE value form; key-cell pairs join with `:` not
  `;`). Standard = `knowledge/standards/technology/composite-key-serialization.md`; `_parse_key`
  flipped in the free migration window; the value-form sweep is **K14**; port step 62 carries
  the company T4 caution.
- 2026-08-04 (weekly groom) — [idea] the 2026-07-27 SME orchestrator-mapping act → **RESOLVED by
  the K7 sign-off (24/24, 2026-08-03)**: §G ruled all seven confirmations; the cascade screen is
  **K11**, the `catalog_has_application` back-flow (§G6's company SUPPORT reading) is **K13**,
  the C14 prefill demotion is §G2, and the folder-availability question is answered in K11's
  acceptance (unmapped-only, naming-pattern optional). The `:Batch` bridge RETIRED at the gate.
- 2026-08-04 (weekly groom) — [idea] the 2026-07-22 defined-mapping mega-entry (grain correction,
  two-tier app-code model, K2 demotion, property-diet rider) → **RESOLVED by the K7 sign-off +
  the K9 build**: folder grain (§A), tiers seal-born/platform/dual-coded (§B2), origin flags
  (§B3), store = source of record (§E2); the loader half is **K8**, the taxonomy capture **K12**.
  Residue re-inboxed slim: the tier-2 platform-code enumeration (SME data entry, no item).
- 2026-08-04 (weekly groom) — [idea] the 2026-07-21 two-pattern code→app model → **RESOLVED by
  the K7 sign-off**: the "GATE DECISION core" it parked (authoritative code→app edge +
  platform-code marker) IS the ruled `BELONGS_TO_APPLICATION` folder-grain edge authored per
  app code with the tier column as the marker. The read-only explorer spec stands unchanged.
- 2026-08-04 (weekly groom) — [idea] the backlog-sharding EPIC proposal → **KEPT PARKED by user
  ruling at this groom** (phases 2–3 are a cross-repo plan change; re-time after the in-flight
  port's PORT-REPORT lands). Entry stays in the inbox with the ruling annotated.

- 2026-08-03 — [feedback] U.S. business-English instruction set (user, in-chat, after "spine"
  in the exec overview failed with its own audience) → guide committed as
  `docs/style/us-business-english.md` + **L22** (wire it in, rewrite the overview, inventory
  idioms, mechanism-name fence).

- 2026-08-03 — [question] "what's upstream of :Metric?" (user, in-chat, minutes after the
  manual graph wipe — the DQV seed's IN_DIMENSION query was the one thing worth asking about
  what was just deleted) → **C23**: the quality seed floats — no measurement writer, no
  vocabulary entries; rule build/defer/prune via the gate.

- 2026-08-02 (weekly groom) — [source→Q6] the company-side fetcher shape → **MERGED into Q6's
  acceptance**, not a new item: acquisition-only connectors over a `Connector` protocol, `web`
  with an INJECTABLE TRANSPORT and an SSRF scheme allow-list, `filedrop` over pathlib. Both
  guarantees written in as non-negotiable — the transport injection is what makes Q6's Track-1
  offline tests real, and the allow-list is the guardrail Q12 exists to enforce. Unblocks Q6, R7
  (released unbuilt 2026-08-01 for exactly this missing fetcher) and Q12 behind it. The line's
  own caution was honoured: the realm is described, never named.
- 2026-08-02 (weekly groom) — [chore→L19] two governed design docs falsified by the S3 identity
  cutover → **MERGED into L19 as acceptance clause (d)** (web-console-tdd's "columns verbatim",
  controlm-ingestion-tdd's `Application.seal_id` stale on both halves), with the
  deliberately-untouched mapping-store COLUMNS named so a later sweep does not "fix" them.
- 2026-08-02 (weekly groom) — [chore] guards that read committed text with a bare substring match
  → **J26**. The instance (test_constraint_count counting `CREATE CONSTRAINT` inside a comment)
  was already fixed in S3; the item owns the CLASS, and the groom found a live second member —
  see G51.
- 2026-08-02 (weekly groom) — [chore] `.gitignore` names the real org and internal domain in two
  comments → **J27**. Promoted rather than parked as a decision: CLAUDE.md §3 already bans real
  org names outside `internal/`, so the default branch is REWORD and the item applies an existing
  rule; the "record the exception in PUBLISH-BOUNDARY.md" branch stays available because the
  boundary is the user's to set.
- 2026-08-02 (weekly groom) — [bug] silent parent joins in the catalog loaders + the [source]
  line's unconditional `SET name = row.name` → **C22**, two lines into one sweep because they
  land on the same files (the L19 precedent). Verified at the groom: the blanking SET is in
  `products.cypher` as well, so C22 covers three loaders, not the two the inbox named. The
  [source] line's three back-flow candidates stay parked on the company gate's sign-off.
- 2026-08-02 (weekly groom) — [question] "How much depgraph audit history do we keep?" (review
  finding F11, open since 2026-07-25) → **RESOLVED by the SME and already executed; no item.**
  Direction 2026-08-02: "the old dep snapshots can be removed this was the intent", retention =
  newest all-files snapshot only. Applied at `e3f65af`: 105 files removed (101 dated, 2
  `drydocs1-*`, 2 tree one-offs), one kept, all recoverable from history. Nothing in code
  referenced a snapshot by name (checked before deleting). Two halves of the question stay open
  as **U12**: the README still documents a prune-to-ten rule and cites two of the deleted files,
  and `snapshot.ps1` still writes `<project>-<date>-<HHmm>.json` when a snapshot already exists
  for today — so the ruling holds only until the next double-run. A rule enforced by whoever
  remembers it is the shape U9 just deleted.
- 2026-08-02 (weekly groom) — **raised AT the groom, not from the inbox** (the skill's optional
  graph/code cross-check, run as a code cross-check): three follow-ons from the self-doc session
  plus one defect it left behind. **U9** + **C21** groomed RETROSPECTIVELY as done — that work
  landed at `e3f65af` before any item existed, and three committed files already cite "U9" as an
  id nothing defined. **U10** = the code-graph package-layer GATE SESSION (drafted 2026-08-02,
  unsigned; its own §I is what opens the build item, so none was groomed ahead of it). **U11** =
  draft the second gate prompt, the `.py → .cypher → :Label` chain the parent gate deferred at
  §H5 — possible only now, because .cypher files became graph nodes for the first time at U9.
  **G51** = the defect: `drydocs bootstrap-schema-graph` targets a database that
  `01_databases.cypher` does not create, so it works only on the machine where it was made by
  hand — and `test_database_names.py`, the guard written for exactly this drift, missed it
  because it keys on the identifier `DATABASE` and the constant is called
  `SCHEMA_GRAPH_DATABASE`. Same family as J26.

- 2026-07-31 (pm, weekly groom — run AFTER the N7 gate + N9 build closed the registry-v2
  work) — [chore] T11 L7-ratification paste-ready snippet still owed producer-side →
  **J25**. Verified genuinely owed before promoting: `docs/port-prompt.md` §6 states the
  four elements a Tier-A ratification entry must carry and records that the snippet was
  "provided in the producer session 2026-07-21", but a repo-wide search for `0252d29` /
  `PORT-REPORT-6fd3270` finds prose references only — the block itself was never
  committed, so the company gate pack cites an artifact no company session can open, and
  tracker T11 has read `pending` since. J25 is producer-side AUTHORING only; the entry
  lands in the company gate-log at their next port and their sign-off stays theirs.
- 2026-07-31 (pm, weekly groom) — [doc] Runbook Rev 3 candidate: mention
  `drydocs load-doc-traceability` in the Refresh/ingest step → **MERGED into L21**
  (Runbook Rev 4) as an acceptance clause. The line parked itself explicitly to "ride the
  next feedback loop rather than bump a fresh Rev for one line", and L21 IS that revision
  — so it became a clause, not an item.
- 2026-07-31 (pm, weekly groom) — [new, raised AT the groom] **J23's own residual: the
  retired `Internal-Confidential` tier survives in FORWARD-LOOKING specs** → **J24**.
  J23 collapsed the vocabulary to three levels the same morning and correctly scoped
  itself to config + the boundary docs + the two tests, leaving history alone. The sweep
  found the token still live in surfaces that are neither config nor history but
  *instructions for assigning a tier*: `UI-WIP/site-plan.md`'s classification union type
  (a TypeScript enum in waiting) and its banner rule, `wf-admin-config-01.md`, two skill
  reference tables that ROUTE material by tier (`data-context-extractor/references/
  platforms.md`, `controlm-runbook-automation/references/fix-package.md`), and the
  `bmc-docs-example.yaml` gate-prompt template. Left as history and named so in J24:
  `config/gate-log.md`, signed-off gate prompts, `done` backlog close-notes,
  `SDLC-Docs/extracted/`, this audit trail. J24 also adds a regression guard to
  `test_classification.py` scoped by an explicit file list, so history can never be swept
  in by accident.
- 2026-07-31 (pm, weekly groom) — [database fix, no item] **M3's acceptance still failed
  its own vocabulary**: it required column mappings "authored in the internal twin —
  Internal-Confidential never lands producer-side", naming a tier retired hours earlier.
  Fixed inline at the groom (now: "Internal, and confidential-handling, so never
  producer-side") rather than deferred into J24 — a `todo` item whose pass/fail test
  cites a dead enum value is exactly what grooming exists to prevent. Deliberately kept
  OUT of J24's scope so each surface has one owner.

- 2026-07-31 — [chore] classification collapse to 3 levels (registry-plan Phase 1; user
  ruling same day, pre-decided) → **J23** (may land ahead of the N7 gate — removes
  machinery, adds none).
- 2026-07-31 — [idea] registry-plan directive captured → **MERGED into N7** same day
  (`2d6f705`: inputs + notes point at `internal/registry-redesign/REGISTRY-PLAN.md`;
  samples re-homed, J22 guard failure cleared). No new item.
- 2026-07-31 — [idea] FCDO ontology crosswalk Phases 1–3 → new **Epic W**
  (fcdo-alignment, phase 2): **W1** crosswalk + gate spec (mechanism-only rows,
  capture-hole rows blocked-on-recapture), **W2** planned property/enum registration
  (Run props + event enum, SKOS attrs on enum gates incl. G27, ColumnShape names),
  **W3** ontology-builder as optional add-source-object aid. Skip list binding; the
  companion [source] live-scrape line stays parked (company-side connector).
- 2026-07-30 — [idea] Source-registry id-field redesign (user directive: flat id conflates
  source SYSTEM with extracted DATASET) + the 2026-07-29 per-side loader→source overlay
  candidate (which had reserved the id) → **N7**, ONE fable/HITL-gated design session
  bundling two-level identity, the overlay, the URN handle, and the reconcile
  same-id/changed-meaning guard; feeds the company T19 gate review. Nothing decided at
  groom — everything routes through the gate.
- 2026-07-30 — [chore] 4 taxonomy-ontology-map entries citing unregistered source ids
  (N4 render day-one finding) → **N8** (per-entry ruling: register / re-point / exempt;
  outlook-dl expected exemption per the DL gate's store-as-source design).
- 2026-07-30 — [bug] J16 manifest-coverage guard tracked-only blind spot (new file passes
  pre-commit, fails post-commit — live N5 incident) → **J22** (widen the walk to
  `git ls-files --others --exclude-standard`, false-positive check on scratch files).
- 2026-07-30 — [chore/question/idea] the R5 follow-up trio → **R11** (Ask-spoke
  LLM-in-the-loop smoke on the agents-venv machine), **R13** (ADK 2.x partial/
  non-persisted event mode check vs the session-growth tripwire), **R12** (promote the
  stub-ADK harness into a committed fixture).
- 2026-07-30 — [chore] verify the neo4j-drydocs MCP server post-APOC-fix + GDS
  disposition (parked-until-port-review; the review completed with PORT-REPORT-e60822fc)
  → **G49**.
- 2026-07-30 — [chore] delete rollback container neo4j-drydocs-ee + verify-then-prune the
  orphan volumes (the neo4jtest probation week ended ~today; user pre-decided 2026-07-23)
  → **G50**.
- 2026-07-30 — [idea] SME feedback FB-03/FB-04 (page-role designations + agent-test
  harness) — retro-recorded, NO item: both were executed and SME-re-ruled same day
  (standalone `web/public/agent-test.html`; FB-03 designations stand); the "early seat
  for R5" note was superseded by R5 building `/ask` directly. V10's audit covers the
  runbook side.
- 2026-07-29 — [doc] "create a SME-Runbook for each module" (user directive, chat) → new
  **Epic V** (sme-runbooks, phase 10): **V1** coverage rule — every modules-registry entry
  maps to a governed runbook, an explicit EXEMPT reason, or a frozen shrink-only
  RUNBOOK_PENDING list (N2's LEDGER_PENDING idiom) — then **V2–V10** per-module runbooks
  (core, load, review, docgen, lineage, remediation, api, agents, web-audit), each gated
  on V1's extend-vs-author dispositions for the five runbooks that already exist.
- 2026-07-29 — [question] "one view of all of the taxonomy by source, ontology, extract and
  loads in one place — is it done?" (user, restating the 2026-07-28 ask) → confirmed **NOT
  built yet**: N3–N6 are the build and all four are still `todo` (N3 is next_ready). The
  restated ask is WIDER than the 07-28 scope (taxonomy + ontology weren't in it), so the
  taxonomy-capture and taxonomy-ontology-map joins were MERGED into **N4**'s acceptance
  rather than opened as a new item.
- 2026-07-29 — [idea] XML-fed CMD_LINE resolution (Control-M XML ingestion parses folder/job
  variables → shared resolver populates the G39 store's cmd_line_resolved; three guardrails:
  one-resolver-in-core, derived-beside-verbatim-with-provenance, precedence-before-first-
  disagreement) → **G46** (resolver cmd-line API), **G47** (controlm-xml-export seam),
  **G48** (resolve-cmdline-staging, v3 store); guardrail 3 stays in the inbox as the
  precedence [question].
- 2026-07-28 evening — [bug] rua_inventory silent scripts drop on metadata-only scripts.csv
  bundles (company fixed theirs same day; producer parity, mechanism-only) → **G45**.
- 2026-07-28 evening — [question] constraints.cypher "deprecated by K4 — kept for old graphs"
  comment under-scoped (role/membership keys are live catalog writes) → **C20**.
- 2026-07-28 evening — [chore] enforcement-matrix render must ride the one entry point (the
  stale-render check caught the 49667dd drift live; the J17 defect shape, second surface) → **J20**.
- 2026-07-28 evening — [idea] agent-runtime target-state follow-ups (ADR 0007 revisit check
  PASSED; detail in internal/agent-platform/) → **R10** (google-adk pin + ADR date-stamp);
  caller-identity slot MERGED into **R3**'s acceptance. The target-state prose itself lives in
  the internal review + the R-item acceptances now.
- 2026-07-28 pm — [question] "do we have ONE document with the loaders and order, commands,
  source→target mapping?" → answered NO, then scoped and groomed as **N3–N6** (Epic N,
  phase 11). It is split today across `internal/repo-README.md` (CLI reference + Control-M
  run order), the startup/refresh runbook (operational chain),
  `04-sme-checklist-and-load-plan.md` (sequential plan) and `config/source-mappings/*.yaml`
  (column ledgers). Built as a RENDER, not a fourth hand-written doc — hand-authoring it
  would create exactly the drift this session fixed twice (the depgraph README's stale scan
  roots, `provision.ps1`'s stale `docker run`). The blocker found while scoping: loaders
  declare `name` and `source_label` but NO source-registry id, so loader→source→column-ledger
  cannot be traversed at all — that is N3, and it has value even if N4–N6 never ship.
  No inbox line preceded this; the question arrived in chat and is recorded here for the trail.
- 2026-07-28 pm (post-UI-merge pass) — [bug] snapshot instrument unpinned (fd2834d) → **U7**
  (revision pin + capability probe); the sibling-repo depgraph fork merge stays inboxed as a
  [question] — user's call, different repo.
- 2026-07-28 pm — [bug] snapshot abs_path machine/worktree-dependent (twice ritual-blocking) → **U8**.
- 2026-07-28 pm — [idea] SME landing feedback FB-01/FB-02 + WF-LND wireframes → **O35** (p2 —
  direct SME feedback).
- 2026-07-28 pm — [bug] loads timeline rail dot clips first character → **O36**.
- 2026-07-28 pm — [idea] DataLens continuity DL-5/6/8 → **O37** (radius tokens), **O38**
  (IdChip convention), **O39** (deep-link slot, depends O38). DL-1/2/3/4/9 shipped pre-groom
  on `feat/datalens-quickwins`; DL-7 was a groom-MERGE into O32's notes, executed on-branch
  (`bc61408`) — counted as this pass's 1 merge.
- 2026-07-28 pm — [idea] DSI review DL-10/11/12 → **O40** (StatTiles click-to-filter), DL-11(a)
  folded into **O38**, DL-11(b) → **B5** (stage taxonomy capture, SME gate for the canonical
  set), **O41** (status-vocabulary map). The Epic R precedent note stays with the R1/ADR-0007
  gate materials in `continuity.md` — gate-session input, not a backlog item.
- 2026-07-28 pm — [idea] agent graph-navigation surface (live-benchmarked) → **R9** (read-only
  query command over the O33-guarded specs; MCP recorded as the later option).
- 2026-07-28 pm — [idea] VERIFIED-LIVE claims don't name their machine → **J18**.
- 2026-07-28 pm — [idea] two sessions built C19 concurrently; pushed-claim wording → **J19**.
- 2026-07-28 pm — [chore] misnamed Copy-feedback export (RESOLVED same day — deleted, user's
  call; it was rev1 YAML content under an .html name, both notes already applied in Rev 2;
  the deletion produced no diff and this trail line is the record it existed) → latent gap
  promoted as **L20** (feedback/ stray-file findings guard).
- 2026-07-28 pm — [doc] startup-runbook three held edits (2026-07-26 line): hold lifted (the
  SME review closed); edit 3 (container facts) landed via **L16** Rev 3; edits 1+2 (supplement
  verb collapse + Appendix B registry gap) → **L21** as one Rev 4.
- 2026-07-28 — [source] Snowflake data-catalog (dataset/distribution) loader plan → **G42**
  (source registration + taxonomy-first extractor), **G43** (cross-check reports),
  **G44** (gate prompt + proposed ontology entries; the dcat one-node-or-two ruling
  rides the gate). Epic-close-out groom run; the plan doc is the mapping ledger.
- 2026-07-28 — [bug] Component-cell comma-split shears parenthetical refs (U3) → **L18**.
- 2026-07-28 — [doc]×3 U3-census doc-drift lines (pre-squash citation sweep + sdlc §DEP
  tables + fan-in hotspot citation gap) consolidated → **L19** (one sweep, one review).
- 2026-07-28 — [bug] bootstrap "Constraints applied." with zero constraints (runMany
  no-ops DDL; pre-D5 window) → **D8** (the missing SHOW CONSTRAINTS count guard — the
  history is already fixed by D5, the item is the structural check).
- 2026-07-28 — [chore] render_gates.py missing from the stale-render ritual → **J17**.
- 2026-07-28 — U5 executed INSIDE the groom run (graph cross-check subsection added to
  this very skill) — **Epic U closed 6/6**, the run's close-out target.
- 2026-07-28 — [bug] depgraph scanner blind spots — one fix, three symptoms (cross-root
  IMPORTS, function-level imports, missing drydocs_api scan root; U1 F1 + U2 census,
  confirmed live by the graph-navigation benchmark 0-vs-24) → **U6** (p2, graph-infra;
  work spans the external depgraph repo + snapshot.ps1 target list); **U4 re-sequenced**
  to depend on U6, encoding the U1 wait-verdict. Companion agent-graph-navigation
  [idea] line stays inboxed (mechanism decision = `drydocs query` CLI vs MCP, user call).
- 2026-07-28 — [bug] ontology.cypher:109 dangling SDLC-subset load reference → **C19**
  (comment fix; the build-the-subset-at-all question recorded IN the item as an open
  user/SME call, not silently dropped).
- 2026-07-28 — [bug] PORT-MANIFEST `default: clean-add` fall-through gap → **J16** (the
  inverse-question guard: no tracked path resolves to default without an allowlisted
  reason; the git-readme.md deliberately-uncovered DECISION gets written into the
  allowlist rather than living only in this inbox).
- 2026-07-28 — [bug] doc_traceability/doc_feedback silent-prereq sweep leftovers → **L17**
  (Q8-pattern loud refusal; doc_feedback is the L5/L6 re-attachment loop, so it headlines).
  The batch_port_orchestrator half of that line was already FIXED 2026-07-27 in-session.
- 2026-07-28 — [chore] web/ 3 high-severity npm advisories → **O34** (audit-fix + verify;
  the 1,485 kB bundle/code-splitting design call recorded as explicitly OUT of O34's scope,
  parked in its notes).
- 2026-07-28 — [idea] Script→SWO rider (`:Script -IS_ENCODED_IN-> SwoClass` by extension,
  G33 §E1(b) precedent; run_as = Agent territory boundary; dead-script detection framing)
  → **MERGED into G22 notes as rider R1** for the gate session's agenda.
- 2026-07-28 — [question] m3_invokes `to_node` broadening (Script → Script|ETLProcess, the
  abioncloud wrapper-payload finding) → **MERGED into G22 notes as rider R2** — same gate
  session, vocabulary-shape decision.
- 2026-07-28 — [bug] SchemaMeta contamination defeats WRITE-side guards too (the Q8 build
  finding) → **MERGED into O33**: acceptance now covers loader prereq/guard queries, and
  the keyless-exemplar root-fix option is recorded in its notes.
- 2026-07-28 — [chore] neo4j-drydocs-ee literal `<password>` (2026-07-03 line) → **MERGED
  into the 2026-07-23 delete-rollback-container line** — deleting the container retires it.
- 2026-07-28 — trail moves, no new ids: the C17 PAT-keying and C18 shadow-model lines
  (both said "Groomed as …" since 2026-07-27, C18 since closed) and the fully-RESOLVED
  p0/boundary J14-residual line (its surviving question is the standalone
  platform-vocabulary line; the 6-digit-table-keys SME ruling is recorded in J15's
  close_note) moved out of the inbox.
- 2026-07-27 — [chat notes] G18→G22 premise correction: the psgmgr CM_DEF_VJOB_DETAIL-style
  table (split by job type) was never built → **G39** (temporary cmd-line staging store,
  graph-sourced — j.cmd_line already loads; next_ready) + **G40** (Python cmd-line parse into
  detail columns via the G26 registry + G15 arg contract; depends G39) + the correction merged
  into **G22**'s notes (gate stays the graph terminus; folder/job VARIABLES stay deferred as
  originally sequenced). Company-side "load into the real detail table when built" recorded in
  G40's notes for their tracker. G37 left unallocated (sequence gap beside G38 — possibly the
  concurrent session's; not risked).
- 2026-07-27 — [chore] EE home db `neo4j` pre-existing strays → **RESOLVED same day, no item**:
  user ruled "wipe it, it can be rebuilt" — 288 nodes deleted, 0 remain; topology DBs verified
  untouched (drydocs 834). The .env comment + dev-environment.yaml home_db_warning guard recurrence.
- 2026-07-27 — [idea] code-graph multi-persona review plan (docs/reviews/code-graph-review-plan.md)
  → **U1** (python-architect, opus), **U2** (PM backlog-truth audit), **U3** (tech-writer
  doc-status board) — all next_ready; optional skill-edit follow-ups → **U4** (tech-debt,
  gated on U1) + **U5** (groom-backlog, gated on U2). Epic U gains its first U-lettered ids.
- 2026-07-27 — [p0/boundary] knowledge/standards real-SEALID relocate-vs-sanitize → **J14**
  (option-b split, mechanism public / values internal); [lesson] field-vs-VALUE sweep failure
  → **J15** (value-shape boundary guard test, 70001-70099 block). Residual platform-vocabulary
  question re-inboxed as its own line.
- 2026-07-27 — [chore] :BusinessApplication index diet → **G36** (rides S3's bootstrap
  re-run); [bug] SchemaMeta exemplar contamination → **O33**; [bug] nothing-reads-ddall →
  **G38** (after G32's ruling); [question] deepdoc charter drift → **MERGED into G32** as
  acceptance clause (e).
- 2026-07-27 — [question] "BusinessApplication identity gate — deferred, resume leaner"
  RESOLVED without an item: the gate resumed on exactly the four-question surface and SIGNED
  OFF 2026-07-27 (22/22, `fc15191`). Build = S3 (acceptance rewritten at sign-off); ADR 0010
  amendment = S1; TOM-roles reopen = G35; glossary reservation = G34.

<!-- when you promote an idea, move its line here with the resulting backlog id -->

- 2026-07-26 groom run (docs-residency design session, straight after G28/G29/G30)
  — **8 promoted / 2 inboxed** (todo 39 → 47). Source was a chat, not inbox lines, so
  nothing was moved out of the inbox except the notes below.
  - **Epic Q (docmeta):** **Q7** registry-vs-loaded reconciliation (user-requested — the
    registry declares corpora and `test_doc_registry.py` enforces the declaration's shape,
    but nothing checks a corpus was ever loaded or landed in the database it declared);
    **Q8** the DESCRIBES silent-drop bug; **Q9** re-file Essential GraphRAG as Neo4j vendor
    docs; **Q10** the failure/activity email corpus; **Q11** document supersession/currency.
  - **Epic G (component-topology):** **G32** the document/content topology ruling +
    ddcontext charter (the decision everything waits on); **G31** the proxy-spine extension
    (prerequisite for every corpus move).
  - **New phase 16 + Epic U — `self-documentation`:** **G33** the code snapshot under a
    Project root. Groomed into phase 6 with the marginal fit flagged, then **re-phased the
    same day on the user's ratification** — *"similar to a major version change of the
    snapshot ritual"*, i.e. a new capability rather than an ADR 0002 follow-up. The framing
    that earned the phase: the depgraph ritual's output stops being a JSON file a human
    reads and becomes a queryable `:Project` subgraph — a different KIND of thing, not a
    bigger version of the same one. Id kept as G33 (ids are stable references and it is
    already named in commit a37043a); new items here take U1, U2, … — **T is not free**, it
    is the port-turn series (`docs/port-T12-*.md`).
  - **The session's through-line, worth keeping:** ONE failure pattern found three times —
    *succeeds loudly, does nothing*. G29 (a supplement that runs and seeds no terms), G30
    (a spec that reads a database nothing writes), Q8 (an `OPTIONAL MATCH` whose target
    class is in another database). All three pass their loads green. Worth treating as a
    review lens rather than three unrelated fixes: **any MATCH that can legitimately find
    nothing needs to distinguish "this row missed" from "the whole class is absent".**
  - **Two decisions recorded that overturn signed-off records**, both routed through the
    gate rather than edited (the discipline G30 set): Q9 amends ADR 0006 §2 (the Q2 book's
    `ddcontext` placement) and G32 amends ADR 0002 D1 + ADR 0006 §2.
  - **One assumption I got wrong and corrected in-session:** I proposed *capture fidelity*
    as the database boundary (faithfully-captured vs inferred) and the user rejected it —
    a faithfully-captured stale Confluence page is MORE dangerous than a lossy capture of a
    good page, because it looks authoritative. The property that earns a boundary is
    **content authority**, not capture fidelity. Recorded because the wrong version is the
    intuitive one and will be re-proposed otherwise.
  - **A prediction that did not survive contact:** I named email retention as the fact that
    would decide 2 databases vs 3. It did not — the extracts are deliberately preserved past
    Outlook's 6–18 months until process/project retirement, so purge is property-scoped, not
    a database drop. The 3-DB decision rests on load separation and wipe blast-radius
    instead. Kept here so the retention argument is not re-run.
  - **Inboxed, not promoted:** the deepdoc scope drift (ADR 0002 vs ADR 0006 vs stated
    intent — a ruling, likely a G32 §) and "nothing reads `ddall`" (both at the top of the
    inbox).

- 2026-07-25 groom run (bare `/groom-backlog`, same session as the pre-UI structure review)
  — **11 promoted / 2 inboxed / 1 merged / 1 resolved-in-groom** (todo 30 → 41):
  - **New Epic S — `structure-remediation` (S1–S9)** from
    `docs/reviews/architecture-structure-review-2026-07-25.md` (15 findings, scored
    `(Impact+Risk)×(6−Effort)` plus a pre-UI cost-of-delay flag the formula cannot encode).
    Given its own epic rather than folded into G because the items share one review
    document, one phased plan, and three ADRs whose acceptance gates them — the board
    should show that sequencing as a unit. Each item keeps its correct existing plan
    phase, so the roadmap strip is unchanged.
    - **S1** — rule on ADRs 0008 / 0009 / 0010 (the decision item; the R1 precedent, so
      nothing is groomed into a done deal). Not a HITL gate: no edge semantics.
    - **S2** — ADR 0008: `drydocs_core/orchestration/` parent over `controlm/`, with the
      neutral `shell.py` / `paths.py` / `crosswalk.py` surface beside it. The review
      measured before recommending: ~1,100 of `controlm/`'s 1,725 lines are irreducibly
      Control-M, so the answer to *"should controlm/ become orchestration/"* is **no
      rename — add a parent**. Graph labels untouched (ADR 0003 rule 4).
    - **S3** — ADR 0010: `app_id` + `id_authority` beside `seal_id`, API and web emitting
      only the neutral pair. **GATE-BOUND** — a property-term binding on the canonical
      `:BusinessApplication` node; the map entry stays `proposed` until sign-off.
    - **S4** — ADR 0009: a `draft` table in `mapping.db` as the console's write-ahead
      buffer, promoted by emitting a YAML/CSV diff. Git stays the commit target.
    - **S5** (split the two monolith YAMLs by domain) · **S6** (JSON Schema per config
      family) · **S7** (record the folder-vs-module naming rule once).
    - **S8** — cli.py regroup. **MERGE**: the review's F6 and the long-parked
      `[idea] cli.py regroup` inbox line are the same work; that line's file was 937 lines
      when written and is 1,519 now, which is the argument for doing it. Its deprecation-alias
      condition carried into the acceptance. No dependency on S1 — reorganizing a CLI needs
      no ADR.
    - **S9** — `UI-WIP/` → `docs/design/ui-exploration/` + loose `docs/*.md` grouped.
      Effort was scored 1 and **corrected to 3–4 the same day** when the attempt measured
      31 tracked references (backlog.yaml 45 hits, the generated board, `PORT-MANIFEST.yaml`,
      two gate prompts, two governed renders, `drydocs_api/app.py`) — branch + port-sequenced,
      never a tidy-up commit.
  - **G28** — the multi-database naming drift, found while writing the executive overview
    against the live gated convention. `drydocs_deepdoc.DATABASE = "drydocs_context"`, a
    database `provisioning/01_databases.cypher` never creates (it creates `ddcontext`), and
    `test_lineage_deepdoc_scaffold.py` **pins that value** — so the suite currently protects
    the wrong name. Also unanswered: `ddlineage` is provisioned and read by four query specs,
    but `drydocs_lineage/writer.py` pins `DATABASE = "drydocs"`, so those specs read an empty
    database. Not a trust-boundary hole — the writer refuses on an allowlist.
    RESOLVED 2026-07-26: that second half was split out of G28 as **G30** (a data-residency
    decision, not a naming fix — bundling them was a grooming error) and is now DONE. Ruled
    for ADR 0002 D1/D2: curated lineage lands in `drydocs`; the four specs repoint there and
    `ddlineage` is documented as provisioned-for-later. Ruling written up as ADR 0002's
    "Residency clarification", with the named trigger to revisit through the gate.
  - **G29** — [idea] supplement consolidation shape A (2026-07-24, designed + user-reviewed)
    → the single `apply-supplements` verb with legacy verbs as delegating aliases, all four
    agreed riders in the acceptance. Its sibling **shape C** re-inboxed slim above: it changes
    what a supplement *means*, so it is gate-worthy, not a refactor.
  - **inboxed:** F11 depgraph-snapshot retention (a user call about audit history — and the
    review's proposed mechanism was wrong: `drydocs prune-snapshots` prunes snapshots inside
    Neo4j, not the JSON files); supplement shape C (above).
  - **resolved in the groom, no promotion:** [doc] reconcile-port skill's stale Track-1 floor
    — measured this session at **114 passed / 3 skipped** (the line said 90/3; the inbox note's
    own 113/3 was already stale, since the 2026-07-25 boundary-guard fix added a fifth
    `test_module_boundary.py` test). Skill updated in place, with the number reframed as a
    FLOOR to re-measure rather than a constant, since this is the second time it has drifted.
  - **kept-updated:** the Databricks Unity Catalog line (its governed-namespace citation was
    consumed by ADR 0010 / S3; the tag-policy and glossary-as-concept-scheme citations stay
    parked) · the acronym-catalog line (the review's §4.2 independently reaches the same
    `CatalogBusinessTerm` home from the identity question rather than the collision question;
    still parked on the gate-log Q6 ruling) · the unlocated-typo bug (G29 rewrites the very
    verb list Appendix B carries, so its rider resolves the best-guess half).
  - **findings deliberately given NO item**, recorded so a future reviewer does not rediscover
    them: F4 / F9 / F10-part (done same day — `432ea43` boundary-guard fix, `bbf29cf` gitignore);
    F5 (the `drydocs/` 4-component flat namespace — deferred to Phase C by ADR 0002-a-1, and
    the review's §6 says explicitly not to reopen it mid-UI-build); F15 (two test roots — `tests/`
    pytest and `graph-tests/` YAML acceptance are two mechanisms, not duplication).
  - **kept parked, unchanged** (trigger checked this pass): gate-log Q6 reopen (SME ruling),
    T11 L7-ratification snippet (owed at the next company session), Oracle connection for
    lineage/remediation, company-side greenfield remediation standards, rollback-container
    deletion, PDN/BIM milestone-grain design, email-DL contact point (gate-tracked), the
    Control-M app-code → SEAL `:Port` block (gate `seal-app-ref-edge-reshape` v2 — note S3
    touches the same node, so run them together if timing allows), env-toggle canonical
    identity, XML WARN-flood port note, compact-timestamp back-flow, AIS acronym port-carry,
    ControlMApplication two-pattern mapping, m7 build follow-up, marketing-site brand kit,
    FW-really-API gap classes, DPL ingestion-leg residuals, company back-flow batch,
    company-side heads-ups, post-squash ref cleanup, Runbook Rev 3 rider, SNYK_TOKEN,
    SEAL/PAT generic terminology (three §Decision calls — **note S3 now overlaps its
    `SEALID`→generic-identity-property call and may close it**), m3_invokes `to_node`
    broadening, depgraph metric extensions, ETL-tooling inventory, JobRun indexes, SaaS
    scaffold research, K2 FID/ALIAS tables, `ctlm_id` ripple, dry-docs.com seed,
    /documentation whitepaper type, lineage live-load gate, remediation slices, Phase C
    packaging, Control-M Workbench, BRD outline, docmeta P4–P7, EE container password,
    `common/` in /list-apps.

- 2026-07-23 groom run (full inbox sweep + the misfiled "UI acceleration session"
  block folded in from the bottom of this file) — 5 promoted / 2 resolved-in-build
  (no promotion) / rest kept parked (todo 25 → 30):
  - [chore] Neo4j-container-recreation residual (the container migration itself
    — `neo4jtest` on named volume `neo4j-testdata`, default ports 7474/7687 — is
    already done; only the doc is stale) → **L16**: refresh
    `docs/design/drydocs-startup-refresh-runbook.md`'s container table + start
    commands (still say `neo4j-drydocs-ee`/7476/7689) via the governed render
    pipeline. The sibling "delete the rollback container after a week + prune
    orphan volumes" chore stays INBOXED (time-gated manual Docker op with no
    repo-testable acceptance — the SNYK_TOKEN / post-squash-cleanup precedent:
    manual user steps don't get a backlog.yaml pull id).
  - Misfiled "## 2026-07-23 — UI acceleration session" block (context-graph
    analysis + underhood build) folded into this trail entry — its groom
    candidates from `UI-WIP/two-track-ui-plan.md` (Track 1 table) promoted:
    **O29** (T1-5 trust-tier/edge-provenance legend live on the /lineage and
    /docs graph-pane canvases, adopting context-graph's declared/observed
    legend pattern); **O30** (T1-7 retire `App.css` legacy-mockup classes into
    the token idiom across SignIn/MyApps/GraphExplorer/TowerDrill/
    CypherConsole); **O31** (T1-8 regenerate `web/src/underhood/
    benchmarkData.ts` from the docmeta evaluation-harness output — no
    standalone eval-harness backlog item exists yet, so the dependency is
    recorded as prose in the item's notes per the groom instruction and
    `depends_on` is left `[]`); **O32** (T1-6 light-mode design pass — not
    previously tracked; dark stays canonical). The "intended-bypass build
    landed on main" record and the context-graph adopt/avoid headlines are
    DONE-work notes only, not backlog-actionable — no item, preserved here and
    in `UI-WIP/two-track-ui-plan.md` / `internal/context-graph-analysis/
    ui-architecture-analysis.md`.
  - [source] By-SEAL bulk MAC inventory line → RESOLVED IN BUILD, no
    promotion: G25 (done 2026-07-23) already carries both the taxonomy-first
    per-SEAL staging and the clone-lag `cross_check()` column the line asked
    for; the assumed-field-contract residual rides the dpl_mac discipline, not
    a separate item.
  - [question] Gate rider (G17 build): MAC subType → kind-enum semantics →
    MERGED into **G27** (done 2026-07-22): the gate BRIEF
    (`config/gate-prompts/etlprocess-kind-enum.yaml`) already carries this
    exact question with a recommendation; the SME sign-off itself stays a
    HITL session, not a fresh backlog item.
  - kept parked, unchanged (checked against backlog.yaml this pass — no
    matching item to merge into, or the recorded trigger/gate hasn't fired):
    Oracle connection for the lineage/remediation path (needs SME scope
    clarification first — a question, not yet scoped work), company-side
    greenfield remediation standards (no FR-REM-5/M2 item exists yet),
    PDN trigger/BIM-90489 milestone-grain design, email-DL contact-point
    ontology mapping (already gate-tracked, nothing further to promote), the
    Control-M app-code → SEAL :Port attribution block (owned by gate
    `seal-app-ref-edge-reshape` v2; the property-diet rider sub-part already
    resolved in-line 2026-07-23), env-toggle canonical-identity constraint,
    XML-run WARN-flood next-port note, compact-timestamp normalization
    back-flow note, AIS acronym port-carry, ControlMApplication two-pattern
    mapping (gate-decision core), m7 build follow-up (lineage live-load
    gate), public marketing-site brand kit, FW-really-API provenance gap
    classes, DPL ingestion-leg residuals, back-flow of un-back-flowed company
    advances, company-side heads-ups (their tracker), post-squash ref cleanup
    (destructive, user-gated), Runbook Rev 3 rider, SNYK_TOKEN manual step,
    SEAL/PAT generic terminology (three §Decision user calls), m3_invokes
    to_node broadening (next vocab gate), depgraph metric extensions
    (sibling repo), ETL-tooling inventory domain, JobRun indexes (provenance
    plan's next touch), SaaS scaffold research (triggers unfired), K2
    FID/ALIAS tables (company-side), ctlm_id ripple (internal-side),
    dry-docs.com seed (website not started), /documentation whitepaper type
    (trigger unfired), lineage live-load gate (HITL scheduling), remediation
    slices (TDD §6/§7), Phase C packaging (plan gate), Control-M Workbench
    (entitlement), BRD outline (later phase), docmeta plan P4–P7 (Q6 still
    todo), EE container password (user deferred), common/ in /list-apps
    (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-23 R1 gate SIGNED OFF (same session as the groom below) — **ADR 0007 ACCEPTED
  as written**; rulings (full text in config/gate-log.md): (a) Tier-2 task-graph residency
  = in-process only (ddcontext persistence deferred; new gate if ever proposed);
  (b) :AgentRun envelope → ddcontext, dedicated writer boundary, question sha256+length
  only in-graph; (c) LLM keys = **environment-split: local/producer Anthropic API key,
  company Azure OpenAI** — Gemini NOT the runtime default, closing the 2026-07-03
  question with a ruling that supersedes its Gemini-shaped assumption. R2 next_ready.
- 2026-07-23 groom run (agentic-Q&A architecture session) — **new phase 15 "Agentic Q&A
  console" + Epic R (R1–R8)** from the llm-graph-builder vs knowledge-graph-of-thoughts
  comparative analysis; **ADR 0007 drafted (PROPOSED)** — SME gate = R1, which also rules
  context-graph escalation residency, :AgentRun target DB, and the LLM key strategy.
  Moved from inbox: the 2026-07-03 [question] LLM key strategy (Gemini vs Anthropic via
  LiteLLM) → decided at **R1**. New module registered: drydocs-agents (agents/ ADK
  service). Analysis dossier (both workflow diagrams) linked from ADR 0007's footnote.
- 2026-07-22 — [source] **Backstage catalog-model assessment T1–T8 groomed**
  (UI-WIP/backstage-catalog-assessment.md; shallow clone surveyed + deleted same day):
  T1 kind-enum gate precedent brief → **G27** (in_progress, pulled at groom); T2+T3
  QuerySpec conventions (derived-edge rule + external ref grammar + no element ids) →
  **O27**; T4 inverse_label display field → **C15**; T5 status.items node-status
  envelope → **O28**; T7 metadata key-prefix governance → **C16**; T8 env-toggle
  canonical-identity constraint → inboxed above (no env-toggle item exists yet); T6
  schema-as-contract on DataAsset = design CONFIRMATION only — already covered by the
  O10 schema-definition frame + the G17 MAC dataset feed chain, no new item.

- 2026-07-21 pm — [task] **C12 platforms-taxonomy gate RUN + SIGNED OFF in-chat** (same
  session, ~an hour after C12 was groomed; the K5 precedent): rendered page presented,
  3/3 as recommended — A+B1–B3 confirmed as written (registry model; Ais* removed;
  USES_SOFTWARE {source: 'batch-port'} landing), B4 existing local no-PROV typing covers
  the migrated fact, B5 airflow row stays as the F2 crosswalk placeholder. Gate-log
  entry appended; platforms.yaml confirmed: true; build follow-ups groomed → **C13**
  (SchedulerKind retirement + vocab/map closure + Ais* straggler sweep) and **C14**
  (batch-port USES_SOFTWARE loader migration). C12 done (todo 22 / done 122).

- 2026-07-21 pm groom run (bare /groom-backlog, same session as the platforms-taxonomy
  pre-rulings) — 3 promoted / 0 inboxed / 1 kept-updated (todo 18 → 21):
  - [idea] SchedulerKind → AisCapability/AiTool deprecation (parked since 2026-07-09;
    groom-condition FULLY FIRED today — C11 captured the company shape am, the SME ruled
    the reshape in-chat pm: Ais* removed both sides, registry model wins, gate prompt
    reshaped to confirm-as-written) → **C12** (run the platforms gate, USER-GATED START;
    build follow-ups groom at sign-off — the K5 gate-RUN precedent).
  - [idea] app-to-app path runbook view wireframe (2026-07-21) → **O26** (Runbooks-page
    App-path tab + QuerySpec runbooks.app-path.v1; lane partition from label sets only —
    the layer/c4_level vocabulary stays a gate question; trigger fired: O17 + O11 done).
  - [idea] launcher-registry config-file migration (2026-07-16, the remaining inboxed
    half) → **G26** (config/ pattern + schema guard; classifier_rule ids pinned by
    invocation_patterns must keep resolving; trigger fired: O12 done — its matrix renders
    this registry as the unguarded-config example G26 retires).
  - kept-updated: the ControlMApplication two-pattern mapping line — O13 shipped same
    day (0dc2831), satisfying its prioritization flag; the gate-decision core stays
    parked on the SME convening the mapping gate / K2's next touch.
  - kept parked, unchanged (trigger checks this pass): AIS acronym port-carry (next
    cross-repo port), MAC subType kind-enum rider (next lineage gate; G22 closest), m7
    build follow-up (lineage live-load / m7 flip), marketing-site brand kit (site not
    started), FW-really-API gap classes (next Script-refinement gate), DPL ingestion-leg
    residuals, company back-flow batch (needs screenshot channel), company-side heads-ups
    (relay next company session), post-squash ref cleanup (user, destructive), Runbook
    Rev 3 rider, SNYK_TOKEN manual step, SEAL/PAT terminology (three §Decision calls),
    m3_invokes to_node broadening (next vocab gate), depgraph metrics (sibling repo),
    ETL-tooling inventory, JobRun indexes, SaaS scaffold research, K2 FID/ALIAS
    (company-side), ctlm_id ripple (internal-side), dry-docs.com seed, /documentation
    whitepaper type, lineage live-load gate (HITL scheduling), remediation slices (TDD
    §6/§7), Phase C packaging, Workbench (entitlement), BRD outline (later phase),
    docmeta P4–P7 (Q6 still todo), EE container password, LLM key strategy, common/
    cosmetic, cli.py regroup (v1.0 window).

- 2026-07-21 groom run (bare /groom-backlog, same day as cmdline-nfr-vetting/G15/G16 and the
  Epic O landings) — 2 promoted / 1 retired-merged / 1 kept-updated (todo 22 → 24):
  - [source] DPL runtime traced end-to-end (2026-07-21) + [idea] ETLProcess kind
    discriminator (2026-07-19; its trigger FIRED — pipeline.json subType is exactly the
    discriminating signal G12 lacked) → **G17** (MAC ingest seam: dataset-flow
    READS_FROM/WRITES_TO candidates + kind-derivation rule + SEAL attribution facts;
    synthetic fixtures, gate-confirmed endpoints, all m3_* statuses untouched;
    depends_on G15 — ready now).
  - [idea] AIS taxonomy back-flow for the platforms gate (flagged 2026-07-10 in the
    66acea8 port report, unactioned since) → **C11** (USER-GATED START: capture the
    company-confirmed AisCapability/AiTool shape into config/taxonomy/platforms.yaml
    as the gate's PROPOSED seed; pull loop skips it until the user supplies the
    screenshot/describe material; the sibling SchedulerKind-deprecation line stays
    parked on that same gate).
  - [source] variable gap analysis (2,384 names vs the alias map) → RETIRED MERGED —
    fully consumed at build time: G15's acceptance (a)/(c) cites it as evidence and
    G16 built its alias rollups, value contracts, and the ETL_ARTIFACT_SHA canonical
    from it. Nothing left to carry.
  - kept-updated: the DPL ingestion-leg line — its open item (b) (DataAsset
    zone/glue-table shapes for the MAC enrichment feed) now rides G17 instead of the
    retired sibling line; its other open items (ingestion-launcher jar sample,
    Pre/Post-exec file-op surface, cross-job %%\\JOB\VAR threading) stay inboxed.
  - kept parked, unchanged (each on its recorded trigger): m7 build follow-up
    (deliberately inboxed at the gate — lands at the lineage live-load / m7 flip),
    public marketing-site brand kit (site not started), FW-really-API provenance gap
    classes (:Script property proposals = gate rider for the next Script-refinement/
    lineage gate session), back-flow of un-back-flowed company advances (needs the
    screenshot/describe channel; spans six modules — batch shape decided when the
    material arrives), company-side heads-ups (their tracker; relay next company
    session), post-squash ref cleanup (user, destructive), Runbook Rev 3 rider,
    SNYK_TOKEN manual step, SEAL/PAT generic terminology (three §Decision user calls),
    m3_invokes to_node broadening (next vocab gate), depgraph metric extensions
    (sibling repo), ETL-tooling inventory domain, JobRun indexes (provenance plan's
    next touch), SaaS scaffold research (triggers unfired), launcher-registry
    config-file migration (O12 todo), K2 FID/ALIAS tables (company-side), ctlm_id
    ripple (internal-side), dry-docs.com seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling —
    unchanged by G15/G16), remediation slices (TDD §6/§7), Phase C packaging (plan
    gate), Workbench (entitlement), SchedulerKind → AisCapability/AiTool (gate; C11
    now feeds it), BRD outline (later phase), docmeta P4–P7 (plan-tracked while Q6
    todo), EE container password (user deferred), LLM key strategy (open question),
    common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-21 — [question] Company draft CMD_LINE/variable NFR ontology vetted vs m3 vocab →
  **RULED same day at gate `cmdline-nfr-vetting`** (config/gate-log.md; guided SME session,
  4/4 as recommended): TRIGGERS from-node stays the LAUNCHER (payload variant rejected);
  `USES_ARTIFACT` registered as vocab entry `m7_uses_artifact` (status: planned); :Script
  refinements adopted (script_role + artifact_* props); all 7 variable-standard deltas
  adopted (ETL_* prefix, ETL_ARTIFACT_SHA, aliases-suggest-values-decide, alias-map
  completion, two platform axes, FACT_REGISTRY migration, mode flags stay literals) →
  engine-alignment work groomed as **G16**.

- 2026-07-21 — [chat] UI extension groom ("extend the UI open items until HITL"): the new
  UI-WIP corpus (DryDocs_UI_Development_Specs.md, gemini-wire-frame.md, icons.md,
  layout-anatomy-checklist.md, new mocks) + site-plan §5 P3 → **O15–O22** (Ownership /
  Loads / Runbooks+Remediation / Docs / Gates-read-only pages, the O20 write-surface HITL
  gate as the chain terminus, UI-WIP commit chore w/ LFS, icon SVG export); demo-content +
  expanded-landing specs **merged into O9** inputs/notes; WEBSITE-IDEAS.MD parked to Inbox
  (public site, separate workstream).

- 2026-07-21 — [source] Real prod DPL CMD_LINE samples (folder/job screenshots +
  variables-simulation views) → **merged into G15** (acceptance upgraded from
  placeholders to observed grammar: single-dash `-pipeline` GUID as the only literal,
  variable-held launcher fallback, -i/-t/-py mode flags, -seal/-fid/-img/-conf/-compute
  property set; one dt-launcher.sh spine across ingest/transform/provision). Remainder
  re-inboxed on the ingestion-leg line: template ingestion-launcher jar unobserved,
  Pre/Post-exec file-op surface, zone/glue DataAsset shapes, cross-job %%\\JOB\VAR.

- 2026-07-21 — [chat] DPL launcher key-parameter capture (--pipeline-id spelling +
  shell-launcher variants + -py route + dataset-id/aws/jar/queue params as properties)
  → **G15**. The sibling 2026-07-21 inbox line (MAC dataset-flow enrichment feed +
  G12 kind discriminator) stays in the inbox — G15's explicit non-goal.

- 2026-07-20 groom run (evening; second machine re-based post-squash, then /groom-backlog) —
  2 promoted / 1 inboxed / 1 kept-updated (todo 17 → 19):
  - session preamble (recorded here — ref state, not backlog): this machine adopted the
    squashed main (reset to 4540bbc), local `feat/mapping-store` DELETED as superseded
    (its content was inside the Initial-import squash and main evolved past it; old
    history kept at local tag `archive/old-history-2026-07-20`).
  - [doc] runbook-mapping-demo free-form pre-L8 (2026-07-18) → **L14** (refit to
    runbook.outline.yaml, 2nd runbook exemplar; trigger = L8 done, e6bcb24).
  - [doc] project-review canonical outline (2026-07-14) → **L15** (review.outline.yaml
    3rd doc type + recorded refresh cadence; same L8 trigger; p3).
  - inboxed: post-squash ref cleanup (stale origin branches feat/mapping-store +
    feature/provenance-audit-fields-plan; local backup branch/stash/tags) — destructive,
    user-gated.
  - kept-updated: SEAL/PAT generic-terminology line — C10's CSDM mining landed (its
    named missing piece); decision surface fully fed, still parked on the three
    §Decision user calls (scope / new-epic plan change / SEALID property).
  - trigger checks this pass: Q6 todo → docmeta P4–P7 stay plan-tracked; O12 todo →
    launcher-registry config-file migration stays; E1 deferred both sides; Runbook Rev 3
    rider + SNYK_TOKEN manual step stay inboxed (new today, correctly parked). All other
    lines kept parked, unchanged on their recorded gates.

- 2026-07-20 — [doc] apply the runbook rev1 SME feedback → EXECUTED SAME-DAY (user-directed,
  no backlog id): both notes applied to the .md (front-matter one item per line; out-of-scope
  drops the company-side Track-2 item), Rev 1→2 with a change note, re-rendered (footer
  "Rev 2 · commit a135a6d"), validator + doc tests green. The rev1.yaml stays as the
  feedback record; the stray -sme.html working copy remains the user's to delete.

- 2026-07-20 — [chore] USER MANUAL STEP: port-bundle transfer → **RETIRED, FULLY COMPLETE**
  (the 07-19 line, end to end): bundle created @ 3ae9b08 (447 commits, full pre-squash
  history) → base64 3-way split → emailed → company side rejoined, hash-verified,
  `git bundle verify` passed, full bundle-port reconciliation ran (their
  PORT-REPORT-bd7952f.md, 2026-07-20) → ALL FIVE local transfer files deleted
  (3 parts post-email; the bundle + .b64.txt deleted 2026-07-20 pm after far-side verify,
  user-directed). Full private history now exists only in local `archive/full-history` +
  the company repo. Recipe reference: `docs/ruff-format-convergence.md` §"Transfer
  without visibility change".

- 2026-07-20 — [question] cross-repo backlog id collision → **DECIDED SAME-DAY (user):
  the DD-series** (`DD1`, `DD2`, …) is reserved for company-side-only items; the producer
  never allocates it, the company never allocates epic-letter ids. Recorded in
  git-readme.md (§backlog id allocation), the backlog.yaml header, and the groom-backlog
  skill id rule. REMAINING (company-side, next session there): renumber their colliding
  C10/K6/N3 → DD1–DD3 before the next port range applies.

- 2026-07-20 pm — bundle-port readout review (company-side photo; their
  PORT-REPORT-bd7952f.md) — 2 mirrored done / 1 line resolved / 1 question inboxed:
  - **P1 + P4 → done** (company completion wins for company-side work — their probes +
    CM_AVG_RUN supplement loader shipped; resolves the 07-18 "concurrent Epic P session"
    observation). P3 becomes next_ready; P5 still waits on P3.
  - port-bundle USER MANUAL STEP line → RESOLVED to its last step (delete the 2 remaining
    local transfer files; far side verified).
  - inboxed: the C10/K6/N3 cross-repo id-collision question (convention needed before the
    next port).
  - noted, no producer change: the company deferred 3 HITL deltas to their own gates
    (docs_*/:DocSource union-add; catalog_supports re-activation; jobrun-observation —
    E1's gate is now deferred BOTH sides); their 4 port commits await review + push.

- 2026-07-20 — [chore] Snyk scanning in CI → EXECUTED SAME-DAY (no backlog id, direct user
  request — the PAT-semicolon precedent): ci.yml gains a `snyk` job — SCA over the Poetry
  manifest (blocking at high severity) + advisory `snyk code` SAST (the ruff idiom).
  Token-gated: every scan step skips cleanly until the SNYK_TOKEN repo secret exists.
  REMAINING USER MANUAL STEP: add SNYK_TOKEN (Settings → Secrets → Actions; token from
  app.snyk.io) — first green scan confirms; consider gating `snyk code` after triage.

- 2026-07-20 — [source] **external/ServiceNow doc set** (6 files downloaded same day: CMDB
  Process Guide .docx, CMDB Product Architecture / Data Manager / Governance Workshop
  .pptx, ITAM-SAM Integration Options .pptx, "What are services and service offerings"
  .pdf) → **C10** (promoted directly from chat, the C9 precedent): housing + SOURCE-MANIFEST
  + classification decision, readable-text conversion (the SDLC-Docs/extracted idiom),
  and per-file concept mining dispositioned incorporate/park/reject — feeds the parked
  generic-terminology idea (the CSDM service/service-offering layer is its missing
  piece). User context in the item notes: the full-circle-docs-era ServiceNow Marketplace
  consideration (research only) and the CMDB-for-taxonomy→ontology reference. Files stay
  untracked until C10's classification step.

- 2026-07-20 — [task] **K5 Product Cabinet gate RUN + SIGNED OFF in-chat** (same session as
  the groom below, later in the day; page rendered via gate_pages.py from the in-flight
  2026-07-19 gate-prep, sections A–E answered in-session, §F signed off — gate-log
  2026-07-20): map entry confirmed; families INDEPENDENT (shared-cto dropped, rename
  history recorded — supersedes 2026-07-10 §B); tech_partner :AreaProduct-only; BOTH
  attribution forms (collapsed catalog_cabinet_attributed_to added); reporting edges
  DEFERRED (internal-side); DevTeam↔BusinessApplication M:N confirmed. Supplement
  follow-up promoted directly → **K6** (the C9 direct-promotion precedent); K5 done
  (todo 22 / done 91). The 07-20 groom entry's "K5 in flight uncommitted" observation is
  RESOLVED — this session took ownership, committed the stream (K5(1)/K5(2) + this
  close-out), and the m3_invokes to_node rider stays parked (this gate was
  Product-Cabinet-scoped; next lineage-vocab gate remains its trigger).

- 2026-07-20 groom run (bare /groom-backlog, day after the weekly run; post history-squash) —
  0 promoted / 0 merged / 1 kept-updated; backlog database untouched (todo 22 / in_progress 1 /
  done 90 stand as of the 07-19 groom):
  - kept-updated: the USER MANUAL STEP port-bundle line gains the SQUASH RIDER — today's
    history squash (main = single commit c5a84c3; full history only in local
    archive/full-history) makes "email the existing 3ae9b08 full-history parts vs re-cut
    from the squashed main" a user decision that must precede the email step.
  - noted closed by the squash: the 07-19 seal-sample residual ("git HISTORY retains both
    seal twins until a rewrite, user-gated") is CLOSED on main/origin — pre-squash history
    survives only in local archive/full-history + the five transfer files (whose deletion
    is the port-bundle line's remaining step).
  - observation (no groom action): **K5 gate-prep is IN FLIGHT, UNCOMMITTED** in the working
    tree — config/gate-prompts/product-cabinet-attribution.yaml (new) + map/vocab/
    schema_graph edits, proposed_at 2026-07-19, all correctly gate-bound (everything
    planned/proposed, nothing applied). Left untouched per the 07-18 P1 precedent: the
    owning session commits and flips K5 todo→in_progress itself; this groom's commit
    excludes those files.
  - observation (user decision, destructive): stash@{0} "On feat/k4-businessapplication-
    reshape: gate-review IDEAS entries" is STALE — its two 2026-07-15 lines reached the
    inbox via another path and were groomed to G12/G13 at the 07-16 pm run (G12 since
    executed). Candidate `git stash drop`; not dropped by the groom.
  - trigger checks this pass: Q4/Q5 done but Q6 still todo → docmeta P4–P7 stay
    plan-tracked; L8 todo → runbook-mapping-demo refit + project-review outline stay;
    O12 todo → launcher-registry config-file migration stays; no other recorded gate moved
    since yesterday's run. All other lines kept parked, unchanged (m3_invokes to_node
    broadening noted as a candidate agenda rider for whichever gate session runs next —
    the in-flight K5 gate is Product-Cabinet-scoped, so adding it is the SME's call).

- 2026-07-19 groom run (weekly inbox groom) — 2 promoted / 2 merged-or-folded / 1 kept-updated:
  - [bug] publish-ceiling drift (real identifiers in publishable-tier files; found by the
    2026-07-19 aborted-mirror pre-publish grep) → **J13** (p1, fable, USER-GATED START — the
    user confirms the real-vs-synthetic term list before execution; the term list is recorded
    internal/-side only, never in publishable tiers; the backlog pull loop skips J13 until then).
  - [idea] file-ops READS_FROM/WRITES_TO extractor pass (G13's missing feed) → **G14**; the
    sibling [idea] surface-`WritePlan.unresolved_file_ops` line FOLDED into G14's acceptance
    (one item — the feed is what makes the counter worth reading).
  - [source] codeflow UI screenshot → MERGED into **O9** (inputs + notes). File already tracked
    at `UI-WIP/codeflow-ui-reference.png`; classification External, captured 2026-07-19 from
    https://github.com/braedonsaunders/codeflow/blob/main/screenshot.png (MIT-licensed repo) —
    cite, don't imitate branding.
  - kept-updated: the USER MANUAL STEP port-bundle line — the create half is done (bundle @
    3ae9b08 encoded + 3-way split); remaining: email the parts, far-side hash confirm, delete
    the five local transfer files.
  - kept parked, unchanged (each on its recorded gate): m3_invokes to_node broadening (next
    vocab gate session), ETLProcess kind discriminator (needs a discriminating signal),
    depgraph metric extensions (sibling-repo work), runbook-mapping-demo refit (L8),
    ETL-tooling inventory domain (direction), JobRun-index fold (provenance plan's next
    touch), SaaS scaffold research (triggers unfired), launcher-registry config-file
    migration, project-review outline (L8), K2 FID/ALIAS tables (company-side), ctlm_id
    ripple (internal-side), dry-docs.com seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling), remediation
    slices (TDD §6/§7), Phase C packaging (plan gate), Workbench (entitlement), SchedulerKind
    → AisCapability/AiTool (SME class definitions), BRD outline (later phase), docmeta P4–P7
    (plan-tracked until Q4–Q6 land), EE container password (user deferred), LLM key strategy
    (open question), common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-19 — [bug] PAT seal_ids semicolon-delimiter mismatch → FIXED SAME-DAY (no backlog id,
  user call — pulled ahead of the catalog-pat team-report onboarding it was parked for):
  `PatProductMappingRow.seal_ids` now normalizes `;` → `,` before the cypher's comma split;
  synthetic sample row T0042 made semicolon-delimited to exercise the path; drift guard
  `test_row_model_normalizes_semicolon_seal_ids`; `internal/pat-evidence/README.md` note updated.

- 2026-07-19 — [chore] seal-sample standing exception → RETIRED EXECUTED SAME-DAY (no backlog id):
  user call — DELETE both `seal_*__sample.csv` twins from the tip rather than synthesize
  replacements (names were fictional; the seal_ids were real). App file e7f8f20 (user, web UI) +
  contacts twin this commit; classification.yaml carve-out removed; `drydocs/data/samples/**` is
  synthetic-only again. Residual: git HISTORY retains both files until a rewrite (user-gated).
  A future SEAL sample, if ever needed, gets synthetic ids (the pat_product_mapping pattern).

- 2026-07-18 — [task] C5-gate follow-up (promoted directly from the gate session):
  pat_product_mapping.cypher still writes the 2026-06-21-deprecated catalog_supports
  edge every load; SME supplied PAT screenshots in-session (Internal-Confidential,
  held out of the repo) showing teams map to 1..n business applications via the PAT
  team report while area-product alignment is volatile + relationship-typed — the
  deprecated edge may be independently asserted (the C5 exception path), so it re-gates
  rather than gets deleted blind → **C9** (p1, fable).

- 2026-07-18 — [bug] design-doc DUAL-HTML render (chat capture + screenshot, promoted
  directly): `.print.html` misrenders in-browser while the screen `.html` already
  print-adapts (white-on-black on screen, black-on-white at print) — SME call: one file
  suffices, retire the `.print.html` series (fold the L6 print-margin anchors into
  @media print) → **L13**. Evidence PNG at repo root, local-only (root-images
  gitignore). Related-not-merged: L9 (Chrome partial render of the screen html).

- 2026-07-18 groom run (weekly inbox groom, on `feat/mapping-store` — the 07-15 K4-branch
  precedent) — 5 promoted / 1 merged / 2 retired-executed / 2 re-inboxed slim / 1 kept-updated:
  - [idea] mapping-store research line → RETIRED EXECUTED-PRE-GROOM (the TechStack plan-07
    precedent — plan-tracked, not epic-itemized): M0–M4 + the wf-mapping-01 live demo BUILT on
    `feat/mapping-store` (807e050), deltas recorded in the plan doc header (store moved to
    drydocs_core; artifact-download submit; no new gates). Groom-touches: **O13** gains a
    progress record + the plan-§6 acceptance rider ("dropdowns read mapping.db via
    drydocs-api"); the plan's unwired M2 rebuild residual promoted → **O14** (staleness
    guard — a stale var/mapping.db serves stale grids until deleted). ETL-tooling inventory
    re-inboxed as its own slim line.
  - docmeta plan line (trigger fired 2026-07-16: P0 verdict = BUILD, Q3 done) → P1–P3
    promoted: **Q4** (gate session + docmeta ADR + planned vocab entries, reconciled against
    active docs_*; fable), **Q5** (doc-source registry ledger + guard test + stray-PDF
    sweep), **Q6** (Port A bkup→producer; module `drydocs-docmeta` REGISTERED as working
    name — final at the Q4 gate, the drydocs-api precedent). Line kept-updated: P4–P7 stay
    plan-tracked; GraphAcademy existence-constraints rider attached.
  - [question/idea/chore] GraphAcademy advisor line → dispositioned per sub-item:
    incremental delete-sweep → **D7**; BaseLoader index preflight EXECUTED PRE-GROOM
    (66049a0); DC-collision check ALREADY ROUTED to the internal-session checklist
    (66049a0/d21d4e5) — **P1 deliberately untouched this groom: its status flip is
    uncommitted in a concurrent Epic P session** (c12ab43 readout); graphrag-llm-navigation
    annotation + the save_data_model save were already done in-line; JobRun-index fold
    re-inboxed slim (provenance plan's next touch).
  - [idea] EE re-bootstrap demonstrable-content loads → MERGED into **D6** (the line's own
    suggestion): the quick-start/bootstrap sequence gains load-software-registry +
    load-bmc-docs (+ optional load-essential-graphrag); Q3's P0 spike already re-ran both
    loads once, proving the gap.
  - inboxed new: runbook-mapping-demo authored free-form pre-L8 (refit when L8 lands; the
    web-console TDD from the same session is auto-swept, nothing to do).
  - kept parked, unchanged (each on its recorded gate): SaaS scaffold research (direction;
    export-target/template-play triggers unfired), launcher-registry config-file migration,
    project-review outline (L8), K2 FID/ALIAS tables (company-side; fid-seal/alias-seal
    mapping domains now visibly registered-but-unavailable in the O13 demo), ctlm_id ripple,
    dry-docs.com seed, /documentation whitepaper type, lineage live-load gate (HITL),
    remediation slices (TDD §6/§7), Phase C packaging, Workbench (entitlement),
    SchedulerKind → AisCapability/AiTool (SME), BRD outline, EE container password,
    LLM key strategy, common/ cosmetic, cli.py regroup (v1.0 window).

- 2026-07-17 admin/steward surfaces groom — 2 promoted (chat captures + the fired
  launcher-line trigger): admin configuration page w/ generated enforcement matrix →
  **O12** (user decisions: CI last-run metadata; secrets .env-only so config renders
  verbatim); power-user manual-mapping stewardship screen (job→application, FID, ALIAS;
  gate-bound manual-loads changesets, zero graph writes; new steward persona) → **O13**.
  Wireframes wf-admin-config-01.* + wf-mapping-01.*; launcher-registry config-file
  migration still inboxed.

- 2026-07-17 site-plan groom — 4 promoted (O8–O11, Epic O phase 12), 2 inbox lines closed:
  - [idea] **UI DECISION: single-track ReUI, Salt DROPPED** (user call) + site plan
    (`UI-WIP/site-plan.md`: system-default 3-state theming dark-first, radial-hub landing,
    one module-subpage template × 9 modules, QuerySpec registry + two-path Neo4j
    data-frame export with provenance manifest/classification banners) → **O8** (shell +
    theme + routes), **O9** (landing + Explorer template), **O10** (Lineage canvas),
    **O11** (QuerySpec + export, module drydocs-api). Existing modules used — the plan's
    `drydocs-ui` module suggestion superseded (registry already names drydocs-web).
  - [idea] UI-stack proposal 2026-07-17 (ReUI free + React Flow + ADK 2.0 compat; Salt
    two-track addendum) → subsumed: stack table = site-plan §1; Salt track dropped by the
    same-day decision; ADK enablers (mcp.reui.io, @reui/skills-claude, AG-UI notes)
    preserved in site-plan §1 + memory. Site-plan §4 backend caveat corrected at groom:
    ADR 0005 ratified + drydocs-api shipped (O5), export endpoints land there.
- 2026-07-16 evening groom, part 2 (user decisions on the same-day [source] line) —
  2 promoted / 1 plan change (user-approved) / housing executed in-session:
  - PLAN CHANGE: new **phase 14 "Document ingestion & doc-graph benchmarks"** + **Epic Q**
    — the docmeta landing zone (AskUserQuestion-approved; the phase-12/13 idiom). The
    docmeta plan's P1+ phases groom here once the P0 verdict + docmeta ADR land.
  - [source] Essential GraphRAG (Manning / Neo4j-sponsored ebook, Bratanič & Hane,
    179 pp) → **Q1** (mine for applicable patterns at chapter level → docmeta P0 verdict
    input; answers "are there more examples of how to do it properly?") + **Q2**
    (Document→Chunk lexical-graph load + >=5-question agent-traversal experiment —
    vocabulary-reusing per the 07-08 bmc-docs gate, no new gate; target DB drydocs-vs-
    ddcontext decided at execution). HOUSING EXECUTED with the groom (user decisions:
    gitignore, publicly available): root-level `/*.pdf` blanket rule (root-images
    precedent; tracked UI-WIP/*.pdf unaffected) + reference/research/README.md seed-table
    row (Manning link verified 2026-07-16).
  - kept-updated: the docmeta plan line — phase 14 / Epic Q recorded as the landing zone
    for its P1–P3 promotions.

- 2026-07-16 evening groom (third run today; bare /groom-backlog, no new notes) —
  0 promoted / 1 inboxed / 0 merged; backlog database untouched (todo 23 / done 71 stand
  as of acf0bfe):
  - inboxed: `Essential-GraphRAG.pdf` found untracked at repo root (Manning / Neo4j-sponsored
    ebook, 179 pp, file dated 07-14) → new [source] line above — registration + housing
    (commit vs cite+gitignore) is a user decision; joins the JPMC annual-report PDFs in the
    untracked-root-PDF class noted at the 07-16 am groom.
  - all other lines kept parked, unchanged — every recorded gate was checked twice earlier
    today (am weekly run, pm post-merge run at acf0bfe); nothing has landed on main since.

- 2026-07-16 pm groom (second run today, post cmdline-lineage-review + the K4-branch merge) —
  2 promoted / 2 retired-executed / 1 line-update:
  - [idea] 2026-07-15 ETLProcess writer endpoint class (lineage vocab gate residual; the
    business-key half decided + implemented extractor-side at cmdline-lineage-review) →
    **G12**. [idea] 2026-07-15 writer file-ops resolution (same gate's second residual;
    endpoints per the gate EDIT: ETLProcess|ControlMJob → DataAsset) → **G13**. Both are
    the pre-flip curated-load-build blockers; shapes gate-confirmed so no HITL surface
    remains — sonnet items with written acceptance.
  - retired to this trail (fully executed/decided in-session, gate-log
    cmdline-lineage-review): the 07-16 [bug] CMDLINE parser gaps line (all four gaps
    closed same day: control-keyword stripping, runScript.sh -g pset payload expansion +
    case-fix, java/.jar + DPL rules, air rule; sanitized twins pinned) and the 07-16
    [question] gate-agenda line ((a)–(d) all decided; cross-machine reconcile with the
    07-15 vocab gate recorded at the b3c455f merge).
  - line-update: the K2 FID/ALIAS company-side line gains the folder-variable FID+SEAL
    co-location as a candidate FID→seal_id source (side finding from the live captures).
  - kept parked, unchanged: launcher-registry human-configurable (new today — trigger =
    web-console admin surfaces or Phase-E urgency); all other lines on their recorded
    gates (verified this morning, unchanged since).

- 2026-07-16 groom run (weekly inbox groom) — 0 promoted / 0 merged / 1 kept-updated;
  backlog database untouched (summary/next_ready stand as of 2026-07-15):
  - kept-updated: the docmeta plan line — **ADR number collision found + corrected**: the
    plan (2026-07-06) reserved "ADR 0004" for its P1 gate output, but 0004 was minted the
    next day as `0004-software-registry-vendor-terminology.md` (accepted 2026-07-07). The
    docmeta ADR now takes the next free number at authoring; the plan doc's 3 stale refs
    (`knowledge/upgrade-plans/docmeta-component.md` §1.1, P1 phase row, port table)
    annotated in the same commit.
  - gate checks run against the repo this pass: L8 still `todo` → project-review outline
    stays parked; docmeta P0 WRITTEN verdict still absent (only the ADR number changed);
    ADR 0005 ratified + O1/O3/O6 done ≠ any parked trigger.
  - kept parked, unchanged (each on its recorded gate): drydocs-project-review outline
    (L8), K2 FID/ALIAS reconciliation tables (company-side sources), ctlm_id ripple checks
    (internal-side), dry-docs.com visual seed (website not started), /documentation
    whitepaper type (trigger unfired), lineage live-load gate (HITL scheduling),
    remediation next slices (TDD §6/§7), Phase C packaging (plan gate), Workbench
    (entitlement), SchedulerKind → AisCapability/AiTool (SME class definitions), BRD
    outline (later phase), docmeta P1–P3 (P0 verdict + the renumbered ADR), EE container
    password (user deferred), LLM key strategy (open question), common/ in /list-apps
    (cosmetic), cli.py regroup (v1.0 window).
  - observation (no action): untracked UI-WIP/ website material (WEBSITE-IDEAS.MD,
    gemini-wire-frame.md, landing PNGs, icons.md) predates the 07-13 re-inbox of the
    dry-docs.com line and is its seed corpus when that gate fires; console-side UI-WIP
    files are O-epic surfaces. Root-level JPMC annual-report PDFs also untracked
    (data-context-extractor inputs — house them or gitignore at next touch).

- 2026-07-15 pm groom (on feat/k4-businessapplication-reshape) — 2 promoted, both
  same-day findings from the O6 session's first live EE bootstrap:
  - [bug] `Neo4jClient.run_script` inherits APOC's comment-`;` split (Cypher 25 rejects
    the empty fragment; loaders already guarded by `base.py::_code_semicolons`) → **D5**.
  - [chore] m3-verify fails on bundled samples — active folders 161020/160501 have no
    sample jobs → **D6** (add-jobs vs downgrade-to-warning left either/or, decided at
    execution).
  - groom-touch on **K4**: the branch feat/k4-businessapplication-reshape is reserved for
    it; the remote stub (40fe038, zero own commits, pre-K2) was re-based onto main a683384.

- 2026-07-15 groom run (weekly inbox groom) — 3 promoted / 1 retired (resolved in place):
  - [chore] `controlm-loader-flow.md` → `docs/history/` move (captured same day at the
    controlm docs status-refresh sweep, e3e7bec) → **J11**. Inbound-linker correction made
    during grooming: grep says README.md + the internal governance doc reference it, NOT
    CHECKPOINT/reviews as the inbox line guessed.
  - [chore] schema_graph.cypher stale (generated 2026-06-09, no drift guard; found at the
    K2 build) → **C8** — regenerate-with-guard vs mark-point-in-time deliberately left as
    an either/or in the acceptance, decided at execution (derived view, no gate needed).
  - [chore] session-ritual `python scripts/...` fails outside the venv → **J12**
    (CLAUDE.md ritual lines + snapshot.ps1's two `& python` calls; re-verified live this
    session — render_design_doc.py failed bare, succeeded under `poetry run`). Execution
    caution recorded: CLAUDE.md carried uncommitted user edits at groom time.
  - retired: the 2026-07-13 UI-branch reconcile line — fully RESOLVED in place by its own
    2026-07-14 updates (all UI branches reconciled; the web stream lives entirely on main);
    no item needed, the resolution narrative is preserved in this trail's 2026-07-14 entries.
  - kept parked, unchanged (each on its recorded gate): drydocs-project-review outline
    (trigger = L8 landing the 2nd doc type), K2 FID/ALIAS reconciliation tables
    (company-side sources), ctlm_id ripple checks (internal-side investigation),
    dry-docs.com visual seed (website not started), /documentation whitepaper type
    (trigger unfired), lineage live-load gate (HITL), remediation next slices (TDD §6/§7
    tracks), Phase C packaging (plan gate), Workbench (entitlement), SchedulerKind →
    AisCapability/AiTool (SME class definitions), BRD outline (later phase), docmeta P1–P3
    (P0 verdict + ADR 0004), EE container password (user deferred), LLM key strategy
    (open question), common/ in /list-apps (cosmetic), cli.py regroup (v1.0 window).

- 2026-07-15 — [bug] psgmgr version filter domain is `'Y'` not `'1'` — resolved by the
  FINALIZED company Control-M ingestion TDD (captured local-only in
  `internal-local/company-backflow/controlm-ingestion-tdd.md`; their live extracts filter `'Y'`
  and returned the worked-example population). Closes staging-ingestion-flow preflight 0.3 → **D4**.
- 2026-07-14 — [idea] Two support queries proven live on the internal graph (dependency-chain
  finder via undirected `shortestPath` over `WAS_INFORMED_BY`; folder-scoped dependency census,
  ~69% cross-folder stat) — groomed to drydocs-api named endpoints → **O7** (closed same day:
  already shipped by O5's `queries.py`; the note was stale — O5 built them in directly).

- 2026-07-14 groom run (ADR 0005 Action items → Epic O; not an inbox groom) — 4 promoted:
  **O3** ratify ADR 0005 (in_progress — awaiting the SME flip, the E1/P2 idiom; gates the
  rest); **O4** GraphAccess seam refit + dev-flag-gated raw Cypher + credential-rule doc
  (ADR items 2/4/5); **O5** thin-API component scaffold (ADR item 3 — the ADR explicitly
  deferred it to this flow; NEW module `drydocs-api`; fable per the component-boundary
  precedent); **O6** live C4/graph view through the seam (the remaining O1 build; O1
  closes on O3+O6). Ran at the feat/web-login-mock --no-ff merge (design pass onto main).

- 2026-07-13 groom run (weekly inbox groom) — 2 promoted / 1 merged / 1 re-inboxed:
  - [chore] ruff cleanup → CI lint gate (2026-07-11, found executing J5) → **J10** (Epic J,
    phase 8; ready — J5 done and live on main). The user's timing flag preserved in the item
    notes: execute during a port lull, the diff touches every Python file.
  - [idea] artifact-design review sub-item 1 (governed-render-fidelity rule: governed
    surfaces — design-doc renders, gate pages, board — publish VERBATIM; editorial treatment
    only for outward-facing docs) → **L12** (Epic L, phase 10).
  - [idea] artifact-design review sub-item 2 (artifact-design skill's "UI, not a document"
    checklist + AI-default-looks list as the UI-WIP/ review lens) → **MERGED into O1** notes;
    O1 re-tiered opus → fable on the groom touch (G3 policy — the bolt-vs-thin-API call is a
    boundary decision).
  - [idea] artifact-design review sub-item 3 (whitepaper "overnight ledger" identity as the
    dry-docs.com visual seed) → re-inboxed as its own slim line, parked until website work starts.
  - kept parked, unchanged (each on its recorded gate): /documentation whitepaper doc-type
    (trigger "white papers recur" hasn't fired), lineage live-load gate session (HITL —
    groom when the SME schedules it), remediation next slices (TDD §6/§7 tracks), Phase C
    packaging (plan gate), Workbench (entitlement), SchedulerKind → AisCapability/AiTool
    (SME class definitions), BRD outline (later phase), docmeta P1–P3 (P0 written verdict +
    ADR 0004), EE container password (user deferred), LLM key strategy (open question),
    common/ in /list-apps (cosmetic), cli.py regroup (v1.0 rename window).
  - hygiene: deleted the stray empty docs/restructure/IDEAS.md.tmp (interrupted-write leftover,
    0 bytes, untracked).

- 2026-07-11 — /tech-debt documentation audit (docs/reviews/tech-debt-documentation.md) —
  0 promoted / 1 merged / 5 executed with the review / 3 deduped:
  merged: README feature-currency gap → **J2** (title broadened; one README pass).
  executed (D-numbers per the report): D2 login tribal-knowledge doc committed under
  internal/ with classification; D5 MODULE_MAP drift (future-markers on shipped H2/H5
  modules; sme_notes/gate_pages rows added; lineage row = populated); D6 stale cron prompt
  → docs/history/ + banner; D7 root console dump → gitignored internal-local/; D8 tracking
  headers on the two 2026-07-09 tech-debt reports.
  deduped: skill staleness → J4; missing runbook → L8; UI-WIP → O1. Structural verdict:
  clean — all point-in-time reviews banner'd, living docs came through the relocate clean.

- 2026-07-11 groom run (G9-close session; directive: groom the remaining NON-HITL items) —
  2 promoted / 1 merged / 1 inboxed:
  - [idea] G9 tech-debt finding #3 (extractor coverage accounting — stale/nameless/no-target
    skips are silent) → **G11** (drydocs-lineage, phase 6; ready — G9 done). Report, never
    drop: the STG_PARSE_QUALITY / UNMATCHED house rule applied to the candidate side.
  - [idea] G9 tech-debt finding #2 (extractor CSV column contract duplicates controlm_jobs.sql
    aliases as strings, silent-drop on alias rename) → **MERGED into N2** (the SQL SELECT-list
    drift guard gains the extractor as a second consumer of the same list). The 2026-07-10
    tech-debt line is fully dispositioned (#1/#4 fixed same day, #2→N2, #3→G11) and retires.
  - [idea] testcontainers end-to-end CSV→Neo4j load test (parked since 2026-07-01) → **J9**
    (drydocs-load, phase 8; ready — no deps, no HITL surface). Covers the never-executed
    Cypher path; opt-in + Docker-gated so the unit suite is untouched.
  - inboxed: the lineage live-load gate session (HITL-dependent by definition — the Fork-3
    writer's refusal IS the gate; groom when the SME schedules it).
  - kept parked, unchanged (each on its recorded non-HITL-groomable gate): remediation next
    slices (OQ-2/OQ-4 + company-side), Phase C packaging (plan gate), Workbench (entitlement),
    SchedulerKind → AisCapability/AiTool (SME class definitions = HITL), BRD outline (later
    phase, user call), docmeta P1–P3 (P0 written verdict + ADR 0004), EE container password
    (user deferred), LLM key strategy (open user question), common/ in /list-apps (cosmetic),
    cli.py regroup (v1.0 rename window).

- 2026-07-10 groom run (G3-close session) — 0 promoted / 1 inboxed / 1 kept-updated / 0 merged:
  - inboxed: remediation next slices (Tier-2 FR-REM-4 gated on OQ-2/OQ-4; XML I/O on schema
    acquisition; A3/B1 company-side) — deliberately NOT itemized; the TDD §6/§7 tracks them,
    groom when their gates open.
  - kept-updated: the Phase-C packaging line — G3 closed IN-MONOREPO so its early-promotion
    trigger (a) expired unfired; the line waits for Phase C proper.
  - all other inbox lines remain parked on their recorded gates (no change today: Workbench/
    entitlement, SchedulerKind/SME classes, BRD, docmeta/P0-verdict+ADR-0004, container
    password, LLM keys, common/ cosmetic, cli regroup/v1.0 window, testcontainers).
  - backlog database untouched this run (G3/G10 changes landed in-session pre-groom:
    G3 done 46, G10 ready — see commits ca9f165..ef57602).

- 2026-07-09 — [idea] design-doc feedback: per-subsection annotate controls when a section
  has >2 subsections (1.a/1.b/1.c… or steps 1/2/3) so feedback keys to the exact subsection
  → **L11**. (chat note, same review pass as L10; design core = stable derived sub-anchors)
- 2026-07-09 — [idea] design-doc feedback widget: appendix "SME - Feedback" panel (divider +
  static HITL how-to: annotate, Copy feedback, create docs/design/feedback/<doc>-rev<N>.yaml,
  paste, save) → **L10** (amended same day: instruction block, not a free-text notes field).
  (chat note after reviewing docs/design/feedback/scans/; answered the open question — the
  export is .yaml per feedback_yaml, not markdown)
- 2026-07-09 groom run (Opus session) — 4 promoted / 1 retired; web/ became a plan change:
  - [chore] repo `.venv` has no pytest / poetry not on PATH → **RETIRED (resolved this session)**:
    pipx + Poetry 2.4.1 installed, in-project `.venv`, dev deps synced; `poetry run pytest -q`
    → 453 passed / 3 skipped. The documented gate now runs. (See memory `drydocs-python-toolchain`.)
  - [doc] `run-drydocs/SKILL.md` stale Gotchas → **J4** (Epic J, phase 8). Verified 2026-07-09:
    still claims "PyYAML not installed" (×2), "159 pass", Aura, and `apply-m3-supplement` — all stale.
  - [chore] CI (GitHub Actions gates + classification publish-boundary guard) → **J5** (user
    confirmed promote 2026-07-09).
  - [chore] unused deps → **J6** (Epic J), **scoped after verification**: only `streamlit` +
    `streamlit-agraph` are dead; `pandas` is intentional (`csv_adapter.py`) and `pypdf` is now used
    (`scripts/ingest_jpmc_reports.py`) — the original note's "imported nowhere" claim corrected.
  - [idea] web/ front end → **O1** + NEW module `drydocs-web` + NEW **phase 12 "Web console /
    graph visualization"** (plan change, user-approved). Marked in_progress — design pass in flight
    (branches `feature/ui-dark-landing-myapps` + `feat/web-console-design-pass`, untracked `UI-WIP/`).
  - Kept parked: BRD outline (later phase), `drydocs-docmeta` plan (gated on the P0 benchmark verdict
    + ADR 0004), the `<password>` EE container (deferred), LLM-key strategy (open question), `common/`
    in `/list-apps` (cosmetic), cli.py regroup (gated on the v1.0 rename window), and the testcontainers
    integration test (testcontainers[neo4j] confirmed unused; not selected this run).

- 2026-07-09 — [chore] Versioning reset (parked since 2026-07-01) → **J3** (Epic J, phase 8),
  executed same day: adopted SemVer (VERSIONING.md), bumped pyproject 0.1.0 → 0.3.0, back-filled
  CHANGELOG.md from the completed epics, cut annotated tag **v0.3.0** (user decision over v0.2.0 —
  matches plan phase 8's `release:` field). Sibling parked lines (CI, cli.py regroup, unused-dep
  removal, integration tests) stay in the inbox.

- 2026-07-09 groom run (this session) — weekly inbox groom, 2 promoted / 5 retired / 2 kept-updated:
  - [doc] README still says `:DEPENDS_ON` for the derived job→job edge → **J2** (Epic J, phase 8).
    VERIFIED 2026-07-09: the loader `controlm_dependencies_derived.cypher` MERGEs `:WAS_INFORMED_BY`
    and vocab `m3_was_informed_by` is active ("Replaces DEPENDS_ON") — README is the stale side
    (4 refs: README.md:16,139,152,231). Naming-drift doc hygiene, same class as J1.
  - [idea] `REQUIRES_SCHEDULER` (:BatchProcessing → :SchedulerKind) unregistered → **C6** (Epic C,
    phase 2 — re-opened). VERIFIED 2026-07-09 still absent from `relationship_vocabulary.yaml`;
    register `status: planned` + HITL gate before wiring the post-load step (edge-meaning ⇒ gate).
  - [idea] **T1** vendor-doc KG traversal benchmark → SUPERSEDED by the `drydocs-docmeta` plan (its
    P0 spike) AND substantially executed: the bmc-docs lexical loader (Document→Chunk,
    llm-graph-builder) shipped + gate `bmc-docs-lexical-load` ACCEPTED 13/13, LOADED LIVE (commits
    `12423f4`/`24d6a4b`). Written benchmark verdict + ADR 0004 still pending before P1–P3 promote.
  - [source] **T2/T3/T4** internal-platform / product-process / SME-context ingestion → ABSORBED into
    the `drydocs-docmeta` sequenced plan (`knowledge/upgrade-plans/docmeta-component.md`, phases
    P0→P7); tracked there until the P0 verdict + ADR 0004 gate, per the docmeta note's own instruction.
  - [bug] `node_classifications` ControlMFolder-vs-`:JobFolder` drift → CLOSED (already RESOLVED
    2026-07-05, ADR 0003 + rename migration); the struck line is retired from the inbox.
  - kept + updated in-inbox: the `drydocs-docmeta` plan note (records the bmc-docs load; T1–T4 folded)
    and the web/ front-end note (flagged the now-active design-pass branches). Parked pending user
    decisions (semver start, CI, cli.py regroup, unused-dep removal, integration tests), open
    questions (LLM key strategy), and piggyback chores stay in the inbox.


- 2026-07-08 groom run (this session) — **new phase 11 "Source governance ledgers"** + 9 items:
  - [question] SEAL ontology reshape + scraped-docs source-of-record → **K3** (gate session;
    K2 gains `depends_on: K3` — the wasAssociatedWith/Entity type conflict means the reshape
    gate runs before the match-policy gate is ticked). Prep was already on main (`0986d6d`).
  - [bug] design-doc HTML Chrome-vs-Brave render discrepancy → **L9**.
  - [idea] provenance diet + source audit fields (2026-07-05) → **M1–M3** (doc-06 Phases 2–5;
    Phases 0–1 shipped 2026-07-07 pre-groom via gate `controlm-q1q3-phase1` + commit `62673ed`).
  - [idea] property-level ontology terms for the audit envelope (2026-07-07) → **M4**.
  - [question] same-row-derived node relationships (city/state/country, 2026-07-07) → **C5**
    (re-opens phase 2 — methodology gap).
  - [idea] source column mappings (doc 08, 2026-07-07) → **N1–N2** (Phases 0–1 per the plan's
    own groom note; later phases stay in the plan doc).
  - [idea] TechStack software registry (2026-07-07) → CLOSED, executed directly as plan-07
    (Phases 0–2 done `caa1e79`/`eb0fe56`; Phase 3 at the software-usage-patterns gate; Phase 4
    deferred). Not backlog-itemized — the plan doc tracks it; itemize the P3 build when its
    gate passes.
  - [idea] "Application contains folders" support view (2026-07-01 review) → SUPERSEDED by the
    gate-confirmed header-row design (`controlm-q1q3-phase1` + `107581d`): ControlMApplication
    + CONTAINS_FOLDER now load in the folder pass from CM_DEF_VJOB JOB_ID=1 — NOT derived from
    per-job APPLICATION reconciliation as the line proposed (that column stays informational).

- 2026-07-08 — Epic L (**documentation infrastructure**, new phase 10) groomed into `backlog.yaml`
  from the deterministic-documentation design conversation. Canonical per-doc-type outlines (stable
  anchors = the render/traceability/HITL id namespace), md-as-source deterministic render, and the
  digital + pen/paper markup loop. `tdd.outline.yaml` drafted same day (L1 in_progress). New module
  `drydocs-docgen`. Sequence (user-set): TDD (L1) → render/feedback (L3–L7) → Runbook (L8, capstone);
  runbook resequenced from L2 → L8. BRD parked above (later phase). Distinct from the
  `drydocs-docmeta` ingestion idea (2026-07-06).
- 2026-07-01 — [source] seal_app_ref attribution → **K1 + K2** (Epic K, phase 9). CORRECTED
  during grooming by the company reconciliation answers: the edge is spec-level on BOTH sides
  (their FR-NS-013/UC-NS-005 docs read ACTIVE with no loader/vocab/gate behind them); the feed
  is STG_APP_FACT semantic facts, NOT job.APPLICATION (explicitly unreliable for SEAL identity).
  Promoted as build items with the company's write shape, gate sequence, and verify shapes.
- 2026-07-01 — [chore] fragment cleanup (naming drift, banners, SDLC-Docs README) → **J1**
  (Epic J, release-infrastructure) via the groom-backlog skill's demonstration run. Sibling
  lines (versioning reset, CI, cli regroup, unused deps, integration tests) stay in the inbox
  pending user decisions (semver start version, rename window).
- 2026-07-01 — Epic I (I1–I4, project board & planning infrastructure) groomed into `backlog.yaml`
  from the architecture-review plan; schema upgraded to `drydocs.backlog.v2` (I1 done same day).
- 2026-06-20 — initial backlog A1–F2 seeded directly into `backlog.yaml` from `02-backlog.md`.
- 2026-07-09 groom run (remote session) — 8 promoted / 0 inboxed; PLAN CHANGE: new phase 13
  "Runtime topology & maintenance windows" + Epic P (ratify — the phase-12/O1 precedent):
  - CM_HOSTS + CM_AVG_RUN onboarding (add-source-object walkthrough ×2; hosts gate SIGNED OFF
    18/18, avg-run gate awaiting SME) → **P1** (internal probes + DC scope call), **P2**
    (avg-run gate session, in_progress awaiting HITL), **P3** (hosts loader + RUNS_ON
    resolution pass), **P4** (avg-run property-supplement loader + job-name index),
    **P5** (the maintenance-window query — the driving use case).
  - Port-boundary tech-debt audit (docs/reviews/tech-debt-port-boundary.md) → **J7** (per-entry
    reconciler guards) + **J8** (skip-guard policy test); Phase-1 PORT-MANIFEST.yaml + guard
    EXECUTED pre-groom (5cfcfa7) — no item, the doc-06 precedent.
  - Taxonomy-ontology-map audit (docs/reviews/tech-debt-taxonomy-ontology-map.md) → **C7**
    (vocab_id + capture fields at the next gate); F1–F4 fixes EXECUTED pre-groom
    (c396d75, ede0b94).

