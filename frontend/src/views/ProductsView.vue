<script setup lang="ts">
import { computed, onMounted, onUnmounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ProductCard from '@/components/products/ProductCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { teaPhoto } from '@/constants/photos'
import { categoryTheme } from '@/utils/category'
import { getApiErrorMessage } from '@/services/api-error'
import { getCategories } from '@/services/categories'
import { getProductFilterOptions, getProducts } from '@/services/products'
import type { Category } from '@/types/category'
import type {
  ProductFilters,
  ProductListItem,
  ProductSort,
} from '@/types/product'

const route = useRoute()
const router = useRouter()

const categories = ref<Category[]>([])
const districts = ref<string[]>([])
const products = ref<ProductListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 12
const isLoading = ref(false)
const errorMessage = ref('')
const validationMessage = ref('')
let latestRequestId = 0

// Trình bày: ngăn kéo bộ lọc trên điện thoại (bottom sheet) và lựa chọn nhanh danh mục, hạng sao.
const isFilterOpen = ref(false)
const bannerPhotoFailed = ref(false)
const starOptions = [
  { value: '', label: 'Tất cả' },
  { value: '3', label: '3 sao' },
  { value: '4', label: '4 sao' },
  { value: '5', label: '5 sao' },
]

const form = reactive({
  search: '',
  category: '',
  star: '',
  district: '',
  minPrice: '',
  maxPrice: '',
  sort: 'newest' as ProductSort,
})

const sortOptions: Array<{ value: ProductSort; label: string }> = [
  { value: 'newest', label: 'Mới nhất' },
  { value: 'name', label: 'Tên A–Z' },
  { value: '-name', label: 'Tên Z–A' },
  { value: 'price', label: 'Giá tăng dần' },
  { value: '-price', label: 'Giá giảm dần' },
  { value: 'rating', label: 'Đánh giá cao' },
]

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const resultText = computed(() => `${total.value} sản phẩm phù hợp`)
const pageNumbers = computed(() => {
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  const end = Math.min(totalPages.value, start + maxVisible - 1)
  start = Math.max(1, end - maxVisible + 1)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})

const activeFilters = computed(() => {
  const filters: Array<{ key: keyof typeof form; label: string }> = []
  if (form.search) filters.push({ key: 'search', label: `Từ khóa: ${form.search}` })
  if (form.category) {
    const category = categories.value.find((item) => item.slug === form.category)
    filters.push({ key: 'category', label: `Danh mục: ${category?.name || form.category}` })
  }
  if (form.star) filters.push({ key: 'star', label: `${form.star} sao` })
  if (form.district) filters.push({ key: 'district', label: `Địa bàn: ${form.district}` })
  if (form.minPrice) filters.push({ key: 'minPrice', label: `Giá từ ${Number(form.minPrice).toLocaleString('vi-VN')}đ` })
  if (form.maxPrice) filters.push({ key: 'maxPrice', label: `Giá đến ${Number(form.maxPrice).toLocaleString('vi-VN')}đ` })
  return filters
})

function queryText(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function queryNumber(value: unknown): number | undefined {
  if (value === '' || value === null || value === undefined) return undefined
  const parsed = Number(value)
  return Number.isFinite(parsed) && parsed >= 0 ? parsed : undefined
}

function hydrateFormFromQuery(): void {
  form.search = queryText(route.query.search)
  form.category = queryText(route.query.category)
  form.star = queryText(route.query.star)
  form.district = queryText(route.query.district)
  form.minPrice = queryText(route.query.min_price)
  form.maxPrice = queryText(route.query.max_price)

  const requestedSort = queryText(route.query.sort) as ProductSort
  form.sort = sortOptions.some((option) => option.value === requestedSort)
    ? requestedSort
    : 'newest'

  const requestedPage = Number(route.query.page)
  currentPage.value = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1
}

function filtersFromRoute(): ProductFilters {
  return {
    page: currentPage.value,
    page_size: pageSize,
    search: form.search || undefined,
    category: form.category || undefined,
    star: queryNumber(form.star),
    district: form.district || undefined,
    min_price: queryNumber(form.minPrice),
    max_price: queryNumber(form.maxPrice),
    sort: form.sort,
  }
}

async function loadProducts(): Promise<void> {
  const requestId = ++latestRequestId
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await getProducts(filtersFromRoute())
    if (requestId !== latestRequestId) return

    const responseTotalPages = Math.max(1, Math.ceil(response.total / pageSize))
    if (response.total > 0 && currentPage.value > responseTotalPages) {
      await router.replace({ name: 'products', query: filterQuery(responseTotalPages) })
      return
    }
    products.value = response.items
    total.value = response.total
  } catch (error) {
    if (requestId !== latestRequestId) return
    products.value = []
    total.value = 0
    errorMessage.value = getApiErrorMessage(
      error,
      'Không thể tải danh sách sản phẩm. Vui lòng thử lại.',
    )
  } finally {
    if (requestId === latestRequestId) isLoading.value = false
  }
}

async function loadCategories(): Promise<void> {
  try {
    categories.value = (await getCategories()).items
  } catch {
    categories.value = []
  }
}

async function loadFilterOptions(): Promise<void> {
  try {
    districts.value = (await getProductFilterOptions()).districts
  } catch {
    districts.value = []
  }
}

function filterQuery(page = 1): Record<string, string> {
  const query: Record<string, string> = {}
  if (page > 1) query.page = String(page)
  if (form.search) query.search = form.search
  if (form.category) query.category = form.category
  if (form.star) query.star = form.star
  if (form.district) query.district = form.district
  if (form.minPrice) query.min_price = form.minPrice
  if (form.maxPrice) query.max_price = form.maxPrice
  if (form.sort !== 'newest') query.sort = form.sort
  return query
}

async function applyFilters(): Promise<void> {
  validationMessage.value = ''
  const minPrice = queryNumber(form.minPrice)
  const maxPrice = queryNumber(form.maxPrice)
  if (minPrice !== undefined && maxPrice !== undefined && minPrice > maxPrice) {
    validationMessage.value = 'Giá tối thiểu không được lớn hơn giá tối đa.'
    return
  }
  await router.push({ name: 'products', query: filterQuery() })
}

async function clearFilters(): Promise<void> {
  validationMessage.value = ''
  Object.assign(form, {
    search: '',
    category: '',
    star: '',
    district: '',
    minPrice: '',
    maxPrice: '',
    sort: 'newest',
  })
  await router.push({ name: 'products' })
}

async function removeFilter(key: keyof typeof form): Promise<void> {
  if (key === 'sort') form.sort = 'newest'
  else form[key] = ''
  await applyFilters()
}

async function selectCategory(slug: string): Promise<void> {
  form.category = slug
  await applyFilters()
}

async function selectStar(value: string): Promise<void> {
  form.star = value
  await applyFilters()
}

async function submitFromDrawer(): Promise<void> {
  await applyFilters()
  if (!validationMessage.value) isFilterOpen.value = false
}

async function goToPage(page: number): Promise<void> {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  await router.push({ name: 'products', query: filterQuery(page) })
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(
  () => route.query,
  () => {
    hydrateFormFromQuery()
    void loadProducts()
  },
  { deep: true, immediate: true },
)

onMounted(() => {
  void loadCategories()
  void loadFilterOptions()
  document.title = 'Sản phẩm OCOP | OCOP Lâm Đồng'
})

onUnmounted(() => {
  document.title = 'OCOP Lâm Đồng'
})
</script>

<template>
  <main class="products-page">
    <section class="page-banner" :class="{ 'has-photo': !bannerPhotoFailed }">
      <img
        v-if="!bannerPhotoFailed"
        class="banner-photo"
        :src="teaPhoto.src"
        alt=""
        @error="bannerPhotoFailed = true"
      />
      <div class="site-content banner-inner">
        <nav class="breadcrumb-trail" aria-label="Đường dẫn">
          <RouterLink to="/">Trang chủ</RouterLink>
          <AppIcon name="chevronRight" :size="14" />
          <span aria-current="page">Sản phẩm OCOP</span>
        </nav>
        <h1>Sản phẩm OCOP Lâm Đồng</h1>
        <p>Đặc sản đã được công nhận 3–5 sao, tìm theo nhóm sản phẩm, hạng sao, địa phương và mức giá.</p>

        <form class="banner-search" role="search" @submit.prevent="applyFilters">
          <label class="banner-search-field">
            <span class="visually-hidden">Tìm theo tên sản phẩm hoặc chủ thể</span>
            <AppIcon name="search" :size="18" />
            <input
              id="product-search"
              v-model.trim="form.search"
              type="search"
              placeholder="Tên sản phẩm, chủ thể: atiso, cà phê, mắc ca..."
            />
          </label>
          <button class="ocop-btn-accent" type="submit" :disabled="isLoading">Tìm</button>
        </form>
      </div>
    </section>

    <div class="site-content category-strip">
      <ul class="category-chips" aria-label="Lọc theo nhóm sản phẩm">
        <li>
          <button type="button" class="chip" :aria-pressed="!form.category" @click="selectCategory('')">
            Tất cả nhóm
          </button>
        </li>
        <li v-for="category in categories" :key="category.id">
          <button
            type="button"
            class="chip"
            :aria-pressed="form.category === category.slug"
            :style="{
              '--chip-bg': categoryTheme(category.slug).background,
              '--chip-fg': categoryTheme(category.slug).foreground,
            }"
            @click="selectCategory(category.slug)"
          >
            <span class="chip-icon" aria-hidden="true"><AppIcon :name="categoryTheme(category.slug).icon" :size="14" /></span>
            {{ category.name }}
          </button>
        </li>
      </ul>
    </div>

    <div class="site-content products-body">
      <div class="products-layout">
        <div v-if="isFilterOpen" class="filter-scrim" aria-hidden="true" @click="isFilterOpen = false" />
        <aside
          id="product-filters"
          class="filter-aside"
          :class="{ open: isFilterOpen }"
          aria-label="Bộ lọc sản phẩm"
          @keydown.esc="isFilterOpen = false"
        >
          <form class="filter-panel" @submit.prevent="submitFromDrawer">
            <div class="filter-heading">
              <h2>Bộ lọc</h2>
              <button class="btn-reset" type="button" @click="clearFilters">Xóa tất cả</button>
              <button class="filter-close" type="button" aria-label="Đóng bộ lọc" @click="isFilterOpen = false">
                <AppIcon name="close" :size="18" />
              </button>
            </div>

            <fieldset class="filter-group">
              <legend>Hạng sao OCOP</legend>
              <div class="star-segment" role="group" aria-label="Chọn hạng sao">
                <button
                  v-for="option in starOptions"
                  :key="option.value"
                  type="button"
                  :aria-pressed="form.star === option.value"
                  @click="selectStar(option.value)"
                >
                  <AppIcon v-if="option.value" name="star" :size="13" />
                  {{ option.label }}
                </button>
              </div>
            </fieldset>

            <div class="filter-group">
              <label class="form-label" for="product-district">Địa bàn</label>
              <input
                id="product-district"
                v-model.trim="form.district"
                class="form-control"
                list="product-district-options"
                type="text"
                placeholder="Xã, phường..."
              />
              <datalist id="product-district-options">
                <option v-for="district in districts" :key="district" :value="district" />
              </datalist>
            </div>

            <fieldset class="filter-group">
              <legend>Khoảng giá (đồng)</legend>
              <div class="price-row">
                <input
                  v-model="form.minPrice"
                  class="form-control"
                  type="number"
                  min="0"
                  step="1000"
                  aria-label="Giá tối thiểu"
                  placeholder="Từ"
                />
                <span aria-hidden="true">–</span>
                <input
                  v-model="form.maxPrice"
                  class="form-control"
                  type="number"
                  min="0"
                  step="1000"
                  aria-label="Giá tối đa"
                  placeholder="Đến"
                />
              </div>
            </fieldset>

            <p v-if="validationMessage" class="filter-error" role="alert">
              {{ validationMessage }}
            </p>
            <button class="ocop-btn-main filter-submit" type="submit" :disabled="isLoading">
              {{ isLoading ? 'Đang tải...' : 'Áp dụng bộ lọc' }}
            </button>
          </form>
        </aside>

        <section class="results" :aria-busy="isLoading" aria-live="polite">
          <div class="result-toolbar">
            <p class="result-count">{{ resultText }}</p>
            <div class="toolbar-actions">
              <button
                class="filter-toggle"
                type="button"
                aria-controls="product-filters"
                :aria-expanded="isFilterOpen"
                @click="isFilterOpen = true"
              >
                <AppIcon name="menu" :size="16" />
                Bộ lọc
                <span v-if="activeFilters.length" class="filter-count">{{ activeFilters.length }}</span>
              </button>
              <label class="sort-field">
                <span>Sắp xếp</span>
                <select
                  v-model="form.sort"
                  class="form-select sort-select"
                  aria-label="Sắp xếp sản phẩm"
                  @change="applyFilters"
                >
                  <option v-for="option in sortOptions" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>
              </label>
            </div>
          </div>

          <div v-if="activeFilters.length" class="active-filters" aria-label="Bộ lọc đang áp dụng">
            <button
              v-for="filter in activeFilters"
              :key="filter.key"
              type="button"
              :aria-label="`Bỏ ${filter.label}`"
              @click="removeFilter(filter.key)"
            >
              {{ filter.label }} <AppIcon name="close" :size="12" />
            </button>
            <button class="clear-all" type="button" @click="clearFilters">Xóa tất cả</button>
          </div>

          <div v-if="errorMessage" class="state-box is-error" role="alert">
            <span class="state-icon" aria-hidden="true"><AppIcon name="refresh" :size="22" /></span>
            <div>
              <strong>Không tải được sản phẩm</strong>
              <p>{{ errorMessage }}</p>
            </div>
            <button class="ocop-btn-main" type="button" @click="loadProducts">Thử lại</button>
          </div>

          <div v-else-if="isLoading" class="product-grid" aria-label="Đang tải sản phẩm">
            <div v-for="index in 6" :key="index" class="loading-card placeholder-glow">
              <span class="placeholder media-placeholder" />
              <span class="skeleton-copy">
                <span class="placeholder col-6" />
                <span class="placeholder col-10" />
                <span class="placeholder col-8" />
              </span>
            </div>
          </div>

          <div v-else-if="products.length" class="product-grid">
            <ProductCard v-for="product in products" :key="product.id" :product="product" />
          </div>

          <div v-else class="state-box is-empty" role="status">
            <span class="state-icon" aria-hidden="true"><AppIcon name="search" :size="22" /></span>
            <div>
              <strong>Chưa tìm thấy sản phẩm phù hợp</strong>
              <p>Thử từ khóa khác, chọn nhóm "Tất cả" hoặc bỏ bớt bộ lọc.</p>
            </div>
            <button class="ocop-btn-ghost" type="button" @click="clearFilters">Xóa bộ lọc</button>
          </div>

          <nav v-if="!isLoading && totalPages > 1" class="pagination-wrap" aria-label="Phân trang">
            <button
              class="page-step"
              type="button"
              :disabled="currentPage === 1"
              @click="goToPage(currentPage - 1)"
            >
              <AppIcon name="chevronLeft" :size="16" /> Trang trước
            </button>
            <div class="page-number-list">
              <button
                v-for="page in pageNumbers"
                :key="page"
                class="page-number"
                :class="{ active: page === currentPage }"
                type="button"
                :aria-current="page === currentPage ? 'page' : undefined"
                :aria-label="`Trang ${page}`"
                @click="goToPage(page)"
              >
                {{ page }}
              </button>
            </div>
            <button
              class="page-step"
              type="button"
              :disabled="currentPage === totalPages"
              @click="goToPage(currentPage + 1)"
            >
              Trang sau <AppIcon name="chevronRight" :size="16" />
            </button>
          </nav>
        </section>
      </div>
    </div>
  </main>
</template>

<style scoped>
.products-page {
  min-height: calc(100vh - 4.5rem);
  background: var(--ocop-surface);
}

/* Đầu trang: ảnh đồi chè thật, lớp tối để chữ trắng đọc rõ, ô tìm nổi bật (search-first). */
.page-banner {
  position: relative;
  overflow: hidden;
  background: var(--ocop-mist-800);
  color: var(--ocop-white);
}

.banner-photo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  object-position: center 65%;
}

