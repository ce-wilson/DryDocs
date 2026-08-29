# Deepdoc — the data-flow overview record, grounded in one production deep-dive

<!-- anchor: front-matter -->
**Status:** PROPOSED — synthesis of one support-driven investigation, **Rev 1, 2026-08-21**. Nothing
here changes the graph; every label, edge, and field below is `status: planned` until the named HITL
gate rules it. ·
**Classification:** Internal-Public — mechanism only. Every real value (SEAL ids, job and folder
names, hosts, URLs, Jira keys, people, distribution lists) is replaced by a role placeholder:
`APP_ID-producer` / `APP_ID-consumer` / `APP_ID-downstream` for applications, `<JIRA-nnnn>` for
issue keys, `Auto` for the SDLC project/space, `<job-preproc>` … `<job-trust>` for jobs,
`<folder>` for the folder, `<DATAFLOW>` for the launcher data-flow name, `<support-DL>` for
distribution lists. The verbatim record lives machine-local under
`internal-local/deepdoc/2026-08-20-session-1/transcripts/` (eight `*-capture.md` files and
`related-backlog.md`); tracked surfaces cite those files by name. ·
**Audience:** the SME ruling the `data-flow-overview` gate; the engineer building epic **MM**;
application-support readers who want to know what this module will answer for them. ·
**Companion:** ADR 0006 (deepdoc = corpus consumer, ruled 2026-08-18 at gate
`document-content-topology` §E: *a corpus-driven retriever seeded from the grounded graph*); ADR 0011
(`:Uncertain` label discipline, `tests/unit/test_uncertain_boundary.py`);
`.claude/skills/controlm-runbook-automation/references/plan.md` (the "data series" traversal);
`docs/patterns/data-catalog/lineage-design-top3.md` (the designed-never-built `:AppDataFlow`);
`knowledge/standards/technology/controlm-greenfield-job-standard.md` (the `%%DATAFLOW` grain);
`internal/remediation/standards-rules-registry.md` rule **R13** (the FW/API gotcha).

> **Read-me-first.** A support analyst spent one evening answering a single question about a single
> Control-M folder — *what is this flow, why does it exist, and why does it keep failing?* — across
> email, the Control-M client, Jira, Bitbucket, Confluence and a chat assistant. Every answer existed
> somewhere; none of it was in one place, and the job names actively misled. This document turns
> that evening into (1) the **record** DryDocs should hold per data flow, (2) the **log substrate** that
> can fill the fields the command line cannot, (3) the **remediation signal** the evening exposed, and
> (4) the **method** the deepdoc module should implement. Each section ends with what is SOURCE,
> what is DERIVED, and what goes to the gate.

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Specify the per-data-flow overview record — the one artifact the investigation proved
missing — and charter its first producer, the `drydocs_deepdoc` module, in concrete terms the
G32 ruling left open.

**In scope.** The record's fields and their provenance; the Control-M **Output-tab** log as an
enrichment pass over CMDLINE lineage; rule R13's second consequence; the SDLC traceability findings
(what Jira, Bitbucket and Confluence can and cannot anchor); the investigation method as a
reproducible skeleton; the open questions for the gate.

**Out of scope.** Code. The backlog items that build any of this are minted separately under
epic **MM**; the gate prompt that rules the record's vocabulary is its own artifact
(`config/gate-prompts/data-flow-overview.yaml`, item MM2).

---

<!-- anchor: the-use-case -->
## 1. The use case — one flow, end to end, as support experienced it

**Trigger.** A support thread: a daily pre-processing job failed for one order date with
`curl: (92) HTTP/2 stream 0 was not closed cleanly: INTERNAL_ERROR` and `ERROR: API data pull step
failed`; it was re-triggered and completed; five days later it failed again with the same error.
The thread carried three distribution lists (two consumer-side support tiers, one producer-side API
team) and no incident number. Nobody on the thread could say what the data *was* or why the job
pulled a **full** extract every day instead of a delta.

**What each surface answered — and what it could not.**

