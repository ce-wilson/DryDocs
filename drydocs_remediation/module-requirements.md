# drydocs-remediation — module requirements

What this component needs to do its job, in three kinds. Markdown rather than a
pip file because two of the three cannot be expressed as packages. Update this
file when a dependency's role or acquisition status changes — the point is that
an implementer (here or at a company deployment) can read one page and know
what is present, what is pending, and why each thing is needed.

Companion to `overview_readme.md` (module invariants: no graph write, imports
only `drydocs_core.*`). Classification: Internal-Public (mechanism only).

## 1. Python

| Package | Kind | Role | Guard |
|---|---|---|---|
| `pyyaml` | main dependency (already in the root `pyproject.toml`) | transcript format load/dump (`formats.py`); change-set artifacts | — |
| `lxml` | **optional group `remediation`** — `poetry install --with remediation` | **VALIDATOR ONLY**: validates an emitted `<folder>.updated.xml` against the acquired `.dtd`/`.xsd` (§2), and parses with comments/DOCTYPE/CDATA intact for inspection | `test_xml_io_edits.py::test_xml_io_imports_are_stdlib_core_and_formats_only` keeps it OUT of the emitter |
| stdlib: `xml.parsers.expat` | — | the byte-offset locator behind `xml_io.load_document` | same guard: the emitter is stdlib-only |
| stdlib: `difflib`, `re`, `dataclasses`, `pathlib` | — | self-check line accounting, reference tokens, the model | — |

**Why lxml must never become the serializer.** Measured (2026-08-12, venv
3.13.3): both ElementTree and lxml rebuild start tags from an attribute dict,
collapsing multi-line attribute wrapping onto one line — a real
`exportdeftable` JOB element wraps a dozen-plus attributes, so any DOM
serializer produces the "100%-diff file no developer can review" that
`fix-package.md` §XML rule 1 forbids. Emission is `xml_io.write` (byte
splicing) and stays that way.

## 2. Control-M schema artifacts (`.dtd` / `.xsd`)

| Artifact | Status | Where to get it |
|---|---|---|
| Utility `.dtd` files (`deftable.dtd` and siblings) | **NOT ACQUIRED** | Likely already ON the company EM host: `<version>\Default\data\Resource` (per the vendor-doc capture in `external/orchestration/bmc-controlm/controlm-xml-definition-format.md` §3) — check there before fighting the 403-blocked docs site |
| `Folder.xsd` (folder-grain schema) | **NOT ACQUIRED** | Same EM-host directory, or the 9.0.21 Utilities doc tree (fetch list in the acquisition stub) |

**Status change (2026-08-12): these are no longer a blocker for emission.**
`xml_io` splices the vendor's own file and never authors XML, so `dump`-path
work proceeds without them. Their remaining role is **validation**: proving an
emitted file is schema-valid, which upgrades the honest residual claim ("the
file differs from a Control-M-produced file by exactly the approved bytes")
toward "Control-M will re-import it". Until acquired, that residual risk rides
on every fix package and is stated in the change doc.

## 3. The BMC Control-M documentation corpus — the full scrape must be loaded

Declared as a first-class dependency of this module, not an optional
reference. It is the substrate for the planned agent lookup beside the SME
diff (deterministic rules decide; the agent answers "does the vendor actually
say that?" with citations), and `external/orchestration/bmc-controlm/
SOURCE-MANIFEST.md` already flags the XML-definition corpus as "the corpus
actually worth ingesting next".

What "loaded" means here, with the trust discipline that already governs the
corpus (VERBATIM / GROUNDED / SYNTHESIZED per `SOURCE-MANIFEST.md`):

| State | Meaning for the agent surface |
|---|---|
| Captured page, VERBATIM/GROUNDED in the manifest | citable as vendor ground truth (with its capture date) |
| `[GROUNDED — search-result snippets only]` (e.g. the XML-definition stub) | citable ONLY as a lead — the answer must say so, never present it as vendor ground truth |
| 403-blocked fetch-list entries | not citable; the gap itself is the answer |

Current known gaps (from the acquisition stub): the `defjob`/`exportdefjob`/
`deftable`/`exportdeftable` utility pages, `XML_File_Rules.htm`, and the XML
deprecation notice. Re-run the fetch from a network that reaches
`documents.bmc.com` (the company network did on 2026-06-11); the raw capture
lands in `vendor_docs_dir()` (never committed), the publishable summary in
`external/orchestration/bmc-controlm/`.

## Filesystem (configuration, not dependency)

The three working zones resolve through `drydocs_core.data_root` (the one
resolver; `DRYDOCS_DATA_ROOT` overrides the `~/data/DryDocs` default):

- `remediation_incoming_dir()` — folder `.xml` exports awaiting a pass
- `remediation_outgoing_dir()` — emitted, self-checked `.updated.xml` files
- `remediation_recommendations_dir()` — change docs, equivalence reports,
  fix-tracking change-sets awaiting the write-authorized loader

Deliberately separate from `controlm_xml_dir()` (the ingestion landing zone):
remediation inputs are per-fix working copies whose lifecycle is the fix
package, not the graph load. Real definitions are Internal; none of this is
ever committed.
