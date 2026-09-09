"""Emit the registered sources as DataHub assets — an MCP file in the file-sink
shape, importable with ``datahub lite import --file`` (or ingested by the
``file`` source into any sink).

The repo imports nothing from ``datahub``: the file-sink JSON is a documented
contract (``examples/mce_files/*.json`` in the DataHub source, Apache-2.0) and
writing it directly keeps DataHub an operator-side tool, installed in its own
environment. What is emitted, per registry row:

* one **container** per SYSTEM (``containerProperties`` carrying the row's
  layer, classification, binding; ``dataPlatformInstance``; ``subTypes``
  ``Source system``; ``status``),
* one **dataset** per DATASET (``datasetProperties`` whose ``customProperties``
  are the five descriptor axes, the declared ``wired`` fact and its reason (CFG13)
  plus the DryDocs id and URN; ``container``
  pointing at its system; ``globalTags`` — one tag per axis value, one
  ``<prefix>.wired.<true|false>`` tag (axes page C2: ``confirmed`` on an asset means
  the semantic ruling only, so the wiring fact is its own tag), plus
  ``<prefix>.synthetic`` when a stand-in exists; ``subTypes`` from the format;
  ``status``; and ``schemaMetadata`` from the synthetic CSV headers when a
  generated table exists, every field ``StringType`` because the CSVs are text),
* one **tag** entity per tag urn used.

Deterministic: the list is ordered (systems, then datasets, then tags, each by
id), ``systemMetadata.lastObserved`` is the config's fixed ``observed_at``, and
the JSON is written sorted. Two runs over one config produce one file.
"""

from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Iterable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from drydocs.source_registration.synthetic import Table
from drydocs_core.source_descriptors import Descriptor, SourceDescriptors

RUN_ID = "drydocs-source-registration"

SUBTYPE_BY_FORMAT = {
    "db": "Table",
    "csv": "File",
    "ascii": "File",
    "json": "File",
    "archive": "Archive",
}


def _observed_ms(descriptors: SourceDescriptors) -> int:
    raw = str(descriptors.datahub.get("observed_at", "1970-01-01T00:00:00Z"))
    dt = datetime.fromisoformat(raw.replace("Z", "+00:00")).astimezone(UTC)
    return int(dt.timestamp() * 1000)


def dataset_name(source_id: str) -> str:
    """The DataHub dataset NAME for a DryDocs id. Only ``[A-Za-z0-9._-]``
    survive, so ``controlm@[db].psgmgr.cm_def_vtab`` -> ``controlm__db_.psgmgr.cm_def_vtab``.
    The true id rides in ``customProperties.drydocs_id``; this only has to be
    unique and urn-safe (guarded by tests/unit/test_synthetic_sources.py)."""
    return re.sub(r"[^A-Za-z0-9._-]", "_", source_id)


def dataset_urn(descriptors: SourceDescriptors, desc: Descriptor) -> str:
    platform = descriptors.platform_for(desc.system_id)
    env = descriptors.datahub.get("env", "PROD")
    return f"urn:li:dataset:(urn:li:dataPlatform:{platform},{dataset_name(desc.source_id)},{env})"


def container_urn(system_id: str) -> str:
    guid = hashlib.md5(f"drydocs:system:{system_id}".encode()).hexdigest()  # - id, not security
    return f"urn:li:container:{guid}"


def tag_urn(descriptors: SourceDescriptors, *parts: str) -> str:
    prefix = descriptors.datahub.get("tag_prefix", "drydocs")
    return "urn:li:tag:" + ".".join((prefix, *parts))


def _mcp(entity_type: str, urn: str, aspect_name: str, aspect: dict, observed: int) -> dict:
    return {
        "entityType": entity_type,
        "entityUrn": urn,
        "changeType": "UPSERT",
        "aspectName": aspect_name,
        "aspect": {"json": aspect},
        "systemMetadata": {
            "lastObserved": observed,
            "runId": RUN_ID,
            "lastRunId": "no-run-id-provided",
        },
    }


def _schema_aspect(platform: str, tables: list[Table]) -> dict:
    fields = []
    for t in tables:
        stem = Path(t.name).stem
        for col in t.header:
            fields.append(
                {
                    "fieldPath": f"{stem}.{col}",
                    "nullable": True,
                    "type": {"type": {"com.linkedin.schema.StringType": {}}},
                    "nativeDataType": "VARCHAR",
                    "recursive": False,
                    "isPartOfKey": False,
                }
            )
    return {
        "schemaName": ",".join(Path(t.name).stem for t in tables),
        "platform": f"urn:li:dataPlatform:{platform}",
        "version": 0,
        "created": {"time": 0, "actor": "urn:li:corpuser:unknown"},
        "lastModified": {"time": 0, "actor": "urn:li:corpuser:unknown"},
        "hash": "",
        "platformSchema": {"com.linkedin.schema.OtherSchema": {"rawSchema": ""}},
        "fields": fields,
    }


