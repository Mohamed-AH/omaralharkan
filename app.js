'use strict';
/* دروس الشيخ عمر الحركان — the whole site in one file: catalog, routes, search and the player. */
const $ = (s, el = document) => el.querySelector(s);
const AR = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = s => { s = Math.max(0, Math.floor(s || 0)); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
  return AR(h ? `${h}:${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}` : `${m}:${String(x).padStart(2, '0')}`); };
const dars = n => n === 1 ? 'درس واحد' : n === 2 ? 'درسان' : n <= 10 ? `${AR(n)} دروس` : `${AR(n)} درساً`;
const mins = s => s ? (s < 3600 ? `${AR(Math.round(s / 60))} د` : fmt(s)) : '';
const hijri = iso => { if (!iso) return ''; try { return new Intl.DateTimeFormat('ar-SA-u-ca-islamic-umalqura-nu-arab', { year: 'numeric', month: 'long', day: 'numeric' }).format(new Date(iso + 'T12:00:00')); } catch { return AR(iso); } };
const norm = s => String(s || '').replace(/[ً-ْـ]/g, '').replace(/[أإآ]/g, 'ا').replace(/ة/g, 'ه').replace(/ى/g, 'ي')
  .replace(/[٠-٩]/g, d => '٠١٢٣٤٥٦٧٨٩'.indexOf(d)).toLowerCase();
const I = {
  play: '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M7 5v14l11-7z"/></svg>',
  pause: '<svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><rect x="6" y="5" width="4" height="14"/><rect x="14" y="5" width="4" height="14"/></svg>',
  find: '<svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" aria-hidden="true"><circle cx="11" cy="11" r="7"/><path d="M20 20l-3.5-3.5"/></svg>'
};

/* ---------- saved state (this browser only) ---------- */
const store = {
  get(k, d) { try { const v = localStorage.getItem('so:' + k); return v == null ? d : JSON.parse(v); } catch { return d; } },
  set(k, v) { try { localStorage.setItem('so:' + k, JSON.stringify(v)); } catch { } }
};
let resume = store.get('resume', {});          // video id -> seconds
let heard = new Set(store.get('heard', []));   // finished video ids
let recent = store.get('recent', []);          // [{v, b, e}] newest first: what is being listened to
let speed = store.get('speed', 1);
const lastVisit = store.get('visit', '');
const saveHeard = () => store.set('heard', [...heard]);

/* ---------- catalog ---------- */
let C, BOOK = {}, VID = {};
const title = (l) => l[2] || `الدرس ${AR(l[1])}`;
function index() {
  for (const b of C.books) {
    BOOK[b.id] = b;
    b.exps.forEach((e, ei) => e.lessons.forEach((l, li) => { VID[l[0]] = { b, ei, li, l }; }));
    b.norm = norm(b.title);
  }
}
const isNew = l => l[4] && lastVisit && l[4] > lastVisit;

/* ---------- views ---------- */
const main = $('#main'), heroSlot = $('#heroSlot');
function setHero(html) { heroSlot.innerHTML = html; }
function current() {  // the newest thing being listened to that is not finished
  for (const r of recent) { const x = VID[r.v]; if (x && !heard.has(r.v)) return x; }
  return null;
}
function contCard(x, big) {
  const l = x.l, at = resume[l[0]] || 0, p = l[3] ? Math.min(100, at / l[3] * 100) : 0;
  return `<button type="button" class="cont rise" style="animation-delay:.35s" data-play="${l[0]}">
    <div class="row"><span class="play">${I.play}</span><div style="min-width:0">
      <div class="k">${big ? 'أكمل من حيث توقفت' : 'تابع'}</div>
      <div class="t">${esc(x.b.title)}، الدرس ${AR(l[1])}</div>
      <div class="s">${esc(title(l))}${l[3] && at ? `، بقي ${mins(l[3] - at)}` : ''}</div></div></div>
    <div class="bar"><i style="width:${p.toFixed(1)}%"></i></div></button>`;
}
function bookCard(b, i) {
  const all = b.exps[0].lessons, done = all.filter(l => heard.has(l[0])).length;
  return `<a class="card rise" style="animation-delay:${(.1 + i * .05).toFixed(2)}s" href="#/book/${b.id}">
    <span class="c">${esc(b.cat)}</span><span class="t">${esc(b.title)}</span>
    ${done ? `<span class="bar"><i style="width:${(done / all.length * 100).toFixed(1)}%"></i></span>` : ''}
    <span class="m"><span>${dars(b.count)}</span><span class="${b.ongoing ? 'on' : ''}">${b.ongoing ? 'يُشرح الآن' : 'مكتمل'}</span></span></a>`;
}

