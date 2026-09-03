"""Control-M API-call framework — the call surface the deploy/pull shell
scripts invoke (G96).

CONVENTION NOTE — read before extending (this is the G96 clause-(a) record;
the README beside the sample config carries the same rules):

* **The .sh stays GENERIC.** Wrapper scripts (company-side:
  ``controlm_common.sh`` / ``controlm_deploy_lite.sh`` /
  ``controlm_folder_pull.sh``) never hardcode directories, hosts, or call
  syntax. They stage inputs, invoke ``python -m
  drydocs_core.adapters.controlm.api <operation>``, test the exit code, and
  move outputs. Everything environment-specific comes from CONFIG.
* **In/out directories resolve from the data root**, never from the repo
  tree: pull output lands in :func:`drydocs_core.data_root
  .remediation_incoming_dir`, deploy input stages in
  :func:`~drydocs_core.data_root.remediation_outgoing_dir` (both under
  ``DRYDOCS_DATA_ROOT``; logs under ``DRYDOCS_LOGDIR``). The config may
  override either path; blank means the data-root default.
* **The filled config is never committed.** The committed artifact is
  ``controlm_api.sample.cfg`` (mechanism-only placeholders). The filled copy
  lives OUTSIDE the tree at ``<DRYDOCS_DATA_ROOT>/controlm-api/
  controlm_api.cfg`` (or wherever ``DRYDOCS_CONTROLM_API_CFG`` points) —
  company-side its home is the vendor-namespaced scripts directory beside
  the adapters. Real endpoints, hostnames, and credentials never enter this
  tree (classification boundary; secrets discipline). Authentication is
  delegated to ``ctm environment`` (token in ``~/.ctm/env.json``) — this
  framework never reads or writes a credential.
* **Call shapes are config templates where the corpus lacks verified
  syntax.** ``API-CALLS.md`` (beside this module) is the discovery
  reference: per operation, the corpus-grounded tool, its provenance, and
  its availability at the target version. An operation with no verified
  template and no grounded default is a REPORTED capability gap (exit code
  3), never a silent fallback — the G96 clause-(d) guardrail. A template
  whose tool the host cannot START (not on PATH, not executable) is a
  fourth outcome, exit code 4, reported through the same JSON channel
  (G133): the operation is supported and configured, so it is neither a
  config error nor a capability gap, and the tool never ran, so it is not
  a run failure either.

Target environment: Control-M **9.0.21.300, XML-first** — the JSON/SaaS
Automation API corpus files are conceptual reference only, and XML
definition files are deprecated-but-fully-supported at this version
(``controlm-xml-definition-format.md``).
"""

from __future__ import annotations

import argparse
import configparser
import json
import os
import string
import subprocess
import sys
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from drydocs_core.data_root import (
    remediation_incoming_dir,
    remediation_outgoing_dir,
    source_dir,
)

TARGET_VERSION = "9.0.21.300"
CFG_ENV = "DRYDOCS_CONTROLM_API_CFG"

# availability tiers at TARGET_VERSION (see API-CALLS.md for the per-call story)
GROUNDED_PARAMS = "grounded-params"  # corpus documents the parameter set
GROUNDED_NAME = "grounded-name"  # corpus names the tool; syntax unverified
API_UNVERIFIED = "api-unverified"  # compatible on paper; install unverified
NO_CORPUS = "no-corpus"  # no corpus ground truth — capability gap

# exit codes the wrapper .sh tests
EXIT_OK = 0
EXIT_RUN_FAILED = 1
EXIT_CONFIG = 2
EXIT_CAPABILITY_GAP = 3
# G133: the tool the template names could not be started — not on PATH, or not
# executable. Its own code because the other three each say something false
# about it: 1 claims the tool ran, 2 claims the config is wrong, 3 claims the
# capability is missing. The wrapper's `*) fail` arm already covers it.
EXIT_NOT_RUNNABLE = 4


@dataclass(frozen=True)
class Operation:
    """One per-object call the framework exposes, with its provenance."""

    name: str
    transport: str  # em-xml-utility | server-utility | automation-api
    tool: str
    availability: str
    corpus_source: str
    version_note: str
    default_template: str | None = None  # only when the corpus grounds it


