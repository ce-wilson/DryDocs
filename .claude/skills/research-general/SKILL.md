---
name: research-general
description: "Subject-agnostic research for an unfamiliar system, platform, acronym or term — 'what is this, who owns it, what does it connect to, and where is it documented?'. Use when opening a trace on something nobody on the team has mapped yet, when decoding an unexplained acronym or token value, or when a platform is internally branded and its vendor is unknown. Not for a specific job's lineage (use research-job-lineage) or a specific failure (use research-job-failure)."
---

# research-general

The default research plan. Answers *what is this, whose is it, what does it connect to, and
where is it written down?*

**Load `research-probe-discipline` first** — the SME interview, the outcome vocabulary, the
control rules, the probe log and the whitelist all live there and are not repeated here. This
skill adds only the **opening questions, the source order, and the exit criteria.**

The log shape, the `?`-node hinge (`drydocs_deepdoc.mindmap` — on `feat/mm-deepdoc-investigate`
until MM3 merges; see the backbone for where it lives) and the five capture rungs are stated
once at the top of `research-probe-discipline`.

---

## 1. Open

Run the five-question SME interview from `research-probe-discipline` §1, plus one:

> **6. What is the smallest question that would make this worth doing?**

Write it into the log's `central_question`. If it cannot be phrased as a question, stop and say
so — there is no trace to open yet.

Then **read the shared ledgers** (`internal/research/_registry/` — the whitelist, `terms`,
`platforms`, `id-shapes`; `research-probe-discipline` §6) for the subject family before
probing anything. A term, a platform or an id shape already there is cited, not re-derived.

---

## 2. Source order

Work down this list. Stop when the central question is answered — the order is by
*cost-to-value*, not by completeness.

### 2.1 Vendor identity — first, if a vendor is plausible

Do this before internal documentation, because it can move the whole subject from **Internal**
to a **publishable External reference with no entitlement at all**. A vendor's public docs
answer *what a route is, what a transfer record contains, what a partner means* for free.

**When a platform is internally branded, the vendor is not in the documentation — it is in the
implementation.** Rebranding reaches names, logos and prose; it rarely reaches protocol
details. Look, in roughly this order:

- **User-agent strings** the API requires or sends
- **Cookie names** (session tokens often carry a vendor product name)
- **Mandatory headers** and their spellings
- **Default ports** and port ranges
- **On-disk path conventions** and account-name shapes
- **Error-message wording** and error-code vocabularies
- **Version strings** embedded in labels — a version is what makes vendor docs *usable*

In the reviewed trace the vendor surfaced in a **mandatory `User-Agent` header** after two days
of documentation not naming it, then was confirmed by a **cookie name** that matched a vendor
product, a **version label** in a field value, and finally an internal change record naming the
vendor's processes.

**Guard (from `research-probe-discipline` §4.4):** a vendor named in a *supported-client
compatibility table* is not the vendor of the system. Ask whether the name appears as the
**subject** or in a list of things the subject talks to.

**Check `platforms.yaml` before any of this.** If the platform is already there, the vendor,
version, era and ownership surface are settled and cited — the two days above were spent once
and need not be spent again. If it is not, the row you write at close is the trace's most
reusable output: `internal_names`, `vendor`, `product`, `revealed_by` (the surfaces above,
each with what was observed), `era`, `ownership_surface`.

Once the vendor is named, register the public reference the way this repo registers every
external source: `reference/REGISTRY.yaml` with a `source_url`, classification External
(`CLAUDE.md` §2-§3; the `reference-librarian` agent owns that file) — that is the platform
row's `graduates_to`.

### 2.2 Internal documentation

Search the wiki **before** the portal where both exist — the wiki is usually API-reachable and
the portal usually is not. Scope the search, and **bracket every zero-result with the two
controls** (`research-probe-discipline` §3.1).

A zero result in one space is a finding about that space, not about the term. The unscoped
control often finds where the term actually lives.

### 2.3 API / specification

Probe for a machine-readable contract before profiling any export. **But read the operation
list before promoting a lead to rung 1** — a product page's feature bullets settle in seconds
what a spec hunt costs a session.

> **"There is an API" is not "there is a source."** An *operational* API that performs actions
> is not a *metadata* API that describes them. If every operation changes state — upload,
> trigger, delete — it answers nothing a lineage question asks, and it is not a thing to
> explore casually.

