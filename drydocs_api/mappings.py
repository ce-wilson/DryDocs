"""Mapping stewardship endpoints (O13) — pure, framework-free handlers.

Reads come from the mapping-store SQLite materialization (plan M2/M3:
drydocs.mapping_store — derived from the committed YAML/CSV, rebuildable,
never the gate-reviewed artifact). Writes DO NOT EXIST here: submitting a
changeset returns a config/manual-loads/ change ARTIFACT (CSV text + manifest
snippet) for the git → gate → loader chain. The server writes nothing; the
loader stays the only graph writer; no new HITL gates are introduced — the
artifact travels the K2-gated manual-loads mechanism as-is.

Role gate: steward or admin (user < steward < admin — the O13 persona model).
"""
from __future__ import annotations

import csv
import io
import sqlite3
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from drydocs_api.handlers import Forbidden
from drydocs_api.sessions import InMemorySessionStore, Session

MAPPING_ROLES = ("steward", "admin")

# The one changeset shape the manual-loads mechanism supports today (K2).
# Extending this is a deliberate change reviewed against the vocabulary.
K2_SHAPE = {
    "source_label": "ControlMJob",
    "relationship": "WAS_ASSOCIATED_WITH",
    "role": "seal_app_ref",
    "target_label": "BusinessApplication",
}

# Registry-driven domain strip (wf-mapping-01 ①). available=False rows render
# as placeholders until their manual table exists as a reconciler input.
DOMAINS: tuple[dict, ...] = (
    {
        "id": "ontology-map",
        "title": "Taxonomy ↔ Ontology map (the loading quintuple)",
        "kind": "quintuple",
        "source": "config/taxonomy-ontology-map.yaml",
        "tier": None,
        "available": True,
    },
    {
        "id": "job-application",
        "title": "Job → Application (tier-5 manual CSV)",
        "kind": "manual",
        "source": "config/manual-loads/",
        "tier": 5,
        "available": True,
    },
    {
        "id": "fid-seal",
        "title": "FID → seal_id (tier 2)",
        "kind": "manual",
        "source": "(K6/T2 — reconciler table not built yet)",
        "tier": 2,
        "available": False,
    },
    {
        "id": "alias-seal",
        "title": "ALIAS → seal_id (tier 4)",
        "kind": "manual",
        "source": "(T3 — reconciler table not built yet)",
        "tier": 4,
        "available": False,
    },
)


class UnknownDomainError(KeyError):
    """Raised for a domain id not in the registry (or not yet available)."""


class ChangesetValidationError(ValueError):
    """A draft entry failed validation — fail closed, return the reason."""


@dataclass(frozen=True)
class _Grid:
    keys: list[str]
    rows: list[dict]


class MappingStore:
    """Read-only accessor over the SQLite materialization. Builds the file on
    first use and REBUILDS it whenever the committed sources drift (source-hash
    comparison against the build-time meta rows — O14). The file is derived:
    safe to create, safe to replace, safe to delete."""

    def __init__(self, db_path: str | Path | None = None) -> None:
        if db_path is None:
            import os

            db_path = os.environ.get("DRYDOCS_MAPPING_DB")
        if db_path is None:
            from drydocs_core.mapping_store import DEFAULT_DB_PATH

            db_path = DEFAULT_DB_PATH
        self._db_path = Path(db_path)

    def _connect(self) -> sqlite3.Connection:
        from drydocs_core.mapping_store import build, is_current

        # Absent, corrupt, or source-drifted all mean the same thing for a
        # derived file: rebuild from the committed sources (O14 guard).
        if not is_current(self._db_path):
            build(self._db_path).close()
        conn = sqlite3.connect(f"file:{self._db_path.as_posix()}?mode=ro", uri=True)
        conn.row_factory = sqlite3.Row
        return conn

    def _select(self, sql: str, params: tuple = ()) -> _Grid:
        conn = self._connect()
        try:
            cur = conn.execute(sql, params)
            keys = [d[0] for d in cur.description]
            return _Grid(keys=keys, rows=[dict(r) for r in cur.fetchall()])
        finally:
            conn.close()

    def grid(self, domain_id: str) -> _Grid:
        if domain_id == "ontology-map":
            return self._select(
                "SELECT id, source_label, relationship_type, role, target_label, "
                "prov_maps_to, matrix_row, vocab_id, status, confirmed_on, applied_on "
                "FROM ontology_mapping ORDER BY seq"
            )
        if domain_id == "job-application":
            return self._select(
                "SELECT file, folder_id, job_id, seal_id, create_target_if_missing, "
                "authored_by, authored_on, note "
                "FROM manual_mapping ORDER BY file, line_no"
            )
        raise UnknownDomainError(domain_id)

    def options(self) -> dict[str, list]:
        labels = self._select("SELECT label, class, prov_type FROM v_label_options")
        rels = self._select(
            "SELECT id, neo4j_label, role, from_node, to_node, domain FROM v_vocab_active"
        )
        summary = self._select("SELECT status, n FROM v_status_summary")
        return {"labels": labels.rows, "relationships": rels.rows, "status_summary": summary.rows}

    def relationship_registered(self, neo4j_label: str, role: str | None) -> bool:
        grid = self._select(
            "SELECT 1 FROM relationship_vocabulary "
            "WHERE neo4j_label = ? AND (role IS ? OR role = ?) LIMIT 1",
            (neo4j_label, role, role),
        )
        return bool(grid.rows)


