# drydocs-remediation — how a defect becomes an authorized fix

This module finds problems in Control-M definitions and proposes corrections. The
question it exists to answer safely is **"may we change this?"** — and the answer is
never the detector's to give.

> **Contract:** `docs/design/drydocs-remediation-tdd.md` wins on conflict. This page is
> the governance walk-through, not a second specification. Rule *values* (real name maps,
> real registry ids and ratification state) are company-side and injected by the caller;
> what lives here is mechanism.

---

## The rule

> **Only ✅-ratified rules may change a definition. Everything else is WARN-only.**

This is enforced in code, not by convention. `transform.propose_greenfield` skips
unratified rules and reports them in `skipped_unratified` — it never silently applies
one. An unratified rule is not "a rule nobody got around to"; it is structurally
incapable of touching a job.

---

## The status ladder

Every rule carries a status in the rules registry (`internal/remediation/standards-rules-registry.md`):

| | Meaning |
|---|---|
| **❓ open** | needs an SME decision before it can even be checked consistently |
| **🟡 provisional** | observed and believed correct, not signed off |
| **✅ ratified** | signed off at the HITL gate — and only now may it drive a change |

### Status is independent of severity

A rule can be **🔴 must-fix** and **🟡 provisional** at the same time. R39b — a data-file
watcher catting a multi-GB file into sysout — is exactly that: we are confident it is a
real defect, and we are still not authorized to fix it automatically.

That separation is the point. *How bad is it* and *may we act unilaterally* are different
questions, and collapsing them is how a linter starts editing production.

---

## Why a detector needs its registry entry first

The registry is the single source for **both** gates:

- **Gate 2 — validate:** run the rules → per-unit conformance report
- **Gate 3 — design:** read each rule's *greenfield action* → the proposed fix

One entry drives both, so as a rule moves ❓ → 🟡 → ✅ both tighten together and cannot
disagree.

A detector with no entry breaks that. It emits findings nothing can rank, nothing can
turn into a fix, and — the real problem — **nothing can sign off on**. There is no
artifact for the SME to approve; you would be asking someone to ratify a behavior that
exists only as Python. The entry is not paperwork ahead of the code. **The entry is the
thing that gets ratified.**

### The worked example: four classes, three detectors

R41–R44 were added as one change, and the split is the lesson.

Three of them (duplicate declaration in one scope, folder-name delimiter drift, stale
authored provenance) are mechanical: register, detect, fixture, done. **R43 is not.**
It is a genuine question — when one name is resolved by two carriers, which carrier owns
it? — and the answer changes what a fix even looks like: rename one carrier, or declare
the shell export. No ruling existed, so R43 shipped **registered with no detector**.

That is the pairing rule read in the other direction. An entry without a detector is a
decision on the record, waiting to be ratified. A detector without an entry is a finding
nobody can sign off on. The failure mode worth naming is letting the three easy rules
carry the hard one over the line: shipping R43 provisional-with-detector would have put
a finding in front of an SME with **no defensible action attached to it**.

---

## The lifecycle, end to end

1. **Observed** — a defect class found in a real definition set, with evidence, written
   up in a capture.
2. **Registry entry, 🟡 provisional** — check, engine, severity, source, and the
   *greenfield action*. This is where the judgement call gets written down rather than
   assumed. For a rule like "the job name and the resource pool disagree about the target
   platform", the entry has to say **which one is wrong** — and a guess written into a
   greenfield action becomes an automated rename.
3. **Detector** — emits `Finding(..., ratified=False)`. It surfaces in the report and is
   prefixed `UNRATIFIED (warn-only)` in the Jira handoff, so a reader is never left to
   infer the rule's standing.
4. **HITL gate** — the SME rules the question from step 2 against real findings rather
   than hypotheticals.
5. **✅ ratified** — and only now may the transform engine act on it.

---

## The second gate people miss: blast radius

Ratification alone is not sufficient. **Blast radius is a separate veto.**

Folder renames and watch-template rewrites are **not Tier-1 material** — propose only,
through the Tier-2 path with mandatory review, however ratified the rule is. R4 (folder
naming) says so outright: flag, never auto-rename.

| | Tier 1 | Tier 2 |
|---|---|---|
| What | deterministic Python, idempotent, unit-tested per rule | agentic, judgement-requiring |
| Runs | in the batch | as a *proposal*, through mandatory HITL review |
| Promotion | — | into Tier 1 when a pattern recurs **identically**, with its own idempotence test |

No LLM runs anywhere in Tier 1.

---

## Two failure classes, reported apart

Not a governance rule, but it belongs beside them, because ranking them together teaches
the wrong triage order:

- **Name drift produces silence.** The fact never loads. Nothing is wrong on any screen;
  a row is simply absent, and absence is not alarming until someone asks for it.
- **A value-contract breach produces a confidently wrong row.** The name resolves, the
  value is false, and everything downstream treats it as true.

The second is worse and must never be filed as a lint warning.

---

## Module invariants

- **Writes no graph.** Neo4j and the Oracle extract are read-only corroboration; the only
  durable outputs are the greenfield artifact and the Jira.
- **Imports only `drydocs_core.*`** — never another component
  (`tests/unit/test_module_boundary.py` enforces it).
- **Format-agnostic definitions** — no XML assumption outside `XmlDefinitionFormat`.
  `dump()` still raises: emitting importable XML needs the vendor schema.

Related: `detect.py` (R1 + the conformance pass) · `transform.py` (the ratified-only
engine) · `jira.py` (the handoff boundary) · `xml_bridge.py` (staged extract → definitions)
