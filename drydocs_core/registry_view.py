"""The class-organized view of the source registry, and the predicates it derives (N26).

WHAT THIS ANSWERS. The load map answered "which loader writes this dataset";
this answers "what IS this dataset" — read from the registry's own axes rather
than from the loader that happens to consume it. The organizing order is the
BDAT layer (a property of the SYSTEM, gate source-registry-v2, 2026-07-31) →
the business application the system belongs to (its application id, a standing
placeholder on every committed row — D1 amendment) → the ONTOLOGY CLASS the
taxonomy-ontology map has ruled for the dataset → the dataset itself. Loaders
are demoted to a count.

NO NEW REGISTRY FIELD. Every value here is DERIVED from fields the registry
already carries, because gate clause D2 (`registry-wiring-readiness`, N10,
unsigned) fences the schema until the SME signs, and because the identity
review (`docs/design/source-registry-identity-review.md`, "what we deliberately
do not take") ruled replica-ness a predicate over `origin`/`system`/`authority`
rather than a column. Four predicates, each a pure function of the row:

- the ONTOLOGY CLASS is the set of `neo4j_label`s over the dataset's map
  entries in a RULED status (`applied` or `confirmed`). A dataset with no such
  entry is UNCLASSIFIED, and says how many entries are still `proposed`.
  `asset_type` is deliberately NOT the class: it is `dcat:Dataset` on every row
  today, a constant, and a constant classifies nothing — the header reports it
  as such rather than rendering thirty identical chips.
- the APPLICATION-ID STATE is `placeholder` / `declared` / `absent`, read from
  the bracket grammar the registry uses for standing placeholders.
- REPLICA-NESS: `origin != system` is the replica predicate; `authority: ADS`
  (the firm's own designation for "a copy approved for redistribution") is its
  corroboration. The two are reported together, never collapsed, so a row where
  they disagree is visible as a row where they disagree.
- the LAYER x CATEGORY MATRIX: the BDAT layer the system carries crossed with
  the `taxonomy_category` the dataset carries. A singleton cell is flagged:
  that is the derivable form of the DPL oddness (a "Data Asset" under the
  `technology` layer occurs exactly once, at `dpl:dataset-registry`), and it
  flags any future row in the same position without anyone typing the id.

WHY CORE. Pure resolve over config facts, no graph, no component import — the
placement test of ADR 0002-A §2. Two consumers need it: `scripts/render_load_map.py`
(the committed view) and the `drydocs registry` verb in `drydocs/cli_schema.py`
(the live answer), and a script cannot be imported by the package. Loader facts
are HANDED IN as plain dicts (`loaders_by_source`), the injected-seam shape
`docs_verify.py` uses, so this module never sees `LOADER_REGISTRY`.

THE STAMP (acceptance g). A committed render cannot carry HEAD's sha — the
drift guard asserts committed == regenerated and the session ritual diffs the
render after every change, so a commit sha in the file would go stale at the
commit that writes it. What the render CAN carry is the content identity of its
inputs: the git BLOB id of each input file (`sha1("blob <len>\\0" + bytes)`,
identical to `git hash-object` because `.gitattributes` normalizes every text
file to LF) plus one digest over the sorted `path blob` lines. That resolves to
a commit with `git log --find-object=<blob>` and changes exactly when an input
changes. The live verb adds HEAD/branch/dirty beside the same digest, so the
two surfaces join on it.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path
from typing import Any

UNCLASSIFIED = "UNCLASSIFIED"
RULED_STATUSES: frozenset[str] = frozenset({"applied", "confirmed"})
ADS = "ADS"
NO_LAYER = "no layer"
NO_CATEGORY = "no category"

APPLICATION_ID_PLACEHOLDER = "placeholder"
APPLICATION_ID_DECLARED = "declared"
APPLICATION_ID_ABSENT = "absent"

REPLICA = "replica"
REPLICA_UNCORROBORATED = "replica-uncorroborated"
ORIGINAL = "original"
ADS_WITHOUT_DISTINCT_ORIGIN = "ads-without-distinct-origin"


# ---- the four predicates ------------------------------------------------------


def application_id_state(value: object) -> str:
    """`placeholder` for the registry's `[bracketed]` standing value, `declared`
    for anything else non-empty, `absent` for None / empty / `~`."""
    if value is None:
        return APPLICATION_ID_ABSENT
    text = str(value).strip()
    if text in ("", "~"):
        return APPLICATION_ID_ABSENT
    if text.startswith("[") and text.endswith("]"):
        return APPLICATION_ID_PLACEHOLDER
    return APPLICATION_ID_DECLARED


def replica_state(dataset: Mapping[str, Any]) -> dict[str, Any]:
    """Replica-ness as two facts kept apart: the predicate (`origin != system`)
    and its corroboration (`authority: ADS`). Never a single boolean."""
    origin = dataset.get("origin")
    carrier = dataset.get("system")
    authority = dataset.get("authority")
    corroborated = authority == ADS
    if origin and carrier and origin != carrier:
        state = REPLICA if corroborated else REPLICA_UNCORROBORATED
    elif corroborated:
        state = ADS_WITHOUT_DISTINCT_ORIGIN
    else:
        state = ORIGINAL
    return {
        "state": state,
        "origin": origin,
        "carrier": carrier,
        "corroboration": f"authority: {ADS}" if corroborated else None,
    }


def acquisition_summary(dataset: Mapping[str, Any]) -> dict[str, Any]:
    """The `acquisition` block flattened to one fixed shape (both live shapes —
    `mode+via` automated, `mode+format+drop_dir+drop_dir_base` manual — fill the
    same five keys; absent ones are null so the render is one column wide)."""
    acq = dataset.get("acquisition") or {}
    return {
        "mode": acq.get("mode") or "undeclared",
        "via": acq.get("via"),
        "format": acq.get("format"),
        "drop_dir": acq.get("drop_dir"),
        "drop_dir_base": acq.get("drop_dir_base"),
    }


def ontology_class(map_rows: Iterable[Mapping[str, Any]]) -> dict[str, Any]:
    """The ruled ontology class(es) of a dataset from its map entries.

    `map_rows` are the load-map's per-source mapping rows (`id`, `status`,
    `label`). Only RULED statuses classify; `proposed` is counted, `rejected`
    is neither. No ruled entry → UNCLASSIFIED, with the reason spelled out."""
    rows = list(map_rows)
    classes = sorted(
        {r["label"] for r in rows if r.get("status") in RULED_STATUSES and r.get("label")}
    )
    pending = sum(1 for r in rows if r.get("status") == "proposed")
    if classes:
        return {"state": "classified", "classes": classes, "pending": pending, "reason": None}
    if pending:
        reason = f"{pending} map entr{'y' if pending == 1 else 'ies'} proposed, none ruled"
    elif rows:
        reason = "map entries exist but none is applied or confirmed"
    else:
        reason = "no map entry - asset_type default only"
    return {"state": UNCLASSIFIED, "classes": [], "pending": pending, "reason": reason}


# ---- the matrix ---------------------------------------------------------------


def layer_category_matrix(
    datasets: Iterable[Mapping[str, Any]], system_by_id: Mapping[str, Mapping[str, Any]]
) -> dict[str, Any]:
    """BDAT layer (from the carrier system) x `taxonomy_category` (from the
    dataset), every cell listing its dataset ids. `singletons` are the cells
    holding exactly one dataset; `displaced` are the singletons whose category
    has its home (two or more rows) under another layer — the derivable form of
    "this row is odd"."""
    cells: dict[str, dict[str, list[str]]] = {}
    for d in datasets:
        layer = (system_by_id.get(d.get("system") or "") or {}).get("layer") or NO_LAYER
        category = d.get("taxonomy_category") or NO_CATEGORY
        cells.setdefault(layer, {}).setdefault(category, []).append(d["id"])
    layers = sorted(cells)
    categories = sorted({c for row in cells.values() for c in row})
    for row in cells.values():
        for ids in row.values():
            ids.sort()
    singletons = [
        {"layer": layer, "category": category, "dataset": ids[0]}
        for layer in layers
        for category, ids in sorted(cells[layer].items())
        if len(ids) == 1
    ]
    # A singleton whose category has a HOME elsewhere — two or more rows under
    # one other layer — is displaced: the category is established there and this
    # row sits alone against it. That is the DPL oddness stated as a predicate
    # ("Data Asset" is a `data`-layer category on four rows and appears once under
    # `technology`), and it flags any later row in the same position by rule.
    displaced = []
    for s in singletons:
        elsewhere = {
            layer: len(cells[layer][s["category"]])
            for layer in layers
            if layer != s["layer"] and s["category"] in cells[layer]
        }
        home = max(elsewhere, key=lambda k: (elsewhere[k], k), default=None)
        if home is not None and elsewhere[home] >= 2:
            displaced.append({**s, "home_layer": home, "home_rows": elsewhere[home]})
    return {
        "layers": layers,
        "categories": categories,
        "cells": {layer: dict(sorted(cells[layer].items())) for layer in layers},
        "singletons": singletons,
        "displaced": displaced,
    }


def constant_fields(datasets: Iterable[Mapping[str, Any]], field: str) -> dict[str, Any]:
    """Whether `field` takes ONE value across every dataset row that carries it —
    `asset_type` today — so the header can say "a constant, not a classification"
    from a measurement rather than an assertion."""
    values: dict[str, int] = {}
    total = 0
    for d in datasets:
        total += 1
        v = d.get(field)
        if v is not None:
            values[str(v)] = values.get(str(v), 0) + 1
    if len(values) == 1:
        ((value, count),) = values.items()
        return {"field": field, "constant": True, "value": value, "rows": count, "of": total}
    return {
        "field": field,
        "constant": False,
        "value": None,
        "rows": sum(values.values()),
        "of": total,
    }


# ---- the class view -----------------------------------------------------------


def dataset_derivations(
    dataset: Mapping[str, Any],
    system: Mapping[str, Any] | None,
    map_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """The per-dataset derived block the load-map source row carries."""
    return {
        "layer": (system or {}).get("layer"),
        "taxonomy_category": dataset.get("taxonomy_category"),
        "acquisition": acquisition_summary(dataset),
        "replica": replica_state(dataset),
        "ontology_class": ontology_class(map_rows),
    }


def class_view(
    systems: Iterable[Mapping[str, Any]],
    datasets: Iterable[Mapping[str, Any]],
    mappings_by_source: Mapping[str, Iterable[Mapping[str, Any]]],
    loaders_by_source: Mapping[str, Iterable[Mapping[str, Any]]],
    doc_sources: Iterable[Mapping[str, Any]] = (),
) -> list[dict[str, Any]]:
    """layer → system (application) → ontology class → datasets.

    Systems are grouped under their BDAT layer; within a system, datasets are
    grouped by their ruled class (UNCLASSIFIED last). Loaders appear as a count
    per dataset — the per-source section of the load map keeps the detail.
    Doc-ledger corpora carry no system and no layer; they are appended as one
    `no layer` group so the view accounts for every registered source."""
    system_list = list(systems)
    system_by_id = {s["id"]: s for s in system_list}
    datasets_by_system: dict[str, list[Mapping[str, Any]]] = {}
    for d in datasets:
        datasets_by_system.setdefault(d.get("system") or "", []).append(d)

    def _dataset_row(d: Mapping[str, Any], system: Mapping[str, Any] | None) -> dict[str, Any]:
        derived = dataset_derivations(d, system, mappings_by_source.get(d["id"], ()))
        return {
            "id": d["id"],
            "taxonomy_category": derived["taxonomy_category"],
            "acquisition_mode": derived["acquisition"]["mode"],
            "authority": d.get("authority"),
            "replica": derived["replica"]["state"],
            "confirmed": bool(d.get("confirmed")),
            "loader_count": len(list(loaders_by_source.get(d["id"], ()))),
            "ontology_class": derived["ontology_class"],
        }

    def _class_groups(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        by_class: dict[str, list[dict[str, Any]]] = {}
        for r in rows:
            oc = r["ontology_class"]
            key = " + ".join(oc["classes"]) if oc["classes"] else UNCLASSIFIED
            by_class.setdefault(key, []).append(r)
        ordered = sorted(k for k in by_class if k != UNCLASSIFIED)
        if UNCLASSIFIED in by_class:
            ordered.append(UNCLASSIFIED)
        return [
            {
                "ontology_class": key,
                "datasets": sorted(by_class[key], key=lambda r: r["id"]),
            }
            for key in ordered
        ]

    layers: dict[str, list[dict[str, Any]]] = {}
    for s in system_list:
        rows = [_dataset_row(d, s) for d in datasets_by_system.get(s["id"], [])]
        layers.setdefault(s.get("layer") or NO_LAYER, []).append(
            {
                "system": s["id"],
                "name": s.get("name"),
                "application_id": s.get("seal_id"),
                "application_id_state": application_id_state(s.get("seal_id")),
                "dataset_count": len(rows),
                "classes": _class_groups(rows),
            }
        )
    orphan_rows = [
        _dataset_row(d, None)
        for sid, ds in datasets_by_system.items()
        if sid not in system_by_id
        for d in ds
    ]
    doc_rows = [_dataset_row(d, None) for d in doc_sources]
    if orphan_rows or doc_rows:
        layers.setdefault(NO_LAYER, [])
        if orphan_rows:
            layers[NO_LAYER].append(
                {
                    "system": None,
                    "name": "datasets naming no registered system",
                    "application_id": None,
                    "application_id_state": APPLICATION_ID_ABSENT,
                    "dataset_count": len(orphan_rows),
                    "classes": _class_groups(orphan_rows),
                }
            )
        if doc_rows:
            layers[NO_LAYER].append(
                {
                    "system": None,
                    "name": "doc-ledger corpora (config/doc-source-registry.yaml)",
                    "application_id": None,
                    "application_id_state": APPLICATION_ID_ABSENT,
                    "dataset_count": len(doc_rows),
                    "classes": _class_groups(doc_rows),
                }
            )
    ordered_layers = sorted(k for k in layers if k != NO_LAYER)
    if NO_LAYER in layers:
        ordered_layers.append(NO_LAYER)
    return [
        {
            "layer": layer,
            "systems": sorted(
                layers[layer], key=lambda s: (s["system"] is None, s["system"] or "")
            ),
        }
        for layer in ordered_layers
    ]


# ---- the loader binding (the verb's answer) -----------------------------------


def loader_binding(
    loader_name: str,
    *,
    declared: str | None,
    effective: str | None,
    bound_loaders: Mapping[str, str | None],
    dataset: Mapping[str, Any] | None,
    system: Mapping[str, Any] | None,
    map_rows: Iterable[Mapping[str, Any]],
) -> dict[str, Any]:
    """What one loader writes, resolved the way the confirmed-gate resolves it.

    `declared` is the class's own `source_id`; `effective` is what
    `SourceRegistry.effective_source_id` returns after the per-side overlay;
    `bound_loaders` maps every loader name to ITS effective id, so the
    "other loaders bound to the same dataset" list is computed here and the
    third-loader case (acceptance f) is one more key in that mapping."""
    others = sorted(n for n, sid in bound_loaders.items() if sid == effective and n != loader_name)
    return {
        "loader": loader_name,
        "declared_source_id": declared,
        "effective_source_id": effective,
        "overlay_applied": effective != declared,
        "dataset": None if dataset is None else dataset_derivations(dataset, system, map_rows),
        "system": None
        if system is None
        else {
            "id": system.get("id"),
            "name": system.get("name"),
            "layer": system.get("layer"),
            "application_id": system.get("seal_id"),
            "application_id_state": application_id_state(system.get("seal_id")),
        },
        "other_loaders_bound_here": others,
    }


# ---- the stamp ----------------------------------------------------------------


def git_blob_id(data: bytes) -> str:
    """git's blob object id for `data` — sha1 over `blob <len>\\0<bytes>`."""
    h = hashlib.sha1()
    h.update(b"blob %d\0" % len(data))
    h.update(data)
    return h.hexdigest()


