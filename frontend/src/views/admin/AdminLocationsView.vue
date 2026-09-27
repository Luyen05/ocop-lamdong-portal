<script setup lang="ts">
import { computed, nextTick, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import LocationPicker from '@/components/location-management/LocationPicker.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import {
  getAdminLocation,
  getAdminLocationChangeRequest,
  listAdminLocationChangeRequests,
  listAdminLocations,
  moderateLocation,
  moderateLocationChangeRequest,
} from '@/services/location-management'
import type {
  LocationChangeRequest,
  LocationModerationStatus,
  LocationPositionCheck,
  LocationWorkflowStatus,
  ManagedLocation,
} from '@/types/location-management'
import { formatTicketPrice, locationTypeStyle } from '@/utils/location'
import {
  LOCATION_SOURCE_LABELS,
  LOCATION_STATUS_META,
  LOCATION_TYPE_OPTIONS,
  formatAccuracy,
  formatCoordinate,
  formatDateTime,
  googleMapsUrl,
  nearestLabel,
} from '@/utils/location-workflow'
import { formatDistance } from '@/utils/location'

type Tab = 'pending' | 'requests' | 'needs_revision' | 'approved' | 'rejected'

const route = useRoute()

const tabs: Array<{ value: Tab; label: string }> = [
  { value: 'pending', label: 'Chờ duyệt' },
  { value: 'requests', label: 'Yêu cầu cập nhật' },
  { value: 'needs_revision', label: 'Cần bổ sung' },
  { value: 'approved', label: 'Đã duyệt' },
  { value: 'rejected', label: 'Bị từ chối' },
]

const decisionOptions: Array<{ value: LocationModerationStatus; label: string; hint: string }> = [
  { value: 'approved', label: 'Duyệt', hint: 'Hiện ngay trên bản đồ công khai' },
  { value: 'needs_revision', label: 'Cần bổ sung', hint: 'Trả lại cho chủ thể sửa, kèm ghi chú' },
  { value: 'rejected', label: 'Từ chối', hint: 'Không hiển thị, kèm lý do' },
]

const tab = ref<Tab>(isTab(route.query.tab) ? route.query.tab : 'pending')
const search = ref('')
const locations = ref<ManagedLocation[]>([])
const requests = ref<LocationChangeRequest[]>([])
const statusCounts = ref<Partial<Record<LocationWorkflowStatus, number>>>({})
const pendingRequestCount = ref(0)
const listLoading = ref(true)
const listError = ref('')

const selectedId = ref<number | null>(null)
const selectedLocation = ref<ManagedLocation | null>(null)
const selectedRequest = ref<LocationChangeRequest | null>(null)
const detailLoading = ref(false)
const detailError = ref('')
const detailPanel = ref<HTMLElement | null>(null)

const decision = ref<LocationModerationStatus>('approved')
const note = ref('')
const submitting = ref(false)
const decisionError = ref('')
const successMessage = ref('')
const adjusting = ref(false)
const adjustedPosition = ref<{ latitude: number; longitude: number } | null>(null)

const isRequestTab = computed(() => tab.value === 'requests')
const listItems = computed(() => (isRequestTab.value ? requests.value : locations.value))
const canModerate = computed(() =>
  isRequestTab.value ? selectedRequest.value?.status === 'pending' : selectedLocation.value?.status === 'pending',
)

const mapLatitude = computed(() => adjustedPosition.value?.latitude ?? selectedLocation.value?.latitude ?? null)
const mapLongitude = computed(() => adjustedPosition.value?.longitude ?? selectedLocation.value?.longitude ?? null)

const noteCopy = computed(() => {
  if (decision.value === 'approved') {
    return {
      label: 'Ghi chú cho chủ thể (không bắt buộc)',
      placeholder: 'Ví dụ: đã chỉnh ghim về đúng cổng vào.',
      submit: isRequestTab.value ? 'Duyệt và áp dụng thay đổi' : 'Duyệt và hiện trên bản đồ',
    }
  }
  if (decision.value === 'needs_revision') {
    return {
      label: 'Cần bổ sung những gì? *',
      placeholder: 'Ví dụ: ghim đang ở giữa vườn, vui lòng đặt lại đúng cổng vào và thêm ảnh cổng.',
      submit: 'Gửi yêu cầu bổ sung',
    }
  }
  return {
    label: 'Lý do từ chối *',
    placeholder: 'Ví dụ: không phải điểm đón khách tham quan.',
    submit: isRequestTab.value ? 'Từ chối yêu cầu' : 'Từ chối điểm',
  }
})

