<script setup lang="ts">
/**
 * Консенсус на чотирьох топологіях: x' = -L x.
 *
 * Числа збігаються з таблицею цієї ж картки: λ₂ = 0,382 / 1,000 / 1,382 / 5,000
 * і теоретична межа t₉₉ = 12,1 / 4,6 / 3,3 / 0,9 с. Початкові висоти —
 * ті самі, що у прикладі коду, тому спільна висота виходить 6,80 м.
 */
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const H0 = [4.2, 9.5, 5.1, 8.0, 7.2] // м, середнє = 6,80
const TOPO = [
  { id: 'chain', name: 'Ланцюг', edges: [[0, 1], [1, 2], [2, 3], [3, 4]], l2: 0.382, t99: 12.1 },
  { id: 'star', name: 'Зірка', edges: [[0, 1], [0, 2], [0, 3], [0, 4]], l2: 1.0, t99: 4.6 },
  { id: 'ring', name: 'Кільце', edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]], l2: 1.382, t99: 3.3 },
  {
    id: 'full', name: 'Повний',
    edges: [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]],
    l2: 5.0, t99: 0.9
  }
]

const pick = ref(0)
const topo = computed(() => TOPO[pick.value])
const x = ref<number[]>([...H0])
const t = ref(0)
const running = ref(true)
const hist = ref<number[][]>([])

const mean = H0.reduce((a, b) => a + b, 0) / H0.length
/** Максимальне відхилення від спільної висоти — за ним і рахують t₉₉. */
const spread = computed(() => Math.max(...x.value.map((v) => Math.abs(v - mean))))
const spread0 = Math.max(...H0.map((v) => Math.abs(v - mean)))
const done = computed(() => spread.value <= 0.01 * spread0)

function laplacian(edges: number[][]) {
  const n = H0.length
  const L = Array.from({ length: n }, () => new Array(n).fill(0))
  for (const [i, j] of edges) {
    L[i][j] -= 1; L[j][i] -= 1; L[i][i] += 1; L[j][j] += 1
  }
  return L
}

function reset() {
  x.value = [...H0]
  t.value = 0
  hist.value = [[...H0]]
}

const DT = 0.02
function stepOnce() {
  const L = laplacian(topo.value.edges)
  const nx = x.value.map((_, i) => {
    let s = 0
    for (let j = 0; j < x.value.length; j++) s += L[i][j] * x.value[j]
    return x.value[i] - DT * s
  })
  x.value = nx
  t.value += DT
  if (hist.value.length < 3000) hist.value.push([...nx])
}

let timer = 0
function tick() {
  if (!running.value) return
  for (let k = 0; k < 3; k++) if (!done.value) stepOnce()
  timer = requestAnimationFrame(tick)
}
onMounted(() => { reset(); timer = requestAnimationFrame(tick) })
onBeforeUnmount(() => cancelAnimationFrame(timer))
watch(running, (v) => { if (v) timer = requestAnimationFrame(tick) })
watch(pick, reset)

/** Координати п'яти вузлів по колу — для схеми топології. */
const NODES = Array.from({ length: 5 }, (_, i) => {
  const a = (i / 5) * Math.PI * 2 - Math.PI / 2
  return { x: 60 + Math.cos(a) * 42, y: 56 + Math.sin(a) * 42 }
})

