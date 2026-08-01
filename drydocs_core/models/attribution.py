"""SEAL attribution rows (backlog K2, gate seal-attribution-match-policy).

Three contracts:

- :class:`StgAppFactRow` — one DRYDOCS_STG.STG_APP_FACT row (semantic facts
  mined from Control-M variables by the C3/C4 normalization stream). The
  attribution loader's *input*; validated inside the adapter before the
  match policy runs.
- :class:`SealAttributionRow` — one resolved attribution *decision*
  (job -> Application), the shape ``seal_attribution.cypher`` consumes.
  Produced only by the match-policy resolver, never read from a source.
- :class:`ManualMappingRow` — one SME-authored manual mapping CSV row
  (config/manual-loads/TEMPLATE-node-mapping.csv), the tier-5 final option.

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
    """One accepted attribution decision — the ``$batch`` row shape of
    ``seal_attribution.cypher`` (gate §D: the edge write shape).

    ``match_method`` is the winning precedence tier (``seal`` | ``fid`` |
    ``app_name`` | ``alias``) — recorded ON CREATE so mixed-precedence
    attribution stays auditable (gate §E). The manual path never produces
    this row (it has its own loader + ``match_method: 'manual'``).
    """

    folder_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    seal_id: str = Field(..., min_length=1)
    match_method: str = Field(..., pattern=r"^(seal|fid|app_name|alias)$")

    @field_validator("folder_id", "job_id", "seal_id", mode="before")
    @classmethod
    def _keys(cls, v: Any) -> str:
        return _stripped_str(v)


class ManualMappingRow(BaseModel):
    """One SME-authored manual mapping (tier 5, gate §F).

    Parsed from a CSV following config/manual-loads/TEMPLATE-node-mapping.csv.
    The generic template columns are validated upstream (supported shape,
    vocabulary existence, manifest registration) — this row is the already-
    narrowed ControlMJob -[WAS_ASSOCIATED_WITH {role: seal_app_ref}]->
    Application shape the manual cypher consumes.
    """

    folder_id: str = Field(..., min_length=1)
    job_id: str = Field(..., min_length=1)
    seal_id: str = Field(..., min_length=1)
    create_target_if_missing: bool = False
    manual_load_file: str = Field(..., min_length=1)
    authored_by: str = Field(..., min_length=1)
    authored_on: str | None = None
    note: str | None = None

    @field_validator(
        "folder_id", "job_id", "seal_id", "manual_load_file", "authored_by", mode="before"
    )
    @classmethod
    def _keys(cls, v: Any) -> str:
        return _stripped_str(v)

    @field_validator("authored_on", "note", mode="before")
    @classmethod
    def _optionals(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator("create_target_if_missing", mode="before")
    @classmethod
    def _flag(cls, v: Any) -> bool:
        if isinstance(v, bool):
            return v
        return str(v).strip().lower() in ("true", "1", "yes", "y")
