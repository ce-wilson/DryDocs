# DRAFT — business-segments CSV load (annual-report source, External/public)

> **Point-in-time draft, preserved verbatim.** Written 2026-08-17 by a remote-control
> session and recovered from that session's scratchpad. Still GATE-BOUND — nothing below
> is registered, built, or loaded.
>
> **Read it against gate `corporate-backbone-vocabulary` (G98, SIGNED 19/19, `faa0bdd8`),
> which landed the same day and was not visible to the draft.** Three corrections:
>
> 1. **§1 is wrong about vocabulary status.** The draft says both rel types are "already
>    `active` in the vocabulary" and so only a source-mapping confirmation is needed. They
>    were in fact **UNREGISTERED** — that omission is the whole reason G98 ran. They are now
>    registered in `49-local-corporate.yaml` under the new `corporate` domain at
>    **`status: planned`, `loader: ~`** — not `active`. The load path therefore still has a
>    vocabulary promotion ahead of it, not just a source confirmation.
> 2. **G-D is CLOSED, not deferred.** The draft parks "unify the two rel types" as optional
>    future work. G98 **§B1 ruled two edge types, not one** — currency is carried by the type
>    name as well as by `effective_to`, and the one-type alternative was explicitly declined.
>    Do not reopen it as an incidental part of this load.
> 3. **This loader inherits an obligation from G98 §B2.** The two-type ruling encodes currency
>    twice, and the two encodings can disagree — a `HAS_BUSINESS_SEGMENT` edge with a non-null
>    `effective_to` is writable and meaningless. The SME ruled a **graph-test** (Neo4j cannot
>    express the constraint), noting the exposure "arrives with the first loader that writes
>    these edges." **This draft describes that first loader**, so the graph-test belongs in its
>    acceptance list in §6, where it does not yet appear.
>
> What G98 **corroborates**: the External / publishable classification in §2 — §E1 ruled the
> annual-report source publishable, which is why the vocabulary entries carry real spellings
> rather than placeholders.

**Status:** DRAFT for SME review — GATE-BOUND. Nothing here is registered, built, or
loaded. Supersession of the recorded "don't put corporate-org changes in CSV land"
note (`drydocs/loaders/business_segments.py` docstring) is itself gate item G-A below.
**Date:** 2026-08-17.
**Source facts verified against:** `drydocs_core/schema/ontology.cypher:204-234` (the
M0 seed), `config/doc-source-registry.yaml:261-284` (`jpmc-reports`, `confirmed: false`),
`drydocs/loaders/business_segments.py` (the no-op refresh path this loader replaces).

---

## 1. What this changes and what it deliberately does not

- **Changes:** Company→BusinessSegment facts stop being a hand-edited Cypher seed and
  become a **registered, SME-authored CSV** loaded by a normal loader with the full
  run envelope (`JobRun` / `WAS_GENERATED_BY`), idempotent MERGE, and registry-bound
  provenance. The `jpmc-reports` entry's dangling `confirmed: false` gets a real
  loader binding at last (the N9 trigger).
- **Does not change:** edge meaning. Both existing rel types are reused exactly as
  seeded — `HAS_BUSINESS_SEGMENT` (current, open-ended) and
  `HAS_BUSINESS_SEGMENT_HISTORICAL` (closed interval) — both already `active` in the
  vocabulary. No new relationship type, so the gate needed is a **source-mapping
  confirmation**, not a new-edge ontology gate. (Optional later question: unify the
  two rel types into one effective-dated type — G-D, explicitly out of scope here.)

## 2. Source registration (External / public)

The CSV is an SME-curated extract **from public filings** — content is External even
though a person typed it (nearest precedent: `manual_seal_attribution.v1`'s
human-authored CSVs, but those are Internal; this one is not).

```yaml
# config/source-registry.yaml (or stay in doc-source-registry — decision G-B)
- id: jpmc-reports:business-segments-csv
  classification: External                # public SEC/IR filings; cite source_url
  connector: filedrop
  source_url: https://www.jpmorganchase.com/ir/annual-report
  trust_default: GROUNDED                 # human extraction citing the page — not VERBATIM
  tier: T1
  refresh: manual                         # annual, or on reorg
  file: config/manual-loads/business_segments.csv   # committed — External content, no secrets
  confirmed: false                        # flips at the gate
```

Note the trust call: the seed stamped `source = "annual report"`; rows in this CSV are
**GROUNDED** (a person read the filing and wrote the row, citing document + page), not
VERBATIM (no verbatim text is carried). Matches the old ingest script's own tiering.