function isTab(value: unknown): value is Tab {
  return typeof value === 'string' && tabs.some((item) => item.value === value)
}

function tabCount(value: Tab): number {
  return value === 'requests' ? pendingRequestCount.value : statusCounts.value[value] ?? 0
}

function typeLabel(value: string): string {
  return LOCATION_TYPE_OPTIONS.find((option) => option.value === value)?.label ?? value
}

function sourceLabel(value: string | null | undefined): string {
  return value ? LOCATION_SOURCE_LABELS[value as keyof typeof LOCATION_SOURCE_LABELS] ?? value : 'Chưa có'
}

function price(value: string | number | null | undefined): string {
  return value === null || value === undefined || value === '' ? 'Liên hệ' : formatTicketPrice(Number(value))
}

function itemKey(item: ManagedLocation | LocationChangeRequest): number {
  return item.id
}

async function loadList(): Promise<void> {
  listLoading.value = true
  listError.value = ''
  try {
    const [locationData, requestData] = await Promise.all([
      listAdminLocations({
        status: isRequestTab.value ? 'pending' : (tab.value as LocationWorkflowStatus),
        search: search.value.trim() || undefined,
        page_size: 100,
      }),
      listAdminLocationChangeRequests('pending'),
    ])
    statusCounts.value = locationData.status_counts
    pendingRequestCount.value = requestData.total
    locations.value = locationData.items
    requests.value = requestData.items
    const first = listItems.value[0]
    if (!listItems.value.some((item) => item.id === selectedId.value)) {
      await select(first ? itemKey(first) : null)
    }
  } catch (error) {
    listError.value = getApiErrorMessage(error, 'Không tải được hàng đợi điểm du lịch.')
  } finally {
    listLoading.value = false
  }
}

async function select(id: number | null, focusDetail = false): Promise<void> {
  selectedId.value = id
  selectedLocation.value = null
  selectedRequest.value = null
  detailError.value = ''
  decisionError.value = ''
  decision.value = 'approved'
  note.value = ''
  adjusting.value = false
  adjustedPosition.value = null
  if (id === null) return
  detailLoading.value = true
  try {
    if (isRequestTab.value) {
      selectedRequest.value = await getAdminLocationChangeRequest(id)
    } else {
      selectedLocation.value = await getAdminLocation(id)
    }
  } catch (error) {
    detailError.value = getApiErrorMessage(error, 'Không tải được chi tiết.')
  } finally {
    detailLoading.value = false
  }
  if (focusDetail) {
    await nextTick()
    detailPanel.value?.focus({ preventScroll: true })
    detailPanel.value?.scrollIntoView?.({ block: 'start' })
  }
}

function onPick(position: { latitude: number; longitude: number }): void {
  if (adjusting.value) adjustedPosition.value = position
}

function toggleAdjust(): void {
  if (adjusting.value) adjustedPosition.value = null
  adjusting.value = !adjusting.value
}

async function submitDecision(): Promise<void> {
  decisionError.value = ''
  const trimmed = note.value.trim()
  if (decision.value !== 'approved' && !trimmed) {
    decisionError.value = 'Cần nhập ghi chú khi yêu cầu bổ sung hoặc từ chối.'
    return
  }
  submitting.value = true
  try {
    if (isRequestTab.value && selectedRequest.value) {
      await moderateLocationChangeRequest(selectedRequest.value.id, { status: decision.value, note: trimmed || null })
    } else if (selectedLocation.value) {
      await moderateLocation(selectedLocation.value.id, {
        status: decision.value,
        note: trimmed || null,
        ...(adjustedPosition.value ?? {}),
      })
    }
    const name = selectedLocation.value?.name ?? selectedRequest.value?.location_name ?? ''
    const verb = decision.value === 'approved' ? 'Đã duyệt' : decision.value === 'needs_revision' ? 'Đã trả lại để bổ sung' : 'Đã từ chối'
    successMessage.value = `${verb}: ${name}.`
    selectedId.value = null
    await loadList()
  } catch (error) {
    decisionError.value = getApiErrorMessage(error, 'Không lưu được quyết định.')
  } finally {
    submitting.value = false
  }
}

