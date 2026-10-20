<script setup lang="ts">
/**
 * Матричні ігри модуля 06: найкращі відповіді, рівноваги, Парето, імовірнісні політики.
 *
 * Виплати — ті самі, що в словнику GAMES блоку коду «Шукає детерміновані рівноваги
 * Неша…» (рядок — агент 1, стовпець — агент 2). Імовірнісну рівновагу 2 × 2 віджет
 * рахує тією самою умовою байдужості, що й функція mixed_2x2 коду, тож p і q
 * збігаються з виводом блоку «Імовірнісні рівноваги…».
 */
import { ref, computed, watch } from 'vue'

type Game = { name: string; ua: string; acts: string[]; meaning: string[]; R1: number[][]; R2: number[][] }
const RPS = [[0, -1, 1], [1, 0, -1], [-1, 1, 0]]
const GAMES: Game[] = [
  { name: "Prisoner's Dilemma", ua: "дилема в'язня", acts: ['C', 'D'], meaning: ['співпрацювати', 'зрадити'],
    R1: [[-1, -5], [0, -3]], R2: [[-1, 0], [-5, -3]] },
  { name: 'Stag Hunt', ua: 'полювання на оленя', acts: ['S', 'H'], meaning: ['олень', 'заєць'],
    R1: [[4, 0], [3, 2]], R2: [[4, 3], [0, 2]] },
  { name: 'Chicken', ua: '«хто зверне»', acts: ['S', 'L'], meaning: ['не звертати', 'звернути'],
    R1: [[0, 7], [2, 6]], R2: [[0, 2], [7, 6]] },
  { name: 'Battle of the Sexes', ua: 'битва статей', acts: ['A', 'B'], meaning: ['місце A', 'місце B'],
    R1: [[10, 2], [0, 7]], R2: [[7, 2], [0, 10]] },
  { name: 'Rock-Paper-Scissors', ua: 'камінь–ножиці–папір', acts: ['R', 'P', 'S'], meaning: ['камінь', 'папір', 'ножиці'],
    R1: RPS, R2: RPS.map((r) => r.map((v) => -v)) },
]

const pick = ref(2)
const g = computed(() => GAMES[pick.value])
const n = computed(() => g.value.acts.length)
const idx = computed(() => [...Array(n.value).keys()])

/** Найкраща відповідь агента 1 у стовпці j і агента 2 у рядку i. */
const best1 = (i: number, j: number) => g.value.R1[i][j] >= Math.max(...g.value.R1.map((r) => r[j]))
const best2 = (i: number, j: number) => g.value.R2[i][j] >= Math.max(...g.value.R2[i])
const nash = (i: number, j: number) => best1(i, j) && best2(i, j)
function pareto(i: number, j: number) {
  const x = g.value.R1[i][j], y = g.value.R2[i][j]
  for (const a of idx.value) for (const b of idx.value) {
    const u = g.value.R1[a][b], v = g.value.R2[a][b]
    if (u >= x && v >= y && (u > x || v > y)) return false
  }
  return true
}
const nEq = computed(() => idx.value.flatMap((i) => idx.value.map((j) => nash(i, j))).filter(Boolean).length)
const eqPareto = computed(() => {
  const eq = idx.value.flatMap((i) => idx.value.filter((j) => nash(i, j)).map((j) => [i, j]))
  return eq.length ? eq.every(([i, j]) => pareto(i, j)) : null
})

const sel = ref<[number, number]>([0, 1])
const c1 = computed(() => g.value.R1[sel.value[0]][sel.value[1]])
const c2 = computed(() => g.value.R2[sel.value[0]][sel.value[1]])

