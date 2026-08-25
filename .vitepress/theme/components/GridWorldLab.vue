<script setup lang="ts">
/**
 * Q-навчання на сітці: цінність поширюється від цілі назад.
 *
 * Та сама задача, що в картці «Код: Q-learning на сітці» модуля 04 і в її
 * результаті: сітка 5×5, ціль у правому нижньому куті, γ = 0,95, α = 0,5,
 * ε-жадібний вибір. Кнопки прокручують епізоди, і видно те саме, що на
 * рисунку лекції: після 2 епізодів цінність є лише біля цілі, після 400 —
 * по всій сітці.
 */
import { ref, computed } from 'vue'

const N = 5
const GOAL = 24 // правий нижній кут
const GAMMA = 0.95
const ALPHA = 0.5
const A = [-N, +N, -1, +1] // вгору, вниз, ліворуч, праворуч

const eps = ref(0.2)
const episodes = ref(0)
const Q = ref<number[][]>(Array.from({ length: N * N }, () => [0, 0, 0, 0]))

/** Детермінований генератор — картинка та сама при кожному відкритті. */
let seed = 12345
function rnd() {
  seed = (seed * 1103515245 + 12345) & 0x7fffffff
  return seed / 0x7fffffff
}

function stepFrom(s: number, a: number) {
  const r = Math.floor(s / N), c = s % N
  if (a === 0 && r === 0) return s
  if (a === 1 && r === N - 1) return s
  if (a === 2 && c === 0) return s
  if (a === 3 && c === N - 1) return s
  return s + A[a]
}

function runEpisodes(k: number) {
  const q = Q.value.map((row) => [...row])
  for (let e = 0; e < k; e++) {
    let s = 0
    for (let t = 0; t < 120; t++) {
      const a = rnd() < eps.value ? Math.floor(rnd() * 4) : q[s].indexOf(Math.max(...q[s]))
      const s2 = stepFrom(s, a)
      const rew = s2 === GOAL ? 1 : -0.01
      const best = s2 === GOAL ? 0 : Math.max(...q[s2])
      q[s][a] += ALPHA * (rew + GAMMA * best - q[s][a])
      s = s2
      if (s === GOAL) break
    }
  }
  Q.value = q
  episodes.value += k
}

function reset() {
  seed = 12345
  Q.value = Array.from({ length: N * N }, () => [0, 0, 0, 0])
  episodes.value = 0
}

const values = computed(() => Q.value.map((row) => Math.max(...row)))
const vmax = computed(() => Math.max(...values.value, 0.001))
/** Частка клітинок, де цінність уже ненульова — «фронт» поширення. */
const filled = computed(() => values.value.filter((v) => v > 0.01).length)
const ARROW = ['↑', '↓', '←', '→']
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Q-навчання: як цінність доходить до старту</div>
        <div class="lab__sub">
          Сітка 5×5, старт у лівому верхньому куті, ціль у правому нижньому.
          γ = 0,95, α = 0,5 — ті самі числа, що в коді лекції.
        </div>
      </div>
      <button class="lab__btn" @click="reset">Спочатку</button>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" @click="runEpisodes(1)">+1 епізод</button>
      <button class="lab__pill" @click="runEpisodes(10)">+10</button>
      <button class="lab__pill" @click="runEpisodes(100)">+100</button>
    </div>

    <div class="lab__controls">
      <label class="lab__ctl">
        <span>Дослідження ε <b>{{ eps.toFixed(2) }}</b></span>
        <input v-model.number="eps" type="range" min="0" max="1" step="0.05" />
      </label>
    </div>

    <div class="gw__grid">
      <div
        v-for="(v, s) in values" :key="s"
        class="gw__cell"
        :class="{ 'is-goal': s === GOAL, 'is-start': s === 0 }"
        :style="{ '--w': Math.max(0, v / vmax) }"
      >
        <span class="gw__v">{{ v > 0.005 ? v.toFixed(2) : '—' }}</span>
        <span v-if="v > 0.005 && s !== GOAL" class="gw__a">
          {{ ARROW[Q[s].indexOf(Math.max(...Q[s]))] }}
        </span>
      </div>
    </div>

    <div class="lab__stats">
      <div class="lab__stat">
        <b>{{ episodes }}</b>
        <span>епізодів навчання</span>
      </div>
      <div class="lab__stat">
        <b>{{ filled }} / 25</b>
        <span>клітинок із ненульовою цінністю</span>
      </div>
      <div class="lab__stat">
        <b>{{ values[0] > 0.005 ? values[0].toFixed(3) : '—' }}</b>
        <span>цінність стартової клітинки</span>
      </div>
      <div class="lab__stat">
        <b>{{ Math.pow(GAMMA, 8).toFixed(3) }}</b>
        <span>межа: γ⁸ за 8 кроків до цілі</span>
      </div>
    </div>

    <p class="lab__note">
      Натисніть «+1 епізод» кілька разів: цінність з'являється спершу лише в
      клітинках біля цілі й лише потім доповзає до старту. Це прямий наслідок
      того, що Q-навчання оновлює одну пару «стан — дія» за крок. Поставте ε = 0
      і перезапустіть: агент піде першим знайденим шляхом і більшу частину сітки
      не побачить узагалі — саме той компроміс дослідження проти використання,
      про який ішлося на початку модуля.
    </p>
  </div>
</template>

<style scoped>
.gw__grid {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 3px;
  max-width: 22rem;
  margin: 0.9rem 0 0.2rem;
}
.gw__cell {
  aspect-ratio: 1;
  border-radius: 6px;
  border: 1px solid var(--uk-line);
  background: color-mix(in srgb, var(--uk-accent) calc(var(--w) * 70%), var(--uk-fill));
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 0.05rem;
}
.gw__cell.is-goal { border-color: var(--uk-green); border-width: 2px; }
.gw__cell.is-start { border-color: var(--uk-warm); border-width: 2px; }
.gw__v {
  font-family: var(--vp-font-family-mono);
  font-size: 0.68rem;
  color: var(--vp-c-text-1);
  font-variant-numeric: tabular-nums;
}
.gw__a { font-size: 0.82rem; line-height: 1; color: var(--vp-c-text-2); }
</style>
