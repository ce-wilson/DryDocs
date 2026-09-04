# Ideas → Backlog: review of the proposed fix, and a redesigned intake

- **Reviewed at:** commit `93f4d832` on `main`, port base `port-base-20260902`; venue NewThinkpad (laptop).
  *Absent here reads as not-yet-ported, not as broken (`docs/style/review-provenance.md`).*

## Context

The signed gate `ontology-domain-registry-and-edition-grain` (2026-09-02, 14/14,
`config/gate-log.md:4345-4435`) ruled the item-id grammar `[<EDITION>-]<MODULE><n>` and
retired both partition rules forward-only. Three `todo` items stand between that ruling and
a finished grammar: **CFG1** (`config/taxonomy/domains.yaml`), **CFG2**
(`config/taxonomy/editions.yaml`), **PLAN2** (the segment in the id-shape sites, the venue
key, the band-check replacement).

The proposal under review: claim CFG1 now, run CFG1 → CFG2 → PLAN2 ahead of LIN2, and land
a ruling for the `Idea` series inside PLAN2 as `<EDITION>-Idea-<n>`.

Separately, and the reason this is a design pass rather than a review: **new ideas are hard
to map.** The inbox is one 7,176-line markdown file holding 254 entries; there is no
idea-vs-idea dedupe anywhere in the tree; no backlog item carries a structured pointer to
the idea it came from; and the idea↔item join is unvalidated in both directions. The
grammar work above fixes *what an id looks like*. It does not touch *how an idea gets
found, typed, or traced* — which is the part that is actually failing.

**Intended outcome:** the grammar chain lands with the Idea ruling made in the right
venue and with a carve-out that does not strand the company; and the inbox becomes a
sharded, dedupe-able, traceable surface on the pattern ADR 0013 already proved for items.

---

# Pass 1 — review of the proposed plan

**Verdict: the sequencing is right and CFG1 is genuinely unblocked. Ship it.** CFG1 has
`depends_on: []`, is on the Ready strip, and both CFG1 and CFG2 are greenfield file
creations (`config/taxonomy/` holds 15 files today, neither `domains.yaml` nor
`editions.yaml`). Running the chain ahead of LIN2 puts a finished grammar into the next
roll, which is the right call — LIN2 needs `neo4jtest` up and is otherwise unaffected.

The recommendation to take `<EDITION>-Idea-<n>` over the band-numbered exception is also
right, for the reason given: one grammar with two shapes is a standing tax. But it needs
four corrections and a carve-out before it is buildable.

## G1 (blocking) — the carve-out is not optional: without it the company can capture nothing

PLAN2's venue rule (`PLAN2.yaml:48-60`) is *"a venue whose file declares no `edition:`
mints nothing and the refusal names the key to set."* Applied to `Idea`, that closes the
**last open channel the company has**.

Verified: three refusals already shut every company item-mint route — `DD` is refused as
**reserved** (`validate.py:88`, `:318-322`), all 27 legacy letters as **frozen**
(`:102-130`, `:323-329`), and anything above 9999 by the **ceiling** (`:152`, `:346-350`).
The Idea path is the only one with no check at all: `_report_allocation` short-circuits at
`:360-364` and mints `f"Idea-{highest+1}"` **without ever calling `next_id()`**. That is
why `Idea-10012` exists.

So the sequence matters more than the grammar. If `<EDITION>-Idea-<n>` ships with PLAN2's
venue rule applied uniformly, then between PLAN2 porting and the company's own edition gate
the company can mint **no item and no idea** — it has no channel at all. That window is not
short: CFG2 (c) explicitly bars the producer from naming the company's code, so the company
must run its own gate first.

**The carve-out, stated as a rule:** *a venue with no declared `edition:` may still mint an
`Idea`, and the id it gets is band-shaped (`Idea-<n>`, n > 9999) until the venue declares
its code.* The inbox is a capture surface, not a commitment surface — refusing a capture
loses the thought, while refusing an item mint only delays work. Concretely, PLAN2 (b)
gains: the Idea path keeps a `legacy_band` mint for an undeclared venue, and the refusal
that names `CFG2` fires only for **item** ids.

## G2 (blocking) — a new grammar ruling does not belong in a build item's acceptance

