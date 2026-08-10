import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))

with drv.session(database="drydocs") as s:
    # Find markdown fence test
    print("=== Query: markdown fence test ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE m.file_id CONTAINS 'test_markdown'
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id
    """):
        print(rec)

    # Find all test files
    print("\n=== Query: test_*.py files that might be relevant ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE m.file_id CONTAINS 'tests/unit/test_'
        AND m.name CONTAINS 'test_'
        AND m.extension = '.py'
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id
        ORDER BY m.file_id
        LIMIT 30
    """):
        print(rec)

drv.close()
