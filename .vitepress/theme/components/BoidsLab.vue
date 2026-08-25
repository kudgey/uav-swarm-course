<script setup lang="ts">
/**
 * Покадрова симуляція рою за правилами Рейнольдса: canvas + requestAnimationFrame.
 *
 * Ваги розділення, вирівнювання та згуртованості — ті самі три правила, що на
 * слайді «Boids: три правила, з яких виникає рух зграї». Радіус звʼязку керує
 * тим, кого апарат узагалі бачить: саме він у Модулі 02 задає граф сусідства.
 *
 * Цикл не крутиться, коли віджет поза екраном або вкладка неактивна.
 */
import { ref, onMounted, onBeforeUnmount, watch } from 'vue'

const props = withDefaults(defineProps<{ count?: number }>(), { count: 60 })

const canvas = ref<HTMLCanvasElement | null>(null)
const wrap = ref<HTMLElement | null>(null)
const running = ref(true)
const visible = ref(false)
const fps = ref(0)

const sep = ref(1.5)
const ali = ref(1.0)
const coh = ref(0.9)
const radius = ref(60)

/** Параметр порядку: наскільки узгоджені напрямки руху, 0 — хаос, 1 — одна зграя. */
const order = ref(0)

type Boid = { x: number; y: number; vx: number; vy: number }
let boids: Boid[] = []
let raf = 0
let last = 0
let acc = 0
let frames = 0

function seed(w: number, h: number) {
  // детермінований розкид: та сама картинка при кожному відкритті
  boids = Array.from({ length: props.count }, (_, i) => {
    const a = (i / props.count) * Math.PI * 2
    return {
      x: w / 2 + Math.cos(a) * (40 + (i % 7) * 9),
      y: h / 2 + Math.sin(a) * (40 + (i % 5) * 11),
      vx: Math.cos(a * 3) * 0.6,
      vy: Math.sin(a * 3) * 0.6
    }
  })
}

function step(w: number, h: number) {
  const r2 = radius.value * radius.value
  for (const b of boids) {
    let cx = 0, cy = 0, ax = 0, ay = 0, sx = 0, sy = 0, n = 0
    for (const o of boids) {
      if (o === b) continue
      const dx = o.x - b.x
      const dy = o.y - b.y
      const d2 = dx * dx + dy * dy
      if (d2 > r2 || d2 === 0) continue
      n++
      cx += o.x; cy += o.y
      ax += o.vx; ay += o.vy
      if (d2 < 400) { sx -= (dx / d2) * 40; sy -= (dy / d2) * 40 }
    }
    if (n) {
      b.vx += (cx / n - b.x) * 0.0009 * coh.value + (ax / n - b.vx) * 0.04 * ali.value + sx * 0.02 * sep.value
      b.vy += (cy / n - b.y) * 0.0009 * coh.value + (ay / n - b.vy) * 0.04 * ali.value + sy * 0.02 * sep.value
    }
    const sp = Math.hypot(b.vx, b.vy) || 1
    if (sp > 1.9) { b.vx = (b.vx / sp) * 1.9; b.vy = (b.vy / sp) * 1.9 }
    b.x += b.vx; b.y += b.vy
    if (b.x < 0) b.x += w
    if (b.x > w) b.x -= w
    if (b.y < 0) b.y += h
    if (b.y > h) b.y -= h
  }

  // параметр порядку — модуль середнього одиничного вектора швидкості
  let ux = 0, uy = 0
  for (const b of boids) {
    const s = Math.hypot(b.vx, b.vy) || 1
    ux += b.vx / s; uy += b.vy / s
  }
  order.value = Math.hypot(ux, uy) / boids.length
}

function draw(ctx: CanvasRenderingContext2D, w: number, h: number) {
  ctx.clearRect(0, 0, w, h)
  // кольори тягнемо з CSS-змінних теми — тоді темна тема працює сама
  const css = getComputedStyle(document.documentElement)
  const line = css.getPropertyValue('--uk-line').trim() || '#d8d8e4'
  const dot = css.getPropertyValue('--uk-accent').trim() || '#3d4ec4'

  ctx.strokeStyle = line
  ctx.lineWidth = 0.6
  ctx.globalAlpha = 0.55
  const r2 = radius.value * radius.value
  for (let i = 0; i < boids.length; i++) {
    for (let j = i + 1; j < boids.length; j++) {
      const dx = boids[j].x - boids[i].x
      const dy = boids[j].y - boids[i].y
      if (dx * dx + dy * dy > r2) continue
      ctx.beginPath()
      ctx.moveTo(boids[i].x, boids[i].y)
      ctx.lineTo(boids[j].x, boids[j].y)
      ctx.stroke()
    }
  }
  ctx.globalAlpha = 1
  ctx.fillStyle = dot
  for (const b of boids) {
    ctx.beginPath()
    ctx.arc(b.x, b.y, 2.6, 0, Math.PI * 2)
    ctx.fill()
  }
}

