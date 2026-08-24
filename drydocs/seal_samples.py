"""Derive the two SEAL loader sample CSVs from the synthetic taxonomy capture.

``drydocs/data/`` is GITIGNORED — *"Sample / local data — may contain sensitive
source data"* (``.gitignore``). The eleven sample CSVs that ARE tracked predate that
rule and are grandfathered; nothing new lands there. That is deliberate and this
module exists to respect it rather than route around it: the SEAL samples are
**generated on the machine that needs them** and never committed, so the boundary
holds and the fixtures still exist.

The gap this closes. The business-application chain (``cli.CHAINS``; before the
G79 split, ``REFRESH_REFERENCE_CHAIN``) has always declared
``seal_application_data__sample.csv`` and ``seal_contact_data__sample.csv``, and both
were deleted at ``9d59f53`` (2026-07-19) for carrying real ``seal_id`` values and never
replaced. So ``drydocs refresh-reference`` printed two yellow skips, exited 0, and wrote
no attribution nodes — a loader pair with no sample and no reproduction path, which is
how the ``seal.py`` bare-Operate-Manager coercion survived to be found by reading rather
than by failing.

DERIVED, NEVER HAND-TYPED. ``config/taxonomy/business-application.yaml`` is the one
place the synthetic applications, people and role holdings live, so generating from it
is what stops a sample drifting away from the capture it claims to mirror. Regenerate
after any change to that file.

THE SPLIT FOLLOWS THE REAL SOURCE SHAPE, not convenience. ``DECO_SEAL_APP_INFO``
carries three contacts INLINE — App Owner, CTO, Information Owner — and every other
role arrives on a separate long-format contact extract. So those three become COLUMNS
on the application row and the rest become contact ROWS. Generating one flat file would
be easier and would exercise neither loader as it actually runs.

Usage:
    poetry run python scripts/build_seal_samples.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import yaml

from drydocs_core.repo_paths import repo_root

REPO_ROOT = repo_root(Path(__file__).resolve().parents[1])
DEFAULT_CAPTURE_PATH = REPO_ROOT / "config" / "taxonomy" / "business-application.yaml"
DEFAULT_SAMPLES_DIR = REPO_ROOT / "drydocs" / "data" / "samples"

APPLICATION_SAMPLE = "seal_application_data__sample.csv"
CONTACT_SAMPLE = "seal_contact_data__sample.csv"

#: The three roles DECO_SEAL_APP_INFO carries inline -> its (sid, name) column pair.
#: Anything not listed here is a contact-extract row. Keyed on the role name the
#: CAPTURE uses; if the SME renames one there, this map is the single thing to update.
EMBEDDED_ROLES: dict[str, tuple[str, str]] = {
    "Application Owner": ("app_owner_sid", "app_owner_name"),
    "Chief Technology Officer": ("chief_tech_officer_sid", "chief_tech_officer_name"),
    "Primary Information Owner": ("info_owner_sid", "info_owner_name"),
}

APPLICATION_HEADER: tuple[str, ...] = (
    "app_id",
    "name",
    "app_short_name",
    "app_state",
    "app_lob",
    "info_classification",
    "app_owner_sid",
    "app_owner_name",
    "chief_tech_officer_sid",
    "chief_tech_officer_name",
    "info_owner_sid",
    "info_owner_name",
)
CONTACT_HEADER: tuple[str, ...] = (
    "app_id",
    "role_name",
    "employee_sid",
    "employee_name",
    "employee_email",
)

#: The synthetic SEALID block SEAL does not issue (PUBLISH-BOUNDARY.md; the capture's
#: own header states the rule). Enforced at generation, so this module CANNOT emit a
#: sample carrying a real id even if the capture is edited to hold one — a structural
#: guarantee rather than a comment asking someone to be careful.
RESERVED_SEALID_RANGE = range(70001, 70100)

#: RFC 2606 reserved TLD: unroutable by definition, so a generated address can never be
#: mailed and can never be mistaken for a real one.
SYNTHETIC_EMAIL_DOMAIN = "example.invalid"


class NonSyntheticCaptureError(RuntimeError):
    """The capture holds an id outside the reserved synthetic block."""


def synthetic_email(full_name: str) -> str:
    """A deterministic non-routable address for an invented person."""
    local = ".".join(part for part in full_name.lower().split() if part)
    return f"{local}@{SYNTHETIC_EMAIL_DOMAIN}"


def build_rows(capture_path: Path = DEFAULT_CAPTURE_PATH) -> tuple[list[dict], list[dict]]:
    """Return ``(application_rows, contact_rows)`` derived from the capture.

    Pure: reads the capture, writes nothing. Raises
    :class:`NonSyntheticCaptureError` if any application id falls outside the
    reserved block, and :class:`ValueError` if two people hold an inline role on
    one application — a real possibility the flat DECO row simply cannot express,
    and one that must fail loudly rather than silently drop a holder.
    """
    capture = yaml.safe_load(capture_path.read_text(encoding="utf-8"))
    nodes = capture["nodes"]
    employees = {e["sid"]: e["name"] for e in nodes["employees"]}
    applications = {str(a["sealid"]): a for a in nodes["business_applications"]}

    outside = sorted(a for a in applications if int(a) not in RESERVED_SEALID_RANGE)
    if outside:
        raise NonSyntheticCaptureError(
            f"{capture_path} holds application id(s) outside the reserved synthetic "
            f"block {RESERVED_SEALID_RANGE.start}-{RESERVED_SEALID_RANGE.stop - 1}: "
            f"{outside}. Refusing to generate a sample from it."
        )

    application_rows: list[dict] = []
    contact_rows: list[dict] = []

    for block in nodes["memberships"]:
        app_id = str(block["sealid"])
        app = applications[app_id]
        row = {
            "app_id": app_id,
            "name": app["name"],
            "app_short_name": app["short_name"],
            "app_state": app["state"],
            "app_lob": app["lob"],
            "info_classification": app["info_classification"],
        }
        for holding in block["roles"]:
            role, sid = holding["role"], holding["sid"]
            if role in EMBEDDED_ROLES:
                sid_column, name_column = EMBEDDED_ROLES[role]
                if sid_column in row:
                    raise ValueError(
                        f"application {app_id} has two holders of the inline role "
                        f"{role!r}; DECO_SEAL_APP_INFO carries one column pair per "
                        f"inline role and cannot represent both."
                    )
                row[sid_column] = sid
                row[name_column] = employees[sid]
            else:
                contact_rows.append(
                    {
                        "app_id": app_id,
                        "role_name": role,
                        "employee_sid": sid,
                        "employee_name": employees[sid],
                        "employee_email": synthetic_email(employees[sid]),
                    }
                )
        application_rows.append(row)

    return application_rows, contact_rows


def _write_csv(path: Path, header: tuple[str, ...], rows: list[dict]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    # newline="" per the csv docs; utf-8 without BOM per the J29 encoding standard.
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(header), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
    return path


def write_samples(
    capture_path: Path = DEFAULT_CAPTURE_PATH,
    out_dir: Path = DEFAULT_SAMPLES_DIR,
) -> tuple[Path, Path]:
    """Generate both sample CSVs; return their paths in chain order (apps, contacts)."""
    application_rows, contact_rows = build_rows(capture_path)
    return (
        _write_csv(out_dir / APPLICATION_SAMPLE, APPLICATION_HEADER, application_rows),
        _write_csv(out_dir / CONTACT_SAMPLE, CONTACT_HEADER, contact_rows),
    )
