<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import StatusPanel from '@/components/ui/StatusPanel.vue'
import { useDialogFocus } from '@/composables/useDialogFocus'
import { listAdminUsers, updateAdminUserStatus } from '@/services/admin-users'
import { getApiErrorMessage } from '@/services/api-error'
import { authStore } from '@/stores/auth'
import type { AdminUser } from '@/types/admin-user'
import type { SocialProvider, UserRole } from '@/types/auth'
import type { SubjectStatus } from '@/types/subject'

const SEARCH_DELAY_MS = 350
const pageSize = 20

const users = ref<AdminUser[]>([])
const page = ref(1)
const total = ref(0)
const isLoading = ref(true)
const errorMessage = ref('')
const statusMessage = ref('')

const filters = reactive<{ q: string; role: UserRole | ''; status: 'active' | 'locked' | '' }>({
  q: '',
  role: '',
  status: '',
})

const pendingUser = ref<AdminUser | null>(null)
const isUpdating = ref(false)
const dialogError = ref('')
const confirmDialog = ref<HTMLElement | null>(null)

const roleLabels: Record<UserRole, string> = {
  admin: 'Quản trị viên',
  subject: 'Chủ thể',
  user: 'Người dùng',
}

const subjectStatusLabels: Record<SubjectStatus, string> = {
  pending: 'hồ sơ chờ duyệt',
  approved: 'hồ sơ đã duyệt',
  rejected: 'hồ sơ bị từ chối',
}

const providerLabels: Record<SocialProvider, string> = {
  google: 'Google',
  facebook: 'Facebook',
}

const currentUserId = computed(() => authStore.currentUser.value?.id ?? null)
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const isDialogOpen = computed(() => Boolean(pendingUser.value))
const willLock = computed(() => Boolean(pendingUser.value?.is_active))

// Mỗi lần tải tăng số thứ tự; kết quả trả về chậm của lần lọc cũ bị bỏ qua.
let latestRequest = 0
let searchTimer: ReturnType<typeof setTimeout> | undefined

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short' }).format(new Date(value))
}

function loginMethods(user: AdminUser): string {
  const methods = user.has_password ? ['Mật khẩu'] : []
  methods.push(...user.social_providers.map((provider) => providerLabels[provider] ?? provider))
  return methods.join(', ') || 'Chưa có'
}

async function loadUsers(): Promise<void> {
  const requestId = ++latestRequest
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await listAdminUsers({
      q: filters.q.trim() || undefined,
      role: filters.role || undefined,
      is_active: filters.status ? filters.status === 'active' : undefined,
      page: page.value,
      page_size: pageSize,
    })
    if (requestId !== latestRequest) return
    users.value = response.items
    total.value = response.total
  } catch (error) {
    if (requestId !== latestRequest) return
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải danh sách người dùng.')
  } finally {
    if (requestId === latestRequest) isLoading.value = false
  }
}

function applyFilters(): void {
  clearTimeout(searchTimer)
  page.value = 1
  void loadUsers()
}

watch(
  () => filters.q,
  () => {
    clearTimeout(searchTimer)
    searchTimer = setTimeout(applyFilters, SEARCH_DELAY_MS)
  },
)

function changePage(nextPage: number): void {
  page.value = Math.min(Math.max(nextPage, 1), totalPages.value)
  void loadUsers()
}

function askToggle(user: AdminUser): void {
  pendingUser.value = user
  dialogError.value = ''
  statusMessage.value = ''
}

function closeDialog(): void {
  if (isUpdating.value) return
  pendingUser.value = null
}

useDialogFocus(isDialogOpen, confirmDialog, closeDialog)

async function confirmToggle(): Promise<void> {
  const user = pendingUser.value
  if (!user || isUpdating.value) return
  isUpdating.value = true
  dialogError.value = ''
  try {
    const updated = await updateAdminUserStatus(user.id, !user.is_active)
    users.value = users.value.map((item) => (item.id === updated.id ? updated : item))
    statusMessage.value = updated.is_active
      ? `Đã mở khóa tài khoản ${updated.email}.`
      : `Đã khóa tài khoản ${updated.email}.`
    isUpdating.value = false
    pendingUser.value = null
    // Đang lọc theo trạng thái thì tải lại để tài khoản vừa đổi rời khỏi danh sách.
    if (filters.status) void loadUsers()
  } catch (error) {
    dialogError.value = getApiErrorMessage(error, 'Không thể cập nhật trạng thái tài khoản.')
    isUpdating.value = false
  }
}

