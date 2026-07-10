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

## HELD — KEPT OUT OF THE REPO (user decision 2026-07-10)

Two governance docs are **deliberately absent** and stay out for now (reviewed 2026-07-10:
real escalation routing / queue-registry content, candidate Internal-Confidential):

- `governance/escalation-scim-reference.md`
- `governance/scim-hpsm-queue-registry.md`

**Durable location:** `ce-wilson/DryDocs-v0-archive@controlm-spinoff` (tip `3e6a39a`),
`internal-standards/governance/` — the archive branch is the system of record for them;
scratchpad copies are ephemeral. **Re-entry is tracked as backlog item G10** (sanitized —
it names this README section, not the docs). Until G10 lands them or records a permanent
out-of-band read path, cross-references from the ported docs (critical-batch §self-heal,
nfr-catalog) dangle by design.

## Caveats

- **Links are archive-relative.** Five sibling docs were already carried to
  `knowledge/standards/` in an earlier re-home (calendar-resolution-projection-plan,
  data-center-naming-convention, description-field-metadata-plan, folder-naming-convention,
  README) — links to those resolve there, not here. Do not "fix" links in these files;
  they are a VERBATIM record. A curated/sanitized mechanism-only extraction into
  `knowledge/` is possible later work, per doc, through the usual classification decision.
- The NEWER contract is `docs/design/drydocs-remediation-tdd.md` — where these plans and
  the TDD conflict, **the TDD wins** (0002-B §4).
