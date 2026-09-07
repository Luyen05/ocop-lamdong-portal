<script setup lang="ts">
import { computed } from 'vue'

import type { ProductListItem } from '@/types/product'

const props = defineProps<{
  product: ProductListItem
}>()

const formattedPrice = computed(() =>
  new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(props.product.price),
)

const truncatedSubject = computed(() => {
  const name = props.product.subject.name
  return name.length > 46 ? `${name.slice(0, 46)}…` : name
})
</script>

<template>
  <article class="product-card">
    <RouterLink class="product-media" :to="`/san-pham/${product.slug}`">
      <img
        v-if="product.primary_image_url"
        :src="product.primary_image_url"
        :alt="product.name"
        loading="lazy"
      />
      <div v-else class="product-placeholder" aria-hidden="true">
        <span class="placeholder-mark">OCOP</span>
        <span>Lâm Đồng</span>
      </div>
      <span class="star-badge">★ OCOP {{ product.star }} SAO</span>
      <span class="category-badge">{{ product.category.name }}</span>
      <span v-if="product.star >= 4" class="vietgap-badge">✓ VietGAP</span>
    </RouterLink>

    <div class="product-body">
      <span class="product-location">⌖ {{ product.subject.district }}</span>
      <h2>
        <RouterLink :to="`/san-pham/${product.slug}`">{{ product.name }}</RouterLink>
      </h2>
      <p class="product-description">{{ product.description }}</p>

      <div class="product-subject">
        <span>Chủ thể:</span>
        <strong :title="product.subject.name">{{ truncatedSubject }}</strong>
      </div>

      <div class="product-price-row">
        <div class="product-price">
          <strong>{{ formattedPrice }}</strong>
          <small>/ {{ product.unit }}</small>
        </div>
        <span class="product-rating">★ {{ product.rating_avg.toFixed(1) }}</span>
      </div>

      <div class="product-actions">
        <RouterLink :to="`/san-pham/${product.slug}`">
          <span aria-hidden="true">◉</span>
          Chi Tiết
        </RouterLink>
        <a href="/#ban-do">
          <span aria-hidden="true">⌖</span>
          Bản Đồ
        </a>
      </div>
    </div>
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
  background: #fff;
  box-shadow: 0 4px 12px rgb(15 23 43 / 5%);
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.product-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 16px 28px rgb(15 23 43 / 12%);
}

.product-media {
  position: relative;
  display: block;
  overflow: hidden;
  aspect-ratio: 1.4 / 1;
  background: #e9eef2;
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
    radial-gradient(circle at 20% 15%, rgb(255 255 255 / 75%), transparent 7rem),
    linear-gradient(145deg, #dcead8, #a9c6a4);
  color: var(--ocop-primary-900);
  text-align: center;
}

.product-placeholder span {
  color: rgb(0 79 59 / 70%);
  font-size: 11px;
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

.star-badge,
.category-badge,
.vietgap-badge {
  position: absolute;
  z-index: 1;
  padding: 5px 10px;
  border-radius: var(--ocop-radius-sm);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  line-height: 14px;
}

.star-badge {
  top: 12px;
  left: 12px;
  background: #ff9500;
  box-shadow: 0 3px 8px rgb(151 60 0 / 20%);
}

.category-badge {
  top: 12px;
  right: 12px;
  max-width: calc(100% - 130px);
  overflow: hidden;
  background: rgb(15 23 43 / 78%);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.vietgap-badge {
  top: 42px;
  left: 12px;
  padding-block: 3px;
  background: var(--ocop-primary-700);
}

.product-body {
  display: flex;
  min-height: 264px;
  flex: 1;
  flex-direction: column;
  padding: 16px;
}

.product-location {
  color: #78909c;
  font-size: 11px;
  font-weight: 500;
}

.product-body h2 {
  display: -webkit-box;
  overflow: hidden;
  min-height: 39px;
  margin: 6px 0;
  font-size: 15px;
  font-weight: 750;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.product-body h2 a {
  color: var(--ocop-navy);
  text-decoration: none;
}

.product-body h2 a:hover {
  color: var(--ocop-primary-700);
}

.product-description {
  display: -webkit-box;
  overflow: hidden;
  min-height: 48px;
  margin: 0;
  color: var(--ocop-slate);
  font-size: 12px;
  line-height: 17px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.product-subject {
  display: flex;
  min-width: 0;
  margin-top: auto;
  padding-top: 12px;
  gap: 4px;
  border-top: 1px solid #edf0f3;
  color: #90a1b9;
  font-size: 10px;
  white-space: nowrap;
}

.product-subject strong {
  overflow: hidden;
  color: #45556c;
  text-overflow: ellipsis;
}

.product-price-row,
.product-price,
.product-actions {
  display: flex;
  align-items: center;
}

.product-price-row {
  margin-top: 7px;
  justify-content: space-between;
  gap: 8px;
}

.product-price {
  min-width: 0;
  gap: 3px;
}

.product-price strong {
  color: var(--ocop-primary-700);
  font-size: 16px;
  line-height: 20px;
  white-space: nowrap;
}

.product-price small {
  overflow: hidden;
  color: #90a1b9;
  font-size: 10px;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-rating {
  flex: 0 0 auto;
  color: #f59e0b;
  font-size: 11px;
  font-weight: 700;
}

.product-actions {
  margin-top: 12px;
  gap: 8px;
}

.product-actions a {
  display: inline-flex;
  min-height: 36px;
  flex: 1;
  align-items: center;
  justify-content: center;
  gap: 6px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-surface-muted);
  color: #45556c;
  font-size: 11px;
  font-weight: 700;
  text-decoration: none;
}

.product-actions a:first-child {
  border-color: var(--ocop-primary-700);
  background: var(--ocop-primary-700);
  color: #fff;
}

.product-actions a:hover {
  filter: brightness(0.96);
}
</style>
