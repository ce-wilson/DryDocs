"""Mapping stewardship endpoints (O13) — pure, framework-free handlers.

Reads come from the mapping-store SQLite materialization (plan M2/M3:
drydocs.mapping_store — derived from the committed YAML/CSV, rebuildable,
never the gate-reviewed artifact). Writes DO NOT EXIST here: submitting a
changeset returns a config/manual-loads/ change ARTIFACT (CSV text + manifest
snippet) for the git → gate → loader chain. The server writes nothing; the
loader stays the only graph writer; no new HITL gates are introduced — the
artifact travels the K2-gated manual-loads mechanism as-is.

S4 (ADR 0009 rule 5) adds the one write this service does perform, and it is
NOT to a committed file: override/defined-mapping drafting writes ROWS to the
`draft` table in var/mapping.db, and a separate promote step turns a draft into
a unified diff for a branch. Git is still the only commit target — what changed
is that an unfinished or concurrent edit now has somewhere durable to live
instead of existing only as a whole-file download that the next editor's
download would silently overwrite.

Role gate: steward or admin (user < steward < admin — the O13 persona model).
"""

from __future__ import annotations

import csv
import difflib
import io
import sqlite3
import uuid
from dataclasses import dataclass
from datetime import date
from pathlib import Path

from drydocs_api.handlers import Forbidden
from drydocs_api.sessions import InMemorySessionStore, Session

MAPPING_ROLES = ("steward", "admin")

# The one changeset shape the manual-loads mechanism supports — the K7 RULED
# edge (gate seal-app-ref-edge-reshape §A1/§C1/§D1, 2026-08-03): folder-grain
# attribution onto the application's BatchProcessing :Port, AUTHORED per app
# code (§B1 — the loader fans out to folders via scheduler_contains_folder). The
# job-grain K2 shape is retired for authoring (§A1: no per-job application
# edge is authored going forward). K8 LANDED 2026-08-04: the loader chain
# (manual_mappings SUPPORTED_SHAPE + folder_attribution.v1) enforces this
# same shape end to end, so a drafted artifact is loadable once registered.
# Extending this is a deliberate change reviewed against the vocabulary.
K2_SHAPE = {
    "source_label": "ControlMFolder",
    "relationship": "BELONGS_TO_APPLICATION",
    "role": "seal_app_ref",
    "target_label": "Port",
}

