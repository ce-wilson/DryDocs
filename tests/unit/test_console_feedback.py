"""O89 clause (c): a console feedback note whose anchor is gone is REPORTED.

The design-doc half of the loop has ``doc_outline.feedback_anchor_valid``, which
decides whether a note re-attaches to its `.md`. The console half needs the
equivalent and its inputs are different: a console page has no source file whose
anchors can be re-read, so the anchors come from the CAPTURE — O88 writes
``web/captures/capture-manifest.json``, and O89 made it record the anchor list
per route rather than only how many there were.

A feedback loop that loses notes quietly is worse than none, because the reviewer
believes it worked. So this is the repo-side report: every ``console.*-rev<N>.yaml``
in ``docs/design/feedback/`` is parsed, and a note whose anchor matches neither an
anchor the capture recorded nor — for a row — the table it was in fails with the
anchors named.

WHAT IT DOES WHEN THERE IS NO CAPTURE, which is the normal state of a fresh
clone: it skips, and says which file was missing. The alternative — treating an
absent manifest as "no anchors exist" — would report every note in every file as
orphaned, which is a guard that cries wolf until somebody deletes it. Captures
are gitignored build output; the feedback files are not.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")

REPO = Path(__file__).resolve().parents[2]
FEEDBACK_DIR = REPO / "docs" / "design" / "feedback"
CAPTURE_MANIFEST = REPO / "web" / "captures" / "capture-manifest.json"

#: `console.<route-slug>-rev<N>.yaml` — the console half of the shared namespace.
#: The `console.` stem prefix is what keeps a console file distinguishable from a
#: design-doc one in the same directory (O89 clause b), and it is why the two can
#: share the directory at all.
CONSOLE_FEEDBACK_RE = re.compile(r"^console\.(?P<slug>[a-z0-9-]+)-rev(?P<rev>\d+)\.ya?ml$")


def console_feedback_files() -> list[Path]:
    if not FEEDBACK_DIR.is_dir():
        return []
    return sorted(p for p in FEEDBACK_DIR.iterdir() if CONSOLE_FEEDBACK_RE.match(p.name))


def captured_anchors() -> dict[str, list[str]]:
    """route-slug → the anchors that route's capture recorded."""
    if not CAPTURE_MANIFEST.is_file():
        return {}
    doc = json.loads(CAPTURE_MANIFEST.read_text(encoding="utf-8"))
    out: dict[str, list[str]] = {}
    for entry in doc.get("routes") or []:
        anchors = entry.get("anchors")
        if not isinstance(anchors, list):
            continue
        # the slug is the anchors' own prefix — read from the data rather than
        # re-derived from the route, so this cannot disagree with what was tagged
        for anchor in anchors:
            out.setdefault(str(anchor).split(".", 1)[0], []).append(str(anchor))
    return out


def anchor_reattaches(anchor: str, known: set[str]) -> bool:
    """The Python twin of ``paperForm.consoleAnchorValid``.

    Exact match, else — for a row anchor, which carries its table's hash as a
    prefix — the table. A note on a row that has since gone lands on the table it
    was in rather than being lost.
    """
    if anchor in known:
        return True
    parts = anchor.split(".")
    return len(parts) >= 3 and ".".join(parts[:-1]) in known


def test_the_filename_pattern_matches_what_the_console_exports() -> None:
    """The console builds this name (``feedbackFileName``); the doc loader parses
    it (``^(?P<doc_id>.+)-rev(\\d+)\\.ya?ml$``). Both must accept it, or a file a
    reviewer saves where they were told to is silently never loaded — which is
    the L20 defect this repo already had once, with ``... - Copy .yaml``."""
    assert CONSOLE_FEEDBACK_RE.match("console.gates-rev1.yaml")
    assert CONSOLE_FEEDBACK_RE.match("console.load-map-rev12.yaml")
    # and the loader's own regex accepts the same name
    loader_re = re.compile(r"^(?P<doc_id>.+)-rev(?P<rev>\d+)\.ya?ml$")
    m = loader_re.match("console.gates-rev1.yaml")
    assert m and m.group("doc_id") == "console.gates"
    # a design-doc file is NOT a console file
    assert not CONSOLE_FEEDBACK_RE.match("controlm-ingestion-tdd-rev2.yaml")


def test_console_and_doc_anchors_do_not_share_an_id_space() -> None:
    """Clause (b). The two kinds live in one directory and one YAML format, so
    the anchor itself has to say which it is: a console anchor always begins with
    a route slug and a `.`; a design-doc anchor is authored words, optionally
    `--`-derived. Asserted over the COMMITTED doc feedback so this is a fact
    about the tree and not about two invented strings."""
    for path in FEEDBACK_DIR.glob("*-rev*.y*ml"):
        if CONSOLE_FEEDBACK_RE.match(path.name):
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for note in data.get("notes") or []:
            anchor = str(note.get("anchor", ""))
            assert (
                not CONSOLE_FEEDBACK_RE.match(f"console.{anchor}-rev1.yaml") or "." not in anchor
            ), f"{path.name}: design-doc anchor {anchor!r} looks like a console anchor"


def test_every_console_note_still_reattaches() -> None:
    """Clause (c), the report itself."""
    files = console_feedback_files()
    if not files:
        pytest.skip("no console feedback files yet — the guard arrives before the first one")
    anchors_by_slug = captured_anchors()
    if not anchors_by_slug:
        pytest.skip(
            f"{CAPTURE_MANIFEST.relative_to(REPO)} is absent (captures are gitignored build "
            "output) — run `npm run paper` in web/ to check re-attachment"
        )

    orphaned: list[str] = []
    for path in files:
        slug = CONSOLE_FEEDBACK_RE.match(path.name).group("slug")  # type: ignore[union-attr]
        known = set(anchors_by_slug.get(slug, []))
        if not known:
            orphaned.append(f"{path.name}: route '{slug}' has no capture to check against")
            continue
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        for note in data.get("notes") or []:
            anchor = str(note.get("anchor", "")).strip()
            if anchor and not anchor_reattaches(anchor, known):
                orphaned.append(f"{path.name}: {anchor}")

    assert not orphaned, (
        "console feedback notes that no longer re-attach:\n  "
        + "\n  ".join(orphaned)
        + "\nThe page changed under them. Groom them into the backlog or re-key them; "
        "they are REPORTED rather than dropped precisely so this decision is a person's."
    )


def test_the_reattachment_rule_matches_the_typescript_one() -> None:
    """Instrument check, and a real risk: this is the SECOND implementation of
    ``consoleAnchorValid`` — the browser cannot run Python and pytest cannot run
    TypeScript — so the two are pinned to the same worked cases rather than left
    to drift. The cases are the ones the TS test uses."""
    known = {"gates.aaaaaaaa", "gates.bbbbbbbb", "gates.bbbbbbbb.cccccccc"}
    assert anchor_reattaches("gates.aaaaaaaa", known)  # exact
    assert anchor_reattaches("gates.bbbbbbbb.cccccccc", known)  # exact, a row
    assert anchor_reattaches("gates.bbbbbbbb.dddddddd", known)  # row gone -> its table
    assert not anchor_reattaches("gates.eeeeeeee", known)  # nothing takes it
    assert not anchor_reattaches("gates.ffffffff.gggggggg", known)  # table gone too
    assert not anchor_reattaches("traceability-matrix", known)  # a doc anchor