onMounted(loadUsers)
onBeforeUnmount(() => clearTimeout(searchTimer))
</script>

<template>
  <div class="users-page">
    <header class="page-heading">
      <div>
        <span>Tài khoản</span>
        <h1>Người dùng</h1>
        <p>Tìm tài khoản, xem cách đăng nhập và khóa tài khoản vi phạm.</p>
      </div>
      <strong>{{ total }} tài khoản</strong>
    </header>

    <form class="filter-bar" role="search" @submit.prevent="applyFilters">
      <label class="filter-field">
        <span>Tìm theo email hoặc họ tên</span>
        <input v-model="filters.q" class="form-control" type="search" maxlength="150" placeholder="Ví dụ: nguyen@gmail.com" />
      </label>
      <label class="filter-field">
        <span>Vai trò</span>
        <select v-model="filters.role" class="form-select" @change="applyFilters">
          <option value="">Tất cả vai trò</option>
          <option value="admin">Quản trị viên</option>
          <option value="subject">Chủ thể</option>
          <option value="user">Người dùng</option>
        </select>
      </label>
      <label class="filter-field">
        <span>Trạng thái</span>
        <select v-model="filters.status" class="form-select" @change="applyFilters">
          <option value="">Tất cả trạng thái</option>
          <option value="active">Đang hoạt động</option>
          <option value="locked">Đã khóa</option>
        </select>
      </label>
    </form>

    <div role="status" aria-live="polite">
      <p v-if="statusMessage" class="alert alert-success">
        <AppIcon name="checkCircle" :size="18" /> {{ statusMessage }}
      </p>
    </div>

    <section class="table-card" aria-label="Danh sách tài khoản">
      <StatusPanel v-if="isLoading" kind="loading" :rows="4" message="Đang tải danh sách người dùng…" />
      <StatusPanel v-else-if="errorMessage" kind="error" :message="errorMessage" @retry="loadUsers" />
      <StatusPanel
        v-else-if="users.length === 0"
        kind="empty"
        title="Không có tài khoản phù hợp"
        message="Đổi từ khóa, vai trò hoặc trạng thái để xem tài khoản khác."
      />
      <table v-else class="table users-table">
        <thead>
          <tr>
            <th scope="col">Tài khoản</th>
            <th scope="col">Vai trò</th>
            <th scope="col">Đăng nhập bằng</th>
            <th scope="col">Ngày tạo</th>
            <th scope="col">Trạng thái</th>
            <th scope="col" class="text-end">Thao tác</th>
          </tr>
        </thead>
        <tbody class="stagger-in">
          <tr v-for="user in users" :key="user.id" :class="{ 'is-locked': !user.is_active }">
            <td data-label="Tài khoản" class="cell-account">
              <div>
                <strong>{{ user.full_name }}</strong>
                <small>{{ user.email }}</small>
                <small v-if="user.phone">{{ user.phone }}</small>
              </div>
            </td>
            <td data-label="Vai trò">
              <div>
                <span>{{ roleLabels[user.role] }}</span>
                <small v-if="user.subject">{{ user.subject.name }} · {{ subjectStatusLabels[user.subject.status] }}</small>
              </div>
            </td>
            <td data-label="Đăng nhập bằng"><div>{{ loginMethods(user) }}</div></td>
            <td data-label="Ngày tạo"><div>{{ formatDate(user.created_at) }}</div></td>
            <td data-label="Trạng thái">
              <div>
                <span class="status-badge" :class="user.is_active ? 'status-approved' : 'status-rejected'">
                  {{ user.is_active ? 'Đang hoạt động' : 'Đã khóa' }}
                </span>
              </div>
            </td>
            <td data-label="Thao tác" class="cell-actions">
              <span v-if="user.id === currentUserId" class="self-note">Tài khoản của bạn</span>
              <button
                v-else
                class="btn"
                :class="user.is_active ? 'btn-outline-danger' : 'btn-light'"
                type="button"
                :aria-label="`${user.is_active ? 'Khóa' : 'Mở khóa'} tài khoản ${user.email}`"
                @click="askToggle(user)"
              >
                <AppIcon :name="user.is_active ? 'lock' : 'unlock'" :size="16" />
                {{ user.is_active ? 'Khóa' : 'Mở khóa' }}
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <nav v-if="totalPages > 1" class="pagination-bar" aria-label="Phân trang người dùng">
      <button class="btn btn-light" type="button" :disabled="page === 1 || isLoading" @click="changePage(page - 1)">
        Trước
      </button>
      <span>Trang {{ page }} / {{ totalPages }}</span>
      <button class="btn btn-light" type="button" :disabled="page === totalPages || isLoading" @click="changePage(page + 1)">
        Sau
      </button>
    </nav>

    <Transition name="ocop-fade">
      <div v-if="pendingUser" class="modal-layer" role="presentation" @click.self="closeDialog">
        <section
          ref="confirmDialog"
          class="confirm-dialog"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="user-status-title"
          aria-describedby="user-status-desc"
          tabindex="-1"
        >
          <h2 id="user-status-title">{{ willLock ? 'Khóa tài khoản này?' : 'Mở khóa tài khoản này?' }}</h2>
          <div id="user-status-desc" class="dialog-body">
            <p><strong>{{ pendingUser.full_name }}</strong> · {{ pendingUser.email }}</p>
            <p v-if="willLock">
              Người dùng sẽ bị đăng xuất ở lần thao tác tiếp theo và không đăng nhập lại được cho tới khi được mở khóa.
            </p>
            <p v-else>Người dùng có thể đăng nhập và sử dụng lại tài khoản như trước.</p>
            <p v-if="pendingUser.role === 'subject' || pendingUser.subject" class="dialog-note">
              {{
                willLock
                  ? 'Sản phẩm và điểm du lịch của chủ thể này sẽ tạm ngừng hiển thị ở trang công khai.'
                  : 'Sản phẩm và điểm du lịch đã duyệt của chủ thể này sẽ hiển thị lại ở trang công khai.'
              }}
            </p>
          </div>
          <div v-if="dialogError" class="alert alert-danger" role="alert">{{ dialogError }}</div>
          <div class="dialog-actions">
            <button class="btn btn-light" type="button" :disabled="isUpdating" @click="closeDialog">Hủy</button>
            <button
              class="btn"
              :class="willLock ? 'btn-danger' : 'btn-success'"
              type="button"
              :disabled="isUpdating"
              @click="confirmToggle"
            >
              {{ isUpdating ? 'Đang xử lý...' : willLock ? 'Xác nhận khóa' : 'Xác nhận mở khóa' }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.users-page { display: grid; gap: var(--admin-space-5); font-family: var(--admin-font); }

.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--admin-space-4); flex-wrap: wrap; }
.page-heading > div > span { color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; text-transform: uppercase; letter-spacing: 0.07em; }
.page-heading h1 { margin: var(--admin-space-1) 0; color: var(--admin-text); font-size: var(--ocop-font-size-title-md); font-weight: 800; }
.page-heading p { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.page-heading > strong { padding: var(--admin-space-1) var(--admin-space-3); border-radius: var(--admin-radius-pill); background: var(--admin-primary-soft); color: var(--admin-primary-dark); font-size: var(--admin-font-xs); font-weight: 800; }

.filter-bar {
  display: grid;
  grid-template-columns: minmax(220px, 1fr) minmax(160px, 200px) minmax(160px, 200px);
  gap: var(--admin-space-3);
  padding: var(--admin-space-4);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-sm);
}
.filter-field { display: grid; gap: var(--admin-space-1); margin: 0; }
.filter-field > span { color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; }
.form-control, .form-select {
  width: 100%;
  min-height: var(--admin-control-height);
  padding: 0 var(--admin-space-3);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  transition: border-color var(--admin-transition);
}
.form-control:focus, .form-select:focus { border-color: var(--admin-primary); }

