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


class Neo4jSettings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="NEO4J_",
        env_file=".env",
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
        env_file=".env",
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
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    log_level: str = "INFO"


def load_settings() -> tuple[Neo4jSettings, OracleSettings, AppSettings]:
    return Neo4jSettings(), OracleSettings(), AppSettings()