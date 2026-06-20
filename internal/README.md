# internal/ — CONFIDENTIAL internal data (stripped on publish)

Company-confidential material that must **never** appear when this repo is published.
Provenance is internal AND the content is sensitive (real identifiers, rosters, schemas).

> Distinct from `knowledge/` — that holds internal *design prose* (ontology docs, naming
> standards) which is publishable. `internal/` holds the **data** that is not.

## What belongs here
| Subdir | Contents |
|--------|----------|
| `org/` | Real LOB→Product→Team rosters, team names, people, SEAL ownership records |
| `schemas/` | Real Oracle schema/table/object names, SIDs, connection details |
| `secrets/` | Never commit real secrets even here — use `.env`; this is for references/notes only |

## Publish discipline
- This directory is listed in [`../PUBLISH-BOUNDARY.md`](../PUBLISH-BOUNDARY.md) and excluded
  from any public push.
- The `config/` layer references internal data **by stable id**, not by value — e.g.
  `precedence.yaml` points at `internal/org/` but commits no real names.
- If you are about to write a real SID, server address, GHE org name, or production data value
  anywhere outside `internal/`, STOP — that is the publish-boundary violation this structure
  exists to prevent.

This directory is intentionally near-empty in the public/template state.
