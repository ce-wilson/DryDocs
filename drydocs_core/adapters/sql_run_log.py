"""Per-run SQL extract log — the HITL verification trail for Oracle extracts.

Ported behavior from the company repo's JDBC path (``jdbc_oracle_adapter.py`` +
``SpiderpRunner.openTee()``): every statement the ``--use-oracle`` path runs is
written to a self-contained, timestamped log OUTSIDE the repo, so the SME/HITL
can verify exactly what was extracted. The producer's Oracle path is
python-oracledb (no JDBC runner here — ``docs/port-prompt.md`` item 14), so the
same log contract is implemented at the adapter seam:

    header (run metadata) -> handshake -> exact SQL (binds rendered for review)
    -> result (csv) -> footer

Two deliberate differences from the company path, both safety-positive:

* Execution stays PARAMETERIZED — binds go to Oracle natively through
  oracledb. :func:`render_sql` is display-only; a rendering bug can corrupt a
  log line, never a query.
* The renderer is born with the company hardening ("don't treat :tokens in SQL
  comments/strings as binds"): substitution happens only in code regions —
  text inside ``--`` / ``/* */`` comments, 'single-quoted strings', and
  "quoted identifiers" is copied verbatim. ``:DEPENDS_ON`` in comments and the
  ``':depends_on'`` literal in ``controlm_dependencies_recursive.sql`` stay
  byte-identical.

Environment (names match the company repo so inspection snippets work in both;
resolution is shared with :mod:`drydocs_core.run_log` — the loader-run logs —
so ONE knob configures the whole log family):

    DRYDOCS_LOGDIR   log directory (generic name, wins when set);
    SPIDERP_LOGDIR   honored fallback; default ``~/logs/DryDocs`` —
                     deliberately outside the repo (code and logs in separate
                     paths). Created automatically if missing.
    DRYDOCS_CALLER / SPIDERP_CALLER   the ``script:`` stamp; defaults to
                     ``drydocs <argv>``.

A log may contain real DSNs and extracted data values — logs live outside the
repo and are never committed. This module is mechanism only.
"""
from __future__ import annotations

import csv
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Mapping, Sequence

from drydocs_core.run_log import caller_stamp, claim_log_path

_RULE = "=" * 66
_THIN_RULE = "-" * 66

_BIND_NAME_RE = re.compile(r":([A-Za-z][A-Za-z0-9_]*)")


def sql_literal(value: Any) -> str:
    """Render one bind value as an Oracle literal (display only)."""
    if value is None:
        return "NULL"
    if isinstance(value, bool):
        return "1" if value else "0"
    if isinstance(value, (int, float)):
        return str(value)
    return "'" + str(value).replace("'", "''") + "'"


def render_sql(query: str, binds: Mapping[str, Any] | None) -> str:
    """Substitute ``:bind`` placeholders with literals — in code regions ONLY.

    Text inside ``--`` line comments, ``/* */`` block comments,
    ``'single-quoted strings'``, and ``"quoted identifiers"`` is copied
    verbatim; a ``:token`` whose name is not in ``binds`` is left untouched
    (python-oracledb likewise drops unused binds). The result is for the run
    log — execution always uses the parameterized original.
    """
    binds = binds or {}
    out: list[str] = []
    i, n = 0, len(query)
    while i < n:
        two = query[i : i + 2]
        ch = query[i]
        if two == "--":
            j = query.find("\n", i)
            j = n if j == -1 else j
            out.append(query[i:j])
            i = j
        elif two == "/*":
            j = query.find("*/", i + 2)
            j = n if j == -1 else j + 2
            out.append(query[i:j])
            i = j
        elif ch == "'":
            j = i + 1
            while j < n:
                if query[j] == "'":
                    if query[j + 1 : j + 2] == "'":  # escaped '' stays inside
                        j += 2
                        continue
                    j += 1
                    break
                j += 1
            else:
                j = n
            out.append(query[i:j])
            i = j
        elif ch == '"':
            j = query.find('"', i + 1)
            j = n if j == -1 else j + 1
            out.append(query[i:j])
            i = j
        elif ch == ":":
            m = _BIND_NAME_RE.match(query, i)
            if m and m.group(1) in binds:
                out.append(sql_literal(binds[m.group(1)]))
                i = m.end()
            else:
                out.append(ch)
                i += 1
        else:
            out.append(ch)
            i += 1
    return "".join(out)


_caller = caller_stamp  # shared with run_log; kept as the module's tested name


class SqlRunLog:
    """One self-contained log per statement-batch run (one per adapter enter).

    Drive it in order: :meth:`open` -> :meth:`handshake` -> :meth:`statement`
    -> :meth:`result_header` / :meth:`result_row` -> :meth:`close`. Every
    method is a no-op after :meth:`close`, and any OSError while writing is
    swallowed after ``open`` succeeds — the log is an audit trail, never the
    reason an extract fails.
    """

    def __init__(self, base_name: str, *, target: str = "", user: str = "") -> None:
        self.base_name = base_name
        self.target = target
        self.user = user
        self.path: Path | None = None
        self._fh = None
        self._csv = None
        self._rows = 0
        self._started = time.monotonic()

    def open(self) -> Path:
        """Create the log dir if missing, claim a timestamped file, write the header."""
        path = claim_log_path(self.base_name)
        self._fh = path.open("w", encoding="utf-8", newline="")
        self.path = path
        self._started = time.monotonic()
        now = datetime.now().astimezone().isoformat(timespec="seconds")
        self._write(
            f"{_RULE}\n"
            f"date       : {now}\n"
            f"script     : {_caller()}\n"
            f"statement  : {self.base_name}\n"
            f"target     : {self.target}\n"
            f"user       : {self.user}\n"
            f"bind mode  : native oracledb binds — SQL below rendered for review only\n"
            f"{_RULE}\n"
        )
        return path

    def handshake(self, detail: str) -> None:
        self._write(f"connected  : {detail}\n")

    def statement(self, rendered_sql: str, binds: Mapping[str, Any] | None = None) -> None:
        self._write(f"\n{_THIN_RULE}\n-- statement 1 --\n{rendered_sql.rstrip()}\n")
        if binds:
            self._write("-- binds (passed natively) --\n")
            for name, value in binds.items():
                self._write(f"{name} = {sql_literal(value)}\n")

    def result_header(self, columns: Sequence[str]) -> None:
        self._write("-- result (csv) --\n")
        self._csv_row(columns)

    def result_row(self, values: Sequence[Any]) -> None:
        self._csv_row(["" if v is None else v for v in values])
        self._rows += 1

    def close(self, error: BaseException | None = None) -> None:
        if self._fh is None:
            return
        elapsed_ms = int((time.monotonic() - self._started) * 1000)
        if error is not None:
            self._write(f"\nFAILED: {error}\n")
        self._write(f"\nDone. 1 statement(s), {self._rows} row(s) in {elapsed_ms} ms.\n")
        try:
            self._fh.close()
        except OSError:
            pass
        self._fh = None
        self._csv = None

    # -- internal ----------------------------------------------------------

    def _write(self, text: str) -> None:
        if self._fh is None:
            return
        try:
            self._fh.write(text)
        except OSError:
            pass

    def _csv_row(self, values: Sequence[Any]) -> None:
        if self._fh is None:
            return
        if self._csv is None:
            self._csv = csv.writer(self._fh, lineterminator="\n")
        try:
            self._csv.writerow(values)
        except OSError:
            pass
