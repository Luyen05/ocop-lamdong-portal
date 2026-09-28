<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { onBeforeRouteLeave, useRoute, useRouter } from 'vue-router'

import LocationPicker from '@/components/location-management/LocationPicker.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import {
  checkLocationPosition,
  createLocationDraft,
  deleteTemporaryLocationImage,
  getMyLocation,
  getMyLocationChangeRequest,
  parseCoordinates,
  requestLocationUpdate,
  resubmitLocationChangeRequest,
  submitLocation,
  updateLocationDraft,
  uploadLocationImage,
} from '@/services/location-management'
import { getLocationFilterOptions } from '@/services/locations'
import { listMyProducts } from '@/services/product-management'
import { getMySubjectApplication } from '@/services/subjects'
import type { LocationType } from '@/types/location'
import type {
  LocationChangeRequest,
  LocationDraftPayload,
  LocationImagePayload,
  LocationPositionCheck,
  LocationWritePayload,
  ManagedLocation,
  SubjectLocationSource,
} from '@/types/location-management'
import type { ManagedProduct } from '@/types/product-management'
import {
  LOCATION_SOURCE_LABELS,
  LOCATION_STATUS_META,
  LOCATION_TYPE_OPTIONS,
  MIN_LOCATION_DESCRIPTION,
  SERVICE_SUGGESTIONS,
  formatAccuracy,
  formatCoordinate,
  formatDateTime,
  insideLamDong,
  nearestLabel,
} from '@/utils/location-workflow'
import { formatDistance, sortVietnamese } from '@/utils/location'

type Method = 'map_pin' | 'device_gps' | 'paste'
type Mode = 'create' | 'draft' | 'request' | 'request-edit' | 'readonly'

interface FormState {
  name: string
  type: LocationType
  description: string
  latitude: number | null
  longitude: number | null
  location_source: SubjectLocationSource | null
  location_accuracy_m: number | null
  district: string
  address: string
  contact_phone: string
  opening_hours: string
  ticket_price: string
  services: string[]
  website: string
  images: LocationImagePayload[]
  product_ids: number[]
}

const MAX_IMAGES = 10
const MAX_IMAGE_BYTES = 5 * 1024 * 1024
const IMAGE_TYPES = ['image/jpeg', 'image/png', 'image/webp']

const route = useRoute()
const router = useRouter()

const location = ref<ManagedLocation | null>(null)
const changeRequest = ref<LocationChangeRequest | null>(null)
const loading = ref(true)
const loadError = ref('')
const saving = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const savedAt = ref<string | null>(null)
const savedSnapshot = ref('')

const form = reactive<FormState>(emptyForm())
const method = ref<Method>('map_pin')
const pasteText = ref('')
const pasteError = ref('')
const parsing = ref(false)
const locating = ref(false)
const gpsError = ref('')
const positionCheck = ref<LocationPositionCheck | null>(null)
const positionCheckError = ref(false)
const districtOptions = ref<string[]>([])
const approvedProducts = ref<ManagedProduct[]>([])
const uploading = ref(0)
const imageError = ref('')
const dragOver = ref(false)
const customService = ref('')
const requestReason = ref('')
const subjectAddress = ref<{ address: string; district: string } | null>(null)
/** Ảnh đã lưu trên máy chủ: bỏ khỏi form thì không xóa file (chỉ xóa ảnh tạm vừa tải lên). */
const savedImagePaths = new Set<string>()

const isCompact = ref(false)
const stepper = ref<HTMLElement | null>(null)
const step = ref(0)
let compactQuery: MediaQueryList | null = null
let checkTimer: ReturnType<typeof setTimeout> | null = null

const steps = [
  { label: 'Thông tin', next: 'Vị trí' },
  { label: 'Vị trí', next: 'Địa chỉ' },
  { label: 'Địa chỉ', next: 'Ảnh' },
  { label: 'Ảnh', next: 'Sản phẩm' },
  { label: 'Sản phẩm và gửi', next: '' },
]

const methods: Array<{ value: Method; label: string; icon: string }> = [
  { value: 'map_pin', label: 'Ghim trên bản đồ', icon: 'map-pin' },
  { value: 'device_gps', label: 'Vị trí hiện tại (GPS)', icon: 'navigation' },
  { value: 'paste', label: 'Dán tọa độ / link', icon: 'map' },
]

const locationId = computed(() => (route.params.id ? Number(route.params.id) : null))
const requestId = computed(() => (route.params.requestId ? Number(route.params.requestId) : null))

const mode = computed<Mode>(() => {
  if (requestId.value) return changeRequest.value?.status === 'needs_revision' ? 'request-edit' : 'readonly'
  if (!location.value) return 'create'
  if (['draft', 'needs_revision'].includes(location.value.status)) return 'draft'
  if (location.value.status === 'approved' && !location.value.open_change_request_id) return 'request'
  return 'readonly'
})
const isReadonly = computed(() => mode.value === 'readonly')
const isRequestMode = computed(() => mode.value === 'request' || mode.value === 'request-edit')

const pageTitle = computed(() => {
  if (mode.value === 'create') return 'Khai báo điểm du lịch'
  if (isRequestMode.value) return 'Đề nghị cập nhật điểm du lịch'
  if (location.value?.status === 'needs_revision') return 'Bổ sung hồ sơ điểm du lịch'
  if (mode.value === 'readonly') return 'Hồ sơ điểm du lịch'
  return 'Khai báo điểm du lịch'
})
const statusLabel = computed(() => (location.value ? LOCATION_STATUS_META[location.value.status].label : 'Bản nháp mới'))
const statusTone = computed(() => (location.value ? LOCATION_STATUS_META[location.value.status].tone : 'neutral'))

const hasPosition = computed(() => form.latitude !== null && form.longitude !== null)
const positionInside = computed(() =>
  hasPosition.value ? insideLamDong(form.latitude as number, form.longitude as number) : false,
)
const primaryCount = computed(() => form.images.filter((image) => image.is_primary).length)

const checklist = computed(() => [
  { key: 'name', label: 'Tên điểm và loại hình', done: form.name.trim().length >= 2 && Boolean(form.type) },
  { key: 'position', label: 'Vị trí trong Lâm Đồng', done: hasPosition.value && positionInside.value },
  { key: 'address', label: 'Địa chỉ và xã/phường', done: form.address.trim().length >= 5 && form.district.trim().length >= 2 },
  {
    key: 'description',
    label: `Mô tả tối thiểu ${MIN_LOCATION_DESCRIPTION} ký tự`,
    done: form.description.trim().length >= MIN_LOCATION_DESCRIPTION,
  },
  { key: 'image', label: 'Ít nhất 1 ảnh (chọn 1 ảnh chính)', done: form.images.length > 0 && primaryCount.value === 1 },
])
const missingItems = computed(() => checklist.value.filter((item) => !item.done))
const isComplete = computed(() => missingItems.value.length === 0)
const missingSummary = computed(() =>
  missingItems.value.length
    ? `Còn thiếu: ${missingItems.value.map((item) => item.label.toLowerCase()).join('; ')}.`
    : 'Đã đủ thông tin để gửi duyệt.',
)

