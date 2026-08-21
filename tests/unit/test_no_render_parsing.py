"""J37 — never parse a render when the object is importable.

The N6 fix replaced a guard that ran `drydocs --help` and parsed the rendered
command list with `app.registered_commands`, the importable object. This sweep
keeps the class from returning: no test may enumerate commands, loaders, specs
or options by invoking `--help` (through CliRunner or a subprocess) — those
are objects. What remains legitimate, and why, is recorded on the J37 item:
CliRunner invocations whose ASSERTED SUBJECT is the verb's own message/exit
contract (bootstrap guard, apply-supplements, refresh-reference, the
source-registry gate), git plumbing (`ls-files`, `rev-parse`, `worktree add` —
machine-readable by design, not a render), and subprocess runs of scripts whose
subject is the process boundary itself (worktree discovery, import isolation).
"""

from __future__ import annotations

import re
from pathlib import Path

TESTS = Path(__file__).resolve().parent
_HELP_INVOKE = re.compile(r"""invoke\([^)]*\[[^\]]*["']--help["']""")
_HELP_SUBPROCESS = re.compile(r"""subprocess\.run\([^)]*["']--help["']""")


def test_no_test_enumerates_anything_by_parsing_help_output() -> None:
    offenders = []
    for path in sorted(TESTS.glob("test_*.py")):
        text = path.read_text(encoding="utf-8")
        if _HELP_INVOKE.search(text) or _HELP_SUBPROCESS.search(text):
            offenders.append(path.name)
    assert not offenders, (
        "test(s) parse `--help` output — the commands/options are importable objects "
        "(app.registered_commands, the Typer param specs); never parse a render when the "
        "object is importable (J37):\n  " + "\n  ".join(offenders)
    )