function changedRows(request: LocationChangeRequest) {
  const current = request.current_data
  const proposed = (request.proposed_data ?? {}) as Record<string, unknown>
  const value = (key: string) => proposed[key] as never
  const rows = [
    { label: 'Tên điểm', before: current.name, after: value('name') },
    { label: 'Loại hình', before: typeLabel(current.type), after: typeLabel(String(value('type') ?? '')) },
    {
      label: 'Vị trí',
      before: formatCoordinate(current.latitude, current.longitude),
      after: formatCoordinate((value('latitude') as number | null) ?? null, (value('longitude') as number | null) ?? null),
    },
    { label: 'Cách lấy vị trí', before: sourceLabel(current.location_source), after: sourceLabel(value('location_source')) },
    { label: 'Xã / phường', before: current.district ?? '—', after: value('district') ?? '—' },
    { label: 'Địa chỉ', before: current.address ?? '—', after: value('address') ?? '—' },
    { label: 'Mô tả', before: current.description ?? '—', after: value('description') ?? '—' },
    { label: 'Giờ mở cửa', before: current.opening_hours ?? '—', after: value('opening_hours') ?? '—' },
    { label: 'Giá vé', before: price(current.ticket_price), after: price(value('ticket_price')) },
    { label: 'Điện thoại', before: current.contact_phone ?? '—', after: value('contact_phone') ?? '—' },
    { label: 'Dịch vụ', before: current.services.join(', ') || '—', after: ((value('services') as string[] | undefined) ?? []).join(', ') || '—' },
    { label: 'Trang web', before: current.website ?? '—', after: value('website') ?? '—' },
    {
      label: 'Ảnh',
      before: `${current.images.length} ảnh`,
      after: `${((value('images') as unknown[] | undefined) ?? []).length} ảnh`,
    },
    {
      label: 'Sản phẩm OCOP gắn kèm',
      before: `${current.product_ids.length} sản phẩm`,
      after: `${((value('product_ids') as unknown[] | undefined) ?? []).length} sản phẩm`,
    },
  ]
  return rows.map((row) => ({ ...row, after: String(row.after ?? '—'), changed: String(row.before) !== String(row.after ?? '—') }))
}

function checkItems(check: LocationPositionCheck | null) {
  if (!check) return []
  const items = [
    check.inside_lam_dong
      ? { ok: true, text: 'Nằm trong tỉnh Lâm Đồng' }
      : { ok: false, text: 'Nằm ngoài khung tỉnh Lâm Đồng: không duyệt được, cần chủ thể đặt lại ghim' },
  ]
  if (check.nearest) {
    items.push(
      check.duplicate_warning
        ? { ok: false, text: `Có thể trùng “${check.nearest.name}” (cách ${formatDistance(check.nearest.distance_m)})` }
        : { ok: true, text: `Không trùng điểm đã duyệt (gần nhất ${nearestLabel(check.nearest.distance_m)}: ${check.nearest.name})` },
    )
  }
  return items
}

watch(tab, () => {
  selectedId.value = null
  successMessage.value = ''
  void loadList()
})

onMounted(loadList)
</script>

