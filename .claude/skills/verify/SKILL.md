---
name: verify
description: Runtime-verify DryDocs changes at their real surface. Use after changing the design-doc renderer (drydocs/docgen/design_doc.py), the board/gate-page renderers, or the CLI — drives the emitted HTML through headless Edge and captures the executed DOM/screenshot as evidence, instead of re-running tests.
---

# verify — DryDocs runtime verification recipes

## Design-doc renderer (drydocs/docgen/design_doc.py)

Surface = the emitted HTML executed in a browser (the annotate JS builds the HITL layer
at runtime — file inspection alone misses it).

1. **Render the real docs** (also required anyway — committed renders must match source):
   ```powershell
   $env:PYTHONPATH = "."; python scripts/render_design_doc.py docs/design/*.md
   ```
   `git status docs/design` — only surfaces you intended to change may be modified.

2. **Determinism**: `Get-FileHash` each output, re-render, hash again — must be identical.

3. **Execute the JS and dump the live DOM** — reuse the `drydocs.docgen.doc_pdf` recipe
   (`find_browser()` + its flag set) with `--dump-dom` (or `--screenshot=<path>`):
   ```python
   base = [str(find_browser()), "--headless=new", "--disable-gpu", "--no-sandbox",
           "--no-first-run", "--no-default-browser-check", "--disable-extensions",
           "--disable-background-networking", "--disable-sync", "--disable-component-update",
           "--disable-dev-shm-usage", "--run-all-compositor-stages-before-draw",
           "--virtual-time-budget=10000"]
   # + [f"--user-data-dir={tempdir}", "--dump-dom", Path(html).resolve().as_uri()]
   ```
   Then assert on the DOM: control counts, id coverage vs the file, panel/toolbar presence.

### Gotchas (verified 2026-07-09)

- **Launch headless Edge from PowerShell/`subprocess`, NOT Git Bash** — from Bash,
  `--dump-dom` intermittently returns 0 bytes with no error. A 0-byte dump is an
  environment artifact, not evidence about the change.
- Keep `--run-all-compositor-stages-before-draw`; dropping it correlated with empty dumps.
- Console output of UTF-8 files shows mojibake (`âœŽ` for ✎) in PS 5.1 — display only.
  When printing DOM slices from Python, use `.encode("ascii", "backslashreplace")`
  (stdout is cp1252).
- Brave hangs headless on this box (2×180s, L4 finding) — Edge/Chrome only.

### Local dev servers — the venue rule (J52, 2026-08-25)

- **A claim about what a LOCAL DEV SERVER (Vite, drydocs-api, the ADK server)
  rendered or returned is evidence ONLY when the browser making the request was
  launched by the session making the claim.** A browser the session merely
  ATTACHED to (the Chrome extension, a pre-existing tab) is not a known venue,
  and "verified" without a known venue is the J18 defect in browser form.
- **The recipe, not just the prohibition:** drive a session-launched headless
  browser from the session scratchpad — the 2026-08-21 close used
  puppeteer-core against a Vite dev server on an alternate port and behaved
  correctly throughout. The same launch caveat above applies: PowerShell/
  `subprocess`, never Git Bash.
- **The observation this rule comes from, cited as an observation:** on
  2026-08-21 an extension-connected tab at `localhost:5173` served a DryDocs
  checkout that did not match the working tree while reporting `isLocal: true`,
  and cache-bypassed fetches from inside that tab disagreed with `curl` against
  the same address. WHY that happened is unproven and deliberately not asserted
  here — the rule stands on the venue argument alone: if you did not launch the
  browser, you do not know what it is pointed at.

## Console routes — the paper form (O88)

A console page is a function of the graph at a moment, so its paper form is a CAPTURE
of the executed DOM, not a render: `npm run paper -- --persona <id>` in `web/` drives
the running console through headless Edge (Playwright-driven, because `--dump-dom`
cannot sign in and a sign-in screen is not a captured page), and writes one
self-contained `.html` per route under `<DRYDOCS_DATA_ROOT>/console-captures/<stamp>/`
with the L6 gutter tags and a `route · commit · captured · api · persona` footer.
`--verify-print` re-opens each file under `emulateMedia({ media: 'print' })` and records
the tag's computed `display`. The capture is a valid input to the design-doc recipe
above: `html_to_pdf(<capture>)` prints it with the same gutter. Details and the default
route set: `web/README.md`, "Paper form (O88)".

## CLI / pipeline changes

Use the `run-drydocs` skill (ingest chain, m3-verify, model-layer checks without Neo4j).
