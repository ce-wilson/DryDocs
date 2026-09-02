"""Generate the N4/N5 load map — ONE surface joining sources, loaders,
commands, order, column ledgers, taxonomy captures and ontology mappings.

Joins the N3 declarations (BaseLoader.source_id, cli.COMMAND_LOADERS,
cli.CANONICAL_LOAD_SEQUENCE) to config/source-registry.yaml, the
config/source-mappings/ column ledgers (via each entry's ``locator.mapping``
pointer), the config/taxonomy/ captures (their top-level ``source:`` key) and
config/taxonomy-ontology-map/ (the per-domain fragment directory since S5;
read through ``yaml_fragments.load_yaml_source``), and emits
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

from drydocs_core import yaml_fragments  # noqa: E402  (needs the sys.path insert above)

REGISTRY = REPO / "config" / "source-registry.yaml"
DOC_REGISTRY = REPO / "config" / "doc-source-registry.yaml"
TAXONOMY_DIR = REPO / "config" / "taxonomy"
MAP_FILE = REPO / "config" / "taxonomy-ontology-map"
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
    map_entries = yaml_fragments.load_yaml_source(MAP_FILE)["mappings"]

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
            captures_by_source.setdefault(source, []).append(path.relative_to(REPO).as_posix())

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
            # source is drift worth seeing on the one surface. An entry may
            # carry an explicit `source_exemption` (the SOURCELESS_LOADERS
            # written-reason idiom; N8): it stays listed WITH its reason, so
            # a ruled no-feed-by-design is distinguishable from drift.
            exemption = str(m.get("source_exemption") or "").strip()
            unmatched_map_sources.append(
                {**row, "source": source, **({"exemption": exemption} if exemption else {})}
            )

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
                # Doc-governance fields (Q16 / the /software surface). `target_db`
                # is the load-bearing one: without it a consumer cannot know when
                # it is ENTITLED to report a document count. A corpus targeting a
                # database the reader cannot query must render "not queried",
                # never 0 — a 0 there is a false claim of absence.
                "tier": entry.get("tier"),
                "curation": entry.get("curation"),
                "connector": entry.get("connector"),
                "target_db": entry.get("target_db"),
                "trust_default": entry.get("trust_default"),
                "graph_locator": entry.get("graph_locator"),
                "taxonomy_path": entry.get("taxonomy_path"),
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
            "command": step.command,
            "mode": step.mode,
            # N6: which operator surfaces run this step. Sorted so the render is
            # deterministic — the declaration holds an unordered frozenset.
            # G79: DERIVED steps carry no literal — resolve through the same
            # function load_profile() uses, so the published surface cannot
            # disagree with what the operator paths actually run.
            "profiles": sorted(cli.step_profiles(step)),
            "profiles_derived": step.profiles is None,
            "note": step.note,
            "loaders": [cls.name for cls in cli.COMMAND_LOADERS.get(step.command, ())],
        }
        for step in cli.CANONICAL_LOAD_SEQUENCE
    ]

    sourceless = [
        {
            "name": cls.name,
            "class": cls.__name__,
            "reason": reason,
            "commands": sorted(commands_by_class.get(cls, [])),
        }
        for cls, reason in sorted(cli.SOURCELESS_LOADERS.items(), key=lambda kv: kv[0].__name__)
    ]

    # G80 (b) — the two facts the guard checks, published beside the other
    # defect lists so the surface is an honest inventory rather than a tidy one.
    # (1) registry loaders no declared command runs: reason (from the written
    # exclusions) or null — a null here is exactly what unchained_loaders()
    # fails the suite on, so a committed null means the guard is being ignored.
    unchained = [
        {
            "name": name,
            "class": cls.__name__,
            "loader": cls.name,
            "reason": cli.UNCHAINED_LOADER_EXCLUSIONS.get(name),
        }
        for name, cls in cli.unchained_registry_loaders()
    ]

    # (2) chain steps whose DECLARED bundled input is not repo content (G78's
    # other half — G78 fails the RUN; this shows the same fact on the map).
    # Declared-generated files (cli.GENERATED_SAMPLE_FILES) are listed
    # PRESENCE-INDEPENDENT with their build recipe as the exemption — probing
    # the filesystem for them would flap the committed render between a machine
    # that has generated them and one that has not. Everything else is package
    # data: absent-on-disk means absent-from-the-repo, and the row ships with
    # exemption null. Paths are repo-relative on purpose (committed==fresh
    # must hold on every machine).
    declared_inputs: list[tuple[str, str, str, Path, str]] = [
        (command, nm, sample, cli.DEFAULT_SAMPLES_DIR, "drydocs/data/samples")
        for command, chain in cli.CHAINS.items()
        for nm, _cls, sample in chain
    ]
    for nm, _cls, sample, sql in (
        cli.CONTROLM_NODE_STAGES + cli.CONTROLM_PART2_STAGES + cli.CONTROLM_REL_STAGES
    ):
        declared_inputs.append(
            ("ingest-controlm", nm, sample, cli.DEFAULT_SAMPLES_DIR, "drydocs/data/samples")
        )
        declared_inputs.append(("ingest-controlm", nm, sql, cli.SQL_DIR, "drydocs/loaders/sql"))
    steps_with_uncommitted_inputs = []
    for command, step_name, filename, directory, rel_dir in declared_inputs:
        generated = cli.GENERATED_SAMPLE_FILES.get(filename)
        if generated is None and (directory / filename).is_file():
            continue
        steps_with_uncommitted_inputs.append(
            {
                "command": command,
                "step": step_name,
                "file": filename,
                "searched": rel_dir,
                "exemption": generated,
            }
        )

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
        "unchained_loaders": unchained,
        "steps_with_uncommitted_inputs": steps_with_uncommitted_inputs,
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
.wr-wired{background:#bbf7d0;color:#166534}
.wr-planned{background:#fde68a;color:#92400e}
.wr-awaiting{background:#e0e7ff;color:#3730a3}
.wr-registered{background:#e5e7eb;color:#374151}
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


# ---- O90: the wiring key ----------------------------------------------------
#
# The SAME cross the console renders (web/src/loadmap/loadMapModel.ts
# wiringState), kept in step deliberately: this is N5's paper surface for the
# same rows, and a key that disagrees between screen and print is worse than no
# key. Two axes the registry already records separately -- `confirmed` (a gate
# ruled the meaning) and a non-empty `loaders` (something is built) -- crossed.
#
# It REPORTS; it does not rule. A registry field asserting wiring readiness is
# gate territory and that gate is drafted and unsigned (N10,
# config/gate-prompts/registry-wiring-readiness.yaml). Nothing here writes such
# a field: it crosses two booleans already in the artifact.
#
# Four cells, not two -- the two middle ones are neither wired nor planned, and
# flattening them is the conflation N10 exists to end.

WIRING_STATES: tuple[tuple[str, str, str], ...] = (
    ("wired", "wired", "a gate ruled its meaning and a loader is built"),
    ("planned", "planned", "a gate ruled its meaning; nothing is built yet"),
    ("awaiting", "built, awaiting gate", "a loader is built; no gate has ruled its meaning"),
    ("registered", "registered", "declared in the registry; neither ruled nor built"),
)


def _wiring_state(source: dict) -> str:
    """Cross `confirmed` with loader presence. Pure function of the row."""
    built = bool(source["loaders"])
    if source["confirmed"]:
        return "wired" if built else "planned"
    return "awaiting" if built else "registered"


def _wiring_chip(state: str) -> str:
    label = next(lbl for sid, lbl, _ in WIRING_STATES if sid == state)
    return f'<span class="chip wr-{state}">{label}</span>'


def _wiring_key(sources: list[dict]) -> str:
    """The legend, with counts read from the data rather than written down."""
    counts: dict[str, int] = {sid: 0 for sid, _, _ in WIRING_STATES}
    for s in sources:
        counts[_wiring_state(s)] += 1
    items = "".join(
        f"<li>{_wiring_chip(sid)}&thinsp;{counts[sid]} &mdash; "
        f'<span class="muted">{meaning}</span></li>'
        for sid, _lbl, meaning in WIRING_STATES
    )
    return (
        '<div class="warn" style="background:#f8fafc;border-color:#e5e7eb">'
        "<b>Wiring key</b> &mdash; the cross of two things the registry records separately: "
        "<i>has a gate ruled this dataset&rsquo;s meaning</i>, and "
        "<i>is a loader built that writes it</i>. Four states, because the two middle ones "
        "are neither wired nor planned."
        f'<ul class="tight">{items}</ul></div>'
    )


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

    add('<!DOCTYPE html>\n<html lang="en"><head><meta charset="utf-8">')
    add('<meta name="viewport" content="width=device-width, initial-scale=1">')
    add("<title>DryDocs — Load Map</title>")
    add(f"<style>{_CSS}</style></head><body>")
    add("<h1>DryDocs — Load Map</h1>")
    add(
        '<p class="sub">GENERATED by scripts/render_load_map.py from the N3 '
        "declarations + config/source-registry.yaml (v2: systems/datasets/"
        "retired) + config/doc-source-registry.yaml + config/source-mappings/ + "
        "config/taxonomy/ + config/taxonomy-ontology-map/ — never hand-edit. "
        f"{len(data['systems'])} systems · {len(data['sources'])} datasets "
        f"({n_ledger} with column ledgers, "
        f"{n_pending} ledger-pending, {n_placeholder} placeholders) · "
        f"{len(data['retired'])} retired ids · "
        f"{len(data['sequence'])} sequence steps.</p>"
    )

    # -- the canonical sequence -----------------------------------------------
    add("<h2>Canonical load sequence</h2>")
    add(
        '<p class="sub">Declared ONCE in drydocs/cli_shared.py '
        "(CANONICAL_LOAD_SEQUENCE, hoisted there at S13 and re-exported from "
        "<code>drydocs.cli</code>, which is still the import path callers use). "
        "<b>runs in</b> names the operator surfaces that run each step (N6): "
        "<code>scheduled-ingest</code> is <code>scripts/ingest.sh</code>, which reads "
        "the declaration at run time; <code>cold-start</code> is Appendix B of the "
        "startup/refresh runbook, held to it by test_load_sequence_surfaces.py. A "
        "standing step outside <code>scheduled-ingest</code> is a ruled omission with a "
        "reason in cli.SCHEDULED_INGEST_EXCLUSIONS, not a gap.</p>"
    )
    add(
        "<table><tr><th>#</th><th>command</th><th>mode</th><th>runs in</th>"
        "<th>loaders</th><th>note</th></tr>"
    )
    for i, step in enumerate(data["sequence"], 1):
        loaders = (
            ", ".join(f"<code>{_esc(n)}</code>" for n in step["loaders"])
            or '<span class="muted">—</span>'
        )
        profiles = (
            ", ".join(f"<code>{_esc(p)}</code>" for p in step["profiles"])
            or '<span class="muted">—</span>'
        )
        add(
            f"<tr><td>{i}</td><td><code>drydocs {_esc(step['command'])}</code></td>"
            f'<td><span class="chip mode-{_esc(step["mode"])}">{_esc(step["mode"])}</span></td>'
            f"<td>{profiles}</td>"
            f"<td>{loaders}</td><td>{_esc(step['note'])}</td></tr>"
        )
    add("</table>")
    ad_hoc = ", ".join(f"<code>drydocs {_esc(c)}</code>" for c in data["ad_hoc_commands"])
    add(f'<p class="sub">Operator-driven (not sequence members): {ad_hoc}.</p>')

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
    add(_wiring_key(data["sources"]))
    add(
        "<table><tr><th>dataset</th><th>system</th><th>origin</th><th>kind</th>"
        "<th>authority</th><th>classification</th>"
        "<th>confirmed</th><th>wiring</th><th>column ledger</th><th>taxonomy</th>"
        "<th>ontology mappings</th><th>loaders</th></tr>"
    )
    for s in data["sources"]:
        ledger = s["ledger"]
        ledger_cell = f'<span class="chip ledger-{ledger["state"]}">{ledger["state"]}</span>'
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
            " ".join(f"{_status_chip(st)}&thinsp;{n}" for st, n in sorted(by_status.items()))
            or '<span class="muted">—</span>'
        )
        loaders = (
            "<br>".join(f"<code>{_esc(loader['name'])}</code>" for loader in s["loaders"])
            or '<span class="muted">—</span>'
        )
        confirmed = "✓" if s["confirmed"] else '<span class="muted">no</span>'
        authority = (
            _esc(s["authority"])
            if s["authority"]
            else ("derived" if s["derived"] else '<span class="muted">—</span>')
        )
        add(
            f'<tr><td><a href="#src-{_esc(s["id"])}"><code>{_esc(s["id"])}</code></a></td>'
            f"<td><code>{_esc(s['system']) or '—'}</code></td>"
            f"<td><code>{_esc(s['origin']) or '—'}</code></td>"
            f"<td>{_esc(s['kind'])}</td><td>{authority}</td>"
            f"<td>{_esc(s['classification'])}</td>"
            f"<td>{confirmed}</td><td>{_wiring_chip(_wiring_state(s))}</td>"
            f"<td>{ledger_cell}</td><td>{captures}</td>"
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
            add('<ul class="tight">')
            for loader in s["loaders"]:
                if loader["commands"]:
                    cmds = ", ".join(f"<code>drydocs {_esc(c)}</code>" for c in loader["commands"])
                elif loader["cli_name"]:
                    cmds = f'ad hoc via <code>drydocs load {_esc(loader["cli_name"])}</code>'
                else:
                    cmds = '<span class="muted">no command</span>'
                add(
                    f"<li><code>{_esc(loader['name'])}</code> "
                    f"({_esc(loader['class'])}, source_label={_esc(loader['source_label'])})"
                    f" — runs in: {cmds}</li>"
                )
            add("</ul>")
        if s["ontology_mappings"]:
            add('<ul class="tight">')
            for m in s["ontology_mappings"]:
                label = f" → <code>{_esc(m['label'])}</code>" if m["label"] else ""
                add(f"<li>{_status_chip(m['status'])} <code>{_esc(m['id'])}</code>{label}</li>")
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
    unmatched = data["map_entries_without_registry_source"]
    drift = [m for m in unmatched if not m.get("exemption")]
    exempt = [m for m in unmatched if m.get("exemption")]
    if drift:
        add("<h2>Map entries citing unregistered sources</h2>")
        add(
            '<div class="warn">These taxonomy-ontology-map entries name a '
            "<code>taxonomy.source</code> with no source-registry entry — surfaced "
            "here, never dropped; rule each at grooming (register the feed, "
            're-point the entry, or record a source_exemption).<ul class="tight">'
        )
        for m in drift:
            add(
                f"<li>{_status_chip(m['status'])} <code>{_esc(m['id'])}</code> → "
                f"<code>{_esc(m['source'])}</code></li>"
            )
        add("</ul></div>")
    if exempt:
        add("<h2>Source-exempt map entries (ruled, no feed by design)</h2>")
        for m in exempt:
            add(
                f"<p>{_status_chip(m['status'])} <code>{_esc(m['id'])}</code> → "
                f"<code>{_esc(m['source'])}</code><br><em>{_esc(m['exemption'])}</em></p>"
            )

    # -- G80: unchained loaders + uncommitted chain inputs ---------------------
    unchained = data["unchained_loaders"]
    silent = [u for u in unchained if not u["reason"]]
    excused = [u for u in unchained if u["reason"]]
    if silent:
        add("<h2>Unchained loaders (SILENT — the suite fails on these)</h2>")
        add(
            '<div class="warn">Registered in LOADER_REGISTRY, run by NO declared '
            "command — reachable only ad hoc via <code>drydocs load &lt;name&gt;</code>, "
            'with no written reason (cli.UNCHAINED_LOADER_EXCLUSIONS).<ul class="tight">'
        )
        for u in silent:
            add(f"<li><code>{_esc(u['name'])}</code> ({_esc(u['class'])})</li>")
        add("</ul></div>")
    if excused:
        add("<h2>Unchained loaders (excluded from every chain, reason on record)</h2>")
        for u in excused:
            add(
                f"<p><code>{_esc(u['name'])}</code> ({_esc(u['class'])}) — reachable "
                f"only ad hoc via <code>drydocs load {_esc(u['name'])}</code>."
                f"<br><em>{_esc(u['reason'])}</em></p>"
            )
    uncommitted = data["steps_with_uncommitted_inputs"]
    if uncommitted:
        add("<h2>Chain inputs not committed with the repo</h2>")
        add(
            '<p class="sub">Declared by a chain constant, not repo content. A row '
            "with an exemption is a per-machine build on record; a row without one "
            "is a missing input a real run would fail on (G78).</p>"
        )
        add(
            "<table><tr><th>command</th><th>step</th><th>file</th><th>searched</th><th>why</th></tr>"
        )
        for row in uncommitted:
            why = (
                f"<em>{_esc(row['exemption'])}</em>"
                if row["exemption"]
                else '<span class="warn">MISSING — no exemption on record</span>'
            )
            add(
                f"<tr><td><code>{_esc(row['command'])}</code></td>"
                f"<td><code>{_esc(row['step'])}</code></td>"
                f"<td><code>{_esc(row['file'])}</code></td>"
                f"<td><code>{_esc(row['searched'])}</code></td><td>{why}</td></tr>"
            )
        add("</table>")
    add("</body></html>")
    return "\n".join(out) + "\n"


def main() -> int:
    data = build_load_map()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    OUT_HTML.write_text(build_load_map_html(data), encoding="utf-8", newline="\n")
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
