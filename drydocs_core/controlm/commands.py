r"""Shell-command parser + launcher registry (Phase C).

Parses the executable side of a job — PRECMD/POSTCMD shell text
(EMBEDDED_SHELL variables), container-override commands (UCM), and OS
CMD_LINE — into typed STG_INVOCATION and STG_FILE_OP rows. Operates on
RESOLVED values (Phase B), so %%vars are already substituted and only
symbolic {ODATE}-style tokens remain.

Design (vendor: controlm-os-job-parameters.md, controlm-api-job-types.md):
  * A command line is split into statements on ``;`` (shell separators),
    respecting single/double quotes.
  * Each statement is tokenized (shlex, POSIX) to argv. argv[0] is the
    verb. Wrapper verbs (sh/bash/ksh/sh -c) are unwrapped to the real
    target. Interpreter is inferred by extension (.sh/.py/.pl/.m) per the
    job-types doc.
  * File-op verbs (mkdir/cp/mv/rm/rmdir/chmod/rename/ln/sed/gzip) -> STG_FILE_OP.
    The set matches the vendor's pre/post-transfer command list
    (controlm-file-transfer-job.md: chmod, mkdir, rename, rm, rmdir); gzip/gunzip
    added for the pure-file-ops wrapper case the 2026-07-15 lineage gate caveat
    names ("unix file operations (move, gzip) with no ETL engine involved"; G14).
  * Everything else dispatches through LAUNCHER_REGISTRY to an
    invocation_type; unmatched executables -> UNKNOWN (the Phase-E backlog).

The registry is intentionally data-driven: growing coverage means adding a
rule, not editing parser logic.
"""
from __future__ import annotations

import re
import shlex
from dataclasses import dataclass, field

# --- launcher registry --------------------------------------------------------

# Each rule: (compiled pattern on the executable BASENAME, invocation_type,
# rule-id for STG_INVOCATION.classifier_rule). First match wins. Seeded from
# observed production commands; extend here as the unparsed backlog reveals
# new launchers (Phase E).
LAUNCHER_REGISTRY: list[tuple[re.Pattern, str, str]] = [
    (re.compile(r"\.m$"),                       "ABINITIO",       "abinitio.graph_or_plan"),
    (re.compile(r"\.pset$"),                    "ABINITIO",       "abinitio.pset"),
    (re.compile(r"^m_\w+", re.I),               "INFORMATICA",    "informatica.mapping_prefix"),
    (re.compile(r"^pmcmd$", re.I),              "INFORMATICA",    "informatica.pmcmd"),
    # the canonical Informatica wrapper launcher (v2 standard templates 6.4/6.5;
    # G16 — previously fell through to the generic .ksh shell rule)
    (re.compile(r"^ICDW_etl_run_interface\.ksh$", re.I), "INFORMATICA", "informatica.icdw_run_interface"),
    (re.compile(r"^run_data_validation\.sh$"),  "VALIDATION_UTIL","validation.run_data_validation"),
    (re.compile(r"^run_calp_temp\.sh$"),        "VALIDATION_UTIL","validation.run_calp_temp"),
    # DPL data-pipeline accelerators. SME 2026-07-16 (gate-log cmdline-lineage-review):
    # DPL is NOT Ab Initio — java zilo ETL framework originally; a -py flag routes to
    # a java-spark/pyspark framework. Common path /apps/tenants/dpl_utils/dt-accelerators/;
    # the launcher spelling observed is dt-launcher.sh (dtlaunch.sh kept as a variant).
    (re.compile(r"^dt-?launch(er)?\.sh$", re.I), "DPL",           "dpl.dt_launcher_accelerator"),
    (re.compile(r"^dt-pipelines-launcher.*\.jar$", re.I), "DPL",  "dpl.pipelines_launcher_jar"),
    # on-prem shell launcher spelling (dpl_processor/bin; extensionless; the
    # _dynamic variant adds spark-params passthrough) — same DPL kind (G15,
    # 2026-07-21 prod samples + variable gap analysis: live folder vars carry it)
    (re.compile(r"^dpl_spark_processor(_dynamic)?$", re.I), "DPL", "dpl.spark_processor_onprem"),
    (re.compile(r"^air$", re.I),                "ABINITIO",       "abinitio.air_cli"),
    (re.compile(r"^java$", re.I),               "JAVA",           "java.interpreter"),
    (re.compile(r"runscript\.sh$", re.I),       "SHELL_SCRIPT",   "abioncloud.runscript_wrapper"),
    (re.compile(r"^(spark-submit|pyspark)$"),   "PYSPARK",        "pyspark.spark_submit"),
    (re.compile(r"python[0-9.]*$"),             "PYTHON",         "python.interpreter"),
    (re.compile(r"\.py$"),                      "PYTHON",         "python.script"),
    (re.compile(r"\.(sh|ksh|bash)$"),           "SHELL_SCRIPT",   "shell.script"),
    (re.compile(r"\.(pl)$"),                    "SHELL_SCRIPT",   "perl.script"),
    (re.compile(r"^(sftp|ftp|scp|aft)$", re.I), "FILE_TRANSFER",  "transfer.client"),
]

