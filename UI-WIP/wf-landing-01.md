# wf-landing-01 — radial-hub landing (rung 2, text wireframe)

> Spec source: `site-plan.md` §3 (module menu + radial hub) · backlog **O9** ·
> visual base: `Gemini_Generated_Landing-Favorite.png` (raster mock — geometry only,
> the build is SVG). Rung-3 companion: `wf-landing-01.html`.
> One fidelity rule: structure/naming/links ONLY here — no color, no copy polish.

```
+---------------------------------------------------------------------------------+
| [logo·wordmark]         [ search: nodes, servers, jobs.... ]  [Prod|UAT|Dev]    |
|                                                     [sys/dark/light] [bell] [@] |  HEADER 64px
+--------+------------------------------------------------------------------------+
| ASIDE  | TOOLBAR:  Home                                              (no page   |
| 250px  |                                                              actions)  |
|        +------------------------------------------------------------------------+
| Over-  |                                                                        |
| view*  |                    RADIAL HUB  (SVG, ~55-60% viewport)                 |
| Expl-  |                                                                        |
| orer   |       (2)Ownership     (1)Explorer      (3)Lineage                     |
| Line-  |              \              |              /                           |
| age    |               \             |             /                            |
| Owner- |  (4)Runbooks --------   [ CORE ]   -------- (5)Docs                    |
| ship   |               /       brand sphere      \                              |
| Run-   |              /              |              \                           |
| books  |    (6)Remediation       (7)Loads         (8)Gates                      |
| Remed- |                                                                        |
| iation |   each spoke = icon + module name + one-liner + health dot             |
| Docs   |                                                                        |
| Gates  |             [ CTA: Explore the graph ]  -> /explorer                   |
| Loads  +------------------------------------------------------------------------+
|        |  [benefit card] [benefit card] [benefit card] [benefit card]           |
| ------ +------------------------------------------------------------------------+
| Settgs |  [ onboarding checklist (first-run only, dismissible) ]                |
| Prof.  +------------------------------------------------------------------------+
| S.out  |  footer: (c) DryDocs · Docs | API | GitHub | Support                   |
+--------+------------------------------------------------------------------------+
```

## Annotation key

1. **One module registry array drives BOTH the aside nav and the hub spokes** —
   spoke click and nav click are the same route (site-plan §3). Adding a module =
   one registry entry, zero layout edits.
2. Spoke order around the core is clockwise from 12 o'clock: Explorer, Lineage,
   Docs, Gates, Loads, Remediation, Runbooks, Ownership — phase-1 modules nearest
   the top. (Mock shows 5 spokes; we have 8 — spacing at 45°.)
3. *Overview is the landing itself* — it appears in the nav (active state) but has
   no spoke; the core sphere is its representation.
4. Health dot per spoke: fed later by the Loads module's JobRun QuerySpec; until
   O11, render as static neutral (no fake green — synthesized-honesty rule).
5. CTA is **generic** `-> /explorer` (design-review 🟡: no hard-coded tower).
6. Header carries: global search, env toggle, **3-state theme toggle**, avatar.
   Breadcrumbs do NOT live here (toolbar owns them — layout-anatomy rule).
7. Benefit cards (4): Automated Discovery · Impact Analysis · Governance & Posture ·
   Change Management (gemini-wire-frame.md set). Copy pass later — placeholder text.
8. Mobile/narrow: hub degrades to a **module card grid** (same registry), aside
   becomes off-canvas drawer. The radial SVG is desktop-only sugar, never the only path.
9. Demo/synthetic content anywhere on this page keeps the
   `EXAMPLE DATA · ILLUSTRATIVE` tag idiom.

## Open items (do NOT resolve silently — HITL design rule)

- [ ] Onboarding checklist contents (which 3–5 first-run steps?).
- [ ] Whether footer repeats the module list (SEO/marketing concern only if this
      shell ever doubles as the public site — see project-website-and-backstory).
