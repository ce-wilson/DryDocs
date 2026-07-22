# T12 — company platforms gate session pack (supersede-or-reconcile)

**Prepared producer-side 2026-07-21** (the paste-ready-materials pattern from the L7
ratification snippet, made durable so it rides the port). This pack is INPUT to a
**company gate session** — it decides nothing by itself. Per the two-tier gate-adoption
doctrine ([`port-prompt.md`](port-prompt.md) guardrail 6, **Tier B**): the company holds
its OWN signed position on platforms (the 2026-06-29 AIS gate), so the producer C12
outcome may NOT be adopted via port — this session must supersede-or-reconcile first.
Until it signs, every C12/C13/C14 semantic flip stays HELD company-side (step 43).

Everything cited here is already in the producer repo in sanitized form (platforms.yaml
`company_confirmed` capture; gate-log 2026-07-21). No internal tool names, instance
data, or org values appear in this pack — the company session fills those from its own
`internal/`.

---

## 1. The two signed positions

**Company 2026-06-29 (AIS gate — BUILT and LOADED company-side):**
- Classes: `:AisCapability` (skos:Concept; 3 areas — orchestration / etl / file-transfer)
  and `:AisTool` (prov:SoftwareAgent; 7 tools — 5 public vendors + 2 internally-built
  managed-file-transfer tools, names company-side only).
- Edges: `IN_CAPABILITY` (skos:broader, 7 edges seeded); `USES_TOOL`
  (app → tool, **declared only** — no edges seeded per the C11 capture).
- `:SchedulerKind` deprecated (deprecated=true, kept for audit).
- Build: `platforms_supplement.cypher`, applied on demand; ontology-map C2c
  adoption: confirmed.
- Known audit gap (company-acknowledged): NO 06-29 gate-log entry exists; backfill was
  offered and is still pending.

**Producer C12 (2026-07-21 pm, SAME SME — config/gate-log.md, 3/3 as recommended):**
- The registry model: NO capability/tool class layer at all ("role over class" — the
  SME: 'Orchestration' was the intended highest classification level; the registry
  `role: orchestrator` carries it; a capability node layer duplicates it).
- The app→orchestrator fact = the ACTIVE registry edge
  `(:BusinessApplication)-[:USES_SOFTWARE {source: 'batch-port'}]->(:SoftwareProduct
  {role: 'orchestrator'})`. `USES_TOOL` retired with the Ais* family.
- Q6: the Ais* spelling is removed **on both sides**; the acronym expansion
  ("Application Integration Streaming") survives ONLY as
  `software-registry.yaml#acronyms` (producer-authoritative; the company's
  source-registry gloss is PROVISIONAL and defers to it — carry across at port,
  never same-file overwrite).
- Producer builds already landed and live-verified on the producer graph:
  **C13** (SchedulerKind seeds retired audit-kept; `seal_requires_scheduler`
  deprecated, superseded_by `reg_uses_software`; map entry closed) and **C14**
  (the `batch_port_orchestrator` loader — crosswalk from platforms.yaml seed rows'
  `software_registry_ref`, edge MERGE keyed on `{source: 'batch-port'}`, unmapped
  strings flagged + reported never guessed; both USES_SOFTWARE writers now key
  their MERGE on `source`).

**The conflict is real but narrow:** both positions agree the concrete tools are
first-class and `:SchedulerKind` is dead. They disagree on whether a
capability/tool class layer exists between apps and the software registry.

## 2. The session question

> Does the company SUPERSEDE its 06-29 AIS position with the C12 registry model,
> or RECONCILE (keep a company-local Ais*/capability view alongside it)?

**Producer recommendation: SUPERSEDE.** The same SME signed both positions and the
later one (C12) explicitly ruled the earlier layer out ("Ais* removed on both sides";
the Integration* rename counter-proposal REJECTED — no replacement class family).
Reconcile would preserve a layer whose meaning C12 found duplicative
(capability area 'orchestration' ≡ registry role 'orchestrator') — listed only for
completeness.

## 3. Ruled vs genuinely open (do not re-litigate the left column)

