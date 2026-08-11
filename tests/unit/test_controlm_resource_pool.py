"""G76 — Quantitative Resource pool classification.

Three properties carry their own tests because a rewrite loses them quietly:
rule ORDER is correctness rather than style, `unknown` is a first-class
outcome rather than an error, and the never-observed `business_app` branch is
labelled speculative rather than presented as evidence.

Every pool name here is SYNTHETIC. The real vocabulary is estate data and
lives in the values twin under internal/ — which is exactly what the
caller-supplied rule table exists to keep out of this repo.
"""

from __future__ import annotations

import dataclasses
import re

import pytest

from drydocs_core.orchestration.controlm import classify_pool
from drydocs_core.orchestration.controlm.resource_pool import (
    DEFAULT_APP_CODE_RE,
    DEFAULT_RULES,
    PoolRule,
)

# A synthetic table with the same SHAPE as a real one: narrow rules first, then
# a broad rule that matches its token anywhere in the name.
NARROW = PoolRule("target_database", re.compile(r"(?:^|-)DBX(?:-|$)", re.IGNORECASE))
CONTROLLER = PoolRule("etl_platform", re.compile(r"-(?:RUN-CTRL|CTRL)(?:-|$)", re.IGNORECASE))
BROAD = PoolRule("source_platform", re.compile(r"-FEED(?:-|$)", re.IGNORECASE))
TERMINAL = PoolRule("host_node", re.compile(r"-(?:NODE|QUEUE)$", re.IGNORECASE))

RULES = (NARROW, CONTROLLER, BROAD, TERMINAL)
APP_CODE_RE = re.compile(r"^(SYN[A-Z0-9]{1,3})(?:-|$)")


class TestDefaultsAreEmptyAndHonest:
    """An un-configured deployment classifies everything unknown. That is the
    accurate answer for a repo that does not hold the vocabulary — not merely
    a safe one."""

    def test_default_rule_table_is_empty(self) -> None:
        assert DEFAULT_RULES == ()

    def test_default_app_code_pattern_is_absent(self) -> None:
        assert DEFAULT_APP_CODE_RE is None

    def test_everything_is_unknown_without_a_table(self) -> None:
        result = classify_pool("SYNAPP-SUBSYS-DBX-NODE")
        assert result.category == "unknown"
        assert result.secondary_label is None

    def test_positional_tokens_still_parse_without_a_table(self) -> None:
        """The grammar is ours; only the vocabulary is caller-supplied."""
        result = classify_pool("SYNAPP-SUBSYS-DBX-NODE")
        assert result.subsystem == "SUBSYS"
        assert result.kind_suffix == "NODE"
        assert result.app_code is None  # no pattern supplied


class TestRuleOrderIsCorrectness:
    def test_first_match_wins(self) -> None:
        result = classify_pool("SYNAPP-DBX-FEED-NODE", rules=RULES)
        assert result.category == "target_database"

    def test_a_broad_rule_placed_first_steals_the_narrow_rule_pools(self) -> None:
        """THE REGRESSION THE ORDERED SEQUENCE EXISTS TO PREVENT.

        Same rules, same input, different order — different answer. A table
        stored as a mapping keyed by category would lose this ordering, and
        the loss stays invisible until a misclassified pool reaches the graph.
        """
        ordered = classify_pool("SYNAPP-DBX-FEED-NODE", rules=(NARROW, BROAD))
        reversed_ = classify_pool("SYNAPP-DBX-FEED-NODE", rules=(BROAD, NARROW))
        assert ordered.category == "target_database"
        assert reversed_.category == "source_platform"
        assert ordered.category != reversed_.category

    def test_controller_rule_precedes_the_broad_feed_rule(self) -> None:
        """A pool satisfying both must read as the narrower category."""
        result = classify_pool("SYNAPP-FEED-RUN-CTRL", rules=RULES)
        assert result.category == "etl_platform"

    def test_terminal_rule_is_anchored(self) -> None:
        assert classify_pool("SYNAPP-SUBSYS-NODE", rules=RULES).category == "host_node"
        assert classify_pool("SYNAPP-NODE-SUBSYS", rules=RULES).category == "unknown"


class TestUnknownIsFirstClass:
    def test_unrecognized_name_classifies_unknown_without_raising(self) -> None:
        result = classify_pool("ZZZ-NOTHING-MATCHES", rules=RULES)
        assert result.category == "unknown"

    def test_unknown_carries_no_secondary_label(self) -> None:
        """No label means the loader adds none and logs a WARN — how misses
        surface in CI instead of becoming a silently absent edge."""
        assert classify_pool("ZZZ-NOTHING", rules=RULES).secondary_label is None

    @pytest.mark.parametrize("empty", [None, "", "   ", "\t"])
    def test_empty_input_always_returns_a_result(self, empty: str | None) -> None:
        result = classify_pool(empty, rules=RULES)
        assert result.category == "unknown"
        assert result.name == ""
        assert result.app_code is None

    def test_recognized_categories_do_carry_their_label(self) -> None:
        assert classify_pool("SYNAPP-DBX-X", rules=RULES).secondary_label == "TargetDatabase"


class TestSpeculativeBusinessAppBranch:
    """NEVER OBSERVED in the captured estate. The branch is kept only because
    the company original reserves it to complete the contract, and it is
    tested as speculative rather than as evidence."""

    def test_two_token_name_with_an_app_code_falls_back_to_business_app(self) -> None:
        result = classify_pool("SYNAPP-SUBSYS", rules=RULES, app_code_re=APP_CODE_RE)
        assert result.category == "business_app"
        assert result.app_code == "SYNAPP"

    def test_fallback_needs_an_app_code(self) -> None:
        result = classify_pool("OTHER-SUBSYS", rules=RULES, app_code_re=APP_CODE_RE)
        assert result.category == "unknown"

    def test_fallback_never_overrides_a_matched_rule(self) -> None:
        result = classify_pool("SYNAPP-NODE", rules=RULES, app_code_re=APP_CODE_RE)
        assert result.category == "host_node"


class TestPositionalTokens:
    def test_app_code_parses_when_a_pattern_is_supplied(self) -> None:
        result = classify_pool("SYNAPP-SUBSYS-DBX", rules=RULES, app_code_re=APP_CODE_RE)
        assert result.app_code == "SYNAPP"

    def test_a_single_token_name_has_no_positional_tokens(self) -> None:
        result = classify_pool("SOLO", rules=RULES)
        assert result.subsystem is None
        assert result.kind_suffix is None

    def test_two_token_name_yields_the_same_token_twice_by_design(self) -> None:
        """RULED, not inherited: with <APP>-<KIND> one token genuinely plays
        both the second-position and terminal roles, and blanking either would
        discard information the name carries. Callers comparing the two fields
        must expect equality on short names."""
        result = classify_pool("SYNAPP-NODE", rules=RULES)
        assert result.subsystem == result.kind_suffix == "NODE"

    def test_classification_is_frozen(self) -> None:
        result = classify_pool("SYNAPP-DBX-X", rules=RULES)
        with pytest.raises(dataclasses.FrozenInstanceError):
            result.category = "unknown"  # type: ignore[misc]