The gate never ruled on the Idea series. I read the full signed record (`gate-log.md`
`:4345-4435`) and the full prompt (`config/gate-prompts/ontology-domain-registry-and-edition-grain.yaml`,
191 lines): the words *Idea*, *IDEAS.md*, *inbox* and *idea inbox* appear in **neither**.
The gate is scoped to backlog item ids. `PLAN2.yaml:62-70` is the first place in the tree
where the gap is even named — and it names it as an open question, correctly.

So "the Idea ruling lands in PLAN2" would make a build item the venue for a grammar
decision the gate did not take. This repo already has the failure mode on file: a confirmed
clause in an unsigned gate never reaches `gate-log.md`, and the ruling then reads as
landed-or-not depending on which document you opened. **Recommendation:** the Idea grammar
goes to the SME as a rider under C40 (or its own short gate prompt) and the ruling lands in
`config/gate-log.md`; PLAN2 (b) then *implements* a signed clause instead of inventing one.
This costs one gate round-trip and removes a whole class of later ambiguity.

## G3 — "the band retires forward-only for Idea" retires a rule the allocator never enforced

§C4 retires the 10000 band. For **items** that is a real retirement — `PRODUCER_BAND_CEILING`
refuses at `validate.py:346-350`. For **Idea** there has never been a code-level door: the
short-circuit at `:360-364` bypasses `next_id()` entirely, and the only band enforcement is
`tests/unit/test_plan_ideas.py:153-171`, a guard over the producer's own file.

Consequence for the plan's wording: **"`Idea-10017` becomes the last band idea" is a claim
about timing, not a mechanism.** Nothing stops the next company session minting
`Idea-10018` the same way, and the producer cannot see it — company ideas never cross
(`port-prompt.md:1004-1006`). Making it true requires *adding* a check to the Idea path,
not retiring one. Pair it with the G1 carve-out: the check is "an undeclared venue mints
band-shaped; a declared venue mints prefixed", which is one branch, not two rules.

## G4 — PLAN2's justification rests on DOC1, and DOC1 is not in the chain

`PLAN2.yaml:66-67` argues for `<EDITION>-Idea-<n>` because *"an instance's inbox is its
own, DOC1 says the inbox is instance-owned."* DOC1 is `status: todo` and is **not** in the
proposed CFG1 → CFG2 → PLAN2 sequence.

