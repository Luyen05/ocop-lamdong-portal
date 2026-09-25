<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import ProductCard from '@/components/products/ProductCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getProducts } from '@/services/products'
import type { ProductListItem } from '@/types/product'

const products = ref<ProductListItem[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

const featuredProducts = computed(() => {
  const certified = products.value.filter((product) => product.star >= 4)
  return (certified.length ? certified : products.value).slice(0, 8)
})

// Tiêu đề trung thực: chỉ ghi "4–5 sao" khi mọi thẻ đang hiện đều đạt 4 sao trở lên.
const isAllCertified = computed(() =>
  featuredProducts.value.length > 0 && featuredProducts.value.every((product) => product.star >= 4),
)

async function loadProducts(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await getProducts({ page: 1, page_size: 8, sort: 'rating' })
    products.value = response.items
  } catch (error) {
    products.value = []
    errorMessage.value = getApiErrorMessage(error, 'Chưa thể kết nối dữ liệu sản phẩm.')
  } finally {
    isLoading.value = false
  }
}

onMounted(loadProducts)
</script>

<template>
  <section id="san-pham-noi-bat" class="featured-section" aria-labelledby="featured-title">
    <div class="ocop-section-head">
      <div>
        <p class="ocop-eyebrow"><AppIcon name="star" :size="13" /> {{ isAllCertified ? 'Được đánh giá cao' : 'Đã được công nhận' }}</p>
        <h2 id="featured-title" class="ocop-section-title">
          {{ isAllCertified ? 'Sản phẩm OCOP nổi bật 4–5 sao' : 'Sản phẩm OCOP tiêu biểu' }}
        </h2>
      </div>
      <RouterLink class="ocop-link-more" :to="{ name: 'products', query: { sort: 'rating' } }">
        Tất cả sản phẩm <AppIcon name="chevronRight" :size="16" />
      </RouterLink>
    </div>

    <div v-if="isLoading" class="product-grid" aria-busy="true" aria-label="Đang tải sản phẩm">
      <div v-for="index in 8" :key="index" class="product-skeleton placeholder-glow">
        <span class="placeholder media-placeholder" />
        <span class="skeleton-copy">
          <span class="placeholder col-6" />
          <span class="placeholder col-10" />
          <span class="placeholder col-8" />
          <span class="placeholder col-5" />
        </span>
      </div>
    </div>

    <div v-else-if="featuredProducts.length" class="product-grid">
      <ProductCard v-for="product in featuredProducts" :key="product.id" :product="product" />
    </div>

    <div v-else class="featured-empty" :class="{ 'is-error': errorMessage }" :role="errorMessage ? 'alert' : 'status'">
      <span class="state-icon" aria-hidden="true"><AppIcon :name="errorMessage ? 'refresh' : 'star'" :size="22" /></span>
      <div class="state-copy">
        <strong>{{ errorMessage || 'Chưa có sản phẩm nổi bật.' }}</strong>
        <p>Sản phẩm 4–5 sao đã được duyệt sẽ xuất hiện tại đây.</p>
      </div>
      <button v-if="errorMessage" class="ocop-btn-main" type="button" @click="loadProducts">
        <AppIcon name="refresh" :size="16" /> Thử lại
      </button>
    </div>
  </section>
</template>

<style scoped>
.featured-section {
  padding-top: var(--ocop-space-12);
}

.product-grid {
  display: grid;
  margin-top: var(--ocop-space-5);
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--ocop-space-6);
}

.product-skeleton {
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.product-skeleton .placeholder {
  display: block;
}

.media-placeholder {
  width: 100%;
  aspect-ratio: 1.4 / 1;
}

.skeleton-copy {
  display: grid;
  padding: var(--ocop-space-4);
  gap: var(--ocop-space-3);
}

.featured-empty {
  display: flex;
  margin-top: var(--ocop-space-5);
  padding: var(--ocop-space-6);
  align-items: center;
  gap: var(--ocop-space-5);
  border: 1px dashed var(--ocop-border-strong);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
  color: var(--ocop-slate);
}

.featured-empty.is-error {
  border: 1px solid var(--ocop-danger-border);
  background: var(--ocop-danger-soft);
}

.state-icon {
  display: grid;
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-mist-100);
  color: var(--ocop-primary-700);
}

.is-error .state-icon {
  background: var(--ocop-card);
  color: var(--ocop-danger-strong);
}

.state-copy {
  flex: 1;
}

.featured-empty strong {
  display: block;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-body-lg);
}

.is-error strong {
  color: var(--ocop-danger-strong);
}

.featured-empty p {
  margin: var(--ocop-space-1) 0 0;
  font-size: var(--ocop-font-size-body);
}

@media (max-width: 991.98px) {
  .product-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--ocop-space-4);
  }
}

@media (max-width: 575.98px) {
  .featured-section {
    padding-top: var(--ocop-space-8);
  }

  .product-grid {
    margin-top: var(--ocop-space-4);
    gap: var(--ocop-space-3);
  }

  .featured-empty {
    flex-direction: column;
    align-items: stretch;
    text-align: left;
  }
}
</style>
