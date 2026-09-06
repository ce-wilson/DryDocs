"""WEB4 — TypeScript `strict` stays on in web/, and nothing is asserted past it.

Two halves of one rule, because either half alone is defeatable:

* **The setting.** Both `web/tsconfig*.json` set `strict: true`, and neither turns
  one of strict's sub-flags back off underneath it. `strict` is a bundle, so
  `{"strict": true, "strictNullChecks": false}` type-checks like the flag was never
  set — the guard would pass and the O70 bet would still be uncashed.
* **The escape hatch.** `@ts-expect-error` / `@ts-ignore` / `@ts-nocheck` under
  `web/src` do not rise above the baseline measured when this landed. The
  compiler being on is worth nothing if the errors it finds are commented away,
  which is exactly what clause (a) of the item forbids.

The baseline is **zero**, measured on 2026-09-05 on the tree that turned the flag
on: strict went on and `tsc -b` passed with no suppression added anywhere. So the
rule reads as "none", and a first suppression must raise `DIRECTIVE_BASELINE` in
the same commit, with the reason — a deliberate act, not a drift.

Why this guard exists at all, given CI already runs `tsc -b`: CI proves the tree
compiles under whatever the tsconfig currently says. It cannot notice the tsconfig
saying less than it did. That is the drift this file is here to stop, and it is the
same shape as the repo's other generated-artifact and convention guards.

**J66 — this guard reads RAW SOURCE on purpose.** The rule's own subject is a
comment (`// @ts-expect-error`), so `code_only()` would strip the very text being
counted; this is the documented exception, and the exception is stated here rather
than assumed. Note the guard cannot count itself: it lives under `tests/unit/`, and
the scan glob is `web/src/**` only.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
WEB = REPO / "web"
TSCONFIGS = ("tsconfig.app.json", "tsconfig.node.json")

#: Suppression directives, counted across web/src. `@ts-nocheck` is not named by
#: the item but belongs to the same class and is the widest of the three — it
#: turns the compiler off for a whole file.
DIRECTIVES = ("@ts-expect-error", "@ts-ignore", "@ts-nocheck")

#: Measured 2026-09-05 on the commit that set `strict: true` (WEB4). Raising this
#: is allowed; doing it silently is the thing the guard refuses.
DIRECTIVE_BASELINE = 0

#: The sub-flags `strict` switches on. Listing them is the point: a config may add
#: any of these explicitly as `true`, but setting one to `false` re-opens the hole
#: `strict: true` was set to close.
STRICT_SUBFLAGS = (
    "noImplicitAny",
    "noImplicitThis",
    "alwaysStrict",
    "strictNullChecks",
    "strictFunctionTypes",
    "strictBindCallApply",
    "strictPropertyInitialization",
    "useUnknownInCatchVariables",
)

_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"(?m)^\s*//.*$")


def _load_jsonc(path: Path) -> dict:
    """tsconfig files are JSONC — the repo's carry comments explaining each block.

    Stripping is deliberately dumb; it is safe here only because these two files
    contain no string literal holding `//` or `/*`. The assertion below is the
    instrument check (J76): if the stripper ever mangles a file, the parse raises
    or the known key vanishes, and the test fails loudly instead of reading a
    half-parsed config as a compliant one.
    """
    text = path.read_text(encoding="utf-8")
    doc = json.loads(_LINE_COMMENT.sub("", _BLOCK_COMMENT.sub("", text)))
    assert "compilerOptions" in doc, f"{path.name}: parsed, but has no compilerOptions"
    return doc


def _sources() -> list[Path]:
    return sorted(
        p
        for ext in ("*.ts", "*.tsx")
        for p in (WEB / "src").rglob(ext)
        if "node_modules" not in p.parts
    )


def test_strict_is_on_in_both_tsconfigs() -> None:
    for name in TSCONFIGS:
        opts = _load_jsonc(WEB / name)["compilerOptions"]
        assert opts.get("strict") is True, (
            f"{name}: `strict` is not true. The Vite React-TS template ships it on; "
            "WEB4 put it back because the generated api.d.ts models optional fields "
            "as optional and only strictNullChecks enforces them."
        )


def test_no_tsconfig_reopens_a_strict_subflag() -> None:
    for name in TSCONFIGS:
        opts = _load_jsonc(WEB / name)["compilerOptions"]
        reopened = [f for f in STRICT_SUBFLAGS if opts.get(f) is False]
        assert not reopened, (
            f"{name}: {reopened} set to false under `strict: true` — that switches the "
            "check back off while the guard above still reads as compliant."
        )


def test_suppression_directives_do_not_rise_above_the_baseline() -> None:
    hits: list[str] = []
    for path in _sources():
        text = path.read_text(encoding="utf-8")
        for lineno, line in enumerate(text.splitlines(), start=1):
            for directive in DIRECTIVES:
                if directive in line:
                    rel = path.relative_to(REPO).as_posix()
                    hits.append(f"{rel}:{lineno}  {directive}")
    assert len(hits) <= DIRECTIVE_BASELINE, (
        f"{len(hits)} suppression directive(s) under web/src, baseline "
        f"{DIRECTIVE_BASELINE}. Fix the site or raise DIRECTIVE_BASELINE in the same "
        "commit with the reason:\n  " + "\n  ".join(hits)
    )


def test_the_scan_actually_reads_the_web_sources() -> None:
    """Instrument check (J76): a glob that matches nothing passes the count test
    vacuously, and would keep passing after web/src moved."""
    sources = _sources()
    assert len(sources) > 100, f"only {len(sources)} TS sources under web/src — glob broken?"
    assert any(p.name == "App.tsx" for p in sources), "web/src/App.tsx not in the scan"
