import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
with drv.session(database="drydocs") as s:
    print("--- benchmarkData ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'benchmarkData' "
                     "AND m.removed_from_source_at IS NULL "
                     "RETURN m.file_id, m.rel_path"):
        print(rec)
    print("--- underhood / under-the-hood / under_hood ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE (m.file_id CONTAINS 'underhood' OR m.file_id CONTAINS 'under-the-hood' OR m.file_id CONTAINS 'under_hood') "
                     "AND m.removed_from_source_at IS NULL "
                     "RETURN m.file_id, m.rel_path ORDER BY m.file_id"):
        print(rec)
    print("--- docmeta ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'docmeta' "
                     "AND m.removed_from_source_at IS NULL "
                     "RETURN m.file_id, m.rel_path ORDER BY m.file_id"):
        print(rec)
    print("--- harness ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'harness' "
                     "AND m.removed_from_source_at IS NULL "
                     "RETURN m.file_id, m.rel_path ORDER BY m.file_id"):
        print(rec)
    print("--- benchmark (general) ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'benchmark' "
                     "AND m.removed_from_source_at IS NULL "
                     "RETURN m.file_id, m.rel_path ORDER BY m.file_id"):
        print(rec)