OPERATIONS: dict[str, Operation] = {
    op.name: op
    for op in (
        Operation(
            "api_probe",
            "automation-api",
            "ctm",
            API_UNVERIFIED,
            "controlm-api-installation.md",
            f"Monthly API compatible 'Control-M 9.0.20 and higher' — {TARGET_VERSION} "
            "in range; emrestsrv install/endpoint/token unverified company-side (OQ-1)",
            default_template="ctm config servers::get",
        ),
        Operation(
            "folder_export",
            "em-xml-utility",
            "exportdeffolder",
            GROUNDED_NAME,
            "controlm-planning-utils.md; controlm-xml-definition-format.md",
            f"XML deprecated from 9.0.21.100 but fully supported until 9.0.22 — "
            f"{TARGET_VERSION} inside the supported window; exact syntax = corpus gap "
            "(DTDs live on the EM under Default/data/Resource)",
        ),
        Operation(
            "folder_deploy",
            "em-xml-utility",
            "deffolder",
            GROUNDED_NAME,
            "controlm-planning-utils.md; controlm-xml-definition-format.md",
            f"same XML supported-but-deprecated window as folder_export at "
            f"{TARGET_VERSION}; syntax unverified",
        ),
        Operation(
            "folder_define",
            "server-utility",
            "ctmdeffolder",
            GROUNDED_PARAMS,
            "controlm-ctmdeffolder-utility.md",
            f"SMART folders only; parameter grain documented (SaaS doc applied to "
            f"{TARGET_VERSION} — verify divergence on the EM)",
        ),
        Operation(
            "job_export",
            "em-xml-utility",
            "exportdefjob",
            GROUNDED_NAME,
            "controlm-xml-definition-format.md; controlm-planning-utils.md",
            f"exports job definitions from the EM database to an output file; XML "
            f"supported-but-deprecated at {TARGET_VERSION}",
        ),
        Operation(
            "job_deploy",
            "em-xml-utility",
            "defjob",
            GROUNDED_NAME,
            "controlm-xml-definition-format.md; controlm-planning-utils.md",
            "reads job processing definitions from a plain text input file written "
            f"in XML format; supported-but-deprecated at {TARGET_VERSION}",
        ),
        Operation(
            "job_define",
            "server-utility",
            "ctmdefine",
            GROUNDED_PARAMS,
            "controlm-ctmdefine-utility.md",
            f"parameter grain documented incl. -INCOND/-OUTCOND/-VARIABLE (SaaS doc "
            f"applied to {TARGET_VERSION} — verify divergence on the EM)",
        ),
        Operation(
            "job_update",
            "em-xml-utility",
            "updatedef",
            GROUNDED_NAME,
            "controlm-planning-utils.md",
            f"named in corpus at high level only; syntax unverified at {TARGET_VERSION}",
        ),
        Operation(
            "variable_set",
            "server-utility",
            "ctmvar",
            GROUNDED_NAME,
            "controlm-variables.md",
            "corpus grounds only that Global variables are created/modified via "
            f"ctmvar; full syntax = corpus gap at {TARGET_VERSION}",
        ),
        Operation(
            "calendar_export",
            "em-xml-utility",
            "exportdefcal",
            GROUNDED_NAME,
            "controlm-planning-utils.md; controlm-calendars.md",
            f"named in corpus at high level only; syntax unverified at {TARGET_VERSION}",
        ),
        Operation(
            "calendar_deploy",
            "em-xml-utility",
            "defcal",
            GROUNDED_NAME,
            "controlm-planning-utils.md; controlm-calendars.md",
            f"named in corpus at high level only; syntax unverified at {TARGET_VERSION}",
        ),
        Operation(
            "calendar_copy",
            "em-xml-utility",
            "copydefcal",
            GROUNDED_NAME,
            "controlm-planning-utils.md",
            f"named in corpus at high level only; syntax unverified at {TARGET_VERSION}",
        ),
        Operation(
            "condition_add",
            "server-utility",
            "(runtime condition add)",
            NO_CORPUS,
            "— (no corpus ground truth)",
            "no runtime condition utility appears in the corpus; definition-grain "
            "in/out conditions ride -INCOND/-OUTCOND on job_define/folder_define — "
            f"runtime add at {TARGET_VERSION} is a REPORTED capability gap",
        ),
        Operation(
            "condition_remove",
            "server-utility",
            "(runtime condition remove)",
            NO_CORPUS,
            "— (no corpus ground truth)",
            "no runtime condition utility appears in the corpus — runtime remove at "
            f"{TARGET_VERSION} is a REPORTED capability gap",
        ),
    )
}


