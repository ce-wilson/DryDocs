"""Anchor-id contract shared across components (Epic L).

The ``<!-- anchor: id -->`` convention is used by the docgen component
(drydocs.doc_outline validation, drydocs.design_doc rendering) AND the load
component (drydocs.loaders.doc_traceability, L7 connector #1) — shared code
routes through core per ADR 0002-a, so the regex and the L11 derived-anchor
separator live here and both components import them.
"""

from __future__ import annotations

import re

#: ``<!-- anchor: some-id -->`` — the section marker (authored, never positional).
ANCHOR_RE = re.compile(r"<!--\s*anchor:\s*([a-z0-9][a-z0-9-]*)\s*-->", re.IGNORECASE)

#: L11 — the screen render derives per-subsection feedback anchors as
#: ``<authored-anchor>--<subsection-slug>``, so ``--`` is RESERVED: never use a
#: double hyphen inside an authored anchor id. A derived anchor degrades to its
#: base authored section when the subsection text (and so its slug) changes.
DERIVED_ANCHOR_SEP = "--"
