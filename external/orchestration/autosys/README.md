# AutoSys (CA / Broadcom Workload Automation) — PLACEHOLDER

Status: **placeholder.** No loader is active. This directory reserves AutoSys as a future
orchestration source and records how it will crosswalk to the **BMC Control-M baseline**.

## Crosswalk to baseline (draft — SME must confirm before activation)

| AutoSys native | BMC baseline concept | DryDocs node | Confidence |
|----------------|----------------------|--------------|------------|
| Job (`insert_job`) | Job | `ControlMJob` | high |
| Box job | Folder / subfolder grouping | `JobFolder` (Collection) | medium |
| `condition:` (s(job), d(file)) | IN condition | `REQUIRES_IN_CONDITION` → `Condition` | high |
| `condition` success → downstream | OUT condition / dependency | `EMITS_OUT_CONDITION` / `WAS_INFORMED_BY` | medium |
| Machine (`machine:`) | execution host | `ExecutionHost` | high |
| `owner:` | run-as user | `AppUser` | high |
| Calendar | calendar | (calendar resolution; see `knowledge/standards/`) | medium |

## To activate
1. Add `SOURCE-MANIFEST.md` (where AutoSys defs come from, version).
2. Complete `crosswalk.md` and run it through the HITL gate.
3. Register in `config/source-registry.yaml` with `orchestrator: autosys`.
4. Only then implement a loader (mirrors the Control-M loader chain, emitting the SAME
   baseline node/edge types — no new concepts).

> Reminder: a "box job" is not a new graph concept — it crosswalks to the existing
> `JobFolder`/grouping. Inventing `:AutoSysBox` would re-introduce taxonomy/ontology drift.
