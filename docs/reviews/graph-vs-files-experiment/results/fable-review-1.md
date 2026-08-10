# Fable Review 1 — Blind review of groom plans ALPHA and BETA (Ideas 96–103)

**Reviewer:** Fable (blind — provenance of each plan not disclosed; scored as artifacts)
**Date:** 2026-08-10
**Verification venue:** desktop working tree at `C:\coding\projects\DryDocs`, current `main`
(backlog.yaml `updated: 2026-08-09`); collision checks also replayed against commit
`bd051ab` (the snapshot BETA claims).

---

## Scores

| Dimension | ALPHA | BETA |
|---|---|---|
| Accuracy | **3** — every named file exists and its grep line numbers replay exactly (C25 at backlog.yaml:14050, K17 at :2479), but 5 of its 6 drafted ids (J18, J19, J20, J21, U9) collide with existing items and its "next free id" table is fabricated (claims highest J = J17 / U = U8 / C = C19; actual J41 / U19 / C28). | **6** — files, epics, phases, and cross-item claims (J41 = preflight machinery, J26 = substring-guard sweep, K21 = ServiceNow/TOM session) all verify, but one drafted id (U19) collides with an existing item that was already present at its own claimed snapshot, and its U19 acceptance names a nonexistent package root (`drydocs_load`) while dropping a real one (`deepdoc`). |
| Completeness | **7** — all eight ideas dispositioned with full field blocks (id/epic/title/type/module/phase/agent/model/priority/status/depends_on/inputs/acceptance/notes), but the executive summary contradicts its own table (lists 99 as a promote, omits 97 and 100; "IDs drafted: J18, D11, J19" vs six actually drafted), U9's `depends_on: [U8]` points at the wrong item (justification says U18), and Ideas 99/103 are left as unresolved either/or dispositions. | **7** — all eight dispositioned decisively (promote/merge/park each committed to, with the assumption stated when a user call is pending), depends_on all real and `done` (J41, U18, C25), but J45 never gets a full field block (no yaml `inputs:`/`acceptance:` — only prose under Idea-103), and its Idea-103 section header says "PARKED" while the summary table says "Promote J45". |
| Sizing quality | **6** — grounded in named files with line estimates that spot-check well (claims software_registry.py = 87 lines; actual 86), but it sizes Idea-96 as S "~200 lines in test file" while its own acceptance (and the idea text) says the check is a port-time check, not a unit test — and it never found the existing `port_preflight.py` machinery, which changes both home and size. | **7** — the Idea-96 M call is anchored on the real, existing preflight pair (`drydocs/port_preflight.py` + `scripts/port_preflight.py` + `tests/unit/test_port_preflight.py`, all verified present), and touch-point counts per item are file-named; the weakness is that with only 3 files read the sizes rest on graph metadata rather than read code (the wrong package-root list in U19 shows what that costs). |
| Convention fidelity | **3** — two of its three epic names do not exist in backlog.yaml (`ports-and-imports`, `config-driven-loaders`; real values are `release-infrastructure`, `config-loaders`), and 5/6 ids are taken; agent/model/phase/module values are valid and acceptance sentences are testable, but ids and epics are the load-bearing conventions and both are broken. | **8** — every epic is real and correctly matched to its series (J → release-infrastructure, exactly what real J18/J41 carry; U → self-documentation; C → ontology-mapping, matching C25 itself), phases 8/16/2 are real plan phases, modules valid, acceptance sentences testable; blemishes are the U19 collision and skipping J42 (highest existing J is J41). |

---

## Spot-checks (six, with evidence)

### ALPHA

1. **CONFIRMED (exactly): "Grep `- id: C25` → found at line 14050; `- id: K17` → line 2479."**
   Replayed: `grep -n "^  - id: C25$" docs/restructure/backlog.yaml` → 14050;
   `- id: K17` → 2479. Both line numbers match to the digit — strong evidence ALPHA
   really navigated the live file.

2. **CONFIRMED: `tests/unit/test_port_reconcile_guards.py` exists and is the manifest's guard.**
   File present; `PORT-MANIFEST.yaml` header (lines ~33–35) names both
   `test_port_manifest.py` (well-formedness) and `test_port_reconcile_guards.py`
   (entry_rules as code, J16 fall-through guard) — matching ALPHA's routing of the
   Idea-96/100 checks. ALPHA's citation of the disposition vocabulary at "lines 20–30"
   and the "derived, regenerate" comment "line 85" also replay (found at ~19–31 and ~83–84).

