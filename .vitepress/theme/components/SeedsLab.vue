<script setup lang="ts">
/**
 * Скільки зерен потрібно, щоб висновок став стабільним.
 *
 * Відтворює картку «Що дає ця одна операція на кривих» і чек-лист модуля 10.
 * Два алгоритми з близькою справжньою якістю: A = 0,62, B = 0,58 при σ = 0,11.
 * Кожен «запуск» — одне зерно; смуга показує ±σ, а окремо рахується
 * довірчий інтервал різниці середніх. Саме він, а не перекриття смуг,
 * дозволяє щось стверджувати.
 */
import { ref, computed } from 'vue'

const TRUE_A = 0.62
const TRUE_B = 0.58
const SIGMA = 0.11

const n = ref(1)

/** Детермінований нормальний шум: та сама картинка на кожній парі. */
function gauss(i: number, salt: number) {
  let s = (i * 2654435761 + salt * 40503) % 2147483647
  const r = () => {
    s = (s * 1103515245 + 12345) & 0x7fffffff
    return s / 0x7fffffff
  }
  const u = Math.max(r(), 1e-9), v = r()
  return Math.sqrt(-2 * Math.log(u)) * Math.cos(2 * Math.PI * v)
}

// зерна дібрані так, щоб відтворити саме той сюжет, що на рисунку лекції:
// один прогін «виграє» B, за 5 і 24 зернами різниця лишається недоведеною
const runsA = computed(() => Array.from({ length: n.value }, (_, i) => TRUE_A + gauss(i, 2) * SIGMA))
const runsB = computed(() => Array.from({ length: n.value }, (_, i) => TRUE_B + gauss(i, 1) * SIGMA))

const mean = (a: number[]) => a.reduce((x, y) => x + y, 0) / a.length
const sd = (a: number[]) => {
  if (a.length < 2) return 0
  const m = mean(a)
  return Math.sqrt(a.reduce((s, v) => s + (v - m) ** 2, 0) / (a.length - 1))
}

const mA = computed(() => mean(runsA.value))
const mB = computed(() => mean(runsB.value))
const diff = computed(() => mA.value - mB.value)

/** 95 % довірчий інтервал різниці середніх (нормальне наближення). */
const se = computed(() => {
  if (n.value < 2) return Infinity
  return Math.sqrt(sd(runsA.value) ** 2 / n.value + sd(runsB.value) ** 2 / n.value)
})
const lo = computed(() => diff.value - 1.96 * se.value)
const hi = computed(() => diff.value + 1.96 * se.value)
const proven = computed(() => n.value >= 2 && lo.value > 0)
/** Чи перекриваються смуги ±σ — те, на що дивляться очима і помиляються. */
const bandsOverlap = computed(() =>
  n.value < 2 ? true : mA.value - sd(runsA.value) < mB.value + sd(runsB.value)
)

const W = 460, H = 130
const px = (v: number) => 40 + ((v - 0.2) / 0.8) * (W - 60)
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Скільки зерен, щоб порівняння щось доводило</div>
        <div class="lab__sub">
          Два алгоритми, справжня різниця +0,04 частки успіху. Ведіть повзунок
          і дивіться, коли висновок стає обґрунтованим.
        </div>
      </div>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Незалежних запусків <b>{{ n }}</b></span>
        <input v-model.number="n" type="range" min="1" max="60" step="1" />
      </label>
    </div>

    <svg class="sd__plot" :viewBox="`0 0 ${W} ${H}`" aria-label="Результати запусків двох алгоритмів">
      <text x="6" y="34" class="sd__lab">A</text>
      <text x="6" y="94" class="sd__lab">B</text>

      <line :x1="px(mA)" y1="16" :x2="px(mA)" y2="46" class="sd__mean" />
      <line :x1="px(mB)" y1="76" :x2="px(mB)" y2="106" class="sd__mean" />

      <circle v-for="(v, i) in runsA" :key="'a' + i" :cx="px(v)" cy="31" r="3" class="sd__dot is-a" />
      <circle v-for="(v, i) in runsB" :key="'b' + i" :cx="px(v)" cy="91" r="3" class="sd__dot is-b" />

      <text x="40" :y="H - 4" class="sd__tick">0,2</text>
      <text :x="W - 24" :y="H - 4" class="sd__tick">1,0</text>
      <text x="120" y="12" class="sd__tick">частка успішних епізодів</text>
    </svg>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ mA.toFixed(3) }}</b>
        <span>середнє A ({{ n }} запусків)</span>
      </div>
      <div class="lab__stat">
        <b>{{ mB.toFixed(3) }}</b>
        <span>середнє B</span>
      </div>
      <div class="lab__stat">
        <b>{{ diff >= 0 ? '+' : '' }}{{ diff.toFixed(3) }}</b>
        <span>різниця середніх</span>
      </div>
      <div class="lab__stat" :class="proven ? 'is-green' : 'is-warm'">
        <b>{{ n < 2 ? '—' : `[${lo.toFixed(2)}; ${hi.toFixed(2)}]` }}</b>
        <span>95 % інтервал різниці</span>
      </div>
      <div class="lab__stat" :class="proven ? 'is-green' : 'is-warm'">
        <b>{{ proven ? 'так' : 'ні' }}</b>
        <span>перевага A доведена</span>
      </div>
    </div>

    <p class="lab__note">
      На одному запуску «перемагає» B, хоча кращий за побудовою експерименту —
      A: висновок просто хибний. За п'ятьма і навіть за двадцятьма чотирма
      зернами середнє A піднімається вище, але різниця лишається недоведеною.
      Доведіть повзунок до кінця: інтервал різниці нарешті перестає містити
      нуль, а смуги розкиду <b v-if="bandsOverlap">усе одно перекриваються</b>.
      Саме тому перекриття смуг не є ані доказом, ані спростуванням —
      стверджувати можна лише за довірчим інтервалом різниці або тестом
      на парних різницях.
    </p>
  </div>
</template>

<style scoped>
.sd__plot { width: 100%; height: auto; background: var(--uk-fill); border-radius: 10px; }
.sd__lab {
  fill: var(--vp-c-text-2);
  font-size: 12px;
  font-weight: 600;
  font-family: var(--vp-font-family-mono);
}
.sd__tick { fill: var(--vp-c-text-3); font-size: 9px; font-family: var(--vp-font-family-mono); }
.sd__dot { opacity: 0.62; }
.sd__dot.is-a { fill: var(--uk-accent); }
.sd__dot.is-b { fill: var(--uk-warm); }
.sd__mean { stroke: var(--vp-c-text-1); stroke-width: 1.6; }
</style>
