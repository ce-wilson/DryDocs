"""BMC Control-M row models.

Sources:
  - ``psgmgr.CM_DEF_VTAB``       (folders; wraps ``dtsremgr.DEF_TAB``)
  - ``psgmgr.CM_DEF_VJOB``       (jobs;    wraps ``dtsremgr.DEF_JOB``)
  - ``psgmgr.CM_DEF_LNKI_P_VW``  (in-conditions;  wraps ``dtsremgr.DEF_LNKI_P``)
  - ``psgmgr.CM_DEF_LNKO_P_VW``  (out-conditions; wraps ``dtsremgr.DEF_LNKO_P``)

The Oracle SELECT lives in ``drydocs/loaders/sql/controlm_*.sql``; this
module defines the columns the loaders expect after projection. CSV
samples in ``data/samples/`` use the same column names so offline dev
paths exercise the same models.
"""
from __future__ import annotations

from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


def _int_or_none(v: Any) -> int | None:
    if v in (None, ""):
        return None
    return int(str(v).strip())


def _str_or_none(v: Any) -> str | None:
    if v is None:
        return None
    s = str(v).strip()
    return s or None


class ControlMFolderRow(BaseModel):
    """One row of ``psgmgr.CM_DEF_VTAB`` (a replicated copy of
    ``dtsremgr.DEF_VTAB`` — it's a table, not a view, despite the family
    name).  BMC calls folders "tables" but they are folders.

    Key schema findings from the actual DDL:
      * Folder NAME is ``SCHED_TABLE`` (NOT a "parent_table" column —
        that name lives only on the job side as a denormalized FK).
      * No ``IS_CURRENT_VERSION`` or ``VERSION_SERIAL`` on this table;
        versioning lives only on jobs + conditions.
      * Active-scheduling filter is ``USER_DAILY IS NOT NULL``.

    Expected projection (matches ``drydocs/loaders/sql/controlm_folders.sql``):
        folder_id, sched_table, data_center, application, user_daily,
        table_status, table_type, instance_name, last_updated,
        last_updated_user, capture_date

    ``application`` comes from the folder HEADER ROW (``CM_DEF_VJOB`` where
    ``JOB_ID = 1`` — the SMART-Table header per the ``controlm-q1q3-phase1``
    gate), LEFT JOINed in the SQL: CM_DEF_VTAB itself carries no APPLICATION
    column. Optional so pre-extension sample CSVs still validate.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    folder_id: str = Field(..., min_length=1)
    sched_table: str = Field(
        ...,
        min_length=1,
        description="Folder name (CM_DEF_VTAB.SCHED_TABLE). Encodes the DAT area product per company convention.",
    )
    data_center: str = Field(
        ...,
        min_length=1,
        description="Control-M server (P12 / P14 / P32 / P33 / ...).",
    )
    application: str | None = Field(
        None,
        description=(
            "Control-M APPLICATION grouping from the folder header row "
            "(CM_DEF_VJOB JOB_ID=1) — becomes :ControlMApplication. "
            "NOT the SEAL business application."
        ),
    )
    user_daily: str | None = Field(
        None,
        description="Active-scheduling flag; null = inactive (quarantined, not dropped).",
    )
    table_status: str | None = Field(
        None,
        description="VARCHAR2(1). Folder lifecycle status code.",
    )
    table_type: int | None = Field(
        None,
        description="NUMBER. Folder type code (Smart Folder, Sub-Folder, etc.).",
    )
    instance_name: str | None = Field(
        None,
        description="Control-M instance name the folder is registered under.",
    )
    last_updated: str | None = Field(None, description="DATE column.")
    last_updated_user: str | None = None
    capture_date: str | None = Field(
        None,
        description="Audit timestamp from the psgmgr replication.",
    )

    @field_validator("application", "user_daily", "table_status", "instance_name",
                      "last_updated", "last_updated_user", "capture_date",
                      mode="before")
    @classmethod
    def _str_passthrough(cls, v: Any) -> str | None:
        return _str_or_none(v)

    @field_validator("table_type", mode="before")
    @classmethod
    def _table_type(cls, v: Any) -> int | None:
        return _int_or_none(v)

    @property
    def active(self) -> bool:
        """True iff ``USER_DAILY`` is set (the only active filter for folders)."""
        return self.user_daily is not None and self.user_daily != ""


class ControlMJobRow(BaseModel):
    """One row of ``psgmgr.CM_DEF_VJOB`` (replicated copy of
    ``dtsremgr.DEF_VJOB``).

    Composite key is ``(job_id, version_serial)`` — new ``VERSION_SERIAL``
    means a new graph node so history is non-destructive (v3 §J node-key
    constraint).

    CM_DEF_VJOB has 100+ columns. We project the identity, classification,
    versioning, and lifecycle fields and skip schedule-detail columns
    (DAY_STR, INTERVAL_SEQUENCE, MONTH_1..MONTH_12, etc.) — surface them
    later when a use case demands.

    Expected projection (matches ``drydocs/loaders/sql/controlm_jobs.sql``):
        job_id, version_serial, folder_id, job_name, parent_table,
        application, group_name, task_type, cyclic, cyclic_type,
        job_order, owner, author, node_id, cmd_line, description,
        memname, priority, critical, active_from, active_till,
        end_folder, is_current_version, version_opcode,
        version_timestamp, version_user, instance_name, capture_date,
        creation_user, creation_date, change_userid, change_date

    The last four are the SOURCE AUDIT ENVELOPE (doc 06 Phase 1; column
    mapping SME-confirmed at gate ``controlm-q1q3-phase1``): they become the
    ``source_created_by/_at`` + ``source_updated_by/_at`` node properties per
    ``config/audit-fields.yaml``. ``VERSION_USER``/``VERSION_TIMESTAMP`` stay
    projected but are NOT the envelope (current-version duplicates, per gate).
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    # --- identity + composite key ---
    job_id: str = Field(..., min_length=1)
    version_serial: int = Field(..., ge=0)
    folder_id: str = Field(..., min_length=1, description="FK to ControlMFolder.folder_id.")
    job_name: str = Field(..., min_length=1)
    parent_table: str | None = Field(
        None,
        description="Denormalized folder name (CM_DEF_VJOB.PARENT_TABLE = CM_DEF_VTAB.SCHED_TABLE).",
    )

    # --- classification ---
    application: str | None = Field(
        None,
        description="Business app name from CM_DEF_VJOB.APPLICATION. Used to reconcile to :Application.seal_id.",
    )
    group_name: str | None = None
    task_type: str | None = Field(None, description="VARCHAR2(21). Job / Smart Folder / etc.")
    cyclic: str | None = Field(None, description="Y/N flag for cyclic execution.")
    cyclic_type: str | None = Field(
        None,
        description="1-char type code. NOT used for condition matching in the canonical recursive SQL.",
    )
    job_order: int | None = None

    # --- ownership ---
    owner: str | None = None
    author: str | None = None
    node_id: str | None = Field(None, description="Target host or agent.")

    # --- execution detail ---
    cmd_line: str | None = None
    description: str | None = None
    memname: str | None = None
    priority: str | None = None
    critical: str | None = None
    active_from: str | None = None
    active_till: str | None = None
    end_folder: str | None = Field(None, description="Y/N flag — last job in folder.")

    # --- versioning + audit ---
    is_current_version: str | None = Field(
        None,
        description="VARCHAR2(1) — 'Y' = current version of this job definition (domain live-verified 2026-07-15, D4).",
    )
    version_opcode: str | None = None
    version_timestamp: str | None = None
    version_user: str | None = None
    instance_name: str | None = None
    capture_date: str | None = None

    # --- source audit envelope (doc 06; gate controlm-q1q3-phase1) ---
    creation_user: str | None = Field(
        None, description="Original creator SID (CREATION_USER) -> source_created_by.")
    creation_date: str | None = Field(
        None, description="Creation timestamp (CREATION_DATE) -> source_created_at.")
    change_userid: str | None = Field(
        None, description="Last editor SID (CHANGE_USERID) -> source_updated_by.")
    change_date: str | None = Field(
        None, description="Last change timestamp (CHANGE_DATE) -> source_updated_at.")

    # --- coercers ---

    @field_validator("version_serial", mode="before")
    @classmethod
    def _version_serial(cls, v: Any) -> int:
        return int(str(v).strip())

    @field_validator("job_order", mode="before")
    @classmethod
    def _job_order(cls, v: Any) -> int | None:
        return _int_or_none(v)

    @field_validator(
        "parent_table", "application", "group_name", "task_type",
        "cyclic", "cyclic_type", "owner", "author", "node_id", "cmd_line",
        "description", "memname", "priority", "critical", "active_from",
        "active_till", "end_folder", "is_current_version", "version_opcode",
        "version_timestamp", "version_user", "instance_name", "capture_date",
        "creation_user", "creation_date", "change_userid", "change_date",
        mode="before",
    )
    @classmethod
    def _str_passthrough(cls, v: Any) -> str | None:
        return _str_or_none(v)


