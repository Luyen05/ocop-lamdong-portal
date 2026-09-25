<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { getMapLocations } from '@/services/locations'
import type { MapFeature } from '@/types/location'
import { locationTypeStyle } from '@/utils/location'

const features = ref<MapFeature[]>([])
const isLoading = ref(true)

// Ảnh xem trước dùng phép chiếu tuyến tính trong khung bao các điểm thật;
// bản đồ tương tác đầy đủ nằm ở trang /ban-do.
const markers = computed(() => {
  if (!features.value.length) return []
  const longitudes = features.value.map((feature) => feature.geometry.coordinates[0])
  const latitudes = features.value.map((feature) => feature.geometry.coordinates[1])
  const [minLng, maxLng] = [Math.min(...longitudes), Math.max(...longitudes)]
  const [minLat, maxLat] = [Math.min(...latitudes), Math.max(...latitudes)]
  const lngSpan = maxLng - minLng || 1
  const latSpan = maxLat - minLat || 1
  return features.value.map((feature) => {
    const [longitude, latitude] = feature.geometry.coordinates
    const style = locationTypeStyle(feature.properties.type)
    return {
      slug: feature.properties.slug,
      name: feature.properties.name,
      icon: style.icon,
      color: style.color,
      x: maxLng === minLng ? 50 : 8 + ((longitude - minLng) / lngSpan) * 84,
      y: maxLat === minLat ? 50 : 10 + ((maxLat - latitude) / latSpan) * 72,
    }
  })
})

// Marker clustering: các điểm quá gần nhau trên khung nhỏ được gom thành một vòng có số lượng,
// tránh chồng lấn và vùng bấm bị che; bấm vào vòng để mở bản đồ đầy đủ.
const CLUSTER_X = 10
const CLUSTER_Y = 16

const clusters = computed(() => {
  const groups: { x: number; y: number; items: typeof markers.value }[] = []
  for (const marker of markers.value) {
    const group = groups.find((item) => Math.abs(item.x - marker.x) < CLUSTER_X && Math.abs(item.y - marker.y) < CLUSTER_Y)
    if (group) {
      group.items.push(marker)
      group.x = group.items.reduce((sum, item) => sum + item.x, 0) / group.items.length
      group.y = group.items.reduce((sum, item) => sum + item.y, 0) / group.items.length
    } else {
      groups.push({ x: marker.x, y: marker.y, items: [marker] })
    }
  }
  return groups
})

const singleMarkers = computed(() => clusters.value.filter((group) => group.items.length === 1).map((group) => group.items[0]))
const groupedMarkers = computed(() => clusters.value.filter((group) => group.items.length > 1))

const legend = computed(() => {
  const seen = new Map<string, { label: string; icon: string; color: string; count: number }>()
  for (const feature of features.value) {
    const item = seen.get(feature.properties.type)
    if (item) {
      item.count += 1
      continue
    }
    const style = locationTypeStyle(feature.properties.type)
    seen.set(feature.properties.type, {
      label: feature.properties.type_label,
      icon: style.icon,
      color: style.color,
      count: 1,
    })
  }
  return [...seen.values()]
})

onMounted(async () => {
  try {
    features.value = (await getMapLocations()).features
  } catch {
    features.value = []
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <section id="ban-do" class="map-card" aria-labelledby="map-title">
    <div class="map-card-head">
      <div>
        <p class="ocop-eyebrow">Bản đồ số</p>
        <h2 id="map-title">Du lịch nông nghiệp Lâm Đồng</h2>
      </div>
      <span class="count-badge">
        <AppIcon name="map-pin" :size="14" />
        {{ features.length }} điểm đến
      </span>
    </div>

    <div class="map-preview">
      <svg class="map-art" viewBox="0 0 560 320" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">
        <rect class="land" width="560" height="320" />
        <path class="grid" d="M0 80 H560 M0 160 H560 M0 240 H560 M140 0 V320 M280 0 V320 M420 0 V320" />
        <path class="hill-a" d="M0 230 C90 190 170 250 260 205 S430 150 560 190 L560 320 L0 320 Z" />
        <path class="hill-b" d="M0 90 C120 60 190 120 300 85 S470 30 560 60 L560 0 L0 0 Z" />
        <path class="road road-main" d="M-10 260 C120 230 220 170 330 160 S470 120 570 110" />
        <path class="road" d="M300 -10 C320 80 360 150 420 210 S470 300 480 330" />
        <ellipse class="lake" cx="410" cy="150" rx="26" ry="14" />
      </svg>
      <p v-if="isLoading" class="map-empty" role="status">Đang tải điểm đến...</p>
      <p v-else-if="!markers.length" class="map-empty" role="status">Chưa có điểm đến được công bố.</p>

      <RouterLink
        v-for="group in groupedMarkers"
        :key="group.items.map((item) => item.slug).join('-')"
        class="map-cluster"
        :style="{ left: `${group.x}%`, top: `${group.y}%` }"
        :to="{ name: 'map' }"
        :aria-label="`${group.items.length} điểm du lịch ở gần nhau: ${group.items.map((item) => item.name).join(', ')}. Mở bản đồ để xem`"
      >
        {{ group.items.length }}
      </RouterLink>

      <RouterLink
        v-for="marker in singleMarkers"
        :key="marker.slug"
        class="map-marker"
        :style="{ left: `${marker.x}%`, top: `${marker.y}%`, '--marker-color': marker.color }"
        :to="{ name: 'map', query: { diem: marker.slug } }"
        :aria-label="`Xem ${marker.name} trên bản đồ`"
      >
        <AppIcon :name="marker.icon" :size="14" />
        <span>{{ marker.name }}</span>
      </RouterLink>
    </div>

    <div v-if="legend.length" class="map-legend" aria-label="Chú giải loại hình">
      <span v-for="item in legend" :key="item.label">
        <i class="legend-dot" :style="{ '--legend-color': item.color }" aria-hidden="true" />
        {{ item.label }} ({{ item.count }})
      </span>
    </div>

    <RouterLink class="ocop-btn-main map-button" :to="{ name: 'map' }">
      <AppIcon name="map" :size="16" />
      Mở bản đồ số, tìm điểm gần bạn
    </RouterLink>
  </section>
</template>

<style scoped>
.map-card {
  display: flex;
  height: 100%;
  flex-direction: column;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-card);
}

.map-card-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ocop-space-3);
}

