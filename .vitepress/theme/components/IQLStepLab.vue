<script setup lang="ts">
/**
 * Незалежне Q-навчання двох агентів у Stag Hunt — раунд за раундом.
 *
 * Модуль 06, картка «Нестаціонарність у прогоні». Дані записав скрипт
 * gamma_course/viz/mod06_record.py: він виконує блок лекції «Незалежне Q-навчання
 * на Stag Hunt…», звіряє вивід і повторює iql() із записом кожного жеребу (зерно 3).
 * Віджет нічого не рахує заново, лише показує записані величини й підставляє
 * їх у правило оновлення Q ← Q + α(r − Q).
 */
import { ref, computed } from 'vue'
import data from '../data/iqlstep.json'

type Ag = { u: number; explore: boolean; a: number; q_before: number[]; r: number; q_after: number[] }
type Step = { t: number; agents: Ag[] }
const STEPS = data.steps as Step[]
const ACT = ['S', 'H']
const NAME = ['олень', 'заєць']
const EPS = data.eps, ALPHA = data.alpha
const WINDOWS = data.windows as [number, number][]
const Q = data.q as number[][] // [Q1(S), Q1(H), Q2(S), Q2(H)] після кожного раунду

const win = ref(1)
const inWin = computed(() => STEPS.filter((s) => s.t >= WINDOWS[win.value][0] && s.t <= WINDOWS[win.value][1]))
const k = ref(0)
const st = computed(() => inWin.value[Math.min(k.value, inWin.value.length - 1)])
function pickWin(w: number) { win.value = w; k.value = w === 1 ? 10 : 0 }
pickWin(1)

const f = (v: number, d = 2) => v.toFixed(d).replace('.', ',').replace('-', '−')
const par = (v: number) => (v < 0 ? `(${f(v)})` : f(v))

