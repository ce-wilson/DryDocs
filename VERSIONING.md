# Versioning policy

DryDocs follows [Semantic Versioning 2.0.0](https://semver.org/): `MAJOR.MINOR.PATCH`.

## Single source of truth

- The version lives in **`pyproject.toml` `[tool.poetry] version`**.
- Git tags **mirror** it as annotated tags named `vMAJOR.MINOR.PATCH` (e.g. `v0.3.0`).
- The rendered board's plan phases may carry an optional `release:` field naming the
  version a phase targets (e.g. phase 8 → `v0.3.0`); the tag is cut when that phase slice ships.

## What the version describes (the "public surface")

Breaking-vs-additive is judged against the surfaces other tools/agents depend on:

1. **The `drydocs` CLI** — command names, arguments, and exit-code contract.
2. **The config schemas** — `drydocs.backlog.v2`, `source-registry`, `taxonomy-ontology-map`,
   `classification`, `source-mapping`, `doc-outline` (their shape + the validators that guard them).
3. **The graph model** — node labels and the **active** terms in
   `drydocs_core/ontology/relationship_vocabulary.yaml`. (`status: planned` terms are not yet public.)

Internal refactors, docs, and anything behind the HITL gate that is still `planned` are **not**
part of the public surface.

## Bump rules

While **`0.x` (pre-1.0)** — where DryDocs is today — SemVer makes no backward-compatibility
promise, so:

| Change | Bump |
|--------|------|
| A feature / epic slice, **or any breaking change** to the public surface | **MINOR** (`0.Y.0`) |
| Fixes, docs, hygiene, refactors with **no** surface change | **PATCH** (`0.Y.Z`) |

At **1.0.0** — cut when the graph model + CLI + config schemas are stable enough to promise
backward compatibility — the usual SemVer rules take over (breaking ⇒ MAJOR, additive ⇒ MINOR,
fix ⇒ PATCH).

## Changelog

Every release has a section in [`CHANGELOG.md`](CHANGELOG.md) following
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Each section cross-references the
backlog epic / item ids (`docs/restructure/backlog.yaml`) that the release covers.

## Cutting a release (the ritual)

1. Move `CHANGELOG.md`'s `[Unreleased]` content into a new `[X.Y.Z] - YYYY-MM-DD` section.
2. Bump `pyproject.toml` `version`.
3. Commit: `chore(release): vX.Y.Z`.
4. Annotated tag at that commit: `git tag -a vX.Y.Z -m "vX.Y.Z"`.
5. Push the branch **and** the tag: `git push origin main --follow-tags`.

## History

`0.1.0` was the poetry-init stub and was never tagged; `0.2.0` was skipped. **`v0.3.0` is the
first tag**, aligned with the "Planning & release infrastructure" phase — the point at which the
repo grew the board, the groom loop, and this policy.
