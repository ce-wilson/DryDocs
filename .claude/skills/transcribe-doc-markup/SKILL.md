---
name: transcribe-doc-markup
description: Turn a scanned/photographed, hand-annotated design-doc printout into anchor-keyed feedback YAML. Use when the user has printed a docs/design/*.print.html (or its .pdf), marked it up by pen, and scanned or photographed it back in — the paper half of the Epic L HITL loop (L6), producing the same docs/design/feedback/<doc>-rev<N>.yaml shape the digital (L5) save-button export produces.
---

# transcribe-doc-markup — paper HITL: scan → anchor-keyed feedback (Epic L / L6)

**The mental model (`docs/design/feedback/README.md`):** two loops produce the SAME
anchor-keyed YAML. The **digital** loop (L5) is a save-button on the `.html` that exports
`{anchor, note}` pairs via `drydocs.design_doc.feedback_yaml`. This skill is the **paper**
loop (L6): a printed page gets marked up by pen, scanned, and this procedure re-attaches
each pen note to the same stable anchor — using the SAME `feedback_yaml` emitter, so L7
ingests both loops identically. **Never hand-write the YAML from memory** — always drive it
through `feedback_yaml`, exactly like the digital loop's clipboard export does.

**Why this works at all:** `drydocs/design_doc.py` renders every anchored section's stable
id into the page's left margin gutter when it builds `.print.html`
(`_inject_margin_anchors`, `.dd-margin-tag` CSS), plus a `Rev N · commit <hash>` footer on
every page (`doc_rev_footer` — deterministic, read from the doc's own front matter, never
git state or a timestamp). Print or PDF a **current** render before annotating — a scan
against a stale `.print.html` will show margin tags that don't match a re-rendered doc.

## Inputs this skill accepts

1. **A scanned PDF** of one or more annotated printed pages.
2. **Photos** (one per page) of an annotated printout — same handling either way.
3. The **doc id + Rev** the annotations were taken against — read this off the page footer
   (`Rev N · commit ...`); if illegible, ask the user rather than guessing.

## Procedure (in order — do not skip or reorder)

### 1. Faithful transcription FIRST (show it, don't skip it)

Exactly the `groom-backlog` pattern for a photo of paper notes: **transcribe every visible
pen mark verbatim** — what is written, not your interpretation of it — and **show this
transcription to the user for confirmation before doing anything else**. For each mark,
record:

- the page/section it's on,
- the margin anchor tag nearest it (the small monospace label in the left gutter — e.g.
  `traceability-matrix`, `hitl-gate`),
- the pen text, verbatim.

If handwriting is illegible or ambiguous, transcribe what you can and flag the gap
explicitly (`[illegible]`) — do not silently fill it in. **Wait for the user to confirm**
the transcription is faithful before step 2.

### 2. Anchor-keying

Match each confirmed transcribed note to its section anchor:

- **Normal case:** the note already carries the margin tag text it was written next to —
  that IS the anchor id (`drydocs/design_doc.py`'s gutter tag and the doc's
  `<!-- anchor: id --> ` comments are the same namespace). Use it directly.
- **Tag cropped/illegible in the scan:** infer from the visible heading text and confirm
  with the user — never silently invent an anchor id.
- **A note spans two sections or sits between two anchors:** ask the user which one it
  belongs to (or whether it should become two notes). This is exactly the kind of ontology
  ambiguity CLAUDE.md routes through the HITL gate rather than auto-deciding.
- Sanity-check every candidate anchor id actually exists in the doc's source `.md`:
  `grep "anchor: <id>" docs/design/<doc>.md` should hit.

### 3. Emit the feedback YAML

Build the `{anchor: note}` mapping from the confirmed, keyed notes and pass it through the
**canonical emitter** — the exact same function the digital loop's clipboard export
mirrors byte-for-byte:

```python
from drydocs.design_doc import feedback_yaml

notes = {
    "traceability-matrix": "FR-CMI-003 row cites the wrong design section -- should be design-data-mapping",
    "hitl-gate": "need the SEAL gate ticket number here",
}
out = feedback_yaml("controlm-ingestion-tdd", notes)
```

Write `out` to `docs/design/feedback/<doc>-rev<N>.yaml`, where `<N>` is the Rev read off
the scanned page's footer (step 1) — **not** the current doc's Rev if it has since moved
on; the feedback is scoped to the Rev it was actually taken against.

**Format (must match `docs/design/feedback/README.md` exactly — this is the whole point):**

```yaml
# design-doc feedback — paste into docs/design/feedback/<doc-id>-rev<N>.yaml
doc: controlm-ingestion-tdd
notes:
  - anchor: traceability-matrix
    note: |
      FR-CMI-003 row cites the wrong design section -- should be design-data-mapping
  - anchor: hitl-gate
    note: |
      need the SEAL gate ticket number here
```

A blank/whitespace-only note is skipped (matches `feedback_yaml`'s behavior) — don't emit
placeholder rows for pen marks that turned out to be nothing (stray dots, a checkmark with
no text, etc.).

### 4. Store the scan (classification-aware)

Move or copy the raw scan/photos into `docs/design/feedback/scans/`, named
`<doc-id>-rev<N>-scan<M>.<ext>` (e.g. `controlm-ingestion-tdd-rev3-scan1.pdf`).

- **This directory is Internal by default and never published** — `.gitignore` excludes
  everything under it except its `README.md`, and `config/classification.yaml`
  `excluded_paths` lists it too (see `docs/design/feedback/scans/README.md` for why: a
  marked-up copy of an Internal doc, plus whatever incidental handwriting/background the
  scan carries, is not something to publish by default).
- If a specific scan genuinely needs a different classification (rare — e.g. it only
  annotates an already-`Internal-Public` doc and carries no incidental information), that
  is a deliberate reclassification decision the user makes explicitly, the same way any
  other source's classification is set — don't assume it.
- The **transcribed YAML from step 3 is NOT covered by this exclusion** — it inherits the
  classification of the doc it annotates (usually publishable), same as the digital loop's
  output.

### 5. Report back

Summarize: which doc/Rev, how many notes transcribed, which anchors they keyed to, where
the scan landed, and the path to the emitted feedback yaml. Point the user at
`docs/restructure/03-hitl-sme-flow.md` if any note itself implies an ontology/edge-meaning
decision (transcribing the feedback is not the same as resolving it).

## Gotchas

- **Never skip step 1's confirmation.** A misread pen mark that goes straight to a
  requirement-affecting note is worse than a paper note that never got digitized.
- Multiple reviewers' handwriting on one scan (different pen colors/ink) → keep it to one
  `feedback_yaml` call but note whose mark is whose in the `note:` text, or ask whether the
  user wants separate feedback files per reviewer.
- A note with no legible margin tag nearby at all (annotation on a blank area, or the tag
  was cropped out of the photo) → ask which section it's about; do not guess from position
  alone.
- `<N>` is the Rev **on the scanned page**, not necessarily the doc's current Rev — a scan
  can be transcribed well after the doc has moved on to a later Rev.
- If `drydocs/design_doc.py` hasn't been re-rendered since the doc's `.md` last changed,
  the margin tags on a fresh printout may not match an old scan — always print a current
  render before annotating (`python scripts/render_design_doc.py docs/design/<doc>.md`,
  then `python scripts/doc_to_pdf.py docs/design/<doc>.print.html` if a physical printout
  is needed).

## Model guidance

Routine transcription runs on sonnet — the judgment calls (illegible handwriting, ambiguous
anchor keying) are exactly what steps 1–2 build in confirmation gates for. Escalate only if
a transcribed note itself implies an ontology/relationship-semantics decision (route it
through the HITL gate, don't resolve it here).
