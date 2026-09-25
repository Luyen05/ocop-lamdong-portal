<script setup lang="ts">
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import 'leaflet.markercluster/dist/MarkerCluster.css'
import 'leaflet.markercluster/dist/MarkerCluster.Default.css'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

import type { Coordinate, MapFeature } from '@/types/location'
import { locationTypeStyle } from '@/utils/location'

const props = withDefaults(
  defineProps<{
    features: MapFeature[]
    selectedSlug?: string | null
    userPosition?: Coordinate | null
    /** Tọa độ tuyến đường theo thứ tự GeoJSON [kinh độ, vĩ độ]. */
    route?: Array<[number, number]> | null
    cluster?: boolean
    initialZoom?: number
    label?: string
  }>(),
  {
    selectedSlug: null,
    userPosition: null,
    route: null,
    cluster: true,
    initialZoom: 9,
    label: 'Bản đồ số điểm du lịch nông nghiệp Lâm Đồng',
  },
)

const emit = defineEmits<{ select: [slug: string] }>()

const LAM_DONG_CENTER: L.LatLngTuple = [11.9404, 108.4583]
const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'

interface TileProvider {
  url: string
  attribution: string
  subdomains: string
}

// Nguồn ảnh nền theo thứ tự ưu tiên. Một số mạng chặn tile.openstreetmap.org nên
// mặc định dùng CARTO (dữ liệu OpenStreetMap) và tự chuyển nguồn khi không tải được.
const TILE_PROVIDERS: TileProvider[] = [
  ...(import.meta.env.VITE_MAP_TILE_URL
    ? [{ url: import.meta.env.VITE_MAP_TILE_URL, attribution: OSM_ATTRIBUTION, subdomains: 'abc' }]
    : []),
  {
    url: 'https://{s}.basemaps.cartocdn.com/rastertiles/voyager/{z}/{x}/{y}{r}.png',
    attribution: `${OSM_ATTRIBUTION} &copy; <a href="https://carto.com/attributions">CARTO</a>`,
    subdomains: 'abcd',
  },
  {
    url: 'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
    attribution: OSM_ATTRIBUTION,
    subdomains: 'abc',
  },
]
const TILE_ERRORS_BEFORE_FALLBACK = 3

const container = ref<HTMLDivElement | null>(null)
const loadError = ref('')

let map: L.Map | null = null
let markerLayer: L.LayerGroup | null = null
let clusterLayer: L.MarkerClusterGroup | null = null
let userLayer: L.LayerGroup | null = null
let routeLayer: L.Polyline | null = null
let tileLayer: L.TileLayer | null = null
let resizeObserver: ResizeObserver | null = null
let isUnmounted = false
const markers = new Map<string, L.Marker>()
const featuresBySlug = new Map<string, MapFeature>()

function markerIcon(feature: MapFeature, selected: boolean): L.DivIcon {
  const style = locationTypeStyle(feature.properties.type)
  // HTML chỉ ghép từ hằng số nội bộ; tên địa điểm được gắn qua textContent ở tooltip.
  return L.divIcon({
    className: 'ocop-marker-anchor',
    html: `<span class="ocop-marker${selected ? ' is-selected' : ''}" style="--marker-color:${style.color}"><i class="bi bi-${style.markerIcon}"></i></span>`,
    // Marker là hình vuông 34px xoay -45°, đỉnh nhọn nằm dưới tâm khoảng 24px.
    iconSize: [34, 34],
    iconAnchor: [17, 40],
    tooltipAnchor: [0, -38],
  })
}

function tooltipContent(feature: MapFeature): HTMLElement {
  const wrapper = document.createElement('span')
  const name = document.createElement('strong')
  name.textContent = feature.properties.name
  const meta = document.createElement('small')
  meta.textContent = `${feature.properties.type_label} · ${feature.properties.district}`
  wrapper.append(name, document.createElement('br'), meta)
  return wrapper
}

function useTileProvider(index: number): void {
  if (!map) return
  const provider = TILE_PROVIDERS[index]
  if (!provider) {
    loadError.value = 'Không tải được ảnh nền bản đồ. Các điểm du lịch vẫn hiển thị bình thường.'
    return
  }
  tileLayer?.remove()
  let hasLoadedTile = false
  let errorCount = 0
  tileLayer = L.tileLayer(provider.url, {
    attribution: provider.attribution,
    subdomains: provider.subdomains,
    maxZoom: 19,
  })
  tileLayer.on('tileload', () => {
    hasLoadedTile = true
  })
  tileLayer.on('tileerror', () => {
    errorCount += 1
    if (!hasLoadedTile && errorCount === TILE_ERRORS_BEFORE_FALLBACK) useTileProvider(index + 1)
  })
  tileLayer.addTo(map)
}

function renderMarkers(fitToFeatures: boolean): void {
  if (!map || !markerLayer) return
  markerLayer.clearLayers()
  markers.clear()
  featuresBySlug.clear()

  for (const feature of props.features) {
    const [longitude, latitude] = feature.geometry.coordinates
    const slug = feature.properties.slug
    const marker = L.marker([latitude, longitude], {
      icon: markerIcon(feature, slug === props.selectedSlug),
      title: feature.properties.name,
      alt: feature.properties.name,
      keyboard: true,
      riseOnHover: true,
    })
    marker.bindTooltip(tooltipContent(feature), { direction: 'top' })
    marker.on('click', () => emit('select', slug))
    marker.addTo(markerLayer)
    markers.set(slug, marker)
    featuresBySlug.set(slug, feature)
  }

  if (fitToFeatures && props.features.length && !props.selectedSlug) {
    const bounds = L.latLngBounds(
      props.features.map((feature) => [
        feature.geometry.coordinates[1],
        feature.geometry.coordinates[0],
      ] as L.LatLngTuple),
    )
    map.fitBounds(bounds, { padding: [32, 32], maxZoom: 13 })
  }
  focusSelected()
}

