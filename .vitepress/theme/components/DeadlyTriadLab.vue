<script setup lang="ts">
/**
 * Смертельна тріада на прикладі Sutton, Barto (2018, розд. 11.2): «w → 2w».
 *
 * Модуль 05, картка «Тріада на числах». Два стани: A з ознакою 1 і B з ознакою 2,
 * тож за лінійної апроксимації V(A) = w, V(B) = 2w. Перехід A → B дає винагороду 0,
 * B → кінець — теж 0, тож справжні цінності обох станів — нуль.
 * Три перемикачі прибирають по одному складнику тріади. Арифметика та сама, що
 * у функції run() блоку коду картки, тож за γ = 0,9 числа збігаються з його виводом.
 */
import { ref, computed } from 'vue'

const ALPHA = 0.1
const W0 = 10
const N = 100
const approx = ref(true)
const boot = ref(true)
const offp = ref(true)
const gamma = ref(0.9)

/** Траєкторії V(A) і V(B) після кожного оновлення. */
const path = computed(() => {
  const g = gamma.value
  let w = W0, vA = W0, vB = 2 * W0
  const A = [W0], B = [2 * W0]
  for (let k = 0; k < N; k++) {
    if (approx.value) {
      // спільний параметр w: V(A) = 1·w, V(B) = 2·w
      w += ALPHA * ((boot.value ? g * 2 * w : 0) - w) * 1
      if (!offp.value) w += ALPHA * (0 - 2 * w) * 2
      A.push(w); B.push(2 * w)
    } else {
      // таблиця: окремі числа для A і B
      vA += ALPHA * ((boot.value ? g * vB : 0) - vA)
      if (!offp.value) vB += ALPHA * (0 - vB)
      A.push(vA); B.push(vB)
    }
  }
  return { A, B }
})

const final = computed(() => path.value.A[N])
const diverges = computed(() => !Number.isFinite(final.value) || Math.abs(final.value) > 1e3)
const nOn = computed(() => [approx.value, boot.value, offp.value].filter(Boolean).length)
const factor = computed(() =>
  approx.value && boot.value && offp.value ? 1 + ALPHA * (2 * gamma.value - 1) : null
)

// графік: логарифмічна вісь |V| від 0,01 до 1e5
const W = 460, H = 200, X0 = 40, Y0 = 12, PW = W - X0 - 10, PH = H - Y0 - 26
const LMIN = -2, LMAX = 5
const px = (k: number) => X0 + (k / N) * PW
const py = (v: number) => {
  const l = Math.log10(Math.max(Math.abs(v), 10 ** LMIN))
  return Y0 + (1 - (Math.min(l, LMAX) - LMIN) / (LMAX - LMIN)) * PH
}
const line = (arr: number[]) => arr.map((v, k) => `${k ? 'L' : 'M'}${px(k).toFixed(1)},${py(v).toFixed(1)}`).join(' ')
const TICKS = [-2, -1, 0, 1, 2, 3, 4, 5]
const tickLabel = (l: number) => (l < 0 ? (10 ** l).toString().replace('.', ',') : (10 ** l).toLocaleString('uk-UA'))
const SHOW = [10, 20, 50, 100]
const fmt = (v: number) =>
  !Number.isFinite(v) ? '∞' : Math.abs(v) >= 1e5 ? v.toExponential(1).replace('.', ',') : v.toFixed(2).replace('.', ',').replace('-', '−')

