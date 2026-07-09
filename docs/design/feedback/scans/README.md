# docs/design/feedback/scans/ — raw paper-HITL scans (Epic L / L6)

**classification: Internal by default — NOT published.** This directory holds the raw
scanned/photographed annotated printouts the `transcribe-doc-markup` skill reads from. A
scan is a marked-up copy of a design doc (which itself typically carries `Internal`
classification per its own front matter — e.g. `controlm-ingestion-tdd.md`), and it may
additionally carry a reviewer's handwriting, phone-camera background, or other incidental
detail that was never vetted for public release. Treat every scan as `Internal` unless a
human deliberately reclassifies it in the same way any other source is reclassified
(`config/classification.yaml`).

**Enforcement:** `.gitignore` excludes everything under this directory except this README
(`docs/design/feedback/scans/*` / `!docs/design/feedback/scans/README.md`), and
`config/classification.yaml`'s `excluded_paths` lists this directory — mirroring the
existing `drydocs/data/` and vendor-PDF carve-outs. This is a stronger default than the
per-file classification check most sources get, because a scan's content isn't something
an agent can safely inspect and classify unattended.

## What lives here

- Raw scans/photos of a printed `.print.html` (or its build-on-demand `.pdf`,
  `scripts/doc_to_pdf.py`) after hand annotation.
- Nothing else — the TRANSCRIBED, anchor-keyed feedback derived from a scan is a separate,
  publishable-by-default artifact: `docs/design/feedback/<doc>-rev<N>.yaml` (the same L5
  schema as the digital loop; see `docs/design/feedback/README.md`).

## Naming

`<doc-id>-rev<N>-scan<M>.<ext>` (e.g. `controlm-ingestion-tdd-rev3-scan1.pdf`) — `<N>` is
the Rev printed in the page footer (`drydocs/design_doc.py:doc_rev_footer`) at the time it
was annotated, so a scan and its transcription can be matched back up.
