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
  countFeaturesByType,
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

interface LocationGroup {
  type: LocationType
  label: string
  items: MapFeature[]
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
const leafletMapRef = ref<InstanceType<typeof LeafletMap> | null>(null)
let compactQuery: MediaQueryList | null = null

// Trạng thái giao diện cảm hứng từ Bản đồ văn hóa (cmap.vn):
// - Đóng/mở thanh bên phải để mở rộng bản đồ toàn màn hình
// - Bật/tắt bảng lớp loại hình & ranh giới tỉnh Lâm Đồng nổi trên bản đồ
// - Tab điều hướng thanh bên (Sự kiện/Điểm đến vs Chi tiết) & đóng/mở từng nhóm accordion
const isSidebarCollapsed = ref(false)
const isLayerMenuOpen = ref(false)
const showBoundary = ref(true)
const activeSidebarTab = ref<'explore' | 'detail'>('explore')
const collapsedGroups = reactive<Record<string, boolean>>({})

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

// Số liệu thống kê nhanh trên thanh KPI banner (kiểu cmap.vn) lấy từ dữ liệu thật đang tải.
const activeDistrictCount = computed(() => {
  const unique = new Set(
    displayFeatures.value.map((feature) => feature.properties.district?.trim()).filter(Boolean),
  )
  return unique.size
})
const totalDistrictCount = computed(() => Math.max(districts.value.length, activeDistrictCount.value))
const activeTypeCount = computed(() => {
  const unique = new Set(displayFeatures.value.map((feature) => feature.properties.type))
  return unique.size
})
const legendEntries = computed(() => countFeaturesByType(mappable.value))

// Gom nhóm danh sách điểm đến theo loại hình dạng accordion (giữ nguyên thứ tự xuất hiện của điểm).
const groupedLocations = computed<LocationGroup[]>(() => {
  const groups = new Map<LocationType, LocationGroup>()
  for (const feature of features.value) {
    const type = feature.properties.type
    const existing = groups.get(type)
    if (existing) {
      existing.items.push(feature)
    } else {
      groups.set(type, {
        type,
        label: feature.properties.type_label,
        items: [feature],
      })
    }
  }
  return [...groups.values()]
})

function isGroupCollapsed(type: LocationType): boolean {
  return Boolean(collapsedGroups[type])
}

function toggleGroup(type: LocationType): void {
  collapsedGroups[type] = !collapsedGroups[type]
}

async function toggleSidebar(): Promise<void> {
  isSidebarCollapsed.value = !isSidebarCollapsed.value
  await nextTick()
  leafletMapRef.value?.invalidateSize()
}

function toggleLayerMenu(): void {
  isLayerMenuOpen.value = !isLayerMenuOpen.value
}

function zoomInMap(): void {
  leafletMapRef.value?.zoomIn()
}

function zoomOutMap(): void {
  leafletMapRef.value?.zoomOut()
}

function resetMapView(): void {
  leafletMapRef.value?.resetView()
}

function switchSidebarTab(tab: 'explore' | 'detail'): void {
  activeSidebarTab.value = tab
  if (tab === 'detail' && selectedCard.value && typeof selectedCard.value.scrollIntoView === 'function') {
    selectedCard.value.scrollIntoView({ block: 'nearest', behavior: scrollBehavior() })
  }
}

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
  activeSidebarTab.value = 'explore'
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
    activeSidebarTab.value = 'detail'
    void revealSelectedCard()
    return
  }
  selectedSlug.value = slug
  activeSidebarTab.value = 'detail'
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
  if (event.key !== 'Escape' || event.defaultPrevented) return
  const target = event.target as HTMLElement | null
  if (target?.closest('input, select, textarea')) return
  if (isLayerMenuOpen.value) {
    isLayerMenuOpen.value = false
    return
  }
  if (!selectedSlug.value) return
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
      activeSidebarTab.value = 'detail'
      clearRoute()
    } else if (!slug && selectedSlug.value) {
      selectedSlug.value = null
      activeSidebarTab.value = 'explore'
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
  <main class="map-page" :class="{ 'is-sidebar-collapsed': isSidebarCollapsed }">
    <!-- Thanh tiêu đề & 3 thẻ KPI thống kê nhanh phía trên bản đồ (cảm hứng từ cmap.vn/ban-do-van-hoa) -->
    <header class="cmap-banner" aria-label="Tổng quan bản đồ số Lâm Đồng">
      <div class="cmap-brand">
        <span class="cmap-brand-badge" aria-hidden="true">
          <AppIcon name="map" :size="20" />
        </span>
        <div class="panel-header">
          <span class="eyebrow">Bản đồ số Lâm Đồng</span>
          <h1>Khám phá du lịch nông nghiệp</h1>
          <p class="visually-hidden">{{ mappableCount }} điểm đến đang hiển thị trên bản đồ.</p>
          <p class="panel-notice" role="status" data-test="unmappable-notice">
            <template v-if="unmappableCount">
              {{ unmappableCount }} điểm chưa có tọa độ hợp lệ nên chưa hiển thị trên bản đồ (vẫn có trong danh sách).
            </template>
          </p>
        </div>
      </div>

      <div class="cmap-kpi-list" aria-label="Số liệu bản đồ">
        <div class="cmap-kpi-pill">
          <strong class="cmap-kpi-value">{{ mappableCount }}</strong>
          <span class="cmap-kpi-label">Điểm đến đang hiển thị trên bản đồ</span>
        </div>
        <div class="cmap-kpi-pill">
          <strong class="cmap-kpi-value">{{ activeDistrictCount }}/{{ totalDistrictCount || activeDistrictCount }}</strong>
          <span class="cmap-kpi-label">Địa bàn có điểm du lịch nông nghiệp</span>
        </div>
        <div class="cmap-kpi-pill">
          <strong class="cmap-kpi-value">{{ activeTypeCount }}</strong>
          <span class="cmap-kpi-label">Nhóm loại hình trải nghiệm</span>
        </div>
      </div>

      <button
        type="button"
        class="cmap-sidebar-toggle"
        :aria-expanded="!isSidebarCollapsed"
        :aria-label="isSidebarCollapsed ? 'Mở bảng danh sách điểm đến' : 'Thu gọn danh sách để xem bản đồ rộng hơn'"
        :title="isSidebarCollapsed ? 'Mở danh sách điểm đến' : 'Thu gọn thanh bên'"
        @click="toggleSidebar"
      >
        <AppIcon :name="isSidebarCollapsed ? 'chevronLeft' : 'chevronRight'" :size="18" />
      </button>
    </header>

    <div class="cmap-workspace">
      <!-- Khu vực bản đồ tương tác bên trái (~2/3 màn hình) kèm các nút nổi kiểu cmap.vn -->
      <section ref="mapCanvas" class="map-canvas" aria-label="Bản đồ">
        <LeafletMap
          ref="leafletMapRef"
          :features="displayFeatures"
          :selected-slug="selectedSlug"
          :user-position="userPosition"
          :route="routeLine"
          :show-boundary="showBoundary"
          @select="selectLocation"
        />

        <!-- Nút nổi góc trên trái: hiển thị phạm vi địa bàn hiện tại -->
        <div class="cmap-float-top-left">
          <div class="cmap-scope-pill">
            <AppIcon name="map-pin" :size="15" />
            <span>
              {{ applied.district ? applied.district : 'Toàn tỉnh Lâm Đồng' }}
              <strong>({{ mappableCount }} điểm đến)</strong>
            </span>
            <button
              v-if="hasFilters"
              type="button"
              class="cmap-scope-clear"
              aria-label="Đặt lại bộ lọc địa bàn và loại hình"
              title="Xóa bộ lọc"
              @click="clearFilters"
            >
              <AppIcon name="close" :size="12" />
            </button>
          </div>
        </div>

        <!-- Nút nổi góc trên phải: bật/tắt lớp loại hình & ranh giới tỉnh (giống nút "Hoạt động" trên cmap.vn) -->
        <div class="cmap-float-top-right">
          <button
            type="button"
            class="cmap-layer-btn"
            :aria-expanded="isLayerMenuOpen"
            aria-label="Tùy chọn lớp hiển thị và loại hình"
            @click="toggleLayerMenu"
          >
            <span>Loại hình</span>
            <span v-if="applied.type" class="cmap-layer-dot" aria-hidden="true" />
            <AppIcon name="dashboard" :size="16" />
          </button>

          <div v-if="isLayerMenuOpen" class="cmap-layer-popover" role="dialog" aria-label="Bộ lọc lớp bản đồ">
            <div class="cmap-layer-head">
              <strong>Lớp hiển thị bản đồ</strong>
              <button
                type="button"
                class="cmap-popover-close"
                aria-label="Đóng bảng lớp bản đồ"
                @click="isLayerMenuOpen = false"
              >
                <AppIcon name="close" :size="12" />
              </button>
            </div>

            <label class="cmap-switch-row">
              <span>Viền ranh giới tỉnh Lâm Đồng</span>
              <input v-model="showBoundary" type="checkbox" class="form-check-input" />
            </label>

            <div v-if="legendEntries.length" class="cmap-layer-types">
              <span class="cmap-layer-subtitle">Lọc nhanh theo loại hình</span>
              <button
                v-for="entry in legendEntries"
                :key="entry.type"
                type="button"
                class="cmap-layer-type-btn"
                :class="{ 'is-active': applied.type === entry.type }"
                @click="selectLegendType(applied.type === entry.type ? '' : entry.type)"
              >
                <span
                  class="cmap-layer-swatch"
                  :style="{ '--swatch-color': locationTypeStyle(entry.type).color }"
                  aria-hidden="true"
                />
                <span class="cmap-layer-name">{{ entry.label }}</span>
                <span class="cmap-layer-count">{{ entry.count }}</span>
              </button>
            </div>
          </div>
        </div>

        <!-- Cụm 4 nút tiện ích góc dưới trái (Định vị, Đặt lại bản đồ, Phóng to, Thu nhỏ) -->
        <div class="cmap-float-bottom-left" role="group" aria-label="Điều khiển nhanh bản đồ">
          <button
            type="button"
            class="cmap-control-btn"
            :class="{ 'is-active': Boolean(userPosition) }"
            :disabled="isLocating"
            aria-label="Vị trí hiện tại của tôi"
            title="Vị trí của tôi"
            @click="locateUser('nearby')"
          >
            <AppIcon name="navigation" :size="16" />
          </button>
          <button
            type="button"
            class="cmap-control-btn"
            aria-label="Đặt lại góc nhìn toàn tỉnh Lâm Đồng"
            title="Toàn cảnh Lâm Đồng"
            @click="resetMapView"
          >
            <AppIcon name="refresh" :size="16" />
          </button>
          <div class="cmap-zoom-group">
            <button
              type="button"
              class="cmap-control-btn"
              aria-label="Phóng to bản đồ"
              title="Phóng to"
              @click="zoomInMap"
            >
              <AppIcon name="plus" :size="15" />
            </button>
            <button
              type="button"
              class="cmap-control-btn"
              aria-label="Thu nhỏ bản đồ"
              title="Thu nhỏ"
              @click="zoomOutMap"
            >
              <span class="cmap-minus-glyph" aria-hidden="true">−</span>
            </button>
          </div>
        </div>

        <!-- Thẻ tóm tắt nổi ngay trên khung bản đồ khi đang chọn một điểm (kiểu Popup Card của cmap.vn) -->
        <div
          v-if="selectedFeature"
          class="cmap-map-popup"
          role="region"
          aria-label="Tóm tắt điểm đang chọn trên bản đồ"
        >
          <img
            class="cmap-popup-thumb"
            :src="selectedFeature.properties.primary_image_url || locationTypeStyle(selectedFeature.properties.type).illustration"
            :alt="selectedFeature.properties.name"
          />
          <div class="cmap-popup-body">
            <div class="cmap-popup-meta">
              <span
                class="cmap-popup-badge"
                :style="{ '--badge-color': locationTypeStyle(selectedFeature.properties.type).color }"
              >
                {{ selectedFeature.properties.type_label }}
              </span>
              <span class="cmap-popup-district">{{ selectedFeature.properties.district }}</span>
            </div>
            <strong class="cmap-popup-title">{{ selectedFeature.properties.name }}</strong>
            <div class="cmap-popup-links">
              <RouterLink
                class="cmap-popup-link"
                :to="{ name: 'location-detail', params: { slug: selectedFeature.properties.slug } }"
              >
                Tìm hiểu thêm
              </RouterLink>
              <button
                v-if="selectedCoordinates"
                type="button"
                class="cmap-popup-route"
                :disabled="isRouting || isLocating"
                @click="showRoute"
              >
                <AppIcon name="navigation" :size="13" />
                Chỉ đường
              </button>
            </div>
          </div>
          <button
            type="button"
            class="cmap-popup-close"
            aria-label="Đóng thẻ tóm tắt trên bản đồ"
            @click="closeSelection"
          >
            <AppIcon name="close" :size="12" />
          </button>
        </div>
      </section>

      <!-- Thanh bên phải (~1/3 màn hình): Thanh tab kiểu cmap.vn + Bộ lọc + Điểm gần bạn + Danh sách accordion + Chi tiết -->
      <aside class="map-panel" aria-label="Công cụ bản đồ">
        <!-- Thanh 3 tab đầu sidebar giống cmap.vn: Trang chủ | Điểm đến | Chi tiết -->
        <nav class="cmap-tabs" aria-label="Chế độ xem thanh bên">
          <RouterLink class="cmap-tab-home" :to="{ name: 'home' }" aria-label="Về trang chủ" title="Trang chủ">
            <AppIcon name="home" :size="17" />
          </RouterLink>
          <button
            type="button"
            class="cmap-tab-btn"
            :class="{ 'is-active': activeSidebarTab === 'explore' }"
            @click="switchSidebarTab('explore')"
          >
            <span>Điểm đến</span>
            <span class="cmap-tab-count">{{ features.length }}</span>
          </button>
          <button
            type="button"
            class="cmap-tab-btn"
            :class="{ 'is-active': activeSidebarTab === 'detail' }"
            :disabled="!selectedFeature"
            @click="switchSidebarTab('detail')"
          >
            <span>Chi tiết</span>
            <span v-if="selectedFeature" class="cmap-tab-dot" aria-hidden="true" />
          </button>
        </nav>

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
              <option value="">Mọi địa bàn ({{ mappableCount }})</option>
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

        <section class="panel-section nearby-section" aria-labelledby="nearby-title">
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
          :class="{ 'is-highlighted': activeSidebarTab === 'detail' }"
          aria-labelledby="selected-title"
          aria-live="polite"
        >
          <div class="selected-cover">
            <img
              class="selected-cover-img"
              :src="selectedFeature.properties.primary_image_url || locationTypeStyle(selectedFeature.properties.type).illustration"
              :alt="selectedFeature.properties.name"
            />
            <div class="section-title-row selected-cover-bar">
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

          <p v-if="routeIntent && !routeResult" class="panel-hint" data-test="route-intent" role="status">
            Điểm đến đã chọn. Bấm “Lấy vị trí &amp; chỉ đường” để xác nhận dùng vị trí hiện tại và tìm tuyến đường.
          </p>
          <div class="selected-actions">
            <button
              v-if="selectedCoordinates"
              class="btn btn-success"
              type="button"
              :disabled="isRouting || isLocating"
              @click="showRoute"
            >
              <AppIcon name="navigation" :size="15" />
              {{ isRouting ? 'Đang tìm đường...' : routeIntent ? 'Lấy vị trí & chỉ đường' : 'Chỉ đường' }}
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
          <a
            v-if="selectedCoordinates"
            class="external-directions"
            :href="directionsUrl"
            target="_blank"
            rel="noopener noreferrer"
          >
            Mở chỉ đường bằng Google Maps
          </a>
        </section>

        <section class="panel-section all-locations-section" aria-labelledby="all-locations-title">
          <div class="section-title-row">
            <h2 id="all-locations-title" ref="allLocationsTitle" tabindex="-1">Tất cả điểm đến</h2>
            <span class="cmap-total-pill">{{ features.length }} điểm</span>
          </div>
          <p v-if="isLoading" class="panel-hint">Đang tải dữ liệu bản đồ...</p>
          <div v-else-if="!features.length && !errorMessage" class="empty-state">
            <p class="panel-hint">
              {{ hasFilters ? 'Không có điểm du lịch phù hợp với bộ lọc.' : 'Chưa có điểm du lịch nào để hiển thị.' }}
            </p>
            <button v-if="hasFilters" class="btn btn-outline-success btn-sm" type="button" @click="clearFilters">
              Xóa bộ lọc
            </button>
          </div>
          <div v-else class="cmap-accordion-list">
            <div v-for="group in groupedLocations" :key="group.type" class="cmap-accordion-group">
              <button
                type="button"
                class="cmap-accordion-header"
                :aria-expanded="!isGroupCollapsed(group.type)"
                @click="toggleGroup(group.type)"
              >
                <span
                  class="cmap-accordion-icon"
                  :style="{ '--group-color': locationTypeStyle(group.type).color }"
                  aria-hidden="true"
                >
                  <AppIcon :name="locationTypeStyle(group.type).icon" :size="16" />
                </span>
                <span class="cmap-accordion-title">{{ group.label }}</span>
                <span class="cmap-accordion-count">{{ group.items.length }}</span>
                <AppIcon
                  :name="isGroupCollapsed(group.type) ? 'chevronDown' : 'chevronUp'"
                  :size="14"
                  class="cmap-accordion-chevron"
                />
              </button>

              <ul v-show="!isGroupCollapsed(group.type)" class="location-list">
                <li v-for="feature in group.items" :key="feature.properties.slug">
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
                    <span class="location-item-body">
                      <strong>{{ feature.properties.name }}</strong>
                      <small>{{ feature.properties.type_label }} · {{ feature.properties.district }}</small>
                    </span>
                    <span class="location-item-price">
                      {{ formatTicketPrice(feature.properties.ticket_price) }}
                    </span>
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </section>

        <p class="panel-note">
          Dữ liệu điểm đến mang tính tham khảo. Tuyến đường do dịch vụ chỉ đường gợi ý (dữ liệu OpenStreetMap).
        </p>
      </aside>
    </div>
  </main>
</template>

<style scoped>
.map-page {
  display: flex;
  min-height: calc(100vh - 4.5rem);
  flex-direction: column;
  background: var(--ocop-surface);
}

/* ════════════════════════════════════════════════════════════════
   Thanh tiêu đề & 3 thẻ KPI thống kê phía trên (kiểu cmap.vn)
   ════════════════════════════════════════════════════════════════ */
.cmap-banner {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-3) var(--ocop-space-4);
  border-bottom: 1px solid var(--ocop-border);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-sm);
}

