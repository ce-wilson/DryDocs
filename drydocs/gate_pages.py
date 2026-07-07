"""HITL SME-gate prompt-page generator (``drydocs-review`` component).

Renders a load-step spec into a **self-contained interactive review page**: an SME
ticks confirmations, progress is saved in the browser (localStorage) and restored on
return, and the page states that **no graph write happens until the mapping is
confirmed** in ``config/taxonomy-ontology-map.yaml`` (decisions logged to
``config/gate-log.md``). This is the *renderer* for the gate described in
``docs/restructure/03-hitl-sme-flow.md`` / ``04-sme-checklist-and-load-plan.md``.

Pure/offline — no Neo4j, no graph write. **The repo is the system of record; the browser
ticks are a working aid.** classification: Internal-Public — the generator is generic and
the committed example spec is a vendor-BMC step. Pages for real PAT/SEAL steps are
Internal-Confidential (real LoB/SEAL data) and render into a gitignored dir, never here.
"""
from __future__ import annotations

import html
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_GATE_PROMPTS_DIR = _REPO_ROOT / "config" / "gate-prompts"


class GateSpecError(RuntimeError):
    """A gate-prompt spec file is malformed."""


@dataclass(frozen=True)
class Section:
    title: str
    confirmations: tuple[str, ...]


@dataclass(frozen=True)
class MappingRow:
    n: Any
    element: str
    target: str
    edge: str = ""


@dataclass(frozen=True)
class PropRow:
    """One node property with its provenance: straight from a source column, or derived."""

    name: str
    origin: str          # "source" | "derived"
    source: str          # column name, or the derivation rule
    note: str = ""


@dataclass(frozen=True)
class ProvenanceBlock:
    """Per-label property inventory — the source-vs-inferred split the SME reviews."""

    label: str
    source_object: str = ""
    key: str = ""
    loader: str = ""
    properties: tuple[PropRow, ...] = ()


@dataclass(frozen=True)
class GateSpec:
    id: str
    title: str
    step: str = ""
    classification: str = "Internal-Public"
    summary: str = ""
    meta: tuple[tuple[str, str], ...] = ()          # header card rows (Module, Source, Registry ref, …)
    sections: tuple[Section, ...] = ()
    mapping: tuple[MappingRow, ...] = ()
    provenance: tuple[ProvenanceBlock, ...] = ()

    @property
    def total_confirmations(self) -> int:
        return sum(len(s.confirmations) for s in self.sections)


def load_gate_spec(path: str | Path) -> GateSpec:
    """Parse a gate-prompt spec. Pure — no graph access."""
    path = Path(path)
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return spec_from_dict(doc, default_id=path.stem)


def spec_from_dict(doc: dict[str, Any], default_id: str = "gate") -> GateSpec:
    if not doc.get("title"):
        raise GateSpecError("gate spec must have a `title`")
    sections: list[Section] = []
    for raw in doc.get("sections") or []:
        title = raw.get("title")
        confs = raw.get("confirmations") or []
        if not title or not isinstance(confs, list):
            raise GateSpecError(f"section needs a `title` and a `confirmations` list: {raw!r}")
        sections.append(Section(title=title, confirmations=tuple(str(c) for c in confs)))
    mapping = tuple(
        MappingRow(
            n=r.get("n", ""),
            element=str(r.get("element", "")),
            target=str(r.get("target", "")),
            edge=str(r.get("edge", "")),
        )
        for r in (doc.get("mapping") or [])
    )
    meta = tuple((str(k), str(v)) for k, v in (doc.get("meta") or {}).items())
    provenance: list[ProvenanceBlock] = []
    for raw in doc.get("provenance") or []:
        props = []
        for p in raw.get("properties") or []:
            origin = str(p.get("origin", "source"))
            if origin not in ("source", "derived"):
                raise GateSpecError(f"property origin must be 'source' or 'derived': {p!r}")
            props.append(PropRow(
                name=str(p.get("name", "")),
                origin=origin,
                source=str(p.get("from", "")),
                note=str(p.get("note", "")),
            ))
        provenance.append(ProvenanceBlock(
            label=str(raw.get("label", "")),
            source_object=str(raw.get("source_object", "")),
            key=str(raw.get("key", "")),
            loader=str(raw.get("loader", "")),
            properties=tuple(props),
        ))
    return GateSpec(
        id=str(doc.get("id", default_id)),
        title=str(doc["title"]),
        step=str(doc.get("step", "")),
        classification=str(doc.get("classification", "Internal-Public")),
        summary=str(doc.get("summary", "")),
        meta=meta,
        sections=tuple(sections),
        mapping=mapping,
        provenance=tuple(provenance),
    )


_CSS = """
body{font-family:system-ui,sans-serif;margin:2rem;max-width:52rem;color:#1a1a1a}
.badge{display:inline-block;padding:.1rem .5rem;border-radius:4px;background:#fde68a;font-size:.8rem}
.banner{background:#eff6ff;border:1px solid #bfdbfe;padding:.6rem .8rem;border-radius:6px;margin:1rem 0}
.progress{height:.5rem;background:#e5e7eb;border-radius:4px;overflow:hidden;margin:.4rem 0}
#bar{height:100%;width:0;background:#2563eb;transition:width .2s}
h2{font-size:1.05rem;margin-top:1.6rem} label{display:block;padding:.25rem 0;cursor:pointer}
table{border-collapse:collapse;width:100%;margin:.5rem 0} th,td{border:1px solid #e2e2e2;padding:.3rem .5rem;text-align:left;font-size:.9rem}
code{font-family:ui-monospace,monospace;background:#f3f4f6;padding:0 .2rem}
.meta{border:1px solid #e2e2e2;border-radius:8px;padding:.6rem 1rem;margin:1rem 0}
.meta table{margin:0} .meta td{border:none;padding:.2rem .6rem} .meta td:first-child{color:#6b7280;white-space:nowrap}
.blockhead{color:#6b7280;font-size:.85rem;font-weight:normal}
.origin{display:inline-block;padding:0 .45rem;border-radius:4px;font-size:.75rem;font-weight:600}
.origin-source{background:#dcfce7;color:#166534}
.origin-derived{background:#fef3c7;color:#92400e}
""".strip()


