"""J15 publish-boundary VALUE-shape guard (2026-07-27).

Lesson (backlog J15 notes): two sanitization sweeps failed the same way — they
grepped for the FIELD NAME (`seal_id`) while real ids survived for months as
VALUES inside Control-M folder-name strings (`PRARAG-HLDM-<id>-…`). A convention
violated twice needs an enforcement point. This guard scans the PUBLISHABLE
tree (git-tracked files outside `internal/`; the gitignored real extracts are
deliberately out of scope — they are *supposed* to hold real values and must
stay untracked) for the shapes real identifiers take:

  A. bare 5-6 digit ids in taxonomy / bundled-sample / knowledge files;
  B. the numeric segments of anything the folder-name parser recognizes as a
     Control-M folder name, ANYWHERE in the tree — the historical miss class;
  C. values paired with `%%SEAL` in test files — the other historical miss.

Every hit must fall inside the reserved synthetic block 70001-70099 or be
allowlisted here with a recorded reason. The guard deliberately embeds NO real
values — membership in the block is the whole check, so the test itself can
never leak what it protects against.
"""

from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from drydocs_core.orchestration.controlm.folder_name import parse_folder_name

REPO = Path(__file__).resolve().parents[2]

SYNTHETIC_BLOCK = range(70001, 70100)

# Scan A scope: files where bare numeric ids are identity-shaped by context.
BARE_ID_PREFIXES = ("config/taxonomy/", "drydocs/data/samples/", "knowledge/")
# Generated numeric metadata (node/edge/line counts, benchmark timings), not
# identity values.
BARE_ID_EXCLUDED_PREFIXES = (
    "knowledge/depgraph-snapshots/",
    "knowledge/upgrade-plans/p0-benchmark/",
)

BINARY_SUFFIXES = {
    ".png",
    ".webp",
    ".jpg",
    ".jpeg",
    ".gif",
    ".ico",
    ".pdf",
    ".pyc",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
    ".zip",
    ".gz",
    ".lock",
}

# --------------------------------------------------------------------------
# Allowlist: (path, value) pairs that may sit outside the synthetic block,
# each with a recorded reason. Ruling 2026-07-27 (J15 build; SME may flip):
# 6-digit Control-M surrogate TABLE KEYS (folder ids) are private-DB row
# keys with no external meaning — no SEAL/roster/credential semantics —
# so they stay. Identity-shaped values (SEAL/FID/roster/DL) never get
# allowlisted; they get resweeped into the block instead.
# --------------------------------------------------------------------------
CTM_FOLDER_KEYS = frozenset(
    {
        "161014",
        "161015",
        "161016",
        "161020",
        "160500",
        "160501",
        "162001",
        "161999",
    }
)
ALLOWLIST: dict[str, tuple[frozenset[str], str]] = {
    "knowledge/org/org-quad-chart.mmd": (
        frozenset({"166534", "334155"}),
        "hex COLOR codes in Mermaid style directives (stroke:#166534 = green-800, "
        "#334155 = slate-700) whose six hex chars happen to be all digits — colors, "
        "not ids. Exposed to this scan when S14 moved the file under knowledge/",
    ),
    "knowledge/org/seal-application-hierarchy.md": (
        frozenset({"145214"}),
        "hex COLOR code in a Mermaid style directive (stroke:#145214) — a color, not "
        "a SEAL id; every actual id in the file is synthetic-block. Same S14 exposure",
    ),
    "config/taxonomy/controlm.yaml": (
        CTM_FOLDER_KEYS,
        "Control-M surrogate folder table keys of the sanitized sample family",
    ),
    "drydocs/data/samples/controlm_folders__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_jobs__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_conditions_in__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_conditions_out__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_dependencies__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
    "drydocs/data/samples/controlm_hosts__sample.csv": (
        CTM_FOLDER_KEYS,
        "sample-family folder table keys",
    ),
}

_BARE_ID = re.compile(r"\b\d{5,6}\b")
# Candidate Control-M folder-name tokens: 6-letter prefix + >=2 dash segments.
_FOLDER_TOKEN = re.compile(r"\b[A-Z]{6}(?:-[A-Z0-9]{2,20}){2,}\b")
_SEAL_PAIR = re.compile(r"%%SEAL\b[^0-9\n]{0,40}(\d{4,7})")


def _tracked_files() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files"],
            cwd=REPO,
            capture_output=True,
            encoding="utf-8",
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable — publishable tree cannot be enumerated")
    return [
        line
        for line in out.splitlines()
        if line
        and not line.startswith("internal/")
        and Path(line).suffix.lower() not in BINARY_SUFFIXES
    ]


def _read(relpath: str) -> str:
    # Tracked-but-locally-deleted files (another session's staged work) scan
    # as empty — the committed tree is guarded by CI on the pushed state.
    try:
        return (REPO / relpath).read_text(encoding="utf-8", errors="ignore")
    except FileNotFoundError:
        return ""


