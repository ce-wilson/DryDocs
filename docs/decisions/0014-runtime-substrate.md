# ADR 0014 — Runtime substrate: logs, settings and data zones are one per-machine settings group

```yaml
status: ACCEPTED          # ruled 2026-08-25 by chad.wilson, WITH AMENDMENTS — see "What the ruling changed"
accepted: 2026-08-25      # drafted PROPOSED at G104; the drafting session never accepts its own ADR
date: 2026-08-24
authored_by: G104 (desktop)
deciders: [chad.wilson]
layer: 0-configuration
relates_to:
  - 0009-configuration-substrate.md            # THE reconciliation — see "Reconciling with ADR 0009"
  - 0002-component-database-topology.md        # per-component logging lands per component
  - drydocs_core/config.py                     # the pydantic-settings shape this extends
  - drydocs_core/run_log.py                    # DRYDOCS_LOGDIR > SPIDERP_LOGDIR > ~/logs/DryDocs
  - drydocs_core/adapters/sql_run_log.py       # shares run_log's resolver
  - agents/common/llm_ledger.py                # the per-DAY jsonl exception
  - drydocs_core/data_root.py                  # DRYDOCS_DATA_ROOT, mandatory since G81
  - config/data-zones.yaml                     # G81's declared zones
  - .env.example
executed_by: G105 (1-3), G106 (4), G107 (5), G108 (6), G109 (7 — DONE 2026-08-24)
```

> **Nothing in this record changes code.** G105–G108 implement it and each `depends_on` this
> ADR, so nothing implemented an unratified ruling. Clause 7 was already executed by G109,
> which ran before the ruling because its remaining work did not depend on any clause here.

## What the ruling changed

Ruled 2026-08-25. **Accepted with four amendments**, all recorded here rather than left in
the chat that produced them.

| Clause | Ruling |
|---|---|
| 1 | **AMENDED** — the settings group is per-KIND, not one global set. See clause 1 |
| 3 | **AMENDED** — the naming rule DERIVES from the declaration; the ledger exception is withdrawn |
| 4 | **AMENDED** — `prune-logs` reads retention from the declaration, not from flags or literals |
| 5 | **DEFERRAL RESOLVED** — `drydocs_api` is out of scope; it has no batches |
| 6 | **WIDENED** — the audit line covers routes that WRITE, not only routes that execute Cypher |
| 7 | **CORRECTED** — the clause's forward list was overtaken by G109 before the ruling |
| 2 | as drafted |

### The governing principle, in the SME's words

> *"The goal is to have everything configurable, not hardcode."*

This is broader than the ADR 0009 question it was given in answer to, and it is the reason
three of the four amendments exist, so it belongs at the top rather than inside one clause.

**It does not mean "everything lives in the environment."** A declaration in committed YAML
is equally configurable, and is where a value with domain meaning belongs. What the
principle forbids is a value buried in a Python literal — which is exactly what this ADR's
own survey found three times over: `run_log.py:147` hardcodes the `load.` prefix,
`llm_ledger.py` hardcodes `qa.graph_qa`, and `AppSettings.log_level` is declared and read by
nobody.

So the rule has two halves that do not compete:

1. **Nothing is hardcoded.** Every runtime value is declared somewhere a reader can find it.
2. **Where the declaration lives** is decided by what kind of value it is — a per-machine
   operational fact goes to the environment and `.env` (gitignored, `!.env.example`
   re-included as the template); a domain fact goes to committed YAML under ADR 0009.

Half 2 is the anti-drift line this ADR already drew. Half 1 is the SME's addition, and it is
what turns clauses 1, 3 and 4 from "configure the log directory" into "stop hardcoding the
things around it".

## Context

A 2026-08-20 survey (Idea-152) read this repo's logging and path layer beside a sister
internal project's, and found the runtime substrate is the one layer with no declared
shape. Everything else — ontology, taxonomy, sources, precedence — has a config family, a
reader and a guard. Logs and paths have environment variables, three writers, and no rule.

### What the survey found, re-verified at drafting

The survey is four days old and G81 landed in between, so every claim was re-checked
against the tree at `21cc11c3` rather than carried forward. **Two of its findings are now
stale, and saying so is part of the record** — an ADR that argues from a false premise
gets re-litigated the first time somebody checks.

