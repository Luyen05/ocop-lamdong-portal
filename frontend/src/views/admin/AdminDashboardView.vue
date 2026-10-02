<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import StatChart, { type StatChartItem } from '@/components/admin/StatChart.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import {
  getAdminDashboard,
  getAdminStatistics,
  type AdminDashboardStats,
  type AdminStatistics,
} from '@/services/admin'
import { getApiErrorMessage } from '@/services/api-error'
import { authStore } from '@/stores/auth'
import { categoryTheme } from '@/utils/category'
import { locationTypeStyle } from '@/utils/location'

const greetingName = computed(() => authStore.currentUser.value?.full_name || 'Quản trị viên')

const stats = ref<AdminDashboardStats | null>(null)
const loading = ref(true)
const errorMessage = ref('')

const statistics = ref<AdminStatistics | null>(null)
const statisticsLoading = ref(true)
const statisticsError = ref('')

// Hàng đợi việc cần làm (pattern: task queue / inbox) đặt lên đầu, thống kê xếp sau.
const tasks = computed(() => [
  {
    title: 'Sản phẩm mới chờ duyệt',
    description: 'Đối chiếu chứng nhận rồi quyết định công khai hay trả lại.',
    count: stats.value?.pending_products ?? 0,
    to: '/quan-tri/san-pham',
  },
  {
    title: 'Yêu cầu sửa hoặc ngừng hiển thị sản phẩm',
    description: 'So sánh dữ liệu cũ và mới theo đề nghị của chủ thể.',
    count: stats.value?.pending_change_requests ?? 0,
    to: '/quan-tri/san-pham',
  },
  {
    title: 'Điểm du lịch chờ duyệt',
    description: 'Kiểm tra ghim trên bản đồ, địa chỉ và ảnh chụp tại điểm.',
    count: stats.value?.pending_locations ?? 0,
    to: '/quan-tri/diem-du-lich',
  },
  {
    title: 'Yêu cầu sửa hoặc ngừng hiển thị điểm',
    description: 'Đối chiếu thông tin đang hiển thị với đề xuất của chủ thể.',
    count: stats.value?.pending_location_change_requests ?? 0,
    to: '/quan-tri/diem-du-lich?tab=requests',
  },
  {
    title: 'Hồ sơ chủ thể chờ xác minh',
    description: 'Xác minh HTX, doanh nghiệp trước khi cấp quyền đăng sản phẩm.',
    count: stats.value?.pending_subject_applications ?? 0,
    to: '/quan-tri/ho-so-chu-the',
  },
])

const openTaskCount = computed(() => tasks.value.reduce((sum, task) => sum + task.count, 0))

function share(part: number, whole: number): number {
  return whole ? Math.round((part / whole) * 100) : 0
}

const approvedShare = computed(() => share(stats.value?.approved_products ?? 0, stats.value?.total_products ?? 0))
const missingDecisionShare = computed(() =>
  share(stats.value?.products_missing_decision ?? 0, stats.value?.total_products ?? 0),
)

const todayLabel = new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date())

// ---------- Thống kê ----------
const STATUS_META: Record<string, { label: string; color: string }> = {
  approved: { label: 'Đã duyệt', color: 'var(--ocop-success)' },
  pending: { label: 'Chờ duyệt', color: 'var(--ocop-info)' },
  needs_revision: { label: 'Cần bổ sung', color: 'var(--ocop-warning)' },
  rejected: { label: 'Bị từ chối', color: 'var(--ocop-danger)' },
  draft: { label: 'Bản nháp', color: 'var(--ocop-mist-500)' },
}
const STATUS_ORDER = Object.keys(STATUS_META)

const STAR_COLORS: Record<number, string> = {
  3: 'var(--ocop-daquy-600)',
  4: 'var(--ocop-daquy-700)',
  5: 'var(--ocop-daquy-800)',
}

