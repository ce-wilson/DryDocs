# Control-M API-call discovery reference (G96 clause c)

What the reference corpus (`external/orchestration/bmc-controlm/`) grounds
per operation, and each call's availability at the target version
**9.0.21.300** (clause d). The framework's per-object surface in `api.py`
is built against this table; `OPERATIONS` mirrors it and a unit test keeps
the two in step.

**Ground rules from the corpus itself:**

- The `controlm-api-folder-reference.md` / `controlm-api-job-properties.md`
  JSON pages are **SaaS conceptual reference only** — their endpoints and
  request/response JSON are flagged SYNTHESIZED in the corpus ("the BMC
  source explicitly did not include API endpoints, HTTP methods, or REST
  service details"). **Nothing here is built against the JSON call shapes.**
- 9.0.21.300 is **XML-first**: XML definition files are deprecated from
  9.0.21.100 but "fully supported until version 9.0.22"
  (`controlm-xml-definition-format.md`) — inside the supported window.
- The per-utility DTDs live on the EM under
  `<version>\Default\data\Resource` — verify exact syntax there when
  filling `[calls]` templates.

## Per-operation table

| Operation | Tool (transport) | Corpus grounding | Availability at 9.0.21.300 |
|---|---|---|---|
| `api_probe` | `ctm config servers::get` (automation-api) | `controlm-api-installation.md` — Monthly on-prem API, CLI env setup, this exact verify command | Compatible "9.0.20 and higher" **on paper**; emrestsrv install, endpoint, and token policy unverified company-side (remediation OQ-1). Grounded default template ships. |
| `folder_export` | `exportdeffolder` (em-xml-utility) — **and a second transport in working use**, the Automation API `GET /deploy/jobs?ctm=&folder=&format=XML` (automation-api); see "Two folder-export transports" below | `controlm-planning-utils.md` (name + purpose only); `controlm-xml-definition-format.md`; the API path grounded by a measured pull, not by the corpus | Available — XML supported-but-deprecated window. **Syntax = corpus gap** for the utility; config template required. The two transports return **different shapes**: the API copy omits six EM-instance attributes and carries `REAL_FOLDER_ID=0` (deployable-shaped, not a defect). |
| `folder_deploy` | `deffolder` (em-xml-utility) | same as `folder_export` | Available; syntax = corpus gap; config template required. |
| `folder_define` | `ctmdeffolder` (server-utility) | `controlm-ctmdeffolder-utility.md` — parameter grain: `-FOLDER`, `-APPLICATION`/`-SUBAPPLICATION`, cyclic, `-RBC`/`-DAYSCAL`/`-WEEKCAL`, `-INCOND`/`-OUTCOND`, `-VARIABLE` (apostrophes for `$`), `-input_file` | Available (SMART folders only). SaaS-doc caveat: verify divergence on the EM before templating. |
| `job_export` | `exportdefjob` (em-xml-utility) | `controlm-xml-definition-format.md` — "exports … from the Control-M/EM database to an output file"; `controlm-planning-utils.md` | Available; argument-file XML shape = corpus gap; config template required. |
| `job_deploy` | `defjob` (em-xml-utility) | `controlm-xml-definition-format.md` — "reads job processing definitions from a plain text input file written in XML format" | Available; syntax = corpus gap; config template required. |
| `job_define` | `ctmdefine` (server-utility) | `controlm-ctmdefine-utility.md` — parameter grain: `-FOLDER`, `-JOBNAME`, `-TASKTYPE`, scheduling/calendar, `-INCOND`/`-OUTCOND`, `-VARIABLE`, `-ON`/`-DO`, `-input_file` | Available. SaaS-doc caveat as above. |
| `job_update` | `updatedef` (em-xml-utility) | `controlm-planning-utils.md` — name + one-line purpose only | Available in principle; syntax = corpus gap; config template required. |
| `variable_set` | `ctmvar` (server-utility) | `controlm-variables.md` — grounds only "Global variables … created/modified via the ctmvar utility" | Available; **full syntax = corpus gap**; config template required. |
| `calendar_export` | `exportdefcal` (em-xml-utility) | `controlm-planning-utils.md` (name only); `controlm-calendars.md` (calendar semantics, no utility syntax) | Available in principle; syntax = corpus gap; config template required. |
| `calendar_deploy` | `defcal` (em-xml-utility) | same as `calendar_export` | Available in principle; syntax = corpus gap; config template required. |
| `calendar_copy` | `copydefcal` (em-xml-utility) | `controlm-planning-utils.md` (name only) | Available in principle; syntax = corpus gap; config template required. |
| `condition_add` | — (no grounded tool) | **no corpus ground truth** for runtime condition add | **Reported capability gap, always** (exit 3). Definition-grain in/out conditions ride `-INCOND`/`-OUTCOND` on `job_define`/`folder_define` (`controlm-ctmdefine-utility.md`, `controlm-ctmdeffolder-utility.md`). |
| `condition_remove` | — (no grounded tool) | **no corpus ground truth** for runtime condition remove | Reported capability gap, always (exit 3). |

## Two folder-export transports, and what the shape difference costs (G133)

The table above used to imply one path. There are two, and they do not return
the same document:

| | `exportdeffolder` (em-xml-utility) | `GET /deploy/jobs?ctm=&folder=&format=XML` (automation-api) |
|---|---|---|
| grounding | corpus names the tool; syntax unverified | not in the corpus; measured 2026-08-30 on one folder present in both exports |
| content | 30 JOB, 21 VARIABLE, 1 INCOND, 1 OUTCOND, 1 RULE_BASED_CALENDAR | identical content |
| EM-instance attributes | carries `IS_CURRENT_VERSION`, `VERSION_SERIAL`, `VERSION_HOST`, `VERSION_OPCODE`, `MODIFIED`, `JOBS_IN_GROUP` | omits all six |
| folder identity | `REAL_FOLDER_ID` as the EM holds it | `REAL_FOLDER_ID=0` |
| shape | an EM-instance record | **deployable** — the id is assigned by Control-M on upload, so the zero is correct for this artifact, not a defect in the pull |

**What that costs, in this repo's terms.** The graph keys folders on
`folder_id` (`drydocs/loaders/cypher/controlm_folders.cypher` MERGEs
`ControlMFolder {folder_id}`, sourced from `CM_DEF_VTAB.TABLE_ID` in
`drydocs/loaders/sql/controlm_folders.sql`), so an API-pulled folder cannot
be reconciled to a loaded folder by identity — only by name.
`IS_CURRENT_VERSION` is a live filter across the loader SQL
(`controlm_folders.sql`, `controlm_jobs.sql`, both conditions loaders), so
without it "these are the current definitions" is an assumption about API
behaviour rather than a field that can be tested.

**What is NOT lost.** The XML lineage extractor keys its rows on
`(data_center, folder_name, subfolder_path, job_name)`
(`drydocs_lineage/extractors/controlm_xml.py`) — names, not ids — so the API
export is usable for the command-line lineage weld unchanged.

**For the D11 gate** (`controlm-definition-precedence`): its clauses A1/A2
assume one XML feed against one replica. The scriptable transport is the one
that loses folder identity and the version columns, so the question is
"which XML, and can it still be joined", not "does XML beat the replica" —
recorded here so the gate session finds it; this reference rules nothing.

## Gaps the next corpus fetch should close

1. **EM XML utility syntax** (`defjob`/`exportdefjob`, `deffolder`/
   `exportdeffolder`, `defcal`/`exportdefcal`, `updatedef`) — the
   `controlm-xml-definition-format.md` fetch list; blocked producer-side by
   documents.bmc.com bot protection, reachable from the company network.
2. **`ctmvar` full syntax** — only the tool's existence is grounded.
3. **Runtime condition add/remove** — identify the 9.0.21.300 mechanism
   (utility or API service) before `condition_add`/`condition_remove` can
   leave the gap tier; do not template them from memory.
4. **Automation API install state on the company EM** — `api_probe` is the
   cheapest test once an endpoint + token exist (OQ-1).
