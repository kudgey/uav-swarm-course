<script setup lang="ts">
/**
 * Цикл DQN крок за кроком на справжніх числах.
 *
 * Модуль 05, картка «Ціль і втрата на числах». Дані записав скрипт
 * gamma_course/viz/m05_dqn_record.py — це той самий прогін DQN, що в блоці коду
 * лекції (зерно 0, крива звірена), кроки 4 998…5 003. Віджет нічого не рахує
 * заново, лише показує записані величини по етапах одного кроку навчання.
 */
import { ref, computed } from 'vue'
import data from '../data/dqnloop.json'

type Row = { idx: number; s: number[]; a: number; r: number; s2: number[]; done: boolean; best_next: number; y: number; q: number; q_after: number }
type Step = {
  t: number; obs: number[]; eps: number; u: number; q_obs: number[]; greedy: number; a: number; random: boolean
  r: number; obs2: number[]; crashed: boolean; timeout: boolean; buffer: number; batch: Row[]; loss: number
  loss_show: number; synced: boolean; q_ref: number[]; qt_ref: number[]
}
const STEPS = data.steps as Step[]
const G = data.meta.gamma
const SYNC = data.meta.sync
const BATCH = data.meta.batch
const ANAME = ['менше тяги', 'висіти', 'більше тяги']
const STAGES = ['1 · дія', '2 · у буфер', '3 · міні-пакет', '4 · ціль y', '5 · втрата й крок θ', '6 · копіювання в target']

const si = ref(STEPS.findIndex((s) => s.synced)) // крок, на якому копіюють θ̄
const stage = ref(0)
const st = computed(() => STEPS[si.value])
const prevQt = computed(() => (si.value > 0 ? STEPS[si.value - 1].qt_ref : st.value.qt_ref))

