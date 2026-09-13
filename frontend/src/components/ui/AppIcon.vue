<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    name: string
    label?: string
    size?: number | string
    strokeWidth?: number
  }>(),
  {
    label: '',
    size: 20,
    strokeWidth: 1.8,
  },
)

const iconPaths: Record<string, string[]> = {
  home: ['M3 10.5 12 3l9 7.5', 'M5 9.5V21h14V9.5', 'M9 21v-7h6v7'],
  dashboard: ['M4 4h6v6H4z', 'M14 4h6v10h-6z', 'M4 14h6v6H4z', 'M14 18h6v2h-6z'],
  package: ['M21 8 12 13 3 8', 'M12 13v9', 'M20 8v9l-8 5-8-5V8l8-5z', 'm7.5 5.5 9 5'],
  'map-pin': ['M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z', 'M12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
  building: ['M3 21h18', 'M6 21V5l6-2v18', 'M18 21V9l-6-2', 'M9 8h.01', 'M9 12h.01', 'M15 12h.01', 'M15 16h.01'],
  users: ['M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2', 'M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8Z', 'M22 21v-2a4 4 0 0 0-3-3.87', 'M16 3.13a4 4 0 0 1 0 7.75'],
  star: ['m12 3 2.75 5.57 6.15.9-4.45 4.33 1.05 6.12L12 17.77 6.5 20.66l1.05-6.12L3.1 9.47l6.15-.9z'],
  newspaper: ['M5 4h14v16H5z', 'M8 8h8', 'M8 12h8', 'M8 16h5'],
  user: ['M20 21a8 8 0 0 0-16 0', 'M12 13a5 5 0 1 0 0-10 5 5 0 0 0 0 10Z'],
  menu: ['M4 6h16', 'M4 12h16', 'M4 18h16'],
  logout: ['M10 17l5-5-5-5', 'M15 12H3', 'M21 19V5a2 2 0 0 0-2-2h-6'],
  arrowLeft: ['m15 18-6-6 6-6', 'M9 12h12'],
  shieldCheck: ['M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10Z', 'm9 12 2 2 4-4'],
  award: ['M12 15a6 6 0 1 0 0-12 6 6 0 0 0 0 12Z', 'm8.5 13.5-1 7 4.5-2 4.5 2-1-7', 'm9.5 9 1.5 1.5L14.5 7'],
  map: ['m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3z', 'M9 3v15', 'M15 6v15'],
  sprout: ['M7 20h10', 'M12 20v-8', 'M12 12C6 12 5 8 5 5c4 0 7 2 7 7Z', 'M12 14c0-4 3-7 7-7 0 4-2 7-7 7Z'],
  food: ['M6 3v7a3 3 0 0 0 6 0V3', 'M9 3v18', 'M17 3v18', 'M17 3c3 2 3 7 0 9'],
  drink: ['M6 3h12l-1 18H7z', 'M8 8h8', 'm14 3 3-2'],
  palette: ['M12 3a9 9 0 0 0 0 18h1.5a2 2 0 0 0 0-4H12a2 2 0 0 1 0-4 8 8 0 0 1 4-15Z', 'M7.5 10h.01', 'M9.5 6.5h.01', 'M14.5 6.5h.01', 'M16.5 10h.01'],
  flower: ['M12 13a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z', 'M12 7c-3-5-7-2-5 2-5-1-6 4-2 6-1 5 4 6 2 3 5 7 2 5-2 5 1 6-4 2-6 1-5-4-6-7-2Z'],
  store: ['M3 9 5 4h14l2 5', 'M5 13v8h14v-8', 'M9 21v-6h6v6', 'M3 9a3 3 0 0 0 6 0 3 3 0 0 0 6 0 3 3 0 0 0 6 0'],
  phone: ['M22 16.92v3a2 2 0 0 1-2.18 2 19.8 19.8 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6A19.8 19.8 0 0 1 2.12 4.2 2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72c.13.96.36 1.9.69 2.8a2 2 0 0 1-.45 2.11L8.1 8.88a16 16 0 0 0 6 6l1.25-1.25a2 2 0 0 1 2.11-.45c.9.33 1.84.56 2.8.69A2 2 0 0 1 22 15.86Z'],
  mail: ['M4 4h16v16H4z', 'm4 7 8 6 8-6'],
  clock: ['M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20Z', 'M12 6v6l4 2'],
  navigation: ['m3 11 19-9-9 19-2-8z'],
  eye: ['M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Z', 'M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6Z'],
  checkCircle: ['M22 11.08V12a10 10 0 1 1-5.93-9.14', 'm9 11 3 3L22 4'],
  chevronRight: ['m9 18 6-6-6-6'],
}

const paths = computed(() => iconPaths[props.name] ?? iconPaths.checkCircle)
</script>

<template>
  <svg
    class="app-icon"
    :width="size"
    :height="size"
    viewBox="0 0 24 24"
    fill="none"
    stroke="currentColor"
    :stroke-width="strokeWidth"
    stroke-linecap="round"
    stroke-linejoin="round"
    :aria-hidden="label ? undefined : 'true'"
    :aria-label="label || undefined"
    :role="label ? 'img' : undefined"
  >
    <path v-for="path in paths" :key="path" :d="path" />
  </svg>
</template>

<style scoped>
.app-icon {
  display: inline-block;
  flex: 0 0 auto;
  vertical-align: -0.15em;
}
</style>
