r"""Control-M variable resolver (C3/C4 normalization, Phase B).

Reproduces AutoEdit substitution offline — the vendor's "Variable
Simulation" — against the definition extract, without executing jobs.

Semantics (external/orchestration/bmc-controlm/controlm-variables.md + observed 9.0.x behavior):

  Sequential assignment.  A job's variable definitions are an ORDERED list
      of assignments, not a set: each value is resolved against the
      environment built so far, then bound (rebinding overwrites — which is
      why duplicate names per job are legitimate). Scope layers apply in
      vendor priority order: folder first, then sub-folder, then job, so
      later layers override earlier ones (job > folder > global).

  Longest-defined-name matching.  At each ``%%`` site the resolver matches
      the LONGEST variable name *defined in scope* — not a regex word
      boundary. ``%%FILE_NAME_PREFIX_%%FILE_NM_SUFFIX`` binds
      FILE_NAME_PREFIX (defined) and leaves the literal ``_``, even though
      ``FILE_NAME_PREFIX_`` is the maximal word token.

  Concatenation delimiter.  A period directly between a variable reference
      and a following ``%%`` reference (``%%A.%%B``) is Control-M's
      concatenation *delimiter* — it terminates the name and is CONSUMED,
      not emitted. Literal dots in a composed value therefore come from
      variable *values*, not the template: the smuggled-dot pattern
      ``%%PREFIX.%%DATE.%%SUFFIX.%%EXT`` with ``SUFFIX='.'`` resolves to
      ``<prefix><date>.<ext>`` — the only surviving dot is SUFFIX's value.
      (SME-confirmed against production, 2026-06-11.) A period after literal
      text (``f.%%EXT``) is kept — it never terminated a variable name.
      Note: the ``..`` literal-period escape is not handled here (this shop
      smuggles dots via values, not ``..``); flagged in the metadata plan.

  Canonical tokens, not values.  System variables resolve at execution
      time, so they canonicalize to symbolic tokens: ``%%$ODATE`` ->
      ``{ODATE}``, ``%%ORDERID`` -> ``{ORDERID}``. Date arithmetic
      compacts: ``%%$CALCDATE %%$ODATE -1`` -> ``{ODATE-1}``. Global /
      pool references (``%%\VAR``, ``%%\\POOL\VAR``) are external state —
      kept verbatim and reported, never inlined.

  Unresolved stays visible.  A user reference with no binding in scope is
      left as literal ``%%NAME`` text and reported. Invariant: a resolved
      value containing no ``%%`` is fully resolved (canonical ``{...}``
      tokens are expected residue, not failures).

  Termination.  Per-value fixed-point iteration is capped at
      MAX_DEPTH (10, matching the recursive-SQL guard) with a seen-set so
      a name is substituted at most once per value (kills self-reference
      loops like ``%%MONTH_END_DATE|%%$MONTH_END_DATE``).

  Environment variants.  When an unresolved name has ``_D/_Q/_P/_T``
      siblings defined in scope (the env-triplet convention), the value is
      re-resolved once per environment letter and emitted as variants —
      the offline answer to runtime selectors like
      ``%%SCRIPT_PATH_%%HOSTNM``.
"""
from __future__ import annotations

import re
from collections.abc import Iterable, Sequence
from dataclasses import dataclass

from .variables import ENV_LETTER_MAP, _is_system_func, _is_system_var

MAX_DEPTH = 10

_WORD_RE = re.compile(r"[A-Za-z0-9_]+")
_EXTERNAL_RE = re.compile(r"%%\\+\w+(?:\\+\w+)?")
_RESIDUAL_REF_RE = re.compile(r"%%\$?([A-Za-z_][A-Za-z0-9_]*)")
# {CALCDATE} {X} -1  ->  {X-1}     (compact date arithmetic; other function
# markers keep their args inline as symbolic residue, e.g. {SUBSTR} {X} 7 2)
_CALCDATE_COMPACT_RE = re.compile(r"\{CALCDATE\}\s+\{(\w+)\}\s+([+-]\d+)")
# canonical runtime-token residue in resolved text ({ODATE}, {ODATE-1}, …) —
# expected symbolic output, never a resolution failure
_CANONICAL_TOKEN_RE = re.compile(r"\{([A-Za-z0-9_$+\-]+)\}")


