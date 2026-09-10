# The company assistant venue is not Claude Code — what that costs the capability layer

**Classification: Internal** — records which assistant tooling the company side runs and
what is reachable there. Never crosses the publish boundary; the public-side record is the
IDEAS entries of 2026-09-10 (Idea-311, Idea-312, Idea-313), which cite this file by path
only.

**Captured 2026-09-10, producer desktop (MSI), from a company-side session readout the SME
shared.** Everything in the first section is `[SME-REPORTED]` and unverifiable from this
machine — the producer cannot read the company tree. Everything in the second section is
`[VERIFIED-PRODUCER]`, measured here by command on 2026-09-10 at `6ae7a0e9`. The two are
kept apart because the conclusion depends on both and only one of them is checkable.

## 1. What the company session reported `[SME-REPORTED]`

The SME's own words, quoted from the readout: *"I don't have access to claude code, just the
model through vs code."*

The session then reported, after checking its own tree:

- **The venue is VS Code with GitHub Copilot, running Claude Opus 5.** Not the Claude Code
  CLI, not the desktop app, not the IDE extension.
- **`neo4j-skills` cannot be enabled there at all.** It is a Claude Code *plugin*
  (`~/.claude/plugins/cache/neo4j-skills-marketplace/…`); that venue has no `claude` CLI and
  no plugins directory. The session's phrasing: a *"dead route in this venue, which is why
  I've had no Neo4j lens all session."*
- **Filesystem skills DO load.** `oracle-db` was active in that session as a
  `.claude/skills/oracle-db/SKILL.md` file.
- **`.claude/settings.local.json` does not exist on that machine**, and the session reported
  that the venue does not read it regardless — so the `skillOverrides: "off"` that holds
  `oracle-db` off producer-side was never gating anything there.
- Incidental, not a capability fact: their main clone sat at a detached HEAD because a
  research worktree held `main` checked out. No work at risk. Recorded only so a later
  reader does not mistake it for a port symptom.

**One correction the session made to a tracked producer document, and it is right.**
`CLAUDE.md` §2 states that `oracle-db` is off and that the enablement call is each repo's
own. That sentence assumes a venue which reads `skillOverrides`. In theirs the claim is not
merely stale, it is inapplicable — there is no override layer to read.

## 1b. The venue split, as that machine measured it `[SME-REPORTED]`

Their session wrote its own findings to a durable memory file and the SME shared it. This is
more specific than section 1 and supersedes it where they differ. Verified on their machine
2026-09-10; unverifiable from here.

- **No Claude Code at all.** `claude` is not on PATH and `~/.claude/plugins/` does not exist.
  What does exist under `~/.claude/` is `{backups, plans, projects, sessions, skills}`.
- **THE FACT WITH THE MOST LEVERAGE, and it is new: that venue loads filesystem skills from
  TWO roots — `.claude/skills/**/SKILL.md` AND `.github/skills/**/SKILL.md`.** There is no
  plugin loader, so any `plugin:skill` route — every `neo4j-skills:*` in this repo — resolves
  to nothing and the session runs with no lens and no error. The second root matters for the
  Teams Edition: `.github/skills/` is a GitHub-native location, which a team on that stack
  would already have, and this repo ships nothing there.
- **`skillOverrides` is a Claude Code mechanism and that venue never reads it.**
  `.claude/settings.local.json` does not exist on that machine in any case. The consequence
  is the inverse of what `CLAUDE.md` §2 describes: **`oracle-db` was always ON there**, and
  had been for as long as the skill has existed, while §2 said it was off.
- Nothing was ever set to un-set: their `~/.claude/settings.json` is `{"env": {}}` — 15 bytes,
  no `enabledPlugins` — and `~/.claude.json` has no `enabledPlugins` either. There is no
  "reset" that would change any of the above.
- **The fix is APPLIED on their side, 2026-09-10**: they authored
  `.claude/skills/neo4j-db/SKILL.md` as the every-venue Neo4j route and repointed
  `CLAUDE.md` §2, `reference/platforms/README.md`, `reference/platforms/neo4j/README.md` and
  `reference/REGISTRY.yaml` at it. Their `reference/platforms/README.md` now reads, correctly:
  start with the repo-local `neo4j-db` skill because it is authoritative for THIS graph's
  topology and failure modes; *under Claude Code, add the matching `neo4j-skills:` plugin skill
  for version-current Neo4j; under VS Code the plugin does not load at all.* That is the right
  shape — repo-local first, plugin as an additive — and it is the shape the producer should
  copy rather than reinvent. All five paths are canonical-producer (§4).

