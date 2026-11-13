'use strict';
/* دروس الشيخ عمر الحركان — the whole site in one file: catalog, routes, search and the player. */
const $ = (s, el = document) => el.querySelector(s);
const AR = n => String(n).replace(/\d/g, d => '٠١٢٣٤٥٦٧٨٩'[d]);
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const fmt = s => { s = Math.max(0, Math.floor(s || 0)); const h = Math.floor(s / 3600), m = Math.floor(s % 3600 / 60), x = s % 60;
  return AR(h ? `${h}:${String(m).padStart(2, '0')}:${String(x).padStart(2, '0')}` : `${m}:${String(x).padStart(2, '0')}`); };
// Arabic counted nouns follow the last two digits: ١٠٠ درس، ١٠٣ دروس، ١١١ درساً
const count = (n, one, two, few, many, sing) => { const r = n % 100; return n === 1 ? one : n === 2 ? two : r === 0 || r === 1 || r === 2 ? `${AR(n)} ${sing}` : r <= 10 ? `${AR(n)} ${few}` : `${AR(n)} ${many}`; };
const dars = n => count(n, 'درس واحد', 'درسان', 'دروس', 'درساً', 'درس');
const mins = s => s ? (s < 3600 ? count(Math.max(1, Math.round(s / 60)), 'دقيقة', 'دقيقتان', 'دقائق', 'دقيقة', 'دقيقة') : fmt(s)) : '';
const hyear = iso => { if (!iso) return ''; try { return new Intl.DateTimeFormat('ar-SA-u-ca-islamic-umalqura-nu-arab', { year: 'numeric' }).format(new Date(iso + 'T12:00:00')); } catch { return AR(iso.slice(0, 4)); } };
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
  return `<a class="card rise" style="animation-delay:${(.1 + i * .05).toFixed(2)}s" href="/book/${b.id}/">
    <span class="c">${esc(b.cat)}</span><span class="t">${esc(b.title)}</span>
    ${done ? `<span class="bar"><i style="width:${(done / all.length * 100).toFixed(1)}%"></i></span>` : ''}
    <span class="m"><span>${dars(b.count)}</span><span class="${b.ongoing ? 'on' : ''}">${b.ongoing ? 'يُشرح الآن' : 'آخر درس ' + hyear(b.last)}</span></span></a>`;
}

