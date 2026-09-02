---
name: research-probe-discipline
description: "The shared backbone for DryDocs research sessions — the SME context interview, the probe-outcome vocabulary, the positive-control rule, the probe log, and the shared ledgers (source whitelist, terms, platforms, id shapes) that stop a session re-discovering what the last one settled. Use whenever a research session searches ANY source and might record an absence, a dead end, or a 'not found'. Loaded by research-general, research-job-failure and research-job-lineage; use it directly for one-off lookups that still need their negatives to be trustworthy."
---

# research-probe-discipline

The backbone every DryDocs research skill sits on. It exists because of one measured failure
mode: **a session records an absence as a property of the platform when it is a property of
the artifact in hand.** One reviewed trace did it six times in two days.

This skill owns four things — the interview, the outcome vocabulary, the controls, and the two
ledgers. It owns no subject matter. Pair it with `research-general`, `research-job-failure` or
`research-job-lineage`.

**What this skill leans on producer-side.** The company build of this method cited two
companions — a `research-scaffold` agent (the two-phase log, the `?`-node hinge, the hop
ledger) and a `source-probe.md` template (the capture ladder). Neither exists in this repo, so
the three things they owned are stated here in the shortest form that lets a session run:

- **The `?`-node hinge is the mind-map state file** — `drydocs_deepdoc.mindmap`, schema
  `drydocs.deepdoc.mindmap.v1` (MM3): a root question, named branches, and slots that are
  `open` (the trailing `?`) or `filled` with an evidence ref and a date. A slot cannot move to
  `filled` without an evidence ref, and the file refuses to load if one did. The next search
  targets the next open slot. *Where it lives, as of 2026-09-02: MM3 is `done` on the branch
  `feat/mm-deepdoc-investigate`, not yet merged — a reader on `main` will not find the module
  until that branch lands, and until then the hinge is the log's Open-questions section.*
