"""DPL Metadata-As-Code (MAC) ingest seam (G17).

A DPL pipeline's definition lives beside it as a per-pipeline SET of JSON
files keyed by the same ``--pipeline-id`` GUID the launcher passes on
CMD_LINE — the identity G15 already extracts and
:func:`~drydocs_lineage.extractors.controlm_inventory._stable_invocation_key`
already uses as the ETLProcess token (``proc#dpl:{GUID}``). The traced shape
(runtime trace, 2026-07-21; mechanism-only — real values stay company-side)
is a 6-JSON set per pipeline; this seam CONSUMES the two whose graph meaning
is gate-confirmed and COUNTS the rest:

- ``pipeline.json`` — the pipeline's own record: the keying GUID,
  ``pipelineType``/``subType`` (the kind discriminator G12 lacked), and the
  owner SEAL id. Type/subType/SEAL land as ETLProcess *properties* (the G12
  rule: properties never identity); the SEAL is an attribution FACT beside
  G15's ``-seal`` launcher property — never an attribution edge (Epic K owns
  those).
- ``dataset_flow.json`` — dataset-level input/output lists (GUID + version +
  zone) that become ``READS_FROM`` / ``WRITES_TO`` CANDIDATES for the
  pipeline's ETLProcess, endpoints exactly per the 2026-07-15 gate EDIT
  (``ETLProcess | ControlMJob -> DataAsset``). No new relationship types;
  every ``m3_*`` vocabulary status is untouched — candidates only, the
  curated-load gate still refuses a live write.

ASSUMED FIELD CONTRACT (defined by the SYNTHETIC fixtures, adjust when a real
sample validates it — same discipline as the UI QuerySpec assumed contracts):

    pipeline.json:      {"pipelineId", "pipelineType", "subType",
                         "ownerSealId", "name"?}
    dataset_flow.json:  {"pipelineId"?,
                         "inputDatasets":  [{"guid", "version"?, "zone"?, "name"?}],
                         "outputDatasets": [ ...same shape... ]}

Kind derivation (acceptance c): where MAC metadata exists, the ETLProcess
``kind`` comes from :data:`_KIND_BY_SUBTYPE` instead of the writer's blind
``'etl'`` default — the writer consults ``properties["mac_kind"]``. A subType
with an OPEN enum question (``provisioning`` — a DB load with no transform;
does the gate-log §a enum EXTEND, or does it map to ``utility``?) takes the
RIDER path: no ``mac_kind``, a ``mac_kind_rider`` property, a coverage count,
and the question rides to the next lineage gate session. Never auto-decided.

Join accounting (acceptance a): a MAC set whose GUID matches no extracted
DPL process is STAGED anyway (``mac_only=true`` — candidates are working
memory, curation decides) and counted + listed; DPL processes with no MAC
set are counted too. Nothing drops silently.
"""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from ..model import DataAssetNode, LineageGraph, ProcessNode, asset_id, process_id

#: the two consumed members of the traced per-pipeline JSON set
PIPELINE_JSON = "pipeline.json"
DATASET_FLOW_JSON = "dataset_flow.json"

#: DPL invocation kind — MUST match controlm_inventory's ``inv.invocation_type.lower()``
_DPL_KIND = "dpl"
#: DataAsset kind for MAC dataset endpoints. Candidate-side shape for the
#: "DataAsset zone/glue-table" open item riding G17: identity = dataset GUID
#: alone (version/zone are properties), pending the G22 clause-f GUID-vs-URN
#: ruling.
MAC_DATASET_KIND = "dpl_dataset"

#: pipeline.json subType → the gate-log 2026-07-16 §a kind enum
#: (etl | utility | notification). THE RECORDED KIND-DERIVATION RULE
#: (G17 acceptance c): only enum-safe mappings live here; any subType NOT in
#: this table takes the rider path (mac_kind_rider property + coverage count,
#: writer default stands until a gate rules it). Known rider: ``provisioning``
#: (DB load, no transform — wrong-by-signal as 'etl', but whether the enum
#: extends or maps to 'utility' is an enum-semantics gate question).
_KIND_BY_SUBTYPE: dict[str, str] = {
    "transformation": "etl",   # ASSUMED subType spelling — synthetic-contract value
}


