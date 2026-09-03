"""O88 guard: the console's print sheet carries the design-doc renderer's L6 gutter
idiom VERBATIM — the ``.dd-margin-tag`` and ``.dd-print-footer`` rules in
``web/src/styles/print.css`` equal the ones in ``drydocs.docgen.design_doc``.

Clause (c) of the item: the console had no print CSS at all, so the print sheet is
new work, but the gutter convention it carries is not and must not be reinvented in
a second idiom. The repo's way of saying that is a drift guard, not a comment: the
Python constant is the importable object (J37), and the ``.css`` file is the artifact
under test, read as CSS rather than as prose.
"""

from __future__ import annotations

import re
from pathlib import Path

from drydocs.docgen.design_doc import _PRINT_MEDIA_CSS

REPO = Path(__file__).resolve().parents[2]
PRINT_CSS = REPO / "web" / "src" / "styles" / "print.css"
INDEX_CSS = REPO / "web" / "src" / "index.css"

SHARED_CLASSES = (".dd-margin-tag", ".dd-print-footer")


def _sans_comments(css: str) -> str:
    """CSS with its comments removed — the sheet's own prose explains the idiom and
    names the classes and ``@media print``, and a guard reads the rules, not the prose
    around them (J66)."""
    return re.sub(r"/\*.*?\*/", "", css, flags=re.S)


def _rule_block(css: str, selector: str) -> str:
    """The declaration block of the FIRST rule whose selector list is EXACTLY
    ``selector`` (anchored at a rule boundary, so ``.a, .b { }`` is not the ``.b``
    rule) — whitespace-normalised so formatting cannot fake a drift."""
    m = re.search(r"(?:^|[}{;])\s*" + re.escape(selector) + r"\s*\{([^}]*)\}", _sans_comments(css))
    assert m, f"{selector} rule not found"
    return re.sub(r"\s+", " ", m.group(1)).strip()


def _console_css() -> str:
    return _sans_comments(PRINT_CSS.read_text(encoding="utf-8"))


def test_console_print_sheet_exists_and_is_imported_by_the_app() -> None:
    assert PRINT_CSS.is_file()
    assert "./styles/print.css" in INDEX_CSS.read_text(
        encoding="utf-8"
    ), "index.css must import the print sheet, or the captured page carries no gutter"


def test_gutter_and_footer_rules_match_the_design_doc_renderer_verbatim() -> None:
    console = _console_css()
    for selector in SHARED_CLASSES:
        assert _rule_block(console, selector) == _rule_block(_PRINT_MEDIA_CSS, selector), (
            f"{selector}: the console print sheet drifted from design_doc._PRINT_MEDIA_CSS — "
            "one idiom, copied verbatim (O88 clause c)"
        )


def test_shared_classes_are_hidden_on_screen() -> None:
    """The tags and the footer exist for paper only: on screen the sheet hides them, and
    the hide line precedes the print block exactly as design_doc's screen sheet does
    (there the line lives in the screen constant, not in _PRINT_MEDIA_CSS)."""
    console = _console_css()
    screen_rule = re.search(
        r"\.dd-margin-tag,\s*\.dd-print-footer\s*\{\s*display:\s*none;?\s*\}", console
    )
    assert screen_rule, "print.css must hide .dd-margin-tag/.dd-print-footer outside @media print"
    assert screen_rule.start() < console.index(
        "@media print"
    ), "the screen-side display:none must precede the @media print block, as in design_doc"


def test_every_print_rule_sits_inside_the_media_block() -> None:
    """TC-SHELL-01's lesson in the other direction: an unlayered broad selector beats
    Tailwind's layered utilities. On paper that is what we want; on screen it would
    silently reflow the console. So apart from the screen-side hide line and @page,
    nothing in print.css may sit outside ``@media print { ... }``."""
    console = _console_css()
    head = console[: console.index("@media print")]
    stripped = re.sub(r"\.dd-margin-tag,\s*\.dd-print-footer\s*\{[^}]*\}", "", head)
    stripped = re.sub(r"@page\s*\{[^}]*\}", "", stripped)
    assert not stripped.strip(), f"rules outside @media print: {stripped.strip()[:120]!r}"
    # and nothing after the block's closing brace either
    depth, end = 0, None
    for i, ch in enumerate(
        console[console.index("@media print") :], start=console.index("@media print")
    ):
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                end = i
                break
    assert end is not None and not console[end + 1 :].strip(), "rules after the @media print block"
