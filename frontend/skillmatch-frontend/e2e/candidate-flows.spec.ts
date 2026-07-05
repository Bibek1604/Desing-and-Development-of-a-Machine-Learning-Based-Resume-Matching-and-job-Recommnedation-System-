import { test, expect, type Page, type Route } from "@playwright/test";

/**
 * Candidate flows — jobs list, apply modal, saved-jobs toggle, dashboard
 * email-verify banner. All API calls are stubbed so we're testing the
 * frontend end-to-end without needing Django running.
 *
 * These are the flows the thesis defends: an IT graduate lands on the
 * platform, browses jobs, applies to one with a cover note, and bookmarks
 * others for later.
 */

const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

const jobs = [
  {
    id: 1, title: "Backend Developer", company: "Leapfrog Technology",
    location: "Kathmandu, Nepal", job_type: "full_time",
    job_type_display: "Full Time",
    description: "Build the next generation of financial APIs in Nepal.",
    requirements: "Python, Django, PostgreSQL, REST APIs.",
    salary_min: 60000, salary_max: 120000, is_active: true,
    created_at: "2026-06-01T00:00:00Z",
    required_skills: [{ id: 1, name: "Python" }, { id: 2, name: "Django" }],
  },
  {
    id: 2, title: "Frontend Developer", company: "Deerwalk",
    location: "Lalitpur, Nepal", job_type: "internship",
    job_type_display: "Internship",
    description: "Ship polished React interfaces for a healthcare product.",
    requirements: "React, TypeScript, Tailwind CSS.",
    salary_min: 25000, salary_max: null, is_active: true,
    created_at: "2026-06-15T00:00:00Z",
    required_skills: [{ id: 3, name: "React" }],
  },
];

const meCandidate = {
  id: 42, email: "cand@example.com", full_name: "Cand Idate",
  role: "candidate", email_verified: true,
};

async function stubJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status, contentType: "application/json", body: JSON.stringify(body),
  });
}

// Preload localStorage tokens before the first navigation so the SPA
// starts up already authenticated.
async function signInAsCandidate(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem("sm_access",  "acc.token.candidate");
    localStorage.setItem("sm_refresh", "ref.token.candidate");
  });
  await page.route(`${API_ORIGIN}/api/auth/me/`, (r) => stubJson(r, meCandidate));
}

test.describe("candidate: jobs list + filters", () => {
  test.beforeEach(async ({ page }) => {
    await signInAsCandidate(page);
    await page.route(new RegExp(`${API_ORIGIN}/api/jobs/(\\?.*)?$`), (r) =>
      stubJson(r, { results: jobs, count: 2, num_pages: 1 }),
    );
    await page.route(`${API_ORIGIN}/api/matching/recommendations/`, (r) =>
      stubJson(r, [
        { job: jobs[0], score: 87, similarity: 65, matched_skills: ["Python", "Django"] },
      ]),
    );
    await page.route(`${API_ORIGIN}/api/applications/`, (r) => stubJson(r, []));
    await page.route(`${API_ORIGIN}/api/saved-jobs/`, (r) => stubJson(r, []));
  });

  test("shows both jobs from the backend", async ({ page }) => {
    await page.goto("/jobs");
    await expect(page.getByText("Backend Developer")).toBeVisible();
    await expect(page.getByText("Frontend Developer")).toBeVisible();
    await expect(page.getByText(/of 2 roles shown/i)).toBeVisible();
  });

  test("location filter narrows results client-side", async ({ page }) => {
    await page.goto("/jobs");
    await page.getByLabel(/filter by location/i).fill("Lalitpur");
    await expect(page.getByText("Frontend Developer")).toBeVisible();
    await expect(page.getByText("Backend Developer")).toHaveCount(0);
    // Clear-filters button appears
    await expect(page.getByRole("button", { name: /clear filters/i })).toBeVisible();
  });

  test("min-salary filter hides jobs below the threshold", async ({ page }) => {
    await page.goto("/jobs");
    await page.getByLabel(/minimum salary/i).fill("50"); // NPR 50k * 1000
    await expect(page.getByText("Backend Developer")).toBeVisible();
    // Frontend intern job (25k) should be filtered out
    await expect(page.getByText("Frontend Developer")).toHaveCount(0);
  });
});