const LOCATION_LABELS: Record<string, string> = {
  tea_coffee_farm: 'Đồi chè, cà phê',
  fruit_garden: 'Vườn cây ăn trái',
  flower_garden: 'Vườn hoa',
  dairy_farm: 'Trang trại bò sữa',
  vegetable_farm: 'Nông trại rau',
  craft_village: 'Làng nghề',
  farmstay: 'Farmstay',
  other: 'Loại hình khác',
}

function capitalize(text: string): string {
  return text ? text.charAt(0).toUpperCase() + text.slice(1) : text
}

function percentText(part: number, whole: number): string {
  if (!whole) return '0%'
  return `${(Math.round((part / whole) * 1000) / 10).toLocaleString('vi-VN')}%`
}

const statusTotal = computed(() => statistics.value?.products_by_status.reduce((sum, item) => sum + item.count, 0) ?? 0)

const statusItems = computed<(StatChartItem & { share: string })[]>(() =>
  [...(statistics.value?.products_by_status ?? [])]
    .sort((a, b) => {
      const ia = STATUS_ORDER.indexOf(a.key)
      const ib = STATUS_ORDER.indexOf(b.key)
      return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib)
    })
    .map((item) => ({
      label: STATUS_META[item.key]?.label ?? item.key,
      value: item.count,
      color: STATUS_META[item.key]?.color ?? 'var(--ocop-mist-400)',
      share: percentText(item.count, statusTotal.value),
    })),
)

const approvedStatusCount = computed(
  () => statistics.value?.products_by_status.find((item) => item.key === 'approved')?.count ?? 0,
)

const publicTotal = computed(() => statistics.value?.approved_by_star.reduce((sum, item) => sum + item.count, 0) ?? 0)

const starItems = computed<StatChartItem[]>(() =>
  (statistics.value?.approved_by_star ?? []).map((item) => ({
    label: `${item.star} sao`,
    fullLabel: `${item.star} sao (${percentText(item.count, publicTotal.value)})`,
    value: item.count,
    color: STAR_COLORS[item.star] ?? 'var(--ocop-mist-600)',
  })),
)

const categoryItems = computed<StatChartItem[]>(() =>
  (statistics.value?.approved_by_category ?? []).map((item) => ({
    label: item.name,
    value: item.count,
    color: categoryTheme(item.slug).foreground,
  })),
)

const emptyCategoryCount = computed(
  () => statistics.value?.approved_by_category.filter((item) => item.count === 0).length ?? 0,
)

const districtItems = computed<StatChartItem[]>(() =>
  (statistics.value?.approved_by_district ?? []).map((item, index) => ({
    label: capitalize(item.district),
    value: item.count,
    color: index < 3 ? 'var(--ocop-tone-sky)' : 'var(--ocop-blue-300)',
  })),
)

function monthParts(value: string): { month: number; year: number } {
  const [year, month] = value.split('-').map(Number)
  return { month: month ?? 0, year: year ?? 0 }
}

const monthItems = computed<StatChartItem[]>(() =>
  (statistics.value?.approved_by_month ?? []).map((item) => {
    const { month, year } = monthParts(item.month)
    return {
      label: `T${month}/${String(year).slice(2)}`,
      fullLabel: `Tháng ${month}/${year}`,
      value: item.count,
      color: 'var(--ocop-tone-sky)',
    }
  }),
)

const monthRange = computed(() => {
  const months = monthItems.value
  if (!months.length) return ''
  return `${months[0]?.fullLabel} đến ${months[months.length - 1]?.fullLabel?.toLowerCase()}`
})

const certYearItems = computed<StatChartItem[]>(() =>
  (statistics.value?.certificates.by_year ?? []).map((item) => ({
    label: String(item.year),
    fullLabel: `Năm ${item.year}`,
    value: item.count,
    color: 'var(--ocop-tone-sky)',
  })),
)