This matters more than an ordering nit, because DOC1 is doing heavy lifting: it *amends
ADR 0015 D2/D6*, which as written **cuts** `backlog_store`, `plan_*` and the `groom-backlog`
skill from Team Edition entirely (`0015:119`, `:213` — *"the skill cut follows the module
cut: `groom-backlog` → backlog machinery … producer-only"*). Un-amended, ADR 0015 says a TE
instance ships no inbox and no groomer; DOC1 (a) is what makes the instance-owned inbox
exist at all. **Recommendation:** DOC1 lands before or with PLAN2 (it is a `fable`-model
docs item, cheap), or PLAN2 (b) cites the gate ruling from G2 instead of an unlanded
amendment.

## G5 — the "seven id-shape sites" is items-only; choosing `<EDITION>-Idea-<n>` roughly doubles it

PLAN2 (a) lists seven sites (from review F1). Choosing the Idea segment adds **seven more**
that no item names:

| Idea-shape site | What it does |
|---|---|
| `validate.py:75` `_IDEA_RE` | anchored inbox-header parse |
| `validate.py:81` `_IDEA_IN_DIFF_RE` | the `git log -p` twin |
| `validate.py:363` | the literal `f"Idea-{highest + 1}"` mint |
| `validate.py:393`, `:416` | the `'-' if label == 'Idea' else ''` render |
| `test_plan_ideas.py:92-93` `_HEADER` | the full entry-header grammar |
| `test_plan_ideas.py:109` | the id-extraction twin |
| `test_plan_ideas.py:163` | `int(i.removeprefix("Idea-").rstrip(...))` — the band guard's parse |

**And an eighth *item* site nobody has named, already broken independent of the edition
segment:** `.claude/skills/lane-handoff-workspace/grade.py:42` uses
`r"\*\*([A-Z]{1,4}\d{1,4}[a-z]?)\*\*"` — `{1,4}` cannot match today's five- and six-letter
module codes `DOCGEN`, `AGENT`, `GRAPH`. That is a live PLAN1 regression sitting in the
lane-handoff grader. It should be fixed now, not bundled into PLAN2.

## G6 — three factual corrections to the plan's premises

1. **RELAY-26 does not exist.** RELAY-25 (`port-prompt.md:2065`) is the highest in the file,
   and `DOC2.yaml:70-71` records that **DOC2 takes the next free relay number when it
   rolls**. Writing "RELAY-26 tells the company…" claims a number DOC2 already expects.
   This is precisely the collision class that forced the `R<n>` → `RELAY-<n>` rename on
   2026-08-09, when a company session anchored `R3(b)` on backlog item `R3` and answered a
   question nobody asked. Take the next number at roll time, from the file.
2. **`Idea-10015`, `Idea-10016`, `Idea-10017` are not in this tree** — not in the working
   tree and not in ~400 revisions of `IDEAS.md`. The producer inbox tops out at `Idea-252`,
   and it contains **zero** five-digit `Idea-` headers by construction
   (`test_plan_ideas.py:153` fails if one appears). These are company-minted ids known here
   only from the screenshot. That does not make the three fixes wrong — it makes their
   *traceability* one-directional, which is worth a line in each commit (see S1 below).
3. **"the allocator refuses both `DD` and `G` past the ceiling"** conflates three
   independent refusals: `DD` is refused as **reserved** and `G` as **frozen**, both
   *unconditionally*, with no reference to `PRODUCER_BAND_CEILING`. The conclusion holds —
   every sanctioned company mint route is shut — but the fix differs per door, so the
   precision matters when PLAN2 rewrites the refusal messages.

## G7 — line-number drift in PLAN2's acceptance, from PLAN3 landing after it was written

`validate.py:67/:68` → `:68/:69`; `PRODUCER_BAND_CEILING :136` → `:152`; the two fetch
warnings `:360/:368` → `:375/:383`; `test_backlog.py` isalpha sites `:395-396`/`:417` →
`:373-374`/`:465`; `test_frozen_series_take_no_new_ids :385` → `:420`; the agreement guard
`:352` → `:386`; `drydocs/port_preflight.py:88` → `drydocs/port/port_preflight.py:88` (the
root path is now a 12-line re-export shim from ADR 0018 D4). Cause: PLAN3 inserted
`FROZEN_BAND` and `_frozen_strays` after PLAN2's acceptance text was written. Refresh the
citations when PLAN2 is claimed, or the build item sends its implementer to the wrong lines.

## G8 (note) — the band rule now disagrees across three documents

`CLAUDE.md:90` still states *"The allocator BANDS (producer 1–9999, company 10000+) … are
unchanged"*; `gate-log.md` §C4 rules both partition rules **retired forward-only**; the code
still enforces the ceiling. **Retired in ruling, live in code, live in the operating
guide.** PLAN2 (c) closes the code half; `CLAUDE.md`'s Mint-rule paragraph and
`git-readme.md:195-201` need the same sweep in the same commit, or the next session reads
the operating guide and mints by the retired rule.

---

# Pass 2 — improving the flow

## The diagnosis, in one line

The grammar work fixes what an id **looks like**. What is failing is everything before the
id exists: **there is no mechanism for "does this already exist?", no field that records
where an item came from, and no guard on either.** Naming is not the bottleneck; the
un-searchable inbox is.

Measured on this tree:

| Symptom | Evidence |
|---|---|
| The inbox is one file | `docs/restructure/IDEAS.md`, 7,176 lines, 254 entries (136 inbox + 118 trail) |
| No idea-vs-idea dedupe exists | The only similarity step is `SKILL.md:39` — `grep -rl <keyword> docs/restructure/backlog/items/` — which greps **items**, never the inbox, and only on the merge branch |
| No provenance field | `grep "^  *source:"` over all 645 items returns **zero**. 248 items carry free prose (`"Groomed 2026-08-07 from Idea-43"`) in `notes:` |
| The join is unguarded both ways | `groomed -> PLAN9` (nonexistent) and `from Idea-999` pass all 26 guards in `test_backlog.py` |
| Tag vocabulary drifted | 6 documented (`IDEAS.md:44`), 13 in use; `test_plan_ideas.py:93` accepts any `[a-z]+` |
| The inbox is a proven merge-conflict site | `PORT-MANIFEST.yaml:283-285` — `union-append`, *"proven conflict site, 3x on 2026-07-09"* |
| The Ready strip is not a queue | 114 of 135 `todo` items are "ready to pull" |

## A. Intake — the routing rule, stated once

Your three intake questions have a clean answer once one confusion is removed: **"technical
debt" and "project configuration" are not the same axis.** `module:` is a closed 20-set;
`type:` is a closed 4-set `{requirement, task, chore, bug}` with **no `debt` value**, and
ADR 0013 Clause 4 (`:141-143`) says deliberately that *"`type` cannot carry this
distinction."* So debt is orthogonal to module, and today it rides `type: chore` plus
whichever module owns the code (the whole 2026-09-02 tech-debt review entered as
`Idea-243`…`Idea-249`, every one tagged `[chore]` with an explicit module line).

The rule, in the order a groomer should apply it:

1. **Is it new?** Run the dedupe (B2). A hit that covers it becomes `merged_into`. A hit
   that partly covers it appends to that idea's body with a dated `KEPT-UPDATED` line (the
   convention already documented at `IDEAS.md:41`). Only a miss mints a new id.
