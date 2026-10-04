<script setup lang="ts">
/**
 * Політ крок за кроком: справжні траєкторії навчених політик висіння.
 *
 * Модуль 05, картка «Політ крок за кроком». Дані записав скрипт
 * gamma_course/viz/m05_flight_record.py: той самий PPO, що на кривій лекції
 * (зерно 0, звірено з кривою), на п'яти етапах навчання, DQN із трьома рівнями
 * тяги після навчання і ручне правило — з тих самих тестових стартів.
 * Віджет нічого не рахує сам, лише програє записані кроки.
 */
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import data from '../data/flight.json'

type Traj = { z: number[]; u: number[]; r: number[]; crashed: boolean }
type Run = { name: string; kind: string; trajs: Traj[] }
const RUNS = data.runs as Run[]
const DT = data.dt
const UH = data.u_hover

const runIdx = ref(RUNS.length - 3) // PPO після 307 тис. кроків
const startIdx = ref(0)
const t = ref(0) // номер кроку
const playing = ref(false)

const traj = computed(() => RUNS[runIdx.value].trajs[startIdx.value])
const nSteps = computed(() => traj.value.u.length)
const z = computed(() => traj.value.z[t.value])
const u = computed(() => (t.value > 0 ? traj.value.u[t.value - 1] : UH))
const r = computed(() => (t.value > 0 ? traj.value.r[t.value - 1] : 0))
const total = computed(() => traj.value.r.slice(0, t.value).reduce((s, x) => s + x, 0))
const vz = computed(() =>
  t.value > 0 ? (traj.value.z[t.value] - traj.value.z[t.value - 1]) / DT : 0
)
const finished = computed(() => t.value >= nSteps.value)

let raf = 0
let last = 0
function tick(now: number) {
  if (!playing.value) return
  if (!last) last = now
  const steps = Math.floor((now - last) / (DT * 1000))
  if (steps > 0) {
    t.value = Math.min(nSteps.value, t.value + steps)
    last += steps * DT * 1000
  }
  if (t.value >= nSteps.value) {
    playing.value = false
    return
  }
  raf = requestAnimationFrame(tick)
}
function play() {
  if (finished.value) t.value = 0
  playing.value = true
  last = 0
  raf = requestAnimationFrame(tick)
}
function pause() {
  playing.value = false
  cancelAnimationFrame(raf)
}
function stepBy(k: number) {
  pause()
  t.value = Math.max(0, Math.min(nSteps.value, t.value + k))
}
watch([runIdx, startIdx], () => {
  pause()
  t.value = 0
})
onMounted(() => {})
onUnmounted(() => cancelAnimationFrame(raf))

