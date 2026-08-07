# AWS MWAA — internal implementation documentation (locator)

> **Classification: Internal.** This file exists because the value below is a real internal
> URL — an internal host plus an internal path — and `PUBLISH-BOUNDARY.md` puts real server
> addresses and internal URLs in `internal/**` and nowhere else. Everything outside this
> directory references this file **by path**, never by value, which is the standing
> `config/`-references-internal-data-by-stable-id rule from `internal/README.md`.

## The locator

| Field | Value |
|---|---|
| **Stable id** | `airflow:internal-implementation-docs` |
| **What it documents** | the firm's own AWS Managed Workflows for Apache Airflow (MWAA) implementation — deployment, conventions, onboarding |
| **URL** | `https://jpmchase.net/docs/ais/orchestration/mwaa/` |
| **Recorded** | 2026-08-07, user-supplied |
| **Verified reachable** | ❌ not checked — this repo has no access to the internal network. Treat as recorded, not validated. |

## Why this is NOT the `publisher_url` already in the registry

Two different facts that both look like "the Airflow URL," and conflating them is the
mistake this file prevents:

| | Answers | Where it lives | Classification |
|---|---|---|---|
| `publisher_url: https://apache.org/` | who **publishes** the software (ADR 0004: vendor = the brand) | `config/taxonomy/software-registry.yaml`, on the `apache` **vendor** row | Internal-Public — publishable |
| the URL above | where **our own implementation** is documented | here | Internal — never published |

The vendor row is correct as it stands and needs no change. Apache Software Foundation
publishes Airflow; the firm operates a managed deployment of it. A vendor's publisher URL is
not a place to record a tenant's runbook, and `software-registry.yaml` is Internal-Public, so
the value could not go there even if the field fit.

Note also the existing registry disposition, which this locator does **not** disturb: MWAA is
deliberately **not** a separate `SoftwareProduct` — stock Airflow object model, AWS-managed
deployment (registered 2026-07-14 for the `airflow-crosswalk` gate, which the SME signed the
same day). This file records where the deployment is *documented*; it makes no claim that the
deployment is a distinct product.

## The `ais` path segment is a LOCATION, not the AIS class layer

Recorded explicitly so nobody re-opens a closed question on the strength of a string match.

The `ais` in the URL path is a segment of the internal documentation site's own
organization — where the page sits. It is **unrelated** to the `Ais*` ontology class layer,
which is a **company-local** artifact of the company-side 2026-06-29 AIS gate, is
**T12-SUPERSEDED** (2026-07-21), and which the producer repo never had at all: C12 took the
direct route and registered `:SchedulerKind` into the software-registry model with no `Ais*`
layer ever existing here (see `docs/port-ais-supplement-company-prompt.md`).

Saving a documentation URL neither revives that layer nor reopens its disposition. This is the
same two-things-one-spelling trap J32 made a standing rule after `group` meant two different
fields — read the segment's job, not its spelling.

## How to reference this

- `config/source-registry.yaml` → the `airflow` **system** row's `locator.internal_docs`
  carries the path to this file. The URL itself never appears there; that row is committed
  outside `internal/`.
- Anything else that needs it cites the stable id `airflow:internal-implementation-docs` or
  this file's path.
- **If the Airflow source ever activates** (today it is a crosswalk-only placeholder with no
  DAG-export feed), this locator is the starting point for the `SOURCE-MANIFEST.md` that
  `external/orchestration/airflow/README.md` step 1 requires — it should answer the MWAA
  environment, the Airflow version actually deployed, and how DAG metadata can be exported.