let catFilter = 'الكل', bookSort = 'cat', bookStatus = 'all';
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
  let books = C.books.filter(b => (catFilter === 'الكل' || b.cat === catFilter) && (bookStatus === 'all' || (bookStatus === 'on') === b.ongoing));
  if (bookSort === 'count') books = [...books].sort((a, b) => b.count - a.count);
  if (bookSort === 'last') books = [...books].sort((a, b) => (b.last || '').localeCompare(a.last || ''));
  if (bookSort === 'abc') books = [...books].sort((a, b) => a.title.replace(/^(ال|كتاب |التعليق على )/g, '').localeCompare(b.title.replace(/^(ال|كتاب |التعليق على )/g, ''), 'ar'));
  const big = books.filter(b => b.count >= 10), small = books.filter(b => b.count < 10);
  const ongoing = C.books.filter(b => b.ongoing);
  main.innerHTML = `
    ${nl ? `<div class="strip rise" style="animation-delay:.45s"><span class="k">${nl.l[4] === C.updated ? 'جديد اليوم' : 'أحدث درس'}</span>
      <a class="t" href="/book/${nl.b.id}/">${esc(nl.b.title)}: ${esc(title(nl.l))}</a><span class="d">${hijri(nl.l[4])}، ${mins(nl.l[3])}</span>
      <button class="go" type="button" data-play="${nl.l[0]}">استمع ←</button></div>` : ''}
    ${catFilter === 'الكل' ? `<section class="block"><div class="head"><div><h2>يُشرح الآن</h2><div class="n">شروح قائمة تُضاف إليها الدروس</div></div></div>
      <div class="grid">${ongoing.map(bookCard).join('')}</div></section>` : ''}
    <section class="block" id="all"><div class="head"><div><h2>الشروح</h2><div class="n">${AR(books.length)} من ${AR(C.books.length)} شرحاً وسلسلة</div></div>
      <div class="chips" role="group" aria-label="الفن">${cats.map(c => `<button class="chip" type="button" data-cat="${esc(c)}" aria-pressed="${c === catFilter}">${esc(c)}</button>`).join('')}</div></div>
      <div class="filters" style="padding:0 0 18px">
        <label class="fl"><span>الترتيب</span><select id="bsort">${[['cat', 'حسب الفن'], ['count', 'الأكثر دروساً'], ['last', 'آخر درس أولاً'], ['abc', 'أبجدياً']].map(([v, t]) => `<option value="${v}"${v === bookSort ? ' selected' : ''}>${t}</option>`).join('')}</select></label>
        <label class="fl"><span>الحالة</span><select id="bstat">${[['all', 'الكل'], ['on', 'يُشرح الآن'], ['done', 'شروح سابقة']].map(([v, t]) => `<option value="${v}"${v === bookStatus ? ' selected' : ''}>${t}</option>`).join('')}</select></label>
        <a class="btn" href="/lessons/" style="display:inline-flex;align-items:center;text-decoration:none;align-self:end">تصفّح كل الدروس ←</a>
      </div>
      <div class="grid">${big.map(bookCard).join('') || '<p class="empty">لا توجد شروح بهذه التصفية</p>'}</div>
      ${small.length ? `<h3 style="font-family:var(--f-title);font-size:24px;margin:40px 0 8px">رسائل ودروس قصيرة</h3>
        <ul class="small-list">${small.map(b => `<li><a href="/book/${b.id}/"><span>${esc(b.title)}</span><span>${dars(b.count)}</span></a></li>`).join('')}</ul>` : ''}
    </section>`;
}

/* ---------- lesson lists: search, filters, sort and pages, all kept in the address (?q=&sort=&page=…) ---------- */
const Q = () => Object.fromEntries(new URLSearchParams(location.search));
function setQ(patch, push) {
  const p = { ...Q(), ...patch };
  if (!('page' in patch)) delete p.page;
  for (const k of Object.keys(p)) if (p[k] === '' || p[k] == null || p[k] === 'all') delete p[k];
  const qs = new URLSearchParams(p).toString();
  const url = location.pathname + (qs ? '?' + qs : '');
  setTimeout(() => go(url, !push, true));  // after the current change/blur events finish
}
const HY = new Map();
const hYear = iso => { if (!iso) return 0; const y = iso.slice(0, 7); if (!HY.has(y)) { let v = 0; try { v = +new Intl.DateTimeFormat('en-u-ca-islamic-umalqura-nu-latn', { year: 'numeric' }).format(new Date(iso + 'T12:00:00')).replace(/\D/g, ''); } catch { } HY.set(y, v); } return HY.get(y); };
const LENS = { s: ['أقل من ٢٠ دقيقة', 0, 1200], m: ['٢٠–٤٥ دقيقة', 1200, 2700], l: ['أكثر من ٤٥ دقيقة', 2700, 1e9] };
const STS = { unheard: 'لم أسمعه', progress: 'بدأته ولم أكمله', heard: 'سمعته', new: 'جديد منذ آخر زيارة' };
function applyFilters(rows, q) {
  if (q.q) { const ws = norm(q.q).trim().split(/\s+/).filter(Boolean);
    rows = rows.filter(r => { const t = r.n || (r.n = norm(title(r.l) + ' ' + r.b.title + ' ' + r.l[1])); return ws.every(w => t.includes(w)); }); }
  if (q.cat) rows = rows.filter(r => r.b.cat === q.cat);
  if (q.book) rows = rows.filter(r => r.b.id === q.book);
  if (q.year) rows = rows.filter(r => String(hYear(r.l[4])) === q.year);
  if (q.len && LENS[q.len]) { const [, a, z] = LENS[q.len]; rows = rows.filter(r => r.l[3] >= a && r.l[3] < z); }
  if (q.st === 'unheard') rows = rows.filter(r => !heard.has(r.l[0]));
  if (q.st === 'heard') rows = rows.filter(r => heard.has(r.l[0]));
  if (q.st === 'progress') rows = rows.filter(r => !heard.has(r.l[0]) && resume[r.l[0]]);
  if (q.st === 'new') rows = rows.filter(r => isNew(r.l));
  return rows;
}
const SORTS = {
  num: ['بترتيب الدروس', (a, b) => a.i - b.i], numd: ['بترتيب الدروس، من الآخر', (a, b) => b.i - a.i],
  new: ['الأحدث أولاً', (a, b) => (b.l[4] || '').localeCompare(a.l[4] || '') || b.i - a.i], old: ['الأقدم أولاً', (a, b) => (a.l[4] || '').localeCompare(b.l[4] || '') || a.i - b.i],
  long: ['الأطول أولاً', (a, b) => b.l[3] - a.l[3]], short: ['الأقصر أولاً', (a, b) => a.l[3] - b.l[3]]
};
const sel = (name, label, opts, val) => `<label class="fl"><span>${label}</span><select data-q="${name}">${opts.map(([v, t]) => `<option value="${esc(v)}"${String(v) === String(val ?? '') ? ' selected' : ''}>${esc(t)}</option>`).join('')}</select></label>`;
let fopen = innerWidth > 640;
const fbox = (q, inner) => { const n = ['cat', 'book', 'sort', 'st', 'len', 'year'].filter(k => q[k]).length;
  return `<details class="fbox"${fopen ? ' open' : ''}><summary>التصفية والترتيب${n ? ` (${AR(n)})` : ''}</summary><div class="fgrid">${inner}</div></details>`; };
