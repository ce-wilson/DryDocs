# Control-M API-call framework (G96)

The per-object call surface the Control-M deploy/pull shell scripts invoke.
The scripts stay **generic**; everything environment-specific comes from
config. This README is the clause-(a) convention note; `api.py`'s module
docstring carries the same rules, and `API-CALLS.md` is the clause-(c)
discovery reference.

## The convention that keeps the .sh generic

1. **Division of labor.** The wrapper `.sh` (company-side:
   `controlm_common.sh`, `controlm_deploy_lite.sh`, `controlm_folder_pull.sh`
   — they live in the vendor-namespaced scripts directory beside the
   adapters and never enter this repo) handles input/output: stage files,
   call `python -m drydocs_core.adapters.controlm.api <operation>`, test the
   exit code, parse the one-line JSON result, move outputs. The Python layer
   owns call resolution, the availability guardrail, and the machine-readable
   result.
2. **Directories come from config, never hardcoded.** Defaults resolve from
   `drydocs_core.data_root` under `DRYDOCS_DATA_ROOT`: pull output →
   `remediation/incoming`, deploy input → `remediation/outgoing` (the G96
   driving scenario), Control-M XML ingestion exports → `controlm-xml`; logs
   under `DRYDOCS_LOGDIR`. The `[paths]` section may override either
   direction; blank means the data-root default.
3. **Sample committed, filled config never.** `controlm_api.sample.cfg` is
   the committed mechanism artifact. The filled copy lives out-of-tree at
   `<DRYDOCS_DATA_ROOT>/controlm-api/controlm_api.cfg` (or
   `DRYDOCS_CONTROLM_API_CFG`). No real endpoints, hostnames, or credentials
   in tracked files — authentication is delegated to `ctm environment`
   (token in `~/.ctm/env.json`); the framework never touches a credential.
4. **Unavailable calls are reported, not faked.** The target environment is
   Control-M **9.0.21.300, XML-first**. Where the reference corpus does not
   ground a call's syntax, the operation resolves only through a
   config-supplied template the operator verified on their EM; with no
   template it exits **3** (reported capability gap). Runtime in/out-condition
   add/remove has no corpus ground truth at all and always reports the gap —
   definition-grain conditions ride `-INCOND`/`-OUTCOND` on
   `job_define`/`folder_define`.

## Exit-code contract (what the .sh tests)

| Code | Meaning |
|---|---|
| 0 | call ran, returncode 0 |
| 1 | call ran and failed |
| 2 | config/usage error (bad path, unknown operation, missing template parameter) |
| 3 | reported capability gap — no verified call shape at 9.0.21.300 |

One JSON object on stdout either way: `ok`, `operation`, `transport`,
`availability`, `argv`, `in_dir`, `out_dir`, `capability_gap`, `message`,
`returncode`, `target_version`.

## Example wrapper shape (generic — the whole point)

```sh
result=$(python -m drydocs_core.adapters.controlm.api folder_export \
  -p name="$FOLDER" -p server="$CTM_SERVER") || rc=$?
case "${rc:-0}" in
  0) mv_outputs_from "$(echo "$result" | jq -r .out_dir)" ;;
  3) log "capability gap: $(echo "$result" | jq -r .message)" ;;
  *) fail "$result" ;;
esac
```
