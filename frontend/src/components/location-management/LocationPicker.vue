<script setup lang="ts">
import L from 'leaflet'
import 'leaflet/dist/leaflet.css'
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'

/**
 * Bản đồ đặt ghim cho điểm du lịch: bấm vào bản đồ hoặc kéo ghim để chọn vị trí.
 * Vòng tròn quanh ghim là phạm vi sai số khi vị trí lấy bằng GPS.
 */
const props = withDefaults(
  defineProps<{
    latitude: number | null
    longitude: number | null
    /** Sai số GPS (mét); không có thì không vẽ vòng. */
    accuracy?: number | null
    readonly?: boolean
    label?: string
  }>(),
  {
    accuracy: null,
    readonly: false,
    label: 'Bản đồ chọn vị trí điểm du lịch',
  },
)

const emit = defineEmits<{ pick: [position: { latitude: number; longitude: number }] }>()

const LAM_DONG_CENTER: L.LatLngTuple = [11.9404, 108.4583]
const OSM_ATTRIBUTION = '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
// Cùng thứ tự nguồn ảnh nền với bản đồ công khai (components/map/LeafletMap.vue): không cần API key,
// lỗi liên tiếp thì chuyển sang nguồn kế tiếp.
const TILE_URLS = [
  ...(import.meta.env.VITE_MAP_TILE_URL ? [import.meta.env.VITE_MAP_TILE_URL as string] : []),
  'https://tile.openstreetmap.org/{z}/{x}/{y}.png',
  'https://{s}.tile.openstreetmap.fr/hot/{z}/{x}/{y}.png',
]

const container = ref<HTMLDivElement | null>(null)
const loadError = ref('')

let map: L.Map | null = null
let marker: L.Marker | null = null
let accuracyCircle: L.Circle | null = null
let tileLayer: L.TileLayer | null = null
let resizeObserver: ResizeObserver | null = null

const pinIcon = L.divIcon({
  className: 'ocop-pick-pin-anchor',
  html: '<span class="ocop-pick-pin"><span></span></span>',
  iconSize: [36, 44],
  iconAnchor: [18, 42],
})

function useTiles(index: number): void {
  if (!map) return
  const url = TILE_URLS[index]
  if (!url) {
    loadError.value = 'Không tải được ảnh nền bản đồ. Bạn vẫn có thể dán tọa độ hoặc dùng GPS.'
    return
  }
  tileLayer?.remove()
  let loaded = false
  let errors = 0
  tileLayer = L.tileLayer(url, { attribution: OSM_ATTRIBUTION, subdomains: 'abc', maxZoom: 19 })
  tileLayer.on('tileload', () => {
    loaded = true
  })
  tileLayer.on('tileerror', () => {
    errors += 1
    if (!loaded && errors === 3) useTiles(index + 1)
  })
  tileLayer.addTo(map)
}

function emitPick(latLng: L.LatLng): void {
  emit('pick', {
    latitude: Number(latLng.lat.toFixed(7)),
    longitude: Number(latLng.lng.toFixed(7)),
  })
}

function render(recenter: boolean): void {
  if (!map) return
  const hasPoint = props.latitude !== null && props.longitude !== null
  if (!hasPoint) {
    marker?.remove()
    marker = null
    accuracyCircle?.remove()
    accuracyCircle = null
    return
  }
  const position: L.LatLngTuple = [props.latitude as number, props.longitude as number]
  if (!marker) {
    marker = L.marker(position, {
      icon: pinIcon,
      draggable: !props.readonly,
      keyboard: true,
      title: 'Ghim vị trí điểm du lịch',
      alt: 'Ghim vị trí điểm du lịch',
    }).addTo(map)
    marker.on('dragend', () => marker && emitPick(marker.getLatLng()))
  } else {
    marker.setLatLng(position)
  }

  accuracyCircle?.remove()
  accuracyCircle = null
  if (props.accuracy && props.accuracy > 0) {
    accuracyCircle = L.circle(position, {
      radius: props.accuracy,
      className: 'ocop-pick-accuracy',
      weight: 1,
      interactive: false,
    }).addTo(map)
  }
  if (recenter) map.setView(position, Math.max(map.getZoom(), 15))
}

