<script setup lang="ts">
/**
 * Розбиття Вороного як зони відповідальності рою.
 *
 * Ілюструє картку «Зони відповідальності: розбиття Вороного» модуля 08.
 * Апарати можна перетягувати мишею. Дві величини рахуються живцем:
 * площа найбільшої комірки (її мінімізують розвідники в гетерогенному рої
 * з модуля 07) і найгірша відстань до найближчого апарата — тобто те місце,
 * де рій «бачить» гірше за все.
 *
 * Кнопка «Розвести» робить кілька кроків Ллойда: кожен апарат зсувається
 * в центр мас своєї комірки. Це і є класичне керування покриттям.
 */
import { ref, computed } from 'vue'

const SIDE = 100          // майданчик 100×100 м
const GRID = 120          // сітка для оцінювання площ і відстаней та малювання зон

const START = [
  [22, 26], [48, 18], [76, 30],
  [18, 58], [42, 46], [82, 62],
  [30, 84], [58, 76], [86, 88]
]
const agents = ref(START.map(([x, y]) => ({ x, y })))

/** Кожній комірці сітки — індекс найближчого апарата. */
const owner = computed(() => {
  const a = agents.value
  const map = new Int8Array(GRID * GRID)
  const dist = new Float32Array(GRID * GRID)
  const step = SIDE / GRID
  for (let gy = 0; gy < GRID; gy++) {
    for (let gx = 0; gx < GRID; gx++) {
      const x = (gx + 0.5) * step
      const y = (gy + 0.5) * step
      let best = 0
      let bd = Infinity
      for (let i = 0; i < a.length; i++) {
        const d = (a[i].x - x) ** 2 + (a[i].y - y) ** 2
        if (d < bd) { bd = d; best = i }
      }
      map[gy * GRID + gx] = best
      dist[gy * GRID + gx] = Math.sqrt(bd)
    }
  }
  return { map, dist }
})

const stats = computed(() => {
  const { map, dist } = owner.value
  const cells = new Array(agents.value.length).fill(0)
  for (let k = 0; k < map.length; k++) cells[map[k]]++
  const cellArea = (SIDE / GRID) ** 2
  const areas = cells.map((c) => c * cellArea)
  const worst = Math.max(...dist)
  return {
    maxArea: Math.max(...areas),
    minArea: Math.min(...areas),
    spread: Math.max(...areas) / Math.max(Math.min(...areas), 1e-9),
    worstDist: worst
  }
})

/** Крок Ллойда: кожен апарат — у центр мас своєї комірки. */
function relax(times = 1) {
  for (let it = 0; it < times; it++) {
    const { map } = owner.value
    const sx = new Array(agents.value.length).fill(0)
    const sy = new Array(agents.value.length).fill(0)
    const n = new Array(agents.value.length).fill(0)
    const step = SIDE / GRID
    for (let gy = 0; gy < GRID; gy++) {
      for (let gx = 0; gx < GRID; gx++) {
        const i = map[gy * GRID + gx]
        sx[i] += (gx + 0.5) * step
        sy[i] += (gy + 0.5) * step
        n[i]++
      }
    }
    agents.value = agents.value.map((p, i) =>
      n[i] ? { x: +(sx[i] / n[i]).toFixed(2), y: +(sy[i] / n[i]).toFixed(2) } : p
    )
  }
}

function reset() {
  agents.value = START.map(([x, y]) => ({ x, y }))
}

/** Палітра зон: один відтінок акценту на апарат. */
const HUES = [210, 150, 28, 265, 190, 340, 95, 250, 15]

const cellsSvg = computed(() => {
  const { map } = owner.value
  const step = SIDE / GRID
  const out: { x: number; y: number; w: number; i: number }[] = []
  // склеюємо горизонтальні смуги одного власника — менше вузлів у DOM
  for (let gy = 0; gy < GRID; gy++) {
    let run = 0
    for (let gx = 1; gx <= GRID; gx++) {
      const same = gx < GRID && map[gy * GRID + gx] === map[gy * GRID + run]
      if (!same) {
        out.push({ x: run * step, y: gy * step, w: (gx - run) * step, i: map[gy * GRID + run] })
        run = gx
      }
    }
  }
  return { rows: out, h: step }
})

