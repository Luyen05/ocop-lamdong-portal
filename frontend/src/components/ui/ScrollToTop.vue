<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'

const isVisible = ref(false)

function updateVisibility(): void {
  isVisible.value = window.scrollY > 360
}

function scrollToTop(): void {
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

onMounted(() => {
  updateVisibility()
  window.addEventListener('scroll', updateVisibility, { passive: true })
})

onBeforeUnmount(() => window.removeEventListener('scroll', updateVisibility))
</script>

<template>
  <Transition name="scroll-button">
    <button
      v-if="isVisible"
      class="scroll-to-top"
      type="button"
      aria-label="Trở về đầu trang"
      @click="scrollToTop"
    >
      <AppIcon name="chevronUp" :size="19" />
    </button>
  </Transition>
</template>

<style scoped>
.scroll-to-top {
  position: fixed;
  z-index: 90;
  right: 20px;
  bottom: 20px;
  display: grid;
  width: 44px;
  height: 44px;
  padding: 0;
  place-items: center;
  border: 1px solid color-mix(in srgb, var(--ocop-white) 28%, transparent);
  border-radius: 50%;
  background: var(--ocop-primary-700);
  box-shadow: 0 10px 24px color-mix(in srgb, var(--ocop-primary-950) 24%, transparent);
  color: var(--ocop-white);
}

.scroll-to-top:hover {
  background: var(--ocop-primary-900);
  transform: translateY(-2px);
}

.scroll-to-top:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--ocop-primary-500) 32%, transparent);
  outline-offset: 3px;
}

.scroll-button-enter-active,
.scroll-button-leave-active {
  transition: opacity 150ms ease, transform 150ms ease;
}

.scroll-button-enter-from,
.scroll-button-leave-to {
  opacity: 0;
  transform: translateY(8px);
}

@media (prefers-reduced-motion: reduce) {
  .scroll-to-top,
  .scroll-button-enter-active,
  .scroll-button-leave-active {
    transition: none;
  }
}
</style>
