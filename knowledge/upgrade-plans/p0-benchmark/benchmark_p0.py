"""docmeta P0 benchmark — traversal vs fulltext vs manifest-routed markdown.

Throwaway spike script (Q3). Creates a fulltext index on Chunk for the
benchmark and DROPS it at the end (DB left as found, minus nothing).
Results -> JSON for the written verdict.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from neo4j import GraphDatabase

REPO = Path(r"C:\coding\projects\sandbox\DryDocs")
CORPUS = REPO / "external" / "orchestration" / "bmc-controlm"
OUT = Path(__file__).parent / "benchmark_p0_results.json"

# creds from .env (gitignored local config)
env = {}
for line in (REPO / ".env").read_text(encoding="utf-8", errors="replace").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip()

driver = GraphDatabase.driver(env["NEO4J_URI"], auth=(env["NEO4J_USER"], env["NEO4J_PASSWORD"]))
DB = "drydocs"


def cy(query: str, **params):
    t0 = time.perf_counter()
    with driver.session(database=DB) as s:
        rows = [dict(r) for r in s.run(query, params)]
    ms = (time.perf_counter() - t0) * 1000
    return rows, ms


def blob(rows) -> str:
    return json.dumps(rows, default=str, ensure_ascii=False)


# --- the fixed question set ---------------------------------------------------
# Each entry: id, class, question, marker (regex the retrieved context must
# contain; None => expect-empty / abstain-correct), per-arm specs.
# Traversal 'naive' vs 'informed' Cypher records retrieval-stage failure
# attribution for paraphrase questions (the ch.8 idea).

QUESTIONS = [
    dict(
        id="SA1",
        cls="structure/aggregation",
        q="How many documents are in the corpus, and which has the most content?",
        marker=r"controlm-",  # a doc id must be present; value-correctness judged from data
        traversal="""MATCH (d:Document)<-[:PART_OF]-(c:Chunk)
                     WITH count(DISTINCT d) AS docs, collect(DISTINCT d.doc_id) AS ids
                     MATCH (d2:Document)<-[:PART_OF]-(c2:Chunk)
                     WITH docs, d2.doc_id AS doc, sum(c2.char_count) AS chars
                     ORDER BY chars DESC LIMIT 1
                     RETURN docs, doc AS largest_doc, chars""",
        fulltext="documentation corpus size largest document",
        manifest=["SOURCE-MANIFEST.md"],
    ),
    dict(
        id="SA2",
        cls="structure/aggregation",
        q="How much of the corpus is Claude inference (SYNTHESIZED) vs vendor-grounded?",
        marker=r"SYNTHESIZED",
        traversal="""MATCH (c:Chunk) WHERE c.chunk_id STARTS WITH 'controlm-'
                     RETURN c.provenance AS provenance, count(*) AS chunks,
                            sum(c.char_count) AS chars ORDER BY chunks DESC""",
        fulltext="SYNTHESIZED inference vendor grounded provenance share",
        manifest=["SOURCE-MANIFEST.md"],
    ),
    dict(
        id="EL1",
        cls="exact lookup",
        q="What is %%LIBMEMSYM?",
        marker=r"LIBMEMSYM",
        traversal="""MATCH (c:Chunk)-[:PART_OF]->(d:Document)
                     WHERE c.text CONTAINS 'LIBMEMSYM'
                     RETURN d.doc_id AS doc, c.heading AS heading,
                            c.provenance AS tier, left(c.text, 1200) AS text""",
        fulltext="LIBMEMSYM",
        manifest=["controlm-variables.md"],
    ),
    dict(
        id="EL2",
        cls="exact lookup",
        q="What does the ctmcreate utility do?",
        marker=r"ctmcreate",
        traversal="""MATCH (c:Chunk)-[:PART_OF]->(d:Document)
                     WHERE c.text CONTAINS 'ctmcreate'
                     RETURN d.doc_id AS doc, c.heading AS heading,
                            c.provenance AS tier, left(c.text, 1200) AS text""",
        fulltext="ctmcreate utility",
        manifest=["controlm-general-parameters.md"],
    ),
    dict(
        id="EL3",
        cls="exact lookup",
        q="What does ODAT mean?",
        marker=r"ODAT",
        traversal="""MATCH (c:Chunk)-[:PART_OF]->(d:Document)
                     WHERE c.text CONTAINS 'ODAT'
                     RETURN d.doc_id AS doc, c.heading AS heading, left(c.text, 600) AS text
                     ORDER BY c.char_count LIMIT 3""",
        fulltext="ODAT order date",
        manifest=["controlm-variables.md"],
    ),
    dict(
        id="PC1",
        cls="paraphrase/conceptual",
        q="How do I make one job wait for another job to finish before it runs?",
        marker=r"prerequisite condition|[Ii]n [Cc]ondition|condition",
        traversal_naive="""MATCH (c:Chunk) WHERE c.text CONTAINS 'wait for another job'
                           RETURN c.heading AS heading, left(c.text, 400) AS text""",
        traversal="""MATCH (c:Chunk)-[:PART_OF]->(d:Document)
                     WHERE c.text CONTAINS 'prerequisite condition'
                     RETURN d.doc_id AS doc, c.heading AS heading, left(c.text, 1200) AS text""",
        fulltext="job wait finish before runs depends",
        manifest=["controlm-events.md"],
    ),
    dict(
        id="PC2",
        cls="paraphrase/conceptual",
        q="Can a job start automatically when a file arrives?",
        marker=r"[Ff]ile ?[Ww]atcher",
        traversal_naive="""MATCH (c:Chunk) WHERE c.text CONTAINS 'when a file arrives'
                           RETURN c.heading AS heading, left(c.text, 400) AS text""",
        traversal="""MATCH (c:Chunk)-[:PART_OF]->(d:Document)
                     WHERE toLower(c.text) CONTAINS 'file watcher'
                     RETURN d.doc_id AS doc, c.heading AS heading, left(c.text, 800) AS text
                     ORDER BY c.char_count LIMIT 3""",
        fulltext="job start automatically file arrives",
        manifest=["controlm-file-watcher.md"],
    ),
    dict(
        id="PC3",
        cls="paraphrase/conceptual",
        q="How do I keep jobs from running on holidays?",
        marker=r"holiday",
        traversal="""MATCH (c:Chunk)-[:PART_OF]->(d:Document)
                     WHERE toLower(c.text) CONTAINS 'holiday'
                     RETURN d.doc_id AS doc, c.heading AS heading, left(c.text, 800) AS text
                     ORDER BY c.char_count LIMIT 3""",
        fulltext="jobs not running holidays",
        manifest=["controlm-calendars.md"],
    ),
    dict(
        id="MD1",
        cls="multi-doc",
        q="Which docs cover pool variables, and how do they relate to %% user variables?",
        marker=r"pool",
        traversal="""MATCH (c:Chunk)-[:PART_OF]->(d:Document)
                     WHERE toLower(c.text) CONTAINS 'pool variable' OR toLower(c.text) CONTAINS 'named pool'
                     RETURN d.doc_id AS doc, collect(c.heading)[..4] AS headings,
                            sum(c.char_count) AS chars""",
        fulltext="pool variables named pool",
        manifest=[
            "controlm-variables.md",
            "controlm-api-job-properties.md",
            "controlm-file-transfer-job.md",
        ],
    ),
    dict(
        id="MD2",
        cls="multi-doc + provenance",
        q="Which Control-M version do these docs target, and is the Automation API compatible with it?",
        marker=r"9\.0\.20 and higher|9\.0\.21\.300",
        traversal="""MATCH (d:Document) WITH DISTINCT d.target_version AS target LIMIT 1
                     MATCH (c:Chunk)-[:PART_OF]->(d2:Document)
                     WHERE c.text CONTAINS '9.0.20 and higher'
                     RETURN target, d2.doc_id AS compat_doc, c.heading AS heading,
                            c.provenance AS tier, left(c.text, 600) AS text""",
        fulltext="version compatible Automation API 9.0.21",
        manifest=["SOURCE-MANIFEST.md", "controlm-api-installation.md"],
    ),
    dict(
        id="PV1",
        cls="provenance",
        q="Are the JSON job-definition examples in the API docs vendor ground truth?",
        marker=r"SYNTHESIZED",
        traversal="""MATCH (c:Chunk)-[:PART_OF]->(d:Document)
                     WHERE d.doc_id STARTS WITH 'controlm-api' AND c.provenance = 'SYNTHESIZED'
                     RETURN d.doc_id AS doc, count(*) AS synthesized_chunks,
                            collect(c.heading)[..5] AS example_headings""",
        fulltext="JSON job definition example ground truth",
        manifest=["SOURCE-MANIFEST.md"],
    ),
    dict(
        id="OS1",
        cls="out-of-scope",
        q="How do I define an AutoSys global variable?",
        marker=None,  # expect-empty: correct behavior is an abstention
        traversal="""MATCH (c:Chunk) WHERE c.text CONTAINS 'AutoSys global variable'
                     RETURN c.heading AS heading, left(c.text, 300) AS text""",
        fulltext="AutoSys global variable define",
        manifest=[],  # router abstains: no AutoSys doc exists in this corpus
    ),
]

# --- run ------------------------------------------------------------------------

results = []

# fulltext index for the benchmark (dropped at the end)
cy("CREATE FULLTEXT INDEX p0_chunk_ft IF NOT EXISTS FOR (c:Chunk) ON EACH [c.heading, c.text]")
cy("CALL db.awaitIndexes()")

FT_QUERY = """CALL db.index.fulltext.queryNodes('p0_chunk_ft', $q) YIELD node, score
              WITH node, score ORDER BY score DESC LIMIT 3
              MATCH (node)-[:PART_OF]->(d:Document)
              RETURN d.doc_id AS doc, node.heading AS heading, score,
                     left(node.text, 1200) AS text"""

for spec in QUESTIONS:
    entry = dict(id=spec["id"], cls=spec["cls"], q=spec["q"], arms={})
    marker = spec["marker"]

    # marker= binds at DEFINITION time, not call time (B023). Harmless today —
    # every call below happens inside this same iteration — but the day an arm
    # goes lazy, gets collected into a list, or the loop is parallelised, late
    # binding would score every question against the LAST marker and report
    # plausible, wrong numbers with no error.
    def score(rows, text_blob, ms, marker=marker):
        found = bool(re.search(marker, text_blob)) if marker else None
        return dict(
            rows=len(rows),
            ms=round(ms, 1),
            chars=len(text_blob),
            marker_found=found,
            empty=(len(rows) == 0),
            sample=text_blob[:300],
        )

    # traversal (naive first where declared — failure attribution)
    if "traversal_naive" in spec:
        rows, ms = cy(spec["traversal_naive"])
        entry["arms"]["traversal_naive"] = score(rows, blob(rows), ms)
    rows, ms = cy(spec["traversal"])
    entry["arms"]["traversal"] = score(rows, blob(rows), ms)

    # fulltext
    rows, ms = cy(FT_QUERY, q=spec["fulltext"])
    entry["arms"]["fulltext"] = score(rows, blob(rows), ms)

    # manifest-routed markdown: cost = full text of the routed file(s)
    t0 = time.perf_counter()
    texts = []
    for fname in spec["manifest"]:
        texts.append((CORPUS / fname).read_text(encoding="utf-8"))
    ms = (time.perf_counter() - t0) * 1000
    text_blob = "\n".join(texts)
    entry["arms"]["manifest"] = dict(
        rows=len(spec["manifest"]),
        ms=round(ms, 1),
        chars=len(text_blob),
        marker_found=(bool(re.search(marker, text_blob)) if marker else None),
        empty=(len(spec["manifest"]) == 0),
        files=spec["manifest"],
    )

    results.append(entry)

cy("DROP INDEX p0_chunk_ft IF EXISTS")
driver.close()

OUT.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")
print(f"wrote {OUT}")
for e in results:
    line = f"{e['id']:4} "
    for arm in ("traversal", "fulltext", "manifest"):
        a = e["arms"][arm]
        mark = (
            "EMPTY"
            if a["empty"]
            else ("HIT" if a["marker_found"] else ("n/a" if a["marker_found"] is None else "miss"))
        )
        line += f"| {arm[:8]}: {mark:5} {a['chars']:>7}ch {a['ms']:>7.1f}ms "
    print(line)
