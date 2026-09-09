"""The Control-M fix ADK app (ADR 0007).

Answers remediation-shaped questions about Control-M objects. One ADK app: the
package exposes ``agent`` so the runtime can reach ``agent.root_agent``.
"""

from . import agent  # noqa: F401
