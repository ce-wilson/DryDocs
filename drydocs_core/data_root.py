"""Out-of-repo data root — where big/confidential source payloads live (G19).

The logs idiom (:mod:`drydocs_core.run_log` — ``~/logs/DryDocs``,
env-overridable) applied to DATA: bundles and other large or
confidential (Internal, J23) source payloads get a real home OUTSIDE the project
tree, and the repo carries only the pointer. ``internal-local/`` remains the
in-tree hand-carry WORKING area (pointers, notes) — never the payload store.

    DRYDOCS_DATA_ROOT   data directory for all out-of-repo source payloads.
                        MANDATORY since G81 (2026-08-23): unset or empty RAISES
                        :class:`DataRootNotSetError`. There is deliberately no
                        default — the old ``~/data/DryDocs`` fallback silently
                        relocated every read and write when the variable was
                        missing, which is how a write lands on somebody's source
                        data. ``~/data/DryDocs`` remains the CONVENTIONAL place
                        to point it, and nothing resolves to it implicitly.

EVERY PATH HERE IS A DECLARED ZONE WITH A MODE (G81). ``config/data-zones.yaml``
declares the system-owned zones (write/scratch) and the read zones that are not
dataset drops; dataset drops stay in ``config/source-registry.yaml``
(``acquisition.drop_dir``, N12). :mod:`drydocs_core.data_zones` joins the two and
enforces the invariant: no write path may equal, contain or be contained by a
read path. A READ-zone helper below takes no ``create`` argument at all — any
path a create-capable helper may build is write-mode by construction.

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

from pathlib import Path

from drydocs_core.env_refs import UnsetVariableError, resolve_optional

DEFAULT_DATA_ROOT = Path.home() / "data" / "DryDocs"
DATA_ROOT_ENV = "DRYDOCS_DATA_ROOT"


class ReadZoneWriteError(RuntimeError):
    """A write was aimed at a declared READ zone — the G81 incident's shape."""


class DataRootNotSetError(UnsetVariableError):
    """``DRYDOCS_DATA_ROOT`` is unset or empty — G81 (d): never a silent default.

    SUBCLASSES the generic unset-variable error rather than being replaced by it
    (G128 clause (a), decided before any resolver moved). The specific type is
    load-bearing at two catch sites — ``drydocs/cli.py`` and
    ``drydocs/cli_ingest.py`` both catch THIS type to print the data root's own
    remediation. Collapsing every unset variable into one type would have made
    an unset ``NEO4J_PASSWORD`` print a message about the data root, which is a
    regression wearing a refactor's clothes. Subclassing keeps
    ``except UnsetVariableError`` working as the family catch while the specific
    handler stays specific.
    """


def resolve_data_root() -> Path:
    """The data root, from ``DRYDOCS_DATA_ROOT``. UNSET IS AN ERROR (G81 (d)).

    THERE IS NO DEFAULT ANY MORE, and the reason is the whole item: until
    2026-08-23 an unset variable silently relocated every read and every write to
    ``~/data/DryDocs`` — a plausible-looking place a person might also pick by
    hand. So the same command in two shells could target two different trees, and
    a write meant for one landed in the other, with success reported either way.
    Same family as G78's fixture-directory default, one layer down and with worse
    consequences: G78 loaded the wrong data, this could destroy the right data.

    :data:`DEFAULT_DATA_ROOT` is KEPT as the documented conventional location —
    it is what an operator should usually point the variable at, and what the
    error message suggests — but nothing resolves to it implicitly.
    """
    raw, _ = resolve_optional(DATA_ROOT_ENV, where="resolve_data_root()")
    if not raw:
        raise DataRootNotSetError(
            f"{DATA_ROOT_ENV} is not set. Every source drop and every output the "
            "system writes is rooted there, so there is deliberately NO default: "
            "an unset variable used to relocate all of them silently to "
            f"{DEFAULT_DATA_ROOT}, which is how a write can land on somebody's "
            "source data (G81). Set it to your data root — the conventional "
            f"location is {DEFAULT_DATA_ROOT}. Set it in your shell profile "
            f"(PowerShell: $env:{DATA_ROOT_ENV}; bash: export {DATA_ROOT_ENV}=...). "
            "config/dev-environment.yaml records it for this repo."
        )
    return Path(raw)


def source_dir(*parts: str, create: bool = False) -> Path:
    """A subfolder under the data root (``source_dir('rua', 'incoming')``).

    THE GENERAL HELPER, AND THE ONE THAT MADE THE INCIDENT POSSIBLE (G81): it
    takes arbitrary parts, so it can name any path under the root — including,
    with no parts at all, the ROOT ITSELF, which contains every declared drop
    zone. Prefer a named helper; this exists for the zones that have not earned
    one yet, and every such call site is now a declared zone in
    ``config/data-zones.yaml``.

    ``create=True`` REFUSES when the target is inside a declared read zone.
    That check lives here rather than only in the test because the test compares
    DECLARATIONS while this compares the path actually being made — and the
    incident's shape is a real mkdir/write landing somewhere a human drops
    source files.
    """
    path = resolve_data_root().joinpath(*parts)
    if create:
        refuse_write_into_read_zone(path, action="create")
        path.mkdir(parents=True, exist_ok=True)
    return path


