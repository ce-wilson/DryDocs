// Unit runner for the console (O80).
//
// WHY VITEST RATHER THAN JEST: the console is a Vite app, so Vitest reuses the
// one transform pipeline the app already builds with — the same esbuild/TS
// settings, the same `resolve` rules, the same JSON imports. A second toolchain
// would mean a second way for `import gazetteer from '../../generated/...'` to
// behave, and a test that passes under a transform the app does not use proves
// nothing about the app.
//
// SCOPE, per O80's scope guard: this config exists to make PURE modules testable.
// `environment: 'node'` is the default here on purpose — resolve.ts touches no
// DOM — and the jsdom environment is opted into per-file with a docblock pragma
// when a component test eventually needs it, rather than paid for globally.
//
// The e2e suite is excluded: Playwright owns e2e/, and Vitest picking those files
// up would run them with no browser and fail confusingly.
import { defineConfig } from 'vitest/config'

export default defineConfig({
  test: {
    include: ['src/**/*.{test,spec}.{ts,tsx}'],
    exclude: ['e2e/**', 'node_modules/**', 'dist/**'],
    environment: 'node',
    globals: false,
    reporters: ['default'],
  },
})
