<script setup lang="ts">
/**
 * Фактичний вивід прикладу. Видний завжди, навіть коли код згорнуто (CodeFold):
 * читач бачить результат, не відкриваючи коду. Під виводом — одна фраза
 * «На що дивитися: …» (передається в слот note).
 */
</script>

<template>
  <div class="ro">
    <div class="ro__head">
      <span class="ro__dot" aria-hidden="true" />
      Вивід
      <em>код запущено, вивід не редагувався</em>
    </div>
    <div class="ro__body">
      <slot />
    </div>
    <div v-if="$slots.note" class="ro__note">
      <slot name="note" />
    </div>
  </div>
</template>

<style scoped>
.ro {
  margin: 0 0 1.6rem;
  border: 1px solid var(--uk-line);
  border-top: 0;
  border-radius: 0 0 10px 10px;
  overflow: hidden;
  background: var(--vp-c-bg);
}
.ro__head {
  display: flex;
  align-items: center;
  gap: 0.45rem;
  padding: 0.45rem 0.9rem;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.02em;
  text-transform: uppercase;
  color: var(--vp-c-text-2);
  background: var(--uk-fill);
  border-top: 1px dashed var(--uk-line);
}
.ro__head em {
  font-style: normal;
  font-weight: 400;
  text-transform: none;
  letter-spacing: 0;
  color: var(--vp-c-text-3);
  margin-left: auto;
}
.ro__dot {
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background: var(--uk-green);
}
.ro__body :deep(div[class*='language-']) {
  margin: 0 !important;
  border-radius: 0 !important;
  background: transparent !important;
}
.ro__body :deep(div.line-numbers-mode) { padding-left: 0 !important; }
.ro__body :deep(pre) {
  padding: 0.75rem 0.9rem !important;
  overflow-x: auto;
}
.ro__body :deep(code) {
  font-size: 0.82rem;
  line-height: 1.55;
  font-variant-numeric: tabular-nums;
}
.ro__body :deep(.line-numbers-wrapper) { display: none; }
.ro__body :deep(.lang), .ro__body :deep(button.copy) { display: none; }
.ro__note {
  padding: 0.55rem 0.9rem 0.65rem;
  border-top: 1px solid var(--uk-line);
  font-size: 0.88rem;
  color: var(--vp-c-text-2);
}
.ro__note :deep(p) { margin: 0; }
@media (max-width: 640px) {
  .ro__head em { display: none; }
  .ro__body :deep(code) { font-size: 0.74rem; }
}
</style>
