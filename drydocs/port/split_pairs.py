"""split_pairs.py - a commit split across two dispositions ports as a broken half (PORT12).

THE DEFECT THIS FINDS, in the instance that produced it. G130 (`01761011`, 2026-08-30)
added three halves of one call chain in one commit: ``constraints_detail`` on
``drydocs_core/neo4j_client.py``, ``undeclared_constraints`` in
``drydocs_core/schema/constraints.py``, and the caller at ``drydocs/cli_schema.py:346``.
Two of those files are ``canonical-producer`` and cross wholesale; the third resolves
through ``default_ok`` to the manifest DEFAULT, which is evaluate-on-collision because
both sides authored it, so it waits on a hand-merge. The consumer took the two, the
sixteen-line method did not make the third, and ``drydocs bootstrap`` raised
``AttributeError: 'Neo4jClient' object has no attribute 'constraints_detail'`` ten days
later - because an uncalled missing method raises nothing until it is called.

WHY PRECISION IS THE WHOLE DESIGN. A check that reported every commit touching both
``drydocs/**`` and ``drydocs_core/**`` would report most commits in this repo and be
switched off within a week. The reportable unit is a PAIR, and both halves must be new
in the same range: a name ADDED to a file the consumer must hand-merge, and NEWLY
REFERENCED from a file that crosses unattended. A stable core API that crossed months
ago is not at risk; the sixteen lines added yesterday are.

WHAT IT DOES NOT DO. It does not gate. The dispositions are correct - ``drydocs_core/**``
is evaluate-on-collision for a reason the manifest states - so a split commit is
legitimate and what it owes is a RELAY LINE naming the pair, not a refusal. It reads
only the producer tree: whether a given consumer actually missed the definition is
theirs to know, and this says where to look.

Pure functions over source text and a loaded manifest; only ``git_*`` and ``main``
shell out. The classifier is the ONE in ``dispositions.py`` (J68), never a second
reading of the manifest.
"""

from __future__ import annotations

import ast
import subprocess
from dataclasses import dataclass
from pathlib import Path

from drydocs.port.dispositions import DEFAULT, DEFAULT_OK, classify, load_manifest
from drydocs_core.check_outcome import CheckOutcome, checked_clean, findings, not_checked

#: Dispositions whose files reach the consumer with no hand on them.
CROSSES_UNATTENDED: frozenset[str] = frozenset({"canonical-producer", "clean-add"})

#: Dispositions that resolve INSIDE the consumer's tree - a person merges, keeps or
#: reconciles - so an addition here arrives only if that person carries it.
#:
#: ``DEFAULT`` and ``default_ok`` are counted here deliberately, and the reason is the
#: G130 case: the manifest DEFAULT is "clean-add when absent on consumer; evaluate when
#: both sides created the path", and which arm applies depends on the CONSUMER's tree,
#: which the producer cannot read. The risky arm is evaluate, so the conservative
#: reading is the one that reports. A false report costs a relay line; a false silence
#: costs an AttributeError on someone else's machine.
NEEDS_A_HAND: frozenset[str] = frozenset(
    {"evaluate", "per-entry", "canonical-company", "union-append", DEFAULT, DEFAULT_OK}
)

#: Neither: regenerated on the consumer's tree from its own sources (J43), so nothing
#: defined here travels as text at all. Excluded from both sides of a pair.
NEITHER: frozenset[str] = frozenset({"derived", "never-port"})


@dataclass(frozen=True)
class SplitPair:
    """One name added on the hand-merge side and newly used on the unattended side."""

    name: str
    defined_in: str
    defined_disposition: str
    used_in: str
    used_disposition: str

    def render(self) -> str:
        return (
            f"{self.name}: defined in {self.defined_in} ({self.defined_disposition}), "
            f"used from {self.used_in} ({self.used_disposition})"
        )


#: A definition here is not one a production file can reach: no module under
#: ``drydocs*`` imports from the test tree, so a reference in an unattended file can
#: never resolve to a test-defined name. Measured rather than assumed - a fake client
#: in ``test_bootstrap_guard.py`` defines ``constraints_detail`` too, and counting it
#: duplicated a true finding on the G130 control.
NOT_A_DEFINITION_SIDE: tuple[str, ...] = ("tests/",)


