r"""Control-M DESCRIPTION-field metadata parser (G66) — the pipe-delimited
``key: value`` grammar the description-metadata standard authors into the
4000-char job/folder DESCRIPTION field.

WHY THIS EXISTS. The Control-M DESCRIPTION field is free text, 1 to 4000 chars,
and — critically — **not runtime-accessible as a %% variable**. It can never
drive job behavior, which is exactly what makes it safe to repurpose: the
company standard fills it with metadata that exists nowhere else in the
estate (how a file was delivered, which MFT routes carried it, who owns it
upstream, which support DLs and downstream consumers to notify, which
ServiceNow queue takes the incident). Extraction turns that free text into
rows; rows become graph edges once the HITL gate rules the vocabulary.

WHAT THIS IS NOT. This module PARSES. It does not classify variables (that is
:mod:`.variables`), it does not resolve substitutions (that is
:mod:`.resolver`), and it does not write a graph or a store. It has no I/O.

STANDARD OF RECORD — ``knowledge/standards/technology/description-field-metadata-plan.md``
§2b (mechanism, sanitized) with the verbatim company capture at
``internal/controlm-config/reference/controlm-job-metadata-standards-capture.md``.
Everything in :data:`TOKEN_REGISTRY` is ``proposed``: no relationship-vocabulary
entry, no property-term binding and no loader exists for any of these terms,
and the DL class itself is still open at gate ``email-dl-contact-point``.
The registry is the parse contract, NOT a ratification.

THE GRAMMAR (six rules, all from the standard, all load-bearing):

1. **Pipe is the only delimiter.** Semicolons appear INSIDE values — a
   multi-address distribution list is one token, not several. Splitting on
   ``;`` shreds a DL into fragments that look like keys.
2. **Split on the FIRST colon only.** Values legally contain colons
   (``SeriesSLA: 17:00 EST``). Splitting on every colon truncates the value
   at the first time separator.
3. **Whitespace-tolerant on both sides.** The wild carries both ``| USER: x``
   and ``|USER:x`` — the standard's own examples are inconsistent.
4. **A key with no value still emits its token.** The standard REQUIRES
   ``PDN_SNOW_QUEUE: NULL`` to be present even when unassigned, so a parse
   always finds the key and returns a parseable result rather than a missing
   match. Oracle does ``NULLIF(..., 'NULL')``; here the literal string
   ``NULL`` becomes Python ``None``, so "explicitly unassigned" and "key
   absent" stay distinguishable.
5. **Unknown keys are RETURNED, never dropped.** The C16 key-prefix
   governance makes a bare key a legal team-local annotation: preserved
   verbatim, never load-bearing. Dropping one loses evidence; promoting one
   breaks the governance.
6. **A value outside its vocabulary is a FINDING, not an exception.** Same
   discipline as the FACT_REGISTRY next door ("aliases suggest, values
   decide") and the G16 WARN stream: report and carry on, never raise, never
   silently coerce. Free text authored by hand will be wrong sometimes, and
   a parser that dies on the first bad row cannot survey an estate.

DELIBERATE NON-GOALS. No escaping convention is defined by the standard for a
value that itself contains ``|`` — the plan records this as open item 2. This
parser therefore cannot recover such a value and does not pretend to: the
pipe wins, and the fragment after it is read as the next token. Recording the
limitation is the honest move; inventing an escape here would fork the
standard.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

#: The token the standard uses to say "this key is deliberately unassigned".
#: Distinct from an absent key — see grammar rule 4.
NULL_LITERAL = "NULL"

#: Splits on the FIRST colon only (grammar rule 2). The key is restricted to
#: token characters so a colon inside prose cannot be mistaken for a key
#: boundary; everything after the first colon is the value, verbatim.
_PAIR = re.compile(r"^\s*(?P<key>[A-Za-z0-9_.\-]+)\s*:\s*(?P<value>.*)$", re.DOTALL)


class Carrier(str, Enum):
    """Where the value physically lives. Three mechanisms with three
    different change-control paths — conflating them invites someone to edit
    a live VARIABLE as casually as they would edit prose."""

    #: a key: value pair inside the DESCRIPTION field — metadata only, never
    #: runtime-accessible, safe to restructure
    DESCRIPTION = "description-token"
    #: a %%-prefixed VARIABLE on the job — LIVE at execution; changing one is
    #: a behavioral change needing the remediation module's equivalence proof
    JOB_VARIABLE = "job-variable"
    #: a VARIABLE at folder / sub-folder scope — live, and inherited
    FOLDER_VARIABLE = "folder-variable"


class JobType(str, Enum):
    FILE_WATCHER = "file_watcher"
    PUBLISHER = "publisher"
    #: appears on both file-watcher and publisher descriptions
    BOTH = "both"


@dataclass(frozen=True)
class TokenSpec:
    """One registered description token.

    ``sql_column`` is the Oracle landing column from the company DDL;
    ``ontology_term`` is what the standard PROPOSES the value means. Neither
    is ratified here — see the module docstring.
    """

    key: str
    job_type: JobType
    sql_column: str
    ontology_term: str
    #: allowed values, or ``None`` when the value is free text
    vocabulary: tuple[str, ...] | None = None
    #: True when the standard says the value may be several entries separated
    #: by ``;`` INSIDE the one token (grammar rule 1)
    multivalued: bool = False
    note: str = ""
    carrier: Carrier = Carrier.DESCRIPTION


#: Delivery mechanisms (capture Part D §3). Route ids are MFTS_AGENT-only —
#: the other two mechanisms carry the literal NULL in both route tokens.
DELIVERY_MECHANISMS = ("MFTS_AGENT", "SFTP_DIRECT", "API_GENERATED")

#: Publisher discriminator (capture Part E §2). One value today; the standard
#: leaves room for more, so this stays an open-but-governed set rather than a
#: boolean — the etlprocess-kind-enum discipline, no catch-all.
JOB_ROLES = ("PUBLISHER",)

#: Every description token the standard defines, keyed by the token spelling
#: as it appears in the field. The single source both the parser and the
#: published register read from, so code and document cannot drift.
TOKEN_REGISTRY: dict[str, TokenSpec] = {
    spec.key: spec
    for spec in (
        # -- FileWatcher: delivery ------------------------------------------
        TokenSpec(
            key="DELIVERY_MECHANISM",
            job_type=JobType.FILE_WATCHER,
            sql_column="DELIVERY_MECHANISM",
            ontology_term="ex:fileDeliveredVia",
            vocabulary=DELIVERY_MECHANISMS,
            note="Always required. The 2026-06-11 field observation spelled this FileDeliveryMechanism.",
        ),
        TokenSpec(
            key="USER",
            job_type=JobType.FILE_WATCHER,
            sql_column="USER_ID",
            ontology_term="ex:systemUser",
            note="Service/functional account. Property of the transfer AGENT, not of the job.",
        ),
        TokenSpec(
            key="ENV",
            job_type=JobType.FILE_WATCHER,
            sql_column="ENV",
            ontology_term="ex:mftsEnv",
            note="Transfer environment. Property of the agent.",
        ),
        TokenSpec(
            key="INBOUND_ROUTE",
            job_type=JobType.FILE_WATCHER,
            sql_column="MFTS_INBOUND_ROUTE_ID",
            ontology_term="ex:mftsRouteId on dprod:inputPort",
            note="MFTS_AGENT only; literal NULL otherwise. Production observation carries a NUMERIC route id under the single key ROUTE_ID — the directional split is new and unreconciled.",
        ),
        TokenSpec(
            key="OUTBOUND_ROUTE",
            job_type=JobType.FILE_WATCHER,
            sql_column="MFTS_OUTBOUND_ROUTE_ID",
            ontology_term="ex:mftsRouteId on dprod:outputPort",
            note="MFTS_AGENT only; literal NULL otherwise.",
        ),
        TokenSpec(
            key="SOURCE_CONTACT",
            job_type=JobType.FILE_WATCHER,
            sql_column="SOURCE_CONTACT",
            ontology_term="prov:wasAttributedTo",
            multivalued=True,
            note="Origin file owner. Would be a new ROLE on the existing WAS_ATTRIBUTED_TO edge, not a new edge type.",
        ),
        # -- Publisher -------------------------------------------------------
        TokenSpec(
            key="JOB_ROLE",
            job_type=JobType.PUBLISHER,
            sql_column="JOB_ROLE",
            ontology_term="ex:jobRole",
            vocabulary=JOB_ROLES,
            note="The discriminator that decides which table a job lands in.",
        ),
        TokenSpec(
            key="PDN_DL",
            job_type=JobType.PUBLISHER,
            sql_column="PDN_DL",
            ontology_term="ex:consumerContact on dprod:outputPort",
            multivalued=True,
            note="Downstream consumers notified on publish.",
        ),
        TokenSpec(
            key="PDN_SNOW_QUEUE",
            job_type=JobType.PUBLISHER,
            sql_column="PDN_SNOW_QUEUE",
            ontology_term="ex:serviceNowQueue",
            note="MANDATORY EVEN WHEN EMPTY (grammar rule 4). Distinct subject from the observed SourceSnowQueue — downstream consumer's queue, not the source system's.",
        ),
        # -- Both ------------------------------------------------------------
        TokenSpec(
            key="EMAIL_DL_L3",
            job_type=JobType.BOTH,
            sql_column="EMAIL_DL_L3",
            ontology_term="ex:supportContact",
            multivalued=True,
            note="Dev / Scrum team. Folder-variable twin is spelled L3_EMAIL_DL_NM — carrier and spelling both differ; precedence unsettled (gate rider G2).",
        ),
        TokenSpec(
            key="EMAIL_DL_L2",
            job_type=JobType.BOTH,
            sql_column="EMAIL_DL_L2",
            ontology_term="ex:supportContact",
            multivalued=True,
            note="Ops support group. Folder-variable twin is spelled L2_EMAIL_DL_NM.",
        ),
    )
}

#: Folder-level VARIABLE names the standard adds (capture Part A, REQ-1).
#: Registered for the register's completeness and for validation; they are
#: NOT description tokens and never appear in a parse result.
FOLDER_VARIABLES: dict[str, TokenSpec] = {
    spec.key: spec
    for spec in (
        TokenSpec(
            key="DevX-project",
            job_type=JobType.BOTH,
            sql_column="",
            ontology_term="",
            carrier=Carrier.FOLDER_VARIABLE,
            note="Ownership attribution where a platform app code makes the folder's owner unreadable.",
        ),
        TokenSpec(
            key="L2_EMAIL_DL_NM",
            job_type=JobType.BOTH,
            sql_column="",
            ontology_term="ex:supportContact",
            multivalued=True,
            carrier=Carrier.FOLDER_VARIABLE,
            note="Folder-scope twin of the EMAIL_DL_L2 description token.",
        ),
        TokenSpec(
            key="L3_EMAIL_DL_NM",
            job_type=JobType.BOTH,
            sql_column="",
            ontology_term="ex:supportContact",
            multivalued=True,
            carrier=Carrier.FOLDER_VARIABLE,
            note="Folder-scope twin of the EMAIL_DL_L3 description token.",
        ),
    )
}


class TokenFindingKind(str, Enum):
    """Everything the parser can object to. All are reported; none raises."""

    #: value not in the token's controlled vocabulary
    VALUE_NOT_IN_VOCABULARY = "value_not_in_vocabulary"
    #: key is not registered — legal per C16 (team-local annotation), kept
    #: verbatim, reported informationally so an inventory can see it
    UNKNOWN_KEY = "unknown_key"
    #: same key appears more than once; first occurrence wins, like the
    #: Oracle REGEXP_SUBSTR(..., 1, 1) the standard's parse statements use
    DUPLICATE_KEY = "duplicate_key"
    #: a pipe-delimited segment carried no colon at all
    UNPARSEABLE_SEGMENT = "unparseable_segment"
    #: a registered token the job type requires is missing entirely
    MISSING_REQUIRED_TOKEN = "missing_required_token"


@dataclass(frozen=True)
class TokenFinding:
    kind: TokenFindingKind
    key: str
    detail: str = ""

    def __str__(self) -> str:  # pragma: no cover - display only
        return f"{self.kind.value}: {self.key} {self.detail}".strip()


@dataclass
class ParsedDescription:
    """One parsed DESCRIPTION field.

    ``tokens`` holds every key found, registered or not, in document order.
    A value of ``None`` means the literal ``NULL`` was present — deliberately
    unassigned, which is NOT the same as the key being absent.
    """

    raw: str
    tokens: dict[str, str | None] = field(default_factory=dict)
    findings: list[TokenFinding] = field(default_factory=list)

    @property
    def is_structured(self) -> bool:
        """True when at least one REGISTERED token was found — i.e. this
        description has adopted the standard rather than carrying prose or
        the generator's boilerplate literal."""
        return any(key in TOKEN_REGISTRY for key in self.tokens)

    @property
    def unknown_keys(self) -> list[str]:
        """Keys present but unregistered — C16 team-local annotations. Legal,
        preserved, never load-bearing."""
        return [key for key in self.tokens if key not in TOKEN_REGISTRY]

    def value(self, key: str) -> str | None:
        return self.tokens.get(key)

    def values(self, key: str) -> list[str]:
        """A multivalued token split on ``;`` — the INNER separator. Returns
        ``[]`` for an absent key or an explicit NULL."""
        raw = self.tokens.get(key)
        if not raw:
            return []
        return [part.strip() for part in raw.split(";") if part.strip()]

    def as_columns(self) -> dict[str, str | None]:
        """Registered tokens keyed by their Oracle landing column — the shape
        the company's REGEXP UPDATE statements produce, so a Python-side
        extract and a SQL-side extract can be compared row for row."""
        return {
            TOKEN_REGISTRY[key].sql_column: value
            for key, value in self.tokens.items()
            if key in TOKEN_REGISTRY
        }


