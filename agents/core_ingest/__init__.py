"""The core-ingest ADK app (ADR 0007).

Answers questions about what the ingest chains loaded and when. One ADK app: the
package exposes ``agent`` so the runtime can reach ``agent.root_agent``.
"""

from . import agent  # noqa: F401
