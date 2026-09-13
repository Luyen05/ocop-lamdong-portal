<script setup lang="ts">
import { useRoute } from 'vue-router'

import AppHeader from '@/components/AppHeader.vue'
import SiteFooter from '@/components/SiteFooter.vue'

const route = useRoute()
</script>

<template>
  <AppHeader
    v-if="route.meta.layout !== 'auth' && route.meta.layout !== 'admin' && route.meta.layout !== 'subject'"
  />
  <RouterView v-slot="{ Component, route: currentRoute }">
    <Transition name="route" mode="out-in">
      <component :is="Component" :key="currentRoute.path" />
    </Transition>
  </RouterView>
  <SiteFooter
    v-if="route.meta.layout !== 'auth' && route.meta.layout !== 'admin' && route.meta.layout !== 'subject'"
  />
</template>

<style>
.route-enter-active {
  transition: opacity 180ms ease-out, transform 180ms ease-out;
}

.route-leave-active {
  transition: opacity 100ms ease-in;
}

.route-enter-from {
  opacity: 0;
  transform: translateY(6px);
}

.route-leave-to {
  opacity: 0;
}

@media (prefers-reduced-motion: reduce) {
  .route-enter-active,
  .route-leave-active {
    transition: none;
  }
}
</style>