### Two venue hazards worth carrying, neither of which is a DryDocs defect

**A worktree can hold `main` hostage, and that is a DIFFERENT cause of detached HEAD than the
one `CLAUDE.md` §0 documents.** Their main clone sat detached because a `research` worktree had
`main` checked out; `git checkout main` then fails with *"already used by worktree at …"*. The
fix is to give the worktree its own branch first (`git switch -c <own-branch>` inside it), then
`git checkout main` in the main checkout. **`git worktree list` is the diagnostic** — it prints
which path holds which branch. Producer-side this specific trap is already avoided rather than
handled: §0's J61 recovery recipe uses `git worktree add --detach`, and a detached worktree
holds no branch to steal. But the producer runs two NON-detached worktrees
(`review/module-sweep`, `feat/web-completeness`), so the trap is reachable here the moment one
of them is pointed at `main`. §0 documents the empty-string symptom of a detached worktree and
never names `git worktree list`; adding one line would close it.

**A multi-file replace matched FUZZILY.** They ran an `oldString` carrying a deliberate typo
(`neo4js-skills` for `neo4j-skills`) as a control, and it matched and replaced anyway — so the
control failed open and a placeholder landed in a real file. Whatever the venue's edit tool
does, it is not exact-match. The mitigation is the one this repo already practises for its own
scripted edits: assert the occurrence COUNT before replacing and re-read after
(`assert text.count(old) == 1`), which turns a fuzzy match into a loud failure instead of a
silent one.

## 2. What is true producer-side `[VERIFIED-PRODUCER]`

Measured at `6ae7a0e9`, 2026-09-10, by `dispositions.classify` against `PORT-MANIFEST.yaml`
and by `git ls-files` / `git check-ignore`:

| thing | where it lives | disposition | does it reach a consumer? |
|---|---|---|---|
| filesystem skills (`.claude/skills/**`, 47 of them) | tracked in the repo | canonical-producer | **yes**, wholesale |
| sub-agents (`.claude/agents/*.md`, 5 of them) | tracked in the repo | canonical-producer | **yes**, wholesale |
| `neo4j-skills` (29 skills, 10 kept) | a Claude Code plugin, outside the repo | none — not a repo path | **no**, never |
| `skillOverrides` enablement state | `.claude/settings.local.json` | classifies canonical-producer by the `.claude/**` glob, but the file is **untracked and gitignored** | **no**, never |

So the capability layer has **three different reachability classes and the tree distinguishes
none of them**. A consumer taking a port receives every skill and agent definition, receives
no plugin, and receives no enablement state — and nothing in the repo says which of the three
any given capability belongs to.

`CLAUDE.md` §2's routing table routes **every** Neo4j task to `neo4j-skills`, unconditionally.
That route is correct on this desktop and unreachable in the venue described above, and the
table carries no condition that would say so.

## 3. Why this is a Teams Edition question and not just a company one

The Teams Edition exists to be deployable by a team that is not this one. That team's
assistant venue is unknown at authoring time, so a capability layer whose reachability is
venue-dependent and undeclared will fail for them in exactly the way it failed here: silently,
by routing work to something that is not there, with no error and no lens.

**The seam already exists and is one key wide.** `config/dev-environment.yaml` is the
declared-never-inferred file: it already carries `edition:` (PLAN2), `side:` (PORT11) and a
`venues:` map (PLAN6) whose entries are exactly this shape —

```yaml
oracle-replica:
  available: false
  what: a live connection to the Control-M replica schema - the oracle-db skill acts on it
```

— a per-side `available:` flag with prose naming the skill it gates. That is already a
capability declaration linking a venue to a skill. What it has no code for is the assistant
venue itself: whether plugins load, whether sub-agents dispatch, whether an override file is
read. The file is canonical-company in `PORT-MANIFEST.yaml`, so each side declares its own
answer and a port never overwrites it, and its own header states the rule this case is a
worked example of: *declared, never inferred — a guess "guesses wrongly on exactly the tree
least able to notice."*

## 4. THE URGENT PART — that session then started BUILDING, on six paths it will lose

