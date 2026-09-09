# Runbook — operate `drydocs-docgen`: render the docs, validate the outline, close the feedback loop

<!-- anchor: front-matter -->
- **Module:** drydocs-docgen — this runbook IS the module runbook for drydocs-docgen
  (V1 coverage rule; authored at V5). It covers the module's whole operate surface: the
  md-is-source / html-is-render contract, outline validation, the PDF path, the ideas
  render, and both halves of the HITL feedback loop.
- **Status:** DESCRIPTIVE — documents the working procedure. **Rev 1, 2026-09-09**,
  authored at commit `2453ac17`. Every command, count and exit code below was RUN on this
  tree — laptop, no Neo4j, no company data, every render written to a scratch directory so
  no committed page moved (J18: the venue is named, and the PDF step in particular is
  venue-dependent).
- **Classification:** Internal-Public (mechanism only — the renderer, the outline contract
  and the feedback file shape. A specific feedback file inherits the classification of the
  doc it annotates, and scans are Internal by default)
- **Audience:** whoever renders a design doc, adds a doc type, validates an outline, or
  runs an SME review round on paper or in the browser
- **Companion:** `docs/design/feedback/README.md` (**read this before running a feedback
  round** — it owns the two-loop contract and the `<doc-id>-rev<N>.yaml` naming rule);
  `docs/design/templates/` (the outline contracts themselves — `tdd.outline.yaml`,
  `runbook.outline.yaml`, `review.outline.yaml`, `sdlc-app-runbook.outline.yaml`);
  `.claude/skills/transcribe-doc-markup/SKILL.md` (the L6 scan-to-YAML step).

---

<!-- anchor: purpose-scope -->
## Purpose & scope

**Purpose.** Operate the machinery every other design doc in this repo is rendered *by*.
The module owns one contract and three procedures that follow from it.

### The one rule to know before running anything

> **The `.md` is the source of truth. The `.html` is a deterministic render of it.**
> Never hand-edit a rendered page; change the markdown and re-render.

"Deterministic" is measured, not asserted. Rendering the same source twice on this tree
produced byte-identical output (`drydocs-core-runbook.md` → 30,829 bytes, two runs, same
hash), and the PDF path normalizes its dates so re-runs are structurally identical too
(243,073 bytes, two runs, same hash). That property is what lets a committed render be
guarded for drift at all — see Verify.

**One HTML surface, not two** (L13): the page carries its print layout as an
`@media print` sheet rather than shipping a separate print file. The same page is what an
SME reads on screen and what comes out of the printer.

### The awkward fact, stated rather than hidden

**Zero of the 55 registered `drydocs` verbs reach this module.** Measured, not assumed —
every one of the 55 callbacks was read and none imports `drydocs.docgen` (Appendix B has
the command). The module is driven entirely by two scripts and one sub-renderer, so every
procedure below is a `python scripts/…` invocation, never a `drydocs …` verb.

**And two verbs that sound like this module's are not.** `docs-verify` and `docs-coverage`
operate the doc **corpus in the graph** — `config/doc-source-registry.yaml`, loaded
`Document`/`Chunk` counts, via `drydocs_core/docs_verify.py`. They have nothing to do with
rendering a design doc. The names collide; the surfaces do not.

### Why the board render is described here

`scripts/render_board.py` is **drydocs-plan's** code, not this module's. It appears in this
runbook for two reasons, and the second is the load-bearing one:

1. Its default-paths run fires this module's ideas render (`render_ideas` →
   `drydocs.docgen.plan_ideas`), so the two chains are joined whether or not that is
   convenient.
2. **drydocs-plan is EXEMPT from module-runbook coverage** — `tests/unit/test_runbook_coverage.py`
   records the reason: *"placeholder — no package. The board renderer is
   `scripts/render_board.py`, operated by the CLAUDE.md §0 session ritual, not by a module
   runbook."* So there is no plan runbook and there will not be one. If this page does not
   describe the run, nothing does.