function focusSelected(previousSlug: string | null = null): void {
  if (!map) return
  const previousFeature = previousSlug ? featuresBySlug.get(previousSlug) : undefined
  if (previousSlug && previousFeature) {
    markers.get(previousSlug)?.setIcon(markerIcon(previousFeature, false))
  }
  const slug = props.selectedSlug
  if (!slug) return
  const marker = markers.get(slug)
  const feature = featuresBySlug.get(slug)
  if (!marker || !feature) return
  marker.setIcon(markerIcon(feature, true))

  const showTooltip = () => marker.openTooltip()
  if (clusterLayer) {
    clusterLayer.zoomToShowLayer(marker, showTooltip)
  } else {
    map.setView(marker.getLatLng(), Math.max(map.getZoom(), 13))
    showTooltip()
  }
}

function renderUserPosition(): void {
  if (!map || !userLayer) return
  userLayer.clearLayers()
  if (!props.userPosition) return
  const position: L.LatLngTuple = [props.userPosition.latitude, props.userPosition.longitude]
  // Màu viền và nền lấy từ token qua class .ocop-user-position (CSS ghi đè thuộc tính SVG).
  L.circleMarker(position, {
    radius: 9,
    weight: 3,
    fillOpacity: 1,
    className: 'ocop-user-position',
  })
    .bindTooltip('Vị trí của bạn', { direction: 'top' })
    .addTo(userLayer)
  if (!props.route?.length) map.setView(position, Math.max(map.getZoom(), 11))
}

function renderRoute(): void {
  if (!map) return
  routeLayer?.remove()
  routeLayer = null
  if (!props.route?.length) return
  const points = props.route.map(([longitude, latitude]) => [latitude, longitude] as L.LatLngTuple)
  routeLayer = L.polyline(points, { className: 'ocop-route-line', weight: 5, opacity: 0.85 }).addTo(map)
  map.fitBounds(routeLayer.getBounds(), { padding: [40, 40] })
}

async function initialize(): Promise<void> {
  if (!container.value) return
  try {
    map = L.map(container.value, { zoomControl: true, attributionControl: true })
    map.setView(LAM_DONG_CENTER, props.initialZoom)
    useTileProvider(0)

    if (props.cluster) {
      // Plugin gom cụm đọc biến toàn cục L theo chuẩn UMD.
      ;(window as unknown as { L: typeof L }).L = L
      await import('leaflet.markercluster')
      if (isUnmounted || !map) return
      clusterLayer = L.markerClusterGroup({ showCoverageOnHover: false, maxClusterRadius: 48 })
      markerLayer = clusterLayer
    } else {
      markerLayer = L.layerGroup()
    }
    markerLayer.addTo(map)
    userLayer = L.layerGroup().addTo(map)

    renderMarkers(true)
    renderUserPosition()
    renderRoute()

    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => map?.invalidateSize())
      resizeObserver.observe(container.value)
    }
  } catch {
    loadError.value = 'Không thể khởi tạo bản đồ. Vui lòng tải lại trang.'
  }
}

watch(() => props.features, () => renderMarkers(true))
watch(() => props.selectedSlug, (_slug, previousSlug) => focusSelected(previousSlug ?? null))
watch(() => props.userPosition, renderUserPosition)
watch(() => props.route, renderRoute)

onMounted(() => {
  void initialize()
})

onBeforeUnmount(() => {
  isUnmounted = true
  resizeObserver?.disconnect()
  map?.remove()
  map = null
  markerLayer = null
  clusterLayer = null
  userLayer = null
  routeLayer = null
  tileLayer = null
  markers.clear()
  featuresBySlug.clear()
})
</script>

<template>
  <div class="leaflet-map-shell">
    <div ref="container" class="leaflet-map" role="region" :aria-label="label" />
    <p v-if="loadError" class="map-load-error" role="alert">{{ loadError }}</p>
  </div>
</template>

<style scoped>
.leaflet-map-shell {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: inherit;
}

.leaflet-map {
  width: 100%;
  height: 100%;
  min-height: inherit;
  border-radius: inherit;
  background: var(--ocop-surface-muted);
}

.map-load-error {
  position: absolute;
  z-index: 500;
  inset: auto 12px 12px;
  margin: 0;
  padding: 10px var(--ocop-space-3);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger);
  font-size: var(--ocop-font-size-small);
}
</style>

<style>
.ocop-user-position {
  stroke: var(--ocop-white);
  fill: var(--ocop-location-user);
}

.ocop-route-line {
  stroke: var(--ocop-location-route);
}

.leaflet-tooltip small {
  font-size: var(--ocop-font-size-caption);
}

.ocop-marker-anchor {
  border: 0;
  background: transparent;
}

.ocop-marker {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border: 2px solid var(--ocop-white);
  border-radius: 50% 50% 50% var(--ocop-radius-xs);
  background: var(--marker-color, var(--ocop-primary-700));
  box-shadow: 0 6px 14px color-mix(in srgb, var(--ocop-neutral-900) 28%, transparent);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-body);
  transform: rotate(-45deg);
  transition: transform 160ms ease;
}

.ocop-marker i {
  transform: rotate(45deg);
}

.ocop-marker.is-selected {
  outline: 3px solid color-mix(in srgb, var(--ocop-star) 70%, transparent);
  transform: rotate(-45deg) scale(1.18);
}

.leaflet-marker-icon:focus-visible .ocop-marker {
  outline: 3px solid color-mix(in srgb, var(--ocop-primary-500) 60%, transparent);
}
</style>
