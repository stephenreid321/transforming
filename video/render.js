// Render stage.html to JPEG frames: node video/render.js <worker> <workers>
// Needs a static server on :8765 at the repo root (python3 -m http.server 8765).
const { chromium } = require("playwright");
const FPS = 30;
(async () => {
  const [w, n] = [+(process.argv[2] || 0), +(process.argv[3] || 1)];
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1920, height: 1080 } });
  await p.goto("http://localhost:8765/video/stage.html?render", { waitUntil: "networkidle" });
  await p.evaluate(() => window.ready);
  const total = await p.evaluate(() => TOTAL);
  const frames = Math.ceil(total * FPS);
  const per = Math.ceil(frames / n);
  for (let f = w * per; f < Math.min(frames, (w + 1) * per); f++) {
    await p.evaluate((t) => render(t), f / FPS);
    await p.screenshot({ path: `${__dirname}/build/frames/${String(f).padStart(5, "0")}.jpg`, type: "jpeg", quality: 93 });
  }
  console.log("worker", w, "done", frames);
  await b.close();
})();
