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
           r'(شرح|للشيخ|الشيخ)\s*عمر بن ح.?م.?د الح.?ر.?ك.?ان\s*(حفظه الله|حفظك الله)?\.?', r'\|\s*الشيخ عمر بن حمد الحركان حفظه الله', r'^\s*(بدأت|ستبدأ|بدأ)\s*(قناة)?\s*', r'"?\s*قناة الشيخ.{0,25}?الرسمية\s*"?', r'حفظ(ه|ك) الله\s*[.،,]?', r'(فضيلة\s*)?الشيخ\s*[:/]?\s*عمر\s*(بن\s*حَ?مَ?د\s*)?الحَ?رْ?كان', r'(اليوم\s*)?(في\s*)?سلس(ل)?[ةه]\s*(يوم\s*)?من التاريخ\s*[؛،,.]?\s*(اليوم)?\s*[\d٠-٩]*\s*\.?', r'^\s*[،,]\s*', r'\bالرسمية\b', r'بث(ًا|ا)\s*مباشر(ًا|ا)?', r'[،,]?\s*قناة\s*(ل?(ال)?شيخ\s*)?(عمر\s*)?(بن\s*حَ?مَ?د\s*)?(ال)?حَ?رْ?كان', r'قناة(?=ال)', r'\s+قناة\s*$', r'\bبث(ًا|ا)\b', r'^\s*ت\s+(?=خطبة)', r'(لفضيلة|فضيلة)\s*الشيخ\s*[:/]?\s*عمر\s*(بن\s*حَ?مَ?د\s*)?(ال)?حَ?رْ?كان\s*(حفظه الله)?\.?', r'\s*شرح\s*$', r'حفظة الله']
def clean(title):
    t = re.sub(r'[\u200e\u200f\ufffc]', '', title)
    for b in BOILER: t = re.sub(b, " ", t)
    t = re.sub(r'[\d٠-٩]{1,4}\s*/\s*[\d٠-٩]{1,2}\s*/\s*[\d٠-٩]{1,4}\s*(?:هـ)?', '', t)
    return re.sub(r'\s+', ' ', t).strip(' .،/|"-')

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
    s = '، '.join(out[:2]).strip()
    s = re.sub(r'للشيخ\s*عمر\s*الحركان|،\s*شرح$|\bقناة$|-?\s*سلسلة دروس قد افلح من تزكى', '', s)
    s = re.sub(r'(14\d\d|\d{1,2})\s*[/\\]\s*\d{1,2}\s*[/\\]\s*(\d{1,4})', '', s)
    s = re.sub(r'^[،,\s]*(الدرس|المجلس)\s*[\(\[]?\s*[\d]+\s*[\)\]]?\s*', '', s)
    s = re.sub(r'^[\[(]?المجلس [^\])]*[\])]?\s*$', '', s)
    bt = META.get(key, ('', ''))[0]
    if bt and s.startswith(bt): s = s[len(bt):].lstrip(' :.·،')
    s = re.sub(r'\s+', ' ', s)
    s = re.sub(r'[\[(]\s*المجلس[^\])]*[\])]|المجلس\s*\(\s*\d*\s*\)', '', s)
    s = re.sub(r'^\s*(في\s+)?(ال)?نحو\s*[.،؛]?\s*', '', s) if key in ('shabrawiya', 'nahw_tatbiq', 'ajurrumiya') else s
    s = re.sub(r'^ت\s+', '', s).strip(' .،,/')
    s = re.sub(r'\s+', ' ', s)
    if s in ('في', 'من', 'الدرس'): s = ''
    return s.translate(AR)