This page therefore **describes** that run and **routes** the ritual to `CLAUDE.md` §0,
which owns when to do it. It does not restate the ritual.

**In scope.** Rendering a design doc; the outline contract and its validator; adding a new
doc type; the PDF path; the ideas render; the L5 digital and L6 paper feedback loops and
the anchor-keyed YAML both produce; the stale-render check.

**Out of scope.** *When* to render — the `CLAUDE.md` §0 session ritual owns that. The
content of any particular doc. The doc corpus in the graph (`docs-verify` /
`docs-coverage`, above). Publishing to Confluence — that is drydocs-review's.

<!-- anchor: prerequisites -->
## Prerequisites

1. **The toolchain.** `poetry install`. Nothing else for the render, validate and ideas
   procedures: no database, no network, no data root, no credentials.
2. **A Chromium-family browser — for the PDF step only.** `drydocs.docgen.doc_pdf`
   searches Brave, then Chrome, then Edge. Measured on this venue: it resolved
   `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe`. A machine with none of
   the three cannot run step 4, and that is a venue limit rather than a defect.
3. **Know which pen you hold before you render.** A default-paths run writes committed
   pages under `docs/plan/` and `web/src/generated/`. In a two-lane burst those belong to
   one lane (`docs/lane-b-handoff.md`); render to a scratch `--out-dir` if they are not
   yours. Every command in this runbook was run that way.

<!-- anchor: startup -->
## Startup

**No service, no daemon.** "Startup" is confirming the module imports and the outline
contracts load.

1. **The module imports.**

   ```powershell
   poetry run python -c "from drydocs.docgen import design_doc, doc_outline, doc_pdf, plan_ideas; print('ok')"
   ```

   *Success:* `ok`. Import `drydocs.docgen.*`, never the flat `drydocs.design_doc` etc. —
   those are one-cycle ADR 0018 D4 re-export shims due for removal at the roll after next.
2. **The outline contracts load.**

   ```powershell
   poetry run python -c "from drydocs.docgen.doc_outline import load_outline; import glob; print([load_outline(p).doc_type for p in sorted(glob.glob('docs/design/templates/*.outline.yaml'))])"
   ```

   *Success:* one `doc_type` per template. Measured on this tree: four templates —
   `review.outline.yaml`, `runbook.outline.yaml`, `sdlc-app-runbook.outline.yaml`,
   `tdd.outline.yaml`.

<!-- anchor: refresh-ingest -->
## Refresh / ingest

Four procedures. None needs a database.

### Step 1 — render a design doc

```powershell
poetry run python scripts/render_design_doc.py docs/design/<doc>.md
poetry run python scripts/render_design_doc.py docs/design/*.md          # all 27 sources
poetry run python scripts/render_design_doc.py docs/design/<doc>.md --out-dir <scratch>
```

Default output is **beside each `.md`** — that is what makes the committed render the
guarded surface. `--out-dir` sends it elsewhere, which is how to render without touching
a committed page.

**`--out-dir` does not create the directory.** Measured: pointing it at a missing path
raises `FileNotFoundError` rather than creating one. Make the directory first.

Measured on this tree: 27 sources under `docs/design/*.md`; one render of
`drydocs-core-runbook.md` produced 30,829 bytes, and a second run to a different directory
produced the identical bytes.

### Step 2 — validate a doc against its outline

```powershell
poetry run python -m drydocs.docgen.doc_outline --outline docs/design/templates/runbook.outline.yaml --doc docs/design/<doc>.md
```

Both flags are **required and named** — a positional invocation exits 2 with a usage line.
Measured on both paths:

| Outcome | Output | Exit |
|---|---|---|
| Conforms | `OK — <doc> conforms to <outline>` | **0** |
| Does not | `FAIL — <doc> does not conform…` then one bullet per missing anchor | **1** |

