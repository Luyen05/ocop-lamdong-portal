<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { useDialogFocus } from '@/composables/useDialogFocus'
import { getApiErrorMessage } from '@/services/api-error'
import {
  cancelLocationChangeRequest,
  deleteLocationDraft,
  listMyLocationChangeRequests,
  listMyLocations,
  requestLocationDeletion,
  resubmitLocationChangeRequest,
} from '@/services/location-management'
import type {
  LocationChangeRequest,
  LocationWorkflowStatus,
  ManagedLocation,
} from '@/types/location-management'
import {
  LOCATION_STATUS_META,
  activeChangeRequest,
  formatDate,
} from '@/utils/location-workflow'

type Tab = 'all' | LocationWorkflowStatus

const locations = ref<ManagedLocation[]>([])
const changeRequests = ref<LocationChangeRequest[]>([])
const loading = ref(true)
const loadError = ref('')
const actionError = ref('')
const successMessage = ref('')
const actionId = ref<number | null>(null)
const tab = ref<Tab>('all')

const deletionTarget = ref<ManagedLocation | null>(null)
const deletionRevision = ref<LocationChangeRequest | null>(null)
const deletionReason = ref('')
const deletionDialog = ref<HTMLElement | null>(null)
const isDeletionOpen = computed(() => Boolean(deletionTarget.value))

const tabs: Array<{ value: Tab; label: string }> = [
  { value: 'all', label: 'Tất cả' },
  { value: 'draft', label: 'Bản nháp' },
  { value: 'pending', label: 'Chờ duyệt' },
  { value: 'needs_revision', label: 'Cần bổ sung' },
  { value: 'approved', label: 'Đã duyệt' },
  { value: 'rejected', label: 'Bị từ chối' },
]

const legend = [
  { key: 'draft', ...LOCATION_STATUS_META.draft },
  { key: 'pending', ...LOCATION_STATUS_META.pending },
  { key: 'needs_revision', ...LOCATION_STATUS_META.needs_revision },
  { key: 'approved', ...LOCATION_STATUS_META.approved },
  {
    key: 'approved-request',
    label: 'Đã duyệt · có yêu cầu cập nhật',
    tone: 'accent',
    hint: 'Bản cũ vẫn hiện trên bản đồ tới khi thay đổi được duyệt.',
  },
  { key: 'rejected', ...LOCATION_STATUS_META.rejected },
]

const visibleLocations = computed(() =>
  tab.value === 'all' ? locations.value : locations.value.filter((item) => item.status === tab.value),
)

function tabCount(value: Tab): number {
  return value === 'all' ? locations.value.length : locations.value.filter((item) => item.status === value).length
}

function requestOf(location: ManagedLocation): LocationChangeRequest | undefined {
  return activeChangeRequest(location, changeRequests.value)
}

function statusLabel(location: ManagedLocation): string {
  const request = requestOf(location)
  if (location.status === 'approved' && request) {
    const kind = request.request_type === 'update' ? 'yêu cầu cập nhật' : 'yêu cầu ngừng hiển thị'
    return request.status === 'needs_revision' ? `Đã duyệt · ${kind} cần bổ sung` : `Đã duyệt · có ${kind}`
  }
  return LOCATION_STATUS_META[location.status].label
}

function statusTone(location: ManagedLocation): string {
  if (location.status === 'approved' && requestOf(location)) return 'accent'
  return LOCATION_STATUS_META[location.status].tone
}

function summary(location: ManagedLocation): string {
  const parts = [location.district || 'Chưa chọn xã/phường']
  parts.push(location.images.length ? `${location.images.length} ảnh` : 'chưa có ảnh')
  return parts.join(' · ')
}

async function loadData(): Promise<void> {
  loading.value = true
  loadError.value = ''
  try {
    const [locationData, requestData] = await Promise.all([listMyLocations(), listMyLocationChangeRequests()])
    locations.value = locationData.items
    changeRequests.value = requestData.items
  } catch (error) {
    loadError.value = getApiErrorMessage(error, 'Không tải được danh sách điểm du lịch.')
  } finally {
    loading.value = false
  }
}