| Surface | Answered | Could not answer |
|---|---|---|
| **Email thread** | The failure signature, the retry history, who is on the hook (`<support-DL>`s), that the job is an **API pull** | What the data is; why full-not-delta; which other jobs depend on it |
| **Control-M client — folder Synopsis** | The folder's *Description* carried the business context in free text: the new system of record replaces a legacy flat file and is now **pulled by web API**; the successor folder belongs to a different application (`APP_ID-downstream`) | Nothing machine-readable: the ingest mode lives in prose |
| **Control-M client — job Output tabs** | Everything the names hide (see §3): the shell wrapper, the API endpoint and query, the three files the pre-processor writes, what each FileWatcher actually watched, the launcher's own statement of the job **kind** (`PLACEMENT`, `INGESTION`, `TRANSFORM`, `PROVISION`), the pipeline and dataset GUIDs, the run-scoped handoff id minted at placement and threaded to the consuming ingestion, the landing prefix | Ownership, business purpose, SDLC history |
| **Jira (`Auto` project)** | 64 lexical hits; two "twin" build stories scored highest on relevance and said only *script → preprocess → `.ctl`/`.tok` → UAT → prod*; the real business *why* (a conversion that missed fields → a regulatory report over-counted → SLA breach) sat in a lower-ranked **epic**; an enterprise change program listed the consumer application in a SEAL→application table | The project is a **COLLABORATION**-type DevX project with **Primary SEAL Application: N/A** — it cannot be joined to the application through the SDLC binding, it is owner-deletable, and issue keys never appear in source |
| **Bitbucket** | Searching issue keys in code returned **0/0/0 across three projects by design**; the win came from a *commit inspect* on a known commit — author, date, issue key in the message, one added file = the folder XML promoted from a staging path to production | Nothing without a commit hash or a folder name as the entry point |
| **Confluence** | The owning team's designated space returned **0** pages; firm-wide search returned ~1,800 and the decisive page was in the **producer's** space: a *TDQ Producer & Consumer* register listing the outbound feed to `APP_ID-consumer`. That page resolved the producer (`APP_ID-producer`) and split producer from consumer | The register documents the **legacy file feed**; the Control-M description says the feed is now an API pull — the inventory that exists is stale |
| **Chat assistant (research log + mind map)** | Held the *central question*, tracked open slots (`?`), forced the identifier decomposition `<folder>` → application? zone? cadence?, and recorded the turn from "lexical match" to "entity resolution" | It could not fill the one slot that needs a human design rationale: **full vs delta** |

**The two findings that make this a DryDocs problem, not a one-off.**

1. **The name token cannot tell an API pull from a pushed file — because the token was misused.**
   This folder holds a `_PREPROC` job, two `_FW` FileWatchers (`DAT` and `TOK`), a `_PLCT`
   placement and a `_TRUST` ingestion; the count varies by flow and team. SME ruling (2026-08-21):
   `_PREPROC`'s intent is *file preparation* — cleaning special characters and whitespace,
   splitting, downloading an already-delivered file, prepping for ingestion — **not** calling an
   API. API pulls were meant to carry their own, deliberately non-intuitive tokens: **`_DLMD`**
   (download external data) or **`_MON`** (monitoring API). Teams reused `_PREPROC` for the pull,
   so the downstream shape looks like a file-push flow. The watchers were written for an inbound
   file transfer. Here the pre-processor
   **writes** the `.csv` and `.tok` to the local drop directory itself, and the watchers then
   "watch" files that already exist on the same host (`File … exists, it's current size is …`,
   then a two-minute size-stability confirmation). The TDQ token the watcher gates on was produced
   by the same process that produced the data — it reconciles a count against itself. Whether the
   watchers are *unnecessary* or *faked* is the SME's call (§4); that the **name does not tell
   you** is a fact.
2. **SDLC traceability has a hole at the application boundary.** Jira keys do not reach code;
   collaboration-type projects do not reach the application id; the one reliable chain was
   *commit → author → issue → epic → business justification*, entered from the Bitbucket side.

---

<!-- anchor: data-flow-record -->
## 2. The data-flow overview record (proposed shape)

Three grains already exist in the repo and were never reconciled:

| Grain | Where | Identity | Status |
|---|---|---|---|
| `%%DATAFLOW` sub-folder | `drydocs_core/orchestration/controlm/variables.py`, `attribution.py`; greenfield standard "sub-folder = `DATAFLOW` = `DS_ID`" | the Control-M variable value | built as a variable fact, no node |
| `:AppDataFlow` | `docs/patterns/data-catalog/lineage-design-top3.md` (DataHub `dataFlow` analogue) | `dataflowUrn` | designed, zero code, zero vocabulary |
| "data series" | `controlm-runbook-automation/references/plan.md:71-79`; `drydocs_api/query_specs.py` `runbooks.series.v1`; web module `runbooks` | a traversal from each `_FW` along `WAS_INFORMED_BY` | derived per query, no persisted identity |

