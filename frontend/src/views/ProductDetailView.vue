<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import axios from 'axios'

import PresentationGallery from '@/components/products/PresentationGallery.vue'
import ProductCard from '@/components/products/ProductCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getProduct, getProducts } from '@/services/products'
import type { ProductDetail, ProductListItem } from '@/types/product'

const route = useRoute()

const product = ref<ProductDetail | null>(null)
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

function formatDate(value: string | null): string {
  if (!value) return 'Chưa cập nhật'
  return new Intl.DateTimeFormat('vi-VN').format(new Date(`${value}T00:00:00`))
}

let latestRequestId = 0

async function loadProduct(slug: string): Promise<void> {
  const requestId = ++latestRequestId
  isLoading.value = true
  errorMessage.value = ''
  product.value = null
  relatedProducts.value = []
  try {
    const loadedProduct = await getProduct(slug)
    if (requestId !== latestRequestId) return
    product.value = loadedProduct
    document.title = `${product.value.name} | OCOP Lâm Đồng`

    try {
      const related = await getProducts({
        page: 1,
        page_size: 4,
        category: product.value.category.slug,
        sort: 'newest',
      })
      if (requestId !== latestRequestId) return
      relatedProducts.value = related.items
        .filter((item) => item.id !== product.value?.id)
        .slice(0, 3)
    } catch {
      if (requestId !== latestRequestId) return
      relatedProducts.value = []
    }
  } catch (error) {
    if (requestId !== latestRequestId) return
    errorTitle.value = axios.isAxiosError(error) && error.response?.status === 404
      ? 'Không tìm thấy sản phẩm'
      : 'Không thể tải sản phẩm'
    errorMessage.value = getApiErrorMessage(
      error,
      'Không thể tải thông tin sản phẩm. Vui lòng thử lại.',
    )
  } finally {
    if (requestId === latestRequestId) isLoading.value = false
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
  latestRequestId++
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
          <PresentationGallery :images="product.images" :primary-url="product.primary_image_url" :name="product.name" />

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
            <p class="product-producer">{{ product.subject.name }} · {{ product.subject.district }}, Lâm Đồng</p>
            <div v-if="product.rating_avg > 0 || product.views > 0" class="rating-row">
              <span v-if="product.rating_avg > 0"><AppIcon name="star" :size="14" /> {{ product.rating_avg.toFixed(1) }}</span>
              <span v-if="product.views > 0">{{ product.views }} lượt xem</span>
            </div>
            <p class="lead-description">{{ product.description }}</p>

            <div class="price-box">
              <strong>{{ formattedPrice }}</strong>
              <span v-if="product.price !== null && product.price > 0 && product.unit">/ {{ product.unit }}</span>
            </div>

            <RouterLink
              class="btn btn-success my-3"
              data-test="experience-cta"
              :to="{ name: 'product-experience', params: { slug: product.slug } }"
            >
              Tìm nơi mua &amp; trải nghiệm
            </RouterLink>
            <aside class="ocop-info" aria-labelledby="ocop-info-title">
              <h2 id="ocop-info-title">Thông tin OCOP</h2>
              <dl class="certification-list">
                <div v-if="product.cert_code"><dt>Số quyết định / chứng nhận</dt><dd>{{ product.cert_code }}</dd></div>
                <div v-if="product.cert_year"><dt>Năm chứng nhận</dt><dd>{{ product.cert_year }}</dd></div>
                <div v-if="product.cert_issued_at"><dt>Ngày cấp</dt><dd>{{ formatDate(product.cert_issued_at) }}</dd></div>
                <div v-if="product.cert_expires_at"><dt>Hiệu lực đến</dt><dd>{{ formatDate(product.cert_expires_at) }}</dd></div>
                <div v-if="product.issuing_authority" class="certification-authority"><dt>Cơ quan công nhận</dt><dd>{{ product.issuing_authority }}</dd></div>
                <div v-if="product.vietgap_code"><dt>Mã VietGAP</dt><dd>{{ product.vietgap_code }}</dd></div>
              </dl>
              <p v-if="!product.cert_code && !product.cert_year && !product.cert_issued_at && !product.cert_expires_at && !product.issuing_authority && !product.vietgap_code" class="metadata-note">Thông tin chứng nhận chi tiết đang cập nhật.</p>
            </aside>
          </div>
        </section>

        <section class="content-section">
          <div v-if="product.story" class="content-block story-block">
            <span class="section-eyebrow">Câu chuyện sản phẩm</span>
            <h2>Câu chuyện sản phẩm</h2>
            <p>{{ product.story }}</p>
          </div>

          <div class="detail-columns">
            <article v-if="product.ingredients" class="content-block">
              <h2>Nguồn gốc &amp; thành phần</h2>
              <p>{{ product.ingredients }}</p>
            </article>
            <article v-if="product.usage_instructions" class="content-block">
              <h2>Hướng dẫn sử dụng</h2>
              <p>{{ product.usage_instructions }}</p>
            </article>
          </div>



          <article class="content-block subject-card"><h2>Chủ thể sản xuất</h2><strong>{{ product.subject.name }}</strong><p>{{ product.subject.district }}, Lâm Đồng</p></article>

          <article v-if="product.recognition_sources.length" class="content-block source-block">
            <span class="section-eyebrow">Nguồn đối chiếu công khai</span>
            <h2>Nguồn thông tin &amp; minh chứng</h2>
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
          <article v-if="product.related_locations?.length" class="content-block location-block">
            <span class="section-eyebrow">Trải nghiệm tại điểm đến</span>
            <h2>Nơi mua &amp; trải nghiệm</h2>
            <ul>
              <li v-for="location in product.related_locations" :key="location.id">
                <div>
                  <strong>{{ location.name }}</strong>
                  <span>{{ location.type_label }} · {{ location.district }}</span>
                </div>
                <RouterLink :to="{ name: 'location-detail', params: { slug: location.slug } }">
                  Xem điểm đến
                </RouterLink>
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
.product-producer, .metadata-note { color: var(--ocop-text-secondary); }
.ocop-info { margin-top: 1rem; padding-top: 1rem; border-top: 1px solid var(--ocop-border); }
.ocop-info h2 { font-size: 1rem; font-weight: 750; }

.detail-page {
  min-height: calc(100vh - 4.5rem);
  background: var(--ocop-surface);
}

.breadcrumb-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  color: var(--ocop-text-secondary);
  font-size: 0.86rem;
}

.breadcrumb-nav a {
  color: var(--ocop-primary-700);
  text-decoration: none;
}

.product-overview,
.detail-loading {
  display: grid;
  gap: 2.5rem;
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
  border-radius: var(--ocop-radius-pill);
  font-size: 0.76rem;
  font-weight: 750;
  text-decoration: none;
}

.category-badge {
  background: var(--ocop-sage-50);
  color: var(--ocop-primary-700);
}

.ocop-badge {
  border: 1px solid var(--ocop-warning-strong);
  font-size: .95rem;
  background: var(--ocop-warning-surface);
  color: var(--ocop-warning-strong);
}

.product-info h1 {
  margin: 1rem 0;
  color: var(--ocop-text-primary);
  font-size: clamp(2.1rem, 5vw, 3.6rem);
  font-weight: 800;
  line-height: 1.08;
}

.rating-row {
  color: var(--ocop-text-secondary);
  font-size: 0.9rem;
}

.rating-row span:first-child {
  color: var(--ocop-gold-700);
  font-weight: 750;
}

.lead-description {
  margin: 1.4rem 0;
  color: var(--ocop-text-secondary);
  font-size: 1.03rem;
  line-height: 1.75;
}

.price-box {
  display: flex;
  align-items: baseline;
  gap: 0.5rem;
  padding: 1rem 1.2rem;
  border-radius: 0.9rem;
  background: var(--ocop-sage-50);
}

.price-box strong {
  color: var(--ocop-primary-700);
  font-size: 1.7rem;
}

.price-box span {
  color: var(--ocop-text-secondary);
}

.certification-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9rem, 1fr));
  gap: .5rem 1rem;
  margin: .5rem 0;
}