.btn {
  display: inline-flex;
  min-height: var(--admin-control-height);
  align-items: center;
  justify-content: center;
  gap: var(--admin-space-2);
  padding: 0 var(--admin-space-4);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: background var(--admin-transition), border-color var(--admin-transition), color var(--admin-transition);
}
.btn-success { border-color: var(--admin-success); background: var(--admin-success); color: var(--admin-on-primary); }
.btn-success:hover { background: var(--admin-success-hover); }
.btn-danger { border-color: var(--admin-danger-text); background: var(--admin-danger-text); color: var(--admin-on-primary); }
.btn-danger:hover { background: var(--admin-danger-hover); }
.btn-light { background: var(--admin-bg); color: var(--admin-text); }
.btn-light:hover { border-color: var(--admin-primary); color: var(--admin-primary-dark); }
.btn-outline-danger { border-color: var(--admin-danger-border); background: transparent; color: var(--admin-danger-text); }
.btn-outline-danger:hover { background: var(--admin-danger-soft); }
.btn:disabled { cursor: not-allowed; opacity: 0.55; }

.alert { display: flex; align-items: center; gap: var(--admin-space-2); margin: 0; padding: var(--admin-space-3) var(--admin-space-4); border-radius: var(--admin-radius-md); font-size: var(--admin-font-sm); }
.alert-success { border: 1px solid var(--admin-success-border); background: var(--admin-success-soft); color: var(--admin-success-text); }
.alert-danger { border: 1px solid var(--admin-danger-border); background: var(--admin-danger-soft); color: var(--admin-danger-text); }

