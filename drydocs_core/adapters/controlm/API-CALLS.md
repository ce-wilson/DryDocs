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
| `folder_export` | `exportdeffolder` (em-xml-utility) | `controlm-planning-utils.md` (name + purpose only); `controlm-xml-definition-format.md` | Available — XML supported-but-deprecated window. **Syntax = corpus gap**; config template required. |
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