@dataclass
class MacCoverage:
    """Per-run accounting — every skip/mismatch is counted BY REASON, never
    silent (the STG_PARSE_QUALITY / UNMATCHED house rule, candidate side)."""

    sets_read: int = 0                  # pipeline.json files parsed
    sets_invalid: int = 0               # unreadable/invalid JSON — set skipped
    sets_no_guid: int = 0               # pipeline.json without a pipelineId — skipped
    matched: int = 0                    # GUID joined an extracted proc#dpl node
    unmatched: int = 0                  # GUID with no extracted DPL process (staged mac_only)
    unmatched_guids: list[str] = field(default_factory=list)
    dpl_without_mac: int = 0            # extracted DPL processes no MAC set covered
    kind_derived: int = 0               # mac_kind stamped from _KIND_BY_SUBTYPE
    kind_riders: int = 0                # subType on the rider path (enum question)
    seal_facts: int = 0                 # ownerSealId captured
    seal_disagreements: int = 0         # MAC ownerSealId != G15 -seal property
    reads_added: int = 0                # READS_FROM candidates
    writes_added: int = 0               # WRITES_TO candidates
    datasets_added: int = 0             # distinct DataAsset nodes staged
    dataset_no_guid: int = 0            # flow entry without a guid — skipped
    dataset_version_conflicts: int = 0  # same GUID seen with a different version
    flow_missing: int = 0               # set without a dataset_flow.json
    flow_guid_mismatch: int = 0         # dataset_flow pipelineId != pipeline.json's
    files_ignored: int = 0              # other *.json in the set (the rest of the 6)

    def as_dict(self) -> dict:
        return asdict(self)

    def summary(self) -> str:
        return (
            f"sets={self.sets_read} matched={self.matched} "
            f"unmatched={self.unmatched} dpl_without_mac={self.dpl_without_mac} | "
            f"kind: derived={self.kind_derived} riders={self.kind_riders} | "
            f"seal: facts={self.seal_facts} disagree={self.seal_disagreements} | "
            f"flow: reads={self.reads_added} writes={self.writes_added} "
            f"datasets={self.datasets_added} missing={self.flow_missing} | "
            f"skipped: invalid={self.sets_invalid} no_guid={self.sets_no_guid} "
            f"ds_no_guid={self.dataset_no_guid} "
            f"version_conflicts={self.dataset_version_conflicts} "
            f"guid_mismatch={self.flow_guid_mismatch} ignored={self.files_ignored}"
        )


def _load_json(path: Path) -> dict | None:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    return data if isinstance(data, dict) else None


