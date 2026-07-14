"""N2 — column-ledger drift guards (doc 08 Phase 1).

Four guards over the ``config/source-mappings/`` ledger, its loaders, and the
source registry:

1. **SQL drift guard** — every loader SQL's ``EXPR AS alias`` SELECT list is
   parsed with a STRICT regex (house style is a flat, one-per-line list; the
   parser FAILS on any line it cannot read — that failure is the signal to
   upgrade to sqlglot, per doc 08). Per ledger object, the UNION of source
   columns referenced across all loader SQLs must set-equal the ledger's
   ``projected`` columns. Catches both drift directions.
   (``controlm_dependencies_recursive.sql`` is excluded by design: a derived
   recursive-CTE projection, not a source-column extract.)
2. **Coverage / census reconciliation** — ``census_failures()``: while every
   census is ``pending`` there is nothing to reconcile (asserted); once a
   census records ``column_count``, explicit rows + the sweep's frozen
   ``count:`` must balance exactly, so new columns since the census must be
   dispositioned BY NAME, never swept (synthetic cases pin the mechanics).
3. **Registry integration** — every ``confirmed: true`` source either carries a
   ``locator.mapping`` pointer to an existing ledger, or is on the explicit
   LEDGER_PENDING list (the four legacy confirmed sources predating doc 08 —
   shrink-only; a NEW confirmed source without a ledger fails).
4. **Lineage extractor CSV contract** (the G9 tech-debt finding #2, merged
   here): the extractor's ``CSV_CONTRACT`` must match the ``row.get()`` keys in
   its code AND remain a subset of ``controlm_jobs.sql``'s alias list — a
   renamed alias fails here instead of silently dropping a column.
"""
from __future__ import annotations

import ast
import re
from pathlib import Path

import pytest
import yaml

from drydocs.source_mappings import SourceMapping
from drydocs_lineage.extractors.controlm_inventory import CSV_CONTRACT

REPO_ROOT = Path(__file__).resolve().parents[2]
SQL_DIR = REPO_ROOT / "drydocs" / "loaders" / "sql"
REGISTRY = REPO_ROOT / "config" / "source-registry.yaml"

# loader SQL -> {table alias -> ledger object}. controlm_folders.sql's H is the
# CM_DEF_VJOB folder HEADER ROW join (gate controlm-q1q3-phase1 §Q3); the ledger
# carries APPLICATION under CM_DEF_VJOB for that reason.
SQL_OBJECT_ALIASES: dict[str, dict[str, str]] = {
    "controlm_folders.sql": {"T": "CM_DEF_VTAB", "H": "CM_DEF_VJOB"},
    "controlm_jobs.sql": {"J": "CM_DEF_VJOB"},
    "controlm_conditions_in.sql": {"L": "CM_DEF_LNKI_P_VW"},
    "controlm_conditions_out.sql": {"L": "CM_DEF_LNKO_P_VW"},
    "controlm_variables.sql": {
        "V": "CM_DEF_SETVAR_VW", "T": "CM_DEF_VTAB", "J": "CM_DEF_VJOB",
    },
    "controlm_hosts.sql": {"H": "CM_HOSTS"},
    "controlm_avg_run.sql": {"A": "CM_AVG_RUN"},
}

# strict, house-style source item: QUAL.SOURCE_COLUMN AS alias
_SOURCE_ITEM_RE = re.compile(
    r"^(?P<qual>[A-Za-z]\w*)\.(?P<col>[A-Za-z]\w*_?)\s+AS\s+(?P<alias>\w+)$"
)
# a derived item is anything else that still ends `AS alias` (e.g. the
# var_scope CASE in controlm_variables.sql). Its INTERNAL column references are
# out of V1 scope — same deferral as WHERE parsing (doc 08: sqlglot when needed).
_DERIVED_ITEM_RE = re.compile(r"\sAS\s+(?P<alias>\w+)$", re.IGNORECASE)


def _select_block(sql_text: str) -> str:
    """The first top-level SELECT ... FROM block, comments stripped, one string."""
    lines = sql_text.splitlines()
    start = next(
        i for i, ln in enumerate(lines) if ln.strip().upper().startswith("SELECT")
    )
    block: list[str] = []
    for ln in lines[start + 1:]:
        if ln.strip().upper().startswith("FROM"):
            return " ".join(block)
        block.append(ln.split("--", 1)[0].strip())
    raise AssertionError("SELECT block has no FROM — not the flat house style")