**Captured the same day, from a later readout `[SME-REPORTED]`.** The session took the
"both" option: author a repo-local `.claude/skills/neo4j-db/SKILL.md` AND correct the
routing documents. It is grounding the skill properly — it re-read
`drydocs_core/schema/provisioning/01_databases.cypher` and corrected its own stale memory
of the database topology, which producer-side is exactly right (`drydocs` for ground truth
and `ddschema` for the schema meta-graph are live; `ddlineage`, `ddcontext` and `ddall` are
retired at G1 / G32 / G102, and the file says so in comments). The work is good. That is
what makes this worth writing down rather than shrugging at.

**Every file it is writing is `canonical-producer`.** Measured here 2026-09-10 by
`dispositions.classify` against `PORT-MANIFEST.yaml`:

| path it is editing | disposition |
|---|---|
| `.claude/skills/neo4j-db/SKILL.md` (new) | canonical-producer |
| `CLAUDE.md` (§2 Neo4j row, oracle-db paragraph) | canonical-producer |
| `reference/REGISTRY.yaml` | canonical-producer |
| `reference/platforms/README.md` | canonical-producer |
| `reference/platforms/neo4j/README.md` | canonical-producer |
| `drydocs_core/schema/provisioning/01_databases.cypher` (read only, so far) | canonical-producer |

Six for six. When they apply `port-base-20260910`, the apply takes each of these wholesale
from the producer and the work is gone — not conflicted, not flagged, silently replaced.

**THIS IS J41 CHECK 3 REPEATING, and the preflight cannot catch it.** The opening sequence's
third check is *"every producer action triggered by company state is landed — anything the
company would otherwise have to do to a `canonical-producer` file"*, and its own motivating
incident is the 2026-08-09 plan that asked the company to edit `PORT-MANIFEST.yaml`, which
its apply phase takes wholesale, *"so the edit would have been reverted in the same session"*.
The difference this time, and it is the reason a guard will not help: **nobody asked them.**
The producer's routing table sent a task to something unreachable, the session correctly
diagnosed it and correctly fixed it, and the fix landed on the wrong side of a one-way port.
Check 3 is a producer-side check over producer-side intent; it has no way to see work the
consumer started on its own initiative.

**What the producer owes, and it is not a rebuke of that session.** The fix belongs
producer-side by disposition, so the producer builds `.claude/skills/neo4j-db/SKILL.md` and
the routing correction, and it crosses on the next roll. Their draft is the specification
for it — a back-flow, sanitized to mechanism, the same shape the adoption dossiers use.
Nothing about the port machinery needs changing; a canonical-producer path doing exactly
what its row says is the machinery working.

**One incidental, recorded so the producer does not chase a phantom.** That session hit
`TypeError: '<' not supported between instances of 'NoneType' and 'str'` running
`sorted(c.name for c in app.registered_commands)`. Not a producer defect: some Typer
commands carry `name=None`, and guardrail 1's own documented re-derive command already
handles it — `sorted(i.name or i.callback.__name__.replace('_','-') for i in ...)`, which
returns 55 verbs cleanly here. Their version was a simplification of the documented one.
Worth knowing only because the naive form is the one anybody writes from memory.

## 5. Their notes, checked claim-by-claim against THIS tree `[VERIFIED-PRODUCER]`

Their draft is going to be the SPEC for the producer-side build (§4), so every factual claim
in it was checked against this repo before any of it is copied. Verified 2026-09-10 at
`c8fd9b49`, 33 claims across six areas, by file-and-line. **Most of it holds. Five things do
not, and one of those would put a wrong fact into a canonical-producer skill.**

### What holds, and it is the load-bearing majority

The whole database-topology story is right: two live databases (`drydocs` ground truth,
`ddschema` meta-graph, pinned to exactly that set by `tests/unit/test_database_names.py`);
exemplars carrying real labels beside `:SchemaMeta`; the single `schemameta_name` constraint
living in `schema_graph.cypher` and deliberately not in `constraints.cypher`; `ddschema`
unaliased; `ddlineage` retired 2026-08-04 under ADR 0002 X1 having never been written;
`ddcontext` retired 2026-08-18 under G32/G102 and ADR 0011, with the trust boundary moving to
an `:Uncertain` label plus a mandatory trust property inside `drydocs`; `ddall` retired with
its second constituent. ADRs 0002 X1, 0005 and 0011 and gates G32 and G102 all exist and say
what they are said to say. The 5.x `FOR … REQUIRE` migration is complete, and `ontology.cypher`
/ `ontology_supplement.cypher` really do carry no constraints. Their correction of their own
stale memory was right.

### THE ONE THAT MATTERS: the Neo4j version, and how it was probably derived

