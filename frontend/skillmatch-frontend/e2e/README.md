# End-to-end tests (Playwright)

19 tests × 2 browser projects (Desktop Chrome + Pixel 7 mobile) = **38 tests
per full run** covering:

* Public pages (home, login, register, forgot-password, verify-email, privacy, 404)
* Auth flows (login success / bad-creds / ?next= redirect, forgot-password, register)
* Candidate flows (jobs list + filters, apply modal with cover note, bookmark
  toggle, dashboard email-verify banner)

All backend requests are stubbed via `page.route()`, so the tests are pure
frontend tests — you don't need Django running to execute them.

## One-time setup (on your machine)

```bash
cd frontend/skillmatch-frontend
npm install                            # installs @playwright/test as a dev dep
npm run playwright:install             # downloads Chromium (~150 MB)
```

## Run

```bash
# Headless (fastest — this is what CI runs)
npm run test:e2e

# Watch tests as they run against real Chrome
npm run test:e2e:hea

# Interactive UI mode (best for developing new tests)
npm run test:e2e:ui
```

The config's `webServer` block auto-boots `npm run dev` on port 3000 if
Playwright doesn't find one already listening.

## Configuration

`playwright.config.ts` at repo root:

* `baseURL` defaults to `http://localhost:3000`; override with `BASE_URL=…` to
  point at a deployed environment (skips the `webServer` block).
* Two `projects` — `chromium` (desktop) and `mobile-chrome` (Pixel 7).
* `retries: 2` and headless when `CI=1` is set.
* Reporters: `list` (stdout) + `html` (open `playwright-report/index.html`
  after a run).

## Adding a test

1. Drop a new `.spec.ts` file in `e2e/`.
2. Stub any backend endpoint you touch:

```ts
await page.route(`${API_ORIGIN}/api/whatever/`, (r) =>
  r.fulfill({ status: 200, contentType: "application/json",
              body: JSON.stringify({ ...mockPayload }) }));
```

3. If the page needs auth, either seed localStorage tokens with
   `page.addInitScript` and stub `/api/auth/me/`, or exercise the login
   form and let the flow authenticate.

## Enumerate tests without running

```bash
npm exec playwright test --list
```