2. **Which module?** Code change to the owning component, looked up in `MODULE_MAP.md`'s
   rendered table (rendered from `drydocs_core/component_map.py`, ADR 0018 D1). Non-code to
   one of the seven work-area modules `config`, `docs`, `ontology`, `taxonomy`, `reference`,
   `graph-infra`, `drydocs-web` (`component_map.py:269-279` carries the one-line definition
   of each). **Project configuration is `module: config`, series `CFG`.**
3. **Is it debt?** Orthogonal. It does not change the answer to (2); it sets `type: chore`
   at promotion and a `debt` tag at capture. Record it so the tech-debt sweep can find its
   own past findings — today it cannot.
4. **Ambiguous module or phase?** That, and only that, is what "park it" is for
   (`SKILL.md:61-70`). Never groom an ontology decision into a done deal.

## B. The sharded inbox

### B1 — Shape

`docs/restructure/ideas/<id>.yaml`, one file per idea, schema `drydocs.ideas.v1`, filename
equal to `id` — the ADR 0013 Clause 1 shape, verbatim, one layer up. Read it through a new
`drydocs_core/idea_store.py` that mirrors `backlog_store.py`'s surface (`item_paths`,
`load_items`, `load_backlog_document`, `derive_summary`, `dump_document`, `natural_id_key`
— `backlog_store.py:87-244`). Core placement is correct under ADR 0002-A §2: pure
parse/typed-model, imports nothing from a component.

**Required at CAPTURE (five fields — an inbox expensive to add to stops being an inbox):**
`id`, `captured` (date), `title` (one line, the dedupe key), `body`, `tags` (guarded
vocabulary).
**Required at GROOM only (when `status` leaves `open`):** `module`, `priority`, and exactly
one of `promoted_to` / `merged_into` / `closed_reason`.
**Optional:** `parked_until` (the named trigger), `related` (ids), `debt`.

`status` keeps today's vocabulary and gains the one it never had: `open`, `parked`,
`groomed`, `merged`, `closed`, **`dropped`** — `IDEAS.md:16-18` offers "drop" as an outcome
and the status list at `:45` has never carried it, so drops are recorded today as `closed`
or not at all.

### B2 — Dedupe, as a mechanism rather than a habit

Add `validate.py --find-similar "<text>"`: score every **non-closed** idea against the note,
print the top 5 with id, status and score. Deterministic, no new dependencies, runs inside
the fork the groomer already uses.

**Do not write a new scorer — the repo already has a tuned one.**
`drydocs/port/port_rename_detect.py` carries `normalized_text` (`:119`),
`text_similarity`/`id_set` (`:214`), `document_frequency` (`:333`), `discriminating`
(`:351`, the idf discount) and `discounted_pair` (`:391`, the stub veto). It cannot be
imported as-is: `component_map.py` puts it in the `port` group and `plan_ideas` in `docgen`,
and `test_module_boundary.py:163-179` fails a component→component import with *"route shared
code through core"*. So this needs a prior extraction to `drydocs_core/text_similarity.py`
with `port_rename_detect` re-pointed — the same core-extraction `Idea-243` already proposes
for `_str_or_none` ×5.