- **The log shape**, by worked example: `internal/research/JOB-MFTS-MM-research.md` — YAML
  front matter (`central_question`, `subject`, `venue`, `sme_context`), a **Brain-map**, a
  **Trace ledger** of numbered hops (H-n), **CORRECTION** blocks that strike a hop in place,
  **Gotchas** (G-n), **Predictions** recorded before the evidence, **Open questions** (OQ-n, the
  SME's to rule), **Acronyms & terms** with a confidence column, and a dated **Notes log**.
- **The capture ladder**, five rungs: 1 spec / bulk export · 2 authenticated API · 3 saved
  HTML · 4 print / PDF · 5 copy-paste. Every claim carries the rung it was captured at.

---

## 1. Open with the SME interview — always, before the first query

Three of the reviewed session's costliest errors were things the SME knew and was never asked.
Ask all five, in one message, and wait.

1. **Subject context** — in one line, what is this and what family does it belong to?
2. **What do you know that I would not find?** — platform relationships, renames, vendor
   identity, org history, who replaced what.
3. **Which identifiers are confirmed, and which were pulled by name?**
4. **Direction and grain** — tracing what, from where, to where, at what grain?
5. **What would make this a success, and what would make it a waste?**

Write the answers into the log front matter, each tagged:

```yaml
sme_context:
  - { fact: "<one line>", status: confirmed }
  - { fact: "<one line>", status: unverified }
```

**An `unverified` fact may not become a join key, a filename, a front-matter field or a graph
property until it is resolved.** Resolving it is action #1, not an item somewhere in the list.

**Then read the shared ledgers (§6) for the subject family before the first query** — the
whitelist for where to look, `terms` for what the tokens mean, `platforms` for what the
platform actually is, `id-shapes` for which identifiers join. What is already there is cited,
not re-derived; a session that re-discovers a term the last session decoded has spent its
budget on nothing.

---

## 2. The outcome vocabulary — classify every probe

"Dead end" collapses five outcomes with very different weight. Only one is worth much.

| Outcome | Meaning | What to do |
|---|---|---|
| `empty` | query ran, zero results | **suspect the query** — indistinguishable from malformed |
| `irrelevant` | results returned, none answered | check for a homonym; record the schema you read |
| `blocked` | auth, permission, rate limit | **retry candidate** — record the auth surface, not "unavailable" |
| `stale` | found it, too old to trust | record the age and what changed since |
| `exhausted` | well-formed query, source genuinely lacks it | **the only durable negative** — requires a control |
| `exhausted_in_scope` | the *artifact* lacks it; the platform may not | **name the projection** |

Never write `exhausted` without a passing control (§3). Never write `blocked` as though it
were `exhausted` — a blocked probe is work someone can finish.

---

## 3. The two controls

### 3.1 Live query → positive control

Every negative probe is paired with a **second query against the same source, same auth, that
must return something.**

- Control returns rows → the negative is real. Record `exhausted`.
- Control returns zero → **the probe is invalid**, not negative. Bad syntax, expired session,
  wrong project/space key. Record `outcome: empty, control_passed: false` and fix the probe.

Prefer two controls that bracket the negative: one **broader in the same scope**, one **same
term unscoped**. Worked shape, from a validated zero-result:

```text
negative : scope = <K> AND text ~ "<term>"      -> 0
control A: scope = <K> AND text ~ "<broader>"   -> 25   (scope + session valid)
control B: text ~ "<term>"                      -> 12   (term + syntax valid)
=> the term is genuinely absent FROM THAT SCOPE
```

Note what control B also bought: it found where the term *does* live.

### 3.2 Census over a file → schema control

Three of the six reviewed errors were not queries at all. They were exhaustive scans of a file
already in hand. A second query cannot validate those — a **schema check** can.

> **Before concluding "the platform does not hold X", ask: does this artifact have a field
> that could express X?**

- No such field exists → the finding is about the **export**. Record `exhausted_in_scope` and
  name the projection: *"this 21-column export cannot express X"*, never *"the platform has
  no X"*.
- The field exists and is empty → now you have a real `exhausted`, scoped to that population.

Two reviewed cases, both avoidable by this one check:

- A 21-column export had no filename-shaped column; recorded as *"a route has no file
  identity"*. A 139-column export of the same object carried the field.
- One account's history was 100% `COMPLETED`; recorded as *"the history is a success view"*.
  Another account's history was 6% `FAILED`.

**Corollary — partition before claiming an absence.** A single account, folder, window or
region is a slice, not the population.

---

## 4. Four rules that are not about absence

**4.1 A `200` is a status line, not a success.** SSO estates serve login pages with HTTP 200.
Read the `<title>`. Treat **near-identical byte lengths across different paths** as one
interstitial page, not as catch-all routing. Absence of `<script src=…>` is another tell: a
real single-page app has bundles; an auth interstitial has a stylesheet.

**4.2 Do not validate a derivative against itself.** If the source artifact is reachable, check
against the source. Comparing one half of an extraction to another half of the same extraction
proves nothing — and produced a confidently wrong defect report in the reviewed session.

**4.3 Cite the artifact and the reading separately.** A model's reading of a screenshot is
GROUNDED evidence; the image is the VERBATIM artifact. Exact strings from a reading — ids,
names, labels — are **transcriptions until corroborated** from a second surface.

**4.4 A name in a list is not the subject.** A vendor named in a *supported-client
compatibility table* is not the vendor of the system. Check whether a name appears as the
**subject** or merely in a list of things the subject talks to.

---

## 5. The probe log

**Write it at the moment the query runs.** A session reconstructing its own dead ends at the
end will confabulate — the review that produced this skill had to do exactly that, and could
only manage it because the hop ledger happened to double as a partial record.

`internal/research/_probes/<subject>-probes.jsonl`, one object per probe:

```json
{"ts":"2026-09-02T14:03:00Z","subject":"<subject>","question":"<the question it serves>",
 "source":"<whitelist id or new>","tool":"<cli+version | api | browser | file>",
 "query":"<exact replayable string>","scope":"<filters/space/account/window>",
 "result_count":0,"outcome":"empty|irrelevant|blocked|stale|exhausted|exhausted_in_scope",
 "control_query":"","control_count":0,"control_passed":true,
 "artifact":"<path if a file was produced>","note":""}
```

Required on every row: `query` must be **replayable verbatim**, and `scope` must state what was
excluded. `blocked` rows record the auth surface hit (e.g. the page title returned), so a later
session retries instead of re-deriving.

**A sibling exists in code.** The deepdoc search log (`drydocs_deepdoc.search_log`, declared
kind `search`, MM3) records `tool / search / theme / novelty / results` per connector search,
where `theme` is the mind-map slot the search targeted. The two row shapes describe the same
act from two sides — this one classifies the outcome, that one scores the novelty — and
whether they converge is Idea-238's question. Until it is answered, a hand-run session writes
this JSONL; a connector-run search writes the search log. *Both the module and Idea-238 are on
`feat/mm-deepdoc-investigate` as of 2026-09-02, unmerged; on `main` this JSONL is the only
search record.*

---

## 6. The shared ledgers — the whitelist, and three more shaped like it

Four files under `internal/research/_registry/`, one discipline. Each exists because a
reviewed session re-discovered something the session before it had already established, and
each is read before the first query and written at close. The shapes ship as templates in
[`references/`](references/); copy one to start the file.

| Ledger | Schema | Stops re-discovering | Graduates to (through the gate) |
|---|---|---|---|
| `source-whitelist.yaml` | `drydocs.source-whitelist.v1` | where to look, and what a source does NOT answer | `config/doc-source-registry.yaml`, `config/source-registry.yaml` |
| `terms.yaml` | `drydocs.research-terms.v1` | what an acronym or token means — and what it does NOT mean | `config/taxonomy/software-registry.yaml` `acronyms:` (the SME-ruled home; the four registry fields are carried verbatim so promotion is a copy) |
| `platforms.yaml` | `drydocs.research-platforms.v1` | what an internally branded platform actually is — vendor, product, version, era — and which surface asserts ownership on it | `reference/REGISTRY.yaml` (the vendor's public docs, External) and a `software-registry.yaml` product row |
| `id-shapes.yaml` | `drydocs.research-id-shapes.v1` | which identifier shapes exist, who mints them, and whether they join | no config home — a confirmed join key is a candidate class for the shared entity extractor; the key's meaning is the gate's |

**What validates a row differs by ledger, and the field says so.** A source row carries its
`control` (§3); a term carries its `evidence` and a `confidence` in the analyst's own
vocabulary (`Confirmed / Partial / Likely / To verify / Corrected`); a platform carries the
implementation surface that `revealed_by` the vendor; an id shape carries `join_key:
confirmed` only with the authoritative record `confirmed_by`. Every row carries
`verified_on`, `verified_by: sme | agent`, `decay`, `classification` and its evidence
breadcrumbs in the state-file grammar (`<kind>:<rest>`).

**Agent-verified is never SME-verified.** `verified_by: agent` marks a corpus-derived
(SYNTHESIZED) row; it stays marked through graduation, where the registry's own `source`
prose must agree with it. A ledger that lets the two blur is worse than no ledger.

### 6.1 The source whitelist

`internal/research/_registry/source-whitelist.yaml` — schema `drydocs.source-whitelist.v1`.
The field list, with the working defaults and the questions still open for the user to rule,
is [`references/source-whitelist.template.yaml`](references/source-whitelist.template.yaml).

**Read it first.** Before probing anything, check whether the source is already recorded: what
rung it reached, what it answers, and — just as important — what it **does not** answer.

**Write to it when:**
- a source answers a question well (`outcome: good`),
- a source is proven blocked, irrelevant or exhausted **with its control**,
- a recorded claim turns out to be wrong — correct the row and say so in `notes`.

Every entry carries `verified_on` and `decay`. **Past decay, re-verify before citing.** One
page the reviewed session leaned on had gone stale in under four months.

### 6.2 Terms, platforms, id shapes

Read them the same way, in the same step. A token already in `terms.yaml` is cited by its
row, not decoded again — and its `not:` list is the homonym check for free. A platform already
in `platforms.yaml` answers "which platform is it, actually?" and "which surface asserts
ownership?" before a probe is spent on either. A shape already in `id-shapes.yaml` says
whether the token in hand is a durable handle, an ephemeral one, or not a key at all. Write
to them at close (§8): new rows, corrected rows, and rows whose confidence moved — with the
evidence that moved it.

### 6.3 Not ingestion registries

| File | Purpose | Gate-bound? |
|---|---|---|
| `internal/research/_registry/*.yaml` | research ledgers — starting points, terms, platforms, id shapes | no |
| `config/doc-source-registry.yaml` | documents a loader may read | **yes** |
| `config/source-registry.yaml` | data sources | **yes** |
| `config/taxonomy/software-registry.yaml` | vendors, products, and the ruled acronym expansions | **yes** |
| `reference/REGISTRY.yaml` | external references (a named vendor's public docs) | **yes** |

A ledger row **graduates** to a config registry through the HITL gate — the
`add-source-object` skill is the walk for a data source, the O68 change-artifact path for an
acronym, the `reference-librarian` agent for a vendor reference. It never short-circuits one.
Set `graduates_to:` only after sign-off.

### 6.4 A wrong row is worse than no row

The prose table the whitelist replaced carried an incorrect lead for two months and sent a
session to a homonym. **Ledger rows need the same evidence, the same validation
(control, confidence, revealing surface, confirming record) and the same decay as the probes
that produced them** — otherwise reuse propagates errors faster than it saves time. A row
past its `decay` is re-verified before it is cited, and a row found wrong is corrected in
place with the reason in `notes`, never deleted.

---

## 7. Classification boundary

- **This skill and its siblings are committed and mechanism-only** (`CLAUDE.md` §3): shapes,
  rules, field names, anonymized examples. **No real hosts, application ids, accounts, folder
  or job names.**
- **The four ledgers and the probe logs are Internal** and live under `internal/research/`
  (`_registry/` and `_probes/`) — tracked in the private repo, excluded from every publish
  (`PUBLISH-BOUNDARY.md`). Real values belong there; the templates under `references/` carry
  only shapes.

If a worked example needs a value to make sense, write it as a shape — `<account>`,
`<space-key>`, `ftsi#####` — not as an instance.

---

## 8. Session close

1. Every probe is in the JSONL, with an outcome class.
2. Every `exhausted*` row has a control.
3. New or corrected sources are written to the whitelist with `verified_on`.
4. **The session's decodes are promoted to the shared ledgers**, with their evidence: every
   term the log's acronyms table settled or corrected → `terms.yaml`; every platform whose
   vendor, version, era or ownership surface was established → `platforms.yaml`; every
   identifier shape whose `join_key` status was settled → `id-shapes.yaml`. Confidence is
   carried as it stands — a `Likely` stays `Likely`, `verified_by: agent` stays `agent` — never
   rounded up at the door.
5. Every `unverified` SME fact is either resolved or still flagged `unverified` — never
   silently promoted.
6. Three metrics in the notes entry:
   - **coverage** — of the candidate sources for the question, how many were probed;
   - **reuse** — how many probes were skipped because the whitelist already answered them;
   - **re-discovery** — how many terms, platforms or shapes the session decoded that a ledger
     already held. Reuse near zero means the ledgers are not paying for themselves;
     re-discovery above zero means they were not read.

---

*Provenance: built producer-side from the transcription
`internal/research/mm-aar-research.md` (Part 4), reviewed at `2c184a79` on `main`; the
company original lives on an unmerged research branch and is not a port candidate. Changes at
the review: the two absent companions restated above, U.S. spelling, and "backbone" for the
original's "spine" per `docs/style/us-business-english.md`.*
