<script setup lang="ts">
import axios from 'axios'
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import LeafletMap from '@/components/map/LeafletMap.vue'
import ProductCard from '@/components/products/ProductCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getLocation } from '@/services/locations'
import type { LocationDetail, MapFeature } from '@/types/location'
import {
  externalDirectionsUrl,
  formatTicketPrice,
  locationTypeStyle,
  safeExternalUrl,
} from '@/utils/location'

const route = useRoute()

const location = ref<LocationDetail | null>(null)
const selectedImageUrl = ref<string | null>(null)
const imageFailed = ref(false)
const isLoading = ref(true)
const errorTitle = ref('Không thể tải điểm du lịch')
const errorMessage = ref('')

const typeStyle = computed(() => locationTypeStyle(location.value?.type ?? 'other'))
const activeImage = computed(() => {
  if (imageFailed.value) return typeStyle.value.illustration
  return selectedImageUrl.value || location.value?.primary_image_url || typeStyle.value.illustration
})
const hasRealImage = computed(() => Boolean(location.value?.images.length) && !imageFailed.value)
const mapFeatures = computed<MapFeature[]>(() => {
  if (!location.value) return []
  const current = location.value
  return [
    {
      type: 'Feature',
      geometry: { type: 'Point', coordinates: [current.longitude, current.latitude] },
      properties: {
        id: current.id,
        slug: current.slug,
        name: current.name,
        type: current.type,
        type_label: current.type_label,
        district: current.district,
        address: current.address,
        opening_hours: current.opening_hours,
        ticket_price: current.ticket_price,
        rating_avg: current.rating_avg,
        primary_image_url: current.primary_image_url,
      },
    },
  ]
})
const directionsUrl = computed(() =>
  location.value ? externalDirectionsUrl(location.value.latitude, location.value.longitude) : '',
)
const websiteUrl = computed(() => safeExternalUrl(location.value?.website))
const sourceUrl = computed(() => safeExternalUrl(location.value?.source_url))
const phoneHref = computed(() =>
  location.value?.contact_phone ? `tel:${location.value.contact_phone.replace(/[^\d+]/g, '')}` : '',
)

function formatDate(value: string): string {
  return new Intl.DateTimeFormat('vi-VN').format(new Date(value))
}

function selectImage(imageUrl: string): void {
  selectedImageUrl.value = imageUrl
  imageFailed.value = false
}

async function loadLocation(slug: string): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  location.value = null
  selectedImageUrl.value = null
  imageFailed.value = false
  try {
    location.value = await getLocation(slug)
    selectedImageUrl.value = location.value.images[0]?.image_url ?? null
    document.title = `${location.value.name} | Du lịch nông nghiệp Lâm Đồng`
  } catch (error) {
    errorTitle.value = axios.isAxiosError(error) && error.response?.status === 404
      ? 'Không tìm thấy điểm du lịch'
      : 'Không thể tải điểm du lịch'
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải thông tin điểm du lịch. Vui lòng thử lại.')
  } finally {
    isLoading.value = false
  }
}

watch(
  () => route.params.slug,
  (slug) => {
    if (typeof slug === 'string') void loadLocation(slug)
  },
  { immediate: true },
)

onUnmounted(() => {
  document.title = 'OCOP Lâm Đồng'
})
</script>

