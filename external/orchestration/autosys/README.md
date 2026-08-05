# AutoSys (CA / Broadcom Workload Automation) — PLACEHOLDER

Status: **placeholder.** No loader is active. This directory reserves AutoSys as a future
orchestration source and records how it will crosswalk to the **BMC Control-M baseline**.

## Crosswalk to baseline (draft — SME must confirm before activation)

| AutoSys native | BMC baseline concept | DryDocs node | Confidence |
|----------------|----------------------|--------------|------------|
| Job (`insert_job`) | Job | `ControlMJob` | high |
| Box job | Folder / subfolder grouping | `ControlMFolder` (Collection) | medium |
| `condition:` (s(job), d(file)) | IN condition | `REQUIRES_IN_CONDITION` → `Condition` | high |
| `condition` success → downstream | OUT condition / dependency | `EMITS_OUT_CONDITION` / `WAS_INFORMED_BY` | medium |
| Machine (`machine:`) | execution host | `ExecutionHost` | high |
| `owner:` | run-as user | `AppUser` | high |
| Calendar | calendar | (calendar resolution; see `knowledge/standards/`) | medium |

## Application attribution — the shape gap (PLACEHOLDER, 2026-08-05)

**Not yet a crosswalk row.** The signed `autosys-crosswalk` gate (2026-07-14) reviewed
11 rows; this is a 12th and needs a gate amendment before it joins
`config/crosswalks/autosys-to-bmc.yaml`. Captured here so the placeholder reflects what
was actually observed.

AutoSys and Control-M attribute work to an application at **different grains**:

| | Control-M (baseline) | AutoSys (observed) |
|---|---|---|
| Attribution key | app code → folder → jobs inherit | code → a **list of instance-qualified name prefixes** |
| Carrier | a folder attribute | the **job name itself** (dotted namespace) |
| Environment | folder/variable convention | encoded in the instance prefix (`t…` / `u…` / `l…` + number) |

An AutoSys job name is a dotted hierarchical namespace — `<instance>.<lob>.<app>.<name>.<type>`
— so attribution is a **name-prefix match**, not a container lookup. The registry row for a
code carries several prefixes at once (one per environment/instance), which is the same
environment-triplet convention already handled for Control-M FID names, applied one level up.

Two traps in that registry, to be handled before any load and NOT discovered at load time:

- **Sentinel SEAL ids.** At least one row carries a non-application placeholder id with the
  free-text instruction that the code must not be used. A sentinel must never mint a
  `:BusinessApplication` — it needs an explicit reject list, not a lookup miss.
- **Lifecycle state trapped in prose.** Decommissioning and access-restriction status live in
  a free-text `info` column alongside a date, not in a status field. Parsing prose into
  status is a gate decision, not a loader convenience.

Third instance of the standing rule (see `fid-identity-and-scope` §G): **a SEAL id appearing
in a field is not an attribution claim unless that field's job is to attribute.** An AutoSys
failure alert can carry two SEAL ids as escalation *routing*; ingesting that as attribution
would manufacture a job belonging to two applications.

## To activate
1. Add `SOURCE-MANIFEST.md` (where AutoSys defs come from, version).
2. Complete `crosswalk.md` and run it through the HITL gate.
3. Register in `config/source-registry.yaml` with `orchestrator: autosys`.
4. Only then implement a loader (mirrors the Control-M loader chain, emitting the SAME
   baseline node/edge types — no new concepts).

> Reminder: a "box job" is not a new graph concept — it crosswalks to the existing
> `ControlMFolder`/grouping. Inventing `:AutoSysBox` would re-introduce taxonomy/ontology drift.
