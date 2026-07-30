"""Ephemeral session-scoped QuerySpecs (R4 / ADR 0007 decision 4).

Every Cypher the graph_qa agent executes is registered HERE, server-side, and
the response envelope carries the returned ``explore_ref`` — Open-in-Explorer
and Export then reuse the existing ``/specs/{ref}/run|export`` paths, so
provenance manifests, classification stamping, watermarking, and DB routing
come for free and the browser still never submits raw Cypher. ``/raw-cypher``
stays admin+dev gated exactly per ADR 0005 — this module is the mechanism that
makes loosening it unnecessary.

The store's rules (all fail closed):

- **Registration is a trusted-caller surface, not a user surface.** The
  endpoint requires the server-side agent key (``DRYDOCS_AGENT_REG_KEY``);
  without the header — or with the env var unset — registration is Forbidden.
  A browser bearer token alone can NEVER register Cypher; otherwise
  ``POST /specs/ephemeral`` + ``/specs/{ref}/run`` would recreate the raw-
  Cypher path ADR 0005 closed to non-admins.
- **Hash-addressed:** the ref is derived from (database, cypher, bound
  params), so re-registering the same execution is idempotent and the ref
  itself commits to what will run.
- **Session-scoped:** a ref resolves only for the owning session token; any
  other session sees the same 404 as a nonexistent ref (no existence leak).
- **TTL-bounded and capacity-bounded:** expired refs stop resolving; the
  store evicts oldest-first past capacity. Ephemeral means ephemeral —
  recurring Cypher graduates through the gate-bound promotion feed (R8),
  never by outliving its TTL here.
- **Read-only twice:** ``ensure_read_only`` at registration AND again on the
  run/export path (exports.py re-validates every spec it executes).
- **Classification is the fail-closed ceiling** (``internal-confidential``):
  un-reviewed Cypher cannot be assumed less sensitive than the most
  restrictive data it could reach in its database.
- **Params are frozen at registration.** An ephemeral spec declares no
  ParamSpecs — the caller re-runs exactly what the agent ran; supplying
  params at run time fails closed (422), the same validate_params rule as
  everywhere else.
"""

from __future__ import annotations

import hashlib
import json
import secrets
import time
from collections import OrderedDict
from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime, timezone

from drydocs_api.guard import ensure_read_only
from drydocs_api.handlers import Forbidden
from drydocs_api.query_specs import (
    SPEC_DATABASES,
    ColumnDef,
    QuerySpec,
    UnknownSpecError,
    is_watermarked,
)
from drydocs_api.sessions import InMemorySessionStore

EPHEMERAL_PREFIX = "eph."
# Fail-closed ceiling: an un-reviewed query gets the most restrictive stamp —
# the export banner + INTERNAL-CONFIDENTIAL__ filename prefix follow from it.
EPHEMERAL_CLASSIFICATION = "internal-confidential"
DEFAULT_TTL_SECONDS = 30 * 60
DEFAULT_CAPACITY = 500


class EphemeralValidationError(ValueError):
    """Raised when a registration payload fails validation (422, never stored)."""


def is_ephemeral_ref(spec_id: str) -> bool:
    return spec_id.startswith(EPHEMERAL_PREFIX)


def _ref_for(cypher: str, database: str, params: Mapping[str, object]) -> str:
    material = "\x00".join(
        (database, cypher, json.dumps(dict(params), sort_keys=True, default=str))
    )
    return EPHEMERAL_PREFIX + hashlib.sha256(material.encode("utf-8")).hexdigest()[:16]


@dataclass(frozen=True)
class EphemeralSpec:
    ref: str
    owner_token: str
    cypher: str
    database: str
    bound_params: Mapping[str, object]  # frozen at registration; replayed verbatim
    description: str
    created_at: float  # epoch seconds (store clock)
    expires_at: float
    columns: tuple[ColumnDef, ...] = ()

    def as_query_spec(self) -> QuerySpec:
        """The QuerySpec shape the run/export path consumes. ``params=()`` is
        the frozen-params rule: user-supplied params fail closed downstream."""
        return QuerySpec(
            id=self.ref,
            database=self.database,
            description=self.description or "ephemeral agent query (ADR 0007)",
            cypher=self.cypher,
            columns=self.columns,
            classification=EPHEMERAL_CLASSIFICATION,
            params=(),
        )

    def expires_at_iso(self) -> str:
        return datetime.fromtimestamp(self.expires_at, tz=timezone.utc).isoformat(
            timespec="seconds"
        )


