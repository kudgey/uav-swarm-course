<script setup lang="ts">
/**
 * Граф сусідства: радіус зв'язку проти зв'язності рою.
 *
 * Та сама задача, що в коді картки «Код: граф сусідства рою» модуля 01:
 * фіксовані позиції апаратів, ребро з'являється, коли відстань ≤ r.
 * λ₂ рахується як друге найменше власне число матриці Лапласа —
 * як і в лекції, а не «друге за величиною».
 *
 * Апарати можна вимикати кліком: це сценарій втрати апаратів із модуля 09.
 */
import { ref, computed } from 'vue'

/** Детермінований розкид 12 апаратів у квадраті 100×70 м. */
const P = [
  [12, 18], [34, 10], [58, 16], [82, 12],
  [8, 42], [30, 38], [55, 44], [78, 40],
  [18, 62], [42, 66], [66, 60], [88, 64]
]

const radius = ref(34)
const dead = ref<number[]>([])

function toggle(i: number) {
  dead.value = dead.value.includes(i)
    ? dead.value.filter((k) => k !== i)
    : [...dead.value, i]
}
function reset() { dead.value = []; radius.value = 34 }

const alive = computed(() => P.map((_, i) => i).filter((i) => !dead.value.includes(i)))

const edges = computed(() => {
  const out: [number, number][] = []
  const a = alive.value
  for (let x = 0; x < a.length; x++)
    for (let y = x + 1; y < a.length; y++) {
      const i = a[x], j = a[y]
      if (Math.hypot(P[i][0] - P[j][0], P[i][1] - P[j][1]) <= radius.value) out.push([i, j])
    }
  return out
})

/** Власні числа симетричної матриці — метод Якобі, вистачає для 12×12. */
function eigenvalues(A: number[][]) {
  const n = A.length
  const M = A.map((r) => [...r])
  for (let sweep = 0; sweep < 60; sweep++) {
    let off = 0
    for (let i = 0; i < n; i++) for (let j = i + 1; j < n; j++) off += M[i][j] * M[i][j]
    if (off < 1e-12) break
    for (let p = 0; p < n; p++)
      for (let q = p + 1; q < n; q++) {
        if (Math.abs(M[p][q]) < 1e-14) continue
        const theta = (M[q][q] - M[p][p]) / (2 * M[p][q])
        const t = Math.sign(theta || 1) / (Math.abs(theta) + Math.sqrt(theta * theta + 1))
        const c = 1 / Math.sqrt(t * t + 1), s = t * c
        for (let k = 0; k < n; k++) {
          const mkp = M[k][p], mkq = M[k][q]
          M[k][p] = c * mkp - s * mkq
          M[k][q] = s * mkp + c * mkq
        }
        for (let k = 0; k < n; k++) {
          const mpk = M[p][k], mqk = M[q][k]
          M[p][k] = c * mpk - s * mqk
          M[q][k] = s * mpk + c * mqk
        }
      }
  }
  return M.map((r, i) => r[i]).sort((a, b) => a - b)
}

const spectrum = computed(() => {
  const a = alive.value
  if (a.length < 2) return [0]
  const idx = new Map(a.map((v, k) => [v, k]))
  const L = Array.from({ length: a.length }, () => new Array(a.length).fill(0))
  for (const [i, j] of edges.value) {
    const x = idx.get(i)!, y = idx.get(j)!
    L[x][y] -= 1; L[y][x] -= 1; L[x][x] += 1; L[y][y] += 1
  }
  return eigenvalues(L)
})

const lambda2 = computed(() => Math.max(0, spectrum.value[1] ?? 0))
/** Кратність нуля у спектрі = число компонент зв'язності. */
const components = computed(() => spectrum.value.filter((v) => v < 1e-8).length)
const connected = computed(() => components.value === 1 && alive.value.length > 1)
const t99 = computed(() => (lambda2.value > 1e-6 ? Math.log(100) / lambda2.value : Infinity))
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Радіус зв'язку, зв'язність і втрата апаратів</div>
        <div class="lab__sub">
          Ребро з'являється, коли відстань між апаратами не більша за радіус.
          Клік по апарату «вимикає» його — так виглядає втрата борта в польоті.
        </div>
      </div>
      <button class="lab__btn" @click="reset">Спочатку</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Радіус зв'язку <b>{{ radius }} м</b></span>
        <input v-model.number="radius" type="range" min="12" max="70" step="1" />
      </label>
    </div>

    <svg class="cn__plot" viewBox="0 0 100 76" aria-label="Граф сусідства рою">
      <line
        v-for="([i, j], k) in edges" :key="k"
        :x1="P[i][0]" :y1="P[i][1]" :x2="P[j][0]" :y2="P[j][1]" class="cn__edge"
      />
      <g v-for="(p, i) in P" :key="i" @click="toggle(i)" class="cn__hit">
        <circle :cx="p[0]" :cy="p[1]" r="2.8"
          :class="dead.includes(i) ? 'cn__dead' : 'cn__node'" />
      </g>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ alive.length }}</b>
        <span>апаратів у строю</span>
      </div>
      <div class="lab__stat">
        <b>{{ edges.length }}</b>
        <span>каналів зв'язку</span>
      </div>
      <div class="lab__stat" :class="connected ? 'is-green' : 'is-warm'">
        <b>{{ lambda2.toFixed(3) }}</b>
        <span>алгебраїчна зв'язність λ₂</span>
      </div>
      <div class="lab__stat" :class="{ 'is-warm': components > 1 }">
        <b>{{ components }}</b>
        <span>компонент зв'язності</span>
      </div>
      <div class="lab__stat">
        <b>{{ t99 === Infinity ? '∞' : t99.toFixed(1) + ' с' }}</b>
        <span>межа часу консенсусу</span>
      </div>
    </div>

    <p class="lab__note">
      Зменшуйте радіус: спершу зникають далекі ребра й λ₂ повільно падає, а потім
      одним кроком графа розпадається — λ₂ стрибком стає нулем, і час консенсусу
      перетворюється на нескінченність. Кратність нуля у спектрі дорівнює числу
      компонент: це і є відповідь на питання «на скільки груп розпався рій».
    </p>
  </div>
</template>

<style scoped>
.cn__plot {
  width: 100%;
  height: auto;
  background: var(--uk-fill);
  border-radius: 10px;
  margin-bottom: 0.2rem;
}
.cn__edge { stroke: var(--uk-line); stroke-width: 0.45; }
.cn__node { fill: var(--uk-accent); transition: fill 0.15s ease; }
.cn__dead { fill: var(--vp-c-text-3); opacity: 0.35; }
.cn__hit { cursor: pointer; }
.cn__hit:hover circle { stroke: var(--uk-warm); stroke-width: 1.1; }
</style>