.cmap-brand {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-3);
}

.cmap-brand-badge {
  display: grid;
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-primary-800);
  color: var(--ocop-daquy-300);
  box-shadow: var(--ocop-shadow-sm);
}

.panel-header h1 {
  margin: 2px 0 0;
  color: var(--ocop-primary-950);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 800;
  line-height: 1.25;
}

.panel-notice {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-warning);
  font-size: var(--ocop-font-size-caption);
}

.panel-notice:empty {
  display: none;
}

.eyebrow {
  display: block;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.cmap-kpi-list {
  display: flex;
  flex: 1 1 auto;
  flex-wrap: wrap;
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-2);
}

.cmap-kpi-pill {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 6px var(--ocop-space-4);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-surface-subtle);
}

.cmap-kpi-value {
  color: var(--ocop-primary-800);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 800;
  line-height: 1;
}

.cmap-kpi-label {
  max-width: 11rem;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-caption);
  font-weight: 600;
  line-height: 1.2;
}

.cmap-sidebar-toggle {
  display: none;
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  place-items: center;
  border: 1px solid var(--ocop-primary-800);
  border-radius: 50%;
  background: var(--ocop-primary-950);
  color: var(--ocop-white);
  transition: transform var(--ocop-duration-fast) ease, background var(--ocop-duration-fast) ease;
}