| Already ruled (C12, same SME) | Genuinely open for THIS session |
|---|---|
| No capability/tool node layer; registry role carries the classification | What happens to the LOADED Ais* graph data: 3 `:AisCapability` + 7 `:AisTool` nodes + 7 `IN_CAPABILITY` edges — deprecate-in-place (audit-kept, the 06-29 SchedulerKind precedent) vs remove. Graph writes are always company-side (T9). |
| `USES_TOOL` retired; landing = `USES_SOFTWARE {source: 'batch-port'}` | Verify `USES_TOOL` really has zero edges company-side (it was declared-only) before retiring the declaration. |
| Ais* spelling removed both sides; acronym only in `software-registry.yaml#acronyms` | The 2 internal MFT tools + etl-area tools: do they get company software-registry rows (roles `tool`/`data-platform` exist in the ALLOWED_ROLES vocabulary)? C14's loader maps ORCHESTRATORS only — the etl/file-transfer areas were never in its scope. Names stay in company `internal/`. |
| `seal_requires_scheduler` retires un-wired; `reg_uses_software` typing covers (B4) | The company crosswalk contents: which company-side orchestrator strings map to which registry refs (their AWS leg = EventBridge Scheduler + Glue — NOT Airflow; the producer airflow row is an F2 crosswalk placeholder only, B5). |
| — | The 06-29 gate-log backfill entry (offered, pending) — this session is the natural moment to land it. |

## 4. If SUPERSEDE signs — company build follow-ups (their C13/C14 analogues)

1. **Gate-log**: append the supersede entry (template below) — and optionally the
   06-29 backfill entry above it, clearly marked as a backfill.
2. **platforms_supplement.cypher**: retire the Ais* seeds audit-kept (the producer
   `ontology.cypher` C13 edit is the pattern: seeds commented with the deprecation
   record, constraints kept for old graphs).
3. **Graph cleanup** per the session's deprecate-vs-remove ruling (their graph, their
   writes — a port never substitutes, T9).
4. **Vocab/map/config flips**: apply the held C12/C13 effects (platforms.yaml
   semantics, `seal_requires_scheduler` deprecation, requires-scheduler map closure)
   via the normal per-entry port mechanics — they arrive in the step-43 range.
5. **C14 company-side**: run the ported `batch_port_orchestrator` loader against THEIR
   business-application capture + THEIR platforms crosswalk; live-verify on their
   graph (edge counts + idempotent re-run; the producer report: 3 batch-port + 4
   registry edges, both writers keyed on `source`). Real SEAL-declared strings replace
   the producer's synthetic ones.
6. **Acronym port caveat** (standing): producer `software-registry.yaml#acronyms` is
   authoritative; the company source-registry gloss stays PROVISIONAL — carry the
   expansion across, don't same-file overwrite.

If RECONCILE signs instead: document the company-local layer's continued meaning in
their ontology-map (who consumes it, why it isn't duplicative), keep Tier B holds on
every C12-driven flip that contradicts it, and add a standing-divergences ledger row —
the producer stays on the registry model regardless.

## 5. Paste-ready company gate-log entry (SUPERSEDE form — edit dates/notes in session)

```markdown
## <YYYY-MM-DD> — Platforms: 06-29 AIS position SUPERSEDED by the registry model (T12) — SIGNED OFF

Session convened per the Tier B doctrine (port-prompt guardrail 6): the producer C12
platforms-taxonomy gate (2026-07-21, same SME, producer gate-log) ruled the registry
model — no capability/tool class layer; role over class; USES_SOFTWARE
{source: 'batch-port'} as the app→orchestrator landing; Ais* removed both sides,
acronym preserved only in software-registry.yaml#acronyms.

Ruling: SUPERSEDE. The 2026-06-29 AIS gate position (AisCapability/AisTool/
IN_CAPABILITY/USES_TOOL) is superseded, not repudiated — kept for audit.
- Loaded Ais* graph data: <deprecate-in-place | remove> — <notes>
- USES_TOOL declaration: retired (verified zero edges: <yes/no + count>)
- Internal MFT / etl tools → registry rows: <ruling>
- Company orchestrator-string crosswalk: <rulings, incl. EventBridge/Glue handling>
- 06-29 backfill entry: <landed above | deferred>

Effect: step-43 Tier B holds RELEASED — C12/C13 config flips apply per the port
mechanics; C14 loader run + live verify tracked as <their follow-up id>.
Confirmed: <n> · Edited: <n> · Rejected: <n> — <SME sign-off>
```

## 6. After the session

- Flip **T12** in the port-prompt tracker (pending → done, with the gate-log date) and
  release/annotate the step-43 holds accordingly.
- Producer-side: nothing further is owed — C12/C13/C14 are complete and pushed; the
  producer only reviews the next PORT-REPORT as usual.