const descriptionLength = computed(() => form.description.trim().length)
const isDirty = computed(() => !isReadonly.value && snapshot() !== savedSnapshot.value)

const mapHint = computed(() => {
  if (isReadonly.value) return 'Vị trí đã khai báo.'
  if (method.value === 'device_gps') return 'Vòng xanh là phạm vi sai số GPS. Kéo ghim nếu cổng vào bị lệch.'
  if (method.value === 'paste') return 'Ghim đặt theo tọa độ đã dán. Kéo ghim nếu cần chỉnh.'
  return hasPosition.value ? 'Kéo ghim hoặc bấm chỗ khác trên bản đồ để chỉnh.' : 'Bấm vào bản đồ để đặt ghim tại cổng vào.'
})

const sourceLabel = computed(() => (form.location_source ? LOCATION_SOURCE_LABELS[form.location_source] : 'Chưa chọn'))
const accuracyLabel = computed(() =>
  form.location_source === 'device_gps' ? formatAccuracy(form.location_accuracy_m) : 'Không có (chỉ có khi dùng GPS)',
)

const serviceChoices = computed(() => {
  const extras = form.services.filter((service) => !SERVICE_SUGGESTIONS.includes(service))
  return [...SERVICE_SUGGESTIONS, ...extras]
})

function emptyForm(): FormState {
  return {
    name: '',
    type: 'fruit_garden',
    description: '',
    latitude: null,
    longitude: null,
    location_source: null,
    location_accuracy_m: null,
    district: '',
    address: '',
    contact_phone: '',
    opening_hours: '',
    ticket_price: '',
    services: [],
    website: '',
    images: [],
    product_ids: [],
  }
}

function text(value: string | null | undefined): string {
  return value ?? ''
}

function subjectSource(value: string | null | undefined): SubjectLocationSource | null {
  return value && value !== 'admin_import' ? (value as SubjectLocationSource) : null
}

function fillForm(source: Partial<LocationWritePayload> | ManagedLocation): void {
  const data = source as Partial<ManagedLocation> & Partial<LocationWritePayload>
  Object.assign(form, emptyForm(), {
    name: text(data.name),
    type: (data.type as LocationType) || 'fruit_garden',
    description: text(data.description),
    latitude: data.latitude ?? null,
    longitude: data.longitude ?? null,
    location_source: subjectSource(data.location_source as string | null | undefined),
    location_accuracy_m: data.location_accuracy_m ?? null,
    district: text(data.district),
    address: text(data.address),
    contact_phone: text(data.contact_phone),
    opening_hours: text(data.opening_hours),
    ticket_price: data.ticket_price === null || data.ticket_price === undefined ? '' : String(Math.round(Number(data.ticket_price))),
    services: [...(data.services ?? [])],
    website: text(data.website),
    images: (data.images ?? []).map((image, index) => ({
      image_url: image.image_url,
      storage_path: image.storage_path ?? null,
      is_primary: image.is_primary,
      sort_order: index,
      alt_text: image.alt_text ?? null,
    })),
    product_ids: 'products' in data && data.products ? data.products.map((product) => product.id) : [...(data.product_ids ?? [])],
  })
  for (const image of form.images) if (image.storage_path) savedImagePaths.add(image.storage_path)
  if (form.location_source === 'device_gps') method.value = 'device_gps'
  else if (form.location_source === 'coordinates' || form.location_source === 'google_maps_link') method.value = 'paste'
  else method.value = 'map_pin'
}

function nullable(value: string): string | null {
  const trimmed = value.trim()
  return trimmed ? trimmed : null
}

function ticketPrice(): number | null {
  const digits = form.ticket_price.replace(/\D/g, '')
  return digits ? Number(digits) : null
}

function imagePayload(): LocationImagePayload[] {
  return form.images.map((image, index) => ({ ...image, sort_order: index }))
}

function draftPayload(): LocationDraftPayload {
  const payload: LocationDraftPayload = {
    name: form.name.trim(),
    type: form.type,
    description: nullable(form.description),
    district: nullable(form.district),
    address: nullable(form.address),
    contact_phone: nullable(form.contact_phone),
    opening_hours: nullable(form.opening_hours),
    ticket_price: ticketPrice(),
    services: [...form.services],
    website: nullable(form.website),
    images: imagePayload(),
    product_ids: [...form.product_ids],
  }
  if (hasPosition.value && form.location_source) {
    payload.latitude = form.latitude
    payload.longitude = form.longitude
    payload.location_source = form.location_source
    payload.location_accuracy_m = form.location_source === 'device_gps' ? form.location_accuracy_m : null
  } else {
    payload.latitude = null
    payload.longitude = null
  }
  return payload
}

function writePayload(): LocationWritePayload {
  return {
    name: form.name.trim(),
    type: form.type,
    description: form.description.trim(),
    latitude: form.latitude as number,
    longitude: form.longitude as number,
    location_source: form.location_source as SubjectLocationSource,
    location_accuracy_m: form.location_source === 'device_gps' ? form.location_accuracy_m : null,
    district: form.district.trim(),
    address: form.address.trim(),
    contact_phone: nullable(form.contact_phone),
    opening_hours: nullable(form.opening_hours),
    ticket_price: ticketPrice(),
    services: [...form.services],
    website: nullable(form.website),
    images: imagePayload(),
    product_ids: [...form.product_ids],
  }
}

function snapshot(): string {
  return JSON.stringify({ ...draftPayload(), reason: requestReason.value.trim() })
}

function markSaved(): void {
  savedSnapshot.value = snapshot()
}

// ---------------------------------------------------------------------------
// Tải dữ liệu
// ---------------------------------------------------------------------------

async function loadReferenceData(): Promise<void> {
  const [options, products, application] = await Promise.allSettled([
    getLocationFilterOptions(),
    listMyProducts('approved'),
    getMySubjectApplication(),
  ])
  const districts = new Set<string>()
  if (options.status === 'fulfilled') options.value.districts.forEach((item) => districts.add(item))
  if (application.status === 'fulfilled') {
    districts.add(application.value.district)
    subjectAddress.value = { address: application.value.address, district: application.value.district }
  }
  districtOptions.value = sortVietnamese([...districts].filter(Boolean))
  if (products.status === 'fulfilled') approvedProducts.value = products.value.items
}

async function loadData(): Promise<void> {
  loading.value = true
  loadError.value = ''
  errorMessage.value = ''
  savedImagePaths.clear()
  try {
    if (requestId.value) {
      const request = await getMyLocationChangeRequest(requestId.value)
      changeRequest.value = request
      location.value = await getMyLocation(request.location_id)
      fillForm((request.proposed_data as Partial<LocationWritePayload>) ?? request.current_data)
      requestReason.value = request.reason ?? ''
    } else if (locationId.value) {
      changeRequest.value = null
      location.value = await getMyLocation(locationId.value)
      fillForm(location.value)
    } else {
      changeRequest.value = null
      location.value = null
      Object.assign(form, emptyForm())
    }
    positionCheck.value = location.value?.position_check ?? null
    markSaved()
  } catch (error) {
    loadError.value = getApiErrorMessage(error, 'Không tải được hồ sơ điểm du lịch.')
  } finally {
    loading.value = false
  }
}

