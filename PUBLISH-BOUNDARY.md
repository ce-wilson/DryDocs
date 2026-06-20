# Publish boundary — what is public vs confidential

This repo is **private but sometimes published**. This file is the contract for what may leave
the private boundary.

## Publishable (stays in a public push)
- `reference/` — external platform/standard/research knowledge (public by nature)
- `external/` — captured vendor product docs (public)
- `knowledge/` — DryDocs design prose: ontology docs, naming standards (no secrets)
- `config/` — pipeline configuration **by id, not by value** (no real names/secrets)
- `config/taxonomy/` — hierarchy *shape* (no confidential rosters)
- `drydocs/`, `tests/`, `docs/`, `scripts/` — code & process docs (no embedded secrets)
- `CLAUDE.md`, `README.md`

## Confidential (stripped before any public push)
- `internal/**` — real rosters, schemas, SIDs, server addresses, GHE org names
- `.env`, `*.env`, credentials, `Neo4j-credentials-*.txt`
- `drydocs/data/samples/**` if it ever contains real (non-synthetic) rows
- Any file with real production data values

## Enforcement
Add to `.gitignore` for the public remote (or a publish script):
```
internal/
.env
*.env
*credentials*
```
And before publishing, grep the diff for real identifiers:
```
git grep -nE '<real-SID-pattern>|<server-host-pattern>|<ghe-org>'   # tune patterns per environment
```

## Rule for agents
Architecture-level only in committed files outside `internal/`. When a task needs a real value,
reference it by a stable id defined in `internal/` — never inline the value.
