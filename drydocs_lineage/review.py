"""Lineage SME review page — re-homed from depgraph's html-review profile (0002-C §4).

Renders a :class:`~drydocs_lineage.model.LineageGraph` as ONE self-contained HTML
file (no server, no Neo4j, no external resources) a subject-matter expert opens in
a browser: one section per Control-M folder, a card per job showing
job/node-target/run-as/application/command and the dependencies it INVOKES (plus
TRIGGERS, and the READS_FROM / WRITES_TO file-op candidates the G14 extractor
pass emits), an assertion panel at the top
(the FR/TC discipline without Cypher), and a per-folder comment box persisted to
localStorage with one-click export of all notes as JSON.

Pattern mirrors ``drydocs.graph_review`` (pure renderer, ontology-free, the SME
reviews *the data*) — mirrored, not imported: components never import each other.
Everything shown here is CANDIDATE material (D2) — this page is exactly what the
curation gate reviews before :func:`drydocs_lineage.writer.write_curated` may run.

Re-home deltas from the depgraph original (kept deliberately small):
- ``Graph`` → ``LineageGraph``; the base-layer ``mark_cycles()`` / multi-project
  stats stayed behind in depgraph (out of the topology).
- ``host`` → ``node_target`` — POLYMORPHIC per gate controlm-hosts-topology
  (a host GROUP in the common case, or a hard-coded agent host; resolution is
  the Epic P RUNS_ON pass). The panel wording says so.
- rel spellings are the registered vocabulary (READS_FROM / WRITES_TO).
"""

from __future__ import annotations

import html
import json
from datetime import UTC, datetime

from .model import LineageGraph
from .writer import unresolved_file_op_candidates

#: kinds we consider "resolved" dependencies; anything else (notably "unknown")
#: means a cmd_line the core parser could not classify — surfaced as a warning.
_UNRESOLVED = "unknown"

_REL_ORDER = ("INVOKES", "TRIGGERS", "READS_FROM", "WRITES_TO")


def _e(v) -> str:
    return html.escape("" if v is None else str(v))


def _assertions(graph: LineageGraph) -> list[dict]:
    jobs = [p for p in graph.processes.values() if p.kind == "controlm_job"]
    missing_target = [j for j in jobs if not j.node_target]
    missing_run_as = [j for j in jobs if not j.run_as]
    # children pointed at by an INVOKES that the parser could not classify
    unresolved = []
    for _src, rel, dst in graph.rels:
        if rel == "INVOKES":
            d = graph.get_any(dst)
            if d is not None and getattr(d, "kind", "") == _UNRESOLVED:
                unresolved.append(d)
    orphan_assets = [
        a
        for a in graph.data_assets.values()
        if not any(r[0] == a.node_id or r[2] == a.node_id for r in graph.rels)
    ]
    # script-src file-op candidates with no owning job — exactly what the
    # writer would drop at plan time (WritePlan.unresolved_file_ops, G14);
    # surfaced here so the loss is reviewed BEFORE a plan is cut.
    file_ops = [r for r in graph.rels if r[1] in ("READS_FROM", "WRITES_TO")]
    unresolved_fops = unresolved_file_op_candidates(graph)
    if unresolved_fops:
        fop_detail = (
            f"{len(unresolved_fops)} of {len(file_ops)} would drop at plan " "(unresolved_file_ops)"
        )
    else:
        fop_detail = f"{len(file_ops)} candidate(s)" if file_ops else "n/a"
    return [
        {
            "label": "Every job has a node target (host or host group)",
            "ok": not missing_target,
            "detail": f"{len(missing_target)} missing" if missing_target else f"{len(jobs)} jobs",
        },
        {
            "label": "Every job has a run-as user",
            "ok": not missing_run_as,
            "detail": f"{len(missing_run_as)} missing" if missing_run_as else f"{len(jobs)} jobs",
        },
        {
            "label": "Every invoked command resolved to a known type",
            "ok": not unresolved,
            "detail": f"{len(unresolved)} unresolved" if unresolved else "all classified",
        },
        {
            "label": "No orphan data assets",
            "ok": not orphan_assets,
            "detail": f"{len(orphan_assets)} orphan" if orphan_assets else "n/a",
        },
        {
            "label": "Every file-op candidate has an owning Activity (job or ETL process)",
            "ok": not unresolved_fops,
            "detail": fop_detail,
        },
    ]


