<script setup lang="ts">
import { computed, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import type { LocationListItem } from '@/types/location'
import { formatTicketPrice, locationTypeStyle } from '@/utils/location'

const props = defineProps<{
  location: LocationListItem
}>()

const imageFailed = ref(false)
const typeStyle = computed(() => locationTypeStyle(props.location.type))
const imageUrl = computed(() =>
  props.location.primary_image_url && !imageFailed.value
    ? props.location.primary_image_url
    : typeStyle.value.illustration,
)
const visibleServices = computed(() => props.location.services.slice(0, 3))
</script>

<template>
  <article class="location-card">
    <RouterLink
      class="location-media"
      :to="{ name: 'location-detail', params: { slug: location.slug } }"
      :aria-label="`Xem chi tiết ${location.name}`"
    >
      <img
        :src="imageUrl"
        :alt="location.primary_image_url && !imageFailed ? location.name : ''"
        loading="lazy"
        @error="imageFailed = true"
      />
      <span class="type-badge" :style="{ '--type-color': typeStyle.color }">
        <AppIcon :name="typeStyle.icon" :size="13" /> {{ location.type_label }}
      </span>
    </RouterLink>

    <div class="location-body">
      <div class="location-meta">
        <span><AppIcon name="map-pin" :size="13" /> {{ location.district }}</span>
        <span v-if="location.opening_hours"><AppIcon name="clock" :size="13" /> {{ location.opening_hours }}</span>
      </div>
      <h3>
        <RouterLink :to="{ name: 'location-detail', params: { slug: location.slug } }">
          {{ location.name }}
        </RouterLink>
      </h3>
      <p v-if="location.description">{{ location.description }}</p>
      <ul v-if="visibleServices.length" class="service-list" aria-label="Dịch vụ trải nghiệm">
        <li v-for="service in visibleServices" :key="service">{{ service }}</li>
      </ul>
      <div class="location-footer">
        <span class="ticket">{{ formatTicketPrice(location.ticket_price) }}</span>
        <RouterLink
          class="map-link"
          :to="{ name: 'map', query: { diem: location.slug } }"
        >
          <AppIcon name="map" :size="14" /> Xem bản đồ
        </RouterLink>
      </div>
    </div>
  </article>
</template>

<style scoped>
.location-card {
  display: flex;
  overflow: hidden;
  flex-direction: column;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-sm);
  transition: transform var(--ocop-transition), box-shadow var(--ocop-transition);
}

.location-card:hover {
  box-shadow: var(--ocop-shadow-card);
  transform: translateY(-2px);
}

.location-media {
  position: relative;
  display: block;
  aspect-ratio: 16 / 10;
  overflow: hidden;
  background: var(--ocop-mint-soft);
}

.location-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.type-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 9px;
  border-radius: var(--ocop-radius-sm);
  background: var(--type-color, var(--ocop-primary-700));
  color: #fff;
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.location-body {
  display: flex;
  flex: 1;
  flex-direction: column;
  padding: 16px;
}

.location-meta {
  display: flex;
  flex-wrap: wrap;
  justify-content: space-between;
  gap: 6px;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
}

.location-meta span {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

h3 {
  margin: 8px 0 6px;
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 750;
  line-height: 1.35;
}

h3 a {
  color: var(--ocop-navy);
  text-decoration: none;
}

h3 a:hover {
  color: var(--ocop-primary-700);
}

p {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.service-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
  margin: 12px 0 0;
  padding: 0;
  list-style: none;
}

.service-list li {
  padding: 3px 8px;
  border-radius: 999px;
  background: var(--ocop-mint-soft);
  color: var(--ocop-primary-900);
  font-size: var(--ocop-font-size-caption);
  font-weight: 600;
}

.location-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 14px;
}

.ticket {
  color: var(--ocop-primary-900);
  font-weight: 750;
}

.map-link {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  gap: 5px;
  padding: 0 12px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-surface-muted);
  color: #45556c;
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  text-decoration: none;
}

.map-link:hover {
  border-color: var(--ocop-mint-border);
  color: var(--ocop-primary-900);
}
</style>
