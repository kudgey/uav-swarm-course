<script setup lang="ts">
/**
 * Одне справжнє оновлення REINFORCE, A2C або PPO по етапах — з мережею на екрані.
 *
 * Модуль 05, картки «Алгоритм REINFORCE / A2C / PPO по кроках». Дані записали скрипти
 * gamma_course/viz/m05_pg_record.py (REINFORCE, A2C → data/pgsteps.json) і
 * m05_flight_record.py (PPO → data/ppostep.json). Вони повторюють прогони лекції
 * (зерно 0) і звіряють криві, тож шари мережі, ймовірності, віддачі й переваги тут —
 * ті самі, що в навчанні. Віджет нічого не навчає сам: формули на панелі лише
 * підставляють записані числа.
 */
import { ref, computed } from 'vue'
import pg from '../data/pgsteps.json'
import ppoData from '../data/ppostep.json'

const props = defineProps<{ algo: 'reinforce' | 'a2c' | 'ppo' }>()
const ANAME = ['менше тяги', 'висіти', 'більше тяги']
const SHORT = ['менше', 'висіти', 'більше']
const ACT: number[] = pg.actions
const R: any = pg.reinforce
const A: any = pg.a2c
const P: any = ppoData

const STAGES = {
  reinforce: ['1 · стан → мережа', '2 · softmax і жереб', '3 · віддача G', '4 · втрата', '5 · крок градієнта'],
  a2c: ['1 · актор', '2 · критик', '3 · перевага', '4 · втрата', '5 · крок градієнта'],
  ppo: ['1 · актор: μ і σ', '2 · жереб дії', '3 · критик і перевага', '4 · 10 епох: ρ', '5 · обрізання'],
}[props.algo]

const samples = computed(() => {
  if (props.algo === 'reinforce') return Object.keys(R.show).map((k) => ({ key: Number(k), label: `крок ${k} епізоду` }))
  if (props.algo === 'a2c') return A.rows.map((_: any, i: number) => ({ key: i, label: `перехід ${i + 1} з 5` }))
  return P.rows.map((r: any, i: number) => ({ key: i, label: r.adv > 0 ? `перехід ${i + 1}: перевага +` : `перехід ${i + 1}: перевага −` }))
})
const k = ref(samples.value[0].key)
const stage = ref(0)
function next() {
  if (stage.value < STAGES.length - 1) stage.value++
}
function prev() {
  if (stage.value > 0) stage.value--
}

// ---- форматування ----
const f = (v: number, d = 3) => v.toFixed(d).replace('.', ',').replace('-', '−')
const fs = (v: number, d = 3) => (v >= 0 ? '+' : '') + f(v, d)
const par = (v: number, d = 3) => (v < 0 ? `(${f(v, d)})` : f(v, d))
const vec = (v: number[], d = 3) => `(${v.map((x) => f(x, d)).join('; ')})`
const onCount = (h: number[]) => h.filter((x) => x > 0).length

// ---- REINFORCE ----
const rT = computed(() => R.a.length)
const r = computed(() => {
  const t = k.value
  const show = R.show[String(t)]
  const pb: number[] = R.pi_before[t]
  const pa: number[] = R.pi_after[t]
  const a: number = R.a[t]
  const ez = show.z.map((z: number) => Math.exp(z))
  const sum = ez.reduce((x: number, y: number) => x + y, 0)
  const G: number = R.G[t]
  const push = pb.map((p, i) => (G / rT.value) * ((i === a ? 1 : 0) - p))
  return { t, s: R.s[t], h1: show.h1, h2: show.h2, z: show.z, ez, sum, pb, pa, a, G, r: R.r[t],
           Gn: t + 1 < rT.value ? R.G[t + 1] : null, logp: R.logp[t], push,
           agree: Math.sign(pa[a] - pb[a]) === Math.sign(G) }
})

// ---- A2C ----
const a2 = computed(() => {
  const row = A.rows[k.value]
  const ent = -row.p.reduce((s: number, p: number) => s + p * Math.log(p), 0)
  return { ...row, ent, actorTerm: -row.adv * row.logp, criticTerm: 0.5 * (row.y - row.v) ** 2,
           agree: Math.sign(row.p_after[row.a] - row.p[row.a]) === Math.sign(row.adv) }
})

