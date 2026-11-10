<script setup lang="ts">
/**
 * Обмін місцями: жадібні польоти рою, записані кодом лекції.
 *
 * Модуль 09, картка «Крок 6. Порівняння». Дані записав скрипт
 * gamma_course/viz/mod09_record.py: він бере моделі, навчені mod09_swarm.py,
 * звіряє їхні оцінки з еталонним звітом і пускає жадібні польоти зерна 0 на колі
 * з 4, 8 і 16 апаратів (перший тестовий епізод). Віджет лише програє положення
 * кожні 0,1 с, пари в контакті (ближче 0,2 м) і найменшу відстань, записані скриптом.
 */
import { ref, computed, watch, onUnmounted } from 'vue'
import data from '../data/swarm09.json'

type Flight = { p: number[][][]; g: number[][]; hits: [number, number][][]; dmin: number[]; reached: number }
const FL = data.flights as Record<string, Flight>  // положення в сантиметрах
const METHODS = data.methods as string[]
const LABEL: Record<string, string> = {
  'прямо': 'прямо до цілі',
  'номери': 'за номерами',
  'відстань': 'за відстанню',
  'усереднення': 'усереднення',
  'усереднення + щільний': '+ щільний штраф',
  'усереднення + щільний → 8': 'донавчання на 8',
}
const SIZES = [4, 8, 16]
const RCOL = data.rcol as number

const method = ref(METHODS[3])
const n = ref(8)
const fl = computed(() => FL[`${method.value}|${n.value}`])
const last = computed(() => fl.value.p.length - 1)
const t = ref(0)
watch([method, n], () => { t.value = 0; stop() })

let timer: ReturnType<typeof setInterval> | null = null
const playing = ref(false)
function stop() { if (timer) clearInterval(timer); timer = null; playing.value = false }
function play() {
  stop(); if (t.value >= last.value) t.value = 0
  playing.value = true
  timer = setInterval(() => { if (t.value < last.value) t.value++; else stop() }, 70)
}
onUnmounted(stop)

/** Пари в контакті на кожному кроці записано з точних положень (на екрані — округлені до 1 см). */
const contacts = computed(() => fl.value.hits)
const pairsSoFar = computed(() => {
  const s = new Set<string>()
  for (let k = 0; k <= t.value; k++) for (const [i, j] of contacts.value[k]) s.add(`${i}-${j}`)
  return s.size
})
const pairsTotal = computed(() => {
  const s = new Set<string>()
  for (const c of contacts.value) for (const [i, j] of c) s.add(`${i}-${j}`)
  return s.size
})
const now = computed(() => fl.value.p[t.value])
const touching = computed(() => new Set(contacts.value[t.value].flat()))
const dmin = computed(() => fl.value.dmin[t.value])
const reached = computed(() => fl.value.reached)

const LIM = computed(() => Math.sqrt(n.value / 4) + 0.35)
const S = 300
const sx = (x: number) => S / 2 + (x / 100 / LIM.value) * (S / 2)
const sy = (y: number) => S / 2 - (y / 100 / LIM.value) * (S / 2)
const rpx = computed(() => (0.1 / LIM.value) * (S / 2))
const trail = (i: number) => fl.value.p.slice(0, t.value + 1).map((q) => `${sx(q[i][0]).toFixed(1)},${sy(q[i][1]).toFixed(1)}`).join(' ')
const f = (v: number, d = 2) => v.toFixed(d).replace('.', ',')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Обмін місцями: політ рою</div>
        <div class="lab__sub">
          Жадібні польоти політик лекції, зерно 0. Учили на 4 апаратах; коло з 8 і 16 — перенос без навчання
          (крім «донавчання на 8»). Червоне — апарати ближче 0,2 м один до одного.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="m in METHODS" :key="m" type="button" class="lab__pill" :class="{ 'is-on': method === m }"
              @click="method = m">{{ LABEL[m] }}</button>
    </div>
    <div class="lab__pills">
      <button v-for="k in SIZES" :key="k" type="button" class="lab__pill" :class="{ 'is-on': n === k }"
              @click="n = k">{{ k }} апаратів</button>
    </div>

    <svg class="sw__scene" :viewBox="`0 0 ${S} ${S}`" role="img" aria-label="Рій згори: апарати летять у протилежні точки кола">
      <circle :cx="S / 2" :cy="S / 2" :r="(Math.sqrt(n / 4) / LIM) * (S / 2)" class="sw__ring" />
      <g v-for="(q, i) in fl.g" :key="'g' + i">
        <line :x1="sx(q[0]) - 4" :y1="sy(q[1]) - 4" :x2="sx(q[0]) + 4" :y2="sy(q[1]) + 4" class="sw__goal" />
        <line :x1="sx(q[0]) - 4" :y1="sy(q[1]) + 4" :x2="sx(q[0]) + 4" :y2="sy(q[1]) - 4" class="sw__goal" />
      </g>
      <polyline v-for="(_, i) in now" :key="'t' + i" :points="trail(i)" class="sw__trail" />
      <circle v-for="(q, i) in now" :key="'d' + i" :cx="sx(q[0])" :cy="sy(q[1])" :r="Math.max(rpx, 3)"
              :class="touching.has(i) ? 'sw__drone sw__drone--hit' : 'sw__drone'" />
    </svg>

    <div class="lab__pills">
      <button class="lab__pill" type="button" @click="playing ? stop() : play()">{{ playing ? 'пауза' : 'політ' }}</button>
      <input v-model.number="t" class="sw__range" type="range" min="0" :max="last" aria-label="Час польоту" @input="stop()" />
    </div>

    <div class="sw__panel">
      <p>Час <b>{{ f(t * 0.1, 1) }} с</b> з {{ f(last * 0.1, 0) }}. Найменша відстань зараз:
        <b :class="{ sw__bad: dmin < RCOL }">{{ f(dmin) }} м</b>.</p>
      <p>Пар, що торкнулися: <b :class="{ sw__bad: pairsSoFar > 0 }">{{ pairsSoFar }}</b>
        (за весь політ — {{ pairsTotal }} з {{ (n * (n - 1)) / 2 }}). Дійшли до цілі наприкінці: {{ reached }} з {{ n }}.</p>
    </div>
  </div>
</template>

<style scoped>
.sw__scene { width: 100%; max-width: 360px; height: auto; display: block; margin: 0.4rem auto; background: var(--uk-fill); border-radius: 10px; }
.sw__ring { fill: none; stroke: var(--vp-c-text-3); stroke-dasharray: 4 4; }
.sw__goal { stroke: #2E9E5B; stroke-width: 1.6; }
.sw__trail { fill: none; stroke: #78A6D8; stroke-width: 1.2; opacity: 0.7; }
.sw__drone { fill: #2E6FB7; stroke: white; stroke-width: 1; }
.sw__drone--hit { fill: #C0392B; }
.sw__range { flex: 1; min-width: 8rem; }
.sw__bad { color: #C0392B; }
.sw__panel { background: var(--uk-fill); border-radius: 10px; padding: 0.6rem 0.9rem; display: grid; gap: 0.35rem; margin-top: 0.4rem; }
.sw__panel p { margin: 0; font-size: 0.88rem; line-height: 1.5; }
</style>
