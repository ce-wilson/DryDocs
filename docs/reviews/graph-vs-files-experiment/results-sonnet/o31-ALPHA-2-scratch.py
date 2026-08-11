import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
with drv.session(database="drydocs") as s:
    print("--- who imports benchmarkData.ts ---")
    for rec in s.run("MATCH (a)-[:IMPORTS]->(b:CodeModule {file_id:'web/src/underhood/benchmarkData.ts'}) "
                     "WHERE a.removed_from_source_at IS NULL RETURN a.file_id"):
        print(rec)
    print("--- what benchmarkData.ts imports ---")
    for rec in s.run("MATCH (a:CodeModule {file_id:'web/src/underhood/benchmarkData.ts'})-[:IMPORTS]->(b) "
                     "RETURN b.file_id"):
        print(rec)
    print("--- modules under knowledge/upgrade-plans/p0-benchmark ---")
    for rec in s.run("MATCH (d:CodeDirectory {file_id:'knowledge/upgrade-plans/p0-benchmark'})-[:CONTAINS_ENTRY*1..]->(m:CodeModule) "
                     "WHERE m.removed_from_source_at IS NULL RETURN m.file_id ORDER BY m.file_id"):
        print(rec)
    print("--- modules under knowledge/upgrade-plans ---")
    for rec in s.run("MATCH (d:CodeDirectory {file_id:'knowledge/upgrade-plans'})-[:CONTAINS_ENTRY*1..]->(m:CodeModule) "
                     "WHERE m.removed_from_source_at IS NULL RETURN m.file_id ORDER BY m.file_id"):
        print(rec)
    print("--- who imports benchmark_p0.py ---")
    for rec in s.run("MATCH (a)-[:IMPORTS]->(b:CodeModule {file_id:'knowledge/upgrade-plans/p0-benchmark/benchmark_p0.py'}) "
                     "WHERE a.removed_from_source_at IS NULL RETURN a.file_id"):
        print(rec)
    print("--- what benchmark_p0.py imports ---")
    for rec in s.run("MATCH (a:CodeModule {file_id:'knowledge/upgrade-plans/p0-benchmark/benchmark_p0.py'})-[:IMPORTS]->(b) "
                     "RETURN b.file_id"):
        print(rec)
    print("--- scripts/render_ modules (regen scripts convention) ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id STARTS WITH 'scripts/render_' "
                     "AND m.removed_from_source_at IS NULL RETURN m.file_id ORDER BY m.file_id"):
        print(rec)
    print("--- all scripts/ dir top level ---")
    for rec in s.run("MATCH (d:CodeDirectory {file_id:'scripts'})-[:CONTAINS_ENTRY]->(m:CodeModule) "
                     "WHERE m.removed_from_source_at IS NULL RETURN m.file_id ORDER BY m.file_id"):
        print(rec)
