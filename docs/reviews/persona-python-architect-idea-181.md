# Persona review — Python architect (subject review: Idea-181, the header standard + freshness guard)

> **Run: 2026-08-27** against Idea-181 (docs/restructure/IDEAS.md, captured
> earlier the same day) and the live tree at `06ae1383`. Method: the idea's
> claims checked against the copier scaffolding ecosystem the TE work (ADR
> 0015) will build on — copier itself, pawamoy/copier-pdm,
> serious-scaffold/ss-python, fastapi/full-stack-fastapi-template — plus
> three repo facts verified locally (no `.pre-commit-config.yaml`; ruff
> `select = ["E","F","W","I","B","UP","N","RUF"]`, no `D` rules; CI checkout
> is default-shallow, no `fetch-depth` override). Read-only — zero backlog
> edits; findings route through IDEAS (Idea-181 gets a KEPT-UPDATED line
> pointing here). Prior runs:
> [`persona-python-architect-2026-08.md`](persona-python-architect-2026-08.md).

## Verdict up front

**Idea-181's diagnosis stands; two of its prescriptions need surgery before
grooming.** The lying-`updated:` finding is real and the four-key header is
the right unit for GOVERNED DATA files. But (F1) the idea's TE premise —
"copier updates rewrite files wholesale, so instances need in-file vintage" —
is wrong about copier, and (F3) the proposed guard (compare `updated:` to git
last-touch in pytest) is blind in this repo's own CI. Scope the header by
file class and move the guard to commit time, and the idea grooms cleanly.

## F1 — Instance vintage is a solved problem in the copier ecosystem, and it is solved centrally, not per-file

All three base templates ride copier's native mechanism: the generated
project carries ONE `.copier-answers.yml` recording the template `_commit`
(the vintage) plus the questionnaire answers, and `copier update` performs a
three-way merge — re-render the OLD vintage from the recorded answers, diff
against the new vintage, apply the diff to the working tree. Local edits
survive unless they conflict on the same lines; conflicts surface as
standard markers. "Template refreshes rewrite files wholesale" is therefore
false for copier — updates are merges keyed on recorded vintage.

Consequence for TE: template-class files need NO per-file `updated:` — the
answers file IS their vintage, and it is authoritative in a way a hand date
never is. The header standard's home is the OTHER file class: instance-owned
governed data (the DryDocs config YAMLs), which a template marks
skip-if-exists and never merges. ADR 0015 D4 already defines the file-class
seam (PORT-MANIFEST disposition vocabulary reused as template file classes)
— the header standard should be scoped BY FILE CLASS at grooming, not
repo-wide.

## F2 — Per-file hand dates in template-managed files are an ecosystem anti-pattern

None of the three templates puts a date or version in any generated file
header. The reason is mechanical: an in-file `updated:` in a template-class
file guarantees a merge conflict on every `copier update` of every instance
(each instance's date differs from the template's), converting the one
metadata line into permanent conflict noise. Vintage lives in exactly one
merge-excluded file. For TE this inverts into a rule: the guard should
FORBID `updated:` in template-class files while REQUIRING it in
governed-data files — same guard, two signs, keyed on the D4 file class.

## F3 — The lying-key guard belongs at commit time; the proposed pytest shape is blind in this repo's own CI

Verified locally: the CI workflow does not override `actions/checkout`
fetch depth, so CI clones are shallow — `git log -1 --format=%as -- <file>`
either fails or reports the shallow boundary, and a pytest comparing
`updated:` to git last-touch would pass vacuously or flake exactly where it
matters. Two further venue traps the idea already half-names: post-port,
company-side git dates are port-day (disjoint histories), and worktree
branches date differently than main. The ecosystem answer (ss-python's
posture generally) is pre-commit as the first gate: a hook over staged
governed YAMLs that bumps-or-fails `updated:` at the moment of the edit —
the date cannot lie because the commit that changes the file is the commit
that stamps it. This repo has NO `.pre-commit-config.yaml` today, so the
pragmatic sequence is: (1) land the header schema + presence guard in pytest
now (venue-safe, no git needed); (2) land the freshness check as a
pre-commit hook, producer-side, when pre-commit is introduced — and record
in the guard's docstring why the git-compare form is CI-hostile here.

## F4 — Python side: the D rules already exist; do not hand-roll

Ruff's pydocstyle family (`D100` undocumented-public-module, `D104` package
docstrings) mechanically closes the 31-missing-docstring gap; the repo's
ruff `select` currently carries no `D` rules. Enabling a narrow slice
(D100/D104, with the formatter-compatible convention setting) is a
one-line pyproject change plus a cleanup sweep — cheaper and stricter than
any bespoke guard. The richer convention (docstring cites its ADR/gate/item
and a date — already true in 214/446 files by culture) is not lintable by
ruff; if it is wanted as a rule, it is a 10-line pytest grep over module
docstrings, and it should be scoped to NEW files via a dated grandfather
set, or it lands as a 240-file sweep nobody asked for.

## F5 — One schema, one guard — not N bespoke tests

The four-key header is uniform across governed files; its validation should
be too. A single JSON Schema for the header block, driven either by one
pytest over the governed globs or by the `check-jsonschema` pre-commit hook,
beats per-file bespoke tests (`test_doc_registry`-style guards stay for the
SEMANTICS that genuinely differ per file — id grammars, field splits — but
presence/shape of the header is one rule). Industry precedent that per-file
header discipline sticks only when linted: the REUSE/SPDX ecosystem, where
`reuse lint` is the whole reason the headers survive.

## F6 — The `schema:` key is the load-bearing one for TE; `updated:` is not

Copier has version-aware `migrations` — scripts that run between template
vintages at `copier update`. When a governed file format evolves
(`drydocs.source-mapping.v1` → v2), the migration keys on the in-file
`schema:` value to find and upgrade instance files the template does not
own. That makes `schema:` the header key TE structurally depends on, while
`updated:` is operator-facing provenance. Grooming order inside the item
should reflect that: schema-key coverage (32 files missing) is the
TE-blocking half; `updated:` coverage is the audit-comfort half.

## Disposition

Route to IDEAS: Idea-181 body gets a KEPT-UPDATED line citing this review —
scope-by-file-class (F1/F2), guard-at-commit-time with the CI-shallow caveat
recorded (F3), ruff `D` slice instead of a bespoke docstring guard (F4), one
header schema (F5), schema-key-first sequencing (F6). No backlog item is
minted by this review (a persona run records; grooming decides — the
standing routine).

Sources: [copier update mechanism](https://copier.readthedocs.io/en/stable/updating/) ·
[copier-pdm](https://github.com/pawamoy/copier-pdm) ·
[ss-python](https://github.com/serious-scaffold/ss-python) ·
[full-stack-fastapi-template copier.yml](https://github.com/fastapi/full-stack-fastapi-template/blob/master/copier.yml)