def refuse_write_into_read_zone(target: Path, *, action: str) -> None:
    """Raise when ``target`` sits inside a declared READ zone (G81 (c), runtime).

    Imported lazily: :mod:`drydocs_core.data_zones` reads this module, so a
    module-level import would be a cycle. A declaration that cannot be read is
    NOT treated as permission — the error propagates, because "we could not
    check" must never resolve to "go ahead" in the one guard standing between a
    write and somebody's source data.
    """
    from drydocs_core.data_zones import read_zone_containing

    zone = read_zone_containing(target)
    if zone is not None:
        raise ReadZoneWriteError(
            f"refusing to {action} {target}: it is inside the READ zone "
            f"{zone.id!r} ({zone.path}). Source data a human dropped there is "
            "never the system's to write — that is the 2026-08-11 overwrite in "
            "one sentence. Write to a `write`-mode zone in config/data-zones.yaml, "
            "or change the zone's mode there if this really is ours to rebuild."
        )


def rua_incoming_dir() -> Path:
    """Landing zone for collected ``rua_*.tar.gz`` bundles. READ zone (G81): a
    hand-carried bundle is source data, so this helper cannot create."""
    return source_dir("rua", "incoming")


def rua_extracted_dir(bundle_name: str | None = None, *, create: bool = False) -> Path:
    """Unpack area — one directory per bundle when ``bundle_name`` is given."""
    parts = ("rua", "extracted") + ((bundle_name,) if bundle_name else ())
    return source_dir(*parts, create=create)


def dpl_registry_dir(seal: str | None = None) -> Path:
    """Landing zone for per-SEAL DPL registry Swagger exports (G25). READ zone.

    NOTE the path: ``dpl-registry/``. The source registry declared ``dpl/`` from
    N12 until G81 corrected it — the two had NEVER agreed, so an operator who
    followed the registry had files nothing read (reconstruction §3b)."""
    parts = ("dpl-registry",) + ((seal,) if seal else ())
    return source_dir(*parts)


def catalog_dir(sub: str | None = None) -> Path:
    """Landing zone for Snowflake data-catalog view exports (G42);
    ``catalog_dir("screenshots")`` is the evidence-capture area. READ zone (G81):
    hand-pulled exports and SME evidence are never the system's to write."""
    parts = ("catalog",) + ((sub,) if sub else ())
    return source_dir(*parts)


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


def email_extracts_dir() -> Path:
    """DRYDOCS_DATA_ROOT/email-extracts/ — the Q10 landing zone: Copilot JSON
    extracts beside their original .msg files. Machine-local; the repo carries
    only synthetic samples (drydocs/data/samples/email-extracts/)."""
    return source_dir("email-extracts")


def controlm_xml_dir() -> Path:
    """Landing zone for Control-M XML definition exports (G47 — the
    9.0.21.300 config SoR; real folder/job/variable values are Internal).
    No filename-fingerprint tree sweep exists for these: exports are
    arbitrarily-named generic ``.xml``, so the guard is this landing-zone
    convention itself plus the classification on the source entry."""
    return source_dir("controlm-xml")


def remediation_incoming_dir() -> Path:
    """Landing zone for folder ``.xml`` exports awaiting a remediation pass.

    Deliberately separate from :func:`controlm_xml_dir` (the INGESTION landing
    zone): remediation inputs are per-fix working copies whose lifecycle is the
    fix package, not the graph load — mixing them would make "which exports are
    loaded?" unanswerable from the tree. Real definitions are Internal; nothing
    here is ever committed."""
    return source_dir("remediation", "incoming")


def remediation_outgoing_dir(*, create: bool = False) -> Path:
    """Output zone for emitted ``<folder>.updated.xml`` files — the
    minimal-diff artifacts ``xml_io.write`` produced and self-checked. One
    fix package's ``target/`` contents stage here before packaging."""
    return source_dir("remediation", "outgoing", create=create)


def remediation_recommendations_dir(*, create: bool = False) -> Path:
    """Output zone for remediation recommendation documents (change docs,
    equivalence reports, fix-tracking change-sets awaiting the loader)."""
    return source_dir("remediation", "recommendations", create=create)


def cmdline_staging_dir(*, create: bool = False) -> Path:
    """G39 job-detail staging store (SQLite). WRITE zone — the system rebuilds it."""
    return source_dir("cmdline-staging", create=create)


def controlm_api_config_dir() -> Path:
    """Holds ``controlm_api.cfg`` (G96), AUTHORED BY AN OPERATOR. READ zone:
    overwriting somebody's endpoint/credential config is the same class as
    overwriting their extract."""
    return source_dir("controlm-api")
