# ADR 0012 — Name the load surface by the DATA: subject, cadence, acquisition

```yaml
status: ACCEPTED          # the naming decision; execution is GN2 and is separately gated
date: 2026-08-11
authored_by: GN1 session (desktop; SME-directed)
deciders: [SME]           # design agreed in session 2026-08-11
layer: cross-cutting
relates_to:
  - 0010-internal-source-term-abstraction.md   # the same concern, one layer down
  - 0002-component-database-topology.md
  - drydocs/cli.py                             # CANONICAL_LOAD_SEQUENCE, LOADER_REGISTRY
  - config/source-registry.yaml                # registry v2 — COMPANY-CANONICAL
  - docs/port/port-prompt.md                        # the deprecation policy crosses here
executed_by: GN2          # nothing in this record renames anything by itself
```

## Why this is an ADR and not a rename commit

In the SME's words: *company jargon entered a project that was meant to be generic
from the start.* `seal`, `pat`, `m1`/`m3` are not poor names — they are **someone
else's vocabulary**, load-bearing in one company and meaningless outside it. That
puts this squarely under the standing goal of a sanitized, standalone DryDocs
another organization could adopt, and makes it a decision with alternatives rather
than a tidy-up.

It also touches a **public contract**. CLI verb names are called by company crons,
scripts and the `run-drydocs` skill, across a repo boundary, so a rename is a
breaking change for a consumer this repo cannot see.

---

## Clause 1 — Three axes, currently collapsed into one

A `LoadStep` today carries a command name, a `mode`, and a hand-assigned tuple of
`profiles`. Three independent questions are answered by that one structure, and
answering them in one place is why none of them is answered well.

| Axis | Question | Today | **Decided** |
|---|---|---|---|
| **Subject** | what data is this? | half-encoded in the command name | **the command name, and nothing else** |
| **Cadence** | how often does it change? | `_COLD` / `_ALL` / `_NONE` literals in `cli.py` | **the source registry entry** |
| **Acquisition** | how do we get it? | invisible; `adapter:` exists but is not policy | **the source registry entry, swappable** |

**The step declares the subject. The registry declares cadence and acquisition. A
profile is DERIVED by filtering on cadence.**

This makes *"the source and the data dictate how often it needs refreshing"* true
in code rather than true in a comment while a tuple literal decides. `load_profile`
becomes a filter over declared cadence, not a hand-maintained membership list.

### Why the collapse is not merely untidy

`refresh-reference` bundles **seven loaders across three unrelated sources**. That
bundle has no organizing principle — so it cannot have a *hole*, because there is
nothing for a hole to be in. That is how `pat_team_roles` came to be gate-confirmed,
implemented, registered, and run by no operator path at all, with nothing red.

Grouping by source makes absence structural: a source either has its loaders wired
or it does not.

---

## Clause 2 — Three bands; only the middle one is source-keyed

The 17-step sequence is three kinds of thing wearing one shape:

```
prepare:   check · bootstrap · bootstrap-schema-graph · apply-supplements
load:      load-<subject>          ← source-keyed, cadence-derived
verify:    verify-<scope>
```

Forcing `check` or `bootstrap` into a source scheme would be the same category
error inverted, so **only the load band takes the subject grammar.**

`m1-verify` and `m3-verify` carry the identical defect the SME named: milestone
ids that mean nothing to a reader and everything to whoever was there. They are
renamed with the rest, not exempted for being internal.

---

## Clause 3 — The subject names the data; the source id names the tool

**Decided, including for widely-known SaaS.** The SME raised ServiceNow and Jira
as candidate exceptions on grounds of recognizability. The counter-argument is the
SME's own, applied one level up:

> The acquisition may change — CSV today, a database call tomorrow.

The same is true of the *system*. If CMDB data later arrives from a different ITSM,
`load-servicenow` is wrong and `load-cmdb` is still right. Recognizability is real
and belongs in the **source registry**, which is where a reader goes to ask "where
does this come from" — not in the command, which answers "what data is this."

| Today | Defect | Direction |
|---|---|---|
| `refresh-reference` | 7 loaders, 3 sources, one name | split by subject |
| `ingest-controlm` | names the **vendor** | subject-named; Control-M becomes the *source* |
| `load-software-registry` | names an internal artifact | subject-named |
| `m1-verify` / `m3-verify` | milestone ids | scope-named |

`ingest-controlm` is worth its own line: §2 of the operating guide already separates
orchestration **vendors** (BMC / AutoSys / Airflow) from the model so the model stays
vendor-neutral. A command named after the vendor contradicts a decision already made,
and would have to be renamed anyway the day AutoSys lands.

### Controlled vocabularies

