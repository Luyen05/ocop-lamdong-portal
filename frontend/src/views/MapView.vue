<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import LeafletMap from '@/components/map/LeafletMap.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import {
  getLocationFilterOptions,
  getMapLocations,
  getNearbyLocations,
  getRoute,
} from '@/services/locations'
import type {
  Coordinate,
  LocationType,
  LocationTypeOption,
  MapFeature,
  NearbyLocation,
  RouteResponse,
} from '@/types/location'
import {
  externalDirectionsUrl,
  formatDistance,
  formatDuration,
  formatTicketPrice,
  isLocationType,
  locationTypeStyle,
  sortVietnamese,
} from '@/utils/location'

const NEARBY_RADIUS_KM = 50
const NEARBY_LIMIT = 5

const route = useRoute()
const router = useRouter()

const features = ref<MapFeature[]>([])
const typeOptions = ref<LocationTypeOption[]>([])
const districts = ref<string[]>([])
const isLoading = ref(false)
const errorMessage = ref('')
const selectedSlug = ref<string | null>(null)

const userPosition = ref<Coordinate | null>(null)
const isLocating = ref(false)
const locationMessage = ref('')
const nearby = ref<NearbyLocation[]>([])
const isLoadingNearby = ref(false)

const routeResult = ref<RouteResponse | null>(null)
const isRouting = ref(false)
const routeMessage = ref('')
let latestRequestId = 0

const filters = reactive({
  search: '',
  type: '' as LocationType | '',
  district: '',
})

const selectedFeature = computed(
  () => features.value.find((feature) => feature.properties.slug === selectedSlug.value) ?? null,
)
const selectedCoordinates = computed(() => {
  if (!selectedFeature.value) return null
  const [longitude, latitude] = selectedFeature.value.geometry.coordinates
  return { latitude, longitude }
})
const routeLine = computed(() => routeResult.value?.geometry.coordinates ?? null)
const directionsUrl = computed(() =>
  selectedCoordinates.value
    ? externalDirectionsUrl(selectedCoordinates.value.latitude, selectedCoordinates.value.longitude)
    : '',
)
const hasFilters = computed(() => Boolean(filters.search || filters.type || filters.district))

function queryText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

async function loadFeatures(): Promise<void> {
  const requestId = ++latestRequestId
  isLoading.value = true
  errorMessage.value = ''
  try {
    const collection = await getMapLocations({
      search: filters.search || undefined,
      type: filters.type || undefined,
      district: filters.district || undefined,
    })
    if (requestId !== latestRequestId) return
    features.value = collection.features
    if (selectedSlug.value && !selectedFeature.value) clearSelection()
  } catch (error) {
    if (requestId !== latestRequestId) return
    features.value = []
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải dữ liệu bản đồ. Vui lòng thử lại.')
  } finally {
    if (requestId === latestRequestId) isLoading.value = false
  }
}

async function loadFilterOptions(): Promise<void> {
  try {
    const options = await getLocationFilterOptions()
    typeOptions.value = options.types
    districts.value = sortVietnamese(options.districts)
  } catch {
    typeOptions.value = []
    districts.value = []
  }
}

async function applyFilters(): Promise<void> {
  filters.search = filters.search.trim()
  await loadFeatures()
  if (userPosition.value) await loadNearby(userPosition.value)
}

async function clearFilters(): Promise<void> {
  Object.assign(filters, { search: '', type: '', district: '' })
  await applyFilters()
}

function clearRoute(): void {
  routeResult.value = null
  routeMessage.value = ''
}

function clearSelection(): void {
  selectedSlug.value = null
  clearRoute()
  if (route.query.diem) void router.replace({ name: 'map', query: {} })
}

function selectLocation(slug: string): void {
  if (slug === selectedSlug.value) return
  selectedSlug.value = slug
  clearRoute()
  void router.replace({ name: 'map', query: { diem: slug } })
}

function geolocationErrorMessage(error: GeolocationPositionError): string {
  if (error.code === error.PERMISSION_DENIED) {
    return 'Bạn chưa cho phép truy cập vị trí. Hãy bật quyền vị trí cho trang web rồi thử lại.'
  }
  if (error.code === error.TIMEOUT) return 'Hết thời gian xác định vị trí. Vui lòng thử lại.'
  return 'Không xác định được vị trí hiện tại của bạn.'
}