## 3. CSV column contract — `business_segments.csv`

| # | Column | Type | Req | Rule |
|---|--------|------|-----|------|
| 1 | `company` | str | ✔ | Business key of `:Company` (`JPMC`); future-proofs multi-company |
| 2 | `company_legal_name` | str | ✔ | e.g. `JPMorgan Chase & Co.` (SET on the Company node) |
| 3 | `code` | str | ✔ | Segment business key (`CCB`, `CIB`, `AWM`, `Corp`, `CB`) — the uniqueness grain |
| 4 | `name` | str | ✔ | Segment display name |
| 5 | `status` | enum | ✔ | `current` \| `retired` — drives `s.retired` |
| 6 | `merged_into` | str | ∅ | Segment code this one folded into (e.g. `CB` → `CIB`); empty for current |
| 7 | `effective_from` | date | ✔ | ISO date; edge property |
| 8 | `effective_to` | date | ∅ | Empty = open-ended → `HAS_BUSINESS_SEGMENT`; set → `HAS_BUSINESS_SEGMENT_HISTORICAL` |
| 9 | `source_doc` | str | ✔ | Which filing, e.g. `annualreport-2024`, `mda10k-2024` |
| 10 | `source_page` | str | ∅ | Page/section citation within the filing |
| 11 | `source_url` | str | ✔ | Public URL of the filing |
| 12 | `captured_at` | date | ✔ | When the SME extracted the row |

**Interval rule (the one that prevents silent overwrites):** a reorg is expressed by
ADDING rows — close the old interval (set `effective_to`) and add the new open row.
The loader never deletes; a code that disappears from the CSV is a validation error,
not a retirement.

**Seed-equivalent content (the initial file, matching ontology.cypher exactly):**

```csv
company,company_legal_name,code,name,status,merged_into,effective_from,effective_to,source_doc,source_page,source_url,captured_at
JPMC,JPMorgan Chase & Co.,CCB,Consumer & Community Banking,current,,2024-04-01,,annualreport-2024,,https://www.jpmorganchase.com/ir/annual-report,2026-06-30
JPMC,JPMorgan Chase & Co.,CIB,Commercial & Investment Bank,current,,2024-04-01,,annualreport-2024,,https://www.jpmorganchase.com/ir/annual-report,2026-06-30
JPMC,JPMorgan Chase & Co.,AWM,Asset & Wealth Management,current,,2024-04-01,,annualreport-2024,,https://www.jpmorganchase.com/ir/annual-report,2026-06-30
JPMC,JPMorgan Chase & Co.,Corp,Corporate,current,,2024-04-01,,annualreport-2024,,https://www.jpmorganchase.com/ir/annual-report,2026-06-30
JPMC,JPMorgan Chase & Co.,CCB,Consumer & Community Banking,current,,2010-01-01,2024-03-31,annualreport-2024,,https://www.jpmorganchase.com/ir/annual-report,2026-06-30
JPMC,JPMorgan Chase & Co.,CIB,Commercial & Investment Bank,current,,2010-01-01,2024-03-31,annualreport-2024,,https://www.jpmorganchase.com/ir/annual-report,2026-06-30
JPMC,JPMorgan Chase & Co.,AWM,Asset & Wealth Management,current,,2010-01-01,2024-03-31,annualreport-2024,,https://www.jpmorganchase.com/ir/annual-report,2026-06-30
JPMC,JPMorgan Chase & Co.,CB,"Commercial Banking (pre-Q2-2024, merged into CIB)",retired,CIB,2010-01-01,2024-03-31,annualreport-2024,,https://www.jpmorganchase.com/ir/annual-report,2026-06-30
```

(Open rows → the 4 current `HAS_BUSINESS_SEGMENT` edges; closed rows → the 4
`HAS_BUSINESS_SEGMENT_HISTORICAL` edges. `2010-01-01` is the seed's stand-in date —
flag for the SME: replace with the real pre-reorg baseline if one is worth recording.)

## 4. Loader sketch — `BusinessSegmentsCsvLoader`

Home: `drydocs/loaders/business_segments.py` (replaces the no-op refresh in place —
same module, MODULE_MAP row unchanged). Follows the `base.py` loader pattern: run
envelope, `run_script`/`run` via `Neo4jClient`, UNWIND batching, MERGE on business keys.

