<script setup lang="ts">
/**
 * Динамічне програмування на марсоході: цінності прохід за проходом.
 *
 * Модуль 04, картка «Модель відома: динамічне програмування». Та сама модель,
 * що в блоці коду картки (Albrecht et al., рис. 2.3), і той самий прохід
 * `sweep`: нові Q і V усіх станів рахуються зі СТАРИХ цінностей попереднього
 * проходу. Обчислення детерміновані, тому числа віджета збігаються з таблицею
 * «прохід | Старт | Точка A | Точка B», яку друкує код, для обох γ.
 */
import { ref, computed } from 'vue'

type Outcome = [number, number, string | null] // ймовірність, винагорода, куди
const STATES = ['Старт', 'Точка A', 'Точка B'] as const
type S = (typeof STATES)[number]
const ACTS = ['ліворуч', 'праворуч'] as const
const MDP: Record<S, Record<(typeof ACTS)[number], Outcome[]>> = {
  'Старт': {
    'ліворуч': [[0.9, -1, 'Точка A'], [0.1, -3, null]],
    'праворуч': [[0.5, 10, null], [0.5, -10, null]]
  },
  'Точка A': {
    'ліворуч': [[1.0, -1, 'Старт']],
    'праворуч': [[0.8, -1, 'Точка B'], [0.2, -3, null]]
  },
  'Точка B': {
    'ліворуч': [[1.0, -1, 'Точка A']],
    'праворуч': [[1.0, 10, null]]
  }
}

const gamma = ref(0.95)
const pass = ref(0)

/** Той самий порядок операцій, що в q_value з коду лекції. */
function qValue(V: Record<string, number>, s: S, a: (typeof ACTS)[number], g: number) {
  let sum = 0
  for (const [p, r, nxt] of MDP[s][a]) sum += p * (r + g * (nxt ? V[nxt] : 0))
  return sum
}

/** Історія проходів: [k] — Q, порахований у проході k+1, і V після нього. */
const history = computed(() => {
  const g = gamma.value
  let V: Record<string, number> = { 'Старт': 0, 'Точка A': 0, 'Точка B': 0 }
  const out: { Q: Record<S, number[]>; V: Record<string, number> }[] = []
  for (let k = 0; k < 6; k++) {
    const Q = {} as Record<S, number[]>
    for (const s of STATES) Q[s] = ACTS.map((a) => qValue(V, s, a, g))
    V = Object.fromEntries(STATES.map((s) => [s, Math.max(...Q[s])]))
    out.push({ Q, V })
  }
  return out
})

const cur = computed(() => (pass.value ? history.value[pass.value - 1] : null))
const prevV = computed(() => (pass.value > 1 ? history.value[pass.value - 2].V : { 'Старт': 0, 'Точка A': 0, 'Точка B': 0 }))
const V = (s: S) => (cur.value ? cur.value.V[s] : 0)
const Q = (s: S, i: number) => (cur.value ? cur.value.Q[s][i] : null)
const best = (s: S) => (cur.value ? cur.value.Q[s].indexOf(Math.max(...cur.value.Q[s])) : -1)
const changed = (s: S) => pass.value > 0 && Math.abs(V(s) - prevV.value[s]) > 1e-9
const delta = computed(() =>
  pass.value ? Math.max(...STATES.map((s) => Math.abs(V(s) - prevV.value[s]))) : null
)
const converged = computed(() => pass.value > 1 && delta.value !== null && delta.value < 1e-9)

function next() {
  if (pass.value < history.value.length) pass.value++
}
function setGamma(g: number) {
  gamma.value = g
  pass.value = 0
}
const fmt = (v: number | null) =>
  v === null ? '—' : v.toFixed(2).replace('.', ',').replace('-', '−')