| Survey claim | Status at drafting |
|---|---|
| `run_log.py` resolves `DRYDOCS_LOGDIR` → `SPIDERP_LOGDIR` → `~/logs/DryDocs` | **Holds** — `run_log.py:61-66` |
| `adapters/sql_run_log.py` honors only the legacy var | **STALE — false.** It imports `claim_log_path` and `caller_stamp` from `run_log` (line 50), so it shares the resolver and honors both. The two log families already agree on the directory; they disagree only on file naming |
| `.env.example` documents neither root | **HALF-STALE.** G81 added a `DRYDOCS_DATA_ROOT` block on 2026-08-23 with the mandatory-since note. `DRYDOCS_LOGDIR` is still undocumented |
| `AppSettings.log_level` is wired to nothing | **Holds.** `config.py:70` declares it; nothing in `drydocs/`, `drydocs_core/`, `drydocs_api/` or `agents/` reads it. `cli.py:938` is the sole `basicConfig` and takes its level from `--verbose` alone |
| `llm_ledger.py` writes a per-DAY `qa.graph_qa.<YYYYmmdd>.jsonl` beside per-RUN files | **Holds** — `llm_ledger.py:83-84` |
| Six code zones have no `source-registry` row | **Holds** — and G81 declared them in `config/data-zones.yaml` instead, which is a second declaration rather than the single one clause 7 asks for |

The shape of the problem after G81: **the data root got a declaration and the log
directory did not.** G81 made `DRYDOCS_DATA_ROOT` mandatory, declared every data zone with
a mode in `config/data-zones.yaml`, and documented it where an operator looks. The log
directory still resolves through a two-variable fallback chain to a home-relative default,
with no declaration, no rotation and a settings field nothing reads. This ADR proposes
that the two stop being different kinds of thing.

## Reconciling with ADR 0009 — the hard requirement

ADR 0009 rule 1 is unambiguous: *"Source of truth is git text, permanently."* An
env-var-and-`.env` settings group has to be squared with that before anything else here
matters.

**This is an exception ADR 0009 already permits, not an amendment to it.** Rule 1 does not
say *all configuration* is git text. It says:

> Anything **an SME gates, a port carries, or a classification test guards** is a committed
> file.

That is a scope clause with three named tests, and the runtime substrate fails all three:

1. **No SME gates a log directory.** The HITL gate reviews meaning — relationship types,
   mappings, ontology terms. `log_retention_days` is not a domain fact and there is no gate
   prompt shape that would hold it.
2. **No port carries it — carrying it would be a defect.** `PORT-MANIFEST.yaml` marks
   `config/dev-environment.yaml` `disposition: canonical-company`, and its `entry_rule`
   settles the principle in one line: *"Each side keeps its OWN file — every value in it is
   a local fact."* The startup runbook's Appendix A states the same rule in the imperative:
   *"container names, ports and paths are local facts that must never be copied across the
   repo boundary."* A committed `log_dir` is exactly such a fact, and the port would carry
   one machine's path onto the other side.
3. **No classification test guards it.** `tests/unit/test_classification.py` requires a
   `classification` on every *source*. A log directory is not a source; it has no
   provenance, no trust axis and nothing to publish.

There is also standing precedent inside 0009's own accepted world: `NEO4J_URI`,
`NEO4J_USER` and `NEO4J_PASSWORD` have lived in `.env` since before 0009, `config.py`'s
three pydantic-settings groups are named in 0009's `affects:` list, and 0009 did not treat
either as a violation. `DRYDOCS_DATA_ROOT` joined them at G81 under the same logic.

**The line this ADR draws, so the exception cannot widen by drift:** a value belongs in the
runtime settings group if and only if it is a **per-machine operational fact** — a path, a
verbosity, a retention window. The moment a value has a domain meaning, a provenance, or an
SME who would want to see it change, it is configuration and it goes to git text under
0009. `config/data-zones.yaml` shows both halves working together correctly and is the
model: the **map** of zones is committed git text (which zones exist, what mode each has,
why); only the **root** they hang off is per-machine. Nothing in this ADR moves a committed
file into the environment.

