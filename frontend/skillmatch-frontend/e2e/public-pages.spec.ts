import { test, expect } from "@playwright/test";

/**
 * Public pages — no auth required. Verifies each unauthenticated route
 * renders its shell without error and the primary nav links are wired.
 */

test.describe("public pages", () => {
  test("home page renders with SkillMatch brand", async ({ page }) => {
    await page.goto("/");
    // The home page uses a SectionHeading/PageHeader — checking the <title>
    // and a stable visible element (Logo link/nav) is enough to prove render.
    await expect(page).toHaveTitle(/SkillMatch/i);
    // Nav "Find Jobs" link is present for anonymous users
    await expect(page.getByRole("link", { name: /find jobs/i })).toBeVisible();
    // "Get Started" CTA (register) present
    await expect(page.getByRole("link", { name: /get started/i })).toBeVisible();
  });

  test("login page shows required fields + Forgot password link", async ({ page }) => {
    await page.goto("/login");
    await expect(page.getByLabel(/email address/i)).toBeVisible();
    await expect(page.getByLabel(/password/i)).toBeVisible();
    await expect(page.getByRole("button", { name: /sign in/i })).toBeVisible();
    // The Forgot-password link we just added must be present.
    await expect(page.getByRole("link", { name: /forgot password/i })).toBeVisible();
  });

  test("register page renders with role toggle", async ({ page }) => {
    await page.goto("/register");
    await expect(page.getByLabel(/email/i)).toBeVisible();
    // Role toggle (aria-pressed on Candidate/Employer buttons)
    const candidateBtn = page.getByRole("button", { name: /candidate/i });
    const employerBtn  = page.getByRole("button", { name: /employer/i });
    await expect(candidateBtn).toBeVisible();
    await expect(employerBtn).toBeVisible();
  });

  test("forgot-password page renders", async ({ page }) => {
    await page.goto("/forgot-password");
    await expect(page.getByRole("heading", { name: /forgot your password/i })).toBeVisible();
    await expect(page.getByRole("button", { name: /send reset link/i })).toBeVisible();
  });

  test("verify-email page renders an error state without valid params", async ({ page }) => {
    await page.goto("/verify-email");
    // Missing uid/token => the page shows the error branch immediately.
    await expect(page.getByRole("heading", { name: /couldn.t verify/i })).toBeVisible();
  });

  test("privacy page renders", async ({ page }) => {
    await page.goto("/privacy");
    // Any heading — we're just checking the page ships and doesn't crash.
    await expect(page.locator("h1, h2").first()).toBeVisible();
  });

  test("not-found renders custom 404 for unknown routes", async ({ page }) => {
    const res = await page.goto("/definitely-not-a-real-page");
    expect(res?.status()).toBe(404);
    // The custom not-found ships "Home" and "Browse jobs" CTAs.
    await expect(page.getByRole("link", { name: /home/i })).toBeVisible();
  });
});