class DplMacExtractor:
    """MAC JSON sets → ETLProcess property enrichment + dataset-level
    READS_FROM/WRITES_TO candidates (curation decides the rest)."""

    name = "dpl-mac"

    def extract(self, source: str | Path, into: LineageGraph) -> MacCoverage:
        """``source`` is a MAC root: a directory whose subdirectories each hold
        one pipeline's JSON set (or itself holds one set — a lone
        ``pipeline.json`` beside its siblings). Returns the run's
        :class:`MacCoverage`; callers report it — nothing drops silently."""
        root = Path(source)
        coverage = MacCoverage()
        set_dirs = sorted(
            {p.parent for p in root.rglob(PIPELINE_JSON)},
        )
        for set_dir in set_dirs:
            self._extract_set(set_dir, into, coverage)

        # the reverse join: extracted DPL processes no MAC set covered keep the
        # writer's default kind (acceptance c) — counted so the gap is visible
        covered = {
            nid for nid in into.processes
            if into.processes[nid].properties.get("mac_covered") == "true"
        }
        coverage.dpl_without_mac = sum(
            1
            for nid, node in into.processes.items()
            if node.kind == _DPL_KIND and nid not in covered
        )
        return coverage

    # -- one pipeline set ---------------------------------------------------
    def _extract_set(
        self, set_dir: Path, graph: LineageGraph, coverage: MacCoverage
    ) -> None:
        pipeline = _load_json(set_dir / PIPELINE_JSON)
        if pipeline is None:
            coverage.sets_invalid += 1
            return
        coverage.sets_read += 1

        guid = str(pipeline.get("pipelineId") or "").strip()
        if not guid:
            coverage.sets_no_guid += 1
            return

        # the rest of the traced 6-JSON set: present, not consumed — counted
        for extra in set_dir.glob("*.json"):
            if extra.name not in (PIPELINE_JSON, DATASET_FLOW_JSON):
                coverage.files_ignored += 1

        node = self._join_process(guid, pipeline, graph, coverage)
        self._apply_pipeline_facts(node, pipeline, coverage)

        flow = _load_json(set_dir / DATASET_FLOW_JSON)
        if flow is None:
            if (set_dir / DATASET_FLOW_JSON).exists():
                coverage.sets_invalid += 1
            else:
                coverage.flow_missing += 1
            return
        flow_guid = str(flow.get("pipelineId") or "").strip()
        if flow_guid and flow_guid != guid:
            # pipeline.json wins (it IS the set's key); mismatch is review material
            coverage.flow_guid_mismatch += 1
        self._apply_dataset_flow(node.node_id, flow, graph, coverage)

    def _join_process(
        self, guid: str, pipeline: dict, graph: LineageGraph, coverage: MacCoverage
    ) -> ProcessNode:
        pid = process_id(_DPL_KIND, guid)
        node = graph.processes.get(pid)
        if node is not None:
            coverage.matched += 1
        else:
            # unmatched GUID: counted + listed, and STAGED anyway (never dropped)
            coverage.unmatched += 1
            coverage.unmatched_guids.append(guid)
            node = ProcessNode(
                node_id=pid,
                kind=_DPL_KIND,
                name=str(pipeline.get("name") or guid),
                properties={"mac_only": "true"},
            )
            graph.add_process(node)
        node.properties["mac_covered"] = "true"
        return node

    def _apply_pipeline_facts(
        self, node: ProcessNode, pipeline: dict, coverage: MacCoverage
    ) -> None:
        pipeline_type = str(pipeline.get("pipelineType") or "").strip()
        sub_type = str(pipeline.get("subType") or "").strip()
        if pipeline_type:
            node.properties["mac_pipeline_type"] = pipeline_type
        if sub_type:
            node.properties["mac_sub_type"] = sub_type
            derived = _KIND_BY_SUBTYPE.get(sub_type)
            if derived:
                node.properties["mac_kind"] = derived
                coverage.kind_derived += 1
            else:
                node.properties["mac_kind_rider"] = sub_type
                coverage.kind_riders += 1

        owner_seal = str(pipeline.get("ownerSealId") or "").strip()
        if owner_seal:
            node.properties["mac_owner_seal"] = owner_seal
            coverage.seal_facts += 1
            g15_seal = node.properties.get("seal", "")
            if g15_seal and g15_seal != owner_seal:
                coverage.seal_disagreements += 1

    def _apply_dataset_flow(
        self, pid: str, flow: dict, graph: LineageGraph, coverage: MacCoverage
    ) -> None:
        for list_key, rel_type in (
            ("inputDatasets", "READS_FROM"),
            ("outputDatasets", "WRITES_TO"),
        ):
            entries = flow.get(list_key) or []
            if not isinstance(entries, list):
                continue
            for entry in entries:
                if not isinstance(entry, dict):
                    coverage.dataset_no_guid += 1
                    continue
                ds_guid = str(entry.get("guid") or "").strip()
                if not ds_guid:
                    coverage.dataset_no_guid += 1
                    continue
                aid = self._stage_dataset(ds_guid, entry, graph, coverage)
                graph.add_rel(pid, rel_type, aid)
                if rel_type == "READS_FROM":
                    coverage.reads_added += 1
                else:
                    coverage.writes_added += 1

    def _stage_dataset(
        self, ds_guid: str, entry: dict, graph: LineageGraph, coverage: MacCoverage
    ) -> str:
        aid = asset_id(MAC_DATASET_KIND, ds_guid)
        props: dict[str, str] = {}
        for src_key, prop in (("version", "version"), ("zone", "zone"), ("name", "dataset_name")):
            value = str(entry.get(src_key) or "").strip()
            if value:
                props[prop] = value
        existing = graph.data_assets.get(aid)
        if existing is None:
            graph.add_data_asset(
                DataAssetNode(
                    node_id=aid, kind=MAC_DATASET_KIND, location=ds_guid,
                    properties=props,
                )
            )
            coverage.datasets_added += 1
        else:
            # first-seen wins (setdefault semantics); a differing version is
            # curation material, not a new node — G22 clause f owns
            # version-as-identity
            old_version = existing.properties.get("version", "")
            new_version = props.get("version", "")
            if old_version and new_version and old_version != new_version:
                coverage.dataset_version_conflicts += 1
        return aid
