// The end-to-end path (O80): sign in, reach a module, assert a rendered value.
//
// WHY THIS PATH AND NOT A RICHER ONE. It is the path every console session
// starts with and the one a person has had to walk by hand after every auth
// change since O69 replaced the client-side persona picker with a real login.
// It crosses all three processes — browser, Vite, drydocs-api — so a failure
// anywhere in that chain is caught, which is precisely what a mocked shell
// cannot do.
//
// WHY /gates IS THE MODULE. It renders from a COMMITTED GENERATED ARTIFACT
// (web/src/generated/gates.json, written by scripts/render_gates.py), so the
// assertion needs no Neo4j — the API's driver is created lazily, so it serves
// /login without a graph, and a graph-backed module would make this suite a
// database test wearing a browser. The value asserted is computed FROM that
// artifact rather than hardcoded, so the test tracks the record instead of
// pinning a number that grooming will move next week.
import { expect, test } from '@playwright/test'

// The import attribute is required: this file is executed by Node (Playwright's
// runner), not bundled by Vite, and Node's ESM loader will not treat a .json
// file as a module without being told to.
import gatesData from '../src/generated/gates.json' with { type: 'json' }

const PERSONA = 'Morpheus' // must match E2E_PERSONA in bootstrap_credential.py
const SECRET = process.env.DRYDOCS_E2E_SECRET as string

const GATE_COUNT = gatesData.gates.length

test.describe('console sign-in and module render', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/')
  })

  test('signs in and renders the gate record from the generated artifact', async ({ page }) => {
    // --- sign in -----------------------------------------------------------
    await expect(page.getByRole('heading', { name: 'DryDocs Console' })).toBeVisible()

    await page.getByRole('button', { name: PERSONA }).click()
    await page.locator('#console-secret').fill(SECRET)
    await page.getByRole('button', { name: 'Sign in' }).click()

    // The sign-in screen going away is the proof the API accepted the secret:
    // a refusal keeps the form up and renders the error instead.
    await expect(page.getByRole('heading', { name: 'DryDocs Console' })).toBeHidden()

    // --- reach a module ----------------------------------------------------
    // Through the nav rather than by URL, so the test also proves the shell
    // rendered a working way in. A goto would pass on a console whose nav is
    // blank.
    // `exact` matters: the signed-in landing page also carries a Gates CARD whose
    // accessible name is "Status unknown Gates Gate…", so a substring match finds
    // two links and Playwright refuses to guess. The nav entry is the one a person
    // uses to change module, and it is named exactly.
    await page.getByRole('link', { name: 'Gates', exact: true }).click()
    await expect(page).toHaveURL(/\/gates$/)

    // --- assert a rendered value -------------------------------------------
    // The count comes from the artifact this page renders, so the assertion
    // stays true as the gate record grows and fails if the page stops reading
    // it.
    await expect(page.getByText(`${GATE_COUNT} gates in the record`)).toBeVisible()
  })

  test('refuses a wrong secret and says so without signing in', async ({ page }) => {
    // The negative half matters as much as the positive one: a login that
    // accepts anything would pass the test above. This is also the only
    // assertion in the suite that the SERVER, not the client, is deciding.
    await page.getByRole('button', { name: PERSONA }).click()
    await page.locator('#console-secret').fill('not-the-secret')
    await page.getByRole('button', { name: 'Sign in' }).click()

    await expect(page.getByRole('heading', { name: 'DryDocs Console' })).toBeVisible()
    await expect(page.getByRole('link', { name: 'Gates', exact: true })).toHaveCount(0)
  })
})
