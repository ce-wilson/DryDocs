"""Re-export shim (ADR 0018 D4, 2026-09-02): this module moved to ``drydocs.docgen.design_doc``.

Kept for ONE port cycle so every old import path, patch target and citation resolves to
the SAME module object (``sys.modules`` alias, so private names and monkeypatches work
through either path). Removed at the roll after next; new code imports the new path.
"""

import sys as _sys

from drydocs.docgen import design_doc as _target

_sys.modules[__name__] = _target