No change to ADR 0009 is proposed. If the user reads rule 1 as broader than its scope
clause, this ADR becomes an amendment and 0009 gains a "runtime substrate" carve-out — that
is the one place the ruling could go the other way, and it is called out here rather than
buried.

## Decision

Seven clauses. Each is decided or explicitly deferred with a named trigger.

### 1. One `RuntimeSettings` group, declared PER KIND — DECIDED, AMENDED AT RULING

**Amendment (2026-08-25).** As drafted this clause gave ONE `log_dir` / `log_level` /
`log_retention_days` for everything. Ruled per-KIND instead, declared in
`config/log-kinds.yaml` (schema `drydocs.log-kinds.v1`) on the `config/data-zones.yaml`
idiom: declare in YAML, resolvers derive, a guard asserts they agree.

**What forced it** is the governing principle above, not a volume problem — four kinds and
86 files is no pressure at all. `kind` is currently a filename convention rather than a
code concept: three sites mint it and none agree (`run_log.py:147` hardcodes `load.`,
`llm_ledger.py` hardcodes `qa.graph_qa`, `sql_run_log` takes a caller-supplied `base_name`
with no prefix enforcement, so that family can write any kind it likes). Nothing can be
configured per kind while no declaration says what the kinds ARE.

The declaration carries one `root` block (base / path / `env`), a `defaults` block (level,
`retention_days`, `rotation`, `format`, `dir`), then one entry per kind naming its `writer`
and overriding only what differs — `load` inherits everything; `qa` takes `rotation:
per-day`, `format: jsonl` and a longer retention; `sql` is declared so the family that
accepts any `base_name` becomes checkable; `api` is declared `status: planned` for clause 6
so the kind exists before its writer does. An optional per-kind `dir` and a
`DRYDOCS_LOGDIR_<KIND>` override generalize the `<INTEGRATION>_LOG_DIR` pattern Idea-152
captured from the sister project.

**A defect this fixes by construction.** `config/data-zones.yaml`'s `run-logs` zone declares
`env: DRYDOCS_LOGDIR` and `data_zones._resolve()` ignores the field, handling only
`base: home` and `base: data_root`. With the variable set, the zone resolves to the untouched
default while every real log lands elsewhere — and G81's declared-equals-resolved guard
misses it, because that guard only walks zones carrying a `helper` and `run-logs` has none.
A single `root` block is one place that resolves the variable, so the class cannot recur.
**The guard gap is separate and must be closed regardless of this clause** (Idea-171).

The fields below are now the per-kind `defaults`, not a global set:

| Field | Default | Today |
|---|---|---|
| `log_dir` | `~/logs/DryDocs` | `run_log.DEFAULT_LOGDIR` |
| `log_level` | `INFO` | `AppSettings.log_level`, read by nothing |
| `log_retention_days` | `90` | does not exist |
| `data_root` | **no default** | `data_root.py`, mandatory since G81 |

`AppSettings.log_level` moves into it; `AppSettings` is left holding nothing and is
retired in the same change rather than kept as an empty shell.

**Defaults do not change, and `data_root` keeps having no default.** G81 made the data root
mandatory *because* a silent default is how a write lands on somebody's source data;
folding it into a settings group must not quietly restore one. The group's `data_root` is
typed as required and raises the same G78 operator-error exit 2, not a pydantic traceback.

`SPIDERP_*` stays one cycle as a deprecated alias on **both** log families, emitting a
deprecation warning when it is the one that resolved, then is dropped. The trigger for
dropping it is the next port after this ADR is accepted — named, because "one cycle" with
no event attached is how a deprecation becomes permanent.

### 2. `dictConfig` from that group — DECIDED

Stdlib `logging.config.dictConfig`, no new runtime dependency. Console handler plus a
JSON-lines file sink in `log_dir`; level from `RuntimeSettings.log_level`; `--verbose` still
wins over the settings value. `run_log.py`'s header/summary contract is untouched — it is a
separate, deliberate artifact with its own readers, and this clause adds a logging backbone
beside it rather than replacing it.

`cli.py`'s single `basicConfig` becomes the one `dictConfig` call. The rule that follows
from it: **no module calls `basicConfig`.** A library that configures the root logger steals
it from its caller.

### 3. The naming rule DERIVES from the declaration — DECIDED, AMENDED AT RULING

