"""Load-balancer name resolution (backlog Z4) — nslookup transcript -> T3 evidence.

THE GAP THIS FILLS. A Control-M job is scheduled against a node name, and that
name is frequently a load-balancer alias rather than a machine. The signed
server-location tiers (gate ``server-location-ontology``, 12/12, 2026-08-19)
join a name to an inventory ``:Server`` only when the strings meet — T1 exact,
T2 the short-name/FQDN rule, nothing fuzzier — so an alias meets neither, is
correctly reported UNMATCHED, and the jobs behind it cannot be placed on a map.
T3 ``dns-resolved`` is the tier the gate declared for exactly this and left
unbuilt; this module is its evidence half.

WHICH NAMES ARE LOAD BALANCERS IS DECIDED BY THE ANSWER, NOT BY THE NAME.
There is no name-pattern classifier here and there must not be one: reading a
naming convention off a hostname invents a rule nobody signed, and it is the
same class of guess the T2 ambiguity guard exists to refuse. So the candidate
set comes from the coverage report — the UNMATCHED rows of the Z3 query
``infra.app-job-host-locations.v1`` are precisely the names T1 and T2 could not
place — and the OUTCOME classifies them:

* ``matched``     — DNS answered with one or more names, at least one of which
                    is an inventory server. Every such pairing becomes a
                    record; an alias fronting three servers yields three, which
                    is the fan-out the gate's §A1 note anticipated ("one
                    LB-alias ExecutionHost may resolve to MANY Servers once T3
                    lands").
* ``unmatched``   — DNS answered, and nothing it named is in the inventory.
                    A real gap: either the export for that application has not
                    been pulled, or the alias fronts machines nobody inventoried.
* ``unresolved``  — the resolver said NXDOMAIN, or could not answer.
* ``unreadable``  — a transcript this parser could not make sense of. Counted
                    rather than skipped, because a parser that silently drops
                    what it does not understand reports a clean run over a
                    format change.

NOTHING IS DROPPED AND NOTHING IS GUESSED, which is the Z3 discipline one layer
out. A name that resolves to a machine no inventory carries is a coverage fact
worth having; deleting it would turn a known gap into an absence.

PURE, AND DELIBERATELY SO. This module touches no database and imports no
query registry. The server list arrives as a parameter — the caller reads
``:Server`` names, or a CSV, or a fixture — which is what lets the whole
mechanism be proven against a canned transcript with no DNS and no Neo4j
anywhere near it. The live collection is company-side by construction
(``drydocs_lineage/collect/lb_resolve.sh``).

THE OUTPUT IS THE EDGE'S OWN SHAPE. Every matched record carries ``nodeid``,
``server``, ``match_tier='dns-resolved'`` and a ``match_evidence`` string, so
the loader that eventually writes ``RESOLVES_TO_SERVER`` consumes this file
unchanged — the shape ``drydocs/loaders/server_resolution.py`` already promises
in its own docstring. This module writes no edges: every graph write goes
through the gated shapes, and that loader is a separate, later act.
"""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path

SCHEMA = "drydocs.lb-resolution.v1"

#: The collector schema stamps this module understands (meta.txt ``schema=``).
#: Dispatch is on the SECTIONS PRESENT, never on this tag — the rua precedent,
#: which is what keeps older bundles ingestible.
KNOWN_COLLECTOR_VERSIONS = frozenset({"lb-resolve/v1"})

MATCH_TIER = "dns-resolved"

# --- nslookup output, and the four ways it is misread ------------------------
# A Linux nslookup answer opens with the RESOLVER's own name and address:
#
#     Server:		10.0.0.53
#     Address:	10.0.0.53#53
#
#     Non-authoritative answer:
#     lb-alias.example	canonical name = pool-a.example.
#     Name:	host-one.example
#     Address: 10.0.0.11
#
# so (1) everything before the answer section is the resolver and must not be
# read as a result — the single most likely way to record the DNS server as the
# machine a job runs on; (2) an ``Address:`` carrying a ``#port`` suffix is the
# resolver line even when it appears elsewhere; (3) a CNAME chain puts
# ``canonical name =`` lines before the ``Name:`` lines, and those intermediate
# names are aliases, not machines; (4) an authoritative answer has no
# "Non-authoritative answer:" banner at all, so the section cannot be found by
# that string alone. Each has a test.
_SERVER_LINE = re.compile(r"^Server:\s*(?P<value>.+?)\s*$")
_NAME_LINE = re.compile(r"^Name:\s*(?P<value>\S+)\s*$")
_ADDRESS_LINE = re.compile(r"^Address(?:es)?:\s*(?P<value>.+?)\s*$")
_CANONICAL_LINE = re.compile(r"canonical name\s*=\s*(?P<value>\S+?)\.?\s*$")
_QUERY_COMMENT = re.compile(r"^;\s*query:\s*(?P<value>\S+)\s*$")
_NXDOMAIN = re.compile(r"can't find\s+(?P<value>\S+?):?\s*(NXDOMAIN|SERVFAIL|REFUSED)", re.I)
_NO_ANSWER = re.compile(r"No answer|server can't find|connection timed out", re.I)