3. **REFUTED (hard): the drafted-id table.** ALPHA's series table says highest J = J17,
   highest U = U8, highest C = C19, and proposes J18/J19/J20/J21/U9 as free. Actual
   backlog.yaml contains `- id: J18` (line 11602, done — the live-verification-venue
   convention item), J19 (11624), J20 (11955), J21 (12016), U9 (13354), with the J series
   running to J41 and U to U19. Five of six drafted ids collide; only D11 is genuinely free
   (D series ends at D10). Epic check: real J items carry `epic: release-infrastructure`,
   not ALPHA's invented `ports-and-imports`; the loaders epic is `config-loaders`, not
   `config-driven-loaders`. (Minor additional miss: ALPHA cites "the union rule in prose,
   line 178–181" of backlog.yaml — backlog.yaml:178 is item A2; the union rule lives in
   PORT-MANIFEST.yaml lines ~156–165. And its "14 files" count for
   `drydocs_core/ontology/relationship_vocabulary/*.yaml` is actually 13.)

### BETA

4. **CONFIRMED: the preflight machinery BETA anchors Idea-96 on exists.**
   `drydocs/port_preflight.py`, `scripts/port_preflight.py`, and
   `tests/unit/test_port_preflight.py` are all present in the tree, and J41
   (`epic: release-infrastructure`, `status: done`, title "The port has a mandatory
   CLOSING sequence and no OPENING one...") is a real, done item — so `depends_on: [J41]`
   is real and satisfied. This is the correct home the idea text implies ("not a unit
   test — the producer tree cannot see the consumer's"), and ALPHA missed it.

5. **CONFIRMED: cross-item claims.** J26's real title is "Guards that read committed text
   with a bare substring match — sweep..." (BETA: "Guard text-match sweep" — accurate);
   K21 is real (`epic: seal-attribution`, ServiceNow-replica/TOM mining), matching
   Idea-102's own text ("K21 found `u_seal_deployment_id`..."), so routing Idea-102 as
   K21 gate riders is grounded. `config/gate-prompts/software-version-context.yaml` and
   `.claude/skills/reconcile-port/SKILL.md` both exist (the former is literally in C25's
   `inputs:` list).

6. **REFUTED (two defects in one drafted item): U19.** (a) Collision: `- id: U19` already
   exists (backlog.yaml line 15487, "Depgraph scanner resolves no imports rooted off a
   directory that is its own sys.path root...", epic self-documentation) — and it already
   existed at BETA's own claimed snapshot commit `bd051ab`
   (`git show bd051ab:docs/restructure/backlog.yaml` contains it), so this is not
   snapshot staleness. (b) The acceptance names eight roots including `drydocs_load` —
   which is a backlog `module:` value, not a Python package — and omits the real
   `drydocs_deepdoc`/`deepdoc` root. Actual pyproject.toml packages: drydocs,
   drydocs_core, drydocs_remediation, drydocs_lineage, drydocs_deepdoc, drydocs_docmeta,
   drydocs_api (+ tests as the non-package scan root). ALPHA's root list for the same
   item, by contrast, matches the idea text exactly.

---

## Validity

**ALPHA: VALID.** Its METRICS block shows only Glob (11), Grep (4), Read (11), and one
`Bash: wc -l backlog.yaml`, with "No graph/Neo4j queries attempted" stated. This is
consistent with rule set 1 (files-only), which its narrative claims. The single `wc -l`
is technically outside the Glob/Grep/Read tool list, but it is disclosed, is a line count
of a file the rules allowed it to Read in full, and discovers no code context a permitted
Read would not — a borderline deviation, not a rule-set violation that flips validity.

**BETA: VALID.** Its METRICS block shows Neo4j query scripts plus Reads of exactly 3 files
(IDEAS.md, backlog.yaml sections), no Glob/Grep/directory sweeps — consistent with rule
set 2 (graph-only discovery + targeted Read), which its narrative claims. It also
honestly discloses a graph limitation (test_markdown_fences.py absent from its CodeModule
scan) rather than papering over it.

---

## Recommendation

Hand **BETA** to the SME. The decisive test for a groom plan is whether its drafted items
can be pasted into backlog.yaml and survive review, and there BETA is one `s/U19/U20/`
(plus a two-word package-root fix) from clean, while ALPHA needs five of six ids
reallocated and two epics renamed before any item is usable — J18/J19/J20/J21/U9 are all
taken and `ports-and-imports`/`config-driven-loaders` don't exist, which means every
ALPHA draft fails the very schema guard (`tests/unit/test_backlog.py` id/epic hygiene)
the backlog runs on. That verdict comes with a real caveat worth recording for the
experiment: ALPHA's file-level grounding is the stronger of the two — its grep line
numbers and line counts replay almost to the digit, and its U9 root list is correct where
BETA's U19 list is wrong — so the ideal plan is BETA's id/epic/dependency skeleton with
ALPHA-grade file verification inside each item. But between the two as submitted, BETA's
errors are cheap to fix and locally contained; ALPHA's are structural, contradict its own
demonstrated ability to grep the live file, and would have collided with the existing
J18–J21 block the moment a groom run tried to commit.