def parse_description(text: str | None) -> ParsedDescription:
    """Shred a DESCRIPTION field into its tokens. Never raises.

    Returns a :class:`ParsedDescription` whose ``tokens`` carry every key
    found — registered or not — and whose ``findings`` carry every objection.
    A description that is ordinary prose parses to zero tokens and one
    ``UNPARSEABLE_SEGMENT`` finding, which is the correct answer for the bulk
    of the estate: it has not adopted the standard.
    """
    result = ParsedDescription(raw=text or "")
    if not text or not text.strip():
        return result

    for segment in text.split("|"):
        if not segment.strip():
            continue
        match = _PAIR.match(segment)
        if match is None:
            result.findings.append(
                TokenFinding(
                    TokenFindingKind.UNPARSEABLE_SEGMENT,
                    key="",
                    detail=f"no key: value pair in {segment.strip()!r}",
                )
            )
            continue

        key = match.group("key")
        value = match.group("value").strip()

        if key in result.tokens:
            # First occurrence wins — the same rule as the standard's Oracle
            # REGEXP_SUBSTR(..., 1, 1) parse statements.
            result.findings.append(
                TokenFinding(
                    TokenFindingKind.DUPLICATE_KEY,
                    key=key,
                    detail="first occurrence kept",
                )
            )
            continue

        spec = TOKEN_REGISTRY.get(key)
        if spec is None:
            result.tokens[key] = value or None
            result.findings.append(
                TokenFinding(
                    TokenFindingKind.UNKNOWN_KEY,
                    key=key,
                    detail="unregistered — kept verbatim, never load-bearing (C16 team-local)",
                )
            )
            continue

        if value == NULL_LITERAL:
            # Grammar rule 4: explicitly unassigned, not absent.
            result.tokens[key] = None
            continue

        result.tokens[key] = value or None
        if spec.vocabulary and value and value not in spec.vocabulary:
            result.findings.append(
                TokenFinding(
                    TokenFindingKind.VALUE_NOT_IN_VOCABULARY,
                    key=key,
                    detail=f"{value!r} not in {list(spec.vocabulary)}",
                )
            )

    return result