// ---- імовірнісні політики (лише 2 × 2) ----
const p = ref(0.5) // агент 1 обирає перший рядок
const q = ref(0.5) // агент 2 обирає перший стовпець
/** Умова байдужості — та сама формула, що mixed_2x2 у коді лекції. */
const mixed = computed(() => {
  if (n.value !== 2) return null
  const A = g.value.R1, B = g.value.R2
  const qs = (A[1][1] - A[0][1]) / (A[0][0] - A[0][1] - A[1][0] + A[1][1])
  const ps = (B[1][1] - B[1][0]) / (B[0][0] - B[1][0] - B[0][1] + B[1][1])
  return ps >= 0 && ps <= 1 && qs >= 0 && qs <= 1 ? { p: ps, q: qs } : null
})
const row = computed(() => [p.value, 1 - p.value])
const col = computed(() => [q.value, 1 - q.value])
/** R̃1(рядок) — середня винагорода агента 1 за кожну свою дію проти q. */
const r1row = computed(() => [0, 1].map((i) => g.value.R1[i][0] * col.value[0] + g.value.R1[i][1] * col.value[1]))
const r2col = computed(() => [0, 1].map((j) => g.value.R2[0][j] * row.value[0] + g.value.R2[1][j] * row.value[1]))
const U1 = computed(() => row.value[0] * r1row.value[0] + row.value[1] * r1row.value[1])
const U2 = computed(() => col.value[0] * r2col.value[0] + col.value[1] * r2col.value[1])
function toEq() {
  if (mixed.value) { p.value = mixed.value.p; q.value = mixed.value.q }
}
watch(pick, () => { sel.value = [0, 1]; p.value = 0.5; q.value = 0.5 })

const f = (v: number, d = 2) => v.toFixed(d).replace('.', ',').replace('-', '−')
const s = (v: number) => (v < 0 ? '−' + Math.abs(v) : String(v))
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Матричні ігри: найкращі відповіді, рівноваги, Парето</div>
        <div class="lab__sub">
          Виплати ті самі, що в коді лекції. Рядок — дія агента 1, стовпець — агента 2, у клітинці «r₁, r₂».
          Підкреслено найкращу відповідь; клітинка, де підкреслені обидва числа, — рівновага Неша.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(gm, i) in GAMES" :key="gm.name" type="button" class="lab__pill" :class="{ 'is-on': pick === i }"
              @click="pick = i">{{ gm.ua }}</button>
    </div>

    <div class="mg__wrap">
      <table class="mg__table">
        <thead>
          <tr><th class="mg__corner">агент 1 \ агент 2</th>
            <th v-for="j in idx" :key="j">{{ g.acts[j] }} <small>{{ g.meaning[j] }}</small></th></tr>
        </thead>
        <tbody>
          <tr v-for="i in idx" :key="i">
            <th>{{ g.acts[i] }} <small>{{ g.meaning[i] }}</small></th>
            <td v-for="j in idx" :key="j" class="mg__cell"
                :class="{ 'is-nash': nash(i, j), 'is-pareto': pareto(i, j), 'is-sel': sel[0] === i && sel[1] === j }"
                @click="sel = [i, j]">
              <span :class="{ u: best1(i, j) }">{{ s(g.R1[i][j]) }}</span>,
              <span :class="{ u: best2(i, j) }">{{ s(g.R2[i][j]) }}</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    <div class="mg__legend">
      <span class="mg__key"><i class="mg__swatch is-nash" /> рівновага Неша</span>
      <span class="mg__key"><i class="mg__swatch is-pareto" /> Парето-оптимальна клітинка</span>
      <span class="mg__key">натисніть на клітинку — добробут і справедливість</span>
      <span class="mg__key">Парето, добробут і справедливість означено в частині 3</span>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ nEq }}</b><span>детермінованих рівноваг</span></div>
      <div class="lab__stat"><b>{{ s(c1 + c2) }}</b><span>добробут W = r₁ + r₂ обраної клітинки</span></div>
      <div class="lab__stat"><b>{{ c1 > 0 && c2 > 0 ? c1 * c2 : '—' }}</b>
        <span>{{ c1 > 0 && c2 > 0 ? 'справедливість F = r₁ · r₂' : 'F має сенс лише за додатних виплат' }}</span></div>
      <div class="lab__stat" :class="eqPareto === null ? '' : eqPareto ? 'is-green' : 'is-warm'">
        <b>{{ eqPareto === null ? '—' : eqPareto ? 'так' : 'ні' }}</b><span>усі рівноваги Парето-оптимальні</span></div>
    </div>

    <template v-if="n === 2">
      <div class="lab__controls">
        <label class="lab__ctl">
          <span>p — агент 1 обирає {{ g.acts[0] }} <b>{{ f(p) }}</b></span>
          <input v-model.number="p" type="range" min="0" max="1" step="0.01" />
        </label>
        <label class="lab__ctl">
          <span>q — агент 2 обирає {{ g.acts[0] }} <b>{{ f(q) }}</b></span>
          <input v-model.number="q" type="range" min="0" max="1" step="0.01" />
        </label>
      </div>
      <p class="mg__line">
        Агент 1 проти q: {{ g.acts[0] }} дає {{ f(r1row[0]) }}, {{ g.acts[1] }} — {{ f(r1row[1]) }}.
        Агент 2 проти p: {{ g.acts[0] }} дає {{ f(r2col[0]) }}, {{ g.acts[1] }} — {{ f(r2col[1]) }}.
        Очікувані віддачі: <b>U₁ = {{ f(U1) }}</b>, <b>U₂ = {{ f(U2) }}</b>.
      </p>
      <p class="mg__line">
        <template v-if="mixed">Імовірнісна рівновага: p = {{ f(mixed.p, 3) }}, q = {{ f(mixed.q, 3) }} — тут кожному агенту
          байдуже, яку дію обрати.
          <button type="button" class="lab__btn" @click="toEq">поставити рівновагу</button></template>
        <template v-else>Імовірнісної рівноваги немає: одна дія краща за будь-якого q — вона домінує.</template>
      </p>
    </template>
    <p v-else class="mg__line">
      Детермінованої рівноваги немає. Якщо обидва грають кожну дію з імовірністю 1/3, будь-яка дія дає 0 — значення гри.
      Агент 1, що грає (1/2, 1/4, 1/4), проти паперу отримує −0,25.
    </p>
  </div>
