import os
from dotenv import load_dotenv
from neo4j import GraphDatabase
load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))
with drv.session(database="drydocs") as s:
    print("--- MODULE_MAP.md location ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'MODULE_MAP' AND m.removed_from_source_at IS NULL RETURN m.file_id"):
        print(rec)
    print("--- ARCHITECTURE.md location ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'ARCHITECTURE' AND m.removed_from_source_at IS NULL RETURN m.file_id"):
        print(rec)
    print("--- CHANGELOG-ish files ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE toLower(m.file_id) CONTAINS 'changelog' AND m.removed_from_source_at IS NULL RETURN m.file_id"):
        print(rec)
    print("--- backlog.yaml location ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id CONTAINS 'backlog.yaml' AND m.removed_from_source_at IS NULL RETURN m.file_id"):
        print(rec)
    print("--- docmeta-component.md (upgrade plan the O31 item likely traces to) ---")
    for rec in s.run("MATCH (m:CodeModule) WHERE m.file_id = 'knowledge/upgrade-plans/docmeta-component.md' RETURN m.file_id"):
        print(rec)
