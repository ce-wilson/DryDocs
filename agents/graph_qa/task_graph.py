"""The Tier-2 task graph — agent working memory, IN-PROCESS ONLY (R6).

R1 gate ruling A (2026-07-23, `config/gate-log.md`): the enhance branch's task
graph is agent working memory in KGoT's NetworkX shape — it **dies with the
run**, and UI snapshots are ephemeral. Persisting it to `ddcontext` (retired
at the G102 fold, 2026-08-18; SYNTHESIZED, session-tagged, TTL-swept) was
considered and DEFERRED; proposing it again is a NEW gate, never a default.
That fold changes where such a proposal would land and nothing about the
deferral — the ruling was about persisting at all, not about where.

That ruling is why this module has no driver, no session, no database name and
no Cypher in it — and why `tests/unit/test_tier2.py` reads the source and fails
if any of those appear. A comment saying "don't persist this" is not a control;
a module that has nothing to persist with is. If persistence is ever gated in,
it belongs in a NEW module with a writer boundary, not smuggled in here.

Shape note: `snapshot()` emits edges as ``{source, target, via}`` — deliberately
the exact record the console's d3 pane already lays out (`web/src/lib/
forceLayout.ts`), so a captured iteration renders with no adapter and no second
viewer. Snapshots are CUMULATIVE state at the end of an iteration, not deltas,
so any one of them can be rendered alone.
"""

from __future__ import annotations

from dataclasses import dataclass

# What a node can be. The vocabulary is closed on purpose: this is working
# memory with four roles, not a general graph, and an open `kind` would drift
# into an unreviewed parallel ontology.
NODE_KINDS = ("question", "subquestion", "evidence", "answer")
EDGE_VIA = ("decomposes_to", "evidence_for", "answers")


@dataclass(frozen=True)
class TaskNode:
    id: str
    kind: str
    label: str
    iteration: int
    rows: int | None = None

    def as_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "label": self.label,
            "iteration": self.iteration,
            "rows": self.rows,
        }


@dataclass(frozen=True)
class TaskEdge:
    source: str
    target: str
    via: str

    def as_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "via": self.via}


class TaskGraph:
    """Append-only working memory for one question. Not thread-safe, not
    shared between runs, and never written anywhere."""

    def __init__(self) -> None:
        self._nodes: dict[str, TaskNode] = {}
        self._edges: list[TaskEdge] = []
        self._snapshots: list[dict] = []

    # -- construction ---------------------------------------------------------
    def add_node(
        self,
        kind: str,
        label: str,
        iteration: int,
        rows: int | None = None,
    ) -> str:
        if kind not in NODE_KINDS:
            raise ValueError(f"unknown task-graph node kind {kind!r}; expected one of {NODE_KINDS}")
        node_id = f"{kind}-{len(self._nodes) + 1}"
        self._nodes[node_id] = TaskNode(
            id=node_id, kind=kind, label=label, iteration=iteration, rows=rows
        )
        return node_id

    def add_edge(self, source: str, target: str, via: str) -> None:
        if via not in EDGE_VIA:
            raise ValueError(f"unknown task-graph edge via {via!r}; expected one of {EDGE_VIA}")
        for endpoint in (source, target):
            if endpoint not in self._nodes:
                raise KeyError(f"task-graph edge endpoint {endpoint!r} is not a node")
        self._edges.append(TaskEdge(source=source, target=target, via=via))

    # -- reading --------------------------------------------------------------
    @property
    def nodes(self) -> list[TaskNode]:
        return list(self._nodes.values())

    def nodes_of_kind(self, kind: str) -> list[TaskNode]:
        return [n for n in self._nodes.values() if n.kind == kind]

    @property
    def snapshots(self) -> list[dict]:
        return list(self._snapshots)

    def capture(self, iteration: int, phase: str = "iteration") -> dict:
        """Freeze the current state as one snapshot.

        `phase` disambiguates the two snapshots that can share an iteration
        number — the state at the END of round N, and the final state once the
        answer node lands. Without it a viewer showing "iteration 2" twice, with
        different contents, looks like a bug rather than a sequence.
        """
        if phase not in ("start", "iteration", "final"):
            raise ValueError(f"unknown snapshot phase {phase!r}")
        snapshot = {
            "iteration": iteration,
            "phase": phase,
            "nodes": [n.as_dict() for n in self._nodes.values()],
            "edges": [e.as_dict() for e in self._edges],
        }
        self._snapshots.append(snapshot)
        return snapshot