def _children(graph: LineageGraph, job_id: str) -> list[tuple[str, object]]:
    out = []
    for src, rel, dst in sorted(graph.rels):
        if src == job_id and rel in _REL_ORDER:
            node = graph.get_any(dst)
            if node is not None:
                out.append((rel, node))
    return out


def _job_card(graph: LineageGraph, job) -> str:
    rows = []
    if job.node_target:
        rows.append(f'<span class="kv"><b>node target</b> {_e(job.node_target)}</span>')
    rows.append(
        f'<span class="kv {"warn" if not job.run_as else ""}"><b>run as</b> '
        f'{_e(job.run_as) or "&mdash; missing"}</span>'
    )
    if job.application:
        rows.append(f'<span class="kv"><b>app</b> {_e(job.application)}</span>')

    deps = _children(graph, job.node_id)
    if deps:
        items = []
        for rel, node in deps:
            kind = getattr(node, "kind", "")
            path = getattr(node, "path", "") or getattr(node, "location", "")
            warn = " warn" if kind == _UNRESOLVED else ""
            # data assets have no name — show the location's last segment (G14)
            name = getattr(node, "name", "") or (
                path.rstrip("/").rsplit("/", 1)[-1] if path else ""
            )
            items.append(
                f'<li class="dep{warn}"><span class="rel">{_e(rel)}</span> '
                f'<span class="kind k-{_e(kind)}">{_e(kind)}</span> '
                f'<span class="dname">{_e(name)}</span>'
                f'{f"<span class=path>{_e(path)}</span>" if path else ""}</li>'
            )
        dep_html = '<ul class="deps">' + "".join(items) + "</ul>"
    else:
        dep_html = (
            '<div class="nodeps">no resolved dependency &mdash; cmd_line empty or unparsed</div>'
        )

    cmd = f'<pre class="cmd">{_e(job.command)}</pre>' if job.command else ""
    return (
        '<div class="job">'
        f'<div class="jname">{_e(job.name)}</div>'
        f'<div class="meta">{" ".join(rows)}</div>'
        f'{cmd}{dep_html}'
        '</div>'
    )


def _archival_rows(rows: list[dict], css: str) -> str:
    items = []
    for r in rows:
        hosts = ", ".join(r.get("hosts", [])) or "&mdash;"
        items.append(
            f'<li class="arow {css}"><span class="apath">{_e(r.get("path", ""))}</span> '
            f'<span class="ahosts">{_e(hosts)}</span>'
            f'<div class="areason">{_e(r.get("reason", ""))}</div></li>'
        )
    return "<ul class='arows'>" + "".join(items) + "</ul>" if items else ""


