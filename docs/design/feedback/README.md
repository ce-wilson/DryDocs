# docs/design/feedback — HITL annotations on design docs (Epic L)

**classification: Internal-Public** (the format is generic; a specific feedback file inherits
the classification of the doc it annotates — keep confidential notes in `internal/`).

Feedback on a design doc re-attaches to the doc's **stable anchors** (`<!-- anchor: id -->`),
so a note survives re-renders and points at a *trackable place in the requirements*. Two loops
produce the same anchor-keyed YAML:

- **Digital (L5):** open the doc's `.html`, click **✎** on a section, type a note (saved in your
  browser via `localStorage`), then **Copy feedback** — it puts a paste-ready block on your
  clipboard. Paste it here as `<doc-id>-rev<N>.yaml`.
- **Paper (L6):** print the same `.html` — its `@media print` sheet is the paper layout, L13 — (or its build-on-demand `.pdf`,
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

### Optional review-outcome fields (L7 graph load)

Beyond the exported format, a feedback file may carry two OPTIONAL fields the graph loader
(`drydocs load-doc-traceability`, gate `doc-traceability-feedback` 2026-07-20) reads — data
entry recording review outcomes, never produced by the Copy-feedback export:

- **file-level `author:`** (or per-note `author:`) — the reviewer's Employee id; the
  attribution edge is written only when it MATCHes a real `:Employee` (never fabricated).
- **per-note `status:`** — the review lifecycle: `open` (default when absent) | `applied` |
  `rejected` | `superseded`. Set it when the rev that addresses the note lands (e.g. the
  runbook rev1 notes were applied in Rev 2).

### Derived subsection anchors (L11)

When a section has **more than two** subsections (sub-headings, or a numbered step list with
3+ items), the screen render gives each subsection its own annotate control under a **derived**
anchor: `<authored-anchor>--<subsection-slug>` (e.g. `detailed-design--stage-2-variable-pass`).
The slug comes from the subsection's own text — content-derived, never positional — so a note
on step "1.b" survives someone inserting a new "1.a". Validity rule
(`doc_outline.feedback_anchor_valid`): a derived anchor re-attaches as long as its base
authored anchor exists; if the subsection text (and so its slug) later changes, the note
degrades to the parent section rather than dangling. Consequence for authors: `--` (double
hyphen) is **reserved** as the derived separator — never use it inside an authored anchor id.

The screen render also ends with a static **SME - Feedback** panel (L10) that walks the
reviewer through the mechanics: annotate → **Copy feedback** → create
`docs/design/feedback/<doc-stem>-rev<N>.yaml` (the exact per-doc filename, current Rev baked
in, is rendered in the panel) → paste and save. The file is YAML, not markdown.
