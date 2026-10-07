<script setup lang="ts">
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'

import PresentationGallery from '@/components/products/PresentationGallery.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getProduct } from '@/services/products'
import { getLocation, getNearbyLocations } from '@/services/locations'
import type { Coordinate, LocationDetail } from '@/types/location'
import type { ProductDetail } from '@/types/product'
import { formatDistance } from '@/utils/location'

const route = useRoute()
const product = ref<ProductDetail | null>(null)
const isLoading = ref(true)
const productError = ref('')
const details = ref<Record<string, LocationDetail>>({})
const isLoadingDetails = ref(false)
const detailError = ref(false)
const isLocating = ref(false)
const locationError = ref('')
const hasLocated = ref(false)
const distances = ref<Record<string, number>>({})
let generation = 0

const locations = computed(() => {
  const related = [...(product.value?.related_locations ?? [])]
  // Nearby has a radius/limit; relations absent from its response remain visible.
  return related.sort((a, b) =>
    (distances.value[a.slug] ?? Infinity) - (distances.value[b.slug] ?? Infinity),
  )
})

async function loadProduct(slug: string): Promise<void> {
  const request = ++generation
  product.value = null
  details.value = {}
  distances.value = {}
  hasLocated.value = false
  isLocating.value = false
  locationError.value = ''
  productError.value = ''
  detailError.value = false
  isLoadingDetails.value = false
  isLoading.value = true
  try {
    const result = await getProduct(slug)
    if (request !== generation) return
    product.value = result
    document.title = `${result.name} – Điểm mua & trải nghiệm | OCOP Lâm Đồng`
    isLoading.value = false
    const related = result.related_locations ?? []
    if (!related.length) return
    isLoadingDetails.value = true
    const results = await Promise.allSettled(related.map((location) => getLocation(location.slug)))
    if (request !== generation) return
    results.forEach((result, index) => {
      const relation = related[index]!
      if (result.status === 'fulfilled' && result.value.id === relation.id && result.value.slug === relation.slug) {
        details.value[relation.slug] = result.value
      } else {
        detailError.value = true
      }
    })
  } catch (error) {
    if (request !== generation) return
    productError.value = getApiErrorMessage(error, 'Không thể tải thông tin sản phẩm. Vui lòng thử lại.')
  } finally {
    if (request === generation) {
      isLoading.value = false
      isLoadingDetails.value = false
    }
  }
}

// Same browser options and error wording as the existing Map geolocation flow.
function requestPosition(): Promise<Coordinate> {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Trình duyệt không hỗ trợ định vị.'))
      return
    }
    navigator.geolocation.getCurrentPosition(
      (position) => resolve({ latitude: position.coords.latitude, longitude: position.coords.longitude }),
      (error) => reject(new Error(
        error.code === error.PERMISSION_DENIED
          ? 'Bạn chưa cho phép truy cập vị trí. Hãy bật quyền vị trí cho trang web rồi thử lại.'
          : error.code === error.TIMEOUT
            ? 'Hết thời gian xác định vị trí. Vui lòng thử lại.'
            : 'Không xác định được vị trí hiện tại của bạn.',
      )),
      { enableHighAccuracy: false, timeout: 10_000, maximumAge: 60_000 },
    )
  })
}

async function findNearby(): Promise<void> {
  if (!locations.value.length || isLocating.value) return
  const request = generation
  const related = [...locations.value]
  isLocating.value = true
  locationError.value = ''
  try {
    const origin = await requestPosition()
    if (request !== generation) return
    const response = await getNearbyLocations(origin, { radiusKm: 200, limit: 50 })
    if (request !== generation) return
    const next: Record<string, number> = {}
    for (const relation of related) {
      const match = response.items.find((item) => item.id === relation.id || item.slug === relation.slug)
      if (match && Number.isFinite(match.distance_m) && match.distance_m >= 0) next[relation.slug] = match.distance_m
    }
    distances.value = next
    hasLocated.value = true
  } catch (error) {
    if (request !== generation) return
    locationError.value = error instanceof Error && !('isAxiosError' in error) && (
      error.message.includes('vị trí') || error.message.includes('định vị')
    ) ? error.message : getApiErrorMessage(error, 'Không thể tìm điểm gần bạn. Vui lòng thử lại.')
  } finally {
    if (request === generation) isLocating.value = false
  }
}

function retry(): void {
  if (typeof route.params.slug === 'string') void loadProduct(route.params.slug)
}

watch(() => route.params.slug, (slug) => {
  if (typeof slug === 'string') void loadProduct(slug)
}, { immediate: true })

onUnmounted(() => {
  generation++
  document.title = 'OCOP Lâm Đồng'
})
</script>

