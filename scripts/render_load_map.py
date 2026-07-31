"""Generate the N4/N5 load map — ONE surface joining sources, loaders,
commands, order, column ledgers, taxonomy captures and ontology mappings.

Joins the N3 declarations (BaseLoader.source_id, cli.COMMAND_LOADERS,
cli.CANONICAL_LOAD_SEQUENCE) to config/source-registry.yaml, the
config/source-mappings/ column ledgers (via each entry's ``locator.mapping``
pointer), the config/taxonomy/ captures (their top-level ``source:`` key) and
config/taxonomy-ontology-map.yaml, and emits
``web/src/generated/load-map.json``. ``tests/unit/test_load_map_json.py`` is
the drift guard; a default-paths ``render_board.py`` run refreshes this file
alongside the board, gates.json and the enforcement matrix (J17/J20 — one
entry point, no stale renders).

Ledger coverage renders in the THREE states governance already defines (N2),
never omitted:
- ``ledger``      — the entry carries a ``locator.mapping`` column ledger;
- ``pending``     — confirmed but no ledger yet (the frozen shrink-only
                    LEDGER_PENDING set, enforced by test_source_mapping_drift);
- ``placeholder`` — not yet SME-confirmed.
A source silently absent from the render is a defect (guarded).

N5 — the HUMAN surface: the same data also renders to
``docs/plan/load-map.html`` (screen + ``@media print``, the board.html house
style). PLACEMENT DECISION (the N5 item's real content, recorded here):
docs/plan/ is the committed generated-surface home — board.html is the
precedent — so the page lives beside it; docs/design/ was rejected because
that tree's contract is hand-authored .md validated against outline
templates, and a generated file there would break both the contract and
test_doc_outline.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

REGISTRY = REPO / "config" / "source-registry.yaml"
DOC_REGISTRY = REPO / "config" / "doc-source-registry.yaml"
TAXONOMY_DIR = REPO / "config" / "taxonomy"
MAP_FILE = REPO / "config" / "taxonomy-ontology-map.yaml"
OUT = REPO / "web" / "src" / "generated" / "load-map.json"
OUT_HTML = REPO / "docs" / "plan" / "load-map.html"


def _ledger_state(entry: dict) -> dict:
    mapping = (entry.get("locator") or {}).get("mapping")
    if mapping:
        return {"state": "ledger", "path": mapping}
    if entry.get("confirmed"):
        return {"state": "pending", "path": None}
    return {"state": "placeholder", "path": None}


def _derived_urn(entry: dict) -> str:
    """D3 — same derivation as drydocs_core.source_registry.Source.urn."""
    carrier = entry.get("system") or entry["id"]
    artifact = entry.get("artifact") or entry["id"]
    return f"urn:drydocs:dataset:({carrier},{artifact},prod)".lower()


def build_load_map() -> dict:
    from drydocs import cli  # deferred: scripts/ runs outside the package

    registry_doc = yaml.safe_load(REGISTRY.read_text(encoding="utf-8"))
    system_entries = registry_doc.get("systems", [])
    dataset_entries = registry_doc.get("datasets", [])
    retired_entries = registry_doc.get("retired", [])
    doc_entries = yaml.safe_load(DOC_REGISTRY.read_text(encoding="utf-8"))["sources"]
    map_entries = yaml.safe_load(MAP_FILE.read_text(encoding="utf-8"))["mappings"]

    system_by_id = {e["id"]: e for e in system_entries}

    # taxonomy captures, joined by their own top-level `source:` declaration —
    # a capture may name a DATASET id (single-feed) or a SYSTEM id (the
    # hierarchy spans several of the system's datasets).
    captures_by_source: dict[str, list[str]] = {}
    # key= on the string, not the Path — see the note in
    # render_enforcement_matrix.py: sorting Path objects is case-folded on
    # Windows and case-sensitive on POSIX. Benign here today (every capture
    # filename is lowercase) and kept that way on purpose, because the day one
    # is not, this render starts drifting per-OS like the matrix did.
    for path in sorted(TAXONOMY_DIR.glob("*.yaml"), key=lambda p: p.as_posix()):
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        source = doc.get("source") if isinstance(doc, dict) else None
        if source:
            captures_by_source.setdefault(source, []).append(
                path.relative_to(REPO).as_posix()
            )

    # loaders by source_id; cli names + commands reverse-joined
    cli_name_by_class = {cls: nm for nm, cls in cli.LOADER_REGISTRY.items()}
    commands_by_class: dict[type, list[str]] = {}
    for command, classes in sorted(cli.COMMAND_LOADERS.items()):
        for cls in classes:
            commands_by_class.setdefault(cls, []).append(command)

    all_classes = set(cli.LOADER_REGISTRY.values())
    for classes in cli.COMMAND_LOADERS.values():
        all_classes.update(classes)

    def _loader_row(cls: type) -> dict:
        return {
            "name": cls.name,
            "class": cls.__name__,
            "cli_name": cli_name_by_class.get(cls),
            "source_label": cls.source_label,
            "commands": sorted(commands_by_class.get(cls, [])),
        }

    loaders_by_source: dict[str, list[dict]] = {}
    for cls in all_classes:
        if cls.source_id is not None:
            loaders_by_source.setdefault(cls.source_id, []).append(_loader_row(cls))
    for rows in loaders_by_source.values():
        rows.sort(key=lambda r: r["name"])

    # ontology mappings by taxonomy.source (dataset ids; doc-corpus ids valid too)
    mappings_by_source: dict[str, list[dict]] = {}
    unmatched_map_sources: list[dict] = []
    registry_ids = {e["id"] for e in dataset_entries} | {e["id"] for e in doc_entries}
    for m in map_entries:
        source = (m.get("taxonomy") or {}).get("source")
        row = {
            "id": m.get("id"),
            "status": m.get("status"),
            "label": (m.get("ontology") or {}).get("neo4j_label"),
        }
        if source in registry_ids:
            mappings_by_source.setdefault(source, []).append(row)
        else:
            # never silently dropped — a map entry pointing at no registered
            # source is drift worth seeing on the one surface
            unmatched_map_sources.append({**row, "source": source})

    systems: list[dict] = []
    for entry in system_entries:  # registry order — the file's own grouping
        systems.append(
            {
                "id": entry["id"],
                "name": entry.get("name"),
                "layer": entry.get("layer"),
                "classification": entry.get("classification"),
                "taxonomy_captures": captures_by_source.get(entry["id"], []),
            }
        )

    sources: list[dict] = []
    for entry in dataset_entries:  # registry order — the file's own grouping
        sid = entry["id"]
        system = system_by_id.get(entry.get("system"), {})
        sources.append(
            {
                "id": sid,
                "home": "source-registry",
                "system": entry.get("system"),
                "origin": entry.get("origin"),
                "kind": entry.get("artifact_kind"),
                "authority": entry.get("authority"),
                "derived": bool(entry.get("derived")),
                "urn": _derived_urn(entry),
                "replaces": entry.get("replaces"),
                "classification": system.get("classification"),
                "confirmed": bool(entry.get("confirmed")),
                "ledger": _ledger_state(entry),
                "taxonomy_captures": captures_by_source.get(sid, []),
                "ontology_mappings": mappings_by_source.get(sid, []),
                "loaders": loaders_by_source.get(sid, []),
            }
        )
    for entry in doc_entries:  # the doc-ledger union (pipeline twins dropped, N9)
        sid = entry["id"]
        sources.append(
            {
                "id": sid,
                "home": "doc-registry",
                "system": None,
                "origin": None,
                "kind": "doc-corpus",
                "authority": None,
                "derived": False,
                "urn": None,
                "replaces": None,
                "classification": entry.get("classification"),
                "confirmed": bool(entry.get("confirmed")),
                "ledger": _ledger_state(entry),
                "taxonomy_captures": captures_by_source.get(sid, []),
                "ontology_mappings": mappings_by_source.get(sid, []),
                "loaders": loaders_by_source.get(sid, []),
            }
        )

    retired = [
        {
            "id": e["id"],
            "replaced_by": list(e.get("replaced_by") or []),
            "reason": e.get("reason"),
        }
        for e in retired_entries
    ]

    sequence = [
        {
            "command": command,
            "mode": mode,
            "note": note,
            "loaders": [cls.name for cls in cli.COMMAND_LOADERS.get(command, ())],
        }
        for command, mode, note in cli.CANONICAL_LOAD_SEQUENCE
    ]

    sourceless = [
        {
            "name": cls.name,
            "class": cls.__name__,
            "reason": reason,
            "commands": sorted(commands_by_class.get(cls, [])),
        }
        for cls, reason in sorted(
            cli.SOURCELESS_LOADERS.items(), key=lambda kv: kv[0].__name__
        )
    ]

    return {
        "note": (
            "GENERATED by scripts/render_load_map.py -- never hand-edit. "
            "tests/unit/test_load_map_json.py fails when this drifts from the "
            "declarations it joins (N3) or the registries it reads (v2: "
            "systems + datasets + the doc-ledger union + retired ids). One "
            "surface answering taxonomy-by-source, ontology, extract and loads."
        ),
        "sequence": sequence,
        "ad_hoc_commands": sorted(cli.AD_HOC_COMMANDS),
        "systems": systems,
        "sources": sources,
        "retired": retired,
        "sourceless_loaders": sourceless,
        "map_entries_without_registry_source": unmatched_map_sources,
    }


# ---- N5: the human surface (docs/plan/load-map.html) ------------------------

_CSS = """
body{font-family:system-ui,sans-serif;margin:0;padding:1.5rem 2rem 4rem;max-width:80rem;
  margin-left:auto;margin-right:auto;color:#1a1a1a;background:#fff}
h1{font-size:1.4rem;margin:.2rem 0 .1rem}
h2{font-size:1.05rem;margin:1.6rem 0 .4rem;border-bottom:1px solid #e2e2e2;padding-bottom:.2rem}
h3{font-size:.95rem;margin:1rem 0 .3rem;font-family:ui-monospace,monospace}
p.sub{color:#6b7280;font-size:.85rem;margin:.1rem 0 .8rem}
table{border-collapse:collapse;width:100%;font-size:.85rem;margin:.4rem 0}
th{text-align:left;background:#f9fafb;border-bottom:1px solid #e2e2e2;padding:.3rem .5rem;
  font-size:.78rem;text-transform:uppercase;letter-spacing:.03em;color:#374151}
td{border-bottom:1px solid #f0f0f0;padding:.3rem .5rem;vertical-align:top}
code,.mono{font-family:ui-monospace,monospace;font-size:.82rem}
.chip{border-radius:4px;padding:.02rem .4rem;font-size:.72rem;white-space:nowrap}
.mode-standing{background:#bbf7d0;color:#166534}
.mode-optional{background:#e0e7ff;color:#3730a3}
.mode-gated{background:#fde68a;color:#92400e}
.ledger-ledger{background:#bbf7d0;color:#166534}
.ledger-pending{background:#fde68a;color:#92400e}
.ledger-placeholder{background:#e5e7eb;color:#374151}
.st-applied{background:#bbf7d0;color:#166534}
.st-confirmed{background:#a7f3d0;color:#065f46}
.st-proposed{background:#e0e7ff;color:#3730a3}
.st-planned{background:#e5e7eb;color:#374151}
.st-rejected{background:#fecaca;color:#991b1b}
.st-other{background:#e5e7eb;color:#374151}
ul.tight{margin:.2rem 0 .2rem 1.1rem;padding:0}
ul.tight li{margin:.1rem 0}
.muted{color:#9ca3af}
.warn{background:#fef3c7;border:1px solid #fde68a;border-radius:6px;padding:.5rem .7rem;
  font-size:.85rem}
@media print{
  body{padding:0;max-width:none;font-size:10pt}
  h2{break-after:avoid}
  table{font-size:8.5pt}
  tr,li{break-inside:avoid}
  .chip{border:1px solid #999;background:#fff!important;color:#000!important}
}
"""


def _esc(text: object) -> str:
    import html

    return html.escape(str(text)) if text is not None else ""


def _status_chip(status: object) -> str:
    known = {"applied", "confirmed", "proposed", "planned", "rejected"}
    cls = f"st-{status}" if status in known else "st-other"
    return f'<span class="chip {cls}">{_esc(status)}</span>'


def build_load_map_html(data: dict) -> str:
    out: list[str] = []
    add = out.append
    n_ledger = sum(1 for s in data["sources"] if s["ledger"]["state"] == "ledger")
    n_pending = sum(1 for s in data["sources"] if s["ledger"]["state"] == "pending")
    n_placeholder = len(data["sources"]) - n_ledger - n_pending

    add("<!DOCTYPE html>\n<html lang=\"en\"><head><meta charset=\"utf-8\">")
    add('<meta name="viewport" content="width=device-width, initial-scale=1">')
    add("<title>DryDocs — Load Map</title>")
    add(f"<style>{_CSS}</style></head><body>")
    add("<h1>DryDocs — Load Map</h1>")
    add(
        '<p class="sub">GENERATED by scripts/render_load_map.py from the N3 '
        "declarations + config/source-registry.yaml (v2: systems/datasets/"
        "retired) + config/doc-source-registry.yaml + config/source-mappings/ + "
        "config/taxonomy/ + config/taxonomy-ontology-map.yaml — never hand-edit. "
        f"{len(data['systems'])} systems · {len(data['sources'])} datasets "
        f"({n_ledger} with column ledgers, "
        f"{n_pending} ledger-pending, {n_placeholder} placeholders) · "
        f"{len(data['retired'])} retired ids · "
        f"{len(data['sequence'])} sequence steps.</p>"
    )

    # -- the canonical sequence -----------------------------------------------
    add("<h2>Canonical load sequence</h2>")
    add(
        '<p class="sub">Declared ONCE in drydocs/cli.py (CANONICAL_LOAD_SEQUENCE); '
        "ingest.sh and the startup/refresh runbook derive from it (N6).</p>"
    )
    add("<table><tr><th>#</th><th>command</th><th>mode</th><th>loaders</th><th>note</th></tr>")
    for i, step in enumerate(data["sequence"], 1):
        loaders = (
            ", ".join(f"<code>{_esc(n)}</code>" for n in step["loaders"])
            or '<span class="muted">—</span>'
        )
        add(
            f"<tr><td>{i}</td><td><code>drydocs {_esc(step['command'])}</code></td>"
            f'<td><span class="chip mode-{_esc(step["mode"])}">{_esc(step["mode"])}</span></td>'
            f"<td>{loaders}</td><td>{_esc(step['note'])}</td></tr>"
        )
    add("</table>")
    ad_hoc = ", ".join(f"<code>drydocs {_esc(c)}</code>" for c in data["ad_hoc_commands"])
    add(
        f'<p class="sub">Operator-driven (not sequence members): {ad_hoc}.</p>'
    )

    # -- systems (v2) ----------------------------------------------------------
    add("<h2>Systems — the things we connect to (v2)</h2>")
    add(
        '<p class="sub">SYSTEM rows carry connection/locator/classification; '
        "DATASET rows below carry the gate state. A taxonomy capture may join "
        "at either level (system when the hierarchy spans several datasets).</p>"
    )
    add(
        "<table><tr><th>system</th><th>name</th><th>layer</th>"
        "<th>classification</th><th>taxonomy captures</th></tr>"
    )
    for sysrow in data["systems"]:
        captures = (
            "<br>".join(f"<code>{_esc(c)}</code>" for c in sysrow["taxonomy_captures"])
            or '<span class="muted">—</span>'
        )
        add(
            f"<tr><td><code>{_esc(sysrow['id'])}</code></td>"
            f"<td>{_esc(sysrow['name'])}</td><td>{_esc(sysrow['layer'])}</td>"
            f"<td>{_esc(sysrow['classification'])}</td><td>{captures}</td></tr>"
        )
    add("</table>")

    # -- dataset summary -------------------------------------------------------
    add("<h2>Datasets — taxonomy · ontology · extract · load</h2>")
    add(
        "<table><tr><th>dataset</th><th>system</th><th>origin</th><th>kind</th>"
        "<th>authority</th><th>classification</th>"
        "<th>confirmed</th><th>column ledger</th><th>taxonomy</th>"
        "<th>ontology mappings</th><th>loaders</th></tr>"
    )
    for s in data["sources"]:
        ledger = s["ledger"]
        ledger_cell = (
            f'<span class="chip ledger-{ledger["state"]}">{ledger["state"]}</span>'
        )
        if ledger["path"]:
            ledger_cell += f'<br><code>{_esc(ledger["path"])}</code>'
        captures = (
            "<br>".join(f"<code>{_esc(c)}</code>" for c in s["taxonomy_captures"])
            or '<span class="muted">—</span>'
        )
        by_status: dict[str, int] = {}
        for m in s["ontology_mappings"]:
            by_status[m["status"]] = by_status.get(m["status"], 0) + 1
        mappings = (
            " ".join(
                f"{_status_chip(st)}&thinsp;{n}" for st, n in sorted(by_status.items())
            )
            or '<span class="muted">—</span>'
        )
        loaders = (
            "<br>".join(f"<code>{_esc(loader['name'])}</code>" for loader in s["loaders"])
            or '<span class="muted">—</span>'
        )
        confirmed = "✓" if s["confirmed"] else '<span class="muted">no</span>'
        authority = (
            _esc(s["authority"]) if s["authority"]
            else ("derived" if s["derived"] else '<span class="muted">—</span>')
        )
        add(
            f'<tr><td><a href="#src-{_esc(s["id"])}"><code>{_esc(s["id"])}</code></a></td>'
            f"<td><code>{_esc(s['system']) or '—'}</code></td>"
            f"<td><code>{_esc(s['origin']) or '—'}</code></td>"
            f"<td>{_esc(s['kind'])}</td><td>{authority}</td>"
            f"<td>{_esc(s['classification'])}</td>"
            f"<td>{confirmed}</td><td>{ledger_cell}</td><td>{captures}</td>"
            f"<td>{mappings}</td><td>{loaders}</td></tr>"
        )
    add("</table>")

    # -- per-source detail (only sources with content) ------------------------
    detailed = [
        s
        for s in data["sources"]
        if s["ontology_mappings"] or s["loaders"] or s["taxonomy_captures"]
    ]
    add("<h2>Per-source detail</h2>")
    add(
        '<p class="sub">Placeholder sources with nothing joined yet are summarized '
        "above only.</p>"
    )
    for s in detailed:
        add(f'<h3 id="src-{_esc(s["id"])}">{_esc(s["id"])}</h3>')
        if s["loaders"]:
            add("<ul class=\"tight\">")
            for loader in s["loaders"]:
                if loader["commands"]:
                    cmds = ", ".join(
                        f"<code>drydocs {_esc(c)}</code>" for c in loader["commands"]
                    )
                elif loader["cli_name"]:
                    cmds = (
                        f'ad hoc via <code>drydocs load {_esc(loader["cli_name"])}</code>'
                    )
                else:
                    cmds = '<span class="muted">no command</span>'
                add(
                    f"<li><code>{_esc(loader['name'])}</code> "
                    f"({_esc(loader['class'])}, source_label={_esc(loader['source_label'])})"
                    f" — runs in: {cmds}</li>"
                )
            add("</ul>")
        if s["ontology_mappings"]:
            add("<ul class=\"tight\">")
            for m in s["ontology_mappings"]:
                label = f" → <code>{_esc(m['label'])}</code>" if m["label"] else ""
                add(
                    f"<li>{_status_chip(m['status'])} <code>{_esc(m['id'])}</code>{label}</li>"
                )
            add("</ul>")

    # -- retired ids (D4) ------------------------------------------------------
    add("<h2>Retired ids (D4 refusal list)</h2>")
    add(
        '<p class="sub">Legacy v1 flat ids — the registry loader and the '
        "loader-source overlay REFUSE every one of them; renamed rows carry "
        "the matching <code>replaces:</code> back-pointer.</p>"
    )
    add("<table><tr><th>retired id</th><th>replaced by</th><th>reason</th></tr>")
    for r in data["retired"]:
        replaced = (
            "<br>".join(f"<code>{_esc(x)}</code>" for x in r["replaced_by"])
            or '<span class="muted">(not re-minted)</span>'
        )
        add(
            f"<tr><td><code>{_esc(r['id'])}</code></td><td>{replaced}</td>"
            f"<td>{_esc(r['reason'])}</td></tr>"
        )
    add("</table>")

    # -- sourceless + drift ----------------------------------------------------
    add("<h2>Named sourceless loaders</h2>")
    for loader in data["sourceless_loaders"]:
        cmds = ", ".join(f"<code>drydocs {_esc(c)}</code>" for c in loader["commands"])
        add(
            f"<p><code>{_esc(loader['name'])}</code> ({_esc(loader['class'])}) — "
            f"runs in: {cmds}.<br><em>{_esc(loader['reason'])}</em></p>"
        )
    if data["map_entries_without_registry_source"]:
        add("<h2>Map entries citing unregistered sources</h2>")
        add(
            '<div class="warn">These taxonomy-ontology-map entries name a '
            "<code>taxonomy.source</code> with no source-registry entry — surfaced "
            "here, never dropped; rule each at grooming (register the feed or "
            "re-point the entry).<ul class=\"tight\">"
        )
        for m in data["map_entries_without_registry_source"]:
            add(
                f"<li>{_status_chip(m['status'])} <code>{_esc(m['id'])}</code> → "
                f"<code>{_esc(m['source'])}</code></li>"
            )
        add("</ul></div>")
    add("</body></html>")
    return "\n".join(out) + "\n"


def main() -> int:
    data = build_load_map()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    OUT_HTML.write_text(build_load_map_html(data), encoding="utf-8")
    n_ledger = sum(1 for s in data["sources"] if s["ledger"]["state"] == "ledger")
    n_pending = sum(1 for s in data["sources"] if s["ledger"]["state"] == "pending")
    print(
        f"wrote {OUT} + {OUT_HTML} ({len(data['sources'])} sources: "
        f"{n_ledger} with ledgers, {n_pending} pending, "
        f"{len(data['sources']) - n_ledger - n_pending} placeholders; "
        f"{len(data['sequence'])} sequence steps)"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
