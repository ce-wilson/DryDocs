---
name: documentation
description: Write and maintain technical documentation. Trigger with "write docs for", "document this", "create a README", "write a runbook", "onboarding guide", "white paper", or when the user needs help with any form of technical writing — API docs, architecture docs, operational runbooks, or an outward-facing white paper.
---

# Technical Documentation

Write clear, maintainable technical documentation for different audiences and purposes.

## Document Types

### README
- What this is and why it exists
- Quick start (< 5 minutes to first success)
- Configuration and usage
- Contributing guide

### API Documentation
- Endpoint reference with request/response examples
- Authentication and error codes
- Rate limits and pagination
- SDK examples

### Runbook
- When to use this runbook
- Prerequisites and access needed
- Step-by-step procedure
- Rollback steps
- Escalation path

### Architecture Doc
- Context and goals
- High-level design with diagrams
- Key decisions and trade-offs
- Data flow and integration points

### Onboarding Guide
- Environment setup
- Key systems and how they connect
- Common tasks with walkthroughs
- Who to ask for what

### White Paper
An outward-facing argument for a decision-maker who will not read the code: why the
system exists, what it does, and what trusting it rests on. Section sequence, derived from
the worked example [`docs/whitepaper/drydocs-whitepaper.md`](../../../docs/whitepaper/drydocs-whitepaper.md)
(Rev 1, 2026-07-12):
- Executive summary — the claim and the payoff in one screen
- The problem — what the reader's organization loses today, in their terms
- The approach — the few ideas the system rests on (DryDocs: four layers, standards-grounded)
- Architecture — enough structure to be credible, no more (diagrams over prose)
- What it does on day one — the concrete first use case, not the vision
- Governance and trust model — who confirms what, and how a wrong claim is caught
- Operating model and roadmap — how it runs, what comes next, what is deliberately not promised
- Conclusion
Choose this type, not the Architecture Doc, when the reader decides rather than builds: the
architecture doc answers "how is it put together", the white paper answers "why should we
have this and what would we be trusting". A white paper is a NON-GOVERNED outward-facing
document (CLAUDE.md section 6: editorial and design treatment are allowed here, unlike the
`docs/design/*` renders) and follows the U.S. business-English style guide below.

## Style — read this before writing prose

**All DryDocs prose follows [`docs/style/us-business-english.md`](../../../docs/style/us-business-english.md)** —
U.S. business-technical English for a U.S. enterprise audience. Plain, concrete, direct:
"backbone"/"core"/"source of truth", not "spine"/"planes"; "becomes outdated", not "decays";
lead with the core claim. The guide carries two boundaries that are part of the rule:
mechanism names (the HITL status `confirmed`, port-prompt guardrails, identifiers) are never
renamed by a style pass, and "crosswalk(s)" is an SME-approved exception (2026-08-03).

## Choosing the type

README for a repo or package; API for an interface; Runbook for an operator at 2 a.m.;
Architecture Doc for a builder; Onboarding for a new teammate; **White Paper for a
decision-maker** — the one type whose reader will not open the code. If a request fits
two, write the one whose reader is named in the request.

## Principles

1. **Write for the reader** — Who is reading this and what do they need?
2. **Start with the most useful information** — Don't bury the lede
3. **Show, don't tell** — Code examples, commands, screenshots
4. **Keep it current** — Outdated docs are worse than no docs
5. **Link, don't duplicate** — Reference other docs instead of copying