async function removeLocation(location: ManagedLocation): Promise<void> {
  if (!window.confirm(`Xóa điểm “${location.name}”? Thao tác này không hoàn tác được.`)) return
  actionId.value = location.id
  actionError.value = ''
  try {
    await deleteLocationDraft(location.id)
    successMessage.value = `Đã xóa “${location.name}”.`
    await loadData()
  } catch (error) {
    actionError.value = getApiErrorMessage(error, 'Không xóa được điểm du lịch.')
  } finally {
    actionId.value = null
  }
}

async function cancelRequest(location: ManagedLocation): Promise<void> {
  const request = requestOf(location)
  if (!request || !window.confirm('Hủy yêu cầu đang chờ xử lý?')) return
  actionId.value = location.id
  actionError.value = ''
  try {
    await cancelLocationChangeRequest(request.id)
    successMessage.value = 'Đã hủy yêu cầu.'
    await loadData()
  } catch (error) {
    actionError.value = getApiErrorMessage(error, 'Không hủy được yêu cầu.')
  } finally {
    actionId.value = null
  }
}

function openDeletion(location: ManagedLocation, revision?: LocationChangeRequest): void {
  deletionTarget.value = location
  deletionRevision.value = revision ?? null
  deletionReason.value = revision?.reason ?? ''
}

function closeDeletion(): void {
  deletionTarget.value = null
  deletionRevision.value = null
  deletionReason.value = ''
}

useDialogFocus(isDeletionOpen, deletionDialog, closeDeletion)

async function sendDeletion(): Promise<void> {
  const location = deletionTarget.value
  if (!location) return
  actionId.value = location.id
  actionError.value = ''
  try {
    if (deletionRevision.value) {
      await resubmitLocationChangeRequest(deletionRevision.value.id, {
        proposed_data: null,
        reason: deletionReason.value,
      })
      successMessage.value = 'Đã bổ sung lý do và gửi lại yêu cầu ngừng hiển thị.'
    } else {
      await requestLocationDeletion(location.id, deletionReason.value)
      successMessage.value = 'Đã gửi yêu cầu ngừng hiển thị. Điểm vẫn hiện trên bản đồ tới khi được duyệt.'
    }
    closeDeletion()
    await loadData()
  } catch (error) {
    actionError.value = getApiErrorMessage(error, 'Không gửi được yêu cầu ngừng hiển thị.')
  } finally {
    actionId.value = null
  }
}

onMounted(loadData)
</script>

