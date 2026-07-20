§META
source_id:      jpmc-annual-report-2024
source_label:   JPMorgan Chase Annual Report 2024 + MD&A 10-K
platform:       document
trust:          SYNTHESIZED
reliability:    0.9
classification: Internal-Public
captured_at:    2026-06-30
documents:
  - assetId:   urn:drydocs:dataasset:document:jpmc:annualreport-2024
    title:     "Resolute Annual Report 2024"
    pages:     372
    creator:   "Acrobat Pro 25.1.20438"
    source:    jpmorgan-chase-annualreport-2024.pdf
  - assetId:   urn:drydocs:dataasset:document:jpmc:mda10k-2024
    title:     "CORP 10K 2024 (MD&A)"
    pages:     118
    creator:   "Workiva / Wdesk"
    source:    managements-discussion-analysis-2024.pdf
proxy_target:   ddcontext (drydocs-deepdoc; SYNTHESIZED content; never written to drydocs directly)

§DATAASSETS
# The two source documents as DataAsset nodes in ddcontext.
# assetId follows urn:drydocs:dataasset:{platform}:{namespace}:{name}
- assetId:    urn:drydocs:dataasset:document:jpmc:annualreport-2024
  name:       annualreport-2024
  namespace:  jpmc
  platform:   document
  format:     PDF
  pages:      372
  isExternalFeed:     true
  isSourceOfRecord:   true    # authoritative for BusinessSegment facts
  trust:      SYNTHESIZED
  reliability: 0.9

- assetId:    urn:drydocs:dataasset:document:jpmc:mda10k-2024
  name:       mda10k-2024
  namespace:  jpmc
  platform:   document
  format:     PDF
  pages:      118
  isExternalFeed:     true
  isSourceOfRecord:   true
  trust:      SYNTHESIZED
  reliability: 0.95   # 10-K is SEC-filed; higher reliability than narrative report

§JOBS
# No Control-M jobs ingest these documents today.
# Extraction is manual / on-demand (drydocs-deepdoc pattern).
# Future: a scheduled deepdoc job would USED the PDF DataAssets and GENERATED
# the BusinessSegment metric nodes below.

§UC
UC1  What business segments does JPMorgan Chase operate in 2024?
     → BusinessSegment nodes: CCB, CIB, AWM, Corp (active); CB (retired Q2-2024)
     → Source: MD&A p7 (business segment highlights), Annual Report p60+

UC2  What were the key 2024 metrics per segment?
     → CCB: ROE 32%, avg deposits -6%, client investment assets +14%, avg loans +9%,
            Card NCO rate 3.34%, debit/credit sales volume +8%, mobile customers +7%
     → CIB: ROE 18%, IB fees +37%, #1 Global IB 9.3% wallet share,
            Markets revenue +7% (Fixed Income +5%, Equity +13%)
     → AWM: ROE 34%, AUM $4.0T (+18%), avg loans +3%, avg deposits +9%

UC3  What were firm-wide financials for FY2024?
     → Total net revenue: $177,556M (+12% vs 2023)
     → Net interest income: $92,583M (+4%)
     → Noninterest revenue: $84,973M (+23%)
     → Net income: $58,471M (+18%)
     → Diluted EPS: $19.75 (+22%)
     → ROTCE: 22% | CET1: 15.7%
     → Source: MD&A p5

