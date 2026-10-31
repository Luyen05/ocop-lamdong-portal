<script setup lang="ts">
import { computed } from 'vue'

import type { LocationType, MapFeature } from '@/types/location'
import { countFeaturesByType, locationTypeStyle } from '@/utils/location'

const props = defineProps<{
  /** Các điểm đang hiển thị (đã lọc, có tọa độ hợp lệ). */
  features: MapFeature[]
  /** Loại hình đang lọc; rỗng nghĩa là mọi loại. */
  activeType: LocationType | ''
}>()

/** Bấm loại đang lọc thì bỏ lọc (phát chuỗi rỗng). */
const emit = defineEmits<{ select: [type: LocationType | ''] }>()

const entries = computed(() => countFeaturesByType(props.features))

function toggle(type: LocationType): void {
  emit('select', props.activeType === type ? '' : type)
}
</script>

<template>
  <section v-if="entries.length" class="map-legend" aria-labelledby="map-legend-title">
    <h2 id="map-legend-title">Chú giải loại hình</h2>
    <ul>
      <li v-for="entry in entries" :key="entry.type">
        <button
          type="button"
          class="legend-item"
          :aria-pressed="activeType === entry.type"
          @click="toggle(entry.type)"
        >
          <span class="legend-swatch" :style="{ '--legend-color': locationTypeStyle(entry.type).color }" aria-hidden="true">
            <i :class="`bi bi-${locationTypeStyle(entry.type).markerIcon}`" />
          </span>
          <span class="legend-label">{{ entry.label }}</span>
          <span class="legend-count">{{ entry.count }}<span class="visually-hidden"> điểm</span></span>
        </button>
      </li>
    </ul>
    <p class="legend-hint">Bấm một loại để chỉ xem loại đó, bấm lần nữa để bỏ lọc.</p>
  </section>
</template>

<style scoped>
.map-legend {
  padding: 14px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
}

.map-legend h2 {
  margin: 0 0 var(--ocop-space-2);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-body-lg);
  font-weight: 800;
}

ul {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(9.5rem, 1fr));
  gap: 6px;
  margin: 0;
  padding: 0;
  list-style: none;
}

.legend-item {
  display: flex;
  width: 100%;
  min-height: 44px;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 6px 10px;
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-surface-subtle);
  color: var(--ocop-navy);
  text-align: left;
}

.legend-item:hover {
  border-color: var(--ocop-mint-border);
}

.legend-item[aria-pressed='true'] {
  border-color: var(--ocop-primary-700);
  background: var(--ocop-mint-soft);
  box-shadow: inset 0 0 0 1px var(--ocop-primary-700);
}

.legend-item:focus-visible {
  outline: 3px solid color-mix(in srgb, var(--ocop-primary-500) 60%, transparent);
  outline-offset: 2px;
}

.legend-swatch {
  display: grid;
  width: 24px;
  height: 24px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: var(--legend-color);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
}

.legend-label {
  min-width: 0;
  flex: 1 1 auto;
  font-size: var(--ocop-font-size-small);
  font-weight: 650;
  line-height: 1.25;
}

.legend-count {
  flex: 0 0 auto;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 800;
}

.legend-hint {
  margin: var(--ocop-space-2) 0 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
}
</style>
