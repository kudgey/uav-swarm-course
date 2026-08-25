<script setup lang="ts">
/**
 * Потокова схема «A → B → C».
 *
 * У Gamma це був рядок `> СХЕМА:`, і там діаграма обрізалася до чотирьох
 * вузлів — довші ланцюги втрачали хвіст. Тут обмеження немає: на вузькому
 * екрані ланцюг просто перебудовується згори вниз.
 */
defineProps<{ nodes: string[]; labels?: string[] }>()
</script>

<template>
  <div class="flow" role="list">
    <template v-for="(node, i) in nodes" :key="i">
      <div class="flow__node" role="listitem">
        <span class="flow__n">{{ i + 1 }}</span>
        <span class="flow__text">{{ node }}</span>
        <span v-if="labels && labels[i]" class="flow__label">{{ labels[i] }}</span>
      </div>
      <div v-if="i < nodes.length - 1" class="flow__arrow" aria-hidden="true">
        <svg viewBox="0 0 24 24" width="18" height="18">
          <path
            d="M4 12h14M13 7l5 5-5 5"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          />
        </svg>
      </div>
    </template>
  </div>
</template>

<style scoped>
.flow {
  display: flex;
  align-items: stretch;
  flex-wrap: wrap;
  gap: 0.35rem;
  margin: 1.4rem 0;
}
.flow__node {
  flex: 1 1 0;
  min-width: 8.5rem;
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  padding: 0.7rem 0.85rem;
  border: 1px solid var(--vp-c-divider);
  border-radius: 10px;
  background: var(--vp-c-bg-soft);
  font-size: 0.84rem;
  line-height: 1.45;
}
.flow__n {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 1.25rem;
  height: 1.25rem;
  border-radius: 50%;
  background: var(--vp-c-brand-1);
  color: #fff;
  font-size: 0.68rem;
  font-weight: 600;
  flex: none;
}
.flow__text { color: var(--vp-c-text-1); }
.flow__label {
  font-size: 0.75rem;
  color: var(--vp-c-text-3);
}
.flow__arrow {
  display: flex;
  align-items: center;
  color: var(--vp-c-text-3);
  flex: none;
}

/* Вузький екран: ланцюг вертикальний, стрілки повертаються вниз. */
@media (max-width: 640px) {
  .flow { flex-direction: column; }
  .flow__arrow { transform: rotate(90deg); align-self: center; }
}
</style>
