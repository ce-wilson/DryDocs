# Chase leadership-page scrape — membership evidence and the self-drift record (2026-08-27)

**Status:** evidence for the drafted, unsigned gate `business-layer-org-structure`
(C28's deliverable; the sign-off is a separate SME session — this document decides
nothing). Registered as `doc-source-registry#chase-leadership-scrape` (External,
`confirmed: false` — no loader binds to it; any load is gated).

**Classification: Internal-Public.** Every fact below is quoted from public,
company-published web pages; each carries its `source_url`. The raw HTML captures
were NOT committed (the `jpmc-reports` never-commit precedent) — they live in the
capture session's local scratchpad, and this transcription is the citable
artifact. The full per-page sha256 table below is what makes a refetch
comparable: the pages publish no edit dates, so the hash is the only change
signal.

**Trust tiers in this document:** quoted sentences are VERBATIM; the roster table
is VERBATIM (transcribed tile and bio text); the unit grouping in section 3 is
SYNTHESIZED and labeled as such.

---

## 1. Capture record

- **Source:** `https://media.chase.com/leadership` (index) plus 22 individual bio
  pages at `https://media.chase.com/leadership/<slug>` — the company's public
  media/press site.
- **Captured:** 2026-08-27, direct HTTP GET (no JS rendering required; the pages
  are server-rendered static HTML, roughly 33 KB each).
- **Scope:** the complete roster the index page listed on the capture date —
  22 leaders, all resolving to the one org unit the page documents: the
  **Consumer & Community Banking (CCB) Leadership Team**.

| page | sha256 | bytes |
|---|---|---|
| `leadership (index)` | `e6d40846b0737a25082107eea3cbaa325f44fb45dd205f4c9b6ee85a6192bb6e` | 43,390 |
| `allison-beer` | `bb5314d0b79f1615cc4422ca0a67fe14876e9b297200d2a6a5dde222fbe10169` | 33,627 |
| `bori-cox` | `f493fe8bd743fec479af34d42a56acd6254a49f3bdaade394f2fc59ff0c04f5a` | 33,008 |
| `carla-hassan` | `1d84f79f05347ee0dc0361917351ddcd9d6ac0bbf68ebf8b75ee05b75d248b9f` | 34,413 |
| `chris-henry` | `84708691334f55fc6e21b7f71e3d1864d80404095bec4ec92551e795ecd0d470` | 33,596 |
| `chris-stang` | `82024d5a8cf91cf9c66dfac76642a33574e282c99c8b5edcc79974dd764867f3` | 33,339 |
| `danielle-bartolomei` | `f563a3f388d2f1a19face6d1ae7109f2ab252ff4211c9a5da5b61d5f61b07d14` | 32,911 |
| `gill-haus` | `15a10878fbd384cb169fee0fc9210be5558916f940c89e5fa60d3f194f30408b` | 34,313 |
| `jennifer-roberts` | `4290e2021dd6e19081e1f60dd236da673f8168432a132a7f4e5b1b6ae0c3a5f2` | 33,393 |
| `jon-shaw` | `cc06d89fb21c2643a0c425aa929550f6061e682385f4280cadbd2d05185e1073` | 32,960 |
| `julie-bohan` | `6022138a674e25ac3447ce908af2c63c3d72db8a5775afbafb781c81bfb235d2` | 33,316 |
| `kristin-lemkau` | `a884c21637b47887cb28163b31fe884be2ba269f21b67eb5f21f9bd97faf756f` | 35,397 |
| `leslie-wims-morris` | `2b796addfe067e5969f0f8d2e8460c8748ec25e060c761c0624708f6d52c3366` | 34,362 |
| `mark-brucker` | `77b84c38ae4ba8abc3a96f67517d29204f75abbad441f689b34434e5f56ab3f7` | 32,952 |
| `melissa-feldsher` | `c401a2f70e724847a914cdaeab2ca4001da31c5d9111f37792e9827d1825c091` | 32,798 |
| `mike-ashworth` | `64e2163e29100f928d5e6d0dee8bf5f1d16e0d3b50ce6df615206ef4d593df78` | 33,021 |
| `pablo-rodriguez` | `4d4e6bf34e382e2fb3fd4747c174e64a3e9480660f62e502a8282d18ee3f6916` | 33,931 |
| `pauline-saunders` | `0be5ab8a7ca1d0f1875dd6dd60e458d324715008055be07fc139fde3ef6c3e0d` | 33,602 |
| `peter-muriungi` | `ee9d3b69b0d03afb68b43a643f8ec46af0ccd5b4a675e93820a32fa68c3ac6a9` | 33,971 |
| `sean-grzebin` | `38d88f390dc42f4aec5605142527478b065e9765e25918095927b9c001902bdd` | 33,089 |
| `seth-wheeler` | `f3fe9bd44c43dd8ec9586ab01e33d2ebab9194edb90040d9c51baabd42a1dd17` | 33,258 |
| `stevie-baron` | `548c681e5cd1350bd1e3d4b0bcb54990b26178f605bbab04235af35b5625ec88` | 33,157 |
| `troy-rohrbaugh` | `c4e2a83c62da717b0e2f90dfa7f1d1f4941e3523e67ce286d621658885aed8d9` | 33,709 |

