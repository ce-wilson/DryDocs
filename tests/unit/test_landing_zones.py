"""Landing-zone guards -- a manual drop folder must be somewhere git clean cannot reach.

THE DEFECT THESE EXIST FOR. ``git clean -fd`` deletes untracked, non-ignored files;
``git clean -fdx`` deletes untracked files INCLUDING ignored ones. A source payload
can never be tracked (PUBLISH-BOUNDARY.md), so inside a working tree it always falls
in one of those two buckets -- meaning NO .gitignore arrangement protects a
hand-carried extract from a port-time sweep. Which files survived a given sweep came
down to whether they happened to be ignored and whether the sweep carried ``-x``.
``docs/port/port-prompt.md`` has carried "NEVER git clean during a port" since the J22
lesson and the extracts were deleted anyway, which is the whole argument for a
checked declaration instead of another sentence in a runbook.

So: ``acquisition.drop_dir_base`` states where a zone is rooted, and these tests make
the declaration load-bearing. ``data_root`` zones resolve outside the tree. ``repo``
zones are permitted ONLY when their contents are TRACKED -- that clause is the one
that closes the hole, because it means an untracked data corpus can never be declared
a landing zone and inherit an in-tree home.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from drydocs_core.landing_zones import (
    BASE_DATA_ROOT,
    BASE_REPO,
    BASES,
    LandingZone,
    inventory,
    manual_zones,
    resolve,
    tracked_paths_under,
)

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---- the shipped registry ---------------------------------------------------


def test_every_manual_row_declares_where_its_drop_dir_is_rooted() -> None:
    """A bare drop_dir is ambiguous: ``pat/`` is data-root-relative and
    ``docs/design/`` is repo-relative, and nothing in the string says which."""
    bad = [z.source_id for z in manual_zones() if z.base not in BASES]
    assert not bad, (
        f"manual rows without a valid acquisition.drop_dir_base: {bad} -- "
        f"must be one of {list(BASES)}. The base is what decides whether a port-time "
        "git clean can reach the payload, so it is not optional and is never guessed "
        "from the path text."
    )


def test_data_root_zones_resolve_outside_the_repo_working_tree() -> None:
    """The actual protection. A zone under DRYDOCS_DATA_ROOT is unreachable by any
    git operation, which is a stronger claim than "it is gitignored"."""
    inside = [
        f"{z.source_id}: {z.path}"
        for z in manual_zones()
        if z.base == BASE_DATA_ROOT and z.inside_repo
    ]
    assert not inside, (
        "data_root landing zones that resolve INSIDE the repo tree:\n  "
        + "\n  ".join(inside)
        + "\nA payload here is untracked-or-ignored either way, so git clean -fdx "
        "deletes it and the reflog cannot bring it back."
    )


def test_repo_based_zones_are_tracked_which_is_what_makes_them_safe() -> None:
    """The clause that closes the hole.

    ``base: repo`` is legitimate only for zones whose contents are COMMITTED --
    tracked files survive every clean. An untracked in-tree corpus declared as a
    landing zone would be exactly the thing that got deleted, so this refuses it at
    declaration time rather than after the sweep.
    """
    failures: list[str] = []
    for zone in manual_zones():
        if zone.base != BASE_REPO:
            continue
        if tracked_paths_under(zone.drop_dir) == 0:
            failures.append(
                f"{zone.source_id}: {zone.drop_dir!r} is repo-based but git tracks "
                "nothing under it"
            )
    assert not failures, (
        "repo-based landing zones whose contents are not tracked:\n  "
        + "\n  ".join(failures)
        + "\nEither the contents are committed artifacts (track them) or they are "
        "source payloads (move the zone to base: data_root, out of the tree). There "
        "is no third option: git clean -fdx removes ignored files too."
    )


def test_declared_zones_are_shape_checked_not_machine_paths() -> None:
    """J15: enumerate the shape, never the values. Real paths live in the internal
    twin, so a committed drop_dir stays a convention."""
    bad = [
        f"{z.source_id}: {z.drop_dir!r}"
        for z in manual_zones()
        if z.drop_dir.startswith(("/", "\\"))
        or "\\" in z.drop_dir
        or ".." in z.drop_dir
        or (len(z.drop_dir) > 1 and z.drop_dir[1] == ":")
    ]
    assert not bad, "drop_dir values that look like real machine paths:\n  " + "\n  ".join(bad)


def test_inventory_reports_without_creating_anything(tmp_path, monkeypatch) -> None:
    """A doctor that creates the folder it is checking would report success on a tree
    it just repaired, hiding the wipe it exists to surface."""
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path / "nonexistent"))
    statuses = inventory([z for z in manual_zones() if z.base == BASE_DATA_ROOT])
    assert statuses, "no data_root zones resolved"
    assert not (
        tmp_path / "nonexistent"
    ).exists(), "inventory() created the data root -- it must be read-only"
    assert all(not s.exists for s in statuses)


# ---- the mechanism, driven over synthetic rows so the negative case
# ---- reproduces off this machine (the S12 lesson) ---------------------------


def _registry(tmp_path: Path, rows: str) -> Path:
    path = tmp_path / "source-registry.yaml"
    path.write_text(rows, encoding="utf-8")
    return path


def test_resolve_bases_differ(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path / "root"))
    assert resolve(BASE_DATA_ROOT, "seal/") == tmp_path / "root" / "seal"
    assert resolve(BASE_REPO, "docs/design/") == REPO_ROOT / "docs/design"


def test_manual_zones_skips_automated_rows(tmp_path) -> None:
    path = _registry(
        tmp_path,
        "datasets:\n"
        "  - id: a:one\n"
        "    acquisition: {mode: manual, format: csv, drop_dir: a/, drop_dir_base: data_root}\n"
        "  - id: b:two\n"
        "    acquisition: {mode: automated, via: db}\n",
    )
    assert [z.source_id for z in manual_zones(path)] == ["a:one"]


def test_a_missing_base_is_surfaced_never_defaulted(tmp_path) -> None:
    """Defaulting would re-introduce the ambiguity the field removes -- and on the
    wrong guess it would default a data payload INTO the tree."""
    path = _registry(
        tmp_path,
        "datasets:\n  - id: a:one\n    acquisition: {mode: manual, format: csv, drop_dir: a/}\n",
    )
    assert manual_zones(path)[0].base == ""


@pytest.mark.parametrize("base", list(BASES))
def test_inside_repo_is_measured_not_inferred_from_the_base(tmp_path, monkeypatch, base) -> None:
    """DRYDOCS_DATA_ROOT is env-settable, so ``base: data_root`` is a DECLARATION and
    ``inside_repo`` is the measurement. Pointing the root at the tree must be caught,
    not trusted away."""
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(REPO_ROOT / "var" / "fake-root"))
    zone = LandingZone(
        source_id="x:y", fmt="csv", drop_dir="seal/", base=base, path=resolve(base, "seal/")
    )
    assert zone.inside_repo is True


def test_inventory_counts_files_recursively(tmp_path, monkeypatch) -> None:
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    (tmp_path / "seal" / "nested").mkdir(parents=True)
    (tmp_path / "seal" / "a.csv").write_text("x", encoding="utf-8")
    (tmp_path / "seal" / "nested" / "b.csv").write_text("y", encoding="utf-8")
    zone = LandingZone(
        source_id="seal:app-extract",
        fmt="csv",
        drop_dir="seal/",
        base=BASE_DATA_ROOT,
        path=resolve(BASE_DATA_ROOT, "seal/"),
    )
    (status,) = inventory([zone])
    assert status.exists and status.file_count == 2 and not status.empty


def test_an_emptied_zone_is_distinguishable_from_a_missing_one(tmp_path, monkeypatch) -> None:
    """The wipe signature. After a clean the DIRECTORY may survive while its contents
    do not, so ``exists`` alone reads as healthy -- ``empty`` is the fact a reader
    needs."""
    monkeypatch.setenv("DRYDOCS_DATA_ROOT", str(tmp_path))
    (tmp_path / "seal").mkdir()
    zone = LandingZone(
        source_id="seal:app-extract",
        fmt="csv",
        drop_dir="seal/",
        base=BASE_DATA_ROOT,
        path=resolve(BASE_DATA_ROOT, "seal/"),
    )
    (status,) = inventory([zone])
    assert status.exists and status.empty and status.file_count == 0