The failure bullets are actionable rather than diagnostic — each names the exact marker to
add, e.g. ``missing required section — add `<!-- anchor: verify -->` before its heading``.

**Anchors are the contract, not headings.** The validator checks that each required
section's `<!-- anchor: id -->` marker is present; it does not check heading text. A
required section may be satisfied by an explicit `N/A — <reason>` so long as the anchor is
there. Anchors are authored and stable, never positional, and never contain `--` (L11
reserves the double hyphen for derived subsection anchors) — because the feedback loop in
step 4 re-attaches notes by anchor, and a renumbered anchor silently orphans every note
keyed to it.

### Step 3 — the PDF path (for the paper loop)

```powershell
poetry run python scripts/doc_to_pdf.py docs/design/<doc>.html --out <scratch>/<doc>.pdf
```

Headless Chromium-family print-to-PDF over the page's own `@media print` sheet, with the
PDF dates normalized so re-runs are structurally identical. **Verified rather than taken
from the docstring:** two runs of the same page produced byte-identical 243,073-byte files
on this venue.

The PDF is **build-on-demand and never committed** (PUBLISH-BOUNDARY) — regenerate before
printing rather than reusing an old one.

### Step 4 — a feedback round, both halves

Both loops produce the *same* artifact: anchor-keyed YAML at
`docs/design/feedback/<doc-id>-rev<N>.yaml`.

- **L5, digital.** Open the doc's `.html`, click **✎** on a section, type a note, then
  **Copy feedback** — it puts a paste-ready block on the clipboard. Notes are held in that
  browser's `localStorage` until copied. *Verified present without clicking:* a freshly
  rendered page contains the `localStorage` handling, the "Copy feedback" control, the
  anchor markers and the `@media print` sheet.
- **L6, paper.** Print the same page (or the step-3 PDF). Each section's anchor id prints
  in the left margin gutter and every page carries a `Rev N · commit <hash>` footer, both
  injected by `drydocs/docgen/design_doc.py`. Annotate by hand, scan into
  `docs/design/feedback/scans/` (**Internal by default — never published**), then run the
  `.claude/skills/transcribe-doc-markup` skill, which transcribes faithfully first and only
  then keys each note to the nearest margin anchor.

The file shape, from a real capture:

```yaml
doc: drydocs-startup-refresh-runbook
author: <reviewer>
notes:
  - anchor: front-matter
    status: applied          # applied in Rev 2 (2026-07-20)
    note: |
      <the reviewer's words>
```

**A later rev carries forward the earlier rev's notes** — a capture is meant to be the
whole of what the reviewer sent, not the part still open. Keep the `<doc-id>-rev<N>.yaml`
name: `drydocs/port/port_rename_detect.py` treats two files whose stems match modulo the
`-rev<N>` suffix as one subject precisely because a rev file is a strict superset of its
predecessor and scored 1.00 on the rename detector's containment measure (PORT2). A
capture named some other way loses that protection.

### The board render — described here, owned elsewhere

```powershell
poetry run python scripts/render_board.py                      # DEFAULT PATHS: writes committed pages
poetry run python scripts/render_board.py --backlog <path> --out <path>   # board only, no side effects
```

**A default-paths run fires eleven sub-renderers besides the board itself.** Counted two
ways on this tree — the `import render_*` lines and the `render_*.main()` calls in the same
block, both 11: gates, enforcement-matrix, load-map, software-registry, context-types,
ui-concepts, gazetteer, remediation-diff, remediation-profile, **ideas**, roadmap. Only
`render_ideas` reaches this module.

> **The count in the tool's own docstring is stale.** `scripts/render_board.py` says *"One
> command refreshes all four"* while enumerating roughly eight in the prose above it and
> calling eleven in the code. `CLAUDE.md` §0 names four as well. Neither is this module's
> to fix; both are recorded here so a reader trusts the command over the sentence. The
> command is in Appendix B — run it rather than believing this paragraph either.

