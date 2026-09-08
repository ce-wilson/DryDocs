# The owed-path carve-out, reviewed — the manifest already rules 73 of the 87

**Date:** 2026-09-08 · **Trigger:** the company's `sme-path-carveout-review.md` + `.csv`,
committed company-side, produced in answer to §5 of
`docs/company-prompts/port-base-20260905-closeout-company-prompt.md`, and relayed by the SME
with one instruction: review it. **Lens:** the producer's own disposition classifier, run
against the producer tree. **Classification:** Internal-Public (mechanism only; path names and
manifest classes). **Pen:** reviews. **Decides nothing** — no `deferred-paths` row is written
here, because a row is a producer ruling and this review exists to say how many rulings are
actually needed.

- **Reviewed at:** commit `42789fd6` on `main`, port base `port-base-20260905`; venue
  NewThinkpad. *Absent here reads as not-yet-ported, not as broken
  (`docs/style/review-provenance.md`).*
- **Subject:** the company's `sme-path-carveout-review.md` and its `.csv` twin —
  `[SME-REPORTED]`, hand-carried. The company's tree cannot be read from here, so their
  87-row absence claim is taken as reported and is NOT what this review checks.
  **The FILE is the citation and the commit sha deliberately is not:** two hand-carries of
  that close-out relayed two different shas for it, neither verifiable from this side, and a
  sha nobody here can resolve is worse than no sha — it reads as checked. The company's own
  ledger holds the number.
- **Instrument:** `drydocs.port.dispositions.classify` at `42789fd6` — the ONE classifier
  (PORT6), called as an importable object against `PORT-MANIFEST.yaml`, never by parsing a
  render (J37).
- **Coverage, stated because it bounds every count below:** 74 of the 87 rows were transcribed
  from the relayed document and classified. **Every one resolved to a real path at
  `port-base-20260905`** — no row names a file that does not exist. The 13 not transcribed are
  named by disposition where they matter, and no claim here depends on them.

## 0. Verdict

**The document is sound, the instrument is right, and its central framing overstates the ask
by a factor of six.** It presents 87 rows as an SME decision surface. Run through the
manifest, **73 of the 87 are already ruled** — by an `entry_rule`, by a `default_ok` row, or
by a disposition that names its own action. **The rows that genuinely need a human are 13 or
14.** Three corrections follow, one of them arithmetic. Nothing here reopens the roll, and the
"presence versus content" caveat the document opens with is correct and worth keeping — it is
the most useful paragraph in it.

## 1. The decision surface is 13–14 rows, not 87

By disposition, with the classifier's own answer beside the document's:

| disposition | rows | already ruled by | needs the SME? |
|---|---|---|---|
| `canonical-producer` | 5 | the disposition itself — take the producer's copy | no |
| `per-entry` | 7 | blocked on the T24 vocabulary migration | no — and not this review's |
| `canonical-company` | 8 | **7** by the `config/gate-prompts/**` entry_rule (§2) | **1** — the `graph-tests` row |
| `evaluate` | 13 | nothing — this is the real bucket | **yes, all of them** |
| `derived` | 3 | J43 — regenerate last, never carry | no |
| `default_ok` (the doc's "clean-add") | 51 | explicit J16 rows with a `reason:` (§3) | no |

**Total needing a ruling: 13 `evaluate` rows plus 1 `graph-tests` row = 14.** The document
already says as much for `canonical-producer` ("the manifest already says take it… the least
ambiguous group") and for `per-entry` ("blocked on the vocabulary migration, not on this
review"). What it does not do is carry that reasoning through the two largest buckets, and
those two are 59 of the 87.

## 2. `canonical-company` — "needs a ruling per row" is wrong for 7 of the 8

The document says: *"the rule says the company copy wins a collision. There is no company
copy, so the rule does not answer it. Needs a ruling per row."*

Seven of the eight are `config/gate-prompts/**`, and that row carries an **`entry_rule`** that
answers it in its first sentence:

> The consumer's real gate specs WIN and are never overwritten. **A producer spec whose slug
> the consumer does not hold is a CLEAN-ADD, taken whole**: every slug an item's `gates:` names
> must resolve to a prompt file … and gates.json is DERIVED from the files present, so a
> missing prompt is a red guard and a gate page that cannot render.

It then gives the enumeration recipe ("Enumerate, do not browse"), and records that the
2026-09-05 apply took ten prompts exactly this way. So the seven are not undecided; they are
decided, and the decision is *take them whole*. Leaving them in an SME queue delays seven
files whose absence makes a gate page fail to render.

**The eighth is different, and the manifest says why in the same breath.** That entry_rule
closes with the governing distinction:

> A rule the apply must read is an `entry_rule`; a **note** explains, it does not authorize.

`graph-tests/**` carries only a note — *"consumer's real acceptance suites win; seed twins
follow producer renames as deliberate consumer commits"* — which does not speak to an absent
file. So `graph-tests/tom-required-contacts.yaml` is the one row in this group that genuinely
needs the SME, and it needs them for a reason the manifest itself supplies.

## 3. The 51 are `default_ok`, not the bare default — the decision IS recorded

The document labels its largest bucket **`clean-add` (default)** and glosses it *"the manifest
default: clean-add when absent on consumer."* Of that bucket, **41 rows were classified and
all 41 returned `default_ok`** — not the unmatched-default rule. Every one matched an explicit
manifest pattern:

`tests/**` 24 · `docs/reviews/**` 5 · `internal/**` 3 · `docs/decisions/**` 3 · `scripts/**` 2 ·
`drydocs_deepdoc/**` 2 · `drydocs_core/**` 1 · `drydocs_api/**` 1

**Not one fell through to the default.** The ten rows not transcribed sit in those same eight
directories, so the same eight patterns match them, but they are unverified and are counted
that way.

`default_ok` is not a synonym for the default. It is the J16 class, and the apply-order gloss
in `scripts/render_port_dispositions.py` states its whole purpose: *"the default ON PURPOSE
(J16) — the row exists to say someone thought about it."* Each row carries a `reason:` — for
the 24 `tests/**` paths, the largest single group in the entire document:

> the suite is producer-authored, but consumer expectations legitimately diverge
> (`test_schema.py`'s constraint count is the standing example, and has its own row) — so
> evaluate-on-collision is exactly right, and the four rows above pin the exceptions that must
> NOT be re-derived.

So the document's sentence — *"the default says take them. Nothing anywhere records a decision
not to; the gap this document exists to close"* — is right in its first clause and wrong in
its second. A decision IS recorded, per directory, with its reason, by someone who wrote the
row for that purpose. The gap the document closes is real and valuable, but it is a **visibility**
gap, not a decision gap: nobody knew these 51 paths were absent. What to do about them was
already written down.

## 4. The summary table's `canonical-company` cells are transposed

Stated: `canonical-company | 1 carried | 7 new | 8 total`. The document's own detail table for
that group lists **seven** rows marked `0902 (closed roll)` and **one** marked `this roll`
(`config/gate-prompts/controlm-folder-identity-grain.yaml`) — the reverse.

The two cells are swapped, and the swap is self-detecting from the totals row:

- **As printed:** the carried column sums to 76 and the new column to 11, against a stated
  TOTAL of 82 and 5.
- **With the swap:** 82 and 5 exactly.

The TOTAL row and the per-row detail are both right; only the one line between them is wrong.
Worth naming plainly because it is the exact class the close-out itself flagged — *"buckets
that don't sum to their own total aren't measuring what they claim"* — and because a reader
who trusts the summary concludes that seven gate prompts arrived this roll when six of the
seven have been owed since a roll that closed COMPLETE.

## 5. One scope detail in the doc-guard note; the conclusion is right

The note says the guard reads *"`docs/design/**` plus `docs/**runbook.md` and `EXTRA_DOCS`."*
It reads **`docs/design/*-runbook.md`** plus `EXTRA_DOCS` — the runbook glob only, not all of
`docs/design/**`.

The conclusion is unaffected and correct: the file is out of scope, and it should stay out.
The precedent cited is real and is in the guard's own docstring
(`tests/unit/test_runbook_currency.py:248` — the port-prompt archive is deliberately absent,
"a record whose paths are statements about what is not here"). Adding this document to
`EXTRA_DOCS` would turn 87 deliberate absences into 87 failures, exactly as the note says.

## 6. What stands, and is worth saying

- **Every path resolves.** All 74 transcribed rows name a real file at `port-base-20260905`.
  Generated, not typed, as the document claims.
- **The "presence, not content" caveat is the best thing in the document** and should survive
  into whatever this becomes. Its two examples are both real: `config/gate-log.md` present on
  both sides with producer entries missing, and `config/source-registry.yaml` present on both
  sides with `cadence:` rows missing — the second of which silently froze a committed render
  for three weeks. An empty column is not a clean bill of health.
- **82 of 87 predate this roll.** That is the finding RELAY-35 asked for and did not get: it
  named seven, and the instrument found eighty-two. The roll that closed COMPLETE closed over
  them.
- **`[SME-REPORTED]`, not verified:** the company also reports that 30 of the 38 failing test
  ids sit in two already-named deferred classes — 27 in the lineage family and 3 in
  `domain_registry`. Recorded as received; not checked here, and it does not bear on any count
  above.

## 7. What this asks for next

Before any `deferred-paths` row is written — and none is written here — the rulings needed are:

1. **The 13 `evaluate` rows** (`docs/design/*-substrate-review.{md,html}`, the source-files
   map, the source-registry identity review, the web-scaffolding review, and the feedback
   capture). These are design docs and their governed renders; the manifest deliberately does
   NOT make them canonical-producer, because a doc the consumer finalizes becomes its own
   canonical-company row and a blanket take would overwrite the next one before anybody
   noticed. Thirteen judgment calls, and they are the real work.
2. **`graph-tests/tom-required-contacts.yaml`** — one ruling, on a row whose only guidance is
   a note.

Everything else in the 87 has an answer already. Seven gate prompts should be taken whole
today; they are not waiting on anyone.
