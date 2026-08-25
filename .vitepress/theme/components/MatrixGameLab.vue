<script setup lang="ts">
/**
 * Матричні ігри: рівновага Неша, Парето-оптимальність, добробут і справедливість.
 *
 * Виплати ті самі, що на картках модуля 05: Prisoner's Dilemma з єдиною
 * рівновагою (D,D) = (−3,−3), Stag Hunt із двома рівновагами (4,4) і (2,2),
 * Chicken і Battle of the Sexes. Клітинки підсвічуються самі: рівновага —
 * там, де жоден агент не виграє від односторонньої зміни дії.
 */
import { ref, computed } from 'vue'

type Game = { id: string; name: string; a: string[]; b: string[]; p: [number, number][][] }

const GAMES: Game[] = [
  {
    id: 'pd', name: "Prisoner's Dilemma", a: ['C', 'D'], b: ['C', 'D'],
    p: [[[-1, -1], [-5, 0]], [[0, -5], [-3, -3]]]
  },
  {
    id: 'sh', name: 'Stag Hunt', a: ['Олень', 'Заєць'], b: ['Олень', 'Заєць'],
    p: [[[4, 4], [1, 3]], [[3, 1], [2, 2]]]
  },
  {
    id: 'ch', name: 'Chicken', a: ['Звернути', 'Прямо'], b: ['Звернути', 'Прямо'],
    p: [[[0, 0], [-1, 1]], [[1, -1], [-10, -10]]]
  },
  {
    id: 'bs', name: 'Battle of the Sexes', a: ['Опера', 'Футбол'], b: ['Опера', 'Футбол'],
    p: [[[2, 1], [0, 0]], [[0, 0], [1, 2]]]
  }
]

const pick = ref(0)
const g = computed(() => GAMES[pick.value])

/** Клітинка (i,j) — рівновага, якщо жодному агенту не вигідно змінити дію самому. */
const nash = computed(() => {
  const p = g.value.p
  const out: boolean[][] = [[false, false], [false, false]]
  for (let i = 0; i < 2; i++)
    for (let j = 0; j < 2; j++) {
      const okA = p[i][j][0] >= p[1 - i][j][0]
      const okB = p[i][j][1] >= p[i][1 - j][1]
      out[i][j] = okA && okB
    }
  return out
})

/** Парето: не існує клітинки, яка не гірша обом і краща хоча б одному. */
const pareto = computed(() => {
  const p = g.value.p
  const all: [number, number][] = []
  for (let i = 0; i < 2; i++) for (let j = 0; j < 2; j++) all.push(p[i][j])
  const out: boolean[][] = [[false, false], [false, false]]
  for (let i = 0; i < 2; i++)
    for (let j = 0; j < 2; j++) {
      const [x, y] = p[i][j]
      out[i][j] = !all.some(([u, v]) => u >= x && v >= y && (u > x || v > y))
    }
  return out
})