.page-banner::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, color-mix(in srgb, var(--ocop-mist-950) 88%, transparent), color-mix(in srgb, var(--ocop-mist-950) 55%, transparent) 55%, color-mix(in srgb, var(--ocop-mist-950) 25%, transparent));
  content: '';
}

.banner-inner {
  position: relative;
  z-index: 1;
  display: flex;
  padding: var(--ocop-space-8) 0 var(--ocop-space-12);
  flex-direction: column;
  align-items: flex-start;
  gap: var(--ocop-space-3);
}

.breadcrumb-trail {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-mist-200);
  font-size: var(--ocop-font-size-small);
}

.breadcrumb-trail a {
  color: var(--ocop-mist-100);
  text-decoration: none;
}

.breadcrumb-trail a:hover {
  text-decoration: underline;
}

.page-banner h1 {
  margin: 0;
  font-size: clamp(1.875rem, 4vw, 2.75rem);
  font-weight: 800;
  letter-spacing: -0.02em;
}

.page-banner p {
  max-width: 40rem;
  margin: 0;
  color: var(--ocop-mist-100);
  font-size: var(--ocop-font-size-body-lg);
}

.banner-search {
  display: flex;
  width: min(100%, 640px);
  margin-top: var(--ocop-space-3);
  padding: var(--ocop-space-2);
  gap: var(--ocop-space-2);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-overlay);
}

