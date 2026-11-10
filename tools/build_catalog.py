"""Build data/catalog.json from the raw channel lists, the dates, the grouping rules and tools/books.json.

Usage: python3 -I tools/build_catalog.py
"""
import json, os, re, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from rules import BOOKS, classify, guess, norm, UNTITLED

ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'data', 'raw')
cfg = json.load(open(os.path.join(HERE, 'books.json'), encoding='utf-8'))
dates = json.load(open(os.path.join(RAW, 'dates.json')))
META = {k: (d, c) for k, d, c, _ in BOOKS}
META['untitled'] = ('بثوث بلا عنوان', 'متفرقات')
META['misc'] = ('دروس ومقاطع متفرقة', 'متفرقات')
AR = str.maketrans('0123456789', '٠١٢٣٤٥٦٧٨٩')

def secs(badge):
    try:
        p = [int(x) for x in badge.split(':')]
    except Exception:
        return 0
    s = 0
    for x in p: s = s * 60 + x
    return s

BOILER = [r'"?\s*قناة الشيخ عمر.*?الرسمية\s*"?\s*(بثًا|بثا)?\s*(مباشرًا|مباشرا|مباشر)?ا?', r'لفضيلة\s*الشيخ\s*[:/]?\s*عمر.*?(حفظه الله|الحركان)\.?',
           r'(شرح|للشيخ|الشيخ)\s*عمر بن ح.?م.?د الح.?ر.?ك.?ان\s*(حفظه الله|حفظك الله)?\.?', r'\|\s*الشيخ عمر بن حمد الحركان حفظه الله', r'^\s*(بدأت|ستبدأ|بدأ)\s*(قناة)?\s*', r'"?\s*قناة الشيخ.{0,25}?الرسمية\s*"?', r'حفظ(ه|ك) الله\s*[.،,]?', r'(فضيلة\s*)?الشيخ\s*[:/]?\s*عمر\s*(بن\s*حَ?مَ?د\s*)?الحَ?رْ?كان', r'(اليوم\s*)?(في\s*)?سلس(ل)?[ةه]\s*(يوم\s*)?من التاريخ\s*[؛،,.]?\s*(اليوم)?\s*[\d٠-٩]*\s*\.?', r'^\s*[،,]\s*']
