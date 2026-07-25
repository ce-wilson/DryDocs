# T12 companion — company-side `Ais*` excision prompt (paste-ready)

**Prepared producer-side 2026-07-25.** The execution companion to
[`port-T12-company-gate-pack.md`](port-T12-company-gate-pack.md): that pack convenes the
company gate session, **this** prompt does the sweep afterwards. It exists because the
producer ran the same purge over three commits (2026-07-21 → 2026-07-24) and the pattern
is worth handing over rather than re-deriving.

**Trigger observed 2026-07-24 (company side):** `Ais*` ghosts are still live in
`drydocs/controlm_app_codes.py` / the `load controlm_app_codes` path. That is **more than
the T12 pack anticipated** — the pack recorded `USES_TOOL` as *declared only, no edges
seeded* (from the C11 capture). A loader referencing it means the "verify zero edges"
line in pack §3 may be **false**. Establish the real edge count before ruling
deprecate-vs-remove.

**Amended 2026-07-25 — the acronym entry is REOPENED, not a survivor.** The first
revision of this prompt listed `software-registry.yaml#acronyms` as an untouchable
Class C audit record. The SME has since supplied evidence that the Q6 premise did not
hold — the `Ais` string was read as *"as-is"*, not as an acronym, and entered the
producer record as `:AiTool` (no "s") twelve days before anyone decoded it. **Step 2b**
now routes this back as an open question and the sweep defers it. Do not let a
company-side session harden a ruling that is under producer review.

Everything below is mechanism-only: no internal tool names, app-code values, SIDs, or
org values appear here, and none should be added when the prompt is pasted.

---

## Paste from here down

