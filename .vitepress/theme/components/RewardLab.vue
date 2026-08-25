<script setup lang="ts">
/**
 * Складена винагорода: внесок кожного доданка за епізод.
 *
 * Ваги й режими взяті з картки «Винагорода як зважена сума» модуля 06
 * і з розкладу на картці «Розподіл штрафів між доданками». Епізод — 8 с
 * при 50 Гц, тобто 400 кроків, dt = 0,02 с, як у наскрізному прикладі
 * з Crazyflie 2.1.
 */
import { ref, computed } from 'vue'

const STEPS = 400
const DT = 0.02

/** Типові значення величин за крок у двох режимах польоту. */
const REGIMES = [
  {
    id: 'hover', name: 'Стабільне висіння',
    dist: 0.09, omega: 0.35, tilt: 0.06, jerk: 0.12, crash: 0
  },
  {
    id: 'rough', name: 'Різкий політ до точки',
    dist: 0.42, omega: 1.30, tilt: 0.24, jerk: 0.55, crash: 0
  },
  {
    id: 'crash', name: 'Політ з аварією',
    dist: 0.55, omega: 2.10, tilt: 0.48, jerk: 0.80, crash: 1
  }
]

const pick = ref(0)
const regime = computed(() => REGIMES[pick.value])

// ваги доданків
const wDist = ref(1.0)
const wOmega = ref(0.1)
const wTilt = ref(0.5)
const wJerk = ref(0.05)
const wAlive = ref(0.5)
const crashPenalty = ref(-10)

const terms = computed(() => {
  const r = regime.value
  const n = r.crash ? Math.round(STEPS * 0.35) : STEPS // аварія обриває епізод
  return [
    { name: 'наближення до цілі', v: -wDist.value * r.dist * n * DT, hint: 'головний сигнал' },
    { name: 'кутова швидкість', v: -wOmega.value * r.omega * n * DT, hint: 'гасить рискання' },
    { name: 'нахил', v: -wTilt.value * r.tilt * n * DT, hint: 'тримає горизонт' },
    { name: 'різкість керування', v: -wJerk.value * r.jerk * n * DT, hint: 'бере до уваги мотори' },
    { name: 'бонус за життя', v: +wAlive.value * n * DT, hint: 'платить за кожну секунду' },
    { name: 'аварія', v: r.crash ? crashPenalty.value : 0, hint: 'разова подія' }
  ]
})

const total = computed(() => terms.value.reduce((a, t) => a + t.v, 0))
const span = computed(() => Math.max(...terms.value.map((t) => Math.abs(t.v)), 1))

/** Скільки віддачі втрачає агент, розбившись: різниця з повним епізодом. */
const lostByCrash = computed(() => {
  const alive = wAlive.value * STEPS * DT
  const aliveCut = wAlive.value * Math.round(STEPS * 0.35) * DT
  return alive - aliveCut
})
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Складена винагорода: хто скільки важить за епізод</div>
        <div class="lab__sub">
          Епізод 8 с при 50 Гц — 400 кроків. Стовпчик показує внесок доданка
          за весь епізод, а не за крок: саме так їх і порівнюють.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button
        v-for="(r, i) in REGIMES" :key="r.id"
        class="lab__pill" :class="{ 'is-on': pick === i }"
        @click="pick = i"
      >{{ r.name }}</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Відстань <b>{{ wDist.toFixed(2) }}</b></span>
        <input v-model.number="wDist" type="range" min="0" max="3" step="0.05" />
      </label>
      <label class="lab__ctl">
        <span>Кутова швидкість <b>{{ wOmega.toFixed(2) }}</b></span>
        <input v-model.number="wOmega" type="range" min="0" max="1" step="0.02" />
      </label>
      <label class="lab__ctl">
        <span>Нахил <b>{{ wTilt.toFixed(2) }}</b></span>
        <input v-model.number="wTilt" type="range" min="0" max="2" step="0.05" />
      </label>
      <label class="lab__ctl">
        <span>Бонус за життя <b>{{ wAlive.toFixed(2) }}</b></span>
        <input v-model.number="wAlive" type="range" min="0" max="2" step="0.05" />
      </label>
      <label class="lab__ctl">
        <span>Штраф за аварію <b>{{ crashPenalty }}</b></span>
        <input v-model.number="crashPenalty" type="range" min="-60" max="0" step="1" />
      </label>
    </div>

    <div class="rw__rows">
      <div v-for="t in terms" :key="t.name" class="rw__row">
        <span class="rw__name">{{ t.name }}</span>
        <div class="rw__track">
          <div
            class="rw__bar" :class="t.v >= 0 ? 'is-pos' : 'is-neg'"
            :style="{
              width: (Math.abs(t.v) / span) * 50 + '%',
              left: t.v >= 0 ? '50%' : 'auto',
              right: t.v < 0 ? '50%' : 'auto'
            }"
          />
          <div class="rw__zero" />
        </div>
        <span class="rw__val" :class="t.v >= 0 ? 'is-pos' : 'is-neg'">
          {{ t.v >= 0 ? '+' : '' }}{{ t.v.toFixed(2) }}
        </span>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat" :class="total >= 0 ? 'is-green' : 'is-warm'">
        <b>{{ total >= 0 ? '+' : '' }}{{ total.toFixed(2) }}</b>
        <span>віддача за епізод</span>
      </div>
      <div class="lab__stat">
        <b>{{ lostByCrash.toFixed(2) }}</b>
        <span>втрачений бонус за життя при аварії</span>
      </div>
      <div class="lab__stat" :class="{ 'is-warm': Math.abs(crashPenalty) < lostByCrash }">
        <b>{{ Math.abs(crashPenalty) < lostByCrash ? 'замало' : 'достатньо' }}</b>
        <span>чи стримує штраф за аварію</span>
      </div>
    </div>

    <p class="lab__note">
      Виберіть «Політ з аварією» і зменшуйте штраф за модулем. Коли він стає
      меншим за втрачений бонус за життя, розбитися вигідніше, ніж летіти:
      агент навчиться падати одразу. Це не помилка алгоритму, а помилка
      постановки — і знаходять її саме таким розкладом, а не за сумарною кривою.
    </p>
  </div>
</template>

<style scoped>
.rw__rows { display: flex; flex-direction: column; gap: 0.4rem; margin: 0.9rem 0 0.2rem; }
.rw__row { display: grid; grid-template-columns: 11rem 1fr 4.4rem; align-items: center; gap: 0.6rem; }
@media (max-width: 640px) {
  .rw__row { grid-template-columns: 8rem 1fr 3.6rem; }
}
.rw__name { font-size: 0.8rem; color: var(--vp-c-text-2); }
.rw__track { position: relative; height: 1.15rem; background: var(--uk-fill); border-radius: 4px; }
.rw__bar { position: absolute; top: 0; bottom: 0; border-radius: 3px; transition: width 0.12s ease; }
.rw__bar.is-pos { background: var(--uk-green); }
.rw__bar.is-neg { background: var(--uk-warm); }
.rw__zero { position: absolute; left: 50%; top: -1px; bottom: -1px; width: 1px; background: var(--vp-c-divider); }
.rw__val {
  font-family: var(--vp-font-family-mono);
  font-size: 0.78rem;
  text-align: right;
  font-variant-numeric: tabular-nums;
}
.rw__val.is-pos { color: var(--uk-green); }
.rw__val.is-neg { color: var(--uk-warm); }
</style>
