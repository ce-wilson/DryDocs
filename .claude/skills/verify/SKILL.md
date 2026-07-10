---
name: verify
description: Runtime-verify DryDocs changes at their real surface. Use after changing the design-doc renderer (drydocs/design_doc.py), the board/gate-page renderers, or the CLI — drives the emitted HTML through headless Edge and captures the executed DOM/screenshot as evidence, instead of re-running tests.
---

# verify — DryDocs runtime verification recipes

## Design-doc renderer (drydocs/design_doc.py)

Surface = the emitted HTML executed in a browser (the annotate JS builds the HITL layer
at runtime — file inspection alone misses it).

1. **Render the real docs** (also required anyway — committed renders must match source):
   ```powershell
   $env:PYTHONPATH = "."; python scripts/render_design_doc.py docs/design/*.md
   ```
   `git status docs/design` — only surfaces you intended to change may be modified.

2. **Determinism**: `Get-FileHash` each output, re-render, hash again — must be identical.

3. **Execute the JS and dump the live DOM** — reuse the `drydocs.doc_pdf` recipe
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

## CLI / pipeline changes

Use the `run-drydocs` skill (ingest chain, m3-verify, model-layer checks without Neo4j).
