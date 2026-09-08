// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { TraceLink } from './TraceLink'

// R18 (d), console half. Three conditions gate the control and each answers a
// different question — did the SERVER record a trace, may THIS PERSON read it,
// and is there a run id to look one up by. The chip must fall back to the plain
// run id it has always shown whenever any of them fails, because a disabled
// button that exists to explain itself is worse than the text it replaced.

const trace = vi.hoisted(() => ({ fetchQaTrace: vi.fn() }))
const files = vi.hoisted(() => ({ download: vi.fn() }))

vi.mock('../lib/qaTrace', async (importOriginal) => {
  const real = await importOriginal<typeof import('../lib/qaTrace')>()
  return { ...real, fetchQaTrace: trace.fetchQaTrace }
})
vi.mock('../components/ui/tableControls', async (importOriginal) => {
  const real = await importOriginal<typeof import('../components/ui/tableControls')>()
  return { ...real, download: files.download }
})

afterEach(() => {
  cleanup()
  trace.fetchQaTrace.mockReset()
  files.download.mockReset()
})

const PAYLOAD = {
  run_id: 'qa-20260908-101112-ab12cd',
  session_id: 'ask-jdoe4821-wjtacr8x',
  enabled: true,
  files: ['qa-debug.graph_qa.20260908.jsonl'],
  records: [{ kind: 'qa_trace', hop: 'run_open', seq: 1 }],
  record_count: 1,
  skipped: 0,
  truncated: false,
}

function mount(overrides: Partial<Parameters<typeof TraceLink>[0]> = {}) {
  render(
    <TraceLink
      runId={PAYLOAD.run_id}
      enabled
      canRead
      apiBase="/api"
      {...overrides}
    />,
  )
}

describe('TraceLink', () => {
  it('offers the trace when a run was recorded and the person may read it', () => {
    mount()
    expect(screen.getByRole('button', { name: /download the decision trace/i })).toBeTruthy()
  })

  it('renders the plain run id when the server recorded no trace', () => {
    // The default deployment: qa-debug is declared without level: DEBUG, so
    // there is nothing behind the id and nothing is offered.
    mount({ enabled: false })
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.getByText(/run qa-20260908/)).toBeTruthy()
  })

  it('renders the plain run id for a persona who may not read it', () => {
    mount({ canRead: false })
    expect(screen.queryByRole('button')).toBeNull()
    expect(screen.getByText(/run qa-20260908/)).toBeTruthy()
  })

  it('renders nothing at all without a run id — there is no lookup to offer', () => {
    const { container } = render(
      <TraceLink runId={undefined} enabled canRead apiBase="/api" />,
    )
    expect(container.textContent).toBe('')
  })

  it('fetches by run id and hands the person the trace as a file', async () => {
    trace.fetchQaTrace.mockResolvedValue(PAYLOAD)
    mount()
    fireEvent.click(screen.getByRole('button'))

    await waitFor(() => expect(files.download).toHaveBeenCalledTimes(1))
    expect(trace.fetchQaTrace).toHaveBeenCalledWith('/api', { runId: PAYLOAD.run_id })
    const [name, body, type] = files.download.mock.calls[0]
    expect(name).toBe(`qa-trace-${PAYLOAD.run_id}.json`)
    expect(type).toBe('application/json')
    expect(JSON.parse(body).records[0].hop).toBe('run_open')
  })

  it('says a trace failed without making the answer above it look broken', async () => {
    trace.fetchQaTrace.mockRejectedValue(new Error('the Ask trace is an admin surface'))
    mount()
    fireEvent.click(screen.getByRole('button'))

    await waitFor(() => expect(screen.getByText(/trace: the Ask trace is an admin surface/)).toBeTruthy())
    expect(files.download).not.toHaveBeenCalled()
    // still offered — a refused read is not a reason to remove the control
    expect(screen.getByRole('button')).toBeTruthy()
  })
})