// ---------------------------------------------------------------------------
// Vị trí
// ---------------------------------------------------------------------------

function setPosition(
  latitude: number,
  longitude: number,
  source: SubjectLocationSource,
  accuracy: number | null = null,
  check: LocationPositionCheck | null = null,
): void {
  form.latitude = latitude
  form.longitude = longitude
  form.location_source = source
  form.location_accuracy_m = source === 'device_gps' ? accuracy : null
  if (check) {
    positionCheck.value = check
    return
  }
  scheduleCheck()
}

function scheduleCheck(): void {
  if (checkTimer) clearTimeout(checkTimer)
  checkTimer = setTimeout(runPositionCheck, 300)
}

async function runPositionCheck(): Promise<void> {
  if (!hasPosition.value) return
  positionCheckError.value = false
  try {
    positionCheck.value = await checkLocationPosition(
      form.latitude as number,
      form.longitude as number,
      location.value?.id,
    )
  } catch {
    positionCheck.value = null
    positionCheckError.value = true
  }
}

function onMapPick(position: { latitude: number; longitude: number }): void {
  if (isReadonly.value) return
  setPosition(position.latitude, position.longitude, 'map_pin')
}

function locate(): void {
  gpsError.value = ''
  if (!('geolocation' in navigator)) {
    gpsError.value = 'Trình duyệt này không hỗ trợ lấy vị trí. Hãy ghim trên bản đồ hoặc dán tọa độ.'
    return
  }
  locating.value = true
  navigator.geolocation.getCurrentPosition(
    (position) => {
      locating.value = false
      const accuracy = Math.min(Math.round(position.coords.accuracy * 100) / 100, 100000)
      setPosition(
        Number(position.coords.latitude.toFixed(7)),
        Number(position.coords.longitude.toFixed(7)),
        'device_gps',
        accuracy,
      )
    },
    (error) => {
      locating.value = false
      gpsError.value =
        error.code === error.PERMISSION_DENIED
          ? 'Bạn đã chặn quyền vị trí. Bật định vị cho trình duyệt trong cài đặt, hoặc chuyển sang "Ghim trên bản đồ".'
          : 'Chưa lấy được vị trí. Thử lại ở nơi thoáng, ngoài trời, hoặc dùng cách khác.'
    },
    { enableHighAccuracy: true, timeout: 20000, maximumAge: 0 },
  )
}

async function applyPaste(): Promise<void> {
  pasteError.value = ''
  if (!pasteText.value.trim()) {
    pasteError.value = 'Dán tọa độ hoặc link Google Maps vào ô trên.'
    return
  }
  parsing.value = true
  try {
    const result = await parseCoordinates(pasteText.value.trim())
    setPosition(result.latitude, result.longitude, result.location_source, null, result.position_check)
  } catch (error) {
    pasteError.value = getApiErrorMessage(error, 'Không đọc được tọa độ.')
  } finally {
    parsing.value = false
  }
}

// ---------------------------------------------------------------------------
// Địa chỉ, dịch vụ, ảnh
// ---------------------------------------------------------------------------

function useSubjectAddress(): void {
  if (!subjectAddress.value) return
  form.address = subjectAddress.value.address
  form.district = subjectAddress.value.district
}

function toggleService(service: string): void {
  form.services = form.services.includes(service)
    ? form.services.filter((item) => item !== service)
    : [...form.services, service]
}

function addCustomService(): void {
  const value = customService.value.trim().slice(0, 60)
  if (value && !form.services.some((item) => item.toLowerCase() === value.toLowerCase())) {
    form.services = [...form.services, value]
  }
  customService.value = ''
}

async function addFiles(files: FileList | File[] | null): Promise<void> {
  if (!files) return
  imageError.value = ''
  const selected = Array.from(files)
  const room = MAX_IMAGES - form.images.length
  if (selected.length > room) imageError.value = `Mỗi điểm tối đa ${MAX_IMAGES} ảnh; chỉ tải ${Math.max(room, 0)} ảnh đầu.`
  for (const file of selected.slice(0, Math.max(room, 0))) {
    if (!IMAGE_TYPES.includes(file.type)) {
      imageError.value = `“${file.name}” không phải ảnh JPEG, PNG hoặc WebP.`
      continue
    }
    if (file.size > MAX_IMAGE_BYTES) {
      imageError.value = `“${file.name}” lớn hơn 5 MB.`
      continue
    }
    uploading.value += 1
    try {
      const uploaded = await uploadLocationImage(file)
      form.images.push({
        image_url: uploaded.image_url,
        storage_path: uploaded.storage_path,
        is_primary: primaryCount.value === 0,
        sort_order: form.images.length,
        alt_text: null,
      })
    } catch (error) {
      imageError.value = getApiErrorMessage(error, `Không tải được “${file.name}”.`)
    } finally {
      uploading.value -= 1
    }
  }
}

function onFileInput(event: Event): void {
  const input = event.target as HTMLInputElement
  void addFiles(input.files).finally(() => {
    input.value = ''
  })
}

function onDrop(event: DragEvent): void {
  dragOver.value = false
  if (isReadonly.value) return
  void addFiles(event.dataTransfer?.files ?? null)
}

function setPrimary(index: number): void {
  form.images.forEach((image, position) => {
    image.is_primary = position === index
  })
}

function removeImage(index: number): void {
  const [removed] = form.images.splice(index, 1)
  if (!removed) return
  if (removed.is_primary && form.images[0]) form.images[0].is_primary = true
  if (removed.storage_path && !savedImagePaths.has(removed.storage_path)) {
    void deleteTemporaryLocationImage(removed.storage_path).catch(() => undefined)
  }
}

// ---------------------------------------------------------------------------
// Lưu, gửi duyệt, gửi yêu cầu
// ---------------------------------------------------------------------------

async function saveDraft(silent = false): Promise<boolean> {
  errorMessage.value = ''
  if (!silent) successMessage.value = ''
  if (form.name.trim().length < 2) {
    if (!silent) errorMessage.value = 'Nhập tên điểm du lịch (tối thiểu 2 ký tự) để lưu nháp.'
    return false
  }
  saving.value = true
  try {
    const saved = location.value
      ? await updateLocationDraft(location.value.id, draftPayload())
      : await createLocationDraft(draftPayload())
    const created = !location.value
    location.value = saved
    fillForm(saved)
    positionCheck.value = saved.position_check
    markSaved()
    savedAt.value = new Date().toISOString()
    if (created) await router.replace(`/chu-the/diem-du-lich/${saved.id}`)
    if (!silent) successMessage.value = 'Đã lưu nháp.'
    return true
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không lưu được bản nháp.')
    return false
  } finally {
    saving.value = false
  }
}