A refetch that changes any hash re-queues review of that page (the
doc-source-registry freshness rule: a changed page never silently overwrites
confirmed content).

## 2. The roster — VERBATIM tier

Tile title = the index page's grid; unit attachment = the bio's own words.

| person | tile title | bio unit attachment (quoted) |
|---|---|---|
| Troy Rohrbaugh | *(none — see drift D3)* | "Co-President of JPMorganChase and a member of the firm's Operating Committee. He is also CEO for Consumer & Community Banking (CCB)... He also leads International Consumer Banking." |
| Allison Beer | CEO, Card Services and Connected Commerce | "chief executive officer for Chase's Card & Connected Commerce businesses and a member of the Consumer & Community Banking leadership team" |
| Jennifer Roberts | CEO, Consumer Banking | "Chief Executive Officer of Chase Consumer Banking" |
| Stevie Baron | Chief Executive Officer for Business Banking | "Chief Executive Officer for Business Banking" |
| Sean Grzebin | CEO, Home Lending | "Chief Executive Officer of Chase Home Lending" |
| Leslie Wims Morris | CEO, Auto | "CEO of Chase Auto and a member of the Consumer & Community Banking (CCB) leadership team" |
| Kristin Lemkau | CEO, J.P. Morgan Wealth Management | "Chief Executive Officer of J.P. Morgan Wealth Management at JPMorgan Chase" |
| Peter Muriungi | CEO, Digital Assets and Blockchain Solutions | "chief executive officer of Digital Assets and Blockchain Solutions and a member of the Consumer & Community Banking Leadership team" |
| Melissa Feldsher | Head of Payments, Consumer & Community Banking | "Head of Payments for Consumer & Community Banking (CCB)" |
| Bori Cox | Chief Financial Officer | "Chief Financial Officer of Consumer & Community Banking" |
| Gill Haus | Chief Information Officer | "Chief Information Officer of Consumer & Community Banking (CCB) at JPMorgan Chase"; "heads the Chase Technology Team and is a member of the CCB Leadership Team and the firm's Global Technology Leadership Team (GTL)" |
| Mike Ashworth | Chief Operating Officer | "Chief Operating Officer for Consumer & Community Banking (CCB)" |
| Seth Wheeler | Chief Data & Analytics Officer | "Chief Data & Analytics Officer for Consumer & Community Banking (CCB)" |
| Mark Brucker | Chief Risk Officer | "Chief Risk Officer for Consumer & Community Banking (CCB)... member of the Firmwide Risk Committee, Risk Operating Committee and CCB Leadership Team" |
| Danielle Bartolomei | Chief Compliance Officer | "a Managing Director and serves as the Chief Compliance and Operational Risk Officer for Consumer & Community Banking" *(see drift D2)* |
| Jon Shaw | Chief Auditor | "Chief Auditor for Consumer and Community Banking and International Consumer Banking and also serves as International Chief Auditor... member of the Audit Operating Committee" |
| Pauline Saunders | Chief Control Manager | "Chief Control Manager for all Consumer & Community Banking (CCB) lines of business... member of the JPMC Control Management Leadership Team and the CCB Leadership Team" |
| Julie Bohan | Head of Human Resources | "Head of Human Resources for Consumer & Community Banking (CCB)... member of the firm's HR Operating Committee" |
| Chris Henry | Head of Strategy & Corporate Development | "Head of Strategy & Corporate Development for Consumer & Community Banking (CCB)... member of the CCB leadership team" |
| Pablo Rodriguez | Chief Communications Officer | "responsible for the strategic planning and execution of internal, external, executive and social media communications that support CCB's eight lines of business and nine functions" |
| Carla Hassan | Chief Marketing Officer | "Chief Marketing Officer of JPMorganChase" — a FIRMWIDE seat listed on the CCB page |
| Chris Stang | Chief Product Officer for Digital | bio leads with responsibility for "Chase Digital Assistant and overall strategy on agentic AI" *(see drift D5)* |

## 3. The unit grouping — SYNTHESIZED tier

Pablo Rodriguez's bio states the shape: CCB has **"eight lines of business and
nine functions."** Grouping the 22 by title pattern reproduces it — eight LOB
heads (Card & Connected Commerce, Consumer Banking, Business Banking, Home
Lending, Auto, J.P. Morgan Wealth Management, Digital Assets & Blockchain
Solutions, Payments) under Troy Rohrbaugh, with the rest as function seats. The
tree layout is INFERENCE from that one sentence plus title patterns; no page
draws it. Any use of the grouping cites this section as SYNTHESIZED, never the
pages.

## 4. What the corpus is evidence FOR, and NOT for

