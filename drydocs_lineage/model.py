"""Lineage graph model — re-homed from depgraph@feat/controlm-lineage (ADR 0002-C §4).

The depgraph prototype's *lineage layer*, reconciled to DryDocs identity and ontology:

- **Identity.** A Control-M job's stable key is the graph's NODE KEY composite
  ``(folder_id, job_id)`` (``constraints.cypher: controlmjob_key``) — the same
  ``folder_id.job_id`` key the prototype used. Invoked artifacts key on their
  canonicalized target; data assets on ``(kind, location)`` (the D1 ``assetId``
  proxy-key shape). Ids are namespaced (``#proc#`` / ``#data#``) so rel endpoints
  resolve unambiguously across the two registries.
- **Ontology.** The typed rels are the ALREADY-REGISTERED gate-bound vocabulary
  entries (all ``status: planned`` — nothing here activates them):
  ``INVOKES`` (m3_invokes, prov:used) · ``TRIGGERS`` (m3_triggers,
  inverse-of prov:wasStartedBy) · ``READS_FROM`` (m3_reads_from, prov:used) ·
  ``WRITES_TO`` (m3_writes_to, prov:generated). The prototype's bare ``READS`` /
  ``WRITES`` normalize to the registered labels on load (see ``REL_ALIASES``).
  Node classes: ``controlm_job`` processes ≙ :ControlMJob; invoked artifacts ≙ the
  m3_invokes :Script target; data assets ≙ the D1 :DataAsset proxy shape.
- **Left behind** (per 0002-C §4): the code layer (FileNode / untyped edges /
  Tarjan cycle marking) — that is depgraph's base profile, out of the topology.

Everything in a :class:`LineageGraph` is a CANDIDATE until curation confirms it
(D2: curated-only writes) — the graph is working memory, not ground truth.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

SCHEMA = "drydocs.lineage-graph.v1"
#: accepted on load: our schema + the depgraph prototype's (lineage sections only)
SCHEMA_COMPAT = {SCHEMA, "depgraph-machine-first/v2"}

#: typed relationship labels — the registered (planned, gate-bound) vocabulary
REL_TYPES = {"INVOKES", "TRIGGERS", "READS_FROM", "WRITES_TO"}
#: depgraph prototype spellings → registered labels
REL_ALIASES = {"READS": "READS_FROM", "WRITES": "WRITES_TO"}
#: label → relationship_vocabulary.yaml id (the ontology contract per edge)
VOCAB_IDS = {
    "INVOKES": "m3_invokes",
    "TRIGGERS": "m3_triggers",
    "READS_FROM": "m3_reads_from",
    "WRITES_TO": "m3_writes_to",
}


@dataclass
class ProcessNode:
    """A unit of execution: a Control-M job, or an artifact it invokes."""

    node_id: str          # stable key (see process_id)
    kind: str             # "controlm_job" | "shell" | "spark_job" | "sql" | ...
    name: str             # job name or script basename
    command: str = ""     # the raw command line (Control-M jobs)
    host: str = ""        # server it runs on (Control-M CM_DEF_VJOB.NODE_ID)
    run_as: str = ""      # system user OR software agent (Control-M OWNER / FID)
    path: str = ""        # script/artifact path, once resolved
    folder: str = ""      # Control-M folder (PARENT_TABLE) — review grouping
    application: str = ""  # business app (Control-M APPLICATION); SEAL reconcile key


@dataclass
class DataAssetNode:
    """A piece of data a process reads or writes (the D1 :DataAsset proxy shape)."""

    node_id: str          # stable key (see asset_id)
    kind: str             # "hdfs" | "s3" | "hive_table" | "local_file" | ...
    location: str         # the actual path / URI / table name
    fmt: str = ""         # "avro" | "parquet" | "csv" | "ebcdic" | ...


# -- stable id helpers (one id scheme, used by every extractor) -----------------
def process_id(kind: str, key: str) -> str:
    """Namespaced process key. For ``controlm_job`` the key is the graph's NODE KEY
    composite ``<folder_id>.<job_id>`` (fallback ``<folder>/<job_name>`` for
    hand-made CSVs)."""
    return f"proc#{kind}:{key}"


def asset_id(kind: str, location: str) -> str:
    return f"data#{kind}:{location}"


@dataclass
class LineageGraph:
    """The lineage working graph: candidates awaiting curation, never ground truth."""

    processes: dict[str, ProcessNode] = field(default_factory=dict)
    data_assets: dict[str, DataAssetNode] = field(default_factory=dict)
    rels: set[tuple[str, str, str]] = field(default_factory=set)  # (src, TYPE, dst)

    # -- mutation ---------------------------------------------------------------
    def add_process(self, node: ProcessNode) -> None:
        self.processes.setdefault(node.node_id, node)

    def add_data_asset(self, node: DataAssetNode) -> None:
        self.data_assets.setdefault(node.node_id, node)

    def add_rel(self, src: str, rel_type: str, dst: str) -> None:
        rel_type = REL_ALIASES.get(rel_type, rel_type)
        if rel_type not in REL_TYPES:
            raise ValueError(f"unknown rel type {rel_type!r}; have {sorted(REL_TYPES)}")
        if src != dst:
            self.rels.add((src, rel_type, dst))

    def get_any(self, node_id: str):
        return self.processes.get(node_id) or self.data_assets.get(node_id)

    # -- stats / serialization (machine-first, ported) ---------------------------
    def stats(self) -> dict:
        return {
            "processes": len(self.processes),
            "data_assets": len(self.data_assets),
            "rels": len(self.rels),
        }

    def to_dict(self) -> dict:
        return {
            "schema": SCHEMA,
            "processes": [asdict(self.processes[k]) for k in sorted(self.processes)],
            "data_assets": [asdict(self.data_assets[k]) for k in sorted(self.data_assets)],
            "rels": [list(r) for r in sorted(self.rels)],
            "stats": self.stats(),
        }

    @classmethod
    def from_dict(cls, data: dict) -> "LineageGraph":
        schema = data.get("schema")
        if schema not in SCHEMA_COMPAT:
            raise ValueError(f"unexpected schema: {schema!r}")
        g = cls()
        for p in data.get("processes", []):
            p = dict(p)
            p.pop("project", None)  # depgraph multi-repo field — dropped on re-home
            g.add_process(ProcessNode(**p))
        for d in data.get("data_assets", []):
            d = dict(d)
            d.pop("project", None)
            g.add_data_asset(DataAssetNode(**d))
        for src, rel_type, dst in data.get("rels", []):
            g.add_rel(src, rel_type, dst)  # aliases normalize here
        return g