@dataclass(frozen=True)
class ApiConfig:
    """Parsed framework config; ``templates`` maps operation → call template."""

    endpoint: str = ""
    environment_name: str = ""
    auth: str = "token"
    pull_out_dir: Path = field(default_factory=remediation_incoming_dir)
    deploy_in_dir: Path = field(default_factory=remediation_outgoing_dir)
    templates: Mapping[str, str] = field(default_factory=dict)
    source_path: Path | None = None


def default_config_path() -> Path:
    """Filled-config home: ``DRYDOCS_CONTROLM_API_CFG`` > data-root default."""
    raw = os.environ.get(CFG_ENV, "").strip()
    return Path(raw) if raw else source_dir("controlm-api") / "controlm_api.cfg"


def load_config(path: str | Path | None = None) -> ApiConfig:
    """Parse the cfg at ``path`` (default: :func:`default_config_path`).

    A missing file is not an error — every setting has a mechanism default —
    but a *named* path that does not exist raises so a mistyped
    ``DRYDOCS_CONTROLM_API_CFG`` never silently falls back.
    """
    cfg_path = Path(path) if path is not None else default_config_path()
    named = path is not None or bool(os.environ.get(CFG_ENV, "").strip())
    parser = configparser.ConfigParser()
    if cfg_path.is_file():
        parser.read(cfg_path, encoding="utf-8")
    elif named:
        raise FileNotFoundError(f"Control-M API config not found: {cfg_path}")

    env = parser["environment"] if parser.has_section("environment") else {}
    paths = parser["paths"] if parser.has_section("paths") else {}
    pull_raw = (paths.get("pull_out_dir") or "").strip()
    deploy_raw = (paths.get("deploy_in_dir") or "").strip()
    templates = (
        {k: v.strip() for k, v in parser["calls"].items() if v.strip()}
        if parser.has_section("calls")
        else {}
    )
    return ApiConfig(
        endpoint=(env.get("endpoint") or "").strip(),
        environment_name=(env.get("environment_name") or "").strip(),
        auth=(env.get("auth") or "token").strip(),
        pull_out_dir=Path(pull_raw) if pull_raw else remediation_incoming_dir(),
        deploy_in_dir=Path(deploy_raw) if deploy_raw else remediation_outgoing_dir(),
        templates=templates,
        source_path=cfg_path if cfg_path.is_file() else None,
    )


@dataclass(frozen=True)
class PlannedCall:
    """A rendered call the wrapper can execute — or a reported gap."""

    operation: Operation
    argv: tuple[str, ...]
    in_dir: Path
    out_dir: Path
    capability_gap: bool = False
    gap_reason: str = ""


@dataclass
class CallResult:
    """Machine-readable outcome — the JSON contract the .sh layer parses."""

    ok: bool
    operation: str
    transport: str
    availability: str
    argv: tuple[str, ...]
    in_dir: str
    out_dir: str
    capability_gap: bool
    message: str
    returncode: int | None = None
    #: the call never started (G133) — ``returncode`` is None and ``message``
    #: carries the OS error; distinct from a call that ran and failed
    not_runnable: bool = False

    def to_json(self) -> str:
        payload = dict(self.__dict__)
        payload["argv"] = list(self.argv)
        payload["target_version"] = TARGET_VERSION
        return json.dumps(payload, sort_keys=True)

    @property
    def exit_code(self) -> int:
        if self.capability_gap:
            return EXIT_CAPABILITY_GAP
        if self.not_runnable:
            return EXIT_NOT_RUNNABLE
        return EXIT_OK if self.ok else EXIT_RUN_FAILED


def _render(template: str, params: Mapping[str, str]) -> tuple[str, ...]:
    fields = {f for _, f, _, _ in string.Formatter().parse(template) if f is not None}
    missing = sorted(f for f in fields if f not in params)
    if missing:
        raise KeyError(f"call template needs parameters not supplied: {', '.join(missing)}")
    return tuple(template.format(**params).split())


