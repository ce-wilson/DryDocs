# Company-side prompt — close out the `7c18ff4b..port-base-20260820` port (the backlog shard)

> Producer-drafted 2026-08-24 for the company-side assistant. Paste or read whole.
> Your port was reviewed producer-side against your own
> `PORT-REPORT-port-base-20260820.md` and your closeout summary. **Verdict: sound.**
> The union arithmetic was re-derived independently and closes exactly; the census
> sums to 544 with zero fall-through; the proof is quoted with its count. Nothing
> below undoes anything or blocks anything — these are five conditions on YOUR
> follow-up list, three of which it does not carry.
>
> **Everything here is recorded in YOUR upgrade ledger (`port-exec-state.md` / the
> PORT-REPORT) and stays there. Nothing in this prompt sends anything to the
> producer, and no reply, sha, or figure is wanted back.** Guardrails stand:
> nothing pushes to the producer remote.

## 1. Your item count disagrees with itself — 478 or 479

`PORT-REPORT-port-base-20260820.md` says **478** in five places: the step-1 union
(416 company + 62 producer-only), the splitter output, and the proof line
(`PROOF OK: 478 items deep-equal`). Your closeout summary says a **479-item tree**.

Producer-side re-derivation supports 478 — the producer monolith the union read
holds 469 items, 469 - 62 producer-only = 407 shared, 416 - 407 = the 9 company-only
`DD1-DD9` you name, and 469 + 9 = 478. So the report is almost certainly right and
the closeout is the number to explain.

Two benign explanations, and they are distinguishable:

- **An item was minted after the tombstone** — your two follow-ups are exactly the
  kind of work that mints one. Then 479 is correct *now* and 478 was correct *at the
  proof*, and one sentence in the ledger saying so closes it.
- **The closeout miscounted.** Then the report stands and nothing changes.

Run `ls docs/restructure/backlog/items/*.yaml | wc -l` against the tombstone commit
and against your current tip; the difference is the answer. Record which it was.
This matters beyond tidiness: the item count is the one number a later port can
check the shard against, so it has to mean something.

## 2. `Track-1` in your report labels the full suite — correct it before it travels

The acceptance line reads `Track-1 (tests/unit/): 2415 passed / 69 skipped / 4
failed`. That is the **full unit suite**. Track-1 is the five-file portable subset —
`test_variable_classifier`, `test_variable_resolver`, `test_variable_staging`,
`test_command_parser`, `test_module_boundary` — and you ran it correctly at closeout:
**123 passed / 3 skipped / 0 failed**, which is consistent with your own history.

Fix the label in `PORT-REPORT-port-base-20260820.md` and give the full-suite figure
its own line. The reason this is worth a commit rather than a shrug: the port
prompt's acceptance gate maintains a **running chain of Track-1 reference figures**
across ports, each compared against the last. A `2415` entering that chain makes
every later comparison meaningless, and the error is invisible once the report is
filed — the two numbers are both real, only the labels are swapped.

## 3. Four failures have now shipped twice under an exemption nobody wrote down

The acceptance gate says, in these words: *"Full `pytest tests/unit/` — ZERO failures
is the contract."* Your report ships **4** with a not-port-introduced argument, and
states they are **identical to `PORT-REPORT-7c18ff4b`**. That is the part to act on:
the same four rode the previous port too, so this is the second consecutive port
closed against a contract that says zero, under a carve-out that exists in neither
the gate nor the manifest.

The argument itself is sound — byte-identical failures at pre-port HEAD prove
not-port-introduced, and the classes named (untracked HR-csv BOM, autocrlf CRLF,
offline venv without the editable install) are all environmental. The problem is
that it is an argument made twice in prose and never written into the rule. **Pick
one, this port:**

- **Fix the environment** so the figure is genuinely zero, or
- **Write the carve-out into your acceptance record** — the four classes, each with
  its reason and the condition under which it stops being acceptable.

A third silent carry makes them permanent, and permanent-by-drift is how a gate
stops meaning anything.

Two of the four also deserve a cause re-check rather than inheritance:

- **`test_render_determinism` (CRLF).** The producer fixed CRLF renderer output by
  writing LF explicitly at every render site. If this still fails on your side, the
  live cause is more likely a local `core.autocrlf` setting than anything inherited —
  a different defect, with a different fix.
- **`test_repo_paths` x2.** The producer has an open note on the same test family
  failing only outside full-suite order. Your diagnosis is the offline venv's missing
  editable `.pth`. Both cannot be the cause of the same two failures; confirming
  which is worth ten minutes, because the venv explanation implies the tests would
  pass in a normal install and the ordering one implies they would not.

## 4. The allocator-band flip has a trigger, and it fires mid-groom

You took `test_backlog.py` at **producer polarity** — the band test asserts every id
is <= 9999. Your report already identifies this correctly: it passes today **only
because you have minted no id >= 10000.**

The consequence worth stating plainly is the timing. The failure does not surface
when someone reviews the test; it surfaces the moment a groom allocates the first
company id in the 10000 band, which is the least convenient moment for a backlog
guard to go red. So the company-polarity variant — assert the company mints >= 10000,
with its own `PORTED_COMPANY_IDS` set for the ids that arrived by port — **lands
before that first id is groomed, not after.** Treat it as a precondition on the next
groom rather than as a follow-up item with no date.

## 5. The seven deferred gate sessions — the shape is already right

Your `DEFERRED` records carry a NONE-graph-writes line and a named RE-ARM each, which
is the honest-lifecycle shape and needs no change. The only thing worth adding as you
run them at your own cadence: each RE-ARM condition should name **what would have to
become true**, not **when you intend to look again**. A date slips silently; a
condition is checkable by whoever opens the record next.

## 6. What the producer checked, and what it is not asking for

Re-derived independently and confirmed: the range (25 commits / 544 paths), the
census sum, the union arithmetic, and the base and backup tags resolving. The seven
hand-reconciles read as specific and defensible — forcing the
`catalog_dev_team_*` edges to `planned` because `pat_team_roles` appears nowhere in
your gate-log is the correct call rather than the convenient one.

Two items need **no action from you**:

- **The `lob-product-team.yaml` manifest gap you found and recorded.** It was a real
  producer defect: the file matched `config/taxonomy/**` as canonical-producer while
  the step-176 apply note ruled it per-entry, and a wholesale take would have dropped
  your real LOB rows. The producer added the per-entry row the same evening; it
  reaches you at the next port. Your census naming the gap is the correct and
  complete record.
- **The three surfaces you authored company-side** — the vocabulary company
  positions, the `doc-source-registry` company fields, and the `lob-product-team`
  company nodes. Your report flags these as company-authored rather than producer
  drift. That is registered producer-side; the next reconcile will treat them as
  company-canonical rather than trying to "correct" them.

## Not part of this follow-up, but worth knowing before the next port

The producer has stopped tracking its own port-review files — a review of YOUR port
transcribes your session, and `docs/reviews/**` is `default_ok`, so a tracked copy
ports back to the repo it is about. They are machine-local from now on.

The practical effect for you: **the next range will hand you a deletion of
`port-review-7c18ff4b-20260820.md` (under the producer's docs/reviews/, already
untracked there — which is why citing its full path would dangle).** That is a producer-side
untracking, not a retraction — its findings stand and several of them are already in
your ledger. Keep your copy; take the deletion or don't, either is fine, and neither
is a discrepancy to chase.

---

**Record the close-out in `port-exec-state.md` as you have been** — that ledger is
the record, and it is yours. Nothing is reported back.
