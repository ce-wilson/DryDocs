import { useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { APPS, PRODUCTS, searchAssets } from './assetSearch'

// The support-user search strip on /ownership (2026-07-21 chat): answers
// "who supports this file/table" and routes load-status questions to the
// asset path sub-page. Narrowing dropdowns FIRST (Product → Application →
// file/table), partial-name search LAST — never a name search across all
// assets. (Use-case wording kept out of the UI per the same-day user call.)
export default function AssetSearchPanel() {
  const [productId, setProductId] = useState('')
  const [appId, setAppId] = useState('')
  const [kind, setKind] = useState<'' | 'file' | 'table'>('')
  const [needle, setNeedle] = useState('')

  const apps = useMemo(() => (productId ? APPS.filter((a) => a.productId === productId) : APPS), [productId])
  const scoped = productId || appId
  const results = useMemo(
    () => (needle.trim().length >= 2 || scoped ? searchAssets({ productId, appId, kind, needle }) : []),
    [productId, appId, kind, needle, scoped],
  )

  return (
    <div className="shrink-0 border-b border-edge-soft bg-panel-2/60 px-3 py-2">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-[11px] font-semibold uppercase tracking-wide text-faint">
          Asset search
        </span>
        <select
          aria-label="Product"
          value={productId}
          onChange={(e) => {
            setProductId(e.target.value)
            setAppId('')
          }}
          className="text-xs"
        >
          <option value="">Product (if known)…</option>
          {PRODUCTS.map((p) => (
            <option key={p.id} value={p.id}>{p.label}</option>
          ))}
        </select>
        <select aria-label="Application" value={appId} onChange={(e) => setAppId(e.target.value)} className="text-xs">
          <option value="">Application (if known)…</option>
          {apps.map((a) => (
            <option key={a.id} value={a.id}>{a.label}</option>
          ))}
        </select>
        <select aria-label="Asset kind" value={kind} onChange={(e) => setKind(e.target.value as '' | 'file' | 'table')} className="text-xs">
          <option value="">file or table…</option>
          <option value="file">file</option>
          <option value="table">table</option>
        </select>
        <input
          type="search"
          value={needle}
          onChange={(e) => setNeedle(e.target.value)}
          placeholder="partial file / table name…"
          aria-label="Partial asset name"
          className="w-56 text-xs"
        />
        <span className="font-mono text-[10px] text-faint">
          {scoped || needle.trim().length >= 2
            ? `${results.length} match${results.length === 1 ? '' : 'es'} in scope`
            : 'narrow first, then search'}
        </span>
      </div>

      {results.length > 0 && (
        <ul className="mt-2 flex max-h-36 flex-col gap-1 overflow-y-auto">
          {results.map((a) => {
            const app = APPS.find((x) => x.id === a.appId)
            return (
              <li key={a.id}>
                <Link
                  to={`/ownership/asset/${a.id}`}
                  className="flex flex-wrap items-center gap-2 rounded-md border border-edge bg-panel px-2.5 py-1.5 text-xs no-underline hover:border-blue-bright"
                >
                  <span className="rounded border border-edge px-1.5 font-mono text-[10px] text-muted">{a.kind}</span>
                  <span className="font-mono text-text">{a.name}</span>
                  <span className="text-faint">{app?.label}</span>
                  <span
                    className={
                      'ml-auto font-mono text-[10px] ' +
                      (a.load.state === 'LATE' ? 'text-brand-soft' : a.load.state === 'RUNNING' ? 'text-blue-bright' : 'text-green')
                    }
                  >
                    {a.load.state}
                  </span>
                  <span className="font-mono text-[10px] text-muted">{a.support.team}</span>
                  <span className="text-blue-bright">path →</span>
                </Link>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}
