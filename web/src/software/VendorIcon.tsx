import type { Vendor } from './softwareModel'

// Renders a vendor's manifest icon, or a labelled initial when it has none.
// Vendors without an icon are reported in vendors_without_icons — never silent,
// never an error (the link is soft by design; see software-registry.yaml).
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

  const img = (asset: string, cls?: string) => (
    <img
      src={`/${asset}`}
      alt=""
      aria-hidden="true"
      title={vendor.name}
      className={cls}
      style={{ ...box, objectFit: 'contain' }}
    />
  )

  // Most marks carry their own colour and read on either ground, so they render
  // as one <img>. A few ship an OFFICIAL on-light/on-dark pair (React's
  // #087EA4 / #58C4DC) — for those, render both and let the theme decide.
  // The `dark:` variant rather than the theme hook on purpose: tokens.css opts
  // Tailwind into the CLASS-based dark variant, and that class is stamped by
  // the pre-paint boot script in index.html — so the right mark is correct on
  // the very first frame with no post-hydration swap, and System mode keeps
  // working without this component subscribing to anything.
  if (!vendor.icon.asset_dark) return img(vendor.icon.asset)
  return (
    <>
      {img(vendor.icon.asset, 'dark:hidden')}
      {img(vendor.icon.asset_dark, 'hidden dark:inline')}
    </>
  )
}
