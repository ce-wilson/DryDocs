import { Component, useState, type ErrorInfo, type ReactNode } from 'react'
import { Outlet, useLocation } from 'react-router-dom'

// WEB5 — one render throw breaks one panel, not the console.
//
// THE DEFECT (S7): there was no ErrorBoundary and no componentDidCatch anywhere
// in web/src. React 19 unmounts the ENTIRE tree on an uncaught render error, so
// a single bad row — an unexpected null where a string was indexed, a malformed
// generated artifact — produced a white page with no navigation and no way back
// except a manual reload.
//
// KEYED ON PATHNAME. A React error boundary latches: once it has caught, it
// renders its fallback until its state is reset or it is remounted. Without the
// key, navigating away from a broken route would carry the broken panel to the
// next one, and the console would stay broken until a reload — the same
// outcome, one layer down. The key remounts the boundary on every navigation,
// so moving away IS the recovery.
//
// It is a class because React has no hook for this; error boundaries are the
// one place a class component is still the only mechanism.

interface Props {
  children: ReactNode
  onReset: () => void
}

interface State {
  error: Error | null
}

class Boundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo): void {
    // The console has no telemetry (S8), so this is the only record a developer
    // gets. It goes to console.error rather than to a UI element on purpose:
    // the component stack is a developer artifact and the panel below is for
    // the person using the page.
    console.error('[route error]', error, info.componentStack)
  }

  render(): ReactNode {
    const { error } = this.state
    if (!error) return this.props.children

    return (
      <div className="flex h-full min-h-0 items-start justify-center p-6" data-route-error>
        <div className="max-w-2xl rounded-lg border border-red/50 bg-red/5 p-4">
          <h2 className="text-sm font-semibold text-red">This panel could not be rendered</h2>
          {/* VERBATIM (the O63 honesty rule): the exact string is what a reader
              pastes into a ticket, and a reworded one is a different string. No
              stack trace and no value from the data that threw — a render error
              on a row of INTERNAL data must not put that row on screen in the
              name of diagnosing it. */}
          <p className="mt-2 font-mono text-[11px] leading-relaxed text-text">{error.message}</p>
          <p className="mt-2 text-[11px] text-muted">
            The rest of the console is unaffected — the navigation still works, and moving to
            another page clears this.
          </p>
          <button
            type="button"
            onClick={() => {
              this.setState({ error: null })
              this.props.onReset()
            }}
            className="mt-3 rounded-md border border-edge bg-bg-2 px-3 py-1 text-sm font-medium text-text"
          >
            Try this page again
          </button>
        </div>
      </div>
    )
  }
}

/** The pathless layout route that wraps every route's outlet.
 *
 * The retry bumps a nonce that is part of the key, so it REMOUNTS the subtree
 * rather than merely clearing the boundary's state. Clearing alone would
 * re-render the same components over the same already-failed data and throw
 * again immediately — a button that looks like a retry and is not one. A
 * remount re-runs the hooks, so the read actually happens again.
 */
export default function RouteErrorBoundary() {
  const { pathname } = useLocation()
  const [nonce, setNonce] = useState(0)
  return (
    <Boundary key={`${pathname}#${nonce}`} onReset={() => setNonce((n) => n + 1)}>
      <Outlet />
    </Boundary>
  )
}
