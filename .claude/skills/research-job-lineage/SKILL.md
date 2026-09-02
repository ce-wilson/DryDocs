---
name: research-job-lineage
description: "Trace a Control-M job or folder up or down its chain — who produces its input, where its output goes, which platform moves the data, and who owns each hop — then turn every unresolved link into a backlog item or IDEAS entry. Use for 'where does this file come from', 'what depends on this folder', 'trace this feed end to end', or when filling lineage gaps in the backlog. Not for a failure investigation (use research-job-failure) or an unfamiliar platform (use research-general)."
---

# research-job-lineage

Answers *what feeds this job, what it feeds, which platform moves the data between, and who
owns each hop* — and converts every link that cannot be closed into tracked work.

**Load `research-probe-discipline` first** — SME interview, outcome vocabulary, controls, probe
log and whitelist live there. This skill adds the **anchor questions, source order, the link
test, and the backlog integration.**

---

## 1. Open

Five-question interview from `research-probe-discipline` §1, plus four:

> **6. What is the anchor?** — a folder, a job, or a feed. Name it exactly.
> **7. Which direction?** — upstream (who sends to us) or downstream (who consumes)?
>   *Do not accept a directional word without unpacking it.* "The opposite direction" once
>   meant *further upstream in the same flow*, not *outbound* — and the wrong reading
>   propagated into the source order and the acceptance test before it was caught.
> **8. What grain?** — folder, job, feed, or file. The answer changes which sources apply.
> **9. Is there a known-good sibling** that already traces end to end? A worked example is
>   worth more than any amount of schema reading.

Read the whitelist for the platform family before probing.

---

## 2. Source order

### 2.1 Orchestrator definition — the anchor

Pull the folder/job from the definition store — the `CM_` replica (the `controlm-db` skill
maps every Control-M concept to its table and column) or the folder XML export, which is the
rung-1 bulk form (`drydocs_lineage/extractors/controlm_xml.py` reads it). Establish: does the
anchor resolve at all, what jobs it contains, what conditions link them, and what variables it
declares.

**Folder-name and job-name conventions are per-team, not platform-guaranteed.** A positional
decode (`drydocs_core.orchestration.controlm.parse_folder_name`) may hold for one application
and silently fail for another. Derive a **candidate** and mark it as such.

### 2.2 The job's declared metadata

The description field is the contract between the job and everything outside the orchestrator:
delivery mechanism, account, environment, source contact, route identifiers. Parse it against
the **closed vocabulary** (`description_tokens`, the same core parser the loaders run) — and
**count unknown spellings rather than dropping them**.

**Two traps here:**

- A **null value can be conformant**. If a standard exempts a field for some mechanisms, a
  missing value is compliance, not a gap. Partition by mechanism before reporting coverage.
- A standard may **forbid recording** a value that demonstrably exists on the platform. That is
  a defect in the standard — take it to the standard (`knowledge/standards/`), not to the
  loader.

### 2.3 The platform the metadata names

Now go to the transfer/movement platform. Two things to establish before profiling anything:

- **Which platform is it, actually?** Internal branding, generational renames and generic use
  of a family name make this genuinely ambiguous. A name in a job token may denote a
  *mechanism*, an *era*, or a *product*.
- **How many exports does it have?** Two exports of the same object with near-disjoint columns
  are common. If they share one key they **join** — and the union is often the full picture
  neither alone provides.

### 2.4 The platform's definition vs event records

Definition (durable) and event (short-window) records are usually **different objects with
different keys and different lifetimes**. Establish for each:

| | definition | event |
|---|---|---|
| identity | | |
| grain | | |
| carries the artifact name? | | |
| retention | | |
| shared key with the other? | | |

**The grain is the finding.** A definition scoped to *(account → directory)* carries no file
identity; a definition scoped to *(feed, extension)* does. Two platforms doing the same job may
differ here, and a model ported across them will be wrong.

### 2.5 Ownership

Resolve the owning application from an **authoritative record** — a deployment CI's
`correlation_id`, not a name lookup. Record which surface asserted it.

Expect owner-vs-name disagreement: a folder named for one application may be owned by another,
by design. Operational routing (where incidents actually land) is stronger evidence than a
name.

### 2.6 Documentation, then ticketing

Wiki before portal, scoped, with both controls. Then incidents/changes for the anchor's CI —
they frequently name connections nothing else does.

---

## 3. The link test

Run the anchor down these links and **record which link it dies at**. Rejection is a result:
three candidates dying at the same link is a stronger finding than one that succeeds.

