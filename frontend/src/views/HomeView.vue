<script setup lang="ts">
import { onMounted, ref } from 'vue'

import HomeHero from '@/components/home/HomeHero.vue'
import ProductCard from '@/components/products/ProductCard.vue'
import { getProducts } from '@/services/products'
import type { ProductListItem } from '@/types/product'

const featuredProducts = ref<ProductListItem[]>([])
const isLoadingProducts = ref(true)
const productLoadFailed = ref(false)

onMounted(async () => {
  try {
    const response = await getProducts({ page: 1, page_size: 4, sort: 'rating' })
    featuredProducts.value = response.items
  } catch {
    productLoadFailed.value = true
  } finally {
    isLoadingProducts.value = false
  }
})
</script>

<template>
  <main>
    <div class="site-content home-hero-wrap">
      <HomeHero />
    </div>

    <section id="san-pham" class="container py-5 py-lg-6">
      <div class="section-heading">
        <div>
          <span class="section-label">Được cộng đồng yêu thích</span>
          <h2 class="mt-2 mb-1">Sản phẩm OCOP nổi bật</h2>
          <p class="mb-0 text-secondary section-copy">
            Những sản phẩm tiêu biểu đã được kiểm duyệt trên hệ thống.
          </p>
        </div>
        <RouterLink class="btn btn-outline-success" to="/san-pham">
          Xem tất cả sản phẩm
        </RouterLink>
      </div>

      <div v-if="isLoadingProducts" class="featured-grid placeholder-glow mt-4">
        <div v-for="index in 4" :key="index" class="featured-placeholder">
          <span class="placeholder col-12 h-100" />
        </div>
      </div>
      <div v-else-if="featuredProducts.length" class="featured-grid mt-4">
        <ProductCard
          v-for="product in featuredProducts"
          :key="product.id"
          :product="product"
        />
      </div>
      <div v-else class="featured-empty mt-4">
        <strong>
          {{ productLoadFailed ? 'Chưa thể kết nối dữ liệu sản phẩm' : 'Chưa có sản phẩm nổi bật' }}
        </strong>
        <p class="mb-0">
          {{
            productLoadFailed
              ? 'Hãy kiểm tra backend hoặc thử lại sau.'
              : 'Sản phẩm đã duyệt sẽ xuất hiện tại đây.'
          }}
        </p>
      </div>
    </section>

    <section id="dia-diem" class="placeholder-band py-5 text-center">
      <div class="container">
        <span class="section-label">Bản đồ số</span>
        <h2 class="mt-2">Điểm đến nông nghiệp Lâm Đồng</h2>
      </div>
    </section>
  </main>
</template>

<style scoped>
.home-hero-wrap {
  padding-top: 24px;
}

.hero-section {
  padding: clamp(4.5rem, 10vw, 8rem) 0;
  background:
    radial-gradient(circle at 78% 30%, rgb(197 222 159 / 70%), transparent 27rem),
    linear-gradient(145deg, #f8faf2, #edf4e5);
}

.hero-grid {
  display: grid;
  align-items: center;
  gap: 3rem;
}

.hero-eyebrow,
.section-label {
  color: #2f6f3e;
  font-size: 0.78rem;
  font-weight: 750;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.hero-section h1 {
  max-width: 47rem;
  margin: 1rem 0 1.25rem;
  color: #18351f;
  font-family: "Segoe UI", Arial, sans-serif;
  font-weight: 800;
  font-size: clamp(2.6rem, 7vw, 5.2rem);
  line-height: 1.02;
}

.hero-section > .container > div > p {
  max-width: 42rem;
  color: #5f6f63;
  font-size: 1.08rem;
  line-height: 1.75;
}

.hero-panel {
  display: grid;
  min-height: 24rem;
  align-content: end;
  padding: 2rem;
  border-radius: 1.5rem;
  background: linear-gradient(160deg, #173a22, #3d7a49);
  color: #fff;
  box-shadow: 0 1.5rem 3.5rem rgb(31 76 40 / 18%);
}

.hero-panel strong {
  max-width: 25rem;
  margin: 1rem 0;
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: clamp(1.8rem, 4vw, 2.6rem);
  line-height: 1.15;
}

.hero-panel p {
  margin: 0;
  color: rgb(255 255 255 / 72%);
}

.panel-badge {
  width: max-content;
  padding: 0.4rem 0.8rem;
  border: 1px solid rgb(255 255 255 / 35%);
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.section-copy {
  max-width: 42rem;
}

.py-lg-6 {
  padding-top: 5rem;
  padding-bottom: 5rem;
}

.section-heading {
  display: flex;
  flex-wrap: wrap;
  align-items: end;
  justify-content: space-between;
  gap: 1.25rem;
}

.section-heading h2,
.placeholder-band h2 {
  color: #18351f;
  font-size: clamp(1.8rem, 4vw, 2.65rem);
  font-weight: 800;
}

.featured-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(min(100%, 15rem), 1fr));
  gap: 1.25rem;
}

.featured-placeholder {
  height: 28rem;
  overflow: hidden;
  border-radius: 1.15rem;
  background: #e4e9e1;
}

.featured-empty {
  padding: 3.5rem 1rem;
  border: 1px dashed #bdc9ba;
  border-radius: 1rem;
  color: #6a746c;
  text-align: center;
}

.featured-empty strong {
  display: block;
  margin-bottom: 0.4rem;
  color: #29432f;
}

.placeholder-band {
  background: #173a22;
  color: #fff;
}

.placeholder-band h2 {
  color: #fff;
}

@media (min-width: 992px) {
  .hero-grid {
    grid-template-columns: 1.2fr 0.8fr;
  }
}
</style>