.cmap-sidebar-toggle:hover {
  background: var(--ocop-primary-800);
}

/* ════════════════════════════════════════════════════════════════
   Bố cục chia đôi: Bản đồ bên trái (~2/3), Thanh bên phải (~1/3)
   ════════════════════════════════════════════════════════════════ */
.cmap-workspace {
  display: grid;
  flex: 1 1 auto;
  min-height: 0;
}

.map-canvas {
  position: relative;
  isolation: isolate;
  height: 62vh;
  min-height: 360px;
}

/* Các điều khiển nổi trên bản đồ kiểu cmap.vn */
.cmap-float-top-left {
  position: absolute;
  z-index: 450;
  top: 12px;
  left: 54px;
  max-width: calc(100% - 190px);
}

.cmap-scope-pill {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 6px 14px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-glass-bg-solid);
  box-shadow: var(--ocop-shadow-sm);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-small);
}

.cmap-scope-clear {
  display: grid;
  width: 24px;
  height: 24px;
  place-items: center;
  border: 0;
  border-radius: 50%;
  background: var(--ocop-mist-100);
  color: var(--ocop-navy);
}

.cmap-float-top-right {
  position: absolute;
  z-index: 460;
  top: 12px;
  right: 12px;
}

.cmap-layer-btn {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 8px 16px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-sm);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
}