let catFilter = 'الكل';
function home() {
  const x = current();
  setHero(`<div class="hero"><div class="who">
      <small class="rise">دروس فضيلة الشيخ</small>
      <h1 class="rise" style="animation-delay:.12s">عمر بن حَمَد الحَرْكان</h1>
      <div class="line draw" aria-hidden="true"></div>
      <p class="rise" style="animation-delay:.25s">شروح المتون العلمية مرتبة كتاباً كتاباً؛ تستمع، وتكمل من حيث توقفت.</p></div>
    ${x ? contCard(x, true) : ''}</div>`);
  const nl = VID[C.latest[0]?.[0]];
  const cats = ['الكل', ...C.cats.map(c => c.name)];
  const books = C.books.filter(b => catFilter === 'الكل' || b.cat === catFilter);
  const big = books.filter(b => b.count >= 10), small = books.filter(b => b.count < 10);
  const ongoing = C.books.filter(b => b.ongoing);
  main.innerHTML = `
    ${nl ? `<div class="strip rise" style="animation-delay:.45s"><span class="k">${nl.l[4] === C.updated ? 'جديد اليوم' : 'أحدث درس'}</span>
      <a class="t" href="#/book/${nl.b.id}">${esc(nl.b.title)}: ${esc(title(nl.l))}</a><span class="d">${hijri(nl.l[4])}، ${mins(nl.l[3])}</span>
      <button class="go" type="button" data-play="${nl.l[0]}">استمع ←</button></div>` : ''}
    ${catFilter === 'الكل' ? `<section class="block"><div class="head"><div><h2>يُشرح الآن</h2><div class="n">شروح قائمة تُضاف إليها الدروس</div></div></div>
      <div class="grid">${ongoing.map(bookCard).join('')}</div></section>` : ''}
    <section class="block" id="all"><div class="head"><div><h2>الشروح</h2><div class="n">${AR(C.books.length)} شرحاً وسلسلة في ${AR(C.cats.length)} فنون</div></div>
      <div class="chips" role="group" aria-label="الفن">${cats.map(c => `<button class="chip" type="button" data-cat="${esc(c)}" aria-pressed="${c === catFilter}">${esc(c)}</button>`).join('')}</div></div>
      <div class="grid">${big.map(bookCard).join('')}</div>
      ${small.length ? `<h3 style="font-family:var(--f-title);font-size:24px;margin:40px 0 8px">رسائل ودروس قصيرة</h3>
        <ul class="small-list">${small.map(b => `<li><a href="#/book/${b.id}"><span>${esc(b.title)}</span><span>${dars(b.count)}</span></a></li>`).join('')}</ul>` : ''}
    </section>`;
}

