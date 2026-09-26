<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { getAdminDashboard, type AdminDashboardStats } from '@/services/admin'
import { getApiErrorMessage } from '@/services/api-error'
import { authStore } from '@/stores/auth'

const greetingName = computed(() => authStore.currentUser.value?.full_name || 'Quản trị viên')

const stats = ref<AdminDashboardStats | null>(null)
const loading = ref(true)
const errorMessage = ref('')

// Hàng đợi việc cần làm (pattern: task queue / inbox) đặt lên đầu, số liệu tổng quan xếp sau.
const tasks = computed(() => [
  {
    title: 'Sản phẩm mới chờ duyệt',
    description: 'Đối chiếu chứng nhận rồi quyết định công khai hay trả lại.',
    count: stats.value?.pending_products ?? 0,
    icon: 'package',
    to: '/quan-tri/san-pham',
  },
  {
    title: 'Yêu cầu sửa hoặc ngừng hiển thị',
    description: 'So sánh dữ liệu cũ và mới theo đề nghị của chủ thể.',
    count: stats.value?.pending_change_requests ?? 0,
    icon: 'refresh',
    to: '/quan-tri/san-pham',
  },
  {
    title: 'Hồ sơ chủ thể chờ xác minh',
    description: 'Xác minh HTX, doanh nghiệp trước khi cấp quyền đăng sản phẩm.',
    count: stats.value?.pending_subject_applications ?? 0,
    icon: 'building',
    to: '/quan-tri/ho-so-chu-the',
  },
])

const openTaskCount = computed(() => tasks.value.reduce((sum, task) => sum + task.count, 0))

const approvedShare = computed(() => {
  const total = stats.value?.total_products ?? 0
  return total ? Math.round(((stats.value?.approved_products ?? 0) / total) * 100) : 0
})

const todayLabel = new Intl.DateTimeFormat('vi-VN', { weekday: 'long', day: '2-digit', month: '2-digit', year: 'numeric' }).format(new Date())

async function loadDashboard(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    stats.value = await getAdminDashboard()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải thống kê quản trị.')
  } finally {
    loading.value = false
  }
}

onMounted(loadDashboard)
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
      <RouterLink class="ocop-btn-ghost" to="/">Xem trang công khai <AppIcon name="chevronRight" :size="16" /></RouterLink>
    </header>

    <div v-if="errorMessage" class="state-box is-error" role="alert">
      <span>{{ errorMessage }}</span>
      <button class="ocop-btn-main" type="button" @click="loadDashboard">Thử lại</button>
    </div>

    <section aria-labelledby="task-title">
      <h2 id="task-title" class="block-title">Việc cần xử lý</h2>
      <div class="task-grid">
        <RouterLink
          v-for="task in tasks"
          :key="task.title"
          class="task-card"
          :class="{ 'is-open': task.count > 0 }"
          :to="task.to"
        >
          <span class="task-icon" aria-hidden="true"><AppIcon :name="task.icon" :size="20" /></span>
          <span class="task-count">{{ loading ? '–' : task.count }}</span>
          <strong>{{ task.title }}</strong>
          <span class="task-desc">{{ task.description }}</span>
          <span class="task-cta">
            {{ task.count > 0 ? 'Xử lý ngay' : 'Xem danh sách' }} <AppIcon name="chevronRight" :size="16" />
          </span>
        </RouterLink>
      </div>
    </section>

    <section aria-labelledby="overview-title" class="overview">
      <h2 id="overview-title" class="block-title">Tổng quan dữ liệu</h2>
      <div class="overview-grid">
        <article class="stat">
          <span class="stat-label">Tổng sản phẩm</span>
          <strong>{{ loading ? '–' : stats?.total_products ?? 0 }}</strong>
          <span class="stat-note">Mọi trạng thái, kể cả bản nháp</span>
        </article>
        <article class="stat">
          <span class="stat-label">Đang công khai</span>
          <strong>{{ loading ? '–' : stats?.approved_products ?? 0 }}</strong>
          <span class="meter" role="img" :aria-label="`${approvedShare}% sản phẩm đang công khai`">
            <span :style="{ width: `${approvedShare}%` }" />
          </span>
          <span class="stat-note">{{ approvedShare }}% tổng số sản phẩm</span>
        </article>
        <article class="stat" :class="{ 'is-warning': (stats?.products_missing_decision ?? 0) > 0 }">
          <span class="stat-label">Thiếu số quyết định công nhận</span>
          <strong>{{ loading ? '–' : stats?.products_missing_decision ?? 0 }}</strong>
          <RouterLink class="stat-link" to="/quan-tri/san-pham">Bổ sung nguồn chứng cứ <AppIcon name="chevronRight" :size="14" /></RouterLink>
        </article>
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

.block-title {
  margin: 0 0 var(--ocop-space-3);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 750;
}

.task-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ocop-space-4);
}

.task-card {
  display: grid;
  grid-template-columns: auto 1fr;
  grid-template-areas:
    'icon count'
    'title title'
    'desc desc'
    'cta cta';
  align-items: center;
  gap: var(--ocop-space-2) var(--ocop-space-3);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  color: var(--ocop-navy);
  text-decoration: none;
  transition: box-shadow var(--ocop-transition), transform var(--ocop-transition);
}

.task-card:hover {
  box-shadow: var(--ocop-shadow-card);
  transform: translateY(-2px);
}

/* Việc còn tồn: viền trái vàng và số lớn màu đậm để nổi lên trước (không chỉ dựa vào màu). */
.task-card.is-open {
  border-color: var(--ocop-daquy-400);
  box-shadow: inset 4px 0 0 var(--ocop-daquy-400);
}

.task-icon {
  display: grid;
  width: 44px;
  height: 44px;
  grid-area: icon;
  place-items: center;
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-mist-100);
  color: var(--ocop-mist-800);
}

.is-open .task-icon {
  background: var(--ocop-daquy-50);
  color: var(--ocop-daquy-700);
}

.task-count {
  grid-area: count;
  justify-self: end;
  color: var(--ocop-mist-400);
  font-size: var(--ocop-font-size-title-lg);
  font-weight: 800;
  line-height: 1;
}

.is-open .task-count {
  color: var(--ocop-mist-950);
}

.task-card strong {
  grid-area: title;
  margin-top: var(--ocop-space-2);
  font-size: var(--ocop-font-size-body-lg);
}

.task-desc {
  grid-area: desc;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
  line-height: 1.5;
}

.task-cta {
  display: inline-flex;
  margin-top: var(--ocop-space-2);
  grid-area: cta;
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-primary-700);
  font-weight: 700;
}

.overview-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ocop-space-4);
}

.stat {
  display: grid;
  align-content: start;
  gap: var(--ocop-space-2);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.stat-label {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
  font-weight: 600;
}

.stat strong {
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-title-lg);
  font-weight: 800;
  line-height: 1.1;
}

.stat-note {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
}

.stat.is-warning strong {
  color: var(--ocop-warning-strong);
}

.stat-link {
  display: inline-flex;
  min-height: 32px;
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-primary-700);
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
  background: var(--ocop-tone-leaf);
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

@media (max-width: 991.98px) {
  .task-grid,
  .overview-grid {
    grid-template-columns: 1fr;
  }

  .dash-head {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