def _archival_section(report) -> str:
    """The G58 dead-script archival section (gate rua-load-shapes §E1/§E3/§H1):
    coverage stated ON the report, three dispositions separately counted, the
    scope-gated misdeployment suppression visible, archived-state
    cross-referenced from G24, and the registry axis's unknowns surfaced.
    Findings are review material — reported, never auto-actioned (§H2)."""
    archived = (
        f"already archived (repo-only): {len(report.already_archived)} &middot; "
        f"never committed (G24): {report.never_committed}"
        if report.corroboration_run
        else "archived-state not observed &mdash; corroboration not run"
    )
    registry = (
        f"active_unknown: {report.active_unknown}"
        if report.active_unknown is not None
        else "registry axis not observed on this run"
    )
    parts = [
        '<section class="wrap checks archival">',
        "<h2>Dead-script archival report</h2>",
        f'<div class="coverage {"warn" if report.metadata_only else ""}">'
        f"{_e(report.coverage_statement)}</div>",
        '<div class="prov">',
        f"<span><b>scripts</b> {report.scripts_total}</span>",
        f"<span><b>in use (CMD_LINE-referenced)</b> {report.in_use}</span>",
        f"<span><b>dead (archive &amp; remove)</b> {len(report.dead)}</span>",
        f"<span><b>misdeployed (relocate, never delete)</b> {len(report.misdeployed)}</span>",
        f"<span><b>dynamically called (keep)</b> {len(report.dynamically_called)}</span>",
        f"<span><b>misdeployment checks suppressed (scope not local)</b> "
        f"{report.misdeployment_suppressed}</span>",
        f"<span>{archived}</span>",
        f"<span>{_e(registry)}</span>",
        "</div>",
        _archival_rows(report.dead, "dead"),
        _archival_rows(report.misdeployed, "mis"),
        _archival_rows(report.dynamically_called, "dyn"),
        "</section>",
    ]
    return "".join(parts)


def to_html(
    graph: LineageGraph,
    *,
    doc_id: str = "lineage-review",
    generated_at: str | None = None,
    archival=None,
) -> str:
    """Render the graph as a single self-contained SME review page.

    ``archival`` is an optional G58 :class:`~.archival.ArchivalReport` — when
    given, the dead-script section renders after the assertion panel (this is
    the surface the §E3 curation ladder already lives on)."""
    gen = generated_at or datetime.now(UTC).strftime("%Y-%m-%d %H:%M UTC")
    doc = _e(doc_id)

    jobs = [p for p in graph.processes.values() if p.kind == "controlm_job"]
    folders: dict[str, list] = {}
    for j in jobs:
        folders.setdefault(j.folder or "(no folder)", []).append(j)

    # kind summary chips (children only — the discovered dependencies)
    kinds: dict[str, int] = {}
    for p in graph.processes.values():
        if p.kind != "controlm_job":
            kinds[p.kind] = kinds.get(p.kind, 0) + 1

    asserts = _assertions(graph)
    all_ok = all(a["ok"] for a in asserts)

    parts: list[str] = []
    w = parts.append
    w("<!doctype html><html lang=en><head><meta charset=utf-8>")
    w('<meta name=viewport content="width=device-width, initial-scale=1">')
    w(f"<title>DryDocs lineage review &mdash; {doc}</title>")
    w(f"<style>{_CSS}</style></head><body>")

    # header
    w('<header><div class="wrap">')
    w(f"<h1>Control-M lineage review &mdash; {doc}</h1>")
    w('<div class="prov">')
    w(f"<span><b>generated</b> {_e(gen)}</span>")
    w(f"<span><b>jobs</b> {len(jobs)}</span>")
    w(f"<span><b>folders</b> {len(folders)}</span>")
    w(f"<span><b>dependencies</b> {sum(kinds.values())}</span>")
    w(f"<span><b>rels</b> {len(graph.rels)}</span>")
    w("</div>")
    if kinds:
        chips = "".join(
            f'<span class="chip k-{_e(k)}">{_e(k)} &middot; {n}</span>'
            for k, n in sorted(kinds.items())
        )
        w(f'<div class="chips">{chips}</div>')
    w('<button class="export" onclick="exportNotes()">&#11015; Export SME notes (JSON)</button>')
    w("</div></header>")

    # assertion panel
    w('<section class="wrap checks">')
    w(
        f'<div class="checkhdr {"ok" if all_ok else "fail"}">'
        f'{"&#10003; all checks passed" if all_ok else "&#9888; review needed"}</div>'
    )
    w("<ul>")
    for a in asserts:
        w(
            f'<li class="{"ok" if a["ok"] else "fail"}">'
            f'<span class="mark">{"&#10003;" if a["ok"] else "&#10007;"}</span> '
            f'{_e(a["label"])} <span class="adetail">{a["detail"]}</span></li>'
        )
    w("</ul></section>")

    # the G58 archival section (optional — rendered when a report is supplied)
    if archival is not None:
        w(_archival_section(archival))

    # folder sections
    for folder in sorted(folders):
        fjobs = sorted(folders[folder], key=lambda j: j.name)
        sid = _e(folder)
        w('<section class="wrap folder">')
        w(f'<h2>{_e(folder)} <span class="fcount">{len(fjobs)} job(s)</span></h2>')
        w('<div class="jobs">')
        for j in fjobs:
            w(_job_card(graph, j))
        w("</div>")
        w(
            f'<textarea class="note" data-sid="{sid}" data-folder="{sid}" '
            f'placeholder="SME notes for {sid} — saved in your browser; click Export to download all"></textarea>'
        )
        w("</section>")

    if not jobs:
        w(
            '<section class="wrap"><p class="empty">No Control-M jobs in this graph. '
            "Point <code>drydocs lineage-review</code> at a controlm_jobs CSV export.</p></section>"
        )

    w(f"<script>const DOC_ID={json.dumps(doc_id)};{_JS}</script>")
    w("</body></html>")
    return "".join(parts)