function frame(t: number) {
  const c = canvas.value
  if (!c) return
  const ctx = c.getContext('2d')!
  const w = c.width / devicePixelRatio
  const h = c.height / devicePixelRatio
  const dt = last ? t - last : 16
  last = t; acc += dt; frames++
  if (acc >= 500) { fps.value = Math.round((frames * 1000) / acc); acc = 0; frames = 0 }
  step(w, h)
  draw(ctx, w, h)
  raf = requestAnimationFrame(frame)
}

function start() {
  if (raf || !running.value || !visible.value) return
  last = 0
  raf = requestAnimationFrame(frame)
}
function stop() {
  cancelAnimationFrame(raf)
  raf = 0
}

function resize() {
  const c = canvas.value
  const box = wrap.value
  if (!c || !box) return
  const w = box.clientWidth
  const h = Math.round(w * 0.5)
  c.width = w * devicePixelRatio
  c.height = h * devicePixelRatio
  c.style.width = w + 'px'
  c.style.height = h + 'px'
  c.getContext('2d')!.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0)
  if (!boids.length) seed(w, h)
}

let io: IntersectionObserver | null = null
let ro: ResizeObserver | null = null
function onVis() {
  document.hidden ? stop() : start()
}

onMounted(() => {
  resize()
  io = new IntersectionObserver(
    ([e]) => {
      visible.value = e.isIntersecting
      e.isIntersecting ? start() : stop()
    },
    { threshold: 0.05 }
  )
  io.observe(wrap.value!)
  ro = new ResizeObserver(resize)
  ro.observe(wrap.value!)
  document.addEventListener('visibilitychange', onVis)
})

onBeforeUnmount(() => {
  stop()
  io?.disconnect()
  ro?.disconnect()
  document.removeEventListener('visibilitychange', onVis)
})

watch(running, (v) => (v ? start() : stop()))

function reset() {
  const box = wrap.value
  if (box) seed(box.clientWidth, Math.round(box.clientWidth * 0.5))
}
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Рій за правилами Рейнольдса</div>
        <div class="lab__sub">
          Три ваги — і вся поведінка. Лінія означає, що апарати бачать одне одного,
          тобто в цей момент вони сусіди у графі рою.
        </div>
      </div>
      <button class="lab__btn" @click="reset">Перезапустити</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Розділення <b>{{ sep.toFixed(1) }}</b></span>
        <input v-model.number="sep" type="range" min="0" max="3" step="0.1" />
      </label>
      <label class="lab__ctl">
        <span>Вирівнювання <b>{{ ali.toFixed(1) }}</b></span>
        <input v-model.number="ali" type="range" min="0" max="3" step="0.1" />
      </label>
      <label class="lab__ctl">
        <span>Згуртованість <b>{{ coh.toFixed(1) }}</b></span>
        <input v-model.number="coh" type="range" min="0" max="3" step="0.1" />
      </label>
      <label class="lab__ctl">
        <span>Радіус зв'язку <b>{{ radius }}</b></span>
        <input v-model.number="radius" type="range" min="20" max="140" step="5" />
      </label>
    </div>

    <div ref="wrap" class="sw__wrap"><canvas ref="canvas" /></div>

    <div class="sw__bar">
      <button class="lab__btn" @click="running = !running">
        {{ running ? 'Пауза' : 'Продовжити' }}
      </button>
      <span class="sw__metric">
        параметр порядку <b>{{ order.toFixed(2) }}</b>
      </span>
      <span class="sw__fps">
        {{ visible ? fps + ' кадр/с' : 'поза екраном — цикл зупинено' }}
      </span>
    </div>

    <p class="lab__note">
      Виставте розділення в нуль — апарати злипнуться в точку, і параметр порядку
      підскочить до одиниці, хоча рій фізично зруйнований. Це показує, навіщо
      поряд із порядком завжди міряють мінімальну дистанцію між апаратами.
    </p>
  </div>
</template>

<style scoped>
.sw__wrap {
  width: 100%;
  background: var(--uk-fill);
  border-radius: 10px;
  overflow: hidden;
}
.sw__wrap canvas {
  display: block;
}
.sw__bar {
  display: flex;
  align-items: center;
  gap: 0.9rem;
  flex-wrap: wrap;
  margin-top: 0.6rem;
}
.sw__metric {
  font-size: 0.8rem;
  color: var(--vp-c-text-2);
}
.sw__metric b {
  font-family: var(--vp-font-family-mono);
  color: var(--uk-accent);
  font-weight: 500;
}
.sw__fps {
  margin-left: auto;
  font-family: var(--vp-font-family-mono);
  font-size: 0.76rem;
  color: var(--vp-c-text-3);
}
</style>