async function submitForReview(): Promise<void> {
  if (!isComplete.value) {
    errorMessage.value = missingSummary.value
    return
  }
  if (!(await saveDraft(true)) || !location.value) return
  saving.value = true
  try {
    location.value = await submitLocation(location.value.id)
    markSaved()
    successMessage.value = 'Đã gửi hồ sơ. Quản trị viên sẽ kiểm tra vị trí và thông tin trước khi hiện trên bản đồ.'
    window.scrollTo?.({ top: 0 })
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không gửi duyệt được.')
  } finally {
    saving.value = false
  }
}

async function sendRequest(): Promise<void> {
  errorMessage.value = ''
  if (!isComplete.value) {
    errorMessage.value = missingSummary.value
    return
  }
  saving.value = true
  try {
    if (mode.value === 'request-edit' && changeRequest.value) {
      await resubmitLocationChangeRequest(changeRequest.value.id, {
        proposed_data: writePayload(),
        reason: nullable(requestReason.value),
      })
    } else if (location.value) {
      await requestLocationUpdate(location.value.id, writePayload(), requestReason.value.trim())
    }
    markSaved()
    await router.push({ path: '/chu-the/diem-du-lich' })
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không gửi được yêu cầu cập nhật.')
  } finally {
    saving.value = false
  }
}

// ---------------------------------------------------------------------------
// Chia bước trên điện thoại
// ---------------------------------------------------------------------------

function sectionVisible(index: number): boolean {
  return !isCompact.value || step.value === index
}

async function goToStep(index: number): Promise<void> {
  if (index > step.value && mode.value !== 'readonly' && !isRequestMode.value && isDirty.value) {
    await saveDraft(true)
  }
  step.value = Math.min(Math.max(index, 0), steps.length - 1)
  stepper.value?.scrollIntoView?.({ block: 'start' })
}

function updateCompact(): void {
  isCompact.value = Boolean(compactQuery?.matches)
}

onBeforeRouteLeave(() => {
  if (!isDirty.value || saving.value) return true
  return window.confirm('Có thay đổi chưa lưu. Rời trang và bỏ các thay đổi này?')
})

watch([locationId, requestId], ([id]) => {
  if (id && location.value?.id === id && !requestId.value) return
  void loadData()
})

onMounted(() => {
  compactQuery = window.matchMedia?.('(max-width: 767.98px)') ?? null
  updateCompact()
  compactQuery?.addEventListener?.('change', updateCompact)
  void loadData()
  void loadReferenceData()
})

onBeforeUnmount(() => {
  compactQuery?.removeEventListener?.('change', updateCompact)
  if (checkTimer) clearTimeout(checkTimer)
})
</script>

