// =============================================================================
// software_registry.cypher  —  third-party software registry (plan 07 / ADR 0004).
//
// Creates Vendor (the brand ONLY) and SoftwareProduct nodes, attributes each
// product to its vendor via MADE_BY (prov:wasAttributedTo), and — for rows
// where used_by_app_id is set — wires the reserved DryDocs :Application to
// the product via USES_SOFTWARE (local domain edge; version/source on the
// edge). Idempotent; the registry YAML is the source of truth.
//
// Parameters: $batch (product_id, name, category, role, type, versions,
//             primary_version, vendor_id, vendor_name, publisher_url,
//             used_by_app_id), $run_id, $loaded_at, $loader, $source_label.
// =============================================================================

UNWIND $batch AS row
MERGE (v:Vendor {vendor_id: row.vendor_id})
  ON CREATE SET v.created_at = datetime($loaded_at),
                v.source     = 'registry'
SET v.name          = row.vendor_name,
    v.publisher_url = row.publisher_url,
    v.last_seen_at  = datetime($loaded_at),
    v.last_run_id   = $run_id

MERGE (sp:SoftwareProduct {product_id: row.product_id})
  ON CREATE SET sp.created_at = datetime($loaded_at),
                sp.source     = 'registry'
SET sp.name         = row.name,
    sp.category     = row.category,
    sp.role         = row.role,
    sp.type         = row.type,
    sp.versions     = row.versions,
    sp.last_seen_at = datetime($loaded_at),
    sp.last_run_id  = $run_id

MERGE (sp)-[m:MADE_BY]->(v)
  ON CREATE SET m.first_seen_at = datetime($loaded_at),
                m.source        = 'registry',
                m.loader        = $loader
SET m.last_seen_at = datetime($loaded_at),
    m.last_run_id  = $run_id

// USES_SOFTWARE only for DryDocs' own stack (used_by_app_id set by the
// adapter from drydocs_application_id — reserved id, company side reconciles
// to the real SEAL id at port time).
WITH row, sp
WHERE row.used_by_app_id IS NOT NULL
MERGE (a:Application {seal_id: row.used_by_app_id})
  ON CREATE SET a.name       = 'DryDocs',
                a.created_at = datetime($loaded_at),
                a.source     = 'registry'
MERGE (a)-[u:USES_SOFTWARE]->(sp)
  ON CREATE SET u.first_seen_at = datetime($loaded_at),
                u.source        = 'registry',
                u.status        = 'active'
SET u.version      = row.primary_version,
    u.last_seen_at = datetime($loaded_at),
    u.last_run_id  = $run_id;