def hijri_year(iso):
    # Tabular Islamic calendar: can differ from Umm al-Qura by a day, which only matters around 1 Muharram.
    y, m, d = map(int, iso.split('-'))
    jd = (1461 * (y + 4800 + (m - 14) // 12)) // 4 + (367 * (m - 2 - 12 * ((m - 14) // 12))) // 12 - (3 * ((y + 4900 + (m - 14) // 12) // 100)) // 4 + d - 32075
    l = jd - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    return 30 * n + j - 30

MONTHS = ['محرم', 'صفر', 'ربيع الأول', 'ربيع الآخر', 'جمادى الأولى', 'جمادى الآخرة', 'رجب', 'شعبان', 'رمضان', 'شوال', 'ذو القعدة', 'ذو الحجة']
def hijri_month(iso):
    y, m, d = map(int, iso.split('-'))
    jd = (1461 * (y + 4800 + (m - 14) // 12)) // 4 + (367 * (m - 2 - 12 * ((m - 14) // 12))) // 12 - (3 * ((y + 4900 + (m - 14) // 12) // 100)) // 4 + d - 32075
    l = jd - 1948440 + 10632
    n = (l - 1) // 10631
    l = l - 10631 * n + 354
    j = ((10985 - l) // 5316) * ((50 * l) // 17719) + (l // 5670) * ((43 * l) // 15238)
    l = l - ((30 - j) // 15) * ((17719 * j) // 50) - (j // 16) * ((15238 * j) // 43) + 29
    return MONTHS[(24 * l) // 709 - 1]

def runs(items):
    """Split one book's lessons into the times it was taught. A new run starts when the numbering goes back
    to the start (lesson 1 or 2, or under half of the run so far) after a break of more than 30 days.
    Re-uploads of old sessions keep their gap short or their numbers high, so they stay in their run."""
    out, cur, top, last = [], [], 0, None
    for r in sorted(items, key=lambda r: (r['date'], r['num'] or 0)):
        gap = (datetime.date.fromisoformat(r['date']) - datetime.date.fromisoformat(last)).days if last and r['date'] else 0
        if cur and r['num'] and top >= 3 and (r['num'] <= 2 or r['num'] < top / 2) and gap > 30:
            out.append(cur); cur, top = [], 0
        cur.append(r)
        if r['num']: top = max(top, r['num'])
        if r['date']: last = r['date']
    if cur: out.append(cur)
    return out

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
        if x['id'] in cfg.get('nums', {}): num = cfg['nums'][x['id']]
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
    if c.get('split'):
        groups, left = [], sorted(items, key=lambda r: r['date'])
        for sp in c['split']:
            groups.append(([r for r in left if r['date'] >= sp['from']], sp['label']))
            left = [r for r in left if r['date'] < sp['from']]
    elif key in ('misc', 'khutbah', 'lecture', 'untitled', 'yawm'):
        groups = [(items, '')]
    else:
        rs = runs(items)[::-1]  # newest first
        years = [hijri_year(g[0]['date']) if g[0]['date'] else 0 for g in rs]
        groups = []
        for i, g in enumerate(rs):
            same = [j for j, y in enumerate(years) if y == years[i]]
            label = '' if len(rs) == 1 else f'شرح {hijri_month(g[0]["date"]) + " " if len(same) > 1 else "عام "}{str(years[i]).translate(AR)}هـ'
            groups.append((g, label))
    exps = []
    for mine, label in groups:
        if not mine: continue
        if key not in ('misc', 'khutbah', 'lecture', 'untitled'):
            # Drop re-uploads: the same lesson number with (almost) the same length. Keep the live stream.
            # Same number with a different length is a different session (a part two, or a series whose
            # numbering restarts per surah or per biography), so it stays.
            keep = []
            for r in sorted(mine, key=lambda r: (not r['live'], r['date'])):
                if r['num'] and any(k['num'] == r['num'] and abs(k['dur'] - r['dur']) <= max(60, k['dur'] * .05) for k in keep): continue
                keep.append(r)
            mine = keep
        numbered = key not in ('misc', 'untitled', 'khutbah', 'lecture') and sum(1 for r in mine if r['num']) * 2 > len(mine)
        if numbered:
            prev = 0
            for r in sorted(mine, key=lambda r: (r['date'], r['id'])):
                r['sk'] = r['num'] or prev + .5
                if r['num']: prev = r['num']
            mine.sort(key=lambda r: (r['sk'], r['date']))
        else:
            mine.sort(key=lambda r: (r['date'], r['id']))
        lessons = []
        for i, r in enumerate(mine):
            n = (r['num'] or 0) if numbered else i + 1
            t = topic(r['title'], key, r['num']) if key not in ('misc',) else clean(r['title'])
            t = cfg.get('titles', {}).get(r['id'], t)
            lessons.append([r['id'], n, t, r['dur'], r['date']])
        exps.append({'label': label, 'from': mine[0]['date'], 'to': mine[-1]['date'], 'lessons': lessons})
    last = max((e['to'] for e in exps), default='')
    days = (datetime.date.fromisoformat(today) - datetime.date.fromisoformat(last)).days if last else 999
    out_books.append({'id': key, 'title': title, 'cat': cat, 'author': c.get('author', ''),
                      'ongoing': days <= 30 and len(exps[0]['lessons']) >= 3 and key not in ('misc', 'khutbah', 'lecture'),
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
items = ''.join(f"""<item><title>{x(b['title'])}: {x(l[2] or 'الدرس ' + str(l[1]).translate(AR))}</title><link>{SITE}book/{b['id']}/</link>
<guid isPermaLink="false">{l[0]}</guid><pubDate>{datetime.datetime.fromisoformat(l[4]).strftime('%a, %d %b %Y 12:00:00 +0300')}</pubDate>
<enclosure url="https://www.youtube.com/watch?v={l[0]}" type="text/html" length="0"/></item>""" for b, l in newest if l[4])
open(os.path.join(ROOT, 'feed.xml'), 'w', encoding='utf-8').write(f"""<?xml version="1.0" encoding="utf-8"?>
<rss version="2.0"><channel><title>دروس الشيخ عمر بن حمد الحركان — الجديد</title><link>{SITE}</link>
<description>أحدث دروس فضيلة الشيخ عمر بن حمد الحركان</description><language>ar</language>{items}</channel></rss>
""")
