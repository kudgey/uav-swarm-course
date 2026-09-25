#!/usr/bin/env node
/*
 * Гейт мобільної верстки: кожна сторінка лекції на ширині 375 px не повинна
 * прокручуватися вбік цілком.
 *
 *   node tools/check_mobile.mjs                       # локальний preview (http://localhost:4173)
 *   node tools/check_mobile.mjs https://uav-swarm-kpi.vercel.app
 *
 * Критерії на кожній сторінці:
 *   1) document.documentElement.scrollWidth <= 375 (верстка строго в ширині пристрою:
 *      емуляція «мобільного» viewport ховає проблему — Chrome розсуває сторінку
 *      до ширини вмісту й зменшує її, тож прокрутки нема, а текст дрібнішає);
 *   2) жоден елемент .vp-doc не виходить за правий край більш ніж на 2 px,
 *      якщо його не обрізає предок із власною прокруткою (широка таблиця чи
 *      формула, що прокручується всередині себе, — це норма). Предок з
 *      overflow: hidden/clip не рятує: вміст там просто зрізаний і недосяжний.
 *
 *   3) блоки коду: кожен <CodeFold> згорнутий за замовчуванням, розкривається
 *      кнопкою, під кожним нефрагментом стоїть видимий <RunOutput>; кількість
 *      блоків на сторінці = кількості <CodeFold> у lectures/NN.md; з розкритими
 *      блоками критерії 1–2 теж виконуються;
 *   4) на сторінці 0 неперехоплених помилок JS (pageerror).
 *
 * Залежностей немає: системний Chrome у headless-режимі + DevTools Protocol
 * через вбудований у Node 22 WebSocket. Шлях до Chrome можна задати змінною CHROME.
 */
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';

const SITE = join(dirname(fileURLToPath(import.meta.url)), '..');
const BASE = (process.argv[2] || 'http://localhost:4173').replace(/\/$/, '');
const WIDTH = 375, HEIGHT = 812, TOL = 2;
const PAGES = ['/', ...Array.from({ length: 12 }, (_, i) => `/lectures/${String(i + 1).padStart(2, '0')}`)];
const CHROME = process.env.CHROME || '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';

const MEASURE = `(() => {
  const W = ${WIDTH}, TOL = ${TOL};
  const doc = document.querySelector('.vp-doc') || document.body;
  // Рятує будь-який предок із власною прокруткою, що сам уміщається в екран
  // (формула в клітинці → таблиця з прокруткою). hidden/clip не рятує: там вміст зрізаний.
  function clippedByAncestor(el) {
    for (let a = el.parentElement; a && a !== document.body; a = a.parentElement) {
      const ox = getComputedStyle(a).overflowX;
      if ((ox === 'auto' || ox === 'scroll') && a.getBoundingClientRect().right <= W + TOL) return true;
    }
    return false;
  }
  const bad = [];
  doc.querySelectorAll('*').forEach(el => {
    if (el.closest('mjx-assistive-mml')) return;          // службова MathML для читачів екрана
    const r = el.getBoundingClientRect();
    if (!r.width || r.right <= W + TOL) return;
    if (clippedByAncestor(el)) return;
    bad.push(el);
  });
  const top = bad.filter(el => !bad.includes(el.parentElement));   // лише зовнішні порушники
  const describe = el => {
    const cls = (el.getAttribute('class') || '').split(/\\s+/).filter(Boolean).slice(0, 2).join('.');
    return el.tagName.toLowerCase() + (cls ? '.' + cls : '');
  };
  const groups = {};
  top.forEach(el => {
    const k = describe(el), over = Math.round(el.getBoundingClientRect().right - W);
    groups[k] = groups[k] || { n: 0, max: 0 };
    groups[k].n++; groups[k].max = Math.max(groups[k].max, over);
  });
  return JSON.stringify({
    overflow: Math.max(0, document.documentElement.scrollWidth - W, window.innerWidth - W),
    offenders: top.length,
    worst: top.reduce((m, el) => Math.max(m, Math.round(el.getBoundingClientRect().right - W)), 0),
    groups,
  });
})()`;

// Блоки коду: згорнуті за замовчуванням, під кожним — видимий вивід; потім розкриваємо всі.
const CODE_UI = `(async () => {
  const folds = [...document.querySelectorAll('.vp-doc .cf')];
  const r = { folds: folds.length, frags: 0, openByDefault: 0, noOutput: 0, hiddenOutput: 0, notOpened: 0 };
  for (const cf of folds) {
    const body = cf.querySelector('.cf__body');
    if (!body || getComputedStyle(body).display !== 'none') r.openByDefault++;
    if (cf.classList.contains('is-fragment')) { r.frags++; continue; }
    const ro = cf.nextElementSibling;
    if (!ro || !ro.classList.contains('ro')) r.noOutput++;
    else if (getComputedStyle(ro).display === 'none' || ro.offsetHeight < 30 || !ro.querySelector('pre')) r.hiddenOutput++;
  }
  folds.forEach(cf => cf.querySelector('.cf__head').click());
  await new Promise(res => setTimeout(res, 300));
  for (const cf of folds) {
    const body = cf.querySelector('.cf__body');
    const btn = cf.querySelector('.cf__btn');
    if (!body || getComputedStyle(body).display === 'none' || !body.querySelector('pre') ||
        body.offsetHeight < 30 || !btn || btn.textContent.trim() !== 'Сховати код') r.notOpened++;
  }
  return JSON.stringify(r);
})()`;

const sleep = ms => new Promise(r => setTimeout(r, ms));