.banner-search-field {
  position: relative;
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
  color: var(--ocop-mist-600);
}

.banner-search-field .app-icon {
  position: absolute;
  left: var(--ocop-space-3);
  pointer-events: none;
}

.banner-search-field input {
  width: 100%;
  height: var(--ocop-control-lg);
  padding: 0 var(--ocop-space-3) 0 calc(var(--ocop-space-8) + var(--ocop-space-2));
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-md);
  outline: 0;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-body-lg);
}

.banner-search-field input:focus {
  border-color: var(--ocop-primary-500);
}

.banner-search button {
  min-width: 96px;
  min-height: var(--ocop-control-lg);
}

/* Chip nhóm sản phẩm nằm sát dưới đầu trang: lọc bằng một chạm. */
.category-strip {
  position: relative;
  z-index: 2;
  margin-top: calc(var(--ocop-space-6) * -1);
}

.category-chips {
  display: flex;
  margin: 0;
  padding: var(--ocop-space-2);
  gap: var(--ocop-space-2);
  overflow-x: auto;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-card);
  list-style: none;
  scrollbar-width: none;
}

.category-chips::-webkit-scrollbar {
  display: none;
}

.chip {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 0 var(--ocop-space-4);
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-pill);
  background: transparent;
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-body);
  font-weight: 600;
  white-space: nowrap;
}

