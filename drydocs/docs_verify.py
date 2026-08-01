"""Q7 — reconcile the doc-source registry against what the graph actually holds.

``config/doc-source-registry.yaml`` DECLARES every document corpus;
``tests/unit/test_doc_registry.py`` enforces the declaration's shape. Nothing
checked that a declared corpus was ever loaded, or that it landed in the database
it declared. This module is that check, and ``drydocs docs-verify`` is its verb.

REGISTRY-DRIVEN, NOT PER-LOADER — the acceptance's requirement, and the reason
for ``graph_locator``. The registry is corpus-keyed but the graph is not: only
the Q13 vendor-docs loader writes ``corpus_id``, while ``bmc_docs`` identifies
its pages by repo-relative ``path`` and ``essential_graphrag`` writes a single
Document whose ``doc_id`` IS the corpus id. Hard-coding those three shapes here
would make this file a per-loader registry that silently rots as loaders change.
Instead each entry declares how to find its own nodes, and a corpus that
declares nothing is reported as such rather than guessed at.

WHY SIX STATUSES AND NOT THE FOUR THE ITEM NAMED. `loaded | missing | stale |
wrong-db` cannot describe two situations that are live in the registry today,
and reporting either as `missing` would be a false diagnosis:

* ``db-absent`` — the declared ``target_db`` does not exist on this server.
  Two entries declare ``dddocs``, which ``schema/provisioning/01_databases.cypher``
  has never created. That is not a load failure; it is the open topology
  question G32 exists to rule on.
* ``unshaped`` — the corpus is registered and real but was never put on the
  lexical Document->Chunk spine (``jpmc-reports`` loaded as :DataAsset slices,
  pre-dating the docmeta plan). Its documents are not missing; they were never
  documents.

Both are reported, neither fails the run. Only ``wrong-db`` sets a non-zero
exit, per the acceptance — it is the G30 failure class at corpus granularity.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field

# --- statuses ----------------------------------------------------------------
LOADED = "loaded"
MISSING = "missing"
STALE = "stale"
WRONG_DB = "wrong-db"
UNSHAPED = "unshaped"
DB_ABSENT = "db-absent"

#: only this one fails the command (acceptance: "exits non-zero on any wrong-db")
FAILING = frozenset({WRONG_DB})

# --- locator vocabulary ------------------------------------------------------
# How a corpus's :Document nodes are found. Declared per entry under
# `graph_locator:`; the value is always parameterised, never interpolated.
MATCH_CORPUS_ID = "corpus_id"  # (:Document {corpus_id: value})  — Q13 loaders
MATCH_DOC_ID = "doc_id"  # (:Document {doc_id: value})     — single-doc corpora
MATCH_PATH_PREFIX = "path_prefix"  # d.path STARTS WITH value        — file-tree corpora
MATCH_NONE = "none"  # not on the lexical spine at all

LOCATOR_KINDS = frozenset({MATCH_CORPUS_ID, MATCH_DOC_ID, MATCH_PATH_PREFIX, MATCH_NONE})

_PREDICATES = {
    MATCH_CORPUS_ID: "d.corpus_id = $value",
    MATCH_DOC_ID: "d.doc_id = $value",
    MATCH_PATH_PREFIX: "d.path STARTS WITH $value",
}


@dataclass(frozen=True)
class CorpusRow:
    """One registry entry's reconciliation against the graph."""

    corpus_id: str
    target_db: str
    status: str
    documents: int = 0
    chunks: int = 0
    #: every database the corpus was actually found in (drives ``wrong-db``)
    found_in: tuple[str, ...] = ()
    detail: str = ""

    @property
    def ok(self) -> bool:
        return self.status not in FAILING


def locator_of(source: dict) -> tuple[str, str | None, bool]:
    """Return ``(kind, value, declared)`` for an entry.

    ``declared`` separates "this corpus is deliberately not on the lexical spine"
    (``match: none``, a ruling someone made) from "nobody said" (no
    ``graph_locator`` at all). Both end up ``unshaped``, but only one of them is
    an answer, and the detail line must not claim the entry said nothing when it
    said ``none`` on purpose.
    """
    loc = source.get("graph_locator")
    declared = loc is not None
    loc = loc or {}
    kind = loc.get("match", MATCH_NONE)
    if kind not in LOCATOR_KINDS:
        raise ValueError(
            f"[{source.get('id')}] graph_locator.match '{kind}' not in {sorted(LOCATOR_KINDS)}"
        )
    return kind, loc.get("value"), declared


def count_query(kind: str) -> str:
    """The counting Cypher for a locator kind.

    COUNT subquery rather than OPTIONAL MATCH: expanding one row per chunk and
    then de-duplicating would make the document count depend on chunk fan-out.
    """
    return f"""
        MATCH (d:Document)
        WHERE {_PREDICATES[kind]}
        RETURN count(d) AS documents,
               sum(COUNT {{ (:Chunk)-[:PART_OF]->(d) }}) AS chunks,
               collect(DISTINCT toString(d.captured_at)) AS captured_at
    """


