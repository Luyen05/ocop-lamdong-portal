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
  padding-top: 48px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  color: var(--ocop-blue);
  font-size: 11px;
  font-weight: 800;
  line-height: 16px;
  text-transform: uppercase;
}

h2 {
  margin: 4px 0 0;
  color: var(--ocop-navy);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.section-heading p {
  margin: 2px 0 0;
  color: var(--ocop-slate);
  font-size: 13px;
}

.demo-label {
  flex: 0 0 auto;
  padding: 5px 9px;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 10px;
  font-weight: 700;
}

.map-preview {
  position: relative;
  min-height: 430px;
  margin-top: 16px;
  overflow: hidden;
  border: 1px solid #cbd5e1;
  border-radius: var(--ocop-radius-lg);
  background:
    radial-gradient(circle at 70% 18%, rgb(153 215 190 / 65%), transparent 20%),
    radial-gradient(circle at 27% 68%, rgb(186 216 154 / 70%), transparent 28%),
    #e9f2e7;
  box-shadow: inset 0 0 50px rgb(71 101 77 / 8%);
}

.map-grid {
  position: absolute;
  inset: -40px;
  opacity: 0.55;
  background-image:
    linear-gradient(28deg, transparent 45%, #fff 46%, #fff 49%, transparent 50%),
    linear-gradient(105deg, transparent 47%, #c7d9ee 48%, #c7d9ee 51%, transparent 52%),
    linear-gradient(0deg, rgb(100 116 139 / 12%) 1px, transparent 1px),
    linear-gradient(90deg, rgb(100 116 139 / 12%) 1px, transparent 1px);
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
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 8px;
  box-shadow: 0 5px 10px rgb(15 23 43 / 24%);
  color: #fff;
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
  padding: 5px 8px;
  border-radius: 6px;
  background: rgb(15 23 43 / 88%);
  color: #fff;
  font-size: 10px;
  transform: rotate(45deg);
}

.map-marker:hover > span,
.map-marker:focus-visible > span {
  display: block;
}

.map-marker:not(:hover) {
  font-size: 13px;
}

.map-legend {
  position: absolute;
  z-index: 2;
  right: 16px;
  bottom: 16px;
  display: flex;
  padding: 10px 12px;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  border: 1px solid rgb(226 232 240 / 90%);
  border-radius: var(--ocop-radius-sm);
  background: rgb(255 255 255 / 92%);
  box-shadow: 0 5px 12px rgb(15 23 43 / 10%);
  color: #45556c;
  font-size: 10px;
}

.map-legend strong {
  color: var(--ocop-navy);
}

.map-legend span {
  display: flex;
  align-items: center;
  gap: 4px;
}

.map-button {
  display: flex;
  width: max-content;
  margin: 12px 0 0 auto;
  padding: 9px 14px;
  align-items: center;
  gap: 5px;
  border: 1px solid var(--ocop-primary-700);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-primary-700);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
  transition: background var(--ocop-transition);
}

.map-button:hover {
  background: var(--ocop-primary-900);
  color: #fff;
}

.map-empty {
  position: absolute;
  z-index: 2;
  inset: 0;
  display: grid;
  margin: 0;
  place-items: center;
  color: var(--ocop-slate);
  font-size: 13px;
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
