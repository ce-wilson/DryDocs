"""Out-of-repo data root — where big/confidential source payloads live (G19).

The logs idiom (:mod:`drydocs_core.run_log` — ``~/logs/DryDocs``,
env-overridable) applied to DATA: bundles and other large or
Internal-Confidential source payloads get a real home OUTSIDE the project
tree, and the repo carries only the pointer. ``internal-local/`` remains the
in-tree hand-carry WORKING area (pointers, notes) — never the payload store.

    DRYDOCS_DATA_ROOT   data directory for all out-of-repo source payloads;
                        default ``~/data/DryDocs``. Created on demand.

Per-source subfolders hang off the root — the rua landing zone (user call
2026-07-21: bundle output is unstructured and can be big, so it lives beside
the logs, not in the tree):

    <root>/rua/incoming/            collected rua_*.tar.gz bundles, as carried
    <root>/rua/extracted/<bundle>/  one dir per unpacked bundle

Payloads under the root may hold real hostnames, uids, home paths, and
profile/script copies (Internal-Confidential) — DATA NEVER ENTERS THE REPO;
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
