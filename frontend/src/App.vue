<script setup lang="ts">
import { computed, onErrorCaptured, ref, watch } from 'vue'
import { useRoute, type RouteLocationNormalizedLoaded } from 'vue-router'

import AppHeader from '@/components/AppHeader.vue'
import MobileTabBar from '@/components/MobileTabBar.vue'
import SiteFooter from '@/components/SiteFooter.vue'
import GlobalStatus from '@/components/ui/GlobalStatus.vue'
import PageSkeleton from '@/components/ui/PageSkeleton.vue'
import RouteProgress from '@/components/ui/RouteProgress.vue'
import ScrollToTop from '@/components/ui/ScrollToTop.vue'
import { isFatalRenderError } from '@/utils/render-error'
import ServerErrorView from '@/views/ServerErrorView.vue'

const route = useRoute()

// Trang đang chờ dựng lần đầu (kiểm tra đăng nhập, tải mã trang): hiện khung xương thay vì màn hình trắng.
const awaitingFirstRoute = computed(() => route.matched.length === 0)

// Lỗi khi dựng giao diện một trang: thay bằng trang lỗi chung, rời trang thì tự gỡ.
const renderError = ref(false)
onErrorCaptured((error, _instance, info) => {
  if (!isFatalRenderError(info)) return true
  console.error(error)
  renderError.value = true
  return false
})
watch(() => route.fullPath, () => {
  renderError.value = false
})

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
  <RouteProgress />
  <GlobalStatus />
  <AppHeader
    v-if="route.meta.layout !== 'auth' && route.meta.layout !== 'admin' && route.meta.layout !== 'subject'"
  />
  <!-- Trang công khai luôn cao tối thiểu một màn hình để chân trang không nhảy xuống khi nội dung tải xong. -->
  <div :class="{ 'route-slot--public': isPublicLayout }">
    <ServerErrorView v-if="renderError" />
    <PageSkeleton v-else-if="awaitingFirstRoute" />
    <RouterView v-else v-slot="{ Component, route: currentRoute }">
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
