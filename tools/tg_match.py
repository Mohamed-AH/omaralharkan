"""Join the Telegram posts (data/raw/telegram.json) to the lessons of the catalog.

For each YouTube lesson it finds: the Telegram post with the lesson's audio, the verses / hadith numbers / rule
numbers the lesson covers (from the lesson card), and a lesson name from the post's caption.
Used by tools/build_catalog.py; run it alone to see what it matched:  python3 -I tools/tg_match.py
"""
import os, re, sys, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rules import classify, norm

AUDIO = ('audio', 'voice')
DATE = re.compile(r'[\d٠-٩]{4}\s*/\s*[\d٠-٩]{1,2}\s*/\s*[\d٠-٩]{1,2}\s*(?:هـ)?|[\d٠-٩]{1,2}\s*-\s*[\d٠-٩]{1,2}\s*-\s*[\d٠-٩]{4}')
RANGE_WORDS = ('سورة', 'الآية', 'الآيات', 'آية', 'آيات', 'الحديث', 'الأحاديث', 'الأحديث', 'القاعدة', 'القواعد', 'الباب')
SESSION = re.compile(r'^درس\s+(العصر|الفجر|المغرب|العشاء|الظهر|الأحد|الإثنين|الاثنين|الثلاثاء|الأربعاء|الخميس|الجمعة|السبت)$')

def days(a, b):
    try: return abs((datetime.date.fromisoformat(a) - datetime.date.fromisoformat(b)).days)
    except Exception: return 999

def days_signed(a, b):
    """Days from a to b (b - a)."""
    try: return (datetime.date.fromisoformat(b) - datetime.date.fromisoformat(a)).days
    except Exception: return 999

def card(text):
    """A lesson card: «٦١ | درس التعليق على تفسير ابن سعدي | سورة البقرة | الآيات (١٩٧-٢٠٢) ١٤٤٨/٠٥/١٩هـ | درس العصر».
    Returns (number, range, topic) from its first lines."""
    head = text.split('للاستماع')[0]
    parts = [p.strip(' .،') for p in re.split(r'[|\n]', head) if p.strip(' .،')]
    num, rng, top = None, [], []
    for i, p in enumerate(parts):
        q = DATE.sub('', p).strip(' .،')
        if not q: continue
        if i == 0 and re.fullmatch(r'[\d٠-٩]+', q):
            num = int(q.translate(str.maketrans('٠١٢٣٤٥٦٧٨٩', '0123456789'))); continue
        if SESSION.match(q) or q.startswith('اليوم في سلسلة'): continue
        if q.startswith(('درس ', 'شرح ', 'التعليق')) or 'درس التعليق' in q: continue
        if any(q.startswith(w) for w in RANGE_WORDS): rng.append(q); continue
        top.append(q)
    return num, '، '.join(rng), '، '.join(top[:1])

def caption(text):
    """A link post's own words: «https://youtube.com/live/… الدرس ٤٨ في تفسير ابن سعدي» -> «الدرس ٤٨ في تفسير ابن سعدي»."""
    t = re.sub(r'https?://\S+', ' ', text)
    t = re.sub(r'"?قناة\s*$', '', t.strip())
    return re.sub(r'\s+', ' ', t).strip(' |.،"')

