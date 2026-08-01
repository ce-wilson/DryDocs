"""G26 — the launcher registry is a schema-guarded CONFIG surface.

config/launcher-registry.yaml is the source of truth commands.py loads at
import; these guards keep it honest:

- schema id + row shape (ordered rules; compilable patterns; required keys);
- rule ids unique — STG_INVOCATION.classifier_rule values and the
  software-registry invocation_patterns rows pin them for gate review, so a
  rename is a BREAKING change this file catches;
- every classifier_rule referenced by config/taxonomy/software-registry.yaml
  invocation_patterns still resolves;
- the loaded module state matches the file (no drift between config and the
  compiled registry / the named-launcher value-contract subset).

Parser BEHAVIOR is deliberately not re-tested here — test_command_parser.py
staying green untouched is the no-behavior-change proof.
"""

from __future__ import annotations

import re
from pathlib import Path

import yaml

from drydocs_core.controlm import commands

REPO_ROOT = Path(__file__).resolve().parents[2]
REGISTRY = REPO_ROOT / "config" / "launcher-registry.yaml"
SOFTWARE_REGISTRY = REPO_ROOT / "config" / "taxonomy" / "software-registry.yaml"

REQUIRED_KEYS = {"pattern", "invocation_type", "rule"}
OPTIONAL_KEYS = {"ignore_case", "named_launcher"}


def _load() -> dict:
    assert REGISTRY.exists(), f"Missing: {REGISTRY}"
    return yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))


def test_schema_and_row_shape() -> None:
    data = _load()
    assert data["schema"] == commands.LAUNCHER_REGISTRY_SCHEMA
    rules = data["rules"]
    assert rules, "registry has no rules — every command would classify UNKNOWN"
    for row in rules:
        missing = REQUIRED_KEYS - set(row)
        assert not missing, f"rule {row.get('rule', '<?>')} missing {sorted(missing)}"
        unknown = set(row) - REQUIRED_KEYS - OPTIONAL_KEYS
        assert not unknown, f"rule {row['rule']} has unknown keys {sorted(unknown)}"
        re.compile(row["pattern"])  # must compile
        assert row["invocation_type"].strip()
        assert row["rule"].strip()


def test_rule_ids_unique() -> None:
    rules = [row["rule"] for row in _load()["rules"]]
    assert len(rules) == len(set(rules)), "duplicate classifier_rule ids"


def test_loaded_module_state_matches_the_file() -> None:
    data = _load()
    assert len(commands.LAUNCHER_REGISTRY) == len(data["rules"])
    for (pattern, itype, rule), row in zip(commands.LAUNCHER_REGISTRY, data["rules"], strict=False):
        assert pattern.pattern == row["pattern"]
        assert bool(pattern.flags & re.IGNORECASE) == bool(row.get("ignore_case"))
        assert itype == row["invocation_type"]
        assert rule == row["rule"]
    named_in_file = {r["rule"] for r in data["rules"] if r.get("named_launcher")}
    assert commands.NAMED_LAUNCHER_RULES == named_in_file
    # the value-contract subset must never include the generic rules
    assert not {r for r in named_in_file if r.startswith(("shell.", "python.", "java.", "perl."))}


def test_invocation_pattern_rows_still_resolve() -> None:
    """software-registry invocation_patterns rows pin classifier_rule ids for
    gate review — every referenced id must exist in the config registry."""
    rule_ids = {row["rule"] for row in _load()["rules"]}
    # the one classifier assigned in parser LOGIC, not a basename rule (G15c)
    rule_ids |= {"dpl.pipeline_guid_literal", "abioncloud.runscript_wrapper.pset_payload"}
    sw = yaml.safe_load(SOFTWARE_REGISTRY.read_text(encoding="utf-8"))
    patterns = (sw.get("invocation_patterns") or {}).get("patterns") or []
    assert patterns, "invocation_patterns rows expected (plan-07 Phase 3 proposal)"
    for row in patterns:
        ref = row.get("classifier_rule")
        if ref:
            assert ref in rule_ids, (
                f"invocation_patterns row {row.get('id')} references "
                f"classifier_rule {ref!r} which no registry rule defines"
            )


def test_schema_mismatch_is_loud(tmp_path) -> None:
    bad = tmp_path / "launcher-registry.yaml"
    bad.write_text("schema: something-else\nrules: []\n", encoding="utf-8")
    try:
        commands.load_launcher_registry(bad)
    except ValueError as exc:
        assert "expected schema" in str(exc)
    else:
        raise AssertionError("schema mismatch must raise, not load an empty registry")
