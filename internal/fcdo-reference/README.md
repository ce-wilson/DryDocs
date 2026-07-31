# internal/fcdo-reference — FCDO Data Publishing Frameworks capture

**Classification: Internal** (confidential handling — J23 collapse 2026-07-31) — contains real employee names, internal
Confluence URLs, and internal org detail. Never leaves `internal/`; excluded from any
public push (`PUBLISH-BOUNDARY.md`).

## What this is

Screenshot-transcription capture (2026-07-30) of the **JPMC Firmwide CDAO / Data
Publishing Strategy team (FCDO)** Confluence space `DATAPUBSTRATEGY` ("Firmwide Data
Publishing Frameworks"), plus a few non-Confluence captures (CCB governance reference
data, the `fcdo-ontology-builder` skill, ServiceNow/SEAL ER diagrams). 117 screenshots,
22 sources. Source screenshots live locally at `C:\coding\@SCREEN-SHOTS` (not in the repo).

| File | Contents |
|---|---|
| `CONFLUENCE-TRANSCRIPT.md` | The unsplit master (all 22 sources, with per-page gap notes) |
| `TRANSCRIPT-1-ONTOLOGY.md` | Ontology design recommendations, upper-ontology bridging, `fcdo-ontology-builder` skill + review session |
| `TRANSCRIPT-2-TAXONOMY.md` | Taxonomy Framework (SKOS+DCMI profile) + live CCB taxonomy reference data |
| `TRANSCRIPT-3-THOUGHTS-VOCAB.md` | Thought pieces, AI-agent discussions, AWM Data Mesh vocabulary |
| `TRANSCRIPT-4-MISC.md` | Framework specs: Identifiers (JDI), Telemetry, Data Mapping, Provenance, Schema Metadata, Business Processes, Data Authority, People & Organizations, Technical Backlog |

## Trust & completeness

- Transcription is **verbatim from screenshots** (source typos preserved) but the
  capture is partial — treat as tier GROUNDED, not VERBATIM. Each file ends with a
  "Gaps in this set" section; the master's "Gaps & Follow-ups" is authoritative.
  **Absence from the transcript is NOT absence from their standard.**
- Known holes that matter for the alignment work: **Descriptive Metadata Framework**
  (the shared identifier/title/description envelope — highest-value recapture),
  **Data Quality Framework**, **Data Contracts Framework (DPROD)**, and most of the
  Taxonomy Framework's normative property tables (§1–§4, §5.1.1+).

## Recapture path (registered)

Registered as doc corpus **`fcdo-frameworks`** in `config/doc-source-registry.yaml`
(`connector: confluence`, `refresh: on-demand`) so the docmeta pipeline can scrape the
live pages — company-network only. A direct scrape supersedes these transcripts and
upgrades trust to VERBATIM. Page IDs for the scrape target list (space
`confluence.prod.aws.jpmchase.net/confluence/spaces/DATAPUBSTRATEGY`):

| Page | ID |
|---|---|
| Identifiers Specification | 5574548071 |
| Telemetry Framework | 5772894333 |
| Data Mapping Framework – Draft | 5816635920 |
| Provenance Framework | 5567744239 |
| [WIP] Provenance CDAO Framework | 6194465802 |
| Schema Metadata Framework | 5567745346 |
| Business Processes Metadata Framework | 5762464960 |
| Data Authority Metadata Framework | 5899885596 |
| People and Organizations Framework | 6030480492 |
| Taxonomy Framework | 5772894415 |
| Thought Pieces (index; child pages individually) | 5140788914 |
| Connecting a Physical Data Model to an Upper Ontology | 5648554621 |
| AI & Agent Native Data Benchmarks | 5938531925 |
| AI Agents for Managing Data Access | 6206552010 |
| Technical Backlog | 5153183917 |
| Our Vocabulary (space DATAMESHANALYTICS) | 4373543268 |

Never-captured siblings to include in the scrape: Descriptive Metadata Framework,
Data Product Framework, Usage Rights Framework, Data Quality Framework, Date and Time
Framework, Postal Address Framework, Party Identifier Framework, Knowledge Base
Framework, Data Contracts Framework (DPROD), Securities Framework, Companies Framework,
Process/Council and Working Groups, vteam Agent Ready Data.

## What to read next

The gap analysis and adoption plan derived from this capture:
[`ALIGNMENT-PLAN.md`](ALIGNMENT-PLAN.md).
