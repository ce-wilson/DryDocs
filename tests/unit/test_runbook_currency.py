"""Operator-document CURRENCY — do the things a document names still exist?

Covers every ``docs/design/*-runbook.md`` plus the documents in ``EXTRA_DOCS``.

The sibling guard (``test_runbook_coverage.py``, V1) proves a module HAS a
runbook. It says nothing about whether that runbook is TRUE, and on 2026-08-04
that gap cost three separate catches, all by a person noticing rather than a
test:

* the mapping-store runbook had been missing K9's ``app_code_mapping`` for a day
  and carried a "nothing here can lose data" rule S4 had just falsified;
* the drydocs-core runbook copied the topology database list inline and named
  ``ddlineage`` hours before the X1 amendment retired it;
* the drydocs-api runbook cited ``tests/unit/test_guard.py`` as its oracle — a
  file that does not exist.

Coverage and currency are different problems and only the first had a test. This
is the second.

WHAT IT CAN AND CANNOT DO. It checks that named things EXIST: repo-relative file
paths in backticks, and ``drydocs`` CLI verbs. It cannot check that a sentence is
still true — "nothing here can lose data" is not detectable by grep, and neither
was the stale database enumeration. So this narrows the gap rather than closing
it, which is why the runbooks also ship re-derive one-liners with the rule that
the CODE wins on disagreement. A pointer cannot go stale; only a copy can.

IT ALSO DOES NOT CHECK COMMIT SHAs, deliberately. ``docs/port/port-prompt.md`` cites
61 of them, and three legitimately do not resolve here: two are company-side (a
port commit and a backup tag) and one is the ``depgraph`` SIBLING repo. A SHA
guard would therefore need a foreign-ref exemption list that grows by two or
three entries at every port — high maintenance, and its failures would mostly be
bookkeeping rather than defects. Paths and verbs are where the real staleness
lives.

WHY PORT-PROMPT IS IN HERE (2026-08-05). It is not a runbook, so nothing swept it
— and it is arguably the highest-consequence document in the repo, because a
company-side session ACTS on it and, as of today, cannot even fetch this repo to
check it. A manual audit found the S5 fragment split had reached the code and not
this document: it explains the monolith->directory change in one step and, three
hundred lines earlier, still cites the two pre-split filenames as current facts
of a producer gate the company is told to trust. That is exactly the class this
guard exists for, and it went unseen for four days for want of a glob.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
DESIGN_DIR = REPO_ROOT / "docs" / "design"

#: Operator documents outside docs/design/*-runbook.md that are worth the same
#: check. Each needs a reason, and each must EXIST — a doc that gets renamed out
#: from under this list would otherwise drop out of coverage silently.
EXTRA_DOCS: dict[str, str] = {
    "docs/port/port-prompt.md": (
        "the cross-repo port instructions — the highest-consequence document here, "
        "because a company-side session acts on it against a tree this repo cannot "
        "see, and (2026-08-05) cannot currently fetch this repo to check it either. "
        "Added after a manual audit found the S5 fragment split had reached the code "
        "and not this document"
    ),
}

#: Paths a document names that are NOT claims about the current tree. Each needs a
#: reason — the exemption IS the reason, same idiom as MODULE_EXEMPT.
HISTORICAL_PATHS: dict[str, str] = {
    "docs/runbook-mapping-demo.md": (
        "front-matter history — the demo runbook records where it was RELOCATED FROM "
        "at the L14 refit. A former path is a fact about the past, not a claim that it exists"
    ),
    "docs/company-prompts/port-fix-a14a8028-company-prompt.md": (
        "the port-prompt ledger cites the fix pack the a14a8028 fix session RAN "
        "(2026-08-06/07, session complete). The pack retired to internal-local/archive/"
        "company-prompts/ at the 2026-08-07 prompt retirement — the citation is a fact "
        "about a completed session, and the full text is one `git show ced0088` away"
    ),
    "docs/reviews/port-review-7c18ff4b-20260820.md": (
        "UNTRACKED producer-side at 103f240c — a producer review of a COMPANY port ports "
        "BACK to the repo it is about, so `docs/reviews/port-review-*` is now gitignored "
        "and the file was `git rm --cached`ed. Step 212 names it to tell that side the "
        "range DELETES a file they may hold, which a diff cannot distinguish from a "
        "retraction. The path is a fact about a completed untracking; the text is one "
        "`git show 103f240c^:docs/reviews/port-review-7c18ff4b-20260820.md` away. "
        "NOTE FOR THE NEXT SESSION ON A MACHINE THAT STILL HAS IT: untracked-but-present "
        "makes this guard pass LOCALLY and fail on a fresh clone — this entry was added "
        "from the CI failure, not from a local run"
    ),
}

#: Paths in ANOTHER repo. Kept separate from HISTORICAL_PATHS on purpose: "this
#: is about the past" and "this is about the other tree" are different claims,
#: and merging them would let a genuinely-stale producer path hide behind a
#: cross-repo excuse. Every entry here must be a path the document asserts is
#: absent producer-side or names in a sibling — never one we simply deleted.
FOREIGN_PATHS: dict[str, str] = {
    "docs/port-prompt.md": (
        "COMPANY-side path, and the ONE the S9 move created (step 177): the producer's "
        "prompt now lives at docs/port/port-prompt.md, while the company's copy is still "
        "at the flat docs root. Step 177 names the flat path to tell that side which of "
        "ITS files the re-pathed manifest rows stop governing — naming their path is the "
        "instruction, not a stale claim about this tree"
    ),
    "drydocs/docmeta/connectors/base.py": (
        "COMPANY-side module. port-prompt names it in the per-file-ignores inventory "
        "precisely to say `drydocs/docmeta/` does not exist producer-side — naming an "
        "absence is the opposite of a stale claim (T21)"
    ),
    "drydocs/scrapers/registry.py": (
        "COMPANY-side module, same inventory, same reason: `drydocs/scrapers/` does not "
        "exist producer-side and port-prompt says so (T21)"
    ),
    "tests/unit/test_employee_roster.py": (
        "COMPANY-side test named in the same per-file-ignores inventory as absent "
        "producer-side, alongside a `test_snow_supp*` this pattern does not match"
    ),
    "drydocs_core/orchestration/controlm/resource_pool_company.py": (
        "COMPANY-side module created AT the caa0406 port (G76 mechanism/vocabulary "
        "split). port-prompt names it in the standing-divergence ledger to say the "
        "estate vocabulary lives THERE and never flows back — naming where a thing "
        "went is the whole point of the entry"
    ),
    "drydocs_core/adapters/controlm_xml_adapter.py": (
        "COMPANY-side module (G75/G76, 2026-08-11). port-prompt names it to say it is "
        "company-canonical and NOT a producer back-flow target — it encodes the "
        "description-token model C30 retired, flattens the C30 scope ladder, and its "
        "FOLDER_ORDER_METHOD filter skips exactly the folders a conformance pass needs. "
        "Naming that absence is the point of the entry, not a stale claim"
    ),
}

#: Extensions worth checking. Deliberately narrow: prose mentions plenty of
#: things that look path-like, and a guard with false positives gets muted.
_PATH = re.compile(
    r"`([A-Za-z0-9_][A-Za-z0-9_./-]*\.(?:py|md|yaml|yml|cypher|sql|json|html|ps1|sh|csv|xlsx))`"
)
#: The lookbehind matters: without it, `run-drydocs skill` matches and reports a
#: `drydocs skill` command that was never claimed to exist. Measured on
#: port-prompt.md, which names the run-drydocs SKILL twice.
_VERB = re.compile(r"(?<![\w-])drydocs\s+([a-z][a-z0-9-]{2,})")

#: `drydocs load <name>` / `drydocs check` — the first is a subcommand argument,
#: not a verb; the second is real but reads as a word elsewhere.
_NOT_VERBS = {"load", "check"}


def _documents() -> dict[str, str]:
    """Every document under this guard, keyed by a name fit for a failure message.

    Runbooks by glob (so a NEW runbook is covered the moment it exists) plus the
    named EXTRA_DOCS. The port-prompt ARCHIVE is deliberately absent: it is a
    record of steps 1-42 as they were written, so its paths are statements about
    the past by construction and every one would need an exemption.
    """
    docs = {p.name: p.read_text(encoding="utf-8") for p in sorted(DESIGN_DIR.glob("*-runbook.md"))}
    for rel in EXTRA_DOCS:
        docs[rel] = (REPO_ROOT / rel).read_text(encoding="utf-8")
    return docs


def _cli_verbs() -> set[str]:
    """The registered command names, read from Typer rather than from `--help`.

    THIS USED TO SHELL OUT AND PARSE THE RENDERED HELP, and on 2026-08-04 — the
    first run on the laptop after it was written — that failed twice over, both
    times on the ENVIRONMENT rather than on the thing under test:

    * ``subprocess.run(..., text=True)`` decodes with the locale codec. Under
      cp1252 the box character ``┐`` (UTF-8 ``E2 94 90``) is undecodable, the
      reader thread raised, and ``stdout`` came back ``None``.
    * the command rows begin with the box char ``│``, not ``|``, so the pattern
      matched nothing — and an empty verb set makes EVERY documented verb look
      unregistered, i.e. the guard fails loudly for a reason that has nothing to
      do with runbooks.

    A tightened regex was measured against the real set and did agree exactly
    (37/37, no false positives). It was still the wrong fix: it buys correctness
    today at the price of a dependency on how rich draws a table. ``app.registered_commands``
    is the same answer with nothing to parse. Same source the sibling N3 guard
    uses (tests/unit/test_load_map_declarations.py).
    """
    from drydocs import cli

    return {
        info.name or info.callback.__name__.replace("_", "-")
        for info in cli.app.registered_commands
    }


def test_every_path_a_document_names_exists() -> None:
    """A document that points at a file which moved sends its reader nowhere.

    Three of the four found on 2026-08-04 were the S5 monolith->directory split
    and a package relocate: the kind of change that updates every importer
    automatically and every DOCUMENT not at all. The fifth, found 2026-08-05 the
    day port-prompt joined, was the SAME S5 split — in the document that explains
    it.

    BACKTICKS ARE AN EXISTENCE CLAIM. A rev note explaining that an earlier
    revision cited the wrong path must NOT backtick the dead name -- quote it as
    plain text. This guard caught exactly that case on its first run, in the very
    note describing the error it was written for.
    """
    failures: list[str] = []
    for name, text in _documents().items():
        for path in sorted(set(_PATH.findall(text))):
            if "/" not in path or path in HISTORICAL_PATHS or path in FOREIGN_PATHS:
                continue
            if not (REPO_ROOT / path).exists():
                failures.append(f"{name}: `{path}` does not exist")
    assert not failures, (
        f"{len(failures)} path(s) name something that is not there — fix the path, or add "
        "it to HISTORICAL_PATHS (a statement about the past) or FOREIGN_PATHS (a path in "
        "another repo), with the reason:\n" + "\n".join(failures)
    )


def test_every_cli_verb_a_document_names_is_registered() -> None:
    """A documented command that no longer exists is worse than an undocumented
    one: the reader trusts it and only finds out at the prompt."""
    verbs = _cli_verbs()
    failures: list[str] = []
    for name, text in _documents().items():
        for verb in sorted(set(_VERB.findall(text))):
            if verb in _NOT_VERBS or verb in verbs:
                continue
            failures.append(f"{name}: `drydocs {verb}` is not a registered command")
    assert not failures, f"{len(failures)} stale CLI verb(s):\n" + "\n".join(failures)


def test_extra_docs_exist_and_carry_a_reason() -> None:
    """A named document that gets renamed would otherwise leave this guard
    covering nothing, silently — the failure mode the sibling coverage guard was
    written for, one level up."""
    for rel, why in EXTRA_DOCS.items():
        assert (REPO_ROOT / rel).exists(), (
            f"EXTRA_DOCS names {rel!r}, which does not exist — it moved, and this "
            "guard stopped covering it the moment it did."
        )
        assert (
            isinstance(why, str) and len(why.strip()) >= 40
        ), f"EXTRA_DOCS[{rel!r}] needs a reason it is worth guarding, not {why!r}"


def test_path_exemptions_carry_a_reason_and_are_still_cited() -> None:
    """Shrink-only, the N2 LEDGER_PENDING idiom: an exemption for a path nobody
    cites any more is dead weight that outlives the reason it was added."""
    all_text = "\n".join(_documents().values())
    for label, table in (("HISTORICAL_PATHS", HISTORICAL_PATHS), ("FOREIGN_PATHS", FOREIGN_PATHS)):
        empty = [p for p, why in table.items() if not why.strip()]
        assert not empty, f"{label} exemption without a reason: {empty}"

        unused = [p for p in table if f"`{p}`" not in all_text]
        assert not unused, f"{label} names a path no document cites any more — remove it: {unused}"