The two borrowed refinements are not optional here. **The idf discount matters more in the
inbox than in the port:** eight-plus entries open with "Source: the 2026-09-02 tech-debt
review", so without `discriminating()` every review-derived idea reads ~0.6-similar to every
other, the tool cries wolf, and it stops being run. **The stub veto matters too** — a
one-line capture is exactly the ten-token case that produced a false all-clear in the port.

It **ranks, never blocks** — a false negative costs a duplicate idea, which `merged_into`
makes recoverable, whereas a blocking check would lose captures. The groom skill's per-note
procedure (`SKILL.md:36-44`) gains one required step before "promote": run it, and record in
the idea's `related:` what was looked at. That converts the single unstructured `grep -rl`
into a step with an output.

### B3 — Traceability, both directions, guarded

The precedent is already in the tree and already argued: `backlog/README.md:9` —
*"`render_gates.py` derives the board's unblocks edges from that field ONLY — a prose
citation of a gate in `acceptance`/`notes` is never an edge."* Same problem, same fix.

- Item gains **`source:`** — optional list of idea ids, guarded when present to resolve to
  real idea files (copy `test_declared_gates_are_lists_of_known_prompt_slugs`,
  `test_backlog.py:610`).
- Idea carries **`promoted_to:` / `merged_into:`**, guarded to resolve to real item files.
- **The join guard:** an idea with `status: groomed` has a non-empty `promoted_to`, and
  every item it names lists it back in `source:` — both directions, on the pattern of the
  epic-item guard at `test_backlog.py:110-119`.

The 248 existing prose mentions are **left alone** and backfilled opportunistically: the
regex `from Idea-(\d+)` over `notes:` is reliable enough to seed `source:` in bulk, but a
bulk edit of 215 item files during a live port is a rename trap. Backfill an item's
`source:` when it is next touched; the guard is *when present*, so nothing goes red.

### B4 — Migration (ADR 0013 Clause 5, verbatim pattern)

Splitter script, then per-idea files, then a **four-check proof**, then `IDEAS.md` becomes a
tombstone with a pointer, exactly as `backlog.yaml` did (`test_monolith_is_a_tombstone`,
`test_backlog.py:709`).

**Measured, not assumed — the parse risk is lower than I first wrote.** A strict header
regex over the file from `## Inbox` (`:92`) onward matches **254 of 254 entries, zero
failures**. Parsing from line 0 yields 255 — the extra is the format *example* in the header
prose at `:31`, which is why the parser starts at `## Inbox` and the example moves to a
`README.md`.

Two real defects surfaced by the same measurement, both to fix in the monolith *before* the
split (the `ffc29b6f` precedent ADR 0013 cites at `:30-31`):

- **`done` is a status in use and is not in the documented vocabulary** — `groomed` 160,
  `open` 30, `parked` 26, `merged` 21, `closed` 15, **`done` 2**. `IDEAS.md:45` never lists
  it. The two map to `closed`, printed for review; the vocabulary stays six.
- **`Idea-241` (`:140`) carries two `prio? **High** —` segments on one header.** Greedy
  status matching swallows its body. The status span must be non-greedy; the defect is in
  the entry, not the parser.

Since there is no monolith *parse* to deep-equal against, the round-trip **is** the equality
proof. Four checks, all before the tombstone:

1. **Id-set equality** — regex over the monolith == filename set == `id:` field set.
2. **Header round-trip, byte-for-byte** — `format_header(parsed) == original_line`. This is
   the sharp one: a dropped `?`, a normalized tag, a lossy status, a reordered field all
   fail here and nowhere else.
3. **Body byte-equality** against the monolith slice. `backlog_store.dump_yaml`'s
   literal-block presenter (`:223-229`) handles the 15 nested-bullet bodies.
