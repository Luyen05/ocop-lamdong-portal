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

// Ảnh "dữ liệu tham khảo" dùng chung cho mọi sản phẩm chưa có ảnh thật: thay bằng khung giữ chỗ
// riêng cho từng sản phẩm để các thẻ không giống hệt nhau, vẫn ghi rõ là chưa có ảnh.
const isReferenceImage = computed(() => props.product.primary_image_url?.includes('/public-reference') ?? false)
const showImage = computed(() => Boolean(props.product.primary_image_url) && !imageFailed.value && !isReferenceImage.value)
const placeholderTones = [
  ['var(--ocop-tone-leaf-soft)', 'var(--ocop-tone-leaf)'],
  ['var(--ocop-daquy-50)', 'var(--ocop-daquy-700)'],
  ['var(--ocop-mist-100)', 'var(--ocop-mist-700)'],
  ['var(--ocop-tone-rose-soft)', 'var(--ocop-tone-rose)'],
  ['var(--ocop-tone-clay-soft)', 'var(--ocop-tone-clay)'],
]
const placeholderStyle = computed(() => {
  const [background, foreground] = placeholderTones[props.product.category.id % placeholderTones.length]
  return { '--placeholder-bg': background, '--placeholder-fg': foreground }
})
const hasPrice = computed(() => props.product.price !== null && props.product.price > 0)

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
          v-if="showImage"
          :src="product.primary_image_url ?? undefined"
          :alt="product.name"
          loading="lazy"
          @error="imageFailed = true"
        />
        <div v-else class="product-placeholder" :style="placeholderStyle">
          <span class="placeholder-mark" aria-hidden="true">{{ product.name.trim().charAt(0).toUpperCase() }}</span>
          <span class="placeholder-note">Ảnh sản phẩm đang cập nhật</span>
        </div>
        <span class="star-badge">
          <span class="stars" aria-hidden="true">
            <AppIcon v-for="index in product.star" :key="index" name="star" :size="11" />
          </span>
          OCOP {{ product.star }} sao
        </span>
      </div>

      <div class="product-body">
        <span class="product-location"><AppIcon name="map-pin" :size="14" /> {{ product.subject.district }}</span>
        <h2>{{ product.name }}</h2>
        <p class="product-meta">
          {{ product.category.name }}
          <span v-if="product.vietgap_code"><AppIcon name="checkCircle" :size="12" /> VietGAP</span>
        </p>

        <p class="product-subject" :title="product.subject.name">
          <AppIcon name="building" :size="13" />
          <span>{{ product.subject.name }}</span>
        </p>

        <div class="product-price-row">
          <div class="product-price" :class="{ 'is-contact': !hasPrice }">
            <strong>{{ hasPrice ? formattedPrice : 'Giá: Liên hệ' }}</strong>
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
  container-type: inline-size;
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
  aspect-ratio: 16 / 10;
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
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-2);
  background:
    radial-gradient(circle at 80% 20%, color-mix(in srgb, var(--ocop-white) 70%, transparent), transparent 45%),
    var(--placeholder-bg, var(--ocop-mist-100));
  text-align: center;
}

.product-placeholder .placeholder-mark {
  display: grid;
  width: 56px;
  height: 56px;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-sm);
  color: var(--placeholder-fg, var(--ocop-mist-800));
  font-size: var(--ocop-font-size-title-md);
  font-weight: 800;
}

.product-placeholder .placeholder-note {
  color: var(--ocop-mist-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 600;
}

/* Huy hiệu sao OCOP (audit G-03): nền xanh đêm, sao vàng dã quỳ, chữ trắng. Chữ 16:1, sao 10:1. */
.star-badge {
  position: absolute;
  z-index: 1;
  top: var(--ocop-space-3);
  left: var(--ocop-space-3);
  display: inline-flex;
  min-height: 28px;
  align-items: center;
  gap: var(--ocop-space-1);
  padding: 0 var(--ocop-space-3);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mist-950);
  box-shadow: 0 3px 8px color-mix(in srgb, var(--ocop-mist-950) 24%, transparent);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  line-height: 1;
  white-space: nowrap;
}

.stars {
  display: inline-flex;
  gap: 1px;
  color: var(--ocop-daquy-400);
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
  display: flex;
  min-width: 0;
  margin: auto 0 0;
  padding-top: var(--ocop-space-3);
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-text-muted);
  font-size: var(--ocop-font-size-caption);
  font-weight: 600;
}

.product-subject span {
  overflow: hidden;
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

.product-price.is-contact strong {
  color: var(--ocop-text-muted);
  font-size: var(--ocop-font-size-body);
  font-weight: 600;
}

.product-price small {
  overflow: hidden;
  color: var(--ocop-text-tertiary);
  font-size: var(--ocop-font-size-caption);
  text-overflow: ellipsis;
  white-space: nowrap;
}

.product-rating {
  display: inline-flex;
  flex: 0 0 auto;
  align-items: center;
  gap: 2px;
  color: var(--ocop-daquy-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.product-rating :deep(.app-icon) {
  color: var(--ocop-daquy-500);
}

/* Thẻ hẹp (lưới 2 cột trên điện thoại): thu gọn chữ và khoảng cách. */
@container (max-width: 220px) {
  .product-body {
    min-height: 0;
    padding: var(--ocop-space-3);
  }

  .product-body h2 {
    min-height: 0;
    font-size: var(--ocop-font-size-body);
  }

  .star-badge {
    top: var(--ocop-space-2);
    left: var(--ocop-space-2);
    padding: 0 var(--ocop-space-2);
  }

  .stars {
    display: none;
  }

  .product-price strong {
    font-size: var(--ocop-font-size-body);
  }
}

.product-card-link:focus-visible {
  border-radius: inherit;
  outline: 3px solid color-mix(in srgb, var(--ocop-primary-500) 28%, transparent);
  outline-offset: -3px;
}
</style>