def _short(name: str) -> str:
    """The short name, DNS suffix stripped — the T2 rule, reused verbatim.

    Matching a resolved FQDN against an inventory that records short names (or
    the reverse) is the same normalization the signed T2 tier already performs,
    so it is applied the same way here rather than reinvented.
    """
    return name.strip().rstrip(".").lower().split(".")[0]


@dataclass(frozen=True)
class NslookupAnswer:
    """One parsed transcript: what was asked, and what DNS said back."""

    query: str
    #: Canonical/alias hops seen before the answer (``canonical name =``).
    aliases: tuple[str, ...] = ()
    #: The machine names the answer section carried (``Name:`` lines).
    names: tuple[str, ...] = ()
    #: Addresses from the ANSWER section only — resolver lines excluded.
    addresses: tuple[str, ...] = ()
    #: True when the resolver explicitly failed to find the name.
    nxdomain: bool = False
    #: Set when the transcript could not be parsed at all.
    unreadable_reason: str | None = None

    @property
    def answered(self) -> bool:
        return bool(self.names or self.addresses)


def parse_nslookup(text: str, *, query: str | None = None) -> NslookupAnswer:
    """Parse one nslookup transcript.

    ``query`` overrides the ``; query:`` comment the collector writes; when
    neither is present the transcript is unreadable, because a resolution
    record with no subject cannot be attributed to a host.
    """
    lines = text.splitlines()
    name_from_comment = None
    for line in lines:
        hit = _QUERY_COMMENT.match(line.strip())
        if hit:
            name_from_comment = hit.group("value")
            break
    subject = (query or name_from_comment or "").strip()
    if not subject:
        return NslookupAnswer(
            query="",
            unreadable_reason="no queried name: neither a '; query:' comment nor a caller value",
        )

    resolver_values: set[str] = set()
    aliases: list[str] = []
    names: list[str] = []
    addresses: list[str] = []
    nxdomain = False
    in_answer = False

    for raw in lines:
        line = raw.strip()
        if not line or line.startswith(";"):
            continue

        if _NXDOMAIN.search(line):
            nxdomain = True
            continue

        server = _SERVER_LINE.match(line)
        if server:
            # The resolver's own identity. Everything up to the answer section
            # belongs to it, INCLUDING the Address: line that follows.
            resolver_values.add(server.group("value").strip())
            in_answer = False
            continue

        if line.lower().startswith("non-authoritative answer") or line.lower().startswith(
            "authoritative answer"
        ):
            in_answer = True
            continue

        canonical = _CANONICAL_LINE.search(line)
        if canonical:
            # A CNAME hop is an ALIAS, never a machine. Seeing one also means
            # the answer section has begun even without a banner.
            in_answer = True
            aliases.append(canonical.group("value").strip().rstrip("."))
            continue

        name = _NAME_LINE.match(line)
        if name:
            in_answer = True
            names.append(name.group("value").strip().rstrip("."))
            continue

        address = _ADDRESS_LINE.match(line)
        if address:
            value = address.group("value").strip()
            if "#" in value:
                # `10.0.0.53#53` — the resolver's own socket, wherever it sits.
                resolver_values.add(value.split("#", 1)[0])
                continue
            if not in_answer:
                continue
            addresses.extend(part.strip() for part in value.split(",") if part.strip())
            continue

    if not names and not addresses and not nxdomain:
        reason = (
            "no answer section"
            if _NO_ANSWER.search(text)
            else "no Name:/Address: lines and no NXDOMAIN"
        )
        return NslookupAnswer(
            query=subject,
            aliases=tuple(aliases),
            unreadable_reason=None if _NO_ANSWER.search(text) else reason,
            nxdomain=bool(_NO_ANSWER.search(text)),
        )

    return NslookupAnswer(
        query=subject,
        aliases=tuple(aliases),
        names=tuple(names),
        addresses=tuple(addresses),
        nxdomain=nxdomain,
    )


@dataclass(frozen=True)
class LbResolutionRecord:
    """One (nodeid -> server) pairing, in the RESOLVES_TO_SERVER edge's shape."""

    nodeid: str
    server: str
    match_tier: str = MATCH_TIER
    match_evidence: str = ""


