"""Lineage extractors — re-homed from depgraph@feat/controlm-lineage (ADR 0002-C §4)."""

from .catalog_crosscheck import (
    AttributionCensus,
    DplGuidCrossCheck,
    PlacementCrossCheck,
    RegistrationCensus,
    attribution_census,
    dpl_guid_crosscheck,
    placement_crosscheck,
    registration_census,
)
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
    "attribution_census",
    "AttributionCensus",
    "CatalogCoverage",
    "CatalogDatasetRecord",
    "CatalogDistributionRecord",
    "CatalogExtract",
    "CloneFolder",
    "CodeRepoExtractor",
    "ControlMInventoryExtractor",
    "ControlMXmlDefsExtractor",
    "corroborate",
    "CorroborationReport",
    "cross_check",
    "dpl_guid_crosscheck",
    "DplGuidCrossCheck",
    "DplMacExtractor",
    "DplRegistryExtractor",
    "ExtractCoverage",
    "git_blob_sha1",
    "GlueInventoryCoverage",
    "GlueTableInventoryExtractor",
    "MacCoverage",
    "parse_clone_folder",
    "parse_database_name",
    "placement_crosscheck",
    "PlacementCrossCheck",
    "registration_census",
    "RegistrationCensus",
    "RegistryCoverage",
    "RegistryCrossCheck",
    "RegistryExtract",
    "RegistryRecord",
    "RepoManifestCoverage",
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
]