<template>
  <div class="review-page">
    <header class="page-head">
      <div>
        <h1>Duyệt điểm du lịch</h1>
        <p>Kiểm tra vị trí trên bản đồ trước khi cho hiện công khai.</p>
      </div>
      <form class="search" role="search" @submit.prevent="loadList">
        <label for="location-search" class="visually-hidden">Tìm theo tên điểm, địa chỉ hoặc đơn vị</label>
        <input id="location-search" v-model="search" type="search" placeholder="Tìm tên điểm, địa chỉ, đơn vị" />
        <button type="submit" class="btn-line"><AppIcon name="search" :size="16" /> Tìm</button>
      </form>
    </header>

    <p v-if="successMessage" class="notice is-success" role="status">{{ successMessage }}</p>

    <div class="tabs" role="group" aria-label="Hàng đợi">
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

    <div class="review-grid">
      <section class="queue" aria-label="Danh sách" :aria-busy="listLoading">
        <p v-if="listLoading" class="state">Đang tải…</p>
        <div v-else-if="listError" class="state is-error" role="alert">
          <p>{{ listError }}</p>
          <button type="button" class="btn-line" @click="loadList">Thử lại</button>
        </div>
        <p v-else-if="!listItems.length" class="state">
          {{ isRequestTab ? 'Không có yêu cầu cập nhật nào đang chờ.' : 'Không có điểm nào ở mục này.' }}
        </p>
        <ul v-else>
          <template v-if="isRequestTab">
            <li v-for="request in requests" :key="request.id">
              <button type="button" :class="['queue-item', { active: selectedId === request.id }]" :aria-current="selectedId === request.id" @click="select(request.id, true)">
                <strong>{{ request.location_name }}</strong>
                <span>{{ request.subject_name }}</span>
                <span class="tags">
                  <span class="tag">{{ request.request_type === 'update' ? 'Cập nhật thông tin' : 'Ngừng hiển thị' }}</span>
                </span>
                <small>Gửi lúc {{ formatDateTime(request.submitted_at) }}</small>
              </button>
            </li>
          </template>
          <template v-else>
            <li v-for="location in locations" :key="location.id">
              <button type="button" :class="['queue-item', { active: selectedId === location.id }]" :aria-current="selectedId === location.id" @click="select(location.id, true)">
                <strong>{{ location.name }}</strong>
                <span>{{ location.subject?.name || 'Chưa gắn đơn vị' }}</span>
                <span class="tags">
                  <span class="tag">{{ location.version > 1 ? 'Đã từng duyệt' : 'Điểm mới' }}</span>
                  <span v-if="location.location_source" class="tag is-sky">{{ sourceLabel(location.location_source) }}</span>
                  <span v-if="location.position_check?.duplicate_warning" class="tag is-warning">Có thể trùng</span>
                  <span v-if="location.position_check && !location.position_check.inside_lam_dong" class="tag is-danger">Ngoài tỉnh</span>
                </span>
                <small>Gửi lúc {{ formatDateTime(location.submitted_at) }}</small>
              </button>
            </li>
          </template>
        </ul>
      </section>

      <article ref="detailPanel" class="detail" tabindex="-1" aria-live="polite">
        <p v-if="detailLoading" class="state">Đang tải chi tiết…</p>
        <div v-else-if="detailError" class="state is-error" role="alert">
          <p>{{ detailError }}</p>
          <button type="button" class="btn-line" @click="select(selectedId)">Thử lại</button>
        </div>
        <p v-else-if="!selectedLocation && !selectedRequest" class="state">Chọn một mục trong danh sách để xem chi tiết.</p>

        <template v-else-if="selectedLocation">
          <header class="detail-head">
            <div>
              <h2>{{ selectedLocation.name }}</h2>
              <span>
                <span class="type-dot" :style="{ background: locationTypeStyle(selectedLocation.type).color }" aria-hidden="true" />
                {{ selectedLocation.type_label }} · {{ selectedLocation.subject?.name || 'Chưa gắn đơn vị' }}
                <template v-if="selectedLocation.subject"> · {{ selectedLocation.subject.phone }}</template>
              </span>
            </div>
            <span :class="['status', `tone-${LOCATION_STATUS_META[selectedLocation.status].tone}`]">
              {{ LOCATION_STATUS_META[selectedLocation.status].label }}
            </span>
          </header>

          <p v-if="selectedLocation.subject && (!selectedLocation.subject.is_active || selectedLocation.subject.status !== 'approved')" class="notice is-error">
            Tài khoản đơn vị đã bị khóa hoặc không còn được duyệt nên không duyệt được điểm này.
          </p>

          <div class="position-grid">
            <div class="map-col">
              <div class="map-box">
                <LocationPicker
                  :latitude="mapLatitude"
                  :longitude="mapLongitude"
                  :accuracy="adjustedPosition ? null : selectedLocation.location_accuracy_m"
                  :readonly="!adjusting"
                  label="Bản đồ vị trí điểm chủ thể khai báo"
                  @pick="onPick"
                />
                <div class="map-actions">
                  <button v-if="canModerate" type="button" class="btn-line" :aria-pressed="adjusting" @click="toggleAdjust">
                    {{ adjusting ? 'Hủy chỉnh vị trí' : 'Chỉnh vị trí' }}
                  </button>
                  <a
                    v-if="selectedLocation.latitude !== null && selectedLocation.longitude !== null"
                    class="btn-line"
                    :href="googleMapsUrl(selectedLocation.latitude, selectedLocation.longitude)"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Mở trên Google Maps<span class="visually-hidden"> (mở tab mới)</span>
                  </a>
                </div>
              </div>
              <p class="hint">
                <template v-if="adjusting">Bấm vào bản đồ hoặc kéo ghim tới đúng cổng vào. Tọa độ mới được lưu kèm ghi chú duyệt để chủ thể biết.</template>
                <template v-else>“Chỉnh vị trí” cho phép kéo ghim; tọa độ mới được lưu kèm ghi chú duyệt để chủ thể biết.</template>
              </p>
              <p v-if="adjustedPosition" class="notice is-info">
                Vị trí mới: <strong class="num">{{ formatCoordinate(adjustedPosition.latitude, adjustedPosition.longitude) }}</strong>
              </p>
            </div>
            <div class="facts-col">
              <dl class="facts">
                <dt>Tọa độ</dt><dd class="num">{{ formatCoordinate(selectedLocation.latitude, selectedLocation.longitude) }}</dd>
                <dt>Cách lấy</dt><dd>{{ sourceLabel(selectedLocation.location_source) }}</dd>
                <dt>Độ chính xác</dt><dd>{{ formatAccuracy(selectedLocation.location_accuracy_m) }}</dd>
                <dt>Địa chỉ</dt><dd>{{ [selectedLocation.address, selectedLocation.district].filter(Boolean).join(', ') || '—' }}</dd>
              </dl>
              <ul class="checks">
                <li v-for="item in checkItems(selectedLocation.position_check)" :key="item.text" :class="item.ok ? 'ok' : 'warn'">
                  <span class="check-mark" aria-hidden="true">{{ item.ok ? '✓' : '!' }}</span>{{ item.text }}
                </li>
                <li class="warn"><span class="check-mark" aria-hidden="true">!</span>Cần đối chiếu: ghim có khớp địa chỉ và ảnh chụp tại điểm không</li>
              </ul>
            </div>
          </div>

          <section class="content" aria-labelledby="content-title">
            <h3 id="content-title">Nội dung chủ thể khai báo</h3>
            <div class="wide"><span>Mô tả</span><p>{{ selectedLocation.description || '—' }}</p></div>
            <div><span>Giờ mở cửa · Giá vé</span><p>{{ selectedLocation.opening_hours || 'Chưa ghi' }} · {{ price(selectedLocation.ticket_price) }}</p></div>
            <div><span>Dịch vụ</span><p>{{ selectedLocation.services.join(', ') || '—' }}</p></div>
            <div><span>Điện thoại</span><p>{{ selectedLocation.contact_phone || '—' }}</p></div>
            <div><span>Sản phẩm OCOP tại điểm</span><p>{{ selectedLocation.products.map((product) => product.name).join(', ') || 'Không gắn sản phẩm' }}</p></div>
            <div class="wide">
              <span>Ảnh (bấm để xem lớn)</span>
              <ul v-if="selectedLocation.images.length" class="photos">
                <li v-for="(image, index) in selectedLocation.images" :key="image.id">
                  <a :href="image.image_url" target="_blank" rel="noopener noreferrer">
                    <img :src="image.image_url" :alt="`Ảnh ${index + 1}${image.is_primary ? ' (ảnh chính)' : ''} của ${selectedLocation.name}, mở tab mới`" loading="lazy" />
                  </a>
                </li>
              </ul>
              <p v-else>Chưa có ảnh.</p>
            </div>
            <div v-if="selectedLocation.review_note" class="wide"><span>Ghi chú duyệt gần nhất</span><p class="pre">{{ selectedLocation.review_note }}</p></div>
          </section>
        </template>

        <template v-else-if="selectedRequest">
          <header class="detail-head">
            <div>
              <h2>{{ selectedRequest.location_name }}</h2>
              <span>{{ selectedRequest.subject_name }} · gửi lúc {{ formatDateTime(selectedRequest.submitted_at) }}</span>
            </div>
            <span class="status tone-accent">{{ selectedRequest.request_type === 'update' ? 'Yêu cầu cập nhật' : 'Yêu cầu ngừng hiển thị' }}</span>
          </header>
          <p class="notice is-info">
            Bản đang hiển thị giữ nguyên tới khi yêu cầu được duyệt.
            <RouterLink :to="`/diem-du-lich/${selectedRequest.location_slug}`">Xem trang công khai hiện tại</RouterLink>
          </p>
          <div v-if="selectedRequest.reason" class="reason"><span>Lý do của đơn vị</span><p>{{ selectedRequest.reason }}</p></div>
          <template v-if="selectedRequest.request_type === 'update'">
            <ul class="checks">
              <li v-for="item in checkItems(selectedRequest.proposed_position_check)" :key="item.text" :class="item.ok ? 'ok' : 'warn'">
                <span class="check-mark" aria-hidden="true">{{ item.ok ? '✓' : '!' }}</span>{{ item.text }}
              </li>
            </ul>
            <div class="compare-wrap">
              <table class="compare">
                <caption class="visually-hidden">So sánh thông tin hiện tại và đề xuất</caption>
                <thead><tr><th scope="col">Thông tin</th><th scope="col">Đang hiển thị</th><th scope="col">Đề xuất</th></tr></thead>
                <tbody>
                  <tr v-for="row in changedRows(selectedRequest)" :key="row.label" :class="{ changed: row.changed }">
                    <th scope="row">{{ row.label }}<span v-if="row.changed" class="visually-hidden"> (có thay đổi)</span></th>
                    <td>{{ row.before }}</td>
                    <td>{{ row.after }}</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </template>
          <p v-else class="notice is-warning">Nếu duyệt, điểm sẽ bị gỡ khỏi bản đồ công khai (dữ liệu vẫn được lưu).</p>
        </template>

        <section v-if="canModerate && (selectedLocation || selectedRequest)" class="decision" aria-labelledby="decision-title">
          <h3 id="decision-title">Quyết định</h3>
          <div class="decision-options" role="radiogroup" aria-label="Quyết định duyệt">
            <button
              v-for="option in decisionOptions"
              :key="option.value"
              type="button"
              role="radio"
              :aria-checked="decision === option.value"
              :class="['decision-option', `is-${option.value}`, { active: decision === option.value }]"
              @click="decision = option.value"
            >
              <strong>{{ option.label }}</strong>
              <span>{{ option.hint }}</span>
            </button>
          </div>
          <label>
            {{ noteCopy.label }}
            <textarea v-model="note" rows="3" maxlength="2000" :placeholder="noteCopy.placeholder" />
          </label>
          <p v-if="decisionError" class="notice is-error" role="alert">{{ decisionError }}</p>
          <div class="decision-submit">
            <button type="button" :class="['btn-submit', `is-${decision}`]" :disabled="submitting" @click="submitDecision">
              {{ submitting ? 'Đang lưu…' : noteCopy.submit }}
            </button>
          </div>
        </section>
      </article>
    </div>
  </div>
