# G86 — can a RULE_BASED_CALENDAR be validated, and can it render as an actual calendar?

**Date:** 2026-09-11 · **Trigger:** backlog item G86 (groomed 2026-08-12 from a user follow-up
asking whether calendars can be validated or rendered in the console). **Lens:** two questions,
answered separately per the acceptance — validation is graph/model work, rendering is a console
surface, and either can ship without the other. **Classification:** Internal-Public (mechanism
only; no vendor data values, no calendar names beyond the synthetic examples below).
**Pen:** `code:drydocs-web` (UI-workstream session, `feat/web-completeness`) for the rendering
half and this ruling; the production validator, when there is data to validate, is
`drydocs_core` — a different pen, named but not built here.

- **Reviewed at:** commit `cc7e40df` on `feat/web-completeness`, port base `port-base-20260910b`;
  venue MSI. *Absent here reads as not-yet-ported, not as broken
  (docs/style/review-provenance.md).*

**A spike ruling, per the acceptance's own terms.** G86 allows a written ruling with a worked
synthetic example, or the validator/renderer itself, and says building both is not required to
close it. This document is the ruling for validation, and points at a real spike for rendering
rather than describing one.

---

## The finding both questions turn on: the pipeline has never acquired an RBC's own rule content

`knowledge/standards/technology/calendar-resolution-projection-plan.md` — the standing plan for
calendar-aware run projection — is honest about this already: Phase A, "Acquire & normalize
calendar data," is `status: planned` and has not shipped. What that means concretely, read from
the ingestion path rather than assumed:

- `tests/unit/fixtures_controlm_xml.py` (fixture F3) carries a `RULE_BASED_CALENDARS` element:

  ```xml
  <RULE_BASED_CALENDARS NAME="WORKDAYS" DAYS="ALL" DAYS_AND_OR="OR"/>
  ```

  This is the **reference** side — which named calendars are assigned to a folder or job, and
  how their lists combine (the vendor doc's *Specific Rule-based calendar scheduling* table:
  Rule-based Calendars List, Excluded RBC List, the AND/OR relationship to a parent SMART
  folder). It says nothing about what WORKDAYS itself contains.
- `drydocs_remediation/xml_io.py` never models calendar elements at all. Its own docstring says
  why: splicing parses only to LOCATE edit spans, so "`INCOND`/`OUTCOND`/`ON`/`CAPTURE`/calendars
  survive because nobody ever rewrites them, not because we modeled them." The reference
  attribute above rides through the pipeline as unmodeled residue — untouched bytes — the same
  way an `OUTCOND` does.
