<script setup lang="ts">
/** Фактичний вивід прикладу: цей код справді запускали, а не переказували. */
</script>

<template>
  <div class="ro">
    <div class="ro__head">
      <span class="ro__dot" />
      Результат виконання
      <em>код запущено локально, вивід не редагувався</em>
    </div>
    <div class="ro__body">
      <slot />
    </div>
  </div>
</template>

<style scoped>
.ro {
  margin: -0.9rem 0 1.6rem;
  border: 1px solid var(--uk-line);
  border-top: 0;
  border-radius: 0 0 10px 10px;
  overflow: hidden;
  background: var(--uk-fill);
}
.ro__head {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.9rem;
  font-size: 0.74rem;
  font-weight: 500;
  letter-spacing: 0.02em;
  color: var(--vp-c-text-2);
  border-bottom: 1px solid var(--uk-line);
}
.ro__dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--uk-green);
  flex: none;
}
.ro__head em {
  font-style: normal;
  font-size: 0.7rem;
  color: var(--vp-c-text-3);
  margin-left: auto;
}
.ro__body :deep(div[class*='language-']) {
  margin: 0;
  border: 0;
  border-radius: 0;
  background: transparent;
}
.ro__body :deep(pre) {
  padding: 0.7rem 0.9rem !important;
  background: transparent !important;
}
.ro__body :deep(code) {
  font-size: 0.78rem;
  line-height: 1.6;
}
.ro__body :deep(.lang),
.ro__body :deep(.copy),
.ro__body :deep(.line-numbers-wrapper) { display: none; }
.ro__body :deep(.vp-code) { padding-left: 0 !important; }
.ro__body :deep(div[class*='language-'].line-numbers-mode) { padding-left: 0; }
</style>
