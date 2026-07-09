# docs/design/feedback — HITL annotations on design docs (Epic L)

**classification: Internal-Public** (the format is generic; a specific feedback file inherits
the classification of the doc it annotates — keep confidential notes in `internal/`).

Feedback on a design doc re-attaches to the doc's **stable anchors** (`<!-- anchor: id -->`),
so a note survives re-renders and points at a *trackable place in the requirements*. Two loops
produce the same anchor-keyed YAML:

- **Digital (L5):** open the doc's `.html`, click **✎** on a section, type a note (saved in your
  browser via `localStorage`), then **Copy feedback** — it puts a paste-ready block on your
  clipboard. Paste it here as `<doc-id>-rev<N>.yaml`.
- **Paper (L6):** print the `.print.html` (or its build-on-demand `.pdf`,
  `scripts/doc_to_pdf.py`) — each section's stable anchor id is visible in the page's left
  margin gutter, plus a `Rev N · commit <hash>` footer on every page
  (`drydocs/design_doc.py:_inject_margin_anchors` / `doc_rev_footer`). Annotate by hand,
  scan into `scans/` (Internal by default — never published, see `scans/README.md`), and
  the `.claude/skills/transcribe-doc-markup` skill turns the pen markup into the same
  anchor-keyed YAML — transcribing faithfully first, then keying each note to the margin
  anchor nearest it.

## Format (`drydocs.design_doc.feedback_yaml`)

```yaml
# design-doc feedback — paste into docs/design/feedback/<doc-id>-rev<N>.yaml
doc: controlm-ingestion-tdd
notes:
  - anchor: traceability-matrix      # must be an anchor that exists in the doc
    note: |
      FR-CMI-003 row cites the wrong design section.
  - anchor: detailed-design
    note: |
      Stage 2 needs the version-serial caveat spelled out.
```

`doc` is the doc stem; each `anchor` must match an `<!-- anchor: id -->` in the source `.md`
(the same id namespace the renderer emits and `doc_outline.py` validates). `<N>` is the doc's
Rev the feedback was taken against. Groomed feedback becomes edits to the `.md` (the single
source) and/or backlog items — never hand-edits to the derived `.html`/`.pdf`.
