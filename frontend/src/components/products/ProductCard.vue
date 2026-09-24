<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import type { ProductListItem } from '@/types/product'

const props = defineProps<{
  product: ProductListItem
}>()

const imageFailed = ref(false)

watch(
  () => props.product.primary_image_url,
  () => {
    imageFailed.value = false
  },
)

const formattedPrice = computed(() => {
  if (props.product.price === null || props.product.price <= 0) return 'Liên hệ'
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(props.product.price)
})

</script>

<template>
  <article class="product-card">
    <RouterLink class="product-card-link" :to="`/san-pham/${product.slug}`">
      <div class="product-media">
        <img
          v-if="product.primary_image_url && !imageFailed"
          :src="product.primary_image_url"
          :alt="product.name"
          loading="lazy"
          @error="imageFailed = true"
        />
        <div v-else class="product-placeholder" aria-hidden="true">
          <span class="placeholder-mark">OCOP</span>
          <span>Lâm Đồng</span>
        </div>
        <span class="star-badge"><AppIcon name="star" :size="12" /> OCOP {{ product.star }} sao</span>
      </div>

      <div class="product-body">
        <span class="product-location"><AppIcon name="map-pin" :size="14" /> {{ product.subject.district }}</span>
        <h2>{{ product.name }}</h2>
        <p class="product-meta">
          {{ product.category.name }}
          <span v-if="product.vietgap_code"><AppIcon name="checkCircle" :size="12" /> VietGAP</span>
        </p>

        <div class="product-subject">
          <span>Chủ thể</span>
          <strong :title="product.subject.name">{{ product.subject.name }}</strong>
        </div>

        <div class="product-price-row">
          <div class="product-price">
            <strong>{{ formattedPrice }}</strong>
            <small v-if="product.price !== null && product.price > 0 && product.unit">/ {{ product.unit }}</small>
          </div>
          <span v-if="product.rating_avg > 0" class="product-rating"><AppIcon name="star" :size="12" /> {{ product.rating_avg.toFixed(1) }}</span>
        </div>
      </div>
    </RouterLink>
  </article>
</template>

<style scoped>
.product-card {
  display: flex;
  height: 100%;
  min-width: 0;
  overflow: hidden;
  flex-direction: column;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  box-shadow: 0 4px 12px color-mix(in srgb, var(--ocop-neutral-900) 5%, transparent);
  transition: transform var(--ocop-transition), box-shadow var(--ocop-transition);
}

.product-card-link {
  display: flex;
  height: 100%;
  min-width: 0;
  flex-direction: column;
  color: inherit;
  text-decoration: none;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 28px color-mix(in srgb, var(--ocop-neutral-900) 12%, transparent);
}

.product-media {
  position: relative;
  display: block;
  overflow: hidden;
  aspect-ratio: 1.4 / 1;
  background: var(--ocop-border-soft);
}

.product-media > img,
.product-placeholder {
  width: 100%;
  height: 100%;
}

.product-media > img {
  object-fit: cover;
  transition: transform 250ms ease;
}

.product-card:hover .product-media > img {
  transform: scale(1.035);
}

.product-placeholder {
  display: grid;
  place-content: center;
  background:
    radial-gradient(circle at 20% 15%, color-mix(in srgb, var(--ocop-white) 75%, transparent), transparent 7rem),
    linear-gradient(145deg, var(--ocop-sage-50), var(--ocop-sage-300));
  color: var(--ocop-primary-900);
  text-align: center;
}

.product-placeholder span {
  color: color-mix(in srgb, var(--ocop-primary-900) 70%, transparent);
  font-size: var(--ocop-font-size-xs);
  font-weight: 700;
  letter-spacing: 0.14em;
  text-transform: uppercase;
}

.product-placeholder .placeholder-mark {
  color: var(--ocop-primary-900);
  font-size: 25px;
  font-weight: 800;
  letter-spacing: 0.1em;
}

.star-badge {
  position: absolute;
  z-index: 1;
  padding: 5px 10px;
  border-radius: var(--ocop-radius-sm);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-xs);
  font-weight: 700;
  line-height: 14px;
}

.star-badge {
  top: 12px;
  left: 12px;
  background: var(--ocop-star-strong);
  box-shadow: 0 3px 8px color-mix(in srgb, var(--ocop-notice) 20%, transparent);
}

.product-body {
  display: flex;
  min-height: 188px;
  flex: 1;
  flex-direction: column;
  padding: var(--ocop-space-4);
}

.product-location {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-caption);
  font-weight: 500;
}

.product-body h2 {
  display: -webkit-box;
  overflow: hidden;
  min-height: 42px;
  margin: 7px 0 var(--ocop-space-1);
  color: var(--ocop-text-primary);
  font-size: var(--ocop-font-size-body-lg);
  font-weight: 750;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.product-meta {
  display: flex;
  margin: 0;
  align-items: center;
  flex-wrap: wrap;
  gap: var(--ocop-space-2);
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-caption);
}

.product-meta span {
  display: inline-flex;
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-success);
  font-weight: 700;
}

.product-subject {
  display: grid;
  min-width: 0;
  margin-top: auto;
  padding-top: var(--ocop-space-3);
  gap: 2px;
  color: var(--ocop-text-tertiary);
  font-size: var(--ocop-font-size-xs);
}

.product-subject strong {
  overflow: hidden;
  color: var(--ocop-text-muted);
  font-size: var(--ocop-font-size-caption);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-price-row,
.product-price {
  display: flex;
  align-items: center;
}

.product-price-row {
  margin-top: 7px;
  justify-content: space-between;
  gap: var(--ocop-space-2);
}

.product-price {
  min-width: 0;
  gap: 3px;
}

.product-price strong {
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-body-lg);
  line-height: 20px;
  white-space: nowrap;
}

.product-price small {
  overflow: hidden;
  color: var(--ocop-text-tertiary);
  font-size: var(--ocop-font-size-xs);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-rating {
  flex: 0 0 auto;
  color: var(--ocop-star);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.product-card-link:focus-visible {
  border-radius: inherit;
  outline: 3px solid color-mix(in srgb, var(--ocop-primary-500) 28%, transparent);
  outline-offset: -3px;
}
</style>
