// =============================================================================
// server_resolution.cypher  —  the derived ExecutionHost -> Server identity pass
//
// Gate: server-location-ontology SIGNED OFF 12/12, 2026-08-19
// (config/gate-log.md §C1 — the K2 match-policy precedent: declared tiers,
// recorded evidence, nothing silent). The signed tiers:
//   T1 exact         nodeid == server name, case-normalized
//   T2 normalized    deterministic short-name/FQDN rule — strip the DNS
//                    suffix, nothing fuzzier; applied ONLY when exactly one
//                    candidate carries the short name (the ambiguity guard —
//                    a legitimate tightening recorded on the vocabulary entry)
//   T3 dns-resolved  the Z4 nslookup evidence file — NOT BUILT at Z3; the Z4
//                    collector adds it, feeding the same edge + evidence shape
//   else UNMATCHED — counted as coverage, NEVER guessed; an unmatched host
//   gets NO edge and appears explicitly unmatched in the Z3 query.
//
// An EDGE, never a merge (§A1): infra_resolves_to_server, carrying
// match_tier + match_evidence + resolved_at. One LB-alias ExecutionHost may
// resolve to MANY Servers once T3 lands.
//
// DERIVED pass (the runs_on_resolution precedent): both inputs are already
// in the graph (ExecutionHost from the hosts pass; Server from the
// server-inventory pass), so it runs only after both, MATCHes endpoints, and
// MERGEs only edges.
//
// Parameters (ServerResolutionPass): $run_id, $resolved_at, $loader.
// =============================================================================

// -- T1: exact (case-normalized). ---------------------------------------------
MATCH (h:ExecutionHost)
WHERE h.nodeid IS NOT NULL AND h.nodeid <> '' AND NOT h:SchemaMeta
MATCH (s:Server)
WHERE NOT s:SchemaMeta AND toLower(s.name) = toLower(h.nodeid)
MERGE (h)-[r:RESOLVES_TO_SERVER]->(s)
  ON CREATE SET r.first_seen_at = datetime($resolved_at),
                r.match_tier    = 'exact',
                r.match_evidence = 'nodeid == server name (case-normalized): ' + toLower(h.nodeid),
                r.source        = 'infra:server-export x ExecutionHost.nodeid',
                r.loader        = $loader
SET r.resolved_at  = datetime($resolved_at),
    r.last_seen_at = datetime($resolved_at),
    r.last_run_id  = $run_id;

// -- T2: normalized short-name — only for hosts T1 left unresolved, and only
//        when exactly ONE server carries the short name (the ambiguity
//        guard: a collision stays unmatched and is counted, never picked). ---
MATCH (h:ExecutionHost)
WHERE h.nodeid IS NOT NULL AND h.nodeid <> '' AND NOT h:SchemaMeta
  AND NOT EXISTS { MATCH (h)-[:RESOLVES_TO_SERVER]->() }
WITH h, split(toLower(h.nodeid), '.')[0] AS short
MATCH (s:Server)
WHERE NOT s:SchemaMeta AND split(toLower(s.name), '.')[0] = short
WITH h, short, collect(s) AS candidates
WHERE size(candidates) = 1
UNWIND candidates AS s
MERGE (h)-[r:RESOLVES_TO_SERVER]->(s)
  ON CREATE SET r.first_seen_at = datetime($resolved_at),
                r.match_tier    = 'normalized',
                r.match_evidence = 'short-name (DNS suffix stripped): ' + short
                                   + ' — nodeid ' + toLower(h.nodeid)
                                   + ' ~ server ' + toLower(s.name),
                r.source        = 'infra:server-export x ExecutionHost.nodeid',
                r.loader        = $loader
SET r.resolved_at  = datetime($resolved_at),
    r.last_seen_at = datetime($resolved_at),
    r.last_run_id  = $run_id;