def _authorize(token: str, sessions: InMemorySessionStore) -> Session:
    session = sessions.resolve(token)  # raises InvalidTokenError
    if session.role not in MAPPING_ROLES:
        raise Forbidden("mappings are steward/admin only (user < steward < admin)")
    return session


def list_domains(token: str, sessions: InMemorySessionStore) -> dict:
    _authorize(token, sessions)
    return {"domains": list(DOMAINS)}


def mapping_grid(
    domain_id: str, token: str, sessions: InMemorySessionStore, store: MappingStore
) -> dict:
    _authorize(token, sessions)
    if domain_id not in {d["id"] for d in DOMAINS if d["available"]}:
        raise UnknownDomainError(domain_id)
    grid = store.grid(domain_id)
    return {"domain": domain_id, "keys": grid.keys, "rows": grid.rows}


def mapping_options(
    token: str, sessions: InMemorySessionStore, store: MappingStore
) -> dict:
    _authorize(token, sessions)
    return store.options()


def draft_changeset(
    entries: list[dict], token: str, sessions: InMemorySessionStore, store: MappingStore
) -> dict:
    """Turn drafted grid assignments into the config/manual-loads/ change
    artifact (wf-mapping-01 ⑤): CSV text in the TEMPLATE column order plus a
    manifest snippet. Validation fails closed; rationale is REQUIRED (it
    becomes the CSV provenance column and the gate reviewer's context)."""
    session = _authorize(token, sessions)
    if not entries:
        raise ChangesetValidationError("changeset is empty")
    if not store.relationship_registered(K2_SHAPE["relationship"], K2_SHAPE["role"]):
        raise ChangesetValidationError(
            "relationship WAS_ASSOCIATED_WITH{role=seal_app_ref} is not registered "
            "in the vocabulary materialization — rebuild var/mapping.db"
        )

    today = date.today().isoformat()
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow([
        "source_label", "source_key", "relationship", "rel_props", "target_label",
        "target_key", "create_target_if_missing", "note", "authored_by", "authored_on",
    ])
    for i, entry in enumerate(entries, start=1):
        folder_id = str(entry.get("folder_id") or "").strip()
        job_id = str(entry.get("job_id") or "").strip()
        seal_id = str(entry.get("seal_id") or "").strip()
        rationale = str(entry.get("rationale") or "").strip()
        if not (folder_id and job_id and seal_id):
            raise ChangesetValidationError(
                f"entry {i}: folder_id, job_id and seal_id are all required"
            )
        if not rationale:
            raise ChangesetValidationError(
                f"entry {i}: rationale is REQUIRED — it is the CSV provenance "
                "column and the gate reviewer's context"
            )
        writer.writerow([
            K2_SHAPE["source_label"],
            f"folder_id={folder_id};job_id={job_id}",
            K2_SHAPE["relationship"],
            f"role={K2_SHAPE['role']}",
            K2_SHAPE["target_label"],
            f"seal_id={seal_id}",
            "true" if entry.get("create_target_if_missing") else "false",
            rationale,
            session.persona_id,
            today,
        ])

    filename = f"jobs-to-apps-{today}-{session.persona_id}.csv"
    manifest_snippet = (
        f"  - file: config/manual-loads/{filename}\n"
        f"    scope: <what these mappings cover — mechanism description>\n"
        f"    status: pending-load\n"
        f"    replaces_with: <REQUIRED — the automation path that retires this file>\n"
        f"    authored_by: {session.persona_id}\n"
    )
    return {
        "filename": filename,
        "csv": out.getvalue(),
        "manifest_snippet": manifest_snippet,
        "entries": len(entries),
        "lifecycle": "draft → submitted (PR) → gated → loaded (next load run)",
        "note": (
            "The server wrote NOTHING. Commit this file under config/manual-loads/, "
            "register it in manifest.yaml (fill replaces_with), and take it through "
            "the existing K2 gate; `drydocs load-manual-mappings` applies it on the "
            "next load run. Manual = tier 5 — it never overrides SEAL evidence."
        ),
    }