<template>
  <main class="location-detail-page">
    <div class="container py-4 py-lg-5">
      <nav class="breadcrumb-nav mb-4" aria-label="Đường dẫn">
        <RouterLink to="/">Trang chủ</RouterLink>
        <span>/</span>
        <RouterLink :to="{ name: 'locations' }">Điểm du lịch</RouterLink>
        <template v-if="location">
          <span>/</span>
          <span aria-current="page">{{ location.name }}</span>
        </template>
      </nav>

      <div v-if="isLoading" class="detail-loading placeholder-glow" aria-label="Đang tải điểm du lịch">
        <span class="placeholder media-loading" />
        <div>
          <span class="placeholder col-4" />
          <span class="placeholder col-10 mt-4" />
          <span class="placeholder col-7 mt-3" />
        </div>
      </div>

      <section v-else-if="errorMessage" class="error-state">
        <span class="error-symbol">!</span>
        <h1>{{ errorTitle }}</h1>
        <p>{{ errorMessage }}</p>
        <RouterLink class="btn btn-success" :to="{ name: 'locations' }">Quay lại danh sách</RouterLink>
      </section>

      <template v-else-if="location">
        <section class="location-overview">
          <div class="gallery">
            <div class="main-image">
              <img
                :src="activeImage"
                :alt="hasRealImage ? location.name : ''"
                @error="imageFailed = true"
              />
            </div>
            <div v-if="location.images.length > 1" class="thumbnail-list" aria-label="Ảnh điểm du lịch">
              <button
                v-for="image in location.images"
                :key="image.id"
                class="thumbnail"
                :class="{ active: activeImage === image.image_url }"
                type="button"
                :aria-label="`Xem ảnh ${image.sort_order + 1}`"
                @click="selectImage(image.image_url)"
              >
                <img :src="image.image_url" alt="" />
              </button>
            </div>
          </div>

          <div class="location-info">
            <span class="type-badge" :style="{ '--type-color': typeStyle.color }">
              <AppIcon :name="typeStyle.icon" :size="14" /> {{ location.type_label }}
            </span>
            <h1>{{ location.name }}</h1>
            <p v-if="location.description" class="lead-description">{{ location.description }}</p>

            <dl class="info-list">
              <div>
                <dt><AppIcon name="map-pin" :size="15" /> Địa chỉ</dt>
                <dd>{{ location.address }}</dd>
              </div>
              <div>
                <dt><AppIcon name="clock" :size="15" /> Giờ mở cửa</dt>
                <dd>{{ location.opening_hours || 'Chưa cập nhật' }}</dd>
              </div>
              <div>
                <dt><AppIcon name="checkCircle" :size="15" /> Giá vé tham khảo</dt>
                <dd>{{ formatTicketPrice(location.ticket_price) }}</dd>
              </div>
              <div>
                <dt><AppIcon name="phone" :size="15" /> Liên hệ</dt>
                <dd>
                  <a v-if="location.contact_phone" :href="phoneHref">{{ location.contact_phone }}</a>
                  <span v-else>Chưa cập nhật</span>
                </dd>
              </div>
              <div v-if="websiteUrl">
                <dt><AppIcon name="compass" :size="15" /> Website</dt>
                <dd>
                  <a :href="websiteUrl" target="_blank" rel="noopener noreferrer">{{ location.website }}</a>
                </dd>
              </div>
            </dl>

            <ul v-if="location.services.length" class="service-list" aria-label="Dịch vụ trải nghiệm">
              <li v-for="service in location.services" :key="service">
                <AppIcon name="checkCircle" :size="13" /> {{ service }}
              </li>
            </ul>

            <div class="action-row">
              <RouterLink class="btn btn-success" :to="{ name: 'map', query: { diem: location.slug } }">
                <AppIcon name="map" :size="16" /> Xem trên bản đồ số
              </RouterLink>
              <a class="btn btn-outline-success" :href="directionsUrl" target="_blank" rel="noopener noreferrer">
                <AppIcon name="navigation" :size="16" /> Chỉ đường bằng Google Maps
              </a>
            </div>

            <aside v-if="location.subject" class="subject-card">
              <span>Đơn vị quản lý</span>
              <strong>{{ location.subject.name }}</strong>
              <small>{{ location.subject.district }}, Lâm Đồng</small>
            </aside>
          </div>
        </section>

        <section class="content-block map-block" aria-labelledby="location-map-title">
          <h2 id="location-map-title">Vị trí trên bản đồ</h2>
          <div class="mini-map">
            <LeafletMap
              :features="mapFeatures"
              :selected-slug="location.slug"
              :cluster="false"
              :initial-zoom="13"
              :label="`Bản đồ vị trí ${location.name}`"
            />
          </div>
        </section>

        <section v-if="location.products.length" class="products-block" aria-labelledby="location-products-title">
          <span class="section-eyebrow">Sản phẩm OCOP tại điểm đến</span>
          <h2 id="location-products-title">Đặc sản được giới thiệu</h2>
          <div class="product-grid">
            <ProductCard v-for="product in location.products" :key="product.id" :product="product" />
          </div>
        </section>

        <p class="source-note">
          Thông tin mang tính tham khảo, cập nhật {{ formatDate(location.updated_at) }}.
          <template v-if="sourceUrl">
            Nguồn:
            <a :href="sourceUrl" target="_blank" rel="noopener noreferrer">trang thông tin công khai</a>.
          </template>
          Vui lòng liên hệ điểm đến trước khi tham quan.
        </p>
      </template>
    </div>
  </main>