def _split_items(block: str) -> list[str]:
    """Split the SELECT list on top-level commas (paren-aware)."""
    items, depth, current = [], 0, []
    for ch in block:
        if ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
        if ch == "," and depth == 0:
            items.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
    tail = "".join(current).strip()
    if tail:
        items.append(tail)
    return [re.sub(r"\s+", " ", i) for i in items if i]


def _parse_projection(sql_file: str) -> tuple[list[tuple[str, str, str]], list[str]]:
    """(source triples, derived aliases). STRICT: an item that is neither a
    clean ``QUAL.COL AS alias`` nor ``<expr> AS alias`` fails — that failure is
    the signal to upgrade this guard to sqlglot (doc 08)."""
    text = (SQL_DIR / sql_file).read_text(encoding="utf-8")
    triples: list[tuple[str, str, str]] = []
    derived: list[str] = []
    for item in _split_items(_select_block(text)):
        m = _SOURCE_ITEM_RE.match(item)
        if m:
            triples.append(
                (m.group("qual").upper(), m.group("col").upper(), m.group("alias"))
            )
            continue
        d = _DERIVED_ITEM_RE.search(item)
        assert d, (
            f"{sql_file}: SELECT item does not parse with the strict grammar — "
            f"either fix the SQL to house style or upgrade this guard to sqlglot "
            f"(doc 08): {item!r}"
        )
        derived.append(d.group("alias"))
    assert triples, f"{sql_file}: empty projection?"
    return triples, derived


@pytest.fixture(scope="module")
def ledger() -> SourceMapping:
    return SourceMapping.load_source("controlm-psgmgr")


# --- 1. SQL drift guard --------------------------------------------------------

def test_loader_projections_set_equal_the_ledger(ledger: SourceMapping) -> None:
    referenced: dict[str, set[str]] = {}
    for sql_file, alias_map in SQL_OBJECT_ALIASES.items():
        triples, _derived = _parse_projection(sql_file)
        for qual, col, _alias in triples:
            assert qual in alias_map, (
                f"{sql_file}: table alias {qual!r} not mapped to a ledger object — "
                "extend SQL_OBJECT_ALIASES"
            )
            referenced.setdefault(alias_map[qual], set()).add(col)

    problems: list[str] = []
    for oname, sql_cols in sorted(referenced.items()):
        projected = set(ledger.projected(oname))
        missing_in_sql = projected - sql_cols
        missing_in_ledger = sql_cols - projected
        if missing_in_sql:
            problems.append(
                f"{oname}: ledger projects {sorted(missing_in_sql)} but no loader SQL selects them"
            )
        if missing_in_ledger:
            problems.append(
                f"{oname}: SQL selects {sorted(missing_in_ledger)} not dispositioned `projected` in the ledger"
            )
    # every ledger object is exercised by at least one loader SQL
    unexercised = set(ledger.objects()) - set(referenced)
    if unexercised:
        problems.append(f"ledger objects no loader SQL references: {sorted(unexercised)}")
    assert not problems, "\n".join(problems)


def test_strict_parser_grammar() -> None:
    assert _SOURCE_ITEM_RE.match("T.TABLE_ID AS folder_id")
    assert _SOURCE_ITEM_RE.match("L.ORDER_ AS order_")
    # expressions classify as DERIVED (alias recorded, internals out of V1 scope)
    assert not _SOURCE_ITEM_RE.match("CASE WHEN a THEN b END AS c")
    assert _DERIVED_ITEM_RE.search("CASE WHEN a THEN b END AS c")
    # an item with no alias at all fails the grammar entirely
    assert not _SOURCE_ITEM_RE.match("T.TABLE_ID") and not _DERIVED_ITEM_RE.search("T.TABLE_ID")
    # paren-aware splitting keeps function args together
    assert _split_items("NVL(a, b) AS x, T.C AS c") == ["NVL(a, b) AS x", "T.C AS c"]


# --- 2. coverage / census reconciliation ----------------------------------------

def test_committed_ledger_census_is_pending_and_reconciles(ledger: SourceMapping) -> None:
    # Phase 0 state: every census pending -> nothing to reconcile, by design
    assert ledger.census_failures() == []


