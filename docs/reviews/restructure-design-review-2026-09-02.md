# Design review — the backlog/edition restructure against the current design

**Date:** 2026-09-02 · **Trigger:** `/system-design` review of the proposed restructure (the
2026-09-01 plan *"A minted domain axis, and a port-prompt restructured around disposition"*)
against the design as it stands after gate `ontology-domain-registry-and-edition-grain`
signed the same day.
**Method:** the plan read clause by clause against the signed gate record
(`config/gate-log.md`, last entry), the eight minted items (CFG1 CFG2 PLAN2 DOC1 DOC2 REF1
ONT1 ONT2), the allocator (`.claude/skills/groom-backlog/validate.py`), the store
(`drydocs_core/backlog_store.py`), the guards (`tests/unit/test_backlog.py`,
`tests/unit/test_port_manifest.py`), the manifest, the port-prompt and ADR 0015. Every
finding cites the line it was read at.
**Classification:** Internal-Public (mechanism only; no org values, no edition names).

- **Reviewed at:** commit `620833e7` on `main`, port base `port-base-20260901`; venue MSI.
  *Absent here reads as not-yet-ported, not as broken (docs/style/review-provenance.md).*

---

## 0. Verdict, in one paragraph

The restructure is sound and most of it is already decided or built: Workstream A (the
port-prompt by disposition, the manifest coupling rows, the coupling and totality
detectors) shipped on 2026-09-01, and Workstream B was resolved by a gate rather than the
plan's options paper, which is the right substitution — the gate is the governed form of the
same document. The signed design is **simpler than the plan** in three places (the series is
the module, not a domain; a domain must own a fragment; the edition is a segment and the
numeric bands retire outright) and each simplification removed a mechanism the plan had to
invent. What remains is build work, and the review found **five defects in the build items
that would each surface at the company port, not here** — the allocator has no idea which
venue it is running in (F2), the frozen table is producer-measured and will fail the
company's own tests the day PLAN1 ports (F3), PLAN2 undercounts the id-shape consumers by
half (F1), the acronyms guard forbids homonyms (F6), and the allocator cannot tell a stale
remote ref from a fresh one (F12). None is expensive. All five belong in item bodies before
the items are pulled, and §8 lists the exact edits.

---

## 1. Requirements the restructure must meet

**Functional.**

| # | Requirement | Where it is met |
|---|---|---|
| R1 | A topic axis for backlog ids that is minted and tracked, not inherited from a fixed letter list | PLAN1 (built `c24ce720`): series = module code from `modules.yaml` `series:`; 27 letters frozen in `FROZEN_SERIES` |
| R2 | An edition axis that scales to the real Area Product population without renumbering | Gate §C1–§C3 → CFG2 + PLAN2 (todo): `[<EDITION>-]<MODULE><n>`, keyed to `area_product_id` |
| R3 | No existing id moves; every citation in signed records keeps resolving | Gate preamble ("nothing renumbers"); the segment is optional; PLAN2 (a) round-trip guard |
| R4 | A working allocator at every base | Producer: yes. Company: **no** — both doors (`RESERVED_SERIES`, `PRODUCER_BAND_CEILING`) still shut until PLAN2 ports, and PLAN2 as written leaves a third gap (F2) |
| R5 | Domains registered as data with their authority | CFG1 (todo), seeded from three real rulings |
| R6 | The 2018 join — requirements to code — traversable | ONT1 (todo): mint `code` + `requirements`, planned `:Requirement→:Code` edge |
| R7 | A port that applies by disposition, one source of disposition truth | **Done** 2026-09-01: port-prompt §"APPLY BY DISPOSITION" (`docs/port/port-prompt.md:2200`), manifest rows `MODULE_MAP.md` (:646, MOVES WITH its guard) and `config/source-registry.yaml` (:824), detectors `test_every_declaration_names_the_guard_that_reads_it` (:249) and `test_every_per_entry_rule_is_total` (:354) |

**Non-functional.**

- *Concurrency across two machines and a company repo with a disjoint history.* The claim
  channel is a pushed file; the mint channel is a pushed stub; the allocator unions local,
  remote refs and history. The design meets this for ids; it does not yet meet it for
  **venue** (F2).
