# Control-M XML Definition Format (9.0.21) — the emdef utility pages

**Status:** ✅ **ACQUIRED 2026-09-11** (G85, requirement d). The five utility pages the
2026-07-02 stub could only see as search results were fetched in a real browser session from
documents.bmc.com. Direct programmatic fetches still get the 403 bot protection; the browser
session did not. Two docs.bmc.com pages stayed out of reach (see Gaps).
**Date Scraped:** 2026-09-11
**Classification:** `External` (public BMC documentation). Publishable.
**Why this corpus matters:** flagged in `SOURCE-MANIFEST.md` as "the corpus actually
worth ingesting next". It is the source-of-record format for 9.0.21.300 job/folder
definitions and the prerequisite for `drydocs-remediation`'s `xml_io` lossless
round-trip contract (see the `controlm-runbook-automation` skill, `fix-package.md` §XML).

## 📑 Provenance

Everything below is **[GROUNDED]**: our paraphrase of the fetched 9.0.21.000 pages, checked
against the page text on the capture date. Nothing is transcribed verbatim and nothing is
SYNTHESIZED. Each lead from the 2026-07-02 stub is either confirmed below or corrected, and
every correction says so. No raw capture was kept: the pages were read in the browser and
summarized directly, so there is nothing in `vendor_docs_dir()` for this file.

## Pages captured

| Page | URL |
|---|---|
| defjob | `https://documents.bmc.com/supportu/9.0.21.000/en-US/Documentation/Utilities/defjob.htm` |
| exportdefjob | `https://documents.bmc.com/supportu/9.0.21.000/en-US/Documentation/Utilities/exportdefjob.htm` |
| deffolder | `https://documents.bmc.com/supportu/9.0.21.000/en-US/Documentation/Utilities/deffolder.htm` |
| exportdeffolder | `https://documents.bmc.com/supportu/9.0.21.000/en-US/Documentation/Utilities/exportdeffolder.htm` |
| XML File Rules | `https://documents.bmc.com/supportu/9.0.21.000/en-US/Documentation/Utilities/XML_File_Rules.htm` |

## Deprecation

- Every emdef utility page carries the same notice: the emdef suite is deprecated from
  9.0.21.100 (except importpromotionrule and exportpromotionrule), is no longer enhanced, and
  loses support in 9.0.22. This confirms the stub's lead.
- Our target, 9.0.21.300, is inside the supported-but-deprecated window.

## Utility names — a correction to the stub

- The folder-grain utilities are **deffolder** (import) and **exportdeffolder** (export). The
  stub guessed `deftable` / `exportdeftable`; no 9.0.21 utility page uses those names. The
  export's root element is `DEFTABLE`, which is the likely source of the guess.
- Job grain: **defjob** imports job definitions from an XML file, and **exportdefjob**
  exports them, selected by an XML arguments file. An export can be edited and re-imported
  with defjob or updatedef.

## Schema files

- Each utility input file has its own `.dtd`; the arguments files share one (`terms.dtd`
  covers exportdefjob, exportdefcal and exportdeffolder).
- The `.dtd` files live on the Control-M/EM host under `Default\data\Resource`. The pages list
  eight: copycal, copyjob, defcal, defjob, deffolder, duplicatejob, terms and update.
- The deffolder page's own parameter table says the request file's header names an `.xsd`
  file, where every other page says `.dtd`. The pages alone do not resolve which is right.
- The schema files themselves were not fetched: they are on the EM host, not the docs site.

## File rules (defjob and XML File Rules)

- Files are case-sensitive, and every attribute value is quoted.
- A parameter that needs several entries is repeated (one INCOND per prerequisite condition,
  for example).
- Each ON_STMT or ON_STEP must be followed by at least one DO parameter.
- Five characters are reserved and must be written as entity codes inside any value: double
  quote, apostrophe, less-than, greater-than and ampersand.
- Condition dates are `mmdd`; times are `hhmm`.
- The EM database validates every submitted file and rejects one with errors, naming the
  offending lines.
- A multi-line value (mail message, Remedy text, instream JCL) uses a length-prefixed line
  format, or CR/LF entity delimiters when the `UseMultiLineNewFormatDisplay` system parameter
  is 1.

## Variables in definition XML

- defjob's parameter table documents **VARIABLE** as defining a variable expression, with the
  whole assignment carried in `NAME` (its example is a `%%PARM1=%%TIME` style expression) and
  an `EXP` field naming the expression.
- The NAME + VALUE form is not documented on any captured page. `drydocs_remediation/xml_io.py`,
  its fixtures and the fix-diff demo all edit `VARIABLE NAME="%%X" VALUE="..."`, the shape of a
  real folder export. The pages neither confirm nor contradict that form; the `.dtd` on the EM
  host is what settles it.
- deffolder does not list VARIABLE among its folder or SMART-folder parameters. For job-level
  parameters inside a folder, it points to defjob's table.

## Export argument files (exportdefjob, exportdeffolder)

- Selection is a `TERMS` document of `TERM` groups; each TERM holds `PARAM` rows with `NAME`,
  `OP` (EQ, NEQ, LIKE) and `VALUE`.
- PARAMs inside one TERM combine with AND; separate TERMs combine with OR.
- An exportdefjob argument must name at least one folder-identity parameter (the data center,
  the folder name, or FOLDER_DSN).

## Gaps (not citable — the gap itself is the answer)

| What | Why |
|---|---|
| emdef Utility Suite Deprecation (docs.bmc.com, ctm9021 space) | docs.bmc.com is not an allowed domain for the capture browser; its substance is repeated on every utility page above |
| XML Format Deprecation notice (docs.bmc.com, controlm 90201 space) | same domain restriction; same substance repeated above |
| The `.dtd` / `.xsd` files | on the EM host, not the docs site; see `drydocs_remediation/module-requirements.md` section 2 |

## Better-than-docs shortcut (company side)

Two authoritative sources still beat the doc pages:
1. The **`.dtd` files** in `<EM home>\Default\data\Resource`, which are the actual schema and
   the only thing that settles the VARIABLE form above.
2. A real `exportdeffolder` output from a non-production folder: ground truth by construction,
   and exactly the "before" artifact P4 of the runbook pipeline exports anyway. Sanitized
   samples go to `internal-local/`; never commit real ones.
