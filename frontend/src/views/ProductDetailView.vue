<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

import ProductCard from '@/components/products/ProductCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getProduct, getProducts } from '@/services/products'
import type { ProductDetail, ProductListItem } from '@/types/product'

const route = useRoute()

const product = ref<ProductDetail | null>(null)
const selectedImageUrl = ref<string | null>(null)
const activeImageFailed = ref(false)
const relatedProducts = ref<ProductListItem[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const errorTitle = ref('Không thể tải sản phẩm')

const formattedPrice = computed(() => {
  if (!product.value) return ''
  if (product.value.price === null || product.value.price <= 0) return 'Liên hệ'
  return new Intl.NumberFormat('vi-VN', {
    style: 'currency',
    currency: 'VND',
    maximumFractionDigits: 0,
  }).format(product.value.price)
})

const activeImage = computed(
  () => selectedImageUrl.value || product.value?.primary_image_url || null,
)

function formatDate(value: string | null): string {
  if (!value) return 'Chưa cập nhật'
  return new Intl.DateTimeFormat('vi-VN').format(new Date(`${value}T00:00:00`))
}

function selectImage(imageUrl: string): void {
  selectedImageUrl.value = imageUrl
  activeImageFailed.value = false
}

async function loadProduct(slug: string): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  product.value = null
  selectedImageUrl.value = null
  activeImageFailed.value = false
  relatedProducts.value = []
  try {
    product.value = await getProduct(slug)
    selectedImageUrl.value = product.value.images[0]?.image_url ?? null
    document.title = `${product.value.name} | OCOP Lâm Đồng`

    try {
      const related = await getProducts({
        page: 1,
        page_size: 4,
        category: product.value.category.slug,
        sort: 'newest',
      })
      relatedProducts.value = related.items
        .filter((item) => item.id !== product.value?.id)
        .slice(0, 3)
    } catch {
      relatedProducts.value = []
    }
  } catch (error) {
    errorTitle.value = axios.isAxiosError(error) && error.response?.status === 404
      ? 'Không tìm thấy sản phẩm'
      : 'Không thể tải sản phẩm'
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
        <h1>{{ errorTitle }}</h1>
        <p>{{ errorMessage }}</p>
        <RouterLink class="btn btn-success" to="/san-pham">
          Quay lại danh sách
        </RouterLink>
      </section>

      <template v-else-if="product">
        <section class="product-overview">
          <div class="gallery">
            <div class="main-image">
              <img
                v-if="activeImage && !activeImageFailed"
                :src="activeImage"
                :alt="product.name"
                @error="activeImageFailed = true"
              />
              <div v-else class="image-placeholder" aria-hidden="true">OCOP</div>
            </div>
            <div v-if="product.images.length > 1" class="thumbnail-list" aria-label="Ảnh sản phẩm">
              <button
                v-for="image in product.images"
                :key="image.id"
                class="thumbnail"
                :class="{ active: activeImage === image.image_url }"
                type="button"
                @click="selectImage(image.image_url)"
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
            <div v-if="product.rating_avg > 0 || product.views > 0" class="rating-row">
              <span v-if="product.rating_avg > 0"><AppIcon name="star" :size="14" /> {{ product.rating_avg.toFixed(1) }}</span>
              <span v-if="product.views > 0">{{ product.views }} lượt xem</span>
            </div>
            <p class="lead-description">{{ product.description }}</p>

            <div class="price-box">
              <strong>{{ formattedPrice }}</strong>
              <span v-if="product.price !== null && product.price > 0 && product.unit">/ {{ product.unit }}</span>
            </div>

            <dl class="certification-list">
              <div>
                <dt>Số quyết định / chứng nhận</dt>
                <dd>{{ product.cert_code || 'Chưa cập nhật' }}</dd>
              </div>
              <div>
                <dt>Năm chứng nhận</dt>
                <dd>{{ product.cert_year || 'Chưa cập nhật' }}</dd>
              </div>
              <div>
                <dt>Ngày cấp</dt>
                <dd>{{ formatDate(product.cert_issued_at) }}</dd>
              </div>
              <div>
                <dt>Hiệu lực đến</dt>
                <dd>{{ formatDate(product.cert_expires_at) }}</dd>
              </div>
              <div class="certification-authority">
                <dt>Cơ quan công nhận</dt>
                <dd>{{ product.issuing_authority || 'Chưa cập nhật' }}</dd>
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

          <article v-if="product.recognition_sources.length" class="content-block source-block">
            <span class="section-eyebrow">Nguồn đối chiếu công khai</span>
            <h2>Văn bản và nguồn công nhận</h2>
            <ul>
              <li v-for="source in product.recognition_sources" :key="source.id">
                <div>
                  <strong>{{ source.title }}</strong>
                  <span>
                    {{ source.verification_level === 'A' ? 'Văn bản chính thức' : 'Cổng thông tin cơ quan nhà nước' }}
                    <template v-if="source.issuing_body"> · {{ source.issuing_body }}</template>
                    <template v-if="source.document_number"> · {{ source.document_number }}</template>
                    <template v-if="source.published_at"> · {{ formatDate(source.published_at) }}</template>
                  </span>
                </div>
                <a :href="source.source_url" target="_blank" rel="noopener noreferrer">
                  Mở nguồn
                </a>
              </li>
            </ul>
          </article>
        </section>

        <section v-if="relatedProducts.length" class="related-section" aria-labelledby="related-title">
          <div class="related-heading">
            <div>
              <span class="section-eyebrow">Có thể bạn quan tâm</span>
              <h2 id="related-title">Sản phẩm cùng danh mục</h2>
            </div>
            <RouterLink :to="{ name: 'products', query: { category: product.category.slug } }">
              Xem tất cả
            </RouterLink>
          </div>
          <div class="related-grid">
            <ProductCard v-for="item in relatedProducts" :key="item.id" :product="item" />
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
  color: var(--ocop-primary-700);
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
  border-color: var(--ocop-primary-700);
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
  color: var(--ocop-primary-700);
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
  color: var(--ocop-primary-700);
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

.certification-list .certification-authority {
  grid-column: 1 / -1;
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
  border-left: 3px solid var(--ocop-primary-700);
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

.source-block ul {
  display: grid;
  margin: 1.25rem 0 0;
  padding: 0;
  gap: 0.75rem;
  list-style: none;
}

.source-block li {
  display: flex;
  padding: 0.9rem 1rem;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border: 1px solid #e0e7dd;
  border-radius: 0.8rem;
  background: #f8faf7;
}

.source-block li div { display: grid; gap: 0.25rem; }
.source-block li span { color: #718075; font-size: 0.78rem; }
.source-block li a { flex: 0 0 auto; color: var(--ocop-primary-700); font-size: 0.82rem; font-weight: 750; }

.related-section { margin-top: 3.5rem; }
.related-heading { display: flex; margin-bottom: 1.25rem; align-items: end; justify-content: space-between; gap: 1rem; }
.related-heading h2 { margin: 0.35rem 0 0; color: #213b28; font-size: clamp(1.5rem, 4vw, 2rem); }
.related-heading > a { color: var(--ocop-primary-700); font-size: 0.85rem; font-weight: 750; }
.related-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.25rem; }

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
  color: var(--ocop-primary-700);
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

@media (max-width: 767.98px) {
  .source-block li { align-items: flex-start; flex-direction: column; }
  .related-grid { grid-template-columns: 1fr; }
}

@media (min-width: 768px) and (max-width: 991.98px) {
  .related-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); }
}

@media (min-width: 992px) {
  .product-overview,
  .detail-loading {
    grid-template-columns: minmax(0, 1.05fr) minmax(22rem, 0.95fr);
    align-items: start;
  }
}
</style>