// ---- PPO: усе в одиницях тяги u = (a + 1) / 2 ----
const SQ2PI = Math.sqrt(2 * Math.PI)
const gauss = (u: number, m: number, s: number) => Math.exp(-((u - m) ** 2) / (2 * s * s)) / (s * SQ2PI)
const pp = computed(() => {
  const row = P.rows[k.value]
  const m = P.meta
  const mu0 = (row.mu0 + 1) / 2, mu1 = (row.mu1 + 1) / 2
  const s0 = m.sigma0 / 2, s1 = m.sigma1 / 2
  const u = (row.a + 1) / 2
  const d0 = gauss(u, mu0, s0), d1 = gauss(u, mu1, s1)
  const rho = row.rho
  const eps = m.eps
  const clip = Math.min(1 + eps, Math.max(1 - eps, rho))
  const o1 = rho * row.adv, o2 = clip * row.adv
  return { ...row, mu0, mu1, s0, s1, u, d0, d1, rho, clip, o1, o2, obj: Math.min(o1, o2),
           clipped: o2 < o1 - 1e-12, inside: rho >= 1 - eps && rho <= 1 + eps }
})

// ---- спільна картинка мережі ----
const lanes = computed(() => {
  if (props.algo === 'reinforce') return { actor: { s: r.value.s, h1: r.value.h1, h2: r.value.h2 }, critic: null }
  if (props.algo === 'a2c') return { actor: { s: a2.value.s, h1: a2.value.h1, h2: a2.value.h2 },
                                     critic: { s: a2.value.s, h1: a2.value.c1, h2: a2.value.c2 } }
  return { actor: { s: pp.value.obs, h1: pp.value.h1, h2: pp.value.h2 },
           critic: { s: pp.value.obs, h1: pp.value.c1, h2: pp.value.c2 } }
})
const tanh = props.algo === 'ppo'
/** На якому етапі вмикається блок схеми. */
const ON: Record<string, number> = {
  reinforce: { in: 0, h: 0, out: 0, dist: 1, cin: 9, ch: 9, cout: 9, sig: 2, loss: 3, upd: 4 },
  a2c: { in: 0, h: 0, out: 0, dist: 0, cin: 1, ch: 1, cout: 1, sig: 2, loss: 3, upd: 4 },
  ppo: { in: 0, h: 0, out: 0, dist: 1, cin: 2, ch: 2, cout: 2, sig: 2, loss: 4, upd: 3 },
}[props.algo] as any
const cls = (key: string) => ({ on: ON[key] === stage.value, seen: ON[key] <= stage.value })

function cell(v: number) {
  const m = Math.min(1, Math.abs(v) / (tanh ? 1 : 1.5))
  const col = v >= 0 ? 'var(--uk-accent)' : 'var(--uk-warm)'
  return { background: `color-mix(in srgb, ${col} ${Math.round(m * 100)}%, var(--uk-fill))` }
}
const hover = ref('')
const hov = (layer: string, i: number, v: number) => { hover.value = `${layer}, нейрон ${i + 1}: ${f(v)}` }

// ---- малий графік епізоду REINFORCE: винагороди й віддачі ----
const EW = 300, EH = 92, EX0 = 30, EPW = EW - EX0 - 6, EY0 = 6, EPH = EH - EY0 - 16
const eMin = Math.min(...R.G, ...R.r), eMax = Math.max(0.5, ...R.G, ...R.r)
const ex = (t: number) => EX0 + (t / (R.a.length - 1)) * EPW
const ey = (v: number) => EY0 + (1 - (v - eMin) / (eMax - eMin)) * EPH
const eLine = (arr: number[]) => arr.map((v, t) => `${t ? 'L' : 'M'}${ex(t).toFixed(1)},${ey(v).toFixed(1)}`).join(' ')

// ---- малий графік гауссіана PPO ----
const GW = 220, GH = 92, GX0 = 6, GPW = GW - 12, GY0 = 6, GPH = GH - GY0 - 14
const gRange = computed(() => {
  const p = pp.value
  const lo = Math.min(p.mu0, p.mu1, p.u) - 3.2 * p.s0
  const hi = Math.max(p.mu0, p.mu1, p.u) + 3.2 * p.s0
  return [lo, hi]
})
const gMax = computed(() => Math.max(gauss(pp.value.mu1, pp.value.mu1, pp.value.s1), gauss(pp.value.mu0, pp.value.mu0, pp.value.s0)) * 1.1)
const gx = (u: number) => GX0 + ((u - gRange.value[0]) / (gRange.value[1] - gRange.value[0])) * GPW
const gy = (d: number) => GY0 + (1 - d / gMax.value) * GPH
function gPath(m: number, s: number) {
  const [lo, hi] = gRange.value
  let d = ''
  for (let i = 0; i <= 120; i++) {
    const u = lo + ((hi - lo) * i) / 120
    d += `${i ? 'L' : 'M'}${gx(u).toFixed(1)},${gy(gauss(u, m, s)).toFixed(1)} `
  }
  return d
}
const steps = (n: number) => n.toLocaleString('uk-UA')
</script>

