<script setup lang="ts">
/**
 * Q-learning на сітці 3×3 крок за кроком.
 *
 * Модуль 04, картка «Q-learning у дії». Віджет НЕ генерує власних епізодів:
 * він програє переходи, записані тим самим Python-кодом, що на картці
 * (gamma_course/viz/m04_gridworld_replay.py → data/gridworld.json), і сам
 * рахує кожне оновлення тими самими операціями. Тому V після 2, 20 і 400
 * епізодів збігаються з виводом коду до сотих.
 */
import { ref, computed } from 'vue'
import data from '../data/gridworld.json'

const GOAL = 2 // клітинка (1,3)
const TRAP = 4 // клітинка (2,2)
const G = data.gamma
const AL = data.alpha
const NAMES = ['вгору', 'вниз', 'ліворуч', 'праворуч']
const ARROW = ['↑', '↓', '←', '→']
const cellName = (s: number) => `(${Math.floor(s / 3) + 1},${(s % 3) + 1})`

type Move = { s: number; a: number; s2: number }
const EPISODES: Move[][] = data.episodes.map((e: string) => {
  const out: Move[] = []
  for (let k = 0; k < e.length; k += 3) out.push({ s: +e[k], a: +e[k + 1], s2: +e[k + 2] })
  return out
})

const ep = ref(0) // скільки епізодів пройдено повністю
const t = ref(0) // скільки кроків поточного епізоду вже застосовано
const Q = ref<number[][]>(Array.from({ length: 9 }, () => [0, 0, 0, 0]))
const last = ref<null | { m: Move; r: number; target: number; old: number; nw: number; nextMax: number; done: boolean }>(null)

function apply(m: Move, record: boolean) {
  const q = Q.value
  const r = m.s2 === GOAL ? 10 : m.s2 === TRAP ? -5 : 0
  const done = m.s2 === GOAL || m.s2 === TRAP
  const nextMax = done ? 0 : Math.max(...q[m.s2])
  const target = r + (done ? 0 : G * nextMax)
  const old = q[m.s][m.a]
  q[m.s][m.a] += AL * (target - q[m.s][m.a]) // те саме правило, що в коді
  if (record) last.value = { m, r, target, old, nw: q[m.s][m.a], nextMax, done }
}

function nextStep() {
  if (ep.value >= EPISODES.length) return
  apply(EPISODES[ep.value][t.value], true)
  t.value++
  if (t.value >= EPISODES[ep.value].length) {
    ep.value++
    t.value = 0
  }
  Q.value = [...Q.value]
}
function finishEpisode() {
  if (ep.value >= EPISODES.length) return
  const moves = EPISODES[ep.value]
  for (; t.value < moves.length; t.value++) apply(moves[t.value], t.value === moves.length - 1)
  ep.value++
  t.value = 0
  Q.value = [...Q.value]
}
function runTo(n: number) {
  while (ep.value < n) finishEpisode()
}
function reset() {
  ep.value = 0
  t.value = 0
  last.value = null
  Q.value = Array.from({ length: 9 }, () => [0, 0, 0, 0])
}

