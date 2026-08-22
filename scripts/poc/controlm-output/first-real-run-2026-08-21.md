# First run against real logs — sanitized record (2026-08-21)

**What this is.** The PoC parsers in this directory were run for the first time against a real
estate's Control-M Output-tab logs — eleven of them, one data-flow neighbourhood. This file records
what came out, **sanitized**: application ids, flow names, hosts, paths, GUIDs and cluster ids are
replaced by shape-preserving placeholders. It exists because the run answered questions MM7's design
was still guessing at, and those answers should not have to be re-derived.

**Provenance.** Verbatim output, real values, venue and fidelity notes:
`internal-local/controlm-output-logs/first-real-run-2026-08-21/join-hops-run-transcription-2026-08-21.md`
(machine-local, gitignored). Substitution table beside it in `sanitization-map.md`. The run was on the
**company machine's working copy**, not the personal desktop; the per-log JSON records stay there.
Placeholders preserve shape deliberately — the two flow families, the base-vs-`_INTM` sibling relation
and the two-application split are the findings, so they survive the rename.

## The output

```text
== HOPS (by launcher_kind) ==

kind        job pipeline_id  dataflow                   app_id            pro_id_in  prov_guid compute    skips
----        --- -----------  --------                   ------            ---------  --------- -------    -----
PREPROC                                                                                                   finding:bearer_token_printed_to_output(x2)
FILEWATCHER
INGESTION       <PIPELINE-1> FLOW_ALPHA_DATA            <APP_ID-ingest>   <PROV-1>             EKS
TRANSFORM       <PIPELINE-2> FLOW_ALPHA_INTM            <APP_ID-derive>                        EKS
TRANSFORM       <PIPELINE-3> FLOW_ALPHA_OTHER_INTM      <APP_ID-derive>                        alias:test finding:spark.kubernetes.appname=test, finding:spark.namespace.alias=test
TRANSFORM       <PIPELINE-4> FLOW_ALPHA_WHOLESALE_INTM  <APP_ID-derive>                        alias:test finding:spark.kubernetes.appname=test, finding:spark.namespace.alias=test
TRANSFORM       <PIPELINE-5> FLOW_BETA_SNPST_DLY        <APP_ID-derive>                        alias:test finding:spark.kubernetes.appname=test, finding:spark.namespace.alias=test
TRANSFORM       <PIPELINE-6> FLOW_BETA_SNPST            <APP_ID-derive>                        EKS
TRANSFORM       <PIPELINE-7> FLOW_BETA_SNPST            <APP_ID-derive>                        EKS
PROVISION       <PIPELINE-8> FLOW_BETA_SNPST_DLY        <APP_ID-derive>                        GKP
UNKNOWN                                                                                                   kind_unknown

== JOIN 1: watcher fed by a predecessor? (R13 second consequence) ==
watcher              /data/<tenant>/dropbox/<FEED>/flow_alpha_data_20260820.csv
  result             transfer_completed
  verdict            INTERNALLY FED -> load_bearing=false PROPOSED (SME rules; unruled until then)

== JOIN 2: pre-processor files -> placement -datFile/-tokFile ==
  (no PLACEMENT hop)

== JOIN 3: provenance chain (placement provenanceGuid -> ingestion -proId) ==
transform            CHAIN BREAKS: No provenanceId is provided!      [x6]
provision            -proId    (GKP; submission <submission-job-id> on <gkp-cluster>)

  [the "CHAIN BREAKS" wording above is what the tool printed on the day and is
   transcribed as printed; it was WRONG and the tool no longer says it -- see
   "The correction that changes what JOIN 3 means" below]

== JOIN 4: flow identity across hops (%%DATAFLOW as the launcher names it) ==
  FLOW_BETA_SNPST            2 hop(s): TRANSFORM+TRANSFORM   app_id(s): <APP_ID-derive>
  FLOW_BETA_SNPST_DLY        2 hop(s): TRANSFORM+PROVISION   app_id(s): <APP_ID-derive>
  FLOW_ALPHA_DATA            1 hop(s): INGESTION             app_id(s): <APP_ID-ingest>
  FLOW_ALPHA_INTM            1 hop(s): TRANSFORM             app_id(s): <APP_ID-derive>
  FLOW_ALPHA_OTHER_INTM      1 hop(s): TRANSFORM             app_id(s): <APP_ID-derive>
  FLOW_ALPHA_WHOLESALE_INTM  1 hop(s): TRANSFORM             app_id(s): <APP_ID-derive>
  note: sibling flow names under different app_ids are the producer/consumer split; gate section A rules the key.

== JOIN 5: ingest mode (derived, never from the name token) ==
                     api-pull   via /apps/<tenant>/scripts/flow_alpha_api_fetch.ksh  host https://api.<internal-domain>

== FINDINGS / SKIPS ==
  PREPROC            finding:bearer_token_printed_to_output(x2)
  PREPROC            redactions=2 (a secret was printed to job output)
  TRANSFORM          finding:spark.kubernetes.appname=test        [x3, paired with]
  TRANSFORM          finding:spark.namespace.alias=test           [x3]
  UNKNOWN            kind_unknown
```

The six identical transform lines in JOIN 3 and the three paired transform findings are collapsed
with a count here; the transcription carries them one per line as printed.

## What the run settles

1. **Eleven logs, zero parser errors, ten of eleven kinds resolved.** Kind detection off the
   launcher's own line held on real material: PREPROC 1, FILEWATCHER 1, INGESTION 1, TRANSFORM 6,
   PROVISION 1, UNKNOWN 1.