function next() {
  if (stage.value < STAGES.length - 1) stage.value++
  else if (si.value < STEPS.length - 1) { si.value++; stage.value = 0 }
}
function prev() {
  if (stage.value > 0) stage.value--
  else if (si.value > 0) { si.value--; stage.value = STAGES.length - 1 }
}
const f = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const sv = (s: number[]) => `(${f(s[0], 2)}; ${f(s[1], 2)})`
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">Один крок навчання DQN: що відбувається всередині</div>
        <div class="lab__sub">
          Записані величини справжнього прогону лекції (зерно 0), кроки {{ STEPS[0].t }}–{{ STEPS[STEPS.length - 1].t }}.
          Міні-пакет має {{ BATCH }} переходи, показано перші 4. Копіювання <span class="tb">θ̄</span> ← θ — кожні {{ SYNC }} кроків.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="(s, i) in STEPS" :key="s.t" type="button" class="lab__pill" :class="{ 'is-on': si === i }"
              @click="si = i; stage = 0">крок {{ s.t }}<template v-if="s.synced"> · <span class="tb">θ̄</span> ← θ</template></button>
    </div>
    <div class="dl__stages">
      <button v-for="(name, i) in STAGES" :key="name" type="button" class="dl__stage"
              :class="{ on: stage === i, done: stage > i }" @click="stage = i">{{ name }}</button>
    </div>

    <div class="dl__panel">
      <template v-if="stage === 0">
        <p>Стан <b>s = {{ sv(st.obs) }}</b>: похибка висоти, м, і вертикальна швидкість, м/с.</p>
        <p>Основна мережа θ видає три оцінки:
          <span v-for="(q, i) in st.q_obs" :key="i" class="dl__q" :class="{ best: i === st.greedy }">
            Q(s, {{ ANAME[i] }}) = {{ f(q) }}</span>
        </p>
        <p>ε = {{ f(st.eps, 4) }}; випадкове число {{ f(st.u, 4) }}
          {{ st.random ? '< ε — дія випадкова' : '≥ ε — беремо дію з найбільшою оцінкою' }}:
          <b>a = «{{ ANAME[st.a] }}»</b>.</p>
      </template>
      <template v-else-if="stage === 1">
        <p>Середовище повертає винагороду <b>r = {{ f(st.r, 4) }}</b> і новий стан
          <b>s′ = {{ sv(st.obs2) }}</b>{{ st.crashed ? ' — аварія' : st.timeout ? ' — кінець епізоду за часом' : '' }}.</p>
        <p>Перехід (s, a, r, s′, кінець = {{ st.crashed ? 'так' : 'ні' }}) додано в кінець буфера:
          тепер у ньому <b>{{ st.buffer.toLocaleString('uk-UA') }}</b> переходів. Навчатися на ньому одразу ніхто не буде.</p>
      </template>
      <template v-else-if="stage === 2">
        <p>З усього буфера беремо {{ BATCH }} випадкові номери. Сусідні кроки одного польоту майже однакові,
          а випадкові — з різних польотів і різних етапів навчання.</p>
        <div class="dl__tab"><table>
          <thead><tr><th>№ у буфері</th><th>s</th><th>a</th><th>r</th><th>s′</th><th>кінець</th></tr></thead>
          <tbody><tr v-for="b in st.batch" :key="b.idx"><td>{{ b.idx }}</td><td>{{ sv(b.s) }}</td>
            <td>{{ ANAME[b.a] }}</td><td>{{ f(b.r, 4) }}</td><td>{{ sv(b.s2) }}</td><td>{{ b.done ? 'так' : 'ні' }}</td></tr></tbody>
        </table></div>
      </template>
      <template v-else-if="stage === 3">
        <p>Ціль рахує <b>target network <span class="tb">θ̄</span></b>: y = r + γ · max Q(s′, ·; <span class="tb">θ̄</span>), γ = {{ f(G, 2) }}; після аварії y = r.</p>
        <div class="dl__tab"><table>
          <thead><tr><th>r</th><th>max Q(s′; <span class="tb">θ̄</span>)</th><th>y</th></tr></thead>
          <tbody><tr v-for="b in st.batch" :key="b.idx">
            <td>{{ f(b.r, 4) }}</td><td>{{ b.done ? '— (кінець)' : f(b.best_next) }}</td>
            <td>{{ b.done ? f(b.y) : `${f(b.r, 4)} + ${f(G, 2)} · ${b.best_next < 0 ? '(' + f(b.best_next) + ')' : f(b.best_next)} = ${f(b.y)}` }}</td></tr></tbody>
        </table></div>
      </template>
      <template v-else-if="stage === 4">
        <p>Основна мережа θ оцінює ті самі пари Q(s, a; θ). Втрата — середній квадрат різниці з ціллю,
          і крок градієнта зсуває лише θ.</p>
        <div class="dl__tab"><table>
          <thead><tr><th>y</th><th>Q(s, a; θ)</th><th>(y − Q)²</th><th>Q після кроку</th></tr></thead>
          <tbody><tr v-for="b in st.batch" :key="b.idx"><td>{{ f(b.y) }}</td><td>{{ f(b.q) }}</td>
            <td>{{ f((b.y - b.q) ** 2, 5) }}</td><td>{{ f(b.q_after) }}</td></tr></tbody>
        </table></div>
        <p>Втрата на всіх {{ BATCH }} переходах <b>L = {{ f(st.loss, 5) }}</b>; на чотирьох показаних — {{ f(st.loss_show, 5) }}.</p>
      </template>
      <template v-else>
        <p v-if="st.synced"><b>Крок {{ st.t }} ділиться на {{ SYNC }}</b>: ваги основної мережі копіюють у target network.
          Від цього кроку всі цілі рахуються вже новою <span class="tb">θ̄</span>.</p>
        <p v-else>Крок {{ st.t }} не ділиться на {{ SYNC }}: target network не змінюється, цілі наступного кроку
          рахуватимуться тією самою <span class="tb">θ̄</span>.</p>
        <p>Оцінки для контрольного стану s = (−0,13; −0,12):</p>
        <div class="dl__tab"><table>
          <thead><tr><th></th><th v-for="n in ANAME" :key="n">{{ n }}</th></tr></thead>
          <tbody>
            <tr><td>θ — основна</td><td v-for="(q, i) in st.q_ref" :key="i">{{ f(q) }}</td></tr>
            <tr><td><span class="tb">θ̄</span> до кроку</td><td v-for="(q, i) in prevQt" :key="i">{{ f(q) }}</td></tr>
            <tr><td><span class="tb">θ̄</span> після кроку</td><td v-for="(q, i) in st.qt_ref" :key="i" :class="{ dl__chg: st.synced }">{{ f(q) }}</td></tr>
          </tbody>
        </table></div>
      </template>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" type="button" :disabled="si === 0 && stage === 0" @click="prev">← назад</button>
      <button class="lab__pill is-on" type="button" :disabled="si === STEPS.length - 1 && stage === STAGES.length - 1" @click="next">далі →</button>
    </div>
  </div>
</template>

<style scoped>
.dl__stages { display: flex; flex-wrap: wrap; gap: 0.3rem; margin: 0.5rem 0; }
.dl__stage {
  font: inherit; font-size: 0.78rem; padding: 0.2rem 0.6rem; border-radius: 6px; cursor: pointer;
  border: 1px solid var(--uk-line); background: transparent; color: var(--vp-c-text-2);
}
.dl__stage.done { color: var(--vp-c-text-1); background: var(--uk-fill); }
.dl__stage.on { border-color: var(--uk-accent); color: var(--uk-accent); font-weight: 600; }
.dl__stage:focus-visible { outline: 2px solid var(--uk-accent); outline-offset: 2px; }
.dl__panel { background: var(--uk-fill); border-radius: 10px; padding: 0.7rem 0.9rem; margin: 0.3rem 0 0.6rem; display: grid; gap: 0.5rem; }
.dl__panel p { margin: 0; font-size: 0.9rem; line-height: 1.55; }
.dl__q { display: inline-block; font-family: var(--vp-font-family-mono); font-size: 0.8rem; margin: 0.1rem 0.5rem 0.1rem 0; }
.dl__q.best { color: var(--uk-green); font-weight: 700; }
.dl__tab { overflow-x: auto; }
.dl__tab td { font-family: var(--vp-font-family-mono); font-size: 0.78rem; white-space: nowrap; }
.tb { font-family: var(--vp-font-family-mono); }
.dl__chg { color: var(--uk-green); font-weight: 700; }
</style>
