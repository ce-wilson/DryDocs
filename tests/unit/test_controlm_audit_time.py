"""G75 — BMC compact audit-timestamp normalization.

Every branch has a test because every branch is a failure mode someone hit,
not a preference. The one that matters most is the last: an unparseable value
must return None so a caller's null-guard drops ONE FIELD, rather than a
malformed string reaching the Neo4j driver and aborting the whole load.
"""

from __future__ import annotations

import pytest

from drydocs_core.orchestration.controlm import normalize_export_timestamp


class TestCompactForm:
    def test_utc_suffix_normalizes_to_z(self) -> None:
        assert normalize_export_timestamp("20250715172540UTC") == "2025-07-15T17:25:40Z"

    def test_bare_z_suffix_normalizes_to_z(self) -> None:
        assert normalize_export_timestamp("20250715172540Z") == "2025-07-15T17:25:40Z"

    def test_lowercase_zone_token_is_accepted(self) -> None:
        assert normalize_export_timestamp("20250715172540utc") == "2025-07-15T17:25:40Z"

    def test_no_zone_token_stays_zoneless(self) -> None:
        assert normalize_export_timestamp("20250715172540") == "2025-07-15T17:25:40"

    @pytest.mark.parametrize("offset", ["+0100", "-0500", "+01:00"])
    def test_numeric_offset_is_kept_verbatim(self, offset: str) -> None:
        """Rewriting an offset to Z would MOVE THE INSTANT — the one
        normalization that would silently corrupt the value."""
        assert normalize_export_timestamp(f"20250715172540{offset}") == (
            f"2025-07-15T17:25:40{offset}"
        )


class TestDateOnly:
    def test_eight_digit_date_becomes_midnight(self) -> None:
        assert normalize_export_timestamp("20250715") == "2025-07-15T00:00:00"

    def test_date_only_keeps_its_zone(self) -> None:
        assert normalize_export_timestamp("20250715UTC") == "2025-07-15T00:00:00Z"


class TestPassThrough:
    """The Oracle projections deliver this form and the loaders' Cypher already
    parses it. A normalizer that rewrote it would break the working path."""

    def test_oracle_space_separated_form_is_untouched(self) -> None:
        assert normalize_export_timestamp("2025-07-15 17:25:40") == "2025-07-15 17:25:40"

    def test_iso_t_form_is_untouched(self) -> None:
        assert normalize_export_timestamp("2025-07-15T17:25:40") == "2025-07-15T17:25:40"

    def test_iso_with_zone_is_untouched(self) -> None:
        assert normalize_export_timestamp("2025-07-15T17:25:40Z") == "2025-07-15T17:25:40Z"

    def test_iso_date_only_is_untouched(self) -> None:
        assert normalize_export_timestamp("2025-07-15") == "2025-07-15"

    def test_surrounding_whitespace_is_stripped(self) -> None:
        assert normalize_export_timestamp("  2025-07-15 17:25:40  ") == "2025-07-15 17:25:40"


class TestUnparseableReturnsNone:
    """THE LOAD-BEARING CASE. A bad value costs one field, never the load.

    This is also the deliberate divergence from the captured company original,
    which documented this behaviour but fell through to returning the input —
    so a garbage string still reached the driver.
    """

    @pytest.mark.parametrize(
        "bad",
        [
            "N/A",
            "PENDING",
            "not a date",
            "202507",  # too short to be either form
            "2025071517254",  # 13 digits — neither 8 nor 14
            "202507151725401",  # 15 digits
            "15/07/2025",  # a real date, but not a form the loaders parse
        ],
    )
    def test_unrecognized_values_return_none(self, bad: str) -> None:
        assert normalize_export_timestamp(bad) is None

    def test_garbage_with_a_zone_token_still_returns_none(self) -> None:
        """Stripping a trailing UTC must not make nonsense look parseable."""
        assert normalize_export_timestamp("GARBAGEUTC") is None


class TestEmptyInput:
    @pytest.mark.parametrize("empty", [None, "", "   ", "\t\n"])
    def test_nothing_in_nothing_out(self, empty: str | None) -> None:
        assert normalize_export_timestamp(empty) is None