let bookState = { order: 'asc', hide: false, q: '', show: 80 };
function bookPage(id, ei = 0) {
  const b = BOOK[id]; if (!b) return notFound();
  ei = Math.min(ei, b.exps.length - 1);
  const e = b.exps[ei];
  setHero(`<div class="sub-hero"><div style="display:flex;flex-wrap:wrap;gap:20px;justify-content:space-between;align-items:end">
    <div><div class="k rise">${esc(b.cat)}</div><h1 class="rise" style="animation-delay:.08s">${esc(b.title)}</h1>${b.author ? `<div class="a rise" style="animation-delay:.14s">${esc(b.author)}</div>` : ''}</div>
    ${b.exps.length > 1 ? `<div class="tabs rise" role="tablist" aria-label="الشرح" style="animation-delay:.2s">${b.exps.map((x, i) =>
      `<button type="button" role="tab" aria-selected="${i === ei}" data-exp="${i}">${esc(x.label)} (${dars(x.lessons.length)})</button>`).join('')}</div>` : ''}
  </div></div>`);
  const done = e.lessons.filter(l => heard.has(l[0])).length;
  let list = e.lessons.map((l, i) => [l, i]);
  if (bookState.hide) list = list.filter(([l]) => !heard.has(l[0]));
  if (bookState.q) { const q = norm(bookState.q); list = list.filter(([l]) => norm(title(l)).includes(q) || AR(l[1]) === bookState.q || String(l[1]) === q); }
  if (bookState.order === 'desc') list.reverse();
  const shown = list.slice(0, bookState.show);
  const cur = current(), nowId = cur && cur.b === b ? cur.l[0] : null;
  const firstUnheard = e.lessons.find(l => !heard.has(l[0]));
  main.innerHTML = `<div class="panel rise">
    <div class="tools">
      ${e.lessons.length <= 60 ? `<div class="beads" aria-hidden="true">${e.lessons.map(l => `<span class="${heard.has(l[0]) ? 'on' : ''}"></span>`).join('')}</div>` : ''}
      <span class="n">سمعت ${AR(done)} من ${AR(e.lessons.length)}، من ${hijri(e.from)} إلى ${hijri(e.to)}</span>
      <span class="sp"></span>
      <label class="find">${I.find}<span class="sr">ابحث في الدروس</span><input id="bq" type="search" placeholder="ابحث في هذا الشرح أو رقم الدرس" value="${esc(bookState.q)}"></label>
      <button class="btn" type="button" data-order aria-pressed="${bookState.order === 'desc'}">${bookState.order === 'desc' ? 'الأحدث أولاً' : 'من الأول'}</button>
      <button class="btn" type="button" data-hide aria-pressed="${bookState.hide}">إخفاء ما سمعته</button>
      ${firstUnheard ? `<button class="btn" type="button" data-play="${firstUnheard[0]}" style="background:var(--green);color:var(--ivory);border-color:var(--green)">${done ? 'أكمل من الدرس ' + AR(firstUnheard[1]) : 'ابدأ من الدرس ' + AR(firstUnheard[1])}</button>` : ''}
    </div>
    <ol class="lessons">${shown.map(([l]) => {
      const at = resume[l[0]], h = heard.has(l[0]);
      const st = [hijri(l[4]), h ? 'سمعته' : at ? `<span class="g">توقفت عند ${fmt(at)}</span>` : '', isNew(l) ? '<span class="g">جديد</span>' : ''].filter(Boolean).join('، ');
      return `<li class="lesson${l[0] === nowId ? ' now' : ''}${h ? ' heard' : ''}"><span class="no">${AR(l[1])}</span>
        <span class="tx"><span class="tt">${esc(title(l))}</span><span class="ss">${st}</span></span>
        <span class="du">${mins(l[3])}</span>
        <button class="pl" type="button" data-play="${l[0]}" aria-label="تشغيل الدرس ${AR(l[1])}">${I.play}</button></li>`; }).join('') || '<li class="empty">لا توجد دروس مطابقة</li>'}</ol>
    ${list.length > shown.length ? `<button class="btn more" type="button" data-more>عرض ${AR(Math.min(80, list.length - shown.length))} درساً آخر</button>` : ''}
    <div style="height:16px"></div></div>`;
  const bq = $('#bq'); bq.oninput = () => { bookState.q = bq.value.trim(); bookState.show = 80; const pos = bq.selectionStart; bookPage(id, ei); const n = $('#bq'); n.focus(); n.setSelectionRange(pos, pos); };
}

