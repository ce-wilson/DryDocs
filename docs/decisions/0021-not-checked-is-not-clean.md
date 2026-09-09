# ADR 0021 — A result names what it did not check: one three-outcome type, and a probe that returns a bare boolean is refused

```yaml
status: ACCEPTED        # user ruling, in-chat, 2026-09-09 at sitting 1 (config/gate-log.md, the ACCEPTED entry); drafted PROPOSED the same day by the Lane A close
date: 2026-09-09
authored_by: Lane A close, desktop (Fable 5.1), from the module sweep's cycle-1 conclusion
deciders: [chad.wilson] # accepted 2026-09-09 as drafted; action items live from that date
layer: cross-cutting    # a return-type convention every component's probes follow; the type lives in core
relates_to:
  - docs/reviews/modules/seams-2026-09-08.md          # slot 10: the cycle conclusion - seven recurrences, six independent correct answers, zero conventions
  - docs/reviews/premise-drift-2026-09-09.md          # organ (b): contract non-propagation is closed by a shared return type, not a convention document
  - docs/reviews/modules/web-2026-09-09.md            # the propagation event caught with dates: a consumer dropped the envelope the day after it shipped
  - drydocs_remediation/equivalence.py                # precedent 1: three-valued proven / diverged / not proven - "no evidence is never evidence"
  - drydocs_lineage/archival.py                       # precedent 2: "no axis proves absence"
  - drydocs_api/schemas.py                            # precedent 3: `truncated` declared on the envelope and READ by the console, never inferred
  - drydocs/port/port_preflight.py                    # precedent 4: CheckResult("suite green", False, "SKIPPED - not a certification")
  - drydocs/plan/plan_board.py                        # precedent 5: "no items" rather than 0 / 0
  - drydocs_deepdoc/investigate.py                    # precedent 6: the scaffold names which of its own bodies raise
  - drydocs/docs_coverage.py                          # the first adopter: None-for-not-probed, expressed through the type
  - CLAUDE.md                                         # J78: a CI check has three outcomes, and UNVERIFIED is neither green nor red
backlog: [DOC4]         # the sweep item this closes the loop on; the instrument item is minted in the Lane A mint pass
```

## Context

### The finding, measured

The module review sweep (DOC4, ten slots, two lenses each, all eleven reports on `main` at
`f06a5f00`) closed its first cycle with one conclusion, stated by slot 10
(`docs/reviews/modules/seams-2026-09-08.md`): across nine module reports it found **one defect
shape seven times** - a result that cannot distinguish *checked and clean* from *not checked*.

| slot | the instance |
|---|---|
| web | a console that truncated silently, and a "full" export that inherited the cap |
| load | a `:JobRun` that records no scope, so a sampled load looks like a full one |
| lineage | a counted `dns-resolved` tier with no writer, so its metric is permanently zero |
| remediation | a findings list with no rule denominator (17 of 45 rules implemented, none of it stated) |
| review-agents | four of six acceptance suites that cannot fail against an empty graph |
| port-docgen-docmeta | a preflight that certifies a base it could not read (`_git` discards the exit code, an unresolvable base yields an empty range, and every range check passes on emptiness) |
| seams | a boundary rule that sees only the import construct people happen to use |

And it found the **correct answer implemented independently six times**, in six modules, with no
written convention anywhere:

1. `drydocs_remediation/equivalence.py` - three-valued **proven / diverged / not proven**, and
   the sentence that carries this record: *no evidence is never evidence*.
2. `drydocs_lineage/archival.py` - *no axis proves absence*; every "absent" is bounded by the
   coverage limit of the observation that failed to see it.
3. `drydocs_api/schemas.py` - `truncated` and `limit` DECLARED on the result envelope, and the
   console renders from the contract, never from `rows.length === limit`.
4. `drydocs/port/port_preflight.py` - `CheckResult("suite green", False, "SKIPPED - not a
   certification")`: a skipped check is explicitly not a pass.
5. `drydocs/plan/plan_board.py` - "no items" rather than `0 / 0`.
6. `drydocs_deepdoc/investigate.py` - the scaffold names which of its own bodies raise.

Six correct implementations. Zero written conventions. Seven recurrences.

### Why a convention document is not the fix

The second pass over `web` (`docs/reviews/modules/web-2026-09-09.md`) caught the propagation
event with dates: the completeness contract entered `drydocs_api/schemas.py` on 2026-09-05, and a
consumer built on 2026-09-06 discarded the envelope it rides on. The review's own diagnosis: *a
developer building a new spec consumer the day after `truncated` shipped had no way to learn it
existed - it is not in a convention document, no lint rule mentions it, no shared hook surfaces
it. Knowing is accidental. A convention document would not have reached the author either; a
shared return type would have.* The premise-drift review (`docs/reviews/premise-drift-2026-09-09.md`)
names the class: **contract non-propagation**, closed by *a shared return type that makes the
wrong version unwritable*, and by nothing weaker.

