"""G131: the agent tier's env fallback, and the trap it used to depend on.

The fallback in ``agents/common/neo4j_tool.py`` reads like an ordinary
precedence rule and was not one: ``agents/.env.example`` shipped a blank
``NEO4J_PASSWORD=`` line, so a copied-and-unfilled file SET that name to the
empty string, and the whole tier kept connecting only because ``not ""`` is
true. Writing the guard as the membership test it looks like would have given
every agent an empty password, silently and tier-wide.

The fix removes the dependence rather than documenting it, and this is the test
that says so: after the blank placeholders are dropped, the value check and the
membership check AGREE. That equivalence is the actual guarantee — a future
simplification is then merely a simplification.

NO CREDENTIAL VALUE APPEARS HERE (G131 clause d). Every fixture below is a
made-up string; nothing reads a real .env, and nothing prints.
"""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
for _entry in (str(REPO_ROOT / "agents"), str(REPO_ROOT)):
    if _entry not in sys.path:
        sys.path.insert(0, _entry)

from common.env_merge import apply_fallbacks, drop_blank_placeholders  # noqa: E402

AGENTS_ENV_EXAMPLE = REPO_ROOT / "agents" / ".env.example"


def _merge(agents_file: dict, root_file: dict, environ: dict | None = None) -> dict:
    """The tier's resolution order, over plain dicts: agents file, then root."""
    env = dict(environ or {})
    for name, value in agents_file.items():  # what load_dotenv does, non-overriding
        env.setdefault(name, value)
    drop_blank_placeholders(agents_file, env)
    apply_fallbacks(root_file, env)
    return env


# --------------------------------------------------------------------------- #
# the defect itself
# --------------------------------------------------------------------------- #
def test_a_blank_line_in_the_agents_file_does_not_shadow_the_root_value() -> None:
    env = _merge({"NEO4J_PASSWORD": ""}, {"NEO4J_PASSWORD": "root-value"})
    assert env["NEO4J_PASSWORD"] == "root-value"


def test_the_two_spellings_of_the_guard_now_agree() -> None:
    """The whole point of the change.

    Before it, ``not environ.get(name)`` and ``name not in environ`` differed on
    exactly the case the defect was about, and only the first one worked. After
    dropping the placeholders they cannot differ, so the rewrite that used to be
    a silent tier-wide breakage is now an ordinary edit.
    """
    agents = {"NEO4J_PASSWORD": "", "NEO4J_USER": "agent-user"}
    root = {"NEO4J_PASSWORD": "root-value", "NEO4J_USER": "root-user", "NEO4J_URI": "root-uri"}

    value_check = _merge(agents, root)

    # the same flow with the membership spelling substituted for the value one
    membership = dict(agents)
    drop_blank_placeholders(agents, membership)
    for name, value in root.items():
        if value and name not in membership:
            membership[name] = value

    assert value_check == membership
    # and both are RIGHT, not merely equal
    assert value_check["NEO4J_PASSWORD"] == "root-value"
    assert value_check["NEO4J_USER"] == "agent-user"
    assert value_check["NEO4J_URI"] == "root-uri"


def test_the_old_membership_spelling_really_did_break_it() -> None:
    """The instrument check (J76): if the broken spelling were harmless the test
    above would be asserting nothing. This reproduces the failure WITHOUT the
    placeholder drop, so the equivalence proved above is a property of the fix
    and not of the fixtures."""
    agents = {"NEO4J_PASSWORD": ""}
    broken = dict(agents)
    for name, value in {"NEO4J_PASSWORD": "root-value"}.items():
        if value and name not in broken:  # no drop_blank_placeholders first
            broken[name] = value
    assert broken["NEO4J_PASSWORD"] == "", "the trap did not reproduce — check the fixture"


# --------------------------------------------------------------------------- #
# the rules, each stated separately
# --------------------------------------------------------------------------- #
def test_a_real_agent_value_still_wins_over_the_root() -> None:
    env = _merge({"NEO4J_DATABASE": "agent-db"}, {"NEO4J_DATABASE": "root-db"})
    assert env["NEO4J_DATABASE"] == "agent-db"


def test_a_blank_line_in_the_root_file_never_overrides_either() -> None:
    env = _merge({}, {"NEO4J_PASSWORD": ""}, {"NEO4J_PASSWORD": "already-set"})
    assert env["NEO4J_PASSWORD"] == "already-set"
    # and it does not invent the name when nothing had it
    assert "GOOGLE_API_KEY" not in _merge({}, {"GOOGLE_API_KEY": ""})


def test_a_shell_exported_empty_value_is_left_alone() -> None:
    """The narrow scope of the placeholder drop, asserted rather than assumed.

    An empty value the SHELL exported is a different thing from a blank line in
    a file, and this module has no business deleting it — so it stays, and the
    fallback's value check (not membership) is what keeps today's behaviour for
    that case. Both rules exist; this is the one that needs the value check.
    """
    env = _merge({}, {"NEO4J_PASSWORD": "root-value"}, {"NEO4J_PASSWORD": ""})
    assert env["NEO4J_PASSWORD"] == "root-value"
    # the name was NOT dropped by the placeholder pass — the agents file never
    # declared it, so nothing here claimed responsibility for it
    only_shell: dict[str, str] = {"SOMETHING_ELSE": ""}
    assert drop_blank_placeholders({}, only_shell) == []
    assert only_shell == {"SOMETHING_ELSE": ""}


def test_drop_reports_what_it_dropped() -> None:
    env = {"A": "", "B": "real"}
    assert drop_blank_placeholders({"A": "", "B": ""}, env) == ["A"]
    assert env == {"B": "real"}


# --------------------------------------------------------------------------- #
# clause (b)/(c): the file that produced the blank line
# --------------------------------------------------------------------------- #
def test_the_shipped_example_declares_no_name_it_does_not_set() -> None:
    """A live line with an empty value in agents/.env.example is the defect's
    source: copy the file, do not fill it, and that name is set to "" for the
    whole tier. The Neo4j and API-key lines ship COMMENTED for that reason, so
    the root .env answers on a one-graph machine.
    """
    offenders = []
    for raw in AGENTS_ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, _, value = line.partition("=")
        if value.strip() == "":
            offenders.append(name.strip())
    assert not offenders, (
        f"agents/.env.example declares {offenders} with no value. A copied file then SETS "
        "those names to the empty string and they shadow the repo-root .env (G131). "
        "Comment the line out instead — an override should have to be uncommented."
    )
