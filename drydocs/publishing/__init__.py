"""Re-export shim (ADR 0018 D4, 2026-09-02): this package moved to ``drydocs.review.publishing``.

Kept for ONE port cycle so every old import path, patch target and citation resolves to
the SAME module object (``sys.modules`` alias, so private names and monkeypatches work
through either path). The submodules are aliased too, so ``drydocs.publishing.assembler``
and ``drydocs.review.publishing.assembler`` are one object, not two copies of one file.
Removed at the roll after next; new code imports the new path.
"""

import sys as _sys

from drydocs.review import publishing as _target
from drydocs.review.publishing import assembler, preview, publisher, validator

for _sub in (assembler, preview, publisher, validator):
    _sys.modules[f"{__name__}.{_sub.__name__.rsplit('.', 1)[-1]}"] = _sub
_sys.modules[__name__] = _target