The investigation supplies the missing fact: the launcher itself names the flow (`-dataflow <DATAFLOW>`
on the command line, `"DataFlow": "<DATAFLOW>"` in the task-service request) and that name is shared
by every DPL job of the flow across zones and **across applications** (the ingestion in
`APP_ID-consumer`'s folder and the transform in `APP_ID-downstream`'s folder carry related flow
names). The `%%DATAFLOW` grain is the right key. `:AppDataFlow` supplies the URN grammar and the
parent edge; the "data series" traversal supplies the membership.

**Proposed record.** One `:DataFlow` node per `<DATAFLOW>` value (label and every edge below are
`status: planned`; the gate may rename). Provenance badge: **SOURCE** = read from a named source
object; **DERIVED** = computed by a named rule.

| Field | Provenance | Source / rule |
|---|---|---|
| `flow_id` (URN `urn:drydocs:dataflow:controlm:<DATAFLOW>`) | SOURCE | `%%DATAFLOW` variable; launcher `-dataflow`; task-service `DataFlow` — three readings of one value, recorded with which ones agreed |
| `owner_app` → `(:Application {APP_ID})` | SOURCE | launcher `-seal`; task-service `spark.kubernetes.seal`; folder-name token (precedence per `config/precedence.yaml`) |
| `producer_app`, `consumer_app` | DERIVED, then SME | producer from the upstream register / API host owner; consumer = `owner_app`. The investigation shows these are **different applications** and that the distinction is the single biggest unlock |
| `ingest_mode` ∈ `api-pull \| file-push \| internal-generated \| unknown` | DERIVED | **never from the name token.** From the pre-processor's resolved command (an HTTP client call = `api-pull`; an MFT/SFTP route id = `file-push`); from a `FileWatcher` whose watched path was written by a predecessor in the same folder (`internal-generated`); else `unknown` — and `unknown` is an honest value, not a default |
| `zone_chain` | DERIVED | ordered folder/job zone tokens along the series (`ONPM → TRUST → RFND → PROV`) — the existing series traversal |
| `members` → `(:ControlMJob)` | DERIVED | the series traversal seeded from the flow's jobs, filtered to the `<DATAFLOW>` value |
| `pipeline_ids[]`, `dataset_ids[]` | SOURCE | CMDLINE `-pipeline` (G15 contract) **and** the Output-tab log (§3) — the log is authoritative when the command line carries a variable |
| `launcher_kinds[]` | SOURCE (log) | `Identified '<KIND>' Job` per member — the kind discriminator G12 wanted, read from the launcher's own assertion |
| `compute_target` | SOURCE (log) | `PROVISION … executes on GKP not EKS`, `spark.namespace.alias`, cluster id in the submission response |
| `placement_handoff` | SOURCE (log) | placement response `provenanceGuid` → the `-proId` of the ingestion that consumes that placement. **Scope is exactly those two jobs** (SME ruling 2026-08-21): the service mints the guid at job run, so it is a run-scoped correlation token, **not** provenance in the PROV-O sense and **not** usable to validate Control-M lineage. A downstream hop logging `No provenanceId is provided!` is expected-absent, not a break; the guid never keys an edge or identifies a flow |
| `landing_prefix` | SOURCE (log) | `<APP_ID>/raw/<dataflow-name>/<provenanceGuid>/<file>` |
| `watchers[]` with `load_bearing: true\|false\|unruled` | DERIVED + SME | present/absent from members; *load-bearing* is R13's second consequence (§4) — proposed by rule, **ruled** by the SME |
| `tdq_self_asserted` | DERIVED | `true` when the token file and the data file share a writer |
| `sdlc_anchors` | SOURCE + SME | `{ jira_project, jira_binding: collaboration\|seal-bound\|none, bitbucket_projects[], confluence_spaces[] }` keyed one `APP_ID` → many projects/spaces; `jira_binding` read from the DevX project page |
| `support_dls[]`, `producer_contact` | SOURCE | email corpus (Q10) headers + the folder's escalation row |
| `business_purpose` | SME | free text, **cited**: the Jira epic / Confluence page that states it |
| `open_questions[]` | SME | e.g. *full vs delta* — a slot the graph cannot fill, kept visible |
| `evidence[]` | SOURCE | breadcrumbs: `email:<extract-id>`, `log:<job>/<run>/<line-range>`, `jira:<key>`, `commit:<sha>`, `confluence:<page-id>`, `transcript:<file>` — PROV-O `prov:wasDerivedFrom` |
| `reliability`, `trust`, `:Uncertain` | mandatory | ADR 0011 clause 1 — every deepdoc write carries them; promotion is a gate write, never a label strip |