const sel = ref<[number, number]>([0, 0])
const cell = computed(() => g.value.p[sel.value[0]][sel.value[1]])
const welfare = computed(() => cell.value[0] + cell.value[1])
const fairness = computed(() => cell.value[0] * cell.value[1])
const nEq = computed(() => nash.value.flat().filter(Boolean).length)
/** Чи є рівновага Парето-оптимальною — головне питання Prisoner's Dilemma. */
const eqIsPareto = computed(() => {
  for (let i = 0; i < 2; i++)
    for (let j = 0; j < 2; j++)
      if (nash.value[i][j] && !pareto.value[i][j]) return false
  return nEq.value > 0
})
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Матрична гра: рівновага проти оптимальності</div>
        <div class="lab__sub">
          Рамка — рівновага Неша, зелений фон — Парето-оптимальна клітинка.
          Натисніть на клітинку, щоб побачити добробут і справедливість.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button
        v-for="(gm, i) in GAMES" :key="gm.id"
        class="lab__pill" :class="{ 'is-on': pick === i }"
        @click="pick = i; sel = [0, 0]"
      >{{ gm.name }}</button>
    </div>

    <table class="mg__table">
      <thead>
        <tr>
          <th />
          <th v-for="(bn, j) in g.b" :key="j">Агент 2: {{ bn }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="(an, i) in g.a" :key="i">
          <th>Агент 1: {{ an }}</th>
          <td
            v-for="(bn, j) in g.b" :key="j"
            class="mg__cell"
            :class="{
              'is-nash': nash[i][j],
              'is-pareto': pareto[i][j],
              'is-sel': sel[0] === i && sel[1] === j
            }"
            @click="sel = [i, j]"
          >
            {{ g.p[i][j][0] }}, {{ g.p[i][j][1] }}
          </td>
        </tr>
      </tbody>
    </table>

    <div class="mg__legend">
      <span class="mg__key"><i class="mg__swatch is-nash" /> рівновага Неша</span>
      <span class="mg__key"><i class="mg__swatch is-pareto" /> Парето-оптимальна</span>
      <span class="mg__key">виплати подано як «агент 1, агент 2»</span>
    </div>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ nEq }}</b>
        <span>детермінованих рівноваг</span>
      </div>
      <div class="lab__stat">
        <b>{{ welfare }}</b>
        <span>добробут обраної клітинки</span>
      </div>
      <div class="lab__stat">
        <b>{{ fairness }}</b>
        <span>справедливість, добуток</span>
      </div>
      <div class="lab__stat" :class="eqIsPareto ? 'is-green' : 'is-warm'">
        <b>{{ eqIsPareto ? 'так' : 'ні' }}</b>
        <span>рівновага Парето-оптимальна</span>
      </div>
    </div>

    <p class="lab__note">
      У Prisoner's Dilemma єдина рівновага не є Парето-оптимальною: обидва
      агенти раціональні, і обидва отримують гірше, ніж могли б. У Stag Hunt
      рівноваг дві, і вибір між ними неможливо зробити наодинці — це і є
      проблема вибору рівноваги з модуля. Для рою висновок практичний: тип гри
      визначає, чи можна взагалі очікувати доброго спільного рішення від
      незалежно навчених агентів.
    </p>
  </div>
</template>

<style scoped>
.mg__table {
  border-collapse: separate;
  border-spacing: 4px;
  margin: 0.9rem 0 0.2rem;
  font-size: 0.86rem;
}
.mg__table th {
  font-weight: 500;
  color: var(--vp-c-text-3);
  font-size: 0.78rem;
  padding: 0.2rem 0.5rem;
  text-align: center;
}
.mg__cell {
  padding: 0.75rem 1.1rem;
  text-align: center;
  border: 2px solid transparent;
  border-radius: 8px;
  background: var(--uk-fill);
  font-family: var(--vp-font-family-mono);
  font-variant-numeric: tabular-nums;
  cursor: pointer;
  transition: border-color 0.15s ease;
}
.mg__cell.is-pareto { background: color-mix(in srgb, var(--uk-green) 18%, var(--uk-fill)); }
.mg__cell.is-nash {
  border-color: var(--uk-accent);
  box-shadow: inset 0 0 0 1px var(--uk-accent);
  font-weight: 600;
}
.mg__cell.is-sel { outline: 2px dashed var(--uk-warm); outline-offset: 2px; }

/* Легенда під таблицею: без неї кольори доводиться вгадувати. */
.mg__legend {
  display: flex;
  flex-wrap: wrap;
  gap: 0.9rem;
  font-size: 0.76rem;
  color: var(--vp-c-text-3);
  margin-bottom: 0.2rem;
}
.mg__key {
  display: inline-flex;
  align-items: center;
  gap: 0.35rem;
}
.mg__swatch {
  width: 0.9rem;
  height: 0.9rem;
  border-radius: 3px;
  border: 2px solid transparent;
  background: var(--uk-fill);
}
.mg__swatch.is-nash { border-color: var(--uk-accent); box-shadow: inset 0 0 0 1px var(--uk-accent); }
.mg__swatch.is-pareto { background: color-mix(in srgb, var(--uk-green) 18%, var(--uk-fill)); }
</style>
