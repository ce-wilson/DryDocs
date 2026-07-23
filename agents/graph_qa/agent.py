"""graph_qa — the tiered read-only Q&A agent (Epic R / ADR 0007, item R2).

A custom ADK agent: the user message is a free-text question; the reply is
one JSON envelope (answer + per-step Cypher + metrics — the contract in
README.md). The pipeline is pure and injected; this wrapper only adapts ADK
in/out, counts session memory for the metrics block, and keeps every failure
inside a well-formed error payload (the api_server must never 500 on a bad
question).
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator
from datetime import datetime

from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from common.graph_read import run_read
from common.neo4j_tool import graph_schema
from graph_qa.envelope import sha256_text
from graph_qa.pipeline import GraphQaPipeline
from graph_qa.providers import ProviderConfigError, provider_from_env

_pipeline: GraphQaPipeline | None = None


def _get_pipeline() -> GraphQaPipeline:
    global _pipeline
    if _pipeline is None:
        _pipeline = GraphQaPipeline(
            provider=provider_from_env(),
            run_read=run_read,
            graph_schema=graph_schema,
        )
    return _pipeline


def _memory_size(ctx: InvocationContext) -> tuple[int, int]:
    """Session memory for the metrics block: (event count, serialized chars)."""
    events = getattr(getattr(ctx, "session", None), "events", None) or []
    chars = 0
    for event in events:
        content = getattr(event, "content", None)
        for part in getattr(content, "parts", None) or []:
            chars += len(getattr(part, "text", "") or "")
    return len(events), chars


class GraphQaAgent(BaseAgent):
    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        question = ""
        user_content = getattr(ctx, "user_content", None)
        if user_content and user_content.parts:
            question = (user_content.parts[0].text or "").strip()

        if not question:
            payload = {"status": "error", "error": "empty question"}
        else:
            try:
                events, chars = _memory_size(ctx)
                now = datetime.now()
                run_id = f"qa-{now:%Y%m%d-%H%M%S}-{sha256_text(question)[:6]}"
                envelope = _get_pipeline().answer(
                    question,
                    run_id=run_id,
                    session_id=getattr(getattr(ctx, "session", None), "id", "") or "",
                    memory_events=events,
                    memory_chars=chars,
                )
                payload = {"status": "success", **envelope.to_dict()}
            except ProviderConfigError as exc:
                payload = {"status": "error", "error": str(exc)}
            except Exception as exc:  # never let a question 500 the server
                payload = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

        yield Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=json.dumps(payload, indent=2, default=str))],
            ),
        )


root_agent = GraphQaAgent(
    name="graph_qa",
    description=(
        "Tiered read-only Q&A over the DryDocs knowledge graph: QuerySpec "
        "router, then schema-grounded text2cypher; returns the ADR 0007 "
        "answer envelope with per-step Cypher and metrics."
    ),
)
