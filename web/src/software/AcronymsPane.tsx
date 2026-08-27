import { useState } from 'react'
import { ACRONYMS, type Acronym } from './softwareModel'

// The /software glossary pane (O68).
//
// WHY IT EXISTS: the three acronyms used to be joined with a middle dot onto the
// end of a 10px footnote that already carried two other sentences. Three entries
// and it already read as prose; the SNOW gloss alone is a full sentence carrying
// a warning, which is the entire reason that entry exists. The data was never the
// problem — the presentation had no room to grow.
//
// THE LAYOUT RULE, and it is not cosmetic: every expansion and note renders IN
// FULL. No truncation, no ellipsis, no tooltip-only text. A design validated on
// AIS and DPL (two words each) proves nothing; SNOW is the case that matters, so
// cells wrap and align to the top rather than clipping to one line.
//
// ADDING IS A WRITE SURFACE, and this one drafts an ARTIFACT — it writes nothing.
// The ui-write-surface gate (O20, signed off 2026-07-21) ruled direct graph write
// REFUSED STANDING, admin edits NEVER, and server-side git DEFERRED. Acronyms live
// in a committed config file rather than the graph, so the refused graph-write tier
// does not literally name this case; the artifact path still applies because the
// committed tree is authored through git and a console that edits config files
// directly reopens the question that gate closed. Same shape /mappings uses: draft
// into a tray, rationale required, submit downloads a snippet that travels git to
// review to merge.

export interface AcronymDraft {
  term: string
  expansion: string
  source: string
  note: string
  rationale: string
}

