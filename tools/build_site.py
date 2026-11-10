"""Write the deployable site to _site/: one real HTML page per address (no # in any URL), each with its own
title, description, canonical link and pre-rendered content for search engines, plus sitemap.xml and robots.txt.
app.js takes over in the browser and moves between pages without reloading (so the player keeps playing).

Usage: python3 -I tools/build_site.py [--out _site]
Canonical address: SITE_URL (default https://omaralharkan.pages.dev/).
"""
import json, os, re, shutil, sys, html
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(ROOT, '_site')
SITE = os.environ.get('SITE_URL', 'https://omaralharkan.pages.dev/').rstrip('/') + '/'
VERIFY = os.environ.get('GSC_VERIFICATION', '').strip()
C = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
TPL = open(os.path.join(ROOT, 'index.html'), encoding='utf-8').read()
AR = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')
e = lambda s: html.escape(str(s), quote=True)
NAME = 'دروس الشيخ عمر بن حمد الحركان'

def dars(n):
    return 'درس واحد' if n == 1 else 'درسان' if n == 2 else f'{str(n).translate(AR)} دروس' if n <= 10 else f'{str(n).translate(AR)} درساً'

def page(path, title, desc, hero, body, index=True):
    url = SITE + path
    head = (f'<link rel="canonical" href="{e(url)}">\n<meta property="og:type" content="website">\n<meta property="og:title" content="{e(title)}">\n'
            f'<meta property="og:description" content="{e(desc)}">\n<meta property="og:url" content="{e(url)}">\n<meta property="og:locale" content="ar_SA">\n'
            + ('' if index else '<meta name="robots" content="noindex,follow">\n')
            + (f'<meta name="google-site-verification" content="{e(VERIFY)}">\n' if VERIFY else ''))
    s = TPL.replace('<title>دروس الشيخ عمر بن حمد الحركان</title>', f'<title>{e(title)}</title>')
    s = re.sub(r'<meta name="description" content="[^"]*">', lambda m: f'<meta name="description" content="{e(desc)}">', s, count=1)
    s = s.replace('</head>', head + '</head>', 1)
    s = s.replace('<div id="heroSlot"></div>', f'<div id="heroSlot">{hero}</div>', 1)
    s = s.replace('<main id="main" class="wrap" tabindex="-1"></main>', f'<main id="main" class="wrap" tabindex="-1">{body}</main>', 1)
    d = os.path.join(OUT, path)
    os.makedirs(d, exist_ok=True)
    open(os.path.join(d, 'index.html'), 'w', encoding='utf-8').write(s)
    return url

if os.path.exists(OUT): shutil.rmtree(OUT)
os.makedirs(OUT)
urls = []

# home
cards = ''.join(f'<li><a href="/book/{b["id"]}/">{e(b["title"])}</a> ({dars(b["count"])})</li>' for b in C['books'])
urls.append(page('', NAME, 'شروح المتون العلمية لفضيلة الشيخ عمر بن حمد الحركان: كتاب التوحيد، صحيح البخاري، شرح السنة للبربهاري، الرحيق المختوم وغيرها، مرتبة كتاباً كتاباً مع الاستماع والمتابعة.',
                 f'<div class="hero"><div class="who"><small>دروس فضيلة الشيخ</small><h1>عمر بن حَمَد الحَرْكان</h1></div></div>',
                 f'<section class="block"><h2>الشروح</h2><ul>{cards}</ul></section>'))

# one page per book, and per explanation when a book was explained more than once
for b in C['books']:
    for ei, x in enumerate(b['exps']):
        path = f'book/{b["id"]}/' + (f'{ei + 1}/' if ei else '')
        label = f' ({x["label"]})' if x['label'] else ''
        lis = ''.join(f'<li>{str(l[1]).translate(AR)}. <a href="https://www.youtube.com/watch?v={l[0]}" rel="noopener">{e(l[2] or "الدرس " + str(l[1]).translate(AR))}</a></li>' for l in x['lessons'])
        topics = '، '.join(l[2] for l in x['lessons'][-6:] if l[2])
        desc = f'{b["title"]}{label}: {dars(len(x["lessons"]))} لفضيلة الشيخ عمر بن حمد الحركان' + (f'، منها: {topics}' if topics else '') + '.'
        urls.append(page(path, f'{b["title"]}{label} | {NAME}', desc[:300],
                         f'<div class="sub-hero"><div class="k">{e(b["cat"])}</div><h1>{e(b["title"])}</h1>' + (f'<div class="a">{e(b["author"])}</div>' if b['author'] else '') + '</div>',
                         f'<div class="panel"><ol class="lessons">{lis}</ol></div>'))

page('search/', f'البحث | {NAME}', 'ابحث في دروس الشيخ عمر بن حمد الحركان.', '', '', index=False)
page('mine/', f'ما أتابعه | {NAME}', 'الدروس التي تتابعها على هذا الجهاز.', '', '', index=False)
nf = TPL.replace('<title>دروس الشيخ عمر بن حمد الحركان</title>', f'<title>الصفحة غير موجودة | {NAME}</title>').replace('</head>', '<meta name="robots" content="noindex">\n</head>', 1)
open(os.path.join(OUT, '404.html'), 'w', encoding='utf-8').write(nf)

for f in ('styles.css', 'app.js', 'feed.xml', '_headers'):
    shutil.copy(os.path.join(ROOT, f), OUT)
os.makedirs(os.path.join(OUT, 'data'))
shutil.copy(os.path.join(ROOT, 'data', 'catalog.json'), os.path.join(OUT, 'data'))
open(os.path.join(OUT, 'robots.txt'), 'w').write(f'User-agent: *\nAllow: /\nDisallow: /search/\nDisallow: /mine/\nSitemap: {SITE}sitemap.xml\n')
last = {b['id']: b['last'] for b in C['books']}
sm = ''.join(f'<url><loc>{e(u)}</loc>' + (f'<lastmod>{last.get(u[len(SITE):].split("/")[1] if "/book/" in u else "", C["updated"]) or C["updated"]}</lastmod>') + '</url>' for u in urls)
open(os.path.join(OUT, 'sitemap.xml'), 'w', encoding='utf-8').write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{sm}</urlset>\n')
print(f'{len(urls)} pages in sitemap, written to {OUT}')
