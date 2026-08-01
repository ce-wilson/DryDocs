"""Source-of-truth precedence resolver — the configuration layer's authority chain.

When several authorities each assert a value for the same fact (e.g. which
``:BusinessSegment`` a ``:CatalogLOB`` reconciles to), the highest authority that
is **active** and has an opinion wins; the rest are recorded as **aliases** — never
silently dropped (see ``config/precedence.yaml#conflict_policy``).

The ordering is **data, not code**: edit ``order:`` in ``config/precedence.yaml`` and
the winner changes with no code edit. ``tests/unit/test_precedence.py`` proves this is
the contract (the D2 acceptance test).

Lower ``authority:`` number = higher precedence. If a chain entry omits ``authority``,
its position in ``order`` is used (top = highest). The ``active:`` map toggles a feed
off without deleting it.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_PRECEDENCE_PATH = _REPO_ROOT / "config" / "precedence.yaml"

# Values that mean "this authority has no opinion" and so cannot win.
_EMPTY = (None, "")


class UnknownAuthorityError(ValueError):
    """A claim cited an authority id that is not in precedence.yaml#order."""


@dataclass(frozen=True)
class Claim:
    """One authority's assertion about a fact.

    ``authority`` must match an ``id`` in precedence.yaml#order. ``value`` of
    None/"" means the authority abstains (it is dropped before ranking).
    """

    authority: str
    value: Any
    confidence: float | None = None
    note: str | None = None

    def as_alias(self) -> str:
        """Compact, primitive-safe alias string for a graph property
        (``authority:value@confidence``)."""
        conf = "" if self.confidence is None else f"@{self.confidence:g}"
        return f"{self.authority}:{self.value}{conf}"


@dataclass(frozen=True)
class Resolution:
    """The outcome of resolving a set of claims."""

    winner: Claim | None
    aliases: tuple[Claim, ...] = ()

    @property
    def value(self) -> Any:
        return self.winner.value if self.winner else None

    @property
    def authority(self) -> str | None:
        return self.winner.authority if self.winner else None

    @property
    def confidence(self) -> float | None:
        return self.winner.confidence if self.winner else None

    @property
    def has_conflict(self) -> bool:
        """True when a winner was chosen over at least one losing authority."""
        return bool(self.winner and self.aliases)

    def alias_strings(self) -> list[str]:
        return [c.as_alias() for c in self.aliases]


class PrecedenceResolver:
    """Resolves conflicting claims using the precedence.yaml authority chain."""

    def __init__(
        self,
        order: Iterable[dict],
        active: dict[str, bool] | None = None,
        conflict_policy: dict | None = None,
    ) -> None:
        self._rank: dict[str, int] = {}
        for idx, entry in enumerate(order):
            aid = entry["id"]
            # Explicit `authority:` wins; otherwise position (top = 1 = highest).
            self._rank[aid] = int(entry.get("authority", idx + 1))
        self._active: dict[str, bool] = dict(active or {})
        self.conflict_policy: dict = dict(conflict_policy or {})

    # ---- construction ----------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str | Path = DEFAULT_PRECEDENCE_PATH) -> PrecedenceResolver:
        doc = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
        return cls(
            order=doc.get("order", []),
            active=doc.get("active", {}),
            conflict_policy=doc.get("conflict_policy", {}),
        )

    # ---- queries ---------------------------------------------------------

    def known(self, authority: str) -> bool:
        return authority in self._rank

    def rank(self, authority: str) -> int:
        if authority not in self._rank:
            raise UnknownAuthorityError(
                f"authority {authority!r} is not in precedence.yaml#order "
                f"(known: {sorted(self._rank)})"
            )
        return self._rank[authority]

    def is_active(self, authority: str) -> bool:
        """A known authority is active unless explicitly toggled off."""
        return self.known(authority) and self._active.get(authority, True)

    # ---- resolution ------------------------------------------------------

    def resolve(self, claims: Iterable[Claim]) -> Resolution:
        """Pick the winning claim by precedence.

        Eligible = known + active + has an opinion. Sort by (rank asc,
        confidence desc, original order) so the highest authority wins; ties
        within one authority break on confidence, then stable input order.
        Losers become aliases. No eligible claim → empty Resolution.
        """
        eligible = [
            (i, c)
            for i, c in enumerate(claims)
            if self.known(c.authority) and self.is_active(c.authority) and c.value not in _EMPTY
        ]
        if not eligible:
            return Resolution(winner=None)

        def _key(ic: tuple[int, Claim]) -> tuple:
            i, c = ic
            return (self._rank[c.authority], -(c.confidence or 0.0), i)

        eligible.sort(key=_key)
        winner = eligible[0][1]
        aliases = tuple(c for _, c in eligible[1:])
        return Resolution(winner=winner, aliases=aliases)
