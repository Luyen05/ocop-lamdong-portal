<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import ErrorPage from '@/components/ui/ErrorPage.vue'
import { authStore } from '@/stores/auth'

const route = useRoute()
const router = useRouter()
const keyword = ref('')

// Địa chỉ đã gõ: hiện lại để người dùng nhận ra gõ sai hay liên kết cũ.
const requestedPath = computed(() => {
  try {
    return decodeURI(route.fullPath).slice(0, 120)
  } catch {
    return route.fullPath.slice(0, 120)
  }
})

// Khu quản trị và chủ thể: đưa về đúng khu của mình thay vì chỉ về trang công khai.
const areaLink = computed(() => {
  const role = authStore.currentUser.value?.role
  if (role === 'admin' && route.path.startsWith('/quan-tri')) return { to: '/quan-tri', label: 'Về trang quản trị' }
  if (role === 'subject' && route.path.startsWith('/chu-the')) return { to: '/chu-the/san-pham', label: 'Về khu chủ thể' }
  return null
})

const canGoBack = computed(() => typeof window !== 'undefined' && window.history.length > 1)

function goBack(): void {
  router.back()
}

function search(): void {
  const text = keyword.value.trim()
  if (text) void router.push({ name: 'products', query: { search: text } })
}
</script>

<template>
  <ErrorPage code="404" title="Không tìm thấy trang" title-id="not-found-title">
    <p>Địa chỉ bạn mở không tồn tại hoặc nội dung đã được chuyển sang vị trí khác.</p>
    <p class="requested-path" data-testid="requested-path"><code>{{ requestedPath }}</code></p>
    <template #actions>
      <RouterLink v-if="areaLink" class="primary-action" :to="areaLink.to">{{ areaLink.label }}</RouterLink>
      <RouterLink :class="{ 'primary-action': !areaLink }" to="/">Về trang chủ</RouterLink>
      <RouterLink to="/san-pham">Xem sản phẩm OCOP</RouterLink>
      <button v-if="canGoBack" type="button" @click="goBack">
        <AppIcon name="arrowLeft" :size="14" /> Quay lại
      </button>
    </template>
    <template #extra>
      <form class="not-found-search" role="search" @submit.prevent="search">
        <label class="visually-hidden" for="not-found-search">Tìm sản phẩm OCOP</label>
        <input
          id="not-found-search"
          v-model="keyword"
          type="search"
          placeholder="Hoặc tìm sản phẩm: atiso, cà phê, mắc ca…"
          autocomplete="off"
        />
        <button type="submit"><AppIcon name="search" :size="16" /> Tìm</button>
      </form>
    </template>
  </ErrorPage>
</template>

<style scoped>
.requested-path {
  margin-top: var(--ocop-space-2);
  font-size: var(--ocop-font-size-small);
  overflow-wrap: anywhere;
}

.requested-path code {
  padding: 2px 8px;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-mist-100);
  color: var(--ocop-mist-950);
}

.not-found-search {
  display: flex;
  gap: var(--ocop-space-2);
}

.not-found-search input {
  min-width: 0;
  flex: 1;
  min-height: var(--ocop-control-md);
  padding: 0 var(--ocop-space-3);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
}

.not-found-search button {
  display: inline-flex;
  align-items: center;
  gap: var(--ocop-space-1);
  padding: 0 var(--ocop-space-4);
  border: 0;
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-accent);
  color: var(--ocop-navy);
  font-weight: 700;
}
</style>
