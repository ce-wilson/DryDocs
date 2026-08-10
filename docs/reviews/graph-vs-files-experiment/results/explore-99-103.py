import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))

with drv.session(database="drydocs") as s:
    # Query 1: Port manifest and port infrastructure
    print("=== Query 1: Port infrastructure files ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'PORT' OR m.file_id CONTAINS 'port')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name, m.extension
        ORDER BY m.file_id
        LIMIT 20
    """):
        print(rec)

    # Query 2: Markdown fence and test related
    print("\n=== Query 2: Markdown fence test modules ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'markdown' OR m.file_id CONTAINS 'test_markdown')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name, m.extension
    """):
        print(rec)

    # Query 3: Review plan and code graph review
    print("\n=== Query 3: Review plan modules ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'review' OR m.file_id CONTAINS 'code-graph')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name, m.extension
        LIMIT 15
    """):
        print(rec)

    # Query 4: Gate infrastructure and ontology vocabulary
    print("\n=== Query 4: Gate and ontology vocabulary modules ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'gate' OR m.file_id CONTAINS 'relationship_vocabulary' OR m.file_id CONTAINS 'ontology')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name, m.extension
        LIMIT 20
    """):
        print(rec)

    # Query 5: Config and registry related
    print("\n=== Query 5: Config and registry modules ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'config/' OR m.file_id CONTAINS 'registry')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name, m.extension
        LIMIT 20
    """):
        print(rec)

drv.close()
