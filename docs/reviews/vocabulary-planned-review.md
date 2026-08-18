# Planned-entry review — the five held at gate `vocabulary-domains-and-id-policy` (§C1b + §C1d)

**Status: ALL 5 RULED (2026-08-18, G91). Gate closed.** Rulings transcribed to
`config/gate-log.md`. The "Evidence / Against" lines below were PRODUCER-DRAFTED to help the
SME rule — they are not SME positions, and where the walk checked them against the code two
did not survive (noted per entry).

**Status of record: AWAITING SME REVIEW.** At the 2026-08-12 gate session the SME held these five
entries out for a file-based review instead of ruling them in-session. They stay
`status: planned` until this review is ruled; the ruling is transcribed back to
`config/gate-log.md` as a follow-up entry citing the gate slug, and any deprecation
lands with `deprecated_at` + a note citing that entry.

**How to rule:** mark each Disposition line `keep-planned` or `deprecate` (with a reason),
then hand the file back. Nothing here flips to `active` — that always requires the
supplement + loader build (the flips-are-follow-ups pattern).

---

## 1. `m3_depends_on_file` — §C1b

| | |
|---|---|
| Label | `USED` (role `file_dependency`) |
| Shape | `ControlMJob -> File` |
| Domain | scheduler (post-rename) |
| Loader / supplement | `~` / `ontology_supplement.cypher` |

**Registry note:** Job waits on a file delivered via MFTS agent (`fmSubPathId`). Normalized
from the pre-ontology `DEPENDS_ON` edge in the architecture diagram: `DEPENDS_ON` is retired
(job→job replaced by `WAS_INFORMED_BY`; job→file is matrix row Activity → Entity = `USED`
with `role=file_dependency`).

