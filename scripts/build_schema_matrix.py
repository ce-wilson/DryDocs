"""Build the schema review matrix: ddschema triples joined to load-map sources.

Queries the ``ddschema`` database for its ``:SchemaMeta`` relationship exemplars,
joins each triple to the registered source + loader that carries it (from
``web/src/generated/load-map.json``), and associates it with backlog items that
cite the vocab id. Writes a dated markdown matrix under ``docs/reviews/``.

Usage::

    poetry run python scripts/build_schema_matrix.py [output.md]

Requires a running Neo4j container with the ``ddschema`` database provisioned.
Connection comes from the environment (never hardcoded)::

    NEO4J_CONTAINER (default: neo4jtest)
    NEO4J_USER      (default: neo4j)
    NEO4J_PASSWORD  (required)
    NEO4J_DATABASE  (default: ddschema)
"""

from __future__ import annotations

import csv
import io
import json
import os
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from drydocs_core.backlog_store import load_backlog_document

REPO = Path(__file__).resolve().parents[1]
OUT = (
    Path(sys.argv[1])
    if len(sys.argv) > 1
    else REPO / "docs" / "reviews" / f"schema-matrix-{date.today():%Y-%m-%d}.md"
)

CONTAINER = os.environ.get("NEO4J_CONTAINER", "neo4jtest")
USER = os.environ.get("NEO4J_USER", "neo4j")
PASSWORD = os.environ.get("NEO4J_PASSWORD")
DATABASE = os.environ.get("NEO4J_DATABASE", "ddschema")

if not PASSWORD:
    raise SystemExit(
        "NEO4J_PASSWORD is not set. This script never carries a credential; "
        "export it (or source your .env) before running."
    )

Q = (
    "MATCH (a:SchemaMeta)-[r]->(b:SchemaMeta) "
    "RETURN [l IN labels(a) WHERE l <> 'SchemaMeta'][0] AS src, type(r) AS rel, "
    "[l IN labels(b) WHERE l <> 'SchemaMeta'][0] AS tgt, r.vocab_id AS vocab, "
    "r.domain AS domain, r.status AS status ORDER BY domain, src, rel, tgt;"
)
raw = subprocess.run(
    [
        "docker",
        "exec",
        CONTAINER,
        "cypher-shell",
        "-u",
        USER,
        "-p",
        PASSWORD,
        "-d",
        DATABASE,
        "--format",
        "plain",
        Q,
    ],
    capture_output=True,
    encoding="utf-8",
).stdout
rows = list(csv.DictReader(io.StringIO(raw.replace(", ", ","))))
if not rows:
    raise SystemExit(
        f"no triples returned from {DATABASE} on container {CONTAINER} — "
        "is the container up and the database provisioned?"
    )

# rel label -> (source id, loaders, mapping status) from the load map
lm = json.loads((REPO / "web/src/generated/load-map.json").read_text(encoding="utf-8"))
relmap: dict[str, list[tuple[str, str, str]]] = {}
for s in lm["sources"]:
    lds = ",".join(x["name"] for x in s.get("loaders") or []) or "(no loader yet)"
    for m in s.get("ontology_mappings") or []:
        key = m.get("label")
        if key:
            relmap.setdefault(key, []).append((s["id"], lds, m["status"]))

