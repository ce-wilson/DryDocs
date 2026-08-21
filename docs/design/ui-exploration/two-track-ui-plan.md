# UI acceleration — two-track plan (producer vs company)

> 2026-07-23. Context: the incubator team's **context-graph** (React 18 + Spring Boot + Neo4j
> EE, production, 3,841 repos) was profiled in
> `internal/context-graph-analysis/ui-architecture-analysis.md`. DryDocs' console (Epic O,
> `web/` + `drydocs_api/`) already implements every planned route with fixture fallbacks; the
> gap is look-and-feel + live data at scale, not structure. This plan splits the remaining UI
> work so the producer repo and the company repo never edit the same surface in the same
> window — ports stay mechanism-only and drift stays boring.
>
> **Intended-bypass note:** the theme pass + the Under-the-Hood view were built ahead of the
> normal wireframe/gate rhythm (user-directed, 2026-07-23) to get a runnable, navigable
> console now. Everything remains read-only; O20 (write-surface gate) is untouched. Retro
> items for anything that sticks go through the normal groom.

## Track 1 — producer (this repo, Claude Code here; Sonnet/Haiku agents)

Work that needs no company data, no company credentials, and lands as ordinary commits:

| # | Item | Status |
|---|------|--------|
| T1-1 | context-graph architecture/UI analysis → `internal/context-graph-analysis/` | DONE (2026-07-23) |
| T1-2 | Theme pass: landing hero (gradient core + petals + glowing network), glass header, card hover-lift, dark-mode graph glow, SkeletonModuleRoute cleanup | branch `feat/ui-underhood-theme` |
| T1-3 | **Under the Hood** route `/under-the-hood`: 3-strategy benchmark showcase — 12-question scoreboard, token-memory tracker, hallucination spotlight (OS1), naive-vs-informed Cypher, 27.4× story; fixture from the committed P0 verdict | branch `feat/ui-underhood-theme` |
| T1-4 | Adopted context-graph patterns, generic form: `StatTiles` At-a-Glance row; empty-state honesty ("which enrichment fills this") — already partially DryDocs idiom | with T1-3 |
| T1-5 | Edge-provenance legend surfaced live in-UI (trust tiers on lineage/docs canvases, not only export manifests) — adopt of context-graph's declared/observed legend | DONE 2026-08-07 (O29) |
| T1-6 | Light-mode design pass (site-plan open follow-up; dark stays canonical) | DONE 2026-08-07 (O32) |
| T1-7 | Retire `App.css` legacy-mockup classes into the token idiom (SignIn/MyApps/GraphExplorer/TowerDrill/CypherConsole) | DONE 2026-08-07 (O30) |
| T1-8 | Eval-harness fixture refresh path: when docmeta's automated benchmark harness lands, regenerate `web/src/underhood/benchmarkData.ts` from its output instead of the hand-carried record | later, ties to docmeta M-eval |

Rationale: all of this is mechanism/fixture-grade, publishable (except T1-1, internal/), and
exercises zero company identifiers — so the company port picks it up as a clean cherry-pick
range with nothing to sanitize.

## Track 2 — company sessions (Opus 4.8, your direction; their tracker T1–T8 continues)

Work that requires company data, company auth, or judgment calls their SMEs own. Producer
ships the seams; company fills them:

| # | Item | Why company-side |
|---|------|------------------|
| T2-1 | Live wiring at scale: drydocs_api → company Neo4j (240K jobs / 1.1M vars); per-spec QuerySpec perf pass (their fleet pages prove the scale is reachable) | real data + real driver tuning |
| T2-2 | Real auth: replace mock personas with company SSO/ADFS pattern (context-graph's C2C/IDA is the local precedent; note their `/api/**` unauth gap as the anti-example) | credentials, IdP config |
| T2-3 | Company-corpus Under-the-Hood: re-run the benchmark against their corpus + their questions; the view re-reads the fixture, zero UI changes | their docs, their SMEs judge recall |
| T2-4 | Fleet-scale pages if wanted (tech-stack adoption, cross-app network) — adapt context-graph's TechStackPage/NetworkPage ideas onto QuerySpecs | only meaningful at their node counts |
| T2-5 | Deployment: serve `web/dist` + drydocs_api behind their ingress (context-graph's bundle-into-server pattern is the precedent; ours stays split FastAPI + static) | infra, networking |
| T2-6 | Anything write-shaped in the console | O20's successor gates; company runs its own gates |

## Port discipline (what keeps this drift-free)

- Producer → company: whole-branch cherry-pick of `feat/ui-underhood-theme` (web/ +
  docs/design/ui-exploration docs only; `internal/` never ports). Company does NOT restyle producer components —
  company-only surfaces live in company-only files/routes so the next port never collides.
- Company → producer: mechanism-only reproduction (the drydocs-review back-flow rule);
  screenshots → reproduce generically, never copy files.
- The UI fixture layer is the seam: producer owns components + fixtures; company owns
  QuerySpec data + env. A page is "ported" when it renders company data with zero component
  edits.
