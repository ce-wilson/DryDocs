import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'

// IBM Plex, self-hosted (O8 acceptance — no Google Fonts CDN, intranet target).
// @fontsource bundles the woff2 files + @font-face rules; only the weights the
// UI actually uses are imported, to keep the bundle lean.
// IBM Plex Sans tops out at weight 700 on Fontsource; browsers fuzzy-match
// font-weight: 800 (used sparingly, e.g. the sign-in h1) to the nearest
// defined face rather than failing, so no 800 import is needed.
import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/ibm-plex-sans/700.css'
import '@fontsource/ibm-plex-mono/400.css'
import '@fontsource/ibm-plex-mono/500.css'
import '@fontsource/ibm-plex-mono/600.css'

import './index.css'
import App from './App.tsx'

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </StrictMode>,
)