def required_tokens(job_type: JobType) -> tuple[str, ...]:
    """Registered tokens for a job type, in registry order. ``BOTH`` tokens
    belong to every type."""
    return tuple(
        key
        for key, spec in TOKEN_REGISTRY.items()
        if spec.job_type is job_type or spec.job_type is JobType.BOTH
    )


def validate(parsed: ParsedDescription, job_type: JobType) -> list[TokenFinding]:
    """Findings from the parse PLUS the completeness check for a job type.

    Route ids are exempted when the delivery mechanism is not ``MFTS_AGENT``:
    the standard says they are MFTS-only, and it also says the token must
    still be present carrying the literal ``NULL`` — which parses to an
    entry with value ``None``, so an explicit NULL satisfies presence while a
    genuinely missing key does not. Reported, never raised.
    """
    findings = list(parsed.findings)
    mechanism = parsed.tokens.get("DELIVERY_MECHANISM")
    route_keys = {"INBOUND_ROUTE", "OUTBOUND_ROUTE"}
    for key in required_tokens(job_type):
        if key in parsed.tokens:
            continue
        if key in route_keys and mechanism != "MFTS_AGENT":
            continue
        findings.append(
            TokenFinding(
                TokenFindingKind.MISSING_REQUIRED_TOKEN,
                key=key,
                detail=f"required for {job_type.value}",
            )
        )
    return findings
