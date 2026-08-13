"""Control-M API-call framework (G96) — the per-object call surface the
deploy/pull shell scripts invoke. See :mod:`.api` for the convention note."""

from drydocs_core.adapters.controlm.api import (
    OPERATIONS,
    TARGET_VERSION,
    ApiConfig,
    CallResult,
    Operation,
    execute,
    load_config,
    plan,
)

__all__ = [
    "ApiConfig",
    "CallResult",
    "Operation",
    "OPERATIONS",
    "TARGET_VERSION",
    "load_config",
    "plan",
    "execute",
]
