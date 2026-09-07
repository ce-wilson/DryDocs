"""Generate the O12 admin-page enforcement matrix (wf-admin-config-01 (4)).

The matrix is GENERATED, never hand-typed: this script scans the SURFACES
registry below against the repo -- every referenced file/dir/test must exist,
every top-level config/ surface must be covered -- and emits
``web/src/generated/enforcement-matrix.json``, which /admin/config renders as
a build-time artifact (the board-render pattern: registry = truth, render =
artifact, ``tests/unit/test_enforcement_matrix.py`` = the drift guard).

Status vocabulary (wf-admin-config-01 (6)):
- ``unguarded``    -- no guard test. (Until O54, 2026-09-03, this branch also
                     fired for ANY ``code_resident`` row regardless of its
                     guards -- right for the launcher registry the flag was
                     invented for, which had none until its G26 migration to
                     config/launcher-registry.yaml on 2026-07-27, and simply
                     wrong once N3/N6 gave the canonical load sequence real
                     guard tests while it stayed code-resident by design.)
- ``gate-pending`` -- the surface carries entries awaiting HITL
                     (``status: proposed`` / ``planned`` / ``placeholder``).
- ``enforced``     -- guarded and nothing pending.

``code_resident`` is a SEPARATE fact -- WHERE the config lives (in a module,
not a config file) -- and the row carries it beside the status rather than
folding it in. A code-resident row names its ``symbols``; only those
declarations render as its content and are scanned for pending markers and
env references, never the whole module.

CI freshness is LAST-RUN metadata only (user decision 2026-07-17): if
``var/ci-last-run.json`` exists (dropped by a CI artifact download), it is
embedded verbatim; otherwise ``ci_last_run`` is null and the page says so --
no live CI polling, ever.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "web" / "src" / "generated" / "enforcement-matrix.json"
CI_ARTIFACT = REPO / "var" / "ci-last-run.json"

CONTENT_CAP = 60_000
_PENDING_RE = re.compile(r"status:\s*(proposed|planned|placeholder)\b")
# Explicit env-reference forms only: ${VAR}, os.environ["VAR"]/get("VAR"),
# env: VAR. Loose "env ... WORD" matching produced false positives.
_ENV_REF_RE = re.compile(
    r"\$\{([A-Z][A-Z0-9_]+)\}"
    r"|os\.environ(?:\.get)?\(\s*[\"']([A-Z][A-Z0-9_]+)"
    r"|\benv:\s*([A-Z][A-Z0-9_]+)"
)

# -- The surface registry (verified against the repo at every generation) -----
# file: repo-relative path; dirs end with '/'. code_resident marks a surface
# whose config lives in a MODULE (see the docstring): such a row names its
# `symbols`, and only those declarations are rendered and scanned.
SURFACES: list[dict] = [
    {
        "id": "source-registry",
        "title": "Source registry",
        "file": "config/source-registry.yaml",
        "consumers": ["drydocs_core/source_registry.py", "drydocs/loaders/"],
        "guard_tests": ["test_source_registry.py"],
        "gate_ref": "per-source gates (add-source-object flow)",
    },
    {
        "id": "loader-source-overlay",
        "title": "Loader-source binding overlay",
        "file": "config/loader-source-overlay.yaml",
        "consumers": ["drydocs_core/source_registry.py", "drydocs/cli.py"],
        "guard_tests": ["test_source_registry.py"],
        "gate_ref": "gate source-registry-v2 D2 (2026-07-31; the company T19 rebind seam)",
    },
    {
        "id": "source-mappings",
        "title": "Column-mapping ledgers",
        "file": "config/source-mappings/",
        "consumers": ["drydocs/loaders/sql/", "drydocs/loaders/base.py"],
        "guard_tests": ["test_source_mappings.py", "test_source_mapping_drift.py"],
        "gate_ref": "doc-08 ledgers (Epic N)",
    },
    {
        "id": "audit-fields",
        "title": "Audit envelope",
        "file": "config/audit-fields.yaml",
        "consumers": ["drydocs/loaders/cypher/"],
        "guard_tests": ["test_audit_fields.py"],
        "gate_ref": "doc-06 per-source envelope",
    },
    {
        "id": "precedence",
        "title": "Precedence",
        "file": "config/precedence.yaml",
        "consumers": ["drydocs_core/precedence.py"],
        "guard_tests": ["test_precedence.py"],
        "gate_ref": None,
    },
    {
        "id": "classification",
        "title": "Sensitivity classification",
        "file": "config/classification.yaml",
        "consumers": ["drydocs/review/publishing/"],
        "guard_tests": ["test_classification.py", "test_publishing.py"],
        "gate_ref": "PUBLISH-BOUNDARY.md",
    },
    {
        "id": "taxonomy-ontology-map",
        "title": "Taxonomy <-> Ontology map",
        "file": "config/taxonomy-ontology-map/",
        "consumers": ["drydocs_core/ontology/", "drydocs/loaders/"],
        "guard_tests": ["test_taxonomy_ontology_map.py"],
        "gate_ref": "HITL gate (docs/restructure/03-hitl-sme-flow.md)",
    },
    {
        "id": "relationship-vocabulary",
        "title": "Relationship vocabulary",
        "file": "drydocs_core/ontology/relationship_vocabulary/",
        "consumers": ["drydocs/loaders/cypher/", "drydocs_core/ontology/"],
        "guard_tests": ["test_controlm_cypher.py", "test_schema.py"],
        "gate_ref": "RELATIONSHIP_GUIDE.md + per-edge gates",
    },
    {
        "id": "taxonomy-captures",
        "title": "Taxonomy captures",
        "file": "config/taxonomy/",
        "consumers": ["drydocs_core/ontology/"],
        "guard_tests": ["test_namespaces.py"],
        "gate_ref": "taxonomy-importer layer (CLAUDE.md section 1)",
    },
    {
        "id": "manual-loads",
        "title": "Manual loads (tier 5)",
        "file": "config/manual-loads/",
        "consumers": ["drydocs/loaders/manual_loads.py"],
        "guard_tests": ["test_manual_loads.py"],
        "gate_ref": "K2 match-policy gate (24/24, 2026-07-14)",
    },
    {
        "id": "seal-contact-overrides",
        "title": "User override lists (M2 store)",
        "file": "config/overrides/",
        "consumers": ["drydocs_core/mapping_store.py", "drydocs_api/mappings.py"],
        "guard_tests": ["test_mapping_store.py", "test_mapping_api.py"],
        "gate_ref": "ui-write-surface gate SME-3 — M2 origin-flagged store (2026-07-21)",
    },
    {
        "id": "review-labels",
        "title": "Review labels",
        "file": "config/review-labels.yaml",
        "consumers": ["drydocs/review/publishing/"],
        "guard_tests": ["test_review_labels.py"],
        "gate_ref": None,
    },
    {
        "id": "glossary",
        "title": "Business glossary (schema half)",
        "file": "config/glossary/",
        "consumers": [],  # G34 scaffold 2026-08-21: reservation only -- no loader reads it yet; content + consumer arrive with epic MM
        "guard_tests": [],  # honest red flag until the content pass lands its shape test
        "gate_ref": "G34 reservation (business-application-identity gate section F2, 2026-07-27); definitions half = internal/glossary/ (Internal)",
    },
    {
        "id": "crosswalks",
        "title": "Orchestrator crosswalks",
        "file": "config/crosswalks/",
        "consumers": ["external/orchestration/"],
        "guard_tests": [],  # gate-signed (F1 13/13, F2 17/17) but NO drift test -- honest red flag
        "gate_ref": "F1 autosys-crosswalk + F2 airflow-crosswalk sign-offs (2026-07-14)",
    },
    {
        "id": "gate-record",
        "title": "Gate prompts + gate log",
        "file": "config/gate-prompts/",
        "extra_files": ["config/gate-log.md"],
        "consumers": ["drydocs/review/publishing/"],
        "guard_tests": ["test_gate_pages.py"],
        "gate_ref": "(is the gate record)",
    },
    {
        "id": "doc-source-registry",
        "title": "Doc-source registry",
        "file": "config/doc-source-registry.yaml",
        "consumers": ["drydocs/loaders/"],
        "guard_tests": ["test_doc_registry.py"],
        "gate_ref": "Q4 docmeta gate (ADR 0006)",
    },
    {
        "id": "doc-capture",
        "title": "Doc-capture policy (page ceiling, delay, scheme allow-list)",
        "file": "config/doc-capture.yaml",
        "consumers": [
            "scripts/external_vendor_scrape.py",
            "drydocs_docmeta/connectors/web.py",
        ],
        "guard_tests": ["test_docmeta_pipeline.py", "test_docmeta_connectors.py"],
        "gate_ref": None,
    },
    {
        "id": "data-zones",
        "title": "Data zones (path modes + the non-overlap invariant)",
        "file": "config/data-zones.yaml",
        "consumers": [
            "drydocs_core/data_zones.py",
            "drydocs_core/data_root.py",
            # the READ half of the invariant: acquisition.drop_dir rows
            "config/source-registry.yaml",
        ],
        "guard_tests": ["test_data_zones.py"],
        "gate_ref": None,
    },
    {
        "id": "source-bindings",
        "title": "Source bindings (one connection profile per carrier; variable NAMES only)",
        "file": "config/source-bindings.yaml",
        "consumers": [
            "drydocs_core/source_bindings.py",
            "drydocs_core/env_refs.py",
            # the `binding:` field on every system row points here, and the guard
            # checks the reference in BOTH directions
            "config/source-registry.yaml",
            "drydocs/cli_schema.py",
        ],
        "guard_tests": ["test_source_bindings.py"],
        "gate_ref": None,
    },
    {
        "id": "log-kinds",
        "title": "Log kinds (root, level, retention, rotation, format per kind)",
        "file": "config/log-kinds.yaml",
        "consumers": [
            "drydocs_core/log_kinds.py",
            "drydocs_core/run_log.py",
            "drydocs_core/adapters/sql_run_log.py",
            "agents/common/llm_ledger.py",
        ],
        "guard_tests": ["test_log_kinds.py", "test_loader_run_log.py"],
        "gate_ref": None,
    },
    {
        "id": "dev-environment",
        "title": "Dev/test environment names",
        "file": "config/dev-environment.yaml",
        "consumers": [".env.example", "agents/.env.example", "web/.env.example"],
        "guard_tests": ["test_dev_environment.py"],
        "gate_ref": None,
    },
    {
        "id": "launcher-registry",
        "title": "Launcher registry",
        "file": "config/launcher-registry.yaml",
        # S2 (ADR 0008): commands.py became the vendor-neutral orchestration/shell.py.
        # The registry was never Control-M-specific — it maps executables to launcher
        # types, which is exactly the knowledge that survives an orchestrator swap.
        "consumers": ["drydocs_core/orchestration/shell.py", "drydocs_lineage/"],
        "guard_tests": ["test_launcher_registry.py", "test_command_parser.py"],
        "gate_ref": None,
    },
    {
        "id": "orchestrator-crosswalks",
        "title": "Orchestrator crosswalks (native -> BMC baseline)",
        "file": "config/crosswalks/",
        # S2 gave this its FIRST runtime consumer (ADR 0008 rule 3). Until then a
        # `fidelity: no-equivalent` row was prose nothing could enforce; crosswalk.py
        # raises NoEquivalent instead of picking the nearest Control-M label.
        "consumers": ["drydocs_core/orchestration/crosswalk.py"],
        "guard_tests": ["test_orchestration_crosswalk.py"],
        "gate_ref": "autosys-crosswalk / airflow-crosswalk (both SIGNED OFF 2026-07-14)",
    },
    {
        "id": "config-schemas",
        "title": "Config-family JSON Schemas",
        "file": "config/schemas/",
        # S6: shape contracts for the config families — editor-time validation
        # with no Python dependency on the package. The guard validates every
        # live family file against its schema AND proves the schemas stand
        # alone (subprocess without drydocs_core on the path).
        "consumers": ["tests/unit/test_config_schemas.py"],
        "guard_tests": ["test_config_schemas.py"],
        "gate_ref": None,
    },
    {
        "id": "canonical-load-sequence",
        "title": "Canonical load sequence",
        # O54: the one code-resident surface, BY DESIGN rather than by neglect.
        # The ordered load sequence, its operator profiles and the scheduled
        # omissions (each with a written reason) are declarations in
        # drydocs/cli_shared.py, re-exported by drydocs/cli.py (S8), and every
        # operator surface DERIVES from them: scripts/ingest.sh calls
        # load_profile at run time, the runbook's Appendix B is held to the
        # same answer, and the load map is rendered from them (N3/N4/N5/N6).
        # Moving them to YAML would put a load ORDER in a file nothing
        # executes; the guards below are what makes code residency safe.
        "file": "drydocs/cli_shared.py",
        "code_resident": True,
        "symbols": ["CANONICAL_LOAD_SEQUENCE", "LOAD_PROFILES", "SCHEDULED_INGEST_EXCLUSIONS"],
        "consumers": ["drydocs/cli.py", "scripts/ingest.sh", "scripts/render_load_map.py"],
        "guard_tests": [
            "test_load_sequence_surfaces.py",
            "test_load_map_declarations.py",
            "test_load_map_json.py",
        ],
        "gate_ref": "N3 (declarations) / N6 (profiles) — guarded declarations, not a gate",
    },
]

# Top-level config/ entries that are deliberately NOT surfaces.
CONFIG_EXEMPT = {"README.md"}


def _read_capped(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > CONTENT_CAP:
        return (
            text[:CONTENT_CAP]
            + f"\n[truncated at {CONTENT_CAP} chars -- full file at {path.name}]\n"
        )
    return text


def _scan_text(text: str) -> tuple[int, list[str]]:
    """Pending-marker count + env-var references in one text."""
    env_refs = {m.group(1) or m.group(2) or m.group(3) for m in _ENV_REF_RE.finditer(text)}
    return len(_PENDING_RE.findall(text)), sorted(env_refs)


def _scan(paths: list[Path]) -> tuple[int, list[str]]:
    """Pending-marker count + env-var references across the surface's files."""
    pending = 0
    env_refs: set[str] = set()
    for p in paths:
        if p.suffix not in {".yaml", ".yml", ".md", ".py"}:
            continue
        found, refs = _scan_text(p.read_text(encoding="utf-8", errors="replace"))
        pending += found
        env_refs.update(refs)
    return pending, sorted(env_refs)


