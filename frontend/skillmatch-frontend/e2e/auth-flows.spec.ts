import { test, expect, type Route } from "@playwright/test";

/**
 * Auth flows — login, forgot-password, ?next= redirect, register.
 *
 * These stub the backend with page.route() so the tests are pure UI tests
 * that don't need Django running. Every assertion is on frontend behaviour
 * — form submission, redirect, toast, banner.
 */

const API_ORIGIN = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

async function stubJson(route: Route, body: unknown, status = 200) {
  await route.fulfill({
    status,
    contentType: "application/json",
    body: JSON.stringify(body),
  });
}

test.describe("auth flows", () => {
  test("login submits with valid credentials and redirects to /dashboard", async ({ page }) => {
    await page.route(`${API_ORIGIN}/api/auth/login/`, (r) =>
      stubJson(r, { access: "acc.token.x", refresh: "ref.token.x" }),
    );
    await page.route(`${API_ORIGIN}/api/auth/me/`, (r) =>
      stubJson(r, {
        id: 1, email: "test@example.com", full_name: "Test User",
        role: "candidate", email_verified: true,
      }),
    );

    await page.goto("/login");
    await page.getByLabel(/email address/i).fill("test@example.com");
    await page.getByLabel(/password/i).fill("supersecret");
    await page.getByRole("button", { name: /sign in/i }).click();

    await page.waitForURL("**/dashboard", { timeout: 5000 });
    expect(page.url()).toContain("/dashboard");
  });

  test("login honours ?next= after successful auth", async ({ page }) => {
    await page.route(`${API_ORIGIN}/api/auth/login/`, (r) =>
      stubJson(r, { access: "a", refresh: "r" }),
    );
    await page.route(`${API_ORIGIN}/api/auth/me/`, (r) =>
      stubJson(r, {
        id: 2, email: "cand@example.com", full_name: "Cand", role: "candidate",
      }),
    );
    // Stub protected page's backend calls so the redirect target renders.
    await page.route(`${API_ORIGIN}/api/matching/dashboard/`, (r) => stubJson(r, {}));

    await page.goto("/login?next=%2Fapplications");
    await page.getByLabel(/email address/i).fill("cand@example.com");
    await page.getByLabel(/password/i).fill("password123");
    await page.getByRole("button", { name: /sign in/i }).click();

    await page.waitForURL("**/applications*", { timeout: 5000 });
    expect(page.url()).toContain("/applications");
  });

  test("login shows an error message on bad credentials", async ({ page }) => {
    await page.route(`${API_ORIGIN}/api/auth/login/`, (r) =>
      stubJson(r, { detail: "No active account found with the given credentials" }, 401),
    );

    await page.goto("/login");
    await page.getByLabel(/email address/i).fill("bad@example.com");
    await page.getByLabel(/password/i).fill("wrong");
    await page.getByRole("button", { name: /sign in/i }).click();

    // humanizeError converts a 401 with detail into a friendly message.
    await expect(page.getByRole("alert")).toBeVisible({ timeout: 5000 });
  });

  test("forgot-password submits and shows success state", async ({ page }) => {
    await page.route(`${API_ORIGIN}/api/auth/password-reset/request/`, (r) =>
      stubJson(r, { detail: "If an account exists, a reset link has been sent." }),
    );

    await page.goto("/forgot-password");
    await page.getByLabel(/email/i).fill("you@example.com");
    await page.getByRole("button", { name: /send reset link/i }).click();

    // Success state: "Check your inbox" panel appears.
    await expect(page.getByText(/check your inbox/i)).toBeVisible({ timeout: 5000 });
    await expect(page.getByText(/you@example.com/i)).toBeVisible();
  });

  test("register page rejects self-registration as admin (client blocks it)", async ({ page }) => {
    await page.goto("/register");
    // Role toggle only exposes Candidate + Employer buttons — Admin is not
    // an option. This is defence-in-depth: the backend also rejects.
    const roleButtons = page.getByRole("button").filter({ hasText: /candidate|employer/i });
    await expect(roleButtons).toHaveCount(2);
    await expect(page.getByRole("button", { name: /admin/i })).toHaveCount(0);
  });
});
