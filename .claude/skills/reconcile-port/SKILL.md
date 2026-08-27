---
name: reconcile-port
description: Reconcile a producer push (ce-wilson/main) onto the company DryDocs main. Use when applying a new DryDocs port, syncing from the ce-wilson producer repo, resolving disjoint-history cherry-pick collisions, validating Track-1 after a port, or writing a port report.
---

You are on the **company** DryDocs repo. The **producer** is
`https://github.com/ce-wilson/DryDocs.git` (`main`). This repo was `git init`-ed
fresh, so the two histories are **disjoint — no common ancestor**. A port is
therefore a **cherry-pick / `git am`**, not a true rebase, and is **one-way**
(producer → company). Company `main` is canonical here and is *ahead* of the
producer in several areas (see the divergence ledger) — keep the company version
of those.

The authoritative per-port detail lives in the producer's `git-readme.md`
(`git show cewilson/main:git-readme.md`). This skill is the repeatable wrapper +
the accumulated lessons from prior ports. Read both.

## Procedure

1. **Preflight.** Clean tree, on `main`. Set a backup tag:
   `git tag -f pre-cewilson-port`. Add/refresh the remote and fetch:
   `git remote add cewilson https://github.com/ce-wilson/DryDocs.git` (ignore if
   it exists), then `git fetch cewilson main --tags`.
   **THEN CHECK THE BASE IS CERTIFIED (J41).** Port
   `<last-ported>..port-base-YYYYMMDD`, never `..HEAD`. **If the producer offers a
   bare SHA or "HEAD", STOP and ask for the tag** — same shape as the
   fetch-failure rule, and for the same reason: producer `HEAD` moves while you
   read it (on 2026-08-09 a base moved 42 → 45 commits mid-session), and an
   untagged commit is one nobody ran the opening sequence against. Two real
   failures shipped in one such range — a `FORCE_COLOR` colour-vs-behaviour test
   failure and a duplicate `Idea-101` — either of which would have broken the
   zero-fail acceptance contract and read as port-introduced.
   If producer HEAD has moved past the tag, that is NORMAL: those commits ride the
   next port, not this one.
2. **Read the manifest first:** `git show cewilson/main:PORT-MANIFEST.yaml` —
   the machine-readable disposition per path (first match wins; `**` spans
   separators, `*`/`?` do not; per-entry rows FORBID whole-file checkout).
   A path matching no row takes `default:` — but only legitimately if it is
   listed in `default_ok:` at the bottom of the manifest with a reason (J16).
   **A path in neither is an un-made decision, not a clean-add:** stop and
   decide it, then send the row back. Then the narrative:
   `git show cewilson/main:git-readme.md` ("Clean-adds", "Canonical-here",
   "Collisions" sections). Manifest wins on disagreement.
3. **Apply onto `main`** (skip the optional scratch branch unless asked):
   - **Clean-adds** (path absent here) → apply untouched.
   - **Canonical-here** → take the producer version wholesale, do **not**
     hand-merge: `git checkout cewilson/main -- <path>`. This includes the
     entire `drydocs_core/controlm/` package, `knowledge/standards/`, the Control-M
     SQL/DDL, `relationship_vocabulary.yaml`, `catalog_ontology_supplement.cypher`,
     **and the `tests/unit/test_variable_*` files** (taking these wholesale
     avoids re-deriving the skip guards — see ledger note).
   - **Collisions** → hand-merge per the ledger below.
4. **Validate Track-1** (the contract — needs no data file).
5. **CHECK THE BACKLOG UNION (J42).** The manifest's row for
   `docs/restructure/backlog/items/*.yaml` promises *"never drop a file"*, and until
   J42 nothing compared the two id sets — every backlog guard reads ONE copy, so a
   port that quietly under-delivered items left both sides internally consistent and
   green. Run it AFTER the apply, from this repo, naming the same port-base tag you
   ported from:
   `poetry run python scripts/port_backlog_union.py --producer-ref port-base-YYYYMMDD`
   Exit 0 = the union holds (any ruled omissions print WITH their reasons). Exit 1 =
   the port dropped items and the run names every id — restore each file from the
   base, or record it in `drydocs.port_backlog_union.UNION_EXCLUSIONS` with the
   reason it stays behind. Exit 2 = a side could not be read, which is a FAILURE and
   never "no difference": the tombstone `docs/restructure/backlog.yaml` has no
   `items` key, so a check aimed there would compare two empty sets and pass for
   being wrong. Paste the printed block into the port report. This covers the UNION
   half only — the status-regression half is the J16 before/after guard above.
