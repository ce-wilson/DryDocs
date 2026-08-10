# Task (identical for both tracks): O53 — HeroArt is the code graph's first front-end orphan

Backlog item O53 (module drydocs-web, groomed 2026-08-07 from Idea-77), verbatim
acceptance:

> web/src/components/HeroArt.tsx is either imported by a live route again or
> DELETED together with its index.css hero-net rule and its ui-components.yaml
> row (coverage pin moved with the history-line convention); the orphan query
> over the TS import edges then returns only vite.config.ts; build + lint green.

Notes from the groom: default is DELETE — OverviewRoute's own comment demoted
the radial hub, only a css comment still cites the file, and O30's App.css
retirement already recorded its remaining rules as dead.

Your job:
1. Independently VERIFY the orphan claim by your track's method before deleting
   anything. If your verification contradicts the claim, STOP and report that
   instead — do not delete a file you found a live importer for.
2. Apply the default (delete) unless verification said otherwise: remove
   HeroArt.tsx, its index.css hero-net rule, and its ui-components.yaml row —
   moving the coverage pin per the history-line convention you find in that
   file's neighboring retired rows.
3. Run the checks the acceptance names: the web build and lint
   (`npm run build` / `npm run lint` in web/ — use what package.json defines),
   and re-run your orphan verification to show only vite.config.ts remains.

You are in an ISOLATED WORKTREE. Commit NOTHING. When done:
- write your unified diff to the absolute results path given in your dispatch
  block (`git diff` output, plus `git status --porcelain` appended),
- return a report: what you verified, what you changed, check results,
- end with the METRICS block (verbatim keys):

```
METRICS
files_read: <n>  [list]
searches_or_queries: <n>  [each one, verbatim]
tool_calls_total: <n>
started/finished: <ISO timestamps>
blocked_on: <anything the track rules prevented, or "nothing">
```

Track-rule note for the GRAPH track only: the loaded graph's IMPORTS edges are
the Python scanner's view of the TS import graph from snapshot `bd051ab`. The
acceptance's "orphan query over the TS import edges" is exactly the shape you
run in Cypher. The FILES track verifies the same claim by grepping importers.
