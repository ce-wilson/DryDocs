"""Q10 — the failure/activity email corpus, loaded as the ACTIVE lexical shape.

The user's source (2026-07-26): "we get emails that reference a failure or
activity and I've extracted those as json files and save the original msg
format... it may require an SME assigning it to a particular folder or process
if it's not extractable from the email."

WHAT LOADS: the Copilot JSON extracts under DRYDOCS_DATA_ROOT/email-extracts/,
as ``(:Document)-[:PART_OF]<-(:Chunk)`` with FIRST_CHUNK/NEXT_CHUNK — pure reuse
of the ACTIVE ``docs_*`` vocabulary (the Q2/essential-graphrag covering-gate
precedent). The original ``.msg`` is referenced by path and NEVER copied or
parsed: after the 6-18 month Outlook purge the file-server pair is the ONLY
copy — a system of record with a backup obligation, not a cache.

WHAT NEVER LOADS HERE: any folder/process assignment. An email whose subject is
not extractable lands UNASSIGNED — that is a valid resting state, not a reject.
The assignment edge (Document → ControlMFolder | ETLProcess) is registered
``status: planned`` (``docs_email_concerns``) and gated by
``config/gate-prompts/email-folder-assignment.yaml``; nothing writes it until
that gate signs.

THE EXTRACT CONTRACT IS ASSUMED (the G47 precedent): defined by the synthetic
fixtures in ``drydocs/data/samples/email-extracts/`` — ``subject``, ``sent_at``,
``body_text``, ``msg_file`` (sibling reference), optional ``message_id``. A row
missing any required key is REJECTED AND COUNTED, never guessed. Confirm the
shape against a real extract before treating field semantics as estate truth.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator
from pathlib import Path
from types import TracebackType
from typing import ClassVar

from drydocs_core.data_root import email_extracts_dir
from drydocs_core.models.docs import EmailExtractRow

from .base import BaseLoader

CYPHER_DIR = Path(__file__).resolve().parent / "cypher"

REQUIRED_KEYS = ("subject", "sent_at", "body_text", "msg_file")


def email_doc_id(subject: str, sent_at: str) -> str:
    """Deterministic Document id: ``email:<12-hex>`` over (subject, sent_at).

    Row-derived, never load-order-derived (truncate-and-reload discipline);
    ``message_id`` is preferred when present but the pair is the guaranteed
    floor, because the Copilot extract always carries both fields.
    """
    digest = hashlib.sha256(f"{subject}\x1f{sent_at}".encode()).hexdigest()[:12]
    return f"email:{digest}"


def split_body(body: str) -> list[str]:
    """Paragraph chunking: blank-line blocks, whitespace-normalized, empties
    dropped. Emails are short — no overlap window, no token budget."""
    blocks = [" ".join(part.split()) for part in body.split("\n\n")]
    return [b for b in blocks if b]


class EmailExtractsAdapter:
    """Reads every ``*.json`` extract in the landing zone; yields chunk rows."""

    def __init__(self, extracts_dir: Path | None = None) -> None:
        self.extracts_dir = extracts_dir or email_extracts_dir()
        self.rejected: list[tuple[str, str]] = []  # (file, reason) — counted, never dropped

    def __enter__(self) -> EmailExtractsAdapter:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        for path in sorted(self.extracts_dir.glob("*.json"), key=lambda p: p.as_posix()):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                self.rejected.append((path.name, f"unreadable extract: {exc}"))
                continue
            missing = [k for k in REQUIRED_KEYS if not payload.get(k)]
            if missing:
                self.rejected.append((path.name, f"missing required key(s): {missing}"))
                continue
            doc_id = (
                f"email:{hashlib.sha256(str(payload['message_id']).encode()).hexdigest()[:12]}"
                if payload.get("message_id")
                else email_doc_id(payload["subject"], payload["sent_at"])
            )
            chunks = split_body(payload["body_text"])
            if not chunks:
                self.rejected.append((path.name, "body_text yields no chunks"))
                continue
            prev: str | None = None
            for seq, text in enumerate(chunks):
                chunk_id = f"{doc_id}#{seq:03d}"
                yield {
                    "doc_id": doc_id,
                    "subject": payload["subject"],
                    "sent_at": payload["sent_at"],
                    "msg_path": str(payload["msg_file"]),
                    "extract_path": path.name,
                    "chunk_id": chunk_id,
                    "seq": seq,
                    "text": text,
                    "char_count": len(text),
                    "prev_chunk_id": prev,
                    "row_checksum": hashlib.sha256(text.encode()).hexdigest(),
                }
                prev = chunk_id


class EmailExtractsLoader(BaseLoader):
    name: ClassVar[str] = "email_extracts.v1"
    source_id: ClassVar[str | None] = "ops-email-extracts"
    cypher_path: ClassVar[Path | None] = CYPHER_DIR / "email_extracts.cypher"
    row_model: ClassVar[type] = EmailExtractRow
    # format-flavored value, the bmc_docs "markdown" / code_snapshot "snapshot"
    # practice — the enum question is Idea-132's standing knock-on
    source_label: ClassVar[str] = "json"
