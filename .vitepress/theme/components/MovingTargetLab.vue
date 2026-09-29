<script setup lang="ts">
/**
 * DQN на ланцюжку A → B → C: навіщо заморожувати ціль.
 *
 * Модуль 05, картка «DQN на числах». Ті самі 12 міні-пакетів, що друкує код
 * картки (random.seed(3), по два переходи з буфера), і ті самі обчислення:
 * спершу цілі обох переходів пакета, потім зсув оцінок, копіювання в
 * target network кожні 3 кроки. Пакети взято з виводу коду: генератор
 * Python у браузері не відтворити, а числа мають збігатися до сотих.
 */
import { ref, computed } from 'vue'

type St = 'A' | 'B' | 'C'
const GAMMA = 0.9
const LR = 0.5
const SYNC = 3
const BUFFER: Record<St, [number, St | null]> = { A: [0, 'B'], B: [0, 'C'], C: [1, null] }
/** Пакети з виводу коду картки («крок  пакет …»). */
const BATCHES: St[][] = [
  ['A', 'C'], ['B', 'C'], ['C', 'A'], ['C', 'A'], ['B', 'C'], ['C', 'A'],
  ['A', 'B'], ['C', 'B'], ['B', 'A'], ['A', 'C'], ['C', 'B'], ['C', 'A']
]
const TRUE: Record<St, number> = { A: 0.81, B: 0.9, C: 1.0 }

const frozen = ref(true)
const step = ref(0)

type Row = { Q: Record<St, number>; Qbar: Record<St, number>; ys: number[]; synced: boolean }
/** Уся історія для поточного режиму: [k] — стан після кроку k+1. */
const history = computed<Row[]>(() => {
  const Q: Record<St, number> = { A: 0, B: 0, C: 0 }
  let Qbar: Record<St, number> = { ...Q }
  const rows: Row[] = []
  BATCHES.forEach((batch, i) => {
    const src = frozen.value ? Qbar : Q
    const ys = batch.map((s) => {
      const [r, nxt] = BUFFER[s]
      return r + GAMMA * (nxt ? src[nxt] : 0)
    })
    batch.forEach((s, k) => { Q[s] += LR * (ys[k] - Q[s]) })
    const synced = (i + 1) % SYNC === 0
    if (synced) Qbar = { ...Q }
    rows.push({ Q: { ...Q }, Qbar: { ...Qbar }, ys, synced })
  })
  return rows
})

const zero: Record<St, number> = { A: 0, B: 0, C: 0 }
const cur = computed(() => (step.value ? history.value[step.value - 1] : null))
const Qnow = computed(() => cur.value?.Q ?? zero)
const QbarNow = computed(() => cur.value?.Qbar ?? zero)
const batch = computed(() => (step.value ? BATCHES[step.value - 1] : []))
/** Скільки разів змінилася ціль для A→B (γ·Q̄(B) або γ·Q(B)) — рахуємо після кожного кроку. */
const targetMoves = computed(() => {
  let moves = 0
  let prev = 0
  for (let k = 0; k < step.value; k++) {
    const src = frozen.value ? history.value[k].Qbar : history.value[k].Q
    const y = GAMMA * src.B
    if (Math.abs(y - prev) > 1e-12) moves++
    prev = y
  }
  return moves
})