function requestCurrentPosition(): Promise<Coordinate> {
  return new Promise((resolve, reject) => {
    if (!('geolocation' in navigator)) {
      reject(new Error('Trình duyệt không hỗ trợ định vị.'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) =>
        resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude }),
      (error) => reject(new Error(geolocationErrorMessage(error))),
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 60_000 },
    )
  })
}

async function loadNearby(origin: Coordinate): Promise<void> {
  isLoadingNearby.value = true
  try {
    const response = await getNearbyLocations(origin, {
      radiusKm: NEARBY_RADIUS_KM,
      limit: NEARBY_LIMIT,
      type: filters.type || undefined,
    })
    nearby.value = response.items
    locationMessage.value = response.items.length
      ? ''
      : `Không có điểm du lịch nào trong bán kính ${NEARBY_RADIUS_KM} km quanh bạn.`
  } catch (error) {
    nearby.value = []
    locationMessage.value = getApiErrorMessage(error, 'Không thể tìm điểm gần bạn.')
  } finally {
    isLoadingNearby.value = false
  }
}

async function locateUser(): Promise<Coordinate | null> {
  isLocating.value = true
  locationMessage.value = ''
  try {
    userPosition.value = await requestCurrentPosition()
    await loadNearby(userPosition.value)
    return userPosition.value
  } catch (error) {
    locationMessage.value = error instanceof Error ? error.message : 'Không xác định được vị trí.'
    return null
  } finally {
    isLocating.value = false
  }
}

async function showRoute(): Promise<void> {
  if (!selectedFeature.value) return
  const destination = selectedFeature.value.properties.slug
  routeMessage.value = ''
  const origin = userPosition.value ?? (await locateUser())
  if (!origin) {
    routeMessage.value = 'Cần vị trí hiện tại của bạn để gợi ý tuyến đường.'
    return
  }
  isRouting.value = true
  try {
    const result = await getRoute(destination, origin)
    if (selectedSlug.value === destination) routeResult.value = result
  } catch (error) {
    routeResult.value = null
    routeMessage.value = getApiErrorMessage(error, 'Không thể gợi ý tuyến đường lúc này.')
  } finally {
    isRouting.value = false
  }
}

watch(
  () => route.query.diem,
  (value) => {
    const slug = queryText(value)
    if (slug && slug !== selectedSlug.value) {
      selectedSlug.value = slug
      clearRoute()
    }
  },
  { immediate: true },
)

onMounted(() => {
  const requestedType = queryText(route.query.type)
  if (isLocationType(requestedType)) filters.type = requestedType
  document.title = 'Bản đồ số du lịch nông nghiệp | OCOP Lâm Đồng'
  void loadFilterOptions()
  void loadFeatures()
})

onUnmounted(() => {
  document.title = 'OCOP Lâm Đồng'
})
</script>

