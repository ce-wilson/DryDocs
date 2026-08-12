# Targeted test port — the remediation XML I/O surface (partial, file-state)

**Date drafted:** 2026-08-12 (producer). **Owner of every phase below: the company
session.** Producer facts are stated as record only; no phase crosses the repo boundary.

## What this is, and is not

This is a **partial, test-only port** of the remediation XML surface — `xml_io` (lossless
Control-M XML read, byte-identical round-trip, EditScript structural edits), the
reference-sweep rename, the three-valued `prove_equivalence` verdict, and the
DATA_CENTER folder-identity fix — so the company can test XML fix emission against real
Control-M exports now, ahead of the next full range port.

It is **not a ledger port**. It does not move "Last completed port" on either side, does
not roll the step ledger, and uses no base tag.

**Dispositions under PORT-MANIFEST first-match-wins — three groups, not one** (corrected
2026-08-12; the first draft over-claimed canonical-producer for everything):

- **canonical-producer** (blind wholesale take is legitimate and the next full port
  converges over it): `drydocs_core/orchestration/controlm/xml_vocab.py` (the
  `drydocs_core/orchestration/**` row) and all of `drydocs_remediation/**`.
- **evaluate** (the manifest FORBIDS a blind path checkout — diff first):
  `drydocs_core/data_root.py` (falls to the `drydocs_core/**` default),
  `drydocs_lineage/extractors/controlm_xml.py` (`drydocs_lineage/**` — "evaluate, do not
  checkout"), and the six pre-existing test files
  (`test_remediation_conformance/xml_bridge/scaffold/handoff`,
  `test_lineage_controlm_xml`, `test_data_root`) under the `tests/**` default.
- **clean-add** (absent on the consumer, applies untouched): the new test files —
  `fixtures_controlm_xml.py`, the three `test_xml_io_*` files,
  `test_remediation_changes/changedoc/equivalence_verdict`.

For the evaluate group: **diff each path (company copy vs `3b9038b1`) before taking
anything.** Take wholesale only where the diff is empty or the producer is a clean
superset of the company copy; any real divergence (company-local expectations, values,
or edits) is a hand-merge that keeps the company-side content and takes the producer
logic. The "next full port converges" argument covers only the canonical-producer group
— the full port evaluates these same paths too; it never blindly takes producer.

## Producer record (verification already performed producer-side)

- **Source content SHA:** `3b9038b1` on producer `main`
  (`fix(remediation): carry DATA_CENTER through the model, locator, and anchors`).
- **Commits whose content rides in the taken paths** (for the record; you apply file
  states, not these commits):
  - The `feat/remediation-xml-io` epic, in full: `ad081e6a` (xml_vocab re-home to core),
    `0a4b0a30` (xml_io reader + round-trip), `e533fc24` (EditScript + self-check +
    structural edits), `3ebb66d3` (defect A′ — rename sweep), `d40c9cb9` (defect B′ —
    equivalence verdict), `be6b8f50` (I/O zones + lxml validator group), `bf37f497`
    (changes.py — approved change-sets, graph anchors), merge `6bf66fe5`, and the
    post-merge fix `3b9038b1`.
  - Partial content from: `339572ee` (**`changedoc.py` only** — its gate prompt, web
    fix-diff surface, and backlog/board edits are excluded), `e1d9ac0c` (C30/G67:
    `formats.py`, `xml_bridge.py`, `detect.py` R30–R40, extractor), `2d6cbb4c` (G69:
    R41–R44, `overview_readme.md`), `5613ea0a` (C29: extractor), `18d4eb51` (two swept
    test lines). Only their hunks inside the taken paths ride; their other surfaces
    (captures, gates, backlog, renders) wait for the full port.
- **Deliberately excluded:** `34a6dc05` (the RATIFIED fix-tracking emitter). It depends
  on the vocabulary domain-rename chain (`496aa268`, `35a1d2b5`, gate log `26d7c395`)
  and rides the next full port. Consequence: change-sets emitted from this state carry
  `gate: GATE-BOUND` — correct for a test; do not treat those artifacts as loadable.
- **Producer certification (J18 venue: desktop, scratch git worktree — no graph
  involved):** base `ae21ee4` + the paths below at `3b9038b1` was assembled and run as a
  mixture. Full unit suite: **1947 passed / 9 skipped / 0 failed** (all skips
  environment-absence, pre-existing). Targeted set (the command in step 5): **164
  passed**. Port-manifest fall-through guards green — every taken path is covered by
  existing rows.

## Preconditions (verify, do not assume)

1. Company `main` carries the `ae21ee4` port (port commit `12420373`, merged 2026-08-10,
   branch `drydocs-port-20260810` deleted). `git log --oneline | head` should show that
   merge in recent history. If it is absent, STOP — this doc's base assumption fails.
2. Clean working tree; `git branch --show-current` before every commit.

## Apply

1. Branch: `git checkout -b drydocs-port-xmltest-20260812`.
2. Fetch the producer remote fresh (never a cached ref), confirm `3b9038b1` is on its
   `main`. **First, the evaluate group:** diff the eight evaluate paths (listed above)
   against `3b9038b1`; where identical or producer-clean-superset, include them in the
   checkout below; where genuinely diverged, hand-merge per the manifest instead of
   checking out. **Then** take the file states (drop any path you hand-merged):

   ```
   git checkout 3b9038b1 -- ^
     drydocs_core/orchestration/controlm/xml_vocab.py ^
     drydocs_core/data_root.py ^
     drydocs_lineage/extractors/controlm_xml.py ^
     drydocs_remediation/ ^
     tests/unit/fixtures_controlm_xml.py ^
     tests/unit/test_xml_io_roundtrip.py ^
     tests/unit/test_xml_io_edits.py ^
     tests/unit/test_xml_io_rename_sweep.py ^
     tests/unit/test_remediation_changes.py ^
     tests/unit/test_remediation_changedoc.py ^
     tests/unit/test_remediation_equivalence_verdict.py ^
     tests/unit/test_remediation_conformance.py ^
     tests/unit/test_remediation_xml_bridge.py ^
     tests/unit/test_remediation_scaffold.py ^
     tests/unit/test_remediation_handoff.py ^
     tests/unit/test_lineage_controlm_xml.py ^
     tests/unit/test_data_root.py
   ```

   (`drydocs_remediation/` at `3b9038b1` is 13 files: `__init__.py`, `changedoc.py`,
   `changes.py`, `corroborate.py`, `detect.py`, `equivalence.py`, `formats.py`,
   `jira.py`, `transform.py`, `xml_bridge.py`, `xml_io.py`, `module-requirements.md`,
   `overview_readme.md`.)

3. **`pyproject.toml` is per-entry (union), NOT a wholesale take, and `poetry.lock` is
   never taken** (manifest: re-lock after the merge). Hand-add this block to the company
   `pyproject.toml`, keeping the company version string and everything else untouched:

   ```toml
   # drydocs-remediation XML VALIDATION (optional, mirroring the api group):
   # lxml validates emitted <folder>.updated.xml against the acquired .dtd/.xsd —
   # it is the VALIDATOR, never the emitter. The minimal-diff emitter is xml_io's
   # stdlib byte-splicer, guarded by test_xml_io_imports_are_stdlib_core_and_formats_only
   # (lxml collapses multi-line attribute wrapping exactly as ElementTree does, so
   # "simplifying" the splicer into it would break the §XML contract).
   # `poetry install --with remediation`. See drydocs_remediation/module-requirements.md.
   [tool.poetry.group.remediation]
   optional = true

   [tool.poetry.group.remediation.dependencies]
   lxml = ">=5.3"
   ```

4. `poetry lock` then `poetry install --with remediation`.
5. Acceptance, targeted first:

   ```
   poetry run pytest -q tests/unit/test_xml_io_roundtrip.py tests/unit/test_xml_io_edits.py ^
     tests/unit/test_xml_io_rename_sweep.py tests/unit/test_remediation_*.py ^
     tests/unit/test_lineage_controlm_xml.py tests/unit/test_data_root.py
   ```

   Expected: **164 passed** (producer-verified on the identical mixture). That number is
   exact only if every evaluate path came back identical/superset and was taken at
   producer state; a hand-merged test file may legitimately shift its count — record the
   delta and the reason. Then the full suite: **no new failures against your own
   pre-port baseline** (the WP1.4/T19 infra-block, if still present, is pre-existing and
   not port-introduced).
6. Commit on the branch with the standard port-commit shape, citing this doc and source
   SHA `3b9038b1`; `--no-ff` merge per your normal review, or hold on the branch if the
   test is exploratory.

## The actual internal test (why this port exists)

Against a real Control-M XML export (`ctm` / ctmfw export of one folder):

1. **Round-trip:** `xml_io.read_document` → serialize → assert byte-identical to the
   input. This is the module's core contract — if a real export breaks it, that is the
   finding; capture the folder's shape (not values) as the defect report.
2. **Edit + minimal diff:** apply an `EditScript` (e.g. a variable value change or a
   rename with the reference sweep) and confirm the diff touches only the intended
   lines — the splicer is position-faithful by design.
3. **Equivalence:** `prove_equivalence` on before/after — expect the three-valued
   verdict, with command lines resolved and diffed.
4. **Validation:** with the acquired `.dtd`/`.xsd` in place, the lxml validator group
   checks the emitted `<folder>.updated.xml`. lxml validates; it never emits.
5. **DATA_CENTER identity:** use a folder that exists in two data centers if available —
   the `3b9038b1` fix carries DATA_CENTER through the model, locator, and anchors, and
   that is the half of folder identity a single-DC test never exercises.

## Recording and supersession

- Note this partial port in your tracker (one line: "test port of the XML surface at
  producer `3b9038b1`, doc `port-xml-test-company-prompt.md`") so the next reconcile is
  not surprised that these paths are ahead of the last ported range.
- The next full range port includes all of the commits above; the wholesale
  `canonical-producer` take converges these files to the newer SHA with no special
  handling. The pyproject block will collide as an already-present union entry — that is
  the expected per-entry outcome, not a conflict.