def _checkbox(cid: str, text: str) -> str:
    return f'    <label><input type="checkbox" id="{cid}"> {html.escape(text)}</label>'


def render_gate_page(spec: GateSpec) -> str:
    """Render a self-contained interactive gate page. Pure — no graph access."""
    parts: list[str] = []

    if spec.meta:
        rows = "\n".join(
            f"      <tr><td>{html.escape(k)}</td><td>{html.escape(v)}</td></tr>" for k, v in spec.meta
        )
        parts.append(f"<div class='meta'><table><tbody>\n{rows}\n    </tbody></table></div>")

    if spec.mapping:
        rows = "\n".join(
            f"      <tr><td>{html.escape(str(m.n))}</td><td>{html.escape(m.element)}</td>"
            f"<td><code>{html.escape(m.target)}</code></td><td><code>{html.escape(m.edge)}</code></td></tr>"
            for m in spec.mapping
        )
        parts.append(
            "<h2>Overview — source &#8594; graph (mini-ER)</h2>\n"
            "    <table><thead><tr><th>#</th><th>Source element</th><th>Graph target</th><th>Edge</th></tr></thead>\n"
            f"    <tbody>\n{rows}\n    </tbody></table>"
        )

    if spec.provenance:
        prov_parts: list[str] = ["<h2>Property provenance — source vs inferred</h2>"]
        for block in spec.provenance:
            head_bits = " &middot; ".join(
                html.escape(b) for b in (block.source_object, block.key, block.loader) if b
            )
            prov_parts.append(
                f"<h3>{html.escape(block.label)}"
                + (f" <span class='blockhead'>{head_bits}</span>" if head_bits else "")
                + "</h3>"
            )
            rows = "\n".join(
                f"      <tr><td><code>{html.escape(p.name)}</code></td>"
                f"<td><span class='origin origin-{p.origin}'>{p.origin.upper()}</span></td>"
                f"<td><code>{html.escape(p.source)}</code></td>"
                f"<td>{html.escape(p.note)}</td></tr>"
                for p in block.properties
            )
            prov_parts.append(
                "<table><thead><tr><th>property</th><th>origin</th>"
                "<th>from (column / rule)</th><th>note</th></tr></thead>\n"
                f"    <tbody>\n{rows}\n    </tbody></table>"
            )
        parts.append("\n".join(prov_parts))

    for si, section in enumerate(spec.sections):
        boxes = "\n".join(
            _checkbox(f"c{si}_{ci}", conf) for ci, conf in enumerate(section.confirmations)
        )
        parts.append(f'<h2>{html.escape(section.title)}</h2>\n{boxes}')

    js = f"""
const KEY = "drydocs-gate:" + {json.dumps(spec.id)};
function boxes() {{ return document.querySelectorAll('input[type=checkbox]'); }}
function update() {{
  const all = boxes(); const n = [...all].filter(c => c.checked).length;
  document.getElementById('count').textContent = n + ' / ' + all.length;
  document.getElementById('bar').style.width = (all.length ? 100 * n / all.length : 0) + '%';
}}
function save() {{
  const s = {{}}; boxes().forEach(c => s[c.id] = c.checked);
  localStorage.setItem(KEY, JSON.stringify(s)); update();
}}
function restore() {{
  const s = JSON.parse(localStorage.getItem(KEY) || '{{}}');
  boxes().forEach(c => {{ if (s[c.id]) c.checked = true; }}); update();
}}
document.addEventListener('DOMContentLoaded', () => {{
  boxes().forEach(c => c.addEventListener('change', save)); restore();
}});
""".strip()

    return (
        "<!doctype html>\n<html><head><meta charset='utf-8'>\n"
        f"<title>{html.escape(spec.title)}</title>\n<style>{_CSS}</style>\n</head><body>\n"
        f"<h1>{html.escape(spec.title)}</h1>\n"
        f"<p>{html.escape(spec.step)} &middot; <span class='badge'>CLASSIFICATION: {html.escape(spec.classification)}</span></p>\n"
        "<div class='banner'><strong>Interactive review page.</strong> Tick each confirmation as you "
        "review — progress is saved in your browser. <strong>No graph write</strong> happens until the "
        "mappings are <code>confirmed</code> in <code>config/taxonomy-ontology-map.yaml</code>; decisions "
        "are logged to <code>config/gate-log.md</code>. The browser ticks are a working aid, not the "
        "system of record — the repo remains the single source of truth.</div>\n"
        f"<p><strong id='count'>0 / {spec.total_confirmations}</strong> confirmations checked</p>\n"
        "<div class='progress'><div id='bar'></div></div>\n"
        + (f"<p>{html.escape(spec.summary)}</p>\n" if spec.summary else "")
        + "\n".join(parts)
        + f"\n<script>\n{js}\n</script>\n</body></html>\n"
    )
