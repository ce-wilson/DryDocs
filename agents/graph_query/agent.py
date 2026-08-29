"""graph_query — the BASIC flow, no LLM involved.

A deterministic custom agent: the user message is treated as a Cypher read
query (empty message = the default C4-component query) and the rows come back
as one JSON event. This proves the full React -> adk api_server -> Neo4j path
without needing a GOOGLE_API_KEY, and gives a stable target for memory-leak
runs (no model variance between requests).
"""

import json
from collections.abc import AsyncGenerator

from common.neo4j_tool import read_cypher
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

# The self-documentation code graph as the gate RULED it, not as G33 first
# proposed it: gate self-documentation-code-graph §C1 picked :CodeModule and
# explicitly rejected option (b) :CodeFile, and §D1 named the edge :IMPORTS.
# The loader writes snake_case `rel_path`. This query trailed all three and
# returned zero rows against a populated graph.
DEFAULT_QUERY = (
    "MATCH (a:CodeModule)-[:IMPORTS]->(b:CodeModule) "
    "RETURN a.rel_path AS source, b.rel_path AS target LIMIT 25"
)


class GraphQueryAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        query = DEFAULT_QUERY
        user_content = getattr(ctx, "user_content", None)
        if user_content and user_content.parts:
            text = (user_content.parts[0].text or "").strip()
            if text:
                query = text
        payload = {"query": query, **read_cypher(query)}
        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=json.dumps(payload, indent=2, default=str))],
            ),
        )


root_agent = GraphQueryAgent(
    name="graph_query",
    description="Runs a read-only Cypher query against the local DryDocs Neo4j and returns rows as JSON.",
)
