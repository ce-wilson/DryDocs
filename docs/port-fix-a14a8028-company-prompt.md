# Company-side prompt — fix the 14 remaining owed failures (PORT-REPORT-a14a8028)

> Producer-drafted 2026-08-06 for the company-side assistant. Paste or read whole.
> Producer facts in this prompt were verified against `cewilson/main` at `a14a8028`.

You are on company `<org>/DryDocs`, branch `drydocs-port-20260806` (3 commits;
revert tag `pre-cewilson-port-20260806` at `5e5ae723` — never rebase it away; the
branch is NOT merged and stays unmerged until SME review). Your durable note is
`/memories/repo/port-a14a8028-owed-failures.md` — read it first, and mark every item
FIXED-with-commit or explicitly DEFERRED as you go.

State: the 16 owed failures collapsed to 4 root causes; the two quick wins landed at
`e21c9f2f` (B3 manifest `default_ok` re-add; ui_components fixed by REVERSAL — the
port had over-adopted the web half of held K18 work). **Suite: 14 failed.**

## Rules in force (non-negotiable)

1. **Fix data/code, never test-edit a divergence** without an investigation note
   (SME condition 2). The producer guards are the contract.
2. **Held work stays held.** K7–K15 folder-attribution / app-code reshape is a
   Tier-B hold. Yesterday's ui_components catch was a silent over-adoption of held
   work — the failure mode to watch for in every fix below. If a fix would land held
   work, STOP and make it a deliberate, logged Tier-B adoption decision.
3. **Two-tier gate doctrine:** producer sign-off ≠ company sign-off. Gate adoptions
   are union-append into YOUR gate-log with your own ratification entry.
4. **Venue every claim (J18):** name branch/db/machine in every "verified" sentence.
5. One commit per work package; quote the suite delta in each report-back message.
6. **A green suite is not a performed migration.** If a live-graph leg is deferred,
   say so in the durable note in those words.

## Work package 1 — Group A data-strictness (4 failures; data fixes, no code)

1. `test_no_bom_on_loader_read_formats` — strip the UTF-8 BOM from the untracked
   `internal/application/adhoc-software-registry-update-by-seal.csv`. Do it in
   Python (`open('rb')` / slice / rewrite) — do NOT pipe file content through
   PowerShell 5.1, which re-adds a BOM (producer step 74 lesson).
2. `test_directory_holds_exactly_one_all_files_snapshot` — prune the 30 depgraph
   snapshots to newest-only (producer U12 retention; `snapshot.ps1` enforces it
   going forward, this is the one-time cleanup).
3. `test_powershell_keeps_non_ascii_out_of_quoted_strings` — ASCII-ify the
   em-dashes/arrows in `internal-local/.../run-kerberos-debug.ps1` and
   `backlogscan.ps1`.
4. `test_committed_newest_snapshot_is_accepted_and_clean` — after the prune,
   regenerate the snapshot; "clean" means `adapter.unmapped_extensions == {}`
   (pinned by producer `test_code_snapshot_loader.py`). If extensions remain
   unmapped, either extend the extension map in `drydocs/loaders/code_snapshot.py`
   (adapter fix) or rule the offending files out of scope — record which, and why.

Acceptance: those 4 green; suite 14 → 10.

## Work package 2 — the K8 folder-grain reshape (6 failures; the focused one)

Root cause (confirmed producer-side): your EXTENDED `manual_mappings` writer — kept
in the clobber-audit re-merge — still writes job-grain
`{ControlMJob, WAS_ASSOCIATED_WITH, seal_app_ref, BusinessApplication}`. Producer
fixtures and store use folder-grain
`ControlMFolder -[BELONGS_TO_APPLICATION {role: seal_app_ref}]->`. Producer
`drydocs_core/manual_mappings.py` is the reference implementation — **diff your
extended copy against it rather than re-deriving the contract** (it also carries the
exact "unsupported shape" error wording your tests expect).

This is producer ledger step 63's grain-breaking caution firing, and step 96
(K18 `tier`→`row_kind`, FORMAT-BREAKING) is in this same port range — **they are one
T23-family migration. Plan them as a unit:**

a. Reshape the writer to folder-grain, preserving your company extensions.
b. K18 rider in the same unit: `tier`→`row_kind` on the CSV header, store column,
   and folder-edge property; tier-authored rows re-author; platform code-level rows
   now REQUIRE the platform's own `app_id` + rationale.
c. Your job-grain tier-5 CSVs: convert key cells per the composite-key serialization
   standard (producer step 62 caution) in the SAME commit that takes the parse flip.
d. LIVE-graph legs are T23 territory and sequence with the S3 re-key: DROP
   `port_unique` FIRST; backfill `app_id = seal_id` on pre-cutover nodes (check for
   partial doubling from the 2026-08-04 crash first); the S10 guard —
   now covering all five of your `:BusinessApplication` MERGE sites including
   `PatAppLinksLoader` — will refuse until nulls are cleared. Do not run loaders
   against the live graph mid-package.
e. The held folder-attribution stream stays held unless you deliberately decide to
   land it here. If you do, log it as a Tier-B adoption. Do not let it slide in as a
   side effect (rule 2).

Acceptance: `test_mapping_store` ×5 + `test_mapping_api` green on fixtures;
suite 10 → 4. The live-graph migration may be its own later session — if deferred,
the durable note says "deferred", never silence.

## Work package 3 — config/data divergence (4 failures; investigate per item)

1. `test_real_registry_gate_state` — your `source-registry.yaml` has
   `controlm@[db].psgmgr.cm_hosts` unconfirmed. Producer is `confirmed: true` via
   gate `controlm-hosts-topology` (2026-07-09), and the producer registry note says
   this confirmation class TRANSFERS per Q6. Either flip your flag citing that gate
   (union-append your gate-log) or run your own ratification — record the choice.
2. `test_authoring_doc_namespace_table` — rule 2's namespace table has 5 rows,
   the guard wants ≥6. Diff your doc against the producer's and add the missing row
   like-for-like; do not invent one.
3. `test_fr_cmi_007_test_cell_splits` — a `;`-split yields 1 citation where 2 are
   expected: fix the citation cell in the doc to carry both.
4. `test_feedback_stray_files` — `control-m.md` in `docs/design/feedback/` doesn't
   match the `<doc>-rev<N>.yaml` convention: rename to the convention, relocate it,
   or add an exemption WITH a note naming which and why.

Acceptance: 4 green; suite 4 → 0.

## Close-out

- Full suite green — expect ~1870 passed / 0 failed / 31 skipped; quote the real
  numbers with venue.
- Durable note fully reconciled: every one of the 14 FIXED-with-commit or DEFERRED
  in so many words (the live-graph T23 legs are the expected deferrals).
- Report back in the established pattern: per-package commits, decisions taken
  (cm_hosts route, unmapped-extensions ruling, whether folder-attribution stayed
  held), and anything the producer should ledger — producer tracker rows T22/T23
  are producer beliefs; your report is what corrects them.
- Then stop. The `--no-ff` merge of `drydocs-port-20260806` onto company `main` is
  the SME's decision, not yours.
