import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Рої БПЛА та машинне навчання',
  description:
    'Магістерський курс: машинне навчання у ройових системах безпілотних апаратів. КПІ ім. Ігоря Сікорського, спеціальність F3.',
  lang: 'uk-UA',
  // GitHub Pages у підкаталозі вимагає base='/<репозиторій>/'.
  // Задається змінною оточення, щоб той самий код працював і на власному домені.
  base: process.env.BASE ?? '/',
  cleanUrls: true,
  // .ipynb VitePress вважає маршрутом і не знаходить сторінки, хоча файл
  // лежить у public/. Дозволяємо саме цей шлях, решту посилань і далі перевіряє.
  ignoreDeadLinks: [/\.ipynb$/],
  lastUpdated: true,
  markdown: {
    math: true,
    lineNumbers: true,
    theme: { light: 'github-light', dark: 'github-dark' },
    image: { lazyLoading: true }
  },
  head: [
    ['meta', { name: 'theme-color', content: '#3D4EC4' }],
    ['meta', { property: 'og:title', content: 'Машинне навчання у ройових системах БПЛА' }]
  ],
  themeConfig: {
    outline: { level: [2, 3], label: 'На цій сторінці' },
    nav: [
      { text: 'Лекції', link: '/lectures/01' },
      { text: 'Лабораторні', link: '/labs' },
      { text: 'Про курс', link: '/about' }
    ],
    sidebar: [
      {
        text: 'Курс',
        items: [
          { text: 'Огляд і структура', link: '/' },
          { text: 'Лабораторні роботи', link: '/labs' },
          { text: 'Про курс і джерела', link: '/about' }
        ]
      },
      {
        text: 'Блок A · Рій як система',
        collapsed: false,
        items: [
          { text: '01 · Вступ до роїв БПЛА', link: '/lectures/01' },
          { text: '02 · Математичні основи роїв БПЛА', link: '/lectures/02' },
          { text: '03 · Керування роєм: строї та топології', link: '/lectures/03' }
        ]
      },
      {
        text: 'Блок B · Навчання з підкріпленням',
        collapsed: false,
        items: [
          { text: '04 · Навчання з підкріпленням: основи', link: '/lectures/04' },
          { text: '05 · Багатоагентне навчання: моделі та виклики', link: '/lectures/05' },
          { text: '06 · Глибоке навчання з підкріпленням для БПЛА', link: '/lectures/06' }
        ]
      },
      {
        text: 'Блок C · Рій, що навчається',
        collapsed: false,
        items: [
          { text: '07 · Багатоагентне навчання для роїв БПЛА', link: '/lectures/07' },
          { text: '08 · Конкретні задачі роїв', link: '/lectures/08' }
        ]
      },
      {
        text: 'Блок D · Надійність і реалізація',
        collapsed: false,
        items: [
          { text: '09 · Безпека та робастність роїв БПЛА', link: '/lectures/09' },
          { text: '10 · Реалізація та викладання', link: '/lectures/10' }
        ]
      }
    ],
    docFooter: { prev: 'Попередній модуль', next: 'Наступний модуль' },
    darkModeSwitchLabel: 'Тема',
    lightModeSwitchTitle: 'Світла тема',
    darkModeSwitchTitle: 'Темна тема',
    sidebarMenuLabel: 'Розділи',
    returnToTopLabel: 'Догори',
    lastUpdatedText: 'Оновлено',
    search: {
      provider: 'local',
      options: {
        translations: {
          button: { buttonText: 'Пошук', buttonAriaLabel: 'Пошук' },
          modal: {
            noResultsText: 'Нічого не знайдено',
            resetButtonTitle: 'Очистити',
            footer: {
              selectText: 'вибрати',
              navigateText: 'навігація',
              closeText: 'закрити'
            }
          }
        }
      }
    },
    footer: {
      message:
        'Матеріали курсу. Схеми із зовнішніх джерел належать їхнім авторам — посилання під кожною ілюстрацією.',
      copyright: 'КПІ ім. Ігоря Сікорського · спеціальність F3 · 2026/2027'
    }
  },
  vite: { server: { fs: { allow: ['..'] } } }
})
