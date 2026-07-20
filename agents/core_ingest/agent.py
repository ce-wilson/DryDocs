"""core_ingest — agent flow for the DryDocs core module when ingesting new data.

LLM agent (needs GOOGLE_API_KEY in agents/.env). Read-only against the graph:
it inspects what is already loaded and advises how a new source should land
(taxonomy first, then ontology — CLAUDE.md section 1). Actual graph writes stay
with the drydocs-load pipeline + HITL gate, never with a chat agent.
"""

import os

from google.adk.agents.llm_agent import Agent

from common.neo4j_tool import graph_schema, read_cypher

root_agent = Agent(
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    name="core_ingest",
    description="DryDocs core-module ingestion assistant: inspects the knowledge graph and advises how new sources should be ingested.",
    instruction="""You assist with ingesting new data into the DryDocs knowledge graph
(production-support graph for D&A batch processing: Control-M jobs, applications,
owners, dependencies).

Ground every answer in the live graph: use graph_schema to see what exists, and
read_cypher to inspect current nodes/relationships. You are READ-ONLY — when a
change is needed, describe the exact loader step or Cypher the human should run
through the DryDocs pipeline instead of pretending to run it. Follow the DryDocs
layering: classify new data as taxonomy first; relationship semantics are an
ontology decision that goes through the HITL gate.""",
    tools=[graph_schema, read_cypher],
)