@dataclass(frozen=True)
class ResolvedVariable:
    """One definition after resolution. Maps 1:1 onto STG_VARIABLE's
    resolved columns."""

    name: str
    scope: str                                  # FOLDER | SUBFOLDER | JOB
    src_ordinal: int                            # definition order within scope chain
    raw_value: str | None
    resolved_value: str
    is_fully_resolved: bool                     # no %% left in resolved_value
    resolution_depth: int                       # substitution iterations used
    unresolved: tuple[str, ...]                 # user names left unresolved
    external_refs: tuple[str, ...]              # %%\global / %%\\pool\var kept verbatim
    variants: tuple[tuple[str, str], ...] = ()  # (environment, resolved) expansions


class _Env:
    """Mutable binding environment with longest-defined-name lookup."""

    def __init__(self) -> None:
        self._bindings: dict[str, str] = {}

    def bind(self, name: str, value: str) -> None:
        self._bindings[name] = value

    def clone(self) -> _Env:
        other = _Env()
        other._bindings = dict(self._bindings)
        return other

    def __contains__(self, name: str) -> bool:
        return name in self._bindings

    def __getitem__(self, name: str) -> str:
        return self._bindings[name]

    def longest_match(self, text: str, pos: int, blocked: set[str]) -> str | None:
        """Longest non-blocked defined name that ``text`` starts with at ``pos``."""
        best: str | None = None
        for name in self._bindings:
            if name in blocked:
                continue
            if text.startswith(name, pos) and (best is None or len(name) > len(best)):
                best = name
        return best

    def env_letters_for(self, name: str) -> list[str]:
        """Env-triplet letters L for which ``name_L`` or ``nameL`` is bound
        (``nameL`` covers stuck composition prefixes ending in ``_``)."""
        return [
            letter
            for letter in ("D", "Q", "P", "T")
            if f"{name}_{letter}" in self._bindings
            or f"{name}{letter}" in self._bindings
        ]

    def env_sibling(self, name: str, letter: str) -> str | None:
        for candidate in (f"{name}_{letter}", f"{name}{letter}"):
            if candidate in self._bindings:
                return self._bindings[candidate]
        return None


def _consume_delimiter(text: str, i: int) -> int:
    """Skip a concatenation-delimiter period at ``i``.

    Called immediately after a variable substitution: a single ``.`` that
    sits between the just-substituted variable and a following ``%%``
    reference is Control-M's name terminator — consumed, not emitted. A
    period followed by anything other than ``%%`` is left for the normal
    literal path (so ``%%VAR.txt`` keeps its dot; only ``%%A.%%B`` drops it).
    """
    return i + 1 if text.startswith(".%%", i) else i


def _substitute_once(
    text: str, env: _Env, blocked: set[str]
) -> tuple[str, bool, set[str]]:
    """One left-to-right substitution pass.

    A name may substitute at MANY sites within one pass (real values
    reference the same variable repeatedly); ``blocked`` prevents a name
    from substituting again in a LATER pass, which is what kills
    self-reference loops (%%MONTH_END_DATE bound to '%%$MONTH_END_DATE').
    Returns (new_text, changed, names substituted this pass).
    """
    out: list[str] = []
    i = 0
    changed = False
    pass_seen: set[str] = set()
    n = len(text)
    while i < n:
        if not text.startswith("%%", i):
            out.append(text[i])
            i += 1
            continue
        j = i + 2
        # %%\... global / pool reference: external state, copy verbatim
        if j < n and text[j] == "\\":
            m = _EXTERNAL_RE.match(text, i)
            out.append(m.group(0) if m else text[i:j + 1])
            i = m.end() if m else j + 1
            continue
        # century-format %%$TOKEN shares the user namespace after the $
        if j < n and text[j] == "$":
            j += 1
        word_m = _WORD_RE.match(text, j)
        if word_m is None:
            out.append(text[i:j])
            i = j
            continue
        word = word_m.group(0)
        is_system = _is_system_func(word) or _is_system_var(word)
        user_name = env.longest_match(text, j, blocked)
        # AutoEdit consults the defined-variable catalog first: a binding
        # wins unless the system token is strictly longer (%%ODATE beats a
        # defined ODAT). A binding shorter than the word token consumes its
        # prefix and leaves the rest literal (FILE_NAME_PREFIX_ case) —
        # but only when the word is not itself a system token.
        if user_name is not None and (
            len(user_name) >= len(word) or not is_system
        ):
            out.append(env[user_name])
            pass_seen.add(user_name)
            i = _consume_delimiter(text, j + len(user_name))
            changed = True
        elif is_system:
            out.append("{" + word.upper() + "}")
            i = _consume_delimiter(text, j + len(word))
            changed = True
        else:
            # no binding: keep the %%NAME text visible and move past it
            out.append(text[i:j + len(word)])
            i = j + len(word)
    return "".join(out), changed, pass_seen