function preset(a: boolean, b: boolean, o: boolean) {
  approx.value = a; boot.value = b; offp.value = o; gamma.value = 0.9
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Смертельна тріада: приберіть будь-який складник</div>
        <div class="lab__sub">
          Стан A (ознака 1) переходить у стан B (ознака 2) з винагородою 0, далі кінець.
          Справжні цінності обох станів — 0. Старт: V(A) = 10, α = 0,1.
        </div>
      </div>
      <button class="lab__btn" @click="preset(true, true, true)">Усі три</button>
    </div>

    <div class="dt__toggles">
      <button type="button" class="dt__tg" :class="{ on: approx }" @click="approx = !approx">
        <b>Апроксимація</b>
        <span>{{ approx ? 'спільний w: V(A) = w, V(B) = 2w' : 'таблиця: окремі V(A) і V(B)' }}</span>
      </button>
      <button type="button" class="dt__tg" :class="{ on: boot }" @click="boot = !boot">
        <b>Бутстреп</b>
        <span>{{ boot ? 'ціль r + γ·V(B) — власна оцінка' : 'ціль — справжня віддача 0' }}</span>
      </button>
      <button type="button" class="dt__tg" :class="{ on: offp }" @click="offp = !offp">
        <b>Off-policy</b>
        <span>{{ offp ? 'оновлюємо лише перехід A → B' : 'оновлюємо й B → кінець, як на шляху агента' }}</span>
      </button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Дисконт γ <b>{{ gamma.toFixed(2).replace('.', ',') }}</b></span>
        <input v-model.number="gamma" type="range" min="0.1" max="0.99" step="0.01" />
      </label>
    </div>

    <svg class="dt__plot" :viewBox="`0 0 ${W} ${H}`" aria-label="Оцінки V(A) і V(B) після кожного оновлення">
      <g v-for="l in TICKS" :key="l">
        <line :x1="X0" :x2="X0 + PW" :y1="py(10 ** l)" :y2="py(10 ** l)" class="dt__grid" />
        <text :x="X0 - 4" :y="py(10 ** l) + 3" class="dt__tick" text-anchor="end">{{ tickLabel(l) }}</text>
      </g>
      <path :d="line(path.B)" class="dt__b" />
      <path :d="line(path.A)" class="dt__a" :class="{ bad: diverges }" />
      <text :x="X0" :y="H - 6" class="dt__tick">0</text>
      <text :x="X0 + PW" :y="H - 6" class="dt__tick" text-anchor="end">{{ N }} оновлень</text>
      <text :x="X0 + 6" :y="Y0 + 10" class="dt__tick">|V|, логарифмічна шкала</text>
    </svg>
    <div class="dt__legend"><i class="a" :class="{ bad: diverges }"></i> V(A) <i class="b"></i> V(B)</div>

    <div class="lab__stats">
      <div class="lab__stat" :class="diverges ? 'is-warm' : 'is-green'">
        <b>{{ diverges ? 'розходиться' : 'обмежена' }}</b>
        <span>складників увімкнено: {{ nOn }} з 3</span>
      </div>
      <div class="lab__stat">
        <b>{{ fmt(final) }}</b>
        <span>V(A) після {{ N }} оновлень</span>
      </div>
      <div class="lab__stat">
        <b>{{ factor === null ? '—' : '×' + factor.toFixed(2).replace('.', ',') }}</b>
        <span>множник w за одне оновлення: 1 + α(2γ − 1)</span>
      </div>
    </div>

    <table class="dt__tab">
      <thead><tr><th>оновлень</th><th v-for="k in SHOW" :key="k">{{ k }}</th></tr></thead>
      <tbody><tr><td>V(A)</td><td v-for="k in SHOW" :key="k">{{ fmt(path.A[k]) }}</td></tr></tbody>
    </table>

    <p class="lab__note">
      <template v-if="diverges">
        Усі три складники разом: перехід A → B щоразу «обіцяє» більше, ніж є, бо V(B) = 2w
        зростає разом із w, а з самого B оцінку ніхто не перевіряє. За γ ≤ 0,5 множник не більший
        за 1 — спробуйте повзунок.
      </template>
      <template v-else-if="!approx && boot && offp">
        Таблиця: V(A) прямує до γ·V(B) = {{ fmt(gamma * 20) }}. Помилка лишається, бо B ніхто не
        оновлює, але вона не росте — оновлення A більше не змінює оцінку B.
      </template>
      <template v-else>
        Досить прибрати один складник, і оцінка вже не вибухає. Порівняйте з рядками таблиці
        у виводі коду над віджетом.
      </template>
    </p>
  </div>
</template>

<style scoped>
.dt__toggles { display: grid; grid-template-columns: repeat(auto-fit, minmax(11rem, 1fr)); gap: 0.5rem; margin: 0.6rem 0 0.4rem; }
.dt__tg {
  font: inherit; text-align: left; display: grid; gap: 0.15rem; padding: 0.5rem 0.7rem; border-radius: 10px;
  border: 1px dashed var(--uk-line); background: transparent; color: var(--vp-c-text-2); cursor: pointer;
}
.dt__tg b { font-size: 0.9rem; color: var(--vp-c-text-1); }
.dt__tg span { font-size: 0.78rem; }
.dt__tg.on { border-style: solid; border-color: var(--uk-warm); background: color-mix(in srgb, var(--uk-warm) 10%, transparent); }
.dt__tg:focus-visible { outline: 2px solid var(--uk-accent); outline-offset: 2px; }
.dt__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; margin-top: 0.3rem; }
.dt__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.dt__tick { fill: var(--vp-c-text-3); font-size: 9px; font-family: var(--vp-font-family-mono); }
.dt__a { fill: none; stroke: var(--uk-accent); stroke-width: 2.4; }
.dt__a.bad { stroke: var(--uk-warm); }
.dt__b { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1.4; stroke-dasharray: 4 3; }
.dt__legend { font-size: 0.78rem; color: var(--vp-c-text-2); display: flex; gap: 0.4rem; align-items: center; margin: 0.25rem 0 0.4rem; }
.dt__legend i { display: inline-block; width: 18px; height: 0; border-top: 2.4px solid var(--uk-accent); }
.dt__legend i.a.bad { border-top-color: var(--uk-warm); }
.dt__legend i.b { border-top: 1.4px dashed var(--vp-c-text-3); margin-left: 0.8rem; }
.dt__tab { margin: 0.6rem 0 0; font-variant-numeric: tabular-nums; }
.dt__tab td, .dt__tab th { font-family: var(--vp-font-family-mono); font-size: 0.8rem; text-align: right; }
</style>
