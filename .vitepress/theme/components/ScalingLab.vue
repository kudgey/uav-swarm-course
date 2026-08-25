<script setup lang="ts">
/**
 * Масштабування рою: що стається, коли політику, навчену на восьми апаратах,
 * запускають на більшому рої.
 *
 * Числа з картки «Масштабування: навчили на восьми, полетіли сто двадцять вісім»
 * модуля 07 — з Batra та ін., CoRL 2021 (arXiv:2109.07735). Опорні точки:
 * 8 → 0,02 зіткнення на апарат за хвилину, 128 → 8,63 без донавчання
 * і 1,37 після донавчання на 2·10⁸ кроків.
 */
import { ref, computed } from 'vue'

/** Виміряні опорні точки; проміжні — інтерполяція в логарифмі N. */
const BASE: [number, number][] = [[8, 0.02], [16, 0.05], [32, 0.63], [64, 3.10], [128, 8.63]]
const TUNED: [number, number][] = [[8, 0.02], [16, 0.03], [32, 0.14], [64, 0.55], [128, 1.37]]

const n = ref(8)
const tuned = ref(false)

function interp(pts: [number, number][], x: number) {
  const lx = Math.log2(x)
  for (let i = 0; i < pts.length - 1; i++) {
    const [x0, y0] = pts[i], [x1, y1] = pts[i + 1]
    const a = Math.log2(x0), b = Math.log2(x1)
    if (lx >= a && lx <= b) return y0 + ((y1 - y0) * (lx - a)) / (b - a)
  }
  return lx < Math.log2(pts[0][0]) ? pts[0][1] : pts[pts.length - 1][1]
}

const collisions = computed(() => interp(tuned.value ? TUNED : BASE, n.value))
/** Скільки разів гірше, ніж на восьми апаратах, на яких політику навчали. */
const factor = computed(() => collisions.value / 0.02)
/** Очікуване число дотиків за трихвилинну місію всім роєм. */
const perMission = computed(() => collisions.value * n.value * 3)

const W = 460, H = 170
const XS = [8, 16, 32, 64, 128]
const yMax = 9
const px = (v: number) => 34 + ((Math.log2(v) - 3) / 4) * (W - 50)
const py = (v: number) => H - 22 - (Math.min(v, yMax) / yMax) * (H - 40)

function path(pts: [number, number][]) {
  const s: string[] = []
  for (let v = 8; v <= 128; v *= 1.06) s.push(`${s.length ? 'L' : 'M'}${px(v).toFixed(1)},${py(interp(pts, v)).toFixed(1)}`)
  s.push(`L${px(128).toFixed(1)},${py(interp(pts, 128)).toFixed(1)}`)
  return s.join(' ')
}
const pathBase = path(BASE)
const pathTuned = path(TUNED)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Перенесення політики на більший рій</div>
        <div class="lab__sub">
          Політику навчали на восьми апаратах. Ведіть повзунок праворуч і дивіться,
          де безкоштовний перенос закінчується.
        </div>
      </div>
      <button class="lab__btn" @click="tuned = !tuned">
        {{ tuned ? 'Без донавчання' : 'З донавчанням' }}
      </button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Апаратів у рої <b>{{ n }}</b></span>
        <input v-model.number="n" type="range" min="8" max="128" step="1" />
      </label>
    </div>

    <svg class="sc__plot" :viewBox="`0 0 ${W} ${H}`" aria-label="Зіткнення залежно від розміру рою">
      <line v-for="x in XS" :key="'g' + x" :x1="px(x)" y1="14" :x2="px(x)" :y2="H - 22" class="sc__grid" />
      <text v-for="x in XS" :key="'t' + x" :x="px(x)" :y="H - 7" class="sc__tick">{{ x }}</text>

      <path :d="pathBase" class="sc__line" :class="{ 'is-dim': tuned }" />
      <path :d="pathTuned" class="sc__line is-tuned" :class="{ 'is-dim': !tuned }" />

      <line :x1="px(n)" y1="14" :x2="px(n)" :y2="H - 22" class="sc__cursor" />
      <circle :cx="px(n)" :cy="py(collisions)" r="4.5" class="sc__dot" />
      <text x="34" y="12" class="sc__axis">зіткнень на апарат за хвилину</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat" :class="collisions > 0.05 ? 'is-warm' : 'is-green'">
        <b>{{ collisions.toFixed(2) }}</b>
        <span>зіткнень на апарат за хвилину</span>
      </div>
      <div class="lab__stat">
        <b>×{{ factor.toFixed(0) }}</b>
        <span>гірше, ніж на восьми</span>
      </div>
      <div class="lab__stat">
        <b>{{ perMission.toFixed(1) }}</b>
        <span>дотиків за місію 3 хв усім роєм</span>
      </div>
      <div class="lab__stat" :class="n <= 16 ? 'is-green' : 'is-warm'">
        <b>{{ n <= 16 ? 'так' : 'ні' }}</b>
        <span>перенос без втрат</span>
      </div>
    </div>

    <p class="lab__note">
      До шістнадцяти апаратів політика переноситься майже без втрат — це приблизно
      двократна зміна N. Далі деградація нелінійна: на 128 апаратах зіткнень
      у чотириста разів більше, ніж на навчальному розмірі. Донавчання на
      2·10⁸ кроків знижує їх приблизно вшестеро, але до рівня восьми не повертає.
      Практичне правило: безкоштовний перенос живе в межах подвоєння рою.
    </p>
  </div>
</template>

<style scoped>
.sc__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; }
.sc__grid { stroke: var(--vp-c-divider); stroke-width: 0.7; }
.sc__tick, .sc__axis {
  fill: var(--vp-c-text-3);
  font-size: 9px;
  text-anchor: middle;
  font-family: var(--vp-font-family-mono);
}
.sc__axis { text-anchor: start; }
.sc__line { fill: none; stroke: var(--uk-warm); stroke-width: 2.2; transition: opacity 0.2s ease; }
.sc__line.is-tuned { stroke: var(--uk-green); }
.sc__line.is-dim { opacity: 0.22; }
.sc__cursor { stroke: var(--uk-accent); stroke-width: 1; stroke-dasharray: 3 3; }
.sc__dot { fill: var(--uk-accent); }
</style>
