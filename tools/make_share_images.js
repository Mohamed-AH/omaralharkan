// Draw the link-preview images (1200x630) shown when a page is shared on WhatsApp, X, Telegram…
// One for the site (og/site.jpg) and one per book (og/<id>.jpg). A book without its own image uses the site one.
// Needs Node and Playwright with Chromium. Run after adding a book:  node tools/make_share_images.js
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const ROOT = path.join(__dirname, '..');
const C = JSON.parse(fs.readFileSync(path.join(ROOT, 'data', 'catalog.json'), 'utf8'));
const OUT = path.join(ROOT, 'og');
fs.mkdirSync(OUT, { recursive: true });
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));

const page = (big, small, top) => `<!doctype html><html lang="ar" dir="rtl"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Aref+Ruqaa:wght@700&family=Amiri:wght@700&family=Alexandria:wght@400;500&display=block" rel="stylesheet">
<style>
html,body{margin:0;width:1200px;height:630px}
body{background-color:#0F2A22;color:#F8F4EA;font-family:Alexandria,sans-serif;
  background-image:radial-gradient(ellipse 70% 60% at 50% 0%,rgba(176,141,87,.28),transparent 70%),repeating-conic-gradient(from 22.5deg at 50% 50%,rgba(176,141,87,.09) 0 12.5%,transparent 0 25%);
  background-size:100% 100%,72px 72px;display:flex;align-items:center;justify-content:center}
.f{position:absolute;inset:28px;border:2px solid rgba(226,199,146,.55);border-radius:28px}
.in{position:relative;text-align:center;padding:0 110px}
.k{font-size:30px;color:#E2C792;font-weight:500;margin-bottom:12px}
h1{margin:0;font-family:${top ? "'Aref Ruqaa'" : 'Amiri'};font-weight:700;font-size:${top ? 112 : big.length > 28 ? 66 : 82}px;line-height:1.35}
.line{width:180px;height:2px;background:#E2C792;margin:30px auto 24px}
.s{font-family:'Aref Ruqaa';font-size:40px;color:#E2C792}
</style></head><body><div class="f"></div><div class="in">
${top ? `<div class="k">${esc(top)}</div>` : ''}<h1>${esc(big)}</h1><div class="line"></div><div class="s">${esc(small)}</div></div></body></html>`;

(async () => {
  const proxy = process.env.HTTPS_PROXY ? { server: process.env.HTTPS_PROXY } : undefined;
  const b = await chromium.launch(proxy ? { proxy } : {});
  const p = await b.newPage({ viewport: { width: 1200, height: 630 } });
  const shot = async (html, file) => {
    await p.setContent(html, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    await p.screenshot({ path: path.join(OUT, file), type: 'jpeg', quality: 82 });
  };
  await shot(page('عمر بن حَمَد الحَرْكان', 'شروح المتون العلمية', 'دروس فضيلة الشيخ'), 'site.jpg');
  for (const bk of C.books) await shot(page(bk.title, 'الشيخ عمر بن حمد الحركان', '').replace('<div class="in">', `<div class="in"><div class="k">${esc(bk.cat)}</div>`), bk.id + '.jpg');
  await b.close();
  console.log(C.books.length + 1, 'images in og/');
})();
