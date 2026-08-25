<script setup lang="ts">
/**
 * Затримка в каналі: чому щільніший граф гірше терпить запізнення.
 *
 * Контрінтуїтивний результат картки «Щільніший граф гірше терпить затримки»
 * модуля 03. Для консенсусу з однаковою затримкою τ на всіх ребрах умова
 * стійкості має вигляд τ < π / (2 λ_max), де λ_max — найбільше власне число
 * лапласіана. Додавання ребер піднімає λ_max, тому гранична затримка падає:
 * рій, який швидше домовляється, першим і розгойдується.
 */
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const TOPO = [
  { id: 'chain', name: 'Ланцюг', edges: [[0, 1], [1, 2], [2, 3], [3, 4]] },
  { id: 'ring', name: 'Кільце', edges: [[0, 1], [1, 2], [2, 3], [3, 4], [4, 0]] },
  { id: 'star', name: 'Зірка', edges: [[0, 1], [0, 2], [0, 3], [0, 4]] },
  {
    id: 'full', name: 'Повний',
    edges: [[0, 1], [0, 2], [0, 3], [0, 4], [1, 2], [1, 3], [1, 4], [2, 3], [2, 4], [3, 4]]
  }
]
/** Реальна затримка радіоканалу з таблиці лекції. */
const RADIO = 0.35
const N = 5
const H0 = [4.2, 9.5, 5.1, 8.0, 7.2]

const pick = ref(1)
const tau = ref(0.35)
const topo = computed(() => TOPO[pick.value])

function laplacian(edges: number[][]) {
  const L = Array.from({ length: N }, () => new Array(N).fill(0))
  for (const [i, j] of edges) {
    L[i][j] -= 1; L[j][i] -= 1; L[i][i] += 1; L[j][j] += 1
  }
  return L
}

/** Найбільше власне число — метод степеневих ітерацій, для 5×5 вистачає. */
function lambdaMax(L: number[][]) {
  let v = new Array(N).fill(1).map((_, i) => 1 + i * 0.1)
  let lam = 0
  for (let it = 0; it < 200; it++) {
    const w = new Array(N).fill(0)
    for (let i = 0; i < N; i++) for (let j = 0; j < N; j++) w[i] += L[i][j] * v[j]
    const norm = Math.hypot(...w) || 1
    v = w.map((x) => x / norm)
    lam = norm
  }
  return lam
}

const lmax = computed(() => lambdaMax(laplacian(topo.value.edges)))
/** Гранична затримка: за нею консенсус утрачає стійкість. */
const tauCrit = computed(() => Math.PI / (2 * lmax.value))
const stable = computed(() => tau.value < tauCrit.value)

// ---- симуляція із запізненням ----
const DT = 0.01
const hist = ref<number[][]>([])
const running = ref(true)
const t = ref(0)
let buf: number[][] = []
let raf = 0

function reset() {
  const lag = Math.max(1, Math.round(tau.value / DT))
  buf = Array.from({ length: lag + 1 }, () => [...H0])
  hist.value = [[...H0]]
  t.value = 0
}

function step() {
  const L = laplacian(topo.value.edges)
  const lag = Math.max(1, Math.round(tau.value / DT))
  const cur = buf[buf.length - 1]
  const old = buf[Math.max(0, buf.length - 1 - lag)]
  // кожен агент реагує на ЗАПІЗНІЛІ стани сусідів, а не на поточні
  const nx = cur.map((x, i) => {
    let s = 0
    for (let j = 0; j < N; j++) s += L[i][j] * old[j]
    const v = x - DT * s
    return Math.max(-40, Math.min(60, v))
  })
  buf.push(nx)
  if (buf.length > lag + 400) buf.shift()
  t.value += DT
  if (hist.value.length < 4000) hist.value.push(nx)
}

function tick() {
  if (running.value) for (let k = 0; k < 6; k++) if (t.value < 24) step()
  raf = requestAnimationFrame(tick)
}
onMounted(() => { reset(); raf = requestAnimationFrame(tick) })
onBeforeUnmount(() => cancelAnimationFrame(raf))
watch([pick, tau], reset)

