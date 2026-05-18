"""Loaders — one per source.

This ``__init__`` re-exports the loader pattern (``BaseLoader`` +
``LoadSummary``) and the SEAL / catalog / Control-M loader classes for
convenient top-level imports::

    from drydocs.loaders import (
        BaseLoader, LoadSummary,
        SealApplicationsLoader, SealContactsLoader,
        CatalogLOBsLoader, ProductLinesLoader, ProductsLoader, DevTeamsLoader,
        ControlMFoldersLoader, ControlMJobsLoader,
        ControlMConditionsInLoader, ControlMConditionsOutLoader,
        ControlMDependenciesDerivedLoader,
    )

The Control-M loaders are also available under ``drydocs.loaders.controlm``
as a grouped namespace; see that module for the convenience re-exports.
"""
from .base import BaseLoader, LoadSummary

# SEAL
from .seal_applications import SealApplicationsLoader
from .seal_contacts import SealContactsLoader

# Catalog
from .catalog import (
    CatalogLOBsLoader,
    DevTeamsLoader,
    ProductLinesLoader,
    ProductsLoader,
)

# Control-M — re-export from the .controlm grouped namespace so adding /
# removing a loader only requires editing one place (controlm.py).
from .controlm import (
    ControlMConditionsInLoader,
    ControlMConditionsOutLoader,
    ControlMDependenciesDerivedLoader,
    ControlMFoldersLoader,
    ControlMJobsLoader,
)

__all__ = [
    "BaseLoader",
    "LoadSummary",
    # SEAL
    "SealApplicationsLoader",
    "SealContactsLoader",
    # Catalog
    "CatalogLOBsLoader",
    "DevTeamsLoader",
    "ProductLinesLoader",
    "ProductsLoader",
    # Control-M
    "ControlMFoldersLoader",
    "ControlMJobsLoader",
    "ControlMConditionsInLoader",
    "ControlMConditionsOutLoader",
    "ControlMDependenciesDerivedLoader",
]