### 2.4 UI exports

Rung 5, and usually the only durable metadata a platform exposes. Two rules:

- **The rung ladder can invert.** Sometimes the rung-2 API reaches only the *operational*
  surface while the durable metadata exists solely as a UI download. Probing "upward" is still
  right — but the upward move that helps may be **sideways, to the vendor**.
- **One export is not the platform** (`research-probe-discipline` §3.2). Ask whether a second
  export of the same object exists; two exports with near-disjoint columns are common, and if
  they share one key they join.

### 2.5 Ticketing and change records

Cheap, authoritative, and frequently the fastest route to ownership. An incident or change
record yields the **CI**, the **assignment group**, the **owning application id** and often the
vendor — in one lookup.

The deployment CI's `correlation_id` is the authoritative application-id join. **Prefer it over
an id obtained by name** (`research-probe-discipline` §1).

---

## 3. Decode as you go

**Read `terms.yaml` first** (`research-probe-discipline` §6). A token already in the ledger is
cited by its row — expansion, confidence and its `not:` list — and is not decoded again; the
ledger exists because every log used to rebuild this table from nothing.

Then keep an acronyms and terms table in the log from the first hop, as the **session's
working copy**: the tokens the ledger did not know, with a confidence column
(`Confirmed / Partial / Likely / To verify / Corrected`). Never silently upgrade a confidence.
At close, every row the session settled or corrected goes to `terms.yaml` with its evidence
(§8 of the backbone). A term that reaches `Confirmed` with an SME behind it is a candidate for
the software registry's `acronyms:` section (`config/taxonomy/software-registry.yaml`, the
SME-ruled home) by the change-artifact path — never a direct edit from a trace, and never
without `verified_by` agreeing with the registry's `source`.

**Two decode traps, both observed:**

- **Homonyms.** The same word means different things on different surfaces — a "route" can be a
  file-transfer path on one platform and a storage destination on another. **Match on the value
  shape and the schema, never on the column or tag name.**
- **Era collisions.** The same identifier string can name different things across generations
  of a platform (a legacy numbering scheme overlapping a current one). Resolve through a host
  or instance list, never by matching the digits.

---

## 4. Exit criteria

The trace closes when **all** hold:

1. The central question is **answered**, or explicitly **reclassified** with the reason.
2. Every open question names **who must rule it** — SME, gate, or a specific evidence pull.
3. Every claim carries a **capture rung** and a **platform/scope stamp**.
4. Every negative carries an **outcome class**, and every `exhausted*` a **control**.
5. Sources are written to the **whitelist**, including the blocked and irrelevant ones.
6. Coverage and reuse are recorded in the notes entry.

---

## 5. Outputs

| Artifact | Where |
|---|---|
| Research log (two-phase, hop ledger, acronyms, open questions) | `internal/research/<subject>-research.md` |
| Probe log (JSONL, written live) | `internal/research/_probes/<subject>-probes.jsonl` |
| New / corrected whitelist rows | `internal/research/_registry/source-whitelist.yaml` |
| Preserved captures | the evidence root (`DRYDOCS_DATA_ROOT`); cite the path, never re-serialize |
| Anything worth doing later | `docs/restructure/IDEAS.md`, minted through the allocator (the `groom-backlog` skill) |

---

## 6. Standing constraints

- **Nothing in `config/` is edited by research.** Registration is gate-bound; a whitelist row
  is not authorization.
- **Zero graph writes.** No new label, relationship type or constraint is introduced by a trace
  — a trace may only *ask* for one, through the gate.
- **Corrections stay in place.** Strike a wrong hop and record what replaced it; do not delete
  it. The recurrence is usually the finding.
- **A difference between two sources is not a defect** until a transform, a convention or a
  predecessor tool has been ruled out.
- **SME knowledge checks an answer; it never supplies one** as evidence without a stamp.

---

*Provenance: built producer-side from `internal/research/mm-aar-research.md` (Part 5),
reviewed at `2c184a79` on `main`; the company original lives on an unmerged research branch.
This skill is where the U-1..U-6 method findings Idea-236 asked to keep producer-side landed
(§2.1, §2.3, §2.4). Changes at the review: the companion citations re-pointed to
`research-probe-discipline`, the registry and allocator cross-references added, U.S.
spelling.*
