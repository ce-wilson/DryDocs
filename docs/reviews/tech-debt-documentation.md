# Tech-debt review — documentation (repo-wide)

**Date:** 2026-07-11
**Classification:** Internal-Public (doc hygiene; no confidential identifiers)
**Scope:** documentation debt only — missing runbooks, outdated READMEs/skills/plans, stale
paths after the Phase B relocate (2026-07-10), tribal knowledge. Per the /tech-debt skill's
category table; scored `(Impact + Risk) × (6 − Effort)`.
**House rules applied:** rendered `.html`/`.print.html`/`board.html` are deterministic
outputs, not duplicated-doc debt; `internal/` exclusions are the publish boundary working as
designed; gate-bound `status: planned` entries are deliberate, not staleness.
**Tracking:** findings dedupe against existing backlog items (J2, J4, L8, O1). Trivial
unambiguous fixes were EXECUTED with this review (the F1–F4-style pre-groom precedent from
the taxonomy-ontology-map review); everything else rides an existing item or a merge.

## Verdict

The documentation estate is in **good shape structurally**: all 12 point-in-time review/plan
docs in `docs/reviews/` carry proper "STATUS: Superseded — kept for historical reference"
banners (so their pre-relocate paths are correct history, not drift); `docs/history/` is
explicit; `02-backlog.md` declares yaml authority; the living process docs
(`docs/restructure/0*.md`, `RELATIONSHIP_GUIDE.md`) came through the Phase B re-path clean.
The debt that remains is **currency, not structure** — two already-itemized stale surfaces
(J2, J4), one feature-currency gap on the README, and a handful of loose artifacts.

## Findings (priority order)

| # | Finding | Impact | Risk | Effort | Score | Disposition |
|---|---------|--------|------|--------|-------|-------------|
| D1 | `run-drydocs/SKILL.md` materially stale: "159 pass, 4 skipped" (×2; actual 566/3), "PyYAML not installed" gotcha (×2; PyYAML is installed — only sample-CSV skips remain), Aura network gotcha (Aura dropped 2026-07-06 — target is the local Docker EE container), `apply-m3-supplement` (renamed `apply-ontology-supplement`). An agent following the skill mis-validates its runs. | 3 | 3 | 1 | 30 | **Tracked: J4** (ready; verified still accurate today) |
| D2 | Tribal knowledge uncommitted: `internal/helpmeloginlocalneo4j.md` (local Neo4j Docker port mapping 7476/7689, login troubleshooting) existed only as an untracked file — invisible to every other machine, defeating the git-sync model. No secrets in it (password deferred to `.env`). | 3 | 3 | 1 | 30 | **EXECUTED**: classification header added, committed under `internal/` |
| D3 | README feature-currency gap: CLI reference lacks `lineage-review` (G9); the `--use-oracle` paragraph doesn't mention the per-run SQL log (the HITL verification trail, `docs/oracle-sql-logging.md`); Tests highlights predate the lineage suites; "Further reading" bills the banner'd-historical `knowledge/ARCHITECTURE.md` as the current repo-organization doc. | 3 | 3 | 2 | 24 | **MERGED into J2** (one README reconcile pass: `:DEPENDS_ON` rename + feature currency) |
| D4 | Missing runbook: no startup/refresh runbook exists; second canonical doc type (outline + instance) not yet authored. | 3 | 4 | 3 | 21 | **Tracked: L8** (ready; the runbook capstone) |
| D5 | `MODULE_MAP.md` drift: `graph_review.py` and `publishing/**` still marked "*(future H2/H5)*" though shipped; shipped `sme_notes.py` + `gate_pages.py` (both classified in the boundary test's review group) have no rows; lineage row still says "populated by the re-home" (done 2026-07-11). | 2 | 2 | 1 | 20 | **EXECUTED**: rows corrected/added |
| D6 | Stale one-shot session artifact at `docs/` root: `next-session-cron-prompt.md` (feature/oracle-ingestion cron pickup — that stream shipped; its companion plans are all banner'd superseded 2026-07-01) sits unbannered where it reads as a live instruction. | 1 | 2 | 1 | 15 | **EXECUTED**: moved to `docs/history/` with a superseded banner |
| D7 | `connection_logs.txt` at repo root: an untracked browser-console dump (localhost SSO discovery noise from the Neo4j-login troubleshooting that produced D2's doc). Not documentation; wrong place. | 1 | 2 | 1 | 15 | **EXECUTED**: relocated to gitignored `internal-local/` |
| D8 | The two living tech-debt reports (`tech-debt-port-boundary.md`, `tech-debt-taxonomy-ontology-map.md`) carry no status header, so a reader can't tell executed findings from open ones without the backlog. | 2 | 1 | 1 | 15 | **EXECUTED**: one-line tracking headers added (J7/J8, C7) |
| D9 | `UI-WIP/` untracked at root. | 1 | 1 | 1 | 10 | **Tracked: O1** (design pass in flight on its branches; no doc action) |

Non-findings verified during the sweep (recorded so they aren't re-audited): all
`docs/reviews/` point-in-time docs banner'd; `docs/restructure/` and `RELATIONSHIP_GUIDE.md`
clean of pre-relocate paths; `02-backlog.md` properly subordinated to the yaml;
`doc-knowledge-ingestion-review.md` dated/classified and absorbed into the docmeta plan;
`knowledge/ARCHITECTURE.md` banner'd historical.

## Phased remediation

- **Phase 0 — with this review (done):** D2, D5, D6, D7, D8 executed; D3 merged into J2.
- **Phase 1 — existing ready backlog, do alongside feature work:** J4 (skill refresh), J2
  (README reconcile, now including feature currency), L8 (runbook capstone). All three are in
  `next_ready` and none needs HITL.
- **Phase 2 — none.** No new items warranted; documentation debt beyond Phase 1 is
  gate-timed by design (design-doc statuses move with their epics).