const locationItems = computed<StatChartItem[]>(() =>
  (statistics.value?.locations_by_type ?? []).map((item) => ({
    label: LOCATION_LABELS[item.key] ?? item.key,
    value: item.count,
    color: locationTypeStyle(item.key).color,
  })),
)

const locationTotal = computed(() => locationItems.value.reduce((sum, item) => sum + item.value, 0))
const approvedSubjects = computed(
  () => statistics.value?.subjects_by_status.find((item) => item.key === 'approved')?.count ?? 0,
)

function describe(items: StatChartItem[], unit = 'sản phẩm'): string {
  return items.map((item) => `${item.fullLabel ?? item.label}: ${item.value} ${unit}`).join('; ')
}

async function loadDashboard(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    stats.value = await getAdminDashboard()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải việc cần xử lý.')
  } finally {
    loading.value = false
  }
}

async function loadStatistics(): Promise<void> {
  statisticsLoading.value = true
  statisticsError.value = ''
  try {
    statistics.value = await getAdminStatistics()
  } catch (error) {
    statisticsError.value = getApiErrorMessage(error, 'Chưa tải được số liệu thống kê.')
  } finally {
    statisticsLoading.value = false
  }
}

onMounted(() => {
  void loadDashboard()
  void loadStatistics()
})
</script>
<template>
  <div class="dashboard-page">
    <header class="dash-head">
      <div>
        <p class="dash-date">{{ todayLabel }}</p>
        <h1>Xin chào, {{ greetingName }}</h1>
        <p class="dash-summary" role="status">
          <template v-if="loading">Đang tải việc cần xử lý...</template>
          <template v-else-if="openTaskCount">Có <strong>{{ openTaskCount }}</strong> việc đang chờ bạn xử lý.</template>
          <template v-else>Không còn việc nào chờ xử lý. Mọi hồ sơ đã được duyệt.</template>
        </p>
      </div>
      <div class="head-actions">
        <a class="dash-btn-ghost" href="#thong-ke"><AppIcon name="barChart" :size="15" /> Xem thống kê</a>
        <RouterLink class="dash-btn-ghost" to="/">Trang công khai <AppIcon name="chevronRight" :size="15" /></RouterLink>
      </div>
    </header>

    <div v-if="errorMessage" class="ad-alert is-error" role="alert">
      <span><AppIcon name="alert" :size="16" /> {{ errorMessage }}</span>
      <button class="ad-btn-primary" type="button" @click="loadDashboard">Thử lại</button>
    </div>

    <section class="top-grid" aria-label="Việc cần xử lý và số liệu chính">
      <div class="ad-card task-panel">
        <div class="card-head">
          <div class="card-head__title">
            <span class="card-icon" aria-hidden="true"><AppIcon name="checkCircle" :size="18" /></span>
            <h2>Việc cần xử lý</h2>
          </div>
          <span class="task-count-badge">{{ loading ? '...' : `${openTaskCount} việc` }}</span>
        </div>
        <ul class="task-list">
          <li v-for="task in tasks" :key="task.title">
            <RouterLink class="task-item" :class="{ 'is-open': task.count > 0 }" :to="task.to">
              <span class="task-num">{{ loading ? '–' : task.count }}</span>
              <span class="task-body">
                <strong>{{ task.title }}</strong>
                <span>{{ task.description }}</span>
              </span>
              <span class="task-arrow"><AppIcon name="chevronRight" :size="14" /></span>
            </RouterLink>
          </li>
        </ul>
      </div>

      <div class="kpi-grid">
        <article class="ad-card kpi-card">
          <div class="kpi-icon-wrap is-primary">
            <AppIcon name="package" :size="20" />
          </div>
          <span class="kpi-label">Tổng sản phẩm</span>
          <strong class="kpi-value">{{ loading ? '–' : (stats?.total_products ?? 0) }}</strong>
          <div class="kpi-meter"><div class="kpi-meter__fill" :style="{ width: `${approvedShare}%` }" /></div>
          <span class="kpi-note">{{ stats?.approved_products ?? 0 }} đang công khai ({{ approvedShare }}%)</span>
        </article>
        <article class="ad-card kpi-card">
          <div class="kpi-icon-wrap is-success">
            <AppIcon name="building" :size="20" />
          </div>
          <span class="kpi-label">Chủ thể đã duyệt</span>
          <strong class="kpi-value">{{ statisticsLoading ? '–' : approvedSubjects }}</strong>
          <span class="kpi-note">{{ stats?.pending_subject_applications ?? 0 }} hồ sơ chờ xác minh</span>
        </article>
        <article class="ad-card kpi-card">
          <div class="kpi-icon-wrap is-accent">
            <AppIcon name="map-pin" :size="20" />
          </div>
          <span class="kpi-label">Điểm du lịch</span>
          <strong class="kpi-value">{{ statisticsLoading ? '–' : locationTotal }}</strong>
          <span class="kpi-note">{{ locationItems.length }} loại hình trên bản đồ</span>
        </article>
        <article class="ad-card kpi-card" :class="{ 'is-warning': (stats?.products_missing_decision ?? 0) > 0 }">
          <div class="kpi-icon-wrap" :class="(stats?.products_missing_decision ?? 0) > 0 ? 'is-warning' : 'is-neutral'">
            <AppIcon name="alert" :size="20" />
          </div>
          <span class="kpi-label">Thiếu số quyết định</span>
          <strong class="kpi-value">{{ loading ? '–' : (stats?.products_missing_decision ?? 0) }}</strong>
          <RouterLink class="kpi-link" to="/quan-tri/san-pham">Bổ sung ngay <AppIcon name="chevronRight" :size="12" /></RouterLink>
        </article>
      </div>
    </section>

    <section id="thong-ke" class="stats-section" aria-labelledby="stats-products-title">
      <div class="section-head">
        <div>
          <span class="card-eyebrow">THỐNG KÊ</span>
          <h2 id="stats-products-title">Sản phẩm OCOP</h2>
        </div>
        <span class="section-note">Số liệu toàn tỉnh, tính đến lúc mở trang</span>
      </div>
      <div v-if="statisticsError" class="ad-alert is-error" role="alert">
        <span><AppIcon name="alert" :size="16" /> {{ statisticsError }}</span>
        <button class="ad-btn-primary" type="button" @click="loadStatistics">Thử lại</button>
      </div>
      <div v-else-if="statisticsLoading" class="chart-grid" aria-busy="true">
        <div class="skeleton span-2" /><div class="skeleton" /><div class="skeleton" /><div class="skeleton span-2" />
        <span class="visually-hidden" role="status">Đang tải số liệu thống kê...</span>
      </div>
      <div v-else-if="statistics" class="chart-grid">
        <StatChart class="span-2" kind="stacked" title="Trạng thái hồ sơ sản phẩm" :description="`${statusTotal} hồ sơ, gồm cả bản nháp của chủ thể`" :items="statusItems" :summary="describe(statusItems, 'hồ sơ')" unit="hồ sơ" :height="40">
          <template #lead>
            <p class="lead-figure"><strong>{{ percentText(approvedStatusCount, statusTotal) }}</strong> hồ sơ đã được duyệt và đang hiển thị công khai</p>
          </template>
          <ul class="status-legend">
            <li v-for="item in statusItems" :key="item.label">
              <span class="legend-label"><span class="dot" :style="{ background: item.color }" />{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <span class="legend-share">{{ item.share }}</span>
            </li>
          </ul>
        </StatChart>
        <StatChart title="Hạng sao OCOP" :description="`${publicTotal} sản phẩm đang công khai`" :items="starItems" :summary="describe(starItems)" :height="240" />
        <StatChart kind="bar" title="Theo nhóm sản phẩm" description="Màu trùng với chip nhóm ở trang công khai" :items="categoryItems" :summary="describe(categoryItems)" :height="Math.max(200, categoryItems.length * 36)">
          <p v-if="emptyCategoryCount" class="note">{{ emptyCategoryCount }} nhóm chưa có sản phẩm được duyệt.</p>
        </StatChart>
        <StatChart class="span-2" kind="bar" :title="`${districtItems.length} xã, phường có nhiều sản phẩm nhất`" description="Theo địa bàn của chủ thể, chỉ tính sản phẩm đang công khai" :items="districtItems" :summary="describe(districtItems)" :height="Math.max(200, districtItems.length * 34)" />
        <StatChart class="span-2" title="Sản phẩm được duyệt theo tháng" :description="monthItems.length ? `Theo ngày duyệt, ${monthRange}` : 'Chưa có sản phẩm nào được duyệt'" :items="monthItems" :summary="describe(monthItems.filter((item) => item.value > 0)) || 'Chưa có sản phẩm nào được duyệt'" :height="260">
          <p v-if="statistics.approved_without_review_date" class="note">{{ statistics.approved_without_review_date }} sản phẩm nhập sẵn không có ngày duyệt nên không nằm trong biểu đồ.</p>
        </StatChart>
        <StatChart kind="bar" title="Giấy chứng nhận OCOP" description="Số sản phẩm theo năm được công nhận" :items="certYearItems" :summary="describe(certYearItems)" :height="Math.max(140, certYearItems.length * 34)">
          <template #lead>
            <div class="cert-tiles">
              <RouterLink class="cert-tile" :class="{ 'is-danger': statistics.certificates.expired > 0 }" to="/quan-tri/san-pham">
                <span>Đã hết hạn</span>
                <strong>{{ statistics.certificates.expired }}</strong>
                <span class="tile-cta">Xem sản phẩm <AppIcon name="chevronRight" :size="12" /></span>
              </RouterLink>
              <div class="cert-tile">
                <span>Hết hạn trong {{ statistics.certificates.expiring_window_days }} ngày</span>
                <strong>{{ statistics.certificates.expiring_soon }}</strong>
                <span class="tile-note">{{ statistics.certificates.expiring_soon ? 'Nên nhắc chủ thể gia hạn' : 'Chưa có sản phẩm nào' }}</span>
              </div>
            </div>
          </template>
        </StatChart>
      </div>
    </section>

    <section v-if="statistics && !statisticsLoading && !statisticsError" class="stats-section" aria-labelledby="stats-interest-title">
      <div class="section-head">
        <div>
          <span class="card-eyebrow">THỐNG KÊ</span>
          <h2 id="stats-interest-title">Mức độ quan tâm và du lịch</h2>
        </div>
      </div>
      <div class="chart-grid">
        <article class="span-2 ad-card plain-card">
          <div class="plain-head">
            <h3>Sản phẩm được xem nhiều nhất</h3>
            <p>Lượt mở trang chi tiết sản phẩm</p>
          </div>
          <ol v-if="statistics.top_viewed_products.length" class="viewed-list">
            <li v-for="(product, index) in statistics.top_viewed_products" :key="product.id">
              <span class="rank">{{ index + 1 }}</span>
              <RouterLink :to="`/san-pham/${product.slug}`">{{ product.name }}</RouterLink>
              <strong>{{ product.views.toLocaleString('vi-VN') }} lượt</strong>
            </li>
          </ol>
          <div v-else class="empty-box">
            <span class="empty-icon" aria-hidden="true"><AppIcon name="eye" :size="24" /></span>
            <strong>Chưa ghi nhận lượt xem nào</strong>
            <p>Bảng xếp hạng sẽ hiện khi người dân bắt đầu mở trang chi tiết sản phẩm.</p>
          </div>
        </article>
        <StatChart kind="bar" title="Điểm du lịch theo loại hình" :description="`${locationTotal} điểm đang hiển thị trên bản đồ số`" :items="locationItems" :summary="describe(locationItems, 'điểm')" unit="điểm" :height="Math.max(160, locationItems.length * 40)" />
      </div>
    </section>
  </div>
</template>

<style scoped>
.dashboard-page { display: grid; gap: var(--admin-space-8); font-family: var(--admin-font); }
.dash-head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--admin-space-4); flex-wrap: wrap; }
.dash-date { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); text-transform: capitalize; }
.dash-head h1 { margin: 4px 0 6px; color: var(--admin-text); font-size: 1.75rem; font-weight: 800; }
.dash-summary { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-base); }
.dash-summary strong { display: inline-flex; align-items: center; padding: 2px 10px; border-radius: var(--admin-radius-pill); background: var(--admin-primary); color: var(--admin-on-primary); font-weight: 700; }
.head-actions { display: flex; gap: var(--admin-space-2); flex-wrap: wrap; }
.dash-btn-ghost { display: inline-flex; align-items: center; gap: 5px; padding: 8px 14px; border: 1px solid var(--admin-border); border-radius: var(--admin-radius-sm); background: var(--admin-card); color: var(--admin-text); font-size: var(--admin-font-sm); font-weight: 600; text-decoration: none; transition: background var(--admin-transition), border-color var(--admin-transition); }
.dash-btn-ghost:hover { border-color: var(--admin-primary); background: var(--admin-primary-soft); color: var(--admin-primary); }
.ad-alert { display: flex; align-items: center; justify-content: space-between; gap: var(--admin-space-3); padding: var(--admin-space-4); border-radius: var(--admin-radius-md); font-size: var(--admin-font-sm); }
.ad-alert.is-error { background: var(--admin-danger-soft); color: var(--admin-danger-text); border: 1px solid var(--admin-danger-border); }
.ad-btn-primary { padding: 7px 14px; border: 0; border-radius: var(--admin-radius-sm); background: var(--admin-primary); color: var(--admin-on-primary); font-size: var(--admin-font-sm); font-weight: 700; cursor: pointer; white-space: nowrap; }
.ad-card { background: var(--admin-card); border: 1px solid var(--admin-border); border-radius: var(--admin-radius-lg); box-shadow: var(--admin-shadow-card); }
.top-grid { display: grid; grid-template-columns: minmax(0, 6fr) minmax(0, 4fr); gap: var(--admin-space-5); }
.task-panel { padding: var(--admin-space-6); }
.card-head { display: flex; align-items: center; justify-content: space-between; gap: var(--admin-space-3); margin-bottom: var(--admin-space-5); }
.card-head__title { display: flex; align-items: center; gap: var(--admin-space-3); }
.card-icon { display: grid; width: 36px; height: 36px; place-items: center; border-radius: var(--admin-radius-md); background: var(--admin-primary-soft); color: var(--admin-primary); }
.card-eyebrow { font-size: var(--admin-font-xs); font-weight: 800; letter-spacing: 0.08em; color: var(--admin-primary); text-transform: uppercase; }
.card-head h2 { margin: 0; font-size: var(--admin-font-sm); font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; color: var(--admin-text); }
.task-count-badge { padding: 4px 12px; border-radius: var(--admin-radius-pill); background: var(--admin-primary-soft); color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 700; white-space: nowrap; }
.task-list { margin: 0; padding: 0; list-style: none; display: grid; gap: 6px; }
.task-item { display: grid; grid-template-columns: 48px minmax(0, 1fr) 24px; align-items: center; gap: 12px; padding: 12px; border: 1px solid var(--admin-border-soft); border-radius: var(--admin-radius-md); background: var(--admin-bg); color: var(--admin-text); text-decoration: none; transition: border-color var(--admin-transition), background var(--admin-transition); }
.task-item:hover { border-color: var(--admin-primary); background: var(--admin-primary-soft); }
.task-num { display: grid; width: 48px; height: 48px; place-items: center; border-radius: var(--admin-radius-sm); background: var(--admin-card); border: 1px solid var(--admin-border); color: var(--admin-muted); font-size: 1.125rem; font-weight: 800; }
.task-item.is-open .task-num { background: var(--admin-primary); border-color: var(--admin-primary); color: var(--admin-on-primary); }
.task-body { display: grid; gap: 2px; }
.task-body strong { font-size: var(--admin-font-sm); font-weight: 700; color: var(--admin-text); }
.task-body span { font-size: var(--admin-font-xs); color: var(--admin-muted); line-height: 1.45; }
.task-arrow { color: var(--admin-muted); }
.task-item.is-open .task-arrow { color: var(--admin-primary); }
.kpi-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--admin-space-4); }
.kpi-card { display: flex; flex-direction: column; gap: 6px; padding: var(--admin-space-5); }
.kpi-icon-wrap { display: grid; width: 40px; height: 40px; place-items: center; border-radius: var(--admin-radius-md); margin-bottom: 4px; }
.kpi-icon-wrap.is-primary { background: var(--admin-primary-soft); color: var(--admin-primary); }
.kpi-icon-wrap.is-success { background: var(--admin-success-soft); color: var(--admin-success-text); }
.kpi-icon-wrap.is-accent { background: var(--admin-accent-soft); color: var(--admin-accent-text); }
.kpi-icon-wrap.is-warning { background: var(--admin-warning-soft); color: var(--admin-warning-text); }
.kpi-icon-wrap.is-neutral { background: var(--admin-badge-draft-bg); color: var(--admin-badge-draft-text); }
.kpi-label { font-size: var(--admin-font-sm); font-weight: 600; color: var(--admin-muted); }
.kpi-value { font-size: 2rem; font-weight: 800; color: var(--admin-text); line-height: 1.1; letter-spacing: -0.02em; }
.kpi-card.is-warning .kpi-value { color: var(--admin-warning-text); }
.kpi-note { font-size: var(--admin-font-xs); color: var(--admin-muted); margin-top: 2px; }
.kpi-link { display: inline-flex; align-items: center; gap: 3px; margin-top: auto; font-size: var(--admin-font-xs); font-weight: 700; color: var(--admin-warning-text); text-decoration: none; }
.kpi-meter { height: 6px; border-radius: var(--admin-radius-pill); background: var(--admin-bg); overflow: hidden; margin: 2px 0; }
.kpi-meter__fill { height: 100%; border-radius: inherit; background: var(--admin-primary); transition: width 0.4s ease; }
.stats-section { display: grid; gap: var(--admin-space-4); scroll-margin-top: 80px; }
.section-head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--admin-space-3); padding-top: var(--admin-space-4); border-top: 1px solid var(--admin-border); }
.section-head h2 { margin: 2px 0 0; font-size: 1.375rem; font-weight: 750; color: var(--admin-text); }
.section-note { color: var(--admin-muted); font-size: var(--admin-font-sm); }
.chart-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--admin-space-5); }
.span-2 { grid-column: span 2; }
.skeleton { min-height: 280px; border-radius: var(--admin-radius-lg); background: linear-gradient(90deg, var(--admin-bg) 25%, var(--admin-border-soft) 50%, var(--admin-bg) 75%); background-size: 200% 100%; animation: shimmer 1.4s infinite; }
@keyframes shimmer { 0% { background-position: 200% 0; } 100% { background-position: -200% 0; } }
.visually-hidden { position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px; overflow: hidden; clip: rect(0,0,0,0); white-space: nowrap; border: 0; }
.lead-figure { display: flex; flex-wrap: wrap; align-items: baseline; gap: var(--admin-space-2); margin: 0; color: var(--admin-muted); font-size: var(--admin-font-base); }
.lead-figure strong { color: var(--admin-success); font-size: 1.75rem; font-weight: 800; letter-spacing: -0.02em; }
.status-legend { display: grid; grid-template-columns: repeat(auto-fit, minmax(110px, 1fr)); gap: var(--admin-space-2); margin: 0; padding: 0; list-style: none; }
.status-legend li { display: flex; flex-direction: column; gap: 2px; padding: var(--admin-space-3); border-radius: var(--admin-radius-sm); background: var(--admin-bg); }
.legend-label { display: flex; align-items: center; gap: 6px; color: var(--admin-muted); font-size: var(--admin-font-xs); }
.dot { width: 9px; height: 9px; border-radius: 3px; flex-shrink: 0; }
.status-legend strong { font-size: var(--admin-font-xl); font-weight: 800; color: var(--admin-text); }
.legend-share { font-size: var(--admin-font-xs); color: var(--admin-muted); }
.note { margin: 0; padding: var(--admin-space-3); border-radius: var(--admin-radius-sm); background: var(--admin-warning-soft); color: var(--admin-warning-text); font-size: var(--admin-font-sm); }
.cert-tiles { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--admin-space-3); }
.cert-tile { display: flex; flex-direction: column; gap: 4px; padding: var(--admin-space-3); border-radius: var(--admin-radius-md); background: var(--admin-bg); color: var(--admin-muted); font-size: var(--admin-font-sm); text-decoration: none; }
.cert-tile strong { color: var(--admin-text); font-size: 1.5rem; font-weight: 800; }
.cert-tile.is-danger { background: var(--admin-danger-soft); }
.cert-tile.is-danger strong { color: var(--admin-danger-text); }
.tile-cta { display: inline-flex; align-items: center; gap: 3px; font-weight: 700; font-size: var(--admin-font-xs); }
.tile-note { color: var(--admin-muted); font-size: var(--admin-font-xs); }
.plain-card { display: flex; flex-direction: column; gap: var(--admin-space-4); padding: var(--admin-space-5); }
.plain-head h3 { margin: 0; font-size: var(--admin-font-sm); font-weight: 800; letter-spacing: 0.05em; text-transform: uppercase; color: var(--admin-text); }
.plain-head p { margin: 4px 0 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.viewed-list { margin: 0; padding: 0; list-style: none; display: grid; gap: 4px; }
.viewed-list li { display: grid; grid-template-columns: 28px minmax(0, 1fr) auto; align-items: center; gap: var(--admin-space-3); min-height: 44px; padding: 6px 0; border-bottom: 1px solid var(--admin-border-soft); }
.viewed-list li:last-child { border-bottom: 0; }
.rank { color: var(--admin-muted); font-weight: 700; font-size: var(--admin-font-sm); }
.viewed-list a { color: var(--admin-text); font-size: var(--admin-font-sm); text-decoration: none; }
.viewed-list a:hover { color: var(--admin-primary); text-decoration: underline; }
.viewed-list strong { color: var(--admin-muted); font-size: var(--admin-font-sm); white-space: nowrap; }
.empty-box { display: flex; min-height: 200px; flex: 1; flex-direction: column; align-items: center; justify-content: center; gap: var(--admin-space-2); border: 1px dashed var(--admin-border); border-radius: var(--admin-radius-md); background: var(--admin-bg); text-align: center; padding: var(--admin-space-6); }
.empty-box strong { color: var(--admin-text); font-size: var(--admin-font-base); }
.empty-box p { max-width: 400px; margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.empty-icon { display: grid; width: 52px; height: 52px; place-items: center; border-radius: 50%; background: var(--admin-card); border: 1px solid var(--admin-border); color: var(--admin-muted); }
@media (max-width: 1199.98px) { .top-grid { grid-template-columns: 1fr; } .chart-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 767.98px) { .dash-head, .section-head { flex-direction: column; align-items: flex-start; } .chart-grid { grid-template-columns: 1fr; } .kpi-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--admin-space-3); } .span-2 { grid-column: auto; } .task-body span { display: none; } }
@media (max-width: 480px) { .kpi-grid { grid-template-columns: 1fr; } }
</style>