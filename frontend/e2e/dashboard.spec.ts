import { test, expect } from "@playwright/test";

test.describe("Dashboard", () => {
  test("shows empty state on load", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Stock Adviser")).toBeVisible();
    await expect(
      page.getByText("Ask the agent about any stock to get started")
    ).toBeVisible();
  });

  test("chat panel is visible with placeholder", async ({ page }) => {
    await page.goto("/");
    await expect(page.getByText("Agent", { exact: true })).toBeVisible();
    await expect(
      page.getByPlaceholder("Ask about a stock...")
    ).toBeVisible();
  });

  test("can type and send a message", async ({ page }) => {
    await page.goto("/");
    const input = page.getByPlaceholder("Ask about a stock...");
    await input.fill("What is the price of AAPL?");
    await page.getByRole("button", { name: "Send" }).click();

    // User message should appear in chat
    await expect(
      page.getByText("What is the price of AAPL?")
    ).toBeVisible();

    // Input should be cleared
    await expect(input).toHaveValue("");
  });

  test("chat panel collapses and expands", async ({ page }) => {
    await page.goto("/");

    // Close chat
    await page.getByText("»").click();
    await expect(
      page.getByPlaceholder("Ask about a stock...")
    ).not.toBeVisible();

    // Reopen chat
    await page.getByText("«").click();
    await expect(
      page.getByPlaceholder("Ask about a stock...")
    ).toBeVisible();
  });

  test("full flow: send message, see agent response and stock tab", async ({
    page,
  }) => {
    // This test requires the backend to be running on port 8881
    // Skip if backend is not available
    test.skip(
      !(await fetch("http://127.0.0.1:8881/health")
        .then((r) => r.ok)
        .catch(() => false)),
      "Backend not running on port 8881"
    );

    await page.goto("/");
    const input = page.getByPlaceholder("Ask about a stock...");
    await input.fill("What is the price of AAPL?");
    await page.getByRole("button", { name: "Send" }).click();

    // Wait for agent to respond (up to 30s)
    await expect(page.locator('[class*="bg-gray-800/50"]').first()).toBeVisible(
      { timeout: 30000 }
    );

    // A stock tab should appear in the tab bar
    await expect(
      page.locator('[class*="rounded-t-lg"]', { hasText: "AAPL" })
    ).toBeVisible({ timeout: 30000 });
  });
});