- The calendar's own rule content — which specific dates, which weekdays, which month-days,
  which advanced combination WORKDAYS actually resolves to — is a **separate Control-M object**
  (a distinct export, per BMC's own Tools-domain Calendars screen), and nothing in this
  repository's ingestion path acquires it. `external/orchestration/bmc-controlm/controlm-
  calendars.md` documents the vendor's calendar model in full; it is reference material, not a
  claim that the data has been pulled in.

So both questions in the acceptance meet the same wall from opposite sides: validation needs a
calendar's rule content to check anything against; rendering needs the same content to draw
anything. Neither is blocked by anything the console or the loader chose to do — both are
blocked by data that was never acquired.

---

## Question 1 — Validation: RULED, not built

**Ruling: internal-consistency validation of an RBC, and validating a job's schedule against the
calendar it names, cannot be built today — not because the logic is hard, but because there is
no calendar rule content anywhere in this pipeline to validate.** What exists is the reference
attribute (which calendars a job/folder names, and their AND/OR combination), and that alone
supports only a narrower, syntactic check: is the named calendar's combination operator one of
the legal values, and does the calendar name meet the vendor's own naming constraints (distributed:
≤30 characters; mainframe: ≤8 uppercase characters, no whitespace — both from the calendars doc's
Authoritative Additions). That is a reference-well-formedness check, not a schedule validation,
and building it now would answer a question nobody asked: G86's premise is "validated against the
calendar it names," which requires the calendar, not just its name.

**The validator itself, as a worked spike, exists — deliberately not in `drydocs_core`.** The
acceptance offers "the validator itself" as an alternative deliverable to a ruling. Building the
production version would mean writing calendar rule-resolution logic in `drydocs_core` against
data the loader has never acquired, which is not a spike, it is authoring a component against a
premise this ruling has just said is false. Instead, the resolvable half of "internal
consistency" — given a hypothetical, fully-specified calendar, can its rules be resolved into a
concrete, checkable date set — is proved out in `web/src/calendar/rbcCalendar.ts`, inside this
lane's own pen, as a worked example rather than a production artifact. It implements all four RBC
rule types from the vendor doc (Specific Dates, Weekdays with nth/last-occurrence, Month Days,
Advanced AND/OR combination) as pure functions, tested in `web/src/calendar/rbcCalendar.test.ts`
against an independent oracle (`Date.UTC`, a different code path than the resolver's own
weekday arithmetic) for every rule type. When Phase A lands real calendar data, this is the shape
the production resolver takes — moved into `drydocs_core` per `MODULE_MAP.md`'s placement test
(pure resolve logic, no graph write, no run cadence), not rewritten from scratch.

**Worked synthetic example — the boundary check the acceptance calls out by name.** Given:

```
calendar WORKDAYS, years: [2026], rule: last Friday of each month
job PRXYZ3C001 names RULE_BASED_CALENDARS="WORKDAYS" DAYS_AND_OR="OR"
```

Validating PRXYZ3C001's schedule against WORKDAYS for **2026** resolves to twelve dates (one
last-Friday per month) and the job's candidate order dates can be checked against that set.
Validating the same job for **2028** must not silently resolve to an empty set — 2026 is
WORKDAYS's only declared year, so 2028 is a coverage gap, not a day WORKDAYS excludes. The two
outcomes are different facts (`resolveRbcYear`'s `'resolved'` vs. `'out-of-coverage'` variants
make that distinction a return-value shape, not a comment) and a validator that collapses them
would report "the job never runs" for a year the calendar was simply never asked about — the
exact silent-projection failure the acceptance calls "WRONG."

---

## Question 2 — Rendering: a scoped spike, real and running

**Ruling: rendering an RBC as an actual calendar is buildable once rule content exists, and the
spike proves the approach rather than asserting it.** `web/src/calendar/RbcCalendarSpike.tsx`
takes a `RuleBasedCalendarDef` and a year/month as props (not a fetch — there is nothing to fetch
yet, per the finding above) and renders a real month grid, matched dates flagged, via
`web/src/calendar/rbcCalendar.ts`'s resolver. Scoped to RBC only, per the acceptance's own
instruction ("render a calendar is really three renderers — scope a spike to RBC only first");
Regular and Periodic calendars are out of scope here and would each need their own renderer.

**The boundary behavior is a distinct rendered state, not a smaller grid.** When the requested
year is outside the calendar's declared coverage, the component does not draw an empty or
partial grid — it renders no grid at all, and shows the boundary explicitly (which years the
calendar does declare) via the shared `EmptyState` primitive. `web/src/calendar/
RbcCalendarSpike.test.tsx` asserts this directly: an out-of-coverage year produces zero day
cells and the boundary message; a covered year produces every day of the month as a cell, matched
or not, so a month with no matches renders as all-non-match rather than being silently thinned.

**Deliberately not wired into a route, a nav entry, or the module registry.** `config/taxonomy/
ui-components.yaml` registers the component (UNBOUND — `calendar` is not a registry module, and
there is no route for it to belong to yet) so the O42 ledger stays complete, but it is reachable
only from its own tests. Routing it into the console now would mean shipping a page backed by
prop-only synthetic data, which is the console's own "never a blank state" convention pointed at
itself: a nav entry that opens to fabricated dates is worse than no nav entry. Wiring it up is the
natural next item once Phase A acquires real RBC content — at that point the spike's resolver
moves to `drydocs_core`, a fetch replaces the prop, and this component (or its
successor) gets a route.

---

## What this ruling does not do

It does not build Regular or Periodic calendar renderers (out of scope per the acceptance). It
does not touch `drydocs_remediation/xml_io.py` or any `drydocs_core` module — those are outside
this lane's pen (`code:drydocs-web`), and the finding above is exactly why touching them now
would be premature: there is nothing yet for a production validator or loader change to act on.
It does not re-open `calendar-resolution-projection-plan.md`'s phasing; Phase A staying `planned`
is the standing decision this ruling confirms rather than revisits.