class ControlMConditionInRow(BaseModel):
    """One row of ``psgmgr.CM_DEF_LNKI_P_VW`` — an IN condition.

    A job CONSUMES a condition. Multiple IN conditions can be combined via
    boolean operators (AND_OR + PARENTHESES + ORDER_).

    Confirmed columns from the actual DDL:
        CAPTURE_DATE, TABLE_ID, JOB_ID, CONDITION, ODATE, AND_OR,
        PARENTHESES, ORDER_, ISN_, VERSION_OPCODE, IS_CURRENT_VERSION,
        VERSION_SERIAL
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    folder_id: str = Field(..., min_length=1, description="TABLE_ID.")
    job_id: str = Field(..., min_length=1)
    version_serial: int = Field(..., ge=0)
    condition_name: str = Field(..., min_length=1, description="The CONDITION column.")
    odate: str | None = Field(None, description="Operational date.")
    and_or: str | None = Field(
        None, description="Boolean operator between adjacent IN conditions (AND / OR)."
    )
    parentheses: str | None = Field(
        None, description="Grouping marker for the IN-condition expression."
    )
    order_: int | None = Field(
        None,
        alias="order_",
        description="Evaluation order within the IN-condition expression.",
    )
    isn: int | None = None
    version_opcode: str | None = None
    is_current_version: str | None = None
    capture_date: str | None = None

    @field_validator("version_serial", "isn", "order_", mode="before")
    @classmethod
    def _int_lnki(cls, v: Any) -> int | None:
        return _int_or_none(v)

    @field_validator(
        "odate", "and_or", "parentheses", "version_opcode",
        "is_current_version", "capture_date",
        mode="before",
    )
    @classmethod
    def _str_lnki(cls, v: Any) -> str | None:
        return _str_or_none(v)


class ControlMConditionOutRow(BaseModel):
    """One row of ``psgmgr.CM_DEF_LNKO_P_VW`` — an OUT condition.

    A job EMITS a condition with a SIGN operator:
       SIGN = '+'  -> add the condition (success)
       SIGN = '-'  -> remove the condition (cleanup)

    Confirmed columns from the actual DDL:
        CAPTURE_DATE, TABLE_ID, JOB_ID, CONDITION, ODATE, SIGN, ISN_,
        VERSION_OPCODE, IS_CURRENT_VERSION, VERSION_SERIAL
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    folder_id: str = Field(..., min_length=1, description="TABLE_ID.")
    job_id: str = Field(..., min_length=1)
    version_serial: int = Field(..., ge=0)
    condition_name: str = Field(..., min_length=1)
    odate: str | None = Field(None, description="Operational date.")
    sign: str | None = Field(None, description="Emit operator (+ / -).")
    isn: int | None = None
    version_opcode: str | None = None
    is_current_version: str | None = None
    capture_date: str | None = None

    @field_validator("version_serial", "isn", mode="before")
    @classmethod
    def _int_lnko(cls, v: Any) -> int | None:
        return _int_or_none(v)

    @field_validator(
        "odate", "sign", "version_opcode", "is_current_version",
        "capture_date",
        mode="before",
    )
    @classmethod
    def _str_lnko(cls, v: Any) -> str | None:
        return _str_or_none(v)