// сцена: висота 0…2 м
const SH = 230, SY0 = 12, SY1 = 210
const sy = (zz: number) => SY1 - (Math.max(0, Math.min(2, zz)) / 2) * (SY1 - SY0)
// графіки
const GW = 300, GX0 = 34, GPW = GW - GX0 - 8
const T_MAX_S = 8
const gx = (k: number) => GX0 + ((k * DT) / T_MAX_S) * GPW
const zy = (zz: number) => 10 + (1 - Math.max(0, Math.min(2, zz)) / 2) * 90
const uy = (uu: number) => 130 + (1 - Math.max(0, Math.min(1, uu))) * 60
const zPath = computed(() => traj.value.z.map((v, k) => `${k ? 'L' : 'M'}${gx(k).toFixed(1)},${zy(v).toFixed(1)}`).join(' '))
const uPath = computed(() => traj.value.u.map((v, k) => `${k ? 'L' : 'M'}${gx(k + 1).toFixed(1)},${uy(v).toFixed(1)}`).join(' '))
const fmt = (v: number, d = 2) => v.toFixed(d).replace('.', ',').replace('-', '−')
const thrustLen = computed(() => 10 + 70 * u.value) // довжина стрілки тяги ∝ u
const weightLen = 10 + 70 * UH
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Політ крок за кроком: що робить політика на різних етапах</div>
        <div class="lab__sub">
          Записані траєкторії з тестових стартів: PPO із кривої лекції (зерно 0) після різної
          кількості кроків навчання, DQN із трьома рівнями тяги та ручне правило.
        </div>
      </div>
    </div>

    <div class="hf__row">
      <span class="hf__lbl">Політика</span>
      <div class="lab__pills">
        <button v-for="(run, i) in RUNS" :key="run.name" class="lab__pill" :class="{ 'is-on': runIdx === i }"
                type="button" @click="runIdx = i">{{ run.name }}</button>
      </div>
    </div>
    <div class="hf__row">
      <span class="hf__lbl">Старт</span>
      <div class="lab__pills">
        <button v-for="(s, i) in data.starts" :key="s" class="lab__pill" :class="{ 'is-on': startIdx === i }"
                type="button" @click="startIdx = i">
          зерно {{ s }} · {{ fmt(RUNS[runIdx].trajs[i].z[0]) }} м
        </button>
      </div>
    </div>

    <div class="hf__main">
      <svg class="hf__scene" :viewBox="`0 0 150 ${SH}`" aria-label="Апарат на вертикальній осі">
        <rect x="0" :y="SY1" width="150" :height="SH - SY1" class="hf__ground" />
        <line x1="6" x2="144" :y1="sy(1)" :y2="sy(1)" class="hf__target" />
        <text x="6" :y="sy(1) + 11" class="hf__tick hf__goal">ціль 1 м</text>
        <text x="8" :y="sy(2) + 9" class="hf__tick">2 м</text>
        <text x="8" :y="SY1 - 3" class="hf__tick">0 м</text>
        <g :transform="`translate(102, ${sy(z)})`">
          <line x1="0" y1="-8" x2="0" :y2="-8 - thrustLen * 0.6" class="hf__thrust" />
          <polygon :points="`-4,${-8 - thrustLen * 0.6} 4,${-8 - thrustLen * 0.6} 0,${-14 - thrustLen * 0.6}`" class="hf__thrust-h" />
          <line x1="0" y1="7" x2="0" :y2="7 + weightLen * 0.6" class="hf__weight" />
          <rect x="-10" y="-4" width="20" height="8" rx="2" class="hf__body" />
          <line x1="-22" x2="22" y1="-5" y2="-5" class="hf__arm" />
          <ellipse cx="-22" cy="-7" rx="9" ry="2" class="hf__prop" />
          <ellipse cx="22" cy="-7" rx="9" ry="2" class="hf__prop" />
        </g>
        <text x="112" :y="sy(z) - 30" class="hf__tick hf__tg">тяга</text>
        <text x="112" :y="sy(z) + 40" class="hf__tick hf__wg">вага</text>
      </svg>

      <svg class="hf__plots" :viewBox="`0 0 ${GW} 200`" aria-label="Висота й тяга в часі">
        <text :x="GX0" y="8" class="hf__tick">висота z, м</text>
        <line :x1="GX0" :x2="GX0 + GPW" :y1="zy(1)" :y2="zy(1)" class="hf__target" />
        <line :x1="GX0" :x2="GX0 + GPW" :y1="zy(0)" :y2="zy(0)" class="hf__axis" />
        <path :d="zPath" class="hf__zline" />
        <text :x="GX0 - 3" :y="zy(2) + 3" class="hf__tick" text-anchor="end">2</text>
        <text :x="GX0 - 3" :y="zy(1) + 3" class="hf__tick" text-anchor="end">1</text>
        <text :x="GX0 - 3" :y="zy(0) + 3" class="hf__tick" text-anchor="end">0</text>
        <text :x="GX0" y="126" class="hf__tick">тяга u (частка максимальної)</text>
        <line :x1="GX0" :x2="GX0 + GPW" :y1="uy(UH)" :y2="uy(UH)" class="hf__hover" />
        <text :x="GX0 + GPW" :y="uy(UH) - 2" class="hf__tick" text-anchor="end">висіння 0,44</text>
        <path :d="uPath" class="hf__uline" />
        <text :x="GX0 - 3" :y="uy(1) + 3" class="hf__tick" text-anchor="end">1</text>
        <text :x="GX0 - 3" :y="uy(0) + 3" class="hf__tick" text-anchor="end">0</text>
        <line :x1="gx(t)" :x2="gx(t)" y1="10" y2="190" class="hf__now" />
        <text :x="GX0" y="199" class="hf__tick">0 с</text>
        <text :x="GX0 + GPW" y="199" class="hf__tick" text-anchor="end">8 с</text>
      </svg>
    </div>

    <div class="lab__controls hf__ctl">
      <div class="lab__pills">
        <button class="lab__pill is-on" type="button" @click="playing ? pause() : play()">{{ playing ? '⏸ пауза' : '▶ політ' }}</button>
        <button class="lab__pill" type="button" @click="stepBy(1)">+1 крок</button>
        <button class="lab__pill" type="button" @click="stepBy(25)">+0,5 с</button>
        <button class="lab__pill" type="button" @click="stepBy(-nSteps)">на старт</button>
      </div>
      <label class="lab__ctl">
        <span>Крок <b>{{ t }} / {{ nSteps }}</b></span>
        <input v-model.number="t" type="range" min="0" :max="nSteps" step="1" @input="pause" />
      </label>
    </div>

    <div class="lab__stats">
      <div class="lab__stat"><b>{{ fmt(t * DT, 2) }} с</b><span>час польоту</span></div>
      <div class="lab__stat"><b>{{ fmt(z) }} м</b><span>висота; v_z ≈ {{ fmt(vz) }} м/с</span></div>
      <div class="lab__stat"><b>{{ fmt(u, 3) }}</b><span>тяга на цьому кроці</span></div>
      <div class="lab__stat" :class="r >= 0 ? 'is-green' : 'is-warm'"><b>{{ fmt(r, 3) }}</b><span>винагорода за крок</span></div>
      <div class="lab__stat"><b>{{ fmt(total) }}</b><span>сума винагород досі</span></div>
    </div>

    <p class="lab__note">
      <template v-if="finished && traj.crashed">
        Аварія на {{ fmt(nSteps * DT, 2) }} с: апарат вийшов за межі (нижче 5 см або далі ніж на метр від цілі).
      </template>
      <template v-else-if="finished">
        Повний епізод 8 с; нормована віддача {{ fmt(total / (nSteps * DT)) }} за секунду.
      </template>
      <template v-else>
        Стрілка вгору — тяга, вниз — вага; коли вони рівні, апарат не прискорюється.
        Порівняйте тягу DQN (лише три значення, «смикання») із плавною тягою PPO.
      </template>
    </p>
  </div>
