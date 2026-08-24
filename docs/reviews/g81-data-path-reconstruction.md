# G81 — data-path reconstruction and zone layout

> **Clause (a) is a deliverable, not a preamble:** *"RECONSTRUCT FIRST, do not
> guess. Establish what wrote over what, from the code, and record it ... a guard
> written against a guessed mechanism guards the wrong thing."* This file is that
> record, plus the layout it justifies. Written 2026-08-23 (laptop) from the code
> at `b9d3eb1`, before any fix was written.
>
> **What this is NOT:** a claim about which mechanism fired on the SME's machine
> on 2026-08-11. The two machines hold independent data roots and this session
> cannot see theirs. What follows is what the code **admits** — the write paths
> that could reach a source directory — ranked by how well each matches the
> incident's shape. That is the honest form of the answer, and it is enough to
> build the guard, because the guard forbids the *class* rather than the instance.

## 1. The incident, as reported

An internal folder holding **extracted CSV source data** was overwritten
(2026-08-11). Recovered from backup, so nothing was permanently lost — but the
class stays live and fires again the moment the backup is restored to the same
place. This is the most severe class the repo has produced: every other failure
that week was a wrong READ; this one destroyed a source.

## 2. The write-capable surface, walked

`drydocs_core/data_root.py` declares **12** path helpers. Eleven take
`create: bool = False` and call `mkdir(parents=True, exist_ok=True)`; the
twelfth, `source_dir(*parts, create=False)`, is fully general — it accepts
*arbitrary* path parts and can create anything under the root, **including the
root itself** when called with no parts.

Every helper resolves through `resolve_data_root()`:

```python
raw = os.environ.get("DRYDOCS_DATA_ROOT", "").strip()
return Path(raw) if raw else DEFAULT_DATA_ROOT      # ~/data/DryDocs
```

Three properties of that surface matter here, and all three are defects rather
than trade-offs:

1. **Nothing distinguishes a folder the system OWNS from a folder a human DROPS
   INTO.** Both are `source_dir(...)` calls returning a `Path`. The distinction
   existed only in the docstrings.
2. **The declaration lives in Python.** A reader cannot enumerate what the system
   touches without reading twelve functions and their call sites — which is
   precisely why an overlap stayed invisible until it destroyed something.
3. **The root has a silent default.** With `DRYDOCS_DATA_ROOT` unset or empty,
   every zone relocates to `~/data/DryDocs` — a plausible-looking place that may
   already hold someone's data. Same family as G78's fixture-directory default,
   one layer down.

## 3. The overlap, measured

Read zones are *already* declared in configuration — `config/source-registry.yaml`
`acquisition.drop_dir` (N12) resolved by `drydocs_core/landing_zones.py`. So the
overlap is computable today, and computing it is what turned this item from a
theory into three findings. Comparing resolved read zones against resolved helper
paths:

| # | Write path | Relation | Read zone |
|---|---|---|---|
| 1 | `controlm_xml_dir()` → `controlm-xml/` | **EQUALS** | `controlm:deftable-xml-export` (`controlm-xml/`) |
| 2 | `rua_extracted_dir()` → `rua/extracted/` | **inside** | `exec-hosts:rua-bundle` (`rua/`) |
| 3 | `rua_incoming_dir()` → `rua/incoming/` | **inside** | `exec-hosts:rua-bundle` (`rua/`) |
| 4 | `source_dir()` → the ROOT | **contains** | *every* `data_root`-based read zone |

Finding 1 is a `create=True`-capable helper aimed **exactly** at a folder a human
hand-drops export files into. Finding 4 is the ur-hole: a public, arbitrary-parts,
create-capable function whose no-argument form is the root itself.

**Findings 2 and 3 run in the direction the acceptance did not name.** Clause (c)
says *"no write-mode path may EQUAL OR CONTAIN a read-mode path"* — but the rua
pair is read-**contains**-write. Two of the four live findings are invisible to
the invariant as literally worded, so **the guard forbids containment in BOTH
directions**, plus equality. That widening is evidence-driven, recorded here
because it is a change to the acceptance's one-sentence rule.

### 3a. The overwrite primitive

`drydocs_lineage/extractors/rua_inventory.py::_unpack`:

```python
dest = Path(unpack_dir) if unpack_dir else rua_extracted_dir(name, create=True)
dest.mkdir(parents=True, exist_ok=True)
with tarfile.open(tarball) as tf:
    tf.extractall(dest, filter="data")
```

`extractall` **overwrites existing files at the destination** with no warning and
no diff. `filter="data"` blocks traversal and absolute paths *inside the tarball*
— it says nothing about whether `dest` is somewhere the system may write. Two
ways `dest` is chosen, and both are unguarded:

- **default** — `rua/extracted/<name>/`, where `<name>` is the tarball's own
  basename, i.e. **attacker-or-accident-controlled by filename**, inside the
  declared `rua/` read zone (finding 2);
- **`unpack_dir`** — an arbitrary caller-supplied directory, checked against
  nothing. A static guard over declared zones cannot see this one, which is why
  the fix needs a runtime refusal at the write site as well.

### 3b. A declaration that has been wrong the whole time

`dpl:pipeline-registry` and `dpl:dataset-registry` declare `drop_dir: dpl/`.
`dpl_registry_dir()` resolves `dpl-registry/`. **These have never agreed.** One of
them has been lying since N12 classified the rows: an operator who followed the
registry dropped exports into `dpl/`, where nothing reads them; an operator who
followed the code used `dpl-registry/`, which the registry does not describe.

Which side holds real files is machine-local and unknowable from here, so this
record does not guess. The correction takes **the code's path** (`dpl-registry/`),
because that is what the G25 flow actually reads, and the new
*declared-zone-equals-helper-resolution* guard is what makes the class impossible
to reintroduce.

## 4. Ranked candidate mechanisms for the incident

Matched against the incident's shape — *a folder of extracted CSV source data,
overwritten* — most to least consistent:

1. **A write into a folder that is also a drop zone.** Findings 1–3. The system
   rebuilt something it believed it owned, on top of a folder a human had been
   dropping source files into. Matches "extracted" and "overwritten" exactly;
   `rua/extracted/` is even *named* for an area a re-run legitimately rebuilds.
2. **The silent default root.** With `DRYDOCS_DATA_ROOT` unset in one shell and
   set in another, the same command targets two different trees; the unset case
   lands on `~/data/DryDocs`, which is exactly the kind of path a person also
   picks by hand. Explains a collision nobody configured.
3. **`unpack_dir` pointed at a source folder.** An operator naming their own
   extract directory as the unpack destination; `extractall` then overwrites file
   by file. Fully consistent, and today there is nothing to stop it.
4. **A general `source_dir(..., create=True)` call** creating or colliding at an
   arbitrary depth, up to and including the root.

All four are closed by the same two mechanisms — a declared mode per zone with an
enforced non-overlap invariant, and a mandatory root — which is why the fix does
not depend on identifying which one fired.

## 5. The layout this justifies

The SME direction asks that the layout be planned with the **architect persona**
and *with* the loader restructure (G79, landed 2026-08-23) rather than after it.
`docs/reviews/persona-python-architect-2026-08.md` is a **code-graph** review
(layering, fan-in, orphans) and rules on no filesystem question, so it neither
supports nor contradicts what follows; this section is the layout record that
direction asks for.

**The governing principle: a path's MODE is a property of the zone, declared once,
and the API cannot violate it.**

| Mode | Meaning | Capability |
|---|---|---|
| `read` | source data a human drops in; the system may **never** write it | reachable only through a helper that cannot create, clean or write |
| `write` | outputs the system owns and may rebuild | may create |
| `scratch` | disposable working space | may create and clean |

**Read zones are not re-declared.** They are already `source-registry.yaml`
`acquisition.drop_dir` rows; duplicating them into a second file would recreate
the drift this repo keeps killing. The new `config/data-zones.yaml` declares the
**system-owned** zones (`write`/`scratch`) plus the read zones that are *not*
dataset drops, and the invariant joins the two sets.

`data_root.py` keeps its helper API — every call site stays valid — but the
helpers become **readers of the declaration** rather than the place the paths are
defined. That is clause (b)'s "out of Python" satisfied without a repo-wide
rename.

### Corrections the layout requires

Both are **declaration corrections, not relocations** — the scope fence forbids
moving anyone's data, and neither moves a byte:

- `exec-hosts:rua-bundle`: `drop_dir: rua/` → `rua/incoming/`. The row was
  over-broad from the start; `data_root.py`'s own module docstring has always
  said the bundles land in `rua/incoming/` and the unpack area is `rua/extracted/`.
  Narrowing the row to what was always documented makes `rua/extracted/` a clean
  sibling instead of a write inside a read zone.
- `dpl:pipeline-registry` / `dpl:dataset-registry`: `drop_dir: dpl/` →
  `dpl-registry/`, per §3b.

## 6. What this record does not do

It does not relocate data, does not rule which mechanism fired on another
machine, and does not touch `DRYDOCS_LOGDIR`'s default. Clause (d) names the
**data** root: a relocated log is annoying, a relocated data root is destructive.
Logs are *declared* under (b) so they can be enumerated, but their resolution
semantics are unchanged.
