# Adoption dossier 4 — the port machinery corrections that postdate your base but govern the slices you have not applied yet

**Hand-carried; NOT port payload. Pin the producer tree at `6a8bd23f`.**
Documents intent; asks for nothing back.

## Why this is hand-carried rather than ported

**A port range is bounded by two tags.** Yours is
`port-base-20260826..port-base-20260901` — 296 commits, fixed at both ends. It is
not "everything on producer `main`", and it does not move while you apply it.
That is the property that makes an apply reproducible, and nothing here asks you
to give it up.

The consequence: **everything below was pushed AFTER the `port-base-20260901`
tag** (17 commits at the time of writing) and is therefore outside your range by
construction. It rides the *next* base.

Which is exactly the problem. Every correction here governs a slice you have not
applied yet — D, E, F and G. Waiting for the next port delivers them **after** the
slices they protect. So they are hand-carried, on the precedent of dossiers 1–3,
and the port itself stays tag-bounded and unchanged.

**Nothing here is required.** Take all of it, some of it, or none, and your range
still applies exactly as it did before.

---

## 1. The rename detector — run before ANY clean-add slice

**The defect, twice in your apply:** a producer path absent your side classifies
as a clean-add. That is true of the PATH and blind to the CONTENT, so a renamed
file arrives as new. `41-local-seal.yaml` → `41-local-business-application.yaml`
cost you 16 duplicated ids, 62 failures and a revert. The crosswalk gate prompt
would have imported a sign-off you deliberately withhold.

**Three files, all `default_ok`, the detector stdlib-only** (`re`, `dataclasses`,
`pathlib`; only the script imports `drydocs_core.repo_paths`, which you have):

```
git fetch cewilson
git checkout 6a8bd23f -- drydocs/port_rename_detect.py \
                         scripts/port_rename_check.py \
                         tests/unit/test_port_rename_detect.py
poetry run pytest tests/unit/test_port_rename_detect.py -q      # expect 11 passed
```

**Then, before each remaining slice:**

```
poetry run python scripts/port_rename_check.py \
    --producer-ref port-base-20260901 --path-prefix <slice prefix>
```

Exit 0 = no proposed clean-add resembles a file you already hold. Exit 1 = it
names the pairs. `--any-directory` widens the compare; both known traps were
in-directory, and the wide sweep is quadratic.

**It reports, it does not decide.** Every pair is adopt / decline / false
positive. Your two failures came from acting without looking, and this restores
the looking step and nothing else.

**Proven on your two traps, on real commits** — across `496aa268~1..496aa268`,
the commit that actually applied the gate rename, it reports both real pairs at
id-set similarity 1.00.

**One warning that is yours as much as ours:** its first run raised
`UnicodeDecodeError: 'charmap' codec can't decode byte 0x9d`. `subprocess(...,
text=True)` decodes with the platform locale — cp1252 on Windows — which is the
same trap that mojibaked your em-dashes and fabricated 18 of 25 "differences".
Fixed here with an explicit `encoding="utf-8"`. **Apply it to any comparison
tooling you keep:** a similarity check that mis-decodes one side compares a
corrupted document against a clean one and reports the corruption as a
difference.

---

## 2. Two manifest rows that change what slice E should take

**Read this before E, not after.** `MODULE_MAP.md` is in E's decision set, and the
manifest you hold has it wrong.

- **`MODULE_MAP.md` was `canonical-producer`; it is now `per-entry`.** Its guard,
  `tests/unit/test_module_boundary.py`, was already `per-entry` — and that split
  is what dropped your `drydocs.scrapers.*`, `drydocs.docmeta.*` and
  `drydocs.seal_projection` rows, after which the default-deny check failed on
  every one of them. **Module rows union.** Producer mechanism crosses whole: the
  placement test, the core-imports-nothing invariant, the S7 rule, and the
  `CORE_PREFIXES` / `COMPONENT_GROUP` vocabulary.