function searchPage(q) {
  setHero(`<div class="sub-hero"><div class="k">البحث</div><h1>«${esc(q)}»</h1></div>`);
  const nq = norm(q).trim(); if (!nq) { main.innerHTML = '<p class="empty">اكتب كلمة للبحث</p>'; return; }
  const words = nq.split(/\s+/);
  const books = C.books.filter(b => words.every(w => b.norm.includes(w)));
  const hits = [];
  for (const b of C.books) b.exps.forEach(e => e.lessons.forEach(l => {
    const t = norm(title(l) + ' ' + b.title);
    if (words.every(w => t.includes(w))) hits.push({ b, l });
  }));
  hits.sort((a, b) => (b.l[4] || '').localeCompare(a.l[4] || ''));
  const mark = s => { let out = esc(s); for (const w of q.trim().split(/\s+/)) if (w.length > 1) out = out.replace(new RegExp(w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), m => `<mark>${m}</mark>`); return out; };
  main.innerHTML = `<div class="panel" style="padding:8px 26px 20px">
    ${books.length ? `<h2 style="font-family:var(--f-title);font-size:24px;margin:16px 0 8px">الكتب</h2><div class="grid">${books.map(bookCard).join('')}</div>` : ''}
    <h2 style="font-family:var(--f-title);font-size:24px;margin:24px 0 8px">الدروس <span style="font-size:15px;color:var(--soft)">(${AR(hits.length)})</span></h2>
    ${hits.length ? `<ul class="results">${hits.slice(0, 150).map(({ b, l }) => `<li><button type="button" data-play="${l[0]}">
      <span class="lesson" style="border:0;flex:1;min-height:0"><span class="no">${AR(l[1])}</span><span class="tx"><span class="b">${esc(b.title)}</span><span class="t" style="display:block">${mark(title(l))}</span><span class="ss">${hijri(l[4])}، ${mins(l[3])}</span></span></span></button></li>`).join('')}</ul>`
      : '<p class="empty">لم نجد دروساً بهذه الكلمات. جرّب كلمة أقصر أو اسم الباب.</p>'}</div>`;
}

function mine() {
  setHero(`<div class="sub-hero"><div class="k">محفوظ في هذا المتصفح</div><h1>ما أتابعه</h1></div>`);
  const items = recent.map(r => VID[r.v]).filter(Boolean);
  const seen = new Set(), books = [];
  for (const x of items) if (!seen.has(x.b.id)) { seen.add(x.b.id); books.push(x); }
  main.innerHTML = `<div class="panel" style="padding:20px 26px">${books.length ? `<div class="grid">${books.map(x => contCard(x)).join('')}</div>
    <p style="font-size:13px;color:var(--soft);margin-top:18px">يُحفظ تقدّمك على هذا الجهاز فقط.</p>` :
    '<p class="empty">لم تبدأ درساً بعد. اختر شرحاً من الصفحة الرئيسية، وسيظهر هنا لتكمل من حيث توقفت.</p>'}</div>`;
  for (const el of main.querySelectorAll('.cont')) { el.style.background = 'var(--green)'; }
}
function notFound() { setHero(''); main.innerHTML = '<p class="empty">الصفحة غير موجودة. <a href="#/">العودة إلى الرئيسية</a></p>'; }

