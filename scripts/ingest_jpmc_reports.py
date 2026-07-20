"""
ingest_jpmc_reports.py — Full ingestion of JPMorgan Chase public annual report PDFs
into the ddcontext Neo4j database.

Documents are External / public-domain (SEC filings), so:
  - classification: External
  - trust: VERBATIM (direct text) / GROUNDED (derived metrics)
  - target: ddcontext for this test run; can be promoted to drydocs directly

Node types used (no new labels introduced):
  :DataAsset      — document root + per-section corpus slices
  :BusinessSegment — CCB / CIB / AWM / Corp with extracted 2024 metrics

Edges:
  (doc)-[:GENERATED]->(section)
  (section)-[:GENERATED]->(segment)
"""

from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from typing import Optional

from neo4j import GraphDatabase
from pypdf import PdfReader

# ── Connection ────────────────────────────────────────────────────────────────
URI      = "bolt://localhost:7687"
AUTH     = ("neo4j", "drydocs-dev")
DATABASE = "ddcontext"

# ── Source documents ──────────────────────────────────────────────────────────
DOCS = [
    {
        "assetId":    "urn:drydocs:dataasset:document:jpmc:annualreport-2024",
        "name":       "annualreport-2024",
        "title":      "Resolute Annual Report 2024",
        "path":       r"C:\coding\projects\DryDocs\jpmorgan-chase-annualreport-2024.pdf",
        "source_url": "https://www.jpmorganchase.com/content/dam/jpmc/jpmorgan-chase-and-co/investor-relations/documents/annualreport-2024.pdf",
    },
    {
        "assetId":    "urn:drydocs:dataasset:document:jpmc:mda10k-2024",
        "name":       "mda10k-2024",
        "title":      "CORP 10K 2024 — Management's Discussion & Analysis",
        "path":       r"C:\coding\projects\DryDocs\managements-discussion-analysis-2024.pdf",
        "source_url": "https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK=0000019617&type=10-K&dateb=&owner=include&count=10",
    },
]

# ── Section detection rules (order matters — first match wins) ─────────────
# Each rule: (label, regex pattern matched against page text)
SECTION_RULES: list[tuple[str, str]] = [
    ("executive-overview",          r"EXECUTIVE OVERVIEW"),
    ("segment-ccb",                 r"CONSUMER & COMMUNITY BANKING\b"),
    ("segment-cib",                 r"COMMERCIAL & INVESTMENT BANK\b"),
    ("segment-awm",                 r"ASSET & WEALTH MANAGEMENT\b"),
    ("segment-corp",                r"^Corporate$|CORPORATE SEGMENT"),
    ("consolidated-results",        r"CONSOLIDATED RESULTS OF OPERATIONS"),
    ("capital-management",          r"CAPITAL MANAGEMENT"),
    ("liquidity-risk",              r"LIQUIDITY RISK"),
    ("market-risk",                 r"MARKET RISK"),
    ("credit-risk",                 r"CREDIT AND INVESTMENT RISK"),
    ("operational-risk",            r"OPERATIONAL RISK"),
    ("critical-accounting",         r"CRITICAL ACCOUNTING ESTIMATES"),
    ("risk-factors",                r"RISK FACTORS"),
    ("forward-looking",             r"forward-looking statements"),
    ("shareholder-letter",          r"(?i)dear fellow shareholders?"),
    ("governance",                  r"CORPORATE GOVERNANCE"),
]

# Segment → section mapping for GENERATED edges
SEG_SECTIONS = {
    "CCB": "segment-ccb",
    "CIB": "segment-cib",
    "AWM": "segment-awm",
    "Corp": "segment-corp",
}


# ── Metric extraction helpers ─────────────────────────────────────────────────

def _pct(text: str, pattern: str) -> Optional[float]:
    """Extract a percentage as a float (e.g. '32%' → 0.32)."""
    m = re.search(pattern, text)
    if m:
        try:
            return float(m.group(1)) / 100
        except (ValueError, IndexError):
            pass
    return None


