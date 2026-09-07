<script setup lang="ts">
import { computed } from 'vue'

import { authStore } from '@/stores/auth'

const greetingName = computed(() => authStore.currentUser.value?.full_name || 'Quản trị viên')

const systemCards = [
  { label: 'Phân quyền', value: '3 vai trò', note: 'Admin, chủ thể và người dùng', tone: 'green' },
  { label: 'Xác thực', value: 'JWT', note: 'Access token và kiểm tra tài khoản', tone: 'blue' },
  { label: 'Dữ liệu không gian', value: 'PostGIS', note: 'Sẵn sàng cho module bản đồ', tone: 'purple' },
  { label: 'Kiểm duyệt', value: '4 nhóm', note: 'Chủ thể, sản phẩm, địa điểm, đánh giá', tone: 'gold' },
]

const priorities = [
  { title: 'Quản lý sản phẩm', description: 'CRUD, ảnh, trạng thái và quy trình kiểm duyệt.', status: 'Ưu tiên 1' },
  { title: 'Quản lý chủ thể OCOP', description: 'Tiếp nhận và xét duyệt hồ sơ đăng ký chủ thể.', status: 'Ưu tiên 2' },
  { title: 'Quản lý điểm du lịch', description: 'Thông tin địa điểm, tọa độ và dịch vụ.', status: 'Ưu tiên 3' },
  { title: 'Kiểm duyệt đánh giá', description: 'Duyệt nội dung trước khi ảnh hưởng điểm trung bình.', status: 'Sau API review' },
]
</script>

<template>
  <main class="dashboard-page">
    <section class="welcome-card">
      <div>
        <span>Khu vực dành riêng cho quản trị viên</span>
        <h1>Xin chào, {{ greetingName }}</h1>
        <p>Theo dõi tiến độ xây dựng hệ thống và truy cập các module quản lý từ một giao diện thống nhất.</p>
      </div>
      <RouterLink to="/">Xem trang công khai →</RouterLink>
    </section>

    <section class="system-section" aria-labelledby="system-title">
      <div class="section-title">
        <div>
          <span>Nền tảng hiện có</span>
          <h2 id="system-title">Tổng quan hệ thống</h2>
        </div>
        <small>Không sử dụng số liệu giả</small>
      </div>
      <div class="system-grid">
        <article v-for="card in systemCards" :key="card.label" :class="`tone-${card.tone}`">
          <span>{{ card.label }}</span>
          <strong>{{ card.value }}</strong>
          <p>{{ card.note }}</p>
        </article>
      </div>
    </section>

    <div class="dashboard-grid">
      <section class="priority-panel" aria-labelledby="priority-title">
        <div class="panel-heading">
          <div>
            <span>Kế hoạch tiếp theo</span>
            <h2 id="priority-title">Module quản trị ưu tiên</h2>
          </div>
        </div>
        <div class="priority-list">
          <article v-for="(item, index) in priorities" :key="item.title">
            <span class="priority-index">{{ index + 1 }}</span>
            <div>
              <strong>{{ item.title }}</strong>
              <p>{{ item.description }}</p>
            </div>
            <small>{{ item.status }}</small>
          </article>
        </div>
      </section>

      <aside class="security-panel">
        <span class="security-icon" aria-hidden="true">🛡️</span>
        <h2>Phân quyền hai lớp</h2>
        <p>Vue Router ngăn truy cập sai vai trò trên giao diện. FastAPI vẫn phải xác minh JWT và role ở mọi API quản trị.</p>
        <ul>
          <li>Không tin dữ liệu role từ frontend</li>
          <li>User và subject nhận phản hồi 403</li>
          <li>Nội dung pending không xuất hiện công khai</li>
        </ul>
      </aside>
    </div>
  </main>
</template>

<style scoped>
.dashboard-page {
  display: grid;
  gap: 24px;
}