// Схема: координати станів і стрілок у viewBox 520×250.
const POS: Record<S | 'База', [number, number]> = {
  'Старт': [70, 180], 'Точка A': [205, 70], 'Точка B': [360, 70], 'База': [465, 180]
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Динамічне програмування: цінності прохід за проходом</div>
        <div class="lab__sub">
          Кожен прохід застосовує рівняння Беллмана до всіх трьох станів одразу, беручи
          цінності з попереднього проходу. Числа — ті самі, що в таблиці коду вище.
        </div>
      </div>
      <button class="lab__btn" @click="pass = 0">Спочатку</button>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" :class="{ 'is-on': gamma === 0.95 }" @click="setGamma(0.95)">γ = 0,95</button>
      <button class="lab__pill" :class="{ 'is-on': gamma === 0.3 }" @click="setGamma(0.3)">γ = 0,3</button>
      <button class="lab__pill" :disabled="pass >= history.length" @click="next">наступний прохід →</button>
    </div>

    <svg class="ms__plot" viewBox="0 0 520 250" aria-label="Марсохід: цінності станів і дій">
      <defs>
        <marker id="ms-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill="context-stroke" />
        </marker>
      </defs>
      <!-- стрілки дій -->
      <path d="M92,158 Q110,95 172,78" class="ms__edge" :class="{ 'is-best': best('Старт') === 0 }" marker-end="url(#ms-arrow)" />
      <path d="M100,196 L428,196" class="ms__edge" :class="{ 'is-best': best('Старт') === 1 }" marker-end="url(#ms-arrow)" />
      <path d="M186,98 Q150,150 100,168" class="ms__edge" :class="{ 'is-best': best('Точка A') === 0 }" marker-end="url(#ms-arrow)" />
      <path d="M242,62 L322,62" class="ms__edge" :class="{ 'is-best': best('Точка A') === 1 }" marker-end="url(#ms-arrow)" />
      <path d="M323,82 L244,82" class="ms__edge" :class="{ 'is-best': best('Точка B') === 0 }" marker-end="url(#ms-arrow)" />
      <path d="M388,94 Q420,120 445,158" class="ms__edge" :class="{ 'is-best': best('Точка B') === 1 }" marker-end="url(#ms-arrow)" />
      <!-- підписи Q на стрілках -->
      <text x="78" y="110" class="ms__q">{{ fmt(Q('Старт', 0)) }}</text>
      <text x="265" y="213" class="ms__q" text-anchor="middle">{{ fmt(Q('Старт', 1)) }} · 50 % база, 50 % втрата</text>
      <text x="152" y="176" class="ms__q" text-anchor="middle">{{ fmt(Q('Точка A', 0)) }}</text>
      <text x="282" y="52" class="ms__q" text-anchor="middle">{{ fmt(Q('Точка A', 1)) }}</text>
      <text x="284" y="100" class="ms__q" text-anchor="middle">{{ fmt(Q('Точка B', 0)) }}</text>
      <text x="440" y="118" class="ms__q">{{ fmt(Q('Точка B', 1)) }}</text>
      <!-- стани -->
      <g v-for="s in STATES" :key="s">
        <circle :cx="POS[s][0]" :cy="POS[s][1]" r="35" class="ms__node" :class="{ 'is-changed': changed(s) }" />
        <text :x="POS[s][0]" :y="POS[s][1] - 5" class="ms__name" text-anchor="middle">{{ s }}</text>
        <text :x="POS[s][0]" :y="POS[s][1] + 12" class="ms__v" text-anchor="middle">V = {{ fmt(V(s)) }}</text>
      </g>
      <circle :cx="POS['База'][0]" :cy="POS['База'][1]" r="35" class="ms__node is-term" />
      <text :x="POS['База'][0]" :y="POS['База'][1] + 4" class="ms__name" text-anchor="middle">База</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ pass }}</b>
        <span>проходів</span>
      </div>
      <div class="lab__stat">
        <b>{{ delta === null ? '—' : fmt(delta) }}</b>
        <span>найбільша зміна V за цей прохід</span>
      </div>
      <div class="lab__stat" :class="best('Старт') === 1 ? 'is-warm' : 'is-green'">
        <b>{{ best('Старт') < 0 ? '—' : ACTS[best('Старт')] }}</b>
        <span>краща дія на старті зараз</span>
      </div>
    </div>

    <p class="lab__note">
      <template v-if="pass === 0">
        Усі цінності поки нулі. Натисніть «наступний прохід»: першою «дізнається» про базу
        Точка B, бо від неї до +10 один крок.
      </template>
      <template v-else-if="converged">
        Прохід {{ pass }} нічого не змінив — цінності встоялися. При γ = {{ gamma === 0.95 ? '0,95' : '0,3' }}
        оптимально на старті — {{ ACTS[best('Старт')] }}.
      </template>
      <template v-else>
        Змінилися стани, обведені зеленим. Інформація про винагороду бази
        за один прохід просувається на один крок назад.
      </template>
    </p>
  </div>
</template>

<style scoped>
.ms__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; margin: 0.4rem 0 0.2rem; }
.ms__edge { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1.4; stroke-dasharray: 4 3; }
.ms__edge.is-best { stroke: var(--uk-green); stroke-width: 2.6; stroke-dasharray: none; }
.ms__node { fill: var(--vp-c-bg); stroke: var(--vp-c-text-2); stroke-width: 1.4; }
.ms__node.is-changed { stroke: var(--uk-green); stroke-width: 3; }
.ms__node.is-term { fill: var(--uk-accent-soft); }
.ms__name { font-size: 10.5px; font-weight: 600; fill: var(--vp-c-text-1); }
.ms__v { font-size: 9.5px; fill: var(--uk-accent); font-family: var(--vp-font-family-mono); }
.ms__q { font-size: 10px; fill: var(--vp-c-text-2); font-family: var(--vp-font-family-mono); }
</style>
