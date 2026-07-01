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
class GateSpec:
    id: str
    title: str
    step: str = ""
    classification: str = "Internal-Public"
    summary: str = ""
    sections: tuple[Section, ...] = ()
    mapping: tuple[MappingRow, ...] = ()

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
    return GateSpec(
        id=str(doc.get("id", default_id)),
        title=str(doc["title"]),
        step=str(doc.get("step", "")),
        classification=str(doc.get("classification", "Internal-Public")),
        summary=str(doc.get("summary", "")),
        sections=tuple(sections),
        mapping=mapping,
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
""".strip()


def _checkbox(cid: str, text: str) -> str:
    return f'    <label><input type="checkbox" id="{cid}"> {html.escape(text)}</label>'


def render_gate_page(spec: GateSpec) -> str:
    """Render a self-contained interactive gate page. Pure — no graph access."""
    parts: list[str] = []
    for si, section in enumerate(spec.sections):
        boxes = "\n".join(
            _checkbox(f"c{si}_{ci}", conf) for ci, conf in enumerate(section.confirmations)
        )
        parts.append(f'<h2>{html.escape(section.title)}</h2>\n{boxes}')

    if spec.mapping:
        rows = "\n".join(
            f"      <tr><td>{html.escape(str(m.n))}</td><td>{html.escape(m.element)}</td>"
            f"<td><code>{html.escape(m.target)}</code></td><td><code>{html.escape(m.edge)}</code></td></tr>"
            for m in spec.mapping
        )
        parts.append(
            "<h2>Taxonomy → ontology mapping</h2>\n"
            "    <table><thead><tr><th>#</th><th>Element</th><th>Ontology target</th><th>Edge</th></tr></thead>\n"
            f"    <tbody>\n{rows}\n    </tbody></table>"
        )

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
