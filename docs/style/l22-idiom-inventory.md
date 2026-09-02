# L22 idiom inventory — outward-facing set, 2026-08-03

Deliverable of backlog **L22** clauses (c) and (d). The sweep covered the
**outward-facing set only** (per the acceptance): the executive overview, the
whitepaper (source + both renders), and the website seed content. Governed
surfaces (`docs/design/*` renders, gate pages, the board) are out of scope —
their prose rides its own rev process. The rules applied are
[`us-business-english.md`](us-business-english.md); "crosswalk(s)" is the
SME-approved exception and was not counted.

## What was swept, what was found, what was done

| Surface | Hits | Disposition |
|---|---|---|
| `docs/overview/drydocs-executive-overview.html` | 21 live-prose occurrences: spine (7), plane(s) (7), decays/rots (2), gate-confirmed (1), guardrails (1), UK spellings — modelled/modelling/signalling (6) | **Rewritten in place, rev 7.** spine→backbone, planes→layers, decays/rots→goes stale/becomes outdated, gate-confirmed→"validated through the SME gate", "tenant guardrails"→"tenant-level access restrictions", spellings Americanized. Source decision recorded in the rev line: the HTML stays the single hand-authored source; no `.md` established. Rev-history lines (head comment + footer) kept verbatim as history. |
| `docs/whitepaper/drydocs-whitepaper.md` + `.html` + `.print.html` | 2: "cannot rot", "Metadata rot compounds" | **Rewritten** in the `.md` and both renders identically: "cannot go stale", "Metadata drift compounds". No other avoid-list hits — the whitepaper was already close to the guide. |
| `docs/design/ui-exploration/site-plan.md` (website seed) | 0 | Nothing to do. |

Content claims in the overview were deliberately **not** refreshed (the ADR
statuses and the "no crosswalk consumer in code" line predate S1/S2 landing) —
that is a content revision, not a style pass, and is noted in the rev-7 line.

## Candidate-rename list (clause d — the fence held; nothing below was renamed)

These terms are on the guide's avoid list but live in the repo as **coined
mechanism names**, not prose. Renaming any of them is a structural decision for
the user to rule separately; the style pass does not touch them. For each: the
term, where it lives, and what a rename would touch.

| Term | Where it lives | What a rename would touch | Recommendation |
|---|---|---|---|
| **"review spine"** | `config/review-labels.yaml` (names itself the review spine), `drydocs/review/review_labels.py` docstrings, `graph-tests/business-application-identity.yaml` comments | Config header comments, module docstrings, graph-test comments, the drydocs-review component's vocabulary — plus the company-side reproduction (drydocs-review back-flow epic) which inherits the term | Keep for now; if renamed, "review ledger" or "review label registry" — do it before the company back-flow reproduces the term further |
| **"lexical spine"** | `config/doc-source-registry.yaml` (entry comments + a `confirmed:` note), `drydocs/docs_verify.py` docstring | Registry comments, docs-verify docstring, N9 close-note references | Same call as "review spine"; the two should be ruled together |
| **guardrail 1–10 / "guardrail N"** | `docs/port/port-prompt.md` (the numbered port guardrails — cross-repo: company PORT-REPORTs cite "guardrail N" by number), gate-ruling citations in code (`drydocs_lineage/writer.py` "G12, guardrail 5", `extractors/controlm_xml.py` "guardrail 1/3"), `config/source-registry.yaml`, crosswalk gate prompts ("orchestrator-onboarding guardrail") | The port workflow's shared vocabulary on BOTH repos, every historical PORT-REPORT and gate log that cites a guardrail by number, memory files | **Keep.** The number citations are load-bearing across two repos; the guide's avoid rule targets outward-facing prose, and none of this is outward-facing |
| **"gate-confirmed"** | Pervasive as the HITL mechanism's own adjective: loader docstrings (`seal_attribution.py`, `batch_port_orchestrator.py`), `crosswalk.py`, cypher headers, `relationship_vocabulary.yaml` comments, web code comments, graph-tests | The standard internal term for "cleared the HITL gate with a recorded sign-off" — dozens of files, both repos, plus gate-log history | **Keep internally.** Outward-facing prose says "validated through the SME gate" (as the overview now does); internal code/config keeps the precise term |
| **HITL status `confirmed`** | `config/taxonomy-ontology-map.yaml` status enum, tests | Schema value + every entry + tests + gate history | **Keep** — named in the guide's scope fence explicitly |

Domain prose inside internal config comments ("DPL accelerator spine",
"launcher spine", "SHORTEST-path spine" in `assetSearch.ts`) was noted but not
listed as candidates: internal, not coined mechanism names, and not
outward-facing. New prose stops coining these per the guide; existing instances
age out as those files are edited.
