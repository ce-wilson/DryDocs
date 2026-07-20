"""J8 — skip-guard policy: tests reading gitignored local assets must SKIP, not fail.

The exact failure a prior port hit: a test referenced a local-only file under the
gitignored ``drydocs/data/`` tree, the consumer cloned without it, and the suite died
with FileNotFoundError instead of a skip (the guard had been lost in a merge). This
policy test makes that loss loud: any tests/unit file that references
``drydocs/data/`` or ``internal-local/`` must carry a skip guard
(``skipif`` / ``importorskip`` / ``pytest.skip``).

Scope notes (kept deliberately simple, per docs/reviews/tech-debt-port-boundary.md
Phase 4 / Class E):

* Literals containing glob characters (``drydocs/data/**``) are manifest/pattern rows,
  not filesystem reads — excluded.
* Segment-chained construction (``... / "drydocs" / "data" / "samples" / ...``) is
  matched too — that is how the variable-stream tests build their sample path.
* The guard requirement is file-level: one guard marker per referencing file. That is
  the granularity the port failure had, and finer analysis would need real dataflow.
"""
from __future__ import annotations

import re
from pathlib import Path

TESTS_DIR = Path(__file__).resolve().parent

_GUARD_RE = re.compile(r"skipif|importorskip|pytest\.skip")
# concrete path literal touching either gitignored tree (either slash direction)
_LITERAL_RE = re.compile(
    r"""["']([^"'\n]*(?:drydocs[/\\]data[/\\]|internal-local[/\\])[^"'\n]*)["']"""
)
# Path-segment chains: "drydocs" / "data" or "data" / "samples"
_SEGMENT_RE = re.compile(
    r"""["']drydocs["']\s*/\s*["']data["']|["']data["']\s*/\s*["']samples["']"""
)
_GLOB_CHARS = set("*?[")


def _references_local_assets(text: str) -> bool:
    for m in _LITERAL_RE.finditer(text):
        if not _GLOB_CHARS.intersection(m.group(1)):
            return True
    return bool(_SEGMENT_RE.search(text))


def _has_guard(text: str) -> bool:
    return bool(_GUARD_RE.search(text))


def test_gitignored_asset_references_carry_a_skip_guard() -> None:
    offenders: list[str] = []
    for path in sorted(TESTS_DIR.glob("*.py")):
        if path.name == Path(__file__).name:
            continue  # this file quotes the patterns it polices
        text = path.read_text(encoding="utf-8")
        if _references_local_assets(text) and not _has_guard(text):
            offenders.append(path.name)
    assert not offenders, (
        "These test files reference gitignored local assets (drydocs/data/ or "
        "internal-local/) without a skipif/importorskip/pytest.skip guard — on a "
        f"fresh clone they FAIL instead of SKIP: {offenders}"
    )


def test_policy_checker_catches_the_port_failure_shape() -> None:
    """The checker itself: unguarded reference -> flagged; guarded / glob / clean -> not."""
    unguarded = 'sample = Path("drydocs/data/samples/x.csv")\nrows = read(sample)\n'
    assert _references_local_assets(unguarded) and not _has_guard(unguarded)

    guarded = unguarded + 'pytest.skip("sample absent")\n'
    assert _has_guard(guarded)

    chained = 'SAMPLE = ROOT / "drydocs" / "data" / "samples" / "y.csv"\n'
    assert _references_local_assets(chained)

    manifest_row = '{"drydocs/data/**": "never-port"}\n'
    assert not _references_local_assets(manifest_row)

    clean = 'FIXTURE = Path("tests/fixtures/lineage/jobs.csv")\n'
    assert not _references_local_assets(clean)