| # | Link | Passes when |
|---|---|---|
| 1 | anchor resolves | the folder/job returns from the definition store |
| 2 | dependency declared | a waiting/triggering relationship exists (watcher, condition, command) |
| 3 | artifact named | a concrete file, mask or dataset — **and the directory it lands in** |
| 4a | **durable handle** | an attribute that reaches the platform's **definition** record (account, directory, cost center) |
| 4b | **ephemeral handle** | an attribute that reaches only the **event** record (often the file name), and expires |
| 5 | counterpart record found | the handle actually retrieves a record — a **set**, not necessarily one row |
| 6 | counterparty named | the sender/receiver is identified |
| 7 | attributable | the counterparty resolves to an owning application |

**Record 4a and 4b separately.** A candidate that passes only on 4b is traceable *this week and
not next* — a materially weaker result, and reporting them as one "pass" hides the only
constraint that cannot be engineered around.

Keep a running candidate table in the log:

| # | Anchor | Reached link | Outcome | Note |
|---|---|---|---|---|

---

## 4. Backlog and IDEAS integration — specific to this skill

Every link that does not close becomes tracked work. This is what makes a lineage trace pay
for itself twice.

**Before creating anything:**

1. Search `docs/restructure/backlog/items/` and `docs/restructure/IDEAS.md` for an existing
   entry on the same gap. Extend it rather than duplicating.
2. **Take the id from the allocator, never from the tree** (the mint rule, `CLAUDE.md` §0 and
   the `groom-backlog` skill):
   `python .claude/skills/groom-backlog/validate.py --next-id <SERIES>` (`Idea` for the inbox,
   the epic letter for an item). It unions the local items, every remote ref's tree and every
   id ever added in history, so an id minted on a parallel branch or the other machine is
   already taken. **Mint, push the stub with its final title, then write the body.** Ids are
   stable references — cited by signed gate records — so an id is never renumbered and a gap
   in the sequence is never reused. *(The company build of this skill said "compare the max
   id against `origin/main` and prefer renumbering the ungroomed side"; that is the failure the
   allocator exists to prevent, and it is corrected here.)*

**What to create:**

- **A gap with a known shape** → a backlog item, `module:` naming the owning component
  (`MODULE_MAP.md` says which directory that is), with **the link number as its acceptance
  criterion** ("closes link 5 for series X").
- **A gap needing a ruling** → an `IDEAS.md` entry, stating the readings and what each costs.
  A groom cannot pick between two readings; do not force it to.
- **A modeling question** → route to the HITL gate. Never introduce a label, relationship type
  or constraint from a trace.

**Write the link number into the item.** It is what lets a later session verify the gap
actually closed, instead of re-deriving the whole chain.

---

## 5. Exit criteria

1. Every link 1–7 is **pass**, **fail-with-reason**, or **not-applicable-with-reason**.
2. 4a and 4b are recorded **separately**.
3. Ownership is resolved from an authoritative record, with the surface named.
4. Every definition/event grain difference is stated explicitly.
5. Every unresolved link has a backlog item or IDEAS entry carrying its link number.
6. Every negative has an outcome class; every `exhausted*` a control.
7. Whitelist updated; coverage and reuse recorded.

---

## 6. Outputs

| Artifact | Where |
|---|---|
| Research log — hop ledger, candidate table, link results | `internal/research/<subject>-research.md` |
| Probe log (JSONL, live) | `internal/research/_probes/<subject>-probes.jsonl` |
| New / corrected whitelist rows | `internal/research/_registry/source-whitelist.yaml` |
| Backlog items with link-number acceptance | `docs/restructure/backlog/items/` (allocator-minted) |
| Rulings and open questions | `docs/restructure/IDEAS.md` (allocator-minted) |
| Preserved captures | the evidence root (`DRYDOCS_DATA_ROOT`) — cite the path |

---

## 7. Standing constraints

- **Nothing in `config/` is edited by research.** **Zero graph writes.** A new relationship
  type goes through `docs/RELATIONSHIP_GUIDE.md`, the vocabulary registry and the gate.
- **A candidate derivation is not a rule.** Present it to the SME; let the gate confirm.
- **A difference between two sources is not a defect** until a transform, convention or
  predecessor tool is ruled out.
- **Corrections stay in place**, struck rather than deleted.
- **Mechanism-only in this skill**; real folder, job, account and application values live in
  the Internal log and the whitelist.

---

*Provenance: built producer-side from `internal/research/mm-aar-research.md` (Part 7),
reviewed at `2c184a79` on `main`; the company original lives on an unmerged research branch.
Changes at the review: §4 step 2 rewritten from "compare max ids and renumber" to the
allocator mint rule (the one place the company method was wrong for this repo, not merely
differently homed); the definition-store, parser and module-map cross-references added; U.S.
spelling.*