const values = computed(() => Q.value.map((row) => Math.max(...row)))
const vmax = computed(() => Math.max(...values.value.map(Math.abs), 0.001))
const agent = computed(() => {
  if (last.value && t.value > 0) return last.value.m.s2
  return 0
})
const epsNow = computed(() => Math.max(0.1, 1 - (ep.value + 1) / 200))
const fmt = (v: number) => v.toFixed(2).replace('.', ',').replace('-', '−')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Q-learning крок за кроком: ті самі епізоди, що в коді</div>
        <div class="lab__sub">
          Сітка 3×3, γ = 0,9, α = 0,5, старт (1,1), ціль (1,3) +10, пастка (2,2) −5.
          Переходи записано кодом картки; віджет лише програє їх і рахує оновлення.
        </div>
      </div>
      <button class="lab__btn" @click="reset">Спочатку</button>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" :disabled="ep >= 400" @click="nextStep">наступний крок</button>
      <button class="lab__pill" :disabled="ep >= 400" @click="finishEpisode">до кінця епізоду</button>
      <button class="lab__pill" :disabled="ep >= 20" @click="runTo(20)">до 20 епізодів</button>
      <button class="lab__pill" :disabled="ep >= 400" @click="runTo(400)">до 400</button>
    </div>

    <div class="gw__wrap">
      <div class="gw__grid">
        <div
          v-for="(v, s) in values" :key="s"
          class="gw__cell"
          :class="{ 'is-goal': s === GOAL, 'is-trap': s === TRAP, 'is-start': s === 0,
                    'is-upd': last && last.m.s === s }"
          :style="{ '--w': s === GOAL || s === TRAP ? 0 : Math.max(0, v / vmax) }"
        >
          <span class="gw__id">{{ cellName(s) }}</span>
          <template v-if="s === GOAL"><b class="gw__tag">ціль +10</b></template>
          <template v-else-if="s === TRAP"><b class="gw__tag">пастка −5</b></template>
          <template v-else>
            <span v-for="a in 4" :key="a" class="gw__q" :class="['q' + (a - 1), { 'is-hit': last && last.m.s === s && last.m.a === a - 1 }]">
              {{ ARROW[a - 1] }}{{ fmt(Q[s][a - 1]) }}
            </span>
          </template>
          <span v-if="agent === s && (ep > 0 || t > 0)" class="gw__agent" aria-label="агент">●</span>
        </div>
      </div>

      <div class="gw__side">
        <div class="lab__stats gw__stats">
          <div class="lab__stat"><b>{{ ep }}{{ t ? ` + ${t} кр.` : '' }}</b><span>епізодів пройдено</span></div>
          <div class="lab__stat"><b>{{ fmt(values[0]) }}</b><span>V(старт) = max Q</span></div>
          <div class="lab__stat"><b>{{ ep < 400 ? epsNow.toFixed(2).replace('.', ',') : '—' }}</b><span>ε у поточному епізоді</span></div>
        </div>
        <p v-if="last" class="gw__upd">
          Останнє оновлення: {{ cellName(last.m.s) }}, {{ NAMES[last.m.a] }} → {{ cellName(last.m.s2) }}<br />
          Q ← {{ fmt(last.old) }} + 0,5 · [{{ fmt(last.r) }}
          <template v-if="!last.done"> + 0,9 · {{ fmt(last.nextMax) }}</template>
          − {{ fmt(last.old) }}] = <b>{{ fmt(last.nw) }}</b>
          <span v-if="last.done"> (кінець епізоду: продовження немає)</span>
        </p>
        <p v-else class="gw__upd">Натисніть «наступний крок».</p>
      </div>
    </div>

    <p class="lab__note">
      Ручний розрахунок картки тут справжній: оновлення до 5,00 відбувається на останньому
      кроці першого епізоду, до 2,25 — на четвертому кроці третього. Далі порівняйте з виводом
      коду: після 2 епізодів V(старт) = 0,00, після 20 — 8,91, після 400 — 9,00.
    </p>
  </div>
</template>

<style scoped>
.gw__wrap { display: flex; flex-wrap: wrap; gap: 1rem; align-items: flex-start; margin: 0.8rem 0 0.2rem; }
.gw__grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 3px;
  width: min(100%, 21rem);
}
.gw__side { flex: 1 1 14rem; min-width: 0; }
.gw__stats { margin-top: 0; }
.gw__cell {
  position: relative;
  aspect-ratio: 1;
  border-radius: 6px;
  border: 1px solid var(--uk-line);
  background: color-mix(in srgb, var(--uk-accent) calc(var(--w) * 55%), var(--uk-fill));
}
.gw__cell.is-goal { background: color-mix(in srgb, var(--uk-green) 22%, var(--uk-fill)); border-color: var(--uk-green); }
.gw__cell.is-trap { background: color-mix(in srgb, var(--uk-warm) 22%, var(--uk-fill)); border-color: var(--uk-warm); }
.gw__cell.is-start { border-color: var(--uk-accent); border-width: 2px; }
.gw__cell.is-upd { box-shadow: 0 0 0 2px var(--uk-green) inset; }
.gw__id { position: absolute; left: 4px; top: 2px; font-size: 0.6rem; color: var(--vp-c-text-3); }
.gw__tag { position: absolute; inset: 0; display: flex; align-items: center; justify-content: center; font-size: 0.72rem; }
.gw__q {
  position: absolute;
  font-family: var(--vp-font-family-mono);
  font-size: 0.58rem;
  color: var(--vp-c-text-2);
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}
.gw__q.is-hit { color: var(--uk-green); font-weight: 700; }
.q0 { top: 14%; left: 50%; transform: translateX(-50%); }
.q1 { bottom: 5%; left: 50%; transform: translateX(-50%); }
.q2 { top: 50%; left: 3px; transform: translateY(-50%); }
.q3 { top: 50%; right: 3px; transform: translateY(-50%); }
.gw__agent {
  position: absolute; left: 50%; top: 50%; transform: translate(-50%, -50%);
  color: var(--uk-warm); font-size: 1.1rem; line-height: 1;
}
.gw__upd { font-family: var(--vp-font-family-mono); font-size: 0.78rem; line-height: 1.5; margin: 0.6rem 0 0; }
</style>
