# Company-side prompt — run the cross-application run_as detection (K25)

> Producer-drafted 2026-08-26 for the company-side assistant. Paste or read whole.
> The producer built the **method** (`drydocs/run_as_detect.py`, tested on synthetic
> rows) and can never run it: the inputs live in psgmgr and the id-owner listing,
> which this repo does not hold and must not hold. What comes back is **counts
> only** — `RunAsDetection.as_dict()` holds ints, booleans and str→int maps, so a
> row dump is unexpressible; job-TYPE strings (TASK_TYPE vocabulary) are the one
> deliberate non-count content. Never return an account, folder or application id.
>
> This is the measurable half of the fid-identity-and-scope gate's §G
> registration-vs-attribution problem (the gate SIGNED 2026-08-19; the §G MALCOLM
> counterexample proved one instance — this measures the CLASS). Its numbers are
> the evidence a **K17** §D/§G ruling and any cross-application-edge amendment
> would cite. Nothing here writes the graph.

Venue: company `<org>/DryDocs`, current `main`. Name the venue in every claim (J18).

## Step 0 — the inputs, all from surfaces doc 09 already specifies

1. **Jobs, per JOB** (never per folder — the class splits inside folders):
   doc 09 **S2**'s grain: `OWNER`, `TASK_TYPE`, and the folder name
   (`T.SCHED_TABLE`), current versions only. Feed each row as
   `JobRow(run_as=OWNER, job_type=TASK_TYPE, folder=SCHED_TABLE)`.
2. **`directory_application`** — the id-owner listing (doc 09 Source B):
   account → the directory's application assignment. Normalize case on BOTH
   sides of the name join before feeding (the K16 rider's correction (3));
   surviving `case_only_mismatches` are then real spelling differences.
3. **`folder_attribution`** — folder → confirmed application attribution, from
   the K8 app-code mapping store. Leave unconfirmed folders OUT: their jobs
   land in `unresolvable_by_reason.folder_unattributed`, which is the honest
   number.
4. **`platform_accounts`** — the SME-confirmed platform-user set. Doc 09 **S3**
   (owners ranked by application/folder spread) produces the candidate list;
   the SME confirms or corrects the top of it. **How a platform account is
   recognized is a K17 ruling the method does not preempt** — this parameter is
   the seam; today the confirmed-list route is the standing evidence-backed
   proposal. The 171-way Control-M platform name belongs here (it IS also in
   the directory — the detector counts that overlap and platform class wins).
5. **`rulings`** — optional; per different-application CASE
   (`(account, attributed_application)` pair), one of `different_subjects` /
   `stale_directory` / `wrong_attribution`. Leave empty on the first run:
   every case parks in `unruled`, and the unruled count is itself a deliverable.

## Step 1 — run it

```python
from drydocs.run_as_detect import JobRow, run_as_detection

result = run_as_detection(
    jobs,
    directory_application=directory_application,
    folder_attribution=folder_attribution,
    platform_accounts=platform_accounts,
)
print(result.as_dict())  # counts only — safe to hand back
assert result.reconciles()
```

## Step 2 — what to hand back, and how to read it

- **`jobs_by_class` / `accounts_by_class`** — the first cut. The platform
  share of the estate is a number nobody has; it is a headline, not a footnote.
- **`class_by_job_type`** — FileWatcher × platform is the DESIGNED pattern;
  `platform_payload_anomaly` (a payload job running as the platform) is the
  countable anomaly, broken down by job type.
- **`outcomes_by_job` / `outcomes_by_account`** — same / different /
  unresolvable, application-class jobs only (platform jobs are expected to
  disagree by construction and are never compared).
- **`different_application_cases` + `cases_by_reading`** — the §G5 split. Every
  case starts `unruled`; a human rules each; re-run with `rulings` filled as
  they land. Never infer a reading.
- **`reconciles`** must be true; if it is not, report that instead of the numbers.

Paste the `as_dict()` JSON (it is counts-only by construction) plus: the venue
line, which extract dates fed inputs 1–3, and how `platform_accounts` was
filled (S3-ranked + SME-confirmed, or otherwise — that detail is evidence for
the K17 recognition ruling).
