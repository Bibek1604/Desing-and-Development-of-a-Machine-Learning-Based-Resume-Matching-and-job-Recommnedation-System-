# SkillMatch Nepal — Frontend Audit Report

**Scope:** `P:\Final year thesis\frontend\skillmatch-frontend\` (Next.js 14.2.5, App Router)
**Date:** 2026-07-05
**Auditor:** Read-only structural + behavioural pass, evidence-cited.

---

## 1. Executive Summary

- **Solid, thesis-grade UI foundation.** A polished Tailwind + custom design system (`tailwind.config.ts` + `DESIGN_SYSTEM.md`), consistent shared primitives (`SectionHeading`, `PageHeader`, `Spinner`, `ErrorState`, `ErrorBoundary`, `Skeleton`), and clean Next.js App Router segmentation. The visual layer is arguably the strongest part of the codebase.
- **Integration layer is production-shaped.** `lib/api.ts` gives a single typed client with bearer tokens, silent 401 refresh, 30 s abort-timeout, DRF-envelope-aware error humanisation, and typed endpoint groups (`auth`, `resumes`, `jobs`, `matching`, `applications`, `feedback`, `notifications`, `admin`). This is unusually clean for a student project.
- **Three role experiences work end-to-end for the happy path** — candidate (upload -> dashboard -> recommended -> apply -> track), employer (post job -> view ranked candidates -> applicants CRUD -> company profile), and admin (users/jobs/apps/skills/resumes + ML retrain/rollback).
- **Missing pieces block a real launch.** No password reset, no email verification, no bookmark/saved-jobs, no messaging, no notification-preferences page, no employer analytics dashboard, no admin audit-log/reports/settings UI, no company-management screen distinct from jobs, no dedicated skill-management screens for the candidate side. All the backend endpoints for these do not have a frontend surface.
- **Security surface is thin.** JWTs live in `localStorage` (XSS-reachable), no CSP / `X-Frame-Options` / `Referrer-Policy` in `next.config.mjs`, no CSRF concept (mitigated by pure-bearer), and no client-side rate-limiting for auth attempts.
- **Overall completion:** roughly **72%** against the thesis's minimum viable scope (candidate/employer/admin CRUD + ML) and roughly **58%** against `SYSTEM_FEATURE_AUDIT.md`'s fuller checklist (which counts messaging, audit logs, reports, permissions matrix, email verification, saved jobs, etc.).

---

## 2. Repository Overview

**Package & tooling** (`package.json` L11-L26)

| Layer | Version | Notes |
|---|---|---|
| next | 14.2.5 | App Router, RSC-capable but nearly every page is `"use client"` |
| react / react-dom | 18.3.1 | |
| lucide-react | 0.417.0 | Only icon system used, consistent |
| recharts | 2.12.7 | Admin dashboard + LiveInsights |
| tailwindcss | 3.4.7 | Content globs `./app/**` and `./components/**` |
| typescript | 5.5.4 | Strict enabled |

Notably **absent**: no state library (Zustand / Redux), no data-fetching lib (SWR / React Query), no form lib (RHF / Formik), no test framework (`jest`, `vitest`, `playwright`), no ESLint config file, no `zod`, no i18n. Everything is hand-rolled `useState + fetch`.

**next.config.mjs** — 6 lines, just `reactStrictMode: true`. **No `headers()` for CSP / HSTS / frame policy, no `images.domains`, no `env` remap, no `rewrites`.**

**tsconfig.json** — `"strict": true`, `moduleResolution: bundler`, path alias `@/*` -> `./*`. No `noUncheckedIndexedAccess`, `noImplicitOverride`, or `exactOptionalPropertyTypes`. Good baseline.

**Tailwind** — extended emerald/teal brand ramps, custom shadows (`card`, `lift`, `glow`, `green`, `pop`), custom animations (`slide-up`, `float`, `shimmer`), gradient backgrounds (`gradient-aurora`, `gradient-brand`). Design tokens live in Tailwind config and `DESIGN_SYSTEM.md`.

**Folder layout** (source only, node_modules/.next excluded):

```
app/
  admin/{page,layout,error,users,jobs,applications,skills,resumes}
  applications/page.tsx
  dashboard/{page,error,ai-insights}
  employer/page.tsx           # 919 lines - largest file
  jobs/{page,[id]/page}
  login/, register/, profile/, upload/, recommended/, privacy/
  layout.tsx, page.tsx (home, 539 lines), loading, error, global-error, not-found
components/  (17 files, 1700 lines total)
context/     AuthContext.tsx, ToastContext.tsx
lib/         api.ts (670 lines), data.ts, score.ts, types.ts
public/logos/
```

Line-count hotspots: `app/employer/page.tsx` (919), `lib/api.ts` (670), `app/page.tsx` (539). The employer file mixes 4 tabs and ~10 sub-components and should be split.

---

## 3. Integration Layer

### `lib/api.ts` (670 lines) — the whole client

**Base + tokens** (`lib/api.ts:6, 15-26`)
- `BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"` — good default, single env var.
- `tokens` object stores `sm_access` / `sm_refresh` in `localStorage` (SSR-safe with `typeof window !== "undefined"` guards).
- `mediaUrl()` (L9-L12) prefixes relative paths — correctly handles absolute URLs too.

**Silent refresh** (`lib/api.ts:29-46, 150-159`)
- `tryRefresh()` posts to `/api/auth/refresh/`; on success, keeps the same refresh, replaces access. On fail, clears both. Single retry, no infinite loop.
- If refresh fails: `window.location.href = "/login"` (L156) — hard nav, wipes state, clean login.

**Timeout** (`lib/api.ts:104-124`)
- Fixed 30 000 ms `AbortController` + `setTimeout`. Distinguishes `AbortError` -> `APIError(0, {}, "timeout")` vs network fail -> `"network"`.

**Error humanisation** (`lib/api.ts:75-102`)
- Understands DRF `{ error: { message } }` envelope, DRF `detail`, DRF field-error arrays, generic strings; falls back to canned messages by status code.

**Endpoint groups** — all typed with explicit interfaces:

| Group | Endpoints | File:line |
|---|---|---|
| `auth` | login / register / me / profile / updateProfile / deleteAccount | L209-L219 |
| `resumes` | list / upload (FormData) / ats / analyze | L244-L255 |
| `jobs` | list / mine / get / create / update | L286-L304 |
| `employerProfile` | get / update / uploadLogo | L315-L324 |
| `candidateProfile` | get / update / uploadAvatar | L363-L372 |
| `matching` | recommendations / jobCandidates / candidateResume / skillGap / careerRecommendations / explain / dashboard | L469-L484 |
| `applications` | list / create / updateStatus / withdraw | L506-L515 |
| `feedback` | send (up/down) | L518-L523 |
| `notifications` | list / unreadCount / markRead / markAllRead / analytics | L544-L555 |
| `admin` | stats + retrain + rollback + modelVersions + users/jobs/applications/skills/resumes CRUD | L612-L670 |

**Missing endpoints (client side):** no `saveJob`, no `passwordReset*`, no `emailVerify*`, no `messaging*`, no `auditLogs`, no `reports`, no `companies` (distinct from employer profile), no `notificationPreferences`.

### `context/AuthContext.tsx` (103 lines)

- `login`, `register` (auto-logs in after register), `logout` (just token clear + state clear) — `useCallback`-memoised.
- On mount, if an access token exists, calls `auth.me()`; on failure clears tokens (L32-L36).
- `useRequireAuth(redirectTo, requiredRole?)` (L86-L103) — waits for `isLoading`, hard-redirects unauth users to `redirectTo`, redirects wrong-role users to `homeForRole(user.role)`.
- **Bypass risk:** the redirect fires inside `useEffect`, so first render still runs — sensitive UI can flash before the redirect. Not a data leak (backend enforces), just cosmetic.

### `context/ToastContext.tsx` (101 lines)
3-type toaster (`success`/`error`/`info`), 5 s auto-dismiss, `aria-live="polite"`, keyed by counter ref. Solid, no external dep.

### Other lib files
- `lib/data.ts` (169 lines) — static hero content (features / steps / stats).
- `lib/score.ts` (49 lines) — shared score band thresholds & Tailwind class helpers.
- `lib/types.ts` (43 lines) — small legacy type shim (mostly superseded by `api.ts` interfaces).

---

## 4. Candidate Feature Matrix

| Feature | Status | Evidence |
|---|---|---|
| Register | Present, role toggle (candidate/employer), password meter, ?role= prefill | `app/register/page.tsx:71-318` |
| Login | Present with humanised errors, `homeForRole` redirect | `app/login/page.tsx:24-39` |
| Logout | Present via `AuthContext.logout` + hard nav to `/` | `context/AuthContext.tsx:52-55`; `components/Navbar.tsx:54-60` |
| Password reset | **Missing** — no page, no `auth.forgotPassword` in `lib/api.ts` | grep for "forgot"/"password reset" -> nothing |
| Email verification | **Missing** — no verify page, no resend endpoint | grep -> nothing |
| Profile edit | Present, 3 sections (basics/education/preferences), avatar upload | `app/profile/page.tsx:63-474`; upload L84-99 |
| Resume upload | Present, drag-drop, PDF/DOCX/DOC/TXT ≤10 MB, fake-progress ticker | `app/upload/page.tsx:65-100` |
| Resume parsing feedback | Present — auto-fetches `/resumes/:id/ats/` after upload, shows strengths/weaknesses/recommendations | `app/upload/page.tsx:93-95`; `lib/api.ts:231-242` |
| Skill extraction display | Present — chips on dashboard and profile, `skills_count` stat | `app/dashboard/page.tsx` StatCard; `app/profile/page.tsx:69` |
| Job search | Present, text + `job_type` filter, Enter to submit, paginated | `app/jobs/page.tsx:33-150` |
| Job filter | Partial — only `job_type` in UI; no location/salary/skill filters | `app/jobs/page.tsx:137-150` |
| Save / bookmark jobs | **Missing** — no `saveJob` API, no bookmark button | grep "save"/"bookmark" -> only "saving" state |
| Apply to job | Present, POST `/applications/` with `cover_note=""`, disables once applied | `app/jobs/page.tsx:73-84`; `app/jobs/[id]/page.tsx:78-89` |
| Cover note on apply | **Missing in UI** — API supports it but nothing collects it | `lib/api.ts:509-510`; `app/jobs/page.tsx:76` |
| Track applications | Present — status pipeline with visual STEPS, withdraw button | `app/applications/page.tsx:34-170` |
| Recommendations | Present — dedicated page with 70% threshold + gap drawer + thumbs feedback | `app/recommended/page.tsx:16-138` |
| Notifications | Present — bell polls unread every 30 s, dropdown, mark-read | `components/NotificationBell.tsx:26-80` |
| Notification preferences | **Missing** — no toggle UI for email/push | — |
| Dashboard | Present, rich: profile card, 4 stat cards, top matches, ATS, career recs | `app/dashboard/page.tsx:77-402` |
| AI insights sub-page | Present | `app/dashboard/ai-insights/page.tsx` |
| Delete account | Present with confirm(), `auth.deleteAccount()`, logout, redirect | `app/profile/page.tsx:101-113` |

---

## 5. Employer Feature Matrix

| Feature | Status | Evidence |
|---|---|---|
| Company registration | **Merged into signup** — no separate flow; sign-up with `role=employer`, company filled later | `app/register/page.tsx:76`; `app/employer/page.tsx:852` |
| Company profile | Present — logo upload, name/website/location/description | `app/employer/page.tsx:641-735` (`CompanyProfilePanel`) |
| Post job (Create) | Present — `PostJobForm` title/company/location/type/desc/req/salary | `app/employer/page.tsx:51-210` |
| View own jobs (Read) | Present via `jobsApi.mine()` in `MyPostingsPanel` | `lib/api.ts:298`; `app/employer/page.tsx:516` |
| Edit job (Update) | **Partial** — only `is_active` toggled from UI; no full-edit form | `app/employer/page.tsx:453-465` |
| Close / deactivate job | Present via `is_active: !active` PATCH | `app/employer/page.tsx:456` |
| Delete job | **Missing** for employer (only admin has it) | `admin.jobs.remove` at `lib/api.ts:639` |
| Applicant list | Present — `ApplicantsPanel` across own postings | `app/employer/page.tsx:747-838` |
| Ranked candidates view | Present — per-job ML-ranked list with matched-skills chips | `app/employer/page.tsx:330-405` (`CandidatesPanel`) |
| Resume view | Present — `ResumeDrawer` renders skills + file link + raw text | `app/employer/page.tsx:275-326` |
| Candidate search / filter | **Missing** — no keyword filter on the candidate panel | no `Search` input in `CandidatesPanel` |
| Shortlist / Reject actions | Present via status dropdown | `app/employer/page.tsx:764-775, 815-825` |
| Messaging | **Missing** entirely | no `messages` route, no API group |
| Dashboard (employer) | **Missing** — landing IS the post-job tab | `app/employer/page.tsx:852` |
| Analytics (funnel, time-to-hire) | **Missing** | — |
| Bulk actions | **Missing** | — |

---

## 6. Admin Feature Matrix

| Feature | Status | Evidence |
|---|---|---|
| User management (list/edit/delete/create) | Present with search, pagination, modal form | `app/admin/users/page.tsx:16-80+`; `admin.users.*` at `lib/api.ts:621-630` |
| Company / Employer management | **Missing as distinct screen** — employers only editable via generic Users tab | `app/admin/layout.tsx:14-21` has no "Companies" item |
| Job management | Present with pagination + delete + create/update | `app/admin/jobs/page.tsx`; L632-L641 |
| Application management | Present — status updates + delete | `app/admin/applications/page.tsx`; L643-L650 |
| Skill management | Present — CRUD | `app/admin/skills/page.tsx`; L652-L662 |
| Resume management | Present — list + delete only (no create/edit) | `app/admin/resumes/page.tsx`; L664-L669 |
| ML model management — retrain | Present — button posts `admin.retrain(800)` and displays metrics banner | `app/admin/page.tsx:131-142` |
| ML model management — rollback | Present — per-row rollback button in `ModelPanel` table | `app/admin/page.tsx:144-155, 187-204` |
| ML version history | Present — full table with accuracy/AUC/samples/trained-at | `app/admin/page.tsx:176-210` |
| Reports (exportable) | **Missing** | — |
| Analytics beyond top-level pie/bar | **Partial** — 2 charts on admin home | `app/admin/page.tsx:71-115` |
| Audit logs | **Missing** | no route, no API |
| Permissions matrix | **Missing** | roles are only 3 flat strings |
| Settings screen | **Missing** — no `/admin/settings` | admin nav lists only 6 items |

---

## 7. Protected Routes & Auth Flow

**Role guard mechanism.** Two variants:

1. `useRequireAuth(redirect, requiredRole?)` inside a page (`context/AuthContext.tsx:86-103`). Used by `app/dashboard/page.tsx:79`, `app/applications/page.tsx:35`, `app/upload/page.tsx:54`, `app/profile/page.tsx:64`, `app/recommended/page.tsx:19`, `app/employer/page.tsx:854`. Wrong role -> hard nav to `homeForRole(user.role)`.
2. Admin layout guards its subtree (`app/admin/layout.tsx:23-39`) — same pattern; spinner while `isLoading || !isAdmin`.

**Bypass considerations:**
- Client-side only; redirect fires in `useEffect` after first paint. Content can flash — but backend also enforces auth so no data leaks.
- No `middleware.ts` — SSR-side redirect not used.

**Token storage.** `localStorage` under `sm_access` / `sm_refresh` (`lib/api.ts:15-26`). Any XSS -> full account takeover. No `HttpOnly` cookies, no rotation of refresh, no device/session list.

**Refresh behaviour.** Silent on 401: refresh, retry once. **Refresh token is reused** (not rotated; `lib/api.ts:40`).

**Redirect after login.** `homeForRole(role)` (`lib/api.ts:181-186`). No `?next=` return-URL support — deep-link intent lost.

---

## 8. UI/UX — Loading, Errors, Responsiveness, Accessibility

**Error boundaries & special routes**
- `app/error.tsx`, `app/global-error.tsx`, `app/not-found.tsx`, `app/loading.tsx`.
- Nested: `app/dashboard/error.tsx`, `app/admin/error.tsx`.
- Reusable `components/ErrorBoundary.tsx` (49 lines) wraps charts in `app/admin/page.tsx:77-113`, `LiveInsights` (`app/page.tsx:331-333`), `CandidatesPanel` (`app/employer/page.tsx:347-404`).

**Skeletons** — hand-rolled `<Skeleton>` / `.skeleton` on: dashboard, applications, jobs, admin tables (`components/admin/parts.tsx::TableSkeleton`).

**Toast pattern** — `context/ToastContext.tsx` used in every mutating page.

**Responsiveness — Tailwind breakpoints.** ~89 lines match `sm:`/`md:`/`lg:`/`xl:` across `.tsx`. Every layout uses `md:grid-cols-2` / `sm:grid-cols-4` — solid mobile-first.

**Mobile drawers.**
- Admin sidebar becomes slide-in drawer < md (`app/admin/layout.tsx:107-114`).
- Navbar drops to hamburger < md (`components/Navbar.tsx` L35).
- Employer's `ResumeDrawer` is a modal-style side panel.

**Accessibility**
- `aria-live="polite"` on toast (`ToastContext.tsx:70`).
- `aria-pressed` on tab toggles (`app/employer/page.tsx:899`, `app/register/page.tsx:200`).
- `aria-label` on password show/hide and toast dismiss.
- `role="alert"` on inline error blocks.
- `role="status"` on loading spinners.
- **Missing:** explicit `<label htmlFor>` linking, `Escape` handler for dropdowns, `prefers-reduced-motion` gating.

---

## 9. Code Quality

**TypeScript `any` usage** — exactly **one** hit: `lib/api.ts:52` `public data: any` (with explicit ESLint disable). Excellent.

**ESLint disables** — 3 total: `components/Avatar.tsx:20`, `components/CompanyLogo.tsx:20` (`no-img-element` — user avatars, valid), and the `api.ts` any. No `next lint` config file — relies on Next's built-in.

**TODO / FIXME / HACK** — **zero** in-source hits. Either genuinely clean or debt-hidden.

**Unused files** — `components/JobCard.tsx` (46 lines) is superseded by `components/jobs/JobCard.tsx` (268 lines with `GapDrawer` + `SkeletonCard`). The pages import the newer one. Top-level `JobCard.tsx` is dead.

**Duplication**
- `LoginPage` and `RegisterPage` share ~50 lines of left brand panel. Extract to `AuthBrandPanel`.
- `applicationsApi.list().then(...)` pattern repeated in `app/jobs/page.tsx:63-71`, `app/jobs/[id]/page.tsx:66-72`, `app/recommended/page.tsx:41-46`, `app/applications/page.tsx:46-47`. Needs a `useApplications()` hook.
- `PostingRow`, `MyPostingsPanel`, `PostJobForm`, `CompanyProfilePanel`, `CandidatesPanel`, `ApplicantsPanel`, `ResumeDrawer` all inside one 919-line file.

**Stale docs** — `README.md` and `DESIGN_SYSTEM.md` present.

---

## 10. Bugs / Red Flags

| # | Severity | Issue | Evidence |
|---|---|---|---|
| B1 | High | Refresh token never rotates. `tryRefresh` re-uses same refresh (`lib/api.ts:40`). If backend rotates, subsequent refreshes 401; if not, stolen tokens have unbounded life. |
| B2 | High | Empty cover note on apply. `applicationsApi.create(jobId)` default `coverNote = ""` (`lib/api.ts:509`); no UI collects it. Silently non-functional. |
| B3 | Medium | Role-guard flash. `useRequireAuth` redirects in `useEffect`; unauthorized UI briefly renders. Cosmetic since data is authed. |
| B4 | Medium | Hard-nav on redirect kills SPA feel. `AuthContext:94, 98` uses `window.location.href` instead of `router.replace`. |
| B5 | Medium | Notification poll runs even for anonymous. `NotificationBell` (`components/NotificationBell.tsx:41-45`) fires every 30 s regardless of auth state. |
| B6 | Medium | Silent catch swallows errors. Many `.catch(() => {})` — `context/AuthContext.tsx:34`, `app/jobs/page.tsx:71`, etc. |
| B7 | Low | Fake progress ticker. `app/upload/page.tsx:82-91` fakes upload progress with `setInterval + Math.random`. |
| B8 | Low | Employer job-edit is only `is_active`. Backend fully supports edit — form missing. |
| B9 | Low | `PostJobForm` company field defaults to profile.company_name but user can freely edit. No server-side enforcement in evidence. |
| B10 | Low | Home page uses `<img>` for logos (`app/page.tsx:294, 466`) — bypasses Next Image. Not critical for SVG. |
| B11 | Low | `useEffect` in `RegisterPage` reads `window.location.search` for `?role=` — comment explains it avoids Suspense boundary. |

---

## 11. Security Frontend Concerns

**Missing security headers.** `next.config.mjs` has no `async headers()` block. No CSP, no `X-Content-Type-Options: nosniff`, no `Referrer-Policy`, no `Permissions-Policy`, no HSTS from Next. Only whatever the reverse-proxy adds.

**XSS surface.** Grep for `dangerouslySetInnerHTML` -> **zero**. User text is rendered as text nodes or inside `<pre>` (`app/employer/page.tsx:317`). Primary XSS vector is closed. However, resume `raw_text` is user-controlled and rendered inside `<pre>`, no length cap.

**localStorage token risk.** JWTs in `sm_access` / `sm_refresh` readable by any script on the origin. Combined with **no CSP**, this is the largest un-mitigated risk. Remediation: move refresh to `HttpOnly; Secure; SameSite=Strict` cookie, keep short-lived access in memory.

**CORS side.** Client makes cross-origin requests to `BASE = http://localhost:8000` in dev. Sends bearer tokens explicitly — credentials-mode is `"omit"` implicitly. No CSRF token used (correct for pure-bearer).

**Input sanitisation.**
- Email inputs use `type="email"` (browser validation only).
- Password minimum 8 chars enforced client-side (`app/register/page.tsx:96-98`). No complexity requirement (only strength meter).
- Salary min/max are `type="number"` (no min/max attrs, no relationship validation client-side).
- Uploaded file type checked via regex `\.(pdf|docx|doc|txt)$/i` (`app/upload/page.tsx:66`) — MIME NOT checked. Backend must revalidate.

**Rate limiting.** No client-side throttling on login/register submit; button disables while `loading` but a script can hammer. Backend must protect.

**Session fixation / logout.** `logout` only clears tokens and state (`context/AuthContext.tsx:52-55`). No server-side revoke call.

---

## 12. Module Scoreboard

| Module | Score /10 | Note |
|---|---|---|
| Design system & visual polish | 9.5 | Custom Tailwind, tokens, consistent primitives, animated hero, real skeletons |
| API client (`lib/api.ts`) | 9.0 | Typed, refresh, timeout, humanised errors |
| Auth context & guards | 7.5 | Solid pattern but hard-nav redirects + no ?next= + no rotation |
| Candidate flow | 7.5 | Full happy path, missing save/bookmark + password reset + verify |
| Employer flow | 6.5 | Post + rank + status works; no dashboard, no analytics, no edit-form, no messaging |
| Admin flow | 7.0 | CRUD works + ML mgmt; no audit logs / reports / settings / permissions |
| Loading / error UX | 8.5 | Boundaries everywhere, skeletons everywhere, toast wired |
| Accessibility | 6.5 | Good aria on interactive parts; missing htmlFor, keyboard-nav for dropdowns |
| Responsiveness | 8.5 | Mobile-first, drawers, ~89 breakpoint lines |
| Code quality (types/dedup) | 8.0 | Almost zero `any`, no TODOs, employer file 919 lines and JobCard duplicated |
| Security | 5.0 | localStorage JWT, no CSP, no rotation, no verified upload MIME |
| Testing | 0.0 | No tests, no test runner in deps |
| Docs | 7.0 | README + DESIGN_SYSTEM present, comments helpful |
| **Weighted average** | **7.0** | — |

---

## 13. Overall Completion

**Against thesis minimum scope** (candidate: upload -> matches -> apply -> track; employer: post -> ranked -> status; admin: CRUD + retrain): **≈ 72%**. Core loop functional end-to-end. Gaps: no password reset, no email verify, no employer analytics, no admin audit-log/reports, no messaging, no saved jobs, no cover-note collection.

**Against `SYSTEM_FEATURE_AUDIT.md`'s fuller checklist** (adds messaging, analytics, audit logs, permissions, settings, email verification, saved jobs, bulk actions, plus perf/testing/security): **≈ 58%**. Missing chunks are entire modules, not just polish.

---

## 14. Prioritised Roadmap

### Critical (ship-blockers for a real user launch)

1. **Password reset flow.** `app/forgot-password/page.tsx` + `app/reset-password/[token]/page.tsx`; extend `auth` in `lib/api.ts` with `forgotPassword(email)` and `resetPassword(token, password)`.
2. **Email verification.** `app/verify-email/[token]/page.tsx` + banner on `app/dashboard/page.tsx` when `user.email_verified === false` with "Resend" action.
3. **Rotate refresh tokens.** Update `lib/api.ts:40` to use the new refresh returned by `/auth/refresh/`. Add proactive refresh before expiry.
4. **Move refresh token out of localStorage.** Persist as `HttpOnly; Secure; SameSite=Strict` cookie via backend `/auth/refresh/`. Keep short-lived access in memory only.
5. **Add security headers.** Extend `next.config.mjs` with `async headers()` returning CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`.

### High

6. **Cover-note dialogue on apply.** Extend `JobCard`/`app/jobs/[id]/page.tsx:78` — modal (`components/ApplyModal.tsx`) that captures `coverNote`.
7. **Saved / bookmarked jobs.** New `saveJob`/`unsaveJob` API group; heart-icon on `components/jobs/JobCard.tsx`; `/saved` route.
8. **Employer dashboard.** New tab (`Tab = "post" | "postings" | "applicants" | "company" | "insights"`) with KPI cards using recharts.
9. **Employer full-edit form.** Extend `PostingRow` in `app/employer/page.tsx:447` with "Edit" action opening a modal reusing `PostJobForm` for update path.
10. **Admin audit log page.** `app/admin/audit/page.tsx` + `admin.auditLogs.list()` in `lib/api.ts`.
11. **Split `app/employer/page.tsx`.** Extract into `components/employer/*.tsx`. Target: 919 -> <200 lines.
12. **Delete unused duplicate.** Remove `components/JobCard.tsx` (46 lines).

### Medium

13. **Return-URL after login.** In `useRequireAuth` pass `redirectTo = "/login?next=" + encodeURIComponent(pathname)`; LoginPage honours `?next`.
14. **Candidate search filters.** Add location + salary + skill multi-select to `app/jobs/page.tsx:125-150`.
15. **Notification preferences UI.** `app/settings/notifications/page.tsx`.
16. **Admin reports export.** `app/admin/reports/page.tsx` — CSV/PDF export.
17. **Form validation library.** Adopt `react-hook-form` + `zod`.
18. **`middleware.ts`** for SSR-side auth redirects — prevent UI-flash.
19. **Data-fetching library.** Adopt SWR or React Query for `applicationsApi.list()` cache-sharing.

### Low

20. **Verify upload MIME server-side and echo client-side.** Currently only extension checked.
21. **`prefers-reduced-motion` gate** in `tailwind.config.ts` animations.
22. **Explicit `htmlFor`/`id`** pairs on `.label`-wrapped inputs.
23. **Escape-to-close** on `NotificationBell` and `ResumeDrawer`.
24. **Tests.** Add `vitest` + `@testing-library/react`; cover `humanizeError`, `AuthProvider`, `useRequireAuth`, `PostJobForm`.
25. **Real progress via `XMLHttpRequest.upload.onprogress`** in `resumes.upload`.
26. **Real logo/company handling** in `components/CompanyLogo.tsx`.

---

*End of report.*
