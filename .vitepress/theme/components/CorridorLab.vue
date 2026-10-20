<script setup lang="ts">
/**
 * Два дрони в коридорі: жадібні польоти, записані кодом лекції.
 *
 * Модуль 06, картка «Що вивчили CQL і IQL». Дані записав скрипт
 * gamma_course/viz/mod06_record.py: він виконує блоки лекції «Коридор як
 * стохастична гра…» (ітерація за цінністю) і «Коридор: CQL проти IQL…»
 * (навчені таблиці), звіряє їхній вивід і пускає жадібні польоти зі старту.
 * Віджет лише програє ці польоти й показує оцінки Q у кожному стані.
 */
import { ref, computed, watch, onUnmounted } from 'vue'
import data from '../data/corridor.json'

type Frame = { s: number[]; obs: string[][] | null; a: number[] | null; r: number; show: any }
type Run = { name: string; kind: string; ret: number; end: string; dived: string; frames: Frame[] }
const RUNS = data.runs as Run[]
const ACTS = data.acts as string[]
const K = 5, HOME = 6
const GROUPS = [
  { key: 'opt', label: 'оптимум' }, { key: 'CQL', label: 'CQL' },
  { key: 'IQL', label: 'IQL' }, { key: 'IQL, сенсор 1', label: 'IQL, сенсор 1' },
]
const group = ref('CQL')
const inGroup = computed(() => RUNS.filter((r) => r.kind === group.value))
const ri = ref(0)
const run = computed(() => inGroup.value[Math.min(ri.value, inGroup.value.length - 1)])
const t = ref(0)
const fr = computed(() => run.value.frames[t.value])
const last = computed(() => run.value.frames.length - 1)
const ret = computed(() => run.value.frames.slice(0, t.value).reduce((s, f) => s + f.r, 0))
watch([group, ri], () => { t.value = 0; stop() })
watch(group, () => { ri.value = 0 })

let timer: ReturnType<typeof setInterval> | null = null
const playing = ref(false)
function stop() { if (timer) clearInterval(timer); timer = null; playing.value = false }
function play() {
  stop(); if (t.value >= last.value) t.value = 0
  playing.value = true
  timer = setInterval(() => { if (t.value < last.value) t.value++; else stop() }, 700)
}
onUnmounted(stop)