# label -> load source family (from the load map + seed/bootstrap knowledge)
LABEL_SOURCE = {
    # controlm estate <- psgmgr CM_ replica loaders
    "ControlMJob": "psgmgr.cm_def_vjob · controlm_jobs.v1",
    "ControlMFolder": "psgmgr.cm_def_vtab · controlm_folders.v1",
    "ControlMApplication": "psgmgr.cm_def_vjob (JOB_ID=1 header row) · controlm_folders.v1",
    "ControlMServer": "psgmgr.cm_def_vtab · controlm_folders.v1",
    "ControlMHostGroup": "psgmgr.cm_hosts · controlm_hosts.v1",
    "ExecutionHost": "psgmgr.cm_hosts · controlm_hosts.v1",
    "Condition": "psgmgr.cm_def_lnki/lnko_p_vw · controlm_conditions_in/out.v1",
    "ControlMJobRun": "psgmgr.cm_hist_vw (planned)",
    "JobRun": "loader run envelope (every loader stamps WAS_GENERATED_BY)",
    "Script": "cmd_line resolution (m3/m7, planned)",
    "ETLProcess": "cmd_line resolution (planned)",
    "AppUser": "cm run_as (planned)",
    "Developer": "deployment provenance (p2, planned)",
    "Deployment": "deployment provenance (p2, planned)",
    "File": "file dependency (m3, planned)",
    "DataAsset": "oracle:schema-inventory (proposed)",
    # catalog <- PAT
    "Product": "pat:product-catalog · products.v1",
    "AreaProduct": "pat:product-catalog · area_products.v1",
    "ProductLine": "pat:product-catalog · product_lines.v1",
    "CatalogLOB": "pat:product-catalog · catalog_lobs.v1",
    "DevTeam": "pat:product-catalog · dev_teams.v1",
    "JiraBoard": "pat:product-catalog · dev_teams.v1",
    "Membership": "seal:app-extract / pat:people-report",
    "ProductRole": "pat:people-report · pat_team_roles.v1",
    "Employee": "seal:app-extract seal_contacts.v1 / pat:people-report",
    # seal / business_application
    "BusinessApplication": "seal:app-extract · seal_applications.v1",
    "Port": "seal:app-extract · batch_port_orchestrator.v1",
    "TOMRole": "seal:app-extract · seal_contacts.v1",
    "Attribution": "seal/pat attribution loaders (+ manual_seal_attribution.v1)",
    # registry
    "SoftwareProduct": "config/software-registry · registry loader",
    "Vendor": "config/software-registry · registry loader",
    # docs
    "Document": "bmc-docs · bmc_docs.v1",
    "Chunk": "bmc-docs · bmc_docs.v1",
    "DocSource": "doc-source-registry (docmeta, planned)",
    "OntologyTerm": "ontology seed (bootstrap)",
    "DesignDoc": "repo:design-docs · doc_sections.v1",
    "DocSection": "repo:design-docs · doc_sections.v1",
    "FeedbackNote": "repo:design-docs · doc_feedback.v1",
    "Requirement": "repo:design-docs · doc_traceability.v1",
    "Component": "repo:design-docs · doc_traceability.v1",
    "TestCase": "repo:design-docs · doc_traceability.v1",
    # architecture / code graph
    "Project": "repo:depgraph-snapshot · code_snapshot.v1",
    "CodeModule": "repo:depgraph-snapshot · code_snapshot.v1",
    "SwoClass": "repo:depgraph-snapshot · code_snapshot.v1",
    "Code": "architecture (planned)",
    "PipelineService": "architecture (planned)",
    "Bitbucket": "architecture (planned)",
    # corporate seed
    "Company": "ontology.cypher seed · drydocs bootstrap",
    "BusinessSegment": "ontology.cypher seed · drydocs bootstrap",
    # quality / context
    "Dataset": "quality domain (c23, planned)",
    "QualityMeasurement": "quality domain (c23, planned)",
    "Metric": "ontology.cypher DQV seed",
    "Dimension": "ontology.cypher DQV seed",
    "Observation": "cm_hist_vw SOSA arm (proposed)",
    "Sensor": "SOSA context (planned)",
    "Result": "SOSA context (planned)",
    "ObservableProperty": "SOSA context (planned)",
}

# Which source-id prefixes may satisfy a triple in each vocab domain.
#
# Both the pre- and post-rename domain keys are carried: the
# vocabulary-domains-and-id-policy gate renamed ``controlm`` -> ``scheduler`` and
# ``seal`` -> ``business_application``, but a ddschema provisioned before that
# gate still reports the old values. Keeping both means the join keeps working
# either side of a re-provision instead of silently degrading every row in those
# domains to "vocab only".
DOMAIN_SOURCES = {
    "controlm": ("controlm@", "oracle:"),
    "scheduler": ("controlm@", "oracle:"),
    "context": ("controlm@",),
    "catalog": ("pat:",),
    "seal": ("seal", "controlm@[db].drydocs_stg"),
    "business_application": ("seal", "controlm@[db].drydocs_stg"),
    "docs": ("bmc-docs", "repo:design-docs", "seal-pat-scrape"),
    "architecture": ("repo:depgraph-snapshot", "seal", "pat:"),
    "corporate": (),
    "registry": (),
    "quality": (),
    "all": (),
}


