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

## 5. What is NOT claimed here

- That sub-agent dispatch is unavailable in that venue. Nobody measured it; the session did
  not test it and the producer cannot. `.claude/agents/*.md` cross wholesale either way, so
  whether five agent definitions arrive live or inert is an **open question**, not a finding.
- That the company should change venue. Which assistant a team runs is theirs to decide, and
  the point of declaring capability is to stop that decision from mattering silently.
- Any figure about the company tree. Section 1 is what one session reported about itself.