.chip:hover {
  background: var(--ocop-mist-50);
}

.chip:has(.chip-icon) {
  padding-left: 6px;
}

.chip-icon {
  display: grid;
  width: 30px;
  height: 30px;
  place-items: center;
  border-radius: 50%;
  background: var(--chip-bg, var(--ocop-mist-100));
  color: var(--chip-fg, var(--ocop-mist-700));
}

/* Nhóm đang chọn: nền theo màu của nhóm (cùng màu nhãn trên thẻ sản phẩm). */
.chip[aria-pressed='true'] {
  border-color: var(--chip-fg, var(--ocop-mist-800));
  background: var(--chip-fg, var(--ocop-mist-800));
  color: var(--ocop-white);
}

.chip[aria-pressed='true'] .chip-icon {
  background: var(--ocop-white);
}

.results {
  min-width: 0;
}

.products-body {
  padding: var(--ocop-space-8) 0 var(--ocop-space-12);
}

.products-layout {
  display: grid;
  grid-template-columns: 280px minmax(0, 1fr);
  align-items: start;
  gap: var(--ocop-space-8);
}

.filter-aside {
  position: sticky;
  top: calc(var(--ocop-control-lg) + var(--ocop-space-6));
}

.filter-panel {
  display: grid;
  gap: var(--ocop-space-5);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.filter-heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-3);
}

