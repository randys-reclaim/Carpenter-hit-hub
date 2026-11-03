// Like render.js, but a job with "alpha": true is captured with a transparent background (for overlays).
// Usage: node render_alpha.js jobs.json   (jobs: [{html, out, w, h, alpha}])
const fs = require('fs');
const { chromium } = require('playwright');
const FONTS = '<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@500;700;800;900&family=JetBrains+Mono:wght@500&display=block" rel="stylesheet">';
(async () => {
  const jobs = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.setContent(`<html><head>${FONTS}<style>html,body{margin:0;background:transparent}</style></head><body><div id="root"></div></body></html>`);
  await page.evaluate(() => document.fonts.ready);
  for (const j of jobs) {
    await page.setViewportSize({ width: j.w, height: j.h });
    await page.evaluate(h => { document.getElementById('root').innerHTML = h; return document.fonts.ready; }, j.html);
    await page.screenshot({ path: j.out, clip: { x: 0, y: 0, width: j.w, height: j.h }, omitBackground: !!j.alpha });
  }
  await browser.close();
})();
