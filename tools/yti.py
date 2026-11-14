import json, sys, time, urllib.request, urllib.error
API='https://youtubei.googleapis.com/youtubei/v1/'
CTX={"client":{"clientName":"WEB","clientVersion":"2.20261002.00.00","hl":"ar","gl":"SA"}}
def post(ep, body):
    body=dict(body, context=CTX)
    r=urllib.request.Request(API+ep+'?prettyPrint=false', json.dumps(body).encode(), {'Content-Type':'application/json'})
    for attempt in range(5):   # YouTube sometimes answers 403/429/5xx for a moment mid-crawl
        try: return json.load(urllib.request.urlopen(r, timeout=60))
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as e:
            if attempt == 4 or (isinstance(e, urllib.error.HTTPError) and e.code not in (403, 429, 500, 502, 503, 504)): raise
            time.sleep(2 * 2 ** attempt)
def walk(o, key):
    if isinstance(o, dict):
        for k,v in o.items():
            if k==key: yield v
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o: yield from walk(v, key)
