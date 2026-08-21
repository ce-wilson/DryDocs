"""N16 — ``BaseLoader.source_label`` is a declared enum, enforced.

The field reaches the graph (``(:JobRun).source``) and the load summary, so it
is provenance a consumer reads, not a code-local tag. Before N16 the enum lived
in a comment that named four values while thirteen loaders shipped eight
others. Ruling (a): widen to the values in use and enforce; the collision with
the mappings' ``source_label`` (a NODE label) is stated on the enum.
"""

from __future__ import annotations

import importlib
import inspect
import pkgutil

from drydocs import loaders
from drydocs.loaders.base import SOURCE_LABELS, BaseLoader


def _loader_classes() -> list[type]:
    found: list[type] = []
    for info in pkgutil.walk_packages(loaders.__path__, prefix="drydocs.loaders."):
        module = importlib.import_module(info.name)
        for _, cls in inspect.getmembers(module, inspect.isclass):
            if (
                issubclass(cls, BaseLoader)
                and cls is not BaseLoader
                and cls.__module__ == info.name
            ):
                found.append(cls)
    return found


def test_every_loader_ships_a_declared_source_label() -> None:
    classes = _loader_classes()
    assert len(classes) >= 20, "the walk found too few loaders — did the package move?"
    offenders = sorted(
        f"{cls.__module__}.{cls.__name__}: {cls.source_label!r}"
        for cls in classes
        if cls.source_label not in SOURCE_LABELS
    )
    assert not offenders, (
        "loader(s) ship a source_label outside SOURCE_LABELS (drydocs/loaders/base.py) — "
        "declare the value there with what it means, or use an existing one:\n  "
        + "\n  ".join(offenders)
    )


def test_the_enum_has_no_dead_values() -> None:
    """`agent` was declared for months and used by nobody; a declared value that
    no loader ships is a comment wearing a frozenset."""
    used = {cls.source_label for cls in _loader_classes()}
    dead = sorted(SOURCE_LABELS - used)
    assert not dead, f"SOURCE_LABELS declares value(s) no loader uses: {dead}"


def test_the_collision_is_stated_on_the_enum() -> None:
    import drydocs.loaders.base as base

    src = inspect.getsource(base)
    assert "mapping_store.py" in src and "SOURCE NODE LABEL" in src