An explicit `--backlog`/`--out` run renders **the board only** and fires none of the
eleven. That is the form to use for a test, a preview, or any session that does not hold
the render pen.

<!-- anchor: verify -->
## Verify

1. **The stale-render check — re-render, then diff.** Renders are deterministic, so a
   diff after re-rendering means a committed page did not match its source:

   ```powershell
   poetry run python scripts/render_design_doc.py docs/design/*.md
   git diff --quiet docs/design ; if ($?) { "clean" } else { "STALE - commit the refresh" }
   ```

   Any diff is a committed render that drifted from its `.md`. Commit the refresh; never
   edit the `.html` to match.
2. **The same check for everything a default board run owns**, per `CLAUDE.md` §0:
   `docs/plan/board.html`, the `docs/design/*.html` set, `web/src/generated/gates.json`,
   `web/src/generated/enforcement-matrix.json`, `web/src/generated/load-map.json` and
   `docs/plan/load-map.html`. The eleven-renderer list above is why: editing a gate prompt
   or a config taxonomy without re-rendering leaves a committed artifact describing
   something the source no longer says, and each has its own drift guard.
3. **Outline conformance is swept, not spot-checked.** `tests/unit/test_doc_outline.py`
   validates every `docs/design/*-runbook.md` against `runbook.outline.yaml` by glob, so a
   new runbook is covered the moment it exists — no registration step, and no way to add
   one that quietly is not checked.
4. **The unit contract.** These pass with no database and no data root:

   ```powershell
   poetry run pytest -q tests/unit/test_doc_outline.py tests/unit/test_design_doc.py tests/unit/test_render_determinism.py tests/unit/test_doc_pdf.py
   ```

<!-- anchor: rollback -->
## Rollback

**Nothing here writes a database, and every output is regenerable from its source.** That
is the module's defining property: the render is a pure function of the `.md`.

- **A bad render** — fix the `.md` and re-render. `git checkout -- docs/design/<doc>.html`
  also works, but it is the weaker move: it restores the page while leaving the source that
  produced the bad one in place.
- **A render written to the wrong place** — a default-paths run wrote beside the sources.
  `git status` names exactly what moved; `git checkout --` the ones that were not yours.
  This is the failure mode `--out-dir` exists to prevent.
- **A default-paths board run in a lane that did not hold the pen** — eleven artifacts plus
  the board moved. Same recovery, larger blast radius, and the reason the explicit
  `--backlog`/`--out` form exists.
- **A PDF** — never committed. Delete and rebuild.
- **A feedback capture** — the one artifact here a person authored rather than a renderer
  produced, so it is the one thing that cannot be regenerated. Treat
  `docs/design/feedback/*.yaml` and the scans as source, not output: a lost capture means
  going back to the reviewer.

<!-- anchor: troubleshooting -->
## Troubleshooting

| Symptom | Diagnosis | Fix |
|---|---|---|
| `FileNotFoundError` from `render_design_doc.py --out-dir` | The directory does not exist; the script does not create it | `mkdir` it first |
| `doc_outline.py: error: the following arguments are required: --outline, --doc` (exit 2) | It was invoked positionally | Both flags are named and required |
| The validator exits `-1` or `255` instead of `1` | PowerShell's display of the process exit code, not the value. Measured through bash it is `1` | Read the exit code in a POSIX shell, or compare against `0` rather than against `1` |
| `FAIL — … missing required section` on a doc that looks complete | The heading is there and the `<!-- anchor: id -->` marker is not — anchors are the contract, headings are not | Add the marker before the heading |
| An SME's notes stopped re-attaching after an edit | An anchor id was renamed or renumbered; feedback is keyed to anchors | Anchors are authored and stable — restore the id. Never use `--` inside one (L11) |
| A committed `.html` differs from a fresh render | The stale-render case Verify step 1 exists for | Commit the refresh; do not edit the `.html` |
| A board render moved eleven files you did not expect | A default-paths run fires every sub-renderer; only an explicit `--backlog`/`--out` run does not | Use the explicit form when you do not hold the render pen |
| `doc_to_pdf.py` cannot find a browser | No Brave/Chrome/Edge on this machine | Venue limit, not a defect. Print from the `.html` instead — it carries the same `@media print` sheet |
| An import of `drydocs.design_doc` (or another flat name) | ADR 0018 D4 re-export shim, due for removal at the roll after next | Import `drydocs.docgen.<name>` |

