import type { Vendor } from './softwareModel'

// Renders a vendor's manifest icon, or a labelled initial when it has none.
// 7 of 12 vendors have no icon — reported, never silent, never an error.
//
// THE GOTCHA: render_software_registry.py writes `asset` WITHOUT a leading
// slash ("vendor-icons/neo4j.svg"). A relative src on the /software route
// resolves to /software/vendor-icons/... and 404s, so the leading slash is
// added here rather than at every call site.

export default function VendorIcon({ vendor, size = 18 }: { vendor?: Vendor; size?: number }) {
  const box = { width: size, height: size, flex: `0 0 ${size}px` }

  if (!vendor?.icon) {
    return (
      <span
        aria-hidden="true"
        title={vendor ? `${vendor.name} — no manifest icon` : 'unknown vendor'}
        style={{
          ...box,
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          border: '1px solid var(--faint)',
          borderRadius: '50%',
          fontSize: size * 0.55,
          color: 'var(--muted)',
          lineHeight: 1,
        }}
      >
        {(vendor?.name ?? '?').slice(0, 1).toUpperCase()}
      </span>
    )
  }

  return (
    <img
      src={`/${vendor.icon.asset}`}
      alt=""
      aria-hidden="true"
      title={vendor.name}
      style={{ ...box, objectFit: 'contain' }}
    />
  )
}