def build_mcps(
    descriptors: SourceDescriptors,
    tables: Iterable[Table] = (),
) -> list[dict[str, Any]]:
    observed = _observed_ms(descriptors)
    by_source: dict[str, list[Table]] = {}
    for t in tables:
        by_source.setdefault(t.source_id, []).append(t)
    for lst in by_source.values():
        lst.sort(key=lambda t: t.name)

    mcps: list[dict] = []
    tags_used: dict[str, str] = {}

    # -- systems as containers -------------------------------------------------
    for system in descriptors.systems():
        urn = container_urn(system.id)
        platform = descriptors.platform_for(system.id)
        props = {
            "system_id": system.id,
            "layer": str(system.data.get("layer") or ""),
            "classification": str(system.data.get("classification") or ""),
            "binding": str(system.data.get("binding") or ""),
        }
        mcps.append(
            _mcp(
                "container",
                urn,
                "containerProperties",
                {
                    "name": str(system.data.get("name") or system.id),
                    "customProperties": props,
                },
                observed,
            )
        )
        mcps.append(
            _mcp(
                "container",
                urn,
                "dataPlatformInstance",
                {"platform": f"urn:li:dataPlatform:{platform}"},
                observed,
            )
        )
        mcps.append(_mcp("container", urn, "subTypes", {"typeNames": ["Source system"]}, observed))
        mcps.append(_mcp("container", urn, "status", {"removed": False}, observed))

    # -- datasets ---------------------------------------------------------------
    for desc in descriptors.all():
        urn = dataset_urn(descriptors, desc)
        platform = descriptors.platform_for(desc.system_id)
        synthetic = by_source.get(desc.source_id, [])
        props = {
            **desc.axis_values(),
            "drydocs_id": desc.source_id,
            "drydocs_urn": desc.urn,
            "system": desc.system_id,
            "confirmed": str(desc.confirmed).lower(),
            "wired": str(desc.wired).lower(),
            "wired_reason": desc.wired_reason or "",
            "derived": str(desc.derived).lower(),
            "synthetic_files": ",".join(t.name for t in synthetic),
        }
        mcps.append(
            _mcp(
                "dataset",
                urn,
                "datasetProperties",
                {
                    "name": desc.source_id,
                    "qualifiedName": desc.urn,
                    "customProperties": props,
                    "tags": [],
                },
                observed,
            )
        )
        mcps.append(
            _mcp(
                "dataset", urn, "container", {"container": container_urn(desc.system_id)}, observed
            )
        )
        mcps.append(
            _mcp(
                "dataset",
                urn,
                "dataPlatformInstance",
                {"platform": f"urn:li:dataPlatform:{platform}"},
                observed,
            )
        )
        mcps.append(
            _mcp(
                "dataset",
                urn,
                "subTypes",
                {"typeNames": [SUBTYPE_BY_FORMAT.get(desc.format, "Dataset")]},
                observed,
            )
        )
        tag_urns = [tag_urn(descriptors, axis, value) for axis, value in desc.axis_values().items()]
        for axis, value in desc.axis_values().items():
            tags_used[tag_urn(descriptors, axis, value)] = f"{axis} = {value}"
        # CFG13 (source-descriptor-axes C2, 2026-09-09): `confirmed` on the asset means
        # the SEMANTIC ruling only; the wiring fact is its OWN tag, so no tagged asset
        # is ambiguous about which of the two it carries.
        wired_value = str(desc.wired).lower()
        t = tag_urn(descriptors, "wired", wired_value)
        tag_urns.append(t)
        tags_used[t] = (
            "wired = true (the pipeline that reads this dataset is built on this side)"
            if desc.wired
            else "wired = false (declared with a reason on the descriptor; not built here)"
        )
        if synthetic:
            t = tag_urn(descriptors, "synthetic")
            tag_urns.append(t)
            tags_used[t] = "a generated stand-in exists (record_origin = sample)"
        mcps.append(
            _mcp("dataset", urn, "globalTags", {"tags": [{"tag": t} for t in tag_urns]}, observed)
        )
        mcps.append(_mcp("dataset", urn, "status", {"removed": False}, observed))
        if synthetic:
            mcps.append(
                _mcp(
                    "dataset", urn, "schemaMetadata", _schema_aspect(platform, synthetic), observed
                )
            )

    # -- tags -------------------------------------------------------------------
    for urn in sorted(tags_used):
        mcps.append(
            _mcp(
                "tag",
                urn,
                "tagProperties",
                {"name": urn.rsplit(":", 1)[1], "description": tags_used[urn]},
                observed,
            )
        )
    return mcps


def write_mcp_file(
    descriptors: SourceDescriptors, path: Path, tables: Iterable[Table] = ()
) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(build_mcps(descriptors, tables), indent=2, sort_keys=True) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    return path
