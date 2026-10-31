<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import LeafletMap from '@/components/map/LeafletMap.vue'
import MapLegend from '@/components/map/MapLegend.vue'
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
  hasValidCoordinates,
  isInsideLamDong,
  isLocationType,
  isSameQuery,
  locationTypeStyle,
  matchesNearbyFilters,
  mergeQuery,
  nearbyToFeature,
  sortVietnamese,
  splitMappableFeatures,
} from '@/utils/location'
import { scrollBehavior } from '@/utils/motion'

const DEFAULT_RADIUS_KM = 50
const RADIUS_OPTIONS_KM = [10, 25, 50, 100]
const NEARBY_LIMIT = 5
// /map/nearby chỉ lọc theo loại hình; khi cần lọc thêm địa bàn/từ khóa phía client thì lấy rộng hơn rồi cắt.
const NEARBY_FETCH_LIMIT = 50
// Dưới 992px bố cục xếp dọc: bản đồ ở trên, panel ở dưới.
const COMPACT_QUERY = '(max-width: 991.98px)'

interface MapFilterState {
  search: string
  type: LocationType | ''
  district: string
}

const route = useRoute()
const router = useRouter()

const features = ref<MapFeature[]>([])
// Điểm chọn từ "Điểm gần bạn" nhưng nằm ngoài bộ lọc hiện tại: thêm tạm vào tập hiển thị.
const extraFeatures = ref<MapFeature[]>([])
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
const radiusKm = ref(DEFAULT_RADIUS_KM)

const routeResult = ref<RouteResponse | null>(null)
const isRouting = ref(false)
const routeMessage = ref('')
let latestRequestId = 0
let latestNearbyId = 0

const isCompact = ref(false)
const selectedCard = ref<HTMLElement | null>(null)
const mapCanvas = ref<HTMLElement | null>(null)
const allLocationsTitle = ref<HTMLElement | null>(null)
let compactQuery: MediaQueryList | null = null

function queryText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function filtersFromQuery(query: Record<string, unknown>): MapFilterState {
  const type = queryText(query.type)
  return {
    search: queryText(query.search).slice(0, 150),
    type: isLocationType(type) ? type : '',
    district: queryText(query.district).slice(0, 100),
  }
}

function sameFilters(first: MapFilterState, second: MapFilterState): boolean {
  return first.search === second.search && first.type === second.type && first.district === second.district
}

// `filters` là giá trị trong ô nhập; `applied` là bộ lọc đã áp dụng (khớp URL và dữ liệu đang hiển thị).
const filters = reactive<MapFilterState>(filtersFromQuery(route.query))
const applied = reactive<MapFilterState>({ ...filters })

const displayFeatures = computed(() => {
  // Không có điểm tạm thì trả đúng mảng gốc: LeafletMap chỉ vẽ lại marker khi tham chiếu mảng đổi.
  if (!extraFeatures.value.length) return features.value
  const present = new Set(features.value.map((feature) => feature.properties.slug))
  return [...features.value, ...extraFeatures.value.filter((feature) => !present.has(feature.properties.slug))]
})
const selectedFeature = computed(
  () => displayFeatures.value.find((feature) => feature.properties.slug === selectedSlug.value) ?? null,
)
const isOutsideFilter = computed(
  () =>
    Boolean(selectedFeature.value) &&
    !features.value.some((feature) => feature.properties.slug === selectedSlug.value),
)
const mappable = computed(() => splitMappableFeatures(features.value).mappable)
const mappableCount = computed(() => splitMappableFeatures(displayFeatures.value).mappable.length)
const unmappableCount = computed(() => splitMappableFeatures(displayFeatures.value).unmappable.length)
const selectedCoordinates = computed(() => {
  if (!selectedFeature.value || !hasValidCoordinates(selectedFeature.value)) return null
  const [longitude, latitude] = selectedFeature.value.geometry.coordinates
  return { latitude, longitude }
})
const routeIntent = computed(() => route.query.action === 'route' && route.query.diem === selectedSlug.value)
const routeLine = computed(() => routeResult.value?.geometry.coordinates ?? null)
const directionsUrl = computed(() =>
  selectedCoordinates.value
    ? externalDirectionsUrl(selectedCoordinates.value.latitude, selectedCoordinates.value.longitude)
    : '',
)
const hasFilters = computed(() => Boolean(filters.search || filters.type || filters.district))
const districtOptions = computed(() =>
  filters.district && !districts.value.includes(filters.district)
    ? [...districts.value, filters.district]
    : districts.value,
)
const hasNearbyFilters = computed(() => Boolean(applied.search || applied.district))