// графік Q агента 1 на всіх раундах (кожен 4-й) і позначка поточного раунду
const W = 520, H = 130, X0 = 30, PW = W - X0 - 8, Y0 = 8, PH = H - Y0 - 20
const N = Q.length
const px = (t: number) => X0 + (t / (N - 1)) * PW
const py = (v: number) => Y0 + (1 - v / 4.2) * PH
const line = (c: number) => Q.filter((_, i) => i % 4 === 0).map((q, i) => `${i ? 'L' : 'M'}${px(i * 4).toFixed(1)},${py(q[c]).toFixed(1)}`).join(' ')
const pathS = line(0), pathH = line(1)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Незалежне Q-навчання у Stag Hunt: раунд за раундом</div>
        <div class="lab__sub">
          Справжній прогін блоку лекції, зерно {{ data.seed }}: ε = {{ f(EPS, 1) }}, α = {{ f(ALPHA, 1) }}, початкові Q = 0.
          Кожен агент знає лише свої дії та свої винагороди.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button type="button" class="lab__pill" :class="{ 'is-on': win === 0 }" @click="pickWin(0)">
        раунди {{ WINDOWS[0][0] }}–{{ WINDOWS[0][1] }}: початок</button>
      <button type="button" class="lab__pill" :class="{ 'is-on': win === 1 }" @click="pickWin(1)">
        раунди {{ WINDOWS[1][0] }}–{{ WINDOWS[1][1] }}: перемикання на (H, H)</button>
    </div>

    <svg class="iq__plot" :viewBox="`0 0 ${W} ${H}`" role="img" aria-label="Оцінки Q агента 1 на всіх раундах">
      <line v-for="v in [0, 2, 4]" :key="v" :x1="X0" :x2="X0 + PW" :y1="py(v)" :y2="py(v)" class="iq__grid" />
      <text v-for="v in [0, 2, 4]" :key="'t' + v" :x="X0 - 4" :y="py(v) + 3" class="iq__tick" text-anchor="end">{{ v }}</text>
      <rect :x="px(WINDOWS[win][0])" :y="Y0" :width="Math.max(2, px(WINDOWS[win][1]) - px(WINDOWS[win][0]))" :height="PH" class="iq__win" />
      <path :d="pathS" class="iq__s" />
      <path :d="pathH" class="iq__h" />
      <line :x1="px(st.t - 1)" :x2="px(st.t - 1)" :y1="Y0" :y2="Y0 + PH" class="iq__cur" />
      <text :x="X0" :y="H - 4" class="iq__tick">раунд 1</text>
      <text :x="X0 + PW" :y="H - 4" class="iq__tick" text-anchor="end">раунд {{ N }}</text>
      <text :x="X0 + PW" :y="Y0 + 10" class="iq__tick" text-anchor="end">Q₁(S) — зелена, Q₁(H) — червона</text>
    </svg>

    <div class="lab__pills">
      <button class="lab__pill" type="button" :disabled="k === 0" @click="k--">← раунд</button>
      <span class="iq__round">раунд {{ st.t }}</span>
      <button class="lab__pill is-on" type="button" :disabled="k >= inWin.length - 1" @click="k++">раунд →</button>
    </div>

    <div class="iq__grid2">
      <div v-for="(ag, i) in st.agents" :key="i" class="iq__card">
        <div class="iq__who">Агент {{ i + 1 }}</div>
        <p>Q до раунду: <span :class="{ best: ag.q_before[0] >= ag.q_before[1] }">Q(S) = {{ f(ag.q_before[0]) }}</span>,
          <span :class="{ best: ag.q_before[1] >= ag.q_before[0] }">Q(H) = {{ f(ag.q_before[1]) }}</span>.</p>
        <p>Жереб u = {{ f(ag.u, 3) }} {{ ag.explore ? '<' : '≥' }} ε = {{ f(EPS, 1) }}:
          {{ ag.explore ? 'дія навмання' : ag.q_before[0] === ag.q_before[1] ? 'Q рівні — нічию розбиває жереб' : 'дія з більшою Q' }}
          → <b>{{ ACT[ag.a] }} ({{ NAME[ag.a] }})</b>.</p>
      </div>
    </div>
    <p class="iq__line">Спільна дія ({{ ACT[st.agents[0].a] }}, {{ ACT[st.agents[1].a] }}) → винагороди з матриці:
      r₁ = {{ st.agents[0].r }}, r₂ = {{ st.agents[1].r }}.</p>
    <div class="iq__grid2">
      <div v-for="(ag, i) in st.agents" :key="'u' + i" class="iq__card">
        <div class="iq__who">Оновлення агента {{ i + 1 }}</div>
        <p class="iq__mono">Q({{ ACT[ag.a] }}) ← {{ f(ag.q_before[ag.a]) }} + {{ f(ALPHA, 1) }} · ({{ ag.r }} − {{ par(ag.q_before[ag.a]) }})
          = <b>{{ f(ag.q_after[ag.a]) }}</b></p>
        <p>Q({{ ACT[1 - ag.a] }}) не змінюється: {{ f(ag.q_after[1 - ag.a]) }}.</p>
      </div>
    </div>
    <p class="lab__note">
      Агент 1 бачить лише своє r₁. Що r₁ за S раптом стало 0, бо агент 2 перейшов на H, для агента 1 виглядає так,
      ніби змінилося саме середовище, — це і є нестаціонарність.
    </p>
  </div>
</template>

<style scoped>
.iq__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; margin: 0.4rem 0; }
.iq__grid { stroke: var(--uk-line); stroke-width: 0.6; }
.iq__tick { fill: var(--vp-c-text-3); font-size: 9px; font-family: var(--vp-font-family-mono); }
.iq__s { fill: none; stroke: var(--uk-green); stroke-width: 1.6; }
.iq__h { fill: none; stroke: var(--uk-warm); stroke-width: 1.6; }
.iq__win { fill: var(--uk-accent); opacity: 0.12; }
.iq__cur { stroke: var(--uk-accent); stroke-width: 1.4; }
.iq__round { font-family: var(--vp-font-family-mono); font-size: 0.85rem; align-self: center; padding: 0 0.4rem; }
.iq__grid2 { display: grid; grid-template-columns: repeat(auto-fit, minmax(14rem, 1fr)); gap: 0.5rem; margin: 0.4rem 0; }
.iq__card { background: var(--uk-fill); border-radius: 10px; padding: 0.55rem 0.8rem; }
.iq__card p { margin: 0.2rem 0; font-size: 0.86rem; line-height: 1.5; }
.iq__who { font-weight: 600; font-size: 0.85rem; margin-bottom: 0.2rem; }
.iq__card .best { font-weight: 700; color: var(--uk-accent); }
.iq__mono { font-family: var(--vp-font-family-mono); font-size: 0.82rem !important; overflow-wrap: anywhere; }
.iq__line { font-size: 0.88rem; margin: 0.3rem 0; }
</style>
