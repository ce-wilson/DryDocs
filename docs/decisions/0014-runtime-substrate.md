# ADR 0014 — Runtime substrate: logs, settings and data zones are one per-machine settings group

```yaml
status: PROPOSED          # NEVER Accepted by the drafting session — acceptance is the user's,
                          # and is recorded in docs/decisions/README.md only after they rule
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
executed_by: G105 (1-3), G106 (4), G107 (5), G108 (6), G109 (7)
```

> **Nothing in this record changes code.** It drafts the decision; G105–G109 implement it,
> and each of them `depends_on` this ADR so that nothing implements an unratified ruling.

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

### 1. One `RuntimeSettings` group — DECIDED

A fourth pydantic-settings group in `drydocs_core/config.py`, `DRYDOCS_` prefix, matching
the three that exist:

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

### 3. One naming rule — DECIDED, with the ledger exception WRITTEN DOWN rather than moved

`<kind>.<name>.<YYYYmmdd-HHMMSS>.{log|jsonl}` for the shared directory.

`agents/common/llm_ledger.py`'s `qa.graph_qa.<YYYYmmdd>.jsonl` **keeps its per-DAY stamp**,
and the exception is recorded here instead of being normalized away. It is an append-only
ledger, not a run artifact: per-run files would shard one queryable history into hundreds of
fragments, and the whole value of a ledger is that it is one file you can read end to end.
The rule it must obey is the one that matters — it lives in `log_dir` and is swept by the
same retention verb.

*This is the clause most likely to be over-ruled, and the counter-argument is that one
exception in a naming rule is how naming rules die. Stated so the user can take the other
side knowingly.*

### 4. `drydocs prune-logs` — DECIDED

A verb mirroring `prune-snapshots`: age plus size, **dry-run by default**. Not a background
sweeper thread. The sister project's unbounded sweeper registry is in the rejected list
below; beyond that, a daemon that deletes files in a CLI whose every other destructive verb
is operator-invoked (`sweep-removed`, `reset`, `prune-snapshots`) would be the only one that
acts on its own.

### 5. `LoaderRunLog` per component per batch — DECIDED IN PRINCIPLE, scope deferred

Every component opens one per batch — G93's remediation case generalized to `_lineage`,
`_docmeta`, `_deepdoc` and `scripts/external_vendor_scrape.py`.

**Deferred:** whether `drydocs_api` counts as a component for this clause, since it serves
requests rather than running batches. Trigger: clause 6's audit line is designed — if that
line already carries what a run log would, the API needs no second surface.

### 6. API request/audit line — DECIDED, one detail deferred

Every Cypher-executing route in `drydocs_api` emits one audit line, actor hashed the way
`:AgentRun` already hashes it. `/raw-cypher` and `/specs/{id}/run` are the routes that make
this non-optional.

**Deferred:** whether the line carries the Cypher text itself. Trigger: the ask-search
question below, which owns it.

### 7. One data-zone declaration — DECIDED, mostly executed by G81 already

`config/data-zones.yaml` is the single declaration and `data_root.py`'s resolvers derive
from it. G81 built the declaration and the guards; what remains is G109's list — the six
zones needing a `source-registry` row or a recorded reason, the `dpl/` vs `dpl-registry/`
reconciliation, resolvers derived rather than restated, `.env.example` gaining
`DRYDOCS_LOGDIR` (the data root is already there), and the in-tree Confluence capture ruled
one way against `landing_zones.py`'s tracked-only rule.

**One thing this clause must not do:** create a *third* place a zone is declared.
`config/data-zones.yaml` and `config/source-registry.yaml` already both describe zones, for
different reasons — the first says what mode a path has, the second says what source lands
there. G109 gives the six zones registry rows and keeps the zone map the authority on mode;
it does not merge the two files.

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
