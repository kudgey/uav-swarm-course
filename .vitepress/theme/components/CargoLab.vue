<script setup lang="ts">
/**
 * Вантаж утрьох: жадібні польоти, записані кодом лекції.
 *
 * Модуль 08, картка «Крок 6. Порівняння методів». Дані записав скрипт
 * gamma_course/viz/mod08_record.py: він виконує блоки decks_new/mod08.md
 * (IA2C, критики V(s) і Q(s,a), COMA, Pareto-AC на 10 зернах), звіряє їхній
 * вивід і пускає жадібні польоти зі старту. Віджет лише програє ці польоти:
 * у кожному кроці — дії, винагорода, π(вантаж) кожного апарата, а для COMA —
 * контрфактична перевага апарата C.
 */
import { ref, computed, watch, onUnmounted } from 'vue'
import data from '../data/cargo08.json'

type Frame = { s: number[]; a: number[] | null; r: number; pi: number[][] | null; advC?: number; lifted?: boolean }
type Run = { name: string; kind: string; ret: number; frames: Frame[] }
const RUNS = data.runs as Run[]
const ACTS = data.acts as string[]
const GROUPS = data.groups as string[]
const NAMES = ['A', 'B', 'C']
const SHORT = ['лів.', 'прав.', 'вант.']  // заголовки таблиці: на 375 px повні слова зливаються
const COLORS = ['#2E6FB7', '#F0A202', '#9B59B6']

const group = ref(GROUPS[0])
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
  timer = setInterval(() => { if (t.value < last.value) t.value++; else stop() }, 800)
}
onUnmounted(stop)

