// Theme state — System / Dark / Light (O8 acceptance). The source of truth for
// "is dark active right now" is the `dark` class on <html>, stamped first by the
// inline pre-paint boot script in index.html (so there is no flash of the wrong
// theme), then kept in sync here as the user toggles or the OS scheme changes.
// Mirror any change to the constants/logic below in the index.html boot script.

export type ThemeMode = 'system' | 'dark' | 'light'

export const THEME_STORAGE_KEY = 'drydocs.theme.v1'
export const THEME_MODES: readonly ThemeMode[] = ['system', 'dark', 'light']

function systemPrefersDark(): boolean {
  return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: dark)').matches
}

export function resolveIsDark(mode: ThemeMode): boolean {
  return mode === 'dark' || (mode === 'system' && systemPrefersDark())
}

// Reads the mode the boot script already stamped as `data-theme-mode` on <html>
// — avoids re-deriving from localStorage (and risking drift from what actually
// painted) on first React render.
export function currentThemeMode(): ThemeMode {
  if (typeof document === 'undefined') return 'system'
  const attr = document.documentElement.getAttribute('data-theme-mode')
  return attr === 'dark' || attr === 'light' ? attr : 'system'
}

export function applyThemeMode(mode: ThemeMode): void {
  const isDark = resolveIsDark(mode)
  const root = document.documentElement
  root.classList.toggle('dark', isDark)
  root.setAttribute('data-theme-mode', mode)
  root.style.colorScheme = isDark ? 'dark' : 'light'
  try {
    localStorage.setItem(THEME_STORAGE_KEY, mode)
  } catch {
    /* privacy mode etc. — theme still applies for this page load */
  }
}