def rel_source(rel: str, domain: str, status: str) -> str:
    prefixes = DOMAIN_SOURCES.get(domain, ())
    hits = [h for h in relmap.get(rel, []) if h[0].startswith(prefixes)] if prefixes else []
    if hits:
        return "<br>".join(f"`{sid}` · {lds} ({st})" for sid, lds, st in hits)
    other = relmap.get(rel)
    if other:
        return (
            f"vocab only in this domain ({status}) — same rel name mapped elsewhere: "
            + "; ".join(f"`{sid}`" for sid, _, _ in other)
        )
    return f"vocab only — no registered source yet ({status})"


def clean(v: str) -> str:
    return v.strip().strip('"')


# backlog association: item ids whose full text mentions the vocab_id (precise) or,
# failing that, the relationship type name as a whole word (noisier, marked ~)
_backlog = load_backlog_document(REPO / "docs/restructure/backlog")  # the sharded tree (ADR 0013)
_items = _backlog["items"] if isinstance(_backlog, dict) and "items" in _backlog else _backlog
ITEM_TEXT = {
    it["id"]: yaml.dump(it, default_flow_style=False)
    for it in _items
    if isinstance(it, dict) and "id" in it
}


def backlog_ids(vocab: str, rel: str) -> str:
    exact = [iid for iid, txt in ITEM_TEXT.items() if vocab and vocab in txt]
    if exact:
        return ", ".join(sorted(exact)[:4]) + ("" if len(exact) <= 4 else f" +{len(exact) - 4}")
    pat = re.compile(rf"\b{re.escape(rel)}\b")
    loose = [iid for iid, txt in ITEM_TEXT.items() if pat.search(txt)]
    if loose:
        return (
            "~" + ", ".join(sorted(loose)[:4]) + ("" if len(loose) <= 4 else f" +{len(loose) - 4}")
        )
    return "—"


by_domain: dict[str, list[dict]] = {}
for r in rows:
    by_domain.setdefault(clean(r["domain"]), []).append(r)

lines = [
    "# Schema matrix — ddschema triples × load sources",  # noqa: RUF001 - × is intentional
    "",
    f"**Basis:** `{DATABASE}` database (container `{CONTAINER}`, queried "
    f"{date.today():%Y-%m-%d}) — {len(rows)} relationship exemplars across "
    f"{len(by_domain)} domains, joined to `web/src/generated/load-map.json` "
    f"({len(lm['sources'])} registered sources) plus the `ontology.cypher` seed. "
    "**Label source** = what writes nodes of that label; **Relationship source** = "
    "the registered source + loader whose ontology mapping carries the edge (with "
    "its gate status), or `vocab only` when the edge is registered in the "
    "vocabulary but no source mapping is wired yet. **Backlog** = backlog/ "
    "item ids whose text cites the vocab id (exact); a `~` prefix means the match "
    "is on the relationship NAME only (noisier); `—` = no item mentions it.",
    "",
    "> Label source is **assigned here, not queried** — the ddschema exemplars carry",
    "> `class`/`prov_type` only, with no source annotation. Treat that column as this",
    "> script's mapping, not as graph-resident fact.",
    "",
]

for domain in sorted(by_domain):
    lines.append(f"## domain: {domain}")
    lines.append("")
    lines.append(
        "| Source label | Label source | Relationship | Vocab id | Status "
        "| Relationship source | Target label | Target label source | Backlog |"
    )
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in by_domain[domain]:
        src, rel, tgt = clean(r["src"]), clean(r["rel"]), clean(r["tgt"])
        vocab, status = clean(r["vocab"]), clean(r["status"])
        lines.append(
            f"| `{src}` | {LABEL_SOURCE.get(src, '?? unmapped')} | **{rel}** | `{vocab}` | {status} "
            f"| {rel_source(rel, domain, status)} | `{tgt}` | {LABEL_SOURCE.get(tgt, '?? unmapped')} "
            f"| {backlog_ids(vocab, rel)} |"
        )
    lines.append("")

unmapped = sorted({clean(r[k]) for r in rows for k in ("src", "tgt")} - set(LABEL_SOURCE))
if unmapped:
    lines.append(f"**Labels without a source assignment (review needed):** {', '.join(unmapped)}")

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
print(
    f"wrote {OUT} — {len(rows)} triples, {len(by_domain)} domains, {len(unmapped)} unmapped labels"
)