# shell verbs that ARE file operations -> STG_FILE_OP (not invocations)
_FILE_OP_VERBS: dict[str, str] = {
    "cp": "COPY", "scp": "COPY",
    "mv": "MOVE", "rename": "MOVE",
    "rm": "DELETE", "rmdir": "DELETE",
    "mkdir": "MKDIR",
    "sed": "TRANSFORM", "awk": "TRANSFORM", "tr": "TRANSFORM",
    "gzip": "COMPRESS", "gunzip": "COMPRESS",
    "chmod": "OTHER", "chown": "OTHER", "ln": "OTHER", "touch": "OTHER",
}
# verbs that are neither invocation nor file-op (control/no-op) — skipped
_NOOP_VERBS = {"cd", "cc", "echo", "ls", "set", "export", "true", "wait", "TZ=",
               "fi", "done", "exit", "[[", "]]", "[", "test", ":"}
# wrapper verbs whose real target is a later token
_WRAPPER_VERBS = {"sh", "bash", "ksh", "zsh", "csh", "env", "nohup", "exec", "time"}
_WRAPPER_FLAGS = {"-c", "-e", "-x", "-eu", "-ex", "-l"}
# shell control keywords that PREFIX a real statement after `;`-splitting
# (`if [[ $? > 0 ]]; then exit 1;else sh wrapper.sh …;fi` — without stripping,
# the `else`-prefixed statement carries the job's MAIN invocation but parses
# UNKNOWN under verb `else`)
_CONTROL_PREFIX_VERBS = {"if", "then", "else", "elif", "do"}


@dataclass(frozen=True)
class Invocation:
    """One executable launch, ready for STG_INVOCATION."""

    invocation_type: str
    executable_path: str | None
    script_path: str | None
    config_path: str | None
    args: tuple[str, ...]
    raw_command: str
    is_classified: bool
    classifier_rule: str | None

    @property
    def target(self) -> str:
        """Best identifier for the launched artifact: script, else executable,
        else the raw statement — what lineage/deepdoc key the child node on.
        (Folded from the depgraph prototype at the G9 re-home, ADR 0002-C §3 —
        the fold's API delta; shared by C2/C3, so it lives in core.)"""
        return self.script_path or self.executable_path or self.raw_command


@dataclass(frozen=True)
class FileOp:
    """One file operation, ready for STG_FILE_OP."""

    op_type: str
    src_pattern: str | None
    tgt_pattern: str | None
    raw_statement: str


@dataclass
class ParsedCommand:
    invocations: list[Invocation] = field(default_factory=list)
    file_ops: list[FileOp] = field(default_factory=list)
    unparsed: list[str] = field(default_factory=list)


def _strip_outer_quotes(command: str) -> str:
    """Strip a single fully-enclosing quote pair.

    Production PRECMD/POSTCMD values frequently wrap the whole shell string
    in double quotes (``"cc x; sed y; mv z"``) — without stripping, the
    semicolons hide inside one quoted span and never split. Only strips when
    the opening quote's match is the final character, so ``'a';'b'`` (two
    separate quoted spans) is left intact.
    """
    s = command.strip()
    if len(s) >= 2 and s[0] in "'\"":
        q = s[0]
        i = 1
        while i < len(s):
            if s[i] == q:
                break
            i += 1
        if i == len(s) - 1:
            return s[1:-1]
    return command