4. **Line accounting** — every non-blank line lands in exactly one destination; print the
   residual. A line in none is a silent loss, a line in two a duplication. This is what
   catches a bad split, and it is the coverage-ledger discipline (`None` for not-probed,
   never `0`) rather than J16's 398 paths taking `default:` in silence.

The 164 `FILED`/`GROOM` run-log blocks in the audit trail are **not** entries; they move to
a `GROOM-LOG.md` as verbatim markdown. ADR 0013 Clause 2 rejected a YAML `_header` as
"lossless but invisible"; these already render, so verbatim markdown passes that acceptance
for free and reduces check 4 to a slice comparison.

### B4a — Two things already in the tree that this design must respect

**The directory name is already ruled — do not re-litigate it.** `CLAUDE.md:72` names the
backlog pen surface as `items/`, `IDEAS.md`/`ideas/`, `epics/`, and
`.claude/skills/lane-handoff/scripts/handoff.py:71` already registers a pen row for
`docs/restructure/ideas/` — *"the sharded inbox, once R6 lands"*.

**`R6` is a phantom citation, and it is this design's own exhibit.** `handoff.py:70`, `:371`
and `tests/unit/test_lane_handoff.py:178` all say the inbox is *"one file until R6 shards
it."* `docs/restructure/backlog/items/R6.yaml` is **"Tier-2 bounded graph-of-thoughts
loop", `status: done`, closed 2026-08-01** — unrelated work. A prose id pointing at the
wrong item, asserted by a test, surviving in three places, is exactly the unguarded-join
defect in miniature. It belongs in the ADR's rationale the way ADR 0013 used the 2026-08-04
three-way rebase (`0013:25-31`), and the citation re-points to the real item id.

### B4b — The burned-id floor (the one thing the shard genuinely breaks)

After the split, `git log --diff-filter=A -- ideas/` sees 254 adds in one commit and nothing
before it. **Every burned Idea id lives only in the monolith's history** — the `Idea-135`
renumber recorded at `PORT-MANIFEST.yaml:667-669` is exactly one. Keeping
`git log --all -p -- IDEAS.md` forever is correct but re-reads a 7,176-line file's whole
revision history on every allocation and finds nothing new after the shard.

**Take a committed floor:** `IDEA_MONOLITH_FLOOR = <the three-term union max on the day of
the shard>`, worded like `FROZEN_SERIES` (`validate.py:90-101`) — **never** "the current
max", because a computed floor rises with every new id and silently re-legalizes what it was
meant to freeze. Keep the `-p` scan behind `--deep` for a one-off audit, and print the floor
beside `local=/remote=/history=` in the allocation report.

### B5 — What sharding buys at the port boundary

This is the strongest argument, and it is not tidiness. `docs/restructure/IDEAS.md` is
`union-append` today and the manifest note calls it a *"proven conflict site, 3x on
2026-07-09."* A sharded inbox takes the **items** row verbatim
(`PORT-MANIFEST.yaml:197-213`): `per-entry`, *"THE ENTRY IS THE FILE (ADR 0013 Clause 6):
one id, one path, so disjoint ids are ordinary git adds/modifications and need no
hand-merge."* The conflict site disappears by construction.

`docs/plan/ideas.html` stays `derived` (`:462-472`) — each side regenerates from its own
reconciled tree, for the reason the row already gives: *"an inbox is the LEAST portable
artifact in the repo."*

## C. Scenario 1 — producer to company

**A correction worth carrying into the design: ideas already cross.** `IDEAS.md` is
`union-append`, so both sides' entries merge. The numeric band exists *because* of that —
`PORT-MANIFEST.yaml:666-669` records that `Idea-59` meant the FID directory producer-side
and `snow_tom_responsibilities` company-side, and the producer's was renumbered to
`Idea-135`. (`port-prompt.md:1004-1006`'s *"the idea inbox, which your repo never reads"*
explains why the **relay** channel exists; it is not the file's disposition. The manifest is
the authority and says union-append.)

The flow, after sharding plus the segment:

```
capture ---> ideas/<seg->Idea-n>.yaml          # per-side; disjoint by prefix
               |
               +-- dedupe (--find-similar) ---> merged_into an existing idea
               |
               +-- groom ---> items/<seg->MODULEn>.yaml   with source: [<idea id>]
                                |
                     port (per-entry, entry-is-the-file; consumer status stands)
                                |
                                v
            company tree: both sides' ideas and items coexist, no hand-merge
```

