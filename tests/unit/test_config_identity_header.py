"""J58 — the four-key identity header, enforced from ONE JSON Schema.

`schema:` / `source:` / `classification:` / `updated:` was a convention with an
exemplar (`config/source-mappings/design-docs.yaml`) and no enforcement point,
so it held where somebody remembered it and lapsed everywhere else. This guard
is the enforcement point, and `config/schemas/identity-header.schema.json` is
the single expression of the rule — N bespoke per-family assertions is exactly
what the acceptance rules out.

FILE CLASS DECIDES WHO MUST CARRY IT, and every class is enumerated in
:data:`CLASSES` below with its reason. The posture is DEFAULT-DENY, the same
rule `test_module_boundary.py` applies to modules: a tracked YAML matching no
class fails as UNCLASSIFIED. That is the part that keeps working after this
item closes — a new governed file cannot quietly arrive without a header,
because arriving without a class is itself the failure.

PRESENCE AND SHAPE ONLY. Nothing here compares `updated` against anything; the
lying-date problem is J59's, split off because the check that would catch it
cannot run in CI.

TWO THINGS THIS GUARD DOES NOT OWN. Gate prompts keep `test_gate_pages.py` as
their enforcement point — this module supplies the schema profile their date
key validates against, and does not add a second guard over the same 60 files.
And the per-family shape schemas (`test_config_schemas.py`) are untouched: they
own what a source-mapping or a registry looks like, this owns the header every
governed file shares.
"""

from __future__ import annotations

import datetime as dt
import json
import subprocess
from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml", reason="PyYAML not installed")
jsonschema = pytest.importorskip("jsonschema", reason="jsonschema not installed (dev group)")

from jsonschema import Draft202012Validator  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
SCHEMA_FILE = REPO / "config" / "schemas" / "identity-header.schema.json"

#: Backlog item files are governed by their own v3 schema and their own guard
#: (`test_backlog.py`), one item per file, and are excluded here for the reason
#: the acceptance measured its baseline over "non-backlog" YAML: 600+ item files
#: carrying a duplicated four-key block would be noise, not provenance.
_EXCLUDED_PREFIXES = ("docs/restructure/backlog/",)

# ---------------------------------------------------------------------------
# THE CLASS MAP. Longest matching prefix wins, so a specific file can carve
# itself out of its directory's class. Every entry carries its reason, because
# the reason is the part a later reader needs in order to classify the NEXT
# file rather than guessing from the neighbours.
# ---------------------------------------------------------------------------
REQUIRED = "required"  # governed data: schema + classification + updated
SOURCE_DESCRIBING = "source-describing"  # + source: the file exists to describe one
GATE_PROMPT = "gate-prompt"  # schema + classification + updated; source is in meta
TEMPLATE = "template"  # copied before use: `updated` FORBIDDEN
FRAGMENT = "fragment"  # one section of a composed document
TOOLING = "tooling"  # somebody else's schema
GENERATED = "generated"  # written by a tool
FIXTURE = "fixture"  # the shape IS the thing under test