<template>
  <div class="lab">
    <div class="lab__head">
      <div>
        <div class="lab__title">
          {{ algo === 'reinforce' ? 'REINFORCE зсередини: перше оновлення' : algo === 'a2c' ? 'A2C зсередини: одне оновлення на 40 тис. кроків' : 'PPO зсередини: одне оновлення на ' + steps(P.meta.steps) + ' кроків' }}
        </div>
        <div class="lab__sub">
          <template v-if="algo === 'reinforce'">Справжній прогін лекції, зерно 0: перший епізод навчання ({{ rT }} кроків, аварія) і крок градієнта після нього.</template>
          <template v-else-if="algo === 'a2c'">Справжній прогін лекції, зерно 0: те саме оновлення з п'яти переходів, що друкує код вище.</template>
          <template v-else>Справжній прогін лекції, зерно 0, старт біля цілі: три переходи з порції {{ steps(P.meta.n) }} кроків.</template>
          Комірки — нейрони, колір — значення; наведіть або торкніться, щоб прочитати число.
        </div>
      </div>
    </div>

    <div class="lab__pills">
      <button v-for="x in samples" :key="x.key" type="button" class="lab__pill" :class="{ 'is-on': k === x.key }"
              @click="k = x.key">{{ x.label }}</button>
    </div>
    <div class="ps__stages">
      <button v-for="(name, i) in STAGES" :key="name" type="button" class="ps__stage"
              :class="{ on: stage === i, done: stage > i }" @click="stage = i">{{ name }}</button>
    </div>

    <!-- схема мережі -->
    <div class="ps__flow">
      <div class="ps__lane">
        <div class="ps__lname">{{ algo === 'reinforce' ? 'політика φ' : 'актор φ' }}</div>
        <div class="ps__row">
          <div class="ps__blk" :class="cls('in')">
            <div class="ps__bt">стан s</div>
            <div class="ps__in"><span>z − 1</span><b>{{ f(lanes.actor.s[0], 2) }}</b><span>v<sub>z</sub></span><b>{{ f(lanes.actor.s[1], 2) }}</b></div>
          </div>
          <div class="ps__arr">→</div>
          <div class="ps__blk" :class="cls('h')">
            <div class="ps__bt">шар 1 · 64</div>
            <div class="ps__grid"><i v-for="(v, i) in lanes.actor.h1" :key="i" :style="cell(v)" @pointerenter="hov('актор, шар 1', i, v)" @pointerdown="hov('актор, шар 1', i, v)"></i></div>
          </div>
          <div class="ps__arr">→</div>
          <div class="ps__blk" :class="cls('h')">
            <div class="ps__bt">шар 2 · 64</div>
            <div class="ps__grid"><i v-for="(v, i) in lanes.actor.h2" :key="i" :style="cell(v)" @pointerenter="hov('актор, шар 2', i, v)" @pointerdown="hov('актор, шар 2', i, v)"></i></div>
          </div>
          <div class="ps__arr">→</div>
          <div class="ps__blk" :class="cls('out')">
            <template v-if="algo !== 'ppo'">
              <div class="ps__bt">логіти z</div>
              <div class="ps__nums"><div v-for="(z, i) in (algo === 'reinforce' ? r.z : a2.z)" :key="i"><span>{{ SHORT[i] }}</span><b>{{ f(z) }}</b></div></div>
            </template>
            <template v-else>
              <div class="ps__bt">вихід</div>
              <div class="ps__nums"><div><span>μ<sub>u</sub></span><b>{{ f(pp.mu0) }}</b></div><div><span>σ<sub>u</sub></span><b>{{ f(pp.s0) }}</b></div></div>
            </template>
          </div>
          <div class="ps__arr">→</div>
          <div class="ps__blk" :class="cls('dist')">
            <template v-if="algo !== 'ppo'">
              <div class="ps__bt">π = softmax(z)</div>
              <div class="ps__bars">
                <div v-for="(p, i) in (algo === 'reinforce' ? r.pb : a2.p)" :key="i" class="ps__b" :class="{ pick: i === (algo === 'reinforce' ? r.a : a2.a) && stage >= ON.dist }">
                  <i :style="{ height: Math.max(2, p * 54) + 'px' }"></i><span>{{ f(p, 2) }}</span>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="ps__bt">гауссіан тяги u</div>
              <svg :viewBox="`0 0 ${GW} ${GH}`" class="ps__g">
                <path :d="gPath(pp.mu0, pp.s0)" class="ps__g0" :class="{ dash: stage >= 3 }" />
                <path v-if="stage >= 3" :d="gPath(pp.mu1, pp.s1)" class="ps__g1" />
                <line v-if="stage >= 1" :x1="gx(pp.u)" :x2="gx(pp.u)" :y1="GY0" :y2="gy(0)" class="ps__gu" />
                <circle v-if="stage >= 1" :cx="gx(pp.u)" :cy="gy(pp.d0)" r="3" class="ps__gd0" />
                <circle v-if="stage >= 3" :cx="gx(pp.u)" :cy="gy(pp.d1)" r="3" class="ps__gd1" />
                <text :x="gx(pp.u)" :y="GH - 2" text-anchor="middle" class="ps__gt" v-if="stage >= 1">u = {{ f(pp.u) }}</text>
              </svg>
            </template>
          </div>
        </div>
      </div>

      <div v-if="lanes.critic" class="ps__lane">
        <div class="ps__lname">критик θ</div>
        <div class="ps__row">
          <div class="ps__blk" :class="cls('cin')">
            <div class="ps__bt">стан s</div>
            <div class="ps__in"><span>z − 1</span><b>{{ f(lanes.critic.s[0], 2) }}</b><span>v<sub>z</sub></span><b>{{ f(lanes.critic.s[1], 2) }}</b></div>
          </div>
          <div class="ps__arr">→</div>
          <div class="ps__blk" :class="cls('ch')">
            <div class="ps__bt">шар 1 · 64</div>
            <div class="ps__grid"><i v-for="(v, i) in lanes.critic.h1" :key="i" :style="cell(v)" @pointerenter="hov('критик, шар 1', i, v)" @pointerdown="hov('критик, шар 1', i, v)"></i></div>
          </div>
          <div class="ps__arr">→</div>
          <div class="ps__blk" :class="cls('ch')">
            <div class="ps__bt">шар 2 · 64</div>
            <div class="ps__grid"><i v-for="(v, i) in lanes.critic.h2" :key="i" :style="cell(v)" @pointerenter="hov('критик, шар 2', i, v)" @pointerdown="hov('критик, шар 2', i, v)"></i></div>
          </div>
          <div class="ps__arr">→</div>
          <div class="ps__blk" :class="cls('cout')">
            <div class="ps__bt">цінність</div>
            <div class="ps__nums"><div><span>V(s)</span><b>{{ f(algo === 'a2c' ? a2.v : pp.v) }}</b></div><div><span>V(s′)</span><b>{{ f(algo === 'a2c' ? a2.v_next : pp.v_next) }}</b></div></div>
          </div>
        </div>
      </div>

      <div class="ps__row ps__tail">
        <div class="ps__blk" :class="cls('sig')" style="order: 1">
          <div class="ps__bt">{{ algo === 'reinforce' ? 'віддача G' : 'перевага Adv' }}</div>
          <svg v-if="algo === 'reinforce'" :viewBox="`0 0 ${EW} ${EH}`" class="ps__ep">
            <line :x1="EX0" :x2="EX0 + EPW" :y1="ey(0)" :y2="ey(0)" class="ps__zero" />
            <path :d="eLine(R.r)" class="ps__er" />
            <path :d="eLine(R.G)" class="ps__eg" />
            <line :x1="ex(r.t)" :x2="ex(r.t)" :y1="EY0" :y2="EY0 + EPH" class="ps__gu" />
            <circle :cx="ex(r.t)" :cy="ey(r.G)" r="3" class="ps__gd0" />
            <text :x="EX0 - 3" :y="ey(0) + 3" text-anchor="end" class="ps__gt">0</text>
            <text :x="EX0 - 3" :y="ey(eMin) + 3" text-anchor="end" class="ps__gt">{{ Math.round(eMin) }}</text>
            <text :x="EX0" :y="EH - 2" class="ps__gt">G — суцільна, r — пунктир</text>
            <text :x="EX0 + EPW" :y="EH - 2" text-anchor="end" class="ps__gt">{{ f(rT * 0.02, 2) }} с</text>
          </svg>
          <div v-else class="ps__big">{{ fs(algo === 'a2c' ? a2.adv : pp.adv) }}</div>
        </div>
        <div class="ps__arr" :style="{ order: algo === 'ppo' ? 4 : 2 }">→</div>
        <div class="ps__blk" :class="cls('loss')" :style="{ order: algo === 'ppo' ? 5 : 3 }">
          <div class="ps__bt">{{ algo === 'ppo' ? 'ціль з обрізанням' : 'втрата L' }}</div>
          <div class="ps__big">{{ algo === 'reinforce' ? f(R.loss) : algo === 'a2c' ? f(A.loss, 5) : fs(pp.obj) }}</div>
        </div>
        <div class="ps__arr" :style="{ order: algo === 'ppo' ? 2 : 4 }">→</div>
        <div class="ps__blk" :class="cls('upd')" :style="{ order: algo === 'ppo' ? 3 : 5 }">
          <div class="ps__bt" v-if="algo === 'ppo'">ρ = π / π<sub>β</sub></div>
          <div class="ps__bt" v-else>π(дія) до → після</div>
          <div class="ps__big" v-if="algo === 'reinforce'">{{ f(r.pb[r.a]) }} → {{ f(r.pa[r.a]) }}</div>
          <div class="ps__big" v-else-if="algo === 'a2c'">{{ f(a2.p[a2.a]) }} → {{ f(a2.p_after[a2.a]) }}</div>
          <div class="ps__big" v-else>{{ f(pp.rho) }}</div>
        </div>
      </div>
      <div class="ps__hover">{{ hover || (tanh ? 'Шари з tanh: синє — додатні значення нейрона, помаранчеве — від\'ємні.' : 'Шари з ReLU: що яскравіше, то більше значення; сіре — нейрон вимкнений, ReLU обнулила від\'ємне.') }}</div>
    </div>

    <!-- панель з формулами -->
    <div class="ps__panel">
      <!-- REINFORCE -->
      <template v-if="algo === 'reinforce'">
        <template v-if="stage === 0">
          <p>Стан на кроці {{ r.t }}: <b>s = {{ vec(r.s, 3) }}</b> — похибка висоти, м, і вертикальна швидкість, м/с.</p>
          <p>Шар 1 рахує 64 числа ReLU(W₁·s + b₁): від'ємні обнуляються, тож увімкнено {{ onCount(r.h1) }} нейронів із 64. Шар 2 так само: {{ onCount(r.h2) }} із 64.
            На виході — три логіти, «сирі бали» дій: <b>z = {{ vec(r.z) }}</b>.</p>
          <p class="ps__mute">Це перший епізод навчання: ваги ще випадкові, тож бали майже однакові.</p>
        </template>
        <template v-else-if="stage === 1">
          <p>softmax: π<sub>i</sub> = e<sup>z<sub>i</sub></sup> / (e<sup>z<sub>0</sub></sup> + e<sup>z<sub>1</sub></sup> + e<sup>z<sub>2</sub></sup>).</p>
          <p>e<sup>z</sup> = {{ vec(r.ez) }}, сума {{ f(r.sum) }}, тож <b>π = {{ vec(r.pb) }}</b>.</p>
          <p>Жереб за цими ймовірностями випав на дію <b>«{{ ANAME[r.a] }}»</b> (тяга {{ f(ACT[r.a]) }}).</p>
        </template>
        <template v-else-if="stage === 2">
          <p>REINFORCE чекає кінця епізоду: апарат упав на {{ f(rT * 0.02, 2) }} с, після {{ rT }} кроків. Тоді віддачу рахують із кінця: G<sub>t</sub> = r<sub>t</sub> + γ·G<sub>t+1</sub>, γ = 0,99.</p>
          <p v-if="r.Gn !== null">Для кроку {{ r.t }}: <b>G = {{ f(r.r) }} + 0,99 · {{ par(r.Gn) }} = {{ f(r.G) }}</b>.</p>
          <p v-else>Крок {{ r.t }} останній: G = r = {{ f(r.G) }}.</p>
          <p class="ps__mute">На графіку всі G від'ємні: кожен крок отримує штраф за все, що сталося після нього, зокрема за аварію.</p>
        </template>
        <template v-else-if="stage === 3">
          <p>Втрата всього епізоду: L = −(1/T) · Σ G<sub>t</sub> · log π(a<sub>t</sub> | s<sub>t</sub>) = <b>{{ f(R.loss) }}</b>, T = {{ rT }}.</p>
          <p>Внесок кроку {{ r.t }}: log π(«{{ ANAME[r.a] }}») = ln {{ f(r.pb[r.a]) }} = {{ f(r.logp) }}; G · log π = {{ f(r.G) }} · {{ par(r.logp) }} = {{ f(r.G * r.logp) }}.</p>
          <p>Поштовх логітам від цього кроку — вектор із картки «REINFORCE на числах», помножений на G/T:
            (G/T) · (e<sub>a</sub> − π) = <b>{{ vec(r.push) }}</b>. Від'ємний G опускає логіт спробуваної дії.</p>
        </template>
        <template v-else>
          <p>Adam робить <b>один</b> крок по всіх 4 547 вагах φ, склавши поштовхи всіх {{ rT }} кроків епізоду. Імовірності в стані кроку {{ r.t }}:</p>
          <div class="ps__tab"><table>
            <thead><tr><th>дія</th><th>до</th><th>після</th><th>зміна</th></tr></thead>
            <tbody><tr v-for="(p, i) in r.pb" :key="i" :class="{ pick: i === r.a }"><td>{{ ANAME[i] }}</td><td>{{ f(p) }}</td><td>{{ f(r.pa[i]) }}</td><td>{{ fs(r.pa[i] - p, 4) }}</td></tr></tbody>
          </table></div>
          <p v-if="r.agree">Спробувана дія стала менш імовірною, як і штовхав від'ємний G.</p>
          <p v-else>Цей крок штовхав дію «{{ ANAME[r.a] }}» вниз, але в сумі її ймовірність зросла: ваги спільні, а інші кроки епізоду ще сильніше штовхали вниз іншу дію. Так виглядає шум REINFORCE: сигнал окремого кроку тоне в сумі всього епізоду.</p>
          <p class="ps__mute">Зміни — у другому-третьому знаку після коми. Щоб політика навчилася, потрібні сотні таких епізодів.</p>
        </template>
      </template>

      <!-- A2C -->
      <template v-else-if="algo === 'a2c'">
        <template v-if="stage === 0">
          <p>Актор — та сама мережа 2 → 64 → 64 → 3, що в REINFORCE, після 40 тис. кроків навчання. Стан <b>s = {{ vec(a2.s, 3) }}</b>; увімкнено {{ onCount(a2.h1) }} і {{ onCount(a2.h2) }} нейронів із 64.</p>
          <p>Логіти z = {{ vec(a2.z) }} → softmax → <b>π = {{ vec(a2.p) }}</b>. Жереб: дія <b>«{{ ANAME[a2.a] }}»</b>, винагорода r = {{ f(a2.r) }}.</p>
        </template>
        <template v-else-if="stage === 1">
          <p>Критик — окрема мережа 2 → 64 → 64 → 1 з власними вагами θ. Для стану s вона видає <b>V(s) = {{ f(a2.v) }}</b>: стільки віддачі звідси в середньому чекають.</p>
          <p>Ту саму мережу проганяють для наступного стану s′ = {{ vec(a2.s2, 3) }}: <b>V(s′) = {{ f(a2.v_next) }}</b>.</p>
        </template>
        <template v-else-if="stage === 2">
          <p>Ціль критика: <b>y = r + γ · V(s′) = {{ f(a2.r) }} + 0,99 · {{ f(a2.v_next) }} = {{ f(a2.y) }}</b>.</p>
          <p>Перевага: <b>Adv = y − V(s) = {{ f(a2.y) }} − {{ f(a2.v) }} = {{ fs(a2.adv) }}</b>. Дія виявилася {{ a2.adv > 0 ? 'трохи кращою' : 'трохи гіршою' }}, ніж чекав критик.</p>
          <p class="ps__mute">Чекати кінця епізоду не треба: усе пораховано після одного кроку.</p>
        </template>
        <template v-else-if="stage === 3">
          <p>Три доданки для цього переходу:</p>
          <p>актор: −Adv · log π(a) = −{{ par(a2.adv) }} · {{ par(a2.logp) }} = {{ f(a2.actorTerm, 4) }};
            критик: ½ (y − V)² = {{ f(a2.criticTerm, 5) }}; ентропія H = −Σ π log π = {{ f(a2.ent) }}.</p>
          <p>Середні по п'яти переходах складають втрату: <b>L = {{ f(A.parts.actor, 4) }} + {{ f(A.parts.critic, 5) }} − 0,01 · {{ f(A.parts.entropy) }} = {{ f(A.loss, 5) }}</b>.
            Мінус перед ентропією — бонус за невпевненість, що підтримує дослідження.</p>
        </template>
        <template v-else>
          <p>Adam робить один крок одразу для обох мереж (темп 7·10⁻⁴, норму градієнта обрізано до 0,5):</p>
          <div class="ps__tab"><table>
            <thead><tr><th></th><th v-for="n in ANAME" :key="n">{{ n }}</th><th>V(s)</th></tr></thead>
            <tbody>
              <tr><td>до</td><td v-for="(p, i) in a2.p" :key="i" :class="{ pick: i === a2.a }">{{ f(p) }}</td><td>{{ f(a2.v) }}</td></tr>
              <tr><td>після</td><td v-for="(p, i) in a2.p_after" :key="i" :class="{ pick: i === a2.a }">{{ f(p) }}</td><td>{{ f(a2.v_after) }}</td></tr>
            </tbody>
          </table></div>
          <p v-if="a2.agree">Перевага {{ a2.adv > 0 ? 'додатна — ймовірність дії зросла' : 'від\'ємна — ймовірність дії впала' }}. Далі — наступні 5 кроків новою політикою.</p>
          <p v-else>Перевага цього переходу мала, і в сумі п'яти переходів дія зсунулася в інший бік.</p>
          <p class="ps__mute">Критик тягнеться до цілей усіх п'яти переходів разом, тож окрема оцінка V(s) може пройти й повз свою ціль y = {{ f(a2.y) }}.</p>
        </template>
      </template>

      <!-- PPO -->
      <template v-else>
        <template v-if="stage === 0">
          <p>Актор PPO у Stable-Baselines3 — мережа 2 → 64 → 64 з tanh: значення нейронів від −1 до 1. Стан <b>s = {{ vec(pp.obs, 3) }}</b>.</p>
          <p>Вихід — одне число μ, центр гауссіана для дії a ∈ [−1; 1]; тяга u = (a + 1)/2, тож центр тяги <b>μ<sub>u</sub> = {{ f(pp.mu0) }}</b>.
            Ширина σ від стану не залежить: це окремий параметр мережі, після {{ steps(P.meta.steps) }} кроків <b>σ<sub>u</sub> = {{ f(pp.s0) }}</b>.</p>
        </template>
        <template v-else-if="stage === 1">
          <p>Дію жеребкують із гауссіана: випала тяга <b>u = {{ f(pp.u) }}</b>, на {{ f(Math.abs(pp.u - pp.mu0) / pp.s0, 1) }} σ від центру.</p>
          <p>Політика запам'ятовує щільність у цій точці: <b>π<sub>β</sub>(u) = {{ f(pp.d0) }}</b>. Це «стара» політика π<sub>β</sub>, з якою потім порівнюватимуть нову.</p>
        </template>
        <template v-else-if="stage === 2">
          <p>Критик — окрема tanh-мережа: V(s) = {{ f(pp.v) }}, V(s′) = {{ f(pp.v_next) }}, винагорода r = {{ f(pp.r) }}.</p>
          <p>Часова різниця, як в A2C: δ = r + γ·V(s′) − V(s) = {{ f(pp.r) }} + 0,99 · {{ par(pp.v_next) }} − {{ par(pp.v) }} = {{ fs(pp.delta) }}.</p>
          <p>Stable-Baselines3 бере не одну δ, а зважену суму δ на багато кроків уперед з вагами (γλ)<sup>k</sup>, λ = 0,95 (GAE): <b>Adv = {{ fs(pp.adv) }}</b>.
            Перед кроком градієнта переваги ще нормують у кожному міні-пакеті.</p>
        </template>
        <template v-else-if="stage === 3">
          <p>Зібрані {{ steps(P.meta.n) }} кроків пройдено {{ P.meta.epochs }} епох міні-пакетами по {{ P.meta.batch }} — це {{ P.meta.epochs * P.meta.n / P.meta.batch }} кроків градієнта.
            Центр зсунувся: μ<sub>u</sub> {{ f(pp.mu0) }} → {{ f(pp.mu1) }}; ширина σ<sub>u</sub> {{ f(pp.s0) }} → {{ f(pp.s1) }}. На графіку стара крива — пунктир, нова — суцільна.</p>
          <p>Щільність у тій самій точці u: π(u) = {{ f(pp.d1) }}. <b>ρ = π(u) / π<sub>β</sub>(u) = {{ f(pp.d1) }} / {{ f(pp.d0) }} = {{ f(pp.rho) }}</b>:
            ймовірність цієї дії {{ pp.rho > 1 ? 'зросла' : 'впала' }} у {{ f(pp.rho > 1 ? pp.rho : 1 / pp.rho, 2) }} раза.</p>
          <p class="ps__mute">{{ pp.adv > 0 ? 'Перевага додатна — крива посунулася до спробуваної дії.' : 'Перевага від\'ємна — крива відсунулася від спробуваної дії.' }}</p>
        </template>
        <template v-else>
          <p>Коридор PPO: [{{ f(1 - P.meta.eps, 1) }}; {{ f(1 + P.meta.eps, 1) }}]. ρ = {{ f(pp.rho) }} — <b>{{ pp.inside ? 'у коридорі' : 'за коридором' }}</b>.</p>
          <p>Ціль PPO для цього переходу (для наочності — з ненормованою перевагою):
            min(ρ·Adv, clip(ρ)·Adv) = min({{ f(pp.o1) }}; {{ f(pp.o2) }}) = <b>{{ f(pp.obj) }}</b>.</p>
          <p v-if="pp.clipped">Мінімум дає обрізаний доданок — сталий, без градієнта: подальша зміна ймовірності цієї дії вже не зараховується, і перехід перестає штовхати політику.</p>
          <p v-else>Мінімум дає звичайний доданок ρ·Adv: перехід і далі штовхає політику.</p>
          <p class="ps__mute">Після {{ P.meta.epochs }} епох за межами коридору опинилося {{ f(P.meta.clipped_share * 100, 1) }}&nbsp;% переходів порції: обрізання тримає більшість кроків малими, але не всі.</p>
        </template>
      </template>
    </div>

    <div class="lab__pills">
      <button class="lab__pill" type="button" :disabled="stage === 0" @click="prev">← назад</button>
      <button class="lab__pill is-on" type="button" :disabled="stage === STAGES.length - 1" @click="next">далі →</button>
    </div>
  </div>
