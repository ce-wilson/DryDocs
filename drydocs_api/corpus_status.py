"""The doc-corpus reconciliation, served to the console (O58).

WHAT THIS IS. ``drydocs docs-verify`` answers "which declared corpus is actually
loaded, and in which database". O58 gives that answer a console surface. This
module is the server half: it adapts a ``GraphRunner`` to the
``run(database, cypher, params)`` seam that ``drydocs_core.docs_verify.verify()``
already takes, and returns rows a browser can render.

THE TRANSPORT CHOICE, which O58 said was the item's real content and had to be
made explicitly rather than defaulted. Option (a) — a server-side sweep endpoint
reusing ``verify()``. The other two were rejected on evidence, not taste:

* (b) N REGISTERED SPECS, joined client-side. A QuerySpec carries exactly one
  ``database:``, and ``SPEC_DATABASES`` is ``{"drydocs"}`` — superseded ``ddcontext`` was
  REMOVED from the reviewed set at G102 (2026-08-18) with the single-database
  fold. Admitting it back so a page could be built would reverse a signed gate
  ruling to serve a UI, which is the wrong direction of travel. Worse, the join
  rule would be a REIMPLEMENTATION of ``verify()``'s status derivation in
  TypeScript: two copies of a reconciliation that must agree, in two languages.
  And it still could not produce ``db-absent``, which comes from
  ``SHOW DATABASES`` — a server-level query no spec can express.
* (c) A GENERATED JSON ARTIFACT, the /software precedent. Fatal on determinism:
  the content depends on a LIVE graph, the two machines hold independent graphs
  (J18), and a committed artifact that differs per machine cannot be drift-guarded
  the way every other generated artifact here is. It would also be stale by
  construction — a reconciliation whose whole value is "as of now".

THE COST OF (a), RECORDED RATHER THAN GLOSSED. This is a read path that is NOT a
QuerySpec, so it is outside the spec registry's review, its per-spec
``classification`` field and the spec guards. What it is NOT is a widening of ADR
0005: decision 2 provides for "named queries shaped for the console's views", the
endpoint takes NO parameters at all, and every Cypher string is chosen server-side
by ``verify()``. The browser cannot influence which query runs — which is the
property ADR 0005 exists to protect. The API already carries a second server-side
query registry (``NAMED_QUERIES`` behind /query/{id}) beside the specs, so a
fixed server-chosen read path is an established shape here, not a new one.

AND IT FORCED A MODULE MOVE, which is the part worth knowing. ``docs_verify``
lived in ``drydocs/`` (the load component); ``drydocs_api`` is a different
component and components may not import each other. Rather than declare a
cross-component exception, the module was PROMOTED to ``drydocs_core`` — where
MODULE_MAP's placement test already put it, since it imports stdlib only and its
one I/O seam is an injected callable. The verb keeps the I/O.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Protocol

from drydocs_core.docs_verify import STATUSES, verify
from drydocs_core.repo_paths import repo_root

#: The declaration this reconciles against. Resolved through ``repo_root`` the
#: way every other repo-file read in this component does, so an installed copy
#: and a working tree agree.
DOC_REGISTRY_PATH = (
    repo_root(Path(__file__).resolve().parent.parent) / "config" / "doc-source-registry.yaml"
)

#: Databases the console sweep visits. Mirrors the CLI verb's own tuple
#: (``drydocs.cli_docs.DOC_SWEEP_DATABASES``) rather than importing it, because
#: that module is a component this one may not import — and a guard asserts the
#: two agree, so the duplication cannot drift silently.
#:
#: The second name is the SUPERSEDED ``ddcontext``, and it is here deliberately
#: for exactly as long as that database exists: the sweep visits it so a corpus
#: stranded there after the G102 fold reports wrong-db loudly instead of
#: vanishing. It drops out on its own once the inert database is dropped, via
#: the SHOW DATABASES intersection below.
SWEEP_DATABASES: tuple[str, ...] = ("drydocs", "ddcontext")  # superseded, swept while it exists


class GraphRunner(Protocol):
    def run(
        self, cypher: str, params: Mapping[str, object], database: str
    ) -> tuple[list[str], list[dict[str, object]]]: ...


def _available(runner: GraphRunner, candidates: Sequence[str]) -> list[str]:
    """Which of ``candidates`` the server actually has.

    ``SHOW DATABASES`` is a server-level query — it is why ``db-absent`` can be
    told apart from ``missing`` at all, and it is precisely what no QuerySpec can
    express. A server that refuses it (permissions, or a cluster that does not
    expose it) yields the candidates unfiltered rather than an error: reporting
    every corpus as ``db-absent`` because the PROBE failed would be a false
    diagnosis of exactly the kind this module exists to remove.
    """
    try:
        _, rows = runner.run("SHOW DATABASES YIELD name RETURN name", {}, "system")
    except Exception:
        return list(candidates)
    names = {str(r.get("name", "")) for r in rows}
    return [db for db in candidates if db in names]


def corpus_status(sources: Sequence[dict], runner: GraphRunner) -> dict[str, object]:
    """Reconcile the declared corpora against the graph. PURE apart from ``runner``.

    Returns the payload the console renders. ``databases_queried`` is carried
    explicitly because the surface's honesty rule turns on it: a database that
    was not queried renders "not queried", never 0 (the O56 rule), and the page
    cannot tell those apart from the rows alone.
    """
    available = _available(runner, SWEEP_DATABASES)

    def run(database: str, cypher: str, params: dict) -> list[dict]:
        _, rows = runner.run(cypher, params, database)
        return rows

    rows = verify(sources, SWEEP_DATABASES, run, available=available)
    return {
        # Not a spec result, so it carries its classification explicitly — the
        # surface badges it the way it badges a spec's.
        "classification": "internal-public",
        "databases_swept": list(SWEEP_DATABASES),
        "databases_queried": available,
        # Every status the reconciliation can EVER return, sent with the payload
        # so the surface renders the real set rather than a hand-copied one. A
        # status added to the core module reaches the page without a UI change.
        "statuses": sorted(STATUSES),
        "rows": [
            {
                "corpus_id": r.corpus_id,
                "target_db": r.target_db,
                "status": r.status,
                "documents": r.documents,
                "chunks": r.chunks,
                "detail": r.detail,
                "ok": r.ok,
            }
            for r in rows
        ],
    }
