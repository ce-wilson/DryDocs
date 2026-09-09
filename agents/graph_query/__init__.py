"""The graph-query ADK app (ADR 0007) — the tier's general question surface.

Tier-0 routes a question to a declared QuerySpec; anything it cannot match falls
through to schema-grounded text2cypher inside a bounded loop. One ADK app: the
package exposes ``agent`` so the runtime can reach ``agent.root_agent``.
"""

from . import agent  # noqa: F401  (ADK app convention: expose agent.root_agent)
