"""Application configuration via pydantic-settings.

Three settings groups, each loaded from environment variables (or .env):
- :class:`Neo4jSettings` (NEO4J_*)
- :class:`OracleSettings` (ORACLE_*)
- :class:`AppSettings`    (DRYDOCS_*)

Use :func:`load_settings` to fetch all three at once. Loaders construct only
what they need; the bootstrap CLI pulls Neo4jSettings first.

A fourth group, :class:`Neo4jDriverBounds` (CORE13), comes from
``config/dev-environment.yaml`` rather than the environment: the four waits are
per-machine operational facts, and that file is the one already ruled
canonical-company for exactly that class of value.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

#: DELIBERATELY NOT routed through ``repo_paths.repo_root`` in the Idea-109 sweep,
#: and it is the one site where following the caller would be a regression rather
#: than a fix. ``.env`` is untracked machine-local credentials: a ``git worktree``
#: gets the tracked tree and NOT this file, so a worktree run that followed the
#: caller would find no ``.env`` at all and lose its database settings. The
#: install's ``.env`` is the one that exists, which makes ``__file__`` the correct
#: anchor here — the rule is repo CONTENT follows the caller, and an untracked
#: local secret is not repo content.
_ENV_FILE = Path(__file__).resolve().parent.parent / ".env"


class Neo4jSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEO4J_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    uri: str = "bolt://localhost:7687"
    user: str = "neo4j"
    password: SecretStr = Field(default=SecretStr(""))
    database: str | None = None
    import_dir: Path | None = None


class OracleSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="ORACLE_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    user: str = ""
    password: SecretStr = Field(default=SecretStr(""))
    dsn: str = ""

    @property
    def configured(self) -> bool:
        return bool(self.user and self.password.get_secret_value() and self.dsn)


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DRYDOCS_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = "INFO"


class RuntimeSettings(BaseSettings):
    """The runtime substrate — ADR 0014 clause 1, accepted 2026-08-25.

    A per-machine operational group: a path, a verbosity, a retention window.
    ADR 0009's rule 1 keeps git text the source of truth for anything an SME
    gates, a port carries, or a classification test guards — this is none of the
    three, which is why it is an exception 0009 already permits rather than an
    amendment to it. (``PORT-MANIFEST.yaml`` marks the sibling
    ``dev-environment.yaml`` ``canonical-company`` for the same reason: every
    value in it is a local fact that must never cross.)

    THE PER-KIND HALF LIVES IN ``config/log-kinds.yaml``, not here. The ruling
    amended clause 1 from one global set to a per-kind declaration, so
    ``log_level`` and ``log_retention_days`` below are the FALLBACKS a kind
    inherits when it declares none of its own — read
    :func:`drydocs_core.log_kinds.load_kinds` for the resolved values. Keeping
    four flat fields here as well would be the second declaration the ADR fences
    against.
    """

    model_config = SettingsConfigDict(
        env_prefix="DRYDOCS_",
        env_file=_ENV_FILE,
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = "INFO"
    log_retention_days: int = 90

    @property
    def log_dir(self) -> Path:
        """Resolved through the ONE root site — ``DRYDOCS_LOGDIR`` >
        ``SPIDERP_LOGDIR`` (deprecated, warns) > the declared default."""
        from drydocs_core.run_log import resolve_log_dir

        return resolve_log_dir()

    @property
    def data_root(self) -> Path:
        """The G81 data root. MANDATORY — unset raises rather than relocating
        every zone to a default, which is how a write lands on source data."""
        from drydocs_core.data_root import resolve_data_root

        return resolve_data_root()


def load_settings() -> tuple[Neo4jSettings, OracleSettings, AppSettings]:
    return Neo4jSettings(), OracleSettings(), AppSettings()


# ── CORE13: how long a caller waits before "the server is not there" ─────────

#: The keys read from ``config/dev-environment.yaml`` ``neo4j.driver``, and the
#: values used when that block is ABSENT. They are a declared fallback, not the
#: literals ADR 0014 forbids — the distinction being that these are named once,
#: in the module the config layer already owns, with the reason attached, and
#: the file overrides every one of them.
#:
#: The block can legitimately be absent, which is why this is a fallback and not
#: a refusal: ``dev-environment.yaml`` is ``canonical-company`` in
#: ``PORT-MANIFEST.yaml``, so a port does NOT carry the producer's copy across.
#: The company's file gains the block by hand, and until it does, a checkout
#: that ports this module still gets bounded waits rather than the unbounded
#: hang CORE13 exists to end. Raising instead would turn a missing optional
#: block into a broken tree on the far side of a port.
DRIVER_BOUND_DEFAULTS: dict[str, float] = {
    "connection_timeout": 15.0,
    "connection_acquisition_timeout": 30.0,
    "max_transaction_retry_time": 30.0,
    "transaction_timeout": 120.0,
}


@dataclass(frozen=True)
class Neo4jDriverBounds:
    """The four waits, in seconds, that keep an unreachable server from hanging
    a caller (core report S4, 2026-09-07).

    Four rather than one because they fail at different layers and one number
    cannot express them — see the comment above ``neo4j.driver`` in
    ``config/dev-environment.yaml``, which carries the reasoning and the values.

    ``transaction_timeout`` is the only one the DRIVER does not take as pool
    configuration: it reaches a managed transaction through
    ``neo4j.unit_of_work``, which is what ``Driver.execute_query`` itself uses
    when handed a ``Query`` carrying a timeout.
    """

    connection_timeout: float = DRIVER_BOUND_DEFAULTS["connection_timeout"]
    connection_acquisition_timeout: float = DRIVER_BOUND_DEFAULTS["connection_acquisition_timeout"]
    max_transaction_retry_time: float = DRIVER_BOUND_DEFAULTS["max_transaction_retry_time"]
    transaction_timeout: float = DRIVER_BOUND_DEFAULTS["transaction_timeout"]

    def pool_config(self) -> dict[str, float]:
        """The subset ``GraphDatabase.driver`` accepts as configuration."""
        return {
            "connection_timeout": self.connection_timeout,
            "connection_acquisition_timeout": self.connection_acquisition_timeout,
            "max_transaction_retry_time": self.max_transaction_retry_time,
        }


def load_driver_bounds(path: Path | None = None) -> Neo4jDriverBounds:
    """Read ``neo4j.driver`` from ``config/dev-environment.yaml``.

    Repo CONTENT follows the caller (Idea-109), so the default path resolves
    through :func:`drydocs_core.repo_paths.repo_root` — unlike ``_ENV_FILE``
    above, which is untracked machine-local credentials and correctly anchors on
    ``__file__``.

    A missing file, a missing block or a missing key each falls back to the
    declared default for that key alone; a value that is not a number is
    ignored the same way rather than crashing a load on a typo in an optional
    block. Every substitution is silent BY DESIGN here and only here: these are
    waits, and a checkout with no block still gets bounded ones.
    """
    from drydocs_core.repo_paths import repo_root

    if path is None:
        path = repo_root(Path(__file__).resolve().parent) / "config" / "dev-environment.yaml"
    block: Any = {}
    if path.is_file():
        try:
            loaded = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            block = ((loaded.get("neo4j") or {}).get("driver")) or {}
        except (yaml.YAMLError, OSError, AttributeError):
            block = {}
    values = dict(DRIVER_BOUND_DEFAULTS)
    if isinstance(block, dict):
        for key in values:
            raw = block.get(key)
            if isinstance(raw, int | float) and not isinstance(raw, bool) and raw > 0:
                values[key] = float(raw)
    return Neo4jDriverBounds(**values)