<template>
  <div class="locations-page">
    <header class="page-head">
      <div>
        <h1>Điểm du lịch của tôi</h1>
        <p>Khai báo trang trại, vườn, cơ sở đón khách của đơn vị để hiện trên bản đồ số.</p>
      </div>
      <RouterLink class="btn-dark" to="/chu-the/diem-du-lich/khai-bao">
        <AppIcon name="map-pin" :size="16" /> Khai báo điểm mới
      </RouterLink>
    </header>

    <p v-if="successMessage" class="notice is-success" role="status">{{ successMessage }}</p>
    <p v-if="actionError" class="notice is-error" role="alert">{{ actionError }}</p>

    <div class="tabs" role="group" aria-label="Lọc theo trạng thái">
      <button
        v-for="item in tabs"
        :key="item.value"
        type="button"
        :aria-pressed="tab === item.value"
        :class="{ active: tab === item.value }"
        @click="tab = item.value"
      >
        {{ item.label }} <span class="count">{{ tabCount(item.value) }}</span>
      </button>
    </div>

    <section class="list-panel" aria-live="polite" :aria-busy="loading">
      <p v-if="loading" class="state">Đang tải danh sách điểm…</p>
      <div v-else-if="loadError" class="state is-error">
        <p>{{ loadError }}</p>
        <button type="button" class="btn-line" @click="loadData">Thử lại</button>
      </div>
      <div v-else-if="!visibleLocations.length" class="state">
        <p v-if="locations.length">Không có điểm nào ở trạng thái này.</p>
        <template v-else>
          <p><strong>Đơn vị chưa khai báo điểm du lịch nào.</strong></p>
          <p>Khai báo vườn, trang trại hoặc cơ sở đón khách để du khách tìm thấy trên bản đồ số.</p>
          <RouterLink class="btn-dark" to="/chu-the/diem-du-lich/khai-bao">Khai báo điểm đầu tiên</RouterLink>
        </template>
      </div>
      <table v-else class="location-table">
        <thead>
          <tr>
            <th scope="col">Điểm du lịch</th>
            <th scope="col">Loại hình</th>
            <th scope="col">Trạng thái</th>
            <th scope="col">Cập nhật</th>
            <th scope="col"><span class="visually-hidden">Thao tác</span></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="location in visibleLocations" :key="location.id">
            <td class="cell-name">
              <strong>{{ location.name }}</strong>
              <span>{{ summary(location) }}</span>
              <p v-if="location.review_note && ['needs_revision', 'rejected'].includes(location.status)" class="note">
                {{ location.reviewed_by_name || 'Quản trị viên' }}: {{ location.review_note }}
              </p>
              <p v-if="requestOf(location)?.review_note" class="note">
                Phản hồi yêu cầu: {{ requestOf(location)?.review_note }}
              </p>
            </td>
            <td data-label="Loại hình">{{ location.type_label }}</td>
            <td data-label="Trạng thái">
              <span :class="['status', `tone-${statusTone(location)}`]">{{ statusLabel(location) }}</span>
            </td>
            <td data-label="Cập nhật" class="cell-date">{{ formatDate(location.updated_at) }}</td>
            <td class="cell-actions">
              <template v-if="['draft', 'needs_revision'].includes(location.status)">
                <RouterLink class="btn-line" :to="`/chu-the/diem-du-lich/${location.id}`">
                  {{ location.status === 'draft' ? 'Tiếp tục khai báo' : 'Bổ sung hồ sơ' }}
                </RouterLink>
              </template>
              <RouterLink v-else-if="location.status === 'pending'" class="btn-line" :to="`/chu-the/diem-du-lich/${location.id}`">
                Xem hồ sơ
              </RouterLink>
              <template v-else-if="location.status === 'approved'">
                <template v-if="!requestOf(location)">
                  <RouterLink class="btn-line" :to="`/chu-the/diem-du-lich/${location.id}`">Đề nghị cập nhật</RouterLink>
                  <button type="button" class="btn-line is-danger" :disabled="actionId === location.id" @click="openDeletion(location)">
                    Đề nghị ngừng hiển thị
                  </button>
                </template>
                <template v-else>
                  <RouterLink
                    v-if="requestOf(location)?.status === 'needs_revision' && requestOf(location)?.request_type === 'update'"
                    class="btn-line"
                    :to="`/chu-the/diem-du-lich/yeu-cau/${requestOf(location)?.id}`"
                  >
                    Bổ sung yêu cầu
                  </RouterLink>
                  <button
                    v-if="requestOf(location)?.status === 'needs_revision' && requestOf(location)?.request_type === 'delete'"
                    type="button"
                    class="btn-line"
                    @click="openDeletion(location, requestOf(location))"
                  >
                    Bổ sung lý do
                  </button>
                  <button type="button" class="btn-line is-danger" :disabled="actionId === location.id" @click="cancelRequest(location)">
                    Hủy yêu cầu
                  </button>
                </template>
                <RouterLink class="btn-text" :to="`/diem-du-lich/${location.slug}`">Xem trang công khai</RouterLink>
              </template>
              <button
                v-if="['draft', 'needs_revision', 'rejected'].includes(location.status)"
                type="button"
                class="btn-text is-danger"
                :disabled="actionId === location.id"
                @click="removeLocation(location)"
              >
                Xóa
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <section class="legend" aria-labelledby="legend-title">
      <h2 id="legend-title">Các trạng thái của một điểm</h2>
      <dl>
        <div v-for="item in legend" :key="item.key">
          <dt><span :class="['status', `tone-${item.tone}`]">{{ item.label }}</span></dt>
          <dd>{{ item.hint }}</dd>
        </div>
      </dl>
    </section>

    <div v-if="deletionTarget" class="dialog-backdrop" role="presentation" @click.self="closeDeletion">
      <form
        ref="deletionDialog"
        class="dialog"
        role="dialog"
        aria-modal="true"
        aria-labelledby="deletion-title"
        tabindex="-1"
        @submit.prevent="sendDeletion"
      >
        <h2 id="deletion-title">{{ deletionRevision ? 'Bổ sung lý do ngừng hiển thị' : 'Đề nghị ngừng hiển thị' }}</h2>
        <p>“{{ deletionTarget.name }}” vẫn hiện trên bản đồ cho tới khi quản trị viên chấp thuận.</p>
        <label>
          Lý do
          <textarea v-model="deletionReason" required minlength="5" maxlength="1000" rows="4" />
        </label>
        <div class="dialog-actions">
          <button type="button" class="btn-line" @click="closeDeletion">Đóng</button>
          <button type="submit" class="btn-danger" :disabled="actionId === deletionTarget.id">
            {{ actionId === deletionTarget.id ? 'Đang gửi…' : deletionRevision ? 'Gửi lại yêu cầu' : 'Gửi yêu cầu' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<style scoped>
.locations-page { display: grid; gap: var(--ocop-space-6); color: var(--ocop-mist-950); }
.page-head { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--ocop-space-6); }
.page-head h1 { margin: 0 0 var(--ocop-space-1); font-size: var(--ocop-font-size-title-md); font-weight: 800; }
.page-head p { margin: 0; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-body); }