This repo already states the rule for one instrument. CLAUDE.md's J78 says a CI check has
**three outcomes**, green, red, and UNVERIFIED, and that a cancelled run is neither green nor red.
This record generalizes J78 from the CI check to every probe the code runs.

### What this is not

This is not a repo that gets completeness wrong. Slot 8 framed it and slot 10 confirmed it from
another layer: it is a repo where **the right answer does not propagate**. A repo that gets
something wrong needs education; a repo where a solved problem does not travel needs a written
convention AND an instrument that makes the wrong version fail. Six correct implementations
already prove nobody needs convincing.

## Decision

Five clauses, D1 to D5.

### D1 - One type, in core

`drydocs_core` gains one small module (working name drydocs_core/check_outcome.py) exporting one
frozen dataclass, working name CheckOutcome, with exactly three states:

| state | meaning | carries |
|---|---|---|
| `CHECKED_CLEAN` | the probe ran over its whole subject and found nothing | the subject's size where one exists (rows scanned, files read), so "clean over 0" is visible |
| `FINDINGS` | the probe ran and found something | the findings themselves, and the size |
| `NOT_CHECKED` | the probe did not run, or ran over less than its subject | a written reason of at least forty characters, never empty - the SOURCELESS_LOADERS idiom, applied to a result |

Two properties are part of the type and not of its callers. **A CheckOutcome never coerces to a
boolean**: `bool(outcome)` raises, so `if outcome:` and `if not outcome:` cannot be written. The
only way to ask "is it clean" is a named accessor that is true for `CHECKED_CLEAN` and false for
BOTH other states. **Every state renders itself**: one method returns the operator-facing line -
"checked, clean (1,204 rows)", "3 findings", "NOT CHECKED - <reason>" - so a render cannot show a
`NOT_CHECKED` result as `0`, as an empty list, or as PASS. Core imports nothing from any
component (`drydocs_core/component_map.py`), so the type lives in core and every component may
import it.

An optional `venue` field carries the J18 stamp where a probe's answer depends on the machine it
ran on. The preflight's `venue_line()` is the precedent.

### D2 - The rule: a probe returns the type, never a bare boolean or a silent empty

A **probe** is any function whose answer depends on something it had to go and look at: a
subprocess, a graph query, a filesystem or tree scan, a network call. A probe returns a
CheckOutcome. It never returns `True`/`False`, never returns an empty list where "nothing looked"
is possible, and never returns `None` as its way of saying "not probed". Three consequences,
stated because each is a recurrence in the table above:

- A subprocess helper that discards the exit code is a probe that cannot say `NOT_CHECKED`; the
  preflight's `_git` is the instance and the first adopter.
- A counter with no writer (`matched_dns_resolved`) is a probe reporting `CHECKED_CLEAN` over a
  subject nobody scanned; the honest interim value is `NOT_CHECKED` with the reason.
- A denominator that is not stated (17 of 45 rules) is a `FINDINGS` result that hides its own
  size; the size travels with the findings.

`None`-for-not-probed, which `drydocs/docs_coverage.py` does correctly today, is the seventh
spelling of the same fact. It is correct there and it is still a spelling: `None` is falsy, and
the next reader writes `if not coverage:`. That report is the second adopter.

### D3 - The instrument: a declared probe registry and a guard that reads code

The rule without an instrument is prose a guard cannot read (J66). The instrument is the
component-map shape applied to probes:

1. A **declared registry** in core - a tuple of dotted names, one per probe, added by the item
   that makes a function a probe. Declared, not inferred: a name-based heuristic (`check_*`,
   `verify_*`) would be exactly the guard-reads-prose class slot 10 measured, and it would miss
   `_git`.
2. A **guard** in the unit suite that, for every registered name, imports the object and reads
   its return annotation through `tests/source_scan.py` - the annotation must be the type, and a
   probe with no annotation fails with the reason. The same guard asserts the type's two
   properties (no boolean coercion; every state renders) with a positive and a negative case.
3. The registry is **shrink-only in one direction**: a registered probe that no longer exists
   fails the guard, so the list cannot rot into a claim.

What the guard does NOT do, stated so it is not over-read: it does not find unregistered probes.
A probe nobody declared is invisible to it, exactly as an undeclared component import is invisible
to the boundary test until declared. Registration is the act the rule asks for, and the sweep's
next cycle is where undeclared probes are found.

