r"""Unit tests for the Phase-B variable resolver.

The multi-step scenarios are transcribed from real folders in the
production extract (controlm_variables__sample.csv): 183213/188252
(CDM bureau date chains), 155768 (SCRIPT_PATH env triplet), 159733
(FileWatch path composition), 161947 (R_PATH multi-site PRECMD).
"""
from __future__ import annotations

from drydocs.controlm.resolver import (
    MAX_DEPTH,
    ResolvedVariable,
    resolve_job,
    resolve_layers,
)


def _by_name(rvs: list[ResolvedVariable]) -> dict[str, ResolvedVariable]:
    """Last binding wins — mirrors sequential assignment."""
    return {rv.name: rv for rv in rvs}


# --- canonical system tokens ---------------------------------------------------

def test_system_var_canonicalizes() -> None:
    out = _by_name(resolve_job([], [("%%ODAT", "%%$ODATE")]))
    rv = out["ODAT"]
    assert rv.resolved_value == "{ODATE}"
    assert rv.is_fully_resolved
    assert rv.unresolved == ()


def test_calcdate_compacts_to_offset_token() -> None:
    # real: %%PREV_ODATE|%%$CALCDATE %%$ODATE -1   (folder 176690)
    out = _by_name(resolve_job([], [("%%PREV_ODATE", "%%$CALCDATE %%$ODATE -1")]))
    assert out["PREV_ODATE"].resolved_value == "{ODATE-1}"
    assert out["PREV_ODATE"].is_fully_resolved


def test_calcdate_chain_through_user_var() -> None:
    # real: folder 183213 — CURR_DATE feeds CURR_DATE_NEXT
    out = _by_name(resolve_job([], [
        ("%%CURR_DATE", "%%$ODATE"),
        ("%%CURR_DATE_NEXT", "%%$CALCDATE %%$CURR_DATE +8"),
    ]))
    assert out["CURR_DATE"].resolved_value == "{ODATE}"
    assert out["CURR_DATE_NEXT"].resolved_value == "{ODATE+8}"


def test_substr_stays_symbolic() -> None:
    # real: %%CURR_DAY_PREV|%%$SUBSTR %%$CURR_DATE_NEXT 7 2  (folder 183213)
    out = _by_name(resolve_job([], [
        ("%%CURR_DATE_NEXT", "%%$CALCDATE %%$ODATE +8"),
        ("%%CURR_DAY_PREV", "%%$SUBSTR %%$CURR_DATE_NEXT 7 2"),
    ]))
    assert out["CURR_DAY_PREV"].resolved_value == "{SUBSTR} {ODATE+8} 7 2"
    assert out["CURR_DAY_PREV"].is_fully_resolved  # symbolic residue is resolved


# --- sequential assignment semantics -------------------------------------------

def test_duplicate_definition_last_wins() -> None:
    # real: %%FileWatch-TIME_LIMIT defined 360 then 120 on one job (folder 185894)
    rvs = resolve_job([], [
        ("%%FileWatch-TIME_LIMIT", "360"),
        ("%%FileWatch-TIME_LIMIT", "120"),
        ("%%ECHO", "%%FileWatch-TIME_LIMIT"),
    ])
    assert [rv.resolved_value for rv in rvs] == ["360", "120", "120"]


def test_forward_reference_stays_unresolved() -> None:
    # a ref to a name defined LATER is not substituted at assignment time
    rvs = resolve_job([], [
        ("%%A", "%%B"),
        ("%%B", "hello"),
    ])
    assert rvs[0].resolved_value == "%%B"
    assert rvs[0].unresolved == ("B",)
    assert not rvs[0].is_fully_resolved


def test_self_reference_terminates() -> None:
    # real: %%MONTH_END_DATE|%%$MONTH_END_DATE  (folder 188252) — the name
    # is expected to arrive from upstream at runtime; must not loop
    rvs = resolve_job([], [
        ("%%MONTH_END_DATE", "%%$MONTH_END_DATE"),
        ("%%PRD", "%%$MONTH_END_DATE"),
    ])
    assert rvs[0].resolved_value == "%%$MONTH_END_DATE"
    assert rvs[0].unresolved == ("MONTH_END_DATE",)
    # the later consumer substitutes once, hits the self-referential stored
    # value, and stops — bounded well under MAX_DEPTH
    assert rvs[1].resolved_value == "%%$MONTH_END_DATE"
    assert rvs[1].resolution_depth < MAX_DEPTH


