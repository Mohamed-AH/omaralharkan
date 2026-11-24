"""Keep data/raw/telegram.json: the posts of the Sheikh's Telegram channel (https://t.me/omaralharkan).

The channel posts, for each lesson, the YouTube live link, the lesson's audio file and a card that ties the two
together (book, lesson number, verses or hadith numbers, Hijri date). tools/build_catalog.py joins these to the
lessons; tools/audio_sync.py copies the audio and PDF files to Cloudflare R2.

Usage:
  python3 -I tools/telegram.py                       # add new posts from the public page t.me/s/omaralharkan
  python3 -I tools/telegram.py --seed result.json    # (re)build from a Telegram Desktop export (JSON)

Each post: {"id", "date" (Riyadh, YYYY-MM-DD), "kind": audio|voice|pdf|photo|video|text, "text", "yt": [video ids],
"tg": [ids of posts it links to]}, plus "name", "dur", "size" when the export or the sync knows them.
Needs no login. A failed fetch leaves the file as it was and does not fail the daily job.
"""
import json, os, re, sys, html, datetime, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(os.path.dirname(HERE), 'data', 'raw', 'telegram.json')
CHANNEL = 'omaralharkan'
RIYADH = datetime.timezone(datetime.timedelta(hours=3))
YT = re.compile(r'(?:youtu\.be/|youtube\.com/(?:live/|watch\?v=|shorts/|embed/))([\w-]{11})')
TG = re.compile(r't\.me/(?:c/1424082945|' + CHANNEL + r')/(\d+)', re.I)

def links(text):
    yt = list(dict.fromkeys(YT.findall(text)))
    tg = list(dict.fromkeys(int(x) for x in TG.findall(text)))
    return yt, tg

def post(pid, date, kind, text, extra=None):
    yt, tg = links(text)
    p = {'id': pid, 'date': date, 'kind': kind, 'text': text.strip(), 'yt': yt, 'tg': [x for x in tg if x != pid]}
    p.update({k: v for k, v in (extra or {}).items() if v})
    return p

# ---------- a Telegram Desktop export (Settings → Advanced → Export Telegram data, JSON) ----------
def from_export(path):
    d = json.load(open(path, encoding='utf-8'))
    out = []
    for m in d['messages']:
        if m.get('type') != 'message': continue
        t = m.get('text', '')
        text = t if isinstance(t, str) else ''.join(x if isinstance(x, str) else x.get('text', '') for x in t)
        text += ''.join(' ' + e['href'] for e in m.get('text_entities', []) if e.get('type') == 'text_link')
        mt, mime = m.get('media_type'), m.get('mime_type', '')
        kind = ('voice' if mt == 'voice_message' else 'audio' if mt == 'audio_file' else 'video' if mt in ('video_file', 'animation', 'video_message')
                else 'pdf' if mime == 'application/pdf' else 'photo' if 'photo' in m else 'file' if 'file' in m else 'text')
        out.append(post(m['id'], m['date'][:10], kind, text,
                        {'name': m.get('file_name') or m.get('title'), 'dur': m.get('duration_seconds'), 'size': m.get('file_size')}))
    return out

# ---------- the public web preview: https://t.me/s/omaralharkan?before=<id> ----------
def fetch(before=None):
    url = f'https://t.me/s/{CHANNEL}' + (f'?before={before}' if before else '')
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (lessons catalog sync)', 'Accept-Language': 'ar,en'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return r.read().decode('utf-8', 'replace')

def plain(fragment):
    s = re.sub(r'<br\s*/?>', '\n', fragment)
    s = re.sub(r'<a [^>]*href="([^"]+)"[^>]*>.*?</a>', lambda m: html.unescape(m.group(1)), s, flags=re.S)
    s = re.sub(r'<[^>]+>', '', s)
    return html.unescape(s).replace('\xa0', ' ')