**This tree pins `neo4j:2026.05.0-enterprise`** (`config/dev-environment.yaml:115`, repeated in
`compose.yaml` and `provision.ps1`, guarded by `tests/unit/test_dev_environment.py:201`). The
string `5.20.0-enterprise` appears NOWHERE in it, and no 5.20 server image ever did.

Their container being 5.20.0 is **not a defect** — `config/dev-environment.yaml` is
canonical-company precisely so each side declares its own container, ports and image, and
`provision.ps1` says in prose that this step is re-created per environment and never copied.
A divergent company container is expected. **The hazard is one level up:** a `neo4j-db` skill
whose Cypher-dialect rules, capability notes and failure modes are grounded in 5.20 would cross
as canonical-producer onto a tree running 2026.05.0. The skill is meant to be authoritative
about *this* graph, and on that point their draft would be authoritatively wrong.

Worse, the likely derivation is a conflation worth naming out loud: `pyproject.toml:18` reads
`neo4j = "^5.20"` — the **Python driver** floor, not a server tag — and the resolved
environment runs driver 5.28.4 against a 2026.05.0 SERVER. The two are decoupled here. And
`dev-environment.yaml:115` carries a one-way door in its own comment: the existing
`neo4j-testdata` store was written by 2026.05.0 and *cannot be downgraded*, so provisioning
this tree against a 5.x image would fail on store format rather than merely differ.

### Four more that would import stale or foreign facts

- **`constraints.cypher` holds 55 constraints, not 36.** Measured with the repo's own
  `declared_constraint_names()` parser rather than grep, and cross-checked commit by commit:
  the count ran 40 → 46 → … → 55 at `a30dd952` (2026-08-19) and has been 55 since. It was
  **never** 36 in reachable history, so this is not a stale-tree reading (J63) — it points at
  a different tree, most likely theirs.
- **Every supplement carries ZERO constraints, and the five files named do not exist here.**
  No `resource_pools`, `contacts`, `locations`, `platforms` or `seal_deployments` supplement
  is tracked. The real chain is declared as data in `drydocs_core/schema/supplements.py`
  (`SUPPLEMENTS`, with an explicitly empty `CHAIN_EXCLUSIONS` and a guard that fails on any
  unchained supplement-shaped file), and its members are MERGE-only term seeders. Their list
  reads like the company tree.
- **`smoke_drydocs_all.cypher` was DELETED 2026-08-19** at the G38 close (`50ed3589`). Their
  provisioning recipe still pipes it. Recreating it is not the fix: it was a FEDERATED read
  across the `ddall` composite and the fold to one content database left it nothing to
  federate. The equivalent check is now `SHOW DATABASES` showing `drydocs` and `ddschema`
  online.
- **`02_proxy_constraints.cypher` is a TOMBSTONE**, retired at G31 (2026-08-18); `provision.ps1`
  no longer runs it. Any "01, then 02, then smoke" sequence describes the pre-2026-08-18 tree.

### Two attribution corrections, small but they will be cited

`bootstrap_schema_graph` does **not create** `ddschema` — `01_databases.cypher:38` does; the
verb writes the meta-graph into an already-provisioned database. That distinction is literally
what item G51 fixed (the verb shipped naming a database nothing provisioned). And **G51 is a
backlog item plus a gate-log RECORD, not a signed gate** ("Direction, not a gate session"); the
two-graph decision and the verb are **C21**. Citing G51 as a gate ruling overstates it.

Separately, "do not drop `neo4j` or `system`" is **not a producer ruling** — nothing in the tree
says it. What the tree says is adjacent and different: `neo4j` is outside the topology, so
loading into it puts data where no query surface looks (`dev-environment.yaml:158-161`). That
is a LOAD warning, not a drop prohibition.

### The scope finding, which is the producer's own problem and not theirs

The routing tree is **already drifted from `CLAUDE.md`'s own keep-10 in five places**, before
any venue question: `reference/platforms/neo4j/README.md:22` still routes to the `aura-*`
skills deleted 2026-07-06; `:23` and `reference/research/README.md:17` route context-graph work
to an `agent-memory` skill outside the keep set; `reference/platforms/README.md:8` and
`reference/REGISTRY.yaml:66` route Snowflake to a skill that is outside the keep set AND
explicitly `"off"`; and `REGISTRY.yaml:23-24` lists twelve plugin skills against `CLAUDE.md`'s
ten, still naming `aura-*`. So the producer's routing fix is landing on existing drift, not on
a clean baseline, and it should sweep all of it rather than repoint one row.