def test_folder_scope_inherited_and_job_overrides() -> None:
    # vendor priority: job-level overrides folder-level
    rvs = resolve_layers([
        ("FOLDER", [("%%DROPBOX", "/apps/dropbox"), ("%%EXT", "dat")]),
        ("JOB",    [("%%EXT", "ctl"), ("%%PATH", "%%DROPBOX/f.%%EXT")]),
    ])
    out = _by_name(rvs)
    assert out["PATH"].resolved_value == "/apps/dropbox/f.ctl"
    assert out["PATH"].scope == "JOB"


# --- longest-defined-name matching ---------------------------------------------

def test_longest_match_consumes_prefix_leaves_literal() -> None:
    # real: %%FileWatch-FILE_PATH|%%DROPBOX/%%FILE_NAME_PREFIX_%%FILE_NM_SUFFIX.%%FILE_EXT
    # (folder 185894): FILE_NAME_PREFIX is defined, FILE_NAME_PREFIX_ is not —
    # the binding consumes its prefix and the underscore stays literal.
    # The '.' between %%FILE_NM_SUFFIX and %%FILE_EXT is a concatenation
    # delimiter (consumed); the single dot in the result is FILE_EXT's value.
    out = _by_name(resolve_job(
        [("%%DROPBOX", "/d"), ("%%FILE_NAME_PREFIX", "CMS_IDW"),
         ("%%FILE_NM_SUFFIX", "????"), ("%%FILE_EXT", ".dat")],
        [("%%FileWatch-FILE_PATH",
          "%%DROPBOX/%%FILE_NAME_PREFIX_%%FILE_NM_SUFFIX.%%FILE_EXT")],
    ))
    assert out["FileWatch-FILE_PATH"].resolved_value == "/d/CMS_IDW_????.dat"
    assert out["FileWatch-FILE_PATH"].is_fully_resolved


def test_concat_delimiter_consumed_smuggled_dot_survives() -> None:
    # SME-confirmed (2026-06-11): %%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION
    # with FILE_NM_SUFFIX='.' and EXTENSION='dat' -> a clean filename. Every
    # '.' between %%refs is a consumed delimiter; the ONLY surviving dot is
    # the smuggled FILE_NM_SUFFIX value '.' (the legacy dot-smuggling pattern).
    out = _by_name(resolve_job(
        [("%%FILE_NM_PREFIX", "Originations_Daily_CRM_Indicator_"),
         ("%%BUS_DATE", "%%$ODATE"),
         ("%%FILE_NM_SUFFIX", "."),
         ("%%EXTENSION", "dat")],
        [("%%WATCH", "%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION")],
    ))
    assert out["WATCH"].resolved_value == "Originations_Daily_CRM_Indicator_{ODATE}.dat"
    assert out["WATCH"].is_fully_resolved


def test_period_after_literal_text_is_kept() -> None:
    # a '.' that does NOT terminate a variable name stays literal:
    # in 'f.%%EXT' the dot follows literal 'f', not a %%ref
    out = _by_name(resolve_job(
        [("%%EXT", "ctl")],
        [("%%PATH", "%%nodir/f.%%EXT")],
    ))
    assert out["PATH"].resolved_value == "%%nodir/f.ctl"


def test_defined_name_beats_shorter_system_token_on_tie() -> None:
    # a user-defined ODATE overrides the system variable (vendor: allowed
    # unless admin-locked)
    out = _by_name(resolve_job([("%%ODATE", "20260611")],
                               [("%%X", "%%ODATE")]))
    assert out["X"].resolved_value == "20260611"


def test_system_token_beats_shorter_user_binding() -> None:
    # ODAT defined, text says %%ODATE: the longer system token wins
    out = _by_name(resolve_job([("%%ODAT", "x")], [("%%Y", "%%ODATE")]))
    assert out["Y"].resolved_value == "{ODATE}"


def test_multi_site_same_name_one_value() -> None:
    # real: %%PRECMD|mkdir -p %%R_PATH/VPC_P_VMSTR_BAL_%%$ODATE/%%R_PATH/backup
    # (folder 161947) — same name substitutes at every site
    out = _by_name(resolve_job(
        [("%%R_PATH", "/apps/serial")],
        [("%%PRECMD", "mkdir -p %%R_PATH/VPC_P_VMSTR_BAL_%%$ODATE/%%R_PATH/backup;")],
    ))
    assert out["PRECMD"].resolved_value == (
        "mkdir -p /apps/serial/VPC_P_VMSTR_BAL_{ODATE}//apps/serial/backup;"
    )