.cmap-layer-btn:hover {
  border-color: var(--ocop-primary-700);
}

.cmap-layer-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ocop-daquy-500);
}

.cmap-layer-popover {
  position: absolute;
  top: calc(100% + 8px);
  right: 0;
  width: 270px;
  padding: var(--ocop-space-3);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-card);
}

.cmap-layer-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: var(--ocop-space-2);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-small);
}

.cmap-popover-close {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border: 1px solid var(--ocop-border);
  border-radius: 50%;
  background: var(--ocop-surface-subtle);
}

.cmap-switch-row {
  display: flex;
  min-height: 40px;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-2);
  padding: 6px 8px;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-surface-subtle);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-small);
  font-weight: 600;
  cursor: pointer;
}

.cmap-layer-types {
  display: grid;
  gap: 4px;
  margin-top: var(--ocop-space-2);
}

.cmap-layer-subtitle {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.cmap-layer-type-btn {
  display: flex;
  min-height: 38px;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 6px 10px;
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-sm);
  background: transparent;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-small);
  text-align: left;
}

.cmap-layer-type-btn:hover,
.cmap-layer-type-btn.is-active {
  border-color: var(--ocop-primary-700);
  background: var(--ocop-mint-soft);
}

.cmap-layer-swatch {
  width: 12px;
  height: 12px;
  flex: 0 0 auto;
  border-radius: 50%;
  background: var(--swatch-color, var(--ocop-primary-700));
}

