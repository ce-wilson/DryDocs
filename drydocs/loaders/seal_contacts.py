"""SEAL Contact Data loader.

Long-format CSV: one row per (seal_id, role_name, employee_id) triple.
The pydantic SealContactRow canonicalizes role labels (e.g. 'L2 Manager'
-> 'L2 Operate Manager') so minor source drift doesn't reject rows.

If the actual SEAL Contact extract is wide-format (one row per app with
five role columns), add a small splayer in this module that emits one
SealContactRow per non-empty role column before invoking the loader.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import ClassVar

from drydocs_core.models import SealContactRow

from .base import BaseLoader

logger = logging.getLogger(__name__)


class SealContactsLoader(BaseLoader):
    name: ClassVar[str] = "seal_contacts.v1"
    source_id: ClassVar[str | None] = "seal:app-extract"
    cypher_path: ClassVar[Path | None] = (
        Path(__file__).resolve().parent / "cypher" / "seal_contacts.cypher"
    )
    row_model: ClassVar[type] = SealContactRow
    source_label: ClassVar[str] = "csv"

    # ---- N15: agreement-candidate detection (gate pending-source-correction,
    # SIGNED 2026-08-18, §B). The load PROPOSES and a steward confirms — an
    # unattended run can only ever leave an OPEN DRAFT (§B2/§B3); auto-retire
    # was offered at the gate and DECLINED. Detection never fails the load,
    # never writes the graph, and never touches seal_contact_override rows.

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._seen_holders: dict[tuple[str, str], str] = {}

    def to_params(self, model) -> dict:
        params = super().to_params(model)
        app = params.get("app_id")
        role = params.get("role_name")
        sid = params.get("employee_sid")
        if app and role and sid:
            self._seen_holders[(str(app), str(role))] = str(sid)
        return params

    def load(self):
        summary = super().load()
        try:
            n = propose_agreement_retirements(
                self._seen_holders, run_id=self.run_id, observed_on=self.loaded_at
            )
            if n:
                logger.info("agreement-candidate detection: %d open draft row(s)", n)
        except Exception:  # — §C3-class: detection is best-effort,
            # the load's own success is never hostage to the proposal channel.
            logger.warning("agreement-candidate detection skipped", exc_info=True)
        return summary


_RETIREMENT_DOMAIN = "seal-contact-retirement"


def detect_agreement_candidates(seen_holders: dict[tuple[str, str], str], conn) -> list[dict]:
    """Pure half: ACTIVE overrides whose corrected holder now EQUALS the loaded
    source holder for the same (app_seal_id, role_name). corrected-in-seal rows
    are skipped by the WHERE clause; disagreement is simply ignored."""
    rows = conn.execute(
        "SELECT app_seal_id, role_name, seal_holder_sid, override_holder_sid "
        "FROM seal_contact_override WHERE status = 'active'"
    ).fetchall()
    out = []
    for app, role, seal_sid, override_sid in rows:
        if seen_holders.get((app, role)) == override_sid:
            out.append(
                {
                    "app_seal_id": app,
                    "role_name": role,
                    "seal_holder_sid_at_authoring": seal_sid,
                    "override_holder_sid": override_sid,
                }
            )
    return out


def propose_agreement_retirements(
    seen_holders: dict[tuple[str, str], str],
    *,
    run_id: str,
    observed_on: str,
    conn=None,
) -> int:
    """Write ONE open draft (domain seal-contact-retirement) proposing each
    candidate's retirement, with the agreement evidence the steward's
    confirmation will archive onto the row (§B4): which run, which source
    value, observed when. Idempotent per candidate: a candidate already on an
    open retirement draft is not proposed again. Never flips any
    seal_contact_override.status — there is no UPDATE in this module."""
    from drydocs_core import mapping_store as ms

    own = conn is None
    if own:
        conn = _store_connection()
    try:
        candidates = detect_agreement_candidates(seen_holders, conn)
        if not candidates:
            return 0
        already = set()
        for d in ms.open_drafts(conn, domain=_RETIREMENT_DOMAIN):
            for payload in ms.draft_payloads(conn, d["draft_id"]):
                already.add((payload.get("app_seal_id"), payload.get("role_name")))
        fresh = [c for c in candidates if (c["app_seal_id"], c["role_name"]) not in already]
        if not fresh:
            return 0
        payloads = [
            {
                **c,
                "proposed_status": "corrected-in-seal",
                "agreement_run_id": run_id,
                "agreement_source_value": seen_holders[(c["app_seal_id"], c["role_name"])],
                "agreement_observed_on": observed_on,
            }
            for c in fresh
        ]
        written = ms.add_draft(
            conn,
            draft_id=f"agree-{run_id[:8]}",
            domain=_RETIREMENT_DOMAIN,
            payloads=payloads,
            authored_by=SealContactsLoader.name,
            authored_on=observed_on[:10],
        )
        conn.commit()
        return written
    finally:
        if own:
            conn.close()


def _store_connection():
    """The same derived-file chain the API wrapper runs (O14): rebuild when the
    committed sources drifted, plain connect when current. Core-only imports —
    a component may never reach into drydocs_api."""
    import os
    import sqlite3

    from drydocs_core.mapping_store import DEFAULT_DB_PATH, build, is_current

    db = Path(os.environ.get("DRYDOCS_MAPPING_DB") or DEFAULT_DB_PATH)
    if not is_current(db):
        return build(db)
    return sqlite3.connect(str(db))