**FOR: membership.** The bios make explicit, quotable membership assertions
("member of the CCB Leadership Team", "member of the firm's Operating
Committee", "member of the firm's Global Technology Leadership Team"). These
support membership and attachment edges of exactly the HAS_MEMBERSHIP shape the
PAT ontology already uses.

**NOT for: reporting lines.** No bio says "reports to." And the silence is
load-bearing, not incidental: the control-function seats (Risk, Compliance,
Audit, Control Management, HR) each declare a SECOND membership in a firmwide
functional org — matrix structure by design. Drawing solid reporting lines from
all 21 to the CCB CEO would be wrong, not merely unverified.

**The two-layer composition.** This corpus joins the `jpmc-reports` layer
(SEC-filed 10-K "Information about our Executive Officers" = the
Operating-Committee register) through Troy Rohrbaugh, who appears in both
worlds; Gill Haus's GTL membership adds one functional-overlay edge between the
layers (Chase Technology inside the firmwide Global Technology org). Two public
sources compose into a two-layer chart with a declared seam. The 10-K layer's
boundary is clean and citable: executive officers of the registrant, nothing
below (EDGAR full-text search confirms the CCB-level names appear in NO SEC
filing, 2001 to present).

## 5. The drift record — the page drifts against itself

Seven findings, each a first-party official page disagreeing with a sibling
page or with its own index. This is the provenance-calibration payload: if the
publisher's OWN surface carries concurrent vintages, then any scrape-sourced
org fact is true as-of its capture and never fresher.

**D1 — one fact, three concurrent vintages.** The CCB customer denominator
appears across sibling bios as: "more than 86 million consumers and 7 million
small businesses" (Bori Cox, Chris Henry, Gill Haus), "more than 87 million
consumers and 7.5 million small businesses" (Mike Ashworth, Pablo Rodriguez;
Troy Rohrbaugh has "nearly 87 million"), and "more than 90 million consumer and
small business Chase customers" (Seth Wheeler, a combined count). Same
denominator, three edit generations, all live on the same day under the same
site chrome. There is no way to tell WHICH is current from the pages alone.

**D2 — tile vs bio title disagreement.** The index tile says Danielle
Bartolomei is "Chief Compliance Officer"; her own bio says "Chief Compliance
AND OPERATIONAL RISK Officer." Two renders of one seat, one publisher, same
page family. (Smaller variant: Allison Beer's tile says "Card Services and
Connected Commerce"; her bio says "Card & Connected Commerce.")

**D3 — a missing field on the most senior row.** Troy Rohrbaugh — the most
senior person on the page — is the ONE tile with no title at all (21 name/title
pairs against 22 tiles). Completeness of a governed surface does not correlate
with seniority of the subject.

**D4 — a stale cross-reference to a moved seat.** Allison Beer's bio describes
Connected Commerce with the near-verbatim sentence Peter Muriungi's bio uses
for his PRIOR seat ("...more than 73 million digitally active customers connect
with relevant brands they love through Chase's travel, dining, shopping and
offers..."). Muriungi's bio says he "led" that team (past tense) and now heads
Digital Assets and Blockchain Solutions. The portfolio moved; the description
was copied forward rather than re-authored — visible only by reading two pages
against each other.

**D5 — turnover visible only by absence.** The "Chief Product Officer for
Digital" seat is held by Chris Stang. The prior Chase Chief Product Officer
(Rohan Amin) appears nowhere on the page — no departure note, no dated change.
The page publishes only current state; history must come from diffing captures,
which is exactly what the sha256 table enables.

**D6 — bio refresh cadence is per-page, not per-site.** Allison Beer's bio
carries a fact stamped "as of December 2024"; Jennifer Roberts's freshest cited
facts are 2020-2021 vintage (J.D. Power 2020, Paycheck Protection Program
2020/2021). Adjacent bios on one governed surface differ by roughly four years
in evidence freshness.

**D7 — an incomplete brand migration dates the pages.** The firm's one-word
brand rendering ("JPMorganChase") appears in the BODY text of some bios and not
at all in others (zero body occurrences in 8 of 22, which use the two-word form
throughout) — an edit-era watermark: bios touched since the rebrand carry the
new form, untouched bios do not. Useful as a coarse last-edited signal on pages
that publish no dates.

**What D1-D7 mean for the gate.** This is live calibration evidence for the
draft gate's section C3 source-grain corollary: a fact from a captured page is
true as-of the capture, and the capture date must ride the fact, because the
source itself demonstrably carries concurrent vintages. It also argues for the
section C proposed rule's first half (as-of assertion for dated-capture facts):
these pages are the extreme case — dated captures of an UNDATED source.

## 6. Disposition

- Corpus registered: `doc-source-registry#chase-leadership-scrape` (External,
  `confirmed: false`, `graph_locator: none` — evidence-only; nothing loads).
- Evidence attached to the drafted gate page
  `config/gate-prompts/business-layer-org-structure.yaml` as a third provenance
  block (the draft is unsigned; attaching evidence to a draft is a draft edit,
  not a rider — L25 governs signed clauses only).
- Any modeling of this corpus (membership edges, the two-layer composition) is
  an ontology decision for the gate session; the taxonomy-first rule applies if
  the roster is ever imported.