.cmap-layer-name {
  flex: 1 1 auto;
  font-weight: 600;
}

.cmap-layer-count {
  color: var(--ocop-primary-700);
  font-weight: 800;
}

.cmap-float-bottom-left {
  position: absolute;
  z-index: 450;
  bottom: 20px;
  left: 12px;
  display: flex;
  flex-direction: column;
  gap: var(--ocop-space-2);
}

.cmap-zoom-group {
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-sm);
}

.cmap-zoom-group .cmap-control-btn {
  border: 0;
  border-radius: 0;
  box-shadow: none;
}

.cmap-zoom-group .cmap-control-btn + .cmap-control-btn {
  border-top: 1px solid var(--ocop-border);
}

.cmap-control-btn {
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-sm);
  color: var(--ocop-navy);
}

.cmap-control-btn:hover,
.cmap-control-btn.is-active {
  border-color: var(--ocop-primary-700);
  background: var(--ocop-mint-soft);
  color: var(--ocop-primary-800);
}

.cmap-minus-glyph {
  font-size: 1.25rem;
  font-weight: 700;
  line-height: 1;
}

/* Thẻ tóm tắt nổi trên bản đồ khi chọn một điểm */
.cmap-map-popup {
  position: absolute;
  z-index: 455;
  right: 16px;
  bottom: 20px;
  left: 68px;
  display: flex;
  max-width: 400px;
  align-items: center;
  gap: var(--ocop-space-3);
  margin-left: auto;
  padding: 10px 12px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-card);
}

