"""List every live stream and video on the channel into data/raw/ (streams_flat.json, videos_flat.json, dates.json).

With YOUTUBE_API_KEY set it uses the YouTube Data API (uploads playlist + videos.list: title, length,
live or not, and the stream/upload date in one pass). Without a key it reads the channel's
public «البث المباشر» and «الفيديوهات» tabs (tools/yti.py) and dates new videos with tools/fetch_dates.py.

Usage: python3 -I tools/crawl.py
Refuses to write if the new list is much shorter than the old one (a broken fetch must not empty the site).
"""
import json, os, re, sys, urllib.request, urllib.parse, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(os.path.dirname(HERE), 'data', 'raw')
CHANNEL_ID = 'UCkuCkn_g5roM4TKAiyHFIwA'   # @omaralharkan
KEY = os.environ.get('YOUTUBE_API_KEY', '').strip()

def load(name, default):
    try: return json.load(open(os.path.join(RAW, name), encoding='utf-8'))
    except Exception: return default

def save(name, data):
    json.dump(data, open(os.path.join(RAW, name), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)

def badge(sec):
    h, m, s = sec // 3600, sec % 3600 // 60, sec % 60
    return f'{h}:{m:02d}:{s:02d}' if h else f'{m}:{s:02d}'

def iso_secs(d):
    m = re.fullmatch(r'P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', d or '')
    if not m: return 0
    D, H, M, S = (int(x or 0) for x in m.groups())
    return D * 86400 + H * 3600 + M * 60 + S

def api(path, **q):
    q['key'] = KEY
    with urllib.request.urlopen(f'https://www.googleapis.com/youtube/v3/{path}?' + urllib.parse.urlencode(q), timeout=60) as r:
        return json.load(r)

def with_api():
    ids, tok = [], None
    while True:
        r = api('playlistItems', part='contentDetails', playlistId='UU' + CHANNEL_ID[2:], maxResults=50, **({'pageToken': tok} if tok else {}))
        ids += [i['contentDetails']['videoId'] for i in r.get('items', [])]
        tok = r.get('nextPageToken')
        if not tok: break
    streams, videos, dates = [], [], {}
    for i in range(0, len(ids), 50):
        r = api('videos', part='snippet,contentDetails,liveStreamingDetails', id=','.join(ids[i:i + 50]))
        for v in r.get('items', []):
            sec = iso_secs(v['contentDetails'].get('duration'))
            if sec <= 60: continue          # Shorts and broken stream stubs
            live = v.get('liveStreamingDetails') or {}
            when = live.get('actualStartTime') or v['snippet']['publishedAt']
            row = {'id': v['id'], 't': v['snippet']['title'], 'badge': [badge(sec)]}
            (streams if live else videos).append(row)
            dates[v['id']] = when[:10]
    return streams, videos, dates

def without_api():
    sys.path.insert(0, HERE)
    from yti import post, walk
    def tab(params):
        items, r = [], post('browse', {'browseId': CHANNEL_ID, 'params': params})
        while True:
            for l in walk(r, 'lockupViewModel'):
                md = l.get('metadata', {}).get('lockupMetadataViewModel', {})
                b = [x.get('text') for x in walk(l.get('contentImage', {}), 'thumbnailBadgeViewModel')]
                items.append({'id': l.get('contentId'), 't': md.get('title', {}).get('content', ''), 'badge': b})
            tok = next(walk(r, 'continuationCommand'), {}).get('token')
            if not tok: return items
            r = post('browse', {'continuation': tok})
    streams = tab('EgdzdHJlYW1z8gYECgJ6AA==')
    videos = tab('EgZ2aWRlb3PyBgQKAjoA')
    ids = os.path.join(RAW, '_ids.json')
    json.dump([x['id'] for x in streams + videos], open(ids, 'w'))
    subprocess.run([sys.executable, '-I', os.path.join(HERE, 'fetch_dates.py'), ids, os.path.join(RAW, 'dates.json')], check=True)
    os.remove(ids)
    return streams, videos, load('dates.json', {})

old = len(load('streams_flat.json', [])) + len(load('videos_flat.json', []))
streams, videos, dates = with_api() if KEY else without_api()
if len(streams) + len(videos) < old * 0.9:
    sys.exit(f'only {len(streams) + len(videos)} videos listed (had {old}); keeping the old lists')
save('streams_flat.json', streams); save('videos_flat.json', videos)
save('dates.json', {**load('dates.json', {}), **dates})
print(f'{len(streams)} lives, {len(videos)} videos ({len(streams) + len(videos) - old:+d})', 'via the Data API' if KEY else 'via the public channel pages')
