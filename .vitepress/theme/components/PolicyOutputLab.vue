<script setup lang="ts">
/**
 * Що видає мережа політики: три ймовірності проти щільності гауссіана.
 *
 * Модуль 05, картка «Навіщо вчити політику напряму». Числа — справжні мережі
 * лекції (зерно 0): актор A2C із трьома рівнями тяги (gamma_course/viz/m05_pg_record.py
 * → data/pgsteps.json) і політика PPO з плавною тягою (m05_flight_record.py →
 * data/ppoout.json). Обидва скрипти повторюють прогони лекції й звіряють криві.
 * Віджет нічого не налаштовує: лише перемикає записані стани й етапи та дає
 * навести курсор на криву, щоб прочитати щільність і ймовірність відрізка.
 */
import { ref, computed } from 'vue'
import pg from '../data/pgsteps.json'
import pout from '../data/ppoout.json'

const ACT: number[] = pg.actions
const ANAME = ['менше тяги', 'висіти', 'більше тяги']
const STATES = [
  { name: 'нижче цілі й опускається', s: '(−0,13; −0,12)' },
  { name: 'точно на цілі', s: '(0; 0)' },
  { name: 'вище цілі й піднімається', s: '(0,13; 0,12)' },
]
const A2C = pg.a2c_out as { steps: number; p: number[][] }[]
const PPO = pout.stages as { steps: number; mu: number[]; sigma: number }[]
const ppoAt = (n: number) => PPO.find((x) => x.steps === n)!
const STAGES = [
  { name: 'до навчання', a2c: A2C[0], ppo: ppoAt(0) },
  { name: 'після 51 тис. кроків', a2c: A2C[1], ppo: ppoAt(51200) },
  { name: 'наприкінці', a2c: A2C[2], ppo: PPO[PPO.length - 1] },
]

const si = ref(0)
const st = ref(2)
const probs = computed(() => STAGES[st.value].a2c.p[si.value])
// політика PPO видає μ і σ для дії a ∈ [−1; 1]; тяга u = (a + 1) / 2
const muU = computed(() => (STAGES[st.value].ppo.mu[si.value] + 1) / 2)
const sgU = computed(() => STAGES[st.value].ppo.sigma / 2)

const SQ2PI = Math.sqrt(2 * Math.PI)
const dens = (u: number) => Math.exp(-((u - muU.value) ** 2) / (2 * sgU.value ** 2)) / (sgU.value * SQ2PI)
/** Функція помилок (Abramowitz–Stegun 7.1.26, похибка < 1,5·10⁻⁷). */
function erf(x: number) {
  const t = 1 / (1 + 0.3275911 * Math.abs(x))
  const y = 1 - (((((1.061405429 * t - 1.453152027) * t) + 1.421413741) * t - 0.284496736) * t + 0.254829592) * t * Math.exp(-x * x)
  return x >= 0 ? y : -y
}
const cdf = (u: number) => 0.5 * (1 + erf((u - muU.value) / (sgU.value * Math.SQRT2)))
const peak = computed(() => 1 / (sgU.value * SQ2PI))
const below = computed(() => cdf(0))
const above = computed(() => 1 - cdf(1))

