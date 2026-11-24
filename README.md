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

## Telegram: audio, lesson ranges and book texts
The Sheikh's Telegram channel (https://t.me/omaralharkan) posts, for each lesson, the YouTube live link, an audio file
and a card naming the book, lesson number, verses or hadith numbers and the Hijri date. The site uses it three ways:
- Each lesson the channel posted gets a Telegram button (its audio post), and its verses / hadith range under the title (searchable).
- Book pages offer the book's text (PDF) when the channel posted one.
- With the audio copied to Cloudflare R2, the player plays the lesson's own audio file instead of the YouTube video:
  it keeps playing with the screen locked, has a «تنزيل» button, and every book with audio gets a podcast feed at
  `/feeds/<book>.xml` (`feed.xml` carries the audio too). «عرض المرئي» still switches to the video at the same moment.

How the data is made:
1. `tools/telegram.py` reads the public page t.me/s/omaralharkan (no login) into `data/raw/telegram.json`.
   `python3 -I tools/telegram.py --seed result.json` rebuilds it from a Telegram Desktop export (JSON).
2. `tools/tg_match.py` joins posts to lessons: by the card's YouTube and Telegram links first, then by the book and lesson
   number in the audio's caption, then by the YouTube link posted just before it. `python3 -I tools/tg_match.py` lists what
   it could not match. A PDF goes to the book its name matches; to place one by hand add `"<post id>": "<book key>"` under `pdfs` in `tools/books.json`.
3. `tools/audio_sync.py` copies each matched audio file and PDF to R2 once and records it in `data/raw/audio.json`.

### Setting up the audio copy (once)
1. Cloudflare → R2 → Create bucket (e.g. `omaralharkan-audio`). In the bucket's Settings → Public access, connect a custom
   domain such as `audio.omaralharkan.com` (or allow the r2.dev address). R2 → Manage API tokens → Create token with
   «Object Read & Write» on that bucket; note the Access Key ID, Secret Access Key and the account ID.
2. https://my.telegram.org → API development tools: create an app, note the API id and hash.
3. On your computer: `pip install telethon && python3 tools/telegram_login.py`, sign in with an account that can see the
   channel (a separate account for the site is best). It prints the session string.
   Instead of an account you can use a bot that is an admin of the channel: put its token in `TG_BOT_TOKEN`.
4. GitHub → Settings → Secrets and variables → Actions:
   - Secrets: `TG_API_ID`, `TG_API_HASH`, `TG_SESSION` (or `TG_BOT_TOKEN`), `R2_ACCOUNT_ID`, `R2_ACCESS_KEY_ID`, `R2_SECRET_ACCESS_KEY`
   - Variables: `R2_BUCKET`, `AUDIO_BASE_URL` (the bucket's public address, ending in `/`)
5. Run the daily job by hand (Actions → Daily lessons sync → Run workflow). The first run copies the 83 files matched
   so far (about 1.1 GB, 29 hours); anything it has no time for follows on the next run. The site's security policy allows `AUDIO_BASE_URL` automatically.

## Daily sync
`.github/workflows/sync.yml` runs every day at 22:00 Riyadh time and on demand (Actions → Daily lessons sync → Run workflow): it lists
the YouTube channel, reads the Telegram channel, builds the catalog, copies new audio to R2 (once set up) and builds again.
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