test.describe("candidate: apply modal + saved jobs", () => {
  test.beforeEach(async ({ page }) => {
    await signInAsCandidate(page);
    await page.route(new RegExp(`${API_ORIGIN}/api/jobs/(\\?.*)?$`), (r) =>
      stubJson(r, { results: jobs, count: 2, num_pages: 1 }),
    );
    await page.route(`${API_ORIGIN}/api/matching/recommendations/`, (r) => stubJson(r, []));
    await page.route(`${API_ORIGIN}/api/applications/`, (r) => stubJson(r, []));
    await page.route(`${API_ORIGIN}/api/saved-jobs/`, (r) => stubJson(r, []));
  });

  test("apply modal opens, collects cover note, and submits", async ({ page }) => {
    let submitted: { job?: number; cover_note?: string } = {};

    // Intercept the POST /applications/ (create) request separately from GET.
    await page.route(`${API_ORIGIN}/api/applications/`, async (route) => {
      if (route.request().method() === "POST") {
        submitted = JSON.parse(route.request().postData() || "{}");
        return stubJson(route, {
          id: 501, job: submitted.job, status: "applied",
          match_score: 74, cover_note: submitted.cover_note, applied_at: "2026-06-30",
        }, 201);
      }
      return stubJson(route, []);
    });

    await page.goto("/jobs");
    // The first Apply button belongs to the first card
    await page.getByRole("button", { name: /^apply$/i }).first().click();
    await expect(page.getByRole("dialog")).toBeVisible();
    const note = "I have shipped 3 Django REST APIs at internships and am eager to grow.";
    await page.getByLabel(/cover note/i).fill(note);
    await page.getByRole("button", { name: /submit application/i }).click();
    await expect(page.getByRole("dialog")).not.toBeVisible({ timeout: 5000 });
    expect(submitted.cover_note).toBe(note);
  });

  test("bookmark button toggles saved state", async ({ page }) => {
    let savedRowId = 900;

    await page.route(`${API_ORIGIN}/api/saved-jobs/`, async (route) => {
      const req = route.request();
      if (req.method() === "POST") {
        const body = JSON.parse(req.postData() || "{}");
        return stubJson(route, {
          id: ++savedRowId, job: body.job, created_at: "2026-06-30",
        }, 201);
      }
      return stubJson(route, []);
    });
    await page.route(new RegExp(`${API_ORIGIN}/api/saved-jobs/\\d+/`), (r) => {
      // DELETE endpoint returns 204 no content.
      return r.fulfill({ status: 204, body: "" });
    });

    await page.goto("/jobs");
    const bookmark = page.getByRole("button", { name: /save this job/i }).first();
    await expect(bookmark).toBeVisible();
    await bookmark.click();
    // After save, the same button is now labelled "Remove from saved jobs".
    await expect(
      page.getByRole("button", { name: /remove from saved jobs/i }).first(),
    ).toBeVisible({ timeout: 5000 });
  });
});

test.describe("candidate: dashboard email-verify banner", () => {
  test("dashboard shows verify banner when email_verified is false", async ({ page }) => {
    await page.addInitScript(() => {
      localStorage.setItem("sm_access",  "acc.token.candidate");
      localStorage.setItem("sm_refresh", "ref.token.candidate");
    });
    await page.route(`${API_ORIGIN}/api/auth/me/`, (r) =>
      stubJson(r, { ...meCandidate, email_verified: false }),
    );
    await page.route(`${API_ORIGIN}/api/matching/dashboard/`, (r) => stubJson(r, {}));

    await page.goto("/dashboard");
    await expect(page.getByText(/confirm your email address/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /resend/i })).toBeVisible();
  });

  test("dashboard hides banner when email is verified", async ({ page }) => {
    await signInAsCandidate(page);
    await page.route(`${API_ORIGIN}/api/matching/dashboard/`, (r) => stubJson(r, {}));

    await page.goto("/dashboard");
    await expect(page.getByText(/confirm your email address/i)).toHaveCount(0);
  });
});
