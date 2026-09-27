<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import LocationCard from '@/components/locations/LocationCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getLocationFilterOptions, getLocations } from '@/services/locations'
import type {
  LocationListItem,
  LocationSort,
  LocationType,
  LocationTypeOption,
} from '@/types/location'
import { isLocationType, sortVietnamese } from '@/utils/location'

const route = useRoute()
const router = useRouter()

const locations = ref<LocationListItem[]>([])
const typeOptions = ref<LocationTypeOption[]>([])
const districts = ref<string[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 12
const isLoading = ref(false)
const errorMessage = ref('')
let latestRequestId = 0

const form = reactive({
  search: '',
  type: '' as LocationType | '',
  district: '',
  sort: 'name' as LocationSort,
})

const sortOptions: Array<{ value: LocationSort; label: string }> = [
  { value: 'name', label: 'Tên A–Z' },
  { value: '-name', label: 'Tên Z–A' },
  { value: 'newest', label: 'Mới cập nhật' },
  { value: 'rating', label: 'Đánh giá cao' },
]

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const hasFilters = computed(() => Boolean(form.search || form.type || form.district))

function queryText(value: unknown): string {
  return typeof value === 'string' ? value.trim() : ''
}

function hydrateFormFromQuery(): void {
  form.search = queryText(route.query.search)
  const requestedType = queryText(route.query.type)
  form.type = isLocationType(requestedType) ? requestedType : ''
  form.district = queryText(route.query.district)
  const requestedSort = queryText(route.query.sort) as LocationSort
  form.sort = sortOptions.some((option) => option.value === requestedSort) ? requestedSort : 'name'
  const requestedPage = Number(route.query.page)
  currentPage.value = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1
}

function filterQuery(page = 1): Record<string, string> {
  const query: Record<string, string> = {}
  if (page > 1) query.page = String(page)
  if (form.search) query.search = form.search
  if (form.type) query.type = form.type
  if (form.district) query.district = form.district
  if (form.sort !== 'name') query.sort = form.sort
  return query
}

async function loadLocations(): Promise<void> {
  const requestId = ++latestRequestId
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await getLocations({
      page: currentPage.value,
      page_size: pageSize,
      search: form.search || undefined,
      type: form.type || undefined,
      district: form.district || undefined,
      sort: form.sort,
    })
    if (requestId !== latestRequestId) return
    const responsePages = Math.max(1, Math.ceil(response.total / pageSize))
    if (response.total > 0 && currentPage.value > responsePages) {
      await router.replace({ name: 'locations', query: filterQuery(responsePages) })
      return
    }
    locations.value = response.items
    total.value = response.total
  } catch (error) {
    if (requestId !== latestRequestId) return
    locations.value = []
    total.value = 0
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải danh sách điểm du lịch. Vui lòng thử lại.')
  } finally {
    if (requestId === latestRequestId) isLoading.value = false
  }
}

async function loadFilterOptions(): Promise<void> {
  try {
    const options = await getLocationFilterOptions()
    typeOptions.value = options.types
    districts.value = sortVietnamese(options.districts)
  } catch {
    typeOptions.value = []
    districts.value = []
  }
}

async function applyFilters(): Promise<void> {
  form.search = form.search.trim()
  await router.push({ name: 'locations', query: filterQuery() })
}

async function clearFilters(): Promise<void> {
  Object.assign(form, { search: '', type: '', district: '', sort: 'name' })
  await router.push({ name: 'locations' })
}

