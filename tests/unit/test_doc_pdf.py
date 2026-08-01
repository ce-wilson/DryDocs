"""Tests for drydocs.doc_pdf — the pure helpers (browser discovery, date normalization,
flag construction). The actual headless render (html_to_pdf) shells out to a browser and
is exercised manually / in the L4 run, not in unit tests.
"""

from __future__ import annotations

from drydocs.doc_pdf import find_browser, normalize_pdf_bytes, print_flags


def test_find_browser_prefers_existing(tmp_path) -> None:
    real = tmp_path / "brave.exe"
    real.write_text("x", encoding="utf-8")
    missing = tmp_path / "nope.exe"
    assert find_browser((str(missing), str(real))) == real
    assert find_browser((str(missing),)) is None


def test_normalize_pdf_dates() -> None:
    raw = b"stuff /CreationDate (D:20260708120000+00'00') more /ModDate (D:20260708120005Z) end"
    out = normalize_pdf_bytes(raw)
    assert b"D:20260708120000" not in out and b"D:20260708120005" not in out
    assert out.count(b"D:00000101000000Z") == 2
    # a PDF with no recognizable dates is returned unchanged
    assert normalize_pdf_bytes(b"no dates here") == b"no dates here"


def test_print_flags_are_fixed_and_headless() -> None:
    flags = print_flags("docs/design/x.html", "out.pdf")
    assert any(f.startswith("--headless") for f in flags)
    assert "--no-first-run" in flags
    assert "--no-pdf-header-footer" in flags
    assert any(f.startswith("--print-to-pdf=") for f in flags)
    assert flags[-1].startswith("file://") and flags[-1].endswith("x.html")


def test_print_flags_deterministic() -> None:
    a = print_flags("a.html", "a.pdf")
    b = print_flags("a.html", "a.pdf")
    assert a == b