function download(filename: string, content: string, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([content], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = filename
  a.click()
  URL.revokeObjectURL(url)
}

/** Fold a long value onto a YAML block scalar so the snippet pastes cleanly. */
function yamlBlock(value: string, indent: string): string {
  const words = value.split(/\s+/).filter(Boolean)
  const lines: string[] = []
  let line = ''
  for (const w of words) {
    if (line && (line + ' ' + w).length > 72) {
      lines.push(line)
      line = w
    } else {
      line = line ? line + ' ' + w : w
    }
  }
  if (line) lines.push(line)
  return '>-\n' + lines.map((l) => indent + l).join('\n')
}

/**
 * The change artifact. It is a paste-ready fragment of the registry PLUS the
 * rationale, because a reviewer reading the diff needs the why and the YAML
 * carries no field the tooling would keep it in.
 */
function draftSnippet(drafts: AcronymDraft[], today: string, author: string): string {
  const header = [
    '# --- DRAFTED IN THE CONSOLE, NOT COMMITTED --------------------------------',
    '# Paste under `acronyms:` in config/taxonomy/software-registry.yaml, on a',
    '# branch, and open it for review. Nothing was written by the console: the',
    '# committed tree is authored through git (gate ui-write-surface / O20).',
    '# drafted-by: ' + author + '   drafted-on: ' + today,
    '#',
    '# RATIONALE (per entry) — carry this into the commit body; the YAML has no',
    '# field for it and a reviewer needs the why, not just the what:',
    ...drafts.map((d) => '#   ' + d.term + ': ' + d.rationale),
    '# ---------------------------------------------------------------------------',
    '',
  ].join('\n')

  const body = drafts
    .map((d) => {
      const rows = [
        '  ' + d.term + ':',
        '    expansion: ' + JSON.stringify(d.expansion),
        '    source: ' + JSON.stringify(d.source),
        '    added: ' + today,
      ]
      if (d.note.trim()) rows.push('    note: ' + yamlBlock(d.note.trim(), '      '))
      return rows.join('\n')
    })
    .join('\n')

  return header + body + '\n'
}

function Row({ a }: { a: Acronym }) {
  return (
    <tr className="align-top">
      <td className="border-b border-edge-soft px-2.5 py-2 font-mono text-[11px] font-semibold text-text">
        {a.term}
      </td>
      <td className="border-b border-edge-soft px-2.5 py-2 text-[11px] text-text">
        {/* In full, always — see the layout rule at the top of this file. */}
        <span>{a.expansion}</span>
        {a.note ? (
          <span className="mt-1 block text-[10px] leading-snug text-muted">{a.note}</span>
        ) : null}
      </td>
      <td className="border-b border-edge-soft px-2.5 py-2 text-[10px] leading-snug text-muted">
        {a.source}
      </td>
      <td className="whitespace-nowrap border-b border-edge-soft px-2.5 py-2 font-mono text-[10px] tabular-nums text-faint">
        {a.added}
      </td>
    </tr>
  )
}

function AcronymDialog({
  onCancel,
  onDraft,
  existing,
}: {
  onCancel: () => void
  onDraft: (d: AcronymDraft) => void
  existing: Set<string>
}) {
  const [term, setTerm] = useState('')
  const [expansion, setExpansion] = useState('')
  const [source, setSource] = useState('')
  const [note, setNote] = useState('')
  const [rationale, setRationale] = useState('')

  const normalized = term.trim().toUpperCase()
  const duplicate = normalized !== '' && existing.has(normalized)
  const ready =
    normalized !== '' &&
    expansion.trim() !== '' &&
    source.trim() !== '' &&
    rationale.trim() !== '' &&
    !duplicate

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      role="dialog"
      aria-modal="true"
      aria-label="Draft an acronym"
    >
      <div className="w-[32rem] max-w-[90vw] rounded-lg border border-edge bg-panel p-4 shadow-xl">
        <h3 className="text-sm font-semibold text-text">Draft an acronym</h3>
        <p className="mt-1 rounded border border-edge-soft bg-bg-2/40 p-2 text-[11px] text-muted">
          This drafts a <strong>change artifact</strong> — a YAML snippet you download and commit on a
          branch. The console writes nothing: the registry is authored through git (gate{' '}
          <code>ui-write-surface</code>, O20).
        </p>

        <label className="mt-3 block text-xs font-medium text-muted">
          Term <span className="text-brand-soft">(required)</span>
          <input
            type="text"
            value={term}
            onChange={(e) => setTerm(e.target.value)}
            placeholder="SNOW"
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 font-mono text-xs text-text"
          />
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Expansion <span className="text-brand-soft">(required)</span>
          <textarea
            value={expansion}
            onChange={(e) => setExpansion(e.target.value)}
            rows={2}
            placeholder="What the letters stand for. A full sentence is fine — the list renders it in full."
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
          />
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Source <span className="text-brand-soft">(required — who said so, and when)</span>
          <input
            type="text"
            value={source}
            onChange={(e) => setSource(e.target.value)}
            placeholder="SME flag 2026-08-09, marked IMPORTANT"
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
          />
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Note (optional — a caveat the expansion alone would lose)
          <textarea
            value={note}
            onChange={(e) => setNote(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
          />
        </label>
        <label className="mt-2 block text-xs font-medium text-muted">
          Rationale{' '}
          <span className="text-brand-soft">(required — travels in the artifact for the reviewer)</span>
          <textarea
            value={rationale}
            onChange={(e) => setRationale(e.target.value)}
            rows={2}
            className="mt-1 w-full rounded-md border border-edge bg-bg-2 p-1.5 text-xs text-text"
          />
        </label>

        {duplicate && (
          <p className="mt-1.5 rounded border border-yellow/50 bg-yellow/10 p-2 text-[11px] text-yellow">
            {normalized} is already in the registry — edit the committed entry rather than drafting a
            second one.
          </p>
        )}

        <div className="mt-3 flex justify-end gap-2">
          <button
            type="button"
            onClick={onCancel}
            className="rounded-md border border-edge bg-bg-2 px-2.5 py-1 text-xs font-medium text-muted hover:text-text"
          >
            Cancel
          </button>
          <button
            type="button"
            disabled={!ready}
            onClick={() =>
              onDraft({
                term: normalized,
                expansion: expansion.trim(),
                source: source.trim(),
                note: note.trim(),
                rationale: rationale.trim(),
              })
            }
            className="rounded-md border border-brand bg-panel-2 px-2.5 py-1 text-xs font-semibold text-text disabled:cursor-not-allowed disabled:border-edge disabled:text-faint"
          >
            Draft acronym
          </button>
        </div>
      </div>
    </div>
  )
}

export default function AcronymsPane({ author, today }: { author: string; today: string }) {
  const [drafts, setDrafts] = useState<AcronymDraft[]>([])
  const [dialog, setDialog] = useState(false)
  const [status, setStatus] = useState<string | null>(null)

  const existing = new Set([...ACRONYMS.map((a) => a.term), ...drafts.map((d) => d.term)])

  return (
    <div className="flex h-full min-h-0 flex-col gap-1.5">
      <div className="flex shrink-0 items-center justify-between gap-2">
        <span className="text-[10px] text-faint">
          {ACRONYMS.length} term{ACRONYMS.length === 1 ? '' : 's'} — the durable answer to &ldquo;what did
          that name mean&rdquo;, authored in <code>config/taxonomy/software-registry.yaml</code>
        </span>
        <button
          type="button"
          onClick={() => setDialog(true)}
          className="rounded-md border border-edge bg-bg-2 px-2.5 py-1 text-xs font-medium text-muted hover:text-text"
        >
          Add an acronym…
        </button>
      </div>

      <div className="min-h-0 flex-1 overflow-auto rounded-md border border-edge">
        <table className="w-full table-fixed border-collapse text-left text-[11px]">
          {/* Fixed widths: the expansion column takes the slack, so a long
              gloss wraps into more LINES rather than squeezing the term and
              date columns until a date breaks across two of them. */}
          <colgroup>
            <col className="w-[7rem]" />
            <col />
            <col className="w-[22rem]" />
            <col className="w-[6rem]" />
          </colgroup>
          <thead className="sticky top-0 bg-panel-2">
            <tr>
              {['Term', 'Expansion', 'Source', 'Added'].map((h) => (
                <th key={h} className="border-b border-edge px-2.5 py-1.5 font-semibold text-muted">
                  {h}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {ACRONYMS.map((a) => (
              <Row key={a.term} a={a} />
            ))}
          </tbody>
        </table>
      </div>

      {drafts.length > 0 && (
        <div className="shrink-0 rounded-md border border-brand bg-panel-2 p-2">
          <p className="text-[11px] text-text">
            {drafts.length} draft{drafts.length === 1 ? '' : 's'}:{' '}
            <span className="font-mono text-[10px] text-muted">
              {drafts.map((d) => d.term).join(', ')}
            </span>
          </p>
          <div className="mt-1.5 flex gap-2">
            <button
              type="button"
              onClick={() => {
                download('acronyms-draft.yaml', draftSnippet(drafts, today, author), 'text/yaml')
                setStatus(
                  'snippet downloaded (' +
                    drafts.length +
                    ' entr' +
                    (drafts.length === 1 ? 'y' : 'ies') +
                    ') — paste it under acronyms: on a branch and commit; the console wrote NO file',
                )
                setDrafts([])
              }}
              className="rounded-md border border-brand bg-panel px-2.5 py-1 text-xs font-semibold text-text"
            >
              Download YAML snippet
            </button>
            <button
              type="button"
              onClick={() => setDrafts([])}
              className="rounded-md border border-edge bg-bg-2 px-2.5 py-1 text-xs font-medium text-muted hover:text-text"
            >
              Discard
            </button>
          </div>
        </div>
      )}

      <p className="shrink-0 text-[10px] text-faint">
        {status ?? (
          <>
            Read-only ledger. <strong>Add</strong> drafts a snippet you commit through git — the console
            never edits the registry (gate <code>ui-write-surface</code>, O20). Every entry states its
            source: an expansion nobody can trace is not a glossary, it is a rumour.
          </>
        )}
      </p>

      {dialog && (
        <AcronymDialog
          existing={existing}
          onCancel={() => setDialog(false)}
          onDraft={(d) => {
            setDrafts((prev) => [...prev, d])
            setDialog(false)
            setStatus(d.term + ' drafted — download the snippet to carry it to git')
          }}
        />
      )}
    </div>
  )
}
