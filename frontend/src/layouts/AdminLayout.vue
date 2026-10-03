<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import PortalShell, { type PortalNavItem, type PortalNotification } from '@/layouts/PortalShell.vue'
import { getAdminDashboard, type AdminDashboardStats } from '@/services/admin'

const route = useRoute()

const navItems: PortalNavItem[] = [
  { label: 'Tổng quan', icon: 'dashboard', to: '/quan-tri', exact: true },
  { label: 'Sản phẩm', icon: 'package', to: '/quan-tri/san-pham' },
  { label: 'Điểm du lịch', icon: 'map-pin', to: '/quan-tri/diem-du-lich' },
  { label: 'Chủ thể / HTX', icon: 'building', to: '/quan-tri/ho-so-chu-the' },
]

const subtitles: Record<string, string> = {
  'admin-dashboard': 'Việc cần xử lý và số liệu toàn hệ thống',
  'admin-products': 'Duyệt sản phẩm và yêu cầu chỉnh sửa',
  'admin-subject-applications': 'Duyệt hồ sơ đơn vị đăng ký chủ thể',
  'admin-locations': 'Duyệt điểm du lịch và yêu cầu cập nhật',
}

const pageTitle = computed(() =>
  typeof route.meta.title === 'string' ? route.meta.title : 'Tổng quan quản trị',
)
const pageSubtitle = computed(() => subtitles[String(route.name)] ?? '')

// Chuông chỉ hiện khi đã lấy được số việc chờ xử lý thật từ GET /admin/dashboard.
const stats = ref<AdminDashboardStats | null>(null)

const notifications = computed<PortalNotification[] | null>(() => {
  if (!stats.value) return null
  return [
    { key: 'subjects', label: 'Hồ sơ chủ thể chờ duyệt', count: stats.value.pending_subject_applications, to: '/quan-tri/ho-so-chu-the' },
    { key: 'products', label: 'Sản phẩm chờ duyệt', count: stats.value.pending_products, to: '/quan-tri/san-pham' },
    { key: 'product-changes', label: 'Yêu cầu chỉnh sửa sản phẩm', count: stats.value.pending_change_requests, to: '/quan-tri/san-pham' },
    { key: 'locations', label: 'Điểm du lịch chờ duyệt', count: stats.value.pending_locations, to: '/quan-tri/diem-du-lich' },
    { key: 'location-changes', label: 'Yêu cầu cập nhật điểm', count: stats.value.pending_location_change_requests, to: '/quan-tri/diem-du-lich' },
  ]
})

async function loadNotifications(): Promise<void> {
  try {
    stats.value = await getAdminDashboard()
  } catch {
    stats.value = null
  }
}

onMounted(loadNotifications)
watch(() => route.fullPath, loadNotifications)
</script>

<template>
  <PortalShell
    brand-title="LÂM ĐỒNG OCOP"
    brand-subtitle="Khu vực quản trị"
    brand-to="/quan-tri"
    nav-label="Điều hướng quản trị"
    :nav-items="navItems"
    role-label="Quản trị viên"
    profile-to="/tai-khoan"
    :page-title="pageTitle"
    :page-subtitle="pageSubtitle"
    :notifications="notifications"
  >
    <RouterView />
  </PortalShell>
</template>
