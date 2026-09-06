<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import { getApiErrorMessage } from '@/services/api-error'
import { getProduct } from '@/services/products'
import type { ProductDetail } from '@/types/product'

const route = useRoute()

const product = ref<ProductDetail | null>(null)
const selectedImageUrl = ref<string | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')

const formattedPrice = computed(() => {
  if (!product.value) return ''
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(product.value.price)
})

const activeImage = computed(
  () => selectedImageUrl.value || product.value?.primary_image_url || null,
)

async function loadProduct(slug: string): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  product.value = null
  selectedImageUrl.value = null
  try {
    product.value = await getProduct(slug)
    selectedImageUrl.value = product.value.images[0]?.image_url ?? null
    document.title = `${product.value.name} | OCOP Lâm Đồng`
  } catch (error) {
    errorMessage.value = getApiErrorMessage(
      error,
      'Không thể tải thông tin sản phẩm. Vui lòng thử lại.',
    )
  } finally {
    isLoading.value = false
  }
}

watch(
  () => route.params.slug,
  (slug) => {
    if (typeof slug === 'string') void loadProduct(slug)
  },
  { immediate: true },
)

onUnmounted(() => {
  document.title = 'OCOP Lâm Đồng'
})
</script>

<template>
  <main class="detail-page">
    <div class="container py-4 py-lg-5">
      <nav class="breadcrumb-nav mb-4" aria-label="Đường dẫn">
        <RouterLink to="/">Trang chủ</RouterLink>
        <span>/</span>
        <RouterLink to="/san-pham">Sản phẩm</RouterLink>
        <template v-if="product">
          <span>/</span>
          <span aria-current="page">{{ product.name }}</span>
        </template>
      </nav>

      <div v-if="isLoading" class="detail-loading placeholder-glow">
        <span class="placeholder media-loading" />
        <div>
          <span class="placeholder col-4" />
          <span class="placeholder col-10 mt-4" />
          <span class="placeholder col-7 mt-3" />
          <span class="placeholder col-5 mt-5" />
        </div>
      </div>

      <section v-else-if="errorMessage" class="error-state">
        <span class="error-symbol">!</span>
        <h1>Không tìm thấy sản phẩm</h1>
        <p>{{ errorMessage }}</p>
        <RouterLink class="btn btn-success" to="/san-pham">
          Quay lại danh sách
        </RouterLink>
      </section>

      <template v-else-if="product">
        <section class="product-overview">
          <div class="gallery">
            <div class="main-image">
              <img v-if="activeImage" :src="activeImage" :alt="product.name" />
              <div v-else class="image-placeholder" aria-hidden="true">OCOP</div>
            </div>
            <div v-if="product.images.length > 1" class="thumbnail-list" aria-label="Ảnh sản phẩm">
              <button
                v-for="image in product.images"
                :key="image.id"
                class="thumbnail"
                :class="{ active: activeImage === image.image_url }"
                type="button"
                @click="selectedImageUrl = image.image_url"
              >
                <img :src="image.image_url" :alt="`Ảnh ${product.name}`" />
              </button>
            </div>
          </div>

          <div class="product-info">
            <div class="badge-row">
              <RouterLink
                class="category-badge"
                :to="{ name: 'products', query: { category: product.category.slug } }"
              >
                {{ product.category.name }}
              </RouterLink>
              <span class="ocop-badge">{{ product.star }} sao OCOP</span>
            </div>

            <h1>{{ product.name }}</h1>
            <div class="rating-row">
              <span>★ {{ product.rating_avg.toFixed(1) }}</span>
              <span>{{ product.views }} lượt xem</span>
            </div>
            <p class="lead-description">{{ product.description }}</p>

            <div class="price-box">
              <strong>{{ formattedPrice }}</strong>
              <span>/ {{ product.unit }}</span>
            </div>

            <dl class="certification-list">
              <div v-if="product.cert_code">
                <dt>Mã chứng nhận OCOP</dt>
                <dd>{{ product.cert_code }}</dd>
              </div>
              <div v-if="product.cert_year">
                <dt>Năm chứng nhận</dt>
                <dd>{{ product.cert_year }}</dd>
              </div>
              <div v-if="product.vietgap_code">
                <dt>Mã VietGAP</dt>
                <dd>{{ product.vietgap_code }}</dd>
              </div>
            </dl>

            <aside class="subject-card">
              <span>Chủ thể sản xuất</span>
              <strong>{{ product.subject.name }}</strong>
              <small>{{ product.subject.district }}, Lâm Đồng</small>
            </aside>
          </div>
        </section>

        <section class="content-section">
          <div v-if="product.story" class="content-block story-block">
            <span class="section-eyebrow">Câu chuyện sản phẩm</span>
            <h2>Nguồn gốc và giá trị bản địa</h2>
            <p>{{ product.story }}</p>
          </div>

          <div class="detail-columns">
            <article v-if="product.ingredients" class="content-block">
              <h2>Thành phần</h2>
              <p>{{ product.ingredients }}</p>
            </article>
            <article v-if="product.usage_instructions" class="content-block">
              <h2>Hướng dẫn sử dụng</h2>
              <p>{{ product.usage_instructions }}</p>
            </article>
          </div>
        </section>
      </template>
    </div>
  </main>
</template>