.filter-heading h2 {
  margin: 0;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 750;
}

.btn-reset {
  min-height: var(--ocop-control-sm);
  padding: 0 var(--ocop-space-2);
  border: 0;
  background: transparent;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
}

.filter-close {
  display: none;
}

.filter-group {
  display: grid;
  gap: var(--ocop-space-2);
  margin: 0;
  padding: 0;
  border: 0;
}

.filter-group legend,
.filter-group .form-label {
  margin: 0;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
}

.star-segment {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: var(--ocop-space-2);
}

.star-segment button {
  display: inline-flex;
  min-height: var(--ocop-control-sm);
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-1);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-card);
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-small);
  font-weight: 600;
}

.star-segment button :deep(.app-icon) {
  color: var(--ocop-daquy-500);
}

.star-segment button[aria-pressed='true'] {
  border-color: var(--ocop-mist-800);
  background: var(--ocop-mist-800);
  color: var(--ocop-white);
}

.star-segment button[aria-pressed='true'] :deep(.app-icon) {
  color: var(--ocop-daquy-300);
}

.price-row {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr);
  align-items: center;
  gap: var(--ocop-space-2);
  color: var(--ocop-slate);
}

.filter-error {
  margin: 0;
  padding: var(--ocop-space-2) var(--ocop-space-3);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-danger-soft);
  color: var(--ocop-danger-strong);
  font-size: var(--ocop-font-size-small);
}