.cmap-popup-thumb {
  width: 64px;
  height: 64px;
  flex: 0 0 auto;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-surface-muted);
  object-fit: cover;
}

.cmap-popup-body {
  min-width: 0;
  flex: 1 1 auto;
}

.cmap-popup-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  margin-bottom: 2px;
}

.cmap-popup-badge {
  padding: 2px 8px;
  border-radius: var(--ocop-radius-pill);
  background: var(--badge-color, var(--ocop-primary-700));
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.cmap-popup-district {
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
  font-weight: 600;
}

.cmap-popup-title {
  display: block;
  overflow: hidden;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-small);
  font-weight: 800;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.cmap-popup-links {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-3);
  margin-top: 6px;
}

.cmap-popup-link {
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  text-decoration: none;
}

.cmap-popup-route {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 3px 10px;
  border: 0;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-daquy-300);
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
}

.cmap-popup-close {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  align-self: flex-start;
  place-items: center;
  border: 1px solid var(--ocop-border);
  border-radius: 50%;
  background: var(--ocop-surface-subtle);
}

/* ════════════════════════════════════════════════════════════════
   Thanh bên phải: Tabs + Bộ lọc + Điểm gần bạn + Accordion + Chi tiết
   ════════════════════════════════════════════════════════════════ */
.map-panel {
  display: flex;
  flex-direction: column;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-3);
  background: var(--ocop-surface);
}

