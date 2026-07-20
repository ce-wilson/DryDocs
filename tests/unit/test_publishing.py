"""Unit tests for the publishing pipeline (drydocs/publishing/) — offline, no Neo4j."""
from __future__ import annotations

from drydocs.publishing import (
    DEFAULT_ALLOWED_MACROS,
    LocalPublisher,
    NoopPublisher,
    Publisher,
    assemble,
    validate,
    validate_macros,
    validate_xml,
    write_preview,
)


# ---- assembler ------------------------------------------------------------
def test_assemble_joins_and_wraps() -> None:
    out = assemble(["<p>a</p>", "", "  <p>b</p>  "])
    assert "<p>a</p>" in out and "<p>b</p>" in out
    assert out.startswith('<div class="drydocs-doc">')


def test_assemble_requires_body_placeholder() -> None:
    import pytest

    with pytest.raises(ValueError):
        assemble(["<p>x</p>"], template="<div>no placeholder</div>")


# ---- validator ------------------------------------------------------------
def test_wellformed_passes() -> None:
    assert validate_xml("<p>hello <strong>world</strong></p>") == []


def test_malformed_fails() -> None:
    errs = validate_xml("<p>unclosed")
    assert errs and "well-formed" in errs[0]


def test_allowed_macro_passes() -> None:
    frag = '<ac:structured-macro ac:name="info"><ac:rich-text-body>hi</ac:rich-text-body></ac:structured-macro>'
    assert validate_macros(frag) == []


def test_disallowed_macro_rejected() -> None:
    frag = '<ac:structured-macro ac:name="html"><ac:plain-text-body>evil</ac:plain-text-body></ac:structured-macro>'
    errs = validate_macros(frag)
    assert errs and "html" in errs[0]
    assert "html" not in DEFAULT_ALLOWED_MACROS


def test_validate_combines_checks() -> None:
    assert validate('<ac:structured-macro ac:name="note">ok</ac:structured-macro>') == []
    assert validate("<p>unclosed") != []


# ---- preview + publishers -------------------------------------------------
def test_write_preview_creates_file(tmp_path) -> None:
    p = write_preview("<html>x</html>", tmp_path / "sub" / "page.html")
    assert p.exists() and p.read_text(encoding="utf-8") == "<html>x</html>"


def test_noop_publisher_records_without_sending() -> None:
    pub = NoopPublisher()
    assert isinstance(pub, Publisher)
    res = pub.publish(title="My Page", body="<p>x</p>", space="DEMO")
    assert res.published is False
    assert pub.sent == [res]


def test_local_publisher_writes_file(tmp_path) -> None:
    pub = LocalPublisher(out_dir=tmp_path)
    res = pub.publish(title="My Page", body="<p>x</p>")
    assert res.published is True
    assert (tmp_path / "My_Page.html").exists()
