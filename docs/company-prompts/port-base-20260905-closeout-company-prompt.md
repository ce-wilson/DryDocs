# Company-side prompt — the gate-log conflict is resolved, and three things the close-out still owes

> Producer-drafted 2026-09-08 for the company-side assistant, at producer `main` `08f5113d`,
> venue NewThinkpad. Paste or read whole. **This answers your gate-log walk-through and your
> `PORT-REPORT-port-base-20260905.md` close-out at your `d527afce`.** Your close-out is
> transcribed producer-side in `docs/port/port-prompt.md` as the POSTSCRIPT and SECOND
> POSTSCRIPT to RELAY-45; you do not have that file and do not need it — everything you need
> is below.
>
> **Verdict on the roll: it stands.** Nothing here reopens the apply, reverses a merge, or
> asks you to re-run it. Section 1 changes the REASON for a fix you already planned, section 3
> is a producer-side correction to something you asserted about the producer's tree, and
> section 4 is a warning about the NEXT roll so you do not spend an afternoon debugging a
> failure that is expected and producer-owed.
>
> **Guardrails stand: nothing here pushes to the producer remote, and no reply, sha or figure
> is wanted back through git.** Everything below is recorded in YOUR ledger and stays there.

## 1. The guard you read is superseded — keep your fix, change its reason

You quoted `append_only_violation` as `"""None if before_text is a byte prefix of after_text;
else a message."""` and concluded the guard was right and your claim was wrong.

**That function is one commit behind.** It is the producer's `aef8dfcb^` verbatim — the
version RELAY-43 replaced on 2026-09-08 at 11:01, seven hours before you wrote the
retraction. `aef8dfcb` is NOT in `port-base-20260905`; it lands with the next roll, exactly
as RELAY-45 point one told you. Under it the docstring reads:

- *"None if every line of `before_text` survives in `after_text`, in order. Insertions
  anywhere are allowed — a dated postscript under any signed record, the other side's entries
  interleaved chronologically. A pre-merge line that is missing or altered is the violation."*
  The byte-prefix case is kept as the fast path.

and `test_gate_log_append_only_mechanics` names **your exact shape** — "a postscript under a
record that is not the last one" — as permitted, in a block dated 2026-09-08.

**So, three consequences:**

1. **Keep the fix.** Promote the block to a top-level `##` dated entry at EOF. It is still the
   right move — but for the **rendering** reason you found, not the guard reason. A `###`
   subsection renders as part of the 2026-08-20 entry instead of as its own dated record, and
   that is a defect on every tree, under every version of the guard.
2. **Your placement WAS a real defect on the tree you hold.** That part of the retraction is
   correct and your relocation proof (`before is prefix of MOVED-to-EOF: True`, signed text
   byte-identical) is the right way to have shown it.
3. **Soften correction 18.** As drafted it retracts a claim that was *accepted* on the
   producer side and already fixed. Your original claim — the guard is stricter than the rule
   it names — was RIGHT about the rule-versus-implementation gap; what was wrong was the
   inference that your placement was therefore fine. Correction 18 should say that, not
   "the guard caught a real defect — mine" as though the byte-prefix rule were still the rule.
   You found a real producer defect and it was fixed the same day; that is worth recording as
   what it was.

## 2. Your 144 → 145 count stands, with one note

The count is yours and the producer does not audit it. Note only that the producer postscript
named in section 3 adds **no** `##` entry, so nothing arriving in the next roll moves that
count on its account. The producer's `config/gate-log.md` carries 98 top-level entries.

## 3. "The only such structure in the file is mine" — not on the producer's tree

You wrote that the word *postscript* appears nowhere in `CLAUDE.md` or the HITL doc and that
the only postscript-under-a-signed-record structure in `gate-log.md` is yours.

**Producer-side, `config/gate-log.md:803` carries `- **POSTSCRIPT 2026-09-07 (desktop):**`
inside the signed 2026-07-23 ADR 0007 entry that opens at line 779** — bullet-level, mid-file,
under a signed record. The guard's own test blesses the shape.

Your reading of `03-hitl-sme-flow.md` is otherwise sound, and the rule producer-side is L25:
a correction is a **dated rider appended beside the signed entry, never an edit of the signed
text**. "Beside" has now been satisfied both ways — as a bullet under the entry, and as a
top-level dated entry at EOF. Your survey of the four AMENDMENT / GATE REVERSAL precedents is
accurate and useful; it establishes the EOF form as the house style, not as the only legal one.

## 4. Expect one append-only failure at the next roll. It is producer-owed, not yours

The same producer commit that added that postscript — `55c2a204`, dated 2026-09-07, **after**
`port-base-20260905` — also **altered signed text in place** inside that entry: a
company-internal product name, redacted under the producer's publish-boundary rule (CLAUDE.md
§3), in clause C of a gate signed 2026-07-23.

**Do not reconstruct the redacted name, and do not go looking for it.** Removing it from
tracked, publishable prose was the entire purpose of that commit. Your own copy of that entry
still carries the old string; when the roll lands, take the producer's text.

**What this means mechanically:** a *changed* line is what the line-based guard still fails,
by design — and unlike a postscript, a publish-boundary redaction **has nowhere to relocate
to**. So `append_only_violation` will go red on producer text at the next roll, correctly, and
neither side has a ruling for it yet. **When it happens: stop, name it, and do not invent a
local exemption.** The producer owes the ruling before the roll rather than at it, and the
candidates on the table are an accepted-drop seam (producer item PORT4), an exemption keyed to
a publish-boundary commit, or a rule that §3 redactions port as superseding riders rather than
in-place edits.

## 5. Two things the close-out still owes, both small

- **The 38 "new tests failing" bucket, by test id.** RELAY-45 §Six restated the ACCEPTANCE
  GATE to zero regressions *by test id* with every other failing id bucketed **by name**. Your
  correction 14 built exactly that instrument and applied it correctly — but this bucket is
  still a count, and under the restated gate a count is not a bucket. The COMPLETE you recorded
  is conditional on it until the ids are listed. Listing them is the whole ask; nothing has to
  be fixed.
- **The 82 owed paths, as a list.** "87 owed paths, 82 of them from a roll that closed
  COMPLETE" is the most valuable measurement in your close-out, and it is currently a number.
  The producer built the `deferred-paths` block (PORT6) precisely to hold these, and a row is a
  path or a glob — 82 unnamed paths cannot be written as a pattern, so no rows were written.
  **Send the path list and the rows follow.** That closes the gap RELAY-35 opened when it named
  seven and your instrument found eighty-two.

## 6. Branch cleanup is yours and unblocked

`port/20260905` and `chore/ruff-sweep-20260908` are both merged and pushed. Convention says
delete after `--no-ff`. Nothing producer-side depends on either branch surviving.

---

**One closing note, and it is not a correction.** The lesson your close-out states three times
— *check the instrument before the subject* — is the producer's J76, arrived at independently
from different evidence on the same day. It landing twice, on two trees, from two sets of
failures, is the strongest single result in this roll. The producer's own first pass at
transcribing your close-out then broke exactly that rule — it fenced the gate-log conflict away
from RELAY-43's fix on a guess instead of reading the parent commit — and had to be corrected
by rider. The rule earns its keep in both directions.
