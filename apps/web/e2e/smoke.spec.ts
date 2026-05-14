import { test, expect } from "@playwright/test";

/**
 * Smoke suite — exercises the key pages without needing a live API.
 * Network calls to http://localhost:8000 are automatically handled by
 * the app (they will surface loading/error states, which we tolerate).
 */

test.describe("Home page", () => {
  test("loads without JS errors and shows the app name", async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(e.message));

    await page.goto("/");
    // App shell must be present
    await expect(page).toHaveTitle(/LLM Insight Studio/i);
    // No unhandled JS exceptions
    expect(errors).toHaveLength(0);
  });

  test("navigation links are reachable", async ({ page }) => {
    await page.goto("/");
    // Check that the datasets, experiments, compare and reports nav links exist
    for (const href of ["/datasets", "/experiments", "/compare", "/reports"]) {
      const link = page.locator(`a[href="${href}"]`).first();
      await expect(link).toBeVisible();
    }
  });
});

test.describe("Datasets page", () => {
  test("renders the dataset import section", async ({ page }) => {
    await page.goto("/datasets");
    // Hugging Face import card heading
    await expect(page.getByText(/Hugging Face dataset/i)).toBeVisible();
  });
});

test.describe("Experiments page", () => {
  test("renders the experiment wizard", async ({ page }) => {
    await page.goto("/experiments/new");
    // Wizard must show the lane selection
    await expect(page.getByText(/Task lanes/i)).toBeVisible();
  });
});

test.describe("Compare page", () => {
  test("renders without crashing", async ({ page }) => {
    await page.goto("/compare");
    // Must render — even an empty/error state is acceptable for smoke
    await expect(page).not.toHaveURL(/error/i);
  });
});

test.describe("Reports page", () => {
  test("renders without crashing", async ({ page }) => {
    await page.goto("/reports");
    await expect(page).not.toHaveURL(/error/i);
  });
});