class EphemeralSpecStore:
    """Bounded in-memory registry keyed (owner_token, ref). In-memory is
    deliberate, like the session store: ephemeral state dies with the server,
    and the durable path for recurring Cypher is spec promotion, not storage."""

    def __init__(
        self,
        ttl_seconds: float = DEFAULT_TTL_SECONDS,
        capacity: int = DEFAULT_CAPACITY,
        clock: Callable[[], float] = time.time,
    ) -> None:
        self._specs: OrderedDict[tuple[str, str], EphemeralSpec] = OrderedDict()
        self._ttl = ttl_seconds
        self._capacity = capacity
        self._clock = clock

    def register(
        self,
        owner_token: str,
        cypher: str,
        database: str,
        params: Mapping[str, object] | None = None,
        description: str = "",
        columns: Sequence[str] = (),
    ) -> EphemeralSpec:
        cypher = (cypher or "").strip()
        if not cypher:
            raise EphemeralValidationError("empty cypher")
        ensure_read_only(cypher)  # raises WriteRejected — never stored
        if database not in SPEC_DATABASES:
            raise EphemeralValidationError(
                f"database '{database}' not in the reviewed spec set {sorted(SPEC_DATABASES)}"
            )
        bound = dict(params or {})
        if any(not isinstance(k, str) for k in bound):
            raise EphemeralValidationError("param names must be strings")

        self._purge_expired()
        now = self._clock()
        spec = EphemeralSpec(
            ref=_ref_for(cypher, database, bound),
            owner_token=owner_token,
            cypher=cypher,
            database=database,
            bound_params=bound,
            description=description,
            created_at=now,
            expires_at=now + self._ttl,
            columns=tuple(ColumnDef(name=str(c), type="string") for c in columns),
        )
        key = (owner_token, spec.ref)
        self._specs[key] = spec  # idempotent re-register refreshes the TTL
        self._specs.move_to_end(key)
        while len(self._specs) > self._capacity:
            self._specs.popitem(last=False)
        return spec

    def resolve(self, owner_token: str, ref: str) -> EphemeralSpec:
        """Owner-scoped lookup: unknown, expired, and foreign-session refs all
        raise the same :class:`UnknownSpecError` (mapped to 404 — no leak)."""
        self._purge_expired()
        try:
            return self._specs[(owner_token, ref)]
        except KeyError as exc:
            raise UnknownSpecError(ref) from exc

    def _purge_expired(self) -> None:
        now = self._clock()
        for key in [k for k, s in self._specs.items() if s.expires_at <= now]:
            del self._specs[key]


# ── pure registration handler (app.py is a thin shell over this) ─────────────


def register_ephemeral(
    agent_key: str | None,
    expected_key: str | None,
    owner_token: str,
    cypher: str,
    database: str,
    params: Mapping[str, object] | None,
    description: str,
    columns: Sequence[str],
    sessions: InMemorySessionStore,
    ephemerals: EphemeralSpecStore,
) -> dict[str, object]:
    """Register one executed Cypher for the session named by ``owner_token``.

    The caller must present the server-side agent key — the trusted-caller
    gate that keeps this endpoint off-limits to browsers (see module doc).
    With no key configured the surface is disabled entirely (fail closed).
    """
    if not expected_key:
        raise Forbidden(
            "ephemeral registration is disabled (DRYDOCS_AGENT_REG_KEY not configured)"
        )
    if not agent_key or not secrets.compare_digest(agent_key, expected_key):
        raise Forbidden("ephemeral registration requires the agent key")
    sessions.resolve(owner_token)  # raises InvalidTokenError — the owner must be live
    spec = ephemerals.register(
        owner_token,
        cypher,
        database,
        params=params,
        description=description,
        columns=columns,
    )
    query_spec = spec.as_query_spec()
    return {
        "explore_ref": spec.ref,
        "database": spec.database,
        "classification": query_spec.classification,
        "watermarked": is_watermarked(query_spec),
        "expires_at": spec.expires_at_iso(),
    }
