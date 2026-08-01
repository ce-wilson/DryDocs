"""Generate the O12 admin-page enforcement matrix (wf-admin-config-01 (4)).

The matrix is GENERATED, never hand-typed: this script scans the SURFACES
registry below against the repo -- every referenced file/dir/test must exist,
every top-level config/ surface must be covered -- and emits
``web/src/generated/enforcement-matrix.json``, which /admin/config renders as
a build-time artifact (the board-render pattern: registry = truth, render =
artifact, ``tests/unit/test_enforcement_matrix.py`` = the drift guard).

Status vocabulary (wf-admin-config-01 (6)):
- ``unguarded``    -- no guard test, or the config is code-resident (was the
                     launcher-registry row until its G26 migration to
                     config/launcher-registry.yaml, 2026-07-27).
- ``gate-pending`` -- the surface carries entries awaiting HITL
                     (``status: proposed`` / ``planned`` / ``placeholder``).
- ``enforced``     -- guarded and nothing pending.

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
# file: repo-relative path; dirs end with '/'. code_resident marks the odd one
# out -- config living in code, the page's KPI example.
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
        "consumers": ["drydocs/publishing/"],
        "guard_tests": ["test_classification.py", "test_publishing.py"],
        "gate_ref": "PUBLISH-BOUNDARY.md",
    },
    {
        "id": "taxonomy-ontology-map",
        "title": "Taxonomy <-> Ontology map",
        "file": "config/taxonomy-ontology-map.yaml",
        "consumers": ["drydocs_core/ontology/", "drydocs/loaders/"],
        "guard_tests": ["test_taxonomy_ontology_map.py"],
        "gate_ref": "HITL gate (docs/restructure/03-hitl-sme-flow.md)",
    },
    {
        "id": "relationship-vocabulary",
        "title": "Relationship vocabulary",
        "file": "drydocs_core/ontology/relationship_vocabulary.yaml",
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
        "consumers": ["drydocs/publishing/"],
        "guard_tests": ["test_review_labels.py"],
        "gate_ref": None,
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
        "consumers": ["drydocs/publishing/"],
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
        "consumers": ["drydocs_core/controlm/commands.py", "drydocs_lineage/"],
        "guard_tests": ["test_launcher_registry.py", "test_command_parser.py"],
        "gate_ref": None,
    },
]

# Top-level config/ entries that are deliberately NOT surfaces.
CONFIG_EXEMPT = {"README.md"}


def _read_capped(path: Path) -> str:
    text = path.read_text(encoding="utf-8", errors="replace")
    if len(text) > CONTENT_CAP:
        return text[:CONTENT_CAP] + f"\n[truncated at {CONTENT_CAP} chars -- full file at {path.name}]\n"
    return text


def _scan(paths: list[Path]) -> tuple[int, list[str]]:
    """Pending-marker count + env-var references across the surface's files."""
    pending = 0
    env_refs: set[str] = set()
    for p in paths:
        if p.suffix not in {".yaml", ".yml", ".md", ".py"}:
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        pending += len(_PENDING_RE.findall(text))
        for m in _ENV_REF_RE.finditer(text):
            env_refs.add(m.group(1) or m.group(2) or m.group(3))
    return pending, sorted(env_refs)


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

        pending, env_refs = _scan(files)
        if s.get("code_resident") or not s["guard_tests"]:
            status = "unguarded"
        elif pending:
            status = "gate-pending"
        else:
            status = "enforced"

        # content: single-file surfaces render verbatim (secrets are .env-only
        # -- files carry env-var REFERENCES, never values); dir surfaces list.
        if is_dir:
            listing = [str(p.relative_to(REPO)).replace("\\", "/") for p in files]
            content = None
        else:
            listing = [s["file"], *s.get("extra_files", [])]
            content = _read_capped(primary)
        extra_contents = {e: _read_capped(REPO / e) for e in s.get("extra_files", [])}

        rows.append(
            {
                "id": s["id"],
                "title": s["title"],
                "file": s["file"],
                "code_resident": bool(s.get("code_resident")),
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
        "ci_note": None if ci_last_run else (
            "no CI artifact at var/ci-last-run.json -- guard-test freshness unknown "
            "(last-run metadata only; the page never polls CI)"
        ),
        "surfaces": rows,
    }


def main() -> int:
    matrix = build_matrix()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(matrix, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"wrote {OUT} ({len(matrix['surfaces'])} surfaces)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
