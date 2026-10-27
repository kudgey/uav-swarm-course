<script setup lang="ts">
/**
 * Політ зсередини: що бачить, що «думає» і що робить навчена політика на кожному з 242 кроків.
 *
 * Модуль 07, картка «3.7 Політ зсередини». Дані записав скрипт gamma_course/viz/mod07_policy_record.py:
 * той самий детермінований політ, що на анімації кроку 3 (зерно 1000), звірений з mod07_pyb.npz.
 * На кожному кроці — 12 чисел стану, активації двох шарів по 64 нейрони (у сотих), середні дії μ,
 * дії a після обрізання, оберти, тяга / вага, оцінка критика V і винагорода r.
 * 60 чисел історії — це дії a попередніх 15 кроків (скрипт перевіряє збіг зі спостереженням).
 * Віджет нічого не рахує сам, лише програє записані кроки.
 */
import { ref, computed, onUnmounted } from 'vue'
import data from '../data/policyflight.json'

type Frame = { s: number[]; h1: number[]; h2: number[]; mu: number[]; a: number[]; rpm: number[]; tw: number; v: number; r: number }
const F = data.frames as Frame[]
const N = F.length
const HZ = data.hz

const k = ref(0)
const playing = ref(false)
const fr = computed(() => F[k.value])

// історія: дії попередніх 15 кроків, найновіша праворуч; до старту — нулі
const hist = computed(() => {
  const out: number[][] = []
  for (let j = 15; j >= 1; j--) {
    const i = k.value - j
    out.push(i >= 0 ? F[i].a : [0, 0, 0, 0])
  }
  return out
})
const clipped = computed(() => fr.value.mu.some((x) => Math.abs(x) > 1))
const total = computed(() => F.slice(0, k.value + 1).reduce((s, f) => s + f.r, 0))

let raf = 0
let last = 0
function tick(now: number) {
  if (!playing.value) return
  if (!last) last = now
  const steps = Math.floor((now - last) / (1000 / HZ))
  if (steps > 0) {
    k.value = Math.min(N - 1, k.value + steps)
    last += (steps * 1000) / HZ
  }
  if (k.value >= N - 1) {
    playing.value = false
    return
  }
  raf = requestAnimationFrame(tick)
}
function play() {
  if (k.value >= N - 1) k.value = 0
  playing.value = true
  last = 0
  raf = requestAnimationFrame(tick)
}
function pause() {
  playing.value = false
  cancelAnimationFrame(raf)
}
function go(to: number) {
  pause()
  k.value = Math.max(0, Math.min(N - 1, to))
}
onUnmounted(() => cancelAnimationFrame(raf))

// −1 → синій, 0 → світло-сірий, +1 → червоний (як на рисунках лекції)
function col(v: number) {
  const x = Math.max(-1, Math.min(1, v))
  const mid = [238, 238, 242]
  const end = x > 0 ? [192, 57, 43] : [46, 111, 183]
  const t = Math.abs(x)
  const c = mid.map((m, i) => Math.round(m + (end[i] - m) * t))
  return `rgb(${c[0]},${c[1]},${c[2]})`
}
const fmt = (v: number, d = 2) => v.toFixed(d).replace('.', ',').replace('-', '−')
const sp = (v: number) => String(Math.round(v)).replace(/\B(?=(\d{3})+(?!\d))/g, '\u202f')

const ROWS = [
  { name: 'положення x, y, z', unit: 'м', i: 0, cls: 'pf__pos' },
  { name: 'крен, тангаж, рискання', unit: 'рад', i: 3, cls: 'pf__ang' },
  { name: 'швидкість x, y, z', unit: 'м/с', i: 6, cls: 'pf__vel' },
  { name: 'кутова швидкість', unit: 'рад/с', i: 9, cls: 'pf__rate' },
]

// графік висоти
const GW = 300, GH = 70, GX0 = 24
const gx = (i: number) => GX0 + (i / (N - 1)) * (GW - GX0 - 6)
const gy = (z: number) => 6 + (1 - Math.min(1.3, Math.max(0, z)) / 1.3) * (GH - 16)
const zPath = F.map((f, i) => `${i ? 'L' : 'M'}${gx(i).toFixed(1)},${gy(f.s[2]).toFixed(1)}`).join(' ')

