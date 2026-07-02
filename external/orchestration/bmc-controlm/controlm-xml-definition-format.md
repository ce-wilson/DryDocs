# Control-M XML Definition Format (9.0.21) — ACQUISITION STUB

**Status:** ⚠️ **ACQUISITION INCOMPLETE** — target pages identified, fetch blocked
(documents.bmc.com + mirrors return HTTP 403 bot-protection to this environment,
2026-07-02). Re-run the fetch from a network that reaches BMC docs (the company
network reached documents.bmc.com for the 2026-06-11 corpus).
**Classification:** `External` (public BMC documentation). Publishable.
**Why this corpus matters:** flagged in `SOURCE-MANIFEST.md` as "the corpus actually
worth ingesting next" — it is the source-of-record format for 9.0.21.300 job/folder
definitions and the prerequisite for `drydocs-remediation`'s `xml_io` lossless
round-trip contract (see the `controlm-runbook-automation` skill, `fix-package.md` §XML).

## 📑 Provenance

Everything below is **[GROUNDED — search-result snippets only]**: facts surfaced in
documents.bmc.com/community search results on 2026-07-02, *not* yet verified against
the full pages. Treat as leads, not vendor ground truth, until the pages are fetched.

## Facts captured so far (verify on fetch)

1. **`defjob`** (Control-M/EM utility) *"reads job processing definitions from a
   plain text input file written in XML format."*
2. **`exportdefjob`** processes an XML arguments file identifying existing job
   processing definitions; exports them from the Control-M/EM database to an
   output file. (`deftable` / `exportdeftable` are the folder/table-grain
   siblings — confirm exact names + elements on fetch.)
3. **DTDs exist and are local:** *"Each utility input file has its own `.dtd`
   file. The arguments files share the same `.dtd` file. Utility `.dtd` files are
   stored in the Control-M EM `<version>\Default\data\Resource` directory."*
   → the authoritative schema may already be ON the company EM host — check that
   directory before fighting the docs site.
4. **⚠️ DEPRECATION (load-bearing for xml_io):** from **9.0.21.100**,
   XML-formatted definition files are **deprecated** — no longer enhanced, but
   *"fully supported until version 9.0.22."* Our target (9.0.21.300) is inside
   the supported-but-deprecated window: the XML round-trip remains the correct
   mechanism for the current environment, but the remediation tooling should
   isolate the serializer (already the plan — C1 `xml_io.py`) so a future
   format migration is a module swap, not a redesign.

## Fetch list (exact targets, 9.0.21)

| Page | URL |
|---|---|
| defjob (XML job definitions) | `https://documents.bmc.com/supportu/9.0.21.000/en-US/Documentation/Utilities/defjob.htm` |
| exportdefjob | `https://documents.bmc.com/supportu/9.0.22/en-US/Documentation/Utilities/exportdefjob.htm` (locate 9.0.21.000 equivalent) |
| deftable / exportdeftable (folder XML) | locate under the same Utilities tree |
| XML File Rules (encoding/escaping/DTD rules) | `.../Documentation/Utilities/XML_File_Rules.htm` |
| XML Format Deprecation notice | `https://docs.bmc.com/docs/controlm/90201/xml-format-deprecation-1449710676.html` |

On successful fetch: replace this stub's "Facts" with the full extraction
(elements/attributes per entity, DTD names, escaping rules), add the standard
per-file Provenance block, and update `SOURCE-MANIFEST.md` (this file is
registered there under the XML gap).

## Better-than-docs shortcut (company side)

Two authoritative sources likely beat the doc pages:
1. The **`.dtd` files** in `<EM home>\Default\data\Resource` — the actual schema.
2. A real `exportdeftable` output from a non-production folder — ground truth by
   construction, and exactly the "before" artifact P4 of the runbook pipeline
   exports anyway. Sanitized samples → `internal-local/`; never commit real ones.