</template>

<style scoped>
.review-page { display: grid; gap: var(--ocop-space-5); color: var(--ocop-mist-950); }
.page-head { display: flex; flex-wrap: wrap; align-items: flex-end; justify-content: space-between; gap: var(--ocop-space-4); }
.page-head h1 { margin: 0 0 var(--ocop-space-1); font-size: var(--ocop-font-size-title-md); font-weight: 800; }
.page-head p { margin: 0; color: var(--ocop-mist-700); }
.search { display: flex; gap: var(--ocop-space-2); }
.search input { width: min(320px, 60vw); min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-3); border: 1px solid var(--ocop-mist-300); border-radius: var(--ocop-radius-sm); font: inherit; }

.btn-line { display: inline-flex; min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-4); align-items: center; justify-content: center; gap: var(--ocop-space-2); border: 1px solid var(--ocop-mist-300); border-radius: var(--ocop-radius-sm); background: var(--ocop-white); color: var(--ocop-mist-950); font-size: var(--ocop-font-size-small); font-weight: 700; text-decoration: none; white-space: nowrap; }
.btn-line[aria-pressed='true'] { border-color: var(--ocop-mist-950); background: var(--ocop-daquy-50); }
:is(a, button, input, textarea):focus-visible { outline: 3px solid var(--ocop-daquy-400); outline-offset: 2px; }

