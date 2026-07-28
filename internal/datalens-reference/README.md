# internal/datalens-reference — HL DataLens runtime-monitor screenshots (UI continuity references)

**classification: Internal** (screenshots of an internal company monitoring tool carrying
real product codes, Control-M folder/job names, and runtime figures — operational
metadata, no people/SIDs/secrets; the `internal/` home — tracked in the private repo,
excluded from any public push per `PUBLISH-BOUNDARY.md`).

User-supplied screenshots of **HL DataLens** (Home Lending SRE's runtime view over the
same batch estate DryDocs models), captured 2026-07-28. Kept as **design-pattern shape
references** for the console's runtime-monitor continuity work (`continuity.md` here,
groom candidates DL-1…DL-9) — not decision evidence, and per the two-track back-flow
rule (`UI-WIP/two-track-ui-plan.md`) patterns are **reproduced generically**, never
copied.

| File | What it shows | Continuity item it feeds |
|---|---|---|
| `HL-Datalens-ui-landing.png` | SLA tracker landing: per-product jobs/progress/SLA table, threshold-colored meters, tab nav | DL-4 (threshold meter), DL-7 (light-mode targets) |
| `HL-Datalens-ui-dataflow.png` | Product drill-down: per-platform data-flow cards (SQL Server / Snowflake / Teradata / S3) | DL-3 (status chips), DL-5 (shape language) |
| `HL-Datalens-ui-dataflow1.png` | Data-flow selection + RAW→TRUSTED→SNOWFLAKE pipeline stage cards | DL-4, ruled-out stacked drill-down |
| `HL-Datalens-ui-dataflow2.png` | Job Details: status filter tabs with count badges, per-job folder/name/timestamps table | DL-1 (tabular-nums), DL-3, DL-6 (identifier chips) |

`continuity.md` — the groom-candidate write-up (DL-1…DL-9) — lives here rather than
`UI-WIP/` because it names the company tool and quotes real identifier shapes
(DL-9's home-ruling, applied at ingestion 2026-07-28). The root-`/*.png` gitignore rule
kept the screenshots untracked while they sat at repo root; this folder is their
classified, tracked home.