**Amendment (2026-08-25). The clause as drafted was wrong, and it was wrong because it was
written without counting.** It asserted `<kind>.<name>.<YYYYmmdd-HHMMSS>.{log|jsonl}` and
called the ledger the one exception to it. Measured against the real directory (desktop,
`C:\coding\projects\logs\DryDocs`, J18): **the rule matches 5 of 86 files.** The other
79 read `load.<name>.v1.<ts>.log`, and the `v1` sits INSIDE `loader_name` rather than as a
fourth field — so the rule was not off by one segment, it described the wrong shape, and
the ledger was never "the one exception". 92% of the directory departed from it.

**The rule is therefore derived rather than asserted:**

```
<kind>.<name>.<stamp>.<ext>
```

where `<stamp>` granularity comes from the kind's `rotation` (`per-run` -> `YYYYmmdd-HHMMSS`,
`per-day` -> `YYYYmmdd`) and `<ext>` from its `format`. `<name>` stays free-form, which is
what makes the 79 `.v1` files conforming.

**The ledger exception is WITHDRAWN — not overruled, dissolved.** Under a derived grammar
`qa.graph_qa.20260820.jsonl` is conforming: `kind=qa`, `name=graph_qa`, `stamp=20260820`,
`ext=jsonl`. The per-day rotation is a declared property of that kind, not a departure from
a rule. The drafted clause flagged itself with "one exception in a naming rule is how naming
rules die"; the amendment removes the exception rather than defending it, which is the same
concern answered properly.

The ledger keeps its per-day file on its own merits, now recorded as the reason for
`rotation: per-day` rather than as an excuse: it is append-only, and its `run` line is the
ONLY place the full question text lands (`:AgentRun` carries sha256 + length), so its value
is that one file reads end to end. Measured: 2 day-files, 54 entries, 18.9 KB, 14 run ids —
per-run sharding would give 14 files, not the "hundreds of fragments" the draft claimed.

### 4. `drydocs prune-logs`, reading retention FROM the declaration — DECIDED, AMENDED AT RULING

**Amendment (2026-08-25).** The verb takes its retention from `config/log-kinds.yaml`, not
from hardcoded values and not from flags alone. `prune-logs` with no arguments does the
declared thing; flags remain one-off overrides. That is the governing principle applied to
this clause — a 90-day window living in a function default is exactly the hardcoded value
the principle forbids, and it is why the ledger can carry its own longer retention without
anyone having to remember to pass it.

A verb mirroring `prune-snapshots`: age plus size, **dry-run by default**. Not a background
sweeper thread. The sister project's unbounded sweeper registry is in the rejected list
below; beyond that, a daemon that deletes files in a CLI whose every other destructive verb
is operator-invoked (`sweep-removed`, `reset`, `prune-snapshots`) would be the only one that
acts on its own.

### 5. `LoaderRunLog` per component per batch — DECIDED IN PRINCIPLE, scope deferred

Every component opens one per batch — G93's remediation case generalized to `_lineage`,
`_docmeta`, `_deepdoc` and `scripts/external_vendor_scrape.py`.

**DEFERRAL RESOLVED AT RULING (2026-08-25): `drydocs_api` is OUT of scope, and it was a
category error rather than a scoping question.** The draft deferred "whether it counts as a
component", pending clause 6's design. The SME's observation settled it faster: it is the
web console's backend — `web/**` is the UI proper (72 `.tsx` files) and
`web/src/lib/graphApi.ts` launches this module via uvicorn — a thin read-only API over the
graph (ADR 0005, O5). It has no batches at all, so a `LoaderRunLog` there has nothing to
open one per. Clause 6 is its surface, which is what the deferral was pointing at anyway.

### 6. API request/audit line — DECIDED, WIDENED AT RULING, one detail deferred

Every route in `drydocs_api` that **executes Cypher OR writes** emits one audit line, actor
hashed the way `:AgentRun` already hashes it. `/raw-cypher` and `/specs/{id}/run` are the
routes that make this non-optional.

**Widened at ruling (2026-08-25), found while resolving clause 5.** The draft said
"Cypher-executing" only. `intake.py` (O46) writes — multipart upload to the data root. It
touches no graph and no tracked file (guarded by `test_no_endpoint_writes_a_tracked_file`),
so it is not a Cypher route and the drafted wording excluded it. That would have left the
one API surface that touches the filesystem as the one with no audit trail, which inverts
the point of the clause.

