import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(os.environ["NEO4J_URI"],
    auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"]))

with drv.session(database="drydocs") as s:
    # Query 1: Code review plan and render design doc
    print("=== Query 1: Review plan and render design doc ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'code-graph-review-plan'
               OR m.file_id CONTAINS 'render_design_doc'
               OR m.file_id CONTAINS 'render_board')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id, m.name
    """):
        print(rec)

    # Query 2: Script modules that might render documentation
    print("\n=== Query 2: Scripts directory ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE m.rel_path CONTAINS 'scripts/'
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id
        LIMIT 20
    """):
        print(rec)

    # Query 3: Design doc templates and outline validation
    print("\n=== Query 3: Design doc and outline validation ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'drydocs/design'
               OR m.file_id CONTAINS 'outline'
               OR m.file_id CONTAINS 'design_doc')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id
    """):
        print(rec)

    # Query 4: drydocs-docgen related modules
    print("\n=== Query 4: Documentation generation modules ===")
    for rec in s.run("""
        MATCH (m:CodeModule)
        WHERE (m.file_id CONTAINS 'drydocs/design'
               OR m.file_id CONTAINS 'docgen'
               OR m.file_id CONTAINS 'markdown')
        AND m.removed_from_source_at IS NULL
        RETURN m.file_id
        LIMIT 15
    """):
        print(rec)

drv.close()
