"""Orchestration — the vendor-NEUTRAL surface, with each vendor beneath it.

Added at S2 (ADR 0008). The problem it solves was not that ``controlm/`` was
misfiled: it was that ``controlm/`` had **no parent and no siblings**, so an
AutoSys or Airflow module had nowhere to land, and the ~600 genuinely neutral
lines (shell/argv parsing, path canonicalization) sat inside a vendor-named
package where a second vendor would either duplicate them or import sideways.

```
orchestration/
├── shell.py        statement split, argv tokenize, wrapper unwrap, interpreter
│                   inference, LAUNCHER_REGISTRY, file-op verbs
├── paths.py        FileRef shape + assembly + PathDialect (vendor vocabulary)
├── crosswalk.py    config/crosswalks/*.yaml native -> baseline; RAISES on
│                   fidelity: no-equivalent
└── controlm/       everything irreducibly Control-M — AutoEdit %%NAME|VALUE
                    variables, the substitution resolver, folder-name convention,
                    field routing, and the Control-M PathDialect
```

TWO RULES THIS PACKAGE ENFORCES BY SHAPE (ADR 0008 rules 1-2):

1. **A vendor directory holds vendor semantics and nothing else.** If a module
   would work unchanged against a different orchestrator it belongs HERE, not
   under a vendor. The dependency direction follows: ``controlm/`` may import
   from this level; nothing at this level may import from ``controlm/``.
   Guarded by ``tests/unit/test_module_boundary.py``.

2. **Neutrality is earned by a second implementation, not asserted by a name.**
   This package exports only what ``controlm/`` and the two confirmed crosswalks
   *both* justify today. It is deliberately NOT a plugin framework — ADR 0008
   rejected that (Option C) as designing an abstraction from one implementation,
   and the crosswalks' 5 ``no-equivalent`` rows are the evidence the vendors do
   not align cleanly enough for an ABC to mean anything yet.

Nothing here touches the graph. ``:ControlMJob`` / ``:ControlMFolder`` /
``:ControlMServer`` / ``:ControlMApplication`` keep their vendor prefixes — that
is ADR 0003 rule 4 working as designed, and it is *why* the canonical labels
(``:BusinessApplication``, ``:Product``) can stay neutral.
"""

from .crosswalk import (
    Crosswalk,
    Mapping,
    NoEquivalentError,
    UnknownConceptError,
    UnknownOrchestratorError,
    load_crosswalks,
    orchestrators,
    resolve,
    unmappable,
)
from .paths import NEUTRAL, FileRef, PathDialect, build_file_ref, classify_role, looks_like_path
from .shell import (
    FileOp,
    Invocation,
    ParsedCommand,
    classify_executable,
    is_registered_launcher,
    parse_command,
    pipeline_guid,
    split_statements,
)

__all__ = [
    # shell — the neutral command parser
    "Invocation",
    "FileOp",
    "ParsedCommand",
    "parse_command",
    "split_statements",
    "classify_executable",
    "is_registered_launcher",
    "pipeline_guid",
    # paths — the neutral shape + the dialect seam
    "FileRef",
    "PathDialect",
    "NEUTRAL",
    "build_file_ref",
    "classify_role",
    "looks_like_path",
    # crosswalk — native -> baseline, refusing on no-equivalent
    "Crosswalk",
    "Mapping",
    "NoEquivalentError",
    "UnknownConceptError",
    "UnknownOrchestratorError",
    "load_crosswalks",
    "orchestrators",
    "resolve",
    "unmappable",
]
