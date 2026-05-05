"""Smoke test the namespaces helper."""
from __future__ import annotations

import pytest

from drydocs.ontology.namespaces import NAMESPACES, expand


def test_required_prefixes_present() -> None:
    for prefix in ["dcat", "prov", "dqv", "org", "swo", "obi", "dprod"]:
        assert prefix in NAMESPACES, f"missing prefix: {prefix}"


def test_expand_basic() -> None:
    assert expand("dcat:Dataset") == "http://www.w3.org/ns/dcat#Dataset"
    assert expand("prov:Activity") == "http://www.w3.org/ns/prov#Activity"


def test_expand_unknown_prefix() -> None:
    with pytest.raises(KeyError):
        expand("nope:foo")


def test_expand_not_a_curie() -> None:
    with pytest.raises(ValueError):
        expand("Dataset")
