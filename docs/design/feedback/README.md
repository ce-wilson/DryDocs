# docs/design/feedback — HITL annotations on design docs (Epic L)

**classification: Internal-Public** (the format is generic; a specific feedback file inherits
the classification of the doc it annotates — keep confidential notes in `internal/`).

Feedback on a design doc re-attaches to the doc's **stable anchors** (`<!-- anchor: id -->`),
so a note survives re-renders and points at a *trackable place in the requirements*. Two loops
produce the same anchor-keyed YAML:

- **Digital (L5):** open the doc's `.html`, click **✎** on a section, type a note (saved in your
  browser via `localStorage`), then **Copy feedback** — it puts a paste-ready block on your
  clipboard. Paste it here as `<doc-id>-rev<N>.yaml`.
- **Paper (L6, planned):** print the `.pdf`, annotate by hand, scan into `scans/`, and the
  transcribe skill turns the markup into the same anchor-keyed YAML.

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
