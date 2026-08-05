"""S10 — the pre-cutover :BusinessApplication refusal.

Pins the guard that S3's §C2 argued for and nothing implemented: a graph holding
pre-cutover application nodes (``seal_id`` set, ``app_id`` null) is INVISIBLE to a
post-cutover MERGE, because a uniqueness constraint ignores nulls. The loader mints
a twin and then dies on the seal_id constraint part-way through the batch.

The four cases here are the four ways that guard can be wrong: it can miss a loader,
it can fire too late (after the :JobRun exists), it can be defeated by the
:SchemaMeta exemplars, or it can refuse a healthy graph.
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest


class _FakeAdapter:
    def __init__(self, rows: list[dict] | None = None) -> None:
        self._rows = rows or []

    def __enter__(self) -> _FakeAdapter:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def rows(self) -> Iterator[dict]:
        yield from self._rows


class _FakeClient:
    """Stands in for the graph, parameterized by how many PRE-CUTOVER apps it holds.

    ``stale`` is what the guard's probe finds: :BusinessApplication nodes with a
    null app_id, excluding the :SchemaMeta exemplars (the probe's own predicate
    does that exclusion, so this fake never counts them — which is why the
    exemplar case below asserts on the QUERY TEXT rather than on a count).
    """

    def __init__(self, stale: int = 0) -> None:
        self.stale = stale
        self.run_calls: list[tuple[str, dict]] = []
        self.run_script_calls: list[tuple[str, dict]] = []

    def run(self, cypher: str, params: dict | None = None, **kwargs) -> list[dict]:
        bind = {**(params or {}), **kwargs}
        self.run_calls.append((cypher, bind))
        if "AS stale" in cypher:
            return [{"stale": self.stale}]
        if "AS found" in cypher:
            # batch_port_orchestrator's endpoint probe — not under test here.
            return [{"found": 1}]
        if "SHOW INDEXES" in cypher:
            return []
        if "AS rows_changed" in cypher:
            return [{"rows_changed": 0}]
        return []

    def run_script(self, script: str, params: dict | None = None) -> None:
        self.run_script_calls.append((script, dict(params or {})))

    def flushed_rows(self) -> list[dict]:
        rows: list[dict] = []
        for _, bind in self.run_calls:
            rows.extend(bind.get("batch", []))
        for _, params in self.run_script_calls:
            rows.extend(params.get("batch", []))
        return rows


def _loader_classes() -> list[type]:
    """Every loader whose Cypher MERGEs the canonical :BusinessApplication node.

    Enumerated here rather than discovered, so ADDING a fifth MERGE site without
    the guard is caught by the coverage test below instead of passing silently.
    """
    from drydocs.loaders.catalog import PatProductMappingLoader
    from drydocs.loaders.manual_loads import ManualSealAttributionLoader
    from drydocs.loaders.seal_applications import SealApplicationsLoader
    from drydocs.loaders.software_registry import SoftwareRegistryLoader

    return [
        SealApplicationsLoader,
        ManualSealAttributionLoader,
        PatProductMappingLoader,
        SoftwareRegistryLoader,
    ]


@pytest.mark.parametrize("loader_cls", _loader_classes(), ids=lambda c: c.name)
def test_pre_cutover_node_refuses_the_load(loader_cls: type) -> None:
    """A single pre-S3 node stops the load, on every MERGE-site loader."""
    client = _FakeClient(stale=1)
    with pytest.raises(RuntimeError, match="null app_id"):
        loader_cls(client, _FakeAdapter(), run_log=False).load()


@pytest.mark.parametrize("loader_cls", _loader_classes(), ids=lambda c: c.name)
def test_clean_graph_proceeds(loader_cls: type) -> None:
    """The guard must not be a load-time tax on a correctly-keyed graph."""
    client = _FakeClient(stale=0)
    summary = loader_cls(client, _FakeAdapter(), run_log=False).load()
    assert summary.status == "OK"


@pytest.mark.parametrize("loader_cls", _loader_classes(), ids=lambda c: c.name)
def test_refusal_writes_nothing_not_even_the_job_run(loader_cls: type) -> None:
    """The whole point is that it lands BEFORE any write.

    A guard that fired after ``_open_run`` would leave a :JobRun recording a load
    that never happened — and the failure this prevents is specifically a
    PARTIAL write, so a partial audit trail is the wrong medicine.
    """
    client = _FakeClient(stale=3)
    with pytest.raises(RuntimeError):
        loader_cls(client, _FakeAdapter(), run_log=False).load()

    assert not client.flushed_rows()
    assert not [c for c, _ in client.run_calls if "MERGE (run:JobRun" in c]
    assert not [c for c, _ in client.run_calls if "SHOW INDEXES" in c], (
        "the identity refusal must precede _preflight_indexes too — a graph this "
        "broken should not be reported as an index problem"
    )


def test_probe_excludes_the_schema_meta_exemplars() -> None:
    """``schema_graph.cypher`` MERGEs :SchemaMeta:BusinessApplication exemplars that
    carry the REAL label with NO key property. A bare null-app_id count matches them,
    so without the predicate this guard would refuse every load in any bootstrapped
    database — the same trap ``_count_real_nodes`` documents."""
    from drydocs.loaders.seal_applications import SealApplicationsLoader

    client = _FakeClient(stale=1)
    with pytest.raises(RuntimeError):
        SealApplicationsLoader(client, _FakeAdapter(), run_log=False).load()

    probes = [c for c, _ in client.run_calls if "AS stale" in c]
    assert probes, "no pre-cutover probe was issued"
    for probe in probes:
        assert "NOT a:SchemaMeta" in probe
        assert "a.app_id IS NULL" in probe


def test_the_message_names_the_remedy_not_only_the_symptom() -> None:
    """A refusal that says only "refusing to load" costs the reader the incident.
    This one has to carry the backfill, the rebuild alternative, and the
    count-duplicates-first caution — the three things the company run needed."""
    from drydocs.loaders.seal_applications import SealApplicationsLoader

    client = _FakeClient(stale=2)
    with pytest.raises(RuntimeError) as excinfo:
        SealApplicationsLoader(client, _FakeAdapter(), run_log=False).load()

    message = str(excinfo.value)
    assert "2 :BusinessApplication" in message, "the count belongs in the message"
    assert "SET a.app_id = a.seal_id" in message
    assert "rebuild" in message
    assert "TC-03" in message, "point at the duplicate-finder, do not describe it"


def test_every_merge_site_carries_the_guard() -> None:
    """Coverage, from the Cypher rather than from memory.

    A new loader that MERGEs the canonical node without the mixin is exactly the
    regression this item exists to prevent, and it would pass every other test in
    this file by simply not being in the list.
    """
    import re
    from pathlib import Path

    from drydocs.loaders.app_identity import PreCutoverApplicationGuard

    cypher_dir = Path(__file__).resolve().parents[2] / "drydocs" / "loaders" / "cypher"
    merge_site = re.compile(r"MERGE\s*\(\s*\w+\s*:\s*BusinessApplication\s*\{")
    merging = {p.name for p in cypher_dir.glob("*.cypher") if merge_site.search(p.read_text())}

    guarded = {cls.cypher_path.name for cls in _loader_classes()}
    assert merging == guarded, (
        f"Cypher files MERGEing :BusinessApplication: {sorted(merging)}; "
        f"loaders carrying the S10 guard: {sorted(guarded)}. "
        "A new MERGE site needs PreCutoverApplicationGuard, or an explanation here."
    )
    for cls in _loader_classes():
        assert issubclass(cls, PreCutoverApplicationGuard)
        mro = cls.__mro__
        from drydocs.loaders.base import BaseLoader

        assert mro.index(PreCutoverApplicationGuard) < mro.index(BaseLoader), (
            f"{cls.__name__}: the guard must precede BaseLoader in the MRO or its "
            "_load never runs"
        )
