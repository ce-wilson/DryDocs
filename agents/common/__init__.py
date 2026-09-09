"""Shared machinery for the agent tier's ADK apps (ADR 0007).

The pieces every agent app needs and none of them should own a copy of: the
read-only graph client and Neo4j tool, the QuerySpec catalog the Tier-0 router
dispatches through, the :AgentRun writer, answer evaluation, and the LLM ledger.
Read-only by construction — the tier answers questions and never writes the
knowledge graph.
"""