def match(posts, lessons, topic=None):
    """posts: the telegram.json list. lessons: {video id: (book key, number, date, name)}.
    topic(text, key, num) turns a caption into a short lesson name (build_catalog.topic).
    Returns {video id: {'t': audio post id, 'r': range, 'n': name}} (keys only when known)."""
    by_id = {p['id']: p for p in posts}
    order = sorted(by_id)
    pos = {pid: i for i, pid in enumerate(order)}
    out = {}
    def put(vid, k, v):
        if vid in lessons and v and k not in out.setdefault(vid, {}): out[vid][k] = v
    used = set()

    # 1. cards: they name the YouTube live and the audio post, and spell out the range
    for p in posts:
        if p['kind'] in AUDIO or len(p['yt']) != 1: continue
        vid = p['yt'][0]
        if 'للاستماع' in p['text']:
            num, rng, top = card(p['text'])
            put(vid, 'r', rng)
            if top: put(vid, 'n', top)
            for t in p['tg']:
                if by_id.get(t, {}).get('kind') in AUDIO and t not in used:
                    put(vid, 't', t); used.add(t); break
        elif p['kind'] == 'text' and vid in lessons:
            c = caption(p['text'])
            if c and topic:
                key, num = lessons[vid][0], lessons[vid][1]
                name = topic(c, key, num)
                if name and len(name) > 2: put(vid, 'n', name)

    # 2. audio posts no card pointed to
    by_book = {}
    for vid, (key, num, date, *_) in lessons.items():
        if num: by_book.setdefault((key, num), []).append((vid, date))
    for pid in order:
        p = by_id[pid]
        if p['kind'] not in AUDIO or pid in used: continue
        i = pos[pid]
        nxt = by_id[order[i + 1]] if i + 1 < len(order) else None
        text = p['text'] + ' ' + (p.get('name') or '').replace('_', ' ')
        if nxt and nxt['kind'] == 'text' and not nxt['yt'] and not nxt['tg'] and days(nxt['date'], p['date']) <= 1 and len(nxt['text']) < 200:
            text += ' ' + nxt['text']  # the caption posted under it: «👆 قراءة في كتاب التوحيد الدرس158», «الدرس ٢٧٩ في البخاري»
        vid = None
        key, num = classify(text)
        if key and num:
            near = sorted((days(d, p['date']), v) for v, d in by_book.get((key, num), []) if days(d, p['date']) <= 3)
            if near: vid = near[0][1]
        if not vid:  # the YouTube link posted just before it, the same day
            for j in range(i - 1, max(-1, i - 4), -1):
                q = by_id[order[j]]
                if q['kind'] in AUDIO: break
                if len(q['yt']) == 1 and q['yt'][0] in lessons and days(q['date'], p['date']) <= 1 and 'للاستماع' not in q['text']:
                    k2, n2 = classify(text)
                    x = lessons[q['yt'][0]]
                    close = not (p.get('dur') and x[4]) or abs(p['dur'] - x[4]) <= max(120, x[4] * .25)
                    if (not k2 or k2 == x[0]) and close: vid = q['yt'][0]
                    break
        if not vid and p.get('dur'):  # one lesson streamed that day or the day before with the same length (±5%)
            same = [v for v, x in lessons.items() if 0 <= days_signed(x[2], p['date']) <= 1 and x[4] and abs(x[4] - p['dur']) <= max(30, x[4] * .05) and 't' not in out.get(v, {})]
            if len(same) > 1: same = [v for v in same if lessons[v][2] == p['date']]
            if len(same) == 1: vid = same[0]
        if vid and 't' not in out.get(vid, {}):
            put(vid, 't', pid); used.add(pid)
    return {v: x for v, x in out.items() if x}

def pdfs(posts, overrides=None):
    """The PDF posts and the book each belongs to: [(book key, post)]."""
    out = []
    for p in posts:
        if p['kind'] != 'pdf': continue
        key = (overrides or {}).get(str(p['id'])) or classify((p.get('name') or '') + ' ' + p['text'])[0]
        if key: out.append((key, p))
    return out

if __name__ == '__main__':
    import json
    sys.argv = sys.argv[:1]
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.dirname(here)
    posts = json.load(open(os.path.join(root, 'data', 'raw', 'telegram.json'), encoding='utf-8'))
    c = json.load(open(os.path.join(root, 'data', 'catalog.json'), encoding='utf-8'))
    lessons = {l[0]: (b['id'], l[1], l[4], l[2], l[3]) for b in c['books'] for e in b['exps'] for l in e['lessons']}
    m = match(posts, lessons)
    aud = [p['id'] for p in posts if p['kind'] in AUDIO]
    got = {x['t'] for x in m.values() if 't' in x}
    print(len(m), 'lessons enriched;', len(got), 'of', len(aud), 'audio posts matched;', sum('r' in x for x in m.values()), 'ranges')
    dur = {p['id']: p.get('dur') for p in posts}
    for v, x in m.items():
        if 't' in x and dur.get(x['t']) and abs(dur[x['t']] - lessons[v][4]) > max(120, lessons[v][4] * .15):
            print('  length differs', v, lessons[v][:3], 'video', lessons[v][4], 'audio', dur[x['t']], 'post', x['t'])
    for pid in aud:
        if pid not in got:
            p = next(q for q in posts if q['id'] == pid)
            print('  unmatched', pid, p['date'], p.get('dur'), (p.get('name') or '')[:40], p['text'][:60].replace('\n', ' '))
