<script setup lang="ts">
import { ref, computed, onUnmounted } from 'vue'
import { withBase } from 'vitepress'

const props = defineProps<{ src: string; alt?: string }>()

/**
 * Звичайні markdown-картинки VitePress префіксує base сам, а вміст
 * компонента — ні. Без withBase на GitHub Pages, де сайт лежить
 * у підкаталозі /<репозиторій>/, усі рисунки дають 404.
 */
const url = computed(() => withBase(props.src))

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
    <div class="uk-figure__frame" @click="open(url)" :title="'Збільшити: ' + (alt || '')">
      <img :src="url" :alt="alt" loading="lazy" />
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