<!-- anchor: contacts-escalation -->
## Contacts & escalation

- **Procedure owner:** the DryDocs producer (repo owner).
- **When to run any of this is the session ritual's call**, not this page's — `CLAUDE.md`
  §0 owns the render-at-session-close rule and the stale-render check that follows it.
- **Adding a doc type is a contract change, not a render.** A new `*.outline.yaml` under
  `docs/design/templates/` defines a new anchor namespace, and the L5/L6 loops key feedback
  to those anchors — so it goes through the same review as any other contract, and the
  template's own header comment is where the reasoning is recorded.
- **A stale render found in the wild is reported with the command that found it**, per the
  Verify step above. That is cheaper than an argument about whether a page is current.
- **A disagreement between this page and the code:** the code wins, and the fix is this
  page. Appendix B re-derives every count and every claim here.

<!-- anchor: appendices -->
## Appendices

### A. The module census — four modules, two scripts, no verbs

| File | Reached by | What it does |
|---|---|---|
| `drydocs/docgen/design_doc.py` | `scripts/render_design_doc.py` | the renderer: md → the single HTML surface, margin anchors, the `Rev N · commit` footer, the L5 feedback controls |
| `drydocs/docgen/doc_outline.py` | its own `-m` CLI; `tests/unit/test_doc_outline.py` | the outline contract: loads a `*.outline.yaml`, checks required anchors and the traceability matrix |
| `drydocs/docgen/doc_pdf.py` | `scripts/doc_to_pdf.py` | browser discovery and headless print-to-PDF with normalized dates |
| `drydocs/docgen/plan_ideas.py` | `scripts/render_ideas.py`, itself fired by a default-paths board run | renders the `IDEAS.md` inbox to its read view |

Two thin CLIs — `scripts/render_design_doc.py` and `scripts/doc_to_pdf.py` — plus the four
outline templates under `docs/design/templates/`. Both scripts exist *"until the
`drydocs/cli.py` entrypoint-boundary TODO is resolved"*, which is why the module has no
registered verb rather than that being a design choice.

### B. Re-derive one-liners — the code wins on disagreement

```powershell
# does ANY registered verb reach this module? (reads the callbacks, never --help; J37)
poetry run python -c "import inspect, drydocs.cli as c; print([ (i.name or i.callback.__name__) for i in c.app.registered_commands if any(n in inspect.getsource(i.callback) for n in ('docgen','doc_outline','design_doc','plan_ideas','doc_pdf'))] or 'NONE')"

# how many sub-renderers does a default-paths board run fire? (two independent counts)
Select-String -Path scripts/render_board.py -Pattern 'import render_[a-z_]*' | Measure-Object | ForEach-Object Count
Select-String -Path scripts/render_board.py -Pattern 'render_[a-z_]*\.main\(\)' | Measure-Object | ForEach-Object Count

# the outline contracts on this tree
poetry run python -c "import glob; from drydocs.docgen.doc_outline import load_outline; print({p.split('/')[-1]: load_outline(p).doc_type for p in sorted(glob.glob('docs/design/templates/*.outline.yaml'))})"

# is a render deterministic? render twice to two directories and compare
poetry run python scripts/render_design_doc.py docs/design/<doc>.md --out-dir <dir-a>
poetry run python scripts/render_design_doc.py docs/design/<doc>.md --out-dir <dir-b>

# which browser the PDF path would use here
poetry run python -c "from drydocs.docgen.doc_pdf import find_browser; print(find_browser())"
```
