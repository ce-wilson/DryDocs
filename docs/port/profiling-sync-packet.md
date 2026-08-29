# SME review status — the profiling capture protocol (company-side review → producer intake)

**Classification: Internal-Public.** This page is mechanism only: it defines a
document format and an intake checklist. No real identifiers, counts, or
instance names appear here, and none may ever be added.

**Wording rule (user direction, 2026-08-27).** The capture artifact is always
framed and titled as an **SME review status** — the SME's own status record of
a review session, authored company-side and carried across by the SME, by
choice. Never "what to send back," never "return," never a requested payload.
This extends the hand-prompts-ask-nothing-back rule to the reverse channel:
nothing on the producer side requests anything; the producer merely defines
what it can ingest when a status arrives.

---

## 1. The gap this closes

The port is one-way (producer → company). The company side now re-profiles
real source data — previously stubs, PoC files, and untracked evidence — and
amends shared surfaces (gate prompts, crosswalks, registries) in place with
measured findings. Protection for those amendments already exists:
`config/gate-prompts/**` is `canonical-company` in `PORT-MANIFEST.yaml` (J51),
so the next port cannot clobber them.

What did NOT exist is the reverse information channel. The port prompt's
RELAY-6 records the gap in its own words: "guardrail 6 has no slot for that
direction" — a company modelling position or measured finding can be
independently re-invented producer-side against the same source, and has
nearly been. The SME review status is the artifact that fills the slot.

Four existing mechanisms compose into this protocol rather than being
reinvented:

- The **K16 counts-only precedent**: findings travel as shape, enforced by
  construction — `drydocs/fid_census.py` holds `int` and `dict[str, int]`
  fields only, so a row dump is unexpressible. A review status carries shape
  statements the same way: ratios, zero/100%, "all N of N," totals.
- The **receiving-table convention**
  (`docs/restructure/09-fid-identity-and-scope.md`, "The numbers"): producer
  cells stay `_pending_` until a measurement exists; an empty cell means "not
  measured yet," never "zero."
- The **divergence ledger** (`.claude/skills/reconcile-port/SKILL.md`):
  entries carry a TRIGGER for their own retirement and are retired with dated
  reasons, never deleted.
- The **ratification-provenance rule** (port prompt, 2026-08-09): a company
  amendment is only distinguishable from a port-arrived copy if it names its
  introducing commit. Every review status therefore cites introducing commits
  for the files it reports amended.

## 2. The artifact

- **Title convention:** `SME review status — <cluster or worktree> — <date>`.
- **One status per review session.** A session that closes without emitting
  one leaves its work invisible to the producer until a later session covers
  it — same failure class as the unpushed-claim lesson (J31).
- **Landing zone (producer side):** `internal-local/company-backflow/` —
  gitignored, never-port, travels by hand only. The raw status file never
  lands in the tracked tree; the intake transcribes durable facts into their
  tracked homes (section 4).
- **Classification by construction:** the status is written shape-only so that
  it is carryable at all. Real row values, SIDs, account or person names, and
  per-named-entity raw counts stay in the company's internal twin, which the
  status names but never carries.

## 3. The four sections of a review status

### 3.1 Report identity

For every source file profiled: file name, rows x columns, sha256, **pull
date** (extract vintage), and the drop-zone path — named, not carried.

Vintage is mandatory, not decorative. The 2026-08-27 PAT session's own §G1
finding is the reason: a role class present in the August pull did not exist
in the June pull, so a June-based ruling would have been correct on its
evidence and wrong in fact, with no signal anything was missing. See the
extract-vintage convention in `docs/restructure/03-hitl-sme-flow.md`.

### 3.2 Schema of record

The exact landed header list per report, plus header-drift observations:
catalog/PDF spellings vs landed spellings, and any one-concept-two-spellings
finding across sibling reports (the crosswalk class — e.g. one edge qualifier
appearing under two column names in two reports; unrecorded, loaders mint two
properties). Standing rule the first session established: a catalog page's
header list is an INVENTORY of reports; the landed file's headers are the
SCHEMA OF RECORD. Registration validates against the landed file, never the
catalog.

### 3.3 Shape-only findings

Findings as shape statements, counts-only by construction:

- ratios and proportions ("all N of N," "zero divergence," "100% single-holder
  at its own key");
- totals where a total is the finding;
- order-of-magnitude and distinct-count statements ("single-digit distinct
  holders");
- alias proofs stated as comparisons ("two reports, same result, zero
  differences on every populated row").

Boundary (currently precedent, ruling pending — see section 5): totals may
appear; disaggregated splits and raw counts per named entity stay in the
company twin. When in doubt, state the shape and point at the twin.

### 3.4 Shared-surface delta list

- **Files amended company-side:** path + the company INTRODUCING COMMIT
  (ratification-provenance). Commits made on a `feat/*` worktree branch are
  cited as `branch@sha`; the merge-to-main sha is recorded at intake when it
  lands, because provenance needs a commit reachable from the company main.
- **New files minted** (config or otherwise shared-shaped): each one is a
  producer `PORT-MANIFEST.yaml` decision within the week — the `config/**`
  canonical-producer fall-through has nearly overwritten company work three
  recorded times.
- **Backlog-item premise flags:** acceptance clauses the measurements
  superseded (the moved-premise class), named by item id and clause.
- **Frozen-shape amendments:** anything that changes a shape both sides
  share signed (the K7/K8 class) is flagged as its own gated item, and its
  eventual ruling is expected to reach the producer so the producer can run
  its own amendment ritual.
- **Open questions** the session chose to leave for a producer session.

## 4. Producer intake checklist (run per status, in this order)

1. Land the file in `internal-local/company-backflow/` (hand-carried).
2. Divergence ledger: add or update entries in
   `.claude/skills/reconcile-port/SKILL.md`, each with a TRIGGER; retire
   entries the status discharges, dated, in place.
3. `PORT-MANIFEST.yaml`: a row for every new company path reported (3.4),
   before the next port roll — never after.
4. Backlog items: append premise-flag notes to the named items; never edit a
   signed record (L25 — riders, not edits).
5. Crosswalk and registry edits the status evidences (3.2 class).
6. Adopt amended Internal-Public pages where the company revision is the
   better artifact (gate prompts are already shape-only by their own fence):
   replace the producer copy, cite the company introducing commit in the
   page header, and add a gate-log RECORD stating the page was amended from
   company review and remains DRAFTED/unsigned producer-side. Two-tier
   doctrine is untouched: producer sign-off and company sign-off stay
   separate acts.
7. Receiving tables: fill `_pending_` cells the status measures, citing the
   status date (K16 style).
8. Guards + renders: full suite, ruff both gates, `render_board.py`,
   stale-render diff — then push and check CI at the pushed sha.

## 5. The volumetrics boundary (status: precedent, ruling pending)

`config/classification.yaml` (sanitize section) records the working rule —
totals stay, disaggregated per-entity splits go to the internal twin — and
explicitly flags it NOT RULED. Three sessions have now independently applied
or re-derived the same fence. The ruling rides the producer's
`tech-partner-attach-level` sign-off session as a rider question: ratify
"totals + ratios + all-N-of-N shape statements are Internal-Public;
disaggregated splits and raw counts per named entity stay in the twin." On
sign-off: gate-log RECORD, one sentence in `PUBLISH-BOUNDARY.md`, and the
classification.yaml comment upgraded from "not ruled" to ruled-with-date.
Until then, this protocol applies the fence as written above.

## 6. Instructions that travel the other way (producer-authored, company-run)

The J41 relay rules exist for the port prompt's STANDING RELAYS; this section
extends them to INFORMAL hand-offs — the one-sentence chat instruction the SME
relays into a company session, often deliberately without context. Measured,
not hypothetical (2026-08-27): a producer sentence — "take the producer copy,
it's plain canonical-producer code" — was relayed context-free; the premise
was wrong (the company file was a 61-command monolith the producer had long
since split into submodules), and a compliant execution would have deleted 57
command definitions. The receiving agent's own caution was the only guard.
Every producer-authored instruction bound for a company session therefore
carries, IN THE SENTENCE ITSELF:

- **its basis** — `[VERIFIED-PRODUCER]` scoped to exactly what was checked
  (the constant exists producer-side; NOT "your file matches mine");
- **its falsifier** — what to do when the company-side object differs
  structurally: STOP AND SCOPE, never proceed;
- **no assertion of company state** — expectations phrased as expectations;
  only `[COMPANY-CONFIRMED]` facts (returned in a PORT-REPORT or an SME
  review status) may be stated as their repo's reality.

A sentence that cannot fit all three is not ready to relay.

## 7. The internal concurrency model (context the intake should expect)

The company side runs multiple concurrent review sessions in git worktrees
(one worktree per cluster, `feat/*` branches off their main, a helper script
managing windows). Consequences for this protocol:

- One SME review status per cluster-session, naming its worktree and branch.
- Cluster statuses double as adoption-session reports where the cluster maps
  to a hand-carried adoption dossier.
- Item claims still serialize across worktrees — one repo, one items/
  directory; claim-pushed-before-work applies per cluster.
- Branch-cited commits are pre-merge; intake records the merge commit when it
  becomes reachable from their main (see 3.4).
