# SME review status — session-close template for profiling / review sessions

**Hand-carried; never ports. For the company-side session's own use.**
This template asks for nothing. It describes the status record a review
session writes for itself at close — the same way your PORT-REPORTs and
upgrade-ledger entries are your own records. Whether any status travels
anywhere is the SME's choice, made outside this document.

## Why a session-close status

Your sessions now profile real source data and amend shared surfaces (gate
prompts, crosswalks, registries) in place with measured findings. A session
that closes without a status record leaves its findings living only in that
session's transcript — the same failure class your claim-before-work rule
exists for. The status is the durable, single-file record of what the session
measured, what it changed, and what it left open.

## Naming and handling

- Title: `SME review status — <cluster or worktree> — <date>`.
- One status per review session. Write it at session close, after the last
  push, so every cited commit exists.
- Write it SHAPE-ONLY (see section 3) so the file itself is clean at your
  Internal-Public tier by construction. Raw counts per named entity, row
  values, SIDs, and person or account names belong in your internal twin
  documents (your existing census convention) — the status names the twin,
  never carries its contents.
- If the session ran in a worktree, the status names the worktree and branch,
  and cites branch commits as `branch@sha`.

## The four sections

### 1. Report identity

Per source file profiled: file name, rows x columns, sha256, pull date, and
the drop-zone path (named, not attached). The pull date is mandatory — your
own §G1 precedent: a role class present in one pull did not exist in the
prior pull, so a ruling keyed to the older extract would have been correct on
its evidence and wrong in fact. A status without vintages cannot support a
vocabulary ruling.

### 2. Schema of record

The exact landed header list per report, plus drift observations: catalog
spellings vs landed spellings, and any one-concept-two-spellings finding
across sibling reports. Your own standing rule applies: the catalog page is
an inventory of reports; the landed file's headers are the schema of record.

### 3. Shape-only findings

State findings as shape, counts-only by construction:

- ratios and proportions ("all N of N," "zero divergence," "100%
  single-holder at its own key");
- totals where the total is itself the finding;
- distinct-count magnitude ("single-digit distinct holders");
- alias proofs as comparisons ("two reports, same result, zero differences on
  every populated row").

Boundary, per your own gate page's fence: totals may appear; disaggregated
splits and per-named-entity raw counts stay in the internal twin the status
names.

### 4. Shared-surface deltas

- Files amended this session: path + introducing commit (`branch@sha` when on
  a worktree branch; add the merge commit in your ledger when it lands).
- New files minted that a future reconcile would meet as a collision.
- Backlog-item acceptance clauses the measurements superseded, by item id and
  clause (the moved-premise class — record, never silently rewrite).
- Anything that would amend a shape both repos hold signed: flag it as its
  own gated item in your gate flow, per your two-tier doctrine.
- Open questions the session deliberately left.

## Worked example (the 2026-08-27 PAT cabinet session)

That session's close-out is the reference shape: a report inventory table for
all thirteen reports (name, rows x columns, sha256, pull date); the landed
header lists; the alias and cardinality findings stated as shape ("proven
alias — two reports, zero divergence"; "single-holder at its own key,
100%, no exception"; "single-digit distinct holders — defer with the shape on
the record"); the workbook disposition (drop zone + sha, workbooks never
committed); and the amended-files list with introducing commits. Counts lived
in the session's internal census twin; the status stated shape and named the
twin.