def split_statements(command: str) -> list[str]:
    """Split a command line into statements on ``;``, respecting quotes and
    treating ``&&`` / ``||`` / ``|`` as separators too. Empty fragments are
    dropped."""
    command = _strip_outer_quotes(command)
    out: list[str] = []
    buf: list[str] = []
    quote: str | None = None
    i = 0
    n = len(command)
    while i < n:
        ch = command[i]
        if quote:
            buf.append(ch)
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in "'\"":
            quote = ch
            buf.append(ch)
            i += 1
            continue
        if ch == ";":
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        if ch in "&|" and i + 1 < n and command[i + 1] == ch:
            out.append("".join(buf))
            buf = []
            i += 2
            continue
        if ch == "|":  # single pipe — treat as a statement boundary too
            out.append("".join(buf))
            buf = []
            i += 1
            continue
        buf.append(ch)
        i += 1
    out.append("".join(buf))
    return [s.strip() for s in out if s.strip()]


def _tokenize(statement: str) -> list[str]:
    """argv tokenization; falls back to whitespace split on shlex errors
    (unbalanced quotes are common in resolved values)."""
    try:
        return shlex.split(statement, posix=True)
    except ValueError:
        return statement.split()


def _strip_wrappers(argv: list[str]) -> list[str]:
    """Drop leading wrapper verbs and their flags so argv[0] is the real
    target. ``sh -c 'python x'`` -> the inner string is re-tokenized."""
    out = list(argv)
    changed = True
    while changed and out:
        changed = False
        head = out[0]
        if head in _WRAPPER_VERBS:
            out = out[1:]
            changed = True
            # consume wrapper flags; if -c, the next token is a command string
            while out and out[0] in _WRAPPER_FLAGS:
                is_c = out[0] == "-c"
                out = out[1:]
                if is_c and out:
                    out = _tokenize(out[0]) + out[1:]
                changed = True
        elif head in _CONTROL_PREFIX_VERBS:
            out = out[1:]
            changed = True
    return out


def _basename(path: str) -> str:
    return re.split(r"[\\/]", path)[-1]


def _looks_config(token: str) -> bool:
    return token.endswith(".json") or token.endswith(".cfg") or token.endswith(".ini")


def _looks_script(token: str) -> bool:
    # a script token has a path separator or a file extension and is not a
    # flag — lets us skip option *values* like `--master yarn` when hunting
    # for the real script in `spark-submit ... /path/job.py`
    return (not token.startswith("-")) and (
        "/" in token or "\\" in token or bool(re.search(r"\.\w+$", token))
    )


def classify_executable(executable: str) -> tuple[str, str | None]:
    """Return (invocation_type, classifier_rule) for an executable token."""
    base = _basename(executable)
    for pattern, itype, rule in LAUNCHER_REGISTRY:
        if pattern.search(base):
            return itype, rule
    return "UNKNOWN", None


#: classifier rules that name a REGISTERED LAUNCHER entrypoint — the G16 value
#: contract ("aliases suggest, values decide"): a variable whose VALUE hits one
#: of these is a launcher reference regardless of the variable's NAME (the
#: JAR_PATH -> dt-launcher.sh gap-analysis gotcha). Generic interpreter /
#: extension rules (shell.script, python.*, java.*) are excluded on purpose —
#: an arbitrary .sh value is not evidence of a launcher.
NAMED_LAUNCHER_RULES = frozenset({
    "dpl.dt_launcher_accelerator",
    "dpl.pipelines_launcher_jar",
    "dpl.spark_processor_onprem",
    "abioncloud.runscript_wrapper",
    "informatica.icdw_run_interface",
    "informatica.pmcmd",
    "validation.run_data_validation",
    "validation.run_calp_temp",
})


def is_registered_launcher(value: str) -> bool:
    """True when the token's basename matches a NAMED launcher registry rule."""
    _, rule = classify_executable(value)
    return rule in NAMED_LAUNCHER_RULES


# DPL pipeline-id flag spellings: single-dash `-pipeline` (observed launcher
# grammar) and `--pipeline-id` (on-prem argument contract). The GUID value is
# the ONLY literal on otherwise fully-variable CMD_LINEs (G15).
_PIPELINE_ID_FLAGS = ("-pipeline", "--pipeline-id")
_GUID_RE = re.compile(r"^[0-9a-fA-F]{8}(-[0-9a-fA-F]{4}){3}-[0-9a-fA-F]{12}$")