<template>
  <div class="editor-page">
    <header class="editor-head">
      <nav aria-label="Đường dẫn" class="crumbs">
        <RouterLink to="/chu-the/diem-du-lich">Điểm du lịch của tôi</RouterLink>
        <span aria-hidden="true">/</span>
        <span>{{ location ? location.name : 'Khai báo điểm mới' }}</span>
      </nav>
      <div class="title-row">
        <h1>{{ pageTitle }}</h1>
        <span :class="['status', `tone-${statusTone}`]">{{ statusLabel }}</span>
      </div>
      <p>Điểm chỉ hiện trên bản đồ công khai sau khi quản trị viên duyệt.</p>
    </header>

    <p v-if="loading" class="state">Đang tải hồ sơ…</p>
    <div v-else-if="loadError" class="state is-error" role="alert">
      <p>{{ loadError }}</p>
      <button type="button" class="btn-line" @click="loadData">Thử lại</button>
    </div>

    <template v-else>
      <div class="banners">
        <p v-if="successMessage" class="notice is-success" role="status">{{ successMessage }}</p>
        <p v-if="errorMessage" class="notice is-error" role="alert">{{ errorMessage }}</p>
        <div
          v-if="location?.review_note && ['needs_revision', 'rejected'].includes(location.status) && !requestId"
          class="notice is-warning"
        >
          <strong>Ghi chú của {{ location.reviewed_by_name || 'quản trị viên' }} ({{ formatDateTime(location.reviewed_at) }})</strong>
          <p>{{ location.review_note }}</p>
          <p v-if="location.status === 'rejected'">Hồ sơ bị từ chối không sửa được nữa. Bạn có thể khai báo lại thành điểm mới.</p>
        </div>
        <p v-if="location?.status === 'pending'" class="notice is-info">
          Hồ sơ đang chờ quản trị viên duyệt nên chưa sửa được. Gửi lúc {{ formatDateTime(location.submitted_at) }}.
        </p>
        <p v-if="mode === 'request'" class="notice is-info">
          Điểm đang hiện trên bản đồ. Thay đổi bạn gửi chỉ được áp dụng sau khi quản trị viên duyệt; tới lúc đó bản cũ vẫn hiển thị.
        </p>
        <p v-if="location?.status === 'approved' && location.open_change_request_id && !requestId" class="notice is-info">
          Điểm đang có một yêu cầu thay đổi chờ xử lý. Xem hoặc hủy yêu cầu ở
          <RouterLink to="/chu-the/diem-du-lich">danh sách điểm</RouterLink>.
        </p>
        <div v-if="changeRequest?.review_note" class="notice is-warning">
          <strong>Phản hồi của {{ changeRequest.reviewed_by_name || 'quản trị viên' }} về yêu cầu</strong>
          <p>{{ changeRequest.review_note }}</p>
        </div>
        <p v-if="location?.status === 'archived'" class="notice is-info">Điểm đã ngừng hiển thị theo đề nghị của đơn vị.</p>
      </div>

      <nav v-if="isCompact && !isReadonly" ref="stepper" class="stepper" aria-label="Các bước khai báo">
        <p>Bước {{ step + 1 }}/{{ steps.length }}: <strong>{{ steps[step]?.label }}</strong></p>
        <ol>
          <li v-for="(item, index) in steps" :key="item.label" :class="{ done: index < step, current: index === step }">
            <span class="visually-hidden">{{ item.label }}{{ index === step ? ' (bước hiện tại)' : '' }}</span>
          </li>
        </ol>
      </nav>

      <div class="editor-grid">
        <fieldset class="editor-form" :disabled="isReadonly || saving">
          <legend class="visually-hidden">Thông tin điểm du lịch</legend>

          <section v-show="sectionVisible(0)" class="card" aria-labelledby="s-info">
            <h2 id="s-info">1. Thông tin điểm</h2>
            <div class="grid-2">
              <label>
                Tên điểm du lịch *
                <input v-model="form.name" type="text" required minlength="2" maxlength="255" autocomplete="off" />
              </label>
              <label>
                Loại hình *
                <select v-model="form.type" required>
                  <option v-for="option in LOCATION_TYPE_OPTIONS" :key="option.value" :value="option.value">{{ option.label }}</option>
                </select>
              </label>
            </div>
            <label>
              Mô tả cho du khách *
              <textarea
                v-model="form.description"
                rows="4"
                maxlength="5000"
                aria-describedby="description-hint"
                placeholder="Du khách đến đây được làm gì, thấy gì? Ví dụ: tham quan vườn, tự tay hái, mua sản phẩm tại vườn."
              />
              <small id="description-hint" :class="{ 'is-ok': descriptionLength >= MIN_LOCATION_DESCRIPTION }">
                Tối thiểu {{ MIN_LOCATION_DESCRIPTION }} ký tự · đã viết {{ descriptionLength }}
              </small>
            </label>
          </section>

          <section v-show="sectionVisible(1)" class="card" aria-labelledby="s-loc">
            <div class="card-head">
              <h2 id="s-loc">2. Vị trí trên bản đồ *</h2>
              <p>Đặt ghim đúng cổng vào để du khách chỉ đường tới nơi. Chọn một trong ba cách:</p>
            </div>

            <div class="segmented" role="radiogroup" aria-label="Cách lấy vị trí">
              <button
                v-for="item in methods"
                :key="item.value"
                type="button"
                role="radio"
                :aria-checked="method === item.value"
                :class="{ active: method === item.value }"
                @click="method = item.value"
              >
                <AppIcon :name="item.icon" :size="16" /> {{ item.label }}
              </button>
            </div>

            <div v-if="method === 'device_gps' && !isReadonly" class="method-box">
              <div>
                <strong>Đang đứng tại điểm du lịch?</strong>
                <span>Trình duyệt sẽ hỏi quyền truy cập vị trí. Nên đứng ngoài trời để GPS chính xác hơn.</span>
              </div>
              <button type="button" class="btn-dark" :disabled="locating" @click="locate">
                <AppIcon name="navigation" :size="16" />
                {{ locating ? 'Đang lấy vị trí…' : form.location_source === 'device_gps' ? 'Lấy lại vị trí' : 'Lấy vị trí hiện tại' }}
              </button>
              <p v-if="gpsError" class="field-error" role="alert">{{ gpsError }}</p>
            </div>

            <div v-if="method === 'paste' && !isReadonly" class="paste-box">
              <label for="paste-input">Tọa độ hoặc link Google Maps</label>
              <div class="inline-field">
                <input
                  id="paste-input"
                  v-model="pasteText"
                  type="text"
                  inputmode="text"
                  placeholder="12.047000, 108.441000"
                  aria-describedby="paste-hint"
                  @keydown.enter.prevent="applyPaste"
                />
                <button type="button" class="btn-line" :disabled="parsing" @click="applyPaste">
                  {{ parsing ? 'Đang đọc…' : 'Đặt ghim' }}
                </button>
              </div>
              <small id="paste-hint">
                Nhận dạng “vĩ độ, kinh độ”, độ-phút-giây hoặc link Google Maps đầy đủ. Link rút gọn maps.app.goo.gl:
                mở link trên trình duyệt rồi chép đường dẫn đầy đủ.
              </small>
              <p v-if="pasteError" class="field-error" role="alert">{{ pasteError }}</p>
            </div>

            <div class="map-box">
              <LocationPicker
                :latitude="form.latitude"
                :longitude="form.longitude"
                :accuracy="form.location_source === 'device_gps' ? form.location_accuracy_m : null"
                :readonly="isReadonly"
                @pick="onMapPick"
              />
              <p class="map-hint">{{ mapHint }}</p>
            </div>

            <dl class="facts">
              <div><dt>Vĩ độ, kinh độ</dt><dd class="num">{{ formatCoordinate(form.latitude, form.longitude) }}</dd></div>
              <div><dt>Cách lấy vị trí</dt><dd>{{ sourceLabel }}</dd></div>
              <div><dt>Độ chính xác</dt><dd>{{ accuracyLabel }}</dd></div>
            </dl>

            <ul v-if="hasPosition" class="checks" aria-live="polite">
              <li :class="positionInside ? 'ok' : 'warn'">
                <AppIcon :name="positionInside ? 'checkCircle' : 'alert'" :size="18" />
                <span v-if="positionInside">Nằm trong tỉnh Lâm Đồng</span>
                <span v-else>Vị trí nằm ngoài tỉnh Lâm Đồng. Kiểm tra lại ghim hoặc thứ tự vĩ độ, kinh độ.</span>
              </li>
              <li v-if="positionCheck?.duplicate_warning && positionCheck.nearest" class="warn">
                <AppIcon name="alert" :size="18" />
                <span>
                  Cách điểm đã duyệt “{{ positionCheck.nearest.name }}” chỉ {{ formatDistance(positionCheck.nearest.distance_m) }}.
                  Nếu là cùng một nơi thì không cần khai báo lại.
                </span>
              </li>
              <li v-else-if="positionCheck?.nearest" class="ok">
                <AppIcon name="checkCircle" :size="18" />
                <span>
                  Không trùng điểm đã có. Điểm gần nhất: {{ positionCheck.nearest.name }}, cách
                  {{ nearestLabel(positionCheck.nearest.distance_m) }}
                </span>
              </li>
              <li v-else-if="positionCheckError" class="muted">
                <AppIcon name="alert" :size="18" />
                <span>Chưa kiểm tra được điểm trùng; quản trị viên sẽ kiểm tra khi duyệt.</span>
              </li>
            </ul>
          </section>

          <section v-show="sectionVisible(2)" class="card" aria-labelledby="s-addr">
            <div class="card-head is-row">
              <h2 id="s-addr">3. Địa chỉ</h2>
              <button v-if="subjectAddress && !isReadonly" type="button" class="btn-line" @click="useSubjectAddress">
                Dùng địa chỉ của đơn vị
              </button>
            </div>
            <div class="grid-address">
              <label>
                Địa chỉ *
                <input v-model="form.address" type="text" maxlength="1000" placeholder="Số nhà, thôn, tên đường" autocomplete="street-address" />
              </label>
              <label>
                Xã / phường *
                <input v-model="form.district" type="text" maxlength="100" list="district-options" placeholder="Ví dụ: Phường Lang Biang - Đà Lạt" />
                <datalist id="district-options">
                  <option v-for="district in districtOptions" :key="district" :value="district" />
                </datalist>
              </label>
            </div>
          </section>

          <section v-show="sectionVisible(2)" class="card" aria-labelledby="s-visit">
            <h2 id="s-visit">4. Thông tin tham quan</h2>
            <div class="grid-3">
              <label>
                Giờ mở cửa
                <input v-model="form.opening_hours" type="text" maxlength="100" placeholder="07:00 - 17:00" />
              </label>
              <label>
                Giá vé (đồng)
                <input v-model="form.ticket_price" type="text" inputmode="numeric" maxlength="12" placeholder="Để trống nếu liên hệ" />
              </label>
              <label>
                Điện thoại
                <input v-model="form.contact_phone" type="tel" maxlength="20" autocomplete="tel" pattern="[0-9+][0-9 ().\-]{7,19}" />
              </label>
            </div>
            <label>
              Trang web hoặc trang mạng xã hội
              <input v-model="form.website" type="url" maxlength="500" placeholder="https://" />
            </label>
            <div class="services">
              <span id="services-label" class="label">Dịch vụ cho du khách</span>
              <div class="chips" role="group" aria-labelledby="services-label">
                <button
                  v-for="service in serviceChoices"
                  :key="service"
                  type="button"
                  class="chip"
                  :aria-pressed="form.services.includes(service)"
                  @click="toggleService(service)"
                >
                  {{ service }}
                </button>
              </div>
              <div v-if="!isReadonly" class="inline-field">
                <label for="custom-service" class="visually-hidden">Thêm dịch vụ khác</label>
                <input
                  id="custom-service"
                  v-model="customService"
                  type="text"
                  maxlength="60"
                  placeholder="Dịch vụ khác, ví dụ: Cắm trại"
                  @keydown.enter.prevent="addCustomService"
                />
                <button type="button" class="btn-line" @click="addCustomService">Thêm</button>
              </div>
            </div>
          </section>

          <section v-show="sectionVisible(3)" class="card" aria-labelledby="s-photo">
            <h2 id="s-photo">5. Ảnh *</h2>
            <div
              v-if="!isReadonly"
              :class="['dropzone', { 'is-over': dragOver }]"
              @dragover.prevent="dragOver = true"
              @dragleave="dragOver = false"
              @drop.prevent="onDrop"
            >
              <AppIcon name="palette" :size="26" />
              <strong>Kéo ảnh vào đây hoặc</strong>
              <label class="btn-line file-button">
                Chọn ảnh từ máy
                <input class="visually-hidden" type="file" accept="image/jpeg,image/png,image/webp" multiple @change="onFileInput" />
              </label>
              <small>JPG, PNG hoặc WebP, tối đa 5 MB mỗi ảnh, tối đa {{ MAX_IMAGES }} ảnh. Cần ít nhất 1 ảnh chụp thật tại điểm.</small>
            </div>
            <p v-if="uploading" class="upload-status" role="status">Đang tải {{ uploading }} ảnh…</p>
            <p v-if="imageError" class="field-error" role="alert">{{ imageError }}</p>
            <ul v-if="form.images.length" class="gallery">
              <li v-for="(image, index) in form.images" :key="image.image_url" :class="{ primary: image.is_primary }">
                <img :src="image.image_url" :alt="`Ảnh ${index + 1} của ${form.name || 'điểm du lịch'}`" loading="lazy" />
                <div class="gallery-actions">
                  <label class="radio">
                    <input type="radio" name="primary-image" :checked="image.is_primary" @change="setPrimary(index)" />
                    Ảnh chính
                  </label>
                  <button v-if="!isReadonly" type="button" class="btn-text is-danger" @click="removeImage(index)">
                    Bỏ ảnh<span class="visually-hidden"> {{ index + 1 }}</span>
                  </button>
                </div>
              </li>
            </ul>
          </section>

          <section v-show="sectionVisible(4)" class="card" aria-labelledby="s-prod">
            <div class="card-head">
              <h2 id="s-prod">6. Sản phẩm OCOP có tại điểm</h2>
              <p>Chỉ hiện sản phẩm của đơn vị đã được duyệt. Không bắt buộc.</p>
            </div>
            <p v-if="!approvedProducts.length" class="muted-text">Đơn vị chưa có sản phẩm OCOP nào được duyệt.</p>
            <label v-for="product in approvedProducts" :key="product.id" class="check-row">
              <input v-model="form.product_ids" type="checkbox" :value="product.id" />
              {{ product.name }}
            </label>
          </section>

          <section v-if="isRequestMode" v-show="sectionVisible(4)" class="card" aria-labelledby="s-reason">
            <h2 id="s-reason">Lý do cập nhật</h2>
            <label>
              Ghi chú cho quản trị viên (không bắt buộc)
              <textarea v-model="requestReason" rows="3" maxlength="1000" placeholder="Ví dụ: đổi giờ mở cửa mùa cao điểm." />
            </label>
          </section>
        </fieldset>

        <aside v-if="!isReadonly" v-show="!isCompact || step === steps.length - 1" class="card status-card" aria-label="Tình trạng hồ sơ">
          <h2>{{ isRequestMode ? 'Trước khi gửi yêu cầu' : 'Trước khi gửi duyệt' }}</h2>
          <ul class="checklist">
            <li v-for="item in checklist" :key="item.key" :class="{ done: item.done }">
              <span class="check-mark" aria-hidden="true">{{ item.done ? '✓' : '!' }}</span>
              <span>{{ item.label }}<span class="visually-hidden">{{ item.done ? ': đã có' : ': còn thiếu' }}</span></span>
            </li>
          </ul>
          <p id="missing-summary" :class="['summary', { 'is-ok': isComplete }]">{{ missingSummary }}</p>
          <div class="after">
            <strong>Sau khi gửi</strong>
            <span>Quản trị viên kiểm tra vị trí và thông tin. Nếu cần sửa, bạn sẽ thấy ghi chú ở đầu trang này.</span>
            <span>Điểm đã duyệt muốn sửa thì gửi yêu cầu cập nhật; điểm cũ vẫn hiện trên bản đồ tới khi được duyệt.</span>
          </div>
        </aside>
      </div>

      <div v-if="!isReadonly" class="action-bar">
        <span class="saved-text" aria-live="polite">
          <template v-if="saving">Đang lưu…</template>
          <template v-else-if="savedAt">Đã lưu nháp lúc {{ formatDateTime(savedAt) }}</template>
          <template v-else-if="isDirty">Có thay đổi chưa lưu</template>
        </span>
        <div class="action-buttons">
          <template v-if="isCompact && step > 0">
            <button type="button" class="btn-line" @click="goToStep(step - 1)">Quay lại</button>
          </template>
          <template v-if="isCompact && step < steps.length - 1">
            <button type="button" class="btn-dark" :disabled="saving" @click="goToStep(step + 1)">
              Tiếp tục: {{ steps[step]?.next }}
            </button>
          </template>
          <template v-else-if="isRequestMode">
            <button type="button" class="btn-accent" :disabled="saving || !isComplete" aria-describedby="missing-summary" @click="sendRequest">
              {{ mode === 'request-edit' ? 'Gửi lại yêu cầu' : 'Gửi yêu cầu cập nhật' }}
            </button>
          </template>
          <template v-else>
            <button type="button" class="btn-line" :disabled="saving" @click="saveDraft()">Lưu nháp</button>
            <button type="button" class="btn-accent" :disabled="saving || !isComplete" aria-describedby="missing-summary" @click="submitForReview">
              Gửi duyệt
            </button>
          </template>
        </div>
      </div>
      <div v-else class="action-bar">
        <RouterLink class="btn-line" to="/chu-the/diem-du-lich">Về danh sách điểm</RouterLink>
        <RouterLink v-if="location?.status === 'approved'" class="btn-text" :to="`/diem-du-lich/${location.slug}`">
          Xem trang công khai
        </RouterLink>
      </div>
    </template>
  </div>
