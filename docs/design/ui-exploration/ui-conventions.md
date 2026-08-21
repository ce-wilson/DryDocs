# Console UI conventions — status vocabulary & identifier rendering

> 2026-07-29 · lands with the O35–O41 UI sweep. Two conventions every surface follows;
> grep-enforceable, token-only (no hex anywhere downstream of `tokens.css`).

## 1. Status vocabulary → StatusChip token map (O41 / DL-12)

One mapping for every status-shaped word in the ecosystem (ours, the runtime monitor's,
and the data-management view's). No surface invents a divergent pairing.

| Ecosystem status (any tool) | Our runtime statuses | Token | Meaning |
|---|---|---|---|
| Ready / Completed | `COMPLETED` | `--green` | done and well |
| Failed / Not Completed | `FAILED` | `--status-fail-soft` (text/chips) · `--status-fail` (fills/meters) | broken — NEVER brand `--red` (DL-2) |
| Processing / Running | `STARTED` | `--teal` | actively working |
| Pending / On Wait | pending-shaped anything | `--yellow` | queued, not yet moving |
| Not Scheduled / Unknown | — | `--muted` | intentionally inert |

Consumers: `StatusChip` (`token` prop), `LoadsTimeline.statusToken`, `Meter` (threshold
fill), `ResultChip` (pass/fail glyphs). Conformance check:

```
git grep -nE "'--(red|green|yellow|teal|status-fail)" web/src   # every hit must match the table
```

`--red`/`--red-soft` are brand-only (HeroArt sphere, HubGlyphs core, BrandMark) — any
status surface using them is a defect.

## 2. Identifier rendering — IdChip + StageBadge (O38 / DL-6 + DL-11a)

Control-M folder/job names, product codes, dataset ids, and run ids are the objects
users carry between tools; they render **identically everywhere**: Plex Mono inside a
subtle chip (`IdChip`, `web/src/components/ui/IdChip.tsx`) — neutral by default,
status-tinted only through §1 tokens. No surface styles an identifier bespoke
(`font-mono text-faint` one-offs are retired as surfaces are touched).

Medallion stage names — `RAW → TRUSTED → REFINED → SNOWFLAKE`, the vocabulary both
neighboring tools already render — use `StageBadge`: flat, mono, uppercase, untinted
(a stage is a place, not a status). The graph-model half of the stage vocabulary is
B5 (taxonomy capture, SME-gated) — these badges are display only and do not imply an
ontology decision.

## 3. Runtime-view deep links ride IdChips (O39 / DL-8)

`IdChip` accepts `runtimeKind` (`job|folder|dataset|run`). When
`VITE_RUNTIME_VIEW_URL_TEMPLATE` is set (see `web/.env.example`) the chip renders an
`↗` affordance to the runtime monitor; unset renders nothing. The template value is
company config (DD-series) — no company URL ever lands in this repo.
