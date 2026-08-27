<script setup lang="ts">
/** Головна: карта курсу за блоками. */
import { withBase } from 'vitepress'

const BLOCKS = [
  {
    code: 'A',
    name: 'Рій як система',
    lead: 'Архітектура роєвої системи цілком, математика опису апарата й графа рою, класичні закони керування строєм і їхні межі.',
    items: [
      { id: '01', t: 'Вступ до роїв БПЛА' },
      { id: '02', t: 'Математичні основи роїв БПЛА' },
      { id: '03', t: 'Керування роєм: строї та топології' }
    ]
  },
  {
    code: 'B',
    name: 'Навчання з підкріпленням',
    lead: 'Постановка задачі навчання: одноагентна, багатоагентна, глибока. Що ламається при переході від таблиці до нейромережі.',
    items: [
      { id: '04', t: 'Навчання з підкріпленням: основи' },
      { id: '05', t: 'Багатоагентне навчання: моделі та виклики' },
      { id: '06', t: 'Глибоке навчання з підкріпленням для БПЛА' }
    ]
  },
  {
    code: 'C',
    name: 'Рій, що навчається',
    lead: 'Інваріантність до перестановки й розміру рою, централізоване навчання з децентралізованим виконанням, прикладні місії.',
    items: [
      { id: '07', t: 'Багатоагентне навчання для роїв БПЛА' },
      { id: '08', t: 'Конкретні задачі роїв' }
    ]
  },
  {
    code: 'D',
    name: 'Надійність і реалізація',
    lead: 'Що робити, коли відмовляє привод, зникає канал або дрейфує барометр. Як це реалізувати й чесно виміряти.',
    items: [
      { id: '09', t: 'Безпека та робастність роїв БПЛА' },
      { id: '10', t: 'Реалізація та викладання' }
    ]
  }
]
</script>

<template>
  <div class="uk-hero">
    <div class="uk-hero__eyebrow">КПІ ім. Ігоря Сікорського · магістратура · 2026/2027</div>
    <h1>Машинне навчання у ройових системах БПЛА</h1>
    <p class="uk-hero__lead">
      Десять модулів — від означення рою й математики його опису до навчених
      багатоагентних політик, їхніх меж і чесного вимірювання результату. Кожна
      тема проходить один і той самий шлях: задача рою → дані апарата →
      комунікація → алгоритм або навчена політика → код і симуляція →
      колективна поведінка → метрики й обмеження.
    </p>
    <p class="uk-hero__author">Kirill Riazanovskiy, PhD</p>
  </div>

  <div class="uk-blocks">
    <section v-for="b in BLOCKS" :key="b.code" class="uk-block">
      <div class="uk-block__tag">БЛОК {{ b.code }}</div>
      <h3>{{ b.name }}</h3>
      <p class="uk-block__lead">{{ b.lead }}</p>
      <ol>
        <li v-for="l in b.items" :key="l.id">
          <a :href="withBase(`/lectures/${l.id}`)">{{ l.t }}</a>
        </li>
      </ol>
    </section>
  </div>

  <div class="uk-facts">
    <div class="uk-fact"><b>10</b><span>модулів</span></div>
    <div class="uk-fact"><b>307</b><span>розділів</span></div>
    <div class="uk-fact"><b>101</b><span>ілюстрація</span></div>
    <div class="uk-fact"><b>13</b><span>віджетів</span></div>
    <div class="uk-fact"><b>5</b><span>лабораторних</span></div>
  </div>

  <div class="uk-thesis">
    <p>
      Головна теза курсу, яку варто тримати в голові від першої лекції до останньої:
      <b>жодна властивість рою не з'являється автоматично</b> — ані масштабованість,
      ані відмовостійкість, ані безпека. Кожну треба спроєктувати, реалізувати
      й виміряти.
    </p>
    <p class="uk-thesis__links">
      <a :href="withBase('/labs')">Лабораторні роботи</a> ·
      <a :href="withBase('/about')">Про курс і джерела</a>
    </p>
  </div>
</template>

<style scoped>
.uk-hero__author {
  margin-top: 1.4rem;
  font-size: 0.95rem;
  color: var(--vp-c-text-2);
  border-left: 3px solid var(--uk-accent);
  padding-left: 0.8rem;
}
.uk-block__lead {
  font-size: 0.86rem;
  line-height: 1.5;
  color: var(--vp-c-text-3);
  margin: 0 0 0.7rem;
}
.uk-block ol { list-style: decimal; }
.uk-block ol li::marker {
  font-family: var(--vp-font-family-mono);
  font-size: 0.78rem;
  color: var(--vp-c-text-3);
}

.uk-facts {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: 0.7rem;
  margin: 2.5rem 0 0;
  padding-top: 1.8rem;
  border-top: 1px solid var(--uk-line);
}
.uk-fact { text-align: center; }
.uk-fact b {
  display: block;
  font-size: 1.75rem;
  font-weight: 600;
  letter-spacing: -0.02em;
  color: var(--uk-accent);
  font-variant-numeric: tabular-nums;
}
.uk-fact span {
  font-size: 0.8rem;
  color: var(--vp-c-text-3);
}

.uk-thesis {
  margin-top: 2.4rem;
  padding-top: 1.8rem;
  border-top: 1px solid var(--uk-line);
  font-size: 0.95rem;
  line-height: 1.62;
  color: var(--vp-c-text-2);
  max-width: 72ch;
}
.uk-thesis__links {
  margin-top: 1rem;
  font-size: 0.9rem;
}
</style>
