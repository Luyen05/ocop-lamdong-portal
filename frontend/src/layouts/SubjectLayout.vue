<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'

import PortalShell, { type PortalNavItem } from '@/layouts/PortalShell.vue'

const route = useRoute()

const navItems: PortalNavItem[] = [
  { label: 'Sản phẩm', icon: 'package', to: '/chu-the/san-pham' },
  { label: 'Điểm du lịch', icon: 'map-pin', to: '/chu-the/diem-du-lich' },
  { label: 'Hồ sơ đơn vị', icon: 'building', to: '/chu-the/ho-so' },
]

const titles: Record<string, string> = {
  'subject-product-create': 'Thêm sản phẩm',
  'subject-product-edit': 'Chỉnh sửa sản phẩm',
  'subject-product-request-edit': 'Yêu cầu chỉnh sửa sản phẩm',
}

const subtitles: Record<string, string> = {
  'subject-profile': 'Thông tin và trạng thái hồ sơ đơn vị',
  'subject-products': 'Quản lý sản phẩm OCOP của đơn vị',
  'subject-product-create': 'Soạn sản phẩm mới và gửi duyệt',
  'subject-product-edit': 'Cập nhật thông tin sản phẩm',
  'subject-product-request-edit': 'Bổ sung yêu cầu chỉnh sửa gửi quản trị viên',
  'subject-locations': 'Quản lý điểm du lịch của đơn vị',
  'subject-location-create': 'Khai báo điểm du lịch mới',
  'subject-location-request-edit': 'Bổ sung yêu cầu cập nhật điểm',
  'subject-location-edit': 'Hồ sơ điểm du lịch',
}

const pageTitle = computed(() => {
  if (typeof route.meta.title === 'string') return route.meta.title
  return titles[String(route.name)] ?? 'Cổng chủ thể'
})
const pageSubtitle = computed(() => subtitles[String(route.name)] ?? '')
</script>

<template>
  <PortalShell
    brand-title="LÂM ĐỒNG OCOP"
    brand-subtitle="Cổng chủ thể"
    brand-to="/chu-the/san-pham"
    nav-label="Điều hướng chủ thể"
    :nav-items="navItems"
    role-label="Chủ thể"
    profile-to="/chu-the/ho-so"
    :page-title="pageTitle"
    :page-subtitle="pageSubtitle"
  >
    <RouterView />
  </PortalShell>
</template>
