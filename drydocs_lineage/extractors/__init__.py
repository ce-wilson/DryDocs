"""Lineage extractors — re-homed from depgraph@feat/controlm-lineage (ADR 0002-C §4)."""
from .code_repo import (
    CodeRepoExtractor,
    CorroborationReport,
    RepoManifestCoverage,
    corroborate,
    git_blob_sha1,
)
from .controlm_inventory import ControlMInventoryExtractor, ExtractCoverage
from .controlm_xml import (
    ControlMXmlDefsExtractor,
    XmlDefsCoverage,
    XmlDefsExtract,
    XmlFolderRecord,
    XmlJobRecord,
    XmlVariableRecord,
)
from .dpl_mac import CloneFolder, DplMacExtractor, MacCoverage, parse_clone_folder
from .dpl_registry import (
    DplRegistryExtractor,
    RegistryCoverage,
    RegistryCrossCheck,
    RegistryExtract,
    RegistryRecord,
    cross_check,
)
from .glue_tables import (
    GlueInventoryCoverage,
    GlueTableInventoryExtractor,
    parse_database_name,
)
from .rua_code_ops import RuaCodeOps, RuaCodeOpsCoverage, RuaCodeOpsExtractor
from .rua_inventory import RuaCoverage, RuaInventoryExtractor
from .snowflake_catalog import (
    CatalogCoverage,
    CatalogDatasetRecord,
    CatalogDistributionRecord,
    CatalogExtract,
    SnowflakeCatalogExtractor,
)

__all__ = [
    "CatalogCoverage",
    "CatalogDatasetRecord",
    "CatalogDistributionRecord",
    "CatalogExtract",
    "CloneFolder",
    "CodeRepoExtractor",
    "ControlMInventoryExtractor",
    "ControlMXmlDefsExtractor",
    "CorroborationReport",
    "RepoManifestCoverage",
    "corroborate",
    "git_blob_sha1",
    "DplMacExtractor",
    "DplRegistryExtractor",
    "ExtractCoverage",
    "GlueInventoryCoverage",
    "GlueTableInventoryExtractor",
    "MacCoverage",
    "parse_database_name",
    "RegistryCoverage",
    "RegistryCrossCheck",
    "RegistryExtract",
    "RegistryRecord",
    "RuaCodeOps",
    "RuaCodeOpsCoverage",
    "RuaCodeOpsExtractor",
    "RuaCoverage",
    "RuaInventoryExtractor",
    "SnowflakeCatalogExtractor",
    "XmlDefsCoverage",
    "XmlDefsExtract",
    "XmlFolderRecord",
    "XmlJobRecord",
    "XmlVariableRecord",
    "cross_check",
    "parse_clone_folder",
]
