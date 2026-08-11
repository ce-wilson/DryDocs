import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
with drv.session(database="drydocs") as s:
    print("--- test files mentioning generated/registry/drift ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id STARTS WITH 'tests/unit/test_' AND "
                     "(m.file_id CONTAINS 'registry' OR m.file_id CONTAINS 'generated' OR m.file_id CONTAINS 'board' OR m.file_id CONTAINS 'gates' OR m.file_id CONTAINS 'enforcement' OR m.file_id CONTAINS 'load_map') "
                     "AND m.removed_from_source_at IS NULL RETURN m.file_id ORDER BY m.file_id"):
        print(rec)
    print("--- what imports benchmark_p0_results.json (none expected, data file) ---")
    print("--- what imports render_software_registry.py ---")
    for rec in s.run("MATCH (a)-[:IMPORTS]->(b:CodeModule {file_id:'scripts/render_software_registry.py'}) "
                     "WHERE a.removed_from_source_at IS NULL RETURN a.file_id"):
        print(rec)
    print("--- web/src/generated dir contents ---")
    for rec in s.run("MATCH (d:CodeDirectory {file_id:'web/src/generated'})-[:CONTAINS_ENTRY*1..]->(m:CodeModule) "
                     "WHERE m.removed_from_source_at IS NULL RETURN m.file_id ORDER BY m.file_id"):
        print(rec)
    print("--- render_board.py imports (entry point orchestrator) ---")
    for rec in s.run("MATCH (a:CodeModule {file_id:'scripts/render_board.py'})-[:IMPORTS]->(b) RETURN b.file_id"):
        print(rec)
    print("--- who imports drydocs_docmeta modules (docmeta package usage) ---")
    for rec in s.run("MATCH (a)-[:IMPORTS]->(b:CodeModule) WHERE b.file_id STARTS WITH 'drydocs_docmeta/' "
                     "AND a.removed_from_source_at IS NULL RETURN DISTINCT a.file_id ORDER BY a.file_id"):
        print(rec)
