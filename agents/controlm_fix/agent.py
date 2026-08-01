"""controlm_fix — agent flow for the 'fix Control-M' support tooling.

LLM agent (needs GOOGLE_API_KEY in agents/.env). Given a failing job/folder,
it walks the graph for the job's dependencies, owners and downstream impact and
proposes a remediation plan. Read-only: fixes are executed by humans/tooling.
"""

import os

from common.neo4j_tool import graph_schema, read_cypher
from google.adk.agents.llm_agent import Agent

root_agent = Agent(
    model=os.getenv("ADK_MODEL", "gemini-flash-latest"),
    name="controlm_fix",
    description="Control-M remediation assistant: diagnoses failing jobs using the DryDocs graph and proposes a fix plan.",
    instruction="""You help production support fix failing BMC Control-M jobs using the
DryDocs knowledge graph.

When given a job, folder or symptom: use graph_schema and read_cypher to find the
job, its conditions/dependencies, owning application and team, and what is impacted
downstream. Then propose a concrete, ordered remediation plan (what to check, what
to rerun, who to page). You are READ-ONLY against the graph and you never execute
Control-M actions — you produce the plan and the exact commands for the operator.""",
    tools=[graph_schema, read_cypher],
)