<style scoped>
.detail-page {
  min-height: calc(100vh - 4.5rem);
  background: #f7f8f4;
}

.breadcrumb-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  color: #768078;
  font-size: 0.86rem;
}

.breadcrumb-nav a {
  color: #3f724a;
  text-decoration: none;
}

.product-overview,
.detail-loading {
  display: grid;
  gap: 2.5rem;
}

.main-image {
  overflow: hidden;
  aspect-ratio: 1 / 0.78;
  border-radius: 1.4rem;
  background: #e6efdf;
}

.main-image img,
.image-placeholder {
  width: 100%;
  height: 100%;
}

.main-image img {
  object-fit: cover;
}

.image-placeholder {
  display: grid;
  place-items: center;
  background:
    radial-gradient(circle at 68% 25%, rgb(222 236 186 / 90%), transparent 12rem),
    linear-gradient(145deg, #edf4e5, #cbdcbc);
  color: #2f6f3e;
  font-size: 1.6rem;
  font-weight: 800;
  letter-spacing: 0.2em;
}

.thumbnail-list {
  display: flex;
  gap: 0.75rem;
  margin-top: 0.85rem;
  overflow-x: auto;
}

.thumbnail {
  width: 4.5rem;
  height: 4.5rem;
  flex: 0 0 auto;
  overflow: hidden;
  padding: 0;
  border: 2px solid transparent;
  border-radius: 0.75rem;
  background: #fff;
}

.thumbnail.active {
  border-color: #2f6f3e;
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.badge-row,
.rating-row {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 0.75rem;
}

.category-badge,
.ocop-badge {
  padding: 0.4rem 0.7rem;
  border-radius: 999px;
  font-size: 0.76rem;
  font-weight: 750;
  text-decoration: none;
}

.category-badge {
  background: #e6f1de;
  color: #2f6f3e;
}

.ocop-badge {
  background: #fff2c0;
  color: #835f05;
}

.product-info h1 {
  margin: 1rem 0;
  color: #172d1d;
  font-size: clamp(2.1rem, 5vw, 3.6rem);
  font-weight: 800;
  line-height: 1.08;
}

.rating-row {
  color: #778078;
  font-size: 0.9rem;
}

.rating-row span:first-child {
  color: #936e0b;
  font-weight: 750;
}

.lead-description {
  margin: 1.4rem 0;
  color: #5f6d62;
  font-size: 1.03rem;
  line-height: 1.75;
}

.price-box {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  padding: 1rem 1.2rem;
  border-radius: 0.9rem;
  background: #edf4e5;
}

.price-box strong {
  color: #2f6f3e;
  font-size: 1.7rem;
}

.price-box span {
  color: #69746c;
}

.certification-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: 0.75rem;
  margin: 1.25rem 0;
}

.certification-list div {
  padding: 0.75rem;
  border: 1px solid #e0e7dd;
  border-radius: 0.75rem;
  background: #fff;
}

.certification-list dt {
  color: #7b847d;
  font-size: 0.72rem;
  font-weight: 600;
}

.certification-list dd {
  margin: 0.25rem 0 0;
  color: #263b2b;
  font-size: 0.9rem;
  font-weight: 700;
}

.subject-card {
  display: grid;
  padding: 1rem 1.15rem;
  border-left: 3px solid #2f6f3e;
  background: #fff;
}

.subject-card span,
.subject-card small {
  color: #778078;
  font-size: 0.8rem;
}

.subject-card strong {
  margin: 0.25rem 0;
  color: #233a29;
}

.content-section {
  display: grid;
  gap: 1.25rem;
  margin-top: 3rem;
}

.content-block {
  padding: clamp(1.4rem, 4vw, 2.25rem);
  border: 1px solid rgb(29 72 39 / 10%);
  border-radius: 1.1rem;
  background: #fff;
}

.content-block h2 {
  margin-bottom: 0.8rem;
  color: #213b28;
  font-size: 1.35rem;
}

.content-block p {
  margin: 0;
  color: #626f65;
  line-height: 1.8;
  white-space: pre-line;
}

.story-block h2 {
  margin: 0.5rem 0 1rem;
  font-size: clamp(1.6rem, 4vw, 2.3rem);
}

.section-eyebrow {
  color: #2f6f3e;
  font-size: 0.75rem;
  font-weight: 750;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}

.detail-columns {
  display: grid;
  gap: 1.25rem;
}

.detail-loading {
  grid-template-columns: 1fr;
}

.media-loading {
  display: block;
  min-height: 26rem;
  border-radius: 1.4rem;
}

.error-state {
  padding: 5rem 1rem;
  text-align: center;
}

.error-symbol {
  display: grid;
  width: 3.5rem;
  height: 3.5rem;
  margin: 0 auto 1rem;
  place-items: center;
  border-radius: 50%;
  background: #fbe3df;
  color: #a63e31;
  font-size: 1.4rem;
  font-weight: 800;
}

.error-state p {
  color: #69736b;
}

@media (min-width: 768px) {
  .detail-columns {
    grid-template-columns: 1fr 1fr;
  }
}

@media (min-width: 992px) {
  .product-overview,
  .detail-loading {
    grid-template-columns: minmax(0, 1.05fr) minmax(22rem, 0.95fr);
    align-items: start;
  }
}
</style>