```python
class BusinessSegmentsCsvLoader(BaseLoader):          # base.py pattern
    """CSV-fed corporate hierarchy: Company -> effective-dated BusinessSegments.

    Supersedes the ontology.cypher M0 seed as the write path for corporate-org
    changes (gate <id>). Seed stays bootstrap-only for empty-DB provisioning.
    """
    name = "business_segments.v2"
    source_id = "jpmc-reports:business-segments-csv"

    def validate(self, rows):
        # fail fast, D3 pattern:
        # - codes unique per (code, effective_from) interval
        # - status=retired requires merged_into; merged_into must exist as a code
        # - open rows (no effective_to) exactly one interval per code
        # - every code seen in the graph still present in the CSV (no silent drops)
        # - all of company/code/name/effective_from/source_doc/source_url present

    def load(self, rows):
        self.client.run_script(SEGMENTS_CYPHER, params={"rows": rows})
```

```cypher
// SEGMENTS_CYPHER — idempotent, current edges
UNWIND $rows AS row
MERGE (c:Company {name: row.company})
  SET c.legal_name = row.company_legal_name,
      c.source     = row.source_doc
MERGE (s:BusinessSegment {code: row.code})
  SET s.name    = row.name,
      s.retired = row.status = 'retired'
WITH c, s, row
CALL {
  WITH c, s, row
  WITH c, s, row WHERE row.effective_to IS NULL
  MERGE (c)-[r:HAS_BUSINESS_SEGMENT]->(s)
    SET r.effective_from = date(row.effective_from),
        r.effective_to   = null,
        r.source         = row.source_doc,
        r.source_url     = row.source_url,
        r.source_page    = row.source_page,
        r.captured_at    = date(row.captured_at)
}
CALL {
  WITH c, s, row
  WITH c, s, row WHERE row.effective_to IS NOT NULL
  MERGE (c)-[r:HAS_BUSINESS_SEGMENT_HISTORICAL]->(s)
    SET r.effective_from = date(row.effective_from),
        r.effective_to   = date(row.effective_to),
        r.source         = row.source_doc + ' (pre-Q2-2024)',
        r.source_url     = row.source_url,
        r.captured_at    = date(row.captured_at)
}
```

- **Idempotency:** MERGE on `Company.name` / `BusinessSegment.code` (both already
  constraint-backed: `company_name`, plus the segment key) and on the rel per
  (company, segment, type). Re-running an unchanged CSV changes nothing.
- **Provenance upgrade over the seed:** edges gain `source_url`, `source_page`,
  `captured_at` — today they carry only the string `"annual report"`.
- **CLI:** wire as `drydocs load-business-segments` (or fold into the manual-loads
  verb family); position in `CANONICAL_LOAD_SEQUENCE` before the catalog loaders
  that hang context off segments. `refresh_business_segments()` survives as the
  post-load verify (its count/codes check becomes the acceptance probe).
- **Seed disposition:** `ontology.cypher` KEEPS its block for empty-DB bootstrap
  (provisioning order needs a Company before catalog reconciliation), but the block
  gains a header comment naming the CSV as the maintenance path of record.

## 5. Gate items

| # | Decision |
|---|---|
| G-A | Supersede the "no CSV land" docstring rule: corporate-org changes move to the registered CSV; seed becomes bootstrap-only. (The rule's original point — don't scatter org facts across ad-hoc CSVs — is preserved by there being exactly ONE registered file.) |
| G-B | Registry home: new object under `source-registry.yaml` vs extending the existing `jpmc-reports` entry in `doc-source-registry.yaml`. Draft assumes a linked child id (`jpmc-reports:business-segments-csv`) either way; flips `confirmed` at this gate. |
| G-C | Trust tier GROUNDED (not VERBATIM) for SME-extracted rows citing document+page — confirm. |
| G-D | (Optional, deferred) Unify `HAS_BUSINESS_SEGMENT` + `_HISTORICAL` into one effective-dated rel type. Out of scope for this load; listed so it is not decided by accident. |

## 6. Acceptance (when built)

- Registry entry passes `test_doc_registry.py` / classification tests; CSV committed
  (External, no secrets — publishable).
- `load-business-segments` on the seed-equivalent CSV against a bootstrapped DB is a
  **zero-delta** run (proves seed parity), and a re-run adds nothing (idempotency).
- Reorg rehearsal: closing CCB's interval + adding a successor row produces exactly
  one closed edge + one new open edge, nothing deleted.
- `refresh_business_segments()` returns 4 active codes before and after.