async function goToPage(page: number): Promise<void> {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  await router.push({ name: 'locations', query: filterQuery(page) })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(
  () => route.query,
  () => {
    hydrateFormFromQuery()
    void loadLocations()
  },
  { deep: true, immediate: true },
)

onMounted(() => {
  void loadFilterOptions()
  document.title = 'Điểm du lịch nông nghiệp | OCOP Lâm Đồng'
})

onUnmounted(() => {
  document.title = 'OCOP Lâm Đồng'
})
</script>

<template>
  <main class="locations-page">
    <section class="page-banner">
      <div class="container py-5">
        <span class="page-eyebrow">Du lịch nông nghiệp Lâm Đồng</span>
        <h1>Điểm đến trải nghiệm</h1>
        <p>Đồi chè, vườn cà phê, vườn dâu, vườn hoa và nông trại mở cửa đón khách tham quan.</p>
        <RouterLink class="btn btn-success mt-3" :to="{ name: 'map' }">
          <AppIcon name="map" :size="16" /> Mở bản đồ số
        </RouterLink>
      </div>
    </section>

    <div class="container py-5">
      <form class="filter-bar" role="search" @submit.prevent="applyFilters">
        <div class="filter-field search-field">
          <label class="form-label" for="location-search">Từ khóa</label>
          <input
            id="location-search"
            v-model="form.search"
            class="form-control"
            type="search"
            maxlength="150"
            placeholder="Tên điểm, địa chỉ, trải nghiệm..."
          />
        </div>
        <div class="filter-field">
          <label class="form-label" for="location-type">Loại hình</label>
          <select id="location-type" v-model="form.type" class="form-select">
            <option value="">Tất cả loại hình</option>
            <option v-for="option in typeOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
        <div class="filter-field">
          <label class="form-label" for="location-district">Địa bàn</label>
          <select id="location-district" v-model="form.district" class="form-select">
            <option value="">Tất cả địa bàn</option>
            <option v-for="district in districts" :key="district" :value="district">
              {{ district }}
            </option>
          </select>
        </div>
        <div class="filter-actions">
          <button class="btn btn-success" type="submit" :disabled="isLoading">Tìm kiếm</button>
          <button v-if="hasFilters" class="btn btn-outline-secondary" type="button" @click="clearFilters">
            Xóa lọc
          </button>
        </div>
      </form>

      <section :aria-busy="isLoading" aria-live="polite">
        <div class="result-toolbar">
          <p class="mb-0 fw-semibold">{{ total }} điểm du lịch phù hợp</p>
          <select
            v-model="form.sort"
            class="form-select sort-select"
            aria-label="Sắp xếp điểm du lịch"
            @change="applyFilters"
          >
            <option v-for="option in sortOptions" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>

        <div v-if="errorMessage" class="alert alert-danger" role="alert">
          {{ errorMessage }}
          <button class="btn btn-sm btn-outline-danger ms-2" type="button" @click="loadLocations">
            Thử lại
          </button>
        </div>

        <div v-else-if="isLoading" class="location-grid" aria-label="Đang tải điểm du lịch">
          <div v-for="index in 6" :key="index" class="loading-card placeholder-glow">
            <span class="placeholder col-12 media-placeholder" />
            <span class="placeholder col-7 mt-4" />
            <span class="placeholder col-10 mt-3" />
          </div>
        </div>

        <div v-else-if="locations.length" class="location-grid">
          <LocationCard v-for="location in locations" :key="location.id" :location="location" />
        </div>

        <div v-else class="empty-state">
          <strong>Chưa tìm thấy điểm du lịch phù hợp</strong>
          <p>Hãy thử từ khóa khác hoặc xóa bớt bộ lọc.</p>
          <button v-if="hasFilters" class="btn btn-outline-success" type="button" @click="clearFilters">
            Xóa bộ lọc
          </button>
        </div>

        <nav v-if="!isLoading && totalPages > 1" class="pagination-wrap" aria-label="Phân trang">
          <button
            class="btn btn-outline-success"
            type="button"
            :disabled="currentPage === 1"
            @click="goToPage(currentPage - 1)"
          >
            Trang trước
          </button>
          <span>Trang {{ currentPage }} / {{ totalPages }}</span>
          <button
            class="btn btn-outline-success"
            type="button"
            :disabled="currentPage === totalPages"
            @click="goToPage(currentPage + 1)"
          >
            Trang sau
          </button>
        </nav>
      </section>

      <p class="data-note">
        Thông tin giờ mở cửa, giá vé và liên hệ là dữ liệu tham khảo từ nguồn công khai;
        vui lòng liên hệ điểm đến trước khi tham quan.
      </p>
    </div>
  </main>
</template>

<style scoped>
.locations-page {
  min-height: calc(100vh - 4.5rem);
  background: var(--ocop-surface);
}

.page-banner {
  background:
    radial-gradient(circle at 82% 25%, color-mix(in srgb, var(--ocop-lime-300) 52%, transparent), transparent 22rem),
    var(--ocop-mint-soft);
}

.page-eyebrow {
  color: var(--ocop-primary-700);
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.page-banner h1 {
  margin: 0.7rem 0;
  color: var(--ocop-primary-950);
  font-size: clamp(2.2rem, 5vw, 3.7rem);
  font-weight: 800;
}

.page-banner p {
  max-width: 42rem;
  margin: 0;
  color: var(--ocop-slate);
}

.page-banner .btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
}

.filter-bar {
  display: grid;
  margin-bottom: 1.75rem;
  padding: 1.25rem;
  gap: 1rem;
  border: 1px solid color-mix(in srgb, var(--ocop-primary-950) 10%, transparent);
  border-radius: 1rem;
  background: var(--ocop-card);
}

.filter-bar .form-label {
  color: var(--ocop-sage-800);
  font-size: 0.84rem;
  font-weight: 700;
}

.filter-actions {
  display: flex;
  align-items: flex-end;
  gap: 0.5rem;
}

.result-toolbar,
.pagination-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.result-toolbar {
  margin-bottom: 1.25rem;
}

.sort-select {
  width: min(12rem, 48%);
}

.location-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 17rem), 1fr));
  gap: 1.25rem;
}

.loading-card {
  min-height: 24rem;
  padding: 1rem;
  border-radius: 1rem;
  background: var(--ocop-card);
}

.media-placeholder {
  display: block;
  height: 11rem;
  border-radius: 0.75rem;
}

.empty-state {
  padding: 4rem 1.5rem;
  border: 1px dashed var(--ocop-border-strong);
  border-radius: 1rem;
  background: var(--ocop-card);
  text-align: center;
}

.empty-state strong {
  display: block;
  color: var(--ocop-primary-950);
  font-size: 1.15rem;
}

.empty-state p {
  margin: 0.5rem 0 1.25rem;
  color: var(--ocop-slate);
}

.pagination-wrap {
  justify-content: center;
  margin-top: 2rem;
}

.pagination-wrap span {
  color: var(--ocop-slate);
  font-size: 0.9rem;
  font-weight: 650;
}

.data-note {
  margin: 2rem 0 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
  text-align: center;
}

@media (min-width: 768px) {
  .filter-bar {
    grid-template-columns: minmax(0, 2fr) minmax(0, 1fr) minmax(0, 1fr) auto;
    align-items: end;
  }
}
</style>