@dataclass
class LbResolutionCoverage:
    """Per-run census. Every queried name lands in exactly one bucket."""

    total_queried: int = 0
    matched: int = 0
    unmatched: int = 0
    unresolved: int = 0
    unreadable: int = 0
    #: (nodeid, [names DNS gave]) for answers nothing in inventory carried —
    #: listed, not merely counted, because the list is the actionable half.
    unmatched_names: list[tuple[str, tuple[str, ...]]] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)

    def reconciles(self) -> bool:
        return (
            self.matched + self.unmatched + self.unresolved + self.unreadable
        ) == self.total_queried

    def as_dict(self) -> dict:
        data = asdict(self)
        data["unmatched_names"] = [[n, list(v)] for n, v in self.unmatched_names]
        data["reconciles"] = self.reconciles()
        return data


@dataclass(frozen=True)
class LbResolutionReport:
    """The evidence file's content: records + coverage + collector provenance."""

    schema: str
    collector: dict[str, str]
    records: tuple[LbResolutionRecord, ...]
    coverage: LbResolutionCoverage

    def as_dict(self) -> dict:
        return {
            "schema": self.schema,
            "collector": dict(self.collector),
            "records": [asdict(r) for r in self.records],
            "coverage": self.coverage.as_dict(),
        }

    def write(self, path: Path) -> Path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(self.as_dict(), indent=2, sort_keys=False) + "\n",
            encoding="utf-8",
            newline="\n",
        )
        return path


def read_meta(bundle: Path) -> dict[str, str]:
    """``meta.txt`` as key=value. Absent is empty, never an error.

    An older or hand-assembled bundle without the envelope still parses; the
    report simply records that its provenance is unknown, which is the honest
    outcome and the one the rua extractor takes for the same reason.
    """
    meta_path = bundle / "meta.txt"
    if not meta_path.is_file():
        return {}
    out: dict[str, str] = {}
    for line in meta_path.read_text(encoding="utf-8").splitlines():
        if "=" in line:
            key, _, value = line.partition("=")
            out[key.strip()] = value.strip()
    return out


def iter_transcripts(bundle: Path) -> list[Path]:
    """Every transcript in the bundle, in a stable order.

    Sorted so a report is byte-identical across runs and platforms — the same
    determinism rule the renderers are held to.
    """
    directory = bundle / "nslookup"
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.glob("*.txt") if p.is_file())


def resolve_bundle(bundle: Path, server_names: set[str]) -> LbResolutionReport:
    """Match a collected bundle against the ingested server list.

    ``server_names`` is the inventory side — ``:Server.name`` values, or any
    equivalent list. Matching is case-insensitive and applies the T2 short-name
    rule in BOTH directions, so a resolver that answers with an FQDN still
    meets an inventory that records short names.
    """
    meta = read_meta(bundle)
    by_short: dict[str, str] = {}
    for name in server_names:
        cleaned = name.strip()
        if cleaned:
            by_short.setdefault(_short(cleaned), cleaned)

    coverage = LbResolutionCoverage()
    records: list[LbResolutionRecord] = []
    collected_at = meta.get("collected_at", "unknown")

    schema_tag = meta.get("schema")
    if schema_tag and schema_tag not in KNOWN_COLLECTOR_VERSIONS:
        coverage.notes.append(
            f"collector schema {schema_tag!r} is newer than this parser knows "
            f"({sorted(KNOWN_COLLECTOR_VERSIONS)}) — parsed on section presence, as designed"
        )

    for path in iter_transcripts(bundle):
        coverage.total_queried += 1
        answer = parse_nslookup(path.read_text(encoding="utf-8", errors="replace"))

        if answer.unreadable_reason is not None:
            coverage.unreadable += 1
            coverage.notes.append(f"{path.name}: {answer.unreadable_reason}")
            continue
        if not answer.answered:
            coverage.unresolved += 1
            continue

        hits = []
        for candidate in answer.names:
            server = by_short.get(_short(candidate))
            if server is not None and server not in {h[1] for h in hits}:
                hits.append((candidate, server))

        if not hits:
            coverage.unmatched += 1
            coverage.unmatched_names.append((answer.query, answer.names))
            continue

        coverage.matched += 1
        for candidate, server in hits:
            via = f" via {' -> '.join(answer.aliases)}" if answer.aliases else ""
            records.append(
                LbResolutionRecord(
                    nodeid=answer.query,
                    server=server,
                    match_evidence=(
                        f"nslookup ({meta.get('lookup_source', 'unknown')}, {collected_at}): "
                        f"{answer.query}{via} -> {candidate}"
                    ),
                )
            )

    records.sort(key=lambda r: (r.nodeid.lower(), r.server.lower()))
    return LbResolutionReport(
        schema=SCHEMA,
        collector={
            "schema": meta.get("schema", "unknown"),
            "collected_at": collected_at,
            "collector_host": meta.get("collector_host", "unknown"),
            "lookup_source": meta.get("lookup_source", "unknown"),
            "resolver": meta.get("resolver", "unknown"),
        },
        records=tuple(records),
        coverage=coverage,
    )