def _obj(column_count, swept_count, explicit=2):
    doc = {
        "schema": "drydocs.source-mapping.v1",
        "source": "s", "classification": "Internal-Public",
        "objects": [{
            "name": "O", "kind": "table",
            "profile": {"profiled_on": "2026-07-11", "via": "unit", "column_count": column_count,
                        "census": "recorded" if column_count else "pending"},
            "columns": [
                {"name": f"C{i}", "disposition": "projected", "target": f"X.c{i}"}
                for i in range(explicit)
            ],
            "default_disposition": {
                "disposition": "excluded", "reason": "scope",
                **({"count": swept_count} if swept_count is not None else {}),
            },
        }],
    }
    return SourceMapping.from_dict(doc)


def test_census_reconciles_when_counts_balance() -> None:
    assert _obj(column_count=10, swept_count=8).census_failures() == []


def test_new_columns_since_census_must_be_dispositioned_by_name() -> None:
    # census grew 10 -> 12; the frozen sweep may NOT absorb the two new columns
    failures = _obj(column_count=12, swept_count=8).census_failures()
    assert len(failures) == 1
    assert "BY NAME" in failures[0] and "12" in failures[0]


def test_census_with_uncounted_sweep_fails() -> None:
    failures = _obj(column_count=10, swept_count=None).census_failures()
    assert len(failures) == 1
    assert "count:" in failures[0]


# --- 3. registry integration -----------------------------------------------------

# Confirmed sources that predate doc 08 and have no ledger YET — shrink-only.
# A NEW confirmed source must ship its ledger (or extend this list through a
# deliberate commit, which is the point: visible, named debt).
# airflow-mwaa (2026-07-14, gate airflow-crosswalk): crosswalk-only activation —
# no live export exists, so there are no columns to ledger; the ledger ships
# with the future loader gate.
LEDGER_PENDING = frozenset({"seal-extract", "catalog-pat", "software-registry", "bmc-docs", "airflow-mwaa"})


def test_every_confirmed_source_has_a_ledger_or_is_named_pending() -> None:
    registry = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    problems: list[str] = []
    seen_pending: set[str] = set()
    for entry in registry.get("sources", []):
        sid = entry.get("id")
        if not entry.get("confirmed"):
            continue
        mapping = (entry.get("locator") or {}).get("mapping")
        if mapping:
            path = REPO_ROOT / mapping
            if not path.exists():
                problems.append(f"{sid}: mapping pointer {mapping} does not exist")
            elif SourceMapping.load(path).source != sid:
                problems.append(f"{sid}: ledger at {mapping} declares a different source id")
        elif sid in LEDGER_PENDING:
            seen_pending.add(sid)
        else:
            problems.append(
                f"{sid}: confirmed source with no locator.mapping ledger pointer "
                "(doc 08 Phase 1) and not on the frozen LEDGER_PENDING list"
            )
    # shrink-only: a pending source that gained a ledger must leave the list
    stale = LEDGER_PENDING - seen_pending
    if stale:
        problems.append(f"LEDGER_PENDING entries no longer pending (remove them): {sorted(stale)}")
    assert not problems, "\n".join(problems)


# --- 4. lineage extractor CSV contract (G9 finding #2, merged into N2) -----------

def test_extractor_csv_contract_matches_its_code() -> None:
    src = (REPO_ROOT / "drydocs_lineage" / "extractors" / "controlm_inventory.py").read_text(
        encoding="utf-8"
    )
    tree = ast.parse(src)
    used: set[str] = set()
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Attribute)
            and node.func.attr == "get"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "row"
            and node.args
            and isinstance(node.args[0], ast.Constant)
        ):
            used.add(node.args[0].value)
    assert used == set(CSV_CONTRACT), (
        f"CSV_CONTRACT drifted from the code: contract-only={sorted(set(CSV_CONTRACT) - used)}, "
        f"code-only={sorted(used - set(CSV_CONTRACT))}"
    )


def test_extractor_csv_contract_matches_the_jobs_sql_aliases() -> None:
    triples, derived = _parse_projection("controlm_jobs.sql")
    aliases = {alias for _q, _c, alias in triples} | set(derived)
    missing = set(CSV_CONTRACT) - aliases
    assert not missing, (
        f"controlm_jobs.sql no longer aliases {sorted(missing)} — the lineage "
        "extractor would silently drop these columns (G9 tech-debt finding #2)"
    )