<template>
  <main class="map-page">
    <aside class="map-panel" aria-label="Công cụ bản đồ">
      <header class="panel-header">
        <span class="eyebrow">Bản đồ số Lâm Đồng</span>
        <h1>Khám phá du lịch nông nghiệp</h1>
        <p>{{ features.length }} điểm đến đang hiển thị trên bản đồ.</p>
      </header>

      <form class="panel-section filter-form" role="search" @submit.prevent="applyFilters">
        <label class="visually-hidden" for="map-search">Tìm điểm du lịch</label>
        <div class="search-row">
          <input
            id="map-search"
            v-model="filters.search"
            class="form-control"
            type="search"
            maxlength="150"
            placeholder="Tìm đồi chè, vườn dâu..."
          />
          <button class="btn btn-success" type="submit" :disabled="isLoading" aria-label="Tìm kiếm">
            <AppIcon name="search" :size="16" />
          </button>
        </div>
        <div class="select-row">
          <select v-model="filters.type" class="form-select" aria-label="Lọc theo loại hình" @change="applyFilters">
            <option value="">Mọi loại hình</option>
            <option v-for="option in typeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.district" class="form-select" aria-label="Lọc theo địa bàn" @change="applyFilters">
            <option value="">Mọi địa bàn</option>
            <option v-for="district in districts" :key="district" :value="district">{{ district }}</option>
          </select>
        </div>
        <button v-if="hasFilters" class="btn-link-reset" type="button" @click="clearFilters">Xóa bộ lọc</button>
      </form>

      <div v-if="errorMessage" class="panel-section alert alert-danger mb-0" role="alert">
        {{ errorMessage }}
        <button class="btn btn-sm btn-outline-danger ms-2" type="button" @click="loadFeatures">Thử lại</button>
      </div>

      <section class="panel-section" aria-labelledby="nearby-title">
        <div class="section-title-row">
          <h2 id="nearby-title">Điểm gần bạn</h2>
          <button class="btn btn-sm btn-outline-success" type="button" :disabled="isLocating" @click="locateUser">
            <AppIcon name="navigation" :size="14" />
            {{ isLocating ? 'Đang định vị...' : userPosition ? 'Cập nhật vị trí' : 'Định vị tôi' }}
          </button>
        </div>
        <p v-if="locationMessage" class="panel-message" role="status">{{ locationMessage }}</p>
        <p v-else-if="!userPosition" class="panel-hint">
          Cho phép truy cập vị trí để tìm điểm du lịch gần nhất trong bán kính {{ NEARBY_RADIUS_KM }} km.
        </p>
        <p v-if="isLoadingNearby" class="panel-hint">Đang tìm điểm gần nhất...</p>
        <ol v-else-if="nearby.length" class="nearby-list">
          <li v-for="item in nearby" :key="item.id">
            <button type="button" :class="{ active: item.slug === selectedSlug }" @click="selectLocation(item.slug)">
              <span>
                <strong>{{ item.name }}</strong>
                <small>{{ item.type_label }} · {{ item.district }}</small>
              </span>
              <em>{{ formatDistance(item.distance_m) }}</em>
            </button>
          </li>
        </ol>
      </section>

      <section v-if="selectedFeature" class="panel-section selected-card" aria-labelledby="selected-title" aria-live="polite">
        <div class="section-title-row">
          <span
            class="type-badge"
            :style="{ '--type-color': locationTypeStyle(selectedFeature.properties.type).color }"
          >
            {{ selectedFeature.properties.type_label }}
          </span>
          <button class="close-button" type="button" aria-label="Bỏ chọn điểm" @click="clearSelection">
            <AppIcon name="close" :size="13" />
          </button>
        </div>
        <h2 id="selected-title">{{ selectedFeature.properties.name }}</h2>
        <p class="selected-address"><AppIcon name="map-pin" :size="13" /> {{ selectedFeature.properties.address }}</p>
        <dl class="selected-facts">
          <div>
            <dt>Giờ mở cửa</dt>
            <dd>{{ selectedFeature.properties.opening_hours || 'Chưa cập nhật' }}</dd>
          </div>
          <div>
            <dt>Giá vé</dt>
            <dd>{{ formatTicketPrice(selectedFeature.properties.ticket_price) }}</dd>
          </div>
        </dl>

        <div class="selected-actions">
          <button class="btn btn-success" type="button" :disabled="isRouting || isLocating" @click="showRoute">
            <AppIcon name="navigation" :size="15" /> {{ isRouting ? 'Đang tìm đường...' : 'Chỉ đường' }}
          </button>
          <RouterLink
            class="btn btn-outline-success"
            :to="{ name: 'location-detail', params: { slug: selectedFeature.properties.slug } }"
          >
            Xem chi tiết
          </RouterLink>
        </div>

        <div v-if="routeResult" class="route-summary" role="status">
          <strong>{{ formatDistance(routeResult.distance_m) }}</strong>
          <span>khoảng {{ formatDuration(routeResult.duration_s) }} lái xe</span>
          <button class="btn-link-reset" type="button" @click="clearRoute">Ẩn tuyến</button>
        </div>
        <p v-if="routeMessage" class="panel-message" role="alert">{{ routeMessage }}</p>
        <a class="external-directions" :href="directionsUrl" target="_blank" rel="noopener noreferrer">
          Mở chỉ đường bằng Google Maps
        </a>
      </section>

      <section class="panel-section" aria-labelledby="all-locations-title">
        <h2 id="all-locations-title">Tất cả điểm đến</h2>
        <p v-if="isLoading" class="panel-hint">Đang tải dữ liệu bản đồ...</p>
        <p v-else-if="!features.length && !errorMessage" class="panel-hint">
          Không có điểm du lịch phù hợp với bộ lọc.
        </p>
        <ul v-else class="location-list">
          <li v-for="feature in features" :key="feature.properties.slug">
            <button
              type="button"
              :class="{ active: feature.properties.slug === selectedSlug }"
              @click="selectLocation(feature.properties.slug)"
            >
              <i
                class="type-dot"
                :style="{ background: locationTypeStyle(feature.properties.type).color }"
                aria-hidden="true"
              />
              <span>
                <strong>{{ feature.properties.name }}</strong>
                <small>{{ feature.properties.type_label }} · {{ feature.properties.district }}</small>
              </span>
            </button>
          </li>
        </ul>
      </section>

      <p class="panel-note">
        Dữ liệu điểm đến mang tính tham khảo. Tuyến đường do dịch vụ OSRM (OpenStreetMap) gợi ý.
      </p>
    </aside>

    <section class="map-canvas" aria-label="Bản đồ">
      <LeafletMap
        :features="features"
        :selected-slug="selectedSlug"
        :user-position="userPosition"
        :route="routeLine"
        @select="selectLocation"
      />
    </section>
  </main>