- *Determinism.* Every render is regenerable and guarded; the restructure adds two data files
  and no render, so it inherits the property for free.
- *The publish boundary.* `editions.yaml` is Internal with a synthetic sample on the
  `lob-product-team.yaml` pattern (`config/taxonomy/lob-product-team.yaml:22`,
  `classification: Internal`); `domains.yaml` is mechanism and publishes. Correct.

**Constraints that bind the build.**

- ADR 0015 is PROPOSED and its Phase 0 gate (URN shared-vs-owned) blocks all TE *code*. The
  restructure's code (PLAN2, CFG1, CFG2) is producer project-management code, not TE code, and
  is not blocked; the amendment (DOC1) is prose. This line is drawn correctly.
- `.claude/**` is `canonical-producer` (`PORT-MANIFEST.yaml:683`): the allocator crosses
  whole to the company. Every allocator behavior therefore has to be right *for a venue the
  producer never runs in*. That single constraint generates F2, F3 and F9.

---

## 2. The design as it stands

```
                       config/taxonomy/                     docs/restructure/backlog/
   +---------------------------------------------+    +------------------------------------+
   | domains.yaml  (CFG1, todo)                   |    | modules.yaml  series: {18 codes}   |
   |  id | title | vocabulary_fragment (REQUIRED) |    |  (PLAN1, built)                    |
   |  minted_by | registered_at | authority       |    +----------------+-------------------+
   |  status/superseded_by                        |                     |
   +----------------------+----------------------+                     |
                          | partitions                                  | names the series
                          v                                             v
   drydocs_core/ontology/relationship_vocabulary/         .claude/skills/groom-backlog/validate.py
     40-..52-local-<domain>.yaml  (13 today; +code,        --next-id --module <m> [--edition <code>]
     +requirements via ONT1; +acronyms via ONT2)             unions local | remote refs | history
                                                              FROZEN_SERIES, RESERVED_SERIES,
   editions.yaml (CFG2, todo; Internal, synthetic)            PRODUCER_BAND_CEILING -> retire (PLAN2)
     code | title | area_product_id | minted_by |                     |
     registered_at | authority | legacy_band                          v
            |                                          items/<[EDITION-]MODULE n>.yaml  (638 today)
            | joins                                     read by drydocs_core.backlog_store
            v                                           rendered by drydocs.plan_board -> board.html
   :AreaProduct {area_product_id}  (K5 §B; constraints.cypher:79)

   Cross-repo: PORT-MANIFEST.yaml dispositions; domains.yaml + editions.yaml per-entry
   (tom-role-vocabulary / lob-product-team precedent); .claude/** canonical-producer.
   Team Edition (ADR 0015, PROPOSED): base backlog canonical-template (frozen);
   instance backlog instance-owned (DOC1 amends D2/D6); ontology base-common (D4 + rider).
```

Two axes, two registries, and — the gate's §A2 — they never share a column. The backlog's
grouping axis is the **module** (a code-placement fact the item already carried as a required
field); the vocabulary's grouping axis is the **domain** (a file/loader partition). The plan
had tried to make one registry serve both, and the price of that was a nullable fragment, a
`series` column on a domain, and a `domain:` field on every item. All three are gone.

---

## 3. Plan versus signed design — the delta

