// Capture the website screenshots shown in the "site" scene: node video/shots.js
// Writes video/build/shots/{search,practices,timer,journal}.png.
// Needs a static server on :8765 at the repo root (python3 -m http.server 8765).
const fs = require("fs");
const { chromium } = require("playwright");
const OUT = `${__dirname}/build/shots`, B = "http://localhost:8765/";
fs.mkdirSync(OUT, { recursive: true });
(async () => {
  const b = await chromium.launch();
  const ctx = await b.newContext({ viewport: { width: 1440, height: 900 }, deviceScaleFactor: 1.5 });
  const p = await ctx.newPage();
  const shot = (n) => p.screenshot({ path: `${OUT}/${n}.png` });
  // search
  await p.goto(B + "chapter-3.html", { waitUntil: "networkidle" });
  await p.click(".search-btn"); await p.waitForTimeout(400);
  await p.keyboard.type("psychological safety", { delay: 20 }); await p.waitForTimeout(800);
  await p.keyboard.press("ArrowDown"); await p.keyboard.press("ArrowDown"); await p.waitForTimeout(300);
  await shot("search");
  // practices
  await p.goto(B + "practices.html", { waitUntil: "networkidle" }); await p.waitForTimeout(500);
  await p.evaluate(() => { const f = document.querySelector("main button, .filters, [class*=filter]"); scrollTo(0, f.getBoundingClientRect().top + scrollY - 100); }); await p.waitForTimeout(300); await shot("practices");
  // timer
  await p.goto(B + "chapter-2.html", { waitUntil: "networkidle" });
  const btn = p.locator(".timer-btn").first();
  await btn.evaluate((el) => { const h = el.closest("section")?.querySelector("h2") || el; scrollTo(0, h.getBoundingClientRect().top + scrollY - 120); });
  await p.waitForTimeout(300);
  await btn.evaluate((el) => el.click()); await p.waitForTimeout(3300);
  await shot("timer");
  // journal
  await p.goto(B + "journal.html", { waitUntil: "networkidle" });
  await p.evaluate(() => localStorage.setItem("reflect:ch1-q1", JSON.stringify("The kitchens are empty and our meetings are full of slides. We rarely talk about what really matters to the people we serve.")));
  await p.reload({ waitUntil: "networkidle" }); await p.waitForTimeout(500);
  await p.locator('[data-qid="ch1-q1"]').evaluate((el) => scrollTo(0, el.closest(".journal-ch").querySelector("h2,h3").getBoundingClientRect().top + scrollY - 110));
  await p.locator('[data-qid="ch1-q2"] button.reflect').click(); await p.waitForTimeout(400);
  await p.evaluate(() => document.activeElement?.blur()); await p.waitForTimeout(200);
  await shot("journal");
  await b.close();
})();
