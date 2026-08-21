# Company-side prompt — close out the `caa04060..7c18ff4b` port after the merge

> Producer-drafted 2026-08-20 for the company-side assistant. Paste or read whole.
> Your branch `drydocs-port-20260820` is reviewed producer-side
> (`docs/reviews/port-review-7c18ff4b-20260820.md`, reaches you at the next port):
> **mergeable as committed.** Nothing below blocks the `--no-ff` merge — the SME
> makes that call. These are conditions on YOUR follow-up list, two of which it
> does not carry. **Everything here is recorded in YOUR upgrade ledger
> (`port-exec-state.md` / the PORT-REPORT) and stays there — nothing in this
> prompt sends anything to the producer.** Guardrails stand: nothing pushes to
> `cewilson`, the HR files stay stashed until the tree is settled,
> `port-prompt.md` is retired, never refreshed.

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

## 3. Note for your ledger: the `drydocs-scrape` connector is a back-flow candidate

The live fetch that closed the `fcdo-frameworks` capture holes ran on connector
code that exists only on your side. Record it in your upgrade ledger as a
**back-flow candidate, mechanism only** — the `Connector` protocol with an
injectable transport, the SSRF scheme allow-list, the run-manifest shape, and
their offline tests. **Do not name a space, corpus, URL, realm, or purpose
string in that entry, and do not put one in any producer-facing text** — the
mechanism is the candidate, never the instance (the same rule every back-flow
follows, and the reason the producer side holds only sanitized templates). If
and when a sanitized patch is prepared, that is a company decision made
company-side; this prompt asks for nothing to be sent.

## What you do NOT need to do

- No manifest rows — the five divergences the `caa0406` report named
  (`description_tokens.py`, `detect.py`, `test_runbook_currency.py`,
  `email-dl-contact-point.yaml`, `ui-components.yaml`) are **groomed
  producer-side as J51** (2026-08-20) and their rows reach you at the next
  port. Keep your kept-divergence list in the report as is; that is the input.
- No answer on "done never crosses" vs. "keep the further-along" for the 12
  shared backlog ids — **ruled producer-side 2026-08-20 (ADR 0013 Clause 4):
  status is per-repo; a port never writes it.** Your union stands as applied,
  and it was already the right rule.
- **Neither F3 nor F4 is yours** — both are done on the producer and were never
  in your lane; do not reach into `IDEAS.md`, `backlog.yaml`, or the ADRs for
  them.

## Done when

Gate-log holds the FID pair in one commit and the board is regenerated; the
PORT-REPORT carries the not-port-introduced section; `stash@{0}` is popped and
the three HR files are back and still untracked; the stale `port-prompt.md` is
retired — **defined (2026-08-20 evening, after your session rightly asked):** NOT
`git rm` (it would orphan every reference), and NOT a reset to a fresh living
ledger (that recreates the two-ledger divergence that made your step-43 copy
stale). Archive your steps-43+ content to `docs/port-prompt-archive-company-
steps-43-NN.md` with a `status: DATED RECORD` header, and replace
`docs/port-prompt.md` with a short POINTER: the port authority is the producer's
`docs/port/port-prompt.md` read at the certified tag + `PORT-MANIFEST.yaml` + the
`reconcile-port` skill; your port history lives in `port-exec-state.md` and
`PORT-REPORT-*.md`. References keep resolving; it never becomes a ledger again —
that is what "never refresh" means. The same tombstone-pointer shape `backlog.yaml`
took on the producer side today. **Record the close-out in `port-exec-state.md` as you have been** — that
ledger is the record, and it is yours. Nothing is reported back.
