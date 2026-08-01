# §FIXPKG — the fix-package contract (developer handoff)

What `drydocs-remediation` emits per data series, exactly shaped for a developer
to pick up from an **existing** Jira, verify, and check in. We never create the
Jira and never deploy; the package must therefore be self-explanatory without a
conversation with us.

## §LAYOUT

```
fix-packages/<series-id>/            # e.g. <APPCODE>-<SERIES>-<YYYYMMDD>
  jira-comment.md                    # paste into the EXISTING Jira (see §JIRA)
  manifest.yaml                      # file list + checksums, graph snapshot ref,
                                     # approval ids from the review gate, tool versions
  original/                          # the "before" — untouched evidence
    <folder>.xml                     # folder export(s) as pulled, byte-preserved
    runbook.xlsx                     # the runbook support was handed (if one exists)
    escalation-db.xlsx               # current SCIM/escalation rows for the series
    issue.md                         # the triggering problem: failures/evidence/dates/queues
  target/                            # the "after" — what dev checks in / applies
    <folder>.updated.xml             # minimal-diff updated definition (§XML)
    runbook.xlsx                     # GENERATED runbook, previous Excel format
    escalation-db.xlsx               # only present when routing/SCIM rows change
    change-doc.md                    # per-change what/why/evidence + XML diff excerpts
    flow.mmd (+ flow.svg)            # mermaid lineage flow for the series
```

Rules:
- `original/` is evidence — never edited, checksummed in the manifest.
- `target/` is fully regenerable from (`original/` + the approved change-set);
  the manifest records the change-set id so regeneration is reproducible.
- Real values live throughout the package — so **fix packages are `Internal`,
  and carry confidential material** (J23 retired the separate fourth tier;
  confidential handling is a note on the entry, not its own level): company
  side under `internal/` conventions; on the producer only sanitized samples
  ever exist, under a gitignored path.

## §XML — round-trip rules for `<folder>.updated.xml`

The updated XML must diff cleanly against the original in the dev team's
tooling. Therefore:

1. **Parse the original; mutate; serialize.** Never regenerate XML from the
   graph model alone — the graph doesn't carry every attribute, and a
   regeneration produces a 100%-diff file no developer can review.
2. **Lossless import**: preserve unknown elements/attributes and sibling order
   from the original document; the internal model keeps what it doesn't
   understand.
3. **Touch only approved fields.** Each mutation maps 1:1 to an approved change
   in the change-set (gate approval id recorded per change).
4. **Self-check before packaging**: re-parse the emitted file; the structural
   diff vs original must equal exactly the intended change list — anything else
   aborts packaging.
