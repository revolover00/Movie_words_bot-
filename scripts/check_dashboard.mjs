// Live unauthenticated endpoint check plus authenticated browser integration
// against the actual handler and database. No test password leaves this process.
import assert from "node:assert/strict";
import { createServer } from "node:http";
import { randomBytes, createHash } from "node:crypto";
import { chromium } from "playwright";
import handler from "../api/dashboard.js";
const password = randomBytes(32).toString("hex");
process.env.DASHBOARD_PASSWORD_HASH = createHash("sha256")
  .update(password)
  .digest("hex");
const denied = await fetch(
  "https://scenelingoo.vercel.app/api/dashboard?data=1",
);
assert.equal(denied.status, 401);
const server = createServer((req, res) => {
  req.query = Object.fromEntries(
    new URL(req.url, "http://localhost").searchParams,
  );
  res.status = (code) => {
    res.statusCode = code;
    return res;
  };
  res.send = (data) => res.end(data);
  res.json = (data) => {
    res.setHeader("Content-Type", "application/json");
    res.end(JSON.stringify(data));
  };
  handler(req, res).catch(() => {
    res.statusCode = 500;
    res.end("Handler failure");
  });
});
await new Promise((resolve) => server.listen(0, "127.0.0.1", resolve));
const base = `http://127.0.0.1:${server.address().port}`;
const browser = await chromium.launch({ headless: true });
try {
  const context = await browser.newContext({
    httpCredentials: { username: "admin", password },
  });
  const response = await context.request.get(base + "/api/dashboard?data=1");
  assert.equal(response.status(), 200);
  const data = await response.json();
  for (const key of ["total", "active", "setup", "stopped", "due"])
    assert.equal(typeof data[key], "number");
  assert.equal(data.total, data.active + data.setup + data.stopped);
  assert.ok(data.due <= data.active);
  for (const key of ["ready", "media_bytes", "media_items"])
    assert.equal(typeof data.preparation[key], "number");
  assert.ok(Array.isArray(data.preparation.runs));
  assert.ok(Array.isArray(data.subscribers.rows));
  assert.ok(data.subscribers.rows.length <= 50);
  assert.ok(!JSON.stringify(data).includes(process.env.BOT_TOKEN));
  const page = await context.newPage();
  const errors = [];
  page.on("pageerror", (error) => errors.push(error.message));
  await page.goto(base);
  await page.waitForFunction(
    () => document.querySelectorAll("#cards .card").length === 5,
  );
  assert.equal(await page.locator("#error").isVisible(), false);
  await page.getByRole("tab", { name: "المشتركون", exact: true }).click();
  assert.equal(await page.locator("#subscriber-search").isVisible(), true);
  assert.ok(
    await page.locator("#subscribers table, #subscribers .empty").count(),
  );
  await page.locator("#subscriber-search").fill("no-match-test-unique-76432");
  await page.locator("#subscriber-find").click();
  await page.waitForFunction(() =>
    document.querySelector("#subscriber-page").textContent.includes("0 مشترك"),
  );
  await page.locator("#subscriber-search").fill("");
  await page.locator("#subscriber-find").click();
  await page.waitForFunction(
    () => !document.querySelector("#refresh").disabled,
  );
  await page.getByRole("button", { name: "تحديث البيانات ↻" }).click();
  await page.waitForFunction(
    () => !document.querySelector("#refresh").disabled,
  );
  await page.setViewportSize({ width: 390, height: 844 });
  assert.equal(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
    true,
  );
  for (const name of [
    "نظرة عامة",
    "المشتركون",
    "التشغيل والسجلات",
    "المحتوى والاستخدام",
  ]) {
    await page.getByRole("tab", { name, exact: true }).click();
    assert.equal(
      await page
        .getByRole("tab", { name, exact: true })
        .getAttribute("aria-selected"),
      "true",
    );
    assert.equal(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= window.innerWidth,
      ),
      true,
    );
  }
  await page.getByRole("tab", { name: "نظرة عامة", exact: true }).click();
  await page
    .getByRole("tab", { name: "نظرة عامة", exact: true })
    .press("ArrowLeft");
  assert.equal(
    await page
      .getByRole("tab", { name: "المشتركون", exact: true })
      .getAttribute("aria-selected"),
    "true",
  );
  assert.deepEqual(errors, []);
  console.log(
    "::notice title=Dashboard smoke::Production rejects unauthenticated access. Actual handler integration passed private auth, real database aggregates, desktop render, refresh and mobile layout.",
  );
} finally {
  await browser.close();
  server.close();
}