/* ---------- routing ---------- */
let lastRoute = '';
function route() {
  const h = decodeURIComponent(location.hash.slice(1) || '/');
  const [path, qs] = h.split('?');
  const parts = path.split('/').filter(Boolean);
  if (h !== lastRoute && !(parts[0] === 'book' && lastRoute.startsWith('/book/' + parts[1]))) bookState = { order: 'asc', hide: false, q: '', show: 80 };
  lastRoute = h;
  document.querySelectorAll('[data-nav]').forEach(a => a.removeAttribute('aria-current'));
  const nav = parts[0] === 'book' && ['khutbah', 'yawm'].includes(parts[1]) ? parts[1] : parts[0] === 'mine' ? 'mine' : !parts.length ? 'home' : '';
  if (nav) $(`[data-nav="${nav}"]`)?.setAttribute('aria-current', 'page');
  if (!parts.length) home();
  else if (parts[0] === 'book') bookPage(parts[1], +(parts[2] || 0));
  else if (parts[0] === 'search') { const q = new URLSearchParams(qs).get('q') || ''; $('#q').value = q; searchPage(q); }
  else if (parts[0] === 'mine') mine();
  else notFound();
  document.title = (parts[0] === 'book' && BOOK[parts[1]] ? BOOK[parts[1]].title + ' | ' : '') + 'دروس الشيخ عمر بن حمد الحركان';
}
addEventListener('hashchange', () => { route(); scrollTo({ top: 0 }); });

document.addEventListener('click', e => {
  const t = e.target.closest('button,a'); if (!t) return;
  if (t.dataset.play) { play(t.dataset.play); return; }
  if (t.dataset.cat) { catFilter = t.dataset.cat; home(); $('#all').scrollIntoView({ block: 'start' }); return; }
  if (t.dataset.exp != null) { location.hash = `#/book/${location.hash.split('/')[2]}/${t.dataset.exp}`; return; }
  if (t.hasAttribute('data-order')) { bookState.order = bookState.order === 'asc' ? 'desc' : 'asc'; route(); return; }
  if (t.hasAttribute('data-hide')) { bookState.hide = !bookState.hide; route(); return; }
  if (t.hasAttribute('data-more')) { bookState.show += 80; route(); return; }
});
$('#searchForm').addEventListener('submit', e => { e.preventDefault(); const q = $('#q').value.trim(); if (q) location.hash = '#/search?q=' + encodeURIComponent(q); });
let st; $('#q').addEventListener('input', () => { clearTimeout(st); st = setTimeout(() => { const q = $('#q').value.trim(); if (q.length > 1) location.replace('#/search?q=' + encodeURIComponent(q)); }, 350); });