def topic(title, key, num):
    """A short lesson name: the title without the channel boilerplate, the book's name, the lesson number and dates."""
    t = title
    for b in BOILER: t = re.sub(b, ' ', t)
    t = re.sub(r'[‎‏￼]', '', t)
    t = re.sub(r'\d{1,2}\s*/\s*\d{1,2}\s*/\s*14\d\d|14\d\d\s*/\s*\d{1,2}\s*/\s*\d{1,2}\s*هـ?', '', t.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789')))
    parts = [p.strip(' .-–؛;:"«»،,') for p in re.split(r'[|؛;"«»]|\s-\s', t)]
    out = []
    for p in parts:
        if not p: continue
        n = norm(p)
        rx = next((r for k, d, c, r in BOOKS if k == key), None)
        if rx and re.search(rx, n):
            p = re.sub(r'^(?:الدرس|درس|اعادة الدرس)?\s*\d*\s*(?:في|من)?\s*', '', p)
            words = re.sub(rx, '', n).strip(' .')
            if len(words) < 3: continue
            p = re.sub(r'^.*?(شرح السنة ?للبربهاري|السنة ?للبربهاري|البخاري|التوحيد|السيرة ?الرحيق|الرحيق المختوم|تفسير ?ابن سعدي|أخصر ?المختصرات|اللمعة|الشبراوية|منظومة ?الآداب|الآداب|زاد المستقنع|رياض الصالحين)\s*[.؛:]?\s*', '', p)
        p = re.sub(r'^(الدرس|درس|اليوم|الحلقة|المجلس)\s*\d+\s*(في|من)?\s*', '', p).strip(' .')
        if re.fullmatch(r'[\d\s()\-.]*', p) or len(p) < 2: continue
        if p.count('(') != p.count(')'): p = p.replace('(', '').replace(')', '')
        out.append(p)
    s = ' · '.join(out[:2]).strip()
    s = re.sub(r'للشيخ\s*عمر\s*الحركان|·\s*شرح$|\bقناة$|-?\s*سلسلة دروس قد افلح من تزكى', '', s)
    s = re.sub(r'(14\d\d|\d{1,2})\s*[/\\]\s*\d{1,2}\s*[/\\]\s*(\d{1,4})', '', s)
    s = re.sub(r'^[،,\s]*(الدرس|المجلس)\s*[\(\[]?\s*[\d]+\s*[\)\]]?\s*', '', s)
    s = re.sub(r'^[\[(]?المجلس [^\])]*[\])]?\s*$', '', s)
    bt = META.get(key, ('', ''))[0]
    if bt and s.startswith(bt): s = s[len(bt):].lstrip(' :.·،')
    s = re.sub(r'\s+', ' ', s)
    return s.translate(AR)

rows = []
for tab in ('streams', 'videos'):
    for x in json.load(open(os.path.join(RAW, tab + '_flat.json'), encoding='utf-8')):
        key, num = classify(x['t'])
        guessed = False
        if not key:
            if UNTITLED.match(norm(x['t'])): key = 'untitled'
            else:
                key, num = guess(x['t'])
                guessed = bool(key)
                key = key or 'misc'
        key = cfg['moves'].get(x['id'], key)
        rows.append({'id': x['id'], 'title': x['t'].strip(), 'key': key, 'num': num, 'guessed': guessed,
                     'dur': secs((x.get('badge') or ['0'])[0]), 'date': dates.get(x['id'], ''), 'live': tab == 'streams'})

today = datetime.date.today().isoformat()
books = {}
for r in rows:
    books.setdefault(r['key'], []).append(r)

out_books = []
for key, items in books.items():
    c = cfg['books'].get(key, {})
    if c.get('hidden'): continue
    title, cat = META.get(key, (key, 'متفرقات'))
    cat = cfg['catmap'].get(cat, cat)
    title = c.get('title', title)
    splits = c.get('split') or [{'from': '0000-00-00', 'label': ''}]
    exps = []
    left = sorted(items, key=lambda r: r['date'])
    for sp in splits:
        mine = [r for r in left if r['date'] >= sp['from']]
        left = [r for r in left if r['date'] < sp['from']]
        if not mine: continue
        numbered = all(r['num'] for r in mine) and key not in ('misc', 'untitled')
        mine.sort(key=lambda r: ((r['num'] or 0), r['date']) if numbered else (r['date'], r['id']))
        if key not in ('misc', 'khutbah', 'lecture', 'untitled'):  # a re-upload of a lesson that was also streamed live: keep the live one
            seen, keep = {}, []
            for r in sorted(mine, key=lambda r: not r['live']):
                if r['num'] and r['num'] in seen: continue
                if r['num']: seen[r['num']] = 1
                keep.append(r)
            mine = sorted(keep, key=lambda r: ((r['num'] or 0), r['date']) if numbered else (r['date'], r['id']))
        lessons = []
        for i, r in enumerate(mine):
            n = r['num'] if (numbered or (r['num'] and key not in ('misc','khutbah','lecture'))) else i + 1
            t = topic(r['title'], key, r['num']) if key not in ('misc',) else re.sub(r'\s+', ' ', re.sub(BOILER[0], ' ', r['title'])).strip()
            lessons.append([r['id'], n, t, r['dur'], r['date']])
        exps.append({'label': sp['label'], 'from': mine[0]['date'], 'to': mine[-1]['date'], 'lessons': lessons})
    last = max((e['to'] for e in exps), default='')
    days = (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(last)).days if last else 999
    out_books.append({'id': key, 'title': title, 'cat': cat, 'author': c.get('author', ''),
                      'ongoing': days <= 45 and key not in ('misc', 'khutbah', 'lecture'),
                      'count': sum(len(e['lessons']) for e in exps), 'last': last, 'exps': exps})

order = {c: i for i, c in enumerate(cfg['cats'])}
out_books.sort(key=lambda b: (order.get(b['cat'], 99), -b['count']))
cat_out = [{'name': c, 'count': sum(b['count'] for b in out_books if b['cat'] == c)} for c in cfg['cats']]
latest = sorted((r for r in rows if not cfg['books'].get(r['key'], {}).get('hidden')), key=lambda r: r['date'], reverse=True)[:12]
catalog = {'updated': today, 'channel': 'https://www.youtube.com/@omaralharkan',
           'cats': [c for c in cat_out if c['count']], 'books': out_books,
           'latest': [[r['id'], r['key']] for r in latest]}
json.dump(catalog, open(os.path.join(ROOT, 'data', 'catalog.json'), 'w', encoding='utf-8'), ensure_ascii=False, separators=(',', ':'))
print(len(out_books), 'series,', sum(b['count'] for b in out_books), 'lessons')

# feed.xml: the newest lessons, for RSS readers and «تابع الجديد»
SITE = os.environ.get('SITE_URL', 'https://omaralharkan.pages.dev/').rstrip('/') + '/'
from xml.sax.saxutils import escape as x
by_id = {l[0]: (b, l) for b in out_books for e in b['exps'] for l in e['lessons']}
newest = sorted(by_id.values(), key=lambda bl: bl[1][4], reverse=True)[:40]
items = ''.join(f"""<item><title>{x(b['title'])} · {x(l[2] or 'الدرس ' + str(l[1]).translate(AR))}</title><link>{SITE}#/book/{b['id']}</link>
<guid isPermaLink="false">{l[0]}</guid><pubDate>{datetime.datetime.fromisoformat(l[4]).strftime('%a, %d %b %Y 12:00:00 +0300')}</pubDate>
<enclosure url="https://www.youtube.com/watch?v={l[0]}" type="text/html" length="0"/></item>""" for b, l in newest if l[4])
open(os.path.join(ROOT, 'feed.xml'), 'w', encoding='utf-8').write(f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>دروس الشيخ عمر بن حمد الحركان — الجديد</title><link>{SITE}</link>
<description>أحدث دروس فضيلة الشيخ عمر بن حمد الحركان</description><language>ar</language>{items}</channel></rss>
""")
