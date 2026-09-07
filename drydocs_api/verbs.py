"""Agent verbs — named, purpose-built tools over REVIEWED QuerySpecs (R16).

::

    from drydocs_api.verbs import VERBS, verb, list_verbs
    verb("impact").spec      # the QuerySpec the verb IS: QUERY_SPECS["verb.impact.v1"]

WHAT A VERB IS. A verb is a NAME bound to one registry spec — nothing more. An
agent asking "what breaks if this job fails" should not have to know that the
answer is ``verb.impact.v1`` with ``-p job=...``; it says ``impact`` and names
the job. That is the whole layer: three verbs at the estate's grain —

    impact   blast radius: every job downstream of one job over the derived
             WAS_INFORMED_BY chain, with distance, gating condition and chain
    context  one job in its neighborhood: folder, data center, application,
             team, flags, direct upstream/downstream, IN/OUT conditions
    trace    the shortest job-chain path between two jobs, one row per hop

WHAT A VERB IS NOT. It is not new Cypher. Each verb's Cypher is a row in
``query_specs.QUERY_SPECS`` (``verb.<name>.v1``) and so passes every registry
guard the other rows pass — ``ensure_read_only`` and ``ensure_no_element_ids``
at registry build, the SchemaMeta/Uncertain exclusion rewrite, the vocabulary
and row-shape guards in ``tests/unit/``. A verb runs through the same
``validate_params`` -> ``execute_spec`` path ``POST /specs/{id}/run`` uses and
returns the same fourteen-key envelope, epistemic label and causes included
(R15), so the properties the item asks for — read-only, every executed
statement exposed, one epistemic wording — are INHERITED, never re-implemented.
Nothing here accepts caller-supplied Cypher; there is no operand for it.

WHAT SITS BESIDE IT, UNCHANGED. The generic ``neo4j-drydocs`` MCP server keeps
answering free Cypher for the sessions that want it, and R4's ephemeral specs
stay the reviewed escape hatch for a question no verb asks. Registering these
verbs as MCP tools is configuration beside this module — a server that calls
``agent_query.main(["verb", name, ...])`` — and not a component of its own.

ADDING A VERB. Write the QuerySpec (``verb.<name>.v1``, ``walk=`` declared —
the epistemic label is null without one, and null is the honest label only
for a spec that has said nothing), let the registry guards review it, then add
one :class:`Verb` row here. ``tests/unit/test_agent_verbs.py`` checks the
binding resolves and the declared shape is the spec's columns.
"""

from __future__ import annotations

from dataclasses import dataclass

from drydocs_api.query_specs import QUERY_SPECS, QuerySpec


class UnknownVerbError(KeyError):
    """No verb by that name; ``VERBS`` names the three."""

    def __str__(self) -> str:  # KeyError would quote the message; keep it plain
        return str(self.args[0]) if self.args else ""


@dataclass(frozen=True)
class Verb:
    """One verb: a name, the registry spec it is, and a one-line summary an
    agent router can show. ``spec`` and ``shape`` are read off the registry so
    the verb can never disagree with the row it binds."""

    name: str
    spec_id: str
    summary: str

    @property
    def spec(self) -> QuerySpec:
        return QUERY_SPECS[self.spec_id]

    @property
    def shape(self) -> tuple[str, ...]:
        """The documented row shape: the spec's column names, in order."""
        return tuple(c.name for c in self.spec.columns)


VERBS: dict[str, Verb] = {
    v.name: v
    for v in (
        Verb(
            name="impact",
            spec_id="verb.impact.v1",
            summary="Blast radius of one job: every downstream job the condition-derived "
            "chain reaches, with folder, distance, gating condition and shortest chain. "
            "Params: job (required), limit.",
        ),
        Verb(
            name="context",
            spec_id="verb.context.v1",
            summary="One job in its neighborhood: folder, data center, application and "
            "team, cyclic/critical/active, direct upstream and downstream jobs, IN/OUT "
            "conditions. One row per folder that defines the name. Params: job, limit.",
        ),
        Verb(
            name="trace",
            spec_id="verb.trace.v1",
            summary="Shortest job-chain path between two jobs, one row per hop with "
            "direction and the condition it rides. Params: from_job, to_job, limit.",
        ),
    )
}


def verb(name: str) -> Verb:
    """Resolve a verb by name; :class:`UnknownVerbError` names the valid set."""
    try:
        return VERBS[name]
    except KeyError:
        raise UnknownVerbError(f"unknown verb {name!r}; verbs: {', '.join(VERBS)}") from None


def list_verbs() -> list[dict[str, object]]:
    """One row per verb, for ``agent_query verbs`` and any router prompt: name,
    the spec it is, its params as declared, its row shape, and its summary."""
    return [
        {
            "name": v.name,
            "spec_id": v.spec_id,
            "summary": v.summary,
            "params": [
                {"name": p.name, "type": p.type, "required": p.required, "default": p.default}
                for p in v.spec.params
            ],
            "columns": list(v.shape),
            "database": v.spec.database,
            "classification": v.spec.classification,
        }
        for v in VERBS.values()
    ]
