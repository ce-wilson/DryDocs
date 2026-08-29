# Company-side prompt — load the `cdo-frameworks` capture into the graph

> Producer-drafted 2026-08-20 for the company-side assistant. Paste or read whole.
> The capture this loads EXISTS ONLY ON YOUR SIDE (the 2026-08-19 live Confluence
> fetch — consolidated HTML + `run-20260819T215955Z` manifest under your
> `internal/knowledge/data/<space>/`). The producer repo carries the mechanism and
> the registry row; guardrail 6 — loads are always yours. Everything below is a
> HAND-PROMPT task because a port cannot carry it: the payload never leaves your
> network.

## What this is

The `cdo-frameworks` corpus (`config/doc-source-registry.yaml`) — the firmwide
data-publishing frameworks the ontology mapping was built from — is registered,
**activated** (`confirmed: true`, user ruling 2026-08-05 at the cdo-crosswalk
sign-off), and as of 2026-08-19 **captured VERBATIM**: your `drydocs-scrape` run
fetched ~50 pages, 0 failed, closing the four capture holes the row named
(Descriptive Metadata + WIP CDAO twin, Data Quality, Data Contracts/DPROD, the
Taxonomy Framework property tables). The registry row is updated producer-side
and reaches you at the next port; nothing in it needs your edit.

## The work, in order

1. **QA the one empty page.** The drafts/upcoming index came back 0 bytes.
   Confirm it is genuinely an empty parent page (likely) or re-fetch it; record
   which in your run notes. An empty capture recorded as "empty by inspection"
   is fine; an empty capture nobody looked at is a hole with a checkmark.

2. **Load via the docmeta pipeline** — the Q10/Q9 lexical shape: one
   `:Document` per page, `:Chunk` via `PART_OF`, corpus id `cdo-frameworks`
   per the corpus-id grammar, into YOUR `drydocs` database (the row's
   `target_db` — the G102 fold applies to you only if/when your own fold gate
   ratifies; until then load to wherever your content realm lives and say so).
   The consolidated HTML is the input; the manifest is the provenance record —
   cite its run id in the load's JobRun note.

3. **T4 `sme-confirm` curation applies per page.** Activation did not waive it:
   pages enter curation-pending and the SME confirms them page-by-page (the
   working-group MINUTES pages are the ones to triage hardest — they are
   meeting notes, not standards, and may deserve exclusion or a lower shelf).

4. **Set `graph_locator`** on your side of the row once loaded (match/value per
   the registry's locator grammar) — that field is the one piece of the row
   that is yours, since only your graph holds the nodes.

5. **Publish-boundary check before any commit**: the capture carries real
   employee names, internal URLs and the space key. All of that stays under
   `internal/`; your commits outside `internal/` cite the corpus id and run id
   only.

## One back-flow ask (your next PORT-REPORT)

`drydocs-scrape` is company-built (your pyproject entry point) and the producer
has no equivalent Confluence connector — the producer's registry row now cites
your capture as the corpus source. Include the scraper's source (or its
location + interface summary) in the next PORT-REPORT's back-flow section so
the producer can disposition it (the J39 family: reproduce mechanism-only, or
adopt). Until then the producer treats the connector as company-canonical.

## What this deliberately does NOT do

- No `dcat:theme` edges, no subject classification — that is C34's gate
  (the skos:ConceptScheme declaration), unsigned. Loading the corpus and
  theming the corpus are different acts; this prompt is the first only.
- No "context search" — the retrieval feature over this corpus is named THEME
  SEARCH and waits on C34; the naming rule (and why "context" never appears in
  a new id) lives in `config/taxonomy/context-types.yaml`'s header.