</template>

<style scoped>
.editor-page { display: grid; gap: var(--ocop-space-5); color: var(--ocop-mist-950); }
.editor-head { display: grid; gap: var(--ocop-space-2); }
.crumbs { display: flex; flex-wrap: wrap; gap: var(--ocop-space-2); color: var(--ocop-mist-600); font-size: var(--ocop-font-size-small); }
.crumbs a { color: var(--ocop-mist-700); }
.title-row { display: flex; flex-wrap: wrap; align-items: center; gap: var(--ocop-space-3); }
.title-row h1 { margin: 0; font-size: var(--ocop-font-size-title-md); font-weight: 800; }
.editor-head > p { margin: 0; color: var(--ocop-mist-700); }

.status { display: inline-block; padding: var(--ocop-space-1) var(--ocop-space-3); border-radius: var(--ocop-radius-pill); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.tone-neutral { background: var(--ocop-mist-100); color: var(--ocop-mist-800); }
.tone-info { background: var(--ocop-tone-sky-soft); color: var(--ocop-tone-sky); }
.tone-warning { background: var(--ocop-warning-soft); color: var(--ocop-warning); }
.tone-success { background: var(--ocop-success-soft); color: var(--ocop-success); }
.tone-danger { background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); }

.state { display: grid; padding: var(--ocop-space-12); justify-items: center; gap: var(--ocop-space-3); border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-lg); background: var(--ocop-white); color: var(--ocop-mist-700); }
.state p { margin: 0; }
.state.is-error { color: var(--ocop-danger-strong); }

