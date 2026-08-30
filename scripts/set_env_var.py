"""Set one declared environment variable in the machine-local `.env` (G129 (c)).

    poetry run python scripts/set_env_var.py NEO4J_PASSWORD
    poetry run python scripts/set_env_var.py --list
    poetry run python scripts/set_env_var.py --remove ORACLE_DSN

THE VALUE IS NEVER AN ARGUMENT. It is read from a prompt, and from a NO-ECHO
prompt whenever the declaration says the variable is secret. An argument lands in
shell history, in the process table, and in whatever scrollback a screen share is
showing -- the same reasoning ``scripts/set_console_credential.py`` already
carries, and this is that pattern applied to the other machine-local file.

THIS IS THE OPERATOR'S TOOL AND NOT A LOAD PATH, which is a distinction worth
stating rather than leaving to be inferred. G126 rules the machine-local tree
READ-mode for the SYSTEM: nothing the pipeline runs may write there. An operator
at a terminal is not the system, so the writer is a script invoked by hand, in
``scripts/`` beside the credential writer, and no module imports it. That
placement IS the enforcement.

ONLY A DECLARED NAME MAY BE SET. Setting an undeclared variable would put a key
in `.env` that no binding may reference and that `.env.example` will never show,
which is precisely the eight-undeclared-variables state G125 and G129 exist to
end. The refusal names the file to add the declaration to.

WHAT IT NEVER DOES: print a value, echo a secret back for confirmation, write to
`.env.example` (generated -- see scripts/render_env_example.py), or touch
anything under git. `.env` is gitignored and stays that way.
"""

from __future__ import annotations

import argparse
import getpass
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from drydocs_core.env_doctor import MACHINE_LOCAL_ENV, dotenv_names  # noqa: E402
from drydocs_core.env_refs import DECLARED_VARIABLES, EnvVar  # noqa: E402

TARGET = REPO_ROOT / MACHINE_LOCAL_ENV

#: Pinned so the file does not churn its line endings between machines -- the
#: same reason the credential writer pins it, and the repo-wide J49 rule.
NEWLINE = "\n"


def _declared(name: str) -> EnvVar | None:
    return next((v for v in DECLARED_VARIABLES if v.name == name), None)


def _prompt(var: EnvVar) -> str:
    """Read the value. No-echo and confirmed when the DECLARATION says secret.

    The declaration decides, not the operator and not a guess at the name: a
    variable is secret because someone wrote it down as secret, which is the same
    rule masking uses. A visible prompt for a path is deliberate -- a data root
    typed blind is a data root typed wrong, and a path is not a credential.
    """
    if var.secret:
        first = getpass.getpass(f"Value for {var.name} (not echoed): ")
        if not first.strip():
            raise SystemExit("refused: empty value. Use --remove to unset it.")
        if getpass.getpass("Confirm: ") != first:
            raise SystemExit("refused: the two entries did not match")
        return first
    value = input(f"Value for {var.name}: ")
    if not value.strip():
        raise SystemExit("refused: empty value. Use --remove to unset it.")
    return value


def _rewrite(lines: list[str], name: str, value: str | None) -> list[str]:
    """Replace, append, or drop ``name``. Every other line survives byte-for-byte.

    An operator's own comments and ordering in `.env` are theirs. A writer that
    normalized the file would be a writer that silently discarded a note somebody
    left themselves about which host a value points at.
    """
    out: list[str] = []
    replaced = False
    for line in lines:
        key = line.split("=", 1)[0].strip().removeprefix("export ").strip()
        if key == name and not line.lstrip().startswith("#"):
            if value is not None and not replaced:
                out.append(f"{name}={value}")
                replaced = True
            continue
        out.append(line)
    if value is not None and not replaced:
        out.append(f"{name}={value}")
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Set a declared environment variable in the machine-local .env."
    )
    parser.add_argument("name", nargs="?", help="the DECLARED variable name to set")
    parser.add_argument(
        "--list", action="store_true", help="show which declared names are set here (names only)"
    )
    parser.add_argument("--remove", metavar="NAME", help="delete a name from the file")
    args = parser.parse_args(argv)

    if args.list:
        present = dotenv_names(TARGET)
        print(f"file: {MACHINE_LOCAL_ENV} ({'present' if TARGET.exists() else 'not created yet'})")
        for var in DECLARED_VARIABLES:
            answering = next((n for n in (var.name, *var.aliases) if n in present), "")
            mark = "set" if answering else "-"
            via = f"  (via {answering})" if answering and answering != var.name else ""
            print(f"  {var.name:<28} {mark}{via}")
        print()
        print("Values are never shown. For the full picture including the process")
        print("environment and which twin documents each variable: drydocs env-doctor")
        return 0

    name = args.remove or args.name
    if not name:
        parser.print_help()
        return 2

    var = _declared(name)
    if var is None:
        known = ", ".join(v.name for v in DECLARED_VARIABLES)
        print(
            f"error: {name!r} is not a declared variable, so setting it would put a key in "
            f"{MACHINE_LOCAL_ENV} that no binding may reference and that .env.example will "
            "never show. Declare it first in drydocs_core/env_refs.py, then re-run.\n"
            f"known: {known}",
            file=sys.stderr,
        )
        return 1

    lines = TARGET.read_text(encoding="utf-8").splitlines() if TARGET.exists() else []

    if args.remove:
        if name not in dotenv_names(TARGET):
            print(f"error: {name} is not set in {MACHINE_LOCAL_ENV}", file=sys.stderr)
            return 1
        updated = _rewrite(lines, name, None)
        TARGET.write_text(NEWLINE.join(updated) + NEWLINE, encoding="utf-8", newline=NEWLINE)
        print(f"removed {name} from {MACHINE_LOCAL_ENV}")
        return 0

    updated = _rewrite(lines, name, _prompt(var))
    TARGET.write_text(NEWLINE.join(updated) + NEWLINE, encoding="utf-8", newline=NEWLINE)
    print(f"set {name} in {MACHINE_LOCAL_ENV} - machine-local, gitignored, never committed")
    if var.secret:
        print("The value was not echoed and is not in your shell history.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