/** Криві висот у координатах SVG. */
const paths = computed(() => {
  const h = hist.value
  if (h.length < 2) return []
  const W = 460, H = 150, T = Math.max(h.length - 1, 1)
  const lo = 3.5, hi = 10
  return H0.map((_, i) =>
    h.map((row, k) => {
      const px = (k / T) * W
      const py = H - ((row[i] - lo) / (hi - lo)) * H
      return `${k ? 'L' : 'M'}${px.toFixed(1)},${py.toFixed(1)}`
    }).join(' ')
  )
})
const meanY = computed(() => 150 - ((mean - 3.5) / (10 - 3.5)) * 150)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Консенсус: топологія проти часу</div>
        <div class="lab__sub">
          П'ять апаратів на різних висотах домовляються про спільну. Закон один
          і той самий, змінюється лише те, хто кого чує.
        </div>
      </div>
      <button class="lab__btn" @click="reset">Спочатку</button>
    </div>

    <div class="lab__pills">
      <button
        v-for="(tp, i) in TOPO" :key="tp.id"
        class="lab__pill" :class="{ 'is-on': pick === i }"
        @click="pick = i"
      >{{ tp.name }}</button>
    </div>

    <div class="cs__grid">
      <svg class="cs__topo" viewBox="0 0 120 112" aria-label="Схема топології">
        <line
          v-for="([a, b], k) in topo.edges" :key="k"
          :x1="NODES[a].x" :y1="NODES[a].y" :x2="NODES[b].x" :y2="NODES[b].y"
          class="cs__edge"
        />
        <g v-for="(n, i) in NODES" :key="i">
          <circle :cx="n.x" :cy="n.y" r="9" class="cs__node" />
          <text :x="n.x" :y="n.y + 3.4" class="cs__lbl">{{ i + 1 }}</text>
        </g>
      </svg>

      <svg class="cs__plot" viewBox="0 0 460 150" preserveAspectRatio="none"
           aria-label="Збіжність висот у часі">
        <line x1="0" :y1="meanY" x2="460" :y2="meanY" class="cs__mean" />
        <path v-for="(d, i) in paths" :key="i" :d="d" class="cs__line" />
      </svg>
    </div>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ topo.l2.toFixed(3) }}</b>
        <span>алгебраїчна зв'язність λ₂</span>
      </div>
      <div class="lab__stat">
        <b>{{ t.toFixed(2) }} с</b>
        <span>модельний час</span>
      </div>
      <div class="lab__stat" :class="{ 'is-green': done }">
        <b>{{ spread.toFixed(2) }} м</b>
        <span>найбільше відхилення</span>
      </div>
      <div class="lab__stat">
        <b>{{ topo.t99.toFixed(1) }} с</b>
        <span>теоретична межа t₉₉</span>
      </div>
    </div>

    <div class="sw__bar">
      <button class="lab__btn" @click="running = !running">
        {{ running ? 'Пауза' : 'Продовжити' }}
      </button>
      <span class="cs__note">
        спільна висота <b>{{ mean.toFixed(2) }} м</b> — середнє початкових, однакове
        для всіх топологій
      </span>
    </div>

    <p class="lab__note">
      Повний граф має вдвічі більше ребер за кільце, а виграє в часі приблизно
      вчетверо: платимо за кожне ребро каналом зв'язку, а отримуємо тільки
      приріст λ₂. Саме тому «додати зв'язків» — не завжди правильна інженерна дія.
    </p>
  </div>
</template>

<style scoped>
.cs__grid {
  display: grid;
  grid-template-columns: 130px 1fr;
  gap: 1rem;
  align-items: center;
  margin-bottom: 1rem;
}
@media (max-width: 640px) {
  .cs__grid { grid-template-columns: 1fr; }
}
.cs__topo { width: 100%; height: auto; }
.cs__edge { stroke: var(--uk-line); stroke-width: 1.6; }
.cs__node { fill: var(--uk-accent); }
.cs__lbl {
  fill: #fff;
  font-size: 8px;
  text-anchor: middle;
  font-family: var(--vp-font-family-mono);
}
.cs__plot {
  width: 100%;
  height: 150px;
  background: var(--uk-fill);
  border-radius: 8px;
}
.cs__line { fill: none; stroke: var(--uk-accent); stroke-width: 1.6; vector-effect: non-scaling-stroke; }
.cs__mean { stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 4 4; vector-effect: non-scaling-stroke; }
.sw__bar { display: flex; align-items: center; gap: 0.9rem; flex-wrap: wrap; margin-top: 0.7rem; }
.cs__note { font-size: 0.8rem; color: var(--vp-c-text-2); }
.cs__note b { font-family: var(--vp-font-family-mono); color: var(--uk-accent); font-weight: 500; }
</style>