.banners { display: grid; gap: var(--ocop-space-3); }
.banners:empty { display: none; }
.notice { margin: 0; padding: var(--ocop-space-3) var(--ocop-space-4); border-radius: var(--ocop-radius-sm); font-size: var(--ocop-font-size-small); line-height: 1.5; }
.notice p { margin: var(--ocop-space-1) 0 0; }
.notice.is-success { background: var(--ocop-success-soft); color: var(--ocop-success); }
.notice.is-error { background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); }
.notice.is-warning { background: var(--ocop-warning-soft); color: var(--ocop-mist-900); }
.notice.is-info { background: var(--ocop-tone-sky-soft); color: var(--ocop-mist-900); }

.stepper { display: grid; gap: var(--ocop-space-2); scroll-margin-top: var(--ocop-space-4); }
.stepper p { margin: 0; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); }
.stepper ol { display: flex; margin: 0; padding: 0; gap: 6px; list-style: none; }
.stepper li { height: 6px; flex: 1; border-radius: var(--ocop-radius-pill); background: var(--ocop-mist-200); }
.stepper li.done { background: var(--ocop-mist-950); }
.stepper li.current { background: var(--ocop-daquy-400); }

.editor-grid { display: grid; grid-template-columns: minmax(0, 1fr) 320px; align-items: start; gap: var(--ocop-space-6); }
.editor-form { display: grid; min-width: 0; margin: 0; padding: 0; gap: var(--ocop-space-5); border: 0; }
.card { display: grid; min-width: 0; gap: var(--ocop-space-4); padding: var(--ocop-space-6); border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-lg); background: var(--ocop-white); }
.card h2 { margin: 0; font-size: var(--ocop-font-size-title-sm); font-weight: 700; }
.card-head { display: grid; gap: var(--ocop-space-1); }
.card-head p { margin: 0; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); }
.card-head.is-row { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--ocop-space-3); }

label, .label { display: grid; gap: 6px; font-size: var(--ocop-font-size-small); font-weight: 600; }
input[type='text'], input[type='tel'], input[type='url'], select, textarea {
  width: 100%; min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-3); border: 1px solid var(--ocop-mist-300);
  border-radius: var(--ocop-radius-sm); background: var(--ocop-white); color: var(--ocop-mist-950); font: inherit; font-size: var(--ocop-font-size-body); font-weight: 400;
}
textarea { padding: var(--ocop-space-3); resize: vertical; }
:is(input, select, textarea):focus-visible { border-color: var(--ocop-mist-700); outline: 3px solid color-mix(in srgb, var(--ocop-daquy-400) 70%, transparent); outline-offset: 1px; }
fieldset:disabled :is(input, select, textarea) { background: var(--ocop-mist-50); color: var(--ocop-mist-800); }
label small, .paste-box small, .dropzone small { color: var(--ocop-mist-600); font-size: var(--ocop-font-size-caption); font-weight: 400; }
label small.is-ok { color: var(--ocop-success); }
.grid-2 { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ocop-space-4); }
.grid-3 { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--ocop-space-4); }
.grid-address { display: grid; grid-template-columns: minmax(0, 2fr) minmax(0, 1fr); gap: var(--ocop-space-4); }

.btn-dark, .btn-line, .btn-accent, .btn-text {
  display: inline-flex; min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-5); align-items: center; justify-content: center; gap: var(--ocop-space-2);
  border-radius: var(--ocop-radius-sm); font-size: var(--ocop-font-size-small); font-weight: 700; text-decoration: none; white-space: nowrap; cursor: pointer;
}
.btn-dark { border: 0; background: var(--ocop-mist-950); color: var(--ocop-white); }
.btn-line { border: 1px solid var(--ocop-mist-400); background: var(--ocop-white); color: var(--ocop-mist-950); }
.btn-accent { border: 0; background: var(--ocop-daquy-400); color: var(--ocop-mist-950); }
.btn-accent:disabled { background: var(--ocop-mist-200); color: var(--ocop-mist-700); opacity: 1; }
.btn-text { padding: 0 var(--ocop-space-2); border: 0; background: transparent; color: var(--ocop-mist-700); text-decoration: underline; }
.is-danger { color: var(--ocop-danger-strong); }
button:disabled { cursor: not-allowed; opacity: 0.65; }
:is(a, button, .file-button):focus-visible, .file-button:focus-within { outline: 3px solid var(--ocop-daquy-400); outline-offset: 2px; }

.segmented { display: grid; padding: var(--ocop-space-1); grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--ocop-space-2); border-radius: var(--ocop-radius-md); background: var(--ocop-mist-100); }
.segmented button { display: inline-flex; min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-3); align-items: center; justify-content: center; gap: var(--ocop-space-2); border: 0; border-radius: var(--ocop-radius-sm); background: transparent; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); font-weight: 600; }
.segmented button.active { background: var(--ocop-white); box-shadow: var(--ocop-shadow-sm); color: var(--ocop-mist-950); }
.method-box { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: var(--ocop-space-4); padding: var(--ocop-space-4); border-radius: var(--ocop-radius-md); background: var(--ocop-tone-sky-soft); }
.method-box > div { display: grid; gap: var(--ocop-space-1); }
.method-box span { color: var(--ocop-mist-800); font-size: var(--ocop-font-size-small); }
.paste-box { display: grid; gap: 6px; font-size: var(--ocop-font-size-small); font-weight: 600; }
.inline-field { display: flex; gap: var(--ocop-space-2); }
.inline-field input { flex: 1; min-width: 0; }
.field-error { width: 100%; margin: 0; color: var(--ocop-danger-strong); font-size: var(--ocop-font-size-small); }

