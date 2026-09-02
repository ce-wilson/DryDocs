---
title: "Mind-map after-action review — the JOB→MFTS search, and the three research skills it produced"
created: 2026-09-02
classification: Internal     # inherits the reviewed artifacts' tier: real hosts, accounts, SEAL ids, tool paths
subject: research-method
reviews: internal/research/JOB-MFTS-MM-research.md
---

<!-- PRODUCER-SIDE TRANSCRIPTION (2026-09-02) of seven company-side artifacts as they stood
     on the company's dd-lineage worktree - a RESEARCH FEATURE BRANCH that is not being merged
     (user ruling, 2026-09-02). Nothing here describes company main: the four skills in Parts
     4-7 do not exist there and are not port candidates. This copy exists so producer-side
     items can cite the research method by path. Reproduced verbatim, each part
     under its original path. Anything marked [illegible] was cut off in the source render
     and is not guessed. Producer review stamp (J63): reviewed_branch main,
     reviewed_port_base port-base-20260901. -->

# Part 1 — The after-action review, as delivered in session

> The conversation in which the JOB→MFTS search was reviewed against the SME's negative-probe
> taxonomy and the plan for three research skills was set. Tool-activity captions are kept,
> prefixed `> _[tool]_`, so the record shows what was measured versus asserted.

> _[tool]_ Analyzed negative-probe taxonomy and assessed control discipline

## After-action review — the JOB→MFTS search, against your taxonomy

**Verdict: it applies, and it would have caught three of the four substantive errors I made.** It would not have caught the fourth, which is worth knowing about. One extension is needed for the shape this session actually took.

First, a caveat that is itself evidence for your last paragraph: **I am reconstructing this from conversation context, not from a probe log.** No JSONL existed. The only reason it isn't pure confabulation is that the research log recorded hops as they happened — so the ledger *was* a partial probe record, by accident of method rather than design.

**Classifying this session's negatives**

| Probe | I recorded it as | Actually | Cost of the error |
| --- | --- | --- | --- |
| API store, 5 URLs → HTTP 200 | **Exhausted** — "SPA catch-all routing", written as a finding (H34) | **Blocked** (ADFS interstitial) | Two hops recorded on a probe that never authenticated |
| `myRoutes/display/_` terminal + browser | Blocked (correct) | **Blocked** | None — G-14 already existed by then |
| `sys_journal_field` → 0 records | "ACL-blocked" (H111) | **Unknown — Empty or Blocked** | Unresolved; I asserted a cause I did not test |
| Malcolm 264/264 `COMPLETED` | **Exhausted** — "history is a success view" (H100), used to answer OQ-13 | **Empty** — that account/window had no failures | **The most expensive error of the session.** A fake absence promoted to a structural finding *and* used to close an open question |
| 21 cols × 89 rows, no file mask (H64) | **Exhausted** — "a route has no file identity" | **Empty** — the 139-column export has `Sender Remote Filename` | Propagated into G-19, G-9 and the reject test |
| "No MFTS route id ever observed" (H14) | **Exhausted** | **Empty** | Superseded within hours |
| DPL "Dataset Routes" (H9) | Correctly a homonym | **Irrelevant** | None — caught by reading the schema, not the tag |
| `space=EMITS AND text ~ "ftsi18193"` → 0 | **Exhausted** | **Exhausted — validated** | None |

That last row is the only place I ran your method, and I ran it by accident: `space=EMITS AND text~"MFTS"` returned 25 and bare `text~"ftsi18193"` returned 12. **Two positive controls bracketing one negative.** It is the only zero-result in this session I would defend.

**Where the rule bites**

The Malcolm case is your trap exactly. `Status = COMPLETED` on 264/264 is indistinguishable, after the fact, from a filtered export. The control was cheap and available: **pull a second account's history and check whether `FAILED` ever appears.** When I finally did — for unrelated reasons — 47 of 725 were `FAILED`. Same source, same export type, control fails the claim in one query.

Same for H64: the control is *"does any column in this export have a filename-shaped header?"* The 21-column export had none — which should have forced the claim down to **"this export cannot express file identity"** rather than **"the platform has no file identity."**

**Where it would not have helped**

**SEAL 90130.** That was not a negative probe. It was a **positive claim adopted from a caveated source and never verified** — you told me it was pulled by name and might be wrong, and I built on it for two days while "resolve SEAL 90130" sat in my own next-actions list. No absence-scoring framework addresses that. The control there is different and simpler: *an identifier supplied with a caveat is unverified until resolved, and must not be used as a join key.*

<!-- excerpt boundary: the next screenshot did not overlap the previous one; the conversation between is not captured -->