.filter-submit {
  width: 100%;
}

.result-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-3);
}

.result-count {
  margin: 0;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-body-lg);
  font-weight: 700;
}

.toolbar-actions {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-2);
}

.filter-toggle {
  display: none;
  min-height: var(--ocop-control-md);
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 0 var(--ocop-space-4);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-card);
  color: var(--ocop-navy);
  font-weight: 700;
}

.filter-count {
  display: grid;
  min-width: 22px;
  height: 22px;
  place-items: center;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-daquy-400);
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-caption);
}

.sort-field {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-2);
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
  white-space: nowrap;
}

.sort-select {
  width: auto;
  min-height: var(--ocop-control-md);
}

.active-filters {
  display: flex;
  margin-top: var(--ocop-space-3);
  flex-wrap: wrap;
  gap: var(--ocop-space-2);
}

.active-filters button {
  display: inline-flex;
  min-height: 36px;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 0 var(--ocop-space-3);
  border: 1px solid var(--ocop-mist-300);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mist-100);
  color: var(--ocop-mist-900);
  font-size: var(--ocop-font-size-small);
  font-weight: 600;
}

.active-filters .clear-all {
  border-color: transparent;
  background: transparent;
  color: var(--ocop-primary-700);
  text-decoration: underline;
}

.product-grid {
  display: grid;
  margin-top: var(--ocop-space-5);
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ocop-space-5);
}

