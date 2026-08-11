import os
from dotenv import load_dotenv
from neo4j import GraphDatabase

load_dotenv(r"C:\coding\projects\DryDocs\.env")
drv = GraphDatabase.driver(
    os.environ["NEO4J_URI"], auth=(os.environ["NEO4J_USER"], os.environ["NEO4J_PASSWORD"])
)

with drv.session(database="drydocs") as s:
    for q in ["code-graph-review-plan", "tech-debt/SKILL", "issue-driven-capture-loop",
              "servicenow-replica-evidence", "port-prompt", "business-application.yaml"]:
        print(f"\n--- CONTAINS '{q}' ---")
        recs = s.run(
            "MATCH (m:CodeModule) WHERE m.file_id CONTAINS $q "
            "AND m.removed_from_source_at IS NULL "
            "RETURN m.file_id AS f LIMIT 10",
            q=q,
        )
        found = [r["f"] for r in recs]
        if not found:
            print("  (no match)")
        for f in found:
            print(" ", f)

    for f in ["tests/unit/test_code_graph_review_plan.py", "docs/reviews/code-graph-review-plan.md"]:
        print(f"\n=== {f} ===")
        recs = s.run(
            "MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule {file_id:$f}) "
            "WHERE a.removed_from_source_at IS NULL RETURN a.file_id AS f", f=f
        )
        print(" imported by:", [r["f"] for r in recs] or "(none)")
        recs = s.run(
            "MATCH (a:CodeModule {file_id:$f})-[:IMPORTS]->(b:CodeModule) "
            "WHERE b.removed_from_source_at IS NULL RETURN b.file_id AS f", f=f
        )
        print(" imports:", [r["f"] for r in recs] or "(none)")

drv.close()