**The one rule that keeps the two channels honest:** an idea is a *capture*; a RELAY is a
*directed instruction to the other side*. They are not interchangeable. A producer idea the
company must act on becomes a RELAY **at roll time**, taking the next free number from
`port-prompt.md` and citing the idea id as its basis — never the reverse, and never a relay
number reserved in advance (G6.1).

**And one rule the items row does not need, which is where the ideas port genuinely
differs.** The same `Idea-N` on both sides is usually **two different ideas**, not one work
item with two completions: backlog ids name the same planned work by construction, inbox ids
are minted by whoever had the thought. The manifest already records the case at `:666-669`.
So the resolution is the `Idea-135` / `G75`-`G76` precedent — **renumber the uncited side,
never a side a signed record cites** — and sharding converts what is today a silent
union-append duplicate into a *visible add/add conflict on one path*. That is a benefit the
backlog row cannot claim. For a genuinely shared idea, `status` and `promoted_to` are
per-repo, on ADR 0013 Clause 4's F4 logic: **a port carries the capture, never the
disposition.**

## D. Scenario 2 — company to team (staged, per your answer)

**Now:** "team" is an ownership axis inside the company repo. Nothing new is needed — an
idea and an item both already carry `module`, and team ownership rides the existing
LOB-Product-Team taxonomy. Do **not** invent a `team:` field yet; it would be a second
registry sharing a column, which the design review's §A2 rule forbids (registries JOIN,
never share).

**Later (TE instances):** the shape is already decided, and it is `DOC1`'s job rather than
this design's. DOC1 (a) amends ADR 0015 D2/D6 so an instance ships a thin
**instance-owned** backlog, inbox and board under the copier `instance-owned` file class,
while the base backlog stays `canonical-template` (frozen), and `groom-backlog` ships with a
mandatory `--scope`. Un-amended, ADR 0015 cuts `backlog_store`, `plan_*` **and the
`groom-backlog` skill** from the template entirely (`0015:119`, `:213`) — so DOC1 is
load-bearing for this scenario, and a sharded inbox makes it *easier*: `instance-owned` is a
path-glob class, and `ideas/` is a directory rather than a file both sides must append to.

Two constraints DOC1 already states and this design must not violate: `depends_on` may point
**instance to base, never base to instance**, and an instance never commits an aggregate
render. The aggregate roll-up stays DOC1 (e)'s open question — review F8 recommends it rides
the `ddestate` composite (ADR 0015 D3) rather than a multi-repo file read, and nothing here
should presuppose otherwise.

---

# Recommended sequence

Grammar chain first — it is claimed, ready, and the inbox work depends on the Idea ruling.

| # | Work | Notes |
|---|---|---|
| 0 | **Idea-grammar rider to the SME** (G2) | The gate never ruled it. Land the ruling in `config/gate-log.md`, including the G1 carve-out. Blocks PLAN2 (b) only. |
| 1 | **CFG1** then **CFG2** | As proposed. Both greenfield; CFG1 is on the Ready strip. |
| 2 | **DOC1** (G4) | Cheap (`fable`, docs). Must precede or accompany PLAN2, which cites it. |
| 3 | **PLAN2** | With refreshed line numbers (G7), all **15** id-shape sites (G5), the carve-out (G1), and the `CLAUDE.md` / `git-readme.md` sweep (G8). |
| 4 | *(independent, now)* `lane-handoff-workspace/grade.py:42` | `[A-Z]{1,4}` cannot match `DOCGEN`/`AGENT`/`GRAPH` — a live PLAN1 regression, unrelated to the segment. |
| 5a | **ADR 0019 — shard the idea inbox** (0018 is the highest), module `docs`/`DOC` | Six clauses mirroring ADR 0013. Deciders: user. The R6 phantom citation (B4a) is its rationale exhibit. |
| 5b | **Extract `drydocs_core/text_similarity.py`**, module `drydocs-core`/`CORE` | Re-point `port_rename_detect` and its tests. Independent; can precede everything. |
| 5c | **The shard, ONE commit**, module `drydocs-plan`/`PLAN` | `idea_store.py` + splitter + four-check proof + tombstone + render + guards + every re-point + the `PORT-MANIFEST` rows. Big on purpose — a half-re-pointed tree is two sources of truth, the defect being fixed. |
| 5d | **The join**, module `drydocs-plan`/`PLAN` | `source:`/`promoted_to:` + the agreement guard + the derivation pass. Separable: the tree works without it, and the human review time is here. |
| 5e | **`--find-similar`**, module `drydocs-plan`/`PLAN` | Plus the `SKILL.md` step and `test_no_two_open_ideas_share_a_normalized_title`. |