/** Ghi bộ lọc/điểm chọn lên URL nhưng giữ các tham số còn lại; không gọi router khi query không đổi. */
function writeQuery(patch: Record<string, string | undefined>, mode: 'push' | 'replace' = 'replace'): void {
  const query = mergeQuery(route.query, patch)
  if (isSameQuery(query, route.query)) return
  void router[mode]({ name: 'map', query })
}

async function loadFeatures(): Promise<void> {
  const requestId = ++latestRequestId
  isLoading.value = true
  errorMessage.value = ''
  try {
    const collection = await getMapLocations({
      search: applied.search || undefined,
      type: applied.type || undefined,
      district: applied.district || undefined,
    })
    if (requestId !== latestRequestId) return
    features.value = collection.features
    // Chỉ giữ điểm "ngoài bộ lọc" khi nó vẫn đang được chọn và chưa nằm trong kết quả mới.
    keepExtras((extra) =>
      extra.properties.slug === selectedSlug.value &&
      !collection.features.some((feature) => feature.properties.slug === extra.properties.slug),
    )
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

/** Áp dụng bộ lọc trong ô nhập: ghi URL (push cho select, replace cho tìm kiếm) rồi tải lại. */
async function applyFilters(urlMode: 'push' | 'replace' | false = 'replace'): Promise<void> {
  filters.search = filters.search.trim()
  Object.assign(applied, filters)
  if (urlMode) {
    writeQuery({ search: applied.search, type: applied.type, district: applied.district }, urlMode)
  }
  await loadFeatures()
  if (userPosition.value) await loadNearby(userPosition.value)
}

async function clearFilters(): Promise<void> {
  Object.assign(filters, { search: '', type: '', district: '' })
  await applyFilters('push')
}

async function selectLegendType(type: LocationType | ''): Promise<void> {
  filters.type = type
  await applyFilters('push')
}

/** Chỉ gán lại khi thật sự có điểm bị bỏ, tránh đổi tham chiếu mảng làm bản đồ vẽ lại toàn bộ marker. */
function keepExtras(predicate: (feature: MapFeature) => boolean): void {
  if (!extraFeatures.value.length) return
  const kept = extraFeatures.value.filter(predicate)
  if (kept.length !== extraFeatures.value.length) extraFeatures.value = kept
}

function clearRoute(): void {
  routeResult.value = null
  routeMessage.value = ''
}

function clearSelection(): void {
  selectedSlug.value = null
  keepExtras(() => false)
  clearRoute()
  writeQuery({ diem: undefined, action: undefined })
}

async function closeSelection(): Promise<void> {
  clearSelection()
  // Nút đóng biến mất cùng thẻ: đưa focus về đầu danh sách để người dùng bàn phím không bị mất vị trí.
  await nextTick()
  allLocationsTitle.value?.focus()
}

function selectLocation(slug: string): void {
  if (slug === selectedSlug.value) {
    void revealSelectedCard()
    return
  }
  selectedSlug.value = slug
  keepExtras((feature) => feature.properties.slug === slug)
  clearRoute()
  writeQuery({ diem: slug, action: undefined })
  void revealSelectedCard()
}

function selectNearby(item: NearbyLocation): void {
  // Điểm gần bạn có thể không thuộc bộ lọc hiện tại: thêm tạm để vẫn có thẻ thông tin và marker.
  if (!features.value.some((feature) => feature.properties.slug === item.slug)) {
    extraFeatures.value = [nearbyToFeature(item)]
  }
  selectLocation(item.slug)
}

/** Phần khung nhìn bị che bởi header dính ở trên và thanh điều hướng dưới (chỉ có trên điện thoại). */
function viewportInsets(): { top: number; bottom: number } {
  const header = document.querySelector<HTMLElement>('.site-header')
  const tabbar = document.querySelector<HTMLElement>('.mobile-tabbar')
  return {
    top: Math.max(0, header?.getBoundingClientRect().bottom ?? 0),
    bottom: tabbar ? tabbar.offsetHeight : 0,
  }
}

/**
 * Trên màn hẹp, thẻ điểm chọn nằm ngay dưới bản đồ (CSS order) nên chỉ cần cuộn đúng đoạn cần thiết cho
 * thẻ lọt vào khung nhìn: chọn từ marker thì bản đồ chỉ bị đẩy lên một phần (vẫn thấy marker), chọn từ
 * danh sách ở phía dưới thì cuộn mềm lên tới thẻ. Tôn trọng prefers-reduced-motion qua scrollBehavior().
 */
async function revealSelectedCard(): Promise<void> {
  if (!isCompact.value) return
  await nextTick()
  const card = selectedCard.value
  if (!card) return
  const insets = viewportInsets()
  const gap = 8
  const rect = card.getBoundingClientRect()
  const top = insets.top + gap
  const bottom = window.innerHeight - insets.bottom - gap
  if (rect.top >= top - 1 && rect.bottom <= bottom + 1) return
  const delta = rect.top < top ? rect.top - top : rect.bottom - bottom
  window.scrollBy({ top: delta, behavior: scrollBehavior() })
}

function showMap(): void {
  const canvas = mapCanvas.value
  if (canvas && typeof canvas.scrollIntoView === 'function') {
    canvas.scrollIntoView({ block: 'start', behavior: scrollBehavior() })
  }
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

function emptyNearbyMessage(origin: Coordinate): string {
  const scope = hasNearbyFilters.value || applied.type ? ' phù hợp với bộ lọc' : ''
  const outside = isInsideLamDong(origin) ? '' : 'Bạn đang ở ngoài Lâm Đồng. '
  return `${outside}Không có điểm du lịch nào${scope} trong bán kính ${radiusKm.value} km quanh bạn.${
    radiusKm.value < RADIUS_OPTIONS_KM[RADIUS_OPTIONS_KM.length - 1] ? ' Hãy thử chọn bán kính lớn hơn.' : ''
  }`
}

/**
 * `report` quyết định có hiện thông báo ở khu "Điểm gần bạn" hay không: khi định vị để chỉ đường,
 * thông báo chỉ nằm cạnh nút "Chỉ đường" (một thông báo duy nhất).
 */
async function loadNearby(origin: Coordinate, report = true): Promise<void> {
  const requestId = ++latestNearbyId
  isLoadingNearby.value = true
  try {
    const response = await getNearbyLocations(origin, {
      radiusKm: radiusKm.value,
      limit: hasNearbyFilters.value ? NEARBY_FETCH_LIMIT : NEARBY_LIMIT,
      type: applied.type || undefined,
    })
    if (requestId !== latestNearbyId) return
    nearby.value = response.items
      .filter((item) => matchesNearbyFilters(item, applied))
      .slice(0, NEARBY_LIMIT)
    if (report) locationMessage.value = nearby.value.length ? '' : emptyNearbyMessage(origin)
  } catch (error) {
    if (requestId !== latestNearbyId) return
    nearby.value = []
    if (report) locationMessage.value = getApiErrorMessage(error, 'Không thể tìm điểm gần bạn.')
  } finally {
    if (requestId === latestNearbyId) isLoadingNearby.value = false
  }
}

async function changeRadius(): Promise<void> {
  if (userPosition.value) await loadNearby(userPosition.value)
}

/** Trả về vị trí hoặc null; thông báo lỗi đi vào ô thông báo của nút đã bấm (`target`). */
async function locateUser(target: 'nearby' | 'route' = 'nearby'): Promise<Coordinate | null> {
  isLocating.value = true
  locationMessage.value = ''
  try {
    userPosition.value = await requestCurrentPosition()
    await loadNearby(userPosition.value, target === 'nearby')
    return userPosition.value
  } catch (error) {
    const message = error instanceof Error ? error.message : 'Không xác định được vị trí.'
    if (target === 'route') routeMessage.value = message
    else locationMessage.value = message
    return null
  } finally {
    isLocating.value = false
  }
}

async function showRoute(): Promise<void> {
  if (!selectedFeature.value || !selectedCoordinates.value) return
  const destination = selectedFeature.value.properties.slug
  routeMessage.value = ''
  const origin = userPosition.value ?? (await locateUser('route'))
  if (!origin) return
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

// Esc bỏ chọn điểm (trừ khi đang gõ trong ô nhập/chọn, nơi Esc có nghĩa riêng).
function onKeydown(event: KeyboardEvent): void {
  if (event.key !== 'Escape' || event.defaultPrevented || !selectedSlug.value) return
  const target = event.target as HTMLElement | null
  if (target?.closest('input, select, textarea')) return
  clearSelection()
}

function onCompactChange(event: MediaQueryListEvent): void {
  isCompact.value = event.matches
}

// Quay lại/tiến tới trong lịch sử hoặc mở liên kết mới: URL là nguồn sự thật cho điểm chọn.
watch(
  () => route.query.diem,
  (value) => {
    const slug = queryText(value)
    if (slug && slug !== selectedSlug.value) {
      selectedSlug.value = slug
      clearRoute()
    } else if (!slug && selectedSlug.value) {
      selectedSlug.value = null
      keepExtras(() => false)
      clearRoute()
    }
  },
  { immediate: true },
)

// Bộ lọc đổi từ phía URL (Back/Forward, liên kết mới): đồng bộ vào ô nhập rồi tải lại.
watch(
  () => JSON.stringify(filtersFromQuery(route.query)),
  () => {
    const next = filtersFromQuery(route.query)
    if (sameFilters(next, applied)) return
    Object.assign(filters, next)
    void applyFilters(false)
  },
)

onMounted(() => {
  document.title = 'Bản đồ số du lịch nông nghiệp | OCOP Lâm Đồng'
  if (typeof window.matchMedia === 'function') {
    compactQuery = window.matchMedia(COMPACT_QUERY)
    isCompact.value = compactQuery.matches
    compactQuery.addEventListener?.('change', onCompactChange)
  }
  window.addEventListener('keydown', onKeydown)
  void loadFilterOptions()
  void loadFeatures()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onKeydown)
  compactQuery?.removeEventListener?.('change', onCompactChange)
})

</script>

<template>
  <main class="map-page">
    <aside class="map-panel" aria-label="Công cụ bản đồ">
      <header class="panel-header">
        <span class="eyebrow">Bản đồ số Lâm Đồng</span>
        <h1>Khám phá du lịch nông nghiệp</h1>
        <p>{{ mappableCount }} điểm đến đang hiển thị trên bản đồ.</p>
        <p class="panel-notice" role="status" data-test="unmappable-notice">
          <template v-if="unmappableCount">
            {{ unmappableCount }} điểm chưa có tọa độ hợp lệ nên chưa hiển thị trên bản đồ (vẫn có trong danh sách).
          </template>
        </p>
      </header>

      <form class="panel-section filter-form" role="search" @submit.prevent="applyFilters('replace')">
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
          <select v-model="filters.type" class="form-select" aria-label="Lọc theo loại hình" @change="applyFilters('push')">
            <option value="">Mọi loại hình</option>
            <option v-for="option in typeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
          <select v-model="filters.district" class="form-select" aria-label="Lọc theo địa bàn" @change="applyFilters('push')">
            <option value="">Mọi địa bàn</option>
            <option v-for="district in districtOptions" :key="district" :value="district">{{ district }}</option>
          </select>
        </div>
        <button v-if="hasFilters" class="btn-link-reset" type="button" @click="clearFilters">Xóa bộ lọc</button>
      </form>

      <MapLegend :features="mappable" :active-type="applied.type" @select="selectLegendType" />

      <div v-if="errorMessage" class="panel-section alert alert-danger mb-0" role="alert">
        {{ errorMessage }}
        <button class="btn btn-sm btn-outline-danger ms-2" type="button" @click="loadFeatures">Thử lại</button>
      </div>

      <section class="panel-section" aria-labelledby="nearby-title">
        <div class="section-title-row">
          <h2 id="nearby-title">Điểm gần bạn</h2>
          <button class="btn btn-sm btn-outline-success" type="button" :disabled="isLocating" @click="locateUser('nearby')">
            <AppIcon name="navigation" :size="14" />
            {{ isLocating ? 'Đang định vị...' : userPosition ? 'Cập nhật vị trí' : 'Định vị tôi' }}
          </button>
        </div>
        <div class="radius-row">
          <label for="nearby-radius">Bán kính tìm</label>
          <select id="nearby-radius" v-model.number="radiusKm" class="form-select form-select-sm" @change="changeRadius">
            <option v-for="option in RADIUS_OPTIONS_KM" :key="option" :value="option">{{ option }} km</option>
          </select>
        </div>
        <p v-if="locationMessage" class="panel-message" role="status">{{ locationMessage }}</p>
        <p v-else-if="!userPosition" class="panel-hint">
          Cho phép truy cập vị trí để tìm điểm du lịch gần nhất trong bán kính {{ radiusKm }} km.
        </p>
        <p v-if="isLoadingNearby" class="panel-hint">Đang tìm điểm gần nhất...</p>
        <ol v-else-if="nearby.length" class="nearby-list">
          <li v-for="item in nearby" :key="item.id">
            <button type="button" :class="{ active: item.slug === selectedSlug }" @click="selectNearby(item)">
              <span>
                <strong>{{ item.name }}</strong>
                <small>{{ item.type_label }} · {{ item.district }}</small>
              </span>
              <em>{{ formatDistance(item.distance_m) }}</em>
            </button>
          </li>
        </ol>
      </section>

      <section
        v-if="selectedFeature"
        ref="selectedCard"
        class="panel-section selected-card"
        aria-labelledby="selected-title"
        aria-live="polite"
      >
        <div class="section-title-row">
          <span
            class="type-badge"
            :style="{ '--type-color': locationTypeStyle(selectedFeature.properties.type).color }"
          >
            {{ selectedFeature.properties.type_label }}
          </span>
          <button class="close-button" type="button" aria-label="Bỏ chọn điểm" @click="closeSelection">
            <AppIcon name="close" :size="13" />
          </button>
        </div>
        <h2 id="selected-title">{{ selectedFeature.properties.name }}</h2>
        <p class="selected-address"><AppIcon name="map-pin" :size="13" /> {{ selectedFeature.properties.address }}</p>
        <p v-if="isOutsideFilter" class="panel-hint selected-note" data-test="outside-filter">
          Điểm này không thuộc bộ lọc hiện tại nhưng vẫn được hiển thị để bạn xem.
        </p>
        <p v-if="!selectedCoordinates" class="panel-hint selected-note" data-test="no-coordinates">
          Điểm này chưa có tọa độ hợp lệ nên chưa hiển thị trên bản đồ và chưa thể chỉ đường.
        </p>
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

        <p v-if="routeIntent && !routeResult" class="panel-hint" data-test="route-intent" role="status">Điểm đến đã chọn. Bấm “Lấy vị trí &amp; chỉ đường” để xác nhận dùng vị trí hiện tại và tìm tuyến đường.</p>
        <div class="selected-actions">
          <button
            v-if="selectedCoordinates"
            class="btn btn-success"
            type="button"
            :disabled="isRouting || isLocating"
            @click="showRoute"
          >
            <AppIcon name="navigation" :size="15" /> {{ isRouting ? 'Đang tìm đường...' : routeIntent ? 'Lấy vị trí & chỉ đường' : 'Chỉ đường' }}
          </button>
          <RouterLink
            class="btn btn-outline-success"
            :to="{ name: 'location-detail', params: { slug: selectedFeature.properties.slug } }"
          >
            Xem chi tiết
          </RouterLink>
          <button v-if="isCompact && selectedCoordinates" class="btn btn-outline-success" type="button" @click="showMap">
            <AppIcon name="map-pin" :size="15" /> Xem trên bản đồ
          </button>
        </div>

        <div v-if="routeResult" class="route-summary" role="status">
          <strong>{{ formatDistance(routeResult.distance_m) }}</strong>
          <span>khoảng {{ formatDuration(routeResult.duration_s) }} lái xe</span>
          <button class="btn-link-reset" type="button" @click="clearRoute">Ẩn tuyến</button>
        </div>
        <p v-if="routeMessage" class="panel-message" role="alert">{{ routeMessage }}</p>
        <a v-if="selectedCoordinates" class="external-directions" :href="directionsUrl" target="_blank" rel="noopener noreferrer">
          Mở chỉ đường bằng Google Maps
        </a>
      </section>

      <section class="panel-section" aria-labelledby="all-locations-title">
        <h2 id="all-locations-title" ref="allLocationsTitle" tabindex="-1">Tất cả điểm đến</h2>
        <p v-if="isLoading" class="panel-hint">Đang tải dữ liệu bản đồ...</p>
        <div v-else-if="!features.length && !errorMessage" class="empty-state">
          <p class="panel-hint">
            {{ hasFilters ? 'Không có điểm du lịch phù hợp với bộ lọc.' : 'Chưa có điểm du lịch nào để hiển thị.' }}
          </p>
          <button v-if="hasFilters" class="btn btn-outline-success btn-sm" type="button" @click="clearFilters">
            Xóa bộ lọc
          </button>
        </div>
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
        Dữ liệu điểm đến mang tính tham khảo. Tuyến đường do dịch vụ chỉ đường gợi ý (dữ liệu OpenStreetMap).
      </p>
    </aside>

    <section ref="mapCanvas" class="map-canvas" aria-label="Bản đồ">
      <LeafletMap
        :features="displayFeatures"
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
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-4);
  background: var(--ocop-surface);
}

.panel-header h1 {
  margin: var(--ocop-space-1) 0;
  color: var(--ocop-primary-950);
  font-size: var(--ocop-font-size-title-md);
  font-weight: 800;
}

.panel-notice {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-warning);
  font-size: var(--ocop-font-size-small);
}