| Plan clause | Signed / built outcome | Assessment |
|---|---|---|
| D1 — series from the domain registry, ≥3 letters | **Superseded.** Series = module code (PLAN1). Domains carry no `series` (§B1) | Better. A backlog item's topic is where its code lives, and `module:` was already required and validated |
| D1 — `vocabulary_fragment` nullable | **Reversed** (§B3): required | Better. Removes the "domain with no consumer" class the plan needed only because domains were also backlog series |
| D1 — `architecture` seed row `status: contested` | **Resolved** (§B4): split now via G87; ONT1 | Better; the marker is unnecessary once the split is a minted item |
| D2 — the 12 domain series codes | **Dropped** with D1 | — |
| D3 — `domain:` field on items, backfilled from epics | **Dropped.** `module:` is the axis | Better. 638 items untouched instead of 638 edits |
| D4 — `[<EDITION>-]<DOMAIN><n>`; band survives grandfathered | **Amended** (§C1, §C4): `<MODULE>`, and both partition rules retire forward-only | The retirement goes further than the plan and is right — but it opens the venue hole in F2 |
| D5 — `editions.yaml` on the lob-product-team pattern | **Confirmed** (§C3); grain = Area Product with an SME definition (§C2) | As planned |
| D6 — port-prompt by disposition; declaration/guard pairs share a disposition | **Built 2026-09-01** (J69; manifest :646/:824; detectors :249/:354) | Complete. The plan file is stale on this |
| Workstream A rows (skill :92, source-registry row, MODULE_MAP per-entry) | **Built** (RELAY-18 retired the skill's asserted dispositions) | Complete |
| B Stage 0 — options paper `docs/design/backlog-id-grammar.md` | **Not written.** A gate prompt YAML took its place (`config/gate-prompts/…yaml`) | Right substitution: the gate prompt carries the provenance table and the confirmations the paper would have carried, and it is the governed form |
| B Stage 0 — register spec-kit/SDD BEFORE the ruling | **Reordered** (§B4): behind the split, REF1 | Acceptable; the split's semantics (the edge) are still ruled at their own gate after REF1 |
| B Stage 1 — amend ADR 0015 | DOC1: dated section, D2/D6 amended, D4 strengthened | As planned |
| B Stage 1 — acronyms, ontology as candidate domains | Ontology = a **rule** (base-common), acronyms = a **domain with a tier axis** (§B5 riders); acronyms get their **own store** (second rider, via C40) | Right shape; F6 on the guard |
| B Stage 2 — allocator domain mint mode | **Reduced** (CFG1 f): a domain is minted by a gate record plus a row; `--check-domain` only if ONT1 needs it | Right. The name-collision question is answerable by the existing union; a mode is not needed |
| B Stage 2 — `git-readme.md:196–201` retirement | PLAN2 (c) | As planned |
| Not in scope — per-domain wired/configured roll-up | Still out of scope | Correct; `source_bindings.STAGES` and ADR 0015 D1 own it |

Net: of the plan's six design decisions, three were simplified, two confirmed, one built.
Nothing in the plan was rejected on substance; what was rejected was machinery.

---

## 4. Findings

Each finding names the item that should carry it. Severity is about *where it surfaces*:
"port" means the producer suite stays green and the company's goes red.

### F1 — PLAN2 names three id-shape consumers; there are at least seven (severity: build)

PLAN2 (a): *"Three regexes gain one optional group: validate.py :67 and :68, backlog_store.py
`_ID_RE`."* Verified sites that parse the id shape:

| Site | Reads | What `AUTO-LOAD1` does to it today |
|---|---|---|
| `validate.py:67` `_ID_RE` | `^(?P<series>[A-Z]+)(?P<number>\d+)$` | no match — named in PLAN2 |
| `validate.py:68` `_FILE_RE` | `(?P<id>[A-Z]+\d+)\.yaml$` | matches `LOAD1` — **silently drops the segment** |
| `backlog_store.py:84` `_ID_RE` | `^([A-Za-z]+)(\d+)([a-z]?)$` | no match → sorts after every conforming id (`natural_id_key` :87) — named in PLAN2 |
| `test_backlog.py:232` | `"".join(ch for ch in iid if ch.isdigit())` | works by accident |
| `test_backlog.py:395–396` | `isalpha()` join → series | series becomes `AUTOLOAD`; frozen check **passes vacuously** |
| `test_backlog.py:417` | `isalpha()` join → series | `AUTOLOAD` not in codes → module-series check **passes vacuously** |
| `drydocs/port_preflight.py:88` | `^chore\(backlog\):\s*[A-Za-z]+[0-9]+\s+in_progress` | a claim commit for an edition id is no longer recognized as a claim → counted as substantive by the port coverage guard |

The two `isalpha()` sites are the dangerous ones: they do not fail, they stop guarding.
**Recommendation:** PLAN2 (a) lists all seven; the three `test_backlog.py` extractions are
replaced by one helper that parses with the allocator's regex (the test already imports the
allocator for the agreement guards at :267 and :352), so there is one grammar and the test
cannot drift from it.