// спільна вісь тяги для обох графіків
const U0 = -0.25, U1 = 1.25
const W = 480, X0 = 44, PW = W - X0 - 12
const px = (u: number) => X0 + ((u - U0) / (U1 - U0)) * PW
const HB = 120, YB0 = 10, PHB = HB - YB0 - 22
const pyB = (p: number) => YB0 + (1 - p) * PHB
const HG = 170, YG0 = 12, PHG = HG - YG0 - 26
const yMax = computed(() => niceMax(peak.value * 1.12))
const pyG = (d: number) => YG0 + (1 - d / yMax.value) * PHG
function niceMax(v: number) {
  const e = 10 ** Math.floor(Math.log10(v))
  for (const m of [1, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (m * e >= v) return m * e
  return 10 * e
}
const yTicks = computed(() => [0, 0.25, 0.5, 0.75, 1].map((k) => k * yMax.value))
const curve = computed(() => {
  const pts: string[] = []
  const n = 360
  for (let k = 0; k <= n; k++) {
    const u = U0 + ((U1 - U0) * k) / n
    pts.push(`${k ? 'L' : 'M'}${px(u).toFixed(1)},${pyG(dens(u)).toFixed(1)}`)
  }
  return pts.join(' ')
})
function area(a: number, b: number) {
  const n = 160
  let d = `M${px(a).toFixed(1)},${pyG(0).toFixed(1)}`
  for (let k = 0; k <= n; k++) {
    const u = a + ((b - a) * k) / n
    d += ` L${px(u).toFixed(1)},${pyG(dens(u)).toFixed(1)}`
  }
  return d + ` L${px(b).toFixed(1)},${pyG(0).toFixed(1)} Z`
}

// курсор: за замовчуванням — центр кривої (або найближча точка в межах осі)
const hu = ref<number | null>(null)
const cur = computed(() => Math.min(U1 - 0.01, Math.max(U0 + 0.01, hu.value ?? muU.value)))
const HALF = 0.005  // половина ширини відрізка тяги
const pSeg = computed(() => cdf(cur.value + HALF) - cdf(cur.value - HALF))
function onMove(ev: PointerEvent) {
  const svg = ev.currentTarget as SVGSVGElement
  const r = svg.getBoundingClientRect()
  const x = ((ev.clientX - r.left) / r.width) * W
  hu.value = U0 + ((x - X0) / PW) * (U1 - U0)
}

const f = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const pct = (v: number) => (v < 0.0005 ? '0' : v > 0.9995 ? '100' : (v * 100).toFixed(v < 0.1 ? 1 : 0).replace('.', ','))
const big = (v: number) => (v === 0 ? '0' : v >= 10 ? v.toFixed(1) : v >= 1 ? v.toFixed(2) : v.toFixed(3)).replace('.', ',')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Що видає мережа політики: ймовірності чи щільність</div>
        <div class="lab__sub">
          Справжні мережі лекції, зерно 0: актор A2C із трьома рівнями тяги й політика PPO з плавною тягою.
          Обидві отримують той самий стан; горизонтальна вісь — тяга u від 0 до 1.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(x, i) in STATES" :key="x.name" type="button" class="lab__pill" :class="{ 'is-on': si === i }"
              @click="si = i; hu = null">{{ x.name }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="(x, i) in STAGES" :key="x.name" type="button" class="lab__pill" :class="{ 'is-on': st === i }"
              @click="st = i; hu = null">{{ x.name }}</button>
    </div>

    <div class="po__cap"><b>Три рівні тяги (A2C, {{ STAGES[st].a2c.steps.toLocaleString('uk-UA') }} кроків).</b>
      Вихід мережі — три ймовірності, їхня сума 1. Стан s = {{ STATES[si].s }}.</div>
    <svg class="po__plot" :viewBox="`0 0 ${W} ${HB}`" role="img" aria-label="Ймовірності трьох рівнів тяги">
      <line v-for="p in [0, 0.5, 1]" :key="p" :x1="X0" :x2="X0 + PW" :y1="pyB(p)" :y2="pyB(p)" class="po__grid" />
      <text v-for="p in [0, 0.5, 1]" :key="'t' + p" :x="X0 - 5" :y="pyB(p) + 3" class="po__tick" text-anchor="end">{{ f(p, 1) }}</text>
      <g v-for="(u, i) in ACT" :key="i">
        <rect :x="px(u) - 14" :y="pyB(probs[i])" width="28" :height="pyB(0) - pyB(probs[i])" class="po__bar" />
        <text :x="px(u)" :y="pyB(probs[i]) - 4" class="po__val" text-anchor="middle">{{ pct(probs[i]) }}&nbsp;%</text>
        <text :x="px(u)" :y="HB - 6" class="po__tick" text-anchor="middle">{{ f(u, 3) }}</text>
      </g>
      <text :x="X0 + PW" :y="YB0 + 8" class="po__tick" text-anchor="end">ймовірність</text>
    </svg>

    <div class="po__cap"><b>Плавна тяга (PPO, {{ STAGES[st].ppo.steps.toLocaleString('uk-UA') }} кроків).</b>
      Вихід мережі — центр μ і ширина σ гауссіана. Наведіть курсор або торкніться кривої.</div>
    <svg class="po__plot po__gauss" :viewBox="`0 0 ${W} ${HG}`" role="img"
         aria-label="Щільність нормального розподілу тяги" @pointermove="onMove" @pointerdown="onMove">
      <rect :x="px(U0)" :y="YG0" :width="px(0) - px(U0)" :height="PHG" class="po__out" />
      <rect :x="px(1)" :y="YG0" :width="px(U1) - px(1)" :height="PHG" class="po__out" />
      <text :x="(px(U0) + px(0)) / 2" :y="YG0 + 12" class="po__tick" text-anchor="middle">обрізається до 0</text>
      <text :x="(px(1) + px(U1)) / 2" :y="YG0 + 12" class="po__tick" text-anchor="middle">обрізається до 1</text>
      <g v-for="(y, k) in yTicks" :key="k">
        <line :x1="X0" :x2="X0 + PW" :y1="pyG(y)" :y2="pyG(y)" class="po__grid" />
        <text :x="X0 - 5" :y="pyG(y) + 3" class="po__tick" text-anchor="end">{{ big(y) }}</text>
      </g>
      <path :d="area(cur - HALF, cur + HALF)" class="po__seg" />
      <path :d="curve" class="po__curve" />
      <line :x1="px(cur)" :x2="px(cur)" :y1="YG0" :y2="pyG(0)" class="po__cursor" />
      <circle :cx="px(cur)" :cy="pyG(dens(cur))" r="3.5" class="po__dot" />
      <text v-for="u in [0, 0.25, 0.5, 0.75, 1]" :key="'u' + u" :x="px(u)" :y="HG - 8" class="po__tick" text-anchor="middle">{{ f(u, 2) }}</text>
      <text :x="X0 + PW" :y="HG - 8" class="po__tick" text-anchor="end">тяга u</text>
      <text :x="px(0) + 4" :y="YG0 + 26" class="po__tick">щільність</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ f(muU) }}</b><span>центр μ, тяга</span></div>
      <div class="lab__stat"><b>{{ f(sgU) }}</b><span>ширина σ, тяга</span></div>
      <div class="lab__stat" :class="{ 'is-warm': peak > 1 }"><b>{{ big(peak) }}</b><span>висота піку{{ peak > 1 ? ' — більша за 1' : '' }}</span></div>
    </div>
    <p class="lab__note">
      У точці u = {{ f(cur) }} щільність {{ big(dens(cur)) }}. Ймовірність, що жереб дасть тягу
      між {{ f(cur - HALF) }} і {{ f(cur + HALF) }}, — площа зафарбованої смужки: {{ pct(pSeg) }}&nbsp;%.
      Приблизно це висота × ширина: {{ big(dens(cur)) }} × 0,01 = {{ pct(dens(cur) * 2 * HALF) }}&nbsp;%.
      <template v-if="below + above > 0.005"> Частина жеребів падає за межі 0…1 ({{ pct(below + above) }}&nbsp;%): таку тягу середовище обріже.</template>
      <template v-if="muU < 0 || muU > 1"> Центр кривої лежить поза межами тяги: майже кожен жереб обріжеться до {{ muU < 0 ? '0' : '1' }}.</template>
    </p>
  </div>
</template>

<style scoped>
.po__cap { font-size: 0.86rem; color: var(--vp-c-text-2); margin: 0.6rem 0 0.2rem; }
.po__cap b { color: var(--vp-c-text-1); }
.po__plot { width: 100%; height: auto; display: block; background: var(--uk-fill); border-radius: 10px; }
.po__gauss { touch-action: pan-y; cursor: crosshair; }
.po__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.po__tick { fill: var(--vp-c-text-3); font-size: 10px; font-family: var(--vp-font-family-mono); }
.po__val { fill: var(--vp-c-text-1); font-size: 11px; font-weight: 600; font-family: var(--vp-font-family-mono); }
.po__bar { fill: var(--uk-accent); opacity: 0.8; }
.po__out { fill: var(--uk-line); opacity: 0.45; }
.po__curve { fill: none; stroke: var(--uk-accent); stroke-width: 2.2; }
.po__seg { fill: var(--uk-warm); opacity: 0.45; }
.po__cursor { stroke: var(--uk-warm); stroke-width: 1; stroke-dasharray: 3 3; }
.po__dot { fill: var(--uk-warm); }
</style>