def _probe(run: Callable[[str, str, dict], list[dict]], db: str, kind: str, value: str) -> dict:
    rows = run(db, count_query(kind), {"value": value})
    if not rows:
        return {"documents": 0, "chunks": 0, "captured_at": []}
    row = rows[0]
    return {
        "documents": int(row.get("documents") or 0),
        "chunks": int(row.get("chunks") or 0),
        "captured_at": [c for c in (row.get("captured_at") or []) if c],
    }


def _freshness(declared: object, graph_values: Sequence[str]) -> tuple[bool, str]:
    """ADR 0006 §4 gate-preserving freshness.

    Returns ``(is_stale, detail)``. Undeterminable is NEVER reported as fresh:
    the older loaders write no ``captured_at``, so for those corpora this says
    so rather than implying the content was checked.
    """
    if not graph_values:
        return False, "freshness uncheckable (graph carries no captured_at)"
    if declared in (None, ""):
        return False, "freshness uncheckable (registry declares no captured_at)"
    want = str(declared)
    if any(got.startswith(want) for got in graph_values):
        return False, ""
    return True, f"registry captured_at={want}, graph carries {sorted(set(graph_values))}"


def verify(
    sources: Iterable[dict],
    databases: Sequence[str],
    run: Callable[[str, str, dict], list[dict]],
    available: Sequence[str] | None = None,
) -> list[CorpusRow]:
    """Reconcile every registry entry against ``databases``.

    ``run(database, cypher, params) -> rows`` is the only I/O seam, so the unit
    suite drives the whole reconciliation against a fake with no Neo4j.
    ``available`` is the set of databases that actually exist (defaults to
    ``databases``); a declared target outside it yields ``db-absent``.
    """
    present = set(databases if available is None else available)
    rows: list[CorpusRow] = []

    for src in sources:
        cid = src.get("id", "<no-id>")
        target = src.get("target_db", "")
        kind, value, declared = locator_of(src)

        if kind == MATCH_NONE or not value:
            rows.append(
                CorpusRow(
                    corpus_id=cid,
                    target_db=target,
                    status=UNSHAPED,
                    detail=(
                        "declared not on the :Document spine (match: none)"
                        if declared
                        else "no graph_locator declared — nobody has ruled how to find this corpus"
                    ),
                )
            )
            continue

        # Probe every database that exists — including when the DECLARED one
        # does not. "Your target_db is unprovisioned" is a much weaker finding
        # than "...and the corpus is sitting in drydocs meanwhile", and the
        # second is the one that tells you what to do about it.
        found: dict[str, dict] = {}
        for db in databases:
            if db not in present:
                continue
            got = _probe(run, db, kind, value)
            if got["documents"]:
                found[db] = got

        if target not in present:
            where = (
                f"; meanwhile present in {sorted(found)} "
                f"({sum(f['documents'] for f in found.values())} docs)"
                if found
                else "; not found in any existing database either"
            )
            rows.append(
                CorpusRow(
                    corpus_id=cid,
                    target_db=target,
                    status=DB_ABSENT,
                    documents=sum(f["documents"] for f in found.values()),
                    chunks=sum(f["chunks"] for f in found.values()),
                    found_in=tuple(found),
                    detail=f"declared target_db '{target}' does not exist on this server{where}",
                )
            )
            continue

        here = found.get(target)
        elsewhere = tuple(db for db in found if db != target)

        if here is None:
            status = WRONG_DB if elsewhere else MISSING
            detail = (
                f"declared {target}, found in {list(elsewhere)}"
                if elsewhere
                else "no :Document matches the declared locator in any database"
            )
            rows.append(
                CorpusRow(
                    corpus_id=cid,
                    target_db=target,
                    status=status,
                    found_in=tuple(found),
                    detail=detail,
                )
            )
            continue

        stale, why = _freshness(src.get("captured_at"), here["captured_at"])
        # A corpus in the right DB *and* somewhere else is still wrong-db: the
        # stray copy is the defect, and reporting `loaded` would hide it.
        if elsewhere:
            status, detail = WRONG_DB, f"also present in {list(elsewhere)} (declared {target} only)"
        elif stale:
            status, detail = STALE, why
        else:
            status, detail = LOADED, why

        rows.append(
            CorpusRow(
                corpus_id=cid,
                target_db=target,
                status=status,
                documents=here["documents"],
                chunks=here["chunks"],
                found_in=tuple(found),
                detail=detail,
            )
        )

    return rows


def exit_code(rows: Iterable[CorpusRow]) -> int:
    return 0 if all(r.ok for r in rows) else 1


@dataclass
class Summary:
    """Counts per status, for the one-line tail the verb prints."""

    by_status: dict[str, int] = field(default_factory=dict)

    @classmethod
    def of(cls, rows: Iterable[CorpusRow]) -> Summary:
        out: dict[str, int] = {}
        for r in rows:
            out[r.status] = out.get(r.status, 0) + 1
        return cls(out)

    def line(self) -> str:
        if not self.by_status:
            return "no corpora declared"
        return " · ".join(f"{n} {s}" for s, n in sorted(self.by_status.items()))
