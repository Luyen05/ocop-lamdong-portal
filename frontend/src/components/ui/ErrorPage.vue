<script setup lang="ts">
/** Khung trang lỗi dùng chung (404, 403, lỗi hiển thị): mã lỗi, tiêu đề, mô tả và nút hành động. */
defineProps<{ code: string; title: string; titleId?: string }>()
</script>

<template>
  <main class="error-page">
    <section class="error-card ocop-enter" :aria-labelledby="titleId || 'error-title'">
      <img class="error-logo" src="/assets/brand/bieu-tuong-128.png" alt="" width="72" height="72" />
      <span class="error-code">{{ code }}</span>
      <slot name="icon" />
      <h1 :id="titleId || 'error-title'">{{ title }}</h1>
      <div class="error-message"><slot /></div>
      <div class="error-actions"><slot name="actions" /></div>
      <div v-if="$slots.extra" class="error-extra"><slot name="extra" /></div>
    </section>
  </main>
</template>

<style scoped>
.error-page {
  display: grid;
  min-height: 65vh;
  padding: var(--ocop-space-12) var(--ocop-space-4);
  grid-template-columns: minmax(0, 1fr);
  place-items: center;
  background: radial-gradient(circle at 50% 10%, color-mix(in srgb, var(--ocop-mint-200) 40%, transparent), transparent 24rem), var(--ocop-surface);
}

.error-card {
  width: min(100%, 560px);
  padding: clamp(var(--ocop-space-8), 6vw, 56px);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-xl);
  background: var(--ocop-card);
  box-shadow: 0 24px 50px color-mix(in srgb, var(--ocop-neutral-900) 10%, transparent);
  text-align: center;
}

.error-logo {
  display: block;
  width: 72px;
  height: 72px;
  margin: 0 auto var(--ocop-space-4);
}

.error-code {
  display: block;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 900;
  letter-spacing: 0.18em;
}

h1 {
  margin: var(--ocop-space-3) 0 0;
  color: var(--ocop-navy);
  font-size: clamp(28px, 5vw, 38px);
  font-weight: 800;
  letter-spacing: -0.7px;
}

.error-message {
  margin: var(--ocop-space-4) auto 0;
  color: var(--ocop-slate);
  line-height: 1.7;
}

.error-message :deep(p) {
  margin: 0;
}

.error-actions {
  display: flex;
  margin-top: 28px;
  flex-wrap: wrap;
  justify-content: center;
  gap: 10px;
}

.error-actions :deep(a),
.error-actions :deep(button) {
  padding: 10px 18px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: transparent;
  color: var(--ocop-primary-900);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
  text-decoration: none;
}

.error-actions :deep(.primary-action) {
  border-color: var(--ocop-primary-700);
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
}

.error-extra {
  margin-top: var(--ocop-space-6);
  padding-top: var(--ocop-space-4);
  border-top: 1px solid var(--ocop-border);
}
</style>