### F2 — The allocator has no venue identity, and "base unprefixed" is ambiguous once the band retires (severity: port; the most important finding)

Today the producer and the company are told apart by **number**: producer 1–9999, company
10000+, in every series (`PRODUCER_BAND_CEILING`, :136). PLAN2 (c) retires that and (b) says
*"without `--edition` the base."* But `.claude/**` is `canonical-producer`, so the company runs
this exact allocator, and the company is a base too (§B2: it mints its own domains) *and* an
edition (§C3: it mints its own code). A company session that runs
`--next-id --module drydocs-load` and forgets `--edition` mints `LOAD13` — the producer's next
id — and nothing refuses it, because the only thing that used to refuse it was the band. PLAN2
(d) says the company mints nothing until it has its code, which is a rule about intention;
the sequence that keeps collapsing in this repo (C19, K9, O69, six mint collisions) is exactly
the one where intention was the mechanism.

The repo already has the right seam. `config/dev-environment.yaml` is `canonical-company`
(`PORT-MANIFEST.yaml:322`) and carries `capability_assert` (:176) with the note: *"Deliberately
a config flag and NOT an env var … this file is canonical-company in PORT-MANIFEST.yaml, so
the divergence lives in the one file already ruled per-side."* An `edition:` key in that file
— `base` on the producer, the company's code on the company, absent on a machine that has not
declared itself — gives the allocator its venue the same way. **Recommendation:** PLAN2 (b)
becomes: the allocator reads the venue's edition from `dev-environment.yaml`; `--edition`
overrides it only downward (a base may mint for an instance it hosts); a venue with no
declared edition mints nothing and says which key to set. "Declared, not inferred" (ADR 0015
D3) applied to the allocator's own venue. This also makes PLAN2 (d) a mechanism: the company's
ported allocator refuses until the company writes one line in a file it already owns.

### F3 — `FROZEN_SERIES` is producer-measured; the company's own legacy ids fail it (severity: port)

`FROZEN_SERIES["G"] = 136` was measured across *this* repo's local tree, remote refs and history
(:88–:97). `test_frozen_series_take_no_new_ids` (:385) fails any `G` id above 136. The gate
record §C4 says `G10001–G10003` and `DD10001–DD10003` exist company-side and *"stay readable
and stay in the frozen table"* — but the table has no entry that admits them: `G` is frozen at
136, `DD` is not in the table at all (it is in `RESERVED_SERIES`). The day PLAN1 ports, the
company's `test_backlog.py` goes red on three ids it minted under a rule that was in force
when it minted them. Note the same guard's own doc explains why the ceiling is a committed
constant and not a computed max — so "let the company recompute" is not available.

**Recommendation:** one rule, written once in the guard and once in the relay: *a legacy
band id (number > 9999, minted before 2026-09-02) is frozen at the band's own max* —
implement as a second table `FROZEN_BAND: {"G": 10003, "DD": 10003}` that the guard consults
for band-shaped numbers, with the same allocator/test agreement guard the first table has.
Carried by PLAN2 (c) and by DOC2's freeze half; see F9 for why it cannot wait for PLAN2.

### F4 — Two id parsers, two grammars, no agreement guard (severity: latent)

`validate.py:67` accepts uppercase only, no suffix. `backlog_store.py:84` accepts any case and
an optional `[a-z]` suffix. Nothing today asserts they agree — the `FROZEN_SERIES` and
`PRODUCER_BAND_CEILING` constants have agreement guards (:267, :352) precisely because
duplication across the standalone allocator and the core store is a deliberate choice; the
regex is the one duplicated thing without one. PLAN2 edits both regexes and is the moment to
add the guard (a fixed list of ids that must parse identically in both, including one with the
segment) or to rule the suffix: today no item id carries one, and `natural_id_key` is the only
consumer that would notice.

### F5 — `domains.yaml` is ontology metadata filed under the taxonomy layer (severity: note; signed)