def pipeline_guid(args: tuple[str, ...] | list[str]) -> str | None:
    """The DPL pipeline GUID literal from an arg list, if present."""
    for i, a in enumerate(args):
        if a in _PIPELINE_ID_FLAGS and i + 1 < len(args) and _GUID_RE.match(args[i + 1]):
            return args[i + 1]
    return None


def parse_invocation_statement(statement: str) -> Invocation | None:
    """Parse one already-split statement into an Invocation, or None if it
    is a no-op / pure assignment."""
    argv = _strip_wrappers(_tokenize(statement))
    # drop leading VAR=value assignments and TZ= style prefixes
    while argv and re.match(r"^\w+=", argv[0]):
        argv = argv[1:]
    if not argv:
        return None
    verb = argv[0]
    if verb in _NOOP_VERBS or verb.endswith("="):
        return None

    itype, rule = classify_executable(verb)
    args = tuple(argv[1:])
    if itype == "UNKNOWN" and pipeline_guid(args):
        # an UNRESOLVED original may hold the launcher in a folder variable
        # (%%PY_LAUNCH / %%SCRIPT_PATH prefix) — the -pipeline GUID literal
        # still identifies a DPL launch (G15 acceptance c)
        itype, rule = "DPL", "dpl.pipeline_guid_literal"

    # for interpreter launches (python, sh-wrapped), the script is the first
    # non-flag argument; for direct script execution the verb IS the script
    script_path: str | None = None
    executable_path: str | None = verb
    if itype in {"PYTHON", "PYSPARK"} or _basename(verb).startswith("python"):
        # prefer a script-looking token (skips `--master yarn` option values),
        # then fall back to the first bare non-flag arg (e.g. `python -m module`)
        script_path = (
            next((a for a in args if _looks_script(a)), None)
            or next((a for a in args if not a.startswith("-")), None)
        )
    elif itype == "JAVA":
        # the launched artifact is the first .jar token (-D*/-jar flags skipped);
        # re-classify on the jar basename so registered launchers (the DPL
        # dt-pipelines-launcher) win over generic JAVA
        script_path = next((a for a in args if a.lower().endswith(".jar")), None)
        if script_path:
            jtype, jrule = classify_executable(script_path)
            if jtype != "UNKNOWN":
                itype, rule = jtype, jrule
    elif rule == "abinitio.air_cli":
        # `air sandbox run /path/graph.pset …` — the target follows the subcommands
        script_path = next((a for a in args if _looks_script(a)), None)
    elif re.search(r"\.(sh|ksh|bash|pl|m|py|pset)$", _basename(verb)):
        script_path = verb
    # for Ab Initio launched via a wrapper (run_calp_temp.sh foo.m), surface
    # the .m/.pset argument as the script
    if script_path is None:
        script_path = next(
            (a for a in args if a.endswith(".m") or a.endswith(".py") or a.endswith(".pset")),
            None,
        )

    config_path = next((a for a in args if _looks_config(a)), None)

    return Invocation(
        invocation_type=itype,
        executable_path=(executable_path or "")[:1000] or None,
        script_path=(script_path or "")[:1000] or None,
        config_path=(config_path or "")[:1000] or None,
        args=args,
        raw_command=statement,
        is_classified=itype != "UNKNOWN",
        classifier_rule=rule,
    )


def parse_file_op_statement(statement: str) -> FileOp | None:
    """Parse one statement into a FileOp if its verb is a file operation."""
    argv = _strip_wrappers(_tokenize(statement))
    while argv and re.match(r"^\w+=", argv[0]):
        argv = argv[1:]
    if not argv:
        return None
    op = _FILE_OP_VERBS.get(argv[0])
    if op is None:
        return None
    # operands = non-flag tokens after the verb
    operands = [a for a in argv[1:] if not a.startswith("-")]
    src = operands[0] if operands else None
    tgt = operands[-1] if len(operands) >= 2 else None
    if op in {"DELETE", "MKDIR"}:  # single-target ops
        src, tgt = (operands[0] if operands else None), None
    if op == "COMPRESS":
        # gzip/gunzip rewrite IN PLACE on a deterministic name contract
        # (file <-> file.gz) — derive the twin as tgt so lineage sees both
        # sides of the flow. Stream forms (-c to stdout) have no derivable
        # target and keep tgt None.
        tgt = None
        if src and "-c" not in argv:
            tgt = src[:-3] if src.endswith(".gz") else src + ".gz"
    return FileOp(
        op_type=op,
        src_pattern=(src or "")[:2000] or None,
        tgt_pattern=(tgt or "")[:2000] or None,
        raw_statement=statement[:4000],
    )


