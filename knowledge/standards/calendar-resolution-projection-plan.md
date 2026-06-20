# PLANNED PHASE — Calendar Resolution & Run Projection

**Corpus:** INTERNAL (company plan) — *not* vendor documentation.
**Status:** 🔵 **PLANNED** ("this or a future phase if necessary") — captured 2026-06-11 from SME.
**Goal:** Resolve Control-M calendar information so we can **project when jobs will run** — reproducing Control-M's own forecast capability outside the product (graph/Python side).

---

## Scope framing: what "projection" can honestly mean

Control-M's **two-plane model** ([job-scheduling](../vendor-bmc/controlm-job-scheduling.md)) splits *when eligible* (scheduling plane) from *whether/if it runs* (prerequisites: events, resources). A definition-driven projection can reproduce the **scheduling plane** exactly; the prerequisite plane is runtime-dependent.

So the projection target, in increasing ambition:
1. **Order-date set** — which ODATEs a job/folder will be ordered on. *(Deterministic from definitions — the core deliverable.)*
2. **Eligible time window per ODATE** — declared From/To time, else the **DC default time** from the data-center name ([data-center-naming-convention](data-center-naming-convention.md), all EST).
3. **Estimated start/end** — window + dependency chains (events) + historical durations (`%%AVG_TIME` style). *(Approximation; this is what BMC Forecast does with statistics.)*

---

## Inputs the resolver needs (inventory)

| Input | Source doc | Notes |
|---|---|---|
| Calendar definitions (Regular/Periodic/RBC) | [controlm-calendars](../vendor-bmc/controlm-calendars.md) incl. **Authoritative Additions** | Regular: explicit days + recurrence per **year**; Periodic: periods `A–Z,1–9`, ≤255 days each, may overlap |
| **RBC include/exclude lists per entity** | calendars doc → *Specific Rule-based calendar scheduling* table | The combination semantics: include lists schedule, exclude lists remove order dates; Folder RBCs vs Control-M RBCs |
| Job ↔ parent SMART folder **AND/OR relationship** | same | Governs how job criteria combine with folder RBC |
| Folder hierarchy + inheritance | [folder-definition-parameters](../vendor-bmc/controlm-folder-definition-parameters.md), [subfolder-creation](../vendor-bmc/controlm-subfolder-creation.md) | SMART → sub-folder → job |
| Scheduling criteria (6 types), cyclic settings | [job-scheduling](../vendor-bmc/controlm-job-scheduling.md) | Every Day / None / Specific Dates / Use Parent / Advanced(RBC) / etc. |
| Confirmation calendars + **8 exception policies** + **Shift By (−62..+62)** | calendars + job-scheduling docs | Applied *after* base date-set resolution |
| Order Method + New Day / **User Daily** time | folder-definition-parameters; [order-parameters](../vendor-bmc/controlm-order-parameters.md) | Automatic (New Day), Specific User Daily (e.g. `PUDLY0900` → 09:00 ordering), Manual = excluded from projection |
| ODATE mechanics (current working date / select date / wait-for-ODATE) | order-parameters | Date semantics of the projection rows |
| **DC default time** | data-center-naming-convention (INTERNAL) | `E####` in server name, EST, when folder/job declares no time |
| Activity periods / Keep Active / retroactive | calendars + job-scheduling docs | Blackouts and extension windows |
| Calendar **synchronization state** | calendars Authoritative Additions | ⚠️ With No Synchronization, the *same calendar name* may differ per Control-M/Server — resolve **per-server**, never globally by name |

---

## Resolution algorithm sketch (Phase B core)

For each candidate date **D** in the projection horizon, per Control-M/Server:

```
1. Is D an ordering day?  (Order Method)
   Automatic → New Day procedure date;  Specific User Daily → that User Daily's schedule;
   Manual/None → not projectable (flag as manual-order-only)
2. SMART folder date-set: evaluate Folder RBCs / Control-M RBCs (include lists)
   minus Excluded RBC list dates
3. Per job (and sub-folder): evaluate its criteria, combined with parent via the
   declared AND/OR relationship; apply its include/exclude RBC lists
4. Apply confirmation calendar → on mismatch, apply the exception policy
   (one of 8: disable / shift next / shift previous / …) and Shift By offset
5. Apply activity periods (blackouts) and Keep Active extensions
6. Result: ODATE ∈ projection  → attach time window:
   declared From/To time  else  DC default (E#### from server name, EST);
   cyclic jobs expand into interval/specific-times series within the window
```

**Validation oracle:** compare projected order-date sets against (a) Control-M's own Forecast/planned view where available, and (b) **observed history** (Active Jobs / run history) for past dates — exactness on the scheduling plane is achievable and should be asserted, not assumed.

---

## Phasing

- **Phase A — Acquire & normalize calendar data.** Pull calendar definitions + RBC lists + AND/OR relationships into the C3 staging model ([[project_controlm_c3_normalization]] — same pipeline that owns jobs/vars; ~240K jobs, 4 DCs). Per-server, year-stamped.
- **Phase B — Date-set resolver.** Implement the algorithm above in Python (consistent with "Python owns var resolution"). Output: `(server, folder, job) → {ODATE…}` over the horizon.
- **Phase C — Time projection.** Attach time windows (declared else DC default), expand cyclic series.
- **Phase D — Validate & publish to graph.** Backtest vs history; emit projection nodes/edges so the graph answers "what runs next Tuesday at 07:00 EST?"

---

## Known limits & gotchas (recorded up front)

1. **Year coverage:** Regular/Periodic calendars apply to explicit years ("Apply on") — projection horizon is capped by how far calendars are populated; missing next-year calendars are an operational reality to detect and report, not assume.
2. **Per-server resolution:** unsynchronized calendars can share a name with different contents across servers.
3. **Manual orders:** Order Method = None and ad-hoc orders (incl. *Ignore scheduling criteria*) are invisible to a definitions-based projection — out of scope, label as such.
4. **Prerequisite plane:** events/resources can delay or starve an eligible job; Phase 1–2 projections are "eligible to run," not "will have run."
5. **z/OS relative calendars** (`+`/`-` closest-date, IOABLCAL) — only if z/OS estate is in scope *(to confirm)*.
6. **Periodic period semantics** (how periods `A–Z,1–9` are referenced by job criteria) — needs a worked production example before Phase B *(to confirm)*.

Related: [[project_controlm_c3_normalization]], [[project-datacenter-naming-time]], [[project-description-metadata-plan]], [[project-controlm-xml-not-json]]