5. **Version caveat**: target is the 9.0.21.300 XML definition format
   (export / `ctmdeffolder` shape). The vendor XML schema docs are a known
   reference gap (see `toolchain.md` §SKILLS); until acquired, treat attributes
   conservatively (preserve, don't normalize).

Typical approved-change kinds (from plan.md P5): FileWatcher Description
enrichment (pipe `key:value` metadata), the **variable review** (§VARS below),
FileWatcher post-exec `cat` (the token/control NFR), rename to the naming
standard, condition corrections, stale-folder disposition (whole-folder delete
is a change-doc recommendation, not an XML edit).

## §VARS — the variable review (remove → normalize → supplement)

Variables are first-class citizens of the change-set. Three passes per series,
every change evidence-backed and gate-approved:

**1. REMOVE — unnecessary variables.**
- *Unreferenced*: `%%` vars that no command line, watch path, or condition in
  the series references — evidence is the P2 CMDLINE/path parse showing zero
  uses. (A var referenced by a *stale* job only is a removal candidate tied to
  that job's disposition.)
- *Duplicates*: repeated `(job, var)` definitions — legal in the source, almost
  always a defect in intent; keep the effective one, remove the shadowed one,
  record which value was live.
- *Retired by standard*: vars superseded by the current conventions (e.g.
  date-format helper vars on placement jobs replaced by `BUS_DATE`).
- *Redundant shadowing*: a job-level definition identical to the inherited
  folder-scope value — delete and inherit.

**2. NORMALIZE — align to the ontology-driven variable model.**
- FileWatcher watch paths rewritten from literals to the standard component
  expression (`%%DROPBOX/%%PARENT_DIR/%%FILE_NM_PREFIX.%%BUS_DATE.
  %%FILE_NM_SUFFIX.%%EXTENSION`) — the greenfield exemplar shape.
- Each standard component variable is *typed by the ontology*, per the
  file-name component standard: prefix → business identity on the
  distribution, `BUS_DATE` → the business date (`dcterms:temporal` — the data's
  date, never load/arrival date), extension → media type / DistributionRole.
  That typing is what makes the variables queryable metadata instead of string
  plumbing.
- The post-exec `cat` reuses the identical expression
  (`knowledge/standards/technology/filewatcher-postexec-token-cat.md`).

**3. SUPPLEMENT — add the new metadata the interface already knows.**
- Missing standard component variables, populated from the file-name
  decomposition (P2 `filename_standard`).
- *Scope placement*: series-wide values defined once at the smart-folder header
  (folder scope) and inherited, instead of copied per job.
- The Description pipe `key:value` enrichment is the documentation counterpart
  of the same facts — variables are the *runtime* copy, the description the
  *human* copy; the generator keeps them consistent.

**Change-set encoding** (what `changes.py` consumes) — one entry per variable
change: `kind` (`remove-var | add-var | set-var | move-to-folder-scope`),
`scope` (`job | folder`), `name`, `old`/`new` value, `evidence`, `approval_id`.
The §XML minimal-diff rules apply unchanged: variable elements are edited in
place, sibling order preserved, and the packaging self-check must see exactly
these entries in the diff.

**Calibration note:** even greenfield-conforming jobs (variable-driven path +
matching `cat`) can still carry findings — e.g. a free-text Description with no
`key:value` block. The review always emits the full finding list; the batch
decides what to fix now vs record.

## §XLSX — the Excel artifacts

- **Runbook** — generated in the *previous* format so consumers see a familiar
  document (format A: vertical `Information | Details | Comments` sheet at
  SEAL/folder grain; format B: job-grain rows with impact statements, layer,
  SLO/SLA, pipeline ids, source/target entities). Content is the §RB projection
  from `plan.md` — every cell traceable to a system of record; cells with no
  system of record yet are flagged `[TRIBAL — captured in P5]` rather than
  silently typed in.
- **Escalation-db sheet** — the SCIM E-columns for the series' jobs, emitted
  only when the change-set alters routing (queue, tier, severity, module/item
  roll-ups). Otherwise omitted so the package doesn't imply an escalation
  change that isn't happening.
- Templates: producer ships neutral templates; the company overlays its real
  workbook templates internally (expected port collision — keep company's).

## §JIRA — `jira-comment.md` (we add info to an existing ticket)

Paste-ready body, structured so the ticket reads as a complete work order:

```
## Fix package — <series-id>
**Trigger:** <1–3 lines: the repeated failures / missed routing / defect>
**Scope:** folders <n>, jobs <n>, FileWatcher → provisioning chain <zones>

### What changed and why
<table: change | job/folder | why | evidence | approval id>

### Artifacts (attached)
original/ … (evidence, untouched)   target/ … (to check in / apply)

### Developer checklist
- [ ] load target/<folder>.updated.xml into a dev workspace; validate
- [ ] diff vs original/<folder>.xml — expect exactly the changes listed above
- [ ] check in via your SCM + deployment path (we do not deploy)
- [ ] if escalation-db.xlsx present: apply SCIM rows with the routing owner
- [ ] confirm; runbook regenerates from the graph after the change lands

**Rollback:** original/<folder>.xml is the exact prior definition.
```

Contract points:
- **No Jira API in v1.** The comment is pasted and files attached by a human.
  If automation is ever wanted, it is "post comment + attachments to a provided
  issue key" — never issue creation, never state transitions.
- The comment never assumes the reader has graph access — evidence is inlined
  or attached.
- The final checklist line closes the loop from `plan.md` P6: after check-in,
  the runbook regenerates and the spreadsheet stops being hand-maintained.