# Registry-driven domain strip (wf-mapping-01 ①). available=False rows render
# as placeholders until their manual table exists as a reconciler input.
DOMAINS: tuple[dict, ...] = (
    {
        "id": "ontology-map",
        "title": "Taxonomy ↔ Ontology map (the loading quintuple)",
        "kind": "quintuple",
        "source": "config/taxonomy-ontology-map/",
        "tier": None,
        "available": True,
    },
    {
        # RETIRED at K15 (2026-08-05). K7 §A1 ruled attribution FOLDER-grain and K8
        # retired the job-grain edge, so this domain's coverage grid read a
        # relationship that no longer exists — it reported every row unresolved and
        # drafted a changeset the server refuses. Retired rather than re-bound: a
        # folder and its jobs carry the SAME app code, so a job-grain grid is N times rows
        # carrying ONE folder-level fact, and a grid that looks per-job invites being
        # read as per-job truth. Authoring lives at `app-code-mapping` (one row per app
        # code); "which application owns this job" stays a one-hop traversal.
        # The row STAYS in the registry, unavailable — a silently vanished domain reads
        # as a bug to anyone who bookmarked ?domain=job-application.
        "id": "job-application",
        "title": "Job → Application (RETIRED at K15 — folder grain supersedes)",
        "kind": "manual",
        "source": "(retired 2026-08-05 — author at app-code-mapping; jobs inherit their folder)",
        "tier": 5,
        "available": False,
    },
    {
        "id": "fid-seal",
        "title": "FID → app_id (tier 2)",
        "kind": "manual",
        "source": "(K6/T2 — reconciler table not built yet)",
        "tier": 2,
        "available": False,
    },
    {
        "id": "alias-seal",
        "title": "ALIAS → app_id (tier 4)",
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
    # K9 — the K7 defined-mapping store (gate seal-app-ref-edge-reshape
    # §E1/§E2, 2026-08-03): the steward-defined app-code → application
    # domain, O24 mechanics verbatim (committed CSV → mapping.db → this
    # console). Unlike the contact overrides it IS a graph-loadable source
    # of record (no machine feed exists to defer to), and override rows may
    # be PERMANENT — no corrected-in-source lifecycle in this domain.
    {
        "id": "app-code-mapping",
        "title": "App code → Application (the K7 defined-mapping store)",
        "kind": "defined",
        "source": "config/overrides/app-code-mappings.csv",
        "tier": None,
        "available": True,
    },
)

# The committed override-list column order — the draft artifact reproduces the
# WHOLE file (existing rows + drafts) so committing it is a plain replace.
#
# S3 BOUNDARY (gate business-application-identity §E1): the WIRE emits app_id — the
# committed FILE keeps app_seal_id. §E1 rules routes, QuerySpecs, column headers and
# fixtures, not the format of an already-committed CSV: renaming this tuple renames the
# header of config/overrides/seal-contact-overrides.csv, which mapping_store.py ingests
# by name, so every committed override list would stop parsing. The file format follows
# when §G3's separate gate retires the alias.
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

# The defined-mapping list's committed column order (K9). A NEW file, so no
# S3 alias boundary applies: the header is app_id from day one (§E1 wire
# rule) — there is no legacy CSV whose parsing a rename would break.
# K18: `tier` renamed `row_kind` end to end (column, wire, edge property)
# before it could surface in a QuerySpec under the ambiguous name.
APP_CODE_HEADER = (
    "app_code",
    "folder_id",
    "row_kind",
    "app_id",
    "declared_end_state",
    "origin",
    "rationale",
    "authored_by",
    "authored_on",
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

    # ── S4 draft buffer (ADR 0009 rule 5) ────────────────────────────────────
    # The read path above stays mode=ro deliberately: every other table is
    # derived from a committed file, and nothing in this service may write one.
    # `draft` is the single exception, so it gets the single writable door.

    def _connect_rw(self) -> sqlite3.Connection:
        from drydocs_core.mapping_store import build, is_current

        if not is_current(self._db_path):
            build(self._db_path).close()  # carries existing drafts across (S4)
        conn = sqlite3.connect(str(self._db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def add_draft(
        self,
        *,
        draft_id: str,
        domain: str,
        payloads: list[dict],
        authored_by: str,
        authored_on: str,
    ) -> int:
        from drydocs_core import mapping_store as core

        conn = self._connect_rw()
        try:
            return core.add_draft(
                conn,
                draft_id=draft_id,
                domain=domain,
                payloads=payloads,
                authored_by=authored_by,
                authored_on=authored_on,
            )
        finally:
            conn.close()

    def draft_payloads(self, draft_id: str) -> list[dict]:
        from drydocs_core import mapping_store as core

        conn = self._connect()
        try:
            return core.draft_payloads(conn, draft_id)
        finally:
            conn.close()

    def draft_domain(self, draft_id: str) -> str | None:
        from drydocs_core import mapping_store as core

        conn = self._connect()
        try:
            return core.draft_domain(conn, draft_id)
        finally:
            conn.close()

    def open_drafts(self, domain: str | None = None) -> list[dict]:
        from drydocs_core import mapping_store as core

        conn = self._connect()
        try:
            return core.open_drafts(conn, domain=domain)
        finally:
            conn.close()

    def set_draft_status(self, draft_id: str, status: str) -> int:
        from drydocs_core import mapping_store as core

        conn = self._connect_rw()
        try:
            return core.set_draft_status(conn, draft_id, status)
        finally:
            conn.close()

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
        # The SELECT aliases are where the S3 boundary sits: the derived table keeps the
        # committed file's column name, the grid the console receives emits app_id
        # (gate business-application-identity §E1 / ADR 0010 rule 4).
        if domain_id == "job-application":
            return self._select(
                "SELECT file, folder_id, job_id, seal_id AS app_id, "
                "create_target_if_missing, authored_by, authored_on, note "
                "FROM manual_mapping ORDER BY file, line_no"
            )
        if domain_id == "seal-contact-override":
            return self._select(
                "SELECT app_seal_id AS app_id, role_name, origin, holder_sid, holder_name, "
                "rationale, authored_by, authored_on, status "
                "FROM v_seal_contact_grid"
            )
        # No alias needed: the K9 file is post-S3, so table, grid and wire all
        # already say app_id.
        if domain_id == "app-code-mapping":
            return self._select(
                "SELECT app_code, folder_id, row_kind, app_id, declared_end_state, "
                "origin, rationale, authored_by, authored_on "
                "FROM v_app_code_grid"
            )
        raise UnknownDomainError(domain_id)

    def override_rows(self) -> list[dict]:
        """The committed override list in file column order (for the full-file
        draft artifact)."""
        cols = ", ".join(OVERRIDE_HEADER)
        return self._select(f"SELECT {cols} FROM seal_contact_override ORDER BY line_no").rows

    def app_code_rows(self) -> list[dict]:
        """The committed defined-mapping list in file column order (for the
        full-file draft artifact)."""
        cols = ", ".join(APP_CODE_HEADER)
        return self._select(f"SELECT {cols} FROM app_code_mapping ORDER BY line_no").rows

    def app_code_migrations(self) -> list[dict]:
        return self._select("SELECT * FROM v_dual_coded_migrations").rows

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
            f"relationship {K2_SHAPE['relationship']}{{role={K2_SHAPE['role']}}} is "
            "not registered in the vocabulary materialization — rebuild var/mapping.db"
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
        # K7 §A1/§B1: authoring is per APP CODE (job identity is retired —
        # the loader fans a code out to its folders, jobs inherit).
        app_code = str(entry.get("app_code") or "").strip()
        app_id = str(entry.get("app_id") or "").strip()
        rationale = str(entry.get("rationale") or "").strip()
        if not (app_code and app_id):
            raise ChangesetValidationError(
                f"entry {i}: app_code and app_id are both required — authoring is "
                "per app code (K7 §B1); the job-grain changeset was retired at §A1"
            )
        if not rationale:
            raise ChangesetValidationError(
                f"entry {i}: rationale is REQUIRED — it is the CSV provenance "
                "column and the gate reviewer's context"
            )
        writer.writerow(
            [
                K2_SHAPE["source_label"],
                f"app_code={app_code}",
                K2_SHAPE["relationship"],
                f"role={K2_SHAPE['role']}",
                K2_SHAPE["target_label"],
                # Post-S3 grammar: the K7 rekey (gate §F2) IS the authorized
                # format change, and no committed manual CSV exists producer-side
                # (manifest files: []) — so the new artifact says app_id outright.
                f"app_id={app_id}",
                "true" if entry.get("create_target_if_missing") else "false",
                rationale,
                session.persona_id,
                today,
            ]
        )

    filename = f"app-codes-to-apps-{today}-{session.persona_id}.csv"
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
        "lifecycle": "draft → submitted (PR) → gated → loaded (drydocs load-manual-mappings)",
        "note": (
            "The server wrote NOTHING. Commit this file under config/manual-loads/, "
            "register it in manifest.yaml (fill replaces_with), and take it through "
            "the existing K2 gate. The K8 folder-grain loader chain enforces this "
            "same shape end to end (manual_mappings SUPPORTED_SHAPE), so the "
            "registered file loads via `drydocs load-manual-mappings`. Manual = "
            "tier 5 — it never overrides SEAL evidence."
        ),
    }


# ---------------------------------------------------------------------------
# O24 — SEAL-contact overrides (ui-write-surface gate SME-3: M2 tier).
#
# S4 / ADR 0009 rule 5 changed the WRITE shape here. Drafting used to return
# the complete updated file (commit-by-replace) — correct for one small list
# and one editor, and unable to survive a second: two sessions each got a whole
# file built from the same committed base, so whichever was committed last
# silently erased the other's work. Drafting now writes ROWS to the mapping.db
# draft buffer, and a separate promote step turns a draft into a unified diff
# for a branch.
#
# What has NOT changed, and is the whole point of the ADR: the server still
# writes no committed file. Git remains the only commit target; promotion
# produces a diff a human applies and a gate reviews.
# ---------------------------------------------------------------------------

#: domain id -> (mapping_store module attribute holding the committed path,
#: committed column order). Resolved at CALL time via getattr so tests can
#: monkeypatch the module constant and redirect the whole chain at a fixture.
_DOMAIN_FILES = {
    "seal-contact-override": ("SEAL_CONTACT_OVERRIDES_PATH", OVERRIDE_HEADER),
    "app-code-mapping": ("APP_CODE_MAPPINGS_PATH", APP_CODE_HEADER),
}


def _committed_path(domain: str) -> Path:
    from drydocs_core import mapping_store as core

    attr, _ = _DOMAIN_FILES[domain]
    return Path(getattr(core, attr))


def _new_draft_id(persona_id: str) -> str:
    """A per-session draft id.

    Random, not derived: two sessions must land on DIFFERENT ids even when they
    draft byte-identical rows at the same moment — distinct ids are exactly what
    makes concurrent drafts survive each other. The persona prefix keeps it
    readable in `v_open_drafts` without making it guessable-by-collision.
    """
    return f"{persona_id}-{uuid.uuid4().hex[:8]}"


def draft_override(
    entries: list[dict],
    token: str,
    sessions: InMemorySessionStore,
    store: MappingStore,
    *,
    draft_id: str | None = None,
) -> dict:
    """Validate drafted override entries and WRITE THEM AS ROWS to the draft
    buffer. Returns a receipt, not a file — promotion emits the diff.

    Validation is unchanged and still fail-closed against the store's own
    ingestion rules, so a stored draft can never be one the committed file
    would refuse. Pass ``draft_id`` to append to an existing draft; omit it to
    start a new one.
    """
    from drydocs_core.models.seal import canonicalize_role

    session = _authorize(token, sessions)
    if not entries:
        raise ChangesetValidationError("no override entries drafted")

    today = date.today().isoformat()
    existing = store.override_rows()
    new_rows: list[dict] = []
    for i, entry in enumerate(entries, start=1):
        app = str(entry.get("app_id") or "").strip()
        role = canonicalize_role(entry.get("role_name"))
        seal_sid = str(entry.get("seal_holder_sid") or "").strip()
        override_sid = str(entry.get("override_holder_sid") or "").strip()
        rationale = str(entry.get("rationale") or "").strip()
        if not app:
            raise ChangesetValidationError(f"entry {i}: app_id is required")
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
                # File-column name — see the OVERRIDE_HEADER boundary note above.
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

    draft_id = draft_id or _new_draft_id(session.persona_id)
    written = store.add_draft(
        draft_id=draft_id,
        domain="seal-contact-override",
        payloads=new_rows,
        authored_by=session.persona_id,
        authored_on=today,
    )
    return {
        "draft_id": draft_id,
        "domain": "seal-contact-override",
        "entries": written,
        "pending": len(store.draft_payloads(draft_id)),
        "committed_rows": len(existing),
        "note": (
            "Drafted to var/mapping.db — NO committed file was written. The rows are "
            "durable across a store rebuild and do not collide with another session's "
            "draft. Promote this draft_id to get the diff to apply and commit "
            "(git review is the review). Overrides NEVER write the graph and NEVER "
            "replace the SEAL value — the surfaces keep both, origin-flagged, and the "
            "source-corrections report carries the fix request to the application "
            "owners (AO privilege)."
        ),
    }


def list_drafts(
    token: str, sessions: InMemorySessionStore, store: MappingStore, domain: str | None = None
) -> dict:
    """Pending drafts, one entry per editing session — the surface that makes
    a second editor's work visible instead of silently overwritable."""
    _authorize(token, sessions)
    return {"drafts": store.open_drafts(domain)}


def promote_draft(
    draft_id: str, token: str, sessions: InMemorySessionStore, store: MappingStore
) -> dict:
    """Turn an open draft into a unified diff against the committed file.

    This is the promote half of ADR 0009 rule 5: propose in the DB, land in git.
    The diff is purely ADDITIVE — the committed text is carried through
    verbatim and the drafted rows are appended — so it applies cleanly to the
    file it was generated against and a reviewer sees exactly the new rows.

    The server still writes nothing. The caller applies the diff on a branch,
    the gate reviews it, and var/mapping.db rematerializes from the committed
    file on the next read.
    """
    _authorize(token, sessions)
    domain = store.draft_domain(draft_id)
    if domain is None:
        raise UnknownDomainError(f"no draft {draft_id!r}")
    if domain not in _DOMAIN_FILES:
        raise UnknownDomainError(f"draft {draft_id!r} targets unknown domain {domain!r}")
    payloads = store.draft_payloads(draft_id)
    if not payloads:
        raise ChangesetValidationError(
            f"draft {draft_id!r} has no open entries (already promoted or discarded)"
        )

    _, header = _DOMAIN_FILES[domain]
    path = _committed_path(domain)
    committed = path.read_text(encoding="utf-8")
    new_text = _append_rows(committed, header, payloads)

    rel = _repo_relative(path)
    diff = "".join(
        difflib.unified_diff(
            committed.splitlines(keepends=True),
            new_text.splitlines(keepends=True),
            fromfile=f"a/{rel}",
            tofile=f"b/{rel}",
        )
    )
    store.set_draft_status(draft_id, "promoted")
    return {
        "draft_id": draft_id,
        "domain": domain,
        "path": rel,
        "filename": f"{path.stem}-{draft_id}.patch",
        "diff": diff,
        "entries": len(payloads),
        "note": (
            "The server wrote NOTHING. Apply this diff on a branch "
            "(`git apply <file>`), review it, and commit — git is the only commit "
            "target. The draft rows stay in var/mapping.db marked 'promoted' as the "
            "record of what was proposed."
        ),
    }


def _append_rows(committed: str, header: tuple[str, ...], rows: list[dict]) -> str:
    """Committed text carried through VERBATIM with the drafted rows appended.

    Verbatim matters: rebuilding the whole file from parsed rows would rewrite
    quoting and line endings the author never touched, turning a two-line
    addition into a whole-file diff that no reviewer can read — and that is
    also what makes two concurrent promotions conflict on every line instead of
    only where they actually disagree.
    """
    if committed and not committed.endswith("\n"):
        committed += "\n"
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    for row in rows:
        writer.writerow(["" if row.get(c) is None else row.get(c) for c in header])
    return committed + out.getvalue()


def _repo_relative(path: Path) -> str:
    """Repo-relative POSIX path for the diff header, with an absolute-path
    fallback so a fixture outside the repo still produces a readable diff."""
    import drydocs_core
    from drydocs_core.repo_paths import repo_root

    # Follows the CALLER's checkout (Idea-109): a fixture inside a worktree is
    # repo-relative to THAT tree, and anchoring on the install would push it down
    # the ValueError branch and print a bare filename in the diff header.
    root = repo_root(Path(drydocs_core.__file__).resolve().parent.parent)
    try:
        return path.resolve().relative_to(root).as_posix()
    except ValueError:
        return path.name


# ---------------------------------------------------------------------------
# K9 — the K7 defined-mapping store (gate seal-app-ref-edge-reshape §E1/§E2).
# O24 mechanics verbatim, including the S4 move to the draft buffer: the server
# writes NOTHING to a committed file — drafting writes rows, promotion emits
# the diff, git review is the review, and var/mapping.db rematerializes once
# committed. Store rows never write the graph (§E3); the K8 loader is the only
# graph writer.
#
# Converted alongside the overrides rather than left on commit-by-replace: it
# is the same mechanism on a sibling file, both share promote_draft(), and two
# different write models living in one module is exactly the confusion ADR 0009
# set out to remove.
# ---------------------------------------------------------------------------


def draft_app_code_mapping(
    entries: list[dict],
    token: str,
    sessions: InMemorySessionStore,
    store: MappingStore,
    *,
    draft_id: str | None = None,
) -> dict:
    """Validate drafted defined-mapping rows and WRITE THEM AS ROWS to the
    draft buffer. Returns a receipt; promotion emits the diff.

    Validation is the STORE'S OWN rule set (shared function), so a stored draft
    can never be refused at materialization — including the 1:1 duplicate check
    against the already-committed rows.
    """
    from drydocs_core.mapping_store import MappingStoreError, validate_app_code_row

    session = _authorize(token, sessions)
    if not entries:
        raise ChangesetValidationError("no defined-mapping entries drafted")

    today = date.today().isoformat()
    existing = store.app_code_rows()
    # Seed the duplicate check with the committed rows: a draft that re-authors
    # an existing (app_code, folder_id, origin) key is a defect, not an edit.
    seen: set[tuple[str, str, str]] = {
        (r["app_code"], r["folder_id"] or "", r["origin"] or "") for r in existing
    }
    new_rows: list[dict] = []
    for i, entry in enumerate(entries, start=1):
        candidate = {
            **entry,
            "origin": entry.get("origin") or "defined",
            "authored_by": session.persona_id,  # server-stamped, never client-supplied
            "authored_on": entry.get("authored_on") or today,
        }
        try:
            new_rows.append(validate_app_code_row(candidate, where=f"entry {i}", seen=seen))
        except MappingStoreError as exc:
            raise ChangesetValidationError(str(exc)) from exc

    draft_id = draft_id or _new_draft_id(session.persona_id)
    written = store.add_draft(
        draft_id=draft_id,
        domain="app-code-mapping",
        payloads=new_rows,
        authored_by=session.persona_id,
        authored_on=today,
    )
    return {
        "draft_id": draft_id,
        "domain": "app-code-mapping",
        "entries": written,
        "pending": len(store.draft_payloads(draft_id)),
        "committed_rows": len(existing),
        "note": (
            "Drafted to var/mapping.db — NO committed file was written. Promote this "
            "draft_id to get the diff to apply and commit (git review is the review). "
            "Rows never write the graph — the K8 loader fans each code out to its "
            "folders and stays the only graph writer (§E3). Overrides in THIS domain "
            "may be PERMANENT (§E2): the arrangement is the arrangement, so the "
            "rationale travels with the row instead of a corrected-in-source lifecycle."
        ),
    }


def app_code_migration_report(
    token: str, sessions: InMemorySessionStore, store: MappingStore
) -> dict:
    """The §B2 stalled-migration surface: every dual-coded row with the end state
    it declared.

    Tier 3 was admitted at the K7 gate ON THE CONDITION that the end state be
    DECLARED. A declaration nothing ever reads back is not a condition, it is a
    form field — so this is where it is read, and "temporarily dual-coded"
    cannot quietly become the permanent state nobody re-opens.

    LIFTED FROM `wip/k9-laptop` (`bfb2f0b`) at J30. The shipped K9 built the
    `v_dual_coded_migrations` view and the authoring UI that writes
    `declared_end_state`, but no reader: the view had exactly one consumer in
    the whole tree, a unit test. The parallel implementation had this endpoint,
    which is the only thing either version had that the other lacked.
    """
    _authorize(token, sessions)
    rows = store.app_code_migrations()
    return {"migrations": rows, "count": len(rows)}


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
        "| Application (app_id) | Role | SEAL currently shows | Correct to | Authored | Rationale |",
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
