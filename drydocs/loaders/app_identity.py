"""The pre-cutover :BusinessApplication refusal (S10).

WHAT THIS PREVENTS. Gate `business-application-identity` (SIGNED OFF 2026-07-27)
re-keyed the canonical application node from the registry-named ``seal_id`` to the
neutral ``app_id``. Its §C2 states the hazard exactly: a Neo4j uniqueness
constraint IGNORES NULLS, so a graph holding pre-cutover nodes — ``seal_id`` set,
``app_id`` null — does not reject a post-cutover ``MERGE (a:BusinessApplication
{app_id: …})``. The MERGE simply cannot see them, mints a SECOND canonical node
for an application that already exists, and the very next ``SET a.seal_id = …``
collides with the original's separately-constrained ``seal_id``.

WHY A GUARD AND NOT A COMMENT. That paragraph existed in the gate, in
``seal_applications.cypher``, and in this repo's graph-tests — and it still
happened. A company run of ``drydocs load seal_applications`` against a graph that
had taken the S3 code but not the S3 re-key died on
``Neo.ClientError.Schema.ConstraintValidationFailed`` MID-LOAD. Mid-load is the
part that matters: batches commit per flush, so the crash leaves a partially
doubled graph rather than rolling back to a clean one.

WHY THE EXISTING DETECTOR IS NOT THIS. ``graph-tests/business-application-identity``
TC-01 asks exactly this question, but it is a verification suite — it runs when
someone runs ``graph-verify``, which is AFTER the loader has done the damage. A
detector that reports the twin is not the guard that prevents it.

SCOPE. Only loaders that MERGE the canonical node can mint the twin. The MATCH-only
sites (``batch_port_orchestrator``, ``seal_attribution``, ``seal_contacts``,
``folder_attribution``) have the opposite failure — a miss writes nothing — which
their own registry-presence refusals already cover.

This REFUSES; it never repairs. Backfilling ``app_id`` on pre-cutover nodes is a
migration, and a loader that quietly migrated the graph it was pointed at would be
a worse version of the same problem.
"""

from __future__ import annotations

from drydocs_core.run_log import LoaderRunLog

from .base import BaseLoader, LoadSummary


class PreCutoverApplicationGuard:
    """Mixin: refuse the load when the target database holds a pre-S3 application.

    Mix in BEFORE :class:`~drydocs.loaders.base.BaseLoader` so the MRO reaches
    this ``_load`` first::

        class SealApplicationsLoader(PreCutoverApplicationGuard, BaseLoader):

    The check runs before ``super()._load`` — which is what reaches
    ``_preflight_indexes`` and ``_open_run`` — so a refused load writes nothing at
    all, not even the :JobRun. That is the established refusal idiom
    (``BatchPortOrchestratorLoader._assert_endpoint_registries_present``).
    """

    def _load(
        self: BaseLoader,  # type: ignore[misc]
        summary: LoadSummary,
        run_log: LoaderRunLog | None,
    ) -> LoadSummary:
        self._assert_no_pre_cutover_applications()
        return super()._load(summary, run_log)  # type: ignore[misc]

    def _assert_no_pre_cutover_applications(self: BaseLoader) -> None:  # type: ignore[misc]
        """Fail loudly on any :BusinessApplication a pre-S3 loader created.

        ``NOT a:SchemaMeta`` is not optional. ``schema_graph.cypher`` MERGEs
        ``:SchemaMeta:BusinessApplication {name: 'BusinessApplication'}`` exemplars
        that carry the REAL label with no key property, so a bare null-app_id count
        matches the exemplar and would refuse every load in a graph that has been
        bootstrapped — the ``_count_real_nodes`` precedent, same trap.
        """
        rows = self.client.run(
            "MATCH (a:BusinessApplication) "
            "WHERE NOT a:SchemaMeta AND a.app_id IS NULL "
            "RETURN count(a) AS stale"
        )
        stale = rows[0].get("stale", 0) if rows else 0
        if not stale:
            return
        raise RuntimeError(
            f"Loader {self.name}: refusing to load — {stale} :BusinessApplication "
            "node(s) in this database carry a null app_id, i.e. they were created "
            "before the seal_id -> app_id cutover (gate business-application-identity, "
            "2026-07-27). A uniqueness constraint IGNORES NULLS, so this loader's "
            "MERGE on app_id cannot match them: it would mint a SECOND canonical node "
            "per application and then fail on the seal_id constraint part-way through, "
            "leaving a partially doubled graph (batches commit per flush). "
            "Fix the graph first, then re-run: either rebuild it (the wipe-and-rebuild "
            "doctrine, §C4), or backfill `MATCH (a:BusinessApplication) WHERE "
            "a.app_id IS NULL SET a.app_id = a.seal_id` — and COUNT existing duplicates "
            "before either, because an earlier partial run may already have doubled some "
            "(`graph-tests/business-application-identity` TC-03 finds them)."
        )
