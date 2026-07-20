"""Convenience re-exports for all Control-M loaders.

Lets downstream code do::

    from drydocs.loaders.controlm import (
        ControlMFoldersLoader,
        ControlMJobsLoader,
        ControlMConditionsInLoader,
        ControlMConditionsOutLoader,
        ControlMDependenciesDerivedLoader,
    )

…instead of importing each loader from its dedicated module. No
behaviour change; pure re-export.

Note: not to be confused with :mod:`drydocs.controlm`, which is the
sibling subpackage holding the folder-name parser.
"""
from .controlm_conditions_in import ControlMConditionsInLoader
from .controlm_conditions_out import ControlMConditionsOutLoader
from .controlm_dependencies_derived import ControlMDependenciesDerivedLoader
from .controlm_folders import ControlMFoldersLoader
from .controlm_jobs import ControlMJobsLoader

__all__ = [
    "ControlMFoldersLoader",
    "ControlMJobsLoader",
    "ControlMConditionsInLoader",
    "ControlMConditionsOutLoader",
    "ControlMDependenciesDerivedLoader",
]