def _allowed(relpath: str, value: str) -> bool:
    entry = ALLOWLIST.get(relpath)
    return bool(entry and value in entry[0])


def _in_block(value: str) -> bool:
    return int(value) in SYNTHETIC_BLOCK


def test_bare_ids_in_taxonomy_samples_knowledge_are_synthetic() -> None:
    """Scan A: any bare 5-6 digit id in identity-bearing file families must be
    in the reserved block or allowlisted with a reason."""
    violations: list[str] = []
    for rel in _tracked_files():
        if not rel.startswith(BARE_ID_PREFIXES):
            continue
        if rel.startswith(BARE_ID_EXCLUDED_PREFIXES):
            continue
        for m in _BARE_ID.finditer(_read(rel)):
            v = m.group(0)
            if not _in_block(v) and not _allowed(rel, v):
                violations.append(f"{rel}: {v}")
    assert not violations, (
        "bare 5-6 digit ids outside the reserved synthetic block 70001-70099 "
        "(resweep the value or allowlist it WITH A REASON in "
        "test_publish_boundary_values.py):\n" + "\n".join(sorted(set(violations)))
    )


def test_folder_name_numeric_segments_are_synthetic_everywhere() -> None:
    """Scan B (the historical miss): every numeric segment of every string the
    folder-name parser recognizes, in EVERY tracked file, must be in-block."""
    violations: list[str] = []
    for rel in _tracked_files():
        text = _read(rel)
        for m in _FOLDER_TOKEN.finditer(text):
            parsed = parse_folder_name(m.group(0))
            if not parsed.prefix_recognized:
                continue
            for seg in parsed.segments:
                if (
                    seg.isdigit()
                    and 5 <= len(seg) <= 6
                    and not _in_block(seg)
                    and not _allowed(rel, seg)
                ):
                    violations.append(f"{rel}: {m.group(0)} -> segment {seg}")
    assert not violations, (
        "folder-name-embedded ids outside the reserved synthetic block "
        "70001-70099 — the exact class two sweeps missed. Resweep the value "
        "(and its internal/ twin key row) rather than allowlisting:\n"
        + "\n".join(sorted(set(violations)))
    )


_DOMAIN_TOKEN = re.compile(r"\b[a-z0-9-]+\.(?:com|net|org|io)\b", re.IGNORECASE)
# Domains .gitignore comments MAY name: none today. The public site domain
# (dry-docs.com) would be the first legitimate entry if a rule ever needs it.
GITIGNORE_DOMAIN_ALLOWLIST: frozenset[str] = frozenset()


def test_gitignore_comments_name_no_domains() -> None:
    """Scan D (J27): the root .gitignore sits in the publishable tree and its
    comments explain what the ignored corpora ARE — which is the useful half.
    An internal domain in a comment is a real value in a publishable file, the
    exact class CLAUDE.md §3 bans. Shape-guarded like the id scans: the test
    embeds no real domain, so it cannot leak what it protects against."""
    violations = [
        m.group(0)
        for m in _DOMAIN_TOKEN.finditer(_read(".gitignore"))
        if m.group(0).lower() not in GITIGNORE_DOMAIN_ALLOWLIST
    ]
    assert not violations, (
        ".gitignore names domain(s) — describe the corpus instead, or allowlist "
        "WITH A REASON in test_publish_boundary_values.py: " + ", ".join(sorted(set(violations)))
    )


def test_seal_variable_values_in_tests_are_synthetic() -> None:
    """Scan C: a value paired with %%SEAL in any tracked test file is a SEAL id
    by construction — it must come from the synthetic block."""
    violations: list[str] = []
    for rel in _tracked_files():
        if not rel.startswith("tests/"):
            continue
        for m in _SEAL_PAIR.finditer(_read(rel)):
            if not (m.group(1).isdigit() and _in_block(m.group(1))):
                violations.append(f"{rel}: %%SEAL value {m.group(1)}")
    assert not violations, (
        "%%SEAL values outside the reserved synthetic block 70001-70099 in "
        "test files:\n" + "\n".join(sorted(set(violations)))
    )


# Scan E (J13 class 2, SME ruling 2026-08-11): Control-M data-center names.
# Shape: <env-letter><instance>-E<hhmm>-<suffix>, e.g. the page's own T032-E0700-DMA.
# The SME ruled the publishable tree carries a NON-PRODUCTION environment letter in
# position 1, so no published example names a live production data center. `P` is
# production and is therefore the one letter banned here.
#
# Shape-guarded like every scan above: the rule is "position 1 is not P", so the test
# names no real data center and cannot leak the inventory it protects. The real values
# live in internal/standards/technology/data-center-inventory.md.
_DC_NAME = re.compile(r"\b([A-Z])(\d{3})-E(\d{4})-([A-Z]{2,3})\b")
PRODUCTION_ENV_LETTER = "P"