</template>

<style scoped>
.mg__wrap { overflow-x: auto; margin: 0.6rem 0 0.3rem; }
.mg__table { border-collapse: collapse; margin: 0 auto; font-variant-numeric: tabular-nums; }
.mg__table th, .mg__table td { border: 1px solid var(--uk-line); padding: 0.45rem 0.7rem; text-align: center; }
.mg__table th { font-size: 0.82rem; background: var(--uk-fill); white-space: nowrap; }
.mg__table th small { display: block; font-weight: 400; color: var(--vp-c-text-3); font-size: 0.72rem; }
.mg__corner { font-weight: 400 !important; color: var(--vp-c-text-2); }
.mg__cell { cursor: pointer; font-family: var(--vp-font-family-mono); font-size: 0.95rem; min-width: 4.5rem; }
.mg__cell .u { text-decoration: underline; text-decoration-thickness: 2px; text-underline-offset: 3px; font-weight: 700; }
.mg__cell.is-pareto { background: var(--uk-green-soft); }
.mg__cell.is-nash { outline: 2px solid var(--uk-accent); outline-offset: -3px; }
.mg__cell.is-sel { box-shadow: inset 0 0 0 3px var(--uk-warm); }
.mg__legend { display: flex; flex-wrap: wrap; gap: 0.4rem 1rem; font-size: 0.78rem; color: var(--vp-c-text-2); margin: 0.3rem 0 0.6rem; }
.mg__key { display: inline-flex; align-items: center; gap: 0.35rem; }
.mg__swatch { display: inline-block; width: 14px; height: 14px; border-radius: 3px; border: 1px solid var(--uk-line); }
.mg__swatch.is-nash { outline: 2px solid var(--uk-accent); outline-offset: -3px; }
.mg__swatch.is-pareto { background: var(--uk-green-soft); }
.mg__line { font-size: 0.88rem; line-height: 1.55; margin: 0.4rem 0; }
</style>