</template>

<style scoped>
.map-page {
  display: grid;
  min-height: calc(100vh - 4.5rem);
  background: var(--ocop-surface);
}

.map-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 16px;
  background: var(--ocop-surface);
}

.panel-header h1 {
  margin: 4px 0;
  color: var(--ocop-primary-950);
  font-size: 1.5rem;
  font-weight: 800;
}

.panel-header p,
.panel-hint,
.panel-note {
  margin: 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
}

.eyebrow {
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
  text-transform: uppercase;
}

.panel-section {
  padding: 14px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
}

.panel-section h2 {
  margin: 0;
  color: var(--ocop-navy);
  font-size: 1rem;
  font-weight: 800;
}

.filter-form {
  display: grid;
  gap: 8px;
}

.search-row,
.select-row {
  display: flex;
  gap: 8px;
}

.select-row .form-select {
  min-width: 0;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-bottom: 8px;
}

.section-title-row .btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.panel-message {
  margin: 8px 0 0;
  color: var(--ocop-warning);
  font-size: var(--ocop-font-size-small);
}

.btn-link-reset {
  justify-self: start;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
}

.nearby-list,
.location-list {
  display: grid;
  gap: 6px;
  margin: 8px 0 0;
  padding: 0;
  list-style: none;
}

.nearby-list button,
.location-list button {
  display: flex;
  width: 100%;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  padding: 8px 10px;
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-surface-subtle);
  color: var(--ocop-navy);
  text-align: left;
}

.location-list button {
  justify-content: flex-start;
}

.nearby-list button:hover,
.location-list button:hover,
.nearby-list button.active,
.location-list button.active {
  border-color: var(--ocop-mint-border);
  background: var(--ocop-mint-soft);
}

.nearby-list strong,
.location-list strong {
  display: block;
  font-size: var(--ocop-font-size-small);
}

.nearby-list small,
.location-list small {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
}

.nearby-list em {
  flex: 0 0 auto;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-style: normal;
  font-weight: 800;
}

.type-dot {
  width: 10px;
  height: 10px;
  flex: 0 0 auto;
  border-radius: 50%;
}

.selected-card {
  border-color: var(--ocop-mint-border);
  box-shadow: var(--ocop-shadow-sm);
}

.selected-card h2 {
  font-size: 1.15rem;
}

.type-badge {
  padding: 4px 9px;
  border-radius: 999px;
  background: var(--type-color, var(--ocop-primary-700));
  color: #fff;
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.close-button {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border: 1px solid var(--ocop-border);
  border-radius: 50%;
  background: #fff;
}

.selected-address {
  margin: 6px 0 10px;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
}

.selected-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin: 0 0 12px;
}

.selected-facts dt {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.selected-facts dd {
  margin: 0;
  font-size: var(--ocop-font-size-small);
  font-weight: 650;
}

.selected-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.selected-actions .btn {
  display: inline-flex;
  align-items: center;
  gap: 5px;
}

.route-summary {
  display: flex;
  flex-wrap: wrap;
  align-items: baseline;
  gap: 8px;
  margin-top: 12px;
  padding: 10px 12px;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-mint-soft);
}

.route-summary strong {
  color: var(--ocop-primary-900);
  font-size: 1.1rem;
}

.route-summary span {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
}

.external-directions {
  display: inline-block;
  margin-top: 10px;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
}

.map-canvas {
  position: relative;
  height: 62vh;
  min-height: 360px;
  order: -1;
}

@media (min-width: 992px) {
  .map-page {
    grid-template-columns: 380px minmax(0, 1fr);
    height: calc(100vh - 4.5rem);
    min-height: 560px;
  }

  .map-panel {
    overflow-y: auto;
    border-right: 1px solid var(--ocop-border);
  }

  .map-canvas {
    height: 100%;
    order: 0;
  }
}
</style>
