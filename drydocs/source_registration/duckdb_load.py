"""Load the extracted synthetic CSVs into one project-local DuckDB file.

DuckDB is not installed by default: the import is lazy and the tests
``importorskip`` it, so a tree without the package loses this step and nothing
else. It IS declared, as of GRAPH6 — the optional
``[tool.poetry.group.source-registration]`` group, so
``poetry install --with source-registration`` is the answer to "where do I get
it". Before that the package was named in no file at all, which is the same
silence with none of the findability. Every column is read as VARCHAR (``all_varchar``) — type inference is
the one thing that would make two loads of one CSV differ, and the profiler
downstream (DataHub's sqlalchemy profiler over ``duckdb:///``) is what should
say what the values look like.

Two extra tables make the file self-describing: ``_sources`` (one row per
loaded table with the dataset's five descriptor axes) and ``_run`` (seed,
bundle schema, table count). Both are derived from the descriptors, never
typed here.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

from drydocs.source_registration.bundle import Extracted
from drydocs_core.source_descriptors import SourceDescriptors

SOURCES_TABLE = "_sources"
RUN_TABLE = "_run"


def table_name(name: str) -> str:
    """``controlm_jobs.csv`` -> ``controlm_jobs``; anything odd becomes ``_``."""
    stem = Path(name).stem
    return "".join(ch if ch.isalnum() or ch == "_" else "_" for ch in stem)


def load(
    descriptors: SourceDescriptors,
    extracted: Iterable[Extracted],
    db_path: Path,
) -> dict[str, int]:
    """Create or replace one table per extracted CSV. Returns table -> row count."""
    import duckdb  # lazy on purpose: optional dependency

    db_path.parent.mkdir(parents=True, exist_ok=True)
    counts: dict[str, int] = {}
    con = duckdb.connect(str(db_path))
    try:
        con.execute(
            f"CREATE OR REPLACE TABLE {SOURCES_TABLE} ("
            "table_name VARCHAR, source_id VARCHAR, file VARCHAR, placement VARCHAR, "
            "acquisition VARCHAR, format VARCHAR, authority VARCHAR, layer VARCHAR, "
            "access VARCHAR, drydocs_urn VARCHAR)"
        )
        for item in sorted(extracted, key=lambda e: (e.source_id, e.name)):
            tname = table_name(item.name)
            con.execute(
                f"CREATE OR REPLACE TABLE {tname} AS "
                "SELECT * FROM read_csv(?, header = true, all_varchar = true)",
                [str(item.path)],
            )
            (n,) = con.execute(f"SELECT count(*) FROM {tname}").fetchone()
            counts[tname] = int(n)
            d = descriptors.get(item.source_id)
            con.execute(
                f"INSERT INTO {SOURCES_TABLE} VALUES (?,?,?,?,?,?,?,?,?,?)",
                [
                    tname,
                    item.source_id,
                    item.name,
                    item.placement,
                    d.acquisition,
                    d.format,
                    d.authority,
                    d.layer,
                    d.access,
                    d.urn,
                ],
            )
        con.execute(
            f"CREATE OR REPLACE TABLE {RUN_TABLE} AS SELECT ? AS seed, ? AS theme, ? AS tables",
            [
                int(descriptors.synthetic.get("seed", 0)),
                str(descriptors.synthetic.get("theme", "")),
                len(counts),
            ],
        )
    finally:
        con.close()
    return counts
