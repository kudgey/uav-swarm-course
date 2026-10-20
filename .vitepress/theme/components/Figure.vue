<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { withBase } from 'vitepress'

const props = defineProps<{ src: string; msrc?: string; alt?: string }>()

/**
 * Звичайні markdown-картинки VitePress префіксує base сам, а вміст
 * компонента — ні. Без withBase на GitHub Pages, де сайт лежить
 * у підкаталозі /<репозиторій>/, усі рисунки дають 404.
 */
const url = computed(() => withBase(props.src))
/** Вузька версія для екранів до 720 px — для рисунків, ширших за 2,2:1. */
const murl = computed(() => (props.msrc ? withBase(props.msrc) : ''))

const zoomed = ref<string | null>(null)

function open(src: string) {
  zoomed.value = src
  document.addEventListener('keydown', onKey)
}
function close() {
  zoomed.value = null
  document.removeEventListener('keydown', onKey)
}
function onKey(e: KeyboardEvent) {
  if (e.key === 'Escape') close()
}
onUnmounted(() => document.removeEventListener('keydown', onKey))
</script>

<template>
  <figure class="uk-figure">
    <div class="uk-figure__frame" :class="{ 'has-m': murl }" @click="open(url)" :title="'Збільшити: ' + (alt || '')">
      <picture>
        <source v-if="murl" media="(max-width: 720px)" :srcset="murl" />
        <img :src="url" :alt="alt" loading="lazy" />
      </picture>
    </div>
    <figcaption class="uk-figure__caption">
      <slot />
    </figcaption>
  </figure>

  <Teleport to="body">
    <div v-if="zoomed" class="uk-lightbox" @click="close">
      <img :src="zoomed" :alt="alt" />
    </div>
  </Teleport>
</template>