### D4 - Adoption is scoped, and the six precedents keep the name only

First adopters, in order: the port preflight (its `CheckResult` gains the third state and
`_git` fails closed - the defect fix ships regardless of this record, and adopts the type once
the record is ACCEPTED), then `drydocs/docs_coverage.py` (None-for-not-probed expressed through
the type, behavior unchanged). After that, the sweep's other recurrences adopt it as their own
items are built: `graph_verify`'s per-suite precondition reports `NOT_CHECKED` on an empty graph;
`detect_all` returns its denominator; the `dns-resolved` tier reports its interim zero honestly;
the `:JobRun` scope is a `FINDINGS` payload.

The six precedent implementations **adopt the name only**: a one-line comment citing this record
at each site. They are correct, and rewriting a correct site to a new spelling is churn for no
defect. A migration is its own item if one is ever wanted.

### D5 - Renders follow the type

Every surface that shows a probe's answer - the board, the preflight report, the coverage report,
the console's completeness badge - shows `NOT_CHECKED` as *not checked* with its reason, in the
same place a finding would appear, never in the place a clean result would. This is the
`TruncationBadge` rule generalized: the state is READ off the type, never inferred from the shape
of the payload.

## Options considered

### A - Write the convention down; no code (rejected)

The cheapest option and the one the web second pass already refuted with dates: the contract was
documented in the schema's own comment and a consumer dropped it the next day. A document does not
reach the author who needs it at the moment they need it.

### B - A lint rule over boolean-returning functions by name (rejected)

`check_*` and `verify_*` are conventions the tree does not follow (`_git`, `evaluate`,
`detect_all`), so a name-based rule is a heuristic that reads prose (J66) and misses the instances
that produced this record. A narrow guard over a declared list survives - that is D3.

### C - The shared type, a declared registry, and a guard (chosen)

One place the fact is stated; the wrong version fails to type-check or fails the guard rather than
failing in a review two months later. The cost is one core module, one registry tuple, and a
registration line per probe.

### D - `Optional[bool]` or `None` for not-checked (rejected)

Correct at one site today and still a spelling: `None` is falsy, carries no reason, and cannot
render itself. The whole problem is that seven spellings exist; an eighth is not the fix.

## Trade-off analysis

The trade is a small new dependency in every component (one core type) against the measured cost
of its absence: seven recurrences in one cycle, one of them at the publish boundary. The registry
is a declared-not-inferred list of the kind this repo already runs (`component_map.py`, the
domain registry, the edition registry), so the discipline is familiar and the guard shape exists.
The risk is over-adoption - a sweep that rewrites the six correct sites to the new type for
tidiness - and D4 refuses it by scope.

## Consequences

**Positive.** The seventh recurrence fails in CI (J78's three outcomes, at every probe) instead of
in a review. A `NOT CHECKED` verdict is representable everywhere a `PASS` is, so a preflight, a
coverage report or a console badge cannot be green on emptiness. Six implementations that already
agree now cite one record.

**Negative.** A registration step per probe, and a guard that finds nothing until someone
registers. A reader who meets the type for the first time pays one page of reading; this record
is that page.

**Revisit trigger.** A probe that needs a fourth state. The expected shape is that "partial" is a
`FINDINGS` or `NOT_CHECKED` result carrying a ratio in its payload, not a fourth state; a real
fourth state is the trigger to amend D1 rather than to add a parallel type.

## Action items (after acceptance)

1. [x] The instrument item (minted in the Lane A mint pass): the type, the registry, the guard,
       positive and negative cases; `MODULE_MAP.md` re-rendered. - CORE10, 2026-09-09:
       `drydocs_core/check_outcome.py`, `PROBES`, `tests/unit/test_check_outcome.py`.
2. [x] The preflight adopts the type (its `_git`/`CheckResult` fix ships first, independently).
       - CORE10: `base_resolves` returns it and is registered; `CheckResult` reads its verdict off it.
3. [x] `drydocs/docs_coverage.py` adopts the type; its report renders `NOT_CHECKED` per class.
       - CORE10: `graph_probe` (registered); `report.probe`; the verb prints its line.
4. [x] One citing comment at each of the six precedent sites - name only. - CORE10 placed the two
       Lane A sites (plan_board, and the preflight's skipped suite, which adopted the type); the four
       under Lane B pens are handed to REM3, LIN4, API5 and DEEP1 by note (one pen per surface).
5. [x] One sentence in CLAUDE.md's working agreements pointing at this record. - CORE10.
