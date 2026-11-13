# دروس الشيخ عمر بن حمد الحركان

A calm, fast front end for the lessons on the Sheikh's YouTube channel (https://www.youtube.com/@omaralharkan):
every live stream and video grouped into books (المتون) and lessons, with search, resume, playback speed,
a listen mode, and an RSS feed of new lessons. No build step: `index.html`, `styles.css`, `app.js` and `data/catalog.json`.

## How the data is made
1. `tools/crawl.py` lists the channel into `data/raw/` (titles, lengths, dates). With a `YOUTUBE_API_KEY` it uses the
   YouTube Data API; without one it reads the channel's public pages.
2. `tools/build_catalog.py` groups the videos into books using `tools/rules.py` (one pattern per book) and
   `tools/books.json` (display names, authors, sections, hidden series, and hand placements), then writes
   `data/catalog.json` and `feed.xml`.

### Fixing where a lesson appears
- A video in the wrong book, or left in «متفرقات»: add `"<video id>": "<book key>"` under `moves` in `tools/books.json`.
- A whole new series: add a line to `BOOKS` in `tools/rules.py` (key, title, section, title pattern).
- Hide a series: `"hidden": true` under its key in `tools/books.json`.
- A wrong lesson number: `"<video id>": <number>` (or `null`) under `nums`; a bad lesson name: `"<video id>": "<name>"` under `titles`.
- A book taught more than once is split into separate series automatically (numbering restarts after a break of more than
  30 days). To set the split dates by hand instead, give the book a `split` list in `tools/books.json`.
Then run `python3 -I tools/build_catalog.py` (or let the daily job do it).

## Daily sync
`.github/workflows/sync.yml` runs every day at 22:00 Riyadh time and on demand (Actions → Daily lessons sync → Run workflow).
Add the API key once: Settings → Secrets and variables → Actions → New repository secret → `YOUTUBE_API_KEY`.
Optionally set an Actions variable `SITE_URL` (e.g. `https://omaralharkan.com/`) for the RSS links.

## Cloudflare Pages
Workers & Pages → Create → Pages → Connect to Git → this repo.
- Production branch: `main`
- Framework preset: None · Build command: `python3 -I tools/build_site.py` · Build output directory: `_site`
- Environment variables: `SITE_URL` = the canonical address (e.g. `https://omaralharkan.com/`), optional `GSC_VERIFICATION` = the Search Console HTML-tag token
Every push (including the daily sync's commits) redeploys. `_headers` sets the security headers, including a
Content-Security-Policy that allows only this site, Google Fonts and YouTube; a new outside service must be added there.

## Share images
`og/` holds the 1200×630 pictures shown when a page is shared (one for the site, one per book). After adding a book, run
`node tools/make_share_images.js` (needs Playwright) and commit `og/`. A book without a picture uses `og/site.jpg`.

## Addresses (no # anywhere)
`/` · `/book/<key>/` · `/book/<key>/2/` (a book's second explanation) · `/search/?q=` · `/mine/`.
`tools/build_site.py` writes a real page for each address with its own title, description, canonical link and the lesson list
pre-rendered, plus `sitemap.xml` and `robots.txt` (search and «ما أتابعه» are noindex). Submit `sitemap.xml` in Search Console.

## Upload without GitHub
`python3 -I tools/build_site.py` then zip the *contents* of `_site/` and upload it in Cloudflare (Pages → Upload assets).

## Local preview
`python3 -I tools/build_site.py && cd _site && python3 -m http.server`, then open http://localhost:8000.
