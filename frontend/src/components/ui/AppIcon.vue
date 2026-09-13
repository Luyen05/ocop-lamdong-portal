<script setup lang="ts">
import {
  ArrowLeft,
  Award,
  Building,
  ChevronRight,
  CircleCheck,
  Clock,
  CupSoda,
  Eye,
  Flower,
  House,
  LayoutDashboard,
  LogOut,
  Mail,
  Map,
  MapPin,
  Menu,
  Navigation,
  Newspaper,
  Package,
  Palette,
  Phone,
  ShieldCheck,
  Sprout,
  Star,
  Store,
  User,
  Users,
  Utensils,
} from '@lucide/vue'
import { computed, type Component } from 'vue'

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

const iconComponents: Record<string, Component> = {
  home: House,
  dashboard: LayoutDashboard,
  package: Package,
  'map-pin': MapPin,
  building: Building,
  users: Users,
  star: Star,
  newspaper: Newspaper,
  user: User,
  menu: Menu,
  logout: LogOut,
  arrowLeft: ArrowLeft,
  shieldCheck: ShieldCheck,
  award: Award,
  map: Map,
  sprout: Sprout,
  food: Utensils,
  drink: CupSoda,
  palette: Palette,
  flower: Flower,
  store: Store,
  phone: Phone,
  mail: Mail,
  clock: Clock,
  navigation: Navigation,
  eye: Eye,
  checkCircle: CircleCheck,
  chevronRight: ChevronRight,
}

const iconComponent = computed(() => iconComponents[props.name] ?? CircleCheck)
</script>

<template>
  <component
    :is="iconComponent"
    class="app-icon"
    :size="size"
    :stroke-width="strokeWidth"
    :aria-hidden="label ? undefined : 'true'"
    :aria-label="label || undefined"
    :role="label ? 'img' : undefined"
  />
</template>

<style scoped>
.app-icon {
  display: inline-block;
  flex: 0 0 auto;
  vertical-align: -0.15em;
}
</style>