def _normalized_bytes(path: Path) -> bytes:
    # `.gitattributes` is `* text=auto eol=lf`, so the blob git stores is the
    # LF form; a CRLF checkout would otherwise hash to an id git never wrote.
    return path.read_bytes().replace(b"\r\n", b"\n")


def input_provenance(root: Path, inputs: Iterable[str]) -> dict[str, Any]:
    """Content identity of the render's inputs: per-file blob ids (directories
    expand to their sorted *.yaml files) and one digest over the sorted
    `path blob` lines. Paths are repo-relative POSIX so the stamp is the same
    on every machine that holds the same content."""
    files: list[Path] = []
    for rel in inputs:
        p = root / rel
        if p.is_dir():
            files.extend(sorted(p.glob("*.yaml"), key=lambda q: q.as_posix()))
        else:
            files.append(p)
    rows = sorted(
        (
            {"path": f.relative_to(root).as_posix(), "blob": git_blob_id(_normalized_bytes(f))}
            for f in files
            if f.is_file()
        ),
        key=lambda r: r["path"],
    )
    digest = hashlib.sha1("\n".join(f"{r['path']} {r['blob']}" for r in rows).encode("utf-8"))
    return {
        "inputs": rows,
        "digest": digest.hexdigest(),
        "how_to_resolve": "git log --find-object=<blob> names the commits that carry an input",
    }
