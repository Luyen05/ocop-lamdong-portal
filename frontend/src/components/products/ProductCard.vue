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
        <span>OCOP</span>
      </div>
      <span class="star-badge">{{ product.star }} sao OCOP</span>
    </RouterLink>

    <div class="product-body">
      <span class="product-category">{{ product.category.name }}</span>
      <h2>
        <RouterLink :to="`/san-pham/${product.slug}`">{{ product.name }}</RouterLink>
      </h2>
      <p class="product-description">{{ product.description }}</p>

      <div class="product-meta">
        <span title="Điểm đánh giá">★ {{ product.rating_avg.toFixed(1) }}</span>
        <span>{{ product.subject.district }}</span>
      </div>

      <div class="product-footer">
        <div>
          <strong>{{ formattedPrice }}</strong>
          <small>/ {{ product.unit }}</small>
        </div>
        <RouterLink
          class="detail-link"
          :to="`/san-pham/${product.slug}`"
          :aria-label="`Xem chi tiết ${product.name}`"
        >
          Xem chi tiết →
        </RouterLink>
      </div>
    </div>
  </article>
</template>

<style scoped>
.product-card {
  height: 100%;
  overflow: hidden;
  border: 1px solid rgb(29 72 39 / 10%);
  border-radius: 1.15rem;
  background: #fff;
  box-shadow: 0 0.65rem 2rem rgb(31 64 38 / 7%);
  transition:
    transform 180ms ease,
    box-shadow 180ms ease;
}

.product-card:hover {
  transform: translateY(-0.25rem);
  box-shadow: 0 1rem 2.5rem rgb(31 64 38 / 13%);
}

.product-media {
  position: relative;
  display: block;
  overflow: hidden;
  aspect-ratio: 4 / 3;
  background: #e9f0e3;
}

.product-media img,
.product-placeholder {
  width: 100%;
  height: 100%;
}

.product-media img {
  object-fit: cover;
  transition: transform 250ms ease;
}

.product-card:hover .product-media img {
  transform: scale(1.035);
}

.product-placeholder {
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 70% 25%, rgb(219 235 186 / 85%), transparent 8rem),
    linear-gradient(145deg, #eaf2df, #cbdcbc);
  color: #2f6f3e;
  font-size: 1.2rem;
  font-weight: 800;
  letter-spacing: 0.18em;
}

.star-badge {
  position: absolute;
  top: 0.85rem;
  left: 0.85rem;
  padding: 0.35rem 0.65rem;
  border-radius: 999px;
  background: #fff6cf;
  color: #835f05;
  font-size: 0.74rem;
  font-weight: 750;
  box-shadow: 0 0.2rem 0.7rem rgb(70 60 20 / 12%);
}

.product-body {
  display: flex;
  height: calc(100% - min(75%, 17rem));
  min-height: 17rem;
  flex-direction: column;
  padding: 1.2rem;
}

.product-category {
  color: #3f7c4d;
  font-size: 0.75rem;
  font-weight: 750;
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.product-body h2 {
  margin: 0.55rem 0;
  font-size: 1.18rem;
  line-height: 1.35;
}

.product-body h2 a {
  color: #17261b;
  text-decoration: none;
}

.product-body h2 a:hover {
  color: #2f6f3e;
}

.product-description {
  display: -webkit-box;
  overflow: hidden;
  margin-bottom: 1rem;
  color: #6b746d;
  font-size: 0.9rem;
  line-height: 1.55;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.product-meta,
.product-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 0.75rem;
}

.product-meta {
  margin-top: auto;
  color: #7a817b;
  font-size: 0.82rem;
}

.product-meta span:first-child {
  color: #936e0b;
  font-weight: 700;
}

.product-footer {
  margin-top: 0.9rem;
  padding-top: 0.9rem;
  border-top: 1px solid #edf0ec;
}

.product-footer strong {
  display: block;
  color: #2f6f3e;
  font-size: 1.05rem;
}

.product-footer small {
  color: #7a817b;
}

.detail-link {
  flex: 0 0 auto;
  color: #2f6f3e;
  font-size: 0.86rem;
  font-weight: 700;
  text-decoration: none;
}
</style>
