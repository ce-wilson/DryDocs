"""G75 — condition-name scope, and the identity rule that follows from it.

The scope classification is trivial. The consequence is not: two LOCAL
conditions sharing a name in different data centers are DIFFERENT conditions,
so a key built from the name alone merges them — inventing a dependency rather
than losing one, which is the failure class that does not announce itself.
"""

from __future__ import annotations

import pytest

from drydocs_core.orchestration.controlm import (
    condition_identity,
    condition_scope,
)


class TestScope:
    def test_pl_prefix_is_local(self) -> None:
        assert condition_scope("PL-SAMPLE-FOLDER-OK") == "LOCAL"

    def test_pg_prefix_is_global(self) -> None:
        assert condition_scope("PG-SAMPLE-CROSS-DC-OK") == "GLOBAL"

    def test_surrounding_whitespace_does_not_hide_the_prefix(self) -> None:
        assert condition_scope("  PL-SAMPLE-OK  ") == "LOCAL"

    @pytest.mark.parametrize(
        "name",
        ["SAMPLE-OK", "XX-SAMPLE-OK", "pl-lowercase-is-not-the-convention", "PL", "PLSAMPLE"],
    )
    def test_anything_else_is_unknown(self, name: str) -> None:
        assert condition_scope(name) == "UNKNOWN"

    @pytest.mark.parametrize("empty", [None, "", "   "])
    def test_empty_is_unknown_not_an_error(self, empty: str | None) -> None:
        """An unrecognized name is a fact about the estate to report, never
        something that should stop a load."""
        assert condition_scope(empty) == "UNKNOWN"


class TestIdentity:
    def test_local_conditions_are_distinct_across_data_centers(self) -> None:
        """THE RULE THIS MODULE EXISTS FOR."""
        one = condition_identity("PL-SAMPLE-OK", "P012-E0700-IB")
        two = condition_identity("PL-SAMPLE-OK", "P032-E0700-DMA")
        assert one != two

    def test_global_conditions_are_the_same_across_data_centers(self) -> None:
        one = condition_identity("PG-SAMPLE-OK", "P012-E0700-IB")
        two = condition_identity("PG-SAMPLE-OK", "P032-E0700-DMA")
        assert one == two

    def test_global_identity_carries_no_data_center(self) -> None:
        assert condition_identity("PG-SAMPLE-OK", "P012-E0700-IB") == ("PG-SAMPLE-OK", "")

    def test_local_identity_carries_the_data_center(self) -> None:
        assert condition_identity("PL-SAMPLE-OK", "P012-E0700-IB") == (
            "PL-SAMPLE-OK",
            "P012-E0700-IB",
        )

    def test_unknown_scope_is_qualified_by_data_center(self) -> None:
        """Assuming the global scope is what would MERGE two distinct
        conditions, so an unrecognized prefix stays data-center-qualified."""
        one = condition_identity("SAMPLE-OK", "P012-E0700-IB")
        two = condition_identity("SAMPLE-OK", "P032-E0700-DMA")
        assert one != two

    def test_missing_data_center_does_not_raise(self) -> None:
        assert condition_identity("PL-SAMPLE-OK", None) == ("PL-SAMPLE-OK", "")
