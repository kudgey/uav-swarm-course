<script setup lang="ts">
/**
 * Дослідження проти використання: ε-жадібний вибір на багаторукому бандиті.
 *
 * Задача з картки «Дослідження проти використання» модуля 04: п'ять важелів
 * із різною середньою винагородою, агент не знає яких. Криві усереднені
 * по 200 незалежних прогонах — саме тому вони гладкі, а не зубчасті.
 */
import { ref, computed } from 'vue'

/** Справжні середні винагороди важелів; агент їх не бачить. */
const TRUE = [1.0, 1.6, 2.2, 1.3, 0.7]
const BEST = 2.2
const STEPS = 500
const RUNS = 200

const eps = ref(0.1)

/** Детермінований шум: та сама картинка при кожному відкритті. */
function rnd(seed: number) {
  let s = seed >>> 0
  return () => {
    s = (s * 1664525 + 1013904223) >>> 0
    return s / 4294967296
  }
}

/** Один прогін ε-жадібного агента; повертає винагороду на кожному кроці. */
function play(e: number, seed: number) {
  const r = rnd(seed)
  const q = new Array(TRUE.length).fill(0)
  const n = new Array(TRUE.length).fill(0)
  const out = new Array(STEPS)
  let optimal = 0
  for (let t = 0; t < STEPS; t++) {
    let a: number
    if (r() < e) a = Math.floor(r() * TRUE.length)
    else {
      let best = 0
      for (let i = 1; i < TRUE.length; i++) if (q[i] > q[best]) best = i
      a = best
    }
    if (a === 2) optimal++
    // винагорода — справжнє середнє плюс шум одиничної дисперсії
    const noise = (r() + r() + r() + r() - 2) * 0.9
    const reward = TRUE[a] + noise
    n[a]++
    q[a] += (reward - q[a]) / n[a]
    out[t] = reward
  }
  return { out, optimalShare: optimal / STEPS }
}

const curves = computed(() => {
  const show = [0, 0.01, 0.1, 0.3]
  return show.map((e) => {
    const avg = new Array(STEPS).fill(0)
    let opt = 0
    for (let run = 0; run < RUNS; run++) {
      const { out, optimalShare } = play(e, 7919 + run * 104729)
      for (let t = 0; t < STEPS; t++) avg[t] += out[t] / RUNS
      opt += optimalShare / RUNS
    }
    return { e, avg, opt }
  })
})

/** Крива для поточного значення повзунка. */
const current = computed(() => {
  const avg = new Array(STEPS).fill(0)
  let opt = 0
  for (let run = 0; run < RUNS; run++) {
    const { out, optimalShare } = play(eps.value, 7919 + run * 104729)
    for (let t = 0; t < STEPS; t++) avg[t] += out[t] / RUNS
    opt += optimalShare / RUNS
  }
  return { avg, opt }
})

const finalAvg = computed(() => {
  const a = current.value.avg
  return a.slice(-100).reduce((x, y) => x + y, 0) / 100
})
const regret = computed(() => (BEST - finalAvg.value) * 100)

const W = 460, H = 160
const px = (t: number) => 34 + (t / STEPS) * (W - 46)
const py = (v: number) => H - 20 - ((v - 0.5) / 2.0) * (H - 34)

function path(avg: number[]) {
  // згладжуємо ковзним вікном 15 кроків, інакше лінія рябить
  const s: string[] = []
  for (let t = 7; t < STEPS - 7; t += 3) {
    let m = 0
    for (let k = t - 7; k <= t + 7; k++) m += avg[k] / 15
    s.push(`${s.length ? 'L' : 'M'}${px(t).toFixed(1)},${py(m).toFixed(1)}`)
  }
  return s.join(' ')
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Дослідження проти використання</div>
        <div class="lab__sub">
          П'ять важелів, агент не знає їхньої якості. Ймовірність ε він пробує
          випадковий, інакше бере найкращий за поточною оцінкою.
          Криві усереднені по {{ RUNS }} прогонах.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Дослідження ε <b>{{ eps.toFixed(2) }}</b></span>
        <input v-model.number="eps" type="range" min="0" max="0.5" step="0.01" />
      </label>
    </div>

    <svg class="ep__plot" :viewBox="`0 0 ${W} ${H}`" aria-label="Середня винагорода за крок">
      <line :x1="34" :y1="py(BEST)" :x2="W - 12" :y2="py(BEST)" class="ep__ideal" />
      <text :x="W - 12" :y="py(BEST) - 4" class="ep__tick" text-anchor="end">
        межа {{ BEST.toFixed(1) }}
      </text>

      <path v-for="c in curves" :key="c.e" :d="path(c.avg)" class="ep__ghost" />
      <path :d="path(current.avg)" class="ep__line" />

      <text x="34" :y="H - 5" class="ep__tick">0</text>
      <text :x="W - 12" :y="H - 5" class="ep__tick" text-anchor="end">{{ STEPS }} кроків</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ finalAvg.toFixed(2) }}</b>
        <span>середня винагорода на останніх 100 кроках</span>
      </div>
      <div class="lab__stat">
        <b>{{ (current.opt * 100).toFixed(0) }} %</b>
        <span>часу на найкращому важелі</span>
      </div>
      <div class="lab__stat" :class="regret > 40 ? 'is-warm' : 'is-green'">
        <b>{{ regret.toFixed(0) }}</b>
        <span>жаль за 100 кроків</span>
      </div>
    </div>

    <p class="lab__note">
      Поставте ε = 0: агент чіпляється за перший важіль, який випадково дав добру
      винагороду, і більше нічого не пробує — крива застигає нижче межі.
      Поставте ε = 0,5: половину кроків він витрачає на явно гірші важелі й теж
      програє. Оптимум лежить між ними, і саме тому в лекції ε зменшують
      із часом: спершу дослідження, потім використання.
    </p>
  </div>
</template>

<style scoped>
.ep__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; }
.ep__line { fill: none; stroke: var(--uk-accent); stroke-width: 2.2; }
.ep__ghost { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1; opacity: 0.25; }
.ep__ideal { stroke: var(--uk-green); stroke-width: 1; stroke-dasharray: 4 3; }
.ep__tick { fill: var(--vp-c-text-3); font-size: 9px; font-family: var(--vp-font-family-mono); }
</style>
