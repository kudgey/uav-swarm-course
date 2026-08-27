import { h } from 'vue'
import DefaultTheme from 'vitepress/theme'
import type { Theme } from 'vitepress'

import '@fontsource/ibm-plex-sans/400.css'
import '@fontsource/ibm-plex-sans/500.css'
import '@fontsource/ibm-plex-sans/600.css'
import '@fontsource/ibm-plex-serif/400.css'
import '@fontsource/jetbrains-mono/400.css'
import './style.css'

import CourseHome from './components/CourseHome.vue'
import Figure from './components/Figure.vue'
import Flow from './components/Flow.vue'
import BoidsLab from './components/BoidsLab.vue'
import ConsensusLab from './components/ConsensusLab.vue'
import PotentialFieldLab from './components/PotentialFieldLab.vue'
import ConnectivityLab from './components/ConnectivityLab.vue'
import RewardLab from './components/RewardLab.vue'
import ScalingLab from './components/ScalingLab.vue'
import GridWorldLab from './components/GridWorldLab.vue'
import SeedsLab from './components/SeedsLab.vue'
import MatrixGameLab from './components/MatrixGameLab.vue'
import RobustnessLab from './components/RobustnessLab.vue'
import EpsilonLab from './components/EpsilonLab.vue'
import DelayLab from './components/DelayLab.vue'
import VoronoiLab from './components/VoronoiLab.vue'
import RunOutput from './components/RunOutput.vue'
import PresToggle from './components/PresToggle.vue'

export default {
  extends: DefaultTheme,
  // Кнопка режиму презентації монтується глобально, а не вручну на сторінці:
  // так вона доступна й на головній, і на кожній лекції.
  Layout() {
    return h(DefaultTheme.Layout, null, {
      'layout-bottom': () => h(PresToggle)
    })
  },
  enhanceApp({ app }) {
    app.component('CourseHome', CourseHome)
    app.component('Figure', Figure)
    app.component('Flow', Flow)
    app.component('BoidsLab', BoidsLab)
    app.component('ConsensusLab', ConsensusLab)
    app.component('PotentialFieldLab', PotentialFieldLab)
    app.component('ConnectivityLab', ConnectivityLab)
    app.component('RewardLab', RewardLab)
    app.component('ScalingLab', ScalingLab)
    app.component('GridWorldLab', GridWorldLab)
    app.component('SeedsLab', SeedsLab)
    app.component('MatrixGameLab', MatrixGameLab)
    app.component('RobustnessLab', RobustnessLab)
    app.component('EpsilonLab', EpsilonLab)
    app.component('DelayLab', DelayLab)
    app.component('VoronoiLab', VoronoiLab)
    app.component('RunOutput', RunOutput)
    app.component('PresToggle', PresToggle)
  }
} satisfies Theme
