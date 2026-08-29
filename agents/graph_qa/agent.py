"""graph_qa — the tiered read-only Q&A agent (Epic R / ADR 0007, items R2-R5).

A custom ADK agent: the user message is a free-text question (part 0; an
optional control part carries the console's drydocs-api session token — see
control.py); the reply is a stream of step events while the pipeline runs
(R5: the Ask spoke renders them live) followed by one JSON envelope (answer
+ per-step Cypher + metrics — the contract in README.md). The pipeline is
pure and injected; this wrapper adapts ADK in/out, bridges the synchronous
pipeline onto the event stream via a thread + queue, counts session memory
for the metrics block, records the R3 telemetry sinks, and keeps every
failure inside a well-formed error payload (the api_server must never 500
on a bad question).
"""

from __future__ import annotations

import asyncio
import json
import logging
from collections.abc import AsyncGenerator
from dataclasses import asdict
from datetime import datetime

from common.agent_run_writer import write_agent_run
from common.ephemeral_client import make_register
from common.graph_read import run_read
from common.llm_ledger import LlmLedger
from common.neo4j_tool import graph_schema_detailed
from google.adk.agents import BaseAgent
from google.adk.agents.invocation_context import InvocationContext
from google.adk.events import Event
from google.genai import types

from graph_qa.control import split_question_and_control
from graph_qa.envelope import sha256_text
from graph_qa.pipeline import GraphQaPipeline
from graph_qa.providers import LiteLlmProvider, ProviderConfigError, provider_from_env

_LOGGER = logging.getLogger(__name__)

_provider: LiteLlmProvider | None = None
_ledger = LlmLedger()  # R3 sink 1: per-LLM-call JSONL in DRYDOCS_LOGDIR


def _get_provider() -> LiteLlmProvider:
    global _provider
    if _provider is None:
        _provider = provider_from_env()
    return _provider


def _build_pipeline(control: dict, on_step, run_id: str | None = None) -> GraphQaPipeline:
    """Per-request pipeline: the provider (and its connection pool) is the
    singleton; the R4 registrar is per-request because the ephemeral specs it
    mints are owned by the ASKING console session's token — which is also why
    the run_id can close over it (G108 ruling D: the API audit's correlation
    key back to this run's ledger lines)."""
    return GraphQaPipeline(
        provider=_get_provider(),
        run_read=run_read,
        graph_schema=graph_schema_detailed,
        ledger=_ledger,
        register_cypher=make_register(
            owner_token=control.get("api_token"),
            api_url=control.get("api_url"),
            run_id=run_id,
        ),
        on_step=on_step,
    )


def _record_run(envelope, question: str, user_id: str) -> None:
    """R3 sinks after the answer: run line in the local ledger (full question
    text lives ONLY there) + the :AgentRun node via the dedicated writer.
    Both best-effort — telemetry never turns a good answer into an error."""
    # G105/ADR 0014 clause 2: still BEST-EFFORT -- telemetry never turns a good
    # answer into an error, and that judgement was always right. What was wrong is
    # that a permanently broken sink reported nothing at all, so the swallow now
    # says so once per failure instead of passing silently.
    try:
        _ledger.run(envelope, question)
    except Exception:
        _LOGGER.warning("graph_qa: ledger write failed; the answer stands", exc_info=True)
    try:
        write_agent_run(envelope, user_id=user_id)
    except Exception:
        _LOGGER.warning("graph_qa: :AgentRun write failed; the answer stands", exc_info=True)


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
    def _event(self, ctx: InvocationContext, payload: dict) -> Event:
        return Event(
            invocation_id=ctx.invocation_id,
            author=self.name,
            content=types.Content(
                role="model",
                parts=[types.Part(text=json.dumps(payload, indent=2, default=str))],
            ),
        )

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        texts: list[str] = []
        user_content = getattr(ctx, "user_content", None)
        if user_content and user_content.parts:
            texts = [(part.text or "") for part in user_content.parts]
        question, control = split_question_and_control(texts)

        if not question:
            yield self._event(ctx, {"status": "error", "error": "empty question"})
            return

        try:
            events, chars = _memory_size(ctx)
            now = datetime.now()
            run_id = f"qa-{now:%Y%m%d-%H%M%S}-{sha256_text(question)[:6]}"
            # ADK 2.0 run_async carries user_id per call; only its hash survives.
            user_id = getattr(ctx, "user_id", "") or ""

            # Bridge the synchronous pipeline onto the event stream: steps land
            # on an asyncio queue from the worker thread and are yielded as
            # {"kind": "step"} events the Ask spoke renders while it waits.
            queue: asyncio.Queue = asyncio.Queue()
            loop = asyncio.get_running_loop()

            def on_step(step) -> None:
                loop.call_soon_threadsafe(queue.put_nowait, step)

            pipeline = _build_pipeline(control, on_step, run_id)
            answer_task = asyncio.ensure_future(
                asyncio.to_thread(
                    pipeline.answer,
                    question,
                    run_id=run_id,
                    session_id=getattr(getattr(ctx, "session", None), "id", "") or "",
                    memory_events=events,
                    memory_chars=chars,
                    user_id=user_id,
                )
            )
            while True:
                getter = asyncio.ensure_future(queue.get())
                done, _ = await asyncio.wait(
                    {getter, answer_task}, return_when=asyncio.FIRST_COMPLETED
                )
                if getter in done:
                    yield self._event(ctx, {"kind": "step", "step": asdict(getter.result())})
                    continue
                getter.cancel()
                break
            while not queue.empty():  # steps that landed with the final result
                yield self._event(ctx, {"kind": "step", "step": asdict(queue.get_nowait())})

            envelope = answer_task.result()  # re-raises pipeline exceptions
            _record_run(envelope, question, user_id)
            payload = {"status": "success", **envelope.to_dict()}
        except ProviderConfigError as exc:
            payload = {"status": "error", "error": str(exc)}
        except Exception as exc:  # never let a question 500 the server
            payload = {"status": "error", "error": f"{type(exc).__name__}: {exc}"}

        yield self._event(ctx, payload)


root_agent = GraphQaAgent(
    name="graph_qa",
    description=(
        "Tiered read-only Q&A over the DryDocs knowledge graph: QuerySpec "
        "router, then schema-grounded text2cypher; streams step events while "
        "running and returns the ADR 0007 answer envelope with per-step "
        "Cypher and metrics."
    ),
)