**Edges (all planned):** `(:Application)-[:HAS_DATA_FLOW]->(:DataFlow)`,
`(:DataFlow)-[:ORCHESTRATES]->(:ControlMJob)` (from `:AppDataFlow`),
`(:DataFlow)-[:FED_BY {feed_name}]->(:Application)` producer side,
`(:DataFlow)-[:LANDS_IN]->(:DataAsset)` the snapshot/target table,
`(:DataFlow)-[:EVIDENCED_BY]->(:Document|:Chunk|:EmailMessage|:LogExcerpt)`.
The first two reuse terms the pattern doc already proposed; the rest are new and go to the gate
with the record.

**What the existing inventory workbook already holds** (folder/job grain, ~8k rows): application
id, SOR/app name, zone, Control-M server, group, job, file name, SOR contact, SNOW CI, SLA,
business impacts — with the last three **blank** on every captured row and the file-name cell
copy-filled across jobs that write different files. A second sheet at the **feed** grain (feed →
folder → refined jobs → frequency → warehouse/DB/schema → work/target/view table → publish target)
is closer to this record and is the natural import seed; its blanks (*Is Risk*, SLA) are exactly the
SME fields above.

---

<!-- anchor: log-substrate -->
## 3. Log-substrate enrichment of CMDLINE lineage (iteration 2)

The G15/G16 launcher contract reads the **command line**; the Output tab shows the command line
*resolved* plus what the launcher did with it. Side by side for one placement job:

| CMDLINE says | Output tab adds |
|---|---|
| `%%PY_LAUNCH -env %%ENV -dataset %%DS_ID -version %%DS_VER -pipeline <GUID> … -tokFile %%TOK_FILE -conf %%CONF_PATH` | every `%%` variable resolved (dataset GUID, version, both file paths, FID, config path) — G46's resolver gives the same answer *when the variables are in the export*; the log gives it regardless |
| nothing | `Identified 'PLACEMENT' Job` — the job **kind** |
| nothing | the placement URL, the credential providers consulted, the two identity-provider client/resource pairs |
| nothing | the response: `provenanceGuid` (run-scoped, see the field table), `rowCount`, then a poll of two landing targets until `COMPLETED`, with the landing keys |
| nothing | a production bearer token printed into the job output by the pre-processor wrapper (`set -x` on) — a finding for the owning team, recorded here as a mechanism risk, not a value |

**Where the job identity comes from — the file name, not the log.** The modern launcher wrapper
writes no job name or run metadata into the Output body; a first run against real logs showed the
job blank on all eleven. These are standard Control-M sysout files, and the identity — job name,
order id, date, run stamp — is carried by the **file name**. Identity is therefore the one part of
the record whose source is the file rather than its contents, with three consequences: the
extractor's input is a *named file*, never a detached text blob, because the name carries the
`<job, order-id, run>` key it joins on; the reader is a tolerant scan with a site-pinnable override,
because sysout naming varies by site; and the name's date field is recorded as `run_date` and is
**not** merged into the launcher's `-od` `order_date`, because on real logs the two differ and which
one the name carries is an open question for the estate.

**Proposed extractor** — a `controlm_output` module in the lineage extractor package,
**PLANNED and not yet written** (backlog MM7 writes it; the path is deliberately not cited
here, because a citation is a claim that the file is in the tree). Same shape as
`dpl_mac.py`: it never creates the seed; it joins onto `:ETLProcess` rows another extractor already
staged **on the pipeline GUID** (falling back to `<job, run>` when the command line carried only a
variable), and it returns an `OutputCoverage` dataclass counting every skip by reason (`no_launcher_banner`,
`kind_unknown`, `guid_mismatch_vs_cmdline`, `truncated_json`, `token_redacted`). Facts it emits onto the
process (all properties, no new edges without the gate): `launcher_kind`, `compute_target`,
`provenance_guid`, `landing_prefix`, `submission_cluster`, `image_digest`, `compute_profile_ref`.
Input = the Output text per `<job, order-id, run>`; acquisition path declared per Idea-133
(`mode: manual | automated`, `via: api | db` — the CM replica's sysout tables if present, else a
hand-staged drop).

