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
    # O24 — the ui-write-surface gate's M2 origin-flagged store (SME-3,
    # 2026-07-21): SEAL says one thing, the support team knows another, and
    # only the application owner (AO privilege) can fix SEAL. Overrides are
    # kept SIDE BY SIDE with the source value (origin flag on every row),
    # never write the graph, and feed the source-corrections report.
    {
        "id": "seal-contact-override",
        "title": "SEAL contacts — operate-manager override list (L1/L2)",
        "kind": "override",
        "source": "config/overrides/seal-contact-overrides.csv",
        "tier": None,
        "available": True,
    },
)

# The committed override-list column order — the draft artifact reproduces the
# WHOLE file (existing rows + drafts) so committing it is a plain replace.
OVERRIDE_HEADER = (
    "app_seal_id",
    "role_name",
    "seal_holder_sid",
    "override_holder_sid",
    "override_holder_name",
    "rationale",
    "authored_by",
    "authored_on",
    "status",
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
        if domain_id == "seal-contact-override":
            return self._select(
                "SELECT app_seal_id, role_name, origin, holder_sid, holder_name, "
                "rationale, authored_by, authored_on, status "
                "FROM v_seal_contact_grid"
            )
        raise UnknownDomainError(domain_id)

    def override_rows(self) -> list[dict]:
        """The committed override list in file column order (for the full-file
        draft artifact)."""
        cols = ", ".join(OVERRIDE_HEADER)
        return self._select(f"SELECT {cols} FROM seal_contact_override ORDER BY line_no").rows

    def source_corrections(self) -> list[dict]:
        return self._select("SELECT * FROM v_source_corrections").rows

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


def mapping_options(token: str, sessions: InMemorySessionStore, store: MappingStore) -> dict:
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
    writer.writerow(
        [
            "source_label",
            "source_key",
            "relationship",
            "rel_props",
            "target_label",
            "target_key",
            "create_target_if_missing",
            "note",
            "authored_by",
            "authored_on",
        ]
    )
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
        writer.writerow(
            [
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
            ]
        )

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


# ---------------------------------------------------------------------------
# O24 — SEAL-contact overrides (ui-write-surface gate SME-3: M2 tier).
# The server still writes NOTHING: drafting returns the UPDATED committed
# file as an artifact; the mapping-store table persists it once committed
# (the file-to-table loop that keeps var/mapping.db rebuildable).
# ---------------------------------------------------------------------------


def draft_override(
    entries: list[dict], token: str, sessions: InMemorySessionStore, store: MappingStore
) -> dict:
    """Validate drafted override entries and return the complete updated
    config/overrides/seal-contact-overrides.csv content (existing committed
    rows + the drafts). Fail-closed mirror of the store's own ingestion rules
    so a returned artifact can never be refused at materialization."""
    from drydocs_core.models.seal import canonicalize_role

    session = _authorize(token, sessions)
    if not entries:
        raise ChangesetValidationError("no override entries drafted")

    today = date.today().isoformat()
    existing = store.override_rows()
    new_rows: list[dict] = []
    for i, entry in enumerate(entries, start=1):
        app = str(entry.get("app_seal_id") or "").strip()
        role = canonicalize_role(entry.get("role_name"))
        seal_sid = str(entry.get("seal_holder_sid") or "").strip()
        override_sid = str(entry.get("override_holder_sid") or "").strip()
        rationale = str(entry.get("rationale") or "").strip()
        if not app:
            raise ChangesetValidationError(f"entry {i}: app_seal_id is required")
        if role is None:
            raise ChangesetValidationError(
                f"entry {i}: role_name {entry.get('role_name')!r} does not "
                "canonicalize to a SEAL role"
            )
        if not override_sid:
            raise ChangesetValidationError(f"entry {i}: override_holder_sid is required")
        if seal_sid and seal_sid == override_sid:
            raise ChangesetValidationError(
                f"entry {i}: override equals the SEAL value — not a correction"
            )
        if not rationale:
            raise ChangesetValidationError(
                f"entry {i}: rationale is REQUIRED — it becomes the "
                "source-corrections report's justification column"
            )
        new_rows.append(
            {
                "app_seal_id": app,
                "role_name": role,
                "seal_holder_sid": seal_sid,
                "override_holder_sid": override_sid,
                "override_holder_name": str(entry.get("override_holder_name") or "").strip(),
                "rationale": rationale,
                "authored_by": session.persona_id,  # server-stamped, never client-supplied
                "authored_on": today,
                "status": "active",
            }
        )

    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(OVERRIDE_HEADER)
    for row in [*existing, *new_rows]:
        writer.writerow(["" if row.get(c) is None else row.get(c) for c in OVERRIDE_HEADER])
    return {
        "filename": "seal-contact-overrides.csv",
        "csv": out.getvalue(),
        "entries": len(new_rows),
        "total_rows": len(existing) + len(new_rows),
        "note": (
            "The server wrote NOTHING. This is the complete updated override list — "
            "replace config/overrides/seal-contact-overrides.csv with it and commit "
            "(git review is the review); var/mapping.db rematerializes it on the next "
            "read. Overrides NEVER write the graph and NEVER replace the SEAL value — "
            "the surfaces keep both, origin-flagged, and the source-corrections report "
            "carries the fix request to the application owners (AO privilege)."
        ),
    }


def source_corrections_report(
    token: str, sessions: InMemorySessionStore, store: MappingStore
) -> dict:
    """The AO-facing artifact: every ACTIVE override with the SEAL current
    value, the corrected value, author and rationale — formatted for the
    application owners, who alone hold the AO privilege to fix SEAL."""
    session = _authorize(token, sessions)
    rows = store.source_corrections()
    today = date.today().isoformat()

    lines = [
        "# SEAL source-corrections report — contact roles",
        "",
        f"Generated {today} by {session.persona_id} from "
        "config/overrides/seal-contact-overrides.csv (via the mapping-store "
        "materialization). DryDocs does NOT write SEAL or the graph: each row "
        "below is a correction request for the application owner, who holds "
        "the AO privilege required to update SEAL itself. Once SEAL is fixed, "
        "flip the row's status to corrected-in-seal in the committed list.",
        "",
        f"Outstanding corrections: {len(rows)}",
        "",
        "| Application (seal_id) | Role | SEAL currently shows | Correct to | Authored | Rationale |",
        "|---|---|---|---|---|---|",
    ]
    for r in rows:
        holder = r.get("override_holder_sid") or ""
        if r.get("override_holder_name"):
            holder = f"{holder} ({r['override_holder_name']})"
        authored = " ".join(p for p in (r.get("authored_by"), r.get("authored_on")) if p)
        lines.append(
            f"| {r['app_seal_id']} | {r['role_name']} "
            f"| {r.get('seal_holder_sid') or '(nobody assigned)'} "
            f"| {holder} | {authored} | {r['rationale']} |"
        )
    if not rows:
        lines.append("| — | — | — | — | — | (no active overrides) |")

    return {
        "filename": f"seal-contact-source-corrections-{today}.md",
        "markdown": "\n".join(lines) + "\n",
        "count": len(rows),
        "generated_on": today,
        "generated_by": session.persona_id,
    }
