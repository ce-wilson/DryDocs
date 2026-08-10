import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))

with drv.session(database="drydocs") as s:
    # Query 1: Imports of test_backlog.py
    print("=== Query 1: Modules importing test_backlog.py ===")
    for rec in s.run("""
        MATCH (a)-[:IMPORTS]->(b:CodeModule {file_id: 'tests/unit/test_backlog.py'})
        WHERE b.removed_from_source_at IS NULL
        RETURN a.file_id
    """):
        print(rec)

    # Query 2: Modules imported by test_backlog.py
    print("\n=== Query 2: Modules imported BY test_backlog.py ===")
    for rec in s.run("""
        MATCH (a:CodeModule {file_id: 'tests/unit/test_backlog.py'})-[:IMPORTS]->(b)
        WHERE a.removed_from_source_at IS NULL AND b.removed_from_source_at IS NULL
        RETURN b.file_id
    """):
        print(rec)

    # Query 3: Software registry loader imports
    print("\n=== Query 3: software_registry.py imports ===")
    for rec in s.run("""
        MATCH (a:CodeModule {file_id: 'drydocs/loaders/software_registry.py'})-[:IMPORTS]->(b)
        WHERE a.removed_from_source_at IS NULL AND b.removed_from_source_at IS NULL
        RETURN b.file_id
        LIMIT 20
    """):
        print(rec)

    # Query 4: Port preflight module
    print("\n=== Query 4: port_preflight.py and related ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE m.file_id CONTAINS 'preflight'
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name
    """):
        print(rec)

    # Query 5: Cypher modules under drydocs/loaders
    print("\n=== Query 5: Cypher files in loaders ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE m.file_id CONTAINS 'drydocs/loaders/cypher'
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id
        LIMIT 30
    """):
        print(rec)

drv.close()