def defined_names(source: str) -> set[str]:
    """Every name ``source`` DEFINES that another module could reach by name.

    Module scope and class bodies ONLY - functions and classes at the top level,
    methods on a class (by bare name, because the use site sees ``client.method()``
    and not the class), and module-level constants.

    NOT ``ast.walk``, and the difference is why the G130 control was run before this
    was trusted: walking descends into function BODIES, so every local variable in a
    changed function counted as a new definition and three locals in one test file
    reached the report. A local is not reachable by name from another module, so it
    cannot be half of a split pair.

    Read as code either way: a name in a comment defines nothing, which is J66 applied
    to the half of the pair that matters most - the lines that did not travel.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()

    found: set[str] = set()

    def collect(body: list[ast.stmt], *, descend_into_classes: bool) -> None:
        for node in body:
            if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
                found.add(node.name)
            elif isinstance(node, ast.ClassDef):
                found.add(node.name)
                if descend_into_classes:
                    # One level: a method is reachable as `obj.method`. A function
                    # nested inside a method is not reachable from anywhere.
                    collect(node.body, descend_into_classes=False)
            elif isinstance(node, ast.Assign):
                found.update(t.id for t in node.targets if isinstance(t, ast.Name))
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                found.add(node.target.id)
            elif isinstance(node, ast.If | ast.Try):
                # A module-level `if TYPE_CHECKING:` or try/except ImportError still
                # binds names at module scope.
                collect(node.body, descend_into_classes=descend_into_classes)
                collect(getattr(node, "orelse", []), descend_into_classes=descend_into_classes)
                for handler in getattr(node, "handlers", []):
                    collect(handler.body, descend_into_classes=descend_into_classes)

    collect(tree.body, descend_into_classes=True)
    return {n for n in found if not n.startswith("__")}


def referenced_names(source: str) -> set[str]:
    """Every name ``source`` USES - bare names and attribute access alike.

    ``cli.constraints_detail()`` is an attribute, not an import, so an import-only
    reading would have missed the case this module exists for.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return set()
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            found.add(node.id)
        elif isinstance(node, ast.Attribute):
            found.add(node.attr)
    return {n for n in found if not n.startswith("__")}


def split_pairs(
    before: dict[str, str],
    after: dict[str, str],
    dispositions: dict[str, str],
    *,
    definitions_in_tree: dict[str, set[str]] | None = None,
) -> tuple[list[SplitPair], list[str], list[str]]:
    """The pairs, from two snapshots of the changed files and their dispositions.

    Returns ``(pairs, ambiguous, carried_by_clean_add)``. Pure: takes text, returns
    findings. ``before`` may
    omit a path the range created; an absent path reads as empty, which is what makes
    every name in a new file count as added.

    ``definitions_in_tree`` maps a name to every non-test module defining it at HEAD.
    It is what makes an attribution honest, and the first run without it is why it
    exists: ``referenced_names`` collects every attribute access, so ``row.description``
    matched a ``description`` field defined somewhere else entirely and 404 "pairs"
    came back, most of them one name meaning two things. A name with more than one
    definition site cannot be attributed to any of them - the detector's claim is
    "this use needs THAT definition" - so those names are returned as ``ambiguous``
    and COUNTED rather than dropped in silence. A silent drop is how a detector starts
    under-reporting with nobody the wiser.
    """
    added_defs: dict[str, list[str]] = {}
    new_refs: dict[str, list[str]] = {}
    defines_locally: dict[str, set[str]] = {}
    carried_by_clean_add: list[str] = []
    for path, text in after.items():
        disp = dispositions.get(path, DEFAULT)
        if disp in NEITHER or not path.endswith(".py"):
            continue
        was = before.get(path, "")
        here = defined_names(text)
        defines_locally[path] = here
        new_here = not was.strip()

        # THE TWO ARMS OF THE DEFAULT. A path that falls through to the manifest
        # default is clean-add when the consumer lacks it and evaluate when both
        # sides have it. A file this range CREATED almost certainly lands on the
        # first arm, arriving whole with every definition in it - that is a new
        # file crossing normally, not a split. Only a file that already existed at
        # the base can take the evaluate arm, which is precisely the G130 shape.
        # An EXPLICIT evaluate / per-entry / canonical-company row is a ruling and
        # needs a hand whatever the file's age.
        falls_to_default = disp in (DEFAULT, DEFAULT_OK)
        crosses_whole = disp in CROSSES_UNATTENDED or (falls_to_default and new_here)

        if disp in NEEDS_A_HAND and not path.startswith(NOT_A_DEFINITION_SIDE):
            if crosses_whole:
                if here - defined_names(was):
                    carried_by_clean_add.append(path)
            else:
                for name in here - defined_names(was):
                    added_defs.setdefault(name, []).append(path)
        if crosses_whole:
            for name in referenced_names(text) - referenced_names(was):
                new_refs.setdefault(name, []).append(path)

    pairs: list[SplitPair] = []
    ambiguous: list[str] = []
    for name in sorted(set(added_defs) & set(new_refs)):
        if definitions_in_tree is not None and len(definitions_in_tree.get(name, set())) > 1:
            ambiguous.append(name)
            continue
        for definer in sorted(added_defs[name]):
            for user in sorted(new_refs[name]):
                # A name the using file defines ITSELF resolves locally; it is not
                # reaching the other module, whatever that module also calls it.
                if name in defines_locally.get(user, set()):
                    continue
                pairs.append(
                    SplitPair(
                        name=name,
                        defined_in=definer,
                        defined_disposition=dispositions.get(definer, DEFAULT),
                        used_in=user,
                        used_disposition=dispositions.get(user, DEFAULT),
                    )
                )
    return pairs, ambiguous, sorted(set(carried_by_clean_add))


