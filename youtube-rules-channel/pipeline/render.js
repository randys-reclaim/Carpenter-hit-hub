// Render HTML snippets to PNG with the preinstalled Playwright Chromium.
// Usage: node render.js jobs.json   (jobs: [{html, out, w, h}])
const fs = require('fs');
const { chromium } = require('playwright');
const FONTS = '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800;900&family=JetBrains+Mono:wght@500&display=block" rel="stylesheet">';
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8')).filter(j => !fs.existsSync(j.out));
  const browser = await chromium.launch();
  const workers = 4;
  let next = 0, done = 0;
  async function worker() {
    const page = await browser.newPage();
    await page.setContent(`<html><head>${FONTS}<style>body{margin:0;background:#0B0B0C}</style></head><body><div id="root"></div></body></html>`);
    await page.evaluate(() => document.fonts.ready);
    while (next < jobs.length) {
      const j = jobs[next++];
      await page.setViewportSize({ width: j.w, height: j.h });
      await page.evaluate(h => { document.getElementById('root').innerHTML = h; return document.fonts.ready; }, j.html);
      await page.screenshot({ path: j.out, clip: { x: 0, y: 0, width: j.w, height: j.h } });
      if (++done % 50 === 0) console.log(`  rendered ${done}/${jobs.length}`);
    }
  }
  await Promise.all(Array.from({ length: workers }, worker));
  await browser.close();
  console.log(`  rendered ${done} images`);
})();
