"""SME Context-Intake — the O46 origin-flagged store + framework-free handlers.

The store half of the intake page (UI-WIP/sme-intake-page-plan.md §3 + §7):
evidence files land under the data root (never the repo tree), records land in
a SQLite store beside them, and every record is stamped at creation —
``origin: sme-intake`` (the O24 origin-flag precedent) and ``classification:
Internal`` (production failure email carries real names and incident detail;
there is no unlabeled default, CLAUDE.md §3).

Hard rules, all inherited:

- **NO graph writes.** Nothing in this module touches Neo4j; the load boundary
  is Q10's (corpus behind G31 → G32, the assignment edge behind Q10's own HITL
  gate). ``admin-accepted`` is a PARKED terminal state here — ``loaded`` exists
  in the vocabulary but no transition in this API can reach it.
- **Storage stays behind one seam** (the 2026-08-06 storage ruling): the store
  root is one configured base path (``DRYDOCS_DATA_ROOT/context-intake/``),
  identity is the sha256 digest, and records carry the RELATIVE key only —
  local → Linux share → object store must be a config change, never a code
  change. No path math above the seam.
- **Evidence is never edited.** A file lands whole, byte-for-byte (the
  adhoc-sme-email rule: a trimmed copy of evidence is no longer evidence).
  Thread handling changes the REVIEW PAYLOAD, never the file.
- **The server owns the status machine.** ``legal_transitions`` is returned per
  record per caller role; the UI renders buttons from it and never encodes the
  machine a second time (the IntakeStepper decision, 2026-08-06).

Thread reuse → ingest the diff (user direction 2026-08-06): people reuse old
email threads, so ingest detects thread identity — conversation headers where
the file carries them, normalized subject (Re:/FW: stripped), quoted-content
overlap against evidence already in the store — and on a match links the new
intake to the prior one(s) and computes the DELTA (the new content above the
quoted tail) as the review payload. Detection FLAGS, never auto-decides: the
SME's Adds-value / No-new-value ruling is the page's surface (O47).

Guard: ``tests/unit/test_intake_api.py`` — offline, framework-free, no Neo4j.
"""

from __future__ import annotations

import difflib
import hashlib
import json
import re
import sqlite3
import uuid
from datetime import UTC, datetime
from pathlib import Path

import yaml

from drydocs_api.handlers import Forbidden
from drydocs_api.sessions import InMemorySessionStore, Session
from drydocs_core.data_root import context_intake_dir

ORIGIN = "sme-intake"
CLASSIFICATION = "Internal"  # stamped at creation, unconditionally

ALLOWED_EXTENSIONS = (".msg", ".json", ".txt")  # .txt = kind:note pending the SME ruling

# ── the status machine (plan §7) — the ONE home of the transition rules ──────
# Roles: SME-side actions are open to every authenticated persona until the
# O47 sme persona lands in the roster; accept/return are admin-only.
_ANY = ("user", "steward", "admin")
_ADMIN = ("admin",)

STATUSES = (
    "draft",
    "ontology-reviewed",
    "correlated",
    "sme-confirmed",
    "admin-accepted",
    "admin-returned",
    "loaded",
    "no-new-value",
)

# status -> tuple of (to, action label, roles allowed to take it).
# `loaded` appears as a STATUS but never as a transition target: the load is
# Q10's, behind its gates — this API parks records at admin-accepted.
TRANSITIONS: dict[str, tuple[tuple[str, str, tuple[str, ...]], ...]] = {
    "draft": (("ontology-reviewed", "Review for ontology", _ANY),),
    "ontology-reviewed": (
        ("correlated", "Correlate", _ANY),
        ("draft", "Back to draft", _ANY),
    ),
    "correlated": (
        ("sme-confirmed", "Confirm", _ANY),
        ("draft", "Back to draft", _ANY),
    ),
    "sme-confirmed": (
        ("admin-accepted", "Accept", _ADMIN),
        ("admin-returned", "Send back", _ADMIN),
    ),
    "admin-returned": (
        ("sme-confirmed", "Re-confirm", _ANY),
        ("draft", "Rework", _ANY),
    ),
    "admin-accepted": (),  # parked: waiting on the Q10/G31/G32 gates
    "loaded": (),
    "no-new-value": (),
}