def _symbol_source(path: Path, names: list[str]) -> str:
    """The source of the module-level declarations named in ``names``, in file
    order, as the CONTENT of a code-resident surface (O54). Read from the
    syntax tree so a comment that mentions a symbol is never mistaken for its
    definition; the slice keeps the declaration's own leading comment block so
    the rendered row carries the reasons written beside the data."""
    import ast

    text = path.read_text(encoding="utf-8", errors="replace")
    lines = text.splitlines()
    tree = ast.parse(text)
    wanted = set(names)
    spans: list[tuple[int, int]] = []
    for node in tree.body:
        targets: list[ast.expr] = []
        if isinstance(node, ast.Assign):
            targets = node.targets
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
        if any(isinstance(t, ast.Name) and t.id in wanted for t in targets):
            start = node.lineno
            # walk back over the contiguous comment block above the declaration
            while start > 1 and lines[start - 2].lstrip().startswith("#"):
                start -= 1
            spans.append((start, node.end_lineno or node.lineno))
    return "\n\n".join("\n".join(lines[a - 1 : b]) for a, b in spans) + ("\n" if spans else "")


def surface_status(surface: dict, pending: int) -> str:
    """The status vocabulary, decided from the GUARDS and the pending count only.

    Whether the config lives in code (``code_resident``) is a fact about WHERE,
    carried on the row beside this; it stopped deciding the status at O54,
    because a guarded declaration in a module is enforced by exactly the same
    mechanism a guarded YAML file is -- a test that fails when it drifts.
    """
    if not surface["guard_tests"]:
        return "unguarded"
    if pending:
        return "gate-pending"
    return "enforced"