// стовпчики μ: шкала −3…3, висота у відсотках від половини поля
const barH = (v: number) => (Math.min(3, Math.abs(v)) / 3) * 50
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Політ зсередини: що бачить, що «думає» і що робить політика</div>
        <div class="lab__sub">
          Записаний політ навченої політики (зерно 1000), 242 кроки по 33 мс. Пересувайте повзунок або
          запустіть політ: на кожному кроці 72 числа проходять через два шари по 64 нейрони й стають чотирма
          обертами моторів.
        </div>
      </div>
    </div>

    <div class="lab__controls pf__ctl">
      <div class="lab__pills">
        <button class="lab__pill is-on" type="button" @click="playing ? pause() : play()">{{ playing ? '⏸ пауза' : '▶ політ' }}</button>
        <button class="lab__pill" type="button" @click="go(k + 1)">+1 крок</button>
        <button class="lab__pill" type="button" @click="go(0)">0 с</button>
        <button class="lab__pill" type="button" @click="go(30)">1 с</button>
        <button class="lab__pill" type="button" @click="go(60)">2 с</button>
        <button class="lab__pill" type="button" @click="go(120)">4 с</button>
      </div>
      <label class="lab__ctl">
        <span>Крок <b>{{ k + 1 }} / {{ N }}</b> · {{ fmt(k / HZ, 2) }} с</span>
        <input v-model.number="k" type="range" min="0" :max="N - 1" step="1" @input="pause" />
      </label>
    </div>

    <div class="pf__grid">
      <section class="pf__card pf__wide">
        <div class="pf__h">1. Бачить: 72 числа</div>
        <div class="pf__see">
          <table class="pf__tab">
            <tr v-for="row in ROWS" :key="row.name">
              <td :class="row.cls">{{ row.name }}, {{ row.unit }}</td>
              <td v-for="j in 3" :key="j" class="pf__num" :class="{ 'is-key': (row.i === 0 || row.i === 6) && j === 3 }">
                {{ fmt(fr.s[row.i + j - 1], 2) }}
              </td>
            </tr>
          </table>
          <div>
            <div class="pf__cap">+ 60 чисел: дії 15 попередніх кроків</div>
            <div class="pf__hist">
              <template v-for="m in 4" :key="m">
                <span class="pf__lab">м{{ m }}</span>
                <span v-for="(act, j) in hist" :key="j" class="pf__cell" :style="{ background: col(act[m - 1]) }" />
              </template>
            </div>
            <div class="pf__axis-lab"><span>0,5 с тому</span><span>щойно</span></div>
          </div>
        </div>
      </section>

      <section class="pf__card">
        <div class="pf__h">2. «Думає»: 64 + 64 нейрони</div>
        <div class="pf__layers">
          <div v-for="(layer, li) in [fr.h1, fr.h2]" :key="li">
            <div class="pf__nn">
              <span v-for="(v, i) in layer" :key="i" class="pf__cell" :style="{ background: col(v / 100) }" />
            </div>
            <div class="pf__cap pf__c">шар {{ li + 1 }}</div>
          </div>
        </div>
        <div class="pf__cap">клітинка — один нейрон, tanh(…): синій −1, червоний +1</div>
      </section>

      <section class="pf__card">
        <div class="pf__h">3. Робить: 4 мотори</div>
        <div class="pf__bars">
          <div class="pf__band" />
          <div class="pf__zero" />
          <div v-for="(mu, m) in fr.mu" :key="m" class="pf__col">
            <div class="pf__bar" :class="{ 'is-cut': Math.abs(mu) > 1 }"
                 :style="{ height: barH(mu) + '%', bottom: mu >= 0 ? '50%' : 50 - barH(mu) + '%' }" />
          </div>
        </div>
        <table class="pf__tab pf__out">
          <tr><td></td><td v-for="m in 4" :key="m" class="pf__num">м{{ m }}</td></tr>
          <tr><td>μ</td><td v-for="(x, m) in fr.mu" :key="m" class="pf__num" :class="{ 'is-cut': Math.abs(x) > 1 }">{{ fmt(x, 2) }}</td></tr>
          <tr><td>a</td><td v-for="(x, m) in fr.a" :key="m" class="pf__num">{{ fmt(x, 2) }}</td></tr>
          <tr><td>об/хв</td><td v-for="(x, m) in fr.rpm" :key="m" class="pf__num">{{ sp(x) }}</td></tr>
        </table>
        <div class="pf__cap">μ — вихід мережі, a — дія після обрізання; смуга — дозволені значення від −1 до 1, шкала стовпчиків ±3</div>
      </section>
    </div>

    <svg :viewBox="`0 0 ${GW} ${GH}`" class="pf__svg pf__plot" aria-label="Висота в часі">
      <line :x1="GX0" :x2="GW - 6" :y1="gy(1)" :y2="gy(1)" class="pf__target" />
      <line :x1="GX0" :x2="GW - 6" :y1="gy(0)" :y2="gy(0)" class="pf__axis" />
      <path :d="zPath" class="pf__z" />
      <circle :cx="gx(k)" :cy="gy(fr.s[2])" r="3" class="pf__dot" />
      <text :x="GX0 - 3" :y="gy(1) + 3" class="pf__tick" text-anchor="end">1 м</text>
      <text :x="GX0 - 3" :y="gy(0) + 3" class="pf__tick" text-anchor="end">0</text>
      <text :x="GX0" :y="GH - 1" class="pf__tick">0 с</text>
      <text :x="GW - 6" :y="GH - 1" class="pf__tick" text-anchor="end">8 с</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ fmt(fr.s[2]) }} м</b><span>висота; вгору {{ fmt(fr.s[8]) }} м/с</span></div>
      <div class="lab__stat" :class="fr.tw >= 1 ? 'is-warm' : ''"><b>{{ fmt(fr.tw) }}</b><span>тяга / вага</span></div>
      <div class="lab__stat"><b>{{ fmt(fr.v, 1) }}</b><span>критик V: очікувана віддача</span></div>
      <div class="lab__stat is-green"><b>{{ fmt(fr.r, 3) }}</b><span>винагорода r за крок</span></div>
      <div class="lab__stat"><b>{{ fmt(total, 1) }}</b><span>сума r досі (з 484)</span></div>
    </div>

    <p class="lab__note">
      <template v-if="clipped">
        Мережа просить більше, ніж дозволено (червоний стовпчик виходить за смугу [−1; 1]) — дію обрізано до межі.
        Так на старті апарат злітає на повних +5 % обертів, тобто з тягою 1,10 ваги.
      </template>
      <template v-else-if="fr.tw < 1">
        Тяга менша за вагу — апарат гальмує підйом або знижується до цілі.
      </template>
      <template v-else>
        Тяга трохи більша за вагу — апарат утримує висоту або підіймається.
      </template>
    </p>
  </div>
