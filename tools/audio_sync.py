"""Copy the lesson audio and the book PDFs from the Telegram channel to Cloudflare R2, so the site can play and
offer them itself. Records what it copied in data/raw/audio.json, which tools/build_catalog.py reads.

Needs (GitHub → Settings → Secrets and variables → Actions):
  secrets  TG_API_ID, TG_API_HASH            from https://my.telegram.org → API development tools
           TG_SESSION                         a login string made once with tools/telegram_login.py
           (or TG_BOT_TOKEN instead of TG_SESSION: a bot that is an admin of the channel)
           R2_ACCOUNT_ID, R2_ACCESS_KEY_ID, R2_SECRET_ACCESS_KEY   an R2 API token with Object Read & Write on the bucket
  variables R2_BUCKET                         the bucket name
            AUDIO_BASE_URL                    the bucket's public address, e.g. https://audio.omaralharkan.com/
Without them it prints a note and does nothing, so the daily job still runs.

Usage: python3 -I tools/audio_sync.py [--max 100]
Only posts a lesson or a book uses are copied (see tools/tg_match.py); each file once.
"""
import json, os, sys, time, tempfile, mimetypes, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
RAW = os.path.join(ROOT, 'data', 'raw')
sys.path.insert(0, HERE)
CHANNEL = 'omaralharkan'
env = lambda k: os.environ.get(k, '').strip()
MAX = int(sys.argv[sys.argv.index('--max') + 1]) if '--max' in sys.argv else 100
BUDGET = 25 * 60  # seconds: stop starting new downloads after this, the rest goes next run

def load(name, default):
    try: return json.load(open(os.path.join(RAW, name), encoding='utf-8'))
    except Exception: return default

def wanted(posts):
    """Post ids worth copying: audio matched to a lesson, and PDFs matched to a book."""
    from tg_match import match, pdfs
    c = json.load(open(os.path.join(ROOT, 'data', 'catalog.json'), encoding='utf-8'))
    lessons = {l[0]: (b['id'], l[1], l[4], l[2], l[3]) for b in c['books'] for e in b['exps'] for l in e['lessons']}
    ids = [x['t'] for x in match(posts, lessons).values() if x.get('t')]
    cfg = json.load(open(os.path.join(HERE, 'books.json'), encoding='utf-8'))
    ids += [p['id'] for _, p in pdfs(posts, cfg.get('pdfs'))]
    return sorted(set(ids), reverse=True)  # newest first

def main():
    need = ['TG_API_ID', 'TG_API_HASH', 'R2_ACCOUNT_ID', 'R2_ACCESS_KEY_ID', 'R2_SECRET_ACCESS_KEY', 'R2_BUCKET', 'AUDIO_BASE_URL']
    missing = [k for k in need if not env(k)] + ([] if env('TG_SESSION') or env('TG_BOT_TOKEN') else ['TG_SESSION or TG_BOT_TOKEN'])
    if missing:
        print('Audio sync skipped, not set up yet:', ', '.join(missing)); return
    import boto3
    from telethon.sync import TelegramClient
    from telethon.sessions import StringSession

    posts = load('telegram.json', [])
    by_id = {p['id']: p for p in posts}
    base = env('AUDIO_BASE_URL').rstrip('/') + '/'
    audio = load('audio.json', {})
    if audio.get('base') != base: audio['base'] = base
    files = audio.setdefault('files', {})
    todo = [i for i in wanted(posts) if str(i) not in files][:MAX]
    if not todo:
        print('Audio sync: nothing new'); save(audio); return

    s3 = boto3.client('s3', endpoint_url=f"https://{env('R2_ACCOUNT_ID')}.r2.cloudflarestorage.com",
                      aws_access_key_id=env('R2_ACCESS_KEY_ID'), aws_secret_access_key=env('R2_SECRET_ACCESS_KEY'), region_name='auto')
    bucket = env('R2_BUCKET')
    client = TelegramClient(StringSession(env('TG_SESSION')), int(env('TG_API_ID')), env('TG_API_HASH'))
    client.start(bot_token=env('TG_BOT_TOKEN')) if env('TG_BOT_TOKEN') else client.connect()
    if not client.is_user_authorized():
        print('Audio sync: the Telegram login (TG_SESSION) is not valid any more; make a new one with tools/telegram_login.py'); return
    started, done = time.time(), 0
    try:
        for chunk in [todo[i:i + 50] for i in range(0, len(todo), 50)]:
            for msg in client.get_messages(CHANNEL, ids=chunk):
                if time.time() - started > BUDGET: break
                if not msg or not msg.file: continue
                p = by_id.get(msg.id, {})
                mime = msg.file.mime_type or 'application/octet-stream'
                ext = (msg.file.ext or mimetypes.guess_extension(mime) or '').lower()
                if ext in ('.oga', '.opus'): ext = '.ogg'
                kind = 'pdf' if mime == 'application/pdf' else 'audio'
                key = f'{kind}/{msg.id}{ext}'
                nice = (p.get('name') or f'{msg.id}{ext}').replace('"', '')
                with tempfile.TemporaryDirectory() as tmp:
                    path = client.download_media(msg, file=os.path.join(tmp, f'{msg.id}{ext}'))
                    s3.upload_file(path, bucket, key, ExtraArgs={
                        'ContentType': mime, 'CacheControl': 'public, max-age=31536000, immutable',
                        'ContentDisposition': "attachment; filename*=UTF-8''" + urllib.parse.quote(nice)})
                    size = os.path.getsize(path)
                files[str(msg.id)] = {'k': key, 's': size, 'd': int(msg.file.duration or 0), 'm': mime}
                done += 1
                print(f'  copied {msg.id} → {key} ({size / 1e6:.1f} MB)')
                save(audio)  # after every file, so a stopped run keeps what it copied
    finally:
        client.disconnect()
        save(audio)
    print(f'Audio sync: {done} copied, {len(todo) - done} left for the next run, {len(files)} in all')

def save(audio):
    json.dump(audio, open(os.path.join(RAW, 'audio.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0, sort_keys=True)

if __name__ == '__main__':
    main()
