<script setup lang="ts">
/**
 * Потенціальні поля: притягання до цілі плюс відштовхування від перешкод.
 *
 * Геометрія як у картці «Числовий приклад: як складаються вектори» модуля 08:
 * апарат стартує в (0; 0), ціль у (8; 0), перешкода в (5; 1) — саме звідси
 * відстань 1,41 м у першому рядку таблиці картки.
 * Коефіцієнти дібрані так, щоб обидва режими були помітні: з однією перешкодою
 * апарат обходить її і доходить, з двома симетричними — зупиняється перед
 * проходом. Це той самий локальний мінімум, про який ідеться в тексті картки.
 */
import { ref, computed, onMounted, onBeforeUnmount, watch } from 'vue'

const W = 560, H = 260
const M = 60 // пікселів на метр по X → 9,3 м у кадрі
const toPx = (x: number, y: number) => ({ px: 24 + x * M, py: H / 2 - y * M })
const toM = (px: number, py: number) => ({ x: (px - 24) / M, y: (H / 2 - py) / M })

const GOAL = { x: 8, y: 0 }
const START = { x: 0, y: 0 }

const obstacles = ref([{ x: 5, y: 1 }])
const katt = ref(1.0)
const krep = ref(12.0)
const rho0 = ref(2.4) // радіус впливу перешкоди, м

const pos = ref({ ...START })
let still = 0
const trail = ref<{ x: number; y: number }[]>([{ ...START }])
const stuck = ref(false)
const steps = ref(0)

/** Сумарна сила: −k_att·(p − p_goal) плюс відштовхування в зоні ρ₀. */
function force(p: { x: number; y: number }) {
  let fx = -katt.value * (p.x - GOAL.x)
  let fy = -katt.value * (p.y - GOAL.y)
  for (const o of obstacles.value) {
    const dx = p.x - o.x, dy = p.y - o.y
    const d = Math.hypot(dx, dy)
    if (d > rho0.value || d < 1e-6) continue
    const mag = krep.value * (1 / d - 1 / rho0.value) / (d * d)
    fx += mag * (dx / d)
    fy += mag * (dy / d)
  }
  return { fx, fy }
}

const dist = computed(() => Math.hypot(pos.value.x - GOAL.x, pos.value.y - GOAL.y))
const fnow = computed(() => {
  const { fx, fy } = force(pos.value)
  return Math.hypot(fx, fy)
})

function reset() {
  pos.value = { ...START }
  trail.value = [{ ...START }]
  stuck.value = false
  steps.value = 0
  still = 0
}

const DT = 0.03
let raf = 0
function tick() {
  if (dist.value > 0.12 && !stuck.value && steps.value < 2000) {
    const { fx, fy } = force(pos.value)
    const mag = Math.hypot(fx, fy)
    if (mag < 1e-9) stuck.value = true
    else {
      const v = Math.min(mag, 3)
      const nx = pos.value.x + (fx / mag) * v * DT
      const ny = pos.value.y + (fy / mag) * v * DT
      // застрягання ловимо за фактичною нерухомістю: у локальному мінімумі
      // сила не зникає, вона лише перестає рухати апарат уперед
      if (Math.hypot(nx - pos.value.x, ny - pos.value.y) < 2e-3) {
        still++
        if (still > 60) stuck.value = true
      } else still = 0
      pos.value = { x: nx, y: ny }
      trail.value.push({ ...pos.value })
      steps.value++
    }
  }
  raf = requestAnimationFrame(tick)
}
onMounted(() => { raf = requestAnimationFrame(tick) })
onBeforeUnmount(() => cancelAnimationFrame(raf))
watch([obstacles, katt, krep, rho0], reset, { deep: true })

function addMirror() {
  obstacles.value = [{ x: 5, y: 1 }, { x: 5, y: -1 }]
}
function single() {
  obstacles.value = [{ x: 5, y: 1 }]
}

/** Перетягування перешкоди мишею. */
const svg = ref<SVGSVGElement | null>(null)
let dragging = -1
function down(i: number) { dragging = i }
function move(e: MouseEvent) {
  if (dragging < 0 || !svg.value) return
  const r = svg.value.getBoundingClientRect()
  const px = ((e.clientX - r.left) / r.width) * W
  const py = ((e.clientY - r.top) / r.height) * H
  const m = toM(px, py)
  obstacles.value[dragging] = { x: +m.x.toFixed(2), y: +m.y.toFixed(2) }
}
function up() { dragging = -1 }

const trailPath = computed(() =>
  trail.value.map((p, i) => {
    const { px, py } = toPx(p.x, p.y)
    return `${i ? 'L' : 'M'}${px.toFixed(1)},${py.toFixed(1)}`
  }).join(' ')
)