.welcome-card {
  display: flex;
  min-height: 190px;
  padding: clamp(24px, 4vw, 40px);
  align-items: flex-end;
  justify-content: space-between;
  gap: 24px;
  overflow: hidden;
  border-radius: 20px;
  background:
    radial-gradient(circle at 86% 15%, rgb(110 231 183 / 28%), transparent 18rem),
    linear-gradient(135deg, #004f3b, #0f3c36 60%, #101a30);
  color: #fff;
  box-shadow: 0 18px 35px rgb(15 23 43 / 12%);
}

.welcome-card span,
.section-title span,
.panel-heading span {
  color: #6ee7b7;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.welcome-card h1 {
  margin: 6px 0;
  font-size: clamp(28px, 4vw, 40px);
  font-weight: 800;
  letter-spacing: -0.8px;
}

.welcome-card p {
  max-width: 650px;
  margin: 0;
  color: #d6e4df;
  line-height: 1.6;
}

.welcome-card a {
  flex: 0 0 auto;
  padding: 10px 15px;
  border: 1px solid rgb(255 255 255 / 25%);
  border-radius: 10px;
  background: rgb(255 255 255 / 10%);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.system-section,
.priority-panel,
.security-panel {
  padding: 22px;
  border: 1px solid var(--ocop-border);
  border-radius: 16px;
  background: #fff;
}

.section-title,
.panel-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 12px;
}

.section-title span,
.panel-heading span {
  color: var(--ocop-primary-700);
}

.section-title h2,
.panel-heading h2,
.security-panel h2 {
  margin: 3px 0 0;
  color: var(--ocop-navy);
  font-size: 19px;
  font-weight: 800;
}

.section-title small {
  color: var(--ocop-slate);
  font-size: 10px;
}

.system-grid {
  display: grid;
  margin-top: 16px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.system-grid article {
  padding: 18px;
  border: 1px solid var(--ocop-border);
  border-radius: 13px;
  background: #f8fafc;
}

.system-grid article > span {
  display: block;
  color: var(--ocop-slate);
  font-size: 10px;
  font-weight: 700;
  text-transform: uppercase;
}

.system-grid strong {
  display: block;
  margin-top: 10px;
  color: var(--card-color, var(--ocop-primary-700));
  font-size: 23px;
}

.system-grid p {
  margin: 4px 0 0;
  color: var(--ocop-slate);
  font-size: 11px;
  line-height: 16px;
}

.tone-blue { --card-color: #0284c7; }
.tone-purple { --card-color: #7e22ce; }
.tone-gold { --card-color: #b45309; }

.dashboard-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.55fr) minmax(260px, 0.75fr);
  gap: 24px;
}

.priority-list {
  display: grid;
  margin-top: 14px;
}

.priority-list article {
  display: grid;
  padding: 14px 0;
  align-items: center;
  grid-template-columns: 32px minmax(0, 1fr) auto;
  gap: 12px;
  border-top: 1px solid #edf1f4;
}

.priority-index {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 8px;
  background: var(--ocop-mint-soft);
  color: var(--ocop-primary-700);
  font-size: 11px;
  font-weight: 800;
}

.priority-list strong {
  color: var(--ocop-navy);
  font-size: 13px;
}

.priority-list p {
  margin: 2px 0 0;
  color: var(--ocop-slate);
  font-size: 11px;
}

.priority-list small {
  padding: 4px 8px;
  border-radius: 999px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 9px;
  font-weight: 700;
}

.security-panel {
  background: #f0fdf4;
}

.security-icon {
  font-size: 34px;
}

.security-panel p,
.security-panel li {
  color: #52665a;
  font-size: 12px;
  line-height: 1.6;
}

.security-panel p {
  margin: 10px 0;
}

.security-panel ul {
  display: grid;
  margin: 0;
  padding-left: 18px;
  gap: 5px;
}

@media (max-width: 991.98px) {
  .system-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .dashboard-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 575.98px) {
  .welcome-card {
    align-items: flex-start;
    flex-direction: column;
  }

  .system-grid {
    grid-template-columns: 1fr;
  }

  .priority-list article {
    align-items: start;
    grid-template-columns: 28px minmax(0, 1fr);
  }

  .priority-list small {
    grid-column: 2;
    justify-self: start;
  }
}
</style>
