"""Application configuration via pydantic-settings.

Three settings groups, each loaded from environment variables (or .env):
- :class:`Neo4jSettings` (NEO4J_*)
- :class:`OracleSettings` (ORACLE_*)
- :class:`AppSettings`    (DRYDOCS_*)

Use :func:`load_settings` to fetch all three at once. Loaders construct only
what they need; the bootstrap CLI pulls Neo4jSettings first.
"""

from __future__ import annotations

from pathlib import Path

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
