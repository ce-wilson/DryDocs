"""SEAL attribution rows (backlog K2/K8, gates seal-attribution-match-policy
and seal-app-ref-edge-reshape).

Four contracts:

- :class:`StgAppFactRow` — one DRYDOCS_STG.STG_APP_FACT row (semantic facts
  mined from Control-M variables by the C3/C4 normalization stream). The
  attribution resolver's *input*; validated inside the adapter before the
  match policy runs.
- :class:`SealAttributionRow` — one resolved K2 job-grain *decision*. Since
  the K7 close-out (2026-08-03) this is an INTERNAL shape only: the K2 match
  policy DEMOTES to the fallback tier feeding the folder-grain resolver
  (§B3) and no per-job application edge is authored (§A1).
- :class:`FolderAttributionRow` — one folder-grain attribution, the shape
  ``folder_attribution.cypher`` consumes (K8): ControlMFolder
  -[BELONGS_TO_APPLICATION {role: seal_app_ref}]-> Port, carrying the §B3
  origin flag so fallback-derived values are disclosed, never presented as
  defined.
- :class:`ManualMappingRow` — one SME-authored manual mapping CSV row
  (config/manual-loads/TEMPLATE-node-mapping.csv), the tier-5 final option —
  authored at the app-code grain per gate §B1 (one authoring mechanism per
  code; the loader fans out to folders), with an optional folder_id for a
  per-folder pin on a shared platform code.

Mechanism only: fact-type names and node keys — real SEAL ids / app names
never appear in committed fixtures (synthetic twins only).
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field, field_validator


def _stripped_str(v: Any) -> str:
    """Coerce Oracle NUMBER / int inputs to the stripped-string node-key form."""
    return str(v).strip()


def _str_or_none(v: Any) -> str | None:
    if v in (None, ""):
        return None
    return str(v).strip() or None


def _int_or_none(v: Any) -> int | None:
    if v in (None, ""):
        return None
    return int(str(v).strip())


class StgAppFactRow(BaseModel):
    """One STG_APP_FACT row — a semantic fact asserted about a job.

    ``fact_type`` values come from the normalizer's FACT_REGISTRY
    (SEAL | FID | DS_ID | DATAFLOW | IMAGE | TGT_TABLE | TGT_DB |
    APP_NAME | ALIAS); only the four attribution tiers participate in
    the match policy — the rest are counted as ignored, never dropped
    silently.

    ``app_fact_sk`` is the staging identity column: monotonically
    increasing, so it doubles as the row-recency key the multi-hit
    tie-break needs ("most-recent STG_APP_FACT.run_id" — the extract SQL
    orders by stg_run.started_at, app_fact_sk, so feed order IS run
    recency; run_id itself is a UUID and carries no order).
    """

    run_id: str = Field(..., min_length=1)
    folder_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    fact_type: str = Field(..., min_length=1)
    fact_value: str = Field(..., min_length=1)
    data_center: str | None = None
    environment: str | None = None
    source_var: str | None = None
    app_fact_sk: int | None = Field(
        None, description="Staging identity column — the row-recency key."
    )

    @field_validator("run_id", "folder_id", "job_id", "fact_type", "fact_value", mode="before")
    @classmethod
    def _keys(cls, v: Any) -> str:
        return _stripped_str(v)

    @field_validator("data_center", "environment", "source_var", mode="before")
    @classmethod
    def _optionals(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator("app_fact_sk", mode="before")
    @classmethod
    def _sk(cls, v: Any) -> int | None:
        return _int_or_none(v)


class SealAttributionRow(BaseModel):
    """One accepted K2 job-grain decision (gate seal-attribution-match-policy).

    ``match_method`` is the winning precedence tier (``seal`` | ``fid`` |
    ``app_name`` | ``alias``). Since the K7 close-out this shape never
    reaches the graph — it is the K2 fallback's INTERNAL result, aggregated
    to the folder grain by the K8 resolver (§B3 demotion); the folder edge
    it feeds carries ``origin: matched-fallback`` so the derivation is
    disclosed.
    """

    folder_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    seal_id: str = Field(..., min_length=1)
    match_method: str = Field(..., pattern=r"^(seal|fid|app_name|alias)$")

    @field_validator("folder_id", "job_id", "seal_id", mode="before")
    @classmethod
    def _keys(cls, v: Any) -> str:
        return _stripped_str(v)


class FolderAttributionRow(BaseModel):
    """One folder-grain attribution — the ``$batch`` row shape of
    ``folder_attribution.cypher`` (K8; gate seal-app-ref-edge-reshape §D2:
    ONE shape everywhere).

    ``origin`` is the §B3 disclosure flag: ``defined`` / ``override`` /
    ``manual-pin`` rows come from the steward store (authored); a
    ``matched-fallback`` row was derived by the demoted K2 match policy at
    load time and is never presented as though it were defined.
    ``match_method`` mirrors the origin for authored rows and records the
    winning K2 tier for fallback rows. ``row_kind`` is the authored row's
    app-code kind (§B2; renamed from ``tier`` at K18 — the K2
    match-precedence tiers keep that word), absent on fallback rows.
    """

    folder_id: str = Field(..., min_length=1)
    app_id: str = Field(..., min_length=1)
    origin: str = Field(..., pattern=r"^(defined|override|manual-pin|matched-fallback)$")
    match_method: str = Field(..., pattern=r"^(defined|override|manual|seal|fid|app_name|alias)$")
    row_kind: str | None = Field(None, pattern=r"^(seal-born|platform|dual-coded)$")
    source: str = Field(..., min_length=1)
    # The authoring steward for authored rows; None on matched-fallback rows
    # (the loader identity becomes the K10 confirmed_by instead).
    authored_by: str | None = None

    @field_validator("folder_id", "app_id", mode="before")
    @classmethod
    def _keys(cls, v: Any) -> str:
        return _stripped_str(v)

    @field_validator("row_kind", "authored_by", mode="before")
    @classmethod
    def _row_kind(cls, v: Any) -> str | None:
        return _str_or_none(v)


class ManualMappingRow(BaseModel):
    """One SME-authored manual mapping (tier 5, gate §F; rekeyed at K8).

    Parsed from a CSV following config/manual-loads/TEMPLATE-node-mapping.csv.
    The generic template columns are validated upstream (supported shape,
    vocabulary existence, manifest registration) — this row is the already-
    narrowed ControlMFolder -[BELONGS_TO_APPLICATION {role: seal_app_ref}]->
    Port shape the manual cypher consumes. Authored at the APP-CODE grain
    (§B1); ``folder_id`` narrows a row to one folder (a per-folder pin on a
    shared platform code) and is otherwise None — the loader fans a
    code-level row out over CONTAINS_FOLDER.
    """

    app_code: str = Field(..., min_length=1)
    folder_id: str | None = None
    app_id: str = Field(..., min_length=1)
    create_target_if_missing: bool = False
    manual_load_file: str = Field(..., min_length=1)
    authored_by: str = Field(..., min_length=1)
    authored_on: str | None = None
    note: str | None = None

    @field_validator("app_code", "app_id", "manual_load_file", "authored_by", mode="before")
    @classmethod
    def _keys(cls, v: Any) -> str:
        return _stripped_str(v)

    @field_validator("folder_id", "authored_on", "note", mode="before")
    @classmethod
    def _optionals(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator("create_target_if_missing", mode="before")
    @classmethod
    def _flag(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("true", "1", "yes", "y")
