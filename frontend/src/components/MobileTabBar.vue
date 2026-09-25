<script setup lang="ts">
import { onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'

// Bottom navigation (tab bar) trên điện thoại: 5 điểm đến ngang hàng, dùng lại các trang sẵn có.
const tabs = [
  { label: 'Trang chủ', to: '/', icon: 'home' },
  { label: 'Sản phẩm', to: '/san-pham', icon: 'package' },
  { label: 'Điểm du lịch', to: '/diem-du-lich', icon: 'map-pin' },
  { label: 'Bản đồ', to: '/ban-do', icon: 'map' },
  { label: 'Tin tức', to: '/tin-tuc', icon: 'newspaper' },
]

const route = useRoute()

// Trang chi tiết (vd /san-pham/:slug) vẫn sáng mục cha tương ứng.
function isActive(to: string): boolean {
  return to === '/' ? route.path === '/' : route.path === to || route.path.startsWith(`${to}/`)
}

// Chừa chỗ cuối trang để thanh không che nội dung (chỉ có tác dụng dưới 768px, xem main.css).
onMounted(() => document.body.classList.add('has-tabbar'))
onBeforeUnmount(() => document.body.classList.remove('has-tabbar'))
</script>

<template>
  <nav class="mobile-tabbar" aria-label="Điều hướng nhanh">
    <RouterLink v-for="tab in tabs" :key="tab.to" :to="tab.to" class="tab-item" :class="{ 'is-active': isActive(tab.to) }">
      <span class="tab-icon" aria-hidden="true"><AppIcon :name="tab.icon" :size="20" /></span>
      <span class="tab-label">{{ tab.label }}</span>
    </RouterLink>
  </nav>
</template>

<style scoped>
.mobile-tabbar {
  display: none;
}

@media (max-width: 767.98px) {
  .mobile-tabbar {
    position: fixed;
    z-index: 95;
    right: 0;
    bottom: 0;
    left: 0;
    display: grid;
    min-height: var(--ocop-tabbar-height);
    padding: var(--ocop-space-1) var(--ocop-space-2) env(safe-area-inset-bottom);
    grid-template-columns: repeat(5, minmax(0, 1fr));
    border-top: 1px solid var(--ocop-border);
    background: var(--ocop-glass-bg-solid);
    box-shadow: 0 -6px 20px color-mix(in srgb, var(--ocop-mist-950) 10%, transparent);
    backdrop-filter: blur(var(--ocop-glass-blur));
  }

  .tab-item {
    display: flex;
    min-height: 56px;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 2px;
    color: var(--ocop-mist-600);
    font-size: var(--ocop-font-size-caption);
    font-weight: 600;
    text-decoration: none;
  }

  .tab-icon {
    display: grid;
    width: 48px;
    height: 28px;
    place-items: center;
    border-radius: var(--ocop-radius-pill);
    transition: background var(--ocop-transition), color var(--ocop-transition);
  }

  /* Mục đang mở: nền vàng dã quỳ quanh icon và chữ đậm, không chỉ đổi màu. */
  .tab-item.is-active {
    color: var(--ocop-mist-950);
    font-weight: 750;
  }

  .tab-item.is-active .tab-icon {
    background: var(--ocop-daquy-400);
  }
}
</style>
