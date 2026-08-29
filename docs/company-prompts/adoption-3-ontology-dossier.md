# Adoption dossier 3 of 3 — ontology: the TOM vocabulary as data, the seal increment, and the planned riders (G70 + K22/C28/K20 fragments)

**Hand-carried; never ports. Read the producer tree at tag `port-base-20260826`.**
Documents intent; asks for nothing back. Sequenced LAST deliberately: this is the
most valuable and the most entangled cluster, it touches company-canonical
surfaces, it changes role identity on loaded rows, and it is the one session that
includes a gate on YOUR side. Run it after the remediation and lineage sessions
have rehearsed the union discipline.

## What this closes

Your side is still running the exposure G70 ended: the TOM role vocabulary
hardcoded across four surfaces in three languages (the SealRole enum, the
`_ROLE_CANONICAL` alias map, the loader's Cypher CASE, the supplement's scheme
seed) — four lists, none agreeing, and the only YAML copy read by no code. That
vocabulary drifted TWICE inside one signed gate with the suite green. The
declaration file is also the ONE place your role names and the producer's can
reconcile — which is why this session starts with a ruling, not a merge.

## The gate comes first, and it is yours

G70 seeds from the producer's signed rulings (tom-roles-enumeration-and-
cardinality, 2026-08-11). Producer sign-off is not company sign-off — your
report's own two-tier doctrine. Before any file lands, YOUR gate rules ONE
question with two halves:

- **Ratify or reconcile:** does the producer's declared scheme — sixteen classes,
  7 required + 9 optional, the Operate Manager split into three
  responsibility-scoped classes, both SRE rows derived, Risk Manager crosswalked
  to `technology_risk_controls` and stopped — match YOUR estate's accountable
  role classes? If your extracts carry names the declaration does not, the
  declaration file is where they surface: as new classes, as aliases, or as
  flagged-undeclared loads. That is an SME ruling, not a merge decision.
- **The catalog verification the file itself says is pending:** the declaration's
  header states its ServiceNow catalog names are TRANSCRIBED from K21 §10.7/§10.8
  because the 83-row catalog export lives company-side. You hold the export; this
  gate is the natural place to verify the transcription against it and record the
  result — the one check the producer structurally cannot run.

## The G70 mechanism, by intent (`4f28010d`)

- `config/taxonomy/tom-role-vocabulary.yaml` is the ONE declared surface; every
  class records both registers (SEAL extract spelling = the canonical the loaders
  key on; ServiceNow catalog row). Cardinality is recorded ONCE on the scheme —
  one-or-more everywhere; singleton-ness is a graph-test question, never a
  database constraint.
- `drydocs_core/ontology/tom_role_vocabulary.py` reads it; SEVENTEEN drift guards
  (`tests/unit/test_tom_role_vocabulary.py`) force the supplement seed, the alias
  table, the loader Cypher, and the taxonomy sample to defer to the declaration.
  This is why partial adoption fails structurally: land the YAML without the
  loader/model/supplement changes and the guards go red immediately, by design.
- **`SealRole` is retired AS THE ADMISSION GATE:** an undeclared name loads
  FLAGGED, never dies at validation. Note before you diff: your report
  record-corrected the earlier "admits+flags" claim — at the pre-port state BOTH
  sides refused unknown roles; this cluster is where the producer side actually
  changed that behavior. Adopting it changes yours the same way: the four classes
  the producer measured as silently lost now load, and the raw source string
  survives verbatim beside the canonical.
- `business-application.yaml` loses its roles register (the declaration replaces
  it; the memberships stay as sample data, guarded against the declaration). Your
  copy is company-canonical and was kept at the port — deleting the register from
  YOUR copy is part of this adoption, not a clobber.

## Do-not-clobber list

- **`m3_seal_app_ref` and your active seal attribution state.** Seal attribution
  is company-canonical. The producer seal increment (`models/seal.py`,
  `seal_contacts.cypher`, the seal ontology supplement) is adopted FOR the
  vocabulary mechanism it carries, not as a re-take of attribution shape — where
  your seal files diverge for attribution reasons, your shape wins and the
  divergence stays ledgered.
- Your gate-log and your gate doctrine. This session writes YOUR gate record;
  producer gate-log stubs remain producer audit.
- Anything the K20 amendment gate may later move (below) — do not pre-apply it.

## The migration

`drydocs/loaders/cypher/migrate_tom_role_split_g70.cypher` moves exactly three
populations (the Operate Manager split — a drift guard pins that it moves
exactly those three). It CHANGES ROLE IDENTITY ON LOADED ROWS. Run it only after
the code cluster is green, with the backup-tag pattern, and read it first. If
your graph carries role rows under names outside the three populations, that is
a finding for the gate above, not a reason to widen the migration.

## The planned riders that ride along (nothing loads)

- **K22 (`a7ee9239`):** the `:DeploymentModule` CI proposal — a G0d-RIDER beside
  the signed §G0d, plus two vocabulary entries registered `planned` only.
  Nothing flips active; attribution stays on `:BusinessApplication`. Take the
  planned rows or not; they write nothing either way.
- **C28/K20 map and vocabulary fragments** (`60-mappings-corporate.yaml`, the
  planned corporate-layer edges, the K20 gate page): ALL entries are `proposed`
  or `planned`, and the K20 gate is an unsigned amendment draft on the
  producer's K5. Your reconcile's `unsigned_activations()` check (landed with
  this port) is the guard here: no entry may go active citing a DRAFTED stub.
  Nothing in this dossier authorizes an activation.

## Done means

- Your gate record exists BEFORE the vocabulary lands, and its ruling is what
  the landed declaration file reflects (ratified as-is, or reconciled with your
  additions — either is a valid outcome; silence is not).
- The seventeen drift guards plus `test_seal_roles.py`, `test_seal_samples.py`,
  and `test_business_key_backbone.py` arrive at the tag's state and pass against
  YOUR declaration file.
- The migration has either run (with the backup tag recorded) or its deferral is
  stated in the adoption report with the folded state it leaves behind.
- The ledger entries for this cluster retire with dated reasons; what remains
  divergent afterwards (seal attribution shape) is re-scoped to exactly that,
  so the next port's reconcile reads a narrow divergence instead of a cluster.

## Out of scope

Signing the producer's K20 amendment (product-cabinet family — a different
scheme, a different gate, and the producer's own SME session). The
ProductRole/cabinet side entirely. Any UI surface. Estate profiling.