UC4  How do catalog LOBs reconcile to business segments?
     → RECONCILES_TO edges: CatalogLOB -[:RECONCILES_TO]-> BusinessSegment
     → Authority: lob-product-team (precedence.yaml #3)
     → Segment codes: CCB, CIB, AWM, Corp

§CYPHER
// Load into ddcontext database.
// Documents as DataAsset proxy nodes (join key: assetId).
// BusinessSegment proxy nodes carry 2024 metric properties (SYNTHESIZED).
// Trust boundary: this Cypher runs ONLY in ddcontext — never in drydocs.

MERGE (ar:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:annualreport-2024'})
SET ar.name            = 'annualreport-2024',
    ar.namespace       = 'jpmc',
    ar.platform        = 'document',
    ar.format          = 'PDF',
    ar.pages           = 372,
    ar.title           = 'Resolute Annual Report 2024',
    ar.isExternalFeed  = true,
    ar.isSourceOfRecord = true,
    ar.trust           = 'SYNTHESIZED',
    ar.reliability     = 0.9,
    ar.captured_at     = date('2026-06-30');

MERGE (mda:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:mda10k-2024'})
SET mda.name            = 'mda10k-2024',
    mda.namespace       = 'jpmc',
    mda.platform        = 'document',
    mda.format          = 'PDF',
    mda.pages           = 118,
    mda.title           = 'CORP 10K 2024 (MD&A)',
    mda.isExternalFeed  = true,
    mda.isSourceOfRecord = true,
    mda.trust           = 'SYNTHESIZED',
    mda.reliability     = 0.95,
    mda.captured_at     = date('2026-06-30');

// BusinessSegment proxy nodes with 2024 metrics.
MERGE (ccb:BusinessSegment {code: 'CCB'})
SET ccb.name                      = 'Consumer & Community Banking',
    ccb.roe_2024                  = 0.32,
    ccb.avg_deposits_yoy          = -0.06,
    ccb.client_investment_assets_yoy = 0.14,
    ccb.avg_loans_yoy             = 0.09,
    ccb.card_nco_rate_2024        = 0.0334,
    ccb.debit_credit_sales_vol_yoy = 0.08,
    ccb.active_mobile_customers_yoy = 0.07,
    ccb.trust                     = 'SYNTHESIZED',
    ccb.reliability               = 0.9,
    ccb.metric_year               = 2024,
    ccb.metric_source             = 'mda10k-2024 p7';

MERGE (cib:BusinessSegment {code: 'CIB'})
SET cib.name                      = 'Commercial & Investment Bank',
    cib.roe_2024                  = 0.18,
    cib.ib_fees_yoy               = 0.37,
    cib.global_ib_wallet_share    = 0.093,
    cib.global_ib_rank            = 1,
    cib.markets_revenue_yoy       = 0.07,
    cib.fixed_income_markets_yoy  = 0.05,
    cib.equity_markets_yoy        = 0.13,
    cib.trust                     = 'SYNTHESIZED',
    cib.reliability               = 0.9,
    cib.metric_year               = 2024,
    cib.metric_source             = 'mda10k-2024 p7';

MERGE (awm:BusinessSegment {code: 'AWM'})
SET awm.name                   = 'Asset & Wealth Management',
    awm.roe_2024               = 0.34,
    awm.aum_trillions_2024     = 4.0,
    awm.aum_yoy                = 0.18,
    awm.avg_loans_yoy          = 0.03,
    awm.avg_deposits_yoy       = 0.09,
    awm.trust                  = 'SYNTHESIZED',
    awm.reliability            = 0.9,
    awm.metric_year            = 2024,
    awm.metric_source          = 'mda10k-2024 p7';

// Firm-wide metrics node (use DataAsset as the carrier — no new node types).
MERGE (firm:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:firmwide-metrics-2024'})
SET firm.name                 = 'firmwide-metrics-2024',
    firm.namespace            = 'jpmc',
    firm.platform             = 'document',
    firm.format               = 'METRICS',
    firm.total_net_revenue_m  = 177556,
    firm.net_interest_income_m = 92583,
    firm.noninterest_revenue_m = 84973,
    firm.net_income_m         = 58471,
    firm.diluted_eps          = 19.75,
    firm.rotce                = 0.22,
    firm.cet1_ratio           = 0.157,
    firm.metric_year          = 2024,
    firm.trust                = 'SYNTHESIZED',
    firm.reliability          = 0.95,
    firm.metric_source        = 'mda10k-2024 p5';

// GENERATED edges: documents -> metrics they produced.
MATCH (mda:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:mda10k-2024'})
MATCH (ccb:BusinessSegment {code: 'CCB'})
MATCH (cib:BusinessSegment {code: 'CIB'})
MATCH (awm:BusinessSegment {code: 'AWM'})
MATCH (firm:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:firmwide-metrics-2024'})
MERGE (mda)-[:GENERATED]->(ccb)
MERGE (mda)-[:GENERATED]->(cib)
MERGE (mda)-[:GENERATED]->(awm)
MERGE (mda)-[:GENERATED]->(firm);

MATCH (ar:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:annualreport-2024'})
MATCH (mda:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:mda10k-2024'})
MERGE (ar)-[:GENERATED]->(mda);

§OQ
OQ1  Corp segment metrics not extracted — pages not clearly tagged in PDF text layer.
     Action: manually verify Corp segment page range in Annual Report.
OQ2  Pre-Q2-2024 CB segment: no 2024 metrics (retired). Confirm no residual data needed.
OQ3  Firm-wide 2022 comparatives omitted (3-year table truncated in PDF extraction).
     Action: re-extract p10 full table for 2022 column.
OQ4  Promotion path: which of these SYNTHESIZED metric properties should be promoted
     to drydocs BusinessSegment nodes via the HITL gate?
     Candidates: roe_2024, aum_trillions_2024, global_ib_wallet_share.
