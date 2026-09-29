<script setup lang="ts">
/**
 * PPO: як обрізання зупиняє крок оновлення.
 *
 * Модуль 05, картка «PPO на числах». Цільова функція одного переходу:
 *   L(ρ) = min(ρ·Adv, clip(ρ, 1−ε, 1+ε)·Adv).
 * Повзунки задають відношення ймовірностей ρ, перевагу Adv і ширину коридору ε;
 * віджет показує, який із двох доданків вибирає min і чи тягне ще градієнт.
 * Кнопки-приклади — ті самі числа, що друкує блок коду на картці.
 */
import { ref, computed } from 'vue'

const rho = ref(1.73)
const adv = ref(2)
const eps = ref(0.2)

const clipped = (r: number) => Math.min(Math.max(r, 1 - eps.value), 1 + eps.value)
const objective = (r: number) => Math.min(r * adv.value, clipped(r) * adv.value)

/** Похідна за ρ: Adv, якщо min бере необрізаний доданок, інакше 0. */
const slope = computed(() => {
  const r = rho.value
  const outside = r < 1 - eps.value || r > 1 + eps.value
  return outside && clipped(r) * adv.value < r * adv.value ? 0 : adv.value
})

const verdict = computed(() => {
  if (adv.value === 0) return 'перевага нульова — оновлювати нічого'
  if (slope.value === 0)
    return adv.value > 0
      ? 'ймовірність уже зросла понад 1+ε — цей перехід більше не штовхає її вгору'
      : 'ймовірність уже впала нижче 1−ε — цей перехід більше не штовхає її вниз'
  if (adv.value > 0) return 'дія вдала: градієнт ще тягне ймовірність угору'
  return rho.value > 1 + eps.value
    ? 'невдалу дію зробили ймовірнішою — штраф не обрізають, градієнт тягне назад'
    : 'дія невдала: градієнт ще тягне ймовірність униз'
})

function preset(r: number, a: number) {
  rho.value = r
  adv.value = a
  eps.value = 0.2
}

const W = 460, H = 190, X0 = 34, Y_PAD = 14
const RMAX = 2.2
const ymin = computed(() => Math.min(0, RMAX * adv.value, -0.2) - 0.2)
const ymax = computed(() => Math.max(0, RMAX * adv.value, 0.2) + 0.2)
const px = (r: number) => X0 + (r / RMAX) * (W - X0 - 12)
const py = (v: number) => Y_PAD + ((ymax.value - v) / (ymax.value - ymin.value)) * (H - 2 * Y_PAD - 12)

function curve(f: (r: number) => number) {
  const s: string[] = []
  for (let i = 0; i <= 110; i++) {
    const r = (i / 110) * RMAX
    s.push(`${i ? 'L' : 'M'}${px(r).toFixed(1)},${py(f(r)).toFixed(1)}`)
  }
  return s.join(' ')
}
const fmt = (v: number, d = 2) => v.toFixed(d).replace('.', ',').replace('-', '−')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">PPO: де обрізання вимикає внесок переходу</div>
        <div class="lab__sub">
          Ціль одного переходу — менший із двох доданків: ρ·Adv і clip(ρ)·Adv.
          Там, де обраний доданок обрізаний, лінія горизонтальна: цей перехід
          більше не штовхає політику далі (інші переходи пакета — можуть).
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Відношення ρ <b>{{ fmt(rho) }}</b></span>
        <input v-model.number="rho" type="range" min="0" :max="RMAX" step="0.01" />
      </label>
      <label class="lab__ctl">
        <span>Перевага Adv <b>{{ fmt(adv, 1) }}</b></span>
        <input v-model.number="adv" type="range" min="-2" max="2" step="0.1" />
      </label>
      <label class="lab__ctl">
        <span>Коридор ε <b>{{ fmt(eps) }}</b></span>
        <input v-model.number="eps" type="range" min="0.05" max="0.4" step="0.01" />
      </label>
    </div>

    <div class="pc__presets">
      <button type="button" class="pc__btn" @click="preset(1.73, 2)">Приклад із коду: Adv = +2</button>
      <button type="button" class="pc__btn" @click="preset(0.47, -2)">Приклад із коду: Adv = −2</button>
    </div>

    <svg class="pc__plot" :viewBox="`0 0 ${W} ${H}`" aria-label="Цільова функція PPO залежно від ρ">
      <rect :x="px(1 - eps)" :y="Y_PAD" :width="px(1 + eps) - px(1 - eps)" :height="H - 2 * Y_PAD - 12" class="pc__band" />
      <line :x1="X0" :y1="py(0)" :x2="W - 12" :y2="py(0)" class="pc__axis" />
      <path :d="curve((r) => r * adv)" class="pc__raw" />
      <path :d="curve(objective)" class="pc__obj" />
      <circle :cx="px(rho)" :cy="py(objective(rho))" r="5" class="pc__dot" :class="{ 'is-stop': slope === 0 && adv !== 0 }" />
      <text :x="px(1)" :y="Y_PAD + 10" class="pc__tick" text-anchor="middle">коридор 1 ± ε</text>
      <text :x="X0" :y="H - 2" class="pc__tick">ρ = 0</text>
      <text :x="px(1)" :y="H - 2" class="pc__tick" text-anchor="middle">1</text>
      <text :x="W - 12" :y="H - 2" class="pc__tick" text-anchor="end">{{ fmt(RMAX, 1) }}</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ fmt(rho * adv) }}</b>
        <span>без обрізання, ρ·Adv</span>
      </div>
      <div class="lab__stat">
        <b>{{ fmt(objective(rho)) }}</b>
        <span>ціль PPO, менший доданок</span>
      </div>
      <div class="lab__stat" :class="slope === 0 && adv !== 0 ? 'is-warm' : 'is-green'">
        <b>{{ fmt(slope, 1) }}</b>
        <span>нахил за ρ: 0 — внесок цього переходу в градієнт нульовий</span>
      </div>
    </div>

    <p class="lab__note">{{ verdict }}.</p>
  </div>
</template>

<style scoped>
.pc__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; }
.pc__band { fill: var(--uk-green); opacity: 0.12; }
.pc__axis { stroke: var(--vp-c-text-3); stroke-width: 1; }
.pc__raw { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1.3; stroke-dasharray: 4 3; }
.pc__obj { fill: none; stroke: var(--uk-accent); stroke-width: 2.4; }
.pc__dot { fill: var(--uk-accent); stroke: var(--vp-c-bg); stroke-width: 2; }
.pc__dot.is-stop { fill: var(--uk-warm); }
.pc__tick { fill: var(--vp-c-text-3); font-size: 9px; font-family: var(--vp-font-family-mono); }
.pc__presets { display: flex; flex-wrap: wrap; gap: 0.5rem; margin: 0.2rem 0 0.7rem; }
.pc__btn {
  font: inherit; font-size: 0.8rem; padding: 0.2rem 0.7rem; border-radius: 999px;
  border: 1px solid var(--uk-accent); color: var(--uk-accent); background: transparent; cursor: pointer;
}
.pc__btn:hover { background: var(--uk-accent-soft); }
</style>
