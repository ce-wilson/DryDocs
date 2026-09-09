# ADR 0021 — A result names what it did not check: one three-outcome type, and a probe that returns a bare boolean is refused

```yaml
status: PROPOSED        # PROPOSED | ACCEPTED | SUPERSEDED — the drafting session never accepts its own ADR; acceptance is the SME's, scheduled for sitting 1 (registry-wiring-readiness) as one message
date: 2026-09-09
authored_by: Lane A close, desktop (Fable 5.1), from the module sweep's cycle-1 conclusion
deciders: []            # acceptance requires the user's dated ruling; nothing here is pre-approved
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

> **Stub.** The number is reserved by this committed, pushed index line; the body follows in
> the next commit. Nothing implements this record until it is ACCEPTED.