document.addEventListener('toggle', e => { if (e.target.classList && e.target.classList.contains('fbox')) fopen = e.target.open; }, true);
function pager(total, page, per) {
  const n = Math.ceil(total / per); if (n <= 1) return '';
  const nums = [...new Set([1, 2, page - 1, page, page + 1, n - 1, n].filter(x => x >= 1 && x <= n))].sort((a, b) => a - b);
  let out = '', prev = 0;
  for (const x of nums) { if (x - prev > 1) out += '<span class="gap">…</span>'; out += x === page ? `<span class="pg on" aria-current="page">${AR(x)}</span>` : `<button class="pg" type="button" data-page="${x}" aria-label="الصفحة ${AR(x)}">${AR(x)}</button>`; prev = x; }
  return `<nav class="pager" aria-label="الصفحات">
    <button class="pg w" type="button" data-page="${page - 1}" ${page <= 1 ? 'disabled' : ''}>السابق</button>${out}
    <button class="pg w" type="button" data-page="${page + 1}" ${page >= n ? 'disabled' : ''}>التالي</button></nav>`;
}
function lessonRow(r, opts) {
  const l = r.l, at = resume[l[0]], h = heard.has(l[0]);
  const st = [opts.book ? `<a class="bk" href="/book/${r.b.id}/">${esc(r.b.title)}</a>` : '', hijri(l[4]), h ? 'سمعته' : at ? `<span class="g">توقفت عند ${fmt(at)}</span>` : '', isNew(l) ? '<span class="g">جديد</span>' : ''].filter(Boolean).join('، ');
  return `<li class="lesson${l[0] === opts.now ? ' now' : ''}${h ? ' heard' : ''}"><span class="no">${AR(l[1])}</span>
    <span class="tx"><span class="tt">${opts.mark ? opts.mark(title(l)) : esc(title(l))}</span><span class="ss">${st}</span></span>
    <span class="du">${mins(l[3])}</span>
    <button class="pl" type="button" data-play="${l[0]}" aria-label="تشغيل ${esc(title(l))}">${I.play}</button></li>`;
}
function activeChips(q, names) {
  const on = Object.keys(names).filter(k => q[k]);
  if (!on.length) return '';
  return `<div class="active">${on.map(k => `<button class="chip x" type="button" data-clear="${k}" aria-label="إزالة ${esc(names[k](q[k]))}">${esc(names[k](q[k]))} ✕</button>`).join('')}
    ${on.length > 1 ? '<button class="chip x" type="button" data-clear="*">مسح الكل</button>' : ''}</div>`;
}
const markWords = q => s => { let out = esc(s); for (const w of (q || '').trim().split(/\s+/)) if (w.length > 1) out = out.replace(new RegExp(w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'g'), m => `<mark>${m}</mark>`); return out; };
function keepFocus(fn) { const a = document.activeElement, id = a && a.id, pos = a && a.selectionStart; fn(); if (id) { const n = document.getElementById(id); if (n) { n.focus(); try { n.setSelectionRange(pos, pos); } catch { } } } }