def plan(operation: str, config: ApiConfig | None = None, /, **params: str) -> PlannedCall:
    """Resolve ``operation`` to a :class:`PlannedCall` under ``config``.

    Resolution order: a ``NO_CORPUS`` operation is always a gap; else the
    config ``[calls]`` template wins; else the corpus-grounded default; else
    a reported gap (clause d — never a silent fallback).
    """
    if operation not in OPERATIONS:
        raise KeyError(f"unknown operation {operation!r} — known: {', '.join(sorted(OPERATIONS))}")
    cfg = config if config is not None else load_config()
    op = OPERATIONS[operation]
    base = {
        "in": str(cfg.deploy_in_dir),
        "out": str(cfg.pull_out_dir),
        "endpoint": cfg.endpoint,
        "environment": cfg.environment_name,
    }
    base.update(params)

    def gap(reason: str) -> PlannedCall:
        return PlannedCall(op, (), cfg.deploy_in_dir, cfg.pull_out_dir, True, reason)

    if op.availability == NO_CORPUS:
        return gap(op.version_note)
    template = cfg.templates.get(operation) or op.default_template
    if not template:
        return gap(
            f"no verified call template for {operation!r} at {TARGET_VERSION} "
            f"({op.availability}; tool {op.tool}) — fill [calls] {operation} in "
            "the config from syntax verified on your EM (see API-CALLS.md)"
        )
    return PlannedCall(op, _render(template, base), cfg.deploy_in_dir, cfg.pull_out_dir)


Runner = Callable[[tuple[str, ...]], "subprocess.CompletedProcess[str]"]


def _default_runner(argv: tuple[str, ...]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(  # — argv comes from the operator's own config
        argv, capture_output=True, text=True, check=False
    )


def execute(planned: PlannedCall, runner: Runner | None = None) -> CallResult:
    """Run a planned call (or report its gap) and return the JSON-able result."""
    op = planned.operation
    common = dict(
        operation=op.name,
        transport=op.transport,
        availability=op.availability,
        argv=planned.argv,
        in_dir=str(planned.in_dir),
        out_dir=str(planned.out_dir),
    )
    if planned.capability_gap:
        return CallResult(ok=False, capability_gap=True, message=planned.gap_reason, **common)
    try:
        proc = (runner or _default_runner)(planned.argv)
    except OSError as exc:
        # G133: subprocess.run raises OSError (FileNotFoundError, PermissionError)
        # only when the child cannot be STARTED — once it runs, its outcome is a
        # returncode. Before this, the exception escaped main() as a traceback
        # with no JSON on stdout, which the wrapper .sh cannot parse.
        return CallResult(
            ok=False,
            capability_gap=False,
            not_runnable=True,
            message=f"cannot start {planned.argv[0]!r}: {exc}",
            **common,
        )
    ok = proc.returncode == 0
    tail = (proc.stdout if ok else (proc.stderr or proc.stdout) or "").strip()
    return CallResult(
        ok=ok,
        capability_gap=False,
        message=tail[-2000:],
        returncode=proc.returncode,
        **common,
    )


def main(argv: list[str] | None = None, *, runner: Runner | None = None) -> int:
    """CLI entry for the wrapper .sh: JSON on stdout, exit code per contract
    (0 ok · 1 run failed · 2 config/usage · 3 reported capability gap ·
    4 tool not runnable).

    ``runner`` is the same seam :func:`execute` exposes, threaded through so a
    test can drive the RUN path of the entry point and not only ``--plan-only``
    (G133 clause e — every CLI test used the planning path, which is how the
    missing-binary traceback went unnoticed). The .sh never passes it.
    """
    ap = argparse.ArgumentParser(
        prog="drydocs-controlm-api",
        description=f"Control-M API-call framework (target {TARGET_VERSION})",
    )
    ap.add_argument("operation", choices=sorted(OPERATIONS))
    ap.add_argument("--cfg", help="config path (else DRYDOCS_CONTROLM_API_CFG)")
    ap.add_argument(
        "-p",
        "--param",
        action="append",
        default=[],
        metavar="KEY=VALUE",
        help="template parameter, repeatable",
    )
    ap.add_argument(
        "--plan-only",
        action="store_true",
        help="render and report the call without executing it",
    )
    ns = ap.parse_args(argv)
    try:
        params = dict(p.split("=", 1) for p in ns.param)
    except ValueError:
        ap.error("--param takes KEY=VALUE")
    try:
        cfg = load_config(ns.cfg)
        planned = plan(ns.operation, cfg, **params)
    except (FileNotFoundError, KeyError, configparser.Error) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stdout)
        return EXIT_CONFIG
    if ns.plan_only:
        result = CallResult(
            ok=not planned.capability_gap,
            operation=planned.operation.name,
            transport=planned.operation.transport,
            availability=planned.operation.availability,
            argv=planned.argv,
            in_dir=str(planned.in_dir),
            out_dir=str(planned.out_dir),
            capability_gap=planned.capability_gap,
            message=planned.gap_reason if planned.capability_gap else "plan only",
        )
    else:
        result = execute(planned, runner=runner)
    print(result.to_json())
    return result.exit_code


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
