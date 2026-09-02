"""SME review-page renderer (``drydocs-review`` component).

Turns live-graph rows into a **self-contained SME review HTML page**: one section per
DATA label, the source provenance on the section header, and one clean node card per
row with ``hidden_props`` stripped.

**No Neo4j in this module** — the CLI (or a script) fetches rows and hands them in as
``{label: [node_props, ...]}``, so rendering is pure and offline. The optional
:class:`drydocs.review.review_labels.ReviewLabels` backbone supplies section order + provenance.

classification: Internal-Public — the renderer is generic. A *rendered page* inherits
the classification of the graph rows fed to it (real graph data is Internal+); such
pages are written to a gitignored output dir, never committed.
"""

from __future__ import annotations

import html
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

# Props never shown on a review card: private keys (``_*``) plus bookkeeping columns
# that add noise without helping an SME judge correctness.
DEFAULT_HIDDEN_PROPS: frozenset[str] = frozenset(
    {"version_serial", "is_current_version", "ingested_at", "load_id"}
)


def _is_hidden(key: str, hidden: frozenset[str]) -> bool:
    return key.startswith("_") or key in hidden


def group_rows(
    rows: Iterable[Mapping[str, Any]], label_key: str = "_label"
) -> dict[str, list[dict[str, Any]]]:
    """Group a flat row stream into ``{label: [props_without_label_key, ...]}``."""
    grouped: dict[str, list[dict[str, Any]]] = {}
    for row in rows:
        label = str(row.get(label_key, "Unlabeled"))
        props = {k: v for k, v in row.items() if k != label_key}
        grouped.setdefault(label, []).append(props)
    return grouped


def _ordered_labels(rows_by_label: Mapping[str, Any], review_labels: Any | None) -> list[str]:
    if review_labels is None:
        return list(rows_by_label)
    backbone = [lbl for lbl in review_labels.all_labels() if lbl in rows_by_label]
    extra = [
        lbl for lbl in rows_by_label if lbl not in backbone
    ]  # present in rows, not in backbone
    return backbone + extra


def _provenance_for(label: str, review_labels: Any | None) -> str:
    if review_labels is None:
        return ""
    srcs = review_labels.sources_for_label(label)
    if not srcs:
        return ""
    return "; ".join(f"{s.id} — {s.provenance}" if s.provenance else s.id for s in srcs)


def _render_card(props: Mapping[str, Any], hidden: frozenset[str]) -> str:
    rows = [
        f'    <div class="kv"><span class="k">{html.escape(str(k))}</span>'
        f'<span class="v">{html.escape("" if v is None else str(v))}</span></div>'
        for k, v in props.items()
        if not _is_hidden(k, hidden)
    ]
    body = "\n".join(rows) if rows else '    <div class="kv empty">(no visible properties)</div>'
    return '  <div class="card">\n' + body + "\n  </div>"


_CSS = """
body{font-family:system-ui,sans-serif;margin:2rem;color:#1a1a1a}
h1{font-size:1.4rem} h2{font-size:1.1rem;margin-top:2rem;border-bottom:1px solid #ddd}
.prov{color:#666;font-size:.85rem;font-weight:normal}
.card{border:1px solid #e2e2e2;border-radius:6px;padding:.6rem .8rem;margin:.5rem 0;background:#fafafa}
.kv{display:flex;gap:.5rem} .k{font-weight:600;min-width:12rem} .v{font-family:ui-monospace,monospace}
.empty{color:#999}
""".strip()


def render_review(
    rows_by_label: Mapping[str, Sequence[Mapping[str, Any]]],
    *,
    review_labels: Any | None = None,
    hidden_props: Iterable[str] = DEFAULT_HIDDEN_PROPS,
    title: str = "DryDocs — SME graph review",
) -> str:
    """Render a self-contained review page. Pure — no graph access.

    ``rows_by_label`` maps each DATA label to its node-property dicts (use
    :func:`group_rows` for a flat stream). ``review_labels`` (optional) orders the
    sections by the review backbone and adds source provenance to each header.
    """
    hidden = frozenset(hidden_props)
    sections: list[str] = []
    for label in _ordered_labels(rows_by_label, review_labels):
        nodes = rows_by_label.get(label) or []
        prov = _provenance_for(label, review_labels)
        header = f'<h2>{html.escape(label)} <span class="prov">({len(nodes)})</span>'
        if prov:
            header += f'<br><span class="prov">{html.escape(prov)}</span>'
        header += "</h2>"
        cards = (
            "\n".join(_render_card(n, hidden) for n in nodes) or "  <p class='empty'>(no rows)</p>"
        )
        sections.append(header + "\n" + cards)

    return (
        "<!doctype html>\n<html><head><meta charset='utf-8'>\n"
        f"<title>{html.escape(title)}</title>\n<style>{_CSS}</style>\n</head><body>\n"
        f"<h1>{html.escape(title)}</h1>\n" + "\n".join(sections) + "\n</body></html>\n"
    )
