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
- A book explained more than once: give it a `split` list in `tools/books.json` (see `tawhid`).
Then run `python3 -I tools/build_catalog.py` (or let the daily job do it).

## Daily sync
`.github/workflows/sync.yml` runs every day at 22:00 Riyadh time and on demand (Actions → Daily lessons sync → Run workflow).
Add the API key once: Settings → Secrets and variables → Actions → New repository secret → `YOUTUBE_API_KEY`.
Optionally set an Actions variable `SITE_URL` (e.g. `https://omaralharkan.com/`) for the RSS links.

## Cloudflare Pages
Workers & Pages → Create → Pages → Connect to Git → this repo.
- Production branch: `main`
- Framework preset: None · Build command: *(empty)* · Build output directory: `/`
Every push (including the daily sync's commits) redeploys. `_headers` sets basic security headers.

## Local preview
`python3 -m http.server` in the repo folder, then open http://localhost:8000.