# --- externals (global / pool scope) --------------------------------------------

def test_pool_refs_kept_verbatim_and_reported() -> None:
    # real: %%PROID|%%\\SCRA_REPORTING\\PROID  (folder 185894)
    out = _by_name(resolve_job([], [("%%PROID", r"%%\\SCRA_REPORTING\\PROID")]))
    rv = out["PROID"]
    assert rv.resolved_value == r"%%\\SCRA_REPORTING\\PROID"
    assert rv.external_refs == (r"%%\\SCRA_REPORTING\\PROID",)
    assert not rv.is_fully_resolved
    assert rv.unresolved == ()  # external, not a user-resolution failure


# --- environment-triplet variant expansion --------------------------------------

def test_env_variant_expansion_script_path() -> None:
    # real: folder 155768 — %%SCRIPT_PATH|%%SCRIPT_PATH_%%HOSTNM where
    # HOSTNM is runtime-derived ({SUBSTR} of DATACENTER); the offline answer
    # is one resolved value per environment
    rvs = resolve_job(
        [("%%SCRIPT_PATH_D", "/apps/dev"),
         ("%%SCRIPT_PATH_Q", "/apps/qa"),
         ("%%SCRIPT_PATH_P", "/apps/prod")],
        [("%%SCRIPT_PATH", "%%SCRIPT_PATH_%%HOSTNM")],
    )
    rv = _by_name(rvs)["SCRIPT_PATH"]
    assert not rv.is_fully_resolved
    variants = dict(rv.variants)
    assert variants["Development"] == "/apps/dev"
    assert variants["QA"] == "/apps/qa"
    assert variants["Production"] == "/apps/prod"


def test_env_variant_expansion_tenv_composition() -> None:
    # real: folder 183213 — %%TENV|%%TENV%%CURRENVIRON with TENV_D/_T/_P
    # defined; the runtime selector contributes the _<letter> suffix
    rvs = resolve_job(
        [("%%TENV_D", "_Dsdv"), ("%%TENV_T", "_Qsdv"), ("%%TENV_P", "_Psdv")],
        [("%%TENV", "%%TENV%%CURRENVIRON")],
    )
    rv = _by_name(rvs)["TENV"]
    variants = dict(rv.variants)
    assert variants["Development"] == "_Dsdv"
    assert variants["Production"] == "_Psdv"


def test_no_variants_without_triplet_siblings() -> None:
    out = _by_name(resolve_job([], [("%%X", "%%UNKNOWN_NAME")]))
    assert out["X"].variants == ()
    assert out["X"].unresolved == ("UNKNOWN_NAME",)


# --- real chain end-to-end -------------------------------------------------------

def test_folder_188252_bureau_chain() -> None:
    # transcribed from folder 188252: the folder header defines the date
    # chain; job 2's POSTCMD consumes %%$PRD_END_DATE_1. MONTH_END_DATE is
    # runtime-provided (self-referential placeholder), so the chain resolves
    # symbolically around it and reports it unresolved.
    folder_defs = [
        ("%%R_DAY_OF_MTH_END", "%%$SUBSTR %%$MONTH_END_DATE 7 2"),
        ("%%PREV_MONTH_END_DT", "%%$CALCDATE %%$MONTH_END_DATE -%%$R_DAY_OF_MTH_END"),
        ("%%PRD_END_DATE_1", "%%$PREV_MONTH_END_DT"),
        ("%%MONTH_END_DATE", "%%$MONTH_END_DATE"),
    ]
    job_defs = [
        ("%%POSTCMD",
         "sh run_calp_temp.sh bureau.m %%$PRD_END_DATE_1,2,Y,NO"),
    ]
    rvs = resolve_job(folder_defs, job_defs)
    out = _by_name(rvs)
    post = out["POSTCMD"]
    # PRD_END_DATE_1 chain substituted; MONTH_END_DATE remains the marker
    assert "PRD_END_DATE_1" not in post.resolved_value
    assert "MONTH_END_DATE" in post.resolved_value
    assert "MONTH_END_DATE" in post.unresolved
    assert post.resolution_depth <= MAX_DEPTH
