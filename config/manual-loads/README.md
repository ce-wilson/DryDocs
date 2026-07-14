# config/manual-loads — SME-authored CSV mappings (the manual final option)

**What this is.** The lowest tier of a derive-and-weight match policy: when no
automated fact tier resolves a mapping, the SME authors a CSV row that states it
directly — *source node* → *pre-defined relationship* → *target node*. First
consumer: the SEAL attribution match policy (gate
`config/gate-prompts/seal-attribution-match-policy.yaml`, backlog K2), where it
is **precedence tier 5**, below SEAL > FID > APP_NAME > ALIAS.

**Every manual load is tech debt by definition.** A manual row exists because
automation can't derive the mapping *yet*. The rules that keep that debt
visible and closable (the `LEDGER_PENDING` precedent — named, deliberate,
shrink-ambition):

1. **Pre-defined relationships only.** The `relationship` column must name an
   entry that already exists in
   `drydocs_core/ontology/relationship_vocabulary.yaml`. A CSV can never
   introduce a new relationship type — that is an ontology decision and goes
   through `ontology-mapper` + the HITL gate.
2. **Provenance stamps.** Edges written from a CSV carry
   `match_method: 'manual'` + `source: 'manual-csv'` + `manual_load_file` +
   `authored_by`. Any node a CSV forces into existence is stamped
   `manually_created: true` (+ the same file/author pointers) and is counted
   as its own line in the coverage report — never blended into matched or
   unmatched counts.
3. **Manifest before load.** Every CSV file is registered in
   [`manifest.yaml`](manifest.yaml) *before* it is loaded. The manifest's
   `pending-load` entries are the queue of files awaiting manual load; every
   entry must name its automated replacement (`replaces_with`) — a manual load
   with no named automation path is not accepted.
4. **Automation supersedes.** If a later automated run resolves the same
   mapping at any higher tier, the automated edge replaces the manual one and
   the manifest entry flips to `superseded` (file retained for audit). That is
   the designed debt-retirement path.

**Template:** [`TEMPLATE-node-mapping.csv`](TEMPLATE-node-mapping.csv).
Composite node keys are `field=value` pairs joined by `;`
(e.g. `folder_id=<FOLDER>;job_id=<JOB>`).

**Status: proposed.** Nothing reads this directory yet — the loader arrives
with the K2 build, after the gate signs off. classification: Internal-Public
(mechanism only). Real CSVs with company values are Internal at minimum and
live under `internal/` per the publish boundary — only the template and
mechanism belong here.