**USER:** add your notes to a new file MFTS-MM-research-after-actions-review.md also, i'm not concerned with the "cost of the error" now. just the plan. I would like to create 2-3 research plan templates for the uses cases. A- as it applies to the job lineage and filling in any backlog and idea gaps. B- for job failures, researching what documentation is available and what connects to what. C. general research. the SME should be asked for give the 'subject contex (that I don't know yet)' and when a good site is found add it to a separate file with date, context, search, etc. and it will be come a 'white list' starting point. I think each of the 3 cases could be customized skills. your goal is to plan the 3 search templates and the claude skills needed. using a few sample guidelines like :#attachment:Pasted text #1 then in a second pass use /create skill to make them

> _[tool]_ The MCP server `GTAssist` may have new tools and requires interaction to start. Start it now?

> _[tool]_ Searched for files in internal/research/_templates directory

Both `create_file` and `run_in_terminal` are currently disabled, so I can't write the file. Here's the plan — say the word once writing is re-enabled and I'll commit it to `internal/research/MFTS-MM-research-after-actions-review.md` verbatim.

## The review, condensed

The defect wasn't bad searching. It was **recording an absence as a property of the platform when it was a property of the artifact in hand** — six instances, same shape.

Your five classes sort them cleanly:

| Probe | Recorded as | Actually |
| --- | --- | --- |
| API store, 5 URLs → 200 | Exhausted ("SPA routing") | **Blocked** — ADFS interstitial |
| `sys_journal_field` → 0 | "ACL-blocked" | **Unknown** — Empty or Blocked, untested |
| Malcolm 264/264 `COMPLETED` | Exhausted — "success view" | **Empty** |
| 21 cols × 89 rows, no file mask | Exhausted — "route has no file identity" | **Empty** — 139-col export has the column |
| `space=EMITS AND text~"ftsi18193"` → 0 | Exhausted | **Exhausted — validated** |

The only defensible zero-result was the one with controls, and it was bracketed by accident.

**Two things your taxonomy doesn't cover, and both bit:**

- **A caveated positive claim** — SEAL 90130 was supplied *as* unverified, used as a join key for two days. No absence framework touches this.
- **A census over a file already in hand** — three errors were exhaustive scans of a *projection*. Exhausted-within-the-artifact is true and useless. Needs a sixth class, `exhausted_in_scope`, and a **schema control** rather than a second query: *does this artifact have a field that could express X?* If not, the finding is about the export, never the platform.

## Three artifacts

1. **Probe log** — `internal/research/_probes/<subject>-probes.jsonl`, written at query time. Fields: ts, question, source, tool, query, scope, result_count, outcome, control_query/count/passed, artifact. `outcome: exhausted` **is not permitted without a passing control.**
2. **Source whitelist** — `internal/research/_registry/source-whitelist.yaml`. This supersedes the prose "Known reference sources" table in `_templates/source-probe.md` — which already carries a wrong row (it points at the DPL dataset-metadata API for MFTS routes; that's a homonym). Correcting it is migration task #1. Per entry: subject_context, host, access{tool,auth,rung}, verified_on/by, **answers[] / does_not_answer[]**, replayable_query, outcome, control, **decay**, classification, graduates_to. Negative entries live here too, with their control. Keep it separate from `doc-source-registry.yaml` and `source-registry.yaml` — those are gate-bound ingestion registries. A whitelist entry **graduates** through the HITL gate; it never short-circuits one.
3. **SME context capture** in log frontmatter, each answer tagged `confirmed | unverified`.

> _[tool]_ Create AAR file for research review (1/4)

> _[tool]_ DD1-SME-MM-research.md

<!-- excerpt boundary: the next screenshot did not overlap the previous one; the conversation between is not captured -->

> _[tool]_ Forked: SME Mindmap agent prompt

> _[tool]_ add your notes to a new file MFTS-MM-research-after-actions-review.md also, i'... 30/31

## SME interview — asked once, at the top, every skill

1. Subject context in one line — what is this, what family does it belong to?
2. What do you know that I wouldn't find? (renames, vendor identity, platform relationships)
3. **Which identifiers are confirmed, and which were pulled by name?**
4. Direction and grain — tracing what, from where, to where?
5. What would make this a success, and what would make it a waste?

`unverified` answers are **barred from use as keys.** This session lost time to exactly three things you knew and I never asked for.

## A / B / C

**A** · `research-job-lineage` — anchor job/folder, direction, known-good sibling. Order: Control-M definition → description tokens → the platform the token names → its route export → ownership (SEAL/CI) → docs → ticketing. Exit: the 7-link test, **recording which link it died at.** Specific to A: every unresolved link becomes an IDEAS or backlog entry *with the link number as its acceptance criterion*; check for existing ids and report id-range drift against `origin/main`.

**B** · `research-job-failure` — order: the notification (it names the contact and often the file) → ticket + CI + group + close notes → the platform's error taxonomy → **changes in the window** → run history → docs last. Two rules from this session: *check for a change in the window first* (a planned change explained a pattern I'd mis-attributed to load balancing), and *never conclude "no failures" from a success view.*

**C** · `research-general` — vendor identity first if suspected, because it moves the subject from Internal to a publishable External reference with no entitlement. Rule: **when a platform is internally branded, look for the vendor in implementation surfaces** — user-agent strings, cookie names, header requirements, ports, identifier shapes. Two days of documentation didn't name it; a mandatory HTTP header did.

## Skill architecture — one spine, three thin skills

| Component | Owns |
| --- | --- |
| `research-scaffold` (existing agent) | two-phase log, `?`-node hinge, hop ledger |
| `source-probe.md` (existing) | capture ladder |
| `research-probe-discipline` (new, shared) | the probe rules, probe-log schema, whitelist read/write, SME interview |
| `research-job-lineage` / `research-job-failure` / `research-general` | opening questions, source order, exit criteria only |

**Hard constraint:** `skills` is committed and mechanism-only per `CLAUDE.md` §3 — shapes, rules, field names, anonymised examples. The whitelist and probe logs are **Internal**, under `research`.

**Build order for pass 2:** whitelist schema + migration → `research-probe-discipline` → C → B → A → back-fill this session's entries.

## Open questions before I build

- One whitelist for all subjects, or one per subject area? (One file searches better; per-subject avoids cross-branch merge conflicts.)
- Does an entry need SME sign-off, or is `verified_by: agent` acceptable with a recorded control?
- Default `decay`? I guessed 90d — the environments page went stale in under four months.
- Commit the probe log, or session-scratch? Committing is what makes reuse measurable.
- **Three skills, or one with a `mode:` parameter?** Three trigger more cleanly; one avoids drift between three copies of the spine. My lean is three, given your triggering needs.

> _[tool]_ Created 4 todos

<!-- excerpt boundary: the next screenshot did not overlap the previous one; the conversation between is not captured -->

> _[tool]_ Ran `import yaml,sys; d=yaml.safe_load(open(r'internal/...`

Whitelist validates — **11 entries**, no missing fields, no uncontrolled `exhausted`. Now the shared spine skill.

> _[tool]_ Created SKILL.md and added 7 todos

Spine done. Now C (general), which exercises it end to end.

> _[tool]_ Created 3 files and ran commands

Now back-filling the session's real sources into the whitelist, and marking the old table superseded.

> _[tool]_ Updated source-whitelist.yaml and source-probe.md +150 -0

Implementation complete — all six build steps done, on `feat/dd_lineage`.

**Built:**

| Artifact | Status |
|---|---|
| MFTS-MM-research-after-actions-review.md | the AAR + plan (cost column dropped, as asked) |
| source-whitelist.yaml | **17 entries**, schema validates, no missing fields, no uncontrolled negatives, no dup ids |
| SKILL.md | the shared spine |
| SKILL.md | C |
| SKILL.md | B |
| SKILL.md | A |

**One spine, three thin skills** — the SME interview, outcome vocabulary, both controls, probe log and whitelist I/O live once in `research-probe-discipline`. A/B/C add only opening questions, source order and exit criteria. That answers OQ-e in favour of three skills without triplicating the method.

**Mechanism-only verified.** I scanned all four skills for hosts, application ids, account patterns, platform names, ticket numbers and folder prefixes — **all clean**. Real values live only in the Internal whitelist and logs. Shapes like `ftsi#####` and `<space-key>` are used instead of instances.

**The whitelist carries negatives too**, each with its control — including the API store as a `blocked` retry candidate (with the byte-length/title evidence that exposed the false positive) and the corrected homonym row as `irrelevant`.

**Supersession applied.** The prose table in source-probe.md is now marked *do not add rows, do not cite*, with the reason: no controls, no dates, no decay, and one row wrong for two months.

**Two design choices I made that you may want to overturn:**

- `decay` **defaults vary by volatility rather than a flat 90d** — 7d for the 7-day event history, 60d for the already-stale environments page, 180d for specs. Your OQ-c guess of 90d felt wrong for a source that expires in a week.
- `verified_by: sme | agent` **is recorded but not enforced** — no entry is gated on sign-off (OQ-b). Every agent-verified entry carries its control instead. Easy to tighten if you'd rather.

Still open for you: OQ-a (one whitelist vs per-subject) and OQ-d (commit the probe log or keep it scratch). I've assumed one file and committed logs for now.

Nothing committed — say the word and I'll commit on `feat/dd_lineage`, confirming the branch first.

> _[tool]_ Completed: *Plan Claude skills for research templates* (4/5)

> _[tool]_ Update source-probe.md to reflect new whitelist (5/5)

> _[tool]_ MFTS-MM-research-after-actions-review.md

Describe what to build

---

# Part 2 — `internal/research/MFTS-MM-research-after-actions-review.md`

> The written-up review. Its own frontmatter and headings are preserved below.

---
title: "After-action review — the JOB→MFTS search — and the plan for three research skills"
created: 2026-09-02
updated: 2026-09-02
status: plan
classification: Internal     # names real hosts, accounts, SEAL ids and tool paths from the reviewed session
subject: research-method
reviews: internal/research/JOB-MFTS-MM-research.md
central_question: >
  The JOB→MFTS trace recorded several absences as findings that later turned out to be
  artifacts of scope. What discipline would have caught them, what durable artifacts does
  that need, and what should the three research skills (job lineage / job failure /
  general) each own?
tags: [research-method, aar, probe-log, source-whitelist, skills, drydocs]
---

# After-action review — the JOB→MFTS search, and the plan it produces

> **Pass 1 settles the artifacts and the skill boundaries. Pass 2 builds them.**

## 1. What the review found

The trace ran two days across ~10 source surfaces and produced 111 hops. Its recurring defect
was **not** bad searching — it was **recording an absence as a property of the platform when it
was a property of the artifact in hand**. Six instances, same shape.

A five-way classification of negative outcomes separates them cleanly:

| Class | Meaning | Worth |
|---|---|---|
| **Empty** | query ran, zero results | little — indistinguishable from malformed |
| **Irrelevant** | results returned, none answered the question | little |
| **Blocked** | auth, permission, rate limit | **a retry candidate, not a dead end** |
| **Stale** | found it, too old to trust | context-dependent |
| **Exhausted** | well-formed query, source genuinely lacks it | **the only one worth much** |

Applied to the reviewed session:

| Probe | Recorded as | Actually |
|---|---|---|
| API store, 5 URLs → HTTP 200 | Exhausted ("SPA catch-all routing") | **Blocked** — ADFS interstitial |
| `myRoutes/display/…` terminal + browser | Blocked | **Blocked** (correct) |
| `sys_journal_field` → 0 records | "ACL-blocked" | **Unknown** — Empty or Blocked, untested |
| One account's history 264/264 `COMPLETED` | Exhausted — "history is a success view" | **Empty** — that account/window had none |
| 21 cols × 89 rows, no file mask | Exhausted — "a route has no file identity" | **Empty** — the 139-col export has the column |
| "No route id of this platform ever observed" | Exhausted | **Empty** |
| A homonym API tag | homonym | **Irrelevant** (correct) |
| `space=<K> AND text ~ "<account>"` → 0 | Exhausted | **Exhausted — validated** |

**The one defensible zero-result was the one with controls** — a broader query in the same
space returned 25, and the same term unscoped returned 12, bracketing the negative. It was run
that way by accident, not by method.

### Two things the classification does not cover, and both bit

**(a) A positive claim adopted from a caveated source.** An application id was supplied *with
the explicit caveat that it was pulled by name*, used as a join key for two days, and was
wrong. No absence-scoring framework touches this. It needs its own rule (§3.3).

**(b) A census over a file already in hand.** Three of the six errors were not queries against
a live source — they were exhaustive scans of an artifact that turned out to be a
**projection**. Exhausted-within-the-artifact is true and useless. This needs a sixth class and
a different control (§3.2).

## 2. Durable artifacts

### 2.1 Probe log — `internal/research/_probes/<subject>-probes.jsonl`

**Written at the moment the query runs.** This AAR had to be reconstructed from conversation
context because no probe log existed — precisely the condition under which a session
confabulates its own dead ends.

One JSON object per probe:

```json
{"ts":"","subject":"","question":"","source":"","tool":"","query":"","scope":"",
 "result_count":0,
 "outcome":"empty|irrelevant|blocked|stale|exhausted|exhausted_in_scope",
 "control_query":"","control_count":0,"control_passed":true,
 "artifact":"","note":""}
```

`outcome: exhausted` is **not permitted without a passing control**. A blocked probe records
the auth surface it hit, so a later session retries rather than re-deriving.

### 2.2 Source whitelist — `internal/research/_registry/source-whitelist.yaml`

**Supersedes the prose "Known reference sources" table** in
[`_templates/source-probe.md`](_templates/source-probe.md), which is already carrying a wrong
row. Negative entries live here too, with the control that proved them: a dead end without a
control is not admissible, because a wrong ledger row propagates faster than an absent one.

`decay` is mandatory — one page the reviewed session relied on was already stale.

Keep separate from the gate-bound ingestion registries. A whitelist entry **graduates** to
`config/doc-source-registry.yaml` or `config/source-registry.yaml` through the HITL gate; it
never short-circuits one.

| File | Purpose | Gate-bound? |
|---|---|---|
| `internal/research/_registry/source-whitelist.yaml` | *research* starting points | no |
| `config/doc-source-registry.yaml` | *ingestion* — documents a loader may read | **yes** |
| `config/source-registry.yaml` | *ingestion* — data sources | **yes** |

### 2.3 SME context capture — log frontmatter (§4)

## 3. Probe discipline — the rules the skills enforce

**3.1 Every negative probe carries a positive control.** A second query, same source, same
auth, that must return something. Control fails ⇒ the probe is **invalid**, not negative.

**3.2 A census over an artifact needs a schema control, not a second query.** Before concluding
"the platform does not hold X", ask: **does this artifact have a field that could express X?**
If no such column exists, the finding is about the **export**, never the platform. Record
`exhausted_in_scope` and name the projection. This alone would have prevented three of six.

**3.3 An identifier supplied with a caveat is unverified.** It may not be used as a join key,
a filename or a frontmatter field until resolved against an authoritative record. Resolving it
goes at the **top** of the action list, not in it.

**3.4 A `200` is a status line, not a success.** Read the `<title>`; treat near-identical byte
lengths across different paths as one interstitial, not as routing.

**3.5 Do not validate a derivative against itself.** If the source artifact is reachable, check
against the source.

**3.6 Cite the artifact and the reading separately.** A model's reading of a screenshot is
GROUNDED; the image is VERBATIM. Exact strings from a reading are transcriptions until
corroborated.

<!-- seam: this screenshot did not overlap the previous one; lines between may be missing -->

## 4. The SME context interview

The reviewed session lost time to three things the SME knew and was never asked for: a platform
identity, an unverified id, and the meaning of a direction word.

1. **Subject context** — in one line, what is this and what family does it belong to?
2. **What do you know that I would not find?** (platform relationships, renames, vendor
   identity, org history)
3. **Which identifiers are confirmed, and which were pulled by name?**
4. **Direction and grain** — tracing what, from where, to where, at what grain?
5. **What would make this a success, and what would make it a waste?**

Answers go into log frontmatter as `sme_context`, each tagged `confirmed | unverified`.
**Anything `unverified` is barred from use as a key (3.3).**

## 5. The three research plans

All share the spine: probe discipline (§3), probe log (§2.1), whitelist (§2.2), SME interview
(§4) and the two-phase log shape. They differ only in **opening questions, source order and
exit criteria.**

### A · Job lineage — `research-job-lineage`

Trace a job/folder up or down its chain; fill backlog and IDEAS gaps.

- **Extra questions:** anchor job/folder? upstream or downstream? a known-good sibling?
- **Source order:** orchestrator definition → job description tokens → the platform the token
  names → that platform's route/config export → ownership → docs → ticketing.
- **Exit:** the 7-link test, recording **which link it died at**. Rejection is a result.
- **Specific to A:** every unresolved link becomes an IDEAS entry or backlog item **with the
  link number as its acceptance criterion**; check for an existing id first and report id-range
  drift against `origin/main`.

### B · Job failure — `research-job-failure`

- **Extra questions:** what failed, when, how did you learn about it? recurring? owning team?
- **Source order:** the notification (it names the contact, often the file) → ticket + CI +
  assignment group + close notes → the platform's error taxonomy → **changes in the window** →
  run history → documentation last.
- **Two rules from the reviewed session:** check for a change in the window **first**; and
  never conclude "no failures" from a success view — partition by status and by account.
- **Exit:** named error class, owning group, CI, runbook present-or-absent, and either a change
  correlation or an explicit "none found, control passed".

### C · General research — `research-general`

- **Extra question:** what is the smallest question that would make this worth doing?
- **Source order:** vendor identity first if suspected — it moves the subject from Internal to
  a publishable External reference and needs no entitlement → internal docs → API/spec → UI
  export → ticketing.
- **Specific to C:** when a platform is internally branded, **look for the vendor in
  implementation surfaces**, not documentation — user-agent strings, cookie names, header
  requirements, default ports, path conventions, identifier shapes.
- **Exit:** the central question is answered or explicitly reclassified; every open question
  names who must rule it.

## 6. Skill architecture

One spine, three thin skills — do not triplicate the method.

| Component | Owns | Home |
|---|---|---|
| `research-scaffold` (existing agent) | two-phase log, `?`-node hinge, hop ledger | `.claude/agents/` |
| `source-probe.md` (existing) | the capture ladder | `internal/research/_templates/` |
| **`research-probe-discipline`** (new, shared) | §3 rules, probe-log schema, whitelist I/O, SME interview | `.claude/skills/` |
| **`research-job-lineage`** (A) | link test, backlog/IDEAS integration | `.claude/skills/` |
| **`research-job-failure`** (B) | notification→ticket→change→history order | `.claude/skills/` |
| **`research-general`** (C) | vendor-first, acronym decode | `.claude/skills/` |

**Hard constraint:** `.claude/skills/` is committed and **mechanism-only** per `CLAUDE.md` §3 —
shapes, rules and field names, with anonymised examples. The **whitelist and probe logs are
Internal** and live under `internal/research/`.

## 7. Build order

1. `source-whitelist.yaml` — schema + migrate the `source-probe.md` table, correcting its wrong
   row as the first entry.
2. `research-probe-discipline` — the shared spine.
3. `research-general` (C) — simplest; exercises the spine end to end.
4. `research-job-failure` (B) — the reviewed session supplies its worked shape.
5. `research-job-lineage` (A) — last; its backlog/IDEAS integration is the fiddliest.
6. Back-fill whitelist entries from the JOB→MFTS log.

## 8. Open questions for the SME

- **OQ-a** — one whitelist for all subjects, or one per subject area?
- **OQ-b** — does an entry need SME sign-off, or is `verified_by: agent` acceptable with a
  recorded control?
- **OQ-c** — default `decay`? 90 days is a guess.
- **OQ-d** — commit the probe log, or session-scratch? Committing makes reuse measurable.
- **OQ-e** — three skills, or one with a `mode:` parameter?

## Metrics worth keeping

**Coverage** — of the candidate sources for a question, how many were probed.

**Reuse rate** — how often a later session skipped a known dead end. If it stays near zero the
ledger is not paying for itself. **Caveat:** the one reuse event observed in the reviewed
session was *negative* — a stale ledger row sent it to a homonym. Ledger entries need the same
outcome class, control and decay as the probes that produced them.

---

# Part 3 — `internal/research/_registry/source-whitelist.yaml`

> The research starting-point ledger the review created — confirmed-good sources AND proven dead
> ends, each with its control. Explicitly NOT an ingestion registry.

```yaml
# Source whitelist — research starting points
#
# WHAT THIS IS: the "where do I look, and what did it actually answer" ledger for research
# sessions. It records BOTH confirmed-good sources and proven dead ends, because a dead end
# without a recorded control is not admissible evidence of absence.
#
# WHAT THIS IS NOT: an ingestion registry. Nothing here authorises a loader to read anything.
#   internal/research/_registry/source-whitelist.yaml  <- research starting points (this file)
#   config/doc-source-registry.yaml                    <- documents a loader may read (GATE-BOUND)
#   config/source-registry.yaml                        <- data sources (GATE-BOUND)
# An entry GRADUATES to a config registry through the HITL gate; it never short-circuits one.
#
# SUPERSEDES: the prose "Known reference sources" table in
# internal/research/_templates/source-probe.md. That table had no controls, no dates and no
# decay, and it carried a wrong row for two months (see id: dpl-dataset-routes-homonym).
#
# CLASSIFICATION: Internal. Real hosts, ids and account shapes appear here by design.
# The SKILLS that read this file are mechanism-only and must never inline its values.
#
# SCHEMA (drydocs.source-whitelist.v1)
#   id                required, kebab-case, stable
#   name              required, human label
#   subject_context   required, SME-supplied one-liner: what family does this belong to
#   host              optional, Internal
#   access:
#     tool            how it is reached (CLI + version, API, browser, file)
#     auth            the auth surface — name it even when it works
#     rung            1 spec/bulk · 2 authenticated API · 3 saved HTML · 4 print/PDF · 5 copy-paste
#   verified_on       required, ISO date the claim below was last true
#   verified_by       required, sme | agent
#   outcome           required, one of the probe outcome classes (see below)
#   control           required when outcome is `exhausted*` — what proved the probe was valid
#   answers           required, list — the questions this source DOES settle
#   does_not_answer   required, list — scope limits, so the next session does not re-derive them
#   replayable_query  required, the exact query/steps to reproduce
#   decay             required, e.g. 90d — after this, re-verify before citing
#   classification    required, External | Internal-Public | Internal
#   graduates_to      optional, the config-registry id if it has been gate-approved
#   notes             optional
#
# OUTCOME CLASSES
#   good              source answers its `answers` list; use it
#   blocked           auth/permission/rate limit — a RETRY CANDIDATE, not a dead end
#   irrelevant        returns results, none answer the question (homonyms live here)
#   stale             found it, too old to trust
#   exhausted         well-formed query, source genuinely lacks it — REQUIRES a control
#   exhausted_in_scope the ARTIFACT lacks it; the platform may not — name the projection
---
schema: drydocs.source-whitelist.v1
updated: 2026-09-02

sources:

  # ------------------------------------------------------------- migrated rows
  - id: dpl-pipelines-api
    name: Data-platform pipelines API
    subject_context: data pipeline definitions
    access: { tool: "HTTP + Kerberos", auth: "Kerberos (works from terminal)", rung: 1 }
    verified_on: 2026-08-31
    verified_by: agent
    outcome: good
    answers:
      - pipeline definitions, control file, flow definition, dataset flow options, token metadata
      - the field contract, VERBATIM, via the published OpenAPI document
    does_not_answer:
      - anything about file transfer
    replayable_query: "GET /remote-api-spec -> internal/research/api-specs/"
    decay: 180d
    classification: Internal

  - id: dpl-dataset-metadata-api
    name: Data-platform dataset metadata API
    subject_context: dataset registration
    access: { tool: "HTTP + Kerberos", auth: "Kerberos", rung: 1 }
    verified_on: 2026-08-31
    verified_by: agent
    outcome: good
    answers: [dataset registration, offerings, publishing, dataset versions and audit fields]
    does_not_answer:
      - "file-transfer routes — see dpl-dataset-routes-homonym"
    replayable_query: "GET /remote-api-spec -> internal/research/api-specs/"
    decay: 180d
    classification: Internal

  - id: chronicle-aurora-replica
    name: Chronicle (Aurora replica)
    subject_context: data platform operational tables
    access: { tool: "read-only MCP snapshot", auth: "none — local snapshot", rung: 2 }
    verified_on: 2026-08-31
    verified_by: agent
    outcome: good
    answers: [pipeline/dataset/glue operational tables]
    does_not_answer:
      - "current values — the snapshot is point-in-time; check provenance before trusting counts"
    replayable_query: "MCP tools; call get_provenance first"
    decay: 30d
    classification: Internal

  - id: controlm-cm-replica
    name: Control-M CM_ replica + folder XML export
    subject_context: batch orchestration
    access: { tool: "Oracle CM_ replica; folder XML export", auth: "FID entitlement", rung: 1 }
    verified_on: 2026-08-31
    verified_by: sme
    outcome: good
    answers: [job/folder/condition definitions, variables, quantitative resources]
    does_not_answer:
      - "anything the desktop GUI renders but the tables do not carry"
    replayable_query: "CM_DEF_V* queries; ITPM folder XML upload/export is the rung-1 bulk form"
    decay: 180d
    classification: Internal
    notes: >
      The desktop GUI is a RENDERING of this data and sits below rung 5 — use it to understand
      the flat data, never to cite it.

  - id: servicenow-classic-jsonv2
    name: ServiceNow — classic UI JSON processor
    subject_context: ITSM (incidents, changes, CMDB, groups)
    access:
      tool: "snow.exe 0.9.1 (NOT the newest build) + .do?...&JSONv2 path traversal"
      auth: "Kerberos/SAML session; the documented REST Table API returns 403 for this account"
      rung: 2
    verified_on: 2026-09-01
    verified_by: agent
    outcome: good
    answers:
      - incident / change_request / cmdb_ci / sys_user_group records by sys_id or number
      - "deployment CI correlation_id = <sealAppId>:<deploymentId> — the authoritative SEAL join"
    does_not_answer:
      - "work notes — sys_journal_field returns 0 rows on this path (untested whether ACL or query)"
      - "sysparm_fields is IGNORED on the .do form; you always get all columns"
    replayable_query: >
      & $SNOW_BIN -table-get "../../../<table>.do?sysparm_query=<encquery>&JSONv2"
    decay: 90d
    classification: Internal
    notes: >
      ALWAYS verify the returned sys_id is the one requested — an unknown parameter is silently
      ignored and returns default rows that look like a match.

  - id: confluence-datacenter
    name: Confluence (Data Center)
    subject_context: internal team-authored standards
    access: { tool: "confluence.exe 0.9.1; CQL via /rest/api/content/search", auth: "Kerberos/SAML", rung: 2 }
    verified_on: 2026-09-01
    verified_by: agent
    outcome: good
    answers: [team-authored standards, route/job mapping pages, space + version + last-modified]
    does_not_answer:
      - "content that lives on the engineering portal instead — see engineering-docs-portal"
    replayable_query: >
      -get "/rest/api/content/search?limit=25&expand=space,version&cql=<urlencoded CQL>"
    decay: 90d
    classification: Internal
    notes: >
      Prefer over the portal wherever a standard exists in both. Scope with `space = <K> AND
      text ~ "<term>"`, and ALWAYS pair a zero-result with an unscoped control (see
      probe-control-worked-example).

  - id: engineering-docs-portal
    name: Internal engineering documentation portal
    subject_context: platform standards (orchestration / ETL / file transfer)
    access: { tool: "browser only", auth: "ADFS OAuth2 + PKCE; Kerberos SPNEGO does NOT satisfy it", rung: 4 }
    verified_on: 2026-09-01
    verified_by: agent
    outcome: blocked
    control: "every path incl. /sitemap.xml returns the same ADFS Home-Realm-Discovery page"
    answers: []
    does_not_answer:
      - "anything, from an agent — capture is a human save/copy"
    replayable_query: "any path; check <title> — 'Home Realm Discovery' means not authenticated"
    decay: 180d
    classification: Internal
    notes: >
      RETRY CANDIDATE, not a dead end. The one untested route is an IDA token for the named
      OAuth resource. A 200 here is the login page, not success.

  - id: seal-application-registry
    name: Application registry (SEAL)
    subject_context: application ownership and org hierarchy
    access: { tool: "whodapp / Verum graph API", auth: "Kerberos", rung: 2 }
    verified_on: 2026-09-01
    verified_by: agent
    outcome: good
    answers: [application ownership, org hierarchy, SID/email resolution]
    does_not_answer:
      - "which application id a platform actually uses — resolve that from its deployment CI"
    replayable_query: "whodapp lookups; or ServiceNow deployment CI correlation_id"
    decay: 90d
    classification: Internal
    notes: >
      An application id obtained BY NAME is unverified. Resolve it against a deployment CI
      before using it as a key — see aar-caveated-identifier.

  # ------------------------------------------------------------- the corrected row
  - id: dpl-dataset-routes-homonym
    name: "Data-platform 'Dataset Routes' API tag"
    subject_context: "NOT file transfer — storage/publication destinations"
    access: { tool: "OpenAPI document", auth: "Kerberos", rung: 1 }
    verified_on: 2026-09-01
    verified_by: agent
    outcome: irrelevant
    control: "schema read in full: platform ∈ {AWS_S3, HORTONS, INFORMATICA}; routeProperties = bucket, region, kmsKeyArn, roleArn, glueTableArn"
    answers: []
    does_not_answer:
      - "file-transfer routes, transfer records, transfer ownership — it is a STORAGE route"
    replayable_query: "read the RouteInformation / RouteProperties schemas, not the tag name"
    decay: 365d
    classification: Internal
    notes: >
      CORRECTS the superseded source-probe.md row, which advised probing this API for
      file-transfer route information. It is a homonym. The lesson generalises: match on the
      value shape and the schema, never on the column or tag NAME.

  # ------------------------------------------------------------- method examples
  - id: probe-control-worked-example
    name: "Worked example — a validated zero result"
    subject_context: research method
    access: { tool: "any search surface", auth: "n/a", rung: 0 }
    verified_on: 2026-09-01
    verified_by: agent
    outcome: exhausted
    control: >
      the negative (space-scoped term, 0 hits) was bracketed by TWO controls on the same
      source and auth: a broader term in the same space returned 25, and the same term
      unscoped returned 12. Both non-zero, so the syntax, session and scope were all valid.
    answers:
      - "the shape of an admissible absence: negative + >=1 passing control, same source/auth"
    does_not_answer:
      - "anything about a specific subject — this row exists as a template"
    replayable_query: "<scoped negative> ; <broader control> ; <unscoped control>"
    decay: 3650d
    classification: Internal-Public

  - id: aar-caveated-identifier
    name: "Worked example — a caveated identifier used as a key"
    subject_context: research method
    access: { tool: "n/a", auth: "n/a", rung: 0 }
    verified_on: 2026-09-01
    verified_by: sme
    outcome: irrelevant
    answers:
      - "an id supplied WITH a caveat is unverified and may not be a join key, filename or frontmatter field"
    does_not_answer: []
    replayable_query: "resolve the id against an authoritative record BEFORE building on it"
    decay: 3650d
    classification: Internal-Public
    notes: >
      Recorded because no absence-scoring rule covers it: this is a POSITIVE claim adopted
      from a caveated source. It propagated into ~27 places over two days while
      "resolve this id" sat unactioned in the session's own next-actions list.

  # ------------------------------------------------------------- MFTS (JOB→MFTS trace, 2026-09-01)
  - id: mfts-myroutes-framework-export
    name: "MFTS myRoutes — route framework export"
    subject_context: "file transfer — MFTS (SEAL 89830), Axway SecureTransport 6.0.x"
    host: "mymfts.gaiacloud.jpmchase.net/myTransfers"
    access: { tool: "browser (SSO) — no API", auth: "ADFS; agent-unreachable", rung: 5 }
    verified_on: 2026-09-01
    verified_by: sme
    outcome: good
    answers:
      - "durable route definitions: Request ID, sender/receiver accounts, directories, protocol"
      - "route owner / ops contact / tech contact — the fields the platform actually notifies"
      - "cost centre (the platform's own KEY FIELD) — present in the 139-column config export"
      - "MFT System Environment — joins the job-side FTS_ID token"
      - "lifecycle state, submitter/modifier, go-live and decommission dates"
    does_not_answer:
      - "transfer events — a separate export with no shared key"
      - "file identity on SOME exports — the 21-column curated export has no filename column,
        the 139-column config export does. NAME THE EXPORT when citing an absence"
    replayable_query: "Search Routes → filter by user / file location / cost centre → Download"
    decay: 90d
    classification: Internal
    notes: >
      TWO route exports exist with near-disjoint columns (21 vs 139), sharing exactly one key:
      Request ID. Join them. An absence claimed against one is scoped to that one.

  - id: mfts-mytransfers-history
    name: "MFTS myTransfers — transfer event history"
    subject_context: "file transfer — MFTS event stream"
    host: "mymfts.gaiacloud.jpmchase.net/myTransfers"
    access: { tool: "browser (SSO)", auth: "ADFS; agent-unreachable", rung: 5 }
    verified_on: 2026-09-01
    verified_by: sme
    outcome: good
    answers:
      - "per-transfer events keyed on Core ID; file name, size, direction, protocol, status"
      - "Environment + Source node — identifies which instance moved the file"
      - "FAILED status and Error Message DO appear — see the control note"
    does_not_answer:
      - "route ids — no Request ID column; joins the framework only via username + directory"
      - "anything older than ~7 days; files themselves are retained days, less if large"
    replayable_query: "myTransfers → filter by user → Download (max ~7 days of history)"
    decay: 7d
    classification: Internal
    notes: >
      CONTROL REQUIRED before claiming a clean record. One account's week was 100% COMPLETED
      and was wrongly recorded as "this history is a success view"; a second account's week was
      6% FAILED with Error Message populated. Partition by account AND window before asserting.
      Retention makes any cited fact unfalsifiable within a week — cite a preserved capture and
      the window it covers, never a re-runnable query.

  - id: mfts-failure-notification-email
    name: "MFTS file transmission failure notice"
    subject_context: "file transfer — MFTS failure channel"
    access: { tool: "email (push)", auth: "n/a — arrives at the registered contact", rung: 1 }
    verified_on: 2026-09-01
    verified_by: sme
    outcome: good
    answers:
      - "a fixed Files List table: Environment, FTS ID, File Name, Timestamp(UTC), Error Message, SNOW Ticket"
      - "an error taxonomy by Issue Type (authentication / connection / network / transfer operation)"
      - "whether SNOW ticketing is configured for that route at all"
    does_not_answer:
      - "route ids; and its 'FTS ID' column value looked account-shaped, not environment-shaped — unresolved"
    replayable_query: "mailbox search on the notice subject; sender is a transmission-control mailbox"
    decay: 180d
    classification: Internal
    notes: >
      The failure channel is a MAILBOX, not a queryable surface. Notices route to the route's
      REGISTERED CONTACT, proving the framework's contact fields are operationally live.
      'Ticketing not Configured' means the failure raises no incident and is invisible to every
      ticket-based process.

  - id: mfts-technical-guide-pdf
    name: "Managed File Transfer external technical guide"
    subject_context: "file transfer — partner-facing standard"
    access: { tool: "SharePoint over Kerberos (Invoke-WebRequest -UseDefaultCredentials)", auth: "Kerberos — works", rung: 1 }
    verified_on: 2026-09-01
    verified_by: agent
    outcome: good
    answers:
      - "environment FQDNs and ports, retention policy, route-request lifecycle and SLAs"
      - "the REST operation list, supported-client matrix, cipher support"
    does_not_answer:
      - "internal-only estate detail — it describes the PARTNER-FACING service"
    replayable_query: "Invoke-WebRequest -UseDefaultCredentials <sharepoint url> -OutFile <path>"
    decay: 180d
    classification: Internal
    notes: >
      TRAP: the filename and subtitle say 'External', meaning AUDIENCE — its own copyright block
      marks the contents confidential, so it is INTERNAL in DryDocs terms. Second trap: its
      vendor mentions are all in a supported-CLIENT compatibility table, not an attribution.

  - id: mfts-environments-page
    name: "MFT environments / URLs / ports reference page"
    subject_context: "file transfer — internal estate reference"
    access: { tool: "engineering docs portal — browser only", auth: "ADFS; would not render, captured as copy/paste", rung: 5 }
    verified_on: 2026-09-01
    verified_by: sme
    outcome: stale
    answers:
      - "environment FQDNs, VIP A/B pairs, transfer-manager hosts per environment and data centre"
      - "the LEGACY-to-current environment name crosswalk"
      - "which route field carries the environment"
    does_not_answer:
      - "environments added after its last-updated date — at least two were missing"
    replayable_query: "<docs portal>/file-transfer/mft/references/environments/ — human save required"
    decay: 60d
    classification: Internal
    notes: >
      STALE by observation, not age alone: a change record named two environments absent from
      this page. Also the source of an ERA-COLLISION warning — legacy and current environment
      numbering overlap, so resolve an environment through the HOST list, never by digits.
      Owed a rung-3 capture; it arrived as copy/paste because the page would not render.

  - id: apistore-product-pages
    name: "API store product + specification pages"
    subject_context: "API catalogue"
    host: "apistore.jpmchase.net"
    access: { tool: "browser", auth: "ADFS — agent-unreachable", rung: 5 }
    verified_on: 2026-09-01
    verified_by: agent
    outcome: blocked
    control: "5 distinct URLs all returned HTTP 200 with <title>Home Realm Discovery</title>, 0 script tags, byte lengths 51711/51713/51715/51729"
    answers: []
    does_not_answer:
      - "anything, from an agent — SME copy/paste is the only route today"
    replayable_query: "any /products/<name> path; CHECK THE <title> before recording a result"
    decay: 180d
    classification: Internal
    notes: >
      RETRY CANDIDATE. The near-identical byte lengths across different paths were initially
      misread as SPA catch-all routing; they were one auth interstitial served four times.
      Untested route: an IDA token against the store's own published resource URI. Content
      reached via SME paste shows the catalogued API is an OPERATIONAL user API
      (upload / download / trigger / change password) — it describes nothing.
```

---

# Part 4 — `.claude/skills/research-probe-discipline/SKILL.md`

~~~markdown
---
name: research-probe-discipline
description: The shared spine for DryDocs research sessions — the SME context interview, the probe-outcome vocabulary, the positive-control rule, the probe log, and the source whitelist. Use whenever a research session searches ANY source and might record an absence, a dead end, or a "not found". Loaded by research-general, research-job-failure and research-job-lineage; use it directly for one-off lookups that still need their negatives to be trustworthy.
---

# research-probe-discipline

The spine every DryDocs research skill sits on. It exists because of one measured failure
mode: **a session records an absence as a property of the platform when it is a property of
the artifact in hand.** One reviewed trace did it six times in two days.

This skill owns four things — the interview, the outcome vocabulary, the controls, and the two
ledgers. It owns no subject matter. Pair it with `research-general`, `research-job-failure` or
`research-job-lineage`.

**Companions, not duplicates:** the two-phase log shape and hop ledger belong to the
`research-scaffold` agent; the capture ladder belongs to
`internal/research/_templates/source-probe.md`. Do not restate either here.

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

Write the answers into the log frontmatter, each tagged:

```yaml
sme_context:
  - { fact: "<one line>", status: confirmed }
  - { fact: "<one line>", status: unverified }
```

**An `unverified` fact may not become a join key, a filename, a frontmatter field or a graph
property until it is resolved.** Resolving it is action #1, not an item somewhere in the list.

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

```
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

---

## 6. The source whitelist

`internal/research/_registry/source-whitelist.yaml` — schema `drydocs.source-whitelist.v1`.

**Read it first.** Before probing anything, check whether the source is already recorded: what
rung it reached, what it answers, and — just as important — what it **does not** answer.

**Write to it when:**
- a source answers a question well (`outcome: good`),
- a source is proven blocked, irrelevant or exhausted **with its control**,
- a recorded claim turns out to be wrong — correct the row and say so in `notes`.

Every entry carries `verified_on` and `decay`. **Past decay, re-verify before citing.** One
page the reviewed session leaned on had gone stale in under four months.

### Not an ingestion registry

| File | Purpose | Gate-bound? |
|---|---|---|
| `internal/research/_registry/source-whitelist.yaml` | research starting points | no |
| `config/doc-source-registry.yaml` | documents a loader may read | **yes** |
| `config/source-registry.yaml` | data sources | **yes** |

A whitelist entry **graduates** to a config registry through the HITL gate. It never
short-circuits one. Set `graduates_to:` only after sign-off.

### A wrong row is worse than no row

The prose table this file replaced carried an incorrect lead for two months and sent a session
to a homonym. **Ledger entries need the same outcome class, control and decay as the probes
that produced them** — otherwise reuse propagates errors faster than it saves time.

---

## 7. Classification boundary

- **This skill and its siblings are committed and mechanism-only** (`CLAUDE.md` §3): shapes,
  rules, field names, anonymised examples. **No real hosts, application ids, accounts, folder
  or job names.**
- **The whitelist and probe logs are Internal** and live under `internal/research/`. Real
  values belong there.

If a worked example needs a value to make sense, write it as a shape — `<account>`,
`<space-key>`, `ftsi#####` — not as an instance.

---

## 8. Session close

1. Every probe is in the JSONL, with an outcome class.
2. Every `exhausted*` row has a control.
3. New or corrected sources are written to the whitelist with `verified_on`.
4. Every `unverified` SME fact is either resolved or still flagged `unverified` — never
   silently promoted.
5. Two metrics in the notes entry:
   - **coverage** — of the candidate sources for the question, how many were probed;
   - **reuse** — how many probes were skipped because the whitelist already answered them.
     If reuse stays near zero across sessions, the ledger is not paying for itself.

~~~

---

# Part 5 — `.claude/skills/research-general/SKILL.md`

~~~markdown
---
name: research-general
description: Subject-agnostic research for an unfamiliar system, platform, acronym or term — "what is this, who owns it, what does it connect to, and where is it documented?". Use when opening a trace on something nobody on the team has mapped yet, when decoding an unexplained acronym or token value, or when a platform is internally branded and its vendor is unknown. Not for a specific job's lineage (use research-job-lineage) or a specific failure (use research-job-failure).
---

# research-general

The default research plan. Answers *what is this, whose is it, what does it connect to, and
where is it written down?*

**Load `research-probe-discipline` first** — the SME interview, the outcome vocabulary, the
control rules, the probe log and the whitelist all live there and are not repeated here. This
skill adds only the **opening questions, the source order, and the exit criteria.**

Log shape and hop ledger come from the `research-scaffold` agent; capture rungs from
`internal/research/_templates/source-probe.md`.

---

## 1. Open

Run the five-question SME interview from `research-probe-discipline` §1, plus one:

> **6. What is the smallest question that would make this worth doing?**

Write it into the log's `central_question`. If it cannot be phrased as a question, stop and say
so — there is no trace to open yet.

Then **read the whitelist** (`internal/research/_registry/source-whitelist.yaml`) for the
subject family before probing anything.

---

## 2. Source order

Work down this list. Stop when the central question is answered — the order is by
*cost-to-value*, not by completeness.

### 2.1 Vendor identity — first, if a vendor is plausible

Do this before internal documentation, because it can move the whole subject from **Internal**
to a **publishable External reference with no entitlement at all**. A vendor's public docs
answer *what a route is, what a transfer record contains, what a partner means* for free.

**When a platform is internally branded, the vendor is not in the documentation — it is in the
implementation.** Rebranding reaches names, logos and prose; it rarely reaches protocol
details. Look, in roughly this order:

- **User-agent strings** the API requires or sends
- **Cookie names** (session tokens often carry a vendor product name)
- **Mandatory headers** and their spellings
- **Default ports** and port ranges
- **On-disk path conventions** and account-name shapes
- **Error-message wording** and error-code vocabularies
- **Version strings** embedded in labels — a version is what makes vendor docs *usable*

In the reviewed trace the vendor surfaced in a **mandatory `User-Agent` header** after two days
of documentation not naming it, then was confirmed by a **cookie name** that matched a vendor
product, a **version label** in a field value, and finally an internal change record naming the
vendor's processes.

**Guard (from `research-probe-discipline` §4.4):** a vendor named in a *supported-client
compatibility table* is not the vendor of the system. Ask whether the name appears as the
**subject** or in a list of things the subject talks to.

### 2.2 Internal documentation

Search the wiki **before** the portal where both exist — the wiki is usually API-reachable and
the portal usually is not. Scope the search, and **bracket every zero-result with the two
controls** (`research-probe-discipline` §3.1).

A zero result in one space is a finding about that space, not about the term. The unscoped
control often finds where the term actually lives.

### 2.3 API / specification

Probe for a machine-readable contract before profiling any export. **But read the operation
list before promoting a lead to rung 1** — a product page's feature bullets settle in seconds
what a spec hunt costs a session.

> **"There is an API" is not "there is a source."** An *operational* API that performs actions
> is not a *metadata* API that describes them. If every operation changes state — upload,
> trigger, delete — it answers nothing a lineage question asks, and it is not a thing to
> explore casually.

### 2.4 UI exports

Rung 5, and usually the only durable metadata a platform exposes. Two rules:

- **The rung ladder can invert.** Sometimes the rung-2 API reaches only the *operational*
  surface while the durable metadata exists solely as a UI download. Probing "upward" is still
  right — but the upward move that helps may be **sideways, to the vendor**.
- **One export is not the platform** (`research-probe-discipline` §3.2). Ask whether a second
  export of the same object exists; two exports with near-disjoint columns are common, and if
  they share one key they join.

### 2.5 Ticketing and change records

Cheap, authoritative, and frequently the fastest route to ownership. An incident or change
record yields the **CI**, the **assignment group**, the **owning application id** and often the
vendor — in one lookup.

The deployment CI's `correlation_id` is the authoritative application-id join. **Prefer it over
an id obtained by name** (`research-probe-discipline` §1).

---

## 3. Decode as you go

Keep an acronyms and terms table in the log from the first hop, with a confidence column
(`Confirmed / Partial / Likely / To verify / Corrected`). Never silently upgrade a confidence.

**Two decode traps, both observed:**

- **Homonyms.** The same word means different things on different surfaces — a "route" can be a
  file-transfer path on one platform and a storage destination on another. **Match on the value
  shape and the schema, never on the column or tag name.**
- **Era collisions.** The same identifier string can name different things across generations
  of a platform (a legacy numbering scheme overlapping a current one). Resolve through a host
  or instance list, never by matching the digits.

---

## 4. Exit criteria

The trace closes when **all** hold:

1. The central question is **answered**, or explicitly **reclassified** with the reason.
2. Every open question names **who must rule it** — SME, gate, or a specific evidence pull.
3. Every claim carries a **capture rung** and a **platform/scope stamp**.
4. Every negative carries an **outcome class**, and every `exhausted*` a **control**.
5. Sources are written to the **whitelist**, including the blocked and irrelevant ones.
6. Coverage and reuse are recorded in the notes entry.

---

## 5. Outputs

| Artifact | Where |
|---|---|
| Research log (two-phase, hop ledger, acronyms, open questions) | `internal/research/<subject>-research.md` |
| Probe log (JSONL, written live) | `internal/research/_probes/<subject>-probes.jsonl` |
| New / corrected whitelist rows | `internal/research/_registry/source-whitelist.yaml` |
| Preserved captures | the evidence root; cite the path, never re-serialise |
| Anything worth doing later | `docs/restructure/IDEAS.md` |

---

## 6. Standing constraints

- **Nothing in `config/` is edited by research.** Registration is gate-bound; a whitelist row
  is not authorisation.
- **Zero graph writes.** No new label, relationship type or constraint is introduced by a trace
  — a trace may only *ask* for one, through the gate.
- **Corrections stay in place.** Strike a wrong hop and record what replaced it; do not delete
  it. The recurrence is usually the finding.
- **A difference between two sources is not a defect** until a transform, a convention or a
  predecessor tool has been ruled out.
- **SME knowledge checks an answer; it never supplies one** as evidence without a stamp.

~~~

---

# Part 6 — `.claude/skills/research-job-failure/SKILL.md`

~~~markdown
---
name: research-job-failure
description: Research a batch job, feed or transfer failure — find what documentation exists, what connects to what, and who owns it. Use when given an incident, an alert, a failure notification email, or "this job failed and I need to know what it touches". Covers the notification → ticket → change-window → run-history order and the failure-surface traps. Not for mapping a healthy job's lineage (use research-job-lineage) or for an unfamiliar platform (use research-general).
---

# research-job-failure

Answers *what failed, what does it connect to, who owns it, and what is written down about it?*

**Load `research-probe-discipline` first** — the SME interview, outcome vocabulary, controls,
probe log and whitelist live there. This skill adds the **failure-specific questions, source
order, traps and exit criteria.**

---

## 1. Open

Five-question interview from `research-probe-discipline` §1, plus four:

> **6. What failed, and when?** — the window matters more than the symptom.
> **7. How did you learn about it?** — alert, email, ticket, downstream complaint, or a user.
> **8. Is this recurring, or the first occurrence?**
> **9. Which team owns the failing component — and is that the same team that owns the thing
> it failed *on*?**

Question 7 is the highest-yield of the four. **The channel a failure arrives on is itself
evidence** — it names the registered contact, often names the artifact, and tells you which
surface the platform considers authoritative for failures.

Read the whitelist for the subject family before probing.

---

## 2. Source order

### 2.1 The notification itself — first

Whatever arrived: alert email, SNS/CloudWatch alarm, platform failure notice, monitoring page.
Mine it before anything else. It typically carries, for free:

- the **artifact** (file name, dataset, job) — often the only place this appears
- the **error text and its class**
- the **registered contact** the platform notifies — i.e. the ownership fields the platform
  actually *uses*, as opposed to the ones merely populated
- whether **ticketing is configured** at all

**Two things to check explicitly:**

- **Is a ticket raised?** A failure notice that says ticketing is not configured means the
  failure is **invisible to every ticket-based process**. That is a finding, and usually a
  fixable gap.
- **Structured metadata in free-text fields.** Alert descriptions and job descriptions
  frequently carry `key: value` blocks stuffed into a prose field — assignment group, severity,
  application id, environment. Parse them; they are the same facts the graph wants. Normalise
  against the closed vocabulary and **count unknown spellings rather than dropping them**.

### 2.2 Ticketing — incident, CI, group, close notes

One lookup yields most of the ownership picture: **CI**, **assignment group**, **priority /
urgency / impact**, **categorisation**, **close code** and **close notes**. Close notes often
contain the actual root cause in plain language.

The deployment CI's `correlation_id` is the **authoritative application-id join** — prefer it
over any id obtained by name.

**Known limit:** work notes may not be reachable through an API bypass even when the record is.
Record that as `blocked` with the surface hit, not as "no work notes exist"
(`research-probe-discipline` §2).

### 2.3 The platform's own error taxonomy

Failure notices and vendor docs usually ship an **Issue Type** vocabulary — authentication,
connection, network, permission, transfer-operation. Capture it; it is the vocabulary any
`:Failure` model should use, and it is authored by the people who built the thing.

Watch for **route-level stop-on-error semantics**: on some platforms one bad credential halts
*further execution* rather than failing a single item, so the blast radius is a queue, not a
file.

### 2.4 Changes in the window — **do this before profiling run history**

> **Check for a planned change covering the failure window before you interpret any pattern in
> the data.**

In the reviewed session a data pattern was confidently explained as load balancing across
nodes. It was a **planned A-side→B-side failover**, documented in a change record, and the
crossover in the data landed exactly inside the change window. The change record also supplied
the vendor attribution and corrected an application id.

Query changes by CI and by window. A change record gives you: the window, the affected
environments, the test plan (which names the runtime components), and whether it succeeded.

### 2.5 Run / transfer history

Now profile the history — with the partition rules below.

### 2.6 Documentation — last

Wiki before portal. Scope the search and bracket zero-results with both controls. Ask
specifically: **is there a runbook, and is it current?** "Absent" and "stale" are different
findings.

---

## 3. Failure-specific traps

**3.1 Never conclude "no failures" from a success view.**
An export may be a success projection. Before claiming a clean record:

- **partition by status** — does a failure status value even appear in the domain?
- **partition by account, folder, window and region** — one slice is not the population.
- apply the **schema control** (`research-probe-discipline` §3.2): does the export have an
  error/status column that *could* express a failure?

Observed: one account's history was 100% complete over a week; another account's was 6% failed.
The first was recorded as "this history is a success view" — wrong, and it was used to answer
an open question.

**3.2 The failure channel and the record channel may be different surfaces.**
Successes may be queryable while failures are pushed as notifications, or vice versa. Establish
which before designing anything. If failures arrive by mailbox, then the failure record and the
email corpus are the *same* problem.

**3.3 A failure record often carries the join key the definition record lacks.**
Definitions are frequently scoped to accounts, directories or partners and carry **no artifact
identity**; the failure event carries the **file name**. So the failure channel may join to the
orchestrator on precisely the attribute the definition channel cannot.

**3.4 Retention windows are short and asymmetric.**
Event history is often days, and the artifacts themselves shorter still. Consequences:

- a fact cited from event history is **unfalsifiable within a week** — cite a **preserved
  capture and the window it covers**, never a query someone could "just re-run";
- **absence means *not in this window*, never *did not happen*.**

**3.5 One incident is one incident.** Recurrence needs a second occurrence, not an assumption.

---

## 4. Build the connection map

The deliverable that makes this skill worth running is *what connects to what*. Assemble, and
mark each edge **observed / documented / inferred**:

```
upstream producer ──▶ transport/route ──▶ landing artifact ──▶ waiting job ──▶ downstream
     │                  │                   │                  │
 contact/owner    environment+node      file name       owning app (CI)
```

For every node record: **who owns it**, **which surface asserted that**, and **what is missing**.
An `inferred` edge is a candidate for the SME, not a fact.

---

## 5. Exit criteria

1. The failure has a **named error class** from the platform's own vocabulary.
2. An **owning group** and a **CI** are identified, each with the surface that asserted them.
3. The **application id** is resolved authoritatively, not by name.
4. A runbook is found, or explicitly recorded **absent** / **stale**.
5. A **change correlation** exists, or an explicit *"none found in window, control passed"*.
6. The connection map is drawn, with every edge marked observed / documented / inferred.
7. Every negative carries an outcome class; every `exhausted*` a control.
8. Whitelist updated; coverage and reuse recorded.

---

## 6. Outputs

| Artifact | Where |
|---|---|
| Research log with hop ledger and connection map | `internal/research/<subject>-research.md` |
| Probe log (JSONL, live) | `internal/research/_probes/<subject>-probes.jsonl` |
| New / corrected whitelist rows | `internal/research/_registry/source-whitelist.yaml` |
| Preserved captures (notifications, exports, records) | evidence root — cite the path |
| Gaps worth fixing (e.g. ticketing not configured) | `docs/restructure/IDEAS.md` |

---

## 7. Standing constraints

- **Read-only.** Never file, update, comment on or close a ticket. Never call an operational
  API that changes state — several "transfer" APIs upload, delete or trigger.
- **Nothing in `config/` is edited by research.** Zero graph writes.
- **Corrections stay in place**, struck rather than deleted.
- **Mechanism-only in this skill**; real values live in the Internal log and the whitelist.

~~~

---

# Part 7 — `.claude/skills/research-job-lineage/SKILL.md`

~~~markdown
---
name: research-job-lineage
description: Trace a Control-M job or folder up or down its chain — who produces its input, where its output goes, which platform moves the data, and who owns each hop — then turn every unresolved link into a backlog item or IDEAS entry. Use for "where does this file come from", "what depends on this folder", "trace this feed end to end", or when filling lineage gaps in the backlog. Not for a failure investigation (use research-job-failure) or an unfamiliar platform (use research-general).
---

# research-job-lineage

Answers *what feeds this job, what it feeds, which platform moves the data between, and who
owns each hop* — and converts every link that cannot be closed into tracked work.

**Load `research-probe-discipline` first** — SME interview, outcome vocabulary, controls, probe
log and whitelist live there. This skill adds the **anchor questions, source order, the link
test, and the backlog integration.**

---

## 1. Open

Five-question interview from `research-probe-discipline` §1, plus four:

> **6. What is the anchor?** — a folder, a job, or a feed. Name it exactly.
> **7. Which direction?** — upstream (who sends to us) or downstream (who consumes)?
>   *Do not accept a directional word without unpacking it.* "The opposite direction" once
>   meant *further upstream in the same flow*, not *outbound* — and the wrong reading
>   propagated into the source order and the acceptance test before it was caught.
> **8. What grain?** — folder, job, feed, or file. The answer changes which sources apply.
> **9. Is there a known-good sibling** that already traces end to end? A worked example is
>   worth more than any amount of schema reading.

Read the whitelist for the platform family before probing.

---

## 2. Source order

### 2.1 Orchestrator definition — the anchor

Pull the folder/job from the definition store (`CM_` replica, or the folder XML export, which
is the rung-1 bulk form). Establish: does the anchor resolve at all, what jobs it contains,
what conditions link them, and what variables it declares.

**Folder-name and job-name conventions are per-team, not platform-guaranteed.** A positional
decode may hold for one application and silently fail for another. Derive a **candidate** and
mark it as such.

### 2.2 The job's declared metadata

The description field is the contract between the job and everything outside the orchestrator:
delivery mechanism, account, environment, source contact, route identifiers. Parse it against
the **closed vocabulary** — and **count unknown spellings rather than dropping them**.

**Two traps here:**

- A **null value can be conformant**. If a standard exempts a field for some mechanisms, a
  missing value is compliance, not a gap. Partition by mechanism before reporting coverage.
- A standard may **forbid recording** a value that demonstrably exists on the platform. That is
  a defect in the standard — take it to the standard, not to the loader.

### 2.3 The platform the metadata names

Now go to the transfer/movement platform. Two things to establish before profiling anything:

- **Which platform is it, actually?** Internal branding, generational renames and generic use
  of a family name make this genuinely ambiguous. A name in a job token may denote a
  *mechanism*, an *era*, or a *product*.
- **How many exports does it have?** Two exports of the same object with near-disjoint columns
  are common. If they share one key they **join** — and the union is often the full picture
  neither alone provides.

### 2.4 The platform's definition vs event records

Definition (durable) and event (short-window) records are usually **different objects with
different keys and different lifetimes**. Establish for each:

| | definition | event |
|---|---|---|
| identity | | |
| grain | | |
| carries the artifact name? | | |
| retention | | |
| shared key with the other? | | |

**The grain is the finding.** A definition scoped to *(account → directory)* carries no file
identity; a definition scoped to *(feed, extension)* does. Two platforms doing the same job may
differ here, and a model ported across them will be wrong.

### 2.5 Ownership

Resolve the owning application from an **authoritative record** — a deployment CI's
`correlation_id`, not a name lookup. Record which surface asserted it.

Expect owner-vs-name disagreement: a folder named for one application may be owned by another,
by design. Operational routing (where incidents actually land) is stronger evidence than a
name.

### 2.6 Documentation, then ticketing

Wiki before portal, scoped, with both controls. Then incidents/changes for the anchor's CI —
they frequently name connections nothing else does.

---

## 3. The link test

Run the anchor down these links and **record which link it dies at**. Rejection is a result:
three candidates dying at the same link is a stronger finding than one that succeeds.

| # | Link | Passes when |
|---|---|---|
| 1 | anchor resolves | the folder/job returns from the definition store |
| 2 | dependency declared | a waiting/triggering relationship exists (watcher, condition, command) |
| 3 | artifact named | a concrete file, mask or dataset — **and the directory it lands in** |
| 4a | **durable handle** | an attribute that reaches the platform's **definition** record (account, directory, cost centre) |
| 4b | **ephemeral handle** | an attribute that reaches only the **event** record (often the file name), and expires |
| 5 | counterpart record found | the handle actually retrieves a record — a **set**, not necessarily one row |
| 6 | counterparty named | the sender/receiver is identified |
| 7 | attributable | the counterparty resolves to an owning application |

**Record 4a and 4b separately.** A candidate that passes only on 4b is traceable *this week and
not next* — a materially weaker result, and reporting them as one "pass" hides the only
constraint that cannot be engineered around.

Keep a running candidate table in the log:

| # | Anchor | Reached link | Outcome | Note |
|---|---|---|---|---|

---

## 4. Backlog and IDEAS integration — specific to this skill

Every link that does not close becomes tracked work. This is what makes a lineage trace pay
for itself twice.

**Before creating anything:**

1. Search `docs/restructure/backlog/items/` and `docs/restructure/IDEAS.md` for an existing
   entry on the same gap. Extend it rather than duplicating.
2. Check id-range drift: compare the max id on this branch against `origin/main`. **This repo
   has had id collisions twice** — ids are allocated by whoever appends next, and parallel
   branches will reuse numbers. Report the drift; prefer renumbering the ungroomed side.

**What to create:**

- **A gap with a known shape** → a backlog item, `module:` naming the owning component, with
  **the link number as its acceptance criterion** ("closes link 5 for series X").
- **A gap needing a ruling** → an `IDEAS.md` entry, stating the readings and what each costs.
  A groom cannot pick between two readings; do not force it to.
- **A modelling question** → route to the HITL gate. Never introduce a label, relationship type
  or constraint from a trace.

**Write the link number into the item.** It is what lets a later session verify the gap
actually closed, instead of re-deriving the whole chain.

---

## 5. Exit criteria

1. Every link 1–7 is **pass**, **fail-with-reason**, or **not-applicable-with-reason**.
2. 4a and 4b are recorded **separately**.
3. Ownership is resolved from an authoritative record, with the surface named.
4. Every definition/event grain difference is stated explicitly.
5. Every unresolved link has a backlog item or IDEAS entry carrying its link number.
6. Every negative has an outcome class; every `exhausted*` a control.
7. Whitelist updated; coverage and reuse recorded.

---

## 6. Outputs

| Artifact | Where |
|---|---|
| Research log — hop ledger, candidate table, link results | `internal/research/<subject>-research.md` |
| Probe log (JSONL, live) | `internal/research/_probes/<subject>-probes.jsonl` |
| New / corrected whitelist rows | `internal/research/_registry/source-whitelist.yaml` |
| Backlog items with link-number acceptance | `docs/restructure/backlog/items/` |
| Rulings and open questions | `docs/restructure/IDEAS.md` |
| Preserved captures | evidence root — cite the path |

---

## 7. Standing constraints

- **Nothing in `config/` is edited by research.** **Zero graph writes.** A new relationship
  type goes through `docs/RELATIONSHIP_GUIDE.md`, the vocabulary registry and the gate.
- **A candidate derivation is not a rule.** Present it to the SME; let the gate confirm.
- **A difference between two sources is not a defect** until a transform, convention or
  predecessor tool is ruled out.
- **Corrections stay in place**, struck rather than deleted.
- **Mechanism-only in this skill**; real folder, job, account and application values live in
  the Internal log and the whitelist.

~~~