# A re-upload of changed bytes re-queues review from these states…
_REQUEUE_FROM = ("ontology-reviewed", "correlated", "sme-confirmed", "admin-returned")
# …and is refused outright once the record is accepted or closed.
_UPLOAD_CLOSED = ("admin-accepted", "loaded", "no-new-value")

# thread-overlap thresholds: a prior evidence counts as the quoted tail when
# at least this fraction of its content lines reappear, and it has enough
# lines for the match to mean something.
_OVERLAP_MIN_FRACTION = 0.6
_OVERLAP_MIN_LINES = 3

_REPO = Path(__file__).resolve().parent.parent
_CONTEXT_TYPES_YAML = _REPO / "config" / "taxonomy" / "context-types.yaml"


class IntakeValidationError(ValueError):
    """Bad input — unknown context type, disallowed file kind, empty payload."""


class UnknownIntakeError(KeyError):
    """Raised for an intake id the store has never issued."""


class IllegalTransitionError(ValueError):
    """A requested status change the machine does not allow from here."""


def _now() -> str:
    return datetime.now(UTC).isoformat(timespec="seconds")


def _active_context_types() -> set[str]:
    data = yaml.safe_load(_CONTEXT_TYPES_YAML.read_text(encoding="utf-8"))
    return {e["id"] for e in data["context_types"] if e["status"] == "active"}


# ── evidence text + preview (display-only; failure is a warning, never a
#    rejection — the file still lands) ───────────────────────────────────────

_DASH_TO_UNDERSCORE = str.maketrans("-", "_")

_HEADER_RE = re.compile(
    r"^(Subject|From|Date|Sent|Message-ID|In-Reply-To|References|Thread-Index)"
    r":[ \t]*(.+?)\s*$",
    re.IGNORECASE | re.MULTILINE,
)


def _printable_runs(data: bytes) -> str:
    """Best-effort text from a binary .msg: printable runs from the latin-1
    view plus the UTF-16LE view (where MAPI stores its strings). Never raises."""
    out: list[str] = []
    for text in (data.decode("latin-1", errors="ignore"), data.decode("utf-16-le", errors="ignore")):
        out.extend(re.findall(r"[\x20-\x7e\t]{4,}", text))
    return "\n".join(out)


def _extract_text(kind: str, data: bytes) -> str:
    if kind in ("txt", "json"):
        return data.decode("utf-8", errors="replace")
    return _printable_runs(data)


def _parse_preview(kind: str, data: bytes) -> dict:
    """Display-only preview: headers for .msg, keys for .json, first line for
    .txt. A parse failure lands as ``warning`` — the upload is never rejected."""
    preview: dict = {"kind": kind, "warnings": []}
    try:
        text = _extract_text(kind, data)
        if kind == "json":
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                preview["keys"] = sorted(parsed.keys())
            else:
                preview["keys"] = []
                preview["shape"] = f"{type(parsed).__name__}[{len(parsed)}]" if isinstance(
                    parsed, list
                ) else type(parsed).__name__
        else:
            # str.translate, not str.replace: the ADR 0009 write-primitive
            # guard (test_no_endpoint_writes_a_tracked_file) bans `.replace()`
            # calls by attribute name and cannot tell str from Path.
            headers = {
                m.group(1).lower().translate(_DASH_TO_UNDERSCORE): m.group(2)
                for m in _HEADER_RE.finditer(text)
            }
            for field in ("subject", "from", "date", "sent", "message_id", "in_reply_to", "references", "thread_index"):
                if field in headers:
                    preview[field] = headers[field]
            if kind == "txt":
                first = next((ln for ln in text.splitlines() if ln.strip()), "")
                preview["first_line"] = first[:200]
            if kind == "msg" and "subject" not in preview:
                preview["warnings"].append("no subject header recovered (MAPI parse is best-effort)")
    except (ValueError, UnicodeError) as exc:
        preview["warnings"].append(f"parse failed: {exc}")
    return preview


# ── thread identity (flag, never auto-decide) ────────────────────────────────

_SUBJECT_PREFIX_RE = re.compile(r"^(re|fw|fwd|aw)\s*(\[\d+\])?\s*:\s*", re.IGNORECASE)


def normalized_subject(subject: str) -> str:
    s = subject.strip()
    while True:
        stripped = _SUBJECT_PREFIX_RE.sub("", s)
        if stripped == s:
            break
        s = stripped
    return re.sub(r"\s+", " ", s).casefold()


def _content_lines(text: str) -> list[str]:
    return [ln.strip() for ln in text.splitlines() if ln.strip()]


