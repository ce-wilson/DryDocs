# Company-side prompt — close out the `caa04060..7c18ff4b` port after the merge

> Producer-drafted 2026-08-20 for the company-side assistant. Paste or read whole.
> Your branch `drydocs-port-20260820` is reviewed producer-side
> (`docs/reviews/port-review-7c18ff4b-20260820.md`, reaches you at the next port):
> **mergeable as committed.** Nothing below blocks the `--no-ff` merge — the SME
> makes that call. These are conditions on YOUR follow-up list, two of which it
> does not carry, and one ask. Guardrails stand: nothing pushes to `cewilson`,
> the HR files stay stashed until the tree is settled, `port-prompt.md` is
> retired, never refreshed.

## 1. The FID ratification is not done until it is in the gate-log — as ONE commit

What landed in the port is an authorization **sentence** in `PORT-REPORT-7c18ff4b.md`.
That is not machine-readable: `config/gate-log.md` is the audit surface
(`union-append` — dropping an entry is an audit violation) and the only thing
`scripts/render_gates.py` reads, so until the entries exist there your board and
`web/src/generated/gates.json` show `fid-identity-and-scope` as **unratified**.

Your follow-up 1 already lists the entries. Two constraints on how they land:

- **The `fid-identity-and-scope` sign-off and the `seal-attribution-match-policy`
  §G3 amendment go in ONE gate-log commit.** The producer instruction was an
  *atomic pair*; a sign-off without its amendment is the half-state that word
  forbids. Write both entries, run `render_gates.py` + `render_board.py`, commit
  the three together.
- The other defer-notes (G102 / G22 / T19 / N12 / N13 / §E2 / K7–K15 /
  corporate-backbone) may ride the same commit or a second one — they are
  *defer* records, not sign-offs, and have no pairing constraint.

## 2. Mark the company-local fixes in the PORT-REPORT as not-port-introduced

The reconcile commit (258 files) also carries two changes that are **yours, not
the port's**: the `control-m-service-now-config.py` syntax fix (cleared six
AST-crash tests) and the Idea-109 `repo_root` sweep over nine company modules
(which exposed and fixed the `cli.py` F821 — producer-verified company-only).

Add a short **"Not port-introduced"** section to `PORT-REPORT-7c18ff4b.md` naming
those paths. Why it matters: the next reconcile runs a divergence census against
`7c18ff4b`, and without that section nine company modules read as producer drift
and get re-litigated. This is an append to the report, not a rewrite — a third
small commit on the branch before the merge, or the first after it.

## 3. One ask: the `drydocs-scrape` connector back-flow

The 2026-08-19 live fetch that closed the `fcdo-frameworks` capture holes ran on
connector code that exists only on your side. The producer wants the
**mechanism** back (transport-injectable `Connector`, the SSRF allow-list, the
run-manifest shape) with no realm, space id, URL, or payload — the same
mechanism-not-instance rule every back-flow follows. When convenient: a sanitized
patch or a pointer to the files and their tests, so the producer can reproduce
it generically. Not urgent; ride it with the next relay.

## What you do NOT need to do

- No manifest rows — the five divergences the `caa0406` report named
  (`description_tokens.py`, `detect.py`, `test_runbook_currency.py`,
  `email-dl-contact-point.yaml`, `ui-components.yaml`) get their
  `PORT-MANIFEST.yaml` rows **producer-side** (Idea-142) and reach you at the
  next port. Keep your kept-divergence list in the report as is; that is the
  input.
- No answer on "done never crosses" vs. "keep the further-along" for the 12
  shared backlog ids — that is a producer ADR question (0013 Clause 4), and the
  SME rules it. Your union stands as applied.

## Done when

Gate-log holds the FID pair in one commit and the board is regenerated; the
PORT-REPORT carries the not-port-introduced section; `stash@{0}` is popped and
the three HR files are back and still untracked; the stale `port-prompt.md` is
retired. Reply with the three commit SHAs.