<template>
  <main class="experience-page">
    <div class="container py-4 py-lg-5">
      <p v-if="isLoading" role="status">Đang tải sản phẩm...</p>
      <section v-else-if="productError" role="alert">
        <h1>Không thể tải sản phẩm</h1>
        <p>{{ productError }}</p>
        <button class="btn btn-outline-success" data-test="retry" type="button" @click="retry">Thử lại</button>
      </section>
      <template v-else-if="product">
        <RouterLink :to="{ name: 'product-detail', params: { slug: product.slug } }">Quay lại sản phẩm</RouterLink>
        <header class="experience-header my-4">
          <h1>{{ product.name }}</h1>
          <p>{{ product.star }} sao OCOP · {{ product.category.name }}</p>
          <p>Chủ thể: {{ product.subject.name }}</p>
        </header>
        <section aria-labelledby="experience-title">
          <h2 id="experience-title">Nơi mua &amp; trải nghiệm sản phẩm</h2>
          <p v-if="!locations.length" class="mt-3">
            Hiện chưa có điểm mua/trải nghiệm được xác minh cho sản phẩm này.
          </p>
          <template v-else>
            <button class="btn btn-success my-3" data-test="locate" type="button" :disabled="isLocating" @click="findNearby">
              {{ isLocating ? 'Đang tìm điểm gần bạn...' : 'Tìm điểm gần tôi' }}
            </button>
            <p v-if="locationError" role="alert" class="text-danger">{{ locationError }}</p>
            <p v-if="hasLocated" role="status">
              Các điểm có khoảng cách được sắp xếp gần nhất trước. Khoảng cách là đường thẳng.
              Chỉ có khoảng cách cho các điểm trong tối đa 50 kết quả gần nhất, bán kính 200 km.
            </p>
            <p v-else>Vị trí chỉ được yêu cầu khi bạn bấm “Tìm điểm gần tôi”.</p>
            <p v-if="isLoadingDetails" role="status">Đang tải địa chỉ và dịch vụ...</p>
            <p v-if="detailError" role="status">Chưa tải được thông tin bổ sung của một số điểm. Bạn vẫn có thể xem chi tiết hoặc bản đồ.</p>
            <div class="experience-grid">
              <article v-for="location in locations" :key="location.id" class="experience-location">
                <PresentationGallery v-if="details[location.slug]" :images="details[location.slug]!.images" :primary-url="details[location.slug]!.primary_image_url" :name="location.name" landscape />
                <div class="location-content">
                  <h3>{{ location.name }}</h3>
                  <p>{{ location.type_label }} · {{ location.district }}</p>
                  <p>Địa chỉ: {{ details[location.slug]?.address || 'Chưa cập nhật' }}</p>
                  <ul v-if="details[location.slug]?.services.length" class="service-chips" aria-label="Dịch vụ"><li v-for="service in details[location.slug]!.services" :key="service">{{ service }}</li></ul>
                  <p v-if="details[location.slug]?.subject" class="manager">Đơn vị quản lý: {{ details[location.slug]!.subject!.name }}</p>
                  <p v-if="distances[location.slug] !== undefined" class="distance" role="status">Cách bạn {{ formatDistance(distances[location.slug]!) }}</p>
                  <p v-else-if="hasLocated">Chưa có khoảng cách</p>
                  <div class="experience-actions">
                    <RouterLink class="btn btn-outline-success" data-test="detail" :to="{ name: 'location-detail', params: { slug: location.slug } }">Xem chi tiết</RouterLink>
                    <RouterLink class="btn btn-outline-success" data-test="map" :to="{ name: 'map', query: { diem: location.slug } }">Xem bản đồ</RouterLink>
                    <RouterLink class="btn btn-success" data-test="directions" :to="{ name: 'map', query: { diem: location.slug, action: 'route' } }">Chỉ đường</RouterLink>
                  </div>
                  <small>Chỉ đường mở bước xác nhận dùng vị trí của bạn trên bản đồ.</small>
                </div>
              </article>
            </div>
          </template>
        </section>
      </template>
    </div>
  </main>
</template>

<style scoped>
.experience-header { padding: 1.25rem; border-left: 4px solid var(--ocop-primary-700); background: var(--ocop-card); }
.location-content { padding: 1.25rem; }
.service-chips { display: flex; flex-wrap: wrap; gap: .4rem; list-style: none; padding: 0; }
.service-chips li { background: var(--ocop-sage-50); color: var(--ocop-primary-700); border-radius: var(--ocop-radius-pill); padding: .3rem .6rem; font-size: .8rem; }
.distance { display: inline-block; padding: .5rem .75rem; border-radius: .5rem; background: var(--ocop-sage-50); color: var(--ocop-primary-700); font-weight: 750; font-size: 1.1rem; }
.manager { font-size: .85rem; color: var(--ocop-text-secondary); }

.experience-page { min-height: 65vh; background: var(--ocop-surface); }
h1, h2, h3 { color: var(--ocop-primary-950); overflow-wrap: anywhere; }
h1 { font-size: clamp(1.5rem, 4vw, 2.2rem); }
h2 { font-size: 1.4rem; }
h3 { font-size: 1.15rem; }
.experience-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 340px), 1fr)); gap: 1rem; }
.experience-location { overflow: hidden; border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-md); background: var(--ocop-card); }
.experience-actions { display: flex; flex-wrap: wrap; gap: .5rem; margin: 1rem 0; }
small { display: block; color: var(--ocop-slate); }
</style>