**Why it is an input to deepdoc and not a deepdoc feature.** G32 §E ruled the parser-driven
command-line reading *an input* to the retriever; the log reading is the same class of input, one
layer richer. It lands in `drydocs-lineage` (curated, ground-truth after gate) and deepdoc **cites**
it (`evidence: log:<job>/<run>/<lines>`).

**Iteration 3 (named, not built):** the run-history side — `CM_HIST` / average-run tables already
loaded (P4) — joined to the same `<job, run>` key, so a flow's record can show its last failure,
its retry, and its SLA window beside its mechanism. The chained multi-extractor run and
`curation.py`'s cadence are the shared prerequisite (item MM7).

---

<!-- anchor: remediation-signal -->
## 4. Remediation signal — R13's second consequence

Rule **R13** (*name token matches derived intent — the FW/API gotcha*) already says: flag a `_FW`
that is in fact API-triggered via a predecessor, and **retoken** it. The evening adds a second
consequence and a sharper test:

- **Test (DERIVED):** a FileWatcher is *internally fed* when its watched path equals a path a
  predecessor in the same folder **writes** (the pre-processor's output file names are in its log
  and in its command). An internally fed watcher's only remaining function is the size-stability
  wait; its TDQ token is self-asserted.
- **Consequence (SME-ruled, never auto-applied):** per flow, mark each watcher `load_bearing:
  true | false | unruled`. `false` proposes a greenfield transform (drop the watcher, keep a
  post-write checksum/row-count step on the producer side); `true` keeps it with the reason
  recorded; `unruled` is the default and the board shows it.
- **Caveat (SME, 2026-08-21) — the watcher and the TDQ step are separate questions.** On an
  API-pull flow the `_FW` may simply not be needed. The TDQ validation needs its own review: it is
  either (a) not needed on this flow, or (b) **masking the fact that no validation happens** — the
  token count it compares was written by the consumer's own pull, not sent by the source. A TDQ step
  that passes against a self-produced token is not evidence of integrity; it reads as evidence. The
  record therefore carries `tdq_self_asserted` beside `load_bearing`, and the gate rules both: keep,
  drop, or replace with a source-sent count (the producer's register already lists structural /
  completeness / timeliness methods per feed — that is where a real token count would come from).
- **Greenfield token (SME-ruled):** R13's "retoken to match intent" now has a target — an API
  pull is `_DLMD` (download external data) or `_MON` (monitoring API), never `_PREPROC`; the
  `_PREPROC` token is reserved for file preparation. The token pair goes to the greenfield job
  standard as a `planned` vocabulary entry before any detector proposes it.
- **Carrier:** `ingest_mode` must become an explicit fact the job carries — a description-metadata
  key (`ingest.mode=api-pull`, under the C16 key-prefix governance) or a folder variable — so the
  next analyst does not rediscover it from a log. The name token stays what R13 says it is: not
  evidence.
- **Dependency:** Idea-31 parked the company greenfield rules "until the remediation M2
  generalization opens"; this consequence is the first producer-modeled rule of that family and
  un-parks exactly that clause (item MM8).

Two further defects the logs surfaced belong in the same batch, as **findings** not rules: a
placement job whose *Description* names a different dataset than every runtime artifact (stale
copy-fill), and a production transform submitted with `appname`/`namespace alias` literally `test`.

---

<!-- anchor: sdlc-traceability -->
## 5. SDLC traceability findings

| Finding | Consequence for the model |
|---|---|
| A DevX **collaboration**-type Jira project has *Primary SEAL Application: N/A* — no application binding, owner-managed permissions, no SDLC-fabric tie | `sdlc_anchors.jira_binding ∈ collaboration \| seal-bound \| none`; a collaboration project is a **signpost**, never an ownership source; the `APP_ID → project` map is SME-entered and dated |
| Lexical relevance ≠ information value: the two top-scored stories were build-task records; the business justification was in a lower-scored epic, the ownership table in a cancelled epic | the search log gets a `novelty` column beside `match_confidence` and a `signpost` flag (3-tool plan A); the retriever ranks by *which open slot a hit fills* |
| Issue keys do not appear in source; code search of keys is 0 by design; **commit inspect** by hash or by folder-file path is the productive path | Bitbucket connector: `commit/analyze` primary, folder-name input accepted (plan B); the `repo-objects-manifest` row (G63) is the producer-side seam |
| The owning team's Confluence space held nothing; the decisive page was in the **producer's** space and its title carried the producer's application id | Confluence connector firm-wide by default, reports space distribution, auto-extracts `APP_ID` tokens from titles (plan C) |
| The same identifier (`Auto`) names a Bitbucket project and a Confluence space | the cross-reference key is `APP_ID` (one) → many `{system, project-or-space}` pairs, each a separate fact with its own evidence |
| An available join nobody consumes: the PAT team report already carries a Jira board per team beside application ids (`internal/pat-evidence/`) | seed for `sdlc_anchors` before any scrape |