.notice { margin: 0; padding: var(--ocop-space-3) var(--ocop-space-4); border-radius: var(--ocop-radius-sm); font-size: var(--ocop-font-size-small); line-height: 1.5; }
.notice.is-success { background: var(--ocop-success-soft); color: var(--ocop-success); }
.notice.is-error { background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); }
.notice.is-info { background: var(--ocop-tone-sky-soft); color: var(--ocop-mist-900); }
.notice.is-warning { background: var(--ocop-warning-soft); color: var(--ocop-mist-900); }
.notice a { color: var(--ocop-mist-900); }

.tabs { display: flex; gap: var(--ocop-space-1); overflow-x: auto; border-bottom: 1px solid var(--ocop-mist-200); }
.tabs button { display: inline-flex; min-height: var(--ocop-control-lg); margin-bottom: -1px; padding: 0 var(--ocop-space-4); flex: 0 0 auto; align-items: center; gap: var(--ocop-space-2); border: 0; border-bottom: 3px solid transparent; background: transparent; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-body); }
.tabs button.active { border-bottom-color: var(--ocop-mist-950); color: var(--ocop-mist-950); font-weight: 700; }
.count { min-width: 24px; padding: 0 var(--ocop-space-2); border-radius: var(--ocop-radius-pill); background: var(--ocop-mist-100); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.tabs button.active .count { background: var(--ocop-daquy-400); color: var(--ocop-mist-950); }

.review-grid { display: grid; grid-template-columns: 320px minmax(0, 1fr); align-items: start; gap: var(--ocop-space-6); }
.queue ul { display: grid; margin: 0; padding: 0; gap: var(--ocop-space-2); list-style: none; }
.queue-item { display: grid; width: 100%; padding: var(--ocop-space-4); gap: 6px; border: 2px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-md); background: var(--ocop-white); color: var(--ocop-mist-950); text-align: left; }
.queue-item.active { border-color: var(--ocop-mist-950); }
.queue-item strong { font-size: var(--ocop-font-size-body); }
.queue-item > span:not(.tags) { color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); }
.queue-item small { color: var(--ocop-mist-600); font-size: var(--ocop-font-size-caption); }
.tags { display: flex; flex-wrap: wrap; gap: 6px; }
.tag { padding: 2px var(--ocop-space-2); border-radius: var(--ocop-radius-pill); background: var(--ocop-mist-100); color: var(--ocop-mist-800); font-size: var(--ocop-font-size-caption); }
.tag.is-sky { background: var(--ocop-tone-sky-soft); color: var(--ocop-tone-sky); }
.tag.is-warning { background: var(--ocop-warning-soft); color: var(--ocop-warning); }
.tag.is-danger { background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); }