CLASSES: dict[str, tuple[str, str]] = {
    # -- governed data ------------------------------------------------------
    "config/": (REQUIRED, "pipeline configuration read by loaders and by people as fact"),
    "config/source-mappings/": (
        SOURCE_DESCRIBING,
        "the exemplar family — a field ledger exists to describe exactly ONE registered "
        "source and is meaningless without naming it, so `source` is required here",
    ),
    "config/gate-prompts/": (
        GATE_PROMPT,
        "already carry an enforced meta header (test_gate_pages); J58 adds the date key",
    ),
    "config/schemas/": (
        TOOLING,
        "JSON Schema files — their own $schema/$id IS their identity block",
    ),
    "config/taxonomy-ontology-map/00-header.yaml": (
        REQUIRED,
        "the composition's header — this is where that family's identity lives",
    ),
    "config/taxonomy-ontology-map/": (
        FRAGMENT,
        "per-domain mapping fragments concatenated into one document; several are "
        "YAML lists at the root and cannot hold a mapping key at all",
    ),
    "graph-tests/": (REQUIRED, "declarative graph assertions — governed data, run against the KG"),
    "reference/REGISTRY.yaml": (REQUIRED, "the external-reference index"),
    "PORT-MANIFEST.yaml": (REQUIRED, "per-path port dispositions — the cross-repo contract"),
    "docs/restructure/roadmap.yaml": (REQUIRED, "the phase list behind the rendered roadmap"),
    "docs/design/templates/": (
        REQUIRED,
        "deterministic outline SPECS the renderer reads (Epic L), not copier templates — "
        "named 'templates' for what they produce, governed data for what they are",
    ),
    "docs/design/feedback/": (
        GENERATED,
        "HITL feedback exports (L5 save button / L6 paper transcription) — a tool writes "
        "them, so a hand-maintained header would be overwritten or would lie",
    ),
    "internal/": (REQUIRED, "Internal governed data — never published, still governed"),
    "knowledge/": (REQUIRED, "Internal-Public design prose and its data"),
    "drydocs_core/ontology/relationship_vocabulary/": (
        FRAGMENT,
        "per-domain vocabulary fragments (S5) composed into one registry; 00-header.yaml "
        "is pure prose and parses to nothing at all",
    ),
    # -- template class: `updated` forbidden --------------------------------
    ".claude/skills/research-probe-discipline/references/": (
        TEMPLATE,
        "*.template.yaml — a session COPIES these before filling them in, so a date here "
        "belongs to the copy; a hand-maintained date in a merged-on-update file is the "
        "ADR 0015 D4 conflict seam",
    ),
    ".claude/skills/": (REQUIRED, "skill-owned governed data (the runbook template spec)"),
    # -- somebody else's schema ---------------------------------------------
    ".github/": (TOOLING, "GitHub Actions workflow — GitHub's schema, not ours"),
    ".pre-commit-config.yaml": (TOOLING, "pre-commit's own schema"),
    "compose.yaml": (
        TOOLING,
        "Docker Compose's own schema (O72's one-command console stack). A `schema:` or "
        "`classification:` key at the top level is not something Compose allows, so the "
        "block cannot go there; the file's provenance is its header comment instead",
    ),
    # -- fixtures ------------------------------------------------------------
    "tests/fixtures/": (FIXTURE, "a fixture's shape is the thing under test"),
    # -- one-offs ------------------------------------------------------------
    "docs/restructure/backlog.yaml": (
        GENERATED,
        "the TOMBSTONE of the pre-ADR-0013 single-file backlog (CLAUDE.md section 0). It is "
        "a marker pointing at items/, not live data, so a header claiming it is current "
        "would be the one thing it must not say",
    ),
}


def _schema() -> dict:
    return json.loads(SCHEMA_FILE.read_text(encoding="utf-8"))


def _tracked_yaml() -> list[str]:
    try:
        out = subprocess.run(
            ["git", "ls-files", "*.yaml", "*.yml"],
            cwd=REPO,
            capture_output=True,
            encoding="utf-8",
            check=True,
        ).stdout
    except (OSError, subprocess.CalledProcessError):  # pragma: no cover
        pytest.skip("git unavailable — the tracked YAML set cannot be enumerated")
    return [
        line.replace("\\", "/")
        for line in out.splitlines()
        if line and not line.replace("\\", "/").startswith(_EXCLUDED_PREFIXES)
    ]


def classify(relpath: str) -> tuple[str, str] | None:
    """Longest matching prefix wins; None means UNCLASSIFIED (a failure)."""
    best: tuple[str, tuple[str, str]] | None = None
    for prefix, entry in CLASSES.items():
        if relpath == prefix or relpath.startswith(prefix):
            if best is None or len(prefix) > len(best[0]):
                best = (prefix, entry)
    return best[1] if best else None


def _load(relpath: str):
    return yaml.safe_load((REPO / relpath).read_text(encoding="utf-8"))


def normalize_dates(doc):
    """YAML turns a bare `2026-07-20` into a date; the schema wants its ISO form.

    Normalizing HERE rather than typing the key loosely in the schema is the
    deliberate half: it lets the schema require a real date string, so a typo
    like `2026-7-20` or a free-text "last week" fails instead of passing as
    "some value is present".
    """
    if isinstance(doc, dict):
        return {k: normalize_dates(v) for k, v in doc.items()}
    if isinstance(doc, dt.date | dt.datetime):
        return doc.isoformat()[:10]
    return doc


# ---------------------------------------------------------------------------
# The rule
# ---------------------------------------------------------------------------