const CW = 76, X0 = 40, Y0 = 40
const cx = (k: number) => {
  const p = fr.value.s[k]
  const same = [0, 1, 2].filter((j) => fr.value.s[j] === p)
  return X0 + (p + 0.5) * CW + (same.indexOf(k) - (same.length - 1) / 2) * 22
}
const f = (v: number, d = 2) => v.toFixed(d).replace('.', ',').replace('-', '−')
const actName = (k: number, a: number) => (a === 2 && fr.value.s[k] !== 0 ? 'стояти' : ACTS[a])
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Вантаж утрьох: політ крок за кроком</div>
        <div class="lab__sub">
          Жадібні польоти політик, навчених у кроках 1–5 (3 000 епізодів, зерна 0–9). Вантаж у клітинці 0 піднімають
          двоє одночасно (+1); якщо тягне один — −0,6.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="g in GROUPS" :key="g" type="button" class="lab__pill" :class="{ 'is-on': group === g }"
              @click="group = g">{{ g }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="(r, i) in inGroup" :key="r.name" type="button" class="lab__pill" :class="{ 'is-on': ri === i }"
              @click="ri = i">зерно {{ i }}<template v-if="r.ret > 0"> ✓</template></button>
    </div>

    <svg class="cg__scene" viewBox="0 0 460 150" role="img" aria-label="Лінія з п'яти клітинок, вантаж і три апарати">
      <rect v-for="c in 5" :key="c" :x="X0 + (c - 1) * CW" :y="Y0" :width="CW" :height="CW" class="cg__cell" />
      <rect :x="X0 + 10" :y="Y0 + CW - 24" :width="CW - 20" height="16" rx="3"
            :class="fr.lifted ? 'cg__load cg__load--up' : 'cg__load'" />
      <text v-for="c in 5" :key="'n' + c" :x="X0 + (c - 0.5) * CW" :y="Y0 + CW + 20" text-anchor="middle"
            class="cg__lbl">{{ c - 1 }}</text>
      <template v-for="k in 3" :key="'d' + k">
        <circle :cx="cx(k - 1)" :cy="Y0 + 28" r="11" :fill="COLORS[k - 1]" class="cg__drone" />
        <text :x="cx(k - 1)" :y="Y0 + 33" text-anchor="middle" class="cg__dl">{{ NAMES[k - 1] }}</text>
      </template>
      <text v-if="fr.lifted" :x="X0 + 2.5 * CW" :y="Y0 - 12" text-anchor="middle" class="cg__ok">вантаж піднято: +1</text>
    </svg>

    <div class="lab__pills">
      <button class="lab__pill" type="button" :disabled="t === 0" @click="t--; stop()">← крок</button>
      <button class="lab__pill" type="button" @click="playing ? stop() : play()">{{ playing ? 'пауза' : 'політ' }}</button>
      <button class="lab__pill is-on" type="button" :disabled="t >= last" @click="t++; stop()">крок →</button>
    </div>

    <div class="cg__panel">
      <p>Крок {{ t }} з {{ last }}. A — клітинка {{ fr.s[0] }}, B — {{ fr.s[1] }}, C — {{ fr.s[2] }}.
        Віддача досі: <b>{{ f(ret, 1) }}</b>.</p>
      <template v-if="fr.a">
        <p>Дії: <template v-for="k in 3" :key="'a' + k"><b>{{ NAMES[k - 1] }}</b> — {{ actName(k - 1, fr.a[k - 1]) }}<template
          v-if="k < 3">, </template></template>; винагорода кроку
          <b :class="{ cg__bad: fr.r < 0, cg__good: fr.r > 0 }">{{ f(fr.r, 1) }}</b>.</p>
        <div v-if="fr.pi" class="cg__tab">
          <table>
            <caption>Імовірності дій кожного апарата в цьому стані</caption>
            <thead><tr><th></th><th v-for="a in SHORT" :key="a">{{ a }}</th></tr></thead>
            <tbody><tr v-for="(vec, i) in fr.pi" :key="i"><th>{{ NAMES[i] }}</th>
              <td v-for="(v, j) in vec" :key="j" :class="{ pick: fr.a[i] === j }">{{ f(v) }}</td></tr></tbody>
          </table>
        </div>
        <p v-if="group === 'COMA' && fr.advC !== undefined">Контрфактична перевага C (8.5):
          <b>{{ f(fr.advC, 3) }}</b> — наскільки дія C краща за його типову дію, коли A і B роблять те, що зробили.</p>
      </template>
      <p v-else><b>Кінець:</b> {{ fr.lifted ? 'вантаж піднято' : 'вантаж ніхто не підняв' }}, віддача {{ f(run.ret, 1) }}.</p>
    </div>
  </div>
</template>

<style scoped>
.cg__scene { width: 100%; max-width: 560px; height: auto; display: block; margin: 0.4rem auto; background: var(--uk-fill); border-radius: 10px; }
.cg__cell { fill: var(--vp-c-bg); stroke: var(--vp-c-text-2); stroke-width: 1.2; }
.cg__load { fill: #8D6E63; transition: transform 0.4s; }
.cg__load--up { fill: #2E9E5B; }
.cg__lbl { fill: var(--vp-c-text-2); font-size: 15px; }
.cg__drone { stroke: white; stroke-width: 2; transition: cx 0.35s; }
.cg__dl { fill: white; font-size: 13px; font-weight: 700; pointer-events: none; transition: x 0.35s; }
.cg__ok { fill: #2E9E5B; font-size: 16px; font-weight: 700; }
.cg__bad { color: #C0392B; }
.cg__good { color: #2E9E5B; }
.cg__panel { background: var(--uk-fill); border-radius: 10px; padding: 0.6rem 0.9rem; display: grid; gap: 0.35rem; margin-top: 0.4rem; }
.cg__panel p { margin: 0; font-size: 0.88rem; line-height: 1.5; }
.cg__tab { overflow-x: auto; }
.cg__tab caption { caption-side: top; text-align: left; font-size: 0.8rem; color: var(--vp-c-text-2); padding-bottom: 0.2rem; }
.cg__tab td, .cg__tab th { font-size: 0.8rem; white-space: nowrap; }
.cg__tab td { font-family: var(--vp-font-family-mono); text-align: right; }
.cg__tab td.pick { color: var(--uk-warm); font-weight: 700; }
</style>