_CSS = """
:root{--bg:#f6f7f9;--card:#fff;--ink:#1c2330;--mut:#5b6676;--line:#e4e8ee;
--accent:#2456b8;--ok:#1a7f4b;--okbg:#e7f6ee;--fail:#b3261e;--failbg:#fdecea;--warn:#9a6700;--warnbg:#fff4d6;}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--ink);
font:14px/1.5 -apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif}
.wrap{max-width:1080px;margin:0 auto;padding:0 20px}
header{background:#fff;border-bottom:1px solid var(--line);padding:22px 0 16px}
h1{margin:0 0 8px;font-size:20px}
.prov{display:flex;flex-wrap:wrap;gap:18px;color:var(--mut);font-size:13px}
.prov b{color:var(--ink);font-weight:600}
.chips{margin-top:12px;display:flex;flex-wrap:wrap;gap:6px}
.chip{font-size:12px;padding:2px 9px;border-radius:20px;background:#eef2f8;border:1px solid var(--line)}
.export{margin-top:14px;background:var(--accent);color:#fff;border:0;border-radius:6px;
padding:8px 14px;font-size:13px;cursor:pointer}
.export:hover{filter:brightness(1.08)}
.checks{margin:20px auto;background:var(--card);border:1px solid var(--line);border-radius:10px;
padding:14px 18px}
.checkhdr{font-weight:600;margin-bottom:8px}
.checkhdr.ok{color:var(--ok)}.checkhdr.fail{color:var(--fail)}
.checks ul{list-style:none;margin:0;padding:0;display:grid;gap:6px}
.checks li{font-size:13px}.checks .mark{display:inline-block;width:18px}
.checks li.ok .mark{color:var(--ok)}.checks li.fail{color:var(--fail);font-weight:600}
.adetail{color:var(--mut);font-size:12px;margin-left:6px}
.folder{margin:24px auto}
h2{font-size:16px;border-bottom:2px solid var(--accent);padding-bottom:6px;margin:0 0 14px}
.fcount{color:var(--mut);font-weight:400;font-size:13px}
.jobs{display:grid;grid-template-columns:repeat(auto-fill,minmax(330px,1fr));gap:12px}
.job{background:var(--card);border:1px solid var(--line);border-radius:9px;padding:12px 13px}
.jname{font-weight:600;font-size:13px;word-break:break-all;margin-bottom:6px}
.meta{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:8px}
.kv{font-size:12px;background:#f1f4f9;border:1px solid var(--line);border-radius:5px;padding:1px 7px}
.kv b{color:var(--mut);font-weight:600;margin-right:3px}
.kv.warn{background:var(--failbg);border-color:#f3c0bb;color:var(--fail)}
.cmd{background:#0f1626;color:#d7e0f0;border-radius:6px;padding:8px 10px;font-size:11.5px;
overflow:auto;margin:0 0 8px;white-space:pre-wrap;word-break:break-all}
.deps{list-style:none;margin:0;padding:0;display:grid;gap:4px}
.dep{font-size:12px;display:flex;flex-wrap:wrap;gap:6px;align-items:baseline}
.rel{font-size:10px;font-weight:700;color:var(--accent);letter-spacing:.04em}
.kind{font-size:10px;padding:1px 6px;border-radius:10px;background:#eef2f8;border:1px solid var(--line)}
.k-pyspark,.k-python{background:#e7f0ff;border-color:#bcd4ff}
.k-abinitio{background:#efe7ff;border-color:#d6c2ff}
.k-shell_script{background:#e9f7ee;border-color:#bfe6cd}
.k-informatica{background:#fff0e6;border-color:#ffd2b0}
.k-unknown{background:var(--warnbg);border-color:#ecd58a;color:var(--warn)}
.dname{font-weight:600}.path{color:var(--mut);font-family:ui-monospace,Menlo,Consolas,monospace;font-size:11px;word-break:break-all}
.dep.warn .dname{color:var(--warn)}
.nodeps{font-size:12px;color:var(--mut);font-style:italic}
.note{width:100%;min-height:60px;margin-top:12px;border:1px dashed #9bb0d0;border-radius:7px;
padding:8px 10px;font:13px inherit;resize:vertical;background:#fbfdff}
.empty{color:var(--mut)}code{background:#eef2f8;padding:1px 5px;border-radius:4px}
.archival h2{border-bottom-color:var(--warn)}
.coverage{font-size:13px;background:#eef2f8;border:1px solid var(--line);border-radius:7px;
padding:9px 12px;margin:8px 0 10px}
.coverage.warn{background:var(--warnbg);border-color:#ecd58a;color:var(--warn);font-weight:600}
.arows{list-style:none;margin:10px 0 0;padding:0;display:grid;gap:6px}
.arow{font-size:12px;border:1px solid var(--line);border-left-width:4px;border-radius:6px;
padding:6px 10px;background:var(--card)}
.arow.dead{border-left-color:var(--fail)}
.arow.mis{border-left-color:var(--warn)}
.arow.dyn{border-left-color:var(--ok)}
.apath{font-family:ui-monospace,Menlo,Consolas,monospace;font-weight:600;word-break:break-all}
.ahosts{color:var(--mut);margin-left:8px}
.areason{color:var(--mut);margin-top:2px}
"""

_JS = """
function _notes(){const o={};document.querySelectorAll('textarea.note').forEach(t=>{
 if(t.value.trim())o[t.dataset.sid]=t.value;});return o;}
function _save(){try{localStorage.setItem('drydocs-lineage-review-'+DOC_ID,JSON.stringify(_notes()));}catch(e){}}
function _load(){try{const d=JSON.parse(localStorage.getItem('drydocs-lineage-review-'+DOC_ID)||'{}');
 document.querySelectorAll('textarea.note').forEach(t=>{if(d[t.dataset.sid])t.value=d[t.dataset.sid];});}catch(e){}}
document.addEventListener('input',e=>{if(e.target.classList&&e.target.classList.contains('note'))_save();});
function exportNotes(){const n=_notes();const out={doc:DOC_ID,exported:new Date().toISOString(),
 notes:Object.keys(n).map(k=>({folder:k,note:n[k]}))};
 const b=new Blob([JSON.stringify(out,null,2)],{type:'application/json'});
 const a=document.createElement('a');a.href=URL.createObjectURL(b);
 a.download='lineage-review-notes-'+DOC_ID+'.json';document.body.appendChild(a);a.click();a.remove();}
window.addEventListener('DOMContentLoaded',_load);
"""