def test_every_tracked_yaml_has_a_declared_class() -> None:
    """DEFAULT-DENY: an unclassified file is the failure, not a free pass.

    This is the assertion that keeps working after this item closes. A new
    governed config arriving without a header would otherwise be invisible —
    here it fails on arrival, and the fix is to add its row above with the
    reason, which is the same act as deciding whether it needs the block.
    """
    unclassified = [rel for rel in _tracked_yaml() if classify(rel) is None]
    assert not unclassified, (
        "tracked YAML in no declared file class (UNCLASSIFIED) — add each to CLASSES in "
        "this file with its class and the reason: " + ", ".join(sorted(unclassified))
    )


def _validator_for(profile: str) -> Draft202012Validator:
    schema = _schema()
    return Draft202012Validator({**schema, "$ref": f"#/$defs/{profile}"})


def _check(cls: str, profile: str) -> list[str]:
    validator = _validator_for(profile)
    offenders: list[str] = []
    for rel in _tracked_yaml():
        entry = classify(rel)
        if entry is None or entry[0] != cls:
            continue
        doc = normalize_dates(_load(rel))
        if not isinstance(doc, dict):
            offenders.append(f"{rel}: not a YAML mapping, so it cannot carry the header")
            continue
        for error in validator.iter_errors(doc):
            if error.path:
                continue  # a nested shape problem belongs to that family's own schema
            offenders.append(f"{rel}: {error.message}")
    return offenders


def test_governed_data_files_carry_the_identity_block() -> None:
    """schema + classification + updated — the triple three closed family schemas
    (data-centers, domains, editions) already settled on independently."""
    offenders = _check(REQUIRED, "governed")
    assert not offenders, (
        "governed config files missing or malforming the identity header "
        "(config/schemas/identity-header.schema.json):\n  " + "\n  ".join(sorted(offenders))
    )


def test_source_describing_files_also_name_their_source() -> None:
    """config/source-mappings/**: a field ledger with no `source:` describes nothing."""
    offenders = _check(SOURCE_DESCRIBING, "full")
    assert not offenders, "source-describing files missing the full block:\n  " + "\n  ".join(
        sorted(offenders)
    )


def test_gate_prompts_carry_the_dated_profile() -> None:
    """Clause (d): the 60 specs gain `updated:` under the same schema.

    Asserted here as the SCHEMA's rule; test_gate_pages.py stays the guard that
    reads those files as gate prompts, so there is one enforcement point per
    concern rather than two guards racing over the same directory.
    """
    offenders = _check(GATE_PROMPT, "gatePrompt")
    assert not offenders, "gate prompts missing the dated identity profile:\n  " + "\n  ".join(
        sorted(offenders)
    )


def test_template_class_files_carry_no_hand_maintained_date() -> None:
    """FORBIDDEN, and the reason is mechanical rather than stylistic.

    A `.template.yaml` is copied before use and its updates arrive as a
    three-way merge (ADR 0015 D4). A date inside it conflicts on every single
    update, forever, and the conflict is never informative — the copy's date was
    always the copy's business.
    """
    offenders: list[str] = []
    for rel in _tracked_yaml():
        entry = classify(rel)
        if entry is None or entry[0] != TEMPLATE:
            continue
        doc = _load(rel)
        if isinstance(doc, dict) and "updated" in doc:
            offenders.append(rel)
    assert not offenders, (
        "template-class files carry a hand-maintained `updated:` — it will conflict on "
        "every three-way merge and tells the reader nothing: " + ", ".join(sorted(offenders))
    )


def test_the_schema_itself_is_valid_and_says_which_classes_exist() -> None:
    """The schema is the rule's single expression, so it has to BE the rule.

    Two things worth failing over: that it compiles at all, and that its prose
    names every class the map uses — a class enumerated only in Python is a
    class the next person reads a glob to discover, which the acceptance rules
    out in as many words.
    """
    schema = _schema()
    Draft202012Validator.check_schema(schema)
    description = schema["description"]
    for label in ("REQUIRED", "FORBIDDEN", "FRAGMENT", "TOOLING", "GENERATED", "FIXTURE"):
        assert label in description, f"the schema's prose does not name the {label} class"
    declared = {entry[0] for entry in CLASSES.values()}
    assert declared <= {
        REQUIRED,
        SOURCE_DESCRIBING,
        GATE_PROMPT,
        TEMPLATE,
        FRAGMENT,
        TOOLING,
        GENERATED,
        FIXTURE,
    }


def test_every_class_entry_carries_a_reason() -> None:
    """A class without a reason is a glob nobody can find, one level up."""
    missing = [prefix for prefix, (_, reason) in CLASSES.items() if not reason.strip()]
    assert not missing, f"class entries with no recorded reason: {missing}"
