import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(
    os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
)

with drv.session(database="drydocs") as s:
    for q in ["PORT-MANIFEST", "44-local-registry", "doc-source-registry", "gate-prompts/software-version-context", "backlog.yaml"]:
        print(f"\n--- CONTAINS '{q}' ---")
        recs = s.run(
            "MATCH (m:CodeModule) WHERE m.file_id CONTAINS $q "
            "AND m.removed_from_source_at IS NULL "
            "RETURN m.file_id AS f LIMIT 10",
            q=q,
        )
        for r in recs:
            print(" ", r["f"])

    # who imports / is imported by the two port_preflight.py candidates
    for f in ["drydocs/port_preflight.py", "scripts/port_preflight.py",
              "drydocs/loaders/manual_loads.py", "tests/unit/test_port_manifest.py",
              "tests/unit/test_port_reconcile_guards.py"]:
        print(f"\n=== {f} ===")
        recs = s.run(
            "MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule {file_id:$f}) "
            "WHERE a.removed_from_source_at IS NULL RETURN a.file_id AS f", f=f
        )
        importers = [r["f"] for r in recs]
        print(" imported by:", importers if importers else "(none)")
        recs = s.run(
            "MATCH (a:CodeModule {file_id:$f})-[:IMPORTS]->(b:CodeModule) "
            "WHERE b.removed_from_source_at IS NULL RETURN b.file_id AS f", f=f
        )
        imports = [r["f"] for r in recs]
        print(" imports:", imports if imports else "(none)")

drv.close()
