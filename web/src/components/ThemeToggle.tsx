import { useEffect, useState } from 'react'
import { applyThemeMode, currentThemeMode, THEME_MODES, type ThemeMode } from '../lib/theme'

const LABEL: Record<ThemeMode, string> = { system: 'System', dark: 'Dark', light: 'Light' }
const GLYPH: Record<ThemeMode, string> = { system: '◐', dark: '●', light: '○' }

// The 3-state System/Dark/Light toggle (O8 acceptance), header cluster
// (site-plan §3: "Header carries: global search, env toggle, 3-state theme
// toggle, avatar" / wf-landing-01 annotation 6). Reads its initial state from
// what the pre-paint boot script already stamped on <html> — no flash, no
// re-derivation from localStorage that could disagree with what painted.
export default function ThemeToggle() {
  const [mode, setMode] = useState<ThemeMode>(() => currentThemeMode())

  // While in System mode, live-follow OS scheme changes without a reload.
  useEffect(() => {
    if (mode !== 'system') return
    const mq = window.matchMedia('(prefers-color-scheme: dark)')
    const onChange = () => applyThemeMode('system')
    mq.addEventListener('change', onChange)
    return () => mq.removeEventListener('change', onChange)
  }, [mode])

  function choose(next: ThemeMode) {
    setMode(next)
    applyThemeMode(next)
  }

  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      className="flex overflow-hidden rounded-md border border-edge text-xs font-semibold"
    >
      {THEME_MODES.map((m) => (
        <button
          key={m}
          type="button"
          role="radio"
          aria-checked={mode === m}
          title={`${LABEL[m]}${m === 'system' ? ' (follows your OS)' : ''}`}
          onClick={() => choose(m)}
          className={
            'flex items-center gap-1.5 px-2.5 py-1.5 transition-colors ' +
            (mode === m ? 'bg-panel-2 text-text' : 'text-muted hover:text-text')
          }
        >
          <span aria-hidden="true">{GLYPH[m]}</span>
          <span className="hidden sm:inline">{LABEL[m]}</span>
        </button>
      ))}
    </div>
  )
}
