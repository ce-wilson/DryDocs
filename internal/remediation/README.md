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

## HELD — PERMANENTLY OUT OF THE REPO (G10 SME gate, 2026-07-12)

Two governance docs are **deliberately absent, permanently** (held 2026-07-10 at the G3
doc port; re-reviewed with the SME 2026-07-12 at the G10 gate — decision: keep out, both):

- `governance/escalation-scim-reference.md`
- `governance/scim-hpsm-queue-registry.md`

**Why:** the only corpus docs carrying real employee names, internal hostnames, and the
full SEAL↔queue↔SNOW-group ownership roster — candidate Internal-Confidential; kept off
this producer remote entirely rather than relying on the publish strip.

**System of record / out-of-band read path:**
`ce-wilson/DryDocs-v0-archive@controlm-spinoff` (tip `3e6a39a`),
`internal-standards/governance/` — re-clone read-only when needed; scratchpad copies are
ephemeral, never commit them. The remediation engine consumes their DATA the way it
consumes all rule values: **company-side injection** (the Tier-1 seam) — nothing
producer-side builds against these files. Their engine-relevant MECHANISMS (the column-Y
`EAPPLICATION` conformance rule, the queue-code grammar, the job↔SCIM 1:1 integrity rule)
may later be extracted sanitized into `knowledge/` per the Caveats extraction path —
per doc, through the usual classification decision.

Cross-references from the ported docs (critical-batch §self-heal, nfr-catalog) dangle
**permanently** by this decision; resolve them in the archive.

## Caveats

- **Links are archive-relative.** Five sibling docs were already carried to
  `knowledge/standards/` in an earlier re-home (calendar-resolution-projection-plan,
  data-center-naming-convention, description-field-metadata-plan, folder-naming-convention,
  README) — links to those resolve there, not here. Do not "fix" links in these files;
  they are a VERBATIM record. A curated/sanitized mechanism-only extraction into
  `knowledge/` is possible later work, per doc, through the usual classification decision.
- The NEWER contract is `docs/design/drydocs-remediation-tdd.md` — where these plans and
  the TDD conflict, **the TDD wins** (0002-B §4).