.panel-notice:empty {
  display: none;
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
  font-size: var(--ocop-font-size-body-lg);
  font-weight: 800;
}

.filter-form {
  display: grid;
  gap: var(--ocop-space-2);
}

.search-row,
.select-row {
  display: flex;
  gap: var(--ocop-space-2);
}

.select-row .form-select {
  min-width: 0;
}

.section-title-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-2);
  margin-bottom: var(--ocop-space-2);
}

.section-title-row .btn {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  gap: 5px;
}

.radius-row {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-2);
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
}

.radius-row label {
  flex: 0 0 auto;
  font-weight: 650;
}

.radius-row .form-select {
  width: auto;
  min-height: 44px;
}

.empty-state {
  display: grid;
  justify-items: start;
  gap: var(--ocop-space-2);
}

.selected-note {
  margin: 0 0 var(--ocop-space-2);
}

.panel-message {
  margin: var(--ocop-space-2) 0 0;
  color: var(--ocop-warning);
  font-size: var(--ocop-font-size-small);
}

.btn-link-reset {
  min-height: 44px;
  justify-self: start;
  padding: 0 var(--ocop-space-1);
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
  margin: var(--ocop-space-2) 0 0;
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
  padding: var(--ocop-space-2) 10px;
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
  padding: var(--ocop-space-1) 9px;
  border-radius: var(--ocop-radius-pill);
  background: var(--type-color, var(--ocop-primary-700));
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.close-button {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border: 1px solid var(--ocop-border);
  border-radius: 50%;
  background: var(--ocop-card);
}

.selected-address {
  margin: 6px 0 10px;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
}

.selected-facts {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--ocop-space-2);
  margin: 0 0 var(--ocop-space-3);
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
  gap: var(--ocop-space-2);
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
  gap: var(--ocop-space-2);
  margin-top: var(--ocop-space-3);
  padding: 10px var(--ocop-space-3);
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
  /* Giữ các z-index của Leaflet (tới 1000) trong khung bản đồ: không đè lên header dính khi cuộn. */
  isolation: isolate;
  height: 62vh;
  min-height: 360px;
  order: -1;
}

/* Màn hẹp: thẻ điểm chọn lên ngay dưới bản đồ để thấy được mà không phải cuộn qua bộ lọc. */
@media (max-width: 991.98px) {
  .selected-card {
    order: -1;
  }
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
