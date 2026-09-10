"""graph_qa — the tiered read-only Q&A agent (Epic R / ADR 0007)."""

# AGENT2: the same bootstrap `common` uses - the repo root on sys.path, with the
# depth stated once. `agents/` is not a package, so `common` is a TOP-LEVEL
# import here and resolves for the same reason `graph_qa` itself does.
from common import _bootstrap  # noqa: F401