.cmap-tabs {
  display: grid;
  grid-template-columns: 48px 1fr 1fr;
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
}

.cmap-tab-home,
.cmap-tab-btn {
  display: inline-flex;
  min-height: 44px;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 0;
  background: transparent;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
  text-decoration: none;
}

.cmap-tab-home {
  border-right: 1px solid var(--ocop-border);
  color: var(--ocop-primary-700);
}

.cmap-tab-btn + .cmap-tab-btn {
  border-left: 1px solid var(--ocop-border);
}

.cmap-tab-btn.is-active {
  background: var(--ocop-surface-muted);
  color: var(--ocop-primary-950);
  box-shadow: inset 0 -3px 0 var(--ocop-primary-700);
}

.cmap-tab-btn:disabled {
  color: var(--ocop-slate);
  opacity: 0.6;
}

.cmap-tab-count {
  padding: 1px 7px;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-primary-800);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
}

.cmap-tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--ocop-daquy-500);
}

.panel-hint,
.panel-note {
  margin: 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
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

.cmap-total-pill {
  padding: 2px 10px;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mist-100);
  color: var(--ocop-primary-800);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
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

/* Accordion nhóm loại hình kiểu cmap.vn */
.cmap-accordion-list {
  display: grid;
  gap: var(--ocop-space-2);
}

.cmap-accordion-group {
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-surface-subtle);
}