</template>

<style scoped>
.hf__row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.3rem 0.6rem; margin: 0.25rem 0; }
.hf__lbl { font-size: 0.8rem; color: var(--vp-c-text-2); min-width: 4.5rem; }
.hf__main { display: grid; grid-template-columns: minmax(0, 150px) minmax(0, 1fr); gap: 0.6rem; margin: 0.6rem 0 0.3rem; }
.hf__scene, .hf__plots { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; }
.hf__ground { fill: var(--uk-line); }
.hf__target { stroke: var(--uk-green); stroke-width: 1.2; stroke-dasharray: 5 4; }
.hf__hover { stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 3 3; }
.hf__axis { stroke: var(--uk-line); stroke-width: 1; }
.hf__tick { fill: var(--vp-c-text-3); font-size: 8.5px; font-family: var(--vp-font-family-mono); }
.hf__tg { fill: var(--uk-warm); }
.hf__goal { fill: var(--uk-green); }
.hf__wg { fill: var(--vp-c-text-2); }
.hf__body { fill: var(--uk-accent); }
.hf__arm { stroke: var(--vp-c-text-1); stroke-width: 2; }
.hf__prop { fill: var(--uk-accent-soft); stroke: var(--uk-accent); stroke-width: 0.6; }
.hf__thrust { stroke: var(--uk-warm); stroke-width: 2.4; }
.hf__thrust-h { fill: var(--uk-warm); }
.hf__weight { stroke: var(--vp-c-text-2); stroke-width: 1.6; stroke-dasharray: 3 2; }
.hf__zline { fill: none; stroke: var(--uk-accent); stroke-width: 1.6; }
.hf__uline { fill: none; stroke: var(--uk-warm); stroke-width: 1.1; }
.hf__now { stroke: var(--vp-c-text-1); stroke-width: 0.8; }
.hf__ctl { align-items: center; }
@media (max-width: 520px) {
  .hf__main { grid-template-columns: minmax(0, 1fr); }
  .hf__scene { max-width: 180px; }
}
</style>