/** Рідке поле стрілок — щоб було видно, куди тягне в кожній точці. */
const arrows = computed(() => {
  const out: { x1: number; y1: number; x2: number; y2: number }[] = []
  for (let gx = 0.5; gx <= 8.5; gx += 0.62) {
    for (let gy = -1.9; gy <= 1.9; gy += 0.62) {
      const { fx, fy } = force({ x: gx, y: gy })
      const m = Math.hypot(fx, fy) || 1
      const len = Math.min(0.26, 0.06 + m * 0.02)
      const a = toPx(gx, gy)
      const b = toPx(gx + (fx / m) * len, gy + (fy / m) * len)
      out.push({ x1: a.px, y1: a.py, x2: b.px, y2: b.py })
    }
  }
  return out
})
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Потенціальні поля: коли метод стає в глухий кут</div>
        <div class="lab__sub">
          Ціль тягне, перешкода відштовхує. Перешкоду можна перетягнути мишею.
          Кнопка «Дві симетричні» ставить другу навпроти першої.
        </div>
      </div>
      <button class="lab__btn" @click="reset">Спочатку</button>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" :class="{ 'is-on': obstacles.length === 1 }" @click="single">
        Одна перешкода
      </button>
      <button class="lab__pill" :class="{ 'is-on': obstacles.length === 2 }" @click="addMirror">
        Дві симетричні
      </button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Притягання <b>{{ katt.toFixed(1) }}</b></span>
        <input v-model.number="katt" type="range" min="0.2" max="3" step="0.1" />
      </label>
      <label class="lab__ctl">
        <span>Відштовхування <b>{{ krep.toFixed(1) }}</b></span>
        <input v-model.number="krep" type="range" min="0" max="14" step="0.5" />
      </label>
      <label class="lab__ctl">
        <span>Радіус впливу <b>{{ rho0.toFixed(1) }} м</b></span>
        <input v-model.number="rho0" type="range" min="0.6" max="3.2" step="0.1" />
      </label>
    </div>

    <svg
      ref="svg" class="pf__plot" :viewBox="`0 0 ${W} ${H}`"
      @mousemove="move" @mouseup="up" @mouseleave="up"
      aria-label="Векторне поле, траєкторія і перешкоди"
    >
      <line v-for="(a, i) in arrows" :key="i"
        :x1="a.x1" :y1="a.y1" :x2="a.x2" :y2="a.y2" class="pf__arrow" />

      <circle v-for="(o, i) in obstacles" :key="'r' + i"
        :cx="toPx(o.x, o.y).px" :cy="toPx(o.x, o.y).py" :r="rho0 * M" class="pf__zone" />

      <path :d="trailPath" class="pf__trail" />

      <circle :cx="toPx(GOAL.x, GOAL.y).px" :cy="toPx(GOAL.x, GOAL.y).py" r="7" class="pf__goal" />
      <circle v-for="(o, i) in obstacles" :key="'o' + i"
        :cx="toPx(o.x, o.y).px" :cy="toPx(o.x, o.y).py" r="9"
        class="pf__obs" @mousedown="down(i)" />
      <circle :cx="toPx(pos.x, pos.y).px" :cy="toPx(pos.x, pos.y).py" r="5.5" class="pf__uav" />
    </svg>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ pos.x.toFixed(2) }}; {{ pos.y.toFixed(2) }}</b>
        <span>положення апарата, м</span>
      </div>
      <div class="lab__stat" :class="{ 'is-green': dist < 0.15 }">
        <b>{{ dist.toFixed(2) }} м</b>
        <span>відстань до цілі</span>
      </div>
      <div class="lab__stat">
        <b>{{ fnow.toFixed(2) }}</b>
        <span>модуль сумарної сили</span>
      </div>
      <div class="lab__stat" :class="{ 'is-warm': stuck }">
        <b>{{ stuck ? 'так' : 'ні' }}</b>
        <span>застряг у мінімумі</span>
      </div>
    </div>

    <p class="lab__note">
      З однією перешкодою апарат обходить її збоку й доходить до цілі. Поставте
      дві симетричні — бічні складові взаємно знищаться, звертати нікуди,
      поздовжні додадуться й переважать притягання: апарат зупиниться перед
      проходом при ненульовій відстані до цілі. Це класичний локальний мінімум,
      і саме він мотивує перехід до навчання в наступних модулях.
    </p>
  </div>
</template>

<style scoped>
.pf__plot {
  width: 100%;
  height: auto;
  background: var(--uk-fill);
  border-radius: 10px;
  margin-bottom: 0.2rem;
  touch-action: none;
}
.pf__arrow { stroke: var(--vp-c-text-3); stroke-width: 1; opacity: 0.42; }
.pf__zone { fill: var(--uk-warm); opacity: 0.09; }
.pf__trail { fill: none; stroke: var(--uk-accent); stroke-width: 2.2; }
.pf__goal { fill: var(--uk-green); }
.pf__obs { fill: var(--uk-warm); cursor: grab; }
.pf__obs:active { cursor: grabbing; }
.pf__uav { fill: var(--uk-accent); stroke: var(--vp-c-bg); stroke-width: 2; }
</style>