.certification-list .certification-authority {
  grid-column: 1 / -1;
}

.certification-list dt {
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-caption);
  font-weight: 600;
}

.certification-list dd {
  margin: 0.25rem 0 0;
  color: var(--ocop-text-primary);
  font-size: 0.9rem;
  font-weight: 700;
}

.subject-card {
  display: grid;
  padding: 1rem 1.15rem;
  border-left: 3px solid var(--ocop-primary-700);
  background: var(--ocop-card);
}

.subject-card span,
.subject-card small {
  color: var(--ocop-text-secondary);
  font-size: 0.8rem;
}

.subject-card strong {
  margin: 0.25rem 0;
  color: var(--ocop-text-primary);
}

.content-section {
  display: grid;
  gap: 1.25rem;
  margin-top: 3rem;
}

.source-block ul,
.location-block ul {
  display: grid;
  margin: 1.25rem 0 0;
  padding: 0;
  gap: 0.75rem;
  list-style: none;
}

.source-block li,
.location-block li {
  display: flex;
  padding: 0.9rem 1rem;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border: 1px solid var(--ocop-border);
  border-radius: 0.8rem;
  background: var(--ocop-surface-subtle);
}

.source-block li div,
.location-block li div { display: grid; gap: 0.25rem; }
.source-block li span,
.location-block li span { color: var(--ocop-text-secondary); font-size: 0.78rem; }
.source-block li a,
.location-block li a { flex: 0 0 auto; color: var(--ocop-primary-700); font-size: 0.82rem; font-weight: 750; }

.related-section { margin-top: 3.5rem; }
.related-heading { display: flex; margin-bottom: 1.25rem; align-items: end; justify-content: space-between; gap: 1rem; }
.related-heading h2 { margin: 0.35rem 0 0; color: var(--ocop-text-primary); font-size: clamp(1.5rem, 4vw, 2rem); }
.related-heading > a { color: var(--ocop-primary-700); font-size: 0.85rem; font-weight: 750; }
.related-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 1.25rem; }

.content-block {
  padding: clamp(1.4rem, 4vw, 2.25rem);
  border: 1px solid color-mix(in srgb, var(--ocop-primary-950) 10%, transparent);
  border-radius: 1.1rem;
  background: var(--ocop-card);
}

.content-block h2 {
  margin-bottom: 0.8rem;
  color: var(--ocop-text-primary);
  font-size: 1.35rem;
}

.content-block p {
  margin: 0;
  color: var(--ocop-text-secondary);
  line-height: 1.8;
  white-space: pre-line;
}

.story-block h2 {
  margin: 0.5rem 0 1rem;
  font-size: clamp(1.6rem, 4vw, 2.3rem);
}

.section-eyebrow {
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-caption);
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
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger-strong);
  font-size: 1.4rem;
  font-weight: 800;
}

.error-state p {
  color: var(--ocop-text-secondary);
}

@media (min-width: 768px) {
  .detail-columns {
    grid-template-columns: 1fr 1fr;
  }
}

@media (max-width: 767.98px) {
  .source-block li,
  .location-block li { align-items: flex-start; flex-direction: column; }
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
