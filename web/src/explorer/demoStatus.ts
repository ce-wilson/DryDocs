import { parseStatusItems, type StatusItem } from '../lib/status'
import type { Selection } from './demoGraph'

// O28 — demo status items for the Explorer inspector.
//
// The Explorer canvas is the SYNTHESIZED demo graph (see demoGraph.ts), so
// these are illustrative, exactly like every other value in that inspector —
// the sidebar already stamps "SYNTHESIZED · illustrative" on the panel.
//
// They matter anyway, and this is the point of the file: they are authored as
// the SAME wire format the live producer emits — JSON strings, parsed through
// the same `parseStatusItems` the live path uses. So the inspector's status
// section is exercised against the real contract rather than a convenient
// object literal, and a shape change breaks the demo surface too, loudly,
// instead of leaving it quietly rendering a format nothing produces.
//
// The live counterpart is `loads.status-items.v1` (the /loads Status frame).
// Wiring THIS panel to live data needs the demo→live selection bridge the
// Explorer does not have yet; that is a graph-plumbing job, not a contract
// one, and the contract is what O28 fixes.

const DEMO_WIRE: Record<string, readonly string[]> = {
  // A job whose last load dropped rows — the commonest real signal.
  EtlJob: [
    '{"level":"warning","message":"3 of 120 rows failed validation","type":"drydocs.loader/rows-rejected"}',
  ],
  // Drift: things the source stopped sending.
  Dataset: [
    '{"level":"warning","message":"4 nodes no longer present in source","type":"drydocs.loader/removed-from-source"}',
  ],
  ControlMJob: [
    '{"level":"info","message":"2 previously-removed nodes returned","type":"drydocs.loader/reactivated"}',
  ],
}

/**
 * Demo status items for a selected node, in the live wire format.
 *
 * An empty result means HEALTHY (a producer ran, nothing to report) — the
 * contract's distinction from "unknown", which is the absence of any run.
 */
export function statusItemsForDemoNode(selection: Selection): StatusItem[] {
  return parseStatusItems(DEMO_WIRE[selection.kind] ?? [])
}
