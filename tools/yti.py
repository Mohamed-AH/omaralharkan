import json, sys, urllib.request
API='https://youtubei.googleapis.com/youtubei/v1/'
CTX={"client":{"clientName":"WEB","clientVersion":"2.20261002.00.00","hl":"ar","gl":"SA"}}
def post(ep, body):
    body=dict(body, context=CTX)
    r=urllib.request.Request(API+ep+'?prettyPrint=false', json.dumps(body).encode(), {'Content-Type':'application/json'})
    return json.load(urllib.request.urlopen(r, timeout=60))
def walk(o, key):
    if isinstance(o, dict):
        for k,v in o.items():
            if k==key: yield v
            yield from walk(v, key)
    elif isinstance(o, list):
        for v in o: yield from walk(v, key)
