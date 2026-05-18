"""Hash-based snapshot writer.

Per v3 §I: anything at or above :Application versions on update.
Below :Application (jobs, folders, files) refreshes in place.

For each :Application / :Product / :CatalogLOB, we compute a stable hash
over the relationship-state we care about, compare it to the most recent
snapshot's hash, and emit a new snapshot only when the hash differs.

Retention: 5 years. A nightly ``prune`` call deletes snapshots whose
``valid_from`` is older than 5y AND that are NOT the most recent for
their entity (the latest snapshot is kept regardless of age so the
"current state" never disappears).
"""
from __future__ import annotations

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta, timezone
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ..neo4j_client import Neo4jClient

LOGGER = logging.getLogger(__name__)


class SnapshotWriter:
    """Materializes :ApplicationSnapshot / :ProductSnapshot / :CatalogLOBSnapshot."""

    def __init__(self, client: "Neo4jClient") -> None:
        self.client = client

    # ---- public API ------------------------------------------------------

    def write_application_snapshots(self) -> dict[str, int]:
        return self._write_snapshots(
            entity_label="Application",
            entity_key="seal_id",
            snapshot_label="ApplicationSnapshot",
            relationship_query="""
                MATCH (a:Application {seal_id: $entity_key})
                OPTIONAL MATCH (p:Product)-[:HAS_APPLICATION]->(a)
                OPTIONAL MATCH (a)-[:HAS_DEV_TEAM]->(dt:DevTeam)
                OPTIONAL MATCH (a)-[:HAS_MEMBERSHIP]->(:Membership)-[:HELD_BY]->(emp:Employee)
                RETURN
                    a.status            AS status,
                    a.risk_level        AS risk_level,
                    a.sox_governed      AS sox_governed,
                    a.deployment_module AS deployment_module,
                    p.product_id        AS product_id,
                    collect(DISTINCT dt.team_id)     AS dev_team_ids,
                    collect(DISTINCT emp.employee_id) AS contact_ids
            """,
        )

    def write_product_snapshots(self) -> dict[str, int]:
        return self._write_snapshots(
            entity_label="Product",
            entity_key="product_id",
            snapshot_label="ProductSnapshot",
            relationship_query="""
                MATCH (p:Product {product_id: $entity_key})
                OPTIONAL MATCH (pl:ProductLine)-[:HAS_PRODUCT]->(p)
                OPTIONAL MATCH (p)-[:HAS_APPLICATION]->(a:Application)
                RETURN
                    p.name                     AS name,
                    pl.product_line_id         AS product_line_id,
                    collect(DISTINCT a.seal_id) AS seal_ids
            """,
        )

    def write_lob_snapshots(self) -> dict[str, int]:
        return self._write_snapshots(
            entity_label="CatalogLOB",
            entity_key="lob_id",
            snapshot_label="CatalogLOBSnapshot",
            relationship_query="""
                MATCH (l:CatalogLOB {lob_id: $entity_key})
                OPTIONAL MATCH (l)-[:HAS_PRODUCT_LINE]->(pl:ProductLine)
                OPTIONAL MATCH (l)-[:RECONCILES_TO]->(s:BusinessSegment)
                RETURN
                    l.code AS code,
                    l.name AS name,
                    collect(DISTINCT pl.product_line_id) AS product_line_ids,
                    collect(DISTINCT s.code) AS segment_codes
            """,
        )

    def write_all(self) -> dict[str, dict[str, int]]:
        return {
            "applications": self.write_application_snapshots(),
            "products": self.write_product_snapshots(),
            "catalog_lobs": self.write_lob_snapshots(),
        }

    # ---- pruning ---------------------------------------------------------

    def prune_older_than(self, retention_years: int = 5) -> dict[str, int]:
        """Delete snapshots older than the retention window, keeping the most
        recent one per entity regardless of age."""
        cutoff = (datetime.now(timezone.utc) - timedelta(days=365 * retention_years)).date().isoformat()
        deleted = {}
        for label in ("ApplicationSnapshot", "ProductSnapshot", "CatalogLOBSnapshot"):
            rows = self.client.run(
                f"""
                MATCH (s:{label})
                WITH s, s.entity_key AS k
                ORDER BY s.valid_from DESC
                WITH k, collect(s) AS snaps
                UNWIND tail(snaps) AS old
                WITH old WHERE old.valid_from < date($cutoff)
                DETACH DELETE old
                RETURN count(*) AS deleted
                """,
                cutoff=cutoff,
            )
            deleted[label] = rows[0]["deleted"] if rows else 0
            LOGGER.info("Pruned %d %s older than %s", deleted[label], label, cutoff)
        return deleted

    # ---- internals -------------------------------------------------------

    def _write_snapshots(
        self,
        *,
        entity_label: str,
        entity_key: str,
        snapshot_label: str,
        relationship_query: str,
    ) -> dict[str, int]:
        entity_rows = self.client.run(
            f"MATCH (e:{entity_label}) RETURN e.{entity_key} AS k"
        )
        keys = [r["k"] for r in entity_rows if r["k"] is not None]

        n_new = 0
        n_unchanged = 0
        for key in keys:
            state_rows = self.client.run(relationship_query, entity_key=key)
            if not state_rows:
                continue
            state = self._stable(state_rows[0])
            digest = hashlib.sha256(state.encode("utf-8")).hexdigest()

            latest_rows = self.client.run(
                f"""
                MATCH (e:{entity_label} {{{entity_key}: $key}})
                OPTIONAL MATCH (e)-[:HAS_VERSION]->(s:{snapshot_label})
                RETURN s.hash AS h, s.snapshot_id AS id
                ORDER BY s.valid_from DESC LIMIT 1
                """,
                key=key,
            )
            latest_hash = latest_rows[0]["h"] if latest_rows else None

            if latest_hash == digest:
                n_unchanged += 1
                continue

            snapshot_id = str(uuid.uuid4())
            now_iso = datetime.now(timezone.utc).replace(microsecond=0).isoformat()

            self.client.run(
                f"""
                MATCH (e:{entity_label} {{{entity_key}: $key}})
                      -[:HAS_VERSION]->(s:{snapshot_label})
                WHERE s.valid_to IS NULL
                SET s.valid_to = date()
                """,
                key=key,
            )
            self.client.run(
                f"""
                MATCH (e:{entity_label} {{{entity_key}: $key}})
                CREATE (s:{snapshot_label} {{
                    snapshot_id: $snapshot_id,
                    entity_key:  $key,
                    hash:        $digest,
                    state_json:  $state_json,
                    valid_from:  date(),
                    valid_to:    null,
                    created_at:  datetime($now_iso)
                }})
                MERGE (e)-[:HAS_VERSION]->(s)
                """,
                key=key,
                snapshot_id=snapshot_id,
                digest=digest,
                state_json=state,
                now_iso=now_iso,
            )
            n_new += 1

        LOGGER.info(
            "%s snapshots: %d new, %d unchanged",
            snapshot_label,
            n_new,
            n_unchanged,
        )
        return {"new": n_new, "unchanged": n_unchanged}

    @staticmethod
    def _stable(d: dict[str, Any]) -> str:
        """Deterministic JSON for hashing: sort keys, sort lists."""
        def normalize(v: Any) -> Any:
            if isinstance(v, list):
                return sorted([normalize(x) for x in v if x is not None],
                              key=lambda x: str(x))
            if isinstance(v, dict):
                return {k: normalize(v[k]) for k in sorted(v)}
            return v

        return json.dumps(normalize(d), sort_keys=True, default=str)