- **`config/source-registry.yaml` had no row at all** and fell through to
  `config/**` canonical-producer — which is what drove your `test_source_registry`
  from 1 failure to 7. It is now `per-entry`. Your field split already reached the
  right answer by hand; this is the rule catching up to it.

**And the skill stopped asserting dispositions entirely.**
`.claude/skills/reconcile-port/SKILL.md` carried four disposition claims and two
had drifted into contradicting the manifest — including a `Canonical-here` bullet
naming `relationship_vocabulary.yaml` for a wholesale `git checkout`, which would
have flattened your own ontology entries and your 19-class TOM register. It never
fired only because the path had already been sharded out of existence. That table
is now headed *"HOW to merge — never WHETHER to take"*, and
**`PORT-MANIFEST.yaml` is the only source of disposition.** On any disagreement,
the manifest wins.

---

## 3. Every per-entry merge rule is now TOTAL

`config/source-bindings.yaml` was not carried from `1bd29b42` because its rule
**enumerated** producer-owned and company-owned fields and `twin` was in neither
list. That is the rule failing, not the session — a per-entry merge with no
instruction for a field has no defensible move.

**And taking it would also have been wrong.** `twin` holds a machine-local path,
so by the row's own principle — *the WHAT crosses and the WHERE never does* — the
**key** is producer mechanism and the **value** is yours.

Four rules now carry a literal `UNNAMED FIELDS:` clause declaring who owns
everything not named, so a field added tomorrow has an answer the day it lands.
**The one to know before you merge:** on `source-bindings.yaml`, when a new field
is genuinely ambiguous, **keep yours.** An unfamiliar producer value can point you
at something that does not exist on your machine; keeping your own only leaves you
a version behind — and the second failure is visible where the first is silent.

**What is owed back, by file, as FIELDS to adopt rather than values to copy:**

| File | Adopt | Keep yours |
|---|---|---|
| `config/source-bindings.yaml` | the `twin:` and `reason:` keys | both values |
| `config/doc-source-registry.yaml` | `classification`, `describes_product`, `replaces`, `source_url` | `landing_zone` |
| `config/audit-fields.yaml` | `notes`, `objects` | `status`, `decided_by` |

---

## 4. Two rulings you were blocked on, both already in the manifest

- **`lob-product-team.yaml` — keep your hierarchy.** *"the company's REAL rows are
  estate data and stay; the producer's rows are the synthetic publishable sample
  and never overwrite them."* The producer has zero `catalogSubLOB` occurrences
  because its file **is** the sample — it never had that tier to drop.
- **`audit-fields.yaml` — union the extension in.** *"UNION: producer additions +
  company-only confirmed-source entries (9 of them at PORT-REPORT-5417ef10)."*
  Your header marks `COMPANY EXTENSION (9/9)`; the count matches exactly.

And one you raised that needs no decision: **`15-node-classifications-company.yaml`
keeps its own file.** The rule is id-keyed and fragments merge in sorted-filename
order, so a company-only fragment at `15-` merges between `10-` and `20-` with no
conflict.

---

## 5. One correction to your vocabulary-migration measurement

Your count of **45 renames** is right, and **175 producer ids vs your 111** is
exact. But **44 carry `deprecated_at: 2026-08-21`, not 45.** The odd one is:

```
seal_requires_scheduler → reg_uses_software     deprecated_at: 2026-07-21
```

A month earlier, at a different gate (C12 platforms-taxonomy, signed 2026-07-21),
and it needs **no data migration at all** — its target `:SchedulerKind` is a
retired label, seeds retired at C12, constraint removed at C13 on 2026-07-23. The
entry's own note reads *"pre-C13 graphs are wiped and rebuilt from bootstrap, so
nothing creates or holds the label."*

**44 renames migrate; 1 retires.** Folding it into the G101 family would send you
looking for nodes that cannot exist.

Also worth checking before you price item A: **`migrate_vocab_ids_g101.cypher` is
probably already in your tree.** It landed at `8dc9a804` on 2026-08-21, which is an
ancestor of `port-base-20260826` — the base you already applied. It is not in the
current range, which is what you observed; that is not the same as unsourced.
