"""The generated SEAL samples must survive the loaders' own row models.

``drydocs/data/`` is gitignored, so these fixtures cannot be committed and pinned by
eye — the generator is the artifact and this file is what keeps it honest. Everything
here derives from the committed capture, so a change to
``config/taxonomy/business-application.yaml`` that breaks the sample contract fails
HERE rather than at a load nobody ran.

Written 2026-08-06 with the generator. Before it, ``seal_contacts`` had no sample and
no test at all, which is the whole reason a role-destroying alias survived in
``seal.py`` long enough to be found by reading.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from drydocs.seal_samples import (
    APPLICATION_HEADER,
    CONTACT_HEADER,
    EMBEDDED_ROLES,
    RESERVED_SEALID_RANGE,
    SYNTHETIC_EMAIL_DOMAIN,
    NonSyntheticCaptureError,
    build_rows,
    write_samples,
)
from drydocs_core.models.seal import SealApplicationRow, SealContactRow

#: Role classes the SME's 2026-08-06 list names that the code cannot admit today —
#: G35 §A3/§A1d. Pinned as an EXPECTATION, not an accident: when the gate rules how an
#: unknown name is handled, this set is the thing that must change with it.
UNADMISSIBLE_TODAY = {
    "Deployment Owner",
    "Deployment Information Owner",
    "Application Module Owner",
    "Site Reliability Engineer",
}


@pytest.fixture(scope="module")
def rows() -> tuple[list[dict], list[dict]]:
    return build_rows()


def test_every_application_row_validates(rows) -> None:
    application_rows, _ = rows
    assert application_rows, "the capture produced no applications"
    for row in application_rows:
        SealApplicationRow.model_validate(row)


def test_every_application_row_carries_all_three_inline_contacts(rows) -> None:
    """DECO_SEAL_APP_INFO's whole point. A row missing one is a capture gap, and the
    loader would silently write two attributions instead of three."""
    application_rows, _ = rows
    for row in application_rows:
        for sid_column, name_column in EMBEDDED_ROLES.values():
            assert row.get(sid_column), f"{row['app_id']} has no {sid_column}"
            assert row.get(name_column), f"{row['app_id']} has no {name_column}"


def test_contact_rows_split_exactly_as_the_code_admits_them(rows) -> None:
    """The sample deliberately carries names the loader REFUSES, so §A3 reproduces on
    demand. This pins which ones — a new refusal is a finding, not noise."""
    _, contact_rows = rows
    refused, accepted = [], []
    for row in contact_rows:
        try:
            SealContactRow.model_validate(row)
        except ValidationError:
            refused.append(row["role_name"])
        else:
            accepted.append(row["role_name"])

    assert set(refused) == UNADMISSIBLE_TODAY
    assert accepted, "every contact row was refused — the sample is not exercising the loader"
    assert not (set(accepted) & UNADMISSIBLE_TODAY)


def test_no_two_contact_rows_collide_on_attribution_id(rows) -> None:
    """THE REGRESSION THAT MATTERS. ``seal_contacts.cypher`` MERGEs on
    ``app_id|SEAL|role|sid``, so two rows sharing a key become ONE node and a role
    holding is lost with no flag — exactly what the bare-Operate-Manager alias did
    until 2026-08-06. A collision here means the sample would silently under-load.
    """
    _, contact_rows = rows
    keys = [
        f"{row['app_id']}|SEAL|{SealContactRow.model_validate(row).role_name.value}|"
        f"{row['employee_sid']}"
        for row in contact_rows
        if row["role_name"] not in UNADMISSIBLE_TODAY
    ]
    duplicates = {key for key in keys if keys.count(key) > 1}
    assert not duplicates, f"attribution_id collision — a holding would be lost: {duplicates}"


def test_the_sample_exercises_one_person_in_all_three_operate_manager_classes(rows) -> None:
    """The case the gate turns on (config/gate-log.md:882). If a capture edit ever
    removes it, the sample stops covering the defect it was built to cover."""
    _, contact_rows = rows
    by_person: dict[tuple[str, str], set[str]] = {}
    for row in contact_rows:
        if "Operate Manager" in row["role_name"]:
            by_person.setdefault((row["app_id"], row["employee_sid"]), set()).add(row["role_name"])
    assert any(
        held == {"L1 Operate Manager", "L2 Operate Manager", "Operate Manager"}
        for held in by_person.values()
    ), "no person holds all three Operate Manager classes on one application"


def test_generated_data_cannot_leave_the_synthetic_block(rows) -> None:
    """The publish boundary, enforced rather than documented. This file family leaked
    real SEALIDs twice (9d59f53, and the 105aa9c p0 sweep)."""
    application_rows, contact_rows = rows
    for row in application_rows:
        assert int(row["app_id"]) in RESERVED_SEALID_RANGE
    for row in contact_rows:
        assert int(row["app_id"]) in RESERVED_SEALID_RANGE
        assert row["employee_email"].endswith(f"@{SYNTHETIC_EMAIL_DOMAIN}")


def test_a_capture_outside_the_reserved_block_is_refused(tmp_path: Path) -> None:
    """The guard is structural: a capture edited to hold a real id cannot be turned
    into a sample, so the refusal does not depend on anyone remembering."""
    capture = tmp_path / "capture.yaml"
    capture.write_text(
        "nodes:\n"
        "  employees: [{sid: K1, name: A Person}]\n"
        "  business_applications:\n"
        "    - {sealid: 12345, name: Real App, short_name: ra, state: Operate,"
        " lob: CCB, info_classification: Internal}\n"
        "  memberships:\n"
        "    - sealid: 12345\n"
        "      roles: [{role: Application Owner, sid: K1}]\n",
        encoding="utf-8",
    )
    with pytest.raises(NonSyntheticCaptureError, match="reserved synthetic block"):
        build_rows(capture)


def test_write_samples_emits_both_files_with_the_declared_headers(tmp_path: Path) -> None:
    """The chain names both filenames (``REFRESH_REFERENCE_CHAIN``); a rename here
    would silently reinstate the skip the generator exists to end."""
    from drydocs.cli import REFRESH_REFERENCE_CHAIN

    declared = {sample for _, _, sample in REFRESH_REFERENCE_CHAIN}
    written = write_samples(out_dir=tmp_path)
    for path, header in zip(written, (APPLICATION_HEADER, CONTACT_HEADER), strict=True):
        assert path.name in declared, f"{path.name} is not declared in the refresh chain"
        assert path.read_text(encoding="utf-8").splitlines()[0] == ",".join(header)
        assert not path.read_text(encoding="utf-8").startswith("﻿"), "BOM (J29)"
