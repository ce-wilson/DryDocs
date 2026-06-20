# vendor/ — external vendor reference that **supports** the project

Third-party / vendor material used to *build and understand* DryDocs. This is
**reference**, not graph content: it documents the external systems DryDocs
ingests from. None of it is loaded into Neo4j directly.

Contrast with [`../knowledge/`](../knowledge/README.md), which holds the
**internal** unstructured knowledge that *defines* the graph.

## Contents

| Path | Vendor | What it is |
|------|--------|-----------|
| `bmc-controlm/` | BMC | Control-M API/folder/job/parameter reference + the raw `bmc-*.txt` source. `SOURCE-MANIFEST.md` records provenance. |

## Adding vendor material

One subdirectory per vendor product (`bmc-controlm/`, future `oracle/`, …).
Keep a `SOURCE-MANIFEST.md` noting where each doc came from and its version, so
it's clear this is captured vendor documentation, not original DryDocs content.
