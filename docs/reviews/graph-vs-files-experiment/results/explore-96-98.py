import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))

with drv.session(database="drydocs") as s:
    # Query 1: Find test_backlog.py and related testing modules
    print("=== Query 1: test_backlog.py and test modules ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE m.file_id CONTAINS 'test_backlog'
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name, m.extension
        LIMIT 10
    """):
        print(rec)

    # Query 2: Find loader modules
    print("\n=== Query 2: Loader modules ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE m.rel_path CONTAINS 'loaders'
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name, m.extension
        LIMIT 20
    """):
        print(rec)

    # Query 3: Software registry related
    print("\n=== Query 3: Software registry modules ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'software' OR m.name CONTAINS 'software')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name, m.extension
        LIMIT 15
    """):
        print(rec)

drv.close()
