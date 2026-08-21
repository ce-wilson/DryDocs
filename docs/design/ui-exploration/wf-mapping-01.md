# wf-mapping-01 — manual mapping stewardship, power-user screen (rung 2)

> Captured 2026-07-17 from chat ("manual mapping for instance Control-M jobs to
> business application, or code to application — a power user screen") — groomed as
> **O13**. Route: `/mappings`, visible to a new **steward (power-user) persona** plus
> admin (extends the O2 mock-persona set). Rung-3 companion: `wf-mapping-01.html`.
>
> **The one rule that shapes everything: the loader stays the ONLY graph writer.**
> This screen never writes to Neo4j. It drafts changes to the *manual mapping tables*
> the reconcilers already consume (K2 match policy: tier precedence
> SEAL > FID > APP_NAME > ALIAS > manual CSV tier-5 in `config/manual-loads/`), and
> those changes travel the existing path: change artifact → review/gate → merge →
> next load run applies them. The UI compresses the drafting, not the governance.

```
+---------------------------------------------------------------------------------+
| [logo]                  [ search.... ]        [Prod|UAT|Dev] [theme] [bell] [@] |
+--------+------------------------------------------------------------------------+
| ASIDE  | TOOLBAR: Home > Mappings > Job→Application     [refresh] [v Export]    |
| (nav + |------------------------------------------------------------------------+
| STEW-  | DOMAIN STRIP: [Job→Application*] [FID→seal_id] [ALIAS→seal_id] (1)     |
| ARD    |------------------------------------------------------------------------+
| badge) |                                                          | CHANGESET   |
|        |  ATTRIBUTION COVERAGE GRID (main pane)                   | TRAY (4)    |
|        |  filter: [unresolved] [tier..] [folder..] [app..]        |             |
|        |  +----------------------------------------------------+ | draft #1    |
|        |  | job (folder/job key) | current app | tier | via    | |  JOBX ->    |
|        |  | PRARAG../JOB_A       | APP-1234    | SEAL | var    | |  APP-9876   |
|        |  | PRARAG../JOB_B       | APP-1234    | APPN | name   | |  rationale~ |
|        |  | PRBCDE../JOB_C       | (none)  (2) | --   | --     | | draft #2    |
|        |  | PRBCDE../JOB_D       | APP-2222 !  | ALIAS| alias  | |  ...        |
|        |  +----------------------------------------------------+ |             |
|        |                                                          | [submit     |
|        |  ROW ACTION: [assign to application...] (3)              |  changeset] |
|        |   -> app picker (search BusinessApplication              |     (5)     |
|        |      by seal_id / name) + REQUIRED rationale             |             |
|        |                                                          | lifecycle:  |
|        |  (bulk: multi-select rows -> one target app)             | draft >     |
|        |                                                          | submitted > |
|        |                                                          | gated >     |
|        |                                                          | loaded (6)  |
+--------+----------------------------------------------------------+------------+
```

## Annotation key

1. **Domains = the reconciler-consumed manual tables**, not free-form mappings:
   - `Job → Application` — tier-5 manual CSV (`config/manual-loads/`), the K2 seam;
   - `FID → seal_id` — tier-2 table (K6/T2: possibly derivable from folder variables);
   - `ALIAS → seal_id` — tier-4 table (T3).
   "Code → application" (repo/script → app) joins the strip when that mapping table
   exists as a reconciler input — same mechanics, new domain tab; the strip is
   registry-driven like the module menu.
2. The grid is the **coverage view**: every job with its CURRENT resolution
   (tier + evidence), unresolved rows floated to top — the steward's work queue.
   `!` marks conflicts (two tiers disagree) — second work queue.
3. Assigning NEVER writes the graph. It drafts a row: `(source key, target seal_id,
   rationale REQUIRED, author, timestamp)`. Rationale is mandatory — it becomes the
   manual CSV's provenance column and the gate reviewer's context.
4. The changeset tray accumulates drafts across domains; persisted per-user
   (localStorage until the api draft endpoint exists).
5. **Submit produces a change ARTIFACT, not a write**: a `config/manual-loads/` CSV
   diff via a drydocs-api draft endpoint (or file download fallback) → lands as a
   branch/PR → HITL review per the K2 gate discipline → merged → **next load run**
   applies it (tier-5 reconciler). The UI compresses drafting; git + gate + loader
   stay the authority chain.
6. Lifecycle chips per entry: `draft → submitted → gated → loaded`; `loaded` is
   confirmed by the coverage grid itself flipping the job's tier to `manual` after
   the next load — the screen self-verifies against the graph.
7. Traceability tie-in: this screen's tables are O12 enforcement-matrix rows
   (`config/manual-loads/` → manual_loads loader → `test_manual_loads.py` → K2 gate)
   — the admin page proves the mapping screen's own surface is guarded.
8. Persona: `steward` sits between user and admin (extends O2 mock auth): sees
   Mappings; does NOT see /admin/config or the Cypher sandbox.

## Open items

- [ ] Draft-endpoint shape: PR-creating (needs git credentials server-side) vs
      artifact download + manual PR — decide at build with whatever the company
      GHE posture allows; wireframe supports both (submit button label changes).
- [ ] Conflict rows (`!`): does a manual tier-5 entry silence the conflict or does
      the conflict escalate to a gate question? (K2 precedence says manual is
      lowest tier — a manual entry does NOT override SEAL evidence. Surface this
      in the assign dialog: "this job already resolves at tier SEAL; a manual
      entry will not override it.")
