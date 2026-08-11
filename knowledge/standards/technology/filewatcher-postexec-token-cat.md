---
standard: control-m-filewatcher-postexec-token-cat
domain: technology
taxonomy_path: technology/orchestration/control-m/job/filewatcher
governs: ControlMJob.post_command     # FileWatcher jobs only (TASK_TYPE/job type = FileWatcher)
authority: internal-standards         # config/precedence.yaml tier 2 — refines the BMC baseline
refines: bmc-baseline
applies_to_source: controlm-psgmgr
status: planned                       # proposed by SME 2026-07-02; promote to active via the gate
trust_tier: internal / SME-asserted / mutable
---

# Internal Standard (NFR) — FileWatcher jobs must `cat` the token/control file post-execution

**Corpus:** INTERNAL (company-specific standard) — *not* vendor documentation.
**Captured:** 2026-07-02, from SME. Proposed for the company standards page; register as
the next rule number in the standards-rules registry when adopted.
**Type:** Non-functional requirement (observability / TDQ evidence), machine-checkable.

---

## Requirement

Every Control-M job of type **FileWatcher** that watches a **token (`.tok`) or control
(`.ctl`) file** MUST define a **post-execution command that `cat`s the watched file**,
using the *same* `%%` variable expression as the Watch path, e.g.:

```
Watch path : %%DROPBOX/%%PARENT_DIR/%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION
Post-exec  : cat %%DROPBOX/%%PARENT_DIR/%%FILE_NM_PREFIX.%%BUS_DATE.%%FILE_NM_SUFFIX.%%EXTENSION
```

Reusing the identical variable expression guarantees the file that was *detected* is the
file that gets *echoed* — no second path to drift.

## Rationale (why this is an NFR, not a style preference)

- **FileWatcher logs record detection, not content.** The watcher confirms existence /
  size / stability of the file; it never captures what the file *declares*. The incoming
  record/file count declared by the source lives **inside** the token/control file.
- **Without the `cat`, the count is only confirmable after raw-zone ingestion** — too
  late for upfront TDQ (technical data quality) reconciliation. A short or duplicate
  feed is discovered downstream, attributed to the load job, and triaged backwards.
- **With the `cat`, the declared incoming count lands in the FileWatcher's sysout at
  detection time**, giving:
  1. an accurate **incoming TDQ / file count** *before* ingestion starts;
  2. a **two-point reconciliation**: declared count (FW sysout) vs landed count
     (raw zone) — a mismatch localizes the fault to the transfer, not the load;
  3. a **point-in-time copy of the control-file content in the Control-M log** —
     incident-triage evidence that survives even if the source overwrites or purges
     the file.

## Scope and guardrails

- **Applies to:** FileWatcher jobs watching `.tok` / `.ctl` (DistributionRole TOK/CTL
  per the file-name component standard) — small metadata files that declare counts.
- **MUST NOT** `cat` the **data file itself** (`.dat`/`.csv`/… — DistributionRole DAT).
  Data files can be multi-GB; echoing one into sysout floods the log and can breach
  sysout limits. If a FileWatcher watches a data file directly (no token/control file in
  the interface), that is a separate finding: recommend adding a control/token file to
  the interface, or capture counts by other means — do not satisfy this NFR by catting
  the data file.
- Compressed tokens: `cat` a compressed file produces garbage in sysout — if the token
  arrives compressed, the post-exec should decompress to stdout (e.g. `zcat`) instead.

## Conformance check (machine-checkable)

Violation predicate, evaluable from the CM_ replica + the file-name decomposition:

```
job.type = FileWatcher
AND watched-file DistributionRole IN (TOK, CTL)
AND (post_execution_command IS NULL
     OR post_execution_command does not reference the watch-path variable expression)
```

- The post-execution command lives on the job definition (UI: "Post-execution command").
  **VERIFY the exact `CM_DEF_VJOB` column name** with the data-dictionary probe
  (`controlm-db` skill, `references/ingest.md` §PROBE) before wiring the check.
- Wired as a P5 conformance finding in the runbook-automation pipeline
  (`controlm-runbook-automation` skill): each violating FileWatcher generates a proposed
  change (add the post-exec `cat`) through the review gate → the Jira fix package.

## Amendment 2026-08-11 (C30) — the check is now an equality, and it has a detector

Two changes, both from the [greenfield job standard](controlm-greenfield-job-standard.md):

**The conformance predicate got simple.** "Post-execution command does not reference the watch-path
variable expression" is nearly impossible to assert against a five-variable composition. Under the
greenfield derived-handle pattern both fields are one token (`%%F_FQN_TOK`), so the check is string
equality: `post_command == "cat " + watch_path`. Implemented as **R39a**.

**The MUST NOT half is now enforced too, and it is the one with teeth.** A deployed `_DAT_ONPM_FW`
job was found carrying `cat` on a `.txt` — DistributionRole DAT. Implemented as **R39b**, severity
must-fix, because the risk in this standard sits in the forbidden clause rather than the required
one: multi-GB into sysout.

**Requirements-page correction:** REQ-3 mandates the post-command "for job type file_watcher"
without qualification, which reads as *all* watchers and would cat data files. It needs the TOK/CTL
scope this standard already states.

## Relationship to other standards

- **File-name component standard** (proposed, website): supplies the DistributionRole
  (TOK/CTL vs DAT) that scopes this rule, and the `%%` variable decomposition the
  post-exec must mirror.
- **Description-field metadata plan**: the FW description enrichment (MFTS route, file
  components) is *documentation*; this NFR is *runtime evidence*. Both together make a
  FileWatcher self-describing: what it expects (description) and what actually arrived
  (sysout).
- **BMC baseline**: post-execution commands are standard vendor capability
  (`external/orchestration/bmc-controlm/` — file-watcher / job-actions docs); this
  standard constrains *how we use* it, per the two-stage validation model (vendor
  legality → internal conformance).