.table-card { overflow: hidden; border: 1px solid var(--admin-border); border-radius: var(--admin-radius-lg); background: var(--admin-card); box-shadow: var(--admin-shadow-sm); }
.table { width: 100%; margin: 0; border-collapse: collapse; }
.table th {
  padding: var(--admin-space-3) var(--admin-space-5);
  border-bottom: 1px solid var(--admin-border);
  background: var(--admin-bg);
  color: var(--admin-muted);
  font-size: var(--admin-font-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-align: left;
  text-transform: uppercase;
  white-space: nowrap;
}
.table th.text-end { text-align: right; }
.table td { padding: var(--admin-space-3) var(--admin-space-5); border-bottom: 1px solid var(--admin-border-soft); color: var(--admin-text); font-size: var(--admin-font-sm); vertical-align: middle; }
.table tbody tr:last-child td { border-bottom: 0; }
.table tbody tr:hover td { background: var(--admin-bg); }
.table td strong { display: block; font-weight: 700; overflow-wrap: anywhere; }
.table td small { display: block; margin-top: var(--admin-space-1); color: var(--admin-muted); font-size: var(--admin-font-xs); overflow-wrap: anywhere; }
.cell-actions { text-align: right; }
.self-note { color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 600; }

.status-badge { display: inline-flex; padding: 3px var(--admin-space-3); border-radius: var(--admin-radius-pill); font-size: var(--admin-font-xs); font-weight: 700; white-space: nowrap; }
.status-approved { background: var(--admin-badge-approved-bg); color: var(--admin-badge-approved-text); }
.status-rejected { background: var(--admin-badge-rejected-bg); color: var(--admin-badge-rejected-text); }

.pagination-bar { display: flex; align-items: center; justify-content: flex-end; gap: var(--admin-space-3); color: var(--admin-muted); font-size: var(--admin-font-sm); font-weight: 600; }

.modal-layer { position: fixed; z-index: 200; inset: 0; display: grid; padding: var(--admin-space-5); place-items: center; overflow-y: auto; background: var(--admin-scrim); }
.confirm-dialog { width: min(100%, 480px); padding: var(--admin-space-6); border-radius: var(--admin-radius-lg); background: var(--admin-card); box-shadow: var(--admin-shadow-modal); }
.confirm-dialog h2 { margin: 0 0 var(--admin-space-3); color: var(--admin-text); font-size: var(--admin-font-xl); font-weight: 800; }
.dialog-body { display: grid; gap: var(--admin-space-2); margin-bottom: var(--admin-space-4); color: var(--admin-text); font-size: var(--admin-font-sm); }
.dialog-body p { margin: 0; overflow-wrap: anywhere; }
.dialog-note { padding: var(--admin-space-3); border-radius: var(--admin-radius-md); background: var(--admin-warning-soft); color: var(--admin-warning-text); }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--admin-space-2); margin-top: var(--admin-space-4); }

@media (max-width: 767.98px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .filter-bar { grid-template-columns: 1fr; }

  /* Điện thoại: mỗi tài khoản là một thẻ, nhãn cột hiện bên trái giá trị. */
  .users-table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .users-table tbody { display: grid; gap: var(--admin-space-3); padding: var(--admin-space-3); }
  .users-table tr { display: grid; gap: var(--admin-space-2); padding: var(--admin-space-4); border: 1px solid var(--admin-border); border-radius: var(--admin-radius-md); background: var(--admin-card); }
  .users-table tbody tr:hover td { background: transparent; }
  .users-table td { display: grid; grid-template-columns: minmax(96px, 35%) minmax(0, 1fr); gap: var(--admin-space-2); padding: 0; border: 0; text-align: left; }
  .users-table td::before { content: attr(data-label); color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; }
  .users-table td.cell-account { grid-template-columns: 1fr; }
  .users-table td.cell-account::before { content: none; }
  .users-table td.cell-actions { grid-template-columns: 1fr; padding-top: var(--admin-space-2); border-top: 1px solid var(--admin-border-soft); }
  .users-table td.cell-actions::before { content: none; }
  .users-table td.cell-actions .btn { width: 100%; }
  .pagination-bar { justify-content: space-between; }
}
</style>