</template>

<style scoped>
.pf__ctl { align-items: center; }
.pf__grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 0.6rem; margin: 0.6rem 0; }
.pf__wide { grid-column: 1 / -1; }
.pf__card { background: var(--uk-fill); border-radius: 10px; padding: 0.5rem 0.7rem; min-width: 0; }
.pf__h { font-size: 0.85rem; font-weight: 600; margin-bottom: 0.3rem; }
.pf__cap { font-size: 0.75rem; color: var(--vp-c-text-2); margin: 0.3rem 0 0.2rem; }
.pf__c { text-align: center; }
.pf__see { display: grid; grid-template-columns: minmax(0, 1.5fr) minmax(0, 1fr); gap: 0.4rem 1rem; align-items: start; }
.pf__tab { width: 100%; border-collapse: collapse; font-size: 0.78rem; margin: 0; display: table; }
.pf__tab td { border: none; padding: 0.08rem 0.25rem; background: transparent; white-space: nowrap; }
.pf__tab tr { background: transparent !important; border: none; }
.pf__see .pf__tab td:first-child { white-space: normal; font-size: 0.74rem; line-height: 1.25; }
.pf__num { text-align: right; font-family: var(--vp-font-family-mono); white-space: nowrap; }
.pf__num.is-key { font-weight: 700; }
.pf__num.is-cut { color: #C0392B; font-weight: 700; }
.pf__pos { color: var(--uk-green); }
.pf__ang { color: #9B59B6; }
.pf__vel { color: var(--uk-accent); }
.pf__rate { color: #C0392B; }
.pf__hist { display: grid; grid-template-columns: 1.8rem repeat(15, minmax(0, 1fr)); gap: 2px; }
.pf__lab { font-size: 0.72rem; color: var(--vp-c-text-2); font-family: var(--vp-font-family-mono); line-height: 1; align-self: center; }
.pf__cell { display: block; aspect-ratio: 1; border-radius: 2px; }
.pf__axis-lab { display: flex; justify-content: space-between; font-size: 0.72rem; color: var(--vp-c-text-2); margin-left: 1.9rem; }
.pf__layers { display: grid; grid-template-columns: 1fr 1fr; gap: 0.6rem; }
.pf__nn { display: grid; grid-template-columns: repeat(8, minmax(0, 1fr)); gap: 1px; }
.pf__bars { position: relative; height: 120px; display: grid; grid-template-columns: repeat(4, 1fr); gap: 0.5rem; padding: 0 0.3rem; }
.pf__band { position: absolute; left: 0; right: 0; top: calc(50% - 50% / 3); height: calc(100% / 3); background: var(--uk-accent-soft); border: 1px dashed var(--uk-accent); border-radius: 3px; }
.pf__zero { position: absolute; left: 0; right: 0; top: 50%; border-top: 1px solid var(--vp-c-text-3); }
.pf__col { position: relative; }
.pf__bar { position: absolute; left: 15%; right: 15%; background: var(--uk-accent); border-radius: 2px; }
.pf__bar.is-cut { background: #C0392B; }
.pf__out { margin-top: 0.4rem; font-size: 0.72rem; }
.pf__out td { padding: 0.08rem 0.12rem; }
.pf__svg { width: 100%; height: auto; display: block; }
.pf__plot { background: var(--uk-fill); border-radius: 10px; margin-bottom: 0.4rem; }
.pf__tick { fill: var(--vp-c-text-2); font-size: 9px; font-family: var(--vp-font-family-mono); }
.pf__axis { stroke: var(--vp-c-text-3); stroke-width: 0.8; }
.pf__target { stroke: var(--uk-green); stroke-width: 1; stroke-dasharray: 4 3; }
.pf__z { fill: none; stroke: var(--uk-accent); stroke-width: 1.4; }
.pf__dot { fill: var(--uk-warm); }
@media (max-width: 720px) {
  .pf__grid, .pf__see { grid-template-columns: minmax(0, 1fr); }
}
</style>
