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
    title: 'Yêu cầu sửa hoặc ngừng hiển thị',
    description: 'So sánh dữ liệu cũ và mới theo đề nghị của chủ thể.',
    count: stats.value?.pending_change_requests ?? 0,
    to: '/quan-tri/san-pham',
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
  5: 'var(--ocop-mist-900)',
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
    color: index < 3 ? 'var(--ocop-mist-700)' : 'var(--ocop-mist-500)',
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
      color: 'var(--ocop-mist-700)',
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
    color: 'var(--ocop-mist-600)',
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
  <main class="dashboard-page">
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
        <a class="ocop-btn-ghost" href="#thong-ke"><AppIcon name="barChart" :size="16" /> Xem thống kê</a>
        <RouterLink class="ocop-btn-ghost" to="/">Xem trang công khai <AppIcon name="chevronRight" :size="16" /></RouterLink>
      </div>
    </header>

    <div v-if="errorMessage" class="state-box is-error" role="alert">
      <span>{{ errorMessage }}</span>
      <button class="ocop-btn-main" type="button" @click="loadDashboard">Thử lại</button>
    </div>

    <section class="top-grid" aria-label="Việc cần xử lý và số liệu chính">
      <div class="task-panel">
        <div class="panel-head">
          <h2 id="task-title">Việc cần xử lý</h2>
          <span>{{ loading ? '' : `${openTaskCount} việc` }}</span>
        </div>
        <ul class="task-list" aria-labelledby="task-title">
          <li v-for="task in tasks" :key="task.title">
            <RouterLink class="task-item" :class="{ 'is-open': task.count > 0 }" :to="task.to">
              <span class="task-count">{{ loading ? '–' : task.count }}</span>
              <span class="task-text">
                <strong>{{ task.title }}</strong>
                <span>{{ task.description }}</span>
              </span>
              <span class="task-cta">{{ task.count > 0 ? 'Xử lý' : 'Xem' }} <AppIcon name="chevronRight" :size="14" /></span>
            </RouterLink>
          </li>
        </ul>
      </div>

      <div class="kpi-grid">
        <article class="kpi">
          <span class="kpi-label">Tổng sản phẩm</span>
          <strong>{{ loading ? '–' : stats?.total_products ?? 0 }}</strong>
          <span class="meter" role="img" :aria-label="`${approvedShare}% sản phẩm đang công khai`">
            <span :style="{ width: `${approvedShare}%` }" />
          </span>
          <span class="kpi-note">{{ stats?.approved_products ?? 0 }} đang công khai, {{ approvedShare }}% tổng số sản phẩm</span>
        </article>
        <article class="kpi">
          <span class="kpi-label">Chủ thể / HTX đã duyệt</span>
          <strong>{{ statisticsLoading ? '–' : approvedSubjects }}</strong>
          <span class="kpi-note">{{ stats?.pending_subject_applications ?? 0 }} hồ sơ đang chờ xác minh</span>
        </article>
        <article class="kpi">
          <span class="kpi-label">Điểm du lịch nông nghiệp</span>
          <strong>{{ statisticsLoading ? '–' : locationTotal }}</strong>
          <span class="kpi-note">{{ locationItems.length }} loại hình trên bản đồ số</span>
        </article>
        <article class="kpi" :class="{ 'is-warning': (stats?.products_missing_decision ?? 0) > 0 }">
          <span class="kpi-label">Thiếu số quyết định công nhận</span>
          <strong>{{ loading ? '–' : stats?.products_missing_decision ?? 0 }}</strong>
          <span class="kpi-note">{{ missingDecisionShare }}% sản phẩm chưa có số quyết định</span>
          <RouterLink class="kpi-link" to="/quan-tri/san-pham">Bổ sung nguồn chứng cứ <AppIcon name="chevronRight" :size="14" /></RouterLink>
        </article>
      </div>
    </section>

    <section id="thong-ke" class="stats-section" aria-labelledby="stats-products-title">
      <div class="section-head">
        <div>
          <span class="ocop-eyebrow">Thống kê</span>
          <h2 id="stats-products-title">Sản phẩm OCOP</h2>
        </div>
        <span class="section-note">Số liệu toàn tỉnh, tính đến lúc mở trang</span>
      </div>

      <div v-if="statisticsError" class="state-box is-error" role="alert">
        <span><AppIcon name="alert" :size="18" /> {{ statisticsError }}</span>
        <button class="ocop-btn-main" type="button" @click="loadStatistics">Thử lại</button>
      </div>

      <div v-else-if="statisticsLoading" class="chart-grid" aria-busy="true">
        <div class="skeleton span-2" /><div class="skeleton" /><div class="skeleton" /><div class="skeleton span-2" />
        <span class="visually-hidden" role="status">Đang tải số liệu thống kê...</span>
      </div>

      <div v-else-if="statistics" class="chart-grid">
        <StatChart
          class="span-2"
          kind="stacked"
          title="Trạng thái hồ sơ sản phẩm"
          :description="`${statusTotal} hồ sơ, gồm cả bản nháp của chủ thể`"
          :items="statusItems"
          :summary="describe(statusItems, 'hồ sơ')"
          unit="hồ sơ"
          :height="40"
        >
          <template #lead>
            <p class="lead-figure">
              <strong>{{ percentText(approvedStatusCount, statusTotal) }}</strong>
              hồ sơ đã được duyệt và đang hiển thị công khai
            </p>
          </template>
          <ul class="status-legend">
            <li v-for="item in statusItems" :key="item.label">
              <span class="legend-label"><span class="dot" :style="{ background: item.color }" />{{ item.label }}</span>
              <strong>{{ item.value }}</strong>
              <span class="legend-share">{{ item.share }}</span>
            </li>
          </ul>
        </StatChart>

        <StatChart
          title="Hạng sao OCOP"
          :description="`${publicTotal} sản phẩm đang công khai`"
          :items="starItems"
          :summary="describe(starItems)"
          :height="240"
        />

        <StatChart
          kind="bar"
          title="Theo nhóm sản phẩm"
          description="Màu trùng với chip nhóm ở trang công khai"
          :items="categoryItems"
          :summary="describe(categoryItems)"
          :height="Math.max(200, categoryItems.length * 36)"
        >
          <p v-if="emptyCategoryCount" class="note">{{ emptyCategoryCount }} nhóm chưa có sản phẩm được duyệt.</p>
        </StatChart>

        <StatChart
          class="span-2"
          kind="bar"
          :title="`${districtItems.length} xã, phường có nhiều sản phẩm nhất`"
          description="Theo địa bàn của chủ thể, chỉ tính sản phẩm đang công khai"
          :items="districtItems"
          :summary="describe(districtItems)"
          :height="Math.max(200, districtItems.length * 34)"
        />

        <StatChart
          class="span-2"
          title="Sản phẩm được duyệt theo tháng"
          :description="monthItems.length ? `Theo ngày duyệt, ${monthRange}` : 'Chưa có sản phẩm nào được duyệt'"
          :items="monthItems"
          :summary="describe(monthItems.filter((item) => item.value > 0)) || 'Chưa có sản phẩm nào được duyệt'"
          :height="260"
        >
          <p v-if="statistics.approved_without_review_date" class="note">
            {{ statistics.approved_without_review_date }} sản phẩm nhập sẵn không có ngày duyệt nên không nằm trong biểu đồ.
          </p>
        </StatChart>

        <StatChart
          kind="bar"
          title="Giấy chứng nhận OCOP"
          description="Số sản phẩm theo năm được công nhận"
          :items="certYearItems"
          :summary="describe(certYearItems)"
          :height="Math.max(140, certYearItems.length * 34)"
        >
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
          <span class="ocop-eyebrow">Thống kê</span>
          <h2 id="stats-interest-title">Mức độ quan tâm và du lịch</h2>
        </div>
      </div>

      <div class="chart-grid">
        <article class="span-2 plain-card">
          <header class="plain-head">
            <h3>Sản phẩm được xem nhiều nhất</h3>
            <p>Lượt mở trang chi tiết sản phẩm</p>
          </header>
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

        <StatChart
          kind="bar"
          title="Điểm du lịch theo loại hình"
          :description="`${locationTotal} điểm đang hiển thị trên bản đồ số`"
          :items="locationItems"
          :summary="describe(locationItems, 'điểm')"
          unit="điểm"
          :height="Math.max(160, locationItems.length * 40)"
        />
      </div>
    </section>
  </main>