.state { display: grid; margin: 0; padding: var(--ocop-space-8) var(--ocop-space-4); justify-items: center; gap: var(--ocop-space-3); border: 1px dashed var(--ocop-mist-300); border-radius: var(--ocop-radius-md); background: var(--ocop-white); color: var(--ocop-mist-700); text-align: center; }
.state p { margin: 0; }
.state.is-error { color: var(--ocop-danger-strong); }

.detail { display: grid; min-width: 0; gap: var(--ocop-space-5); padding: var(--ocop-space-6); border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-lg); background: var(--ocop-white); scroll-margin-top: var(--ocop-space-4); }
.detail:focus { outline: none; }
.detail > .state { border: 0; }
.detail-head { display: flex; flex-wrap: wrap; align-items: flex-start; justify-content: space-between; gap: var(--ocop-space-4); }
.detail-head h2 { margin: 0 0 var(--ocop-space-1); font-size: var(--ocop-font-size-title-md); font-weight: 800; }
.detail-head > div > span { color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); }
.type-dot { display: inline-block; width: 10px; height: 10px; margin-right: 4px; border-radius: 50%; }
.status { display: inline-block; padding: var(--ocop-space-1) var(--ocop-space-3); border: 1px solid transparent; border-radius: var(--ocop-radius-pill); font-size: var(--ocop-font-size-caption); font-weight: 700; white-space: nowrap; }
.tone-neutral { background: var(--ocop-mist-100); color: var(--ocop-mist-800); }
.tone-info { background: var(--ocop-tone-sky-soft); color: var(--ocop-tone-sky); }
.tone-warning { background: var(--ocop-warning-soft); color: var(--ocop-warning); }
.tone-success { background: var(--ocop-success-soft); color: var(--ocop-success); }
.tone-accent { border-color: var(--ocop-daquy-300); background: var(--ocop-daquy-50); color: var(--ocop-mist-900); }
.tone-danger { background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); }

.position-grid { display: grid; grid-template-columns: minmax(0, 3fr) minmax(0, 2fr); gap: var(--ocop-space-5); }
.map-col { display: grid; gap: var(--ocop-space-2); align-content: start; }
.map-box { position: relative; height: 320px; overflow: hidden; border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-md); }
.map-actions { position: absolute; z-index: 500; top: var(--ocop-space-3); left: var(--ocop-space-3); display: flex; flex-wrap: wrap; gap: var(--ocop-space-2); max-width: calc(100% - 80px); }
.hint { margin: 0; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); }
.facts-col { display: grid; gap: var(--ocop-space-3); align-content: start; }
.facts { display: grid; margin: 0; grid-template-columns: auto minmax(0, 1fr); gap: var(--ocop-space-2) var(--ocop-space-4); font-size: var(--ocop-font-size-small); }
.facts dt { color: var(--ocop-mist-600); font-weight: 400; }
.facts dd { margin: 0; font-weight: 600; overflow-wrap: anywhere; }
.num { font-variant-numeric: tabular-nums; }
.checks { display: grid; margin: 0; padding: var(--ocop-space-3); gap: var(--ocop-space-2); border-radius: var(--ocop-radius-md); background: var(--ocop-mist-50); font-size: var(--ocop-font-size-small); list-style: none; }
.checks li { display: flex; gap: var(--ocop-space-2); }
.checks .check-mark { font-weight: 800; }
.checks .ok .check-mark { color: var(--ocop-success); }
.checks .warn .check-mark { color: var(--ocop-warning); }