function setMode(f: boolean) {
  frozen.value = f
}
const fmt = (v: number) => v.toFixed(2).replace('.', ',')
const X: Record<St, number> = { A: 62, B: 206, C: 350 }
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Рухома ціль: DQN на ланцюжку A → B → C</div>
        <div class="lab__sub">
          Буфер із трьох переходів, щокроку випадковий пакет із двох, γ = 0,9, α = 0,5.
          Пакети й числа — ті самі, що у виводі коду вище.
        </div>
      </div>
      <button class="lab__btn" @click="step = 0">Спочатку</button>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" :class="{ 'is-on': frozen }" @click="setMode(true)">ціль від замороженої копії</button>
      <button class="lab__pill" :class="{ 'is-on': !frozen }" @click="setMode(false)">ціль від живих оцінок</button>
      <button class="lab__pill" :disabled="step >= BATCHES.length" @click="step++">наступний крок →</button>
    </div>

    <svg class="mt__plot" viewBox="0 0 470 150" aria-label="Ланцюжок станів A, B, C з оцінками">
      <defs>
        <marker id="mt-arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" orient="auto">
          <path d="M0,0 L10,5 L0,10 z" fill="context-stroke" />
        </marker>
      </defs>
      <line v-for="s in (['A', 'B'] as St[])" :key="'e' + s" :x1="X[s] + 40" y1="55" :x2="X[s] + 100" y2="55"
            class="mt__edge" marker-end="url(#mt-arrow)" />
      <line x1="390" y1="55" x2="455" y2="55" class="mt__edge" marker-end="url(#mt-arrow)" />
      <text x="422" y="46" class="mt__r" text-anchor="middle">r = 1</text>
      <g v-for="s in (['A', 'B', 'C'] as St[])" :key="s">
        <circle :cx="X[s]" cy="55" r="38" class="mt__node" :class="{ 'is-batch': batch.includes(s) }" />
        <text :x="X[s]" y="50" class="mt__name" text-anchor="middle">{{ s }}</text>
        <text :x="X[s]" y="66" class="mt__q" text-anchor="middle">Q = {{ fmt(Qnow[s]) }}</text>
        <text v-if="frozen" :x="X[s]" y="108" class="mt__bar" text-anchor="middle">копія Q̄ = {{ fmt(QbarNow[s]) }}</text>
        <text :x="X[s]" y="130" class="mt__true" text-anchor="middle">справжня {{ fmt(TRUE[s]) }}</text>
      </g>
    </svg>

    <p v-if="cur" class="mt__upd">
      Крок {{ step }}: пакет {{ batch.join(' + ') }}, цілі y = {{ cur.ys.map(fmt).join(' і ') }}
      <template v-if="frozen"> — пораховані від копії Q̄</template>
      <template v-else> — пораховані від поточних Q</template>.
      <b v-if="frozen && cur.synced"> Після кроку копію оновлено: Q̄ ← Q.</b>
    </p>
    <p v-else class="mt__upd">Натисніть «наступний крок».</p>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ step }} / 12</b><span>кроків</span></div>
      <div class="lab__stat"><b>{{ fmt(Qnow.A) }}</b><span>Q(A), справжня 0,81</span></div>
      <div class="lab__stat" :class="frozen ? 'is-green' : 'is-warm'">
        <b>{{ targetMoves }}</b><span>разів змінилася ціль для A → B</span>
      </div>
    </div>

    <p class="lab__note">
      Із замороженою копією ціль для A → B змінюється лише після копіювання, кожні три кроки;
      від живих оцінок — щоразу, коли оновилася B. У таблиці це навіть прискорює збіжність:
      оновлення B не зачіпає A. У нейромережі всі оцінки спільні, крок заради одного стану
      зсуває цілі інших, і рухома ціль розгойдує навчання — тому DQN її заморожує.
    </p>
  </div>
</template>

<style scoped>
.mt__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; margin: 0.4rem 0 0.2rem; }
.mt__edge { stroke: var(--vp-c-text-2); stroke-width: 1.5; }
.mt__node { fill: var(--vp-c-bg); stroke: var(--vp-c-text-2); stroke-width: 1.4; }
.mt__node.is-batch { stroke: var(--uk-green); stroke-width: 3; }
.mt__name { font-size: 13px; font-weight: 700; fill: var(--vp-c-text-1); }
.mt__q { font-size: 10px; fill: var(--uk-accent); font-family: var(--vp-font-family-mono); }
.mt__bar { font-size: 10px; fill: var(--vp-c-text-2); font-family: var(--vp-font-family-mono); }
.mt__true { font-size: 9.5px; fill: var(--uk-green); }
.mt__r { font-size: 10px; fill: var(--vp-c-text-2); }
.mt__upd { font-family: var(--vp-font-family-mono); font-size: 0.78rem; line-height: 1.5; margin: 0.5rem 0 0; }
</style>
