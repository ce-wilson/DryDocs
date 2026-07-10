# internal/remediation — spinoff doc port (G3 / ADR 0002-B)

**Provenance:** ported VERBATIM 2026-07-10 from `ce-wilson/DryDocs-v0-archive@controlm-spinoff`
(tip `3e6a39a`), `internal-standards/` — the remediation IP the archive inventory surfaced
(0002-B §4). **Classification: Internal** (real folder/job names, QR names, VR self-heal codes,
PAT product mappings, Jira ids throughout — publish-excluded per PUBLISH-BOUNDARY.md).
**Trust: VERBATIM** — nothing edited, links are archive-relative and may dangle (see below).

## What this is

The rule source and plans the `drydocs-remediation` component (G3) builds from:

| File | Role |
|---|---|
| `standards-rules-registry.md` | **R1–R29 machine-checkable rules** — the single source for validation (Gate 2) + greenfield generation (Gate 3). Rules carry ratification status (✅/🟡/❓): **unratified rules stay gate-bound** — the engine may WARN on 🟡/❓ but only ✅ rules drive greenfield changes. |
| `controlm-remediation-{spinoff-plan,flow,m0-poc-scope,phases-m1-m4-scope,information-needed}.md` | the phased component plans (M0 PoC → M4) |
| `m0-poc-worked-example.md` | the M0 worked example (real folder/job — the reason this dir is Internal) |
| `standards-normalization-plan.md` | predecessor plan — EVALUATE against current `knowledge/standards/` before relying on it |
| `governance/` | the R13–R29 source corpus (naming standards, NFR catalog, critical-batch/self-heal, greenfield recommendations) |

## HELD FOR REVIEW — not yet ported (user call 2026-07-10)

Two governance docs are **deliberately absent**, pending the user's classification review
(candidate Internal-Confidential — real escalation routing / queue registry):

- `governance/escalation-scim-reference.md`
- `governance/scim-hpsm-queue-registry.md`

They remain readable in the archive. Cross-references to them from the ported docs
(e.g. critical-batch §self-heal, nfr-catalog) will dangle until the review lands them here.

## Caveats

- **Links are archive-relative.** Five sibling docs were already carried to
  `knowledge/standards/` in an earlier re-home (calendar-resolution-projection-plan,
  data-center-naming-convention, description-field-metadata-plan, folder-naming-convention,
  README) — links to those resolve there, not here. Do not "fix" links in these files;
  they are a VERBATIM record. A curated/sanitized mechanism-only extraction into
  `knowledge/` is possible later work, per doc, through the usual classification decision.
- The NEWER contract is `docs/design/drydocs-remediation-tdd.md` — where these plans and
  the TDD conflict, **the TDD wins** (0002-B §4).