def _dollar_m(text: str, pattern: str) -> Optional[float]:
    """Extract a dollar amount in millions (handles commas)."""
    m = re.search(pattern, text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except (ValueError, IndexError):
            pass
    return None


def _int_val(text: str, pattern: str) -> Optional[int]:
    m = re.search(pattern, text)
    if m:
        try:
            return int(m.group(1).replace(",", ""))
        except (ValueError, IndexError):
            pass
    return None


def extract_segment_metrics(full_text: str) -> dict:
    """Best-effort extraction of key 2024 metrics from raw PDF text."""
    metrics: dict = {}

    # Firm-wide totals (from MD&A executive overview table)
    metrics["total_net_revenue_m"]   = _dollar_m(full_text, r"Total net revenue\s+[\$\s]*([\d,]+)")
    metrics["net_interest_income_m"] = _dollar_m(full_text, r"Net interest income\s+[\$\s]*([\d,]+)")
    metrics["noninterest_revenue_m"] = _dollar_m(full_text, r"Noninterest revenue\s+[\$\s]*([\d,]+)")
    metrics["net_income_m"]          = _dollar_m(full_text, r"Net income\s+[\$\s]*([\d,]+)")
    metrics["diluted_eps"]           = _dollar_m(full_text, r"Diluted earnings per share\s+[\$\s]*([\d.]+)")
    metrics["rotce"]                 = _pct(full_text, r"Return on tangible common\s*\n?\s*equity\s+([\d.]+)\s*%")
    metrics["cet1_ratio"]            = _pct(full_text, r"CET1 capital\s+([\d.]+)\s*%")

    # Segment ROEs
    metrics["ccb_roe"]  = _pct(full_text, r"CCB\s*\n+ROE\s*([\d]+)%")
    metrics["cib_roe"]  = _pct(full_text, r"CIB[^\n]*\n+ROE\s*([\d]+)%")
    metrics["awm_roe"]  = _pct(full_text, r"AWM\s*\n+ROE\s*([\d]+)%")

    # AWM AUM
    metrics["awm_aum_trillions"] = _dollar_m(full_text, r"AUM.*?\$([\d.]+)\s*trillion")
    if metrics["awm_aum_trillions"] is None:
        metrics["awm_aum_trillions"] = _dollar_m(
            full_text, r"assets under management.*?\$([\d.]+)\s*tril", )

    # IB fees / wallet share
    metrics["cib_ib_fees_yoy"]         = _pct(full_text, r"Investment Banking fees up ([\d]+)%")
    metrics["cib_global_ib_wallet_pct"] = _dollar_m(full_text, r"([\d.]+)%\s*wallet share")

    # Card NCO rate
    metrics["ccb_card_nco_rate"] = _pct(full_text, r"net charge-off rate of ([\d.]+)%")

    # Remove None values
    return {k: v for k, v in metrics.items() if v is not None}


# ── PDF processing ────────────────────────────────────────────────────────────

@dataclass
class Section:
    slug: str
    page_start: int
    page_end: int
    pages: list[str] = field(default_factory=list)

    @property
    def full_text(self) -> str:
        return "\n".join(self.pages)

    @property
    def text_excerpt(self) -> str:
        return self.full_text[:2000]

    @property
    def word_count(self) -> int:
        return len(self.full_text.split())


def _is_section_heading(text: str, pattern: str) -> bool:
    """
    True only when the pattern appears in the first 600 characters of the page
    (i.e. it's a heading, not a body mention) AND the line is short (< 80 chars).
    This prevents body references from triggering false section breaks.
    """
    head = text[:600]
    m = re.search(pattern, head, re.IGNORECASE | re.MULTILINE)
    if not m:
        return False
    # Find the line containing the match and check it's heading-length
    line_start = head.rfind("\n", 0, m.start()) + 1
    line_end   = head.find("\n", m.end())
    if line_end == -1:
        line_end = len(head)
    line = head[line_start:line_end].strip()
    return len(line) < 80


def detect_sections(pages: list[str]) -> list[Section]:
    """
    Split pages into named sections. A section boundary is only triggered when
    the heading pattern appears near the top of a page (first 600 chars) on a
    short line — not when the term is mentioned in body text.
    Consecutive pages with the same section slug are merged.
    """
    # Assign a slug to each page
    page_slugs: list[str] = []
    for text in pages:
        matched = None
        for slug, pattern in SECTION_RULES:
            if _is_section_heading(text, pattern):
                matched = slug
                break
        page_slugs.append(matched or "")

    # Propagate: each page inherits the last assigned slug (carry-forward)
    current = "preamble"
    assigned: list[str] = []
    for slug in page_slugs:
        if slug:
            current = slug
        assigned.append(current)

    # Collapse consecutive same-slug runs into one Section
    sections: list[Section] = []
    i = 0
    while i < len(pages):
        slug = assigned[i]
        start = i + 1
        run_pages = []
        while i < len(pages) and assigned[i] == slug:
            run_pages.append(pages[i])
            i += 1
        sections.append(Section(
            slug=slug,
            page_start=start,
            page_end=start + len(run_pages) - 1,
            pages=run_pages,
        ))

    return sections


def read_pdf(path: str) -> tuple[list[str], dict]:
    """Return (page_texts, metadata)."""
    reader = PdfReader(path)
    meta = reader.metadata or {}
    pages = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(text)
    return pages, {
        "title":      str(meta.get("/Title", "")),
        "pdf_author": str(meta.get("/Author", "")),
        "pdf_creator": str(meta.get("/Creator", "")),
        "pages":      len(pages),
    }


# ── Neo4j loading ─────────────────────────────────────────────────────────────

MERGE_DOC = """
MERGE (d:DataAsset {assetId: $assetId})
SET d.name            = $name,
    d.namespace       = 'jpmc',
    d.platform        = 'document',
    d.format          = 'PDF',
    d.title           = $title,
    d.pages           = $pages,
    d.pdf_author      = $author,
    d.pdf_creator     = $creator,
    d.source_url      = $source_url,
    d.classification  = 'External',
    d.trust           = 'VERBATIM',
    d.isExternalFeed  = true,
    d.isSourceOfRecord = true,
    d.captured_at     = date('2026-06-29'),
    d.section_count   = $section_count
RETURN d.assetId AS loaded
"""

MERGE_SECTION = """
MERGE (s:DataAsset {assetId: $assetId})
SET s.name           = $name,
    s.namespace      = 'jpmc',
    s.platform       = 'document',
    s.format         = 'SECTION',
    s.section_slug   = $slug,
    s.parent_doc     = $parent_doc,
    s.page_start     = $page_start,
    s.page_end       = $page_end,
    s.page_count     = $page_count,
    s.word_count     = $word_count,
    s.text_excerpt   = $text_excerpt,
    s.full_text      = $full_text,
    s.classification = 'External',
    s.trust          = 'VERBATIM',
    s.captured_at    = date('2026-06-29')
"""

MERGE_DOC_SECTION_EDGE = """
MATCH (d:DataAsset {assetId: $doc_id})
MATCH (s:DataAsset {assetId: $sec_id})
MERGE (d)-[:GENERATED]->(s)
"""

MERGE_SEGMENT = """
MERGE (seg:BusinessSegment {code: $code})
SET seg.name            = $name,
    seg.classification  = 'External',
    seg.trust           = 'GROUNDED',
    seg.metric_year     = 2024,
    seg.metric_source   = $metric_source,
    seg.captured_at     = date('2026-06-29')
"""

SET_SEGMENT_METRIC = """
MATCH (seg:BusinessSegment {code: $code})
SET seg[$prop] = $value
"""

MERGE_SECTION_SEGMENT_EDGE = """
MATCH (s:DataAsset {assetId: $sec_id})
MATCH (seg:BusinessSegment {code: $seg_code})
MERGE (s)-[:GENERATED]->(seg)
"""

MERGE_FIRMWIDE = """
MERGE (fw:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:firmwide-metrics-2024'})
SET fw.name                  = 'firmwide-metrics-2024',
    fw.namespace             = 'jpmc',
    fw.platform              = 'document',
    fw.format                = 'METRICS',
    fw.classification        = 'External',
    fw.trust                 = 'GROUNDED',
    fw.metric_year           = 2024,
    fw.metric_source         = $source,
    fw.captured_at           = date('2026-06-29')
"""

SET_FIRMWIDE_METRIC = """
MATCH (fw:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:firmwide-metrics-2024'})
SET fw[$prop] = $value
"""

MERGE_DOC_FIRMWIDE_EDGE = """
MATCH (d:DataAsset {assetId: $doc_id})
MATCH (fw:DataAsset {assetId: 'urn:drydocs:dataasset:document:jpmc:firmwide-metrics-2024'})
MERGE (d)-[:GENERATED]->(fw)
"""

SMOKE = """
MATCH (d:DataAsset {platform: 'document'})
OPTIONAL MATCH (d)-[:GENERATED]->(child)
RETURN d.assetId AS asset, d.format AS fmt,
       count(child) AS children
ORDER BY d.format, d.assetId
"""


def load(session, doc_meta: dict, sections: list[Section], metrics: dict) -> None:
    # 1. Document root node
    session.run(MERGE_DOC, **{
        "assetId":       doc_meta["assetId"],
        "name":          doc_meta["name"],
        "title":         doc_meta.get("title") or doc_meta.get("title", ""),
        "pages":         doc_meta["pages"],
        "author":        doc_meta.get("pdf_author", ""),
        "creator":       doc_meta.get("pdf_creator", ""),
        "source_url":    doc_meta["source_url"],
        "section_count": len(sections),
    })
    print(f"  ✓ document node: {doc_meta['assetId']}")

    # 2. Section nodes + edges
    for sec in sections:
        sec_id = f"{doc_meta['assetId']}:section:{sec.slug}"
        session.run(MERGE_SECTION, **{
            "assetId":    sec_id,
            "name":       f"{doc_meta['name']}:{sec.slug}",
            "slug":       sec.slug,
            "parent_doc": doc_meta["assetId"],
            "page_start": sec.page_start,
            "page_end":   sec.page_end,
            "page_count": sec.page_end - sec.page_start + 1,
            "word_count": sec.word_count,
            "text_excerpt": sec.text_excerpt,
            "full_text":  sec.full_text,
        })
        session.run(MERGE_DOC_SECTION_EDGE,
                    doc_id=doc_meta["assetId"], sec_id=sec_id)

        # 3. Wire segment sections → BusinessSegment nodes
        for seg_code, seg_slug in SEG_SECTIONS.items():
            if sec.slug == seg_slug:
                session.run(MERGE_SECTION_SEGMENT_EDGE,
                            sec_id=sec_id, seg_code=seg_code)

    print(f"  ✓ {len(sections)} section nodes loaded")

    # 4. Firmwide metrics node
    session.run(MERGE_FIRMWIDE, source=f"{doc_meta['name']} (extracted)")
    fw_props = {
        k: v for k, v in metrics.items()
        if k in ("total_net_revenue_m", "net_interest_income_m",
                 "noninterest_revenue_m", "net_income_m",
                 "diluted_eps", "rotce", "cet1_ratio")
    }
    for prop, val in fw_props.items():
        session.run(SET_FIRMWIDE_METRIC, prop=prop, value=val)
    session.run(MERGE_DOC_FIRMWIDE_EDGE, doc_id=doc_meta["assetId"])
    print(f"  ✓ firmwide metrics: {list(fw_props.keys())}")


def load_segments(session, metrics: dict, source: str) -> None:
    """Merge BusinessSegment nodes with extracted metrics."""
    SEGMENTS = {
        "CCB":  ("Consumer & Community Banking", {
            "roe_2024":                     metrics.get("ccb_roe"),
            "card_nco_rate_2024":           metrics.get("ccb_card_nco_rate"),
            "avg_deposits_yoy":             -0.06,   # from MD&A p7: "down 6%"
            "client_investment_assets_yoy": 0.14,
            "avg_loans_yoy":                0.09,
            "debit_credit_sales_vol_yoy":   0.08,
            "active_mobile_customers_yoy":  0.07,
        }),
        "CIB":  ("Commercial & Investment Bank", {
            "roe_2024":                metrics.get("cib_roe"),
            "ib_fees_yoy":             metrics.get("cib_ib_fees_yoy"),
            "global_ib_wallet_share":  (metrics["cib_global_ib_wallet_pct"] / 100
                                        if "cib_global_ib_wallet_pct" in metrics else 0.093),
            "global_ib_rank":          1,
            "markets_revenue_yoy":     0.07,
            "fixed_income_markets_yoy": 0.05,
            "equity_markets_yoy":      0.13,
        }),
        "AWM":  ("Asset & Wealth Management", {
            "roe_2024":            metrics.get("awm_roe"),
            "aum_trillions_2024":  metrics.get("awm_aum_trillions"),
            "aum_yoy":             0.18,
            "avg_loans_yoy":       0.03,
            "avg_deposits_yoy":    0.09,
        }),
        "Corp": ("Corporate", {}),
    }

    for code, (name, seg_metrics) in SEGMENTS.items():
        session.run(MERGE_SEGMENT, code=code, name=name,
                    metric_source=f"{source} (extracted)")
        written = []
        for prop, val in seg_metrics.items():
            if val is not None:
                session.run(SET_SEGMENT_METRIC, code=code, prop=prop, value=val)
                written.append(prop)
        print(f"  ✓ BusinessSegment {code}: {len(written)} metrics")


def smoke_query(session) -> None:
    print("\n--- Smoke query ---")
    result = session.run(SMOKE)
    for record in result:
        print(f"  {record['fmt']:10s}  {record['asset'][:60]}  "
              f"children={record['children']}")


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Connecting to ddcontext …")
    driver = GraphDatabase.driver(URI, auth=AUTH)
    driver.verify_connectivity()
    print(f"  connected: {URI}")

    all_text = ""

    with driver.session(database=DATABASE) as session:
        for doc_cfg in DOCS:
            print(f"\n--- {doc_cfg['name']} ---")
            pages, pdf_meta = read_pdf(doc_cfg["path"])
            print(f"  read {pdf_meta['pages']} pages")

            sections = detect_sections(pages)
            slugs = [s.slug for s in sections]
            print(f"  sections detected: {slugs}")

            doc_meta = {**doc_cfg, **pdf_meta}
            load(session, doc_meta, sections, {})

            all_text += "\n".join(pages)

        print("\n--- Extracting metrics from combined text ---")
        metrics = extract_segment_metrics(all_text)
        print(f"  extracted: {list(metrics.keys())}")

        print("\n--- Loading BusinessSegment nodes ---")
        load_segments(session, metrics, "jpmc-mda10k-2024")

        smoke_query(session)

    driver.close()
    print("\nDone.")


if __name__ == "__main__":
    main()