def _canonicalize(text: str) -> str:
    """Compact function markers: {CALCDATE} {ODATE} -1 -> {ODATE-1};
    other function markers keep their args inline as symbolic residue."""
    prev = None
    while prev != text:
        prev = text
        text = _CALCDATE_COMPACT_RE.sub(lambda m: "{" + m.group(1) + m.group(2) + "}", text)
    return text


def _resolve_value(raw: str, env: _Env) -> tuple[str, int]:
    """Fixed-point substitution of one value.

    Returns (resolved, depth) where depth is the number of passes that
    changed the text (0 = the value needed no substitution at all).
    """
    resolved, depth, _ = _resolve_value_traced(raw, env)
    return resolved, depth


def _resolve_value_traced(raw: str, env: _Env) -> tuple[str, int, set[str]]:
    """:func:`_resolve_value` plus the set of user names substituted —
    the provenance :func:`resolve_command_line` reports."""
    text = raw
    blocked: set[str] = set()
    depth = 0
    while True:
        new_text, changed, pass_seen = _substitute_once(text, env, blocked)
        text = new_text
        if not changed:
            break
        blocked |= pass_seen
        depth += 1
        if depth >= MAX_DEPTH:
            break
    return _canonicalize(text), depth, blocked


def _residuals(text: str) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(unresolved user names, external %%\\ refs) left in resolved text."""
    externals = tuple(_EXTERNAL_RE.findall(text))
    scrubbed = _EXTERNAL_RE.sub(" ", text)
    unresolved = tuple(dict.fromkeys(_RESIDUAL_REF_RE.findall(scrubbed)))
    return unresolved, externals


def _strip_prefix(name: str) -> str:
    return name[2:] if name.startswith("%%") else name


def _expand_env_variants(
    raw_value: str, env: _Env, unresolved: tuple[str, ...]
) -> tuple[tuple[str, str], ...]:
    """Per-environment expansion of runtime name composition.

    Handles ``%%PREFIX_%%SELECTOR`` (SCRIPT_PATH_ + HOSTNM -> SCRIPT_PATH_P)
    and ``%%PREFIX%%SELECTOR`` (TENV + CURRENVIRON -> TENV_P): when a stuck
    name has _D/_Q/_P/_T triplet siblings in scope, bind the ADJACENT
    selector reference to each environment letter and re-resolve — the
    normal longest-match substitution then composes the sibling name. A
    variant is only emitted when the stuck name actually disappears.
    """
    for stuck in unresolved:
        letters = env.env_letters_for(stuck)
        if len(letters) < 2:
            continue
        # selector = the unresolved ref immediately following the stuck
        # prefix in the raw text (%%STUCK%%SELECTOR / %%STUCK%%$SELECTOR)
        selectors = [
            u for u in unresolved
            if u != stuck
            and (f"{stuck}%%{u}" in raw_value or f"{stuck}%%${u}" in raw_value)
        ]
        if not selectors:
            continue
        variants: list[tuple[str, str]] = []
        for letter in letters:
            for sel_value in (letter, f"_{letter}"):
                overlay = env.clone()
                for sel in selectors:
                    overlay.bind(sel, sel_value)
                v_resolved, _ = _resolve_value(raw_value, overlay)
                v_unresolved, _ext = _residuals(v_resolved)
                # accept only when the composition actually bound: no
                # residual may still start with the stuck name (TENV + 'D'
                # leaves %%TENVD — that is a failed composition, not success)
                if not any(u.startswith(stuck) for u in v_unresolved):
                    variants.append((ENV_LETTER_MAP[letter], v_resolved))
                    break
        if variants:
            return tuple(variants)
    return ()


def resolve_layers(
    layers: Sequence[tuple[str, Iterable[tuple[str, str | None]]]],
) -> list[ResolvedVariable]:
    """Resolve an ordered scope chain.

    ``layers`` is vendor priority order, outermost first:
    ``[("FOLDER", folder_defs), ("SUBFOLDER", ...), ("JOB", job_defs)]``.
    Each defs iterable is the ORDERED (name, value) list for that scope.
    Returns one ResolvedVariable per input definition, in processing order.
    """
    results, _env, _scopes = _resolve_scope_chain(layers)
    return results


def _resolve_scope_chain(
    layers: Sequence[tuple[str, Iterable[tuple[str, str | None]]]],
) -> tuple[list[ResolvedVariable], _Env, dict[str, str]]:
    """The one scope-chain walk (guardrail: never a second engine) —
    :func:`resolve_layers` and :func:`resolve_command_line` both run through
    here. Also returns the final environment and each bound name's LAST
    binding scope (rebinding overwrites, so job > subfolder > folder)."""
    env = _Env()
    results: list[ResolvedVariable] = []
    scope_by_name: dict[str, str] = {}
    ordinal = 0
    for scope, defs in layers:
        for raw_name, raw_value in defs:
            ordinal += 1
            name = _strip_prefix((raw_name or "").strip())
            value = "" if raw_value is None else str(raw_value)
            resolved, depth = _resolve_value(value, env)
            unresolved, externals = _residuals(resolved)

            variants = _expand_env_variants(value, env, unresolved)

            rv = ResolvedVariable(
                name=name,
                scope=scope,
                src_ordinal=ordinal,
                raw_value=raw_value,
                resolved_value=resolved,
                is_fully_resolved="%%" not in resolved,
                resolution_depth=depth,
                unresolved=unresolved,
                external_refs=externals,
                variants=tuple(variants),
            )
            results.append(rv)
            if name:
                env.bind(name, resolved)
                scope_by_name[name] = scope
    return results, env, scope_by_name


@dataclass(frozen=True)
class ResolvedCommandLine:
    """One CMD_LINE resolved against a job's variable scope chain (G46).

    A DERIVED fact beside the verbatim command, never a replacement: ``raw``
    travels unchanged, and the provenance says exactly what happened —
    which names substituted (with the scope that bound them), what stayed
    unresolved, and which canonical runtime tokens are EXPECTED residue
    (``{ODATE}``-class values only exist at execution time; their presence
    is not a failure)."""

    raw: str
    resolved: str
    is_fully_resolved: bool                      # no %% left in resolved
    resolution_depth: int
    substituted: tuple[tuple[str, str], ...]     # (name, binding scope), name-sorted
    unresolved: tuple[str, ...]                  # user refs with no binding — visible, reported
    external_refs: tuple[str, ...]               # %%\global / %%\\pool\var kept verbatim
    canonical_tokens: tuple[str, ...]            # {ODATE}-class residue, first-seen order
    variants: tuple[tuple[str, str], ...] = ()   # (environment, resolved) expansions


def resolve_command_line(
    layers: Sequence[tuple[str, Iterable[tuple[str, str | None]]]],
    cmd_line: str,
) -> ResolvedCommandLine:
    """Resolve a verbatim CMD_LINE against its variable scope chain.

    ``layers`` is the same vendor-priority chain :func:`resolve_layers`
    takes (outermost first: folder, sub-folder, job). The environment is
    built by the SAME sequential-assignment walk and the command text goes
    through the SAME fixed-point substitution pass — this module is the one
    resolver both ingestion paths (Oracle staging, XML export) call; no
    caller may re-implement substitution.

    The scope attributed to each substituted name is its LAST binding scope
    (job overrides folder — vendor priority order), which is the binding
    that actually produced the substituted value.
    """
    _results, env, scope_by_name = _resolve_scope_chain(layers)
    resolved, depth, substituted = _resolve_value_traced(cmd_line, env)
    unresolved, externals = _residuals(resolved)
    variants = _expand_env_variants(cmd_line, env, unresolved)
    tokens = tuple(dict.fromkeys(_CANONICAL_TOKEN_RE.findall(resolved)))
    return ResolvedCommandLine(
        raw=cmd_line,
        resolved=resolved,
        is_fully_resolved="%%" not in resolved,
        resolution_depth=depth,
        substituted=tuple(sorted(
            (name, scope_by_name.get(name, "")) for name in substituted)),
        unresolved=unresolved,
        external_refs=externals,
        canonical_tokens=tokens,
        variants=tuple(variants),
    )


def resolve_job(
    folder_defs: Iterable[tuple[str, str | None]],
    job_defs: Iterable[tuple[str, str | None]],
) -> list[ResolvedVariable]:
    """Resolve one job's definitions under its folder scope (the common
    two-layer case; use resolve_layers directly when sub-folders exist)."""
    return resolve_layers([("FOLDER", folder_defs), ("JOB", job_defs)])
