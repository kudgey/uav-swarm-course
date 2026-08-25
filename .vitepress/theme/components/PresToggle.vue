<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'

const on = ref(false)

function toggle() {
  on.value = !on.value
  document.documentElement.classList.toggle('uk-pres', on.value)
}

function onKey(e: KeyboardEvent) {
  const t = e.target as HTMLElement
  if (t && /^(INPUT|TEXTAREA|SELECT)$/.test(t.tagName)) return
  if (e.key === 'p' && !e.metaKey && !e.ctrlKey && !e.altKey) toggle()
}

onMounted(() => document.addEventListener('keydown', onKey))
onUnmounted(() => {
  document.removeEventListener('keydown', onKey)
  document.documentElement.classList.remove('uk-pres')
})
</script>

<template>
  <button class="uk-pres-toggle" @click="toggle" :title="'Режим презентації — клавіша P'">
    <span>{{ on ? 'Звичайний вигляд' : 'Режим презентації' }}</span>
    <kbd>P</kbd>
  </button>
</template>