_CONTAINER_CMD_RE = re.compile(
    r"command:\s*(?P<arr>.+?)\s*[}\]]", re.IGNORECASE | re.DOTALL
)


def extract_container_command(value: str) -> str | None:
    """Pull the inner shell command from a UCM container-override value.

    The override carries an array like
    ``command: /bin/sh, -c, python /app/app.py --job_name ...`` — the real
    command is the element(s) after the ``-c`` flag. Returns None when the
    override has no command array (e.g. environment-only overrides).
    """
    m = _CONTAINER_CMD_RE.search(value)
    if m is None:
        return None
    elements = [e.strip() for e in m.group("arr").split(",")]
    if "-c" in elements:
        idx = elements.index("-c")
        inner = ", ".join(elements[idx + 1:]).strip()
        # the inner command itself may contain commas (arg lists) — those
        # were split above; rejoin with space which tokenizes the same
        return inner.replace(",", " ").strip() or None
    # no -c: the array itself is the argv
    return " ".join(e for e in elements if e and e != "/bin/sh") or None


# wrapper launchers whose REAL payload rides an argument flag: the abioncloud
# runScript.sh wrapper carries its Ab Initio pset (plus an optional nested
# -run_prog_command_line script) inside the quoted -g value. Without expansion
# every wrapper job collapses onto the same wrapper node — the pset that
# discriminates the workload never surfaces (SME session 2026-07-16).
_WRAPPER_PAYLOAD_FLAGS: dict[str, str] = {"abioncloud.runscript_wrapper": "-g"}
_NESTED_COMMAND_FLAGS = {"-run_prog_command_line"}


def _expand_wrapper_payload(inv: Invocation) -> list[Invocation]:
    """Surface a registered wrapper's payload: the .pset/.m inside the payload
    flag becomes the invocation's script (type ABINITIO; the wrapper stays
    executable_path), and a nested -run_prog_command_line target becomes its
    own Invocation. Non-wrapper invocations pass through unchanged."""
    flag = _WRAPPER_PAYLOAD_FLAGS.get(inv.classifier_rule or "")
    if not flag:
        return [inv]
    payload = next(
        (inv.args[i + 1] for i, a in enumerate(inv.args)
         if a == flag and i + 1 < len(inv.args)),
        None,
    )
    if not payload:
        return [inv]
    tokens = _tokenize(payload)
    out = inv
    pset = next((t for t in tokens if t.endswith((".pset", ".m"))), None)
    if pset:
        out = Invocation(
            invocation_type="ABINITIO",
            executable_path=inv.executable_path,
            script_path=pset[:1000],
            config_path=inv.config_path,
            args=inv.args,
            raw_command=inv.raw_command,
            is_classified=True,
            classifier_rule="abioncloud.runscript_wrapper.pset_payload",
        )
    expanded = [out]
    for i, t in enumerate(tokens):
        if t in _NESTED_COMMAND_FLAGS and i + 1 < len(tokens):
            nested = parse_invocation_statement(tokens[i + 1])
            if nested is not None:
                expanded.append(nested)
    return expanded


def parse_command(command: str) -> ParsedCommand:
    """Parse a full (resolved) command line into invocations + file ops.
    Unclassifiable non-trivial statements are collected in ``unparsed``."""
    result = ParsedCommand()
    for stmt in split_statements(command):
        fop = parse_file_op_statement(stmt)
        if fop is not None:
            result.file_ops.append(fop)
            continue
        inv = parse_invocation_statement(stmt)
        if inv is None:
            continue
        for expanded in _expand_wrapper_payload(inv):
            result.invocations.append(expanded)
            if not expanded.is_classified:
                result.unparsed.append(expanded.raw_command)
    return result