The three per-tool search scripts built during the session (one each for Jira, Bitbucket,
Confluence; shared CSV log keyed off `DRYDOCS_LOGDIR` with `tool / search / theme / results / date`)
are the **connectors-in-waiting**. They re-home as mechanism-only deepdoc connectors with real
hosts/config in `internal-local/` (item MM5); their shared "IDs in → references out" contract is the
entity/ID extractor of §6.

---

<!-- anchor: the-method -->
## 6. The method — graph-seeded retrieval in practice

What actually moved the investigation, in the order it happened:

1. **Central question as evaluation criterion.** Every hit judged by *does this explain the
   business context or the implementation?* — this demoted the high-scoring twins.
2. **Mind map as the backlog.** Branches = slots (business / naming / Control-M / lineage /
   ownership / references); trailing `?` = open slots; the next search targets the next `?`.
3. **Identifier decomposition.** `<folder>` → `{application-id?, process, zone?, cadence?}` turned a
   string into *things to chase*.
4. **Application-id chase across sources**, which produced the SEAL→application table.
5. **Producer/consumer split** — entity resolution, the biggest single unlock.
6. **Business justification → mechanics**, then the email to ground the failure.
7. **Cross-source triangulation:** the same ids recurring in independent sources raised
   confidence in *meaning*, which no single-source score can.

Net: *the score got to the neighborhood; novelty + entity extraction + gap tracking got to the
answer.* Build-time facts (UAT → prod promotion) were separated from run-time lineage — a
correction worth encoding: `evidence` carries `phase: build | run`.

**Skeleton for `drydocs_deepdoc.investigate()` (item MM10):**

```
seed      = grounded graph lookup (folder | job | APP_ID | file name)      # never a free string
slots     = mind-map state: the record fields of §2 still `unknown` for this seed
loop until no slot changes or budget spent:
    pick the open slot with the highest expected novelty
    run the connector(s) that can fill it, carrying IDs in → references out
    extract entities; score hits by (match_confidence, novelty = new ids vs graph+record, slot filled)
    write ContextFinding(subject = existing proxy node, predicate, object, reliability, trust,
                         evidence = breadcrumb, phase) — :Uncertain, never a new subject
    append (tool, search, theme = slot, novelty, results, date) to the search log
hand the record + open slots to the SME gate; promotion is a gate write
```

The loop is ADR 0006's charter made procedural: seeded from the graph, creates nothing whose subject
is not already there, cites the corpus, and leaves the human the slots only a human can fill.

---

<!-- anchor: open-questions -->
## 7. Open questions for the SME gate

1. **Label and key.** `:DataFlow` keyed on `<DATAFLOW>`, or fold into `:AppDataFlow`'s URN? Is
   `<DATAFLOW>` unique firm-wide or per application (the evidence shows one application's flow and a
   downstream application's *related* flow names)?
2. **`ingest_mode` enum** — the four values above, or a richer set (API pull, MFT push, SFTP push,
   DB extract, internally generated)?
3. **Watcher and TDQ ruling for this flow** — are the two internally fed watchers load-bearing? Is
   the TDQ step needed at all, or is it masking the absence of a validation (it compares a token the
   consumer's own pull wrote, not one the source sent)? If the watchers go, is "drop + source-sent or
   producer-side count" the greenfield, or does the FileWatcher remain the standard's required shape?
4. **Full vs delta** — the slot no source filled; the snapshot table suggests full-by-design, the
   regulatory report suggests completeness, the API may offer no delta. The full pull is also what
   breaks the HTTP/2 stream. Human design rationale required.
5. **Provenance breadcrumb grammar** — `evidence_ref` as a URN per source kind, or reuse
   `prov:wasDerivedFrom` to `:Document`/`:Chunk` nodes for every kind (which means email messages
   and log excerpts become corpus documents first)?
6. **Where the stale legacy feed register lives in the graph** — as a dated `:Document` the record
   cites with `superseded_by`, or as a retired `FED_BY` edge with an `as_of`?
7. **Security finding routing** — a bearer token printed to job output is out of DryDocs' scope to
   fix; which surface records it for the owning team without the value ever entering the graph?