2. **R13's second consequence fires on real data, not just the samples.** The watcher waits on a file
   the same flow's pre-processor wrote, and that pre-processor's derived mode is `api-pull`. The
   name token could not have told anyone this; the resolved command did.
3. **No hop outside placement→ingestion carries the handoff token — six transforms of six.** The
   run made this look like a defect; it is not one. See the correction section below: the guid's
   scope *is* those two jobs, so six-of-six is the token working as designed. What the run does
   establish is the **frequency**: nothing downstream carries it, so nothing downstream can be
   correlated by it.
4. **Compute target is not uniform and not inferable.** EKS on four hops, GKP on the provision hop
   (from the launcher's own assertion), and on three hops the namespace alias resolves to the literal
   string `test`, so `compute_target` reports `alias:test` rather than guessing. The
   *not read* / *unresolvable* / *resolved* distinction earns its place in the record shape.
5. **Two applications, six flow names, one neighbourhood.** The ingested feed sits under one
   application id; every derivative (`_INTM`, `_SNPST`) sits under the other — the producer/consumer
   split, visible in the launcher arguments alone. Gate `data-flow-overview` §A (firm-wide vs
   per-application key) now has real evidence to rule on, and it is evidence *for* the question, not
   an answer to it: the same flow-name family appears under two ids.
6. **The pipeline GUID is per flow name, not per job.** Eight distinct GUIDs across eight launcher
   hops, and where one flow name has two hops (`FLOW_BETA_SNPST`) the GUIDs differ. Identity for the
   flow record cannot be the pipeline GUID.

## The correction that changes what JOIN 3 means

**SME ruling, 2026-08-21.** `provenanceGuid` is **not provenance**. The placement service mints it
**at job run**, and it is used **only between the two jobs that JOIN 3 names** — placement produces
it, the ingestion consuming that placement carries it as `-proId`. It is a run-scoped handoff token.
**It cannot be used to validate Control-M lineage.**

The PoC's original wording got this backwards. It printed `CHAIN BREAKS` at each transform, which
asserts that a chain was supposed to continue and did not. There is no chain to break: a transform
has no handoff to receive. Three things follow, and they are binding on MM7:

1. **Absence downstream is expected, not a defect.** A hop that logs `No provenanceId is provided!`
   is behaving correctly. The extractor still records the absence — it is worth counting — but as an
   expected-absent observation, never as a lineage break or a remediation signal.
2. **The guid must never key an edge, identify a flow, or join hops beyond the pair.** Flow identity
   is the `%%DATAFLOW` name plus the application id (finding 5 below). Using a run-scoped token as a
   graph key would manufacture false lineage that looks authoritative because of what it is called.
3. **The word is a trap in this repo specifically.** DryDocs grounds its edges in PROV-O, where
   *provenance* means derivation history. The vendor's field name collides with that and means
   something much narrower. Anywhere the term crosses from a log into our model it needs the scope
   stated with it.

What the token **is** good for: correlating one placement run to the ingestion run that consumed it,
and reading the landing prefix that carries it. Both are run-level facts, not lineage.

## What the run exposes as gaps

| Gap | Evidence | Next step |
|---|---|---|
| **No PLACEMENT log collected** | JOIN 2 `(no PLACEMENT hop)`, `prov_guid` empty on every row, yet ingestion consumed a `-proId` | collect the placement job's Output tab for this neighbourhood; it is the only hop that *mints* provenance |
| **`job` column empty on every row** | header-block job name never reaches the record, though the bundled samples populate it | parser gap, not a log gap — `Set-HeaderFields` matches a header shape these logs do not use; capture one real header block and widen the pattern |
| **One log matches no kind rule** | `kind_unknown` | characterize its shape; it is the eleventh log and a whole job class may be unrepresented |
| **Ingest mode derived for one hop only** | JOIN 5 shows a single mode | mode is per-flow, and only the PREPROC hop carries the evidence; flows without a PREPROC log resolve to `unknown` with a reason, as designed |

## Two findings that belong to the estate, not to the parser

- **A bearer token is printed into a production job's Output tab, twice.** The parser redacts it in
  its own output and counts it (`redactions=2`), but the secret is in the log itself, readable by
  anyone with the job's Output tab. This is an operational security issue for the owning team to fix
  at the source; it is recorded here as mechanism (a `finding:` category the extractor emits), and
  the real values stay in the machine-local transcription.
- **Three of six transforms run with `spark.kubernetes.appname=test` and
  `spark.namespace.alias=test`.** Whether that is a naming convention or a real misconfiguration is
  an SME question, not a parser question. The extractor's job is to surface it; MM7's coverage
  dataclass should carry it as a first-class finding rather than a skip.

## What this changes for MM7

The PoC was written to frame the field list. It did, and the run amends it:

- `compute_target` needs three states, not two — resolved, alias-unresolved, absent.
- `provenance_guid` / `pro_id_in` are a **placement→ingestion pair correlation**, scoped and
  labelled as such. No chain-status field, no lineage role, no edge. The field's docstring carries
  the scope so the next reader does not re-infer a chain from the name.
- The findings set (`bearer_token_printed_to_output`, `appname=test`, `namespace.alias=test`) is
  separate from the skip-reason set: a *skip* is something the extractor could not do, a *finding* is
  something the extractor did and the estate should look at. `OutputCoverage` should count them
  apart.
- Flow identity is the `%%DATAFLOW` name plus the application id, never the pipeline GUID.
