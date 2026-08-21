# wf-admin-config-01 — admin configuration page (rung 2, text wireframe)

> Spec source: the 2026-07-16 IDEAS launcher-registry line ("end state = an admin screen
> in the web console, Epic O candidate") — groomed 2026-07-17 as **O12**. Route:
> `/admin/config`, visible ONLY to the admin persona (O2 gating). Rung-3 companion:
> `wf-admin-config-01.html`.
>
> **The DryDocs twist vs. a typical SaaS config console:** config here is
> config-as-code behind HITL gates. The page therefore has **no edit controls** — it is
> the *traceability lens*: what is configured, which code consumes it, which test
> enforces it, which gate approved it. "Edit" = a deep link to the repo path + the gate
> flow. This keeps the site-plan read-only rule intact.

```
+---------------------------------------------------------------------------------+
| [logo]                  [ search.... ]        [Prod|UAT|Dev] [theme] [bell] [@] |  HEADER (global)
+--------+------------------------------------------------------------------------+
| ASIDE  | TOOLBAR:  Home > Admin > Configuration        [refresh] [v Export] (1) |
| (nav + |------------------------------------------------------------------------+
| ADMIN  |                                                          | RIGHT       |
| badge) |  GRAPH PANE: traceability chain of SELECTED surface (2)  | SIDEBAR     |
|        |                                                          | surface     |
|        |  [config file] --> [consumer] --> [guard test] --> [gate]| metadata:   |
|        |   source-        loaders/         test_source_    per-   |  path       |
|        |   registry.yaml  base.py+adapters registry.py     source |  schema/ver |
|        |                                                          |  last commit|
|        |  (chain re-renders on matrix row select)                 |  gate ref   |
|        |                                                          |  classifi-  |
|        |========== resizable divider ============================ |  cation     |
|        |                                                          |             |
|        |  DATA FRAMES                                             | [view file] |
|        |  [ Enforcement matrix ] [ Surface detail ] [ Gate log ]  | [repo path] |
|        |  +----------------------------------------------------+ | [gate flow] |
|        |  | surface | file | consumers | guard tests | gate |st| |     (3)     |
|        |  | rows... (generated, see (4))                       | |             |
|        |  +----------------------------------------------------+ |             |
+--------+----------------------------------------------------------+------------+
```

Instantiates the shared template (`wf-module-subpage-01.md`) — graph pane = the trace
chain, tabs = matrix / detail / gate log, inspector = surface metadata. No template
drift.

## Annotation key

1. Export (O11 path) applies to the matrix itself — auditors get the enforcement
   matrix as CSV+manifest. The matrix QuerySpec is classification `internal-public`
   (mechanism, no data values).
2. Graph pane shows the **selected surface's chain** as a mini React Flow DAG:
   `config file → code consumer(s) → guard test(s) → gate reference`. Multi-consumer
   surfaces fan out. Clicking a chain node selects that column in the matrix row.
3. Inspector actions are LINKS, not editors: `view file` (read-only render tab),
   `repo path` (copy), `gate flow` (the surface's gate prompt / gate-log anchor).
4. **The matrix is GENERATED, never hand-typed**: a build step
   (`scripts/render_enforcement_matrix.py`) scans `config/` + `tests/unit/` +
   consumer annotations and emits `enforcement-matrix.json`; the page renders that
   artifact. A unit test fails when (a) a config surface has no matrix row, or
   (b) a row references a missing file/test — the matrix cannot drift from the repo.
   (Same pattern as the board render: yaml = truth, render = artifact, test = guard.)
5. Surface detail tab renders the YAML read-only with the schema header highlighted;
   `internal` surfaces show the classification banner and redact values the
   client-side never sees (server sends structure + keys only for surfaces
   carrying confidential material — since J23 that handling is a property of
   the entry, not a separate tier).
6. Status column values: `enforced` (guard test exists + passing at last CI),
   `unguarded` (surface with no test — a visible red flag, this is the page's KPI),
   `gate-pending` (entries with status planned awaiting HITL).

## The enforcement matrix — seed rows (verify consumers at generator build)

| Surface | File | Consumer (code) | Guard test | Gate ref |
|---|---|---|---|---|
| Source registry | `config/source-registry.yaml` | loaders/adapters (`drydocs/loaders/`, add-source-object flow) | `test_source_registry.py` | per-source gates |
| Column ledgers | `config/source-mappings/` | loader extract SQL + `to_params` | `test_source_mappings.py`, `test_source_mapping_drift.py` | doc-08 ledgers |
| Audit envelope | `config/audit-fields.yaml` | loader cypher audit props | `test_audit_fields.py` | doc-06 per-source |
| Precedence | `config/precedence.yaml` | conflict resolution at load | `test_precedence.py` | — |
| Classification | `config/classification.yaml` | publish boundary / publishing | `test_classification.py`, `test_publishing.py` | PUBLISH-BOUNDARY.md |
| Taxonomy→ontology map | `config/taxonomy-ontology-map.yaml` | mapping activation, ontology loaders | `test_taxonomy_ontology_map.py` | HITL (03-hitl-sme-flow) |
| Relationship vocabulary | `drydocs_core/ontology/relationship_vocabulary.yaml` | cypher templates / loaders | `test_controlm_cypher.py` (+vocab checks) | RELATIONSHIP_GUIDE + gates |
| Taxonomy captures | `config/taxonomy/*.yaml` | taxonomy-importer outputs | (namespace checks) | — |
| Manual loads (tier 5) | `config/manual-loads/` | `manual_loads.py` | `test_manual_loads.py` | K2 match-policy |
| Review labels | `config/review-labels.yaml` | drydocs-review components | `test_review_labels.py` | — |
| Crosswalks | `config/crosswalks/` | orchestrator mapping (F1/F2) | (crosswalk gate acceptance) | F1 13/13, F2 17/17 |
| Gate prompts/log | `config/gate-prompts/`, `gate-log.md` | HITL flow, gate pages | `test_gate_pages.py` | (is the gate record) |
| Launcher registry | TODAY: `drydocs_core/controlm/commands.py` (code-resident) | command parser | `test_command_parser.py` | — |

The launcher-registry row demonstrates the page's purpose: it renders with
`file = code-resident` — visibly the odd one out, which is exactly the argument for
its config-file migration (still inboxed, separate groom).

## Open items — RESOLVED (user decisions 2026-07-17)

- [x] CI test-result freshness: **"last run" metadata only** — the matrix shows each
      guard test's result + timestamp from the most recent CI artifact; no live CI
      polling. Stale-run age renders as plain text (e.g. "last run 3d ago"), not a
      health color.
- [x] Confidential redaction: **dissolved — secrets are `.env`-only.** Config files
      never carry secret values (they carry env-var *references*); therefore the
      surface-detail tab can render every config file verbatim. The matrix gains an
      `env-refs` cell listing which env keys a surface expects — names only, values
      never leave the server.
- Follow-on surface: manual mapping stewardship (job→application etc.) is NOT this
  page — it is the power-user screen `wf-mapping-01.md` (**O13**).
