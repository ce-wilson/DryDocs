r"""Control-M variable taxonomy classifier (C3/C4 normalization, Phase A).

Classifies each ``%%NAME|VALUE`` definition from the variable extract into
the taxonomy that drives downstream normalization (resolution in Phase B,
command parsing in Phase C). One primary ``VariableKind`` per definition,
plus feature flags and extracted tokens — classification never loses the
raw text.

Kind precedence (first match wins; value-structure kinds outrank
name-registry kinds because a fact-named variable holding a cross-flow
pointer is a pointer, not a fact):

    MALFORMED       name is empty / contains whitespace / not a valid token
    EMBEDDED_SHELL  PRECMD / POSTCMD (and the observed POSCMD typo) — value
                    is shell text for the Phase-C mini-parser
    PLUGIN_NS       namespaced name (%%FileWatch-*, %%UCM-*) — routed to the
                    matching APPL_TYPE handler
    FLOW_REF        value is a global (%%\VAR) or pool-qualified
                    (%%\\POOL\VAR) reference — vendor scopes for cross-job
                    shared state (controlm-variables.md §Scope Levels); this
                    shop uses pools to hand values between dataflow jobs.
                    Becomes a REFERENCES_FLOW edge candidate, never inlined
    DYNAMIC_NAME    adjacent %%refs compose a variable *name* at runtime
                    (%%SCRIPT_PATH_%%HOSTNM, %%TENV%%CURRENVIRON) — resolve
                    per-environment in Phase B, ambiguous by construction
    SEMANTIC_FACT   name in the fact registry (SEAL, FID_*, DATAFLOW, ...)
                    with a plain value — mined directly into STG_APP_FACT
    SYSTEM_FUNC     value uses only Control-M system tokens — functions
                    (CALCDATE, SUBSTR, GETENV, WCALC, BLANK) and/or system
                    variables (ODATE, ORDERID, JOBNAME, ...), in either
                    %%TOKEN or century-format %%$TOKEN syntax — canonicalized
                    to symbolic tokens, never "resolved"
    VAR_REF         value references other USER variables — Phase B substitutes
    LITERAL         none of the above

Vendor reference: external/orchestration/bmc-controlm/controlm-variables.md (Control-M SaaS docs
applied to 9.0.21.300 — see its version notice). Confirmed there: resolution
priority job > folder > global > system; SMART-folder variables inherit to
sub-folders and jobs; resolution happens at execution time (so date tokens
are canonicalized, not resolved). The doc's name/value constraint table
(alphanumeric-only names, 214-char values) is contradicted by observed
9.0.x production data and is NOT enforced here.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum

from .commands import is_registered_launcher


class VariableKind(str, Enum):
    MALFORMED      = "MALFORMED"
    EMBEDDED_SHELL = "EMBEDDED_SHELL"
    PLUGIN_NS      = "PLUGIN_NS"
    FLOW_REF       = "FLOW_REF"
    DYNAMIC_NAME   = "DYNAMIC_NAME"
    SEMANTIC_FACT  = "SEMANTIC_FACT"
    SYSTEM_FUNC    = "SYSTEM_FUNC"
    VAR_REF        = "VAR_REF"
    LITERAL        = "LITERAL"


# --- token grammar ------------------------------------------------------------

# any %%$TOKEN — the classic AutoEdit century-format (4-digit-year) notation
# for system tokens, still live in 9.0.x even though the SaaS docs drop it.
# NOT every %%$TOKEN is a system token though: this shop also references
# user variables with dollar syntax (observed: %%$PRD_END_DATE_1,
# %%$DROPBOX). Tokens are split via the registries below.
DOLLAR_TOKEN_RE = re.compile(r"%%\$([A-Za-z][A-Za-z0-9_]*)")

# Control-M function library, per external/orchestration/bmc-controlm/controlm-variables.md
# (§Variable Functions): CALCDATE, SUBSTR, GETENV, WCALC, BLANK. Both
# %%FUNC and %%$FUNC syntaxes occur (observed: %%$CALCDATE ... and plain
# %%SUBSTR %%DATACENTER 1 1).
KNOWN_SYSTEM_FUNCS = frozenset({"CALCDATE", "SUBSTR", "GETENV", "WCALC", "BLANK"})

# Control-M system variables, per external/orchestration/bmc-controlm/controlm-variables.md
# (§System Variables Reference): job-general, scheduling, environment, and
# action variables. Referenced as %%NAME or century-format %%$NAME — never
# user-defined, so they must NOT enter the Phase-B resolution hot set.
KNOWN_SYSTEM_VARIABLES = frozenset({
    # job general
    "JOBNAME", "OWNER", "APPLIC", "ORDERID", "RUNCOUNT",
    # scheduling (ODATE-prefixed variants like ODATE_1 handled separately)
    "ODATE", "NEXT", "ODAY", "OMONTH", "OYEAR", "OWDAY",
    # environment
    "DATE", "TIME", "MONTH", "DAY", "YEAR", "WDAY",
    # action / status
    "COMPSTAT", "AVG_TIME", "JOBID", "NODEID",
})


def _is_system_func(token: str) -> bool:
    return token.upper() in KNOWN_SYSTEM_FUNCS


def _is_system_var(token: str) -> bool:
    t = token.upper()
    return t in KNOWN_SYSTEM_VARIABLES or t.startswith("ODATE")

# backslash-scoped references, per external/orchestration/bmc-controlm/controlm-variables.md
# (§Scope Levels): %%\VAR is a GLOBAL variable (server-wide), %%\\POOL\VAR
# is a pool-qualified reference. This shop uses the two-segment form to
# hand values between jobs of a dataflow (%%\\SCRA_REPORTING\PROID) — the
# graph treats both as cross-job shared state. Separator backslash count
# varies in the wild; match one-or-more.
POOL_REF_RE = re.compile(r"%%\\+(\w+)\\+(\w+)")     # %%\\POOL\VAR
GLOBAL_REF_RE = re.compile(r"%%\\+(\w+)(?!\\|\w)")  # %%\VAR with no second segment

# plain %%VAR reference — no $ (system func), no \ (flow ref), no dash
# (namespaced names never appear as in-value references)
PLAIN_REF_RE = re.compile(r"%%(?![$\\])([A-Za-z_][A-Za-z0-9_]*)")

# a %%ref abutting another %%ref composes a variable NAME at runtime:
# %%TENV%%CURRENVIRON, %%SCRIPT_PATH_%%HOSTNM. Greedy var-name matching in
# Control-M makes these ambiguous — Phase B expands them per environment.
ADJACENT_REF_RE = re.compile(r"%%[A-Za-z_][A-Za-z0-9_]*%%")

# valid variable name after the %% prefix is stripped: word chars, with an
# optional single namespace dash segment (FileWatch-FILE_PATH, UCM-CLUSTER_NAME)
VALID_NAME_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*(-[A-Za-z0-9_]+)*$")

# environment-triplet suffix (FID_D / FID_Q / FID_P, ENV_D / ENV_T / ENV_P,
# SCRIPT_PATH_D/Q/P ...). A candidate only — confirmed at job level when at
# least two siblings of the same base name exist (see classify_job_variables).
ENV_SUFFIX_RE = re.compile(r"^(?P<base>.+)_(?P<env>[DQPT])$")

ENV_LETTER_MAP = {
    "D": "Development",
    "Q": "QA",
    "T": "QA",  # observed alternate test-environment letter (ENV_T / TENV_T)
    "P": "Production",
}

# PRECMD / POSTCMD hold shell text. POSCMD is a real typo observed in
# production definitions (folder 161947) — the value is still shell.
SHELL_VAR_NAMES = {"PRECMD", "POSTCMD", "POSCMD", "PRECOMMAND", "POSTCOMMAND"}

# name -> STG_APP_FACT.fact_type. Names are matched after stripping a
# confirmed env suffix, so FID_D / FID_Q / FID_P all map through FID.
FACT_REGISTRY: dict[str, str] = {
    "SEAL":            "SEAL",
    "SEALID":          "SEAL",
    "FID":             "FID",
    "RFID":            "FID",
    "DS_ID":           "DS_ID",
    "DS_VER":          "DS_VER",
    "DS_NAME":         "DS_NAME",
    "PID":             "DS_ID",
    "DATAFLOW":        "DATAFLOW",
    # -- artifact / launcher canonicals (G16; gate cmdline-nfr-vetting SME-4;
    # ratification source = the digested v2 command-line/variables standard).
    # A NAME here is a SUGGESTION only — _value_fact() decides by VALUE
    # (aliases suggest, values decide). IMAGE -> ARTIFACT_URI is the v2
    # decision-log clean break (the old IMAGE -> IMAGE mapping is removed).
    "ETL_ARTIFACT_URI":     "ARTIFACT_URI",
    "IMAGE":                "ARTIFACT_URI",
    "IMAGE_NAME":           "ARTIFACT_URI",
    "IMG_PATH":             "ARTIFACT_URI",
    "CONTAINER_IMAGE":      "ARTIFACT_URI",
    "JAR_PATH":             "ARTIFACT_URI",
    "USER_JAR":             "ARTIFACT_URI",
    "JAR_LOC":              "ARTIFACT_URI",
    "JAR_NAME":             "ARTIFACT_URI",
    "MULTI_FILE_JAR":       "ARTIFACT_URI",
    "PYTHON_SCRIPT":        "ARTIFACT_URI",   # gap-analysis gotcha: often holds the launcher
    "PY_PATH":              "ARTIFACT_URI",   # ditto — the value contract corrects it
    "ETL_ARTIFACT_KIND":    "ARTIFACT_KIND",
    "ETL_ARTIFACT_SHA":     "ARTIFACT_SHA",
    "IMAGE_SHA":            "ARTIFACT_SHA",
    "PRE_MR_IMAGE_SHA":     "ARTIFACT_SHA",
    "ETL_PLATFORM":         "ETL_PLATFORM",
    "ETL_PLATFORM_FLAGS":   "PLATFORM_FLAGS",
    "LAUNCHER_SCRIPT_PATH": "LAUNCHER_SCRIPT_PATH",
    "PY_LAUNCH":            "LAUNCHER_SCRIPT_PATH",
    "PY_LAUNCHER":          "LAUNCHER_SCRIPT_PATH",
    "SCRIPT_PATH":          "LAUNCHER_SCRIPT_PATH",
    "ACCELERATOR_PATH":     "LAUNCHER_SCRIPT_PATH",
    "MULTI_SCRIPT_PATH":    "LAUNCHER_SCRIPT_PATH",
    "TGT_TABLE":       "TGT_TABLE",
    "TGT_TABLE_PQU":   "TGT_TABLE",
    "TGT_DB_NM":       "TGT_DB",
    "APP_NAME":        "APP_NAME",
    "ALIAS":           "ALIAS",
    "NOTIFY":          "NOTIFICATION",
    "EMAIL":           "NOTIFICATION",
    "EMAIL_GRP":       "NOTIFICATION",
    "EMAIL_LIST":      "NOTIFICATION",
}

# --- G16: value contracts (aliases suggest, VALUES decide) ---------------------

# a bare hex digest (sha1 40 / sha256 64) is a content hash, never a URI —
# without this, IMAGE_SHA-style values pollute ARTIFACT_URI (gap analysis)
_SHA_DIGEST_RE = re.compile(r"^([0-9a-f]{40}|[0-9a-f]{64})$", re.IGNORECASE)

#: fact_type -> the canonical (WARN-free) variable name; any other name that
#: rolls up here is an ALIAS — still materialized (non-destructive on legacy),
#: but flagged for rename via ClassifiedVariable.fact_alias_of
CANONICAL_FACT_NAMES: dict[str, str] = {
    "ARTIFACT_URI":         "ETL_ARTIFACT_URI",
    "ARTIFACT_KIND":        "ETL_ARTIFACT_KIND",
    "ARTIFACT_SHA":         "ETL_ARTIFACT_SHA",
    "ETL_PLATFORM":         "ETL_PLATFORM",
    "PLATFORM_FLAGS":       "ETL_PLATFORM_FLAGS",
    "LAUNCHER_SCRIPT_PATH": "LAUNCHER_SCRIPT_PATH",
}


def _value_fact(text: str) -> str | None:
    """Classify a plain literal VALUE into the artifact/launcher family.

    The load-bearing G16 rule: a value that IS a registered named launcher is
    LAUNCHER_SCRIPT_PATH regardless of the variable's name (the JAR_PATH ->
    dt-launcher.sh gotcha); a bare SHA digest is ARTIFACT_SHA, never a URI.
    Returns None when the value carries no contract evidence."""
    stripped = text.strip()
    if not stripped or any(ch.isspace() for ch in stripped):
        return None  # multi-token values are commands, not single artifacts
    if _SHA_DIGEST_RE.match(stripped):
        return "ARTIFACT_SHA"
    if is_registered_launcher(stripped):
        return "LAUNCHER_SCRIPT_PATH"
    return None


@dataclass(frozen=True)
class ClassifiedVariable:
    """One classified variable definition. ``raw_name`` / ``raw_value`` are
    always preserved; everything else is derived."""

    raw_name: str
    raw_value: str | None
    name: str                                  # raw_name minus the %% prefix
    kind: VariableKind
    # feature extraction (populated regardless of primary kind)
    plugin_namespace: str | None = None        # 'FileWatch', 'UCM', ...
    fact_type: str | None = None               # FACT_REGISTRY hit, if any
    env_candidate: str | None = None           # D/Q/P/T suffix letter (unconfirmed)
    env_tag: str | None = None                 # confirmed by classify_job_variables
    plain_refs: tuple[str, ...] = ()           # user %%VAR references in value
    dollar_refs: tuple[str, ...] = ()          # user vars referenced as %%$VAR
    system_funcs: tuple[str, ...] = ()         # CALCDATE, SUBSTR, GETENV, ...
    system_vars: tuple[str, ...] = ()          # ODATE, ORDERID, JOBNAME, ...
    flow_refs: tuple[tuple[str, str], ...] = ()  # (pool/flow, var) two-segment refs
    global_refs: tuple[str, ...] = ()          # %%\VAR single-segment global refs
    has_adjacent_refs: bool = False            # dynamic-name composition hazard
    value_is_delimiter: bool = False           # value is pure punctuation (dot-smuggling)
    fact_name_mismatch: bool = False           # G16 WARN: name suggested one fact family,
                                               # the VALUE decided another (values win)
    fact_alias_of: str | None = None           # G16 WARN: canonical name to rename to;
                                               # None == canonical spelling (WARN-free)

    @property
    def all_var_refs(self) -> tuple[str, ...]:
        """Every USER-variable reference, regardless of %% / %%$ syntax —
        the Phase-B resolution input set. System variables and functions
        are excluded: they canonicalize to symbolic tokens, not lookups."""
        return self.plain_refs + self.dollar_refs

    def with_env_tag(self, env_tag: str) -> "ClassifiedVariable":
        return ClassifiedVariable(**{**self.__dict__, "env_tag": env_tag})


def _strip_prefix(name: str) -> str:
    return name[2:] if name.startswith("%%") else name


def classify_variable(name: str, value: str | None) -> ClassifiedVariable:
    """Classify a single ``%%NAME|VALUE`` definition.

    Pure function of (name, value) — env-triplet confirmation needs job
    context and lives in :func:`classify_job_variables`.
    """
    raw_name = name or ""
    bare = _strip_prefix(raw_name.strip())
    val = value if value is None else str(value)

    is_valid_name = bool(bare) and VALID_NAME_RE.match(bare) is not None

    # feature extraction up front, on the value text
    text = val or ""
    dollar_tokens = DOLLAR_TOKEN_RE.findall(text)
    flow_refs = tuple(POOL_REF_RE.findall(text))
    scrubbed = POOL_REF_RE.sub(" ", DOLLAR_TOKEN_RE.sub(" ", text))
    global_refs = tuple(GLOBAL_REF_RE.findall(scrubbed))
    scrubbed = GLOBAL_REF_RE.sub(" ", scrubbed)
    plain_tokens = PLAIN_REF_RE.findall(scrubbed)
    has_adjacent = bool(ADJACENT_REF_RE.search(scrubbed))

    # route every token: system function / system variable / user reference.
    # Both %%TOKEN and century-format %%$TOKEN syntaxes carry system tokens.
    system_funcs = tuple(
        t for t in (*dollar_tokens, *plain_tokens) if _is_system_func(t)
    )
    system_vars = tuple(
        t for t in (*dollar_tokens, *plain_tokens)
        if _is_system_var(t) and not _is_system_func(t)
    )
    dollar_refs = tuple(
        t for t in dollar_tokens
        if not _is_system_func(t) and not _is_system_var(t)
    )
    plain_refs = tuple(
        t for t in plain_tokens
        if not _is_system_func(t) and not _is_system_var(t)
    )

    env_m = ENV_SUFFIX_RE.match(bare) if is_valid_name else None
    env_candidate = env_m.group("env") if env_m else None
    fact_base = env_m.group("base") if env_m else bare
    fact_type = (
        FACT_REGISTRY.get(bare) or FACT_REGISTRY.get(fact_base)
        if is_valid_name
        else None
    )

    ns = bare.split("-", 1)[0] if is_valid_name and "-" in bare else None

    any_user_refs = bool(plain_refs or dollar_refs)
    any_system_tokens = bool(system_funcs or system_vars)

    # G16 value contract: on a plain literal value, the VALUE decides the
    # artifact/launcher fact family — the name is only a suggestion. Applies
    # to any valid name, registered or not (a launcher-valued %%FOO is still
    # a launcher reference). A correction over an existing name-suggested
    # family is the name-value-mismatch WARN.
    fact_name_mismatch = False
    if (
        is_valid_name and text
        and not any_user_refs and not any_system_tokens
        and not flow_refs and not global_refs and not has_adjacent
    ):
        value_fact = _value_fact(text)
        if value_fact is not None and value_fact != fact_type:
            fact_name_mismatch = fact_type is not None
            fact_type = value_fact
    # alias-rename WARN: the name rolls up to a G16 canonical but is not the
    # canonical spelling itself (legacy stays materialized — non-destructive)
    canonical = CANONICAL_FACT_NAMES.get(fact_type or "")
    fact_alias_of = (
        canonical if canonical and bare != canonical and fact_base != canonical
        else None
    )
    # Dot-smuggling detector (metadata-plan Phase 2): a value that is wholly
    # punctuation — '.', '_', '-', '/' — is a literal delimiter parked in a
    # variable so it survives concatenation-delimiter stripping (e.g.
    # FILE_NM_SUFFIX='.'). Pattern-based by construction: it flags the
    # PRACTICE regardless of the variable name people gave it.
    stripped = text.strip()
    value_is_delimiter = bool(stripped) and not any(c.isalnum() for c in stripped)
    common = dict(
        raw_name=raw_name,
        raw_value=val,
        name=bare,
        plugin_namespace=ns,
        fact_type=fact_type,
        env_candidate=env_candidate,
        plain_refs=plain_refs,
        dollar_refs=dollar_refs,
        system_funcs=system_funcs,
        system_vars=system_vars,
        flow_refs=flow_refs,
        global_refs=global_refs,
        has_adjacent_refs=has_adjacent,
        value_is_delimiter=value_is_delimiter,
        fact_name_mismatch=fact_name_mismatch,
        fact_alias_of=fact_alias_of,
    )

    # precedence chain — see module docstring for the rationale
    if not is_valid_name:
        kind = VariableKind.MALFORMED
    elif bare in SHELL_VAR_NAMES:
        kind = VariableKind.EMBEDDED_SHELL
    elif ns is not None:
        kind = VariableKind.PLUGIN_NS
    elif flow_refs or global_refs:
        kind = VariableKind.FLOW_REF
    elif has_adjacent:
        kind = VariableKind.DYNAMIC_NAME
    elif fact_type is not None and not any_user_refs and not any_system_tokens:
        kind = VariableKind.SEMANTIC_FACT
    elif any_system_tokens and not any_user_refs:
        kind = VariableKind.SYSTEM_FUNC
    elif any_user_refs:
        kind = VariableKind.VAR_REF
    else:
        kind = VariableKind.LITERAL

    return ClassifiedVariable(kind=kind, **common)


def classify_job_variables(
    definitions: list[tuple[str, str | None]],
) -> list[ClassifiedVariable]:
    """Classify all definitions of one job and confirm env triplets.

    An ``_D`` / ``_Q`` / ``_P`` / ``_T`` suffix is only an environment tag
    when the job defines the same base name under at least two different
    suffix letters (FID_D + FID_Q + FID_P). A lone ``_D`` name is just a
    name — never tagged on suffix alone (guards against BUS_DT-style false
    positives, which the regex already excludes, and genuine one-off names
    like CURR_DATE_NEXT that it does not).
    """
    classified = [classify_variable(n, v) for n, v in definitions]

    by_base: dict[str, set[str]] = {}
    for cv in classified:
        if cv.env_candidate:
            base = cv.name[: -(len(cv.env_candidate) + 1)]
            by_base.setdefault(base, set()).add(cv.env_candidate)

    confirmed = {base for base, envs in by_base.items() if len(envs) >= 2}
    return [
        cv.with_env_tag(ENV_LETTER_MAP[cv.env_candidate])
        if cv.env_candidate
        and cv.name[: -(len(cv.env_candidate) + 1)] in confirmed
        else cv
        for cv in classified
    ]
