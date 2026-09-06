<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import ProductCard from '@/components/products/ProductCard.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getProducts } from '@/services/products'
import type { ProductListItem } from '@/types/product'

const products = ref<ProductListItem[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

const featuredProducts = computed(() => {
  const certified = products.value.filter((product) => product.star >= 4)
  return (certified.length ? certified : products.value).slice(0, 4)
})

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
    <div class="section-heading">
      <div>
        <span class="eyebrow">★ Chất Lượng Xuất Sắc</span>
        <h2 id="featured-title">Sản Phẩm OCOP Nổi Bật 4 - 5 Sao</h2>
      </div>
      <RouterLink :to="{ name: 'products', query: { sort: 'rating' } }">
        Tất cả sản phẩm <span aria-hidden="true">→</span>
      </RouterLink>
    </div>

    <div v-if="isLoading" class="product-grid" aria-label="Đang tải sản phẩm">
      <div v-for="index in 4" :key="index" class="product-skeleton placeholder-glow">
        <span class="placeholder media-placeholder" />
        <span class="placeholder col-7 mt-3" />
        <span class="placeholder col-10 mt-3" />
        <span class="placeholder col-5 mt-3" />
      </div>
    </div>

    <div v-else-if="featuredProducts.length" class="product-grid">
      <ProductCard v-for="product in featuredProducts" :key="product.id" :product="product" />
    </div>

    <div v-else class="featured-empty" role="status">
      <strong>{{ errorMessage || 'Chưa có sản phẩm nổi bật.' }}</strong>
      <p>Sản phẩm 4–5 sao đã được duyệt sẽ xuất hiện tại đây.</p>
      <button v-if="errorMessage" type="button" @click="loadProducts">Thử lại</button>
    </div>
  </section>
</template>

<style scoped>
.featured-section {
  padding-top: 48px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  display: block;
  margin-bottom: 4px;
  color: #c2410c;
  font-size: 11px;
  font-weight: 800;
  line-height: 16px;
  text-transform: uppercase;
}

.section-heading h2 {
  margin: 0;
  color: var(--ocop-navy);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.section-heading > a {
  flex: 0 0 auto;
  color: var(--ocop-primary-700);
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.product-grid {
  display: grid;
  margin-top: 16px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.product-skeleton {
  min-height: 410px;
  padding: 12px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: #fff;
}

.product-skeleton .placeholder {
  display: block;
}

.media-placeholder {
  width: 100%;
  height: 196px;
  border-radius: var(--ocop-radius-md);
}

.featured-empty {
  margin-top: 16px;
  padding: 44px 20px;
  border: 1px dashed var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: #fff;
  color: var(--ocop-slate);
  text-align: center;
}

.featured-empty strong {
  display: block;
  color: var(--ocop-navy);
}

.featured-empty p {
  margin: 6px 0 0;
  font-size: 12px;
}

.featured-empty button {
  margin-top: 12px;
  padding: 7px 14px;
  border: 1px solid var(--ocop-primary-700);
  border-radius: var(--ocop-radius-sm);
  background: #fff;
  color: var(--ocop-primary-700);
  font-size: 12px;
  font-weight: 700;
}

@media (max-width: 991.98px) {
  .product-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 575.98px) {
  .section-heading {
    align-items: flex-start;
  }

  .product-grid {
    grid-template-columns: 1fr;
  }
}
</style>
