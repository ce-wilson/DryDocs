# Planned-entry review — the five held at gate `vocabulary-domains-and-id-policy` (§C1b + §C1d)

**Status: AWAITING SME REVIEW.** At the 2026-08-12 gate session the SME held these five
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

**Disposition:** _pending_

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

**Disposition:** _pending_

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

**Disposition:** _pending_

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

**Disposition:** _pending_

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

**Disposition:** _pending_
