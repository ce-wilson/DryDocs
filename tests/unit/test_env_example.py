"""G122 — every env-var name a settings group declares appears in .env.example.

The runtime shape must be reproducible from a clean checkout: an operator
copies `.env.example` to `.env` and fills in values. A field added to a
settings group without a line here is a knob nobody can discover without
reading the source — the same drift class the runbook-currency guard closes
for prose, applied to the committed environment template.

NAMES ONLY. The template ships no real value (`PUBLISH-BOUNDARY.md`); this
guard asserts the KEY exists as a declared `NAME=` line, never anything about
what follows the `=`.

The group walk is INTROSPECTED, not hand-listed: every BaseSettings subclass
in drydocs_core.config, env_prefix + field name -> expected env var. A new
group or field is covered the moment it exists, and pydantic properties
(log_dir, data_root — resolved elsewhere) are not fields, so they are
excluded by construction.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

from pydantic_settings import BaseSettings

from drydocs_core import config as config_mod

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_EXAMPLE = REPO_ROOT / ".env.example"


def _settings_groups() -> list[type[BaseSettings]]:
    return [
        member
        for _, member in inspect.getmembers(config_mod, inspect.isclass)
        if issubclass(member, BaseSettings)
        and member is not BaseSettings
        and member.__module__ == config_mod.__name__
    ]


def _declared_keys() -> set[str]:
    keys: set[str] = set()
    for line in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"^([A-Z][A-Z0-9_]*)=", line)
        if m:
            keys.add(m.group(1))
    return keys


def test_groups_exist_and_declare_prefixes() -> None:
    """Precondition: the walk found real groups (an empty walk would make the
    completeness assertion vacuously green — the G81 empty-declaration trap)."""
    groups = _settings_groups()
    assert len(groups) >= 3, [g.__name__ for g in groups]
    for group in groups:
        assert group.model_config.get("env_prefix"), f"{group.__name__} declares no env_prefix"


def test_every_settings_field_has_an_env_example_line() -> None:
    declared = _declared_keys()
    missing: list[str] = []
    for group in _settings_groups():
        prefix = group.model_config.get("env_prefix", "")
        for field_name in group.model_fields:
            env_name = f"{prefix}{field_name}".upper()
            if env_name not in declared:
                missing.append(f"{env_name} (settings group {group.__name__})")
    assert not missing, (
        ".env.example is missing declared settings keys — add a NAME= line "
        "(names only, never a real value):\n  " + "\n  ".join(sorted(set(missing)))
    )