</template>

<style scoped>
.dashboard-page {
  display: grid;
  gap: var(--ocop-space-8);
}

.dash-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--ocop-space-4);
}

.dash-date {
  margin: 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
  text-transform: capitalize;
}

.dash-head h1 {
  margin: var(--ocop-space-1) 0;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-title-md);
  font-weight: 800;
}

.dash-summary {
  margin: 0;
  color: var(--ocop-mist-700);
  font-size: var(--ocop-font-size-body-lg);
}

.dash-summary strong {
  padding: 0 var(--ocop-space-2);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-daquy-400);
  color: var(--ocop-mist-950);
}

.head-actions {
  display: flex;
  flex-wrap: wrap;
  gap: var(--ocop-space-2);
}

/* ---------- Hàng đầu: việc cần xử lý + số liệu chính ---------- */
.top-grid {
  display: grid;
  grid-template-columns: minmax(0, 5fr) minmax(0, 7fr);
  gap: var(--ocop-space-6);
}

.task-panel {
  display: flex;
  flex-direction: column;
  gap: var(--ocop-space-4);
  padding: var(--ocop-space-6);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-mist-950);
  color: var(--ocop-mist-100);
}

.panel-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: var(--ocop-space-3);
}

.panel-head h2 {
  margin: 0;
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 700;
}

