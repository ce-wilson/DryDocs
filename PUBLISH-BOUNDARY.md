# Publish boundary — the GitHub `.gitignore`-style guard

This repo is **private but sometimes published**. This file is the contract for what may leave
the private boundary onto a public GitHub remote.

**Driven by classification.** What is publishable is decided by each source's **sensitivity
classification** ([`config/classification.yaml`](config/classification.yaml)), not by directory
alone. The directory layout aligns with it, but the per-source `classification` label is
authoritative.

| Classification | Publishable? | Typical home |
|----------------|--------------|--------------|
| **External** | ✅ yes | `reference/`, `external/` |
| **Internal-Public** (Internal-Public Availability) | ✅ yes | `knowledge/` |
| **Internal** | ❌ no — excluded from public push | `internal/` |
| **Internal-Confidential** | ❌ no — excluded + extra protection | `internal/` |

## Publishable (stays in a public push)
- `reference/` — External platform/standard/research knowledge (public by nature)
- `external/` — External captured vendor product docs (public URLs in each `SOURCE-MANIFEST`)
- `knowledge/` — Internal-Public design prose: ontology docs, naming standards (no secrets)
- `config/` — pipeline configuration **by id, not by value** (no real names/secrets)
- `config/taxonomy/` — hierarchy *shape* (no confidential rosters)
- `drydocs/`, `drydocs_core/`, `drydocs_api/`, `drydocs_lineage/`, `drydocs_deepdoc/`,
  `drydocs_remediation/`, `web/`, `tests/`, `docs/`, `scripts/` — code & process docs
  (no embedded secrets)
- `CLAUDE.md`, `README.md`

## Excluded before any public push (classification: Internal or Internal-Confidential)
- `internal/**` — real rosters, schemas, SIDs, server addresses, GHE org names
- `internal-local/**` — gitignored entirely (never committed to ANY remote): real configs,
  raw extracts, screenshot evidence, Confluence sandbox output
- `.env`, `*.env`, credentials, `Neo4j-credentials-*.txt`
- `drydocs/data/samples/**` if it ever contains real (non-synthetic) rows
- Any file whose source is registered `Internal` / `Internal-Confidential` in
  `config/source-registry.yaml`, or any file with real production data values

## Enforcement
1. **Required label** — every source in `config/source-registry.yaml` must carry a
   `classification` (and `source`); `tests/unit/test_classification.py` fails CI otherwise.
2. **`.gitignore` for the public remote** (or a publish script):
   ```
   internal/
   .env
   *.env
   *credentials*
   ```
3. **Pre-publish grep** of the diff for real identifiers:
   ```
   git grep -nE '<real-SID-pattern>|<server-host-pattern>|<ghe-org>'   # tune per environment
   ```

## Rule for agents
Architecture-level only in committed files outside `internal/`. When a task needs a real value,
reference it by a stable id defined in `internal/` — never inline the value. When you register a
new source, set its `classification` — there is no unlabeled default.
