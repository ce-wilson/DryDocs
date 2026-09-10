"""The repo root, computed ONCE, so the agent tier can import ``drydocs_*``.

WHY THIS EXISTS AT ALL. The agent tier runs in its own interpreter
(``agents/.venv``), deliberately: ``agents/requirements.txt`` pins
``neo4j>=6.2,<7`` while the repo's ``pyproject.toml`` pins ``neo4j = "^5.20"``,
and that file says in as many words that the agents venv "may lead, but only by
declaration". So the repo is NOT pip-installed here — the packages are reached
by path, and something has to put the repo root on ``sys.path``.

WHAT IT REPLACES (AGENT2). Nine copies of the same five-line preamble, each
hard-coding ``parents[2]``, each sitting BETWEEN the import block and the
``drydocs_*`` imports it enabled — which is what forced thirteen ``# noqa: E402``
suppressions across eight files. The depth was the real cost: nine literals that
all silently mean "this file is exactly two directories below the repo root", so
moving any one of those files broke it at import time and the fix was to edit a
number nobody could search for. Here the depth is stated once, next to the reason.

HOW IT REACHES YOU. Never import this module from a leaf. ``common/__init__.py``
and ``graph_qa/__init__.py`` import it, so importing ANYTHING from either package
runs it first — which is why the ``drydocs_*`` imports in those modules are now
ordinary top-of-file imports with no suppression. That works because ``agents/``
is on ``sys.path`` before any of this (``serve.py`` puts it there; ADK's
``NestedAgentLoader`` lists apps by directory; the tests insert it), and because
``agents/`` is not itself a package — its subdirectories are imported as
top-level ``common`` / ``graph_qa``.

Importing this module twice is free: the guard below is the same idempotence
check the nine copies each carried.
"""

from __future__ import annotations

import sys
from pathlib import Path

#: The repo root: ``agents/common/_bootstrap.py`` -> ``common/`` -> ``agents/``
#: -> the root. Verified, not assumed — this file sits at the same depth as the
#: eight leaves it replaces, so the index is the same ``2`` they each carried.
#: That it is unchanged is the point: the value was never wrong, it was written
#: nine times, and the ninth copy is the one that would have gone stale silently.
REPO_ROOT: Path = Path(__file__).resolve().parents[2]

if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))
