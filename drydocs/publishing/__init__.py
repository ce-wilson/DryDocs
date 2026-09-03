"""Re-export shim (ADR 0018 D4, 2026-09-02): this package moved to ``drydocs.review.publishing``.

Kept for ONE port cycle so every old import path, patch target and citation resolves to
the SAME module object (``sys.modules`` alias, so private names and monkeypatches work
through either path). EVERY submodule of the target package is aliased too - discovered
with ``pkgutil``, never a fixed tuple - so ``drydocs.publishing.<x>`` and
``drydocs.review.publishing.<x>`` are one object for any ``<x>`` the package holds. The
first cut listed the producer's four by name; the company's package holds two more
(``confluence_client``, ``manifest``) that the tuple did not cover, and a submodule the
tuple misses imports as a SECOND copy of one file - the two-copies hazard this shim
exists to prevent (found by the company's chunk-1 report, 2026-09-03). Removed at the
roll after next; new code imports the new path.
"""

import importlib as _importlib
import pkgutil as _pkgutil
import sys as _sys

from drydocs.review import publishing as _target

for _info in _pkgutil.iter_modules(_target.__path__):
    _sub = _importlib.import_module(f"{_target.__name__}.{_info.name}")
    _sys.modules[f"{__name__}.{_info.name}"] = _sub
_sys.modules[__name__] = _target