def _overlap(new_lines: list[str], old_lines: list[str]) -> float:
    """Fraction of the PRIOR evidence's content lines that reappear verbatim —
    a reply carrying the thread quotes the old mail's lines wholesale."""
    if len(old_lines) < _OVERLAP_MIN_LINES:
        return 0.0
    new_set = set(new_lines)
    return sum(1 for ln in set(old_lines) if ln in new_set) / len(set(old_lines))


def _delta(new_lines: list[str], old_lines: list[str]) -> list[str]:
    """The new content above/around the quoted tail: lines of the new evidence
    that the prior evidence does not contain, order preserved."""
    matcher = difflib.SequenceMatcher(a=old_lines, b=new_lines, autojunk=False)
    out: list[str] = []
    for tag, _i1, _i2, j1, j2 in matcher.get_opcodes():
        if tag in ("insert", "replace"):
            out.extend(new_lines[j1:j2])
    return out


# ── the store ────────────────────────────────────────────────────────────────


def default_intake_root() -> Path:
    """``DRYDOCS_DATA_ROOT/context-intake/`` — the one configured base path
    (storage ruling 2026-08-06). Created on first write, not on import."""
    return context_intake_dir()


class IntakeStore:
    """SQLite record store + evidence staging under ONE root directory.

    Records reference evidence by ``rel_key`` (``<intake_id>/<filename>``,
    posix) and sha256 only — the root can move (local → share → object store)
    without any record lying.
    """

    def __init__(self, root: Path) -> None:
        self.root = Path(root)
        self._conn: sqlite3.Connection | None = None

    @property
    def conn(self) -> sqlite3.Connection:
        if self._conn is None:
            self.root.mkdir(parents=True, exist_ok=True)
            # FastAPI serves sync routes from a threadpool, so requests reach
            # this shared connection from varying threads. CPython's sqlite3
            # is compiled serialized (threadsafety 3): sharing is safe once
            # the same-thread check is relaxed, and keeping ONE connection
            # keeps each handler's multi-statement update a single commit.
            self._conn = sqlite3.connect(
                str(self.root / "intake.db"), check_same_thread=False
            )
            self._conn.row_factory = sqlite3.Row
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS intake (
                    intake_id      TEXT PRIMARY KEY,
                    created_at     TEXT NOT NULL,
                    created_by     TEXT NOT NULL,
                    origin         TEXT NOT NULL,
                    classification TEXT NOT NULL,
                    context_type   TEXT NOT NULL,
                    note           TEXT NOT NULL DEFAULT '',
                    area_json      TEXT NOT NULL DEFAULT '{}',
                    status         TEXT NOT NULL,
                    thread_of_json TEXT NOT NULL DEFAULT '[]',
                    thread_flagged INTEGER NOT NULL DEFAULT 0,
                    thread_decision TEXT,
                    review_payload TEXT
                );
                CREATE TABLE IF NOT EXISTS evidence (
                    evidence_id  TEXT PRIMARY KEY,
                    intake_id    TEXT NOT NULL,
                    filename     TEXT NOT NULL,
                    rel_key      TEXT NOT NULL,
                    sha256       TEXT NOT NULL,
                    size         INTEGER NOT NULL,
                    kind         TEXT NOT NULL,
                    pair_key     TEXT NOT NULL,
                    preview_json TEXT NOT NULL,
                    uploaded_at  TEXT NOT NULL,
                    superseded   INTEGER NOT NULL DEFAULT 0
                );
                CREATE TABLE IF NOT EXISTS event (
                    intake_id TEXT NOT NULL,
                    at        TEXT NOT NULL,
                    actor     TEXT NOT NULL,
                    action    TEXT NOT NULL,
                    detail    TEXT NOT NULL DEFAULT ''
                );
                """
            )
        return self._conn

    # -- records ------------------------------------------------------------

    def _record(self, intake_id: str) -> sqlite3.Row:
        row = self.conn.execute(
            "SELECT * FROM intake WHERE intake_id = ?", (intake_id,)
        ).fetchone()
        if row is None:
            raise UnknownIntakeError(intake_id)
        return row

    def _log(self, intake_id: str, actor: str, action: str, detail: str = "") -> None:
        self.conn.execute(
            "INSERT INTO event (intake_id, at, actor, action, detail) VALUES (?,?,?,?,?)",
            (intake_id, _now(), actor, action, detail),
        )

    def evidence_rows(self, intake_id: str, *, include_superseded: bool = False) -> list[sqlite3.Row]:
        q = "SELECT * FROM evidence WHERE intake_id = ?"
        if not include_superseded:
            q += " AND superseded = 0"
        return list(self.conn.execute(q + " ORDER BY uploaded_at, filename", (intake_id,)))

    def _all_prior_evidence(self, exclude_intake: str) -> list[sqlite3.Row]:
        return list(
            self.conn.execute(
                "SELECT * FROM evidence WHERE intake_id != ? AND superseded = 0",
                (exclude_intake,),
            )
        )

    def evidence_path(self, rel_key: str) -> Path:
        return self.root / Path(rel_key)


# ── record serialization + the legal-transitions map ─────────────────────────


def _serialize(row: sqlite3.Row) -> dict:
    rec = dict(row)
    rec["area"] = json.loads(rec.pop("area_json"))
    rec["thread_of"] = json.loads(rec.pop("thread_of_json"))
    rec["thread_flagged"] = bool(rec["thread_flagged"])
    return rec


def legal_transitions(record: dict, role: str) -> dict:
    """The per-record, per-role map the UI renders its buttons from — the
    server owns the machine (IntakeStepper decision, 2026-08-06)."""
    status = record["status"]
    allowed = [
        {"to": to, "action": action}
        for to, action, roles in TRANSITIONS[status]
        if role in roles
    ]
    out = {
        "status": status,
        "transitions": allowed,
        "waiting_on_gate": status == "admin-accepted",  # the Q10/G31/G32 park
        "terminal": status in ("loaded", "no-new-value"),
    }
    if record["thread_flagged"] and record["thread_decision"] is None and status == "draft":
        out["thread_decision_required"] = True
        out["thread_decisions"] = ["adds-value", "no-new-value"]
    return out


# ── handlers (pure; app.py is the thin FastAPI shell) ────────────────────────


def _authorize(token: str, sessions: InMemorySessionStore) -> Session:
    return sessions.resolve(token)  # raises InvalidTokenError


def create_intake(
    context_type: str,
    area: dict,
    note: str,
    token: str,
    sessions: InMemorySessionStore,
    store: IntakeStore,
) -> dict:
    session = _authorize(token, sessions)
    valid = _active_context_types()
    if context_type != "other" and context_type not in valid:
        raise IntakeValidationError(
            f"unknown context type '{context_type}' — the vocabulary is "
            "config/taxonomy/context-types.yaml (or 'other', with the detail in the note)"
        )
    if context_type == "other" and not note.strip():
        raise IntakeValidationError(
            "context type 'other' requires a note — the free text is the vocabulary-growth signal"
        )
    intake_id = uuid.uuid4().hex[:12]
    store.conn.execute(
        "INSERT INTO intake (intake_id, created_at, created_by, origin, classification,"
        " context_type, note, area_json, status) VALUES (?,?,?,?,?,?,?,?,?)",
        (
            intake_id,
            _now(),
            session.persona_id,
            ORIGIN,
            CLASSIFICATION,
            context_type,
            note,
            json.dumps(area or {}, sort_keys=True),
            "draft",
        ),
    )
    store._log(intake_id, session.persona_id, "created", f"context_type={context_type}")
    store.conn.commit()
    return get_intake(intake_id, token, sessions, store)


def add_evidence(
    intake_id: str,
    filename: str,
    data: bytes,
    token: str,
    sessions: InMemorySessionStore,
    store: IntakeStore,
) -> dict:
    """Land one evidence file: whole, digested, previewed, thread-checked.

    Same name + same bytes = idempotent no-op. Same name + CHANGED bytes
    supersedes the old row and re-queues review (status back to draft) —
    changed evidence is never silently swapped under a review in flight.
    """
    session = _authorize(token, sessions)
    record = store._record(intake_id)
    if record["status"] in _UPLOAD_CLOSED:
        raise IllegalTransitionError(
            f"intake {intake_id} is {record['status']} — evidence can no longer change"
        )
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise IntakeValidationError(
            f"'{ext}' is not an accepted evidence kind {ALLOWED_EXTENSIONS} "
            "(a third kind is an SME ruling, not a default)"
        )
    if not data:
        raise IntakeValidationError(f"{filename}: empty upload")
    safe_name = Path(filename).name  # no path components from the client
    digest = hashlib.sha256(data).hexdigest()
    kind = ext.lstrip(".")

    existing = store.conn.execute(
        "SELECT * FROM evidence WHERE intake_id = ? AND filename = ? AND superseded = 0",
        (intake_id, safe_name),
    ).fetchone()
    if existing is not None and existing["sha256"] == digest:
        return _evidence_out(store, intake_id, existing["evidence_id"], token, sessions)

    # the file lands WHOLE under the root; the record carries the relative key only
    rel_key = f"{intake_id}/{safe_name}"
    dest = store.evidence_path(rel_key)
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)

    preview = _parse_preview(kind, data)
    evidence_id = uuid.uuid4().hex[:12]

    if existing is not None:  # changed bytes: supersede + re-queue
        store.conn.execute(
            "UPDATE evidence SET superseded = 1 WHERE evidence_id = ?",
            (existing["evidence_id"],),
        )
        store._log(
            intake_id,
            session.persona_id,
            "evidence-superseded",
            f"{safe_name}: {existing['sha256'][:12]} -> {digest[:12]}",
        )
        if record["status"] in _REQUEUE_FROM:
            store.conn.execute(
                "UPDATE intake SET status = 'draft' WHERE intake_id = ?", (intake_id,)
            )
            store._log(
                intake_id,
                session.persona_id,
                "re-queued",
                f"changed evidence {safe_name} returned the review to draft",
            )

    store.conn.execute(
        "INSERT INTO evidence (evidence_id, intake_id, filename, rel_key, sha256, size,"
        " kind, pair_key, preview_json, uploaded_at) VALUES (?,?,?,?,?,?,?,?,?,?)",
        (
            evidence_id,
            intake_id,
            safe_name,
            rel_key,
            digest,
            len(data),
            kind,
            Path(safe_name).stem,
            json.dumps(preview, sort_keys=True),
            _now(),
        ),
    )
    store._log(intake_id, session.persona_id, "evidence-added", f"{safe_name} sha256={digest[:12]}")

    _check_thread(store, intake_id, kind, data, preview, session)
    store.conn.commit()
    return _evidence_out(store, intake_id, evidence_id, token, sessions)


def _check_thread(
    store: IntakeStore,
    intake_id: str,
    kind: str,
    data: bytes,
    preview: dict,
    session: Session,
) -> None:
    """Thread-identity detection against evidence already in the store
    (other intakes). Flags + computes the delta; NEVER decides."""
    new_text = _extract_text(kind, data)
    new_lines = _content_lines(new_text)
    new_subject = normalized_subject(preview.get("subject", ""))
    reply_refs = " ".join(
        str(preview.get(f, "")) for f in ("in_reply_to", "references")
    )

    matches: list[tuple[str, str]] = []  # (prior_intake_id, via)
    best_old_lines: list[str] | None = None
    for prior in store._all_prior_evidence(intake_id):
        p = json.loads(prior["preview_json"])
        via = None
        prior_mid = str(p.get("message_id", ""))
        if prior_mid and prior_mid in reply_refs:
            via = "conversation-headers"
        prior_subject = normalized_subject(p.get("subject", ""))
        if via is None and new_subject and prior_subject and new_subject == prior_subject:
            via = "normalized-subject"
        old_lines = None
        if via is None:
            path = store.evidence_path(prior["rel_key"])
            if path.exists():
                old_lines = _content_lines(_extract_text(prior["kind"], path.read_bytes()))
                if _overlap(new_lines, old_lines) >= _OVERLAP_MIN_FRACTION:
                    via = "quoted-content-overlap"
        if via is not None:
            matches.append((prior["intake_id"], via))
            if old_lines is None:
                path = store.evidence_path(prior["rel_key"])
                old_lines = (
                    _content_lines(_extract_text(prior["kind"], path.read_bytes()))
                    if path.exists()
                    else []
                )
            if best_old_lines is None or len(old_lines) > len(best_old_lines):
                best_old_lines = old_lines

    if not matches:
        return

    record = store._record(intake_id)
    prior_ids = sorted({m[0] for m in matches})
    known = set(json.loads(record["thread_of_json"]))
    delta_lines = _delta(new_lines, best_old_lines or [])
    store.conn.execute(
        "UPDATE intake SET thread_flagged = 1, thread_of_json = ?, review_payload = ?"
        " WHERE intake_id = ?",
        (
            json.dumps(sorted(known | set(prior_ids))),
            "\n".join(delta_lines),
            intake_id,
        ),
    )
    store._log(
        intake_id,
        session.persona_id,
        "thread-flagged",
        "; ".join(f"{iid} via {via}" for iid, via in matches),
    )


def _evidence_out(
    store: IntakeStore,
    intake_id: str,
    evidence_id: str,
    token: str,
    sessions: InMemorySessionStore,
) -> dict:
    out = get_intake(intake_id, token, sessions, store)
    out["evidence_id"] = evidence_id
    return out


def get_intake(
    intake_id: str, token: str, sessions: InMemorySessionStore, store: IntakeStore
) -> dict:
    session = _authorize(token, sessions)
    record = _serialize(store._record(intake_id))
    if session.role == "user" and record["created_by"] != session.persona_id:
        raise Forbidden("users see their own intakes; the queue is steward/admin")
    evidence = []
    for row in store.evidence_rows(intake_id):
        e = dict(row)
        e["preview"] = json.loads(e.pop("preview_json"))
        e["superseded"] = bool(e["superseded"])
        evidence.append(e)
    record["evidence"] = evidence
    record["legal_transitions"] = legal_transitions(record, session.role)
    return record


def list_intakes(token: str, sessions: InMemorySessionStore, store: IntakeStore) -> dict:
    session = _authorize(token, sessions)
    q = "SELECT * FROM intake"
    params: tuple = ()
    if session.role == "user":
        q += " WHERE created_by = ?"
        params = (session.persona_id,)
    rows = store.conn.execute(q + " ORDER BY created_at", params).fetchall()
    records = []
    for row in rows:
        rec = _serialize(row)
        rec["legal_transitions"] = legal_transitions(rec, session.role)
        records.append(rec)
    return {"intakes": records}


def transition(
    intake_id: str,
    to: str,
    note: str,
    token: str,
    sessions: InMemorySessionStore,
    store: IntakeStore,
) -> dict:
    session = _authorize(token, sessions)
    record = store._record(intake_id)
    status = record["status"]
    row = next((t for t in TRANSITIONS[status] if t[0] == to), None)
    if row is None:
        raise IllegalTransitionError(
            f"{status} -> {to} is not a legal transition"
            + (" (admin-accepted is parked until the Q10/G31/G32 gates clear)" if status == "admin-accepted" else "")
        )
    if session.role not in row[2]:
        raise Forbidden(f"{status} -> {to} is {'/'.join(row[2])} only")
    if record["thread_flagged"] and record["thread_decision"] is None and status == "draft":
        raise IllegalTransitionError(
            "this intake continues a known thread — the Adds-value / No-new-value "
            "decision comes first (thread-decision endpoint)"
        )
    if to == "admin-returned" and not note.strip():
        raise IntakeValidationError("a return goes back with a note — the SME needs the why")
    store.conn.execute("UPDATE intake SET status = ? WHERE intake_id = ?", (to, intake_id))
    store._log(intake_id, session.persona_id, f"transition:{status}->{to}", note)
    store.conn.commit()
    return get_intake(intake_id, token, sessions, store)


def thread_decision(
    intake_id: str,
    decision: str,
    token: str,
    sessions: InMemorySessionStore,
    store: IntakeStore,
) -> dict:
    """The SME's ruling on a flagged thread continuation (plan §3):
    ``adds-value`` — the delta proceeds as this intake's content; or
    ``no-new-value`` — linkage + decision recorded, the intake STOPS (terminal,
    but the record exists so a third bounce shows both prior decisions)."""
    session = _authorize(token, sessions)
    record = store._record(intake_id)
    if not record["thread_flagged"]:
        raise IntakeValidationError("no thread continuation was flagged on this intake")
    if record["thread_decision"] is not None:
        raise IntakeValidationError(
            f"thread decision already recorded: {record['thread_decision']}"
        )
    if decision not in ("adds-value", "no-new-value"):
        raise IntakeValidationError("decision must be 'adds-value' or 'no-new-value'")
    new_status = "no-new-value" if decision == "no-new-value" else record["status"]
    store.conn.execute(
        "UPDATE intake SET thread_decision = ?, status = ? WHERE intake_id = ?",
        (decision, new_status, intake_id),
    )
    store._log(intake_id, session.persona_id, f"thread-decision:{decision}", "")
    store.conn.commit()
    return get_intake(intake_id, token, sessions, store)