.loading-card {
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.loading-card .placeholder {
  display: block;
}

.media-placeholder {
  width: 100%;
  aspect-ratio: 16 / 10;
}

.skeleton-copy {
  display: grid;
  padding: var(--ocop-space-4);
  gap: var(--ocop-space-3);
}

.state-box {
  display: flex;
  margin-top: var(--ocop-space-5);
  padding: var(--ocop-space-6);
  align-items: center;
  gap: var(--ocop-space-5);
  border: 1px dashed var(--ocop-border-strong);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.state-box > div {
  flex: 1;
}

.state-box strong {
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-body-lg);
}

.state-box p {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-slate);
}

.state-box.is-error {
  border: 1px solid var(--ocop-danger-border);
  background: var(--ocop-danger-soft);
}

.state-box.is-error strong {
  color: var(--ocop-danger-strong);
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

.pagination-wrap {
  display: flex;
  margin-top: var(--ocop-space-8);
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-3);
}

.page-step,
.page-number {
  display: inline-flex;
  min-width: var(--ocop-control-md);
  min-height: var(--ocop-control-md);
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-1);
  padding: 0 var(--ocop-space-3);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-card);
  color: var(--ocop-navy);
  font-weight: 600;
}

.page-step:disabled {
  opacity: 0.45;
}

.page-number-list {
  display: flex;
  gap: var(--ocop-space-1);
}

.page-number.active {
  border-color: var(--ocop-mist-800);
  background: var(--ocop-mist-800);
  color: var(--ocop-white);
}

.filter-scrim {
  display: none;
}

@media (max-width: 991.98px) {
  .products-layout {
    grid-template-columns: minmax(0, 1fr);
  }

  .filter-toggle {
    display: inline-flex;
  }

  /* Điện thoại, máy tính bảng: bộ lọc thành bottom sheet, mở bằng nút "Bộ lọc". */
  .filter-aside {
    position: fixed;
    z-index: 120;
    right: 0;
    bottom: 0;
    left: 0;
    top: auto;
    display: none;
    max-height: 85vh;
    overflow-y: auto;
    border-radius: var(--ocop-radius-xl) var(--ocop-radius-xl) 0 0;
    background: var(--ocop-card);
    box-shadow: var(--ocop-shadow-overlay);
  }

  .filter-aside.open {
    display: block;
  }

  .filter-panel {
    border: 0;
    padding-bottom: calc(var(--ocop-space-5) + env(safe-area-inset-bottom));
  }

  .filter-close {
    display: grid;
    width: var(--ocop-control-md);
    height: var(--ocop-control-md);
    padding: 0;
    place-items: center;
    border: 1px solid var(--ocop-border);
    border-radius: 50%;
    background: var(--ocop-card);
    color: var(--ocop-navy);
  }

  .btn-reset {
    margin-left: auto;
  }

  .star-segment {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .filter-scrim {
    position: fixed;
    z-index: 110;
    inset: 0;
    display: block;
    background: color-mix(in srgb, var(--ocop-mist-950) 45%, transparent);
  }

  .product-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 575.98px) {
  .banner-inner {
    padding: var(--ocop-space-6) 0 var(--ocop-space-12);
  }

  .banner-search button {
    min-width: 72px;
  }

  .result-toolbar {
    flex-wrap: wrap;
  }

  .toolbar-actions {
    width: 100%;
  }

  .sort-field {
    min-width: 0;
    flex: 1;
  }

  .sort-field span {
    display: none;
  }

  .sort-select {
    width: 100%;
  }

  .product-grid {
    gap: var(--ocop-space-3);
  }

  .state-box {
    flex-direction: column;
    align-items: stretch;
  }

  .pagination-wrap {
    gap: var(--ocop-space-2);
  }

  .page-step {
    padding: 0 var(--ocop-space-2);
    font-size: var(--ocop-font-size-small);
  }
}
</style>
