---
name: research-job-failure
description: "Research a batch job, feed or transfer failure — find what documentation exists, what connects to what, and who owns it. Use when given an incident, an alert, a failure notification email, or 'this job failed and I need to know what it touches'. Covers the notification -> ticket -> change-window -> run-history order and the failure-surface traps. Not for mapping a healthy job's lineage (use research-job-lineage) or for an unfamiliar platform (use research-general)."
---

# research-job-failure

Answers *what failed, what does it connect to, who owns it, and what is written down about it?*

**Load `research-probe-discipline` first** — the SME interview, outcome vocabulary, controls,
probe log and whitelist live there. This skill adds the **failure-specific questions, source
order, traps and exit criteria.**

---

## 1. Open

Five-question interview from `research-probe-discipline` §1, plus four:

> **6. What failed, and when?** — the window matters more than the symptom.
> **7. How did you learn about it?** — alert, email, ticket, downstream complaint, or a user.
> **8. Is this recurring, or the first occurrence?**
> **9. Which team owns the failing component — and is that the same team that owns the thing
> it failed *on*?**

Question 7 is the highest-yield of the four. **The channel a failure arrives on is itself
evidence** — it names the registered contact, often names the artifact, and tells you which
surface the platform considers authoritative for failures.

Read the shared ledgers for the subject family before probing (`research-probe-discipline`
§6): the whitelist for where to look, `platforms` for the platform's ownership surface and
error taxonomy already on record, `terms` for the tokens in the notification.

---

## 2. Source order

### 2.1 The notification itself — first

Whatever arrived: alert email, SNS/CloudWatch alarm, platform failure notice, monitoring page.
Mine it before anything else. It typically carries, for free:

- the **artifact** (file name, dataset, job) — often the only place this appears
- the **error text and its class**
- the **registered contact** the platform notifies — i.e. the ownership fields the platform
  actually *uses*, as opposed to the ones merely populated
- whether **ticketing is configured** at all

**Two things to check explicitly:**

- **Is a ticket raised?** A failure notice that says ticketing is not configured means the
  failure is **invisible to every ticket-based process**. That is a finding, and usually a
  fixable gap.
- **Structured metadata in free-text fields.** Alert descriptions and job descriptions
  frequently carry `key: value` blocks stuffed into a prose field — assignment group, severity,
  application id, environment. Parse them; they are the same facts the graph wants
  (`drydocs_core.orchestration.controlm.description_tokens` is the parser for a Control-M
  description). Normalize against the closed vocabulary and **count unknown spellings rather
  than dropping them**.

### 2.2 Ticketing — incident, CI, group, close notes

One lookup yields most of the ownership picture: **CI**, **assignment group**, **priority /
urgency / impact**, **categorization**, **close code** and **close notes**. Close notes often
contain the actual root cause in plain language.

The deployment CI's `correlation_id` is the **authoritative application-id join** — prefer it
over any id obtained by name.

**Known limit:** work notes may not be reachable through an API bypass even when the record is.
Record that as `blocked` with the surface hit, not as "no work notes exist"
(`research-probe-discipline` §2).

### 2.3 The platform's own error taxonomy

Failure notices and vendor docs usually ship an **Issue Type** vocabulary — authentication,
connection, network, permission, transfer-operation. Capture it; it is the vocabulary any
`:Failure` model should use, and it is authored by the people who built the thing. Registering
it is the ontology's call (`docs/RELATIONSHIP_GUIDE.md`, the vocabulary registry, the gate) —
a trace captures, it does not register.

Watch for **route-level stop-on-error semantics**: on some platforms one bad credential halts
*further execution* rather than failing a single item, so the blast radius is a queue, not a
file.

### 2.4 Changes in the window — **do this before profiling run history**

> **Check for a planned change covering the failure window before you interpret any pattern in
> the data.**

In the reviewed session a data pattern was confidently explained as load balancing across
nodes. It was a **planned A-side to B-side failover**, documented in a change record, and the
crossover in the data landed exactly inside the change window. The change record also supplied
the vendor attribution and corrected an application id.

