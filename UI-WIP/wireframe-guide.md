# Wireframes with Claude — a working guide

How to document DryDocs web design with wireframes and iterate on them in Claude
(Cowork for artifacts, Claude Code for commits — per `CLAUDE.md` §0).

## 1. What a wireframe is for

A wireframe pins down **structure** (what goes where, what it's called, what it links to)
before anyone argues about color or copy. Rule: one fidelity level per document. Don't
polish pixels in a layout discussion, and don't debate layout in a themed mockup like
`drydocs-landing-dark.html` — that file is already high fidelity, which is why a
stripped-back print version is the right thing to draw on.

## 2. The fidelity ladder (and which Claude format fits each rung)

| Rung | Purpose | Format Claude reads/writes best |
|------|---------|-------------------------------|
| 1. Paper sketch | Think fast, throw away | Photo/scan (PNG or PDF) — drop into chat; Claude reads handwriting and arrows |
| 2. Text wireframe | Structure as a diff-able artifact | ASCII-box layout or nested outline in Markdown — lives in git, reviewable in PRs |
| 3. Line wireframe | Proportions, spacing, flows | SVG or grayscale HTML (no theme, boxes + labels) |
| 4. Mockup | Look & feel, tokens | Themed HTML like `drydocs-landing-dark.html` |

Each rung is a commit. Name them so they sort:
`UI-WIP/wf-<view>-<nn>.<ext>` → `wf-landing-01.md`, `wf-myapps-02.svg`.

## 3. Text wireframes (rung 2) — the workhorse

Claude is strongest here: they're precise, versionable, and cheap to revise. Example
for the landing view:

```
+--------------------------------------------------------------+
| LOGO  Overview Graph Lineage Pipelines Teams About  [Sign In] |
+--------------------------------------------------------------+
| H1: value proposition          |  hero illustration           |
| sub: product name              |  (node network + core)       |
| [Explore Graph] [Watch Demo]   |                              |
+--------------------------------------------------------------+
| feat 1 | feat 2 | feat 3 | feat 4                             |
+--------------------------------------------------------------+
| "Explore by Tower"                                            |
| [HL card] [Auto card] [Cards card] [Shared card]              |
+--------------------------------------------------------------+
```

Add an **annotation key** below the sketch — numbered notes beat prose:

```
1. H1 = benefit statement, not brand name (see design-review.md, rec #2)
2. Tower card click -> #/tower/<key> (hash route)
3. My Apps entry appears here when signed in
```

## 4. The paper → scan → Claude loop

Yes, this works, and it's a good habit:

1. **Print** the letter-size wireframe pack (`drydocs-wireframe-print.pdf`) — grayscale
   outlines of each view with margins and note lines for pen.
2. **Draw** on it: cross things out, arrow things to new positions, number your notes
   (①②③) so you can reference them ("move ② above ①").
3. **Scan or photograph** (phone photo is fine — flat, even light, one page per image)
   and drop the images into a Cowork chat.
4. **Ask Claude** to: transcribe every annotation into a numbered change list, apply
   the changes to the text wireframe / mockup, and flag anything ambiguous instead of
   guessing (that's your HITL gate for design).
5. **Commit** the updated wireframe + the scan itself (`UI-WIP/scans/wf-landing-01-annotated.pdf`)
   so the decision trail survives.

Tips for scans Claude reads well: dark pen (not pencil), write in the margins rather
than on top of dense mockup ink, one idea per annotation, number everything.

## 5. Iterating in chat — prompts that work

- "Here's my annotated scan. List every markup you can find as numbered changes before
  touching any file." (forces a transcription check — you approve the list first)
- "Apply changes 1, 3, 4 to `drydocs-landing-dark.html`; skip 2, I'm not sure yet."
- "Generate a rung-2 text wireframe of the My Apps view from the current mockup" —
  downshifting fidelity is a great way to document what exists.
- "Diff wf-landing-01.md against 02 and summarize what changed and why."

## 6. Fit with the DryDocs workflow

- Wireframes are **artifacts** → produce them in Cowork, land them as commits.
- Each accepted wireframe change that implies build work → an item in
  `docs/restructure/backlog.yaml` (groomed from `IDEAS.md`); the wireframe file is the
  item's spec, the design review its acceptance context.
- Ambiguity in a sketch is never auto-decided — same HITL rule as ontology edges.