function zoom(delta: number): void {
  map?.setZoom(map.getZoom() + delta)
}

onMounted(() => {
  if (!container.value) return
  try {
    map = L.map(container.value, { zoomControl: false, attributionControl: true })
    const hasPoint = props.latitude !== null && props.longitude !== null
    map.setView(hasPoint ? [props.latitude as number, props.longitude as number] : LAM_DONG_CENTER, hasPoint ? 15 : 9)
    useTiles(0)
    if (!props.readonly) map.on('click', (event: L.LeafletMouseEvent) => emitPick(event.latlng))
    render(false)
    if (typeof ResizeObserver !== 'undefined') {
      resizeObserver = new ResizeObserver(() => map?.invalidateSize())
      resizeObserver.observe(container.value)
    }
  } catch {
    loadError.value = 'Không khởi tạo được bản đồ. Bạn vẫn có thể dán tọa độ hoặc dùng GPS.'
  }
})

watch(
  () => [props.latitude, props.longitude, props.accuracy],
  ([latitude, longitude], previous) => {
    const moved = !previous || latitude !== previous[0] || longitude !== previous[1]
    // Chỉ đưa bản đồ tới ghim khi ghim nằm ngoài khung đang xem (vd. vừa dán tọa độ hoặc lấy GPS).
    const outside = Boolean(
      map && latitude !== null && longitude !== null && !map.getBounds().contains([latitude as number, longitude as number]),
    )
    render(moved && outside)
  },
)

onBeforeUnmount(() => {
  resizeObserver?.disconnect()
  map?.remove()
  map = null
  marker = null
  accuracyCircle = null
  tileLayer = null
})
</script>

<template>
  <div class="picker">
    <div ref="container" class="picker-map" role="region" :aria-label="label" />
    <div class="picker-zoom">
      <button type="button" aria-label="Phóng to bản đồ" @click="zoom(1)">+</button>
      <button type="button" aria-label="Thu nhỏ bản đồ" @click="zoom(-1)">−</button>
    </div>
    <p v-if="loadError" class="picker-error" role="alert">{{ loadError }}</p>
  </div>
</template>

<style scoped>
.picker { position: relative; height: 100%; min-height: inherit; }
.picker-map { width: 100%; height: 100%; min-height: inherit; border-radius: inherit; background: var(--ocop-mist-100); }
.picker-zoom { position: absolute; z-index: 500; top: var(--ocop-space-3); right: var(--ocop-space-3); display: grid; gap: var(--ocop-space-2); }
.picker-zoom button { width: var(--ocop-control-md); height: var(--ocop-control-md); border: 1px solid var(--ocop-mist-300); border-radius: var(--ocop-radius-sm); background: var(--ocop-white); color: var(--ocop-mist-950); font-size: var(--ocop-font-size-title-sm); font-weight: 700; }
.picker-zoom button:focus-visible { outline: 3px solid var(--ocop-daquy-400); outline-offset: 2px; }
.picker-error { position: absolute; z-index: 500; inset: var(--ocop-space-3) calc(var(--ocop-control-md) + var(--ocop-space-5)) auto var(--ocop-space-3); margin: 0; padding: var(--ocop-space-2) var(--ocop-space-3); border-radius: var(--ocop-radius-sm); background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); font-size: var(--ocop-font-size-small); }
</style>

<style>
.ocop-pick-pin-anchor { border: 0; background: transparent; }
.ocop-pick-pin {
  position: relative;
  display: block;
  width: 36px;
  height: 36px;
  border: 2px solid var(--ocop-mist-950);
  border-radius: 50% 50% 50% 0;
  background: var(--ocop-daquy-400);
  box-shadow: var(--ocop-shadow-sm);
  transform: rotate(-45deg);
}
.ocop-pick-pin > span {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 12px;
  height: 12px;
  margin: -6px 0 0 -6px;
  border-radius: 50%;
  background: var(--ocop-mist-950);
}
.leaflet-marker-icon:focus-visible .ocop-pick-pin { outline: 3px solid var(--ocop-tone-sky); outline-offset: 2px; }
.ocop-pick-accuracy { fill: var(--ocop-tone-sky); fill-opacity: 0.12; stroke: var(--ocop-tone-sky); stroke-opacity: 0.5; }
</style>