Query changes by CI and by window. A change record gives you: the window, the affected
environments, the test plan (which names the runtime components), and whether it succeeded.

### 2.5 Run / transfer history

Now profile the history — with the partition rules below.

### 2.6 Documentation — last

Wiki before portal. Scope the search and bracket zero-results with both controls. Ask
specifically: **is there a runbook, and is it current?** "Absent" and "stale" are different
findings.

---

## 3. Failure-specific traps

**3.1 Never conclude "no failures" from a success view.**
An export may be a success projection. Before claiming a clean record:

- **partition by status** — does a failure status value even appear in the domain?
- **partition by account, folder, window and region** — one slice is not the population.
- apply the **schema control** (`research-probe-discipline` §3.2): does the export have an
  error/status column that *could* express a failure?

Observed: one account's history was 100% complete over a week; another account's was 6% failed.
The first was recorded as "this history is a success view" — wrong, and it was used to answer
an open question.

**3.2 The failure channel and the record channel may be different surfaces.**
Successes may be queryable while failures are pushed as notifications, or vice versa. Establish
which before designing anything. If failures arrive by mailbox, then the failure record and the
email corpus are the *same* problem (the docmeta email corpus, Q10).

**3.3 A failure record often carries the join key the definition record lacks.**
Definitions are frequently scoped to accounts, directories or partners and carry **no artifact
identity**; the failure event carries the **file name**. So the failure channel may join to the
orchestrator on precisely the attribute the definition channel cannot.

**3.4 Retention windows are short and asymmetric.**
Event history is often days, and the artifacts themselves shorter still. Consequences:

- a fact cited from event history is **unfalsifiable within a week** — cite a **preserved
  capture and the window it covers**, never a query someone could "just re-run";
- **absence means *not in this window*, never *did not happen*.**

**3.5 One incident is one incident.** Recurrence needs a second occurrence, not an assumption.

---

## 4. Build the connection map

The deliverable that makes this skill worth running is *what connects to what*. Assemble, and
mark each edge **observed / documented / inferred**:

```text
upstream producer ──▶ transport/route ──▶ landing artifact ──▶ waiting job ──▶ downstream
     │                  │                   │                  │
 contact/owner    environment+node      file name       owning app (CI)
```

For every node record: **who owns it**, **which surface asserted that**, and **what is missing**.
An `inferred` edge is a candidate for the SME, not a fact.

---

## 5. Exit criteria

1. The failure has a **named error class** from the platform's own vocabulary.
2. An **owning group** and a **CI** are identified, each with the surface that asserted them.
3. The **application id** is resolved authoritatively, not by name.
4. A runbook is found, or explicitly recorded **absent** / **stale**.
5. A **change correlation** exists, or an explicit *"none found in window, control passed"*.
6. The connection map is drawn, with every edge marked observed / documented / inferred.
7. Every negative carries an outcome class; every `exhausted*` a control.
8. Whitelist updated; coverage and reuse recorded.

---

## 6. Outputs

| Artifact | Where |
|---|---|
| Research log with hop ledger and connection map | `internal/research/<subject>-research.md` |
| Probe log (JSONL, live) | `internal/research/_probes/<subject>-probes.jsonl` |
| New / corrected whitelist rows | `internal/research/_registry/source-whitelist.yaml` |
| Preserved captures (notifications, exports, records) | the evidence root (`DRYDOCS_DATA_ROOT`) — cite the path |
| Gaps worth fixing (e.g. ticketing not configured) | `docs/restructure/IDEAS.md`, minted through the allocator |

---

## 7. Standing constraints

- **Read-only.** Never file, update, comment on or close a ticket. Never call an operational
  API that changes state — several "transfer" APIs upload, delete or trigger.
- **Nothing in `config/` is edited by research.** Zero graph writes.
- **Corrections stay in place**, struck rather than deleted.
- **Mechanism-only in this skill**; real values live in the Internal log and the whitelist.

---

*Provenance: built producer-side from `internal/research/mm-aar-research.md` (Part 6),
reviewed at `2c184a79` on `main`; the company original lives on an unmerged research branch.
Changes at the review: the description-token parser and the ontology route cross-referenced,
U.S. spelling.*
