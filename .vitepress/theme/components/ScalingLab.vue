<script setup lang="ts">
/**
 * Масштабування рою: політику, навчену на восьми квадрокоптерах, запускають на більшому рої.
 *
 * Модуль 09, картка «5.1 Те саме в рої квадрокоптерів». Числа — табл. 1 з Batra та ін.,
 * CoRL 2021 (arXiv:2109.07735): зіткнень на апарат за хвилину і відстань до цілі
 * для 8–128 апаратів, без донавчання і після донавчання на 2·10⁸ кроків.
 * Віджет показує лише виміряні точки, без інтерполяції.
 */
import { ref, computed } from 'vue'

type Row = { n: number; col: number; dist: number; colFt: number; distFt: number }
const ROWS: Row[] = [
  { n: 8, col: 0.02, dist: 0.42, colFt: 0.0, distFt: 0.41 },
  { n: 16, col: 0.09, dist: 0.57, colFt: 0.08, distFt: 0.63 },
  { n: 32, col: 0.9, dist: 0.86, colFt: 0.16, distFt: 0.81 },
  { n: 48, col: 2.43, dist: 1.11, colFt: 0.23, distFt: 0.92 },
  { n: 64, col: 5.36, dist: 1.7, colFt: 0.29, distFt: 1.12 },
  { n: 128, col: 8.63, dist: 4.32, colFt: 1.37, distFt: 3.05 },
]

const i = ref(0)
const tuned = ref(false)
const row = computed(() => ROWS[i.value])
const col = computed(() => (tuned.value ? row.value.colFt : row.value.col))
const dist = computed(() => (tuned.value ? row.value.distFt : row.value.dist))

const W = 460, H = 170
const yMax = 9
const px = (k: number) => 40 + (k / (ROWS.length - 1)) * (W - 70)
const py = (v: number) => H - 24 - (v / yMax) * (H - 44)
const pts = (key: 'col' | 'colFt') => ROWS.map((r, k) => `${px(k).toFixed(1)},${py(r[key]).toFixed(1)}`).join(' ')
const f = (v: number) => v.toFixed(2).replace('.', ',')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Перенос політики на більший рій квадрокоптерів</div>
        <div class="lab__sub">
          Batra та ін., 2021: політику навчали на 8 апаратах, потім запускали на більшому рої
          без донавчання і після донавчання. Лише виміряні точки.
        </div>
      </div>
      <button class="lab__btn" type="button" @click="tuned = !tuned">
        {{ tuned ? 'Без донавчання' : 'З донавчанням' }}
      </button>
    </div>

    <div class="lab__pills">
      <button v-for="(r, k) in ROWS" :key="r.n" type="button" class="lab__pill" :class="{ 'is-on': i === k }"
              @click="i = k">{{ r.n }}</button>
    </div>

    <svg class="sc__plot" :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Зіткнення на апарат за хвилину залежно від розміру рою">
      <line v-for="(r, k) in ROWS" :key="'g' + r.n" :x1="px(k)" y1="14" :x2="px(k)" :y2="H - 24" class="sc__grid" />
      <text v-for="(r, k) in ROWS" :key="'t' + r.n" :x="px(k)" :y="H - 8" class="sc__tick">{{ r.n }}</text>
      <polyline :points="pts('col')" class="sc__line" :class="{ 'is-dim': tuned }" />
      <polyline :points="pts('colFt')" class="sc__line is-tuned" :class="{ 'is-dim': !tuned }" />
      <circle v-for="(r, k) in ROWS" :key="'b' + r.n" :cx="px(k)" :cy="py(r.col)" r="3" class="sc__pt" :class="{ 'is-dim': tuned }" />
      <circle v-for="(r, k) in ROWS" :key="'f' + r.n" :cx="px(k)" :cy="py(r.colFt)" r="3" class="sc__pt is-tuned" :class="{ 'is-dim': !tuned }" />
      <circle :cx="px(i)" :cy="py(col)" r="6" class="sc__dot" />
      <text x="40" y="11" class="sc__axis">зіткнень на апарат за хвилину</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat" :class="col > 0.1 ? 'is-warm' : 'is-green'">
        <b>{{ f(col) }}</b>
        <span>зіткнень на апарат за хвилину</span>
      </div>
      <div class="lab__stat">
        <b>{{ f(dist) }} м</b>
        <span>відстань до цілі</span>
      </div>
      <div class="lab__stat">
        <b>{{ row.n / 8 }}×</b>
        <span>більше апаратів, ніж у навчанні</span>
      </div>
    </div>
  </div>
</template>

<style scoped>
.sc__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; }
.sc__grid { stroke: var(--vp-c-divider); stroke-width: 0.7; }
.sc__tick, .sc__axis {
  fill: var(--vp-c-text-3);
  font-size: 11px;
  text-anchor: middle;
  font-family: var(--vp-font-family-mono);
}
.sc__axis { text-anchor: start; }
.sc__line { fill: none; stroke: var(--uk-warm); stroke-width: 2.2; transition: opacity 0.2s ease; }
.sc__line.is-tuned { stroke: var(--uk-green); }
.sc__pt { fill: var(--uk-warm); transition: opacity 0.2s ease; }
.sc__pt.is-tuned { fill: var(--uk-green); }
.is-dim { opacity: 0.22; }
.sc__dot { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
</style>