</template>

<style scoped>
.location-detail-page {
  min-height: calc(100vh - 4.5rem);
  background: var(--ocop-surface);
}

.breadcrumb-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 0.45rem;
  color: var(--ocop-slate);
  font-size: 0.86rem;
}

.breadcrumb-nav a {
  color: var(--ocop-primary-700);
  text-decoration: none;
}

.detail-loading,
.location-overview {
  display: grid;
  gap: 2rem;
}

.media-loading {
  display: block;
  min-height: 20rem;
  border-radius: 1rem;
}

.error-state {
  padding: 4rem 1.5rem;
  border: 1px dashed var(--ocop-border-strong);
  border-radius: 1rem;
  background: var(--ocop-card);
  text-align: center;
}

.error-symbol {
  display: inline-grid;
  width: 3rem;
  height: 3rem;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger);
  font-weight: 800;
}

.error-state h1 {
  margin: 1rem 0 0.5rem;
  font-size: 1.6rem;
}

.error-state p {
  color: var(--ocop-slate);
}

.main-image {
  overflow: hidden;
  aspect-ratio: 4 / 3;
  border-radius: 1.25rem;
  background: var(--ocop-mint-soft);
}

.main-image img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.thumbnail-list {
  display: flex;
  gap: 0.6rem;
  margin-top: 0.75rem;
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
  background: var(--ocop-card);
}

.thumbnail.active {
  border-color: var(--ocop-primary-700);
}

.thumbnail img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.type-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 5px 10px;
  border-radius: var(--ocop-radius-pill);
  background: var(--type-color, var(--ocop-primary-700));
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.location-info h1 {
  margin: 0.85rem 0 0.6rem;
  color: var(--ocop-primary-950);
  font-size: clamp(1.8rem, 4vw, 2.6rem);
  font-weight: 800;
}

.lead-description {
  color: var(--ocop-sage-800);
  line-height: 1.7;
}

.info-list {
  display: grid;
  gap: 0.75rem;
  margin: 1.25rem 0;
  padding: 1.1rem;
  border: 1px solid var(--ocop-border);
  border-radius: 1rem;
  background: var(--ocop-card);
}

.info-list div {
  display: grid;
  gap: 0.2rem;
}

.info-list dt {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ocop-slate);
  font-size: 0.8rem;
  font-weight: 700;
}

.info-list dd {
  margin: 0;
  color: var(--ocop-navy);
  overflow-wrap: anywhere;
}

.service-list {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin: 0 0 1.25rem;
  padding: 0;
  list-style: none;
}

.service-list li {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 5px 10px;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mint-soft);
  color: var(--ocop-primary-900);
  font-size: var(--ocop-font-size-small);
  font-weight: 600;
}

.action-row {
  display: flex;
  flex-wrap: wrap;
  gap: 0.6rem;
}

.action-row .btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.subject-card {
  display: grid;
  gap: 0.15rem;
  margin-top: 1.25rem;
  padding: 1rem;
  border-left: 4px solid var(--ocop-primary-700);
  border-radius: 0.75rem;
  background: var(--ocop-mint-soft);
}

.subject-card span,
.subject-card small {
  color: var(--ocop-slate);
  font-size: 0.8rem;
}

.content-block,
.products-block {
  margin-top: 2.5rem;
}

.content-block h2,
.products-block h2 {
  margin: 0.25rem 0 1rem;
  color: var(--ocop-primary-950);
  font-size: 1.4rem;
  font-weight: 800;
}

.section-eyebrow {
  color: var(--ocop-primary-700);
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.mini-map {
  height: 340px;
  min-height: 340px;
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: 1rem;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 15rem), 1fr));
  gap: 1.25rem;
}

.source-note {
  margin: 2rem 0 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
}

@media (min-width: 992px) {
  .detail-loading,
  .location-overview {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
    align-items: start;
  }
}
</style>