**Evidence for keeping:** file-watcher jobs are a real, common Control-M mechanic (the FW
task type; the DPL ingestion leg's `.dat`/`.tok` conditions), and the greenfield-standard
rulings (C30/G67) treat FW as inherently inbound — a file-dependency edge is the graph-side
counterpart. **Against:** no feed is wired; the MFTS `fmSubPathId` source has not been
profiled.

**Checked at the walk, and the "against" understates it.** The FileWatcher model is BUILT
producer-side except for this edge: `:File` carries a hand-written index
(`constraints.cypher:140`, `file_arrival` on `f.arrived_at`), the job type is parsed
(`description_tokens.py`, `JobType.FILE_WATCHER`), and the watched-path role resolves
(`paths.py`, `FILEWATCH|WATCH|FW_` → `WATCH_INPUT`). The FileWatcher metadata LOADER is
company-only, which is why nothing writes it here. And something already waits on the
ruling: `config/gate-prompts/autosys-crosswalk.yaml:102` flags its `d(file)` row as
approximate — *"may need a FileWatcher-job mapping instead"* — with §115 making resolve-or-defer
a gate condition.

**Disposition:** **keep-planned** (SME, 2026-08-18). Id migrated to
`scheduler_depends_on_file`; `m3_depends_on_file` deprecated as an ID MIGRATION, not a
semantic retirement.

---

## 2. `m3_executed_by` — §C1b

| | |
|---|---|
| Label | `EXECUTED_BY` |
| Shape | `ControlMJobRun -> AppUser` |
| Domain | scheduler (post-rename) |
| Loader / supplement | `~` / `ontology_supplement.cypher` |

**Registry note:** Run executed as a service account (Run-as-User; EPV rows with
Use Case='CONTROL-M'). Matrix row: Activity → Agent. Feed: Control-M history API.

**Evidence for keeping:** the run-as/OWNER axis is already load-bearing elsewhere
(psgmgr OWNER queries; the EPV FID work feeding K16/K17). **Against:** the from-node
`ControlMJobRun` barely exists — runtime ingestion (job-run history) is not scheduled
producer-side, and `p2_instance_of` (the run→definition edge) is itself only planned,
so this edge would dangle from a node type with no loader.

**The grain question the walk had to answer first:** this is the RUN-grain run-as (what a
particular run executed as, from the Control-M history API) — NOT the job definition's
configured account. Checking that surfaced a gap: the DEFINITION-level fact
(`CM_DEF_VJOB.OWNER`, loadable from psgmgr today) had **no registered edge at all**; every
`:AppUser` entry was run-grain, host-side, or unrelated.

**Disposition:** **keep-planned / HOLD on K17** (SME, 2026-08-18), matching `m3_delegates_to`
at rua-load-shapes §A1 — *"not declined — blocked on identity"*. Id migrated to
`scheduler_executed_by`. A sibling `scheduler_runs_as` (ControlMJob → AppUser, the configured
account) was RAISED in the same ruling, planned, carrying the same K17 keying fence.

---

## 3. `catalog_has_area_product` — §C1d

| | |
|---|---|
| Label | `HAS_AREA_PRODUCT` |
| Shape | `Product -> AreaProduct` |
| Domain | catalog |
| Loader / supplement | `area_products.cypher` / `catalog_ontology_supplement.cypher` |

**Registry note:** Product contains Area Product Groups (Team of Teams). Local catalog
hierarchy.

**Evidence for keeping:** part of the ratified PAT ontology design (AreaProduct = Team of
Teams); the loader file is already named. **Against:** the PAT build has been sequenced
behind other work since the design landed; if AreaProduct is no longer wanted, all three
catalog entries below retire together.

**The "Against" line did not survive checking, and it was never an SME position** — it was
drafted here to prompt a ruling. `:AreaProduct` was already live in three ACTIVE entries
(`catalog_supports_area_product`, and the two K5 Cabinet edges scoped `Product | AreaProduct`),
so "no longer wanted" was not the live option. Nor do entries 3 and 4 stand or fall together:
3 is WRITTEN (`area_products.cypher` MERGEs it with the C22 orphan sweep) and 4 has no writer
at all.

**Disposition:** **ACTIVATE** (SME, 2026-08-18). It already met this file's own bar —
`active = supplement + loader both exist` — and was held as planned on a DATA gap, a different
axis. The sample carries `area_products: 0`; the production PAT extract carries the layer.

---

## 4. `catalog_area_product_has_dev_team` — §C1d

| | |
|---|---|
| Label | `HAS_DEV_TEAM` |
| Shape | `AreaProduct -> DevTeam` |
| Domain | catalog |
| Loader / supplement | `area_products.cypher` / `catalog_ontology_supplement.cypher` |

**Registry note:** Area Product Group contains DevTeams. Same label as Product→DevTeam;
`from_node` type distinguishes context in queries.

**Evidence:** stands or falls with `catalog_has_area_product` (entry 3) — the same
AreaProduct model and the same named loader.

**That pairing is wrong on both halves.** Entry 3 is written and entry 4 is not — the named
loader `area_products.cypher` never wrote this edge, and its header claimed otherwise until
corrected at this ruling. The only `HAS_DEV_TEAM` writer is `dev_teams.cypher`, parented on
`:Product`.

**Disposition:** **deprecate — redundant** (SME, 2026-08-18). DevTeam↔AreaProduct is already
carried by the ACTIVE `catalog_supports_area_product` (`DevTeam -[:SUPPORTS]-> AreaProduct`,
C4 2026-06-21); this entry declared the same pair in the opposite direction under a second
label. Never built, so nothing is deleted. NOT a rejection of `:AreaProduct` — its sibling
went active in the same ruling.

---

## 5. `catalog_dev_team_has_membership` — §C1d

| | |
|---|---|
| Label | `HAS_MEMBERSHIP` |
| Shape | `DevTeam -> Membership` |
| Domain | catalog |
| Loader / supplement | `pat_team_roles.cypher` / `catalog_ontology_supplement.cypher` |

**Registry note:** DevTeam has a timed role-holder membership. Reuses the `org:Membership`
n-ary pattern from SEAL (Application→Membership). PAT-side human roles: Tech Partner,
Area Tech Partner, Software Engineering Manager, Software Engineer, SRE Director, etc.

**Evidence for keeping:** the PAT role-holder model is live work (K20 drafts the Tech
Partner-level K5 amendment; the TOM roles gate signed 2026-08-11). **Cross-current:** the
SEAL-side `HAS_MEMBERSHIP` chain (`seal_has_membership` / `seal_of_role` / `seal_held_by`)
was DEPRECATED 2026-07-15 in favor of qualified attribution — if PAT follows the same
pattern shift, this entry would be superseded by an attribution triple rather than built.
This is the strongest candidate for re-shaping instead of keeping as-is.

**Checked at the walk — and the "cross-current" understated it in one direction and
overstated it in another.** `pat_team_roles.cypher` ALREADY writes the full n-ary triple
(`HAS_MEMBERSHIP`, `OF_ROLE`, `HELD_BY`) while only this leg is registered — but that is NOT
a registration gap. The C8 rule says identical triples are REUSED, never twinned, and both
other legs are identical to the SEAL ones. The real defect: the entries to be reused are
DEPRECATED, so a loader would mint "no longer loaded" edges on every run — and the estate is
truncate-and-reload, so nothing about that is benign.
Two carve-outs had spared it: K4's own note (*"org: stays for the PAT product hierarchy only
… NOT deprecated"*) and C20 (2026-07-28), which scoped the K4 retirement to the SEAL loaders
and kept `:Role`/`:Membership` load-bearing catalog-side.

**Disposition:** **re-shape onto qualified attribution** (SME, 2026-08-18) — superseding both
carve-outs. This was the last holdout on the reified Membership pattern; SEAL moved at K4 and
the PAT product side at K5, so one employee was reaching the graph by two different routes.
Replaced by `catalog_dev_team_qualified_attribution` + `catalog_dev_team_attribution_had_role`,
both planned, with the `HAS_AGENT` hop REUSED from `seal_attribution_has_agent` per C8.
`pat_team_roles.cypher` is fenced do-not-run until rewritten.
