"""Lineage extractors — re-homed from depgraph@feat/controlm-lineage (ADR 0002-C §4)."""
from .controlm_inventory import ControlMInventoryExtractor, ExtractCoverage
from .dpl_mac import CloneFolder, DplMacExtractor, MacCoverage, parse_clone_folder
from .dpl_registry import (
    DplRegistryExtractor,
    RegistryCoverage,
    RegistryCrossCheck,
    RegistryExtract,
    RegistryRecord,
    cross_check,
)
from .code_repo import (
    CodeRepoExtractor,
    CorroborationReport,
    RepoManifestCoverage,
    corroborate,
    git_blob_sha1,
)
from .rua_code_ops import RuaCodeOps, RuaCodeOpsCoverage, RuaCodeOpsExtractor
from .rua_inventory import RuaCoverage, RuaInventoryExtractor

__all__ = [
    "CloneFolder",
    "CodeRepoExtractor",
    "ControlMInventoryExtractor",
    "CorroborationReport",
    "RepoManifestCoverage",
    "corroborate",
    "git_blob_sha1",
    "DplMacExtractor",
    "DplRegistryExtractor",
    "ExtractCoverage",
    "MacCoverage",
    "RegistryCoverage",
    "RegistryCrossCheck",
    "RegistryExtract",
    "RegistryRecord",
    "RuaCodeOps",
    "RuaCodeOpsCoverage",
    "RuaCodeOpsExtractor",
    "RuaCoverage",
    "RuaInventoryExtractor",
    "cross_check",
    "parse_clone_folder",
]
