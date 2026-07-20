# DAT NFR Checklist — Catalog (Data & Analytics Products)

**Corpus:** INTERNAL (governance, tier ③ DAT). **Status:** 🟠 DIGESTED — 2026-06-17.
**Sources:** "NFR Checklist for DAT products" (DAT SRE; `NFR1`/`NFR2` pages), the **ICDW Snowflake NFR** variant page (same categories, with added *Framework Application* + *Evidence Required* columns), `HomeLending-NFR1/2` (HLT view), Jira refs `DPL-17622` / `DPL-17622`.

> ⚠️ **Provenance:** this is the DAT SRE-owned NFR standard *as observed in the checklist pages* — verbatim category/initiative/description, **Operation Risk** column transcribed. Where a row is a question ("What and How will…?") it is an *open requirement to answer per product*, not a settled rule. Confirm interpretation with DAT SRE.

This is the requirements catalog behind [dat-naming-standard.md](dat-naming-standard.md) §2b and the synthesis in [nfr-consistency-and-greenfield.md](nfr-consistency-and-greenfield.md). HLT (tier ④) inherits it and adds the application-view deltas ([hlt-naming-standard.md](hlt-naming-standard.md)).

---

## 1. The checklist (by category)

Risk = the checklist's **Operation Risk** column (impact of *not* meeting it).

### Monitoring
| Initiative | Requirement | Risk |
|---|---|---|
| What & how is the **application** monitored? | Standardized monitoring **product** — Splunk, Control-M for batch schedule, Control Center, etc. | High |
| How is the **platform service** monitored? | **Datadog / Splunk / Grafana / Managed Dynatrace** for **all hops** within the services. | High |

### Alerting
| Initiative | Requirement | Risk |
|---|---|---|
| Alerts generated & logged in SNOW | **All failures create incidents in SNOW** with proper description **from each hop**. | High |

### Error Handling
| Initiative | Requirement | Risk |
|---|---|---|
| Error capture pattern + log standardization | Errors **traceable back to the origination** of the issue; **throw exceptions and propagate errors with specific error codes + descriptive messages**. | High |

### Logging
| Initiative | Requirement | Risk |
|---|---|---|
| Logging pattern | Common standards for logging. | Medium |
| Physical log storage | **S3 or NAS**. | Low |
| Milestones captured | **All hops** milestone. | High |
| Log indexing | See **§2 (structured logging spec)** below. | High |
| Centralized logging | **Splunk** (CCB Splunk or Doppler Splunk). | High |
| Distributed tracing use cases | Trace + **span IDs** to pinpoint hot spots / root cause across frameworks. | High |
| Streamline logging | History retention for logs; **application vs services**. | Medium |

### Performance
| Initiative | Requirement | Risk |
|---|---|---|
| Performance matrix | Benchmark — **TPS, throughput, load time for 1 / 10 / 50 GB files**. | Medium |
| Concurrency | No. of concurrent executions + **upper limits** for services. | Medium |

### Operational Support Readiness
| Initiative | Requirement | Risk |
|---|---|---|
| Data viewer tools | What tool queries the data. | High |
| Pipeline registration / validation access | How code compatibility tracks with the latest framework. | Medium |
| Dashboard | Real-time services / event monitoring / job execution / historical trends. | High |
| Backend access for observability & automation | Services should have **API access**. | Medium |
| Restartability | **Self-heal framework**. | High |
| Health check API | Health-check API service. | High |
| Access | Shared interactive access to all monitoring tools / logs / S3 bucket. | High |
| Runbooks | With **SLO/SLA impact statements, SOR/downstream, support contacts, recovery steps**. | Medium |
| Job failure categories | Define categories & pattern. | Medium |
| Escalation matrix | Who supports all aspects of infra and how to engage. | High |

### Batch Processing
| Initiative | Requirement | Risk |
|---|---|---|
| Scheduling + event-driven approach | Process for **on-prem scheduling** and **event-driven**; common solution + **naming standards** for apps adopting the same framework. | High |
| Job execution status | Rows processed, throughput, files generated + metadata, **real-time and history**, SLA. | High |
| Data-issue troubleshooting | Data validation, **TDQ issue backtrack**, recon, audit history. | High |
| How is code managed | New DPL version image vs existing image. | Medium |
| Backward compatibility | — | Medium |

### Stability & Resiliency
| Initiative | Requirement | Risk |
|---|---|---|
| Workload management | Capacity-management review process. | Medium |
| Resiliency & shared resource allocation | — | Medium |
| Compute properties | — | Medium |
| Retention policies & archive | Process to check retention policies and archive. | Medium |
| Trap document | — | Medium |

### Build, Test & Deploy
| Initiative | Requirement | Risk |
|---|---|---|
| Automation deployment | **CI/CD — Jules adoption / Jet**. | Low |
| Manual fallback | If automated deployment fails, is deployment done manually? | Low |

### Security
| Initiative | Requirement | Risk |
|---|---|---|
| Separation of duty | Roles & access controls. | High |
| Code compatibility | **AMI compatibility between framework and application** code maintained. | Medium |

### Behavioral Analytics
| Initiative | Requirement | Risk |
|---|---|---|
| Metrics | Job promotion. | Low |

---

## 2. Structured-logging spec (the load-bearing logging requirement)