6. **Don't push.** Write a port report (template below) and stop.

## Encoding trap (company send-back, PORT-REPORT-ae21ee4, 2026-08-10)

PowerShell 5.1 mojibakes em-dashes in `git show` output (the console codepage, not
git), which makes block-extraction from producer files UNSAFE there — a copied block
silently differs from the source. For any per-entry/union work on files containing
em-dashes (`backlog.yaml`, `IDEAS.md`, this repo's prose generally), do the
extraction and insert in PYTHON reading the file as UTF-8, never by pasting from
PowerShell output. The ae21ee4 port hit this live and routed around it; this note is
the producer-side half of that lesson.

## Collision ledger (resolve these by keeping the noted side)

| Path | Resolution |
|---|---|
| `drydocs/cli.py` | Keep company `m6-verify` (and `ingest-controlm-xml` etc.); **add** producer `analyze-variables` + `normalize-variables`, `m3-verify` (validates the ported M3 structural layer — keep it, it is **not** a stray), the `_scope_binds` / `--folder/--run-as/--developer-sid/--row-cap` options, and the `_oracle_adapter(query, bind_params=None)` change; merge imports. Confirm your `OracleAdapter` accepts `bind_params` and forwards it to `cursor.execute` (company Kerberos adapter already does). |
| `drydocs_core/models/__init__.py` | Union — keep **all** row models from both sides in imports + `__all__`. |
| `drydocs_core/models/controlm.py` | Keep company `ControlMQuantitativeRow`; add producer `ControlMVariableRow` (`AliasChoices` import is shared). |
| `tests/unit/test_schema.py` | Keep company `EXPECTED_CONSTRAINTS = 44` (ahead of producer's 35). |
| `tests/unit/test_controlm_cypher.py` | Keep company version (`scope_key` + version_serial-as-property). |
| `tests/unit/test_variable_classifier.py`, `test_variable_staging.py` | **Canonical-here — take producer wholesale.** They already carry `skipif(not SAMPLE.exists())` guards (producer commit `9e9fe1c`). Do not re-write your own guard; that caused redundant divergence in a prior port. |
| `pyproject.toml` | Union — preserve company's Python-version constraints, Oracle/Kerberos deps, and any extra test deps; **add** producer's new deps: `requests` (aura manager) and `pypdf` (PDF ingestion). Neither conflicts with company deps. |
| `tests/unit/test_module_boundary.py` | **Canonical-here — take producer wholesale.** It carries the `ENTRYPOINT_MODULES` exemption (`drydocs.cli` is the composition root and may wire any component), which is the settled resolution to the company `cli.py` → review-module cross-import failure — do NOT extract review commands into a sub-app or collapse groups to dodge the guard (that was options B/C, rejected; A is documented in `MODULE_MAP.md`). |

**Skipped-commit policy:** the early overlap commits where company content is
already richer (prior ports skipped `3bc7adb`, `0eb98a5`, `6c5b7b5`, `0063f07`)
stay skipped — confirm with the operator if a new one appears.

## Divergence ledger (company is ahead — keep company)

- **`drydocs/cli.py` + the `cli_*` submodules — the company tree carries BOTH
  CLI generations AT ONCE (found 2026-08-27, company worktree session):** the
  ported split modules (their `cli_docs.py` holds the producer
  `load_doc_traceability`) ALONGSIDE the pre-split monolith (their `cli.py`
  still defines an inline one) — duplicate command paths, not a simple
  behind/ahead. Company-measured shape: their root 3,584 lines / 61 inline
  `@app.command` vs producer 1,201 / 4 + submodules. The pair already bit
  once as a PARTIAL ATOM: `cli_docs.py` crossed without its
  `DOC_TRACEABILITY_CHAIN` dependency (producer `cli.py:364`), producing
  their 58-red baseline; their session resolved it minimally,
  company-authored, after MEASURING rather than taking the producer copy —
  a producer sentence recommending the wholesale take was wrong and is the
  incident behind profiling-sync-packet.md §6. NEITHER side's copy is
  wholesale-takeable; de-duplicating onto the split is the company's own
  reconcile session. TRIGGER: their SME review status citing the
  constant-fix commit retires the partial-atom half; the
  duplicate-generations half retires only when a company reconcile session
  closes the de-dup with its own commit cited.
- **`config/taxonomy/tom-role-vocabulary.yaml` — the register is company-RULED
  (2026-08-26 G70 adoption session): Module Owner renamed, Capacity Planner
  added, IRM flipped `required` — ruled against 232k-row report exports the
  producer never sees.** Manifest row landed 2026-08-27 (per-entry, the
  lob-product-team shape): company-ruled classes stay; producer mechanism and
  producer-NEW classes cross; required/scope/active on EXISTING classes are
  never merged or "synced" — each side's SME owns its register.
- **`config/gate-log.md` two-tier doctrine (ruled at PORT-REPORT-e33f8d02):
  producer DRAFTED stubs are NOT appended company-side** — producer
  gate-drafting is captured by the landed gate-prompt files; the company log is
  the company's audit. Do not count producer stubs as missing entries at the
  union check, and never write producer stubs into the company log.
- **`drydocs_remediation/detect.py` — divergent+deferred union pending
  (e33f8d02):** company carries DPL detectors and lacks R41–R44; producer b26
  dropped DPL and refactored. Neither side is taken wholesale — the
  remediation-adoption session (dossier `adoption-1-remediation-dossier.md`,
  hand-carried) does the union: keep `detect_dpl_findings`, add R41–R44.
- **Ontology + lineage clusters — deferred whole at e33f8d02 (both the 20260825
  and 20260826 increments), adoption path is the three hand-carried dossiers**
  (remediation, then lineage, then ontology-behind-a-company-gate). The G70
  slice began 2026-08-26 company-side (register reconciled, wiring built);
  until an adoption report closes a cluster, its files stay at the
  company-divergent state and are NOT re-taken by a later port.
- **`drydocs/run_as_detect.py` per-line reconcile — ENDED 2026-08-27:** the
  producer adopted ASCII `x` (`64ec0e7e`), so the RUF002/RUF003 divergence
  e33f8d02 recorded dies at the next port; no per-line handling needed.

- Verify command: company `m6-verify` vs producer `m3-verify`.
- `EXPECTED_CONSTRAINTS`: company is ahead as a **superset** (base + snow-support
  supplements; 45 ⊇ 40 at the 2026-07-20 bundle port). Counts drift every port —
  trust the live `test_schema.py` / `constraints.cypher` on each side, not any
  recorded number (66acea8 lesson: "trust the file, not the ledger").
- Condition key: `scope_key` vs producer `folder_id`.
- Suite size: company suite is much larger (scrapers/Confluence). **Do not chase
  the producer's `186 passed` full-suite number** — only zero *new* failures matters.
- **Permanently-diverged tests (bd7952f bundle port, 2026-07-20) — removed
  company-side; do NOT re-add them as clean-adds and do NOT count them in
  acceptance:** `tests/unit/test_publishing.py` (producer publishing template;
  company ships the real Confluence connector), `tests/unit/test_sql_run_log.py`
  (producer adapter-level `run_log`; company uses cli-level `_load_run_log`), and
  `tests/unit/test_schema_graph.py` (expects the producer `docs_*` vocab /
  regenerated schema_graph — company defers that ontology). **Sequencing trap:**
  the 388a30d follow-up "commit the drift guard" conflicts with the bundle-port
  removal — re-add `test_schema_graph.py` ONLY after the company's own
  doc-traceability-feedback gate activates the doc vocab; until then it fails by
  design.
- `drydocs_core/adapters/oracle_adapter.py`: company version is **Kerberos-aware**
  (thick via `_init_thick_client` / `externalauth` when `ORACLE_KERBEROS=True`);
  the producer version is thin-only. **Keep company's** — it carries the JPMC
  connection config (`client_path`, `tns_admin`, TNS alias). The producer's
  scope-bind SQL runs under it unchanged.
- **Company-only modules the producer has never had** (surfaced by the
  2026-06-30 port report; ~175 company-only paths). These are **not** clean-adds
  and must never be deleted or "reconciled" — they simply do not exist producer
  side, so an inbound port leaves them untouched:
  - *Architectural / low-sanitization-risk* — `graph_review.py`, `graph_verify.py`,
    `sme_notes.py`, `drydocs/publishing/`, `site/`. These are back-flow candidates
    (reproduce generically in the public producer via the screenshot/describe
    channel; set `classification` on each). If/when the producer grows a generic
    same-named file, it becomes a **collision** — add a ledger row then.
- **`drydocs-review` collisions are LIVE (ledger row, 2026-07-07).** The producer's
  generic twins landed 2026-07-01 (Epic H: `graph_review.py`, `graph_verify.py`,
  `review_labels.py`, `sme_notes.py`, `gate_pages.py`, `drydocs/publishing/**`,
  `config/review-labels.yaml`, `config/gate-prompts/**`, `graph-tests/**`) — resolve
  **Canonical-COMPANY** per port-prompt step 10 / git-readme "`drydocs-review` —
  back-flow stream". Three 2026-07-07 refinements (port-prompt steps 17–18):
  (a) seed-file rename `vendor-bmc-*` → `bmc-docs-*` must be applied company-side
  (the producer's generic tests assert the new names); (b) the `gate_pages.py`
  meta-card + SOURCE/DERIVED provenance extension is pure mechanism — fold into the
  company copy and upgrade real specs to the test-enforced standard format, or
  decline delta + tests together; (c) `config/gate-log.md` merges ADDITIVELY
  (append-only audit — never drop either side's entries).
  - *Internal data-bearing — never back-flow as values* — `locations.py`
    (DSNs/server locations), `seal_deployments.py` (real SEAL IDs),
    `controlm_app_codes.py` (app-code values), ServiceNow HPSM config. Company-side
    only; at most a bare schema/template may cross, never the values.
- **`seal_app_ref` (Epic K) — back-flow-origin, so check before taking wholesale.**
  Producer `main` carries a `job-seal-app-ref` relationship + `m3_seal_app_ref` mapping
  as `status: planned`/`proposed` in `relationship_vocabulary.yaml` +
  `taxonomy-ontology-map.yaml` (both normally Canonical-here → take producer). But Epic K
  was **groomed from company reconciliation** — the concept came FROM the company. So:
  - While it is `planned`/`proposed` on the producer, it is **inert** (no graph impact) —
    taking the producer ontology files wholesale is safe.
  - **If company `main` has already promoted `m3_seal_app_ref` to `active`/`confirmed`
    (or has a live loader for it), that specific entry is a back-flow COLLISION — keep
    the company's active version; do NOT downgrade it to the producer's `planned` state.**
    Reconcile per-entry, not by taking the whole file blindly.
- **Fixture file naming — DOUBLE vs SINGLE underscore (G78, SME-confirmed 2026-08-11).**
  Producer fixtures are `<loader>__sample.csv` (two underscores: `catalog_lobs__sample.csv`);
  company fixtures are `<loader>_sample.csv` (one). The same file therefore cannot serve
  both sides, and before G78 a file copied across was SILENTLY SKIPPED ("No sample for …,
  skipping") rather than rejected. Since G78 (2026-08-21) the producer chain verbs FAIL BY
  NAME on a missing fixture and `refresh-reference` has no fixture default at all
  (`--samples-dir` for fixtures, `--source <id>` for landing zones) — so a company port
  that keeps its single-underscore fixtures must either rename them or carry its own
  the subject chains' fixture names (`cli.CHAINS`; one `REFRESH_REFERENCE_CHAIN` tuple
  before the G79 split); do not "fix" the divergence by loosening the
  resolver back to a skip.
- **The six un-back-flowed company advances — ALL SIX DISPOSITIONED (J39, 2026-08-26).**
  One reproduced, five ledgered with reason + trigger; none left undecided, nothing
  touching edge meaning adopted outside a gate:
  1. **controlm_folders.sql `J` table alias — REPRODUCED** (mechanism-only, the alias
     rename H→J with a provenance comment in the file). The one advance whose whole
     content was visible from the diff shape; the standing cosmetic divergence ends.
  2. **snow-support schema pair (`hpsm_queue_key`/`sn_group_name`) + `snow-snowflake-itsm`
     stub — LEDGERED, partially superseded.** G100 (2026-08-18) already brought
     :ServiceNowGroup producer-side with the sys_user_group sourcing note; the constraint
     pair and the source stub are the ITSM LOADER's to carry. TRIGGER: the snow loader
     build after gate `snow-cmdb-ci-classes` (Q4) signs — adopting constraints for a
     loader that does not exist is dead DDL.
  3. **drydocs_remediation DPL watch-drift rule + tests — LEDGERED.** The rule's CONTENT
     has never been seen producer-side (only its existence, via the J51 DPL-* id list);
     reproducing a detector from its name manufactures semantics. TRIGGER: the
     screenshot/describe channel or the drydocs-review back-flow epic delivering the rule
     body; it then lands as an R-rule through detect.py's registry like R41-R44 did.
  4. **graph_verify Assertion refactor — LEDGERED.** graph_verify.py itself is
     company-only; the producer cannot refactor what it does not hold. TRIGGER: the
     drydocs-review back-flow epic, which reproduces the whole toolkit — the refactor
     rides in with it, never separately.
  5. **docgen deviations vs the finalized company TDD — OVERTAKEN, closed.** Two things
     ended it: the renderer converged through the L-epic fixes (the 2026-08-24
     nested-fence fix regenerated every runbook render), and J43 (2026-08-26) ruled the
     TDD renders `derived` — regenerated from the reconciled tree with the CURRENT
     renderer, so a deviation list against a frozen render is a category that no longer
     exists. Residue, if their regeneration ever shows semantic loss: that is a renderer
     BUG filed as one, not a deviation to catalog.
  6. **CONFLUENCE_BASE_URL config seam — LEDGERED.** The mechanism (base-URL as config,
     value company-side) is right, but the producer has no confluence connector — the
     doc-source-registry's cdo row says 'when the confluence connector runs' in its own
     words. A config seam with no consumer is dead config. TRIGGER: the confluence
     connector build in drydocs_docmeta/connectors/; the seam ships WITH it.
- **PAT catalog ontology — company is AHEAD and the producer has ADOPTED NOTHING (C26,
  2026-08-21; adoption = C27, gated on the COMPANY catalog gate's own sign-off).** The
  company gate page `internal/org/catalog/_catalog_gate_page.html` (dated 2026-06-25, "SME
  Gate Prompt — PAT Catalog Loader", step 1 of 3) diverges from the producer catalog
  ontology in FIVE ways. Keep company on every one; do not "reconcile" them into the
  producer shape, and do not let a port pick a side by accident:
  1. **Grain** — company models `:SubLOB` + `HAS_SUB_LOB` (LOB→SubLOB, "only CIB and AWM have
     them"; `product_lines.cypher` anchors on `parent_sub_lob_id` with a `:LOB {lob_id}`
     fallback). Producer flattens `LoB → Sub-LoB → Product Line` to `CatalogLOB → ProductLine`,
     and the flattening is INVISIBLE: a sub-LoB id in `parent_lob_id` MERGEs a phantom LOB.
  2. **Range** — company widens `HAS_PRODUCT_LINE` to `(:SubLOB|:LOB) → ProductLine`; producer
     `catalog_has_product_line` is `CatalogLOB → ProductLine` only.
  3. **Label — SETTLED, both levels, and NOT by C27.** LOB: the company's own **GATE
     REVERSAL of 2026-08-06** (their `gate-log.md:1678`, port `drydocs-port-20260806`,
     producer head `a14a8028`) retired the 2026-06-25 gate and adopted the full producer
     model — `:LOB` -> `:CatalogLOB`, `code` reinstated, TC-CAT-003 retired. Both sides now
     `MERGE (l:CatalogLOB {lob_id: ...})`. Sub-LoB: **RULED 2026-08-25 (SME, Option 1) —
     `CatalogSubLOB`**; the company relabels its active `:SubLOB` build, the producer's
     reserved label stands, the shared vocab id `catalog_has_sub_lob` is unchanged. Do NOT
     re-open either as a divergence to preserve.
  4. **Map ids — the C26 reservation named the WRONG ids and is retired.** It reserved
     `sub-lob-org-unit` + `catalog-lob-reconciles-segment` off the 2026-06-25 page; the company
     actually built `lob-has-sub-lob` + `sub-lob-has-product-line` and KEPT the producer's
     `lob-reconciles-to-segment`. Both reservations moved to `rejected` with `superseded_by`
     at the C27 ruling (2026-08-25) — a placeholder guarding a name nobody mints guards
     nothing. The producer keeps `lob-has-product-line` / `lob-reconciles-to-segment`
     (confirmed 2026-06-21); the company's two live in their own company-only fragment and
     never arrive here. **The real reservation is a rule, not a row: the producer must not
     mint `lob-has-sub-lob` or `sub-lob-has-product-line` for anything else** — the per-entry
     merge is id-keyed, so that would land as one id with two meanings.
  5. **Capture grain** — company ingests the 5-field `pat_lob_sublob_productline.csv` (164
     rows, with a Sub-LoB Name column); producer `config/taxonomy/lob-product-team.yaml`
     has no Sub-LoB column at all.
  Producer reservations (NAMES only, no meaning): vocabulary `catalog_has_sub_lob` and
  `catalog_sub_lob_has_product_line` (`planned`, 42-local-catalog.yaml), node label
  `CatalogSubLOB` (`planned`, 10-node-classifications.yaml), the two map ids above
  (`proposed`). **Two rulings the C27 gate must settle TOGETHER, never one at a time:** the
  LABEL ruling (`:LOB` vs `:CatalogLOB`) and the KEY ruling (the S3 `app_id` rename, signed
  2026-07-27, which the company page PRE-DATES) — a label decision made before the key
  decision re-opens the moment the key lands on the shapes. **Relay items (company-side
  fixes, not producer work):** (i) the page's functional-org target "Corporate" is ambiguous
  against the seeded `:BusinessSegment {code:"Corp", name:"Corporate"}` — read as a code it
  MERGEs a phantom segment; (ii) the page's `drydocs/schema/ontology.cypher` path is
  period-correct for 2026-06-25 (pre-G2 Phase-B relocate, 2026-07-10) — refresh it only if
  the prompt is revised. Gate MECHANICS match `gate_pages.py` throughout (localStorage ticks,
  no-write-until-confirmed, `{confidence, authority, aliases}` on RECONCILES_TO,
  skos:closeMatch aliases, precedence winner `lob-product-team`): content drifted, mechanism
  did not. Also absorbed here (from the 2026-08-02 inbox line): `pat_app_links` stub
  governance, `pat_product_owners`, and the `products` step-2a supplement fields — all ride
  C27's trigger.

## Track-1 acceptance (the contract)

Run as a SINGLE line (multi-line `\` continuations break in some agent shells):

```
poetry run pytest tests/unit/test_variable_classifier.py tests/unit/test_variable_resolver.py tests/unit/test_variable_staging.py tests/unit/test_command_parser.py tests/unit/test_module_boundary.py -q
```

(If `poetry` is not on PATH, use `python -m pytest <same files> -q`.) Expect
**114 passed, 3 skipped, 0 failed** (measured 2026-07-25; was 90/3 when this skill
was written — the suite grows, so treat the number as a FLOOR and re-measure on the
producer side before calling a company-side count a regression). The 3 skips are the
sample-backed tests (`test_sample_classifies_end_to_end`, `test_sample_bundle_smoke`,
`test_sample_end_to_end_counts`) — the production CSV is gitignored and never
transfers, so they skip, not fail. A `FileNotFoundError` instead of a skip means
the skip guard was lost in the port (re-apply the Canonical-here test files).
`test_module_boundary.py` is pure stdlib (no sample needed) — **5 tests** (Epic H6
added the default-deny `test_every_module_is_classified` and the entrypoint-exemption
test `test_entrypoint_is_exempt_but_still_classified`; the 2026-07-25 guard fix added
`test_declared_component_imports_are_load_bearing`), always pass; it guards the
`drydocs-core` ↔ component boundary (ADR 0002 D3). **Entrypoint rule:** `cli.py` is the
composition root and may import any component (`ENTRYPOINT_MODULES`) — a company `cli.py`
that owns the review commands passes as-is; do NOT extract a `review_cli.py` sub-app.

## Per-entry guards — run them around the merge (J7)

The PORT-MANIFEST `per-entry` / `union-append` entry_rules are executable
(`tests/unit/test_port_reconcile_guards.py`): status no-downgrade (vocabulary
`active`, map `confirmed`/`applied`, **backlog `done`** — J16), no dropped
entries, gate-log append-only. Use them to PROVE the merge respected the rules
instead of eyeballing:

```
# 1. BEFORE applying the port — snapshot the consumer copies
mkdir "$env:TEMP/reconcile-before"
cp config/gate-log.md "$env:TEMP/reconcile-before/"
# ADR 0013: the backlog is a sharded TREE — snapshot the ASSEMBLED document under the old name:
poetry run python -c "from pathlib import Path; import os; from drydocs_core.backlog_store import dump_document; (Path(os.environ['TEMP'])/'reconcile-before'/'backlog.yaml').write_text(dump_document(), encoding='utf-8')"
# J51 (optional, arms two no-drop guards): the list-shaped per-entry files — detector ids and exemption keys
poetry run python -c "import os; from pathlib import Path; from drydocs_remediation import detect; d=Path(os.environ['TEMP'])/'reconcile-before'; (d/'detect-rule-ids.txt').write_text('
'.join(detect.CONFORMANCE_RULE_IDS), encoding='utf-8')"
poetry run python -c "import os, importlib; from pathlib import Path; m=importlib.import_module('tests.unit.test_runbook_currency'); d=Path(os.environ['TEMP'])/'reconcile-before'; (d/'runbook-exemption-keys.txt').write_text('
'.join(f'{t}:{k}' for t in ('HISTORICAL_PATHS','FOREIGN_PATHS','DEFERRED_VERBS') for k in sorted(getattr(m,t,{}) or {})), encoding='utf-8')"
# S5: the two registries are fragment DIRECTORIES — snapshot the MERGED documents:
poetry run python -c "from pathlib import Path; import os; from drydocs_core import yaml_fragments as yf; d = Path(os.environ['TEMP'])/'reconcile-before'; (d/'relationship_vocabulary.yaml').write_text(yf.merged_text('drydocs_core/ontology/relationship_vocabulary'), encoding='utf-8'); (d/'taxonomy-ontology-map.yaml').write_text(yf.merged_text('config/taxonomy-ontology-map'), encoding='utf-8')"

# 2. apply the range / resolve collisions as usual

# 3. AFTER — the guards fail on any downgrade, dropped entry, or audit truncation
$env:RECONCILE_BEFORE_DIR = "$env:TEMP/reconcile-before"
poetry run pytest tests/unit/test_port_reconcile_guards.py -q

# 4. TEARDOWN — clear the variable and drop the snapshot. Do not skip this.
Remove-Item Env:RECONCILE_BEFORE_DIR
Remove-Item -Recurse -Force "$env:TEMP/reconcile-before"
```

**Step 4 is not tidiness.** The variable outliving its before-dir is a real
recorded failure: a later, unrelated session in the same shell ran the full suite
and got four reconcile-guard failures that had nothing to do with its work, and
spent the time proving that before moving on. The guard now fails with
"re-snapshot it or clear the variable" instead of a bare `FileNotFoundError`, but
the cheap fix is still to not leave it set.

With `RECONCILE_BEFORE_DIR` **unset** the live checks skip and only the
fixture-driven mechanics run — so the file is safe in every CI. **Set but
unusable** (missing dir, or a snapshot short of all four files) FAILS rather than
skips, deliberately: a set variable claims the port's safety check is armed, and
silently skipping it would report green on an unchecked merge. The pyproject
version-string rule is asserted separately in `test_port_manifest.py` (keep the
consumer's version; producer `v*` tags never cherry-pick).

## Track-2 (optional — real data, or fresh sample)

Bundled exact counts (89 passed; `normalize-variables` → inv=6, file_op=16,
file_ref=92, notif=14, app_fact=66, 86.2%) only hold with the bundled sample
present. For a fresh `psgmgr` pull:

- **Connection mode is environment-specific — check before assuming.** The
  producer's `OracleAdapter` is thin-only (no `init_oracle_client`), but the
  COMPANY adapter is Kerberos-aware and goes THICK when `ORACLE_KERBEROS=True`
  (calls `_init_thick_client` + `connect(externalauth=True)` against a TNS
  alias). In that config a plain `--use-oracle` run uses OCI and WILL hit the
  real Kerberos SPN errors (ORA-12514 / ORA-12638) — that is a DBA / SPN /
  tnsnames issue, NOT a code toggle. Thin mode is only an option if you can set
  `ORACLE_KERBEROS=False` AND supply a real `host:port/service` DSN (a bare TNS
  alias resolves only via tnsnames and won't work thin).
- Scope binds are **connection-mode agnostic** (NULL-tolerant SQL predicates —
  they work the same under thick/Kerberos once the SQL is ported): `--folder`
  (SCHED_TABLE LIKE), `--run-as` (tenant FID = `OWNER`), `--developer-sid`
  (`AUTHOR`/`CREATION_USER`/`CHANGE_USERID`, or folder `LAST_UPDATED_USER`),
  `--row-cap`. NULL = full population. If your `normalize-variables` lacks these
  flags or the SQL still pulls all ~1.1M rows, you have NOT yet ported the scope
  commits — re-port `controlm_variables.sql` wholesale and merge the cli.py
  scope options (see the collision ledger).
- The `psgmgr.CM_DEF_SETVAR_VW` source-view name is **confirmed** (2026-07-10,
  against live `psgmgr` — a view with its own `IS_CURRENT_VERSION` /
  `VERSION_SERIAL`, so the variable extracts now filter `V.IS_CURRENT_VERSION = 'Y'` —
  literal corrected `'1'`→`'Y'` 2026-07-15, D4, per the finalized company ingestion TDD).
  If a future port surfaces a different object, re-confirm and report.
- Judge a fresh pull on *runs clean / no UNKNOWN invocation leakage / plausible
  coverage*, **not** the bundled counts.

## Port report (write this, do not push)

```
Port Report: cewilson/main -> <company>/main
- What applied (clean cherry-picks): <count + the controlm/canonical-here paths>
- What conflicted + resolution: <per collision ledger>
- What was skipped: <commits + why>
- Track-1 result: <N passed, 3 skipped, 0 failed>
- Backlog union (J42): <paste the scripts/port_backlog_union.py block — producer/consumer counts, missing ids, accepted differences, PASS|FAIL>
- Track-2 status: <ran/blocked + CM_DEF_SETVAR_VW finding>
- State: branch ahead of <company>/main by N; NOT pushed; backup tag pre-cewilson-port
- New divergences observed: <add to the ledger if any>
```