.content { display: grid; padding-top: var(--ocop-space-4); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ocop-space-4) var(--ocop-space-6); border-top: 1px solid var(--ocop-mist-100); font-size: var(--ocop-font-size-small); }
.content h3, .content .wide { grid-column: 1 / -1; }
.content h3, .decision h3 { margin: 0; font-size: var(--ocop-font-size-body-lg); font-weight: 700; }
.content > div { display: grid; gap: var(--ocop-space-1); }
.content span, .reason span { color: var(--ocop-mist-600); }
.content p, .reason p { margin: 0; line-height: 1.6; overflow-wrap: anywhere; }
.pre { white-space: pre-line; }
.photos { display: flex; margin: 0; padding: 0; flex-wrap: wrap; gap: var(--ocop-space-3); list-style: none; }
.photos a { display: block; overflow: hidden; border-radius: var(--ocop-radius-sm); }
.photos img { display: block; width: 140px; height: 96px; background: var(--ocop-mist-100); object-fit: cover; }
.reason { display: grid; gap: var(--ocop-space-1); font-size: var(--ocop-font-size-small); }

.compare-wrap { overflow-x: auto; }
.compare { width: 100%; border-collapse: collapse; font-size: var(--ocop-font-size-small); }
.compare th, .compare td { padding: var(--ocop-space-2) var(--ocop-space-3); border-top: 1px solid var(--ocop-mist-100); text-align: left; vertical-align: top; overflow-wrap: anywhere; }
.compare thead th { background: var(--ocop-mist-50); color: var(--ocop-mist-700); font-weight: 600; }
.compare tbody th { width: 22%; color: var(--ocop-mist-700); font-weight: 600; }
.compare tr.changed td:last-child { background: var(--ocop-daquy-50); font-weight: 600; }

.decision { display: grid; gap: var(--ocop-space-3); padding: var(--ocop-space-5); border-radius: var(--ocop-radius-md); background: var(--ocop-mist-50); }
.decision-options { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--ocop-space-3); }
.decision-option { display: grid; min-height: 64px; padding: var(--ocop-space-3); gap: var(--ocop-space-1); border: 2px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-md); background: var(--ocop-white); color: var(--ocop-mist-950); text-align: left; }
.decision-option span { font-size: var(--ocop-font-size-small); }
.decision-option.active.is-approved { border-color: var(--ocop-success); background: var(--ocop-success-soft); }
.decision-option.active.is-needs_revision { border-color: var(--ocop-warning); background: var(--ocop-warning-soft); }
.decision-option.active.is-rejected { border-color: var(--ocop-danger-strong); background: var(--ocop-danger-soft); }
.decision label { display: grid; gap: 6px; font-size: var(--ocop-font-size-small); font-weight: 600; }
.decision textarea { padding: var(--ocop-space-3); border: 1px solid var(--ocop-mist-300); border-radius: var(--ocop-radius-sm); background: var(--ocop-white); font: inherit; font-weight: 400; resize: vertical; }
.decision-submit { display: flex; justify-content: flex-end; }
.btn-submit { min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-5); border: 0; border-radius: var(--ocop-radius-sm); color: var(--ocop-white); font-size: var(--ocop-font-size-small); font-weight: 700; }
.btn-submit.is-approved { background: var(--ocop-success); }
.btn-submit.is-needs_revision { background: var(--ocop-mist-950); }
.btn-submit.is-rejected { background: var(--ocop-danger-strong); }
.btn-submit:disabled { opacity: 0.65; }

@media (max-width: 1199.98px) {
  .position-grid { grid-template-columns: 1fr; }
}
@media (max-width: 991.98px) {
  .review-grid { grid-template-columns: 1fr; }
}
@media (max-width: 767.98px) {
  .search, .search input { width: 100%; }
  .detail { padding: var(--ocop-space-4); }
  .content, .decision-options { grid-template-columns: 1fr; }
  .decision-submit .btn-submit { width: 100%; }
}
</style>
