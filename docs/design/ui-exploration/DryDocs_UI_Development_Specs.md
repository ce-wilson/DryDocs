# DryDocs UI Development Specifications

This document contains the layout, content, and visual specifications for four (4) application pages of the DryDocs DevOps Knowledge Graph platform. These specifications are designed to be ingested by an LLM to generate React components or HTML/CSS layouts.

---

## Global Application Shell (Applies to all pages)

**Layout Structure:**
* **Sidebar (Left, 250px fixed):**
    * Brand Logo: DryDocs (Red sphere with revolving rectangular shapes).
    * Navigation Links: Global Enterprise View (Active on Page 1), Cards Tower (Active on Page 2), Home Lending Tower (Active on Page 3), Auto Tower (Active on Page 4).
    * Bottom links: Settings, User Profile (Logged in as: Chad Wilson), Logout.
* **Top Header (Fixed height, 64px):**
    * Breadcrumbs indicating current view.
    * Global Search Bar (Search nodes, servers, jobs).
    * Environment Toggle: [ Prod | UAT | Dev ].
* **Main Content Area (Fluid width, scrollable):**
    * Split into two vertical sections:
        * **Top 50-60%:** Interactive Lineage Graph View (Visual).
        * **Bottom 40-50%:** Data Frames / Detail Tables (Tabular).

**Visual Language (Dark Mode / Schematic):**
* **Background:** Dark slate/navy (`#0f172a` or similar) with subtle grid lines.
* **Accents:** Cyber-teal, neon green (healthy), amber (warning), soft red (error).
* **Typography:** Monospace for technical data (e.g., Fira Code), sans-serif for UI elements (e.g., Inter).
* **Components:** Glassmorphism panels for data tables, neon-outlined nodes for graphs.

---

## Page 1: Global Enterprise View (Google Cloud Centric)

**Intent:** Show a high-level data flow encompassing connected enterprise Google Cloud products and their integration points.

**1. Top Section: Lineage Graph (Hero Visual)**
* **Style:** A sweeping, complex network graph zooming out to show macro-level architecture.
* **Key Nodes (Icons/Labels):**
    * On-Premises Data Center (Origin).
    * Google Cloud Pub/Sub (Ingestion stream).
    * Google Cloud Dataflow (Streaming analytics).
    * Google Kubernetes Engine (GKE) (Microservices hosting).
    * Google BigQuery (Enterprise Data Warehouse).
    * Looker (BI & Reporting).
* **Connections:** Flowing lines with animated "data packets" (dots moving along paths) indicating live data movement.

**2. Bottom Section: Data Frames (Tabular Data)**
* **Tabs:** [ System Health ] | [ Cloud Spend ] | [ Recent Incidents ]
* **Active Tab (System Health):**
    * Table Headers: `Service`, `Region`, `Uptime (90d)`, `Active Nodes`, `Throughput (GB/s)`, `Status`.
    * Sample Row 1: `GCP BigQuery`, `us-central1`, `99.99%`, `Auto-scaled`, `1.2`, `[Healthy - Green]`.
    * Sample Row 2: `Dataflow Pipeline (Ingest)`, `us-central1`, `99.95%`, `12`, `0.8`, `[Healthy - Green]`.

---

## Page 2: Tower - Cards

**Intent:** Drill-down into the specific technologies supporting the Credit Card business unit.

**1. Top Section: Lineage Graph**
* **Style:** Directed Acyclic Graph (DAG) flowing left-to-right.
* **Key Nodes:**
    * Source: `Oracle RAC (Exadata)` - Node color: Blue.
    * ETL Process: `Informatica PowerCenter` - Node color: Orange.
    * Storage/Target: `AWS S3 (Raw Zone)` -> `AWS Snowflake (Curated)` - Node color: Light Blue/White.
* **Connections:** Solid lines. The link between Informatica and AWS S3 should show a "Last sync: 5 mins ago" badge.

**2. Bottom Section: Data Frames**
* **Tabs:** [ ETL Job Executions ] | [ Database Connections ] | [ Schema Drifts ]
* **Active Tab (ETL Job Executions):**
    * Table Headers: `Job ID`, `Workflow Name`, `Source`, `Target`, `Start Time`, `Duration`, `Status`.
    * Sample Row 1: `CRD-EXT-001`, `wf_daily_transactions`, `Oracle (PRD)`, `AWS S3`, `02:00:00 UTC`, `45m 12s`, `[Success - Green]`.
    * Sample Row 2: `CRD-LOD-005`, `wf_load_snowflake`, `AWS S3`, `Snowflake`, `02:50:00 UTC`, `12m 04s`, `[Success - Green]`.

---

## Page 3: Tower - Home Lending

**Intent:** Drill-down into the Mortgage/Home Lending data pipeline.

**1. Top Section: Lineage Graph**
* **Style:** Tree-like layout showing data converging from multiple sources into a central lake.
* **Key Nodes:**
    * Sources: `SQL Server (Loan Origination)`, `External SFTP (Credit Bureaus)`. (Note: Built around pull-based batch architecture without an API layer).
    * ETL Process: `PySpark (EMR Cluster)` - Node color: Spark Yellow/Blue.
    * Storage/Target: `AWS S3 (Delta Lake)` -> `AWS Snowflake (Reporting Views)`.
* **Connections:** Lines from SQL Server and secure SFTP file drops merging into the PySpark node, then fanning out to Snowflake.

**2. Bottom Section: Data Frames**
* **Tabs:** [ Spark Cluster Metrics ] | [ Data Quality Rules ] | [ Pipeline Lineage ]
* **Active Tab (Spark Cluster Metrics):**
    * Table Headers: `Cluster ID`, `Job Name`, `Executor Cores`, `Memory Util`, `Data Processed`, `State`.
    * Sample Row 1: `emr-hl-prod-99`, `pyspark_loan_agg`, `32`, `85%`, `4.5 TB`, `[Running - Blue pulsing]`.
    * Sample Row 2: `emr-hl-prod-102`, `pyspark_credit_score_sync`, `16`, `40%`, `500 GB`, `[Completed - Green]`.

---

## Page 4: Tower - Auto

**Intent:** Drill-down into the Auto Finance legacy-to-cloud data pipeline.

**1. Top Section: Lineage Graph**
* **Style:** Highlighted critical path graph, showing a complex legacy transition.
* **Key Nodes:**
    * Source: `Teradata (Legacy EDW)` - Node color: Dark Orange.
    * ETL Process: `Ab Initio (Co>Operating System)` - Node color: Purple.
    * Storage/Target: `AWS S3 (Landing)` -> `AWS Snowflake (Auto Mart)`.
* **Connections:** Thick lines indicating heavy batch volumes. One connection (e.g., Teradata to Ab Initio) should have a warning icon indicating "High Latency".

**2. Bottom Section: Data Frames**
* **Tabs:** [ Batch Schedules ] | [ Error Logs ] | [ Volume Metrics ]
* **Active Tab (Batch Schedules):**
    * Table Headers: `Job Group`, `Graph Name`, `Trigger`, `Expected SLA`, `Actual Completion`, `Status`.
    * Sample Row 1: `AUTO_DLY_BATCH`, `Extract_Teradata_Core`, `01:00 EST`, `03:00 EST`, `04:15 EST`, `[SLA Missed - Amber/Warning]`.
    * Sample Row 2: `AUTO_DLY_BATCH`, `Load_Snowflake_Mart`, `Dependency`, `05:00 EST`, `Pending`, `[Waiting - Grey]`.