const svg = ref<SVGSVGElement | null>(null)
let drag = -1
function down(i: number) { drag = i }
function move(e: MouseEvent) {
  if (drag < 0 || !svg.value) return
  const r = svg.value.getBoundingClientRect()
  const x = ((e.clientX - r.left) / r.width) * SIDE
  const y = ((e.clientY - r.top) / r.height) * SIDE
  const a = [...agents.value]
  a[drag] = { x: Math.max(1, Math.min(SIDE - 1, +x.toFixed(2))),
              y: Math.max(1, Math.min(SIDE - 1, +y.toFixed(2))) }
  agents.value = a
}
function up() { drag = -1 }
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Зони відповідальності: розбиття Вороного</div>
        <div class="lab__sub">
          Кожен апарат відповідає за точки, до яких він найближчий. Перетягніть
          апарат мишею — межі перерахуються самі, і для цього апарату досить
          знати положення лише своїх сусідів.
        </div>
      </div>
      <button class="lab__btn" @click="reset">Спочатку</button>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" @click="relax(1)">Крок Ллойда</button>
      <button class="lab__pill" @click="relax(12)">Розвести повністю</button>
    </div>

    <svg
      ref="svg" class="vr__plot" :viewBox="`0 0 ${SIDE} ${SIDE}`"
      @mousemove="move" @mouseup="up" @mouseleave="up"
      aria-label="Розбиття Вороного між апаратами рою"
    >
      <rect
        v-for="(r, k) in cellsSvg.rows" :key="k"
        :x="r.x" :y="r.y" :width="r.w + 0.02" :height="cellsSvg.h + 0.02"
        :fill="`hsl(${HUES[r.i % HUES.length]} 62% 58%)`" opacity="0.32" shape-rendering="crispEdges"
      />
      <circle
        v-for="(p, i) in agents" :key="i"
        :cx="p.x" :cy="p.y" r="2.1"
        :fill="`hsl(${HUES[i % HUES.length]} 62% 42%)`"
        class="vr__dot" @mousedown="down(i)"
      />
    </svg>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ Math.round(stats.maxArea) }} м²</b>
        <span>найбільша комірка</span>
      </div>
      <div class="lab__stat">
        <b>{{ Math.round(stats.minArea) }} м²</b>
        <span>найменша комірка</span>
      </div>
      <div class="lab__stat" :class="stats.spread < 2 ? 'is-green' : 'is-warm'">
        <b>{{ stats.spread.toFixed(1) }}×</b>
        <span>розкид навантаження</span>
      </div>
      <div class="lab__stat">
        <b>{{ stats.worstDist.toFixed(1) }} м</b>
        <span>найгірша відстань до апарата</span>
      </div>
    </div>

    <p class="lab__note">
      Зсуньте два апарати в один кут: їхні комірки стиснуться, а протилежний
      бік майданчика дістанеться одному апарату — розкид навантаження
      підскочить у рази. Це та сама патологія, яку в лабораторній роботі 5
      ловлять метрикою «розкид внеску між дронами». Натисніть «Розвести
      повністю»: кроки Ллойда зсувають кожен апарат у центр мас його зони,
      і розкид падає до одиниці. Мінімізація найбільшої комірки й означає
      «зробити покриття рівномірним».
    </p>
  </div>
</template>

<style scoped>
.vr__plot {
  width: 100%;
  height: auto;
  background: var(--uk-fill);
  border-radius: 10px;
  touch-action: none;
}
.vr__dot { cursor: grab; stroke: var(--vp-c-bg); stroke-width: 0.8; }
.vr__dot:active { cursor: grabbing; }
</style>
