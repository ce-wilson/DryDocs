"""Regenerate tests/fixtures/adk/stub-run-sse.txt (R12).

A one-command regeneration, because a fixture nobody can rebuild gets deleted
instead of updated -- and the drift guard in
tests/integration/test_stub_adk_ask_wiring.py names this script by path when it
fails, so the instruction cannot rot into something that no longer works.

WRITES BYTES, NOT TEXT. The file records an SSE stream, where the blank line
between frames IS the delimiter lib/adk.ts scans for. Python's text mode
translates ``\n`` to the platform line ending, which on Windows would write
CRLF and make the recorded bytes differ from the wire. .gitattributes exempts
the path from eol normalisation for the same reason.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))

from tests.stub_adk import events_for, sse_body  # noqa: E402

OUT = REPO / "tests" / "fixtures" / "adk" / "stub-run-sse.txt"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_bytes(sse_body(events_for([{"text": "q"}], None)).encode("utf-8"))
    print(f"wrote {OUT.relative_to(REPO)} ({OUT.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