.panel-head span {
  color: var(--ocop-mist-300);
  font-size: var(--ocop-font-size-small);
}

.task-list {
  display: grid;
  gap: var(--ocop-space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.task-item {
  display: flex;
  min-height: 64px;
  align-items: center;
  gap: var(--ocop-space-4);
  padding: var(--ocop-space-3) var(--ocop-space-4);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-mist-900);
  color: var(--ocop-mist-100);
  text-decoration: none;
  transition: background var(--ocop-transition);
}

.task-item:hover {
  background: var(--ocop-mist-800);
  color: var(--ocop-white);
}

.task-count {
  display: grid;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  place-items: center;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-mist-800);
  color: var(--ocop-mist-300);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 800;
}

/* Việc còn tồn: ô số vàng dã quỳ, chữ đậm, không chỉ dựa vào màu. */
.task-item.is-open .task-count {
  background: var(--ocop-daquy-400);
  color: var(--ocop-mist-950);
}

.task-text {
  display: flex;
  min-width: 0;
  flex: 1;
  flex-direction: column;
  gap: 2px;
}

.task-text strong {
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-body);
}

.task-text span {
  color: var(--ocop-mist-300);
  font-size: var(--ocop-font-size-small);
  line-height: 1.45;
}

.task-cta {
  display: inline-flex;
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-mist-300);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
  white-space: nowrap;
}

.is-open .task-cta {
  color: var(--ocop-daquy-300);
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--ocop-space-4);
}

.kpi {
  display: flex;
  flex-direction: column;
  gap: var(--ocop-space-2);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.kpi-label {
  color: var(--ocop-mist-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 600;
}

.kpi strong {
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-title-lg);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.1;
}

.kpi-note {
  color: var(--ocop-mist-700);
  font-size: var(--ocop-font-size-small);
}

.kpi.is-warning {
  border-color: var(--ocop-warning-border);
  background: var(--ocop-warning-soft);
}

.kpi.is-warning strong {
  color: var(--ocop-warning-strong);
}

.kpi-link {
  display: inline-flex;
  min-height: 32px;
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-warning-strong);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
}

.meter {
  display: block;
  height: 8px;
  overflow: hidden;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mist-100);
}

.meter > span {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: var(--ocop-success);
}

/* ---------- Thống kê ---------- */
.stats-section {
  display: grid;
  gap: var(--ocop-space-4);
  scroll-margin-top: var(--ocop-space-6);
}