async function launch() {
  if (!existsSync(CHROME)) throw new Error(`Chrome не знайдено: ${CHROME} (задайте змінну CHROME)`);
  const dir = mkdtempSync(join(tmpdir(), 'mobile-audit-'));
  const proc = spawn(CHROME, ['--headless=new', '--remote-debugging-port=0', `--user-data-dir=${dir}`,
    '--no-first-run', '--no-default-browser-check', '--hide-scrollbars', 'about:blank'], { stdio: 'ignore' });
  const portFile = join(dir, 'DevToolsActivePort');
  for (let i = 0; i < 400 && !existsSync(portFile); i++) await sleep(100);   // до 40 с на холодний старт
  if (!existsSync(portFile)) throw new Error('Chrome не відкрив порт налагодження за 40 с');
  const port = readFileSync(portFile, 'utf8').split('\n')[0].trim();
  return { proc, dir, port };
}

function cdp(wsUrl) {
  const ws = new WebSocket(wsUrl);
  let id = 0; const pending = new Map(), waiters = [], errors = [];
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    else if (m.method) {
      if (m.method === 'Runtime.exceptionThrown') errors.push(m.params.exceptionDetails);
      waiters.filter(w => w.method === m.method).forEach(w => { w.res(m); waiters.splice(waiters.indexOf(w), 1); });
    }
  };
  const ready = new Promise(r => { ws.onopen = r; });
  return {
    ready,
    errors,
    send: (method, params = {}) => new Promise(res => { const i = ++id; pending.set(i, res); ws.send(JSON.stringify({ id: i, method, params })); }),
    once: (method, ms = 30000) => new Promise((res, rej) => { waiters.push({ method, res }); setTimeout(() => rej(new Error('timeout ' + method)), ms); }),
    close: () => ws.close(),
  };
}

async function measure(port, url) {
  const t = await (await fetch(`http://127.0.0.1:${port}/json/new?about:blank`, { method: 'PUT' })).json();
  const c = cdp(t.webSocketDebuggerUrl); await c.ready;
  await c.send('Emulation.setDeviceMetricsOverride', { width: WIDTH, height: HEIGHT, deviceScaleFactor: 2, mobile: false });
  await c.send('Page.enable');
  await c.send('Runtime.enable');                       // pageerror = Runtime.exceptionThrown
  const loaded = c.once('Page.loadEventFired', 45000);
  await c.send('Page.navigate', { url });
  await loaded; await sleep(1500);                     // віджети й шрифти
  const ev = async expr => JSON.parse((await c.send('Runtime.evaluate',
    { expression: expr, returnByValue: true, awaitPromise: true })).result.result.value);
  const m = await ev(MEASURE);
  m.code = await ev(CODE_UI);
  m.open = await ev(MEASURE);                           // та сама перевірка з розкритим кодом
  m.pageerrors = c.errors.map(e => (e.exception && e.exception.description || e.text || '').split('\n')[0]);
  c.close();
  await fetch(`http://127.0.0.1:${port}/json/close/${t.id}`);
  return m;
}

// Скільки блоків коду очікувати на сторінці: <CodeFold> у зібраному lectures/NN.md.
function expected(p) {
  const f = join(SITE, p.replace(/^\//, '') + '.md');
  if (p === '/' || !existsSync(f)) return { folds: 0, frags: 0 };
  const md = readFileSync(f, 'utf8');
  return { folds: (md.match(/<CodeFold /g) || []).length, frags: (md.match(/ fragment>/g) || []).length };
}

const { proc, dir, port } = await launch();
let failed = 0, worstAll = 0, foldsAll = 0, fragsAll = 0, errsAll = 0;
console.log(`ширина ${WIDTH} px · ${BASE}`);
try {
  for (const p of PAGES) {
    const m = await measure(port, BASE + p);
    const k = m.code, exp = expected(p), o = m.open;
    const codeBad = k.openByDefault + k.noOutput + k.hiddenOutput + k.notOpened +
      (k.folds !== exp.folds || k.frags !== exp.frags ? 1 : 0);
    const ok = m.overflow === 0 && m.offenders === 0 && o.overflow === 0 && o.offenders === 0 &&
      codeBad === 0 && m.pageerrors.length === 0;
    if (!ok) failed++;
    foldsAll += k.folds; fragsAll += k.frags; errsAll += m.pageerrors.length;
    worstAll = Math.max(worstAll, m.overflow, m.worst, o.overflow, o.worst);
    const g = Object.entries({ ...m.groups, ...o.groups }).sort((a, b) => b[1].max - a[1].max).slice(0, 3)
      .map(([key, v]) => `${key}×${v.n} (до ${v.max} px)`).join(', ');
    const code = k.folds ? ` · код ${k.folds - k.frags}+${k.frags}ф` : '';
    console.log(`${ok ? '  ok ' : '  !! '} ${p.padEnd(13)} прокрутка ${String(Math.max(m.overflow, o.overflow)).padStart(4)} px · порушників ${String(m.offenders + o.offenders).padStart(3)}${code}${g ? ' · ' + g : ''}`);
    if (codeBad) console.log(`       код: знайдено ${k.folds} (фрагментів ${k.frags}), очікувано ${exp.folds} (${exp.frags}); ` +
      `розкриті одразу ${k.openByDefault}, без виводу ${k.noOutput}, вивід схований ${k.hiddenOutput}, не розкрились ${k.notOpened}`);
    for (const e of m.pageerrors) console.log(`       pageerror: ${e}`);
  }
} finally {
  proc.kill(); try { rmSync(dir, { recursive: true, force: true }); } catch {}
}
console.log(`\nнайбільше переповнення: ${worstAll} px (згорнутий і розкритий код)`);
console.log(`блоків коду: ${foldsAll} (фрагментів ${fragsAll}), pageerror: ${errsAll}`);
console.log(`проблем: ${failed}`);
process.exit(failed ? 1 : 0);