def parse_page(page):
    """The posts on one preview page, oldest first."""
    out = []
    for chunk in re.split(r'(?=<div class="tgme_widget_message_wrap)', page)[1:]:
        m = re.search(r'data-post="[^"/]+/(\d+)"', chunk)
        if not m or 'service_message' in chunk[:600]: continue
        pid = int(m.group(1))
        t = re.search(r'<time datetime="([^"]+)"', chunk)
        date = datetime.datetime.fromisoformat(t.group(1)).astimezone(RIYADH).date().isoformat() if t else ''
        tx = re.search(r'<div class="tgme_widget_message_text[^"]*"[^>]*>(.*?)</div>(?=\s*(?:</div>|<a class="tgme_widget_message_link_preview|<div class="tgme_widget_message_footer|<div class="media_not_supported))', chunk, re.S)
        text = plain(tx.group(1)) if tx else ''
        name, dur = '', 0
        if 'tgme_widget_message_voice' in chunk:
            kind = 'voice'
            d = re.search(r'tgme_widget_message_voice_duration[^>]*>([\d:]+)<', chunk)
            if d: dur = sum(int(x) * 60 ** i for i, x in enumerate(reversed(d.group(1).split(':'))))
        elif 'tgme_widget_message_document_wrap' in chunk:
            title = re.search(r'tgme_widget_message_document_title[^>]*>(.*?)</div>', chunk, re.S)
            name = plain(title.group(1)).strip() if title else ''
            icon = re.search(r'tgme_widget_message_document_icon([^"]*)"', chunk)
            kind = 'audio' if icon and 'audio' in icon.group(1) else 'pdf' if name.lower().endswith('.pdf') else 'file'
            if name in ('Audio', 'Document'): name = ''
        elif 'tgme_widget_message_video' in chunk or 'tgme_widget_message_roundvideo' in chunk: kind = 'video'
        elif 'tgme_widget_message_photo_wrap' in chunk: kind = 'photo'
        else: kind = 'text'
        out.append(post(pid, date, kind, text, {'name': name, 'dur': dur}))
    return sorted(out, key=lambda p: p['id'])

def from_web(known_max, pages=25):
    """Walk the preview back from the newest post until it reaches posts we already have."""
    got, before = {}, None
    for _ in range(pages):
        page = fetch(before)
        ps = parse_page(page)
        if not ps: break
        for p in ps: got[p['id']] = p
        if ps[0]['id'] <= known_max + 1: break
        before = ps[0]['id']
    return list(got.values())

def merge(old, new):
    by = {p['id']: p for p in old}
    for p in new:
        if p['id'] in by:  # keep what the export or the audio sync knew (file name, length, size)
            q = by[p['id']]
            keep = {k: q[k] for k in ('name', 'dur', 'size') if q.get(k) and not p.get(k)}
            if q['kind'] in ('audio', 'voice', 'pdf') and p['kind'] in ('file', 'text'): keep['kind'] = q['kind']
            by[p['id']] = {**p, **keep}
        else:
            by[p['id']] = p
    return sorted(by.values(), key=lambda p: p['id'])

def save(posts):
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('[\n' + ',\n'.join(json.dumps(p, ensure_ascii=False, separators=(',', ':')) for p in posts) + '\n]\n')

if __name__ == '__main__':
    old = json.load(open(OUT, encoding='utf-8')) if os.path.exists(OUT) else []
    if '--seed' in sys.argv:
        new = from_export(sys.argv[sys.argv.index('--seed') + 1])
    else:
        try:
            new = from_web(max((p['id'] for p in old), default=0))
        except Exception as ex:
            print('Telegram: could not read the public channel page, keeping the old list:', ex)
            sys.exit(0)
    posts = merge(old, new)
    save(posts)
    print(f'Telegram: {len(posts)} posts ({len(posts) - len(old):+d}), '
          f"{sum(p['kind'] in ('audio', 'voice') for p in posts)} with audio, {sum(p['kind'] == 'pdf' for p in posts)} PDFs")
