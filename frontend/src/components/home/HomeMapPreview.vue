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

const legend = computed(() => {
  const seen = new Map<string, { label: string; icon: string; color: string }>()
  for (const feature of features.value) {
    if (seen.has(feature.properties.type)) continue
    const style = locationTypeStyle(feature.properties.type)
    seen.set(feature.properties.type, {
      label: feature.properties.type_label,
      icon: style.icon,
      color: style.color,
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
  <section id="ban-do" class="map-section" aria-labelledby="map-title">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Bản Đồ Số PostGIS &amp; Leaflet</span>
        <h2 id="map-title">Xem Nhanh Bản Đồ Du Lịch Nông Nghiệp Lâm Đồng</h2>
        <p>Định vị trang trại, đồi chè, vườn dâu và tìm đường đến điểm gần bạn nhất</p>
      </div>
      <span class="demo-label">{{ features.length }} điểm đến</span>
    </div>

    <div class="map-preview">
      <div class="map-grid" aria-hidden="true" />
      <p v-if="isLoading" class="map-empty">Đang tải điểm đến...</p>
      <p v-else-if="!markers.length" class="map-empty">Chưa có điểm đến được công bố.</p>

      <RouterLink
        v-for="marker in markers"
        :key="marker.slug"
        class="map-marker"
        :style="{ left: `${marker.x}%`, top: `${marker.y}%`, '--marker-color': marker.color }"
        :to="{ name: 'map', query: { diem: marker.slug } }"
        :aria-label="`Xem ${marker.name} trên bản đồ`"
      >
        <AppIcon :name="marker.icon" :size="15" />
        <span>{{ marker.name }}</span>
      </RouterLink>

      <div v-if="legend.length" class="map-legend">
        <strong>Chú giải:</strong>
        <span v-for="item in legend" :key="item.label">
          <AppIcon :name="item.icon" :size="14" :style="{ color: item.color }" /> {{ item.label }}
        </span>
      </div>
    </div>

    <RouterLink class="map-button" :to="{ name: 'map' }">
      Mở Bản Đồ Số Toàn Màn Hình <AppIcon name="chevronRight" :size="16" />
    </RouterLink>
  </section>
</template>

<style scoped>
.map-section {
  padding-top: var(--ocop-space-12);
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--ocop-space-4);
}

.eyebrow {
  color: var(--ocop-blue);
  font-size: var(--ocop-font-size-xs);
  font-weight: 800;
  line-height: 16px;
  text-transform: uppercase;
}

h2 {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-navy);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.section-heading p {
  margin: 2px 0 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
}

.demo-label {
  flex: 0 0 auto;
  padding: 5px 9px;
  border: 1px solid var(--ocop-info-border);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-info-soft);
  color: var(--ocop-blue-700);
  font-size: var(--ocop-font-size-2xs);
  font-weight: 700;
}

.map-preview {
  position: relative;
  min-height: 430px;
  margin-top: var(--ocop-space-4);
  overflow: hidden;
  border: 1px solid var(--ocop-neutral-300);
  border-radius: var(--ocop-radius-lg);
  background:
    radial-gradient(circle at 70% 18%, color-mix(in srgb, var(--ocop-mint-300) 65%, transparent), transparent 20%),
    radial-gradient(circle at 27% 68%, color-mix(in srgb, var(--ocop-lime-300) 70%, transparent), transparent 28%),
    var(--ocop-tone-leaf-soft);
  box-shadow: inset 0 0 50px color-mix(in srgb, var(--ocop-primary-950) 8%, transparent);
}

.map-grid {
  position: absolute;
  inset: -40px;
  opacity: 0.55;
  background-image:
    linear-gradient(28deg, transparent 45%, var(--ocop-card) 46%, var(--ocop-card) 49%, transparent 50%),
    linear-gradient(105deg, transparent 47%, var(--ocop-info-border) 48%, var(--ocop-info-border) 51%, transparent 52%),
    linear-gradient(0deg, color-mix(in srgb, var(--ocop-neutral-500) 12%, transparent) 1px, transparent 1px),
    linear-gradient(90deg, color-mix(in srgb, var(--ocop-neutral-500) 12%, transparent) 1px, transparent 1px);
  background-size: 210px 160px, 240px 190px, 42px 42px, 42px 42px;
  transform: rotate(-4deg) scale(1.08);
}

.map-marker {
  position: absolute;
  padding: 0;
  background: var(--marker-color, var(--ocop-primary-700));
  text-decoration: none;
  z-index: 2;
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border: 3px solid var(--ocop-white);
  border-radius: 50% 50% 50% var(--ocop-radius-sm);
  box-shadow: 0 5px 10px color-mix(in srgb, var(--ocop-neutral-900) 24%, transparent);
  color: var(--ocop-white);
  transform: translate(-50%, -50%) rotate(-45deg);
}

.map-marker :deep(.app-icon) {
  transform: rotate(45deg);
}

.map-marker > span {
  position: absolute;
  left: 31px;
  display: none;
  width: max-content;
  max-width: 160px;
  padding: 5px var(--ocop-space-2);
  border-radius: 6px;
  background: color-mix(in srgb, var(--ocop-neutral-900) 88%, transparent);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-2xs);
  transform: rotate(45deg);
}

.map-marker:hover > span,
.map-marker:focus-visible > span {
  display: block;
}

.map-marker:not(:hover) {
  font-size: var(--ocop-font-size-small);
}

.map-legend {
  position: absolute;
  z-index: 2;
  right: 16px;
  bottom: 16px;
  display: flex;
  padding: 10px var(--ocop-space-3);
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  border: 1px solid color-mix(in srgb, var(--ocop-neutral-200) 90%, transparent);
  border-radius: var(--ocop-radius-sm);
  background: color-mix(in srgb, var(--ocop-white) 92%, transparent);
  box-shadow: 0 5px 12px color-mix(in srgb, var(--ocop-neutral-900) 10%, transparent);
  color: var(--ocop-text-muted);
  font-size: var(--ocop-font-size-2xs);
}

.map-legend strong {
  color: var(--ocop-navy);
}

.map-legend span {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-1);
}

.map-button {
  display: flex;
  width: max-content;
  margin: var(--ocop-space-3) 0 0 auto;
  padding: 9px 14px;
  align-items: center;
  gap: 5px;
  border: 1px solid var(--ocop-primary-700);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  text-decoration: none;
  transition: background var(--ocop-transition);
}

.map-button:hover {
  background: var(--ocop-primary-900);
  color: var(--ocop-white);
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

@media (max-width: 767.98px) {
  .section-heading {
    align-items: flex-start;
  }

  .section-heading p {
    max-width: 250px;
  }

  .map-preview {
    min-height: 390px;
  }

  .map-legend {
    right: 10px;
    bottom: 10px;
    left: 10px;
  }

  .map-marker > span {
    display: none !important;
  }
}
</style>
