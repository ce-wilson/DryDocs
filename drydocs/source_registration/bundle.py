"""The gzip bundle: one repo-tracked file holding every synthetic CSV, extracted
on demand into the landing zones the loaders read.

Why a bundle and not loose files. ``drydocs/data/`` is gitignored and the tracked
fixtures there are grandfathered; one force-added ``.json.gz`` is a single
publish-boundary decision instead of a dozen. It is ``never-port`` (PORT-MANIFEST),
so every consumer tree lacks it — which is why every test that reads it skips
on absence rather than failing (``tests/unit/test_synthetic_sources.py``).

Byte-stable: the JSON is sorted and compact, the gzip header carries
``mtime=0`` and no filename, so two runs over one config produce one file and a
diff on the bundle means the generator or the config changed.

Extraction never writes into the repo tree: a ``base: repo`` landing zone
(``internal/server-inventory/``) is written under ``<out_root>/repo/<drop_dir>``
instead, and a db-carried dataset's CSV mirror goes under ``<out_root>/<mirror_dir>``.
"""

from __future__ import annotations

import gzip
import json
from dataclasses import dataclass
from pathlib import Path

from drydocs.source_registration.synthetic import SyntheticSources, Table
from drydocs_core.data_root import resolve_data_root
from drydocs_core.landing_zones import BASE_REPO, LandingZone, manual_zones
from drydocs_core.repo_paths import repo_root
from drydocs_core.source_descriptors import SourceDescriptors

BUNDLE_SCHEMA = "drydocs.synthetic-sources.v1"
REPO_ROOT = repo_root(Path(__file__).resolve().parents[2])


@dataclass(frozen=True)
class Extracted:
    source_id: str
    name: str
    path: Path
    placement: str


def bundle_path(descriptors: SourceDescriptors) -> Path:
    rel = descriptors.synthetic.get("bundle", "drydocs/data/samples/synthetic-sources.json.gz")
    return REPO_ROOT / rel


def pack(tables: tuple[Table, ...], seed: int) -> bytes:
    payload = {
        "schema": BUNDLE_SCHEMA,
        "seed": seed,
        "files": [
            {"source_id": t.source_id, "name": t.name, "content": t.to_csv()}
            for t in sorted(tables, key=lambda t: (t.source_id, t.name))
        ],
    }
    text = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return gzip.compress(text.encode("utf-8"), compresslevel=9, mtime=0)


def write_bundle(descriptors: SourceDescriptors, path: Path | None = None) -> Path:
    gen = SyntheticSources(descriptors)
    out = path or bundle_path(descriptors)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(pack(gen.tables(), gen.seed))
    return out


def read_bundle(path: Path) -> dict:
    with gzip.open(path, "rb") as fh:
        doc = json.loads(fh.read().decode("utf-8"))
    if doc.get("schema") != BUNDLE_SCHEMA:
        raise ValueError(f"{path}: unexpected bundle schema {doc.get('schema')!r}")
    return doc


def _targets(descriptors: SourceDescriptors, out_root: Path) -> dict[str, tuple[Path, str]]:
    """source_id -> (directory, placement) for every planned dataset."""
    zones: dict[str, LandingZone] = {z.source_id: z for z in manual_zones()}
    mirror = out_root / descriptors.synthetic.get("mirror_dir", "psgmgr-mirror")
    targets: dict[str, tuple[Path, str]] = {}
    for plan in descriptors.synthetic_plans():
        zone = zones.get(plan.source_id)
        if plan.placement == "zone" and zone is not None:
            if zone.base == BASE_REPO:
                targets[plan.source_id] = (out_root / "repo" / zone.drop_dir, "zone")
            else:
                targets[plan.source_id] = (out_root / zone.drop_dir, "zone")
        else:
            targets[plan.source_id] = (mirror, "mirror")
    return targets


def extract(
    descriptors: SourceDescriptors,
    *,
    bundle: Path | None = None,
    out_root: Path | None = None,
) -> tuple[Extracted, ...]:
    """Write every bundled CSV to its target directory. ``out_root`` defaults to
    ``DRYDOCS_DATA_ROOT`` (raises ``DataRootNotSetError`` when unset)."""
    src = bundle or bundle_path(descriptors)
    doc = read_bundle(src)
    root = Path(out_root) if out_root is not None else resolve_data_root()
    targets = _targets(descriptors, root)
    written: list[Extracted] = []
    for entry in doc["files"]:
        directory, placement = targets[entry["source_id"]]
        directory.mkdir(parents=True, exist_ok=True)
        path = directory / entry["name"]
        # newline="" so the bundled "\n" rows land unchanged on every platform
        with path.open("w", encoding="utf-8", newline="") as fh:
            fh.write(entry["content"])
        written.append(Extracted(entry["source_id"], entry["name"], path, placement))
    return tuple(written)
