# Control-M Automation API Installation - Vendor Specifications

**Source:** BMC Software - Control-M Automation API **Monthly (on-prem)** Documentation
**Document:** API_Installation.htm (https://documents.bmc.com/supportu/API/Monthly/en-US/Documentation/API_Installation.htm)
**Date Scraped:** 2026-07-09
**Purpose:** Automation API component installation reference — REST API server, CLI, Workbench — for the remediation acquisition spike (drydocs-remediation TDD OQ-1)

⚠️ **VERSION NOTICE:** This is the **Monthly release** documentation set (the on-prem
Automation API distributed via S3/EPD — NOT the SaaS doc set the older `controlm-api-*.md`
files came from). The page documents the current monthly package `PADEV.9.0.22.120`; our
target environment is Control-M **9.0.21.300**. Per the page's own compatibility statement
(VERBATIM below), monthly API releases are compatible with Control-M 9.0.20 and higher —
9.0.21.300 is in range, subject to what is actually installed on the company EM.

---

## 📑 Provenance Classification

Tiers: **[VERBATIM]** BMC quotes · **[GROUNDED]** Claude paraphrase of sourced content ·
**[SYNTHESIZED]** Claude-authored, not in source (do NOT load as vendor ground truth).
See SOURCE-MANIFEST default tier rule.

- **[VERBATIM]:** the quoted compatibility and Java statements below.
- **[GROUNDED]:** component descriptions, install/uninstall procedures, port/prereq facts,
  CLI environment setup, Workbench steps — paraphrased from the fetched page.
- **[SYNTHESIZED]:** the "Notes for Planning Agents" section (remediation OQ-1 analysis) —
  Claude inference, never vendor ground truth.

⚠️ **Acquisition note:** fetched 2026-07-09 through a real browser session — direct
programmatic fetch of documents.bmc.com returns HTTP 403 (bot protection), the known
producer-side blocker recorded in the docmeta plan.

---

## Components Overview

Three installable Automation API components [GROUNDED]:

| Component | What it is | How it arrives |
|---|---|---|
| **Control-M REST API** | the API server (the `emrestsrv` process on Control-M/EM) | monthly download from Amazon S3 or EPD; versions install side-by-side |
| **Control-M Automation API CLI** | the `ctm` command-line client | installed on Control-M/EM during Control-M installation; installable standalone from the endpoint |
| **Control-M Workbench** | a self-contained development environment (no Control-M install needed) | Docker image from distribution.bmc.com |

## REST API — Compatibility and Versioning

Direct quotes [VERBATIM]:

> "Control-M Automation API monthly releases are compatible with Control-M 9.0.20 and higher."

> "Control-M Automation API no longer supports Java 11 as of version 9.0.21.325, the monthly
> release of October 2024. Starting with this version of Control-M Automation API, Java 17 or
> higher is required."

Additional facts [GROUNDED]:
- Different API versions can reside side-by-side; installing a Control-M version carrying an
  older API does not overwrite a newer API.
- The documentation flags per-feature minimum Control-M versions.
- Upgrading from below 9.0.21.100 changes the old default ports **48080/48081** to the new
  defaults **32080/32081** automatically.
- During an upgrade the API process (`emrestsrv`) is stopped and automatically restarted.

## REST API — Install / Uninstall

[GROUNDED] Install from **Amazon S3** or **EPD** (Control-M/Enterprise Manager 9.0.22
download page): save the `PADEV.9.0.22.120` package to a temp directory; UNIX requires
`chmod +x`; run the `.bin`/`.exe` **as the same user account that installed Control-M/EM**.
The installer extracts to `/tmp` by default (override with the `INST_TEMP_DIR` environment
variable). Uninstall: run `uninstall.bin`/`uninstall.bat` under
`<EM_HOME>/install/PADEV.9.0.22.120`.

## Automation API CLI

[GROUNDED] Prerequisites: **Python 3.8.4+** and **pip 20.1.1+** (the CLI migrated from
node.js to Python; a node-based CLI keeps running where Python is absent, and old-CLI usage
is logged server-side in `.../automation-api/downloads/old-cli-usage.log`); **Java 17+
64-bit** for the Provision service (a different Java than the API server's). The CLI and
REST API server versions must match — the system auto-upgrades/downgrades the CLI.

Install: download `install_ctm_cli.py` **from the endpoint itself** —
`https://<controlmEndPointHost>:8443/automation-api/install_ctm_cli.py` (or from a local
Workbench at `https://localhost:8443/...`) — then `python install_ctm_cli.py`; verify with
`ctm` (prints the API service list). On Windows with multiple CLI installs, launch via
`ctm.cmd` (not `ctm.bat`); locate with `where ctm`.

## CLI Environment Setup

[GROUNDED] An *environment* = REST API endpoint + **API token**, or endpoint + username +
password:

```
ctm environment add <env> "https://<controlmEndPointHost>:8443/automation-api" "<token>"
ctm environment set <env>
```

- The first API token is obtained through the Control-M user interface (see the vendor's
  "Creating an API Token" / Authentication Service pages).
- Environments persist in `~/.ctm/env.json` (Linux) / `%USERPROFILE%\.ctm\env.json` (Windows).
- CA-signed-certificate enforcement: set `rootCertificateRequired` to `true` via
  `environment configure`.
- Setup verification is itself a **pull**: `ctm config servers::get` returns the
  Control-M/Servers this endpoint knows.
- On-screen docs: `ctm documentation restApi` (environment-specific REST reference) and
  `ctm doc gettingStarted`.

## Control-M Workbench (Docker)

[GROUNDED] A standalone development Control-M as a Docker image (hosted on
distribution.bmc.com; EPD entitlement + a Personal Access Token required for
`docker login`):

```
docker pull distribution.bmc.com/ctmem/workbench:9.22.120-GA
docker run -dt --cpus=4 -m 8g -p 8443:8443 --hostname=workbench distribution.bmc.com/ctmem/workbench:9.22.120-GA
```

Requirements: ports **8443** (endpoint) and **7005** (Provision service) free; ~8 GB memory
for the container; container healthy within ~3 minutes; examples in the vendor GitHub
repository.

## Notes for Planning Agents

[SYNTHESIZED — remediation OQ-1 analysis; not vendor content]

- **OQ-1 partial answer:** an on-prem pull path exists in principle for our 9.0.21.300
  environment — the Monthly REST API installs on Control-M/EM and is compatible "9.0.20 and
  higher". What remains TBD company-side: whether the API server is *installed* on the
  company EM, its endpoint/port reachability, token issuance policy, and which services our
  role can call.
- **The verify command doubles as the availability probe:** `ctm config servers::get` (or
  the equivalent REST call against `https://<host>:8443/automation-api`) is the cheapest
  "what can I pull" test once an endpoint + token exist.
- **Workbench is the greenfield test bed:** a local Docker Control-M means Tier-1/Tier-2
  fix packages could be *deployed and executed* against a disposable environment before the
  Jira handoff — a stronger-than-offline equivalence check, without touching production and
  without violating SoD. Candidate addition to the remediation TDD when OQ-1 closes.
- **CLI is Python-based** (3.8.4+), which sits naturally beside the DryDocs runtime; the
  `DefinitionFormat` API impl could shell the `ctm` CLI or call REST directly — decide when
  the spike lands.