For human readability **and** machine parsing (Splunk indexers, no custom regex):

- **Structured logging**; separate **LogTypes** into logical categories: **Informational, Error, Metrics/Audit, System, Web**.
- **Mandatory key/value fields** (the onboarding key-pairs for Splunk):
  `PipelineId/graph pset · Component · JobId · Event · Exception · ErrorCode · OrderDate · BusinessDate · OwnerSealId · Service · Path · Level · Userid · Message · Timestamp`
- **Index on `ErrorCode`** (sample queries require it).

> 🔗 **This key set is the same metadata the graph wants.** `Component`/`OwnerSealId` = SEAL, `OrderDate` = ODATE, `BusinessDate` = BUS_DATE, `PipelineId` = the pipeline-derived SEAL source, `Path` = watched/written file path. The structured-log fields, the **ESC-DB special-instructions** ([escalation-scim-reference §3](escalation-scim-reference.md)), and the **Description-field metadata plan** ([../description-field-metadata-plan.md](../description-field-metadata-plan.md)) are **three carriers of one canonical metadata model** — the greenfield should emit once and project to all three.

**Sample query requirements (must be answerable from the index):** milestone metrics per pipeline (execution dashboard); executions in a window; failed vs successful; all error codes in a window (needs ErrorCode index); filter pipelines by a specific ErrorCode.

Referenced Jira: `DPL-17622` (logging) — *"issue doesn't exist or you don't have permission"* in the page, i.e. an unresolved/over-restricted link (a data-quality smell, like the broken SCIM refs).

---

## 3. ICDW / Snowflake NFR variant

The Snowflake/ICDW area carries the **same NFR categories** (Alerting, ErrorHandling/Logging, Monitoring, Performance, Operational Readiness, Control-M naming standards, Control-M design standards, custom codes, batch) re-expressed for that framework, with **two added columns**: **Framework Application** (which framework the requirement targets) and **Evidence Required** (what proof closes the item — e.g. *"TDQ issue backtrack… sample attached", "Evidence: SRE approval"*). It confirms the checklist is the firmwide DAT template, **instantiated per framework** with an evidence/sign-off gate.

> Design signal: NFRs are meant to be **evidenced and signed off**, not self-asserted. The greenfield conformance report should produce that evidence automatically where it can (e.g. "structured-log fields present", "1:1 SCIM exists", "naming validates") rather than leaving a human to attest.

---

## 4. Lifecycle / decommissioning (HLT view, `HomeLending-NFR2`)

**Standard decommissioning workflow:** (1) identify jobs/folders; (2) mark **deprecated** in Control-M + update SCIM; (3) remove from QA/DEV via the **planning interface**, remove from PROD via **Autom8** request; (4) export backups; (5) update docs + SCIM to **decommissioned** status; (6) assign **Dev Resolver Group** for decommissioned jobs/folders.

**Compliance validation (key points):** all jobs follow approved naming; SCIM routes incidents to the correct resolver groups; regular lifecycle reviews identify decommission candidates; documentation maintained for audit; capacity management aligned to firmwide policy.

**Cited authorities:** *Control-M Guidelines for HLT AWS Modernization · JPMC Incident Management Standards · Service Operations Capacity Management (TCS-083) · Corporate Policies CP-2120 / CP-2121.* Reference docs: *"Control-M guidelines for HLT AWS", "Remove a Folder from PROD and QA and DEV", "Incident Management — SCIM Standards", "Offboard from HortonWorks Hadoop".*

> Ties to the DAT decommissioning rule ([dat-naming-standard §2b](dat-naming-standard.md)): decommissioned jobs (`%PRPL`→prod) deleted with the **GTI team** after normalization.

---

## 5. Implications for the greenfield (proposed rules)

The NFR catalog converts to checkable conformance. Extending the [standards rules registry](../standards-rules-registry.md) (which now spans **R1–R29**; R21–R25 below originate here):

- **R21 — structured-log fields present.** Job/pipeline emits the §2 mandatory key set; `ErrorCode` indexable. (Auto-evidenceable.)
- **R22 — runbook completeness.** Non-self-heal jobs carry SLO/SLA impact, SOR/downstream, contacts, recovery steps (in Description, per the column-T discipline). Pairs with **R17** (self-heal eligibility).
- **R23 — monitoring binding declared.** Every job declares its monitoring product + dashboard (Grafana/Splunk) so no job is observability-orphaned (the L1-default gap, but for monitoring).
- **R24 — lifecycle/decommission state valid.** Lifecycle designation (`PRPL`/`VERF`/`Decommissioned`) consistent across name, SCIM `EWORKGROUP`, and folder location; decommissioned ⇒ Dev Resolver Group assigned.
- **R25 — NFR evidence gate.** High-risk NFR items (Monitoring, Alerting, Error Handling, Restartability, Escalation matrix) must have evidence before a job is "greenfield-complete" — the ICDW *Evidence Required* discipline generalized.

> Catalog-level principle for the greenfield: **High-risk NFRs are gates, not suggestions.** The eight design principles in [nfr-consistency-and-greenfield.md](nfr-consistency-and-greenfield.md) should be checked against this catalog so none is dropped.

Related: [[project-controlm-escalation-governance]], [[project-description-metadata-plan]], [[project-controlm-remediation-spinoff]]
