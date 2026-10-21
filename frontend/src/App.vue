<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, type RouteLocationNormalizedLoaded } from 'vue-router'

import AppHeader from '@/components/AppHeader.vue'
import MobileTabBar from '@/components/MobileTabBar.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import ScrollToTop from '@/components/ui/ScrollToTop.vue'

const route = useRoute()

const isPublicLayout = computed(
  () => route.meta.layout !== 'auth' && route.meta.layout !== 'admin' && route.meta.layout !== 'subject',
)

// Khu quản trị và chủ thể giữ nguyên khung (thanh bên, đầu trang) khi đổi trang con;
// chỉ phần nội dung bên trong chuyển cảnh. Trang công khai vẫn dựng lại theo đường dẫn.
function routeKey(current: RouteLocationNormalizedLoaded): string {
  const layout = current.meta.layout
  if ((layout === 'admin' || layout === 'subject') && current.matched[0]) return current.matched[0].path
  return current.path
}
</script>

<template>
  <AppHeader
    v-if="route.meta.layout !== 'auth' && route.meta.layout !== 'admin' && route.meta.layout !== 'subject'"
  />
  <!-- Trang công khai luôn cao tối thiểu một màn hình để chân trang không nhảy xuống khi nội dung tải xong. -->
  <div :class="{ 'route-slot--public': isPublicLayout }">
    <RouterView v-slot="{ Component, route: currentRoute }">
      <Transition name="route" mode="out-in">
        <component :is="Component" :key="routeKey(currentRoute)" />
      </Transition>
    </RouterView>
  </div>
  <SiteFooter
    v-if="route.meta.layout !== 'auth' && route.meta.layout !== 'admin' && route.meta.layout !== 'subject'"
  />
  <ScrollToTop
    v-if="route.meta.layout !== 'auth' && route.meta.layout !== 'admin' && route.meta.layout !== 'subject'"
  />
  <MobileTabBar
    v-if="route.meta.layout !== 'auth' && route.meta.layout !== 'admin' && route.meta.layout !== 'subject'"
  />
</template>

<style>
.route-slot--public {
  min-height: 100vh;
  min-height: 100svh;
}

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
