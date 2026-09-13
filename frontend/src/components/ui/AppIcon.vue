<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    name: string
    label?: string
    size?: number | string
    /** Giữ lại để tương thích với các vị trí từng dùng icon SVG. */
    strokeWidth?: number
  }>(),
  {
    label: '',
    size: 20,
    strokeWidth: 1.8,
  },
)

const iconNames: Record<string, string> = {
  home: 'house',
  dashboard: 'grid-1x2-fill',
  package: 'box-seam',
  'map-pin': 'geo-alt',
  building: 'buildings',
  users: 'people',
  star: 'star-fill',
  newspaper: 'newspaper',
  user: 'person-circle',
  menu: 'list',
  logout: 'box-arrow-right',
  arrowLeft: 'arrow-left',
  shieldCheck: 'shield-check',
  award: 'award',
  map: 'map',
  sprout: 'tree',
  food: 'egg-fried',
  drink: 'cup-straw',
  palette: 'palette',
  flower: 'flower1',
  store: 'shop',
  phone: 'telephone',
  mail: 'envelope',
  clock: 'clock',
  navigation: 'cursor',
  eye: 'eye',
  eyeSlash: 'eye-slash',
  search: 'search',
  compass: 'compass',
  lock: 'lock',
  close: 'x-lg',
  circle: 'circle',
  refresh: 'arrow-clockwise',
  checkCircle: 'check-circle',
  chevronRight: 'chevron-right',
  chevronLeft: 'chevron-left',
}

const iconName = computed(() => iconNames[props.name] ?? 'check-circle')
const normalizedSize = computed(() =>
  typeof props.size === 'number' ? `${props.size}px` : props.size,
)
</script>

<template>
  <i
    :class="['app-icon', 'bi', `bi-${iconName}`]"
    :style="{ fontSize: normalizedSize }"
    :aria-hidden="label ? undefined : 'true'"
    :aria-label="label || undefined"
    :role="label ? 'img' : undefined"
  />
</template>

<style scoped>
.app-icon {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  justify-content: center;
  line-height: 1;
  vertical-align: -0.125em;
}
</style>
