import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
with drv.session(database="drydocs") as s:
    print("--- demoDocs.ts location ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'demoDocs' "
                     "AND m.removed_from_source_at IS NULL RETURN m.file_id"):
        print(rec)
    print("--- any script writing .ts directly (name heuristics) ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id STARTS WITH 'scripts/' AND m.extension = '.py' "
                     "AND m.removed_from_source_at IS NULL RETURN m.file_id ORDER BY m.file_id"):
        print(rec)
    print("--- render_gates.py content path check (imports) ---")
    for rec in s.run("MATCH (a:CodeModule {file_id:'scripts/render_gates.py'})-[:IMPORTS]->(b) RETURN b.file_id"):
        print(rec)
    print("--- test files referencing benchmarkData or underhood ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE (m.file_id CONTAINS 'benchmarkData' OR m.file_id CONTAINS 'underhood') AND m.file_id STARTS WITH 'tests' "
                     "AND m.removed_from_source_at IS NULL RETURN m.file_id"):
        print(rec)
    print("--- web/src/routes UnderTheHoodRoute ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'UnderTheHood' AND m.removed_from_source_at IS NULL RETURN m.file_id"):
        print(rec)
