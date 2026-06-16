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
  * File-op verbs (mkdir/cp/mv/rm/rmdir/chmod/rename/ln/sed) -> STG_FILE_OP.
    The set matches the vendor's pre/post-transfer command list
    (controlm-file-transfer-job.md: chmod, mkdir, rename, rm, rmdir).
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
    (re.compile(r"^m_\w+", re.I),               "INFORMATICA",    "informatica.mapping_prefix"),
    (re.compile(r"^pmcmd$", re.I),              "INFORMATICA",    "informatica.pmcmd"),
    (re.compile(r"^run_data_validation\.sh$"),  "VALIDATION_UTIL","validation.run_data_validation"),
    (re.compile(r"^run_calp_temp\.sh$"),        "VALIDATION_UTIL","validation.run_calp_temp"),
    (re.compile(r"^dtlaunch\.sh$"),             "ABINITIO",       "abinitio.dtlaunch_accelerator"),
    (re.compile(r"runscript\.sh$"),             "SHELL_SCRIPT",   "abioncloud.runscript_wrapper"),
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
    "chmod": "OTHER", "chown": "OTHER", "ln": "OTHER", "touch": "OTHER",
}
# verbs that are neither invocation nor file-op (control/no-op) — skipped
_NOOP_VERBS = {"cd", "cc", "echo", "ls", "set", "export", "true", "wait", "TZ="}
# wrapper verbs whose real target is a later token
_WRAPPER_VERBS = {"sh", "bash", "ksh", "zsh", "csh", "env", "nohup", "exec", "time"}
_WRAPPER_FLAGS = {"-c", "-e", "-x", "-eu", "-ex", "-l"}


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
            out.append("".join(buf)); buf = []; i += 1; continue
        if ch in "&|" and i + 1 < n and command[i + 1] == ch:
            out.append("".join(buf)); buf = []; i += 2; continue
        if ch == "|":  # single pipe — treat as a statement boundary too
            out.append("".join(buf)); buf = []; i += 1; continue
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
    return out


def _basename(path: str) -> str:
    return re.split(r"[\\/]", path)[-1]


def _looks_config(token: str) -> bool:
    return token.endswith(".json") or token.endswith(".cfg") or token.endswith(".ini")


def classify_executable(executable: str) -> tuple[str, str | None]:
    """Return (invocation_type, classifier_rule) for an executable token."""
    base = _basename(executable)
    for pattern, itype, rule in LAUNCHER_REGISTRY:
        if pattern.search(base):
            return itype, rule
    return "UNKNOWN", None


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

    # for interpreter launches (python, sh-wrapped), the script is the first
    # non-flag argument; for direct script execution the verb IS the script
    script_path: str | None = None
    executable_path: str | None = verb
    if itype in {"PYTHON", "PYSPARK"} or _basename(verb).startswith("python"):
        script_path = next((a for a in args if not a.startswith("-")), None)
    elif re.search(r"\.(sh|ksh|bash|pl|m|py)$", _basename(verb)):
        script_path = verb
    # for Ab Initio launched via a wrapper (run_calp_temp.sh foo.m), surface
    # the .m argument as the script
    if script_path is None:
        script_path = next((a for a in args if a.endswith(".m") or a.endswith(".py")), None)

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
        result.invocations.append(inv)
        if not inv.is_classified:
            result.unparsed.append(stmt)
    return result