def test_data_center_names_are_not_production() -> None:
    """Scan E: no publishable file may carry a production-environment data-center
    name. Position 1 of the DC name is the environment letter (see
    knowledge/standards/technology/data-center-naming-convention.md); the swap to a
    non-production letter is the sanitization, not a typo, so a `P` reappearing here
    means a real value came back in — most likely pasted from a live query."""
    violations: list[str] = []
    for rel in _tracked_files():
        for m in _DC_NAME.finditer(_read(rel)):
            if m.group(1) == PRODUCTION_ENV_LETTER:
                violations.append(f"{rel}: {m.group(0)}")
    assert not violations, (
        "production data-center name(s) in the publishable tree — position 1 must "
        "not be the production environment letter. Swap position 1 to the "
        "non-production letter (the grammar is unchanged; only the environment "
        "value moves) and keep the real value in the internal/ twin:\n"
        + "\n".join(sorted(set(violations)))
    )


# ---- Scan D: redacted infrastructure names (SME ruling 2026-08-25) ----------

#: sha256 of every token the publish boundary redacts by NAME rather than by
#: shape. HASHED, never written literally, for the reason this module's docstring
#: gives: a guard that embeds the value it protects leaks it in the act of
#: guarding. Both cases are pinned because a lowercase spelling publishes the
#: token just as effectively as an uppercase one.
#:
#: Entry 1 is the Oracle database alias behind `[db]` in every `*@[db].psgmgr.*`
#: id. The signed grammar (gate `source-registry-v2` 2026-07-31; `gate-log.md`
#: :1075 and :2971) redacts the DATABASE and keeps the schema. The SME ruled
#: 2026-08-25 that it is an ALIAS rather than a SID and is still not published.
#: The real value lives in `internal/standards/technology/database-inventory.md`,
#: which is outside the publish boundary and is the designed home for the
#: placeholder -> value key.
REDACTED_NAME_HASHES = {
    "acf450137af266f39ded914223648645fb3a4144bbe4c5f73e2789ee62d7cb68",
    "5b511eb811e26bfa455d1ffc224b397f18cfd27908be74a549c1eeae35f12141",
}

#: The ONE published form that is allowed, and why. The token also serves as a
#: deprecated env-var PREFIX (`<alias>_LOGDIR`, `_CALLER`, `_DSN`), kept so a live
#: shell or scheduled job exporting the old name keeps working; renaming it
#: defeats the only reason it exists and the failure is silent. ADR 0014 clause 1
#: (accepted 2026-08-25) rules the prefix DROPPED at the next port after
#: acceptance, so THIS ALLOWANCE IS TEMPORARY -- when that lands, delete this
#: constant and the guard tightens to "no published form at all".
_ENV_PREFIX_MARKER = "_"

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9]{4,15}")


def test_redacted_infrastructure_names_are_not_published() -> None:
    """A name the boundary redacts must not appear in the publishable tree.

    The J15 lesson one level over: those sweeps grepped the FIELD name while real
    values survived as VALUES. This is the mirror case -- the id grammar redacted
    the database in every id, and the same token then sat in prose in a skill, in
    `PORT-MANIFEST.yaml` and in a port archive, doing a different job. Three
    tracked files published exactly what twenty-eight ids were careful to remove.
    """
    import hashlib

    offenders: list[str] = []
    # _tracked_files() already drops internal/ and binaries -- the publishable
    # tree by the same definition the other three scans use, not a second one.
    for rel in _tracked_files():
        body = _read(rel)
        for match in _TOKEN.finditer(body):
            token = match.group(0)
            if hashlib.sha256(token.encode()).hexdigest() not in REDACTED_NAME_HASHES:
                continue
            if body[match.end() : match.end() + 1] == _ENV_PREFIX_MARKER:
                # `<token>_...` is the env-var PREFIX, the temporary allowance
                # above. A trailing underscore is the whole distinction the SME
                # ruling draws: the bare token is the published NAME, the
                # prefixed form is a compatibility mechanism with a scheduled
                # end. Enumerating suffixes instead (_LOGDIR, _CALLER) was the
                # first cut and missed _DSN and the bare `<token>_` references
                # in prose -- an allowlist of spellings rots the moment someone
                # writes a fourth one.
                continue
            line = body[: match.start()].count(chr(10)) + 1
            offenders.append(f"{rel}:{line}")

    assert not offenders, (
        "a redacted infrastructure name is published in: "
        + ", ".join(sorted(set(offenders)))
        + ". The value belongs in internal/ (outside the boundary), never in a "
        "tracked publishable file. This guard names the FILE, never the value."
    )