def tree_definitions(files: dict[str, str]) -> dict[str, set[str]]:
    """name -> every non-test module defining it. The attribution denominator."""
    out: dict[str, set[str]] = {}
    for path, text in files.items():
        if path.startswith(NOT_A_DEFINITION_SIDE) or not path.endswith(".py"):
            continue
        for name in defined_names(text):
            out.setdefault(name, set()).add(path)
    return out


# ---- the git-backed half (everything above is pure) -------------------------


def git_show(rev: str, path: str, *, repo: Path | None = None) -> str:
    """The file's text at ``rev``, or ``""`` when it did not exist there."""
    p = subprocess.run(
        ["git", "show", f"{rev}:{path}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        cwd=repo,
    )
    return p.stdout if p.returncode == 0 else ""


def git_resolves(rev: str, *, repo: Path | None = None) -> bool:
    """Whether git can see ``rev`` HERE - the not-checked case, named."""
    return (
        subprocess.run(
            ["git", "rev-parse", "--verify", f"{rev}^{{commit}}"],
            capture_output=True,
            cwd=repo,
        ).returncode
        == 0
    )


def git_changed_paths(base: str, head: str, *, repo: Path | None = None) -> list[str]:
    p = subprocess.run(
        ["git", "diff", "--name-only", f"{base}..{head}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=repo,
    )
    return [line for line in p.stdout.splitlines() if line.strip()]


def git_tracked_python(rev: str, *, repo: Path | None = None) -> list[str]:
    """Every tracked ``.py`` path at ``rev`` - the denominator for attribution."""
    p = subprocess.run(
        ["git", "ls-tree", "-r", "--name-only", rev],
        capture_output=True,
        text=True,
        encoding="utf-8",
        cwd=repo,
    )
    return [line for line in p.stdout.splitlines() if line.endswith(".py")]


def check_range(
    base: str,
    head: str = "HEAD",
    *,
    repo: Path | None = None,
    manifest: Path | None = None,
) -> CheckOutcome:
    """The split pairs in ``base..head`` - findings, clean, or NOT CHECKED with a reason.

    NOT CHECKED is a real answer and not a failure mode: an unresolvable base (a tag
    this clone never fetched is the ordinary case) means nothing was compared, and
    saying "no pairs" there would be the exact defect ADR 0021 exists to stop.
    """
    for rev in (base, head):
        if not git_resolves(rev, repo=repo):
            return not_checked(
                f"the revision {rev!r} does not resolve in this clone, so no range was "
                "compared and no statement about split pairs can be made here (PORT12)"
            )

    root = repo or Path.cwd()
    doc = load_manifest(manifest or root / "PORT-MANIFEST.yaml")
    paths = [p for p in git_changed_paths(base, head, repo=repo) if p.endswith(".py")]
    if not paths:
        return checked_clean(size=0, subject=f"{base}..{head}, no Python file changed")

    dispositions = {p: classify(p, doc)[0] for p in paths}
    before = {p: git_show(base, p, repo=repo) for p in paths}
    after = {p: git_show(head, p, repo=repo) for p in paths}

    tracked = git_tracked_python(head, repo=repo)
    in_tree = tree_definitions({p: git_show(head, p, repo=repo) for p in tracked})

    pairs, ambiguous, clean_added = split_pairs(
        before, after, dispositions, definitions_in_tree=in_tree
    )
    subject = f"{base}..{head}, {len(paths)} Python file(s) changed"
    if ambiguous:
        subject += f", {len(ambiguous)} name(s) too ambiguous to attribute"
    if clean_added:
        subject += f", {len(clean_added)} new file(s) carried whole by clean-add"
    if pairs:
        return findings(pairs, size=len(paths), subject=subject)
    return checked_clean(size=len(paths), subject=subject)