def build_matrix() -> dict:
    errors: list[str] = []
    rows: list[dict] = []

    for s in SURFACES:
        primary = REPO / s["file"]
        is_dir = s["file"].endswith("/")
        target = REPO / s["file"].rstrip("/")
        if not target.exists():
            errors.append(f"surface {s['id']}: missing {s['file']}")
            continue

        files: list[Path]
        if is_dir:
            # Sort on the POSIX STRING, never on the Path objects.
            # `sorted()` over Path compares PurePath._str_normcase, which is
            # case-FOLDED on Windows and case-SENSITIVE on POSIX — so the same
            # directory renders in two different orders depending on the OS, and
            # a matrix committed from Windows fails this file's own drift guard
            # the moment CI regenerates it on Linux. That is exactly what
            # happened: `config/taxonomy/` put README.md between platforms.yaml
            # and software-registry.yaml on Windows, but first on Linux, and CI
            # was red from 2026-07-21 to 2026-07-31 because of it.
            # test_render_determinism.py pins this.
            files = sorted(
                (p for p in target.rglob("*") if p.is_file()),
                key=lambda p: p.as_posix(),
            )
        else:
            files = [primary]
        for extra in s.get("extra_files", []):
            ep = REPO / extra
            if not ep.exists():
                errors.append(f"surface {s['id']}: missing extra file {extra}")
            else:
                files.append(ep)

        for c in s["consumers"]:
            if not (REPO / c.rstrip("/")).exists():
                errors.append(f"surface {s['id']}: missing consumer {c}")
        for t in s["guard_tests"]:
            if not (REPO / "tests" / "unit" / t).exists():
                errors.append(f"surface {s['id']}: missing guard test {t}")

        symbols = list(s.get("symbols", []))
        if s.get("code_resident"):
            # O54: a code-resident surface is its DECLARATIONS, not its module.
            # Render and scan only the named symbols; the rest of the file is
            # code, and scanning it would report every env read in the CLI as
            # if the load sequence referenced it.
            if not symbols:
                errors.append(f"surface {s['id']}: code_resident rows must name symbols")
                continue
            content = _symbol_source(primary, symbols)
            missing_symbols = [n for n in symbols if f"{n}" not in content]
            if missing_symbols:
                errors.append(
                    f"surface {s['id']}: symbols not defined in {s['file']}: {missing_symbols}"
                )
                continue
            pending, env_refs = _scan_text(content)
        else:
            pending, env_refs = _scan(files)
            content = None if is_dir else _read_capped(primary)
        status = surface_status(s, pending)

        # content: single-file surfaces render verbatim (secrets are .env-only
        # -- files carry env-var REFERENCES, never values); dir surfaces list.
        if is_dir:
            listing = [str(p.relative_to(REPO)).replace("\\", "/") for p in files]
        else:
            listing = [s["file"], *s.get("extra_files", [])]
        extra_contents = {e: _read_capped(REPO / e) for e in s.get("extra_files", [])}

        rows.append(
            {
                "id": s["id"],
                "title": s["title"],
                "file": s["file"],
                "code_resident": bool(s.get("code_resident")),
                "symbols": symbols,
                "consumers": s["consumers"],
                "guard_tests": s["guard_tests"],
                "gate_ref": s["gate_ref"],
                "status": status,
                "pending_entries": pending,
                "env_refs": env_refs,
                "files": listing,
                "content": content,
                "extra_contents": extra_contents,
            }
        )

    # completeness: every top-level config/ entry must be covered by a surface
    covered = set()
    for s in SURFACES:
        top = s["file"].split("/")
        if top[0] == "config" and len(top) > 1:
            covered.add(top[1])
        for extra in s.get("extra_files", []):
            parts = extra.split("/")
            if parts[0] == "config" and len(parts) > 1:
                covered.add(parts[1])
    for entry in sorted(p.name for p in (REPO / "config").iterdir()):
        if entry not in covered and entry not in CONFIG_EXEMPT:
            errors.append(f"config/{entry} has NO enforcement-matrix surface row")

    if errors:
        raise SystemExit("enforcement-matrix generation failed:\n  " + "\n  ".join(errors))

    ci_last_run = None
    if CI_ARTIFACT.exists():
        ci_last_run = json.loads(CI_ARTIFACT.read_text(encoding="utf-8"))

    return {
        "note": (
            "GENERATED by scripts/render_enforcement_matrix.py -- never hand-edit. "
            "tests/unit/test_enforcement_matrix.py fails when this drifts from the repo."
        ),
        "ci_last_run": ci_last_run,
        "ci_note": None
        if ci_last_run
        else (
            "no CI artifact at var/ci-last-run.json -- guard-test freshness unknown "
            "(last-run metadata only; the page never polls CI)"
        ),
        "surfaces": rows,
    }


def main() -> int:
    matrix = build_matrix()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(
        json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )
    print(f"wrote {OUT} ({len(matrix['surfaces'])} surfaces)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