.btn-dark, .btn-line, .btn-danger, .btn-text {
  display: inline-flex; min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-4); align-items: center; justify-content: center;
  gap: var(--ocop-space-2); border-radius: var(--ocop-radius-sm); font-size: var(--ocop-font-size-small); font-weight: 700;
  text-decoration: none; white-space: nowrap; cursor: pointer;
}
.btn-dark { border: 0; background: var(--admin-primary); color: var(--admin-on-primary); }
.btn-dark:hover { background: var(--admin-primary-dark); color: var(--admin-on-primary); }
.btn-line { border: 1px solid var(--ocop-mist-300); background: var(--ocop-white); color: var(--ocop-mist-950); }
.btn-line:hover { border-color: var(--ocop-mist-600); color: var(--ocop-mist-950); }
.btn-text { border: 0; background: transparent; color: var(--ocop-mist-700); text-decoration: underline; }
.is-danger { color: var(--ocop-danger-strong); }
.btn-line.is-danger { border-color: var(--ocop-danger-border); }
.btn-danger { border: 0; background: var(--ocop-danger-strong); color: var(--ocop-white); }
button:disabled { cursor: not-allowed; opacity: 0.6; }
:is(a, button):focus-visible { outline: 3px solid var(--ocop-daquy-400); outline-offset: 2px; }

.notice { margin: 0; padding: var(--ocop-space-3) var(--ocop-space-4); border-radius: var(--ocop-radius-sm); font-size: var(--ocop-font-size-small); }
.notice.is-success { background: var(--ocop-success-soft); color: var(--ocop-success); }
.notice.is-error { background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); }

