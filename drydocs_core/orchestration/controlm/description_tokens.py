r"""Control-M DESCRIPTION-field metadata parser (G66) — the pipe-delimited
``key: value`` grammar the description-token standard authors into the
4000-char job/folder DESCRIPTION field.

WHY THIS EXISTS. The Control-M DESCRIPTION field is free text, 1 to 4000 chars,
and — critically — **not runtime-accessible as a %% variable**. It can never
drive job behavior, which is exactly what makes it safe to repurpose: the
company standard fills it with metadata that exists nowhere else in the
estate (how a file was delivered, which transfer instance carried it, who owns
it upstream, which source-system records it references). Extraction turns that
free text into rows; rows become graph edges once the HITL gate rules the
vocabulary.

WHAT THIS IS NOT. This module PARSES. It does not classify variables (that is
:mod:`.variables`), it does not resolve substitutions (that is
:mod:`.resolver`), and it does not write a graph or a store. It has no I/O.

STANDARD OF RECORD — the **Control-M greenfield job standard**
(``knowledge/standards/technology/controlm-greenfield-job-standard.md``, the
C30 ruling of 2026-08-11) with the normative authoring page at
``knowledge/standards/technology/controlm-guidelines-and-standards.md`` (C31,
§7). The earlier capture — ``description-field-metadata-plan.md`` §2b with the
verbatim company transcription at
``internal/controlm-config/reference/controlm-job-metadata-standards-capture.md``
— remains the history of what the estate actually carries (the C29 era below),
not the target state. Everything in :data:`TOKEN_REGISTRY` is ``proposed``: no
relationship-vocabulary entry, no property-term binding and no loader exists
for any of these terms, and the DL class itself is still open at gate
``email-dl-contact-point``. The registry is the parse contract, NOT a
ratification.

THE SENTINEL AND THE THREE POPULATIONS (guidelines §7.5; gate
``email-dl-contact-point`` rider §G6 rules the convention, so the marker lives
in exactly ONE constant — :data:`GRAMMAR_SENTINEL` — and a different ruling is
a one-line change here, never a rewrite). Three different things write this
field, and they cannot all be parsed the same way:

- **tagged** — begins with the sentinel (``DD1|``) at position 0: authored to
  the token standard, and the ONLY population the grammar formally governs.
  The marker itself never becomes a token and never becomes a finding. The
  test is ``startswith`` at position 0 — no strip, no substring search — so a
  description that merely QUOTES the convention in prose cannot
  false-positive, and the check stays the cheapest predicate available to a
  SQL scan over the whole estate.
- **generator-literal** — begins with one of the DPL generator's fixed
  boilerplate literals (:data:`GENERATOR_LITERALS`). Machine-generated; the
  stub-integration plan's E1 provenance discriminator keys on that literal
  match, which is exactly why the sentinel exists: it PARTITIONS the field so
  a token block and the literal never collide, and nothing already deployed
  migrates. The absence of the tag on a literal-match description already IS
  the provenance signal — no ``GENERATED_BY`` token is ever minted.
- **untagged** — everything else. Untagged is NOT a defect and is never
  reported as one: untagged means unread. A description with no registered
  key is legacy waterfall prose and yields no tokens at all (prose must not
  manufacture tokens that mimic a C16 annotation). A description that DOES
  carry registered keys is the pre-sentinel C29 estate — ~240K deployed
  descriptions authored before the marker existed — and this parser's job is
  to read the field as the estate actually filled it, so those parse in full
  and validate against the era they were authored to (see ERAS).

THE DIGIT IS A VERSION, NOT A TEMPLATE ID. ``DD1|`` means "version 1 of this
grammar" and nothing else; a future ``DD2|`` is read side by side through a
grammar migration (:attr:`ParsedDescription.grammar_version`). The marker MUST
NOT select a job template — ``TASKTYPE`` plus the registered ``JOB_ROLE``
token do that (guidelines §7.2) — because spending the version slot on
template identity leaves the first grammar change with no way to announce
itself.

FOLDER SCOPE IS PREFERRED, DOCUMENTED HERE, NOT ENFORCED. ``get_description()``
is generator-owned, so a tagged block on a GENERATED JOB is overwritten at the
next regeneration — the tag does not protect it. Folder descriptions are
hand-held, which is where authored metadata survives. The parser reads
whatever it is given; this note exists so nobody tags jobs and loses the
block. The adoption measure is *tagged folders ÷ folders* — a number that
grows (:func:`sentinel_coverage`) — never "how much of our metadata is wrong",
a number that never closes.

ERAS. C30 retired tokens without unwriting the deployed estate: a greenfield
standard governs what gets AUTHORED next, it cannot retroactively rewrite
~240K descriptions. So retired tokens stay REGISTERED with a lifecycle marker
(:attr:`TokenSpec.retired_by`) — a legacy description parses them as a
known-retired token, never as an unregistered key — and completeness is
era-aware: :func:`required_tokens` returns the CURRENT (C30) set and never
demands a retired token, while :func:`validate` holds a legacy description
only to the set it was authored to. The era discriminator is the sentinel
(tagged ⇒ C30) or, failing that, the presence of a C30-introduced token.

THE GRAMMAR (six rules, all from the standard, all load-bearing):

1. **Pipe is the only delimiter.** Semicolons appear INSIDE values — a
   multi-address distribution list is one token, not several. Splitting on
   ``;`` shreds a DL into fragments that look like keys. (``REC_ID`` is the
   one comma-separated token — the spec's ``separator`` says so.)
2. **Split on the FIRST colon only.** Values legally contain colons
   (``SeriesSLA: 17:00 EST``). Splitting on every colon truncates the value
   at the first time separator.
3. **Whitespace-tolerant on both sides.** The wild carries both ``| USER: x``
   and ``|USER:x`` — the standard's own examples are inconsistent.
4. **A key with no value still emits its token.** The C29 standard REQUIRED
   ``PDN_SNOW_QUEUE: NULL`` to be present even when unassigned, so a parse
   always finds the key and returns a parseable result rather than a missing
   match. Oracle does ``NULLIF(..., 'NULL')``; here the literal string
   ``NULL`` becomes Python ``None``, so "explicitly unassigned" and "key
   absent" stay distinguishable.
5. **Unknown keys are RETURNED, never dropped** — within a structured block.
   The C16 key-prefix governance makes a bare key a legal team-local
   annotation: preserved verbatim, never load-bearing. Dropping one loses
   evidence; promoting one breaks the governance. (In an untagged description
   with NO registered key there is no block — that is prose, and prose yields
   nothing; see THE SENTINEL above.)
6. **A value outside its vocabulary is a FINDING, not an exception.** Same
   discipline as the FACT_REGISTRY next door ("aliases suggest, values
   decide") and the G16 WARN stream: report and carry on, never raise, never
   silently coerce. Where the standard rules a SHAPE rather than a closed set
   (``FTS_ID``), the shape decides and the vocabulary tuple documents known
   members without closing the set.

DELIBERATE NON-GOALS. No escaping convention is defined by the standard for a
value that itself contains ``|`` — guidelines §7.5 rules the embedded pipe a
visible defect (the fragment surfaces as an unknown key, returned rather than
dropped), and the plan records the missing escape as open item 2. This parser
therefore cannot recover such a value and does not pretend to: the pipe wins,
and the fragment after it is read as the next token. Recording the limitation
is the honest move; inventing an escape here would fork the standard.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field
from enum import Enum

#: The token the standard uses to say "this key is deliberately unassigned".
#: Distinct from an absent key — see grammar rule 4.
NULL_LITERAL = "NULL"

#: Guidelines §7.5: the first characters of any description authored to the
#: token standard. ONE constant, one predicate (position-0 ``startswith``) —
#: gate ``email-dl-contact-point`` §G6 rules the convention, so a different
#: ruling is a one-line change here.
GRAMMAR_SENTINEL = "DD1|"

#: The version-aware form of :data:`GRAMMAR_SENTINEL`: ``DD<version>|`` at
#: position 0. The digit is a grammar VERSION, never a template id (§7.5) —
#: ``DD1`` and a future ``DD2`` are read side by side through a migration.
_SENTINEL = re.compile(r"^DD(?P<version>[0-9]+)\|")

#: The DPL generator's fixed boilerplate, stamped verbatim by
#: ``get_description()``. Prefix-matched at position 0: the second literal is
#: completed by the dataset name at generation time. The stub-integration
#: plan's E1 provenance discriminator keys on these strings EXACTLY as they
#: are — which is why the sentinel partitions the field instead of a token
#: block ever landing next to them.
GENERATOR_LITERALS = (
    "Generated Control-M Folder",
    "Generated job to trigger DPL transformation in AWS for dataset: ",
)

#: Splits on the FIRST colon only (grammar rule 2). The key is restricted to
#: token characters so a colon inside prose cannot be mistaken for a key
#: boundary; everything after the first colon is the value, verbatim.
_PAIR = re.compile(r"^\s*(?P<key>[A-Za-z0-9_.\-]+)\s*:\s*(?P<value>.*)$", re.DOTALL)


class DescriptionPopulation(str, Enum):
    """Which of the three §7.5 populations a description belongs to. The
    populations are DISJOINT by construction — that is the whole point of the
    sentinel — so both the token parser and the E1 provenance discriminator
    keep working with zero migration of anything already deployed."""

    #: begins with the sentinel — authored to the token standard
    TAGGED = "tagged"
    #: begins with a DPL generator boilerplate literal — machine-generated
    GENERATOR_LITERAL = "generator-literal"
    #: everything else — legacy prose (unread) or the pre-sentinel C29 estate
    UNTAGGED = "untagged"


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
    #: allowed values, or ``None`` when the value is free text. When
    #: ``value_shape`` is also set, this tuple documents KNOWN members and
    #: the shape decides (grammar rule 6).
    vocabulary: tuple[str, ...] | None = None
    #: True when the standard says the value may be several entries separated
    #: by ``separator`` INSIDE the one token (grammar rule 1)
    multivalued: bool = False
    #: the INNER separator for a multivalued value. ``;`` everywhere except
    #: ``REC_ID``, which C30 §5.1 rules comma-separated.
    separator: str = ";"
    #: regex the whole value must match when the standard rules a SHAPE, not
    #: a closed set (C30 §5.1: FTS_ID is ``FTS[A-Z]*[0-9]+`` because new
    #: instances appear and FTSCAT1 already breaks a naive FTS<digit> enum)
    value_shape: str | None = None
    #: the ruling that retired this token from the AUTHORING standard, or
    #: ``""`` while it is current. Retire-in-place, never delete: the
    #: deployed estate still carries the token and deleting the entry would
    #: silently reclassify real estate data as a C16 team-local annotation —
    #: the one reading governance cannot afford.
    retired_by: str = ""
    #: the ruling that introduced this token AFTER the C29 capture, or ``""``
    #: for an original member. Drives the era-aware completeness check: a
    #: legacy description is never held to a token that did not exist when it
    #: was authored.
    introduced_by: str = ""
    note: str = ""
    carrier: Carrier = Carrier.DESCRIPTION


#: Delivery mechanisms (capture Part D §3). Route ids are MFTS_AGENT-only —
#: the other two mechanisms carry the literal NULL in both route tokens.
DELIVERY_MECHANISMS = ("MFTS_AGENT", "SFTP_DIRECT", "API_GENERATED")

#: Job-role discriminator values. PUBLISHER is the C29 capture (Part E §2);
#: PLACEMENT and TRUST_INGEST are the C30 greenfield command-job set (§5.2 /
#: guidelines §7.2 — "that is the whole set"). All three stay legal: aliases
#: suggest, values decide, and the estate still carries the C29 spelling.
JOB_ROLES = ("PUBLISHER", "PLACEMENT", "TRUST_INGEST")

#: Known MFTS File Transfer instances (C30 §5.1). Documentation, NOT a closed
#: enum — the FTS_ID check is the SHAPE on its spec, because new instances
#: appear and FTSCAT1 already breaks a naive FTS<digit> pattern.
FTS_INSTANCES = ("FTS1", "FTS2", "FTS6", "FTS7", "FTSCAT1")

#: Every description token the standard defines — current AND retired — keyed
#: by the token spelling as it appears in the field. The single source both
#: the parser and the published register read from, so code and document
#: cannot drift (guarded by the registry-vs-standard agreement test).
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
            key="FTS_ID",
            job_type=JobType.FILE_WATCHER,
            sql_column="FTS_ID",
            ontology_term="ex:mftsEnv",
            vocabulary=FTS_INSTANCES,
            value_shape=r"FTS[A-Z]*[0-9]+",
            introduced_by="C30 (2026-08-11) §5.1",
            note=(
                "Bare MFTS File Transfer instance id — the author drops a version "
                "fragment ('ST 6.0 - FTS2' → 'FTS2'). Carries the transfer-instance "
                "concept ENV held on a watcher (the proposed term follows the "
                "concept); the check is the shape, the vocabulary documents known "
                "members. Feeds dprod:inputPort."
            ),
        ),
        TokenSpec(
            key="REC_ID",
            job_type=JobType.FILE_WATCHER,
            sql_column="REC_ID",
            ontology_term="ex:sourceSystemReference on dprod:inputPort",
            multivalued=True,
            separator=",",
            introduced_by="C30 (2026-08-11) §5.1",
            note=(
                "Source-system reference id(s), comma-separated. Explicitly NOT a "
                "route id (C30: a watcher is inherently inbound, so this is a "
                "SOURCE reference, not a route pair)."
            ),
        ),
        TokenSpec(
            key="ENV",
            job_type=JobType.FILE_WATCHER,
            sql_column="ENV",
            ontology_term="ex:mftsEnv",
            retired_by="C30 (2026-08-11) §5.1 — ENV → FTS_ID on a watcher",
            note=(
                "Transfer environment; property of the agent. One key carried two "
                "concepts (transfer instance on a watcher, deployment environment "
                "on command jobs): the transfer instance moved to FTS_ID and ENV "
                "keeps the meaning it already has everywhere else."
            ),
        ),
        TokenSpec(
            key="INBOUND_ROUTE",
            job_type=JobType.FILE_WATCHER,
            sql_column="MFTS_INBOUND_ROUTE_ID",
            ontology_term="ex:mftsRouteId on dprod:inputPort",
            retired_by="C30 (2026-08-11) §5.1 — a watcher is inherently inbound; direction rides the job type",
            note=(
                "MFTS_AGENT only; literal NULL otherwise. Production observation "
                "carries a NUMERIC route id under the single key ROUTE_ID — the "
                "directional split is new and unreconciled (Idea-104, still the "
                "SME's: retiring the pair does NOT answer whether the real MFT "
                "route id is the numeric form or the MFTS_RT_* string)."
            ),
        ),
        TokenSpec(
            key="OUTBOUND_ROUTE",
            job_type=JobType.FILE_WATCHER,
            sql_column="MFTS_OUTBOUND_ROUTE_ID",
            ontology_term="ex:mftsRouteId on dprod:outputPort",
            retired_by="C30 (2026-08-11) §5.1 — a watcher is inherently inbound; the outbound leg is the FILE_DIR variable",
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
        # -- Publisher / command jobs ---------------------------------------
        TokenSpec(
            key="JOB_ROLE",
            job_type=JobType.PUBLISHER,
            sql_column="JOB_ROLE",
            ontology_term="ex:jobRole",
            vocabulary=JOB_ROLES,
            note=(
                "The discriminator that decides which table a job lands in. Under "
                "C30 §5.2 it is the ENTIRE command-job description (with the "
                "sentinel): PLACEMENT / TRUST_INGEST."
            ),
        ),
        TokenSpec(
            key="PDN_DL",
            job_type=JobType.PUBLISHER,
            sql_column="PDN_DL",
            ontology_term="ex:consumerContact on dprod:outputPort",
            multivalued=True,
            retired_by="C30 (2026-08-11) §5.3 — the PDN contact moved to folder scope as EMAIL_DL_PDN",
            note="Downstream consumers notified on publish (Production Delay Notification — business users, not a support tier).",
        ),
        TokenSpec(
            key="PDN_SNOW_QUEUE",
            job_type=JobType.PUBLISHER,
            sql_column="PDN_SNOW_QUEUE",
            ontology_term="ex:serviceNowQueue",
            retired_by="C30 (2026-08-11) §5.3 — dropped outright: it paired a business notification with a ServiceNow TECHNICIAN queue; the escalation DB owns technician routing",
            note=(
                "Was MANDATORY EVEN WHEN EMPTY (grammar rule 4). Distinct subject "
                "from the observed SourceSnowQueue — downstream consumer's queue, "
                "not the source system's."
            ),
        ),
        # -- Both (C29 era; C30 moved the pair to folder scope) -------------
        TokenSpec(
            key="EMAIL_DL_L3",
            job_type=JobType.BOTH,
            sql_column="EMAIL_DL_L3",
            ontology_term="ex:supportContact",
            multivalued=True,
            retired_by="C30 (2026-08-11) §5.3 — contacts are folder-scope documentation; see FOLDER_VARIABLES['EMAIL_DL_L3']",
            note="Dev / Scrum team. Folder-variable twin was spelled L3_EMAIL_DL_NM pre-C30 — carrier and spelling both differ; precedence unsettled (gate rider G2).",
        ),
        TokenSpec(
            key="EMAIL_DL_L2",
            job_type=JobType.BOTH,
            sql_column="EMAIL_DL_L2",
            ontology_term="ex:supportContact",
            multivalued=True,
            retired_by="C30 (2026-08-11) §5.3 — contacts are folder-scope documentation; see FOLDER_VARIABLES['EMAIL_DL_L2']",
            note="Ops support group. Folder-variable twin was spelled L2_EMAIL_DL_NM pre-C30.",
        ),
    )
}

#: Folder-level VARIABLE names the standards add (capture Part A REQ-1, plus
#: the C30 §5.3 contact relocation). Registered for the register's
#: completeness and for validation; they are NOT description tokens and never
#: appear in a parse result. The C30 spellings and the pre-rename twins are
#: BOTH registered so a live extract authored either way still resolves.
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
            key="EMAIL_DL_L2",
            job_type=JobType.BOTH,
            sql_column="",
            ontology_term="ex:supportContact",
            multivalued=True,
            carrier=Carrier.FOLDER_VARIABLE,
            introduced_by="C30 (2026-08-11) §5.3",
            note=(
                "Ops support tier at folder scope — the C30 spelling. Spelled "
                "L2_EMAIL_DL_NM before the rename; both resolve."
            ),
        ),
        TokenSpec(
            key="EMAIL_DL_L3",
            job_type=JobType.BOTH,
            sql_column="",
            ontology_term="ex:supportContact",
            multivalued=True,
            carrier=Carrier.FOLDER_VARIABLE,
            introduced_by="C30 (2026-08-11) §5.3",
            note=(
                "Dev / Scrum support tier at folder scope — the C30 spelling. "
                "Spelled L3_EMAIL_DL_NM before the rename; both resolve."
            ),
        ),
        TokenSpec(
            key="EMAIL_DL_PDN",
            job_type=JobType.BOTH,
            sql_column="",
            ontology_term="ex:consumerContact",
            multivalued=True,
            carrier=Carrier.FOLDER_VARIABLE,
            introduced_by="C30 (2026-08-11) §5.3",
            note=(
                "Production Delay Notification — downstream BUSINESS users, not a "
                "support tier. Same carrier as the L2/L3 twins, different audience, "
                "different ontology role: the register must never collapse them "
                "(C30 §5.3). No pre-rename twin exists — the folder-variable table "
                "did not carry a PDN member before C30."
            ),
        ),
        TokenSpec(
            key="L2_EMAIL_DL_NM",
            job_type=JobType.BOTH,
            sql_column="",
            ontology_term="ex:supportContact",
            multivalued=True,
            carrier=Carrier.FOLDER_VARIABLE,
            note="Pre-C30 spelling of the folder-scope ops support DL — renamed EMAIL_DL_L2 by C30 §5.3; kept so live extracts authored either way resolve.",
        ),
        TokenSpec(
            key="L3_EMAIL_DL_NM",
            job_type=JobType.BOTH,
            sql_column="",
            ontology_term="ex:supportContact",
            multivalued=True,
            carrier=Carrier.FOLDER_VARIABLE,
            note="Pre-C30 spelling of the folder-scope dev/Scrum DL — renamed EMAIL_DL_L3 by C30 §5.3; kept so live extracts authored either way resolve.",
        ),
    )
}


class TokenFindingKind(str, Enum):
    """Everything the parser can object to. All are reported; none raises."""

    #: value not in the token's controlled vocabulary (or, where the spec
    #: rules a SHAPE, not matching it)
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
    ``population`` says which §7.5 population the raw text belongs to, and
    ``grammar_version`` carries the sentinel's digit for the tagged one.
    """

    raw: str
    tokens: dict[str, str | None] = field(default_factory=dict)
    findings: list[TokenFinding] = field(default_factory=list)
    population: DescriptionPopulation = DescriptionPopulation.UNTAGGED
    grammar_version: int | None = None

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
        """A multivalued token split on its INNER separator — ``;`` unless
        the spec says otherwise (``REC_ID`` is comma-separated, C30 §5.1).
        Returns ``[]`` for an absent key or an explicit NULL."""
        raw = self.tokens.get(key)
        if not raw:
            return []
        spec = TOKEN_REGISTRY.get(key)
        separator = spec.separator if spec else ";"
        return [part.strip() for part in raw.split(separator) if part.strip()]

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

    Classifies the text into its §7.5 population first. A tagged description
    has its sentinel stripped (never a token, never a finding) and is parsed
    under the full grammar. A generator literal yields nothing — the E1
    provenance discriminator owns that population. Untagged text is parsed
    and kept ONLY if it carries at least one registered key (the pre-sentinel
    C29 estate); otherwise it is legacy prose and yields zero tokens and zero
    findings, because untagged is not a defect and prose must not manufacture
    tokens that mimic a C16 annotation.
    """
    raw = text or ""
    result = ParsedDescription(raw=raw)
    if not raw.strip():
        return result

    sentinel = _SENTINEL.match(raw)  # position 0 — no strip (§7.5)
    if sentinel is not None:
        result.population = DescriptionPopulation.TAGGED
        result.grammar_version = int(sentinel.group("version"))
        body = raw[sentinel.end() :]
    elif any(raw.startswith(literal) for literal in GENERATOR_LITERALS):
        result.population = DescriptionPopulation.GENERATOR_LITERAL
        return result
    else:
        body = raw

    for segment in body.split("|"):
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
        if value and spec.value_shape is not None:
            # Grammar rule 6, shape form: the shape decides, the vocabulary
            # tuple only documents known members.
            if re.fullmatch(spec.value_shape, value) is None:
                result.findings.append(
                    TokenFinding(
                        TokenFindingKind.VALUE_NOT_IN_VOCABULARY,
                        key=key,
                        detail=f"{value!r} does not match shape {spec.value_shape!r}",
                    )
                )
        elif spec.vocabulary and value and value not in spec.vocabulary:
            result.findings.append(
                TokenFinding(
                    TokenFindingKind.VALUE_NOT_IN_VOCABULARY,
                    key=key,
                    detail=f"{value!r} not in {list(spec.vocabulary)}",
                )
            )

    if (
        result.population is DescriptionPopulation.UNTAGGED
        and not result.is_structured
    ):
        # Legacy waterfall prose — untagged means unread. Keeping the
        # manufactured pairs would make prose indistinguishable from a
        # legitimate C16 annotation inside a real block.
        result.tokens.clear()
        result.findings.clear()

    return result


def _registry_for(job_type: JobType) -> list[TokenSpec]:
    return [
        spec
        for spec in TOKEN_REGISTRY.values()
        if spec.job_type is job_type or spec.job_type is JobType.BOTH
    ]


def required_tokens(job_type: JobType) -> tuple[str, ...]:
    """Registered tokens the CURRENT (C30) standard requires for a job type,
    in registry order. ``BOTH`` tokens belong to every type. Era-aware by
    exclusion: a retired token is NEVER demanded here — a job authored to C30
    validates clean without it, while :func:`validate` still holds a legacy
    description to the set it was authored to."""
    return tuple(spec.key for spec in _registry_for(job_type) if not spec.retired_by)


def _legacy_required_tokens(job_type: JobType) -> tuple[str, ...]:
    """The C29-era set: every original-capture token for the job type,
    retired or not, EXCLUDING anything a later ruling introduced — a legacy
    description is never held to a token that did not exist when it was
    authored."""
    return tuple(spec.key for spec in _registry_for(job_type) if not spec.introduced_by)


#: Tokens whose presence marks a description as authored to C30 even without
#: the sentinel (the greenfield corpus predating DD1| adoption).
_C30_MARKER_TOKENS = frozenset(
    key for key, spec in TOKEN_REGISTRY.items() if spec.introduced_by
)


def validate(parsed: ParsedDescription, job_type: JobType) -> list[TokenFinding]:
    """Findings from the parse PLUS the era-aware completeness check.

    The era discriminator: a TAGGED description, or one carrying a
    C30-introduced token, is held to the current (C30) required set; an
    untagged structured description is the pre-sentinel estate and is held
    only to the C29 set it was authored to. A generator literal and untagged
    prose are UNREAD — untagged is not a defect and is never reported as one,
    so no completeness findings are manufactured for them.

    Route ids are exempted when the delivery mechanism is not ``MFTS_AGENT``:
    the C29 standard says they are MFTS-only, and it also says the token must
    still be present carrying the literal ``NULL`` — which parses to an
    entry with value ``None``, so an explicit NULL satisfies presence while a
    genuinely missing key does not. Reported, never raised.
    """
    findings = list(parsed.findings)
    if parsed.population is DescriptionPopulation.GENERATOR_LITERAL:
        return findings
    if (
        parsed.population is DescriptionPopulation.UNTAGGED
        and not parsed.is_structured
    ):
        return findings

    current_era = parsed.population is DescriptionPopulation.TAGGED or any(
        key in parsed.tokens for key in _C30_MARKER_TOKENS
    )
    required = (
        required_tokens(job_type) if current_era else _legacy_required_tokens(job_type)
    )

    mechanism = parsed.tokens.get("DELIVERY_MECHANISM")
    route_keys = {"INBOUND_ROUTE", "OUTBOUND_ROUTE"}
    for key in required:
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


@dataclass(frozen=True)
class SentinelCoverage:
    """Adoption, not compliance (§7.5): *tagged ÷ total* is a number that
    grows, unlike "how much of our metadata is wrong", a number that never
    closes. Fewer than ten folders carry the standard today — a sample
    proving the mechanism, not a shortfall."""

    tagged: int = 0
    total: int = 0

    @property
    def ratio(self) -> float:
        return self.tagged / self.total if self.total else 0.0


def sentinel_coverage(descriptions: Iterable[str | None]) -> SentinelCoverage:
    """Count sentinel adoption over a set of descriptions. Position-0
    ``startswith`` only — the same predicate a SQL scan would use — so a
    description that quotes the convention in prose never counts."""
    tagged = 0
    total = 0
    for text in descriptions:
        total += 1
        if text is not None and _SENTINEL.match(text) is not None:
            tagged += 1
    return SentinelCoverage(tagged=tagged, total=total)
