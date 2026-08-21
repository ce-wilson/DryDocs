# Control-M Output-tab log parsers — proof of concept (frames MM7)

**What this is.** Throwaway-grade PowerShell that reads one Control-M job *Output* log and pulls
out the metadata each hop of a DPL data flow contributes — the second iteration of the
command-line lineage (`G15/G16` read the command line; this reads what the launcher *did* with
it). It exists to make the log patterns visible and debuggable before the real extractor
(`drydocs_lineage/extractors/controlm_output.py`, backlog **MM7**) is written. One script per
job shape, on purpose: each file's header lists the exact lines it matches.

**What it is not.** Not a component, not imported by anything, writes no graph. Mechanism only:
the scripts carry no host names, application ids, or people; the bundled samples are synthetic.

## Run it

```powershell
# one log, as a field/value table
.\Parse-ControlMOutput.ps1 -Path C:\path\to\job.log -AsTable

# a folder of logs -> one JSON per log, then the cross-hop joins
.\Parse-ControlMOutput.ps1 -Path ..\..\..\internal-local\controlm-output-logs -OutDir ..\..\..\internal-local\controlm-output-logs\parsed
.\Join-Hops.ps1 -JsonDir ..\..\..\internal-local\controlm-output-logs\parsed

# the bundled synthetic samples (safe to commit; real logs never are)
.\Parse-ControlMOutput.ps1 -Path .\samples -OutDir $env:TEMP\poc-out ; .\Join-Hops.ps1 -JsonDir $env:TEMP\poc-out
```

Real logs go under `internal-local/controlm-output-logs/` (git-ignored). Copy the Output tab text
into a `.log`/`.txt` file; the panel's soft-wrap marker (trailing `\`) is handled.

## The job shapes and what each contributes

| Script | Detected by | Fields this hop owns |
|---|---|---|
| `Parse-Preproc.ps1` | `.ksh` launcher + `curl` / bearer-token lines | **ingest mode** (`api-pull` from the resolved command, never the name token), the three files it writes (`_original_` csv, `.tok`, trailer-stripped csv), API host (query string dropped), the curl failure signature; **redacts** the bearer token it prints and counts it |
| `Parse-FileWatcher.ps1` | `+ ctmfw …` | watched path, result (`transfer_completed` / exists / none), size, token-vs-data role |
| `Parse-Placement.ps1` | `Identified 'PLACEMENT' Job` | **produces the `provenanceGuid`**, dat/tok file args, landing targets (`MERCURY_S3`, `AWS_S3`), landing prefix `<APP_ID>/raw/<flow>/<guid>/` |
| `Parse-Ingestion.ps1` | `Identified 'INGESTION' Job` | **consumes `-proId`**, `-dataflow` vs task-request `DataFlow` (agreement checked), `-seal` vs `spark.kubernetes.seal`, image digest, compute target from the namespace alias, `task_request_closed` |
| `Parse-Transform.ps1` | `Identified 'TRANSFORM' Job` | same as ingestion plus `provenance_warning` (*No provenanceId is provided!* — the chain breaks here) and the `appname=test` finding |
| `Parse-Provision.ps1` | `Identified 'PROVISION' Job. Provision jobs execute on GKP not EKS!` | compute target **GKP** from the launcher's own line, v2 submission URL, response `jobID` / `httpStatus` / `cluster`, GKP credential key |

Every parser emits the same record (`Common.ps1 → New-Result`). A field a log does not carry is
`null` — *not read* stays distinguishable from *empty* (gate `data-flow-overview` §C). Anything
the parser could not do is a counted `skip_reasons` entry (`no_launcher_banner`, `truncated_json`,
`guid_mismatch_vs_cmdline`, `kind_unknown`, `no_pro_id_on_command_line`, …) — the same reason set
MM7's `OutputCoverage` dataclass will carry.

## What `Join-Hops.ps1` derives (the data-flow record's DERIVED fields)

1. **Watcher fed by a predecessor?** `FILEWATCHER.watched_path == PREPROC.data_files[*]` →
   *internally fed* → `load_bearing=false` **proposed** (R13's second consequence; the SME rules,
   `unruled` until then).
2. **Pre-processor files → placement `-datFile`/`-tokFile`.**
3. **Provenance chain:** `PLACEMENT.provenance_guid == INGESTION.pro_id_in` → MATCH/MISMATCH;
   a TRANSFORM with the warning is reported as the break.
4. **Flow identity across hops** by `dataflow`, with the app ids seen — sibling flow names under
   different app ids are the producer/consumer split the gate's §A key ruling decides.
5. **Ingest mode**, derived; `unknown` printed as a value when no PREPROC log was supplied.

## Known simplifications (deliberate, PoC)

- Kind detection is one rule; a log with no `Identified` line and no `ctmfw`/`.ksh` is `UNKNOWN`.
- The task-service JSON is key-scraped line by line because the panel often cuts it; nested
  objects are flattened.
- Join keys are exact string matches on paths/GUIDs; no normalization of case or trailing slashes.
- Windows PowerShell 5.1: ASCII-only source (an em dash in a BOM-less `.ps1` is a parse error),
  no `$args`/`$pid` as variable names (automatic variables), `[AllowEmptyString()]` on every
  `string[]` parameter because logs have blank lines.