/* ---------- player (YouTube embed: small in listen mode, large on «عرض المرئي») ---------- */
let yt = null, ytReady = false, cur = null, pendingStart = 0, tick = null;
const P = $('#player');
function loadYT() {
  if (window.YT || loadYT.once) return; loadYT.once = 1;
  const s = document.createElement('script'); s.src = 'https://www.youtube.com/iframe_api'; document.head.appendChild(s);
}
window.onYouTubeIframeAPIReady = () => {
  yt = new YT.Player('yt', { width: '100%', height: '100%', host: 'https://www.youtube-nocookie.com',
    playerVars: { playsinline: 1, rel: 0, modestbranding: 1, hl: 'ar' },
    events: { onReady: () => { ytReady = true; if (cur) start(); }, onStateChange: onState } });
};
function play(vid) {
  const x = VID[vid]; if (!x) return;
  cur = x; pendingStart = heard.has(vid) ? 0 : (resume[vid] || 0);
  recent = [{ v: vid, b: x.b.id, e: x.ei }, ...recent.filter(r => r.b !== x.b.id)].slice(0, 12); store.set('recent', recent);
  P.hidden = false; $('#nowT').textContent = title(x.l); $('#nowB').textContent = `— ${x.b.title}، الدرس ${AR(x.l[1])}`;
  $('#dur').textContent = fmt(x.l[3]);
  if (!ytReady) loadYT(); else start();
  document.querySelectorAll('.lesson.now').forEach(el => el.classList.remove('now'));
  document.querySelector(`[data-play="${vid}"]`)?.closest('.lesson')?.classList.add('now');
  if ('mediaSession' in navigator) {
    navigator.mediaSession.metadata = new MediaMetadata({ title: title(x.l), artist: 'الشيخ عمر بن حمد الحركان', album: x.b.title,
      artwork: [{ src: `https://i.ytimg.com/vi/${vid}/hqdefault.jpg`, sizes: '480x360', type: 'image/jpeg' }] });
    navigator.mediaSession.setActionHandler('nexttrack', next);
    navigator.mediaSession.setActionHandler('seekbackward', () => skip(-15));
    navigator.mediaSession.setActionHandler('seekforward', () => skip(30));
  }
}
function start() {
  yt.loadVideoById({ videoId: cur.l[0], startSeconds: Math.floor(pendingStart) });
  yt.setPlaybackRate(speed);
}
function onState(ev) {
  const playing = ev.data === YT.PlayerState.PLAYING;
  $('#pp').innerHTML = playing ? I.pause : I.play; $('#pp').setAttribute('aria-label', playing ? 'إيقاف مؤقت' : 'تشغيل');
  clearInterval(tick);
  if (playing) { yt.setPlaybackRate(speed); tick = setInterval(progress, 1000); }
  if (ev.data === YT.PlayerState.ENDED) { finish(); next(); }
}
function progress() {
  if (!cur || !yt.getCurrentTime) return;
  const t = yt.getCurrentTime(), d = yt.getDuration() || cur.l[3];
  $('#cur').textContent = fmt(t); $('#dur').textContent = fmt(d);
  if (d) $('#seek').value = Math.round(t / d * 1000);
  if (Math.floor(t) % 5 === 0) {
    if (d > 60 && (t >= d * .95 || d - t <= 30)) finish();
    else if (t > 5) { resume[cur.l[0]] = t; store.set('resume', resume); }
  }
}
function finish() {
  if (!cur || heard.has(cur.l[0])) return;
  heard.add(cur.l[0]); delete resume[cur.l[0]]; saveHeard(); store.set('resume', resume);
}
function next() {
  if (!cur) return;
  const e = cur.b.exps[cur.ei], n = e.lessons[cur.li + 1];
  if (n) play(n[0]);
}
const skip = s => { if (yt && yt.getCurrentTime) yt.seekTo(Math.max(0, yt.getCurrentTime() + s), true); };
$('#pp').onclick = () => { if (!yt || !yt.getPlayerState) return; yt.getPlayerState() === YT.PlayerState.PLAYING ? yt.pauseVideo() : yt.playVideo(); };
$('#back').onclick = () => skip(-15); $('#fwd').onclick = () => skip(30); $('#next').onclick = next;
$('#seek').oninput = e => { if (yt && yt.getDuration) yt.seekTo(e.target.value / 1000 * yt.getDuration(), true); };
const SPEEDS = [1, 1.25, 1.5, 1.75, 2];
const showSpeed = () => { $('#speed').textContent = AR(String(speed).replace('.', '٫')) + '×'; };
$('#speed').onclick = () => { speed = SPEEDS[(SPEEDS.indexOf(speed) + 1) % SPEEDS.length]; store.set('speed', speed); showSpeed(); if (yt && yt.setPlaybackRate) yt.setPlaybackRate(speed); };
function setBig(on) { P.classList.toggle('big', on); $('#scrim').hidden = !on; $('#mode').setAttribute('aria-pressed', on); $('#mode').textContent = on ? 'صوت فقط' : 'عرض المرئي'; }
$('#mode').onclick = () => setBig(!P.classList.contains('big'));
$('#scrim').onclick = () => setBig(false);
addEventListener('keydown', e => { if (e.key === 'Escape') setBig(false); });
addEventListener('pagehide', () => { if (cur && yt && yt.getCurrentTime) { const t = yt.getCurrentTime(); if (t > 5 && !heard.has(cur.l[0])) { resume[cur.l[0]] = t; store.set('resume', resume); } } });

/* ---------- start ---------- */
fetch('data/catalog.json').then(r => r.json()).then(data => {
  C = data; index(); showSpeed();
  $('#updated').textContent = hijri(C.updated);
  route();
  store.set('visit', C.updated);
}).catch(() => { main.innerHTML = '<p class="empty">تعذّر تحميل الفهرس. حدّث الصفحة.</p>'; });
