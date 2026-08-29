# Adoption dossier 2 of 3 — lineage: mounts, scope chain, and the INVOKES split (G56/G92/G97)

**Hand-carried; never ports. Read the producer tree at tag `port-base-20260826`.**
Documents intent so the session does not reverse-engineer it from diffs; asks for
nothing back. Sequenced SECOND: mostly producer-new mechanism in
`drydocs_lineage/**`, with exactly one migration against your loaded graph.

## What this closes

Your `drydocs_lineage/**` sits at the pre-port divergent state with three
producer features held back. All three are extraction/collection mechanism —
none reads your rule values, none needs your estate data to adopt, and the one
graph-touching piece is an explicit migration you run deliberately or not at all.

## The three features, by intent

**G56 — the collector captures the mount table, so shared-vs-local storage is
DERIVED (`6fd395fb`; bundle schema v3).** A deployment path may be SHARED, and
then the same path on N hosts is ONE FILE SEEN N TIMES, not N deployments — a
fact no bundle section could answer before this (the rua-load-shapes
D-amendment). The collector (`collect/rua_inventory.sh`) emits `mounts.tsv`
UNCONDITIONALLY — read-only and instant, so "optional" is the INGEST contract,
not a config knob. It is deliberately NOT `lsblk` (an NFS spec is not a block
device, so a shared mount never appears there) and NOT `fstab` alone (configured
intent, not actual state): `findmnt -rn -o SOURCE,TARGET,FSTYPE,OPTIONS`,
`/proc/mounts` fallback, `meta.txt` recording which answered. The extractor
(`extractors/rua_inventory.py`) dispatches on PRESENCE, never the `schema=` tag,
so v1/v2 bundles come out byte-identical. Each path resolves against the LONGEST
matching mount target; `storage_scope` derives from fstype using exactly the
amendment's set; an unlisted fstype is `unknown`, counted and NAMED, never
guessed in either direction.

**G92 — the job's scope chain resolves BEFORE the file-op parse (`30c7fb7e`).**
The defect it closes: a POSTCMD moving `%%R_PATH/out.dat` and a CMD_LINE moving
`/data/r/out.dat` planned edges to TWO DataAsset nodes for ONE file, because
`_file_op` keyed the asset off the verbatim operand. A feed change, not a new
parser or resolver: the chain builds once per run, and shell text goes through
core's `resolve_command_line` — the one resolver whose stated guardrail is that
no caller re-implements substitution, now pinned by a test asserting the module
imports no regex engine. Raw stays BESIDE resolved (the G46 derived-fact shape):
the asset keys on the resolved location and every distinct raw spelling
ACCUMULATES in `raw_operands` — two jobs spelling one path two ways is exactly
the evidence that makes a wrong binding findable. `{ODATE}`-class residue is
EXPECTED and counted apart from a real miss.

**G97 — launcher and payload stop sharing the INVOKES fold (`949b3b71`).** The
writer emits `USES_ARTIFACT` to the PAYLOAD a launcher dispatches; `INVOKES`
keeps the launcher; `:Script` gains `script_role {launcher, payload}` plus the
SME-3 artifact properties. It builds what two signed gates already ruled —
nothing is reopened, no vocabulary entry edited. THE BOUNDARY THAT LOOKS WRONG
AND IS NOT: an Ab Initio pset or DPL pipeline reached THROUGH a launcher STAYS
on `INVOKES`. rua-load-shapes B2 widened `scheduler_invokes` only, and
cmdline-nfr-vetting SME-2 ruled m7 as ControlMJob->Script{payload}, which the
live vocabulary entry still says. That bucket is counted under its own name,
never as "unclassified" — the reason is a ruling, not missing evidence. The
split is minted at EXTRACTION because three things forbid a writer-only variant:
`add_rel` refuses labels outside `REL_TYPES`; `plan_curated` enforces
confirmed <= graph.rels; `script_role` on both endpoints needs a launcher node
the extractor never minted.

## Adoption order and the one migration

1. Take the cluster's code and tests together (G92 and G97 both land in
   `extractors/controlm_inventory.py`, so they adopt as one unit; G56 is
   separable but there is no reason to split).
2. Re-run YOUR collector after adoption to get v3 bundles. Existing bundles keep
   working unchanged — that is what the presence dispatch buys.
3. **`drydocs/loaders/cypher/migrate_payload_invokes_to_uses_artifact_g97.cypher`
   is the only file in this cluster that touches loaded data.** Read it before
   running; run it only against a graph already carrying folded INVOKES edges,
   after the code cluster is green, with your backup-tag pattern. If you defer
   the migration, say so in the adoption report — the folded edges keep
   accumulating until it runs, and an unmentioned deferral reads as done.

## Expect, and do not misread

- **DataAsset counts FALL on the first post-adoption inventory run.** That is
  G92 collapsing duplicates, not data loss; the five new resolve counters on the
  coverage summary line are how the run shows it.
- The G61 gate prompt in your tree (`script-provenance-gaps`, landed with the
  port as an inert file) has a section B2 that RATIFIES the launcher/payload
  boundary G97 operates. Adopting G97 does not need that gate signed — the
  boundary is already ruled by the two gates above — but if your side runs its
  own G61 equivalent, run it against the adopted code, not the deferred state.

## Done means

- `tests/unit/test_lineage_rua.py` and `tests/unit/test_lineage_inventory.py`
  arrive at the tag's state and pass (they were deferred with the code, so
  "arrive and pass," not "go green").
- `drydocs_lineage/writer.py` and `model.py` match the tag for the G97 surface;
  your side's any-divergent writer behavior that predates this cluster is a
  ledger question, not something to fold silently into this session.
- Zero deltas outside `drydocs_lineage/**`, the migration cypher, and the two
  test files.

## Out of scope

The ontology cluster (dossier 3) — including everything under
`drydocs_core/ontology/relationship_vocabulary/**`. The G97 vocabulary entries
themselves are already active on both sides; this session changes no vocabulary
status. Estate profiling numbers (RELAY-15/RELAY-16 territory) are separate work.
