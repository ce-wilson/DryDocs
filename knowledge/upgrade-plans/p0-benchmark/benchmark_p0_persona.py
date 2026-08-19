"""docmeta Q19 — the P0 questions re-run with a PERSONA in the loop.

Throwaway spike script, same character as benchmark_p0.py (Q3): one run, one
JSON, not a harness (Q19 fence (e)). Differences from the original, and they
are the point of the item:

  * The Cypher is NOT hand-written. A Sonnet subagent — given ONLY the graph
    schema and the 12 questions, in a fresh context that never saw the
    original queries or the regex ground truths — generated one query per
    question (persona_queries.json, committed beside this script).
  * Grading is MECHANICAL: the original marker regexes from benchmark_p0.py,
    applied unchanged to whatever the persona's query retrieved. No human
    judge in the loop; adjudications, if any, are recorded in the results
    JSON and the write-up, never silently applied.

Safety: persona queries are executed inside execute_read, so a query that
tried to write fails instead of writing; a static keyword screen runs first
and records (not silently skips) anything it refuses.
"""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from neo4j import GraphDatabase

from drydocs_core.config import Neo4jSettings

HERE = Path(__file__).parent
QUERIES = HERE / "persona_queries.json"
ORIGINAL = HERE / "benchmark_p0_results.json"
OUT = HERE / "benchmark_p0_persona_results.json"
DB = "drydocs"

# The ORIGINAL ground truths, verbatim from benchmark_p0.py — the persona never
# saw these. marker None => expect-empty (abstain-correct).
MARKERS: dict[str, str | None] = {
    "SA1": r"controlm-",
    "SA2": r"SYNTHESIZED",
    "EL1": r"LIBMEMSYM",
    "EL2": r"ctmcreate",
    "EL3": r"ODAT",
    "PC1": r"prerequisite condition|[Ii]n [Cc]ondition|condition",
    "PC2": r"[Ff]ile ?[Ww]atcher",
    "PC3": r"holiday",
    "MD1": r"pool",
    "MD2": r"9\.0\.20 and higher|9\.0\.21\.300",
    "PV1": r"SYNTHESIZED",
    "OS1": None,
}

WRITE_TOKENS = re.compile(
    r"\b(CREATE|MERGE|DELETE|DETACH|SET|REMOVE|DROP|CALL\s+db\.index|LOAD\s+CSV|FOREACH)\b",
    re.I,
)


def main() -> None:
    settings = Neo4jSettings()
    driver = GraphDatabase.driver(
        settings.uri, auth=(settings.user, settings.password.get_secret_value())
    )

    persona = json.loads(QUERIES.read_text(encoding="utf-8"))
    original = {e["id"]: e for e in json.loads(ORIGINAL.read_text(encoding="utf-8"))}

    results = []
    with driver.session(database=DB) as session:
        for spec in persona:
            qid, cypher = spec["id"], spec["cypher"]
            marker = MARKERS[qid]
            entry: dict = dict(id=qid, cypher=cypher, note=spec.get("note", ""))

            if WRITE_TOKENS.search(cypher):
                entry["refused"] = "write-keyword screen"
                entry.update(rows=0, ms=None, chars=0, marker_found=False, empty=True)
                results.append(entry)
                continue

            t0 = time.perf_counter()
            try:
                rows = session.execute_read(lambda tx, c=cypher: [dict(r) for r in tx.run(c)])
                entry["error"] = None
            except Exception as exc:  # a failing query IS a persona result
                rows = []
                entry["error"] = f"{type(exc).__name__}: {exc}"
            ms = (time.perf_counter() - t0) * 1000

            text_blob = json.dumps(rows, default=str, ensure_ascii=False)
            found = bool(re.search(marker, text_blob)) if marker else None
            empty = len(rows) == 0
            # scoring rule, stated: marker questions score on marker_found;
            # OS1 (marker None) scores on abstention — empty is CORRECT.
            correct = (found is True) if marker else empty
            entry.update(
                rows=len(rows),
                ms=round(ms, 1),
                chars=len(text_blob),
                marker_found=found,
                empty=empty,
                correct=correct,
                sample=text_blob[:300],
            )

            # deltas vs the original hand-written traversal arm
            orig = original.get(qid, {}).get("arms", {}).get("traversal")
            if orig:
                entry["delta_vs_original_traversal"] = dict(
                    original_marker_found=orig["marker_found"],
                    original_chars=orig["chars"],
                    original_ms=orig["ms"],
                    chars_delta=len(text_blob) - orig["chars"],
                    ms_delta=round(ms - orig["ms"], 1),
                )
            results.append(entry)

    driver.close()
    OUT.write_text(json.dumps(results, indent=1, ensure_ascii=False), encoding="utf-8")

    score = sum(1 for e in results if e.get("correct"))
    print(f"wrote {OUT}")
    print(
        f"persona score: {score}/12 mechanical "
        "(original hand-written traversal: 10/12 mechanical, 12/12 after its "
        "2 disclosed author adjudications — see the persona-rerun explainer)"
    )
    for e in results:
        mark = "OK " if e.get("correct") else ("ERR" if e.get("error") else "miss")
        print(
            f"{e['id']:4} {mark} rows={e.get('rows', 0):>3} "
            f"chars={e.get('chars', 0):>7} ms={e.get('ms')}"
        )


if __name__ == "__main__":
    main()
