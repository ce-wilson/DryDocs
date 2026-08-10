# TRACK RULES — GRAPH (label: see dispatch)

All code-context discovery goes through the Neo4j code graph. You may `Read` a
specific file ONLY after something (the graph, or the task input) named its path.
**Forbidden: Glob, Grep, directory listings, `git grep`, any tree sweep.**

The graph: database `drydocs`, loaded 2026-08-10 from the depgraph snapshot at
commit `bd051ab` (branch main, clean). Schema: `(:Project {project_id:'drydocs'})`,
`(:CodeModule {file_id, name, extension, rel_path})`, `(:CodeDirectory)`, edges
`HAS_MODULE`, `IMPORTS` (module→module), `CONTAINS_ENTRY` (directory tree).
Soft-deleted nodes carry `removed_from_source_at` — filter them out with
`WHERE m.removed_from_source_at IS NULL`.

Connection recipe (run from the repo root; the explicit dotenv path matters —
bare load_dotenv() crashes under `python -`):

```python
import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
with drv.session(database="drydocs") as s:
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS $q "
                     "AND m.removed_from_source_at IS NULL "
                     "RETURN m.file_id LIMIT 25", q="HeroArt"):
        print(rec)
```

Run via `poetry run python <script-file>` (write your query scripts to the
results directory, suffix `-scratch.py`; they count as tool calls, not as
files_read).

Example useful shapes:
- who imports X: `MATCH (a)-[:IMPORTS]->(b:CodeModule {file_id:$f}) RETURN a.file_id`
- what X imports: reverse the pattern
- modules under a directory: `MATCH (d:CodeDirectory {file_id:$dir})-[:CONTAINS_ENTRY*1..]->(m:CodeModule) RETURN m.file_id`

Known shared handicap, stated in advance: the graph is a snapshot at `bd051ab`;
the working tree has moved (docs-only commits since). If a graph answer looks
stale, SAY SO in your report — noticing is graded.