.map-box { position: relative; height: 340px; overflow: hidden; border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-md); }
.map-hint { position: absolute; z-index: 500; top: var(--ocop-space-3); left: var(--ocop-space-3); max-width: calc(100% - 80px); margin: 0; padding: var(--ocop-space-2) var(--ocop-space-3); border-radius: var(--ocop-radius-sm); background: var(--ocop-white); box-shadow: var(--ocop-shadow-sm); color: var(--ocop-mist-800); font-size: var(--ocop-font-size-small); }
.facts { display: grid; margin: 0; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--ocop-space-3); }
.facts div { display: grid; gap: 2px; padding: var(--ocop-space-3); border-radius: var(--ocop-radius-sm); background: var(--ocop-mist-50); }
.facts dt { color: var(--ocop-mist-600); font-size: var(--ocop-font-size-caption); font-weight: 400; }
.facts dd { margin: 0; font-weight: 700; }
.num { font-variant-numeric: tabular-nums; }
.checks { display: grid; margin: 0; padding: 0; gap: var(--ocop-space-2); list-style: none; }
.checks li { display: flex; align-items: flex-start; gap: var(--ocop-space-2); font-size: var(--ocop-font-size-small); }
.checks li.ok :deep(.app-icon) { color: var(--ocop-success); }
.checks li.warn { color: var(--ocop-mist-950); }
.checks li.warn :deep(.app-icon) { color: var(--ocop-warning); }
.checks li.muted { color: var(--ocop-mist-700); }

.services { display: grid; gap: var(--ocop-space-2); }
.chips { display: flex; flex-wrap: wrap; gap: var(--ocop-space-2); }
.chip { min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-4); border: 1px solid var(--ocop-mist-300); border-radius: var(--ocop-radius-pill); background: var(--ocop-white); color: var(--ocop-mist-800); font-size: var(--ocop-font-size-small); font-weight: 600; }
.chip[aria-pressed='true'] { border-color: var(--ocop-mist-900); background: var(--ocop-mist-900); color: var(--ocop-white); }

.dropzone { display: grid; padding: var(--ocop-space-6); justify-items: center; gap: var(--ocop-space-2); border: 2px dashed var(--ocop-mist-300); border-radius: var(--ocop-radius-md); background: var(--ocop-mist-50); text-align: center; }
.dropzone.is-over { border-color: var(--ocop-mist-700); background: var(--ocop-daquy-50); }
.dropzone :deep(.app-icon) { color: var(--ocop-mist-600); }
.file-button { display: inline-flex; font-size: var(--ocop-font-size-small); }
.upload-status { margin: 0; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); }
.gallery { display: grid; margin: 0; padding: 0; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: var(--ocop-space-3); list-style: none; }
.gallery li { overflow: hidden; border: 2px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-md); background: var(--ocop-white); }
.gallery li.primary { border-color: var(--ocop-daquy-400); }
.gallery img { display: block; width: 100%; aspect-ratio: 4 / 3; background: var(--ocop-mist-100); object-fit: cover; }
.gallery-actions { display: flex; padding: var(--ocop-space-1) var(--ocop-space-2); align-items: center; justify-content: space-between; gap: var(--ocop-space-1); }
.radio { display: inline-flex; min-height: var(--ocop-control-md); align-items: center; gap: var(--ocop-space-2); font-size: var(--ocop-font-size-caption); }
.radio input, .check-row input { width: 20px; height: 20px; accent-color: var(--ocop-mist-900); }
.check-row { display: flex; min-height: var(--ocop-control-md); padding: 0 var(--ocop-space-3); align-items: center; gap: var(--ocop-space-3); border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-sm); font-weight: 400; }
.muted-text { margin: 0; color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); }

.status-card { position: sticky; top: var(--ocop-space-6); gap: var(--ocop-space-4); padding: var(--ocop-space-5); }
.status-card h2 { font-size: var(--ocop-font-size-body-lg); }
.checklist { display: grid; margin: 0; padding: 0; gap: 10px; list-style: none; }
.checklist li { display: flex; align-items: center; gap: 10px; color: var(--ocop-mist-950); font-size: var(--ocop-font-size-small); font-weight: 600; }
.checklist li.done { color: var(--ocop-mist-800); font-weight: 400; }
.check-mark { display: grid; width: 24px; height: 24px; flex-shrink: 0; place-items: center; border-radius: var(--ocop-radius-pill); background: var(--ocop-warning-soft); color: var(--ocop-warning); font-size: var(--ocop-font-size-small); font-weight: 800; }
.done .check-mark { background: var(--ocop-success-soft); color: var(--ocop-success); }
.summary { margin: 0; padding: var(--ocop-space-3); border-radius: var(--ocop-radius-sm); background: var(--ocop-warning-soft); color: var(--ocop-mist-900); font-size: var(--ocop-font-size-small); line-height: 1.5; }
.summary.is-ok { background: var(--ocop-success-soft); color: var(--ocop-success); }
.after { display: grid; gap: 6px; padding-top: var(--ocop-space-3); border-top: 1px solid var(--ocop-mist-100); color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); line-height: 1.5; }
.after strong { color: var(--ocop-mist-950); }

.action-bar { position: sticky; z-index: 600; bottom: 0; display: flex; flex-wrap: wrap; margin-bottom: var(--ocop-space-4); padding: var(--ocop-space-4) var(--ocop-space-6); align-items: center; justify-content: space-between; gap: var(--ocop-space-4); border: 1px solid var(--ocop-mist-200); border-radius: var(--ocop-radius-lg); background: var(--ocop-white); box-shadow: 0 -8px 24px color-mix(in srgb, var(--ocop-mist-950) 8%, transparent); }
.saved-text { color: var(--ocop-mist-700); font-size: var(--ocop-font-size-small); }
.action-buttons { display: flex; flex-wrap: wrap; gap: var(--ocop-space-3); }

@media (max-width: 1199.98px) {
  .editor-grid { grid-template-columns: 1fr; }
  .status-card { position: static; }
}
@media (max-width: 767.98px) {
  .card { padding: var(--ocop-space-4); }
  .grid-2, .grid-3, .grid-address, .facts, .segmented { grid-template-columns: 1fr; }
  .map-box { height: 320px; }
  .action-bar { margin-inline: calc(var(--ocop-space-4) * -1); margin-bottom: 0; padding: var(--ocop-space-3) var(--ocop-space-4); border-radius: 0; }
  .action-buttons { width: 100%; }
  .action-buttons > * { flex: 1; }
  .saved-text:empty { display: none; }
}
@media (prefers-reduced-motion: reduce) {
  * { scroll-behavior: auto !important; }
}
</style>