CLAUDE.md §1 routes `config/taxonomy/` to layer 1 (classification) and
`drydocs_core/ontology/` to layer 2. `domains.yaml` partitions layer-2 files and will be read
by a layer-2 guard (CFG1 c: "a domain named in any fragment entry must exist in the
registry"), so an ontology file points at a taxonomy-layer file for its own membership.
`editions.yaml`, by contrast, *is* taxonomy: org classification keyed to `area_product_id`.
§B1 signed the path and `config/taxonomy/` already holds non-classification data
(`tom-role-vocabulary.yaml`, `software-registry.yaml`), so this is a note, not a defect. The
cost is one cross-layer pointer; the alternative
(`drydocs_core/ontology/relationship_vocabulary/01-domains.yaml`, beside the fragments it
partitions, under the same manifest family) is available through C40 if the pointer ever
confuses a placement decision. No action recommended now.

### F6 — ONT2's guard forbids the real case: one acronym, two expansions (severity: build)

ONT2 (b): *"a term present in two common tiers is a guard failure, not a precedence question."*
Acronym pages exist because acronyms collide: the same three letters carry a technical meaning
and a company meaning. The guard as written makes that unrepresentable, so the SME would be
forced to pick one meaning per acronym for the whole estate — the opposite of what a tier axis
is for. **Recommendation:** the entry key is `(acronym, tier)`, the uniqueness guard is *one
expansion per (acronym, tier)*, and homonyms across tiers are allowed. That makes the
resolution order among the three common tiers a real rule rather than a formality, and it was
never ruled: the SME listed *"company, SDLC, technical, then the edition specific"*; ONT2 wrote
`technical → sdlc → company`. Both orders are defensible (the estate's own meaning first, or
the vendor's) and the difference decides what a reader sees. Put the order on ONT2's seeding
gate as a question, beside the per-row tier placements the item already sends there.

### F7 — The base-common ontology guard has nothing to exercise it producer-side (severity: build)

CFG1 (e): *"an edition row may not reuse a base id, and a base row is never deprecated by an
edition."* No edition row exists in this repo and none will — the company mints its code at
its own gate and the producer never names it (CFG2 c). A guard with no positive case is
vacuous until the company ports, which is where it first runs unobserved. **Recommendation:**
CFG1 (e) ships with a test-only fixture that injects a synthetic edition row and asserts both
refusals (the `test_the_coupling_detector_catches_an_uncoupled_pair` pattern at
`test_port_manifest.py:264` — every detector in that file has a companion that proves it
fires). CFG2's synthetic sample gives the edition code to use.

### F8 — The aggregate board has no mechanism, and should not get one yet (severity: open question, correctly deferred)

DOC1 (b): *"the aggregate (all-editions) board is something only a base renders."* Instances
are copier-generated repositories; the base cannot read N instance backlogs without a fetch
topology that nothing declares. The graph side has its answer — the `ddestate` composite (ADR
0015 D3) — and a backlog roll-up would most naturally ride the same rail (items loaded as
nodes, rendered from the composite) rather than a multi-repo file read. That is a Team Edition
design question and belongs in ADR 0015's follow-up list, not in DOC1. **Recommendation:** DOC1
(e) records it as an open question in the dated section so the amendment does not read as
though the roll-up exists.

### F9 — Sequencing: the freeze half of RELAY-23 must carry F3, or the company cannot run its own suite (severity: port)

DOC2 is *"freeze half now, prefix half after PLAN2."* The freeze half ports PLAN1, and PLAN1's
guard is what F3 breaks. Today the company has no working allocator at all (the plan's
finding; `RESERVED_SERIES` refuses `DD`, the ceiling refuses `G` at 10003 — both verified
at :303 and :331 on this tree, and since PLAN1 a third door — `G` is FROZEN at :308 — shuts before the band is even reached) and mints by hand; after the freeze half it would also have a
red guard. The `FROZEN_BAND` table is a producer-side change to `test_backlog.py` and
`validate.py`, small enough to ride with the freeze relay rather than wait for PLAN2, and
that is the recommendation. The prefix half then carries F2's venue key.

### F10 — ONT1's split is the first real use of G87 above the vocabulary, and its cost is known (severity: note)

24 `architecture` entries and 20 `docs` entries are candidates to re-home under `code` and
`requirements` (CFG1 b counts). G87 (2026-08-21) moved the epoch-tag ids the same way, as add-new +
deprecate-old pairs with `replaces:`; the cost is one pass over the fragments and one gate
table. `:Requirement` has no label today; the edge is registered `planned`; whether `test` is
a third domain rides with ONT1's proposal. This is sequenced correctly — REF1 first, because
the edge's semantics (direction, grain, verdict-on-edge versus observation) are ruled at the
edge's own gate and the spec-driven-development sources are what that gate reads.

### F11 — Workstream A is complete and the plan file is stale (severity: housekeeping)

Every Workstream A row is built: the disposition-first apply section
(`docs/port/port-prompt.md:2200`), `MODULE_MAP.md` per-entry with *"MOVES WITH
`tests/unit/test_module_boundary.py`, ALWAYS"* (`PORT-MANIFEST.yaml:655`), the
`config/source-registry.yaml` row (:824–:859, which records the 1→7 failure), the coupling
detector (:249) and the totality detector (:354). The plan under
`~/.claude/plans/structured-watching-kernighan.md` still lists all of it as pending and lists
Stage 0/1/2 as the path for Workstream B; both halves are superseded by this record and the
gate. The plan is not a tracked surface, so nothing to commit — but a session that reads it
cold would re-plan finished work.

### F12 — The allocator cannot tell a stale remote ref from a fresh one (severity: reliability)

`_report_allocation` fetches first (`validate.py:341`) and `_git` *"returns "" on any failure,
never raises"* (:162). The two warnings that follow fire when there are **no** remote refs
(:360) or when **none could be read** (:368). A failed fetch on a checkout that has remote
refs is neither: the stale remote-tracking refs read fine, the union is silently a day old, and
the docstring's promise — *"the CALLER reports which sources answered, so a degraded run is
visible"* — does not hold for the case the fetch exists to cover (*"a stale remote-tracking
ref is a ref that cannot see the id the other machine pushed an hour ago, which is the whole
failure"*, :339). **Recommendation:** `_git` returns success alongside output for the fetch
call only, and a failed fetch prints a third warning: *fetch failed; remote refs may be
stale; treat as provisional*. Five lines; belongs to PLAN2 since it is in the allocator
anyway, or to a CORE-series chore if PLAN2 should stay scoped.

---

## 5. Scale and reliability

**Load.** 638 items today, 18 module series, two bases, ~20 editions when the company
generates them. Per-edition volume is small (an instance backlog is "thin" by DOC1's own
word), so the board render and the allocator union stay linear in a few thousand files. Not a
concern at any horizon the ADR names.

**The collision surface after the restructure.** Before: two rules partitioned the number
line and disagreed (the `DD10`-vs-`DD10001` ambiguity). After: the segment partitions the
*name*, and a collision requires two venues to mint the same `<EDITION>-<MODULE><n>` — which
the union over remote refs catches for the two producer machines, and which the venue key
(F2) prevents between producer and company. The residual is the one CLAUDE.md already
names: a session that dies before its first push is invisible, and no convention changes that.

**Failure modes and what happens.**

| Failure | Behavior today | After the recommended edits |
|---|---|---|
| Fetch fails, refs present | silent stale union (F12) | warned, number marked provisional |
| No `--edition` on a company venue | mints a producer-shaped id | refused; names the key to set (F2) |
| Company legacy band id under the frozen guard | red on port (F3) | admitted by `FROZEN_BAND` |
| Undeclared edition segment | (not yet parseable) | refused as a typo, per PLAN2 (b) |
| Two editions mint the same code | (not yet possible) | CFG2 (e) uniqueness guard; codes are minted by a gate and pushed, I6 |
| Edition overrides a base ontology row | guard vacuous (F7) | fixture-proven refusal |

**Monitoring.** CI is the tripwire and it is already a ritual step (Idea-111); the restructure
adds guards to the suite and no new surface that CI does not run. The one thing CI cannot see
is the company's suite — which is why F3 and F9 are port findings and why the relay is the
place to carry them.

---

## 6. Trade-offs made, stated

| Decision | Chosen | Given up | Why it is right |
|---|---|---|---|
| Series axis | module code | a domain-derived series (plan D1/D2) | `module:` is already required, validated and enforced by `test_module_boundary`; a domain is a vocabulary partition and most backlog items touch no vocabulary |
| Fragment | required | fragment-less domains as pure backlog topics | after PLAN1 there is no consumer for a domain without entries; a required field is a smaller registry and a stronger guard |
| Edition | a declared segment keyed to `area_product_id` | numeric bands | bands encode tenancy in digits nobody can read and need an ordering the Area Product population does not have; the segment names the same tenant the URN names |
| Partition rules | both retired forward-only | the grandfathered band (plan D4) | two live rules that disagree is the defect; one retired rule with a pointer is the fix. Cost: F2, F3 — both one-line mechanisms |
| Architecture/code | split now, G87 shape | wait for the ADR to rule | the split is the product thesis (requirements ↔ code ↔ tests, 2018); the G87 mechanism is proven; the edge's semantics still get their own gate |
| Acronyms | own store, four tiers | keep the software-registry block as home (the 2026-07-21 ruling) | a term is not a product; MFTS is the case that proves it (a white-labeled Axway product with its own term). C40 exists for exactly this re-look |
| Instance backlog | thin, instance-owned | cut from Team Edition (ADR 0015 D2 as drafted) | the completeness ledger generates work (D1); generated work needs a place to land that `copier update` will not overwrite |
| Options paper | a gate prompt | `docs/design/backlog-id-grammar.md` (plan Stage 0) | the gate prompt is the governed form of the same content; a design doc would have been a second copy |

---

## 7. What to revisit as the system grows

1. **When the company has minted its edition code** — whether "base unprefixed" should stay
   a producer privilege at all. Once every venue has a declared edition in
   `dev-environment.yaml`, an *unprefixed* id is only a convenience for the producer's own
   files, and a rule that every id carries its segment is simpler than a rule with an
   exception. Not now: it would rename 638 files.
2. **When a second Area Product instance exists** — the aggregate roll-up (F8), and with it
   whether `depends_on` instance→base is enough or instances need to depend on each other
   (two Area Products sharing an application is the SME's own definition of the grain, so
   they will).
3. **When ONT1 lands** — whether `test` is a third domain, and whether the converge verdict
   is an edge property or an observation. ADR 0015 D5 (`:Uncertain` by construction) is the
   pattern the verdict should follow if it is an observation.
4. **When the acronyms fragment passes ~100 rows** — whether the four tiers are enough or
   `technical` needs a vendor sub-axis (the software-registry row already carries the
   vendor; a link by name may do).
5. **If a third base ever appears** (a second company, the standalone-template goal) —
   `minted_by` and `authority` already carry it; the venue key in F2 carries it; nothing else
   in the design assumes two.

---

## 8. Recommended edits to the item bodies

Concrete, in pull order. None reopens a signed clause.

| Item | Clause | Edit |
|---|---|---|
| PLAN2 | (a) | list all seven id-shape sites (F1); replace the three `isalpha()` extractions in `test_backlog.py` with one parse helper that uses the allocator's regex |
| PLAN2 | (b) | the allocator reads the venue's edition from `config/dev-environment.yaml` `edition:`; `--edition` overrides downward only; no declared edition → refuse and name the key (F2) |
| PLAN2 | (c) | add `FROZEN_BAND` for band-shaped legacy ids with an agreement guard (F3); add the fetch-failed warning (F12) |
| PLAN2 | (e) | add the regex agreement guard between `validate.py` and `backlog_store.py` (F4) |
| DOC2 | freeze half | carry `FROZEN_BAND` with PLAN1's port, not after PLAN2 (F9); tell the company its allocator is refused until `dev-environment.yaml` declares its edition |
| CFG1 | (e) | ship the base-common guard with a synthetic-edition fixture that proves both refusals (F7) |
| ONT2 | (b), (f) | key = `(acronym, tier)`; homonyms across tiers allowed; the common-tier resolution order goes to the seeding gate as a question (F6) |
| DOC1 | (e) | record the aggregate roll-up as an open question in the dated section (F8) |

Everything else in the eight items reads as buildable as written.
