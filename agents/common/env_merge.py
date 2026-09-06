"""How the agent tier resolves its environment, and why the rule is written out.

THE DEFECT (G131, from Idea-203). The agent tier reads `agents/.env` first and
then falls back to the repo-root `.env`. The fallback was one line:

    if _value and not os.getenv(_name):
        os.environ[_name] = _value

which reads like an ordinary precedence rule — "take the root value unless this
name is already set" — and is not one. `agents/.env.example` shipped a blank
``NEO4J_PASSWORD=`` line, so a developer who copies the file and does not fill
it in has that name SET, to the empty string, before the fallback runs. The
whole agent tier keeps working only because ``not ""`` is true.

Rewrite that guard as the membership test it appears to be — ``_name not in
os.environ`` — and the blank line wins instead: every agent connects with an
empty password, and the failure is silent and tier-wide. Nothing in the code
said so, which is what made it a trap rather than a subtlety.

WHAT THIS MODULE DOES ABOUT IT. Not a comment. A blank line in an env FILE means
"not set here", never "set to empty", so ``drop_blank_placeholders`` removes
those names from the environment before the fallback runs. After it, the two
spellings agree — and ``test_agent_env_merge.py`` asserts they agree, so the
rewrite that used to be a silent breakage is now merely a rewrite.

WHY THE FALLBACK STILL CHECKS THE VALUE and not just membership, given the
above: a variable EXPORTED empty by the shell is a different thing from a blank
line in a file, and this module has no business deleting it. The value check
keeps today's behaviour for that case exactly; the blank-drop removes the case
this defect was about. Both rules are named, so neither can be "simplified" by
someone who cannot see what it was for.

No credential value is ever read, logged or returned here — the functions move
names between mappings and nothing prints.
"""

from __future__ import annotations

from collections.abc import MutableMapping


def drop_blank_placeholders(
    file_values: dict[str, str | None], environ: MutableMapping[str, str]
) -> list[str]:
    """Un-set names a env FILE declared with no value.

    Only names the file declared blank AND that are currently empty in the
    environment — so a name something else set to a real value is untouched, and
    a name something else deliberately exported as empty is left alone too. That
    narrowness is the point: this removes a placeholder, it does not clean up
    the environment.

    Returns the names dropped, so a caller can report them.
    """
    dropped = []
    for name, value in file_values.items():
        if value == "" and environ.get(name) == "":
            del environ[name]
            dropped.append(name)
    return dropped


def apply_fallbacks(
    file_values: dict[str, str | None], environ: MutableMapping[str, str]
) -> list[str]:
    """Fill names the process has no real value for, from a lower-precedence file.

    Two rules, stated rather than implied:
      * a blank line in the fallback file is NOT a value, so it never overrides;
      * a name that already has a non-empty value keeps it.

    Returns the names filled.
    """
    filled = []
    for name, value in file_values.items():
        if not value:
            continue
        if environ.get(name):
            continue
        environ[name] = value
        filled.append(name)
    return filled
