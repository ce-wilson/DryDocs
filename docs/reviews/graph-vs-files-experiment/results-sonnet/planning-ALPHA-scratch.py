import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(
    os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
)

queries = [
    "test_backlog",
    "port_reconcile",
    "port_preflight",
    "render_board",
    "test_markdown_fences",
    "code_graph_review_plan",
    "manual_loads",
    "software_registry",
    "seal_applications",
    "seal_contacts",
    "test_port_preflight",
    "manifest",
]

with drv.session(database="drydocs") as s:
    # sanity: node counts
    rec = s.run(
        "MATCH (m:CodeModule) WHERE m.removed_from_source_at IS NULL RETURN count(m) AS n"
    ).single()
    print("LIVE CodeModule count:", rec["n"])
    rec = s.run("MATCH (m:CodeModule) RETURN count(m) AS n").single()
    print("TOTAL CodeModule count (incl removed):", rec["n"])
    rec = s.run(
        "MATCH (m:CodeModule) WHERE m.removed_from_source_at IS NULL AND m.extension <> '.py' "
        "RETURN DISTINCT m.extension AS ext, count(*) AS n ORDER BY n DESC"
    )
    print("Non-.py extensions present:")
    for r in rec:
        print(" ", r["ext"], r["n"])

    for q in queries:
        print(f"\n--- CONTAINS '{q}' ---")
        recs = s.run(
            "MATCH (m:CodeModule) WHERE m.file_id CONTAINS $q "
            "AND m.removed_from_source_at IS NULL "
            "RETURN m.file_id AS f LIMIT 25",
            q=q,
        )
        found = [r["f"] for r in recs]
        if not found:
            print("  (no match)")
        for f in found:
            print(" ", f)

drv.close()