</template>

<style scoped>
.ps__stages { display: flex; flex-wrap: wrap; gap: 0.3rem; margin: 0.5rem 0; }
.ps__stage {
  font: inherit; font-size: 0.78rem; padding: 0.2rem 0.6rem; border-radius: 6px; cursor: pointer;
  border: 1px solid var(--uk-line); background: transparent; color: var(--vp-c-text-2);
}
.ps__stage.done { color: var(--vp-c-text-1); background: var(--uk-fill); }
.ps__stage.on { border-color: var(--uk-accent); color: var(--uk-accent); font-weight: 600; }
.ps__stage:focus-visible { outline: 2px solid var(--uk-accent); outline-offset: 2px; }

.ps__flow { border: 1px solid var(--uk-line); border-radius: 10px; padding: 0.5rem 0.6rem; display: grid; gap: 0.45rem; }
.ps__lane { display: grid; gap: 0.2rem; }
.ps__lname { font-size: 0.72rem; text-transform: uppercase; letter-spacing: 0.04em; color: var(--vp-c-text-3); }
.ps__row { display: flex; flex-wrap: wrap; align-items: center; gap: 0.3rem; }
.ps__tail { border-top: 1px dashed var(--uk-line); padding-top: 0.45rem; }
.ps__arr { color: var(--vp-c-text-3); font-size: 0.9rem; }
.ps__blk {
  border: 1px solid var(--uk-line); border-radius: 8px; padding: 0.3rem 0.4rem; background: var(--vp-c-bg);
  opacity: 0.32; transition: opacity 0.2s, border-color 0.2s, box-shadow 0.2s;
}
.ps__blk.seen { opacity: 1; }
.ps__blk.on { border-color: var(--uk-accent); box-shadow: 0 0 0 2px color-mix(in srgb, var(--uk-accent) 25%, transparent); }
.ps__bt { font-size: 0.68rem; color: var(--vp-c-text-2); margin-bottom: 0.2rem; white-space: nowrap; }
.ps__in { display: grid; grid-template-columns: auto auto; gap: 0.1rem 0.35rem; font-size: 0.74rem; align-items: baseline; }
.ps__in span { color: var(--vp-c-text-3); }
.ps__in b, .ps__nums b, .ps__big { font-family: var(--vp-font-family-mono); }
.ps__grid { display: grid; grid-template-columns: repeat(8, 9px); gap: 1px; }
.ps__grid i { width: 9px; height: 9px; border-radius: 1px; cursor: crosshair; }
.ps__nums { display: grid; gap: 0.1rem; font-size: 0.74rem; }
.ps__nums div { display: flex; justify-content: space-between; gap: 0.5rem; }
.ps__nums span { color: var(--vp-c-text-3); }
.ps__bars { display: flex; align-items: flex-end; gap: 0.35rem; height: 72px; }
.ps__b { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; height: 100%; font-size: 0.68rem; font-family: var(--vp-font-family-mono); }
.ps__b i { width: 18px; background: var(--uk-line); border-radius: 2px 2px 0 0; }
.ps__b.pick i { background: var(--uk-warm); }
.ps__big { font-size: 0.95rem; font-weight: 600; padding: 0.1rem 0; white-space: nowrap; }
.ps__g { width: 170px; height: auto; display: block; }
.ps__ep { width: 240px; height: auto; display: block; }
.ps__g0 { fill: none; stroke: var(--uk-accent); stroke-width: 2; }
.ps__g0.dash { stroke-dasharray: 4 3; stroke-width: 1.4; opacity: 0.8; }
.ps__g1 { fill: none; stroke: var(--uk-green); stroke-width: 2; }
.ps__gu { stroke: var(--uk-warm); stroke-width: 1; stroke-dasharray: 3 3; }
.ps__gd0 { fill: var(--uk-accent); }
.ps__gd1 { fill: var(--uk-green); }
.ps__gt { fill: var(--vp-c-text-3); font-size: 9px; font-family: var(--vp-font-family-mono); }
.ps__zero { stroke: var(--uk-line); stroke-width: 0.8; }
.ps__er { fill: none; stroke: var(--vp-c-text-3); stroke-width: 1; stroke-dasharray: 2 2; }
.ps__eg { fill: none; stroke: var(--uk-accent); stroke-width: 1.8; }
.ps__hover { font-size: 0.74rem; color: var(--vp-c-text-2); font-family: var(--vp-font-family-mono); min-height: 1.1rem; }

.ps__panel { background: var(--uk-fill); border-radius: 10px; padding: 0.7rem 0.9rem; margin: 0.5rem 0 0.6rem; display: grid; gap: 0.45rem; }
.ps__panel p { margin: 0; font-size: 0.9rem; line-height: 1.55; overflow-wrap: break-word; }
.ps__mute { color: var(--vp-c-text-2); font-size: 0.84rem !important; }
.ps__tab { overflow-x: auto; }
.ps__tab td { font-family: var(--vp-font-family-mono); font-size: 0.78rem; white-space: nowrap; }
.ps__tab .pick, .ps__tab tr.pick td { color: var(--uk-warm); font-weight: 700; }
</style>