### And the boundary sweep came back clean

Swept the tracked tree at `c8fd9b49` for three classes: a private corporate container-registry
hostname — **absent everywhere**, inside `internal/` and out; a hard-coded Neo4j password or
auth pair — **absent everywhere**; a corporate internal domain suffix — present, and **confined
entirely to `internal/`** (16 files), which is the tier that is allowed to hold it. Every
corporate-looking host outside `internal/` is a public-web hostname on an External-classified
source, and every other host-like string is an RFC placeholder or loopback. `.env` is
gitignored and no `.env`-shaped file carrying values is tracked. **Nothing to remediate here.**

## 6. The file their rewrite sits on top of has FOUR defects in 35 lines, and one is ours

Their rewritten `reference/platforms/neo4j/README.md` was shared, so it could be diffed against
the producer's. **The rewrite is a real improvement**: it adds a venue routing table at the top
that says plainly which route loads where, and it states the complement correctly — the
repo-local skill carries what is true of *this* graph, the plugin carries version-current
vendor Neo4j, "they are complements, not substitutes." That framing is the thing to keep.

**But it is additive, so it inherits everything already wrong underneath it.** The producer's
own copy of that file is 35 lines and carries four defects, measured 2026-09-10 at `84ecb090`:

| line | defect | since |
|---|---|---|
| 22 | routes "Aura provisioning / agents / analytics" to `neo4j-skills:neo4j-aura-*-skill` | those directories were deleted **2026-07-06** |
| 23 | routes agent-memory / context-graph work to `neo4j-skills:neo4j-agent-memory-skill` | not in the keep-10 that `CLAUDE.md:253-254` declares |
| 29 | cites a local mirror at `../../../llm-graph-builder` | **the path does not exist**, is untracked and is not gitignored |
| 32 | "Server: Neo4j 5.x with APOC … Target 2025.x/2026.x" | the pin is `neo4j:2026.05.0-enterprise` |

Their rewrite keeps lines 22, 23 and 32 verbatim. Only the routing table above them is new.

**Line 29 is worth its own note, because it explains why nobody caught it.** The preflight's
cited-paths check only resolves backticked paths carrying a known EXTENSION
(`_CITED_EXTENSIONS`); `llm-graph-builder` is a bare directory name, so it is invisible to the
one guard that would have found it. A dead directory citation is exactly as misleading to a
reader as a dead file citation and no instrument here sees it.

### THE CORRECTION I OWE, and it moves the blame

§5 attributed their `5.20.0-enterprise` grounding to a conflation of `pyproject.toml`'s
`neo4j = "^5.20"` — the Python driver floor — with the server image tag. That conflation is
real and the two ARE decoupled here (driver 5.28.4 against a 2026.05.0 server). **But there is
a second and more likely source, and it is ours**: line 32 of the producer's own Neo4j
reference document, the canonical-producer file whose entire job is to be authoritative about
the platform, opens with "Server: Neo4j 5.x". A consumer reading our reference doc and
concluding the server is 5.x has read it correctly. The doc is wrong.

So the sentence to carry forward is not "they misread pyproject". It is: **our platform
reference names the wrong server generation, and the consumer inherited it.** That is the same
class as the dead Neo4j route — a canonical-producer document that bills the consumer — and it
is the second instance in the same file.

### One thing that is NOT a collision, stated because §4 implied a wider one

Their `.claude/skills/oracle-db/SKILL.md` was also shared. Its frontmatter, description, domain
blurb, directory tree and category-routing table match the producer's **exactly** in the
visible portion, and the producer's own copy is the same 19-subdirectory tree
(`admin/ agent/ appdev/ … sqlcl/`, tracked). That is ported producer content sitting where it
should, not a divergence — so nothing is at risk there, and a port replacing it replaces it
with itself. §4's list of six at-risk paths stands as written; this is not a seventh.

## 7. What is NOT claimed here

- That sub-agent dispatch is unavailable in that venue. Nobody measured it; the session did
  not test it and the producer cannot. `.claude/agents/*.md` cross wholesale either way, so
  whether five agent definitions arrive live or inert is an **open question**, not a finding.
- That the company should change venue. Which assistant a team runs is theirs to decide, and
  the point of declaring capability is to stop that decision from mattering silently.
- Any figure about the company tree. Section 1 is what one session reported about itself.