function bookPage(id, ei = 0) {
  const b = BOOK[id]; if (!b) return notFound();
  ei = Math.min(ei, b.exps.length - 1);
  const e = b.exps[ei], q = Q(), PER = 50;
  setHero(`<div class="sub-hero"><div style="display:flex;flex-wrap:wrap;gap:20px;justify-content:space-between;align-items:end">
    <div><div class="k rise">${esc(b.cat)}</div><h1 class="rise" style="animation-delay:.08s">${esc(b.title)}</h1>${b.author ? `<div class="a rise" style="animation-delay:.14s">${esc(b.author)}</div>` : ''}</div>
    ${b.exps.length > 1 ? `<div class="tabs rise" role="tablist" aria-label="الشرح" style="animation-delay:.2s">${b.exps.map((x, i) =>
      `<button type="button" role="tab" aria-selected="${i === ei}" data-exp="${i}">${esc(x.label)} (${dars(x.lessons.length)})</button>`).join('')}</div>` : ''}
  </div></div>`);
  const done = e.lessons.filter(l => heard.has(l[0])).length;
  let rows = applyFilters(e.lessons.map((l, i) => ({ l, b, i })), q);
  rows.sort(SORTS[q.sort] ? SORTS[q.sort][1] : SORTS.num[1]);
  const pages = Math.max(1, Math.ceil(rows.length / PER)), page = Math.min(Math.max(1, +q.page || 1), pages);
  const shown = rows.slice((page - 1) * PER, page * PER);
  const cur = current(), now = cur && cur.b === b ? cur.l[0] : null;
  const firstUnheard = e.lessons.find(l => !heard.has(l[0]));
  const years = [...new Set(e.lessons.map(l => hYear(l[4])).filter(Boolean))].sort((a, b) => b - a);
  main.innerHTML = `<div class="panel rise">
    <div class="tools">
      ${e.lessons.length <= 60 ? `<div class="beads" aria-hidden="true">${e.lessons.map(l => `<span class="${heard.has(l[0]) ? 'on' : ''}"></span>`).join('')}</div>` : ''}
      <span class="n">سمعت ${AR(done)} من ${AR(e.lessons.length)}، من ${hijri(e.from)} إلى ${hijri(e.to)}</span>
      <span class="sp"></span>
      ${firstUnheard ? `<button class="btn" type="button" data-play="${firstUnheard[0]}" style="background:var(--green);color:var(--ivory);border-color:var(--green)">${done ? 'أكمل من الدرس ' + AR(firstUnheard[1]) : 'ابدأ من الدرس ' + AR(firstUnheard[1])}</button>` : ''}
    </div>
    <div class="filters">
      <label class="find">${I.find}<span class="sr">ابحث في الدروس</span><input id="fq" data-q="q" type="search" placeholder="ابحث في هذا الشرح أو برقم الدرس" value="${esc(q.q || '')}"></label>
      ${fbox(q, `${sel('sort', 'الترتيب', Object.entries(SORTS).map(([k, v]) => [k === 'num' ? '' : k, v[0]]), q.sort)}
      ${sel('st', 'حالتي', [['', 'الكل'], ...Object.entries(STS)], q.st)}
      ${sel('len', 'المدة', [['', 'أي مدة'], ...Object.entries(LENS).map(([k, v]) => [k, v[0]])], q.len)}
      ${years.length > 1 ? sel('year', 'السنة', [['', 'كل السنوات'], ...years.map(y => [y, AR(y) + 'هـ'])], q.year) : ''}`)}
    </div>
    ${activeChips(q, { q: v => `«${v}»`, st: v => STS[v] || v, len: v => (LENS[v] || [v])[0], year: v => AR(v) + 'هـ' })}
    <div class="count">${rows.length === e.lessons.length ? '' : `${dars(rows.length)} مطابقة. `}${rows.length > PER ? `عرض ${AR((page - 1) * PER + 1)}–${AR(Math.min(page * PER, rows.length))} من ${AR(rows.length)}` : ''}</div>
    <ol class="lessons">${shown.map(r => lessonRow(r, { now, mark: q.q && markWords(q.q) })).join('') || '<li class="empty">لا توجد دروس مطابقة. <button class="chip" type="button" data-clear="*">مسح التصفية</button></li>'}</ol>
    ${pager(rows.length, page, PER)}
    <div style="height:16px"></div></div>`;
}

function lessonsPage() {
  const q = Q(), PER = 30;
  const all = []; for (const b of C.books) b.exps.forEach(e => e.lessons.forEach((l, i) => all.push({ l, b, i })));
  let rows = applyFilters(all, q);
  rows.sort(SORTS[q.sort] ? SORTS[q.sort][1] : SORTS.new[1]);
  const pages = Math.max(1, Math.ceil(rows.length / PER)), page = Math.min(Math.max(1, +q.page || 1), pages);
  const shown = rows.slice((page - 1) * PER, page * PER);
  const pool = q.cat ? C.books.filter(b => b.cat === q.cat) : C.books;
  const years = [...new Set(all.map(r => hYear(r.l[4])).filter(Boolean))].sort((a, b) => b - a);
  const nq = norm(q.q || '').trim(), books = nq ? C.books.filter(b => nq.split(/\s+/).every(w => b.norm.includes(w))) : [];
  setHero(`<div class="sub-hero"><div class="k">${q.q ? 'نتائج البحث' : 'كل الدروس'}</div><h1>${q.q ? `«${esc(q.q)}»` : 'جميع الدروس'}</h1>
    <div class="a">${dars(rows.length)}${rows.length !== all.length ? ` من ${AR(all.length)}` : ''}</div></div>`);
  main.innerHTML = `<div class="panel rise">
    <div class="filters">
      <label class="find">${I.find}<span class="sr">ابحث</span><input id="fq" data-q="q" type="search" placeholder="ابحث عن درس أو باب أو كتاب" value="${esc(q.q || '')}"></label>
      ${fbox(q, `${sel('cat', 'الفن', [['', 'كل الفنون'], ...C.cats.map(c => [c.name, c.name])], q.cat)}
      ${sel('book', 'الكتاب', [['', 'كل الكتب'], ...pool.map(b => [b.id, b.title])], q.book)}
      ${sel('sort', 'الترتيب', [['', 'الأحدث أولاً'], ['old', 'الأقدم أولاً'], ['long', 'الأطول أولاً'], ['short', 'الأقصر أولاً']], q.sort)}
      ${sel('st', 'حالتي', [['', 'الكل'], ...Object.entries(STS)], q.st)}
      ${sel('len', 'المدة', [['', 'أي مدة'], ...Object.entries(LENS).map(([k, v]) => [k, v[0]])], q.len)}
      ${sel('year', 'السنة', [['', 'كل السنوات'], ...years.map(y => [y, AR(y) + 'هـ'])], q.year)}`)}
    </div>
    ${activeChips(q, { q: v => `«${v}»`, cat: v => v, book: v => BOOK[v]?.title || v, st: v => STS[v] || v, len: v => (LENS[v] || [v])[0], year: v => AR(v) + 'هـ' })}
    ${books.length && page === 1 ? `<div style="padding:4px 26px 8px"><div class="count" style="padding:0 0 8px">كتب مطابقة</div><div class="grid">${books.slice(0, 8).map(bookCard).join('')}</div></div>` : ''}
    <div class="count">${rows.length > PER ? `عرض ${AR((page - 1) * PER + 1)}–${AR(Math.min(page * PER, rows.length))} من ${AR(rows.length)}` : ''}</div>
    <ol class="lessons">${shown.map(r => lessonRow(r, { book: true, mark: q.q && markWords(q.q) })).join('') || '<li class="empty">لم نجد دروساً مطابقة. جرّب كلمة أقصر أو أزل بعض التصفية. <button class="chip" type="button" data-clear="*">مسح التصفية</button></li>'}</ol>
    ${pager(rows.length, page, PER)}
    <div style="height:16px"></div></div>`;
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
function notFound() { setHero(''); main.innerHTML = '<p class="empty">الصفحة غير موجودة. <a href="/">العودة إلى الرئيسية</a></p>'; }

/* ---------- routing: clean paths, no # (/, /book/<id>/, /book/<id>/<n>/, /lessons/?q=&…, /mine/) ---------- */
const bookUrl = (id, ei) => `/book/${id}/${ei ? (ei + 1) + '/' : ''}`;
function go(url, replace, keepScroll) {
  history[replace ? 'replaceState' : 'pushState'](null, '', url);
  keepFocus(route);
  if (!keepScroll) scrollTo({ top: 0 });
}
function route() {
  const parts = decodeURIComponent(location.pathname).split('/').filter(Boolean);
  if (parts[0] === 'search') { history.replaceState(null, '', '/lessons/' + location.search); return route(); }
  document.querySelectorAll('[data-nav]').forEach(a => a.removeAttribute('aria-current'));
  let nav = parts[0] === 'book' && ['khutbah', 'yawm'].includes(parts[1]) ? parts[1] : ['mine', 'lessons'].includes(parts[0]) ? parts[0] : !parts.length ? 'home' : '';
  if (nav) document.querySelectorAll(`[data-nav="${nav}"]`).forEach(a => a.setAttribute('aria-current', 'page'));
  if (parts[0] !== 'lessons' && document.activeElement !== $('#q')) $('#q').value = '';
  if (!parts.length) home();
  else if (parts[0] === 'book') bookPage(parts[1], Math.max(0, (+parts[2] || 1) - 1));
  else if (parts[0] === 'lessons') { if (document.activeElement !== $('#q')) $('#q').value = Q().q || ''; lessonsPage(); }
  else if (parts[0] === 'mine') mine();
  else notFound();
  document.title = (parts[0] === 'book' && BOOK[parts[1]] ? BOOK[parts[1]].title + ' | ' : parts[0] === 'lessons' ? (Q().q ? `«${Q().q}» | ` : 'كل الدروس | ') : '') + 'دروس الشيخ عمر بن حمد الحركان';
}
addEventListener('popstate', () => keepFocus(route));

document.addEventListener('click', e => {
  const t = e.target.closest('button,a'); if (!t) return;
  if (t.dataset.play) { play(t.dataset.play); return; }
  if (t.dataset.cat) { catFilter = t.dataset.cat; home(); $('#all').scrollIntoView({ block: 'start' }); return; }
  if (t.dataset.exp != null) { go(bookUrl(location.pathname.split('/')[2], +t.dataset.exp)); return; }
  if (t.dataset.page) { setQ({ page: t.dataset.page === '1' ? '' : t.dataset.page }, true); (main.querySelector('.filters') || main).scrollIntoView({ block: 'start' }); return; }
  if (t.dataset.clear) { if (t.dataset.clear === '*') go(location.pathname, false, true); else setQ({ [t.dataset.clear]: '' }, true); return; }
  // same-site links open without reloading the page (the player keeps playing)
  if (t.tagName === 'A' && t.origin === location.origin && !t.target && !t.hasAttribute('download') && !/\.(xml|json|txt)$/.test(t.pathname)
      && !e.ctrlKey && !e.metaKey && !e.shiftKey && e.button === 0) { e.preventDefault(); go(t.pathname + t.search); }
});
document.addEventListener('change', e => {
  const t = e.target;
  if (t.dataset.q) { const patch = { [t.dataset.q]: t.value }; if (t.dataset.q === 'cat') patch.book = ''; setQ(patch, true); }
  if (t.id === 'bsort') { bookSort = t.value; home(); }
  if (t.id === 'bstat') { bookStatus = t.value; home(); }
});
let ft; document.addEventListener('input', e => {
  if (e.target.id !== 'fq') return;
  clearTimeout(ft); const v = e.target.value; ft = setTimeout(() => setQ({ q: v.trim() }), 250);
});
$('#searchForm').addEventListener('submit', e => { e.preventDefault(); const q = $('#q').value.trim(); go('/lessons/' + (q ? '?q=' + encodeURIComponent(q) : '')); });
let st; $('#q').addEventListener('input', () => { clearTimeout(st); st = setTimeout(() => { const q = $('#q').value.trim(); if (q.length > 1) go('/lessons/?q=' + encodeURIComponent(q), location.pathname.startsWith('/lessons'), location.pathname.startsWith('/lessons')); }, 300); });

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
function closePlayer() {  // keep the place, stop the sound, hide the bar
  if (cur && yt && yt.getCurrentTime) { const t = yt.getCurrentTime(); if (t > 5 && !heard.has(cur.l[0])) { resume[cur.l[0]] = t; store.set('resume', resume); } }
  clearInterval(tick); if (yt && yt.stopVideo) yt.stopVideo();
  setBig(false); P.hidden = true; cur = null;
  document.querySelectorAll('.lesson.now').forEach(el => el.classList.remove('now'));
  if ('mediaSession' in navigator) navigator.mediaSession.metadata = null;
  keepFocus(route);
}
$('#close').onclick = closePlayer;

/* phones: bottom nav and the «المزيد» sheet */
const sheet = $('#sheet'), sheetBg = $('#sheetBg');
function openSheet(on) { sheet.hidden = sheetBg.hidden = !on; $('#bnMore').setAttribute('aria-expanded', on); if (on) $('#sheetX').focus(); }
$('#bnMore').onclick = () => openSheet(sheet.hidden);
$('#sheetX').onclick = sheetBg.onclick = () => openSheet(false);
sheet.addEventListener('click', e => { if (e.target.closest('a')) openSheet(false); });
addEventListener('keydown', e => { if (e.key === 'Escape' && !sheet.hidden) openSheet(false); });
$('#bnSearch').onclick = () => { scrollTo({ top: 0, behavior: 'smooth' }); $('#q').focus(); };
addEventListener('keydown', e => { if (e.key === 'Escape') setBig(false); });
addEventListener('pagehide', () => { if (cur && yt && yt.getCurrentTime) { const t = yt.getCurrentTime(); if (t > 5 && !heard.has(cur.l[0])) { resume[cur.l[0]] = t; store.set('resume', resume); } } });

/* ---------- start ---------- */
fetch('/data/catalog.json').then(r => r.json()).then(data => {
  C = data; index(); showSpeed();
  $('#sheetCats').innerHTML = C.cats.map(c => `<li><a href="/lessons/?cat=${encodeURIComponent(c.name)}">${esc(c.name)} <span>${dars(c.count)}</span></a></li>`).join(''); $('#pp').innerHTML = I.play;
  $('#updated').textContent = hijri(C.updated);
  route();
  store.set('visit', C.updated);
}).catch(() => { main.innerHTML = '<p class="empty">تعذّر تحميل الفهرس. حدّث الصفحة.</p>'; });