.cmap-accordion-header {
  display: flex;
  width: 100%;
  min-height: 48px;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 8px 12px;
  border: 0;
  background: var(--ocop-card);
  color: var(--ocop-navy);
  text-align: left;
}

.cmap-accordion-header:hover {
  background: var(--ocop-surface-muted);
}

.cmap-accordion-icon {
  display: grid;
  width: 32px;
  height: 32px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--ocop-radius-sm);
  background: color-mix(in srgb, var(--group-color, var(--ocop-primary-700)) 15%, var(--ocop-white));
  color: var(--group-color, var(--ocop-primary-700));
}

.cmap-accordion-title {
  flex: 1 1 auto;
  font-size: var(--ocop-font-size-small);
  font-weight: 800;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}

.cmap-accordion-count {
  padding: 2px 8px;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mist-100);
  color: var(--ocop-primary-800);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
}

.cmap-accordion-chevron {
  color: var(--ocop-slate);
}

.nearby-list,
.location-list {
  display: grid;
  gap: 6px;
  margin: var(--ocop-space-2) 0 0;
  padding: 0;
  list-style: none;
}

.cmap-accordion-group .location-list {
  margin: 0;
  padding: var(--ocop-space-2);
  border-top: 1px solid var(--ocop-border);
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
  background: var(--ocop-card);
  color: var(--ocop-navy);
  text-align: left;
}

.location-list button {
  justify-content: flex-start;
}

.location-item-body {
  min-width: 0;
  flex: 1 1 auto;
}

.location-item-price {
  flex: 0 0 auto;
  padding: 2px 8px;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-surface-muted);
  color: var(--ocop-primary-800);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
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

/* Thẻ chi tiết điểm đang chọn (đặt lên đầu danh sách khi đang ở tab Chi tiết) */
.selected-card {
  border-color: var(--ocop-primary-700);
  box-shadow: var(--ocop-shadow-card);
}

.selected-card.is-highlighted {
  order: -1;
}

.selected-cover {
  position: relative;
  overflow: hidden;
  height: 132px;
  margin: -14px -14px var(--ocop-space-3);
  border-bottom: 1px solid var(--ocop-border);
  background: var(--ocop-surface-muted);
}

.selected-cover-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.selected-cover-bar {
  position: absolute;
  inset: 10px 10px auto;
  margin: 0;
}

.selected-card h2 {
  font-size: 1.15rem;
}

.type-badge {
  padding: var(--ocop-space-1) 10px;
  border-radius: var(--ocop-radius-pill);
  background: var(--type-color, var(--ocop-primary-700));
  box-shadow: var(--ocop-shadow-sm);
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
  box-shadow: var(--ocop-shadow-sm);
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
  padding: 10px;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-surface-subtle);
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

/* Màn hẹp: thẻ điểm chọn lên ngay dưới bản đồ để thấy được mà không phải cuộn qua bộ lọc. */
@media (max-width: 991.98px) {
  .selected-card {
    order: -1;
  }

  .cmap-kpi-list {
    justify-content: flex-start;
  }

  .cmap-map-popup {
    display: none;
  }
}

@media (min-width: 992px) {
  .map-page {
    height: calc(100vh - 4.5rem);
    min-height: 600px;
  }

  .cmap-sidebar-toggle {
    display: grid;
  }

  .cmap-workspace {
    grid-template-columns: minmax(0, 1fr) 420px;
    overflow: hidden;
  }

  .map-page.is-sidebar-collapsed .cmap-workspace {
    grid-template-columns: minmax(0, 1fr);
  }

  .map-page.is-sidebar-collapsed .map-panel {
    display: none;
  }

  .map-canvas {
    height: 100%;
  }

  .map-panel {
    overflow-y: auto;
    border-left: 1px solid var(--ocop-border);
  }
}
</style>