**Precondition on 5c, and it is hard (ADR 0013 Clause 6, `:206-212`):** the split does not
land while a range containing `IDEAS.md` is being applied. `port-base-20260902` is mid-apply
**right now**, and `IDEAS.md` is `union-append` — an in-flight range is precisely when the
monolith is being merged. The shard is the *first step of the next range*, never spliced
into one in progress; whatever union the in-flight port produces is the splitter's input.

Step 5c is a **net deletion** in the allocator: `_IDEA_RE` (`validate.py:75`),
`_IDEA_IN_DIFF_RE` (`:81`), `idea_ids()` (`:264-289`) and the short-circuit (`:360-364`) go,
replaced by parameterizing `local_ids`/`remote_ids`/`historical_ids` (`:209-257`), which
already do the right thing for per-file ids. Seven of the fifteen id-shape sites in G5 stop
existing. **Constraint on that refactor:** `test_backlog.py:484-521` asserts by AST that
`known_ids` calls those three by name — parameterizing is fine, renaming or inlining is not.
Route the Idea branch through a new `next_idea_id()` so it finally gets the three rules it
skips today (max+1 never the lowest gap, the band ceiling, the floor) instead of a post-hoc
test catching them.

**Four re-points that go red the day 5c lands, none of them obvious:**

- `tests/unit/test_supplements.py:341-348` — `_HISTORICAL` is an **exact-path** set
  containing `docs/restructure/IDEAS.md`, filtered at `:360` by `rel not in _HISTORICAL`.
  One path becomes 254, and the supplement guard reds on every historical idea quoting a
  retired chain. Fix: prefix match on `docs/restructure/ideas/`.
- `tests/unit/test_plan_roadmap.py:145` — a third idea join nobody has named; it does a
  substring test over the raw file. Rewriting it to read `status` makes it *stronger*: it
  can then tell "groomed" from "mentioned inside a groomed entry's body", and it starts
  failing when the roadmap cites an `Idea-N` that does not exist.
- `drydocs/plan/plan_board.py:576-578` — the board's quick-capture box copies
  `- [tag] text` "paste into docs/restructure/IDEAS.md". A markdown line pasted into a file
  that exists; a YAML file needs a filename, which needs an allocation. **This is the one
  place the shard makes capture harder**, and the ADR should say so in Consequences rather
  than discover it.
- `natural_id_key` (`backlog_store.py:84`) does not match `Idea-207a` — it degrades to text
  sort, putting `Idea-10` before `Idea-2`. The ideas store needs its own sort key
  (date DESC, then id DESC, reproducing "new entries at the top").

# Verification

- `poetry run pytest -q` green; `python -c "import drydocs.cli"`; `drydocs --help`.
- `python .claude/skills/groom-backlog/validate.py` reports `ALL CHECKS PASS` and the derived
  counts still reconcile (`items=645` today).
- `validate.py --next-id Idea` returns the same number before and after the shard, and its
  `sources:` line shows local, remote and history all populated (today: `local=251
  remote=251 history=240`).
- **Deep-equality proof**: re-assemble the sharded inbox and diff against the parsed
  monolith; any entry the splitter could not parse is listed, never skipped.
- `poetry run python scripts/render_board.py`, then `git diff --quiet docs/plan/board.html
  docs/plan/ideas.html` — renders are deterministic, so a diff means a committed render did
  not match its source.
- `pytest tests/unit/test_port_manifest.py tests/unit/test_port_reconcile_guards.py` — the
  new `ideas/*.yaml` row must leave no path in `default:` silently, and must leave no dead
  row behind for the retired `IDEAS.md`.
