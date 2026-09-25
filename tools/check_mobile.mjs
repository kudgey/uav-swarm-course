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
 * Залежностей немає: системний Chrome у headless-режимі + DevTools Protocol
 * через вбудований у Node 22 WebSocket. Шлях до Chrome можна задати змінною CHROME.
 */
import { spawn } from 'node:child_process';
import { mkdtempSync, readFileSync, existsSync, rmSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

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
  let id = 0; const pending = new Map(), waiters = [];
  ws.onmessage = ev => {
    const m = JSON.parse(ev.data);
    if (m.id && pending.has(m.id)) { pending.get(m.id)(m); pending.delete(m.id); }
    else if (m.method) waiters.filter(w => w.method === m.method).forEach(w => { w.res(m); waiters.splice(waiters.indexOf(w), 1); });
  };
  const ready = new Promise(r => { ws.onopen = r; });
  return {
    ready,
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
  const loaded = c.once('Page.loadEventFired', 45000);
  await c.send('Page.navigate', { url });
  await loaded; await sleep(1500);                     // віджети й шрифти
  const r = await c.send('Runtime.evaluate', { expression: MEASURE, returnByValue: true });
  c.close();
  await fetch(`http://127.0.0.1:${port}/json/close/${t.id}`);
  return JSON.parse(r.result.result.value);
}

const { proc, dir, port } = await launch();
let failed = 0, worstAll = 0;
console.log(`ширина ${WIDTH} px · ${BASE}`);
try {
  for (const p of PAGES) {
    const m = await measure(port, BASE + p);
    const ok = m.overflow === 0 && m.offenders === 0;
    if (!ok) failed++;
    worstAll = Math.max(worstAll, m.overflow, m.worst);
    const g = Object.entries(m.groups).sort((a, b) => b[1].max - a[1].max).slice(0, 3)
      .map(([k, v]) => `${k}×${v.n} (до ${v.max} px)`).join(', ');
    console.log(`${ok ? '  ok ' : '  !! '} ${p.padEnd(13)} прокрутка сторінки ${String(m.overflow).padStart(4)} px · порушників ${String(m.offenders).padStart(3)}${g ? ' · ' + g : ''}`);
  }
} finally {
  proc.kill(); try { rmSync(dir, { recursive: true, force: true }); } catch {}
}
console.log(`\nнайбільше переповнення: ${worstAll} px`);
console.log(`проблем: ${failed}`);
process.exit(failed ? 1 : 0);