.tabs { display: flex; gap: var(--ocop-space-1); overflow-x: auto; border-bottom: 1px solid var(--ocop-mist-200); scrollbar-width: thin; }
.tabs button { display: inline-flex; min-height: var(--ocop-control-lg); margin-bottom: -1px; padding: 0 var(--ocop-space-4); flex: 0 0 auto; align-items: center; gap: var(--ocop-space-2); border: 0; border-bottom: 3px solid transparent; background: transparent; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-body); }
.tabs button.active { border-bottom-color: var(--ocop-mist-950); color: var(--ocop-mist-950); font-weight: 700; }
.count { min-width: 24px; padding: 0 var(--ocop-space-2); border-radius: var(--ocop-radius-pill); background: var(--ocop-mist-100); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.tabs button.active .count { background: var(--ocop-daquy-400); color: var(--ocop-mist-950); }

.list-panel { overflow: hidden; border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-lg); background: var(--ocop-white); }
.state { display: grid; padding: var(--ocop-space-12) var(--ocop-space-6); justify-items: center; gap: var(--ocop-space-2); color: var(--ocop-mist-700); text-align: center; }
.state p { margin: 0; }
.state.is-error { color: var(--ocop-danger-strong); }
.location-table { width: 100%; border-collapse: collapse; font-size: var(--ocop-font-size-small); }
.location-table th { padding: var(--ocop-space-3) var(--ocop-space-5); background: var(--ocop-mist-50); color: var(--ocop-mist-700); font-weight: 600; text-align: left; }
.location-table td { padding: var(--ocop-space-4) var(--ocop-space-5); border-top: 1px solid var(--ocop-mist-100); vertical-align: top; }
.cell-name strong { display: block; font-size: var(--ocop-font-size-body); }
.cell-name > span { color: var(--ocop-mist-600); }
.cell-date { color: var(--ocop-mist-700); white-space: nowrap; }
.note { max-width: 46ch; margin: var(--ocop-space-2) 0 0; padding: var(--ocop-space-2) var(--ocop-space-3); border-radius: var(--ocop-radius-sm); background: var(--ocop-warning-soft); color: var(--ocop-mist-900); }
.cell-actions { display: flex; flex-wrap: wrap; justify-content: flex-end; gap: var(--ocop-space-2); }

.status { display: inline-block; padding: var(--ocop-space-1) var(--ocop-space-3); border: 1px solid transparent; border-radius: var(--ocop-radius-pill); font-size: var(--ocop-font-size-caption); font-weight: 700; white-space: nowrap; }
.tone-neutral { background: var(--ocop-mist-100); color: var(--ocop-mist-800); }
.tone-info { background: var(--ocop-tone-sky-soft); color: var(--ocop-tone-sky); }
.tone-warning { background: var(--ocop-warning-soft); color: var(--ocop-warning); }
.tone-success { background: var(--ocop-success-soft); color: var(--ocop-success); }
.tone-accent { border-color: var(--ocop-daquy-300); background: var(--ocop-daquy-50); color: var(--ocop-mist-900); }
.tone-danger { background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); }

.legend { display: grid; gap: var(--ocop-space-3); padding: var(--ocop-space-5) var(--ocop-space-6); border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-lg); background: var(--ocop-white); }
.legend h2 { margin: 0; font-size: var(--ocop-font-size-body-lg); font-weight: 700; }
.legend dl { display: grid; margin: 0; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--ocop-space-4); }
.legend dt { font-weight: 400; }
.legend dd { margin: var(--ocop-space-2) 0 0; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); line-height: 1.5; }

.dialog-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; padding: var(--ocop-space-5); place-items: center; background: color-mix(in srgb, var(--ocop-mist-950) 55%, transparent); }
.dialog { display: grid; width: min(100%, 500px); gap: var(--ocop-space-3); padding: var(--ocop-space-6); border-radius: var(--ocop-radius-lg); background: var(--ocop-white); box-shadow: var(--ocop-shadow-overlay); }
.dialog h2 { margin: 0; font-size: var(--ocop-font-size-title-sm); }
.dialog p { margin: 0; color: var(--ocop-mist-700); }
.dialog label { display: grid; gap: var(--ocop-space-2); font-weight: 600; }
.dialog textarea { padding: var(--ocop-space-3); border: 1px solid var(--ocop-mist-300); border-radius: var(--ocop-radius-sm); font: inherit; resize: vertical; }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--ocop-space-2); }

@media (max-width: 991.98px) {
  .legend dl { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
@media (max-width: 767.98px) {
  .page-head { flex-direction: column; align-items: stretch; }
  .location-table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); }
  .location-table, .location-table tbody, .location-table tr, .location-table td { display: block; }
  .location-table tr { padding: var(--ocop-space-4); border-top: 1px solid var(--ocop-mist-100); }
  .location-table tr:first-child { border-top: 0; }
  .location-table td { padding: var(--ocop-space-1) 0; border: 0; }
  .location-table td[data-label]::before { content: attr(data-label) ": "; color: var(--ocop-mist-600); }
  .cell-actions { justify-content: flex-start; padding-top: var(--ocop-space-3) !important; }
  .legend dl { grid-template-columns: 1fr; }
}
</style>
