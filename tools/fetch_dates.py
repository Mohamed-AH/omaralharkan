"""Fill data/dates.json with each video's stream/upload date (YYYY-MM-DD) via YouTube's public web API."""
import json, sys, re, os, datetime, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import yti; yti.CTX['client']['hl'] = 'en'
from yti import post, walk
ids, out = sys.argv[1], sys.argv[2]
want = json.load(open(ids))
try: have = json.load(open(out))
except Exception: have = {}
today = datetime.date.today()
def one(vid):
    try:
        r = post('next', {'videoId': vid})
        t = next((v.get('simpleText') for v in walk(r, 'dateText')), '') or ''
        m = re.search(r'([A-Z][a-z]{2}) (\d{1,2}), (\d{4})', t)
        if m: return vid, datetime.datetime.strptime(m.group(0), '%b %d, %Y').date().isoformat()
        m = re.search(r'(\d+) (hour|minute|day)s? ago', t)
        if m: return vid, (today - datetime.timedelta(days=int(m.group(1)) if m.group(2) == 'day' else 0)).isoformat()
        return vid, None
    except Exception: return vid, None
todo = [v for v in want if v not in have]
with cf.ThreadPoolExecutor(16) as ex:
    for vid, d in ex.map(one, todo):
        if d: have[vid] = d
json.dump(have, open(out, 'w'), indent=0)
print(len(have), 'of', len(want), 'dated')