class ControlMVariableRow(BaseModel):
    """One variable definition from ``psgmgr.CM_DEF_SETVAR_VW`` — the view
    behind the SQL Developer variable extract (name confirmed 2026-07-10).

    Accepts BOTH column shapes:
      * the formal projection from ``controlm_variables.sql``
        (data_center, folder_id, folder_name, job_id, job_name, appl_type,
        var_scope, var_name, var_value), and
      * the raw SQL Developer export headers
        (TABLE_NAME | JOB_NAME | JOB_ID | APPL_TYPE | NAME | VALUE) —
        note TABLE_NAME in that export actually carries TABLE_ID values.

    Duplicate (job, var_name) definitions are legitimate in the source —
    %%FileWatch-TIME_LIMIT was observed defined twice on one job with
    different values. Never dedupe at the model layer.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    folder_id: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("folder_id", "table_name", "table_id"),
        description="TABLE_ID (the raw extract mislabels it TABLE_NAME).",
    )
    job_id: str = Field(..., min_length=1)
    var_name: str = Field(
        ...,
        min_length=1,
        validation_alias=AliasChoices("var_name", "name"),
        description="Variable name including the %% prefix.",
    )
    var_value: str | None = Field(
        None,
        validation_alias=AliasChoices("var_value", "value"),
    )
    data_center: str | None = Field(
        None,
        description="Control-M server; absent from the raw SQL Developer export.",
    )
    folder_name: str | None = Field(
        None, description="SCHED_TABLE; only present in the formal projection."
    )
    job_name: str | None = None
    appl_type: str | None = Field(
        None, description="OS / FileWatch / AIAWSWLK / ... (plugin job type)."
    )
    var_scope: str | None = Field(
        None,
        description="FOLDER (smart-folder header row) or JOB; derived in SQL.",
    )

    @field_validator(
        "var_value", "data_center", "folder_name", "job_name",
        "appl_type", "var_scope",
        mode="before",
    )
    @classmethod
    def _str_var(cls, v: Any) -> str | None:
        return _str_or_none(v)


class ControlMDependencyRow(BaseModel):
    """One row of the recursive-predecessor SQL output.

    Each row is a (successor job, matching condition, predecessor job)
    triple plus the recursion level and the full dependency path.

    Matches the SELECT in
    ``drydocs/loaders/sql/controlm_dependencies_recursive.sql``.
    """

    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True,
        extra="ignore",
    )

    in_parent_table: str = Field(..., description="Successor folder name.")
    in_job_name: str = Field(..., min_length=1, description="Successor job name.")
    in_parent_table_id: str = Field(..., description="Successor folder id.")
    in_job_id: str = Field(..., description="Successor job id.")
    in_table_job_id: str = Field(
        ..., description="Composite '<folder_id>.<job_id>' for the successor."
    )
    out_condition: str = Field(
        ..., description="The condition name that links them."
    )
    dependent_table: str = Field(..., description="Predecessor folder name.")
    dependent_job: str = Field(..., min_length=1, description="Predecessor job name.")
    dependent_table_id: str = Field(..., description="Predecessor folder id.")
    dependent_job_id: str = Field(..., description="Predecessor job id.")
    out_table_job_id: str = Field(
        ..., description="Composite '<folder_id>.<job_id>' for the predecessor."
    )
    recursion_level: int = Field(..., ge=1)
    dependency_path: str = Field(
        ..., description="Full ' -> '-joined chain from successor back to this predecessor."
    )

    @field_validator("recursion_level", mode="before")
    @classmethod
    def _rl(cls, v: Any) -> int:
        return int(str(v).strip())
