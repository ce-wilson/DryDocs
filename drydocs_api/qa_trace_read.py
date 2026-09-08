"""Reading the R18 Ask decision trace back — the `qa-debug` kind (R18 clause d).

One handler, framework-free, in its own module — the ``log_estate.py`` shape:
a function over injectable inputs that ``app.py`` wires to a route in a few
lines, testable with no server.

WHY THE READER IS HERE AND THE WRITER IS IN ``agents/``. ``drydocs_api`` never
imports the agents tree: it is a separate venv, which is why ``audit.py``
reimplements ``actor_hash`` rather than importing the identical function from
``agent_run_writer``. Reading a declared log kind needs nothing from the writer
— ``drydocs_core.log_kinds`` holds the naming rule and
``drydocs_core.run_log`` holds the directory — so the split costs nothing and
keeps the import boundary intact. The sibling reader for the 90-day ledger
(``agents/common/ledger_read.py``) sits on the agents side for the opposite
reason: its consumers are the agent's own on-demand tools.

THIS IS THE FIRST ROUTE THAT SERVES LOG CONTENTS, and that is a real boundary
rather than a formality. ``log_estate.py`` states the standing position: for the
``api-debug`` kind, capturing Cypher text is ruled and SURFACING it is held for
SME review, so that surface reports a kind's size and retention and has no
parameter that names a file. R18's acceptance (d) rules the question the other
way for THIS kind — "an admin can retrieve or download the trace by
run_id/session_id" — so the route exists, admin-gated exactly like
``/raw-cypher`` and ``/admin/log-estate``, and the difference is worth naming:
the api-debug concern was a rendered page anyone with the console could read.
The held api-debug question is untouched; nothing here can reach that kind.

THE FILTER IS MANDATORY, NOT A CONVENIENCE. A call with neither ``run_id`` nor
``session_id`` is REFUSED rather than answered with everything: "retrieve the
trace by run_id/session_id" is a lookup, and the same route with the filter
omitted would be a bulk log download wearing a lookup's name. It is also what
makes acceptance (d)'s "distinguish one question from concurrent sessions"
true — two sessions interleave their lines in one day-file, and the correlation
key is the only thing that separates them.

A CORRUPT LINE IS SKIPPED AND COUNTED, never fatal — ``ledger_read``'s ruling,
for the same reason: the writer is best-effort by design, so a half-written last
line is a normal state of the world, and a reader that raised on one would make
the whole day unreadable.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from drydocs_core.log_kinds import LogKindError, kind
from drydocs_core.run_log import resolve_log_dir

#: The kind and the free-form <name> segment its writer uses
#: (agents/common/qa_trace.TRACE_KIND / TRACE_NAME). Stated rather than
#: imported — see the module docstring on the venv boundary.
TRACE_KIND = "qa-debug"
TRACE_NAME = "graph_qa"
TRACE_PREFIX = f"{TRACE_KIND}.{TRACE_NAME}"

#: Response bound. A trace is tens of records for a normal run and can be
#: hundreds for a Tier-2 one; this is headroom with a flag rather than a limit
#: anyone is expected to hit, and it exists so one pathological run cannot
#: become an unbounded response.
MAX_RECORDS = 2_000


class TraceQueryError(ValueError):
    """The caller asked for no particular trace — refused, never widened."""


def trace_enabled(kinds_path: Path | None = None) -> bool:
    """Whether this deployment's declaration turns the trace on. Reported so an
    empty result on a server with debug OFF reads as "nothing was recorded"
    rather than as "your run id is wrong" — two different problems with the
    same empty list."""
    try:
        return kind(TRACE_KIND, kinds_path).level == "DEBUG"
    except LogKindError:
        return False


def trace_files(log_dir: Path | None = None) -> list[Path]:
    """Every day-file, oldest first. A missing directory is not an error — it
    is the state of a machine that has never recorded a trace."""
    directory = log_dir or resolve_log_dir()
    if not directory.is_dir():
        return []
    return sorted(directory.glob(f"{TRACE_PREFIX}.*.jsonl"))


def read_trace(
    run_id: str | None = None,
    session_id: str | None = None,
    log_dir: Path | None = None,
    kinds_path: Path | None = None,
) -> dict[str, Any]:
    """The admin payload: one run's (or one session's) trace records, in order.

    Records are returned in the order they were written and carry the writer's
    own ``seq``, so a consumer never has to trust file order to reconstruct a
    run — which matters exactly when it is hardest to reason about, with two
    sessions interleaved in one file.
    """
    run_id = (run_id or "").strip() or None
    session_id = (session_id or "").strip() or None
    if not run_id and not session_id:
        raise TraceQueryError(
            "name the trace you want: run_id or session_id. This route is a "
            "lookup by correlation key, not a log download."
        )

    records: list[dict] = []
    files: list[str] = []
    skipped = 0
    truncated = False
    for path in trace_files(log_dir):
        files.append(path.name)
        try:
            text = path.read_text(encoding="utf-8")
        except OSError:
            skipped += 1
            continue
        for line in text.splitlines():
            if not line.strip():
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                skipped += 1
                continue
            if not isinstance(record, dict):
                skipped += 1
                continue
            if run_id and record.get("run_id") != run_id:
                continue
            if session_id and record.get("session_id") != session_id:
                continue
            if len(records) >= MAX_RECORDS:
                truncated = True
                break
            records.append(record)
        if truncated:
            break

    records.sort(key=lambda r: (r.get("seq") if isinstance(r.get("seq"), int) else 0))
    return {
        "run_id": run_id,
        "session_id": session_id,
        "enabled": trace_enabled(kinds_path),
        "files": files,
        "records": records,
        "record_count": len(records),
        "skipped": skipped,
        "truncated": truncated,
    }
