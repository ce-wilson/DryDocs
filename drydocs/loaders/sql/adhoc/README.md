# Ad-hoc / investigation queries

Versioned home for **investigation, profiling, and QA** SQL — the keepers from
SQL-Developer exploration. **Not part of the ship path:** the loaders reference
`controlm_*.sql` by name, so nothing here is run by the framework.

Convention:
- **Queries only, sanitized — never paste real result rows** (this is the public
  producer repo). Commit the SQL structure; keep results local in SQL Developer.
- One file per theme; label each query with the question it answers.
- New directory → **clean-add** on sync (ports wholesale, no collision).

Workflow: explore in SQL Developer → if a query is worth keeping, drop it here
(sanitized) → it's now versioned, portable, and rerunnable. Promote a query to
`drydocs/loaders/sql/` only when it becomes part of the ingestion pipeline.