.section-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--ocop-space-3);
  padding-top: var(--ocop-space-4);
  border-top: 1px solid var(--ocop-border);
}

.section-head h2 {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-title-md);
  font-weight: 750;
}

.section-note {
  color: var(--ocop-mist-600);
  font-size: var(--ocop-font-size-small);
}

.chart-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ocop-space-6);
}

.span-2 {
  grid-column: span 2;
}

.skeleton {
  min-height: 300px;
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-mist-100);
}

.lead-figure {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: var(--ocop-space-3);
  margin: 0;
  color: var(--ocop-mist-700);
  font-size: var(--ocop-font-size-body);
}

.lead-figure strong {
  color: var(--ocop-success);
  font-size: var(--ocop-font-size-title-lg);
  font-weight: 800;
  letter-spacing: -0.02em;
}

.status-legend {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
  gap: var(--ocop-space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.status-legend li {
  display: flex;
  flex-direction: column;
  gap: var(--ocop-space-1);
  padding: var(--ocop-space-3);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-mist-50);
}

.legend-label {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-2);
  color: var(--ocop-mist-700);
  font-size: var(--ocop-font-size-small);
}

.status-legend strong {
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 800;
}

.legend-share {
  color: var(--ocop-mist-600);
  font-size: var(--ocop-font-size-caption);
}

.dot {
  width: 10px;
  height: 10px;
  flex-shrink: 0;
  border-radius: var(--ocop-radius-xs);
}

.note {
  margin: 0;
  padding: var(--ocop-space-3);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-daquy-50);
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-small);
}

.cert-tiles {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--ocop-space-3);
}

.cert-tile {
  display: flex;
  flex-direction: column;
  gap: var(--ocop-space-1);
  padding: var(--ocop-space-3);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-mist-50);
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-small);
  text-decoration: none;
}

.cert-tile strong {
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-title-md);
  font-weight: 800;
}

.cert-tile.is-danger {
  background: var(--ocop-danger-soft);
}

.cert-tile.is-danger strong {
  color: var(--ocop-danger-strong);
}

.tile-cta {
  display: inline-flex;
  align-items: center;
  gap: var(--ocop-space-1);
  font-weight: 700;
}

.tile-note {
  color: var(--ocop-mist-600);
  font-size: var(--ocop-font-size-caption);
}

.plain-card {
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--ocop-space-4);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.plain-head h3 {
  margin: 0;
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-body-lg);
  font-weight: 700;
}

.plain-head p {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-mist-600);
  font-size: var(--ocop-font-size-small);
}

.viewed-list {
  display: grid;
  gap: var(--ocop-space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.viewed-list li {
  display: grid;
  grid-template-columns: 28px minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--ocop-space-3);
  min-height: 44px;
  border-bottom: 1px solid var(--ocop-border-soft);
}

.rank {
  color: var(--ocop-mist-500);
  font-weight: 700;
}

.empty-box {
  display: flex;
  min-height: 220px;
  flex: 1;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-2);
  padding: var(--ocop-space-6);
  border: 1px dashed var(--ocop-border-strong);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-mist-50);
  text-align: center;
}

.empty-box p {
  max-width: 420px;
  margin: 0;
  color: var(--ocop-mist-700);
  font-size: var(--ocop-font-size-small);
}

.empty-icon {
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-card);
  color: var(--ocop-mist-600);
}

.state-box {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-4);
  border: 1px solid var(--ocop-danger-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger-strong);
}

@media (max-width: 1199.98px) {
  .top-grid {
    grid-template-columns: 1fr;
  }

  .chart-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 767.98px) {
  .dash-head,
  .section-head {
    flex-direction: column;
    align-items: flex-start;
  }

  .chart-grid {
    grid-template-columns: minmax(0, 1fr);
  }

  .kpi-grid {
    gap: var(--ocop-space-3);
  }

  .kpi {
    padding: var(--ocop-space-4);
  }

  .kpi strong {
    font-size: var(--ocop-font-size-title-md);
  }

  .span-2 {
    grid-column: auto;
  }

  .task-panel {
    padding: var(--ocop-space-4);
  }

  .task-text span {
    display: none;
  }
}
</style>