Both are **open-but-governed** — additions are cheap riders, never a catch-all.

**Cadence** (on the source):

| Value | Meaning |
|---|---|
| `static` | rarely changes; cold start only |
| `slow` | weeks or months — business applications, org structure, software inventory |
| `daily` | the operational estate — batch jobs, pipelines |
| `on-demand` | only when asked — adhoc probes, experiments |

Cadence sits on the **source**, so if two loaders on one source need different
cadences, that is a signal the entry is really two datasets. That forcing function
is intended.

**Acquisition** (on the source): `file-drop` · `db-pull` · `api-pull` · `repo` · `scrape`

This is the seam the CSV-to-database move needs: change `acquisition`, swap the
adapter, and the loader, the command name, the sequence position and the cadence
are all unchanged. It is also — see Clause 5 — the fix for a live defect, not only
future-proofing.

---

## Clause 4 — Deprecation policy, because the verbs are a public contract

**New names ship with the old ones as deprecated aliases for one port cycle, then
drop.** Precedent exists rather than being invented here: `cli.py` already carries
legacy-verb aliasing for supplements.

**GN2 must not overlap an in-flight port.** A wide rename landing in pieces leaves
two repos disagreeing about verb names for as long as the pieces take, so the change
freezes other producer work, lands whole, is ported whole, and only then does normal
work resume. This is the SME's condition and it is the correct one.

---

## Clause 5 — The three layers do NOT move together

This is the clause GN2 would otherwise discover the hard way.

| Layer | Ownership | How it moves |
|---|---|---|
| **CLI verbs** | producer-canonical | GN2, with aliases (Clause 4) |
| **`LOADER_REGISTRY` keys, loader class names** | producer-canonical, internal | GN2, freely — no external caller |
| **Source registry ids** (`pat:*`, `snow:*`) | **COMPANY-CANONICAL** | **NOT a producer edit** |

Registry v2 is a company-canonical surface under the standing divergence ledger —
future ports reconcile v2 against v2 — and retired ids are governed by the D4
refusal list, which exists to make a resurrected id structurally impossible.

**Therefore: renaming a `pat:*` source id is a cross-repo reconciliation that mints
new retired-id entries, not a rename.** GN2 executes the first two layers. The third
is proposed to the company through the relay channel and lands only by agreement.
A producer-side unilateral change here would fork the registry on identity, which is
precisely what D4 exists to prevent.

---

## Clause 6 — What this does NOT decide

- **It does not fix the silent-skip bug.** A step whose input is missing reports
  success today, and a default run loads synthetic fixtures into a real graph. That
  is **G78**, a p0 correctness defect, deliberately kept out of this record: naming
  is generalization, that is correctness, and coupling them would hold a live bug
  behind a design decision.
- **It does not split any chain.** That is **G79**, and it lands under the OLD names
  on purpose — splitting and renaming in one change makes the port diff unreviewable,
  and the split is the half that carries behavioural risk.
- **It does not rename anything.** GN2 does, after this is accepted.

---

## Alternatives considered

**A. Leave the names; document the mapping.** Cheapest, and it fails the actual
goal — a glossary that translates `seal` and `pat` for an outside reader is an
admission that the vocabulary is someone else's. It also leaves cadence in code.

**B. Rename the commands only, leave cadence in the profile tuples.** Half the
value. The names would read better while the thing that actually caused the
`pat_team_roles` omission — a bundle with no organizing principle and hand-assigned
membership — would remain. Renaming a bundle does not give it a principle.

**C. Rename everything at once, including source ids, producer-side.** Rejected on
Clause 5: registry v2 is company-canonical and D4 governs retirement, so this forks
the registry on identity. The cost of the fork is silent and permanent; the cost of
the relay is one round trip.

**D. Exempt widely-known SaaS tools from the subject rule.** Rejected on Clause 3,
using the SME's own acquisition-may-change argument. The exemption buys familiarity
and sells back the stability the whole change exists to gain.

---

## Consequences

**Gained.** Cadence becomes a declared property of the data rather than a decision
embedded in code. Acquisition becomes swappable, which is both the CSV-to-database
seam and part of the G78 fix. Commands say what they load. A source with unwired
loaders becomes visible instead of merely wrong.

**Paid.** One port cycle carrying deprecated aliases; a frozen window for GN2; a
cross-repo negotiation for the source-id layer; and every surface derived from the
sequence regenerates at once — `load-map.json`, `load-map.html`, `ingest.sh`, the
startup runbook Appendix B (held by `test_load_sequence_surfaces`), the load runbook,
and the skills that name verbs.

**Not paid, and worth saying:** no graph write changes, no ontology term moves, and
no gate is required by this record. It renames a surface, not a meaning.