> ### Task: excise the retired `Ais*` class family, company-side
>
> You are working in the **company** DryDocs repo. The producer repo ran this same purge
> after its C12 platforms-taxonomy gate; this is the company-side equivalent. Work the
> steps in order. **Step 0 is a hard gate — do not skip it.**
>
> ---
>
> #### Step 0 — Check the gate before touching anything
>
> Read `config/gate-log.md` and look for a **T12 / platforms supersede-or-reconcile**
> entry (the session convened from `docs/port-T12-company-gate-pack.md`).
>
> - **SUPERSEDE signed** → proceed to step 1. The ruling authorizes the sweep.
> - **RECONCILE signed** → **stop.** A company-local capability/tool view survives by
>   ruling; there is nothing to purge. Report that instead, and instead check that each
>   surviving surface *documents* why it is not duplicative.
> - **No entry at all** → **stop and report.** Under the two-tier gate-adoption doctrine
>   (`docs/port-prompt.md` guardrail 6, **Tier B**), the company holds its own signed
>   position — the 2026-06-29 AIS gate — and the producer's C12 outcome may not be
>   adopted by port. Purging first would destroy the audit trail of a signed gate. Run
>   the session from the pack, then come back.
>
> Whatever you find, quote the entry (or its absence) in your first message. Do not
> infer the ruling from the state of the code.
>
> #### Step 1 — Survey before editing
>
> Grep the whole repo, case-sensitively, for `AisTool`, `AisCapability`, `Ais`,
> `IN_CAPABILITY`, `USES_TOOL`, and `SchedulerKind`. Include `.py`, `.cypher`, `.sql`,
> `.yaml`, `.md`, `.json`, `.ts`/`.tsx`, and test files. Produce **one table** — file,
> line, what the reference is — and classify every hit into exactly one of the three
> classes in step 2. **Do not edit anything during the survey.** Present the table and
> the classification, then proceed.
>
> Surfaces to expect company-side (predicted from the producer sweep + the C11 capture —
> confirm each, and treat the list as a floor, not a ceiling):
>
> | Surface | Why it is expected to carry `Ais*` |
> |---|---|
> | `drydocs/controlm_app_codes.py` + the `load controlm_app_codes` path | **The observed hit.** Data-bearing, company-only module. Establish whether it *writes* `USES_TOOL`/`:AisTool` or merely names them. |
> | `drydocs_core/schema/platforms_supplement.cypher` | The 06-29 build: 3 `:AisCapability` + 7 `:AisTool` + 7 `IN_CAPABILITY` seeds. |
> | the `apply-platforms-supplement` CLI verb + its `cli.py` wiring / verify checks | Company-only verb that applies the supplement. |
> | `config/taxonomy-ontology-map.yaml` (the C2c adoption entry) | `adoption: confirmed` for the 06-29 model. |
> | `drydocs_core/ontology/relationship_vocabulary.yaml` | `USES_TOOL`, `IN_CAPABILITY` entries. |
> | `config/taxonomy/platforms.yaml` | The company copy (created 2026-07-09, stale headers per the C11 capture). |
> | `drydocs_core/schema/constraints.cypher` | Any `capability_id` / `tool_id` key constraints. |
> | tests asserting label sets, constraint counts, or seeded nodes | These pin the old shape and will fail loudly — that is the point. |
> | web console / query-spec label lists, if the company copy has them | Producer had `Ais` strings in explorer demo data and query specs. |
>
> #### Step 2 — Three classes, three different treatments
>
> This is the whole discipline. The producer purge got its shape from keeping these
> apart; collapsing them either destroys audit history or leaves live ghosts.
>
> **Class A — live build / write paths → RETIRE AUDIT-KEPT, do not delete.**
> Seeds get **commented out with the deprecation record inline** (date, ruling, what
> supersedes them). Constraints on retired labels **stay** with a deprecation comment —
> old graphs still carry the nodes, and dropping a constraint is a graph write, not a
> config edit. Loader code that *writes* the retired edge is retargeted or disabled per
> the gate ruling, never silently repointed.
> *Producer precedent:* `ontology.cypher` `:SchedulerKind` seeds commented with the
> record; `constraints.cypher` `scheduler_kind` kept (count unchanged); the
> `"ControlM SchedulerKind seeded"` verify check retired alongside the seeds.
>
> **Class B — superseded capture prose → EXCISE, leave a pointer.**
> Delete the block, then rewrite the file header to state the *gate outcome* and point
> to where the full capture still lives (git history at the named revision + the session
> pack). Compress any Q&A into a short closed-rulings record and let the canonical prose
> stay in `gate-log.md`. Never leave a header claiming a superseded state.
> *Producer precedent:* `platforms.yaml` lost its `company_confirmed` block and its
> pre-supersede Q&A; the header now carries the C12 outcome plus "full capture: this
> file's git history (rev 2026-07-21) + the T12 pack".
>
> **Class C — sanctioned survivors → DO NOT TOUCH.**
> These are the audit record. Removing them is the failure mode this step exists to
> prevent:
> - `config/gate-log.md` — **append-only**, both the 06-29 entry (backfill it if the
>   session landed one) and the new supersede entry. Never edit or drop either.
> - The signed gate-prompt / session pack files.
> - Map and vocabulary entries closed as `rejected` / `deprecated` **with their
>   superseded-by notes** — a closed entry that names the retired thing is *doing its
>   job*. `superseded_by`, `deprecated_at`, and the RESOLVED notes stay.
>
> #### Step 2b — The acronym entry is NOT a Class C survivor: it is REOPENED
>
> An earlier revision of this prompt listed the acronym expansion as an untouchable
> Class C survivor. **That was wrong and is withdrawn.** Treat this as its own item.
>
> **Status:** the Q6 ruling (2026-07-21) made
> `config/taxonomy/software-registry.yaml#acronyms` the durable home for "Application
> Integration Streaming", with the company's own source-registry gloss as a PROVISIONAL
> entry deferring to it. **That ruling is REOPENED producer-side as of 2026-07-25** on
> SME information that was not on the table at Q6 — see the evidence note below.
>
> **What you do about it: nothing.** Do not delete the entry, do not harden it, do not
> carry the expansion across into any new file, and do not cite it as authoritative
> anywhere. Leave the company's PROVISIONAL gloss exactly where it sits. In the step-6
> residual grep, list every acronym hit as **"REOPENED producer-side — deferred, not
> swept"**, distinct from the sanctioned survivors. If a company ruling on the acronym is
> wanted in the same session, that is a fresh gate call with the evidence below as input
> — not something this sweep decides.
>
> **The evidence, so the reopen is reviewable rather than a bare instruction.** Two
> questions were conflated at Q6 and they have opposite answers:
>
> 1. *Is AIS a genuine company term?* Evidence says **yes**, independent of us: the
>    internal engineering-docs portal is rooted at `/docs/ais/{orchestration,etl,
>    file-transfer}/` and independently corroborated the three capability areas. That
>    path predates the modeling work and is not ours to rename.
> 2. *Was `:AisTool` a considered modeling choice in our taxonomy?* Evidence says **no**.
>    The string entered the producer record 2026-07-09 (commit `761a201`) as `:AiTool` —
>    **no "s"** — attributed to in-chat direction and flagged "not yet defined in the
>    ontology". It stayed inconsistently spelled for twelve days across `backlog.yaml`,
>    `IDEAS.md`, and the port-prompt archive, and was "corrected" to `AisTool` on
>    2026-07-21 by **matching the C11 screenshot, not by decoding it**. The expansion was
>    not established until Q6 that same afternoon. The SME reports having read the string
>    as **"as-is"** throughout, never as an acronym.
>
> Q6 answered (1) and was applied as though it had settled (2). It had not.
>
> **If a note survives the reopen, the protective sentence is not the expansion.** It is
> **"this does not mean 'as-is'"**. As-is/to-be is a standard architecture-modeling
> idiom, so a reader meeting `:AisTool` cold is likelier to read a current-state-vs-
> target-state marker than to wonder about an acronym — and that misreading imports a
> whole false meaning. Forgetting an acronym is the milder failure. Note also that the
> expansion was already ruled partly inaccurate at Q6 ("Streaming" is a misnomer — the
> folder also carried ETL and managed file transfer).
>
> **Nothing is at risk either way.** `config/gate-log.md` carries the expansion verbatim
> and is append-only, so the audit record survives regardless of what the registry entry
> does. That is precisely why this can be deferred instead of decided under time
> pressure by a sweep.
>
> #### Step 3 — The landing shape (what replaces what)
>
> No new node or edge types. The app→orchestrator fact lands on the **already-active**
> registry edge:
>
> ```
> (:BusinessApplication)-[:USES_SOFTWARE {source: 'batch-port'}]->
> (:SoftwareProduct {role: 'orchestrator'})
> ```
>
> `role: 'orchestrator'` carries the classification that `:AisCapability` used to
> ("role over class"); `:SoftwareProduct` *is* the concrete-tool class that `:AisTool`
> used to be. `USES_TOOL` and `IN_CAPABILITY` retire; `:SchedulerKind` was already dead
> on both sides. The `source` property distinguishes these declared-orchestrator edges
> from registry stack rows (`source: 'registry'`) — both writers must key their MERGE on
> `source`, or the second writer eats the first one's edges.
>
> The ported `batch_port_orchestrator` loader is the producer's implementation of this.
> Running it company-side is **T9-gated** (your graph, your verify) and takes *your*
> SEAL-declared strings and *your* crosswalk — not the producer's synthetic ones.
>
> #### Step 4 — Graph data is a separate decision, and it is not yours
>
> Config edits do not touch loaded nodes. The fate of the loaded `:AisCapability` /
> `:AisTool` / `IN_CAPABILITY` data — **deprecate-in-place (audit-kept, the 06-29
> `SchedulerKind` precedent) vs remove** — is a T12 session ruling. Execute what the
> gate-log says. If the entry is silent, **stop and ask**; do not infer it, and do not
> write to the graph on your own authority (T9).
>
> Before any such write: get the real counts. `MATCH ()-[r:USES_TOOL]->() RETURN
> count(r)` and the same for `IN_CAPABILITY` and each label. If `USES_TOOL` turns out to
> have edges — plausible given `controlm_app_codes` references it — that **contradicts**
> the T12 pack's "declared only" premise and needs re-ruling before anything is removed.
>
> #### Step 5 — Boundary rules
>
> - `drydocs/controlm_app_codes.py` is **`never-port` / data-bearing** (real app-code
>   values). Fix it in place company-side. Its *mechanism* change (which edge type, which
>   label) may be reported back to the producer as prose; its **values never back-flow**.
> - Same for `locations.py`, `seal_deployments.py`, and anything under `internal-local/`.
> - Do not add producer-side files that the company doesn't have, and do not delete
>   company-only capability the producer never had — that is the classic "reconcile"
>   failure mode (Class D in the port-boundary tech-debt review).
>
> #### Step 6 — Verify and report
>
> 1. Full unit suite green (`poetry run pytest -q`) — record the pass/skip counts. Tests
>    pinning the retired shape should be *updated to pin the exclusion*, not deleted:
>    assert the retired label/edge is absent from seeded sets, the way the producer's
>    `test_schema_graph` pins `seal_requires_scheduler` and `SchedulerKind` on the
>    exclusion side.
> 2. `python -c "import drydocs.cli"` and `drydocs --help` still work (the
>    `apply-platforms-supplement` verb may have changed shape — say so).
> 3. Re-run the step-1 grep. Every remaining hit must be either a **named Class C
>    survivor** or a **step-2b deferred acronym hit** — list the two groups separately
>    ("sanctioned survivors, deliberately untouched" vs "REOPENED producer-side,
>    deferred"). An unexplained residual hit means the sweep is not done.
> 4. If any graph write happened: edge/node counts before and after, plus an idempotent
>    re-run showing no drift.
>
> #### Step 7 — Commit shape
>
> Branch (`fix/ais-excision` or similar) — this is *bringing external direction in*, so
> it branches by the git model rather than committing straight to `main`. Then
> `--no-ff` merge and delete.
>
> Split the work the way the producer did rather than one mega-commit: the **build
> retirement** (Class A) and the **prose excision** (Class B) are separate reviewable
> units, and any **graph write** is a third. Each commit message should name the gate
> ruling it executes, list the sanctioned survivors it deliberately left alone, and
> carry the test counts.
>
> Finally: flip **T12** in the port-prompt tracker (pending → done, with the gate-log
> date) and release or annotate the step-43 Tier B holds.

---

## Producer-side reference: the purge as actually executed

Three commits, in order. If the company session wants the diffs, they are on producer
`main`.

| Commit | Date | What it did |
|---|---|---|
| `ed93fe7` | 2026-07-21 pm | **The decision landing.** Pre-gate SME rulings applied across the gate prompt, `taxonomy-ontology-map.yaml`, `relationship_vocabulary.yaml`, `platforms.yaml`, and `software-registry.yaml` (the `#acronyms` note created here — the ruled home for the expansion). Statuses stayed gate-bound; nothing was enacted yet. |
| `27102d6` | 2026-07-21 | **C13 — the build retirement (Class A) + straggler sweep.** `:SchedulerKind` seeds commented out audit-kept; `scheduler_kind` constraint kept with a deprecation comment (count unchanged at 48); `seal_requires_scheduler` → `deprecated` with `superseded_by: reg_uses_software` (retired un-wired — no loader ever ran); map entry → `rejected` (SUPERSEDED, not repudiated); `cli.py` verify check retired with the seeds; `schema_graph.cypher` regenerated and tests re-pinned on the exclusion side. Suite 831 green. |
| `15c9d3f` | 2026-07-24 | **The Q6 follow-through (Class B).** `platforms.yaml`'s `company_confirmed` capture block, the company build mechanics, and the pre-supersede Q&A excised — 106 lines out, 51 in. Header rewritten to the gate outcome plus a pointer to the full capture (git history rev 2026-07-21 + the T12 pack); Q1–Q6 compressed to a closed-rulings record; seed rows kept **verbatim** (they are the batch-port crosswalk contract). Suite 900 passed / 6 skipped. |

The commit that closed it named its **sanctioned survivors** explicitly —
`software-registry.yaml#acronyms`, the `requires-scheduler` map entry's RESOLVED note,
and the signed gate pack `config/gate-prompts/platforms-taxonomy.yaml`. Copy that habit:
naming what you deliberately left behind is what makes the residual grep hits readable
six months later. (The first of those three is **no longer a survivor** — see step 2b;
the other two stand. The habit is what transfers, not that particular list.)

**The ruling being executed**, for citation (producer `config/gate-log.md`,
2026-07-21, C12, 3/3 as recommended): *the capability node layer is NOT adopted — the
registry `role` vocabulary carries the classification; the tool class MERGES into
`:SoftwareProduct`; `USES_TOOL` retires with the family; the spelling is removed on both
sides, with the acronym expansion surviving only in `software-registry.yaml#acronyms`;
the `Integration*` rename counter-proposal stays REJECTED.*

That quote is the ruling as signed and stays verbatim — but the acronym clause within it
is the one **reopened 2026-07-25** (step 2b). Everything else in it stands.