h2 {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 750;
  line-height: 1.3;
}

.count-badge {
  display: inline-flex;
  min-height: 28px;
  flex: 0 0 auto;
  align-items: center;
  gap: var(--ocop-space-1);
  padding: 0 var(--ocop-space-3);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mist-100);
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.map-preview {
  position: relative;
  min-height: 200px;
  flex: 1;
  overflow: hidden;
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-mist-50);
}

.map-art {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.map-art .land { fill: var(--ocop-mist-50); }
.map-art .grid { fill: none; stroke: var(--ocop-mist-100); stroke-width: 1; }
.map-art .hill-a { fill: var(--ocop-tone-leaf-soft); }
.map-art .hill-b { fill: var(--ocop-mist-100); }
.map-art .road { fill: none; stroke: var(--ocop-card); stroke-linecap: round; stroke-width: 5; }
.map-art .road-main { stroke-width: 6; }
.map-art .lake { fill: var(--ocop-mist-200); }

.map-marker {
  position: absolute;
  z-index: 2;
  display: grid;
  width: 32px;
  height: 32px;
  padding: 0;
  place-items: center;
  border: 2px solid var(--ocop-white);
  border-radius: 50% 50% 50% var(--ocop-radius-xs);
  background: var(--marker-color, var(--ocop-primary-700));
  box-shadow: 0 4px 10px color-mix(in srgb, var(--ocop-mist-950) 28%, transparent);
  color: var(--ocop-white);
  text-decoration: none;
  transform: translate(-50%, -50%) rotate(-45deg);
}

.map-cluster {
  position: absolute;
  z-index: 2;
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border: 3px solid var(--ocop-white);
  border-radius: 50%;
  background: var(--ocop-mist-800);
  box-shadow: 0 0 0 6px color-mix(in srgb, var(--ocop-mist-800) 22%, transparent), 0 4px 10px color-mix(in srgb, var(--ocop-mist-950) 28%, transparent);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-body);
  font-weight: 800;
  text-decoration: none;
  transform: translate(-50%, -50%);
}

.map-cluster:hover {
  background: var(--ocop-mist-950);
  color: var(--ocop-white);
}

.map-marker :deep(.app-icon) {
  transform: rotate(45deg);
}

.map-marker > span {
  position: absolute;
  left: 30px;
  display: none;
  width: max-content;
  max-width: 160px;
  padding: var(--ocop-space-1) var(--ocop-space-2);
  border-radius: var(--ocop-radius-xs);
  background: color-mix(in srgb, var(--ocop-mist-950) 90%, transparent);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  transform: rotate(45deg);
}

.map-marker:hover > span,
.map-marker:focus-visible > span {
  display: block;
}

.map-legend {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--ocop-space-2) var(--ocop-space-4);
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-small);
}

.map-legend span {
  display: flex;
  min-width: 0;
  align-items: center;
  gap: var(--ocop-space-2);
}

.legend-dot {
  width: 12px;
  height: 12px;
  flex: 0 0 auto;
  border: 2px solid var(--ocop-card);
  border-radius: 50%;
  background: var(--legend-color);
  box-shadow: 0 0 0 1px var(--ocop-mist-200);
}

.map-button {
  width: 100%;
}

.map-empty {
  position: absolute;
  z-index: 2;
  inset: 0;
  display: grid;
  margin: 0;
  place-items: center;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
}

@media (max-width: 575.98px) {
  .map-card {
    padding: var(--ocop-space-4);
  }

  .map-preview {
    min-height: 220px;
  }

  .map-legend {
    font-size: var(--ocop-font-size-caption);
  }

  .map-marker > span {
    display: none !important;
  }
}
</style>