// координати клітинок на схемі
const CW = 64, X0 = 70, Y0 = 92
const cx = (p: number, who: number) => {
  if (p === HOME) return who === 0 ? X0 + 5 * CW + 34 : X0 - 34
  if (p === K) return X0 + 2.5 * CW
  return X0 + (p + 0.5) * CW
}
const cy = (p: number) => (p === K ? Y0 - CW * 0.5 : Y0 + CW * 0.5)
const f = (v: number, d = 1) => v.toFixed(d).replace('.', ',').replace('-', '−')
const where = (p: number) => (p === K ? 'кишеня' : p === HOME ? 'вилетів' : `клітинка ${p}`)
const showObs = (o: string[]) => `(${o[0] === '5' ? 'K' : o[0] === '6' ? 'вилетів' : o[0]}; ${o[1] === '5' ? 'K' : o[1] === '6' ? 'вилетів' : o[1]})`
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Коридор: як летять навчені політики</div>
        <div class="lab__sub">
          Жадібні польоти зі старту після 3 000 епізодів навчання — ті самі таблиці, що в коді вище; оптимум — з
          ітерації за цінністю. Синій летить праворуч, помаранчевий — ліворуч.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="g in GROUPS" :key="g.key" type="button" class="lab__pill" :class="{ 'is-on': group === g.key }"
              @click="group = g.key">{{ g.label }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="(r, i) in inGroup" :key="r.name" type="button" class="lab__pill" :class="{ 'is-on': ri === i }"
              @click="ri = i">{{ group === 'opt' ? r.name.replace('оптимум: ', '') : 'зерно ' + i }}</button>
    </div>

    <svg class="cl__scene" viewBox="0 0 460 176" role="img" aria-label="Коридор із двома дронами">
      <rect v-for="c in 5" :key="c" :x="X0 + (c - 1) * CW" :y="Y0" :width="CW" :height="CW" class="cl__cell" />
      <rect :x="X0 + 2 * CW" :y="Y0 - CW" :width="CW" :height="CW" class="cl__pocket" />
      <text :x="X0 + 2.5 * CW" :y="Y0 - CW - 8" text-anchor="middle" class="cl__lbl">кишеня</text>
      <text v-for="c in 5" :key="'n' + c" :x="X0 + (c - 0.5) * CW" :y="Y0 + CW + 16" text-anchor="middle" class="cl__lbl">{{ c - 1 }}</text>
      <text :x="X0 - 34" :y="Y0 + CW + 16" text-anchor="middle" class="cl__lbl">вихід ←</text>
      <text :x="X0 + 5 * CW + 34" :y="Y0 + CW + 16" text-anchor="middle" class="cl__lbl">→ вихід</text>
      <circle :cx="cx(fr.s[0], 0)" :cy="cy(fr.s[0])" r="17" class="cl__blue" />
      <circle :cx="cx(fr.s[1], 1)" :cy="cy(fr.s[1])" r="17" class="cl__orange" />
    </svg>

    <div class="lab__pills">
      <button class="lab__pill" type="button" :disabled="t === 0" @click="t--; stop()">← крок</button>
      <button class="lab__pill" type="button" @click="playing ? stop() : play()">{{ playing ? 'пауза' : 'політ' }}</button>
      <button class="lab__pill is-on" type="button" :disabled="t >= last" @click="t++; stop()">крок →</button>
    </div>

    <div class="cl__panel">
      <p>Крок {{ t }} з {{ last }}. Синій — {{ where(fr.s[0]) }}, помаранчевий — {{ where(fr.s[1]) }}.
        Віддача досі: <b>{{ f(ret, 0) }}</b>.</p>
      <template v-if="fr.a">
        <p v-if="group === 'IQL, сенсор 1' && fr.obs">Спостереження (своє місце; місце іншого): синій {{ showObs(fr.obs[0]) }},
          помаранчевий {{ showObs(fr.obs[1]) }}.</p>
        <p>Спільна дія: синій — <b>{{ ACTS[fr.a[0]] }}</b>, помаранчевий — <b>{{ ACTS[fr.a[1]] }}</b>;
          винагорода кроку {{ f(fr.r, 0) }}.<template v-if="(fr.a[0] === 2 && fr.s[0] !== 2 && fr.s[0] !== K) || (fr.a[1] === 2 && fr.s[1] !== 2 && fr.s[1] !== K)">
          «Кишеня» не над клітинкою 2 — те саме, що «чекати».</template></p>
        <div v-if="fr.show && fr.show.kind === 'joint'" class="cl__tab">
          <table>
            <caption>{{ group === 'opt' ? 'Q*(s, a)' : 'Q(s, a) у CQL' }}: рядок — дія синього, стовпець — помаранчевого</caption>
            <thead><tr><th></th>
              <th v-for="a in ACTS" :key="a">{{ a }}</th></tr></thead>
            <tbody><tr v-for="(rowq, i) in fr.show.q" :key="i"><th>{{ ACTS[i] }}</th>
              <td v-for="(v, j) in rowq" :key="j" :class="{ pick: fr.a[0] === i && fr.a[1] === j }">{{ f(v) }}</td></tr></tbody>
          </table>
        </div>
        <div v-else-if="fr.show" class="cl__tab">
          <table>
            <caption>Власні оцінки Q кожного дрона над його діями</caption>
            <thead><tr><th></th><th v-for="a in ACTS" :key="a">{{ a }}</th></tr></thead>
            <tbody><tr v-for="(vec, i) in fr.show.q" :key="i"><th>{{ i === 0 ? 'синій' : 'помаранчевий' }}</th>
              <td v-for="(v, j) in vec" :key="j" :class="{ pick: fr.a[i] === j }">{{ f(v) }}</td></tr></tbody>
          </table>
        </div>
      </template>
      <p v-else><b>Кінець:</b> {{ run.end }}, віддача {{ f(run.ret, 0) }}, у кишеню пірнав {{ run.dived }}.</p>
    </div>
  </div>
</template>

<style scoped>
.cl__scene { width: 100%; max-width: 560px; height: auto; display: block; margin: 0.4rem auto; background: var(--uk-fill); border-radius: 10px; }
.cl__cell { fill: var(--vp-c-bg); stroke: var(--vp-c-text-2); stroke-width: 1.2; }
.cl__pocket { fill: var(--uk-warm-soft); stroke: var(--vp-c-text-2); stroke-width: 1.2; }
.cl__lbl { fill: var(--vp-c-text-2); font-size: 15px; }
.cl__blue { fill: #2E6FB7; stroke: white; stroke-width: 2; transition: cx 0.35s, cy 0.35s; }
.cl__orange { fill: #F0A202; stroke: white; stroke-width: 2; transition: cx 0.35s, cy 0.35s; }
.cl__panel { background: var(--uk-fill); border-radius: 10px; padding: 0.6rem 0.9rem; display: grid; gap: 0.35rem; margin-top: 0.4rem; }
.cl__panel p { margin: 0; font-size: 0.88rem; line-height: 1.5; }
.cl__tab { overflow-x: auto; }
.cl__tab caption { caption-side: top; text-align: left; font-size: 0.8rem; color: var(--vp-c-text-2); padding-bottom: 0.2rem; }
.cl__tab td, .cl__tab th { font-size: 0.8rem; white-space: nowrap; }
.cl__tab td { font-family: var(--vp-font-family-mono); text-align: right; }
.cl__tab td.pick { color: var(--uk-warm); font-weight: 700; }
</style>
