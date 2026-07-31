# internal/registry-redesign/ — source-registry v2 design capture

**Classification: Internal** (real SEAL ids in `samples/target-partial-start.csv`;
internal system names throughout). Never leaves the private repo.

The design input for **backlog N7** (source-registry schema v2). Plan of record:
[`REGISTRY-PLAN.md`](REGISTRY-PLAN.md) — the three-distinction ruling (software
registry vs ingestion sources vs replica datasets), the `{origin}[@{carrier}]:{artifact}`
id grammar, the FCDO Data Authority (SOR/ADS) field adoption, and the 3-level
classification simplification.

## Samples (user-saved, 2026-07-31)

| File | What it is | Why it's here |
|---|---|---|
| `samples/target-partial-start.csv` | The user's target-state worksheet: the current 18 registry entries + the target column set (Taxonomy Category, Asset Type, CMDB_CI, Layer, File/Query/API, Source_Seal_id, SOR, ShortName, source URL, Query/Report Source, URN). Carries **real SEAL ids** (PAT 88152, SEAL 32010, Verum 87674, psgmgr app 82507). | The v2 row shape is derived from these columns. |
| `samples/SNOW-CMDB.csv` | ServiceNow CMDB class/relationship taxonomy sample (Catalog → Base class → relationship → `cmdb_ci_*` display names). | The `cmdb_ci` crosswalk source for system rows; a future `snow:cmdb-ci-classes` dataset. |
| `samples/DataHubExample.csv` | Excerpt from a separate chat mapping legacy asset types onto DataHub entities + URN conventions (`urn:li:dataset:(urn:li:dataPlatform:{platform},{name},{env})`), with worked rows (Control-M job, Ab Initio flow, Tableau dashboard). | The URN-handle pattern and the SOR/source-URL/query-report field-to-landing-spot mapping. |
| `samples/software-development-process-model.ipynb` | Public Neo4j example gist (Jeffrey A. Miller): SDLC graph with a NodeDomain/NodeType metamodel (Human / Process / Technical / Knowledge / Testing / Web). | Precedent for the `layer` (view) field and "every source is an SDLC participant". |
| `samples/aws-global-infrastructure-graph.ipynb` | Public Neo4j example gist (Aidan Casey, 2014): AWS regions/AZs/services/prices inventory graph. | Precedent for an infrastructure-inventory taxonomy branch. |

Not captured as a file: the 2026-07-31 chat screenshot — two ER diagrams (ServiceNow
CMDB application-service model; ITSM + Architecture management planes) with a
three-source color key (ServiceNow / SEAL / Verum), the per-node source-of-record
attribution pattern the `origin` + `authority` fields target.

Related: `internal/fcdo-reference/` (JDI identifier spec §A, Data Authority framework
§H — the transcript references the plan cites) · `docs/restructure/backlog.yaml` N7 ·
`config/source-registry.yaml` (current v1) · J21 (interim hardening of v1).
