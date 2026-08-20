# Producer review — company port `caa04060..7c18ff4b` (branch `drydocs-port-20260820`)

> Classification: Internal-Public (mechanism only; no SIDs, handles, or data values).
> Reviewed 2026-08-20 (desktop) from the company apply session's own close-out
> summary and its `PORT-REPORT-caa0406.md` send-back, transcribed here. Facts marked
> **verified** were re-derived on the producer repo; everything else is the company
> session's claim, recorded as such.

## What the company session reports

| Fact | Value | Producer check |
|---|---|---|
| Range | `caa04060..7c18ff4b` — 247 commits / 316 paths | **verified**: `git rev-list --count` = 247, `git diff --name-only` = 316 |
| Branch / backup | `drydocs-port-20260820`; tag `pre-cewilson-port-20260820` | company-side |
| Commits | reconcile (258 files) + `PORT-REPORT-7c18ff4b.md` — **not pushed, not merged** | company-side |
| Acceptance | 2404 passed / 67 skipped / 4 carry-over failures, all working-tree or environment (offline venv ×2, autocrlf CR on snapshot JSON, untracked HR CSV BOM) — none in the commit, all green on a clean CI checkout | plausible; the four named causes are known classes |
| Earlier survey | 11 failed → 10 after a stale `test_enforcement_matrix` regen → 4 after the company fixed a pre-existing broken `control-m-service-now-config.py` (6 AST-crash tests) | company-side |
| `caa0406` send-back | already complete in `PORT-REPORT-caa0406.md` (the prior port, `ae21ee4..port-base-20260811`, 63 commits / 106 paths, steps 124–134; 2141 / 28 / 1, the 1 = pre-existing WP1.4/T18 snapshot block) | consistent with the 2026-08-11 ledger |

**The five directives, as executed:** (1) gate sign-offs deferred to post-merge — no
`gate-log.md` edits in the port commit, so the board stays consistent; (2) the FID
atomic pair recorded as an **authorization in the PORT-REPORT**, formal gate-log
`SIGNED-OFF` entries deferred to post-merge; (3) board regen deferred to after the PR;
(4) PORT-REPORT written and committed; (5) confirmed.

**Company post-merge follow-ups (their list):** gate-log SIGNED-OFF entries (FID pair +
G102 / G22 / T19 / N12 / N13 / §E2 / K7–K15 / corporate-backbone); regenerate the board;
`git stash pop` the three stashed HR files; retire the stale `port-prompt.md`; SME call on
excluding the standalone RAIIDER scripts from ruff N999 or renaming them.

## Findings

### F1 — The FID "atomic pair" is not yet atomic, and is not yet in the audit surface
The handoff's instruction was *ratify the FID sign-off + the §G3 amendment as an atomic
pair after the suite is green*. What landed is an authorization sentence in the
PORT-REPORT, with both gate-log entries deferred. That is a reasonable sequencing choice
(directive 1 keeps the board consistent through the merge), but two things must hold at
the follow-up or the ratification is not what was asked for:
- **both entries land in ONE gate-log commit** — a sign-off without its §G3 amendment is
  the half-state the word "atomic" exists to forbid;
- `config/gate-log.md` is the audit surface (`union-append`; dropping an entry is an audit
  violation). Until the entries exist there, `render_gates.py` / `gates.json` on the
  company side show the FID gate as **unratified** — the PORT-REPORT sentence is not
  machine-readable. **Action (company): follow-up 1 is not optional housekeeping; it is
  the ratification.**

### F2 — Company-local fixes are bundled into the reconcile commit
The reconcile commit (258 files) also carries the `control-m-service-now-config.py` syntax
fix and the Idea-109 `repo_root` sweep over nine company modules. Neither is
port-introduced. **Action (company): the PORT-REPORT must list them as
not-port-introduced**, or the next reconcile's divergence census reads nine company
modules as producer drift. The `cli.py` F821 the sweep exposed is **company-only —
verified: `ruff --select F821 drydocs/cli.py` is clean on the producer**; no back-flow.

### F3 — Five named divergences have no PORT-MANIFEST row (the Idea-142 obligation)
The `caa0406` report names canonical-producer paths the company legitimately diverges on.
**Verified on the producer manifest:** `description_tokens.py`, `detect.py`,
`test_runbook_currency.py`, `email-dl-contact-point.yaml`, and `ui-components.yaml` have
**no row** (`resource_pool.py` already has its G76 mechanism-here/vocabulary-yours pin).
Per Idea-142 (High), each gets a per-entry/union row with an `entry_rule`, or a recorded
reason wholesale stays right. Producer-side action, groomable now:

| Path | Company state (their report) | Proposed disposition |
|---|---|---|
| `drydocs_core/orchestration/controlm/description_tokens.py` | union-merged: producer C30 conformance model + company live-load parser coexist in one module | **back-flow candidate first**: split the two models into separate modules producer-side, then the row is clean-add + canonical-company |
| `drydocs_remediation/detect.py` (+ `__init__.py`) | union: producer R30–R40 + company `detect_dpl_findings` / `dpl_review` | per-entry by detector id; shared `Finding` shape is the contract |
| `tests/unit/test_runbook_currency.py` | adapted: company `HISTORICAL_PATHS` (T19) + `DEFERRED_VERBS` (T22), `FOREIGN_PATHS` emptied | per-entry on the exemption lists; retire when T19/T22 land (their report says the same) |
| `config/gate-prompts/email-dl-contact-point.yaml` | canonical-company, but producer Section G / G4 re-posed per the SME's 2026-08-11 ruling | evaluate, with the note that Section G is SME intent crossing INTO a company-canonical file |
| `config/taxonomy/ui-components.yaml` | producer-minus-one (68/29) under the K7–K15 Tier-B hold | per-entry; the hold is the entry_rule |

### F4 — A status-direction ambiguity in the backlog union
The `caa0406` report: *12 shared ids with status diff KEPT at company status (done never
crosses)*. The manifest entry_rule says keep the one **further along**. If producer-`done`
items were kept at company-`todo`, that is the opposite rule — and it may be the *right*
rule for build items, because `done` is a per-repo fact (built here ≠ wired there). The
two rules cannot both stand in one entry_rule. **Question for the SME / Y2:** is `status`
per-repo for `type: build` items? ADR 0013 Clause 4 inherits "never regress" for the
per-file rule and should carry the answer.

### F5 — Handoff items not visible in the summary
Not confirmed by anything I can see: that `PORT-REPORT-7c18ff4b.md` carries *every kept
divergence in the census* and the four fields `caa0406` lacked (the session says the
send-back is already in `PORT-REPORT-caa0406.md`, which is consistent); and the
`drydocs-scrape` connector back-flow ask. **Action (producer, at the report):** read the
report itself, not the chat summary, for the census; raise the scrape back-flow ask.

## Verdict
**Mergeable on the company's terms** — the committed tree is green on CI, the reversibility
tag exists, and the deferrals are recorded. The `--no-ff` merge is the SME's call, and
**F1 and F2 are conditions on the follow-up, not on the merge.** Producer owes F3 (five
manifest rows / reasons — groom from Idea-142) and F5 (read the report; raise the scrape
back-flow), and F4 is a question to rule, not a defect.
