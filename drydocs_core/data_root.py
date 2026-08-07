"""Out-of-repo data root — where big/confidential source payloads live (G19).

The logs idiom (:mod:`drydocs_core.run_log` — ``~/logs/DryDocs``,
env-overridable) applied to DATA: bundles and other large or
confidential (Internal, J23) source payloads get a real home OUTSIDE the project
tree, and the repo carries only the pointer. ``internal-local/`` remains the
in-tree hand-carry WORKING area (pointers, notes) — never the payload store.

    DRYDOCS_DATA_ROOT   data directory for all out-of-repo source payloads;
                        default ``~/data/DryDocs``. Created on demand.

Per-source subfolders hang off the root — the rua landing zone (user call
2026-07-21: bundle output is unstructured and can be big, so it lives beside
the logs, not in the tree):

    <root>/rua/incoming/            collected rua_*.tar.gz bundles, as carried
    <root>/rua/extracted/<bundle>/  one dir per unpacked bundle

and the DPL registry landing zone (G25 — per-SEAL Swagger exports of the
taxonomy registry; real SEALs + GUIDs + lifecycle state):

    <root>/dpl-registry/<seal>/     pipeline_id.json / dataset_id.json per SEAL

and the data-catalog landing zone (G42 — full-pull exports of the curated
dataset/distribution views; real dataset names, GUIDs, app ids, emails,
buckets — plus the evidence screenshots, which never sit in the repo tree
even gitignored):

    <root>/catalog/                 view exports (CSV)
    <root>/catalog/screenshots/     SME evidence captures

Payloads under the root may hold real hostnames, uids, home paths, and
profile/script copies (confidential (Internal, J23)) — DATA NEVER ENTERS THE REPO;
``tests/unit/test_data_root.py`` sweeps the tree to enforce it.
"""

from __future__ import annotations

import os
from pathlib import Path

DEFAULT_DATA_ROOT = Path.home() / "data" / "DryDocs"
DATA_ROOT_ENV = "DRYDOCS_DATA_ROOT"


def resolve_data_root() -> Path:
    """The configurable data root: DRYDOCS_DATA_ROOT > ``~/data/DryDocs``."""
    raw = os.environ.get(DATA_ROOT_ENV, "").strip()
    return Path(raw) if raw else DEFAULT_DATA_ROOT


def source_dir(*parts: str, create: bool = False) -> Path:
    """A per-source subfolder under the data root (``source_dir('rua', 'incoming')``)."""
    path = resolve_data_root().joinpath(*parts)
    if create:
        path.mkdir(parents=True, exist_ok=True)
    return path


def rua_incoming_dir(*, create: bool = False) -> Path:
    """Landing zone for collected ``rua_*.tar.gz`` bundles."""
    return source_dir("rua", "incoming", create=create)


def rua_extracted_dir(bundle_name: str | None = None, *, create: bool = False) -> Path:
    """Unpack area — one directory per bundle when ``bundle_name`` is given."""
    parts = ("rua", "extracted") + ((bundle_name,) if bundle_name else ())
    return source_dir(*parts, create=create)


def dpl_registry_dir(seal: str | None = None, *, create: bool = False) -> Path:
    """Landing zone for per-SEAL DPL registry Swagger exports (G25)."""
    parts = ("dpl-registry",) + ((seal,) if seal else ())
    return source_dir(*parts, create=create)


def catalog_dir(sub: str | None = None, *, create: bool = False) -> Path:
    """Landing zone for Snowflake data-catalog view exports (G42);
    ``catalog_dir("screenshots")`` is the evidence-capture area."""
    parts = ("catalog",) + ((sub,) if sub else ())
    return source_dir(*parts, create=create)


def vendor_docs_dir(vendor_tree: str | None = None, *, create: bool = False) -> Path:
    """Landing zone for VERBATIM external-vendor documentation captures.

    Vendor help trees are the vendor's own words, not our summary — the
    ``external/ServiceNow/extracted/`` .gitignore precedent generalized to a
    real out-of-repo home. Our publishable artifacts stay in
    ``external/orchestration/`` (summaries we wrote); the raw capture lands
    here and is never committed:

        <root>/vendor-docs/<tree>/pages/     captured .htm, one file per topic
        <root>/vendor-docs/<tree>/capture-manifest.json

    ``vendor_tree`` is the capture id from the scraper's TREES table (e.g.
    ``bmc-controlm-9.0.20-utilities``).
    """
    parts = ("vendor-docs",) + ((vendor_tree,) if vendor_tree else ())
    return source_dir(*parts, create=create)


def context_intake_dir(*, create: bool = False) -> Path:
    """Landing zone for SME context-intake evidence + records (O46 — .msg/.json/.txt
    uploads with real names and incident detail, classification Internal; the
    intake.db record store sits beside the per-intake evidence dirs):

        <root>/context-intake/intake.db
        <root>/context-intake/<intake_id>/<filename>

    The 2026-08-06 storage ruling keys on this being ONE configured base path:
    records carry sha256 digests + relative keys only, so local → Linux share →
    object store is a config change, never a code change."""
    return source_dir("context-intake", create=create)


def controlm_xml_dir(*, create: bool = False) -> Path:
    """Landing zone for Control-M XML definition exports (G47 — the
    9.0.21.300 config SoR; real folder/job/variable values are Internal).
    No filename-fingerprint tree sweep exists for these: exports are
    arbitrarily-named generic ``.xml``, so the guard is this landing-zone
    convention itself plus the classification on the source entry."""
    return source_dir("controlm-xml", create=create)