const W = 460, H = 150
const paths = computed(() => {
  const h = hist.value
  if (h.length < 2) return []
  const lo = -6, hi = 20
  const T = Math.max(h.length - 1, 1)
  return H0.map((_, i) =>
    h.map((row, k) => {
      const x = (k / T) * W
      const y = H - ((Math.max(lo, Math.min(hi, row[i])) - lo) / (hi - lo)) * H
      return `${k ? 'L' : 'M'}${x.toFixed(1)},${y.toFixed(1)}`
    }).join(' ')
  )
})

/** Розмах на кінці: якщо росте — консенсус розійшовся. */
const spread = computed(() => {
  const last = hist.value[hist.value.length - 1] || H0
  return Math.max(...last) - Math.min(...last)
})
const diverged = computed(() => spread.value > 12)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Затримка в каналі: щільніший граф ламається першим</div>
        <div class="lab__sub">
          Той самий протокол консенсусу, але сусіди повідомляють свій стан
          із запізненням τ. Оберіть топологію й ведіть повзунок.
        </div>
      </div>
      <button class="lab__btn" @click="reset">Спочатку</button>
    </div>

    <div class="lab__pills">
      <button
        v-for="(tp, i) in TOPO" :key="tp.id"
        class="lab__pill" :class="{ 'is-on': pick === i }"
        @click="pick = i"
      >{{ tp.name }} ({{ tp.edges.length }} ребер)</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Затримка τ <b>{{ tau.toFixed(2) }} с</b>{{ Math.abs(tau - RADIO) < 0.005 ? ' — реальний радіоканал' : '' }}</span>
        <input v-model.number="tau" type="range" min="0" max="0.7" step="0.01" />
      </label>
    </div>

    <svg class="dl__plot" :viewBox="`0 0 ${W} ${H}`" preserveAspectRatio="none"
         aria-label="Висоти агентів у часі за наявності затримки">
      <path v-for="(d, i) in paths" :key="i" :d="d"
            class="dl__line" :class="{ 'is-bad': diverged }" />
    </svg>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ topo.edges.length }}</b>
        <span>ребер у графі</span>
      </div>
      <div class="lab__stat">
        <b>{{ lmax.toFixed(2) }}</b>
        <span>найбільше власне число λ<sub>max</sub></span>
      </div>
      <div class="lab__stat">
        <b>{{ tauCrit.toFixed(3) }} с</b>
        <span>гранична затримка π / (2λ<sub>max</sub>)</span>
      </div>
      <div class="lab__stat" :class="stable ? 'is-green' : 'is-warm'">
        <b>{{ stable ? 'стійкий' : 'розходиться' }}</b>
        <span>стан за поточної τ</span>
      </div>
    </div>

    <p class="lab__note">
      Повзунок стоїть на 0,35 с — це реальна затримка радіоканалу з таблиці
      лекції. Переключайте топології: ланцюг і кільце ще працюють, а зірка
      й повний граф уже розходяться. Причому зірка має рівно стільки ж ребер,
      скільки ланцюг, — справа не в їх кількості, а в тому, що вони роблять
      із λ<sub>max</sub>. Швидкість збіжності задає λ₂, а стійкість до
      запізнення — λ<sub>max</sub>, і додавання ребер піднімає обидва.
      Повний граф виграє у швидкості 13,1 раза, але допустима затримка падає
      на 28 %. Це прямо суперечить інтуїції «більше зв'язків — краще».
    </p>
  </div>
</template>

<style scoped>
.dl__plot {
  width: 100%;
  height: 150px;
  background: var(--uk-fill);
  border-radius: 10px;
}
.dl__line {
  fill: none;
  stroke: var(--uk-accent);
  stroke-width: 1.6;
  vector-effect: non-scaling-stroke;
}
.dl__line.is-bad { stroke: var(--uk-warm); }
</style>