**Deferred:** whether the line carries the Cypher text itself. Trigger: the ask-search
question below, which owns it.

### 7. One data-zone declaration — DECIDED, mostly executed by G81 already

`config/data-zones.yaml` is the single declaration and `data_root.py`'s resolvers derive
from it. **That decision is unchanged and G109 upheld it. The clause's forward-looking list
was overtaken before the ruling and is corrected here** — G109 ran on 2026-08-24 because none
of its remaining work depended on a clause in this ADR.

What G109 actually did, which is not what this clause predicted: it did **not** give the six
zones `source-registry` rows. Two of them were already satisfied by G81 (the `dpl/` vs
`dpl-registry/` reconciliation, and resolvers deriving with a guard in both directions). For
the rest it took the acceptance's own "recorded reason a zone legitimately has none" branch,
because a write zone has no provenance, trust axis or acquisition mode — its registry row
would be a field set of nulls asserting a source that does not exist — and because
`data-zones.yaml`'s header already rules that a zone duplicating a registry row FAILS the
guard. What it fixed instead was the READ SURFACE: `drydocs landing-zones` reported only the
registry, so every zone in the other declaration was invisible to the one command that
answers "are my extracts still there". It now reports both (26 zones, was 15) with a
mode-aware `--check`. It also ruled the in-tree Confluence capture OUT of the tree and added
`DRYDOCS_LOGDIR` to `.env.example`.

**One thing this clause must not do, and G109 honoured it:** create a *third* place a zone is
declared. `config/data-zones.yaml` and `config/source-registry.yaml` already both describe
zones, for different reasons — the first says what mode a path has, the second says what
source lands there. The zone map stays the authority on mode; the two files are not merged.

## Rejected alternatives

The sister project's own recorded gotchas, captured by Idea-152 as an anti-checklist. Each
is a real defect that shipped somewhere; they are listed as rejected so they are not
re-proposed as conveniences.

| Rejected | Why |
|---|---|
| Level hardcoded, no env override | The defect we already have — `AppSettings.log_level` reads nothing |
| A Linux-absolute default path | Breaks on Windows, which is a primary dev platform here. `Path.home()` is the portable form and is what `run_log` already uses |
| Silent fallback to the local profile on a misconfigured box | The G81 lesson exactly: a silent fallback for a *data* path destroyed source data. A log path silently relocating is milder and the same shape |
| One process-start timestamp shared by every file | Every file in a run collides or overwrites; also makes local-time stamps ambiguous across a DST boundary |
| Unbounded sweeper registry keyed by per-incident logger names | Memory grows with incident count. Clause 4's operator-invoked verb has no registry at all |
| Moving the settings source of truth into git YAML | Would put one machine's paths in a committed file and port them to the other side — the failure ADR 0009's own port argument exists to prevent |

**Out of scope, named:** persisting executed Cypher server-side for ask-search. Idea-152
raised it; its owning surface is undecided, and clause 6's deferral points at it. It is a
separate idea, not a clause here.

## Consequences

**Good.** One place answers "where does output go and how loud is it". `log_retention_days`
gives the log directory the bound it has never had. The two log families and the ledger
share a directory, a retention verb and — with one recorded exception — a naming rule. The
data root and the log directory stop being different kinds of thing.

**Costs.** A fourth settings group is a fourth thing to know about. The `SPIDERP_*`
deprecation touches two families and needs its cycle actually ended rather than forgotten.
Clause 3 ships a documented inconsistency on purpose.

**Risk if not accepted.** Nothing breaks tomorrow — the substrate has been in this state for
months. What continues is that each new component invents its own logging, which is how
`drydocs_api` — including `/raw-cypher` — came to log nothing at all. The second-order cost
is subtler and worth naming precisely, because it is not a bug: `agents/graph_qa/agent.py`
drops telemetry failures deliberately and says why (*"telemetry never turns a good answer
into an error"*), which is the right call. But with no logging backbone behind it, the
correct choice to not fail also means a permanently broken ledger writes nothing and reports
nothing. Clause 2 is what turns that silence into a warning line without changing the
swallow.
