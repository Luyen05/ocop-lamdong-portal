<script setup lang="ts">
import axios from 'axios'
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ProductCard from '@/components/products/ProductCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { teaPhoto } from '@/constants/photos'
import { useFocusTrap } from '@/composables/useFocusTrap'
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
import { scrollBehavior } from '@/utils/motion'
import {
  DISTRICT_MAX_LENGTH,
  hasPriceConflict,
  normalizeProductFilters,
  PRICE_CONFLICT_MESSAGE,
  priceNumber,
  SEARCH_MAX_LENGTH,
  VALID_STARS,
  type ProductFilterValues,
} from '@/utils/product-filters'

const route = useRoute()
const router = useRouter()

const categories = ref<Category[]>([])
const categoriesLoaded = ref(false)
const districts = ref<string[]>([])
const products = ref<ProductListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 12
const isLoading = ref(false)
const errorMessage = ref('')
// 422: điều kiện lọc sai, thử lại cùng điều kiện cũng vô ích nên không hiện nút "Thử lại".
const errorRetryable = ref(true)
const validationMessage = ref('')
let latestRequestId = 0

// Trình bày: ngăn kéo bộ lọc trên điện thoại (bottom sheet) và lựa chọn nhanh danh mục, hạng sao.
const isFilterOpen = ref(false)
const bannerPhotoFailed = ref(false)
const starOptions = [
  { value: '', label: 'Tất cả' },
  ...VALID_STARS.map((value) => ({ value, label: `${value} sao` })),
]

// Nháp trong form: chỉ từ khóa, địa bàn và khoảng giá là nháp (chỉ áp dụng khi bấm Tìm/Áp dụng).
// Nhóm, hạng sao và sắp xếp áp dụng ngay nên luôn phản chiếu URL.
const form = reactive<ProductFilterValues>({
  search: '',
  category: '',
  star: '',
  district: '',
  minPrice: '',
  maxPrice: '',
  sort: 'newest',
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
// Đang tải thì không hiện số cũ; lỗi thì ẩn hẳn dòng này (tránh "0 sản phẩm phù hợp" sai sự thật).
const resultText = computed(() => (isLoading.value ? 'Đang tải…' : `${total.value} sản phẩm phù hợp`))
const pageNumbers = computed(() => {
  const maxVisible = 5
  let start = Math.max(1, currentPage.value - Math.floor(maxVisible / 2))
  const end = Math.min(totalPages.value, start + maxVisible - 1)
  start = Math.max(1, end - maxVisible + 1)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})

function queryText(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

// Giá trị lọc trong URL sau khi chuẩn hóa (tham số sai bị bỏ), chưa xét min > max.
const queryFilters = computed<ProductFilterValues>(() => normalizeProductFilters({
  search: route.query.search,
  category: route.query.category,
  star: route.query.star,
  district: route.query.district,
  minPrice: route.query.min_price,
  maxPrice: route.query.max_price,
  sort: route.query.sort,
}))

// URL có min > max: xử lý như applyFilters (báo lỗi, không áp dụng khoảng giá), tránh 422 từ backend.
const urlPriceConflict = computed(() => hasPriceConflict(queryFilters.value))

const appliedForm = computed<ProductFilterValues>(() => {
  const filters = queryFilters.value
  return urlPriceConflict.value ? { ...filters, minPrice: '', maxPrice: '' } : filters
})

function categoryLabel(slug: string): string | null {
  const category = categories.value.find((item) => item.slug === slug)
  if (category) return category.name
  // Danh mục chưa tải xong thì chưa hiện chip (tránh lộ slug thô); tải xong mà không có thì báo rõ.
  return categoriesLoaded.value ? 'không hợp lệ' : null
}

const activeFilters = computed(() => {
  const applied = appliedForm.value
  const filters: Array<{ key: keyof typeof form; label: string }> = []
  if (applied.search) filters.push({ key: 'search', label: `Từ khóa: ${applied.search}` })
  if (applied.category) {
    const name = categoryLabel(applied.category)
    if (name) filters.push({ key: 'category', label: `Danh mục: ${name}` })
  }
  if (applied.star) filters.push({ key: 'star', label: `${applied.star} sao` })
  if (applied.district) filters.push({ key: 'district', label: `Địa bàn: ${applied.district}` })
  if (applied.minPrice) filters.push({ key: 'minPrice', label: `Giá từ ${Number(applied.minPrice).toLocaleString('vi-VN')}đ` })
  if (applied.maxPrice) filters.push({ key: 'maxPrice', label: `Giá đến ${Number(applied.maxPrice).toLocaleString('vi-VN')}đ` })
  return filters
})

// Chỉ ghi đè ô nháp khi giá trị đó trong URL đổi (Back/Forward, bỏ chip...). Bấm chip nhóm, hạng sao
// hay đổi sắp xếp không làm mất những gì người dùng đang gõ ở ô khác.
let hydrated: ProductFilterValues | null = null

function hydrateFormFromQuery(forceAll = false): void {
  const next = queryFilters.value
  const target = form as Record<keyof ProductFilterValues, string>
  for (const key of Object.keys(next) as Array<keyof ProductFilterValues>) {
    if (forceAll || !hydrated || hydrated[key] !== next[key]) target[key] = next[key]
  }
  hydrated = { ...next }
  validationMessage.value = urlPriceConflict.value ? PRICE_CONFLICT_MESSAGE : ''
  const requestedPage = Number(queryText(route.query.page))
  currentPage.value = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1
}

function filtersFromRoute(): ProductFilters {
  const applied = appliedForm.value
  return {
    page: currentPage.value,
    page_size: pageSize,
    search: applied.search || undefined,
    category: applied.category || undefined,
    star: applied.star ? Number(applied.star) : undefined,
    district: applied.district || undefined,
    min_price: priceNumber(applied.minPrice),
    max_price: priceNumber(applied.maxPrice),
    sort: applied.sort,
  }
}

// Sau khi đổi trang hoặc "Thử lại", nút vừa bấm có thể biến mất: đưa focus về dòng kết quả (hoặc khối lỗi).
const resultCountRef = ref<HTMLElement | null>(null)
const errorBoxRef = ref<HTMLElement | null>(null)
let focusResultsAfterLoad = false

async function settleFocus(): Promise<void> {
  if (!focusResultsAfterLoad) return
  focusResultsAfterLoad = false
  await nextTick()
  const target = errorMessage.value ? errorBoxRef.value : resultCountRef.value
  target?.focus({ preventScroll: true })
}

async function loadProducts(): Promise<void> {
  const requestId = ++latestRequestId
  isLoading.value = true
  errorMessage.value = ''
  errorRetryable.value = true
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
    isLoading.value = false
    void settleFocus()
  } catch (error) {
    if (requestId !== latestRequestId) return
    products.value = []
    total.value = 0
    if (axios.isAxiosError(error) && error.response?.status === 422) {
      errorRetryable.value = false
      errorMessage.value = 'Từ khóa, địa bàn hoặc khoảng giá chưa phù hợp. Hãy chỉnh lại hoặc xóa bộ lọc.'
    } else {
      errorMessage.value = getApiErrorMessage(
        error,
        'Không thể tải danh sách sản phẩm. Vui lòng thử lại.',
      )
    }
    isLoading.value = false
    void settleFocus()
  } finally {
    if (requestId === latestRequestId) isLoading.value = false
  }
}

async function retryLoad(): Promise<void> {
  focusResultsAfterLoad = true
  void loadProducts()
  // Nút "Thử lại" biến mất ngay khi bắt đầu tải: giữ focus ở dòng kết quả trong lúc chờ.
  await nextTick()
  resultCountRef.value?.focus({ preventScroll: true })
}

async function loadCategories(): Promise<void> {
  try {
    categories.value = (await getCategories()).items
    categoriesLoaded.value = true
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

function filterQuery(page = 1, filters: ProductFilterValues = appliedForm.value): Record<string, string> {
  const normalized = normalizeProductFilters(filters)
  const query: Record<string, string> = {}
  if (page > 1) query.page = String(page)
  if (normalized.search) query.search = normalized.search
  if (normalized.category) query.category = normalized.category
  if (normalized.star) query.star = normalized.star
  if (normalized.district) query.district = normalized.district
  if (normalized.minPrice) query.min_price = normalized.minPrice
  if (normalized.maxPrice) query.max_price = normalized.maxPrice
  if (normalized.sort !== 'newest') query.sort = normalized.sort
  return query
}

async function applyFilters(): Promise<void> {
  validationMessage.value = ''
  if (hasPriceConflict(form)) {
    validationMessage.value = PRICE_CONFLICT_MESSAGE
    return
  }
  await router.push({ name: 'products', query: filterQuery(1, form) })
}

async function clearFilters(): Promise<void> {
  validationMessage.value = ''
  await router.push({ name: 'products' })
  hydrateFormFromQuery(true)
}

async function removeFilter(key: keyof typeof form): Promise<void> {
  const filters = { ...appliedForm.value }
  if (key === 'sort') filters.sort = 'newest'
  else filters[key] = ''
  await router.push({ name: 'products', query: filterQuery(1, filters) })
}

// Chip nhóm, nút hạng sao và ô sắp xếp áp dụng ngay, chỉ đổi đúng bộ lọc đó trên các bộ lọc đang áp dụng;
// giá trị đang gõ dở trong form (chưa bấm Tìm/Áp dụng) không bị gửi kèm và cũng không bị xóa.
async function applyQuickFilter(change: Partial<ProductFilterValues>): Promise<void> {
  const filters = { ...appliedForm.value, ...change }
  await router.push({ name: 'products', query: filterQuery(1, filters) })
}

async function selectCategory(slug: string): Promise<void> {
  await applyQuickFilter({ category: slug })
}

async function selectStar(value: string): Promise<void> {
  await applyQuickFilter({ star: value })
}

async function changeSort(): Promise<void> {
  await applyQuickFilter({ sort: form.sort })
}

async function submitFromDrawer(): Promise<void> {
  await applyFilters()
  if (!validationMessage.value) isFilterOpen.value = false
}

async function goToPage(page: number): Promise<void> {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  focusResultsAfterLoad = true
  await router.push({ name: 'products', query: filterQuery(page) })
  window.scrollTo({ top: 0, behavior: scrollBehavior() })
}

// Ngăn kéo bộ lọc: chỉ là hộp thoại (bottom sheet) ở màn hẹp, cùng mốc với CSS (max-width: 991.98px).
const SHEET_QUERY = '(max-width: 991.98px)'
const isSheet = ref(false)
const sheetOpen = computed(() => isFilterOpen.value && isSheet.value)
const filterAsideRef = ref<HTMLElement | null>(null)
const filterToggleRef = ref<HTMLButtonElement | null>(null)
const filterCloseRef = ref<HTMLButtonElement | null>(null)
let sheetMedia: MediaQueryList | null = null

function syncSheetMode(): void {
  isSheet.value = Boolean(sheetMedia?.matches)
  // Quay lại màn rộng: bộ lọc là cột cố định, không còn là ngăn kéo.
  if (!isSheet.value) isFilterOpen.value = false
}

useFocusTrap(sheetOpen, filterAsideRef, {
  onEscape: () => { isFilterOpen.value = false },
  initialFocus: () => filterCloseRef.value,
  returnFocusTo: () => filterToggleRef.value,
})

// Ô tìm kiếm và dải chip nhóm: gợi ý cuộn ngang khi còn chip bị che.
const chipsRef = ref<HTMLElement | null>(null)
const chipsFade = reactive({ start: false, end: false })

function updateChipsFade(): void {
  const element = chipsRef.value
  if (!element) return
  const max = element.scrollWidth - element.clientWidth
  chipsFade.start = element.scrollLeft > 1
  chipsFade.end = max > 1 && element.scrollLeft < max - 1
}

let chipsObserver: ResizeObserver | null = null

watch(
  () => route.query,
  () => {
    hydrateFormFromQuery()
    void loadProducts()
  },
  { deep: true, immediate: true },
)

// Danh sách nhóm tải xong mới đo được độ rộng dải chip.
watch(() => categories.value.length, () => void nextTick(updateChipsFade))

onMounted(() => {
  void loadCategories()
  void loadFilterOptions()
  document.title = 'Sản phẩm OCOP | OCOP Lâm Đồng'
  if (typeof window.matchMedia === 'function') {
    sheetMedia = window.matchMedia(SHEET_QUERY)
    sheetMedia.addEventListener?.('change', syncSheetMode)
    isSheet.value = sheetMedia.matches
  }
  if (typeof ResizeObserver !== 'undefined' && chipsRef.value) {
    chipsObserver = new ResizeObserver(updateChipsFade)
    chipsObserver.observe(chipsRef.value)
  }
  updateChipsFade()
})

onBeforeUnmount(() => {
  sheetMedia?.removeEventListener?.('change', syncSheetMode)
  chipsObserver?.disconnect()
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
        <p>Đặc sản được công nhận OCOP, tìm theo nhóm sản phẩm, hạng sao, địa phương và mức giá.</p>

        <form class="banner-search" role="search" @submit.prevent="applyFilters">
          <label class="banner-search-field">
            <span class="visually-hidden">Tìm theo tên sản phẩm hoặc chủ thể</span>
            <AppIcon name="search" :size="18" />
            <input
              id="product-search"
              v-model.trim="form.search"
              type="search"
              :maxlength="SEARCH_MAX_LENGTH"
              placeholder="Tìm sản phẩm, chủ thể"
            />
          </label>
          <button class="ocop-btn-accent" type="submit">Tìm</button>
        </form>
      </div>
    </section>

    <div class="site-content category-strip">
      <div
        class="category-chips-wrap"
        :class="{ 'fade-start': chipsFade.start, 'fade-end': chipsFade.end }"
      >
        <ul ref="chipsRef" class="category-chips" aria-label="Lọc theo nhóm sản phẩm" @scroll.passive="updateChipsFade">
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
    </div>

    <div class="site-content products-body">
      <div class="products-layout">
        <div v-if="isFilterOpen" class="filter-scrim" aria-hidden="true" @click="isFilterOpen = false" />
        <aside
          id="product-filters"
          ref="filterAsideRef"
          class="filter-aside"
          :class="{ open: isFilterOpen }"
          aria-label="Bộ lọc sản phẩm"
        >
          <div
            class="filter-dialog"
            :role="sheetOpen ? 'dialog' : undefined"
            :aria-modal="sheetOpen ? 'true' : undefined"
            :aria-labelledby="sheetOpen ? 'product-filters-title' : undefined"
            :tabindex="sheetOpen ? -1 : undefined"
          >
            <form class="filter-panel" @submit.prevent="submitFromDrawer">
              <div class="filter-heading">
                <h2 id="product-filters-title">Bộ lọc</h2>
                <button class="btn-reset" type="button" @click="clearFilters">Xóa tất cả</button>
                <button ref="filterCloseRef" class="filter-close" type="button" aria-label="Đóng bộ lọc" @click="isFilterOpen = false">
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
                  :maxlength="DISTRICT_MAX_LENGTH"
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
                    inputmode="numeric"
                    min="0"
                    aria-label="Giá tối thiểu"
                    placeholder="Từ"
                  />
                  <span aria-hidden="true">–</span>
                  <input
                    v-model="form.maxPrice"
                    class="form-control"
                    type="number"
                    inputmode="numeric"
                    min="0"
                    aria-label="Giá tối đa"
                    placeholder="Đến"
                  />
                </div>
              </fieldset>

              <p v-if="validationMessage" class="filter-error" role="alert">
                {{ validationMessage }}
              </p>
              <button class="ocop-btn-main filter-submit" type="submit">Áp dụng bộ lọc</button>
            </form>
          </div>
        </aside>

        <section class="results" :aria-busy="isLoading">
          <div class="result-toolbar">
            <p v-show="!errorMessage" ref="resultCountRef" class="result-count" role="status" tabindex="-1">{{ resultText }}</p>
            <div class="toolbar-actions">
              <button
                ref="filterToggleRef"
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
                  @change="changeSort"
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
              :title="filter.label"
              :aria-label="`Bỏ ${filter.label}`"
              @click="removeFilter(filter.key)"
            >
              <span class="filter-chip-label">{{ filter.label }}</span> <AppIcon name="close" :size="12" />
            </button>
            <button class="clear-all" type="button" @click="clearFilters">Xóa tất cả</button>
          </div>

          <div v-if="errorMessage" ref="errorBoxRef" class="state-box is-error" role="alert" tabindex="-1">
            <span class="state-icon" aria-hidden="true"><AppIcon name="refresh" :size="22" /></span>
            <div>
              <strong>{{ errorRetryable ? 'Không tải được sản phẩm' : 'Điều kiện lọc không hợp lệ' }}</strong>
              <p>{{ errorMessage }}</p>
            </div>
            <button v-if="errorRetryable" class="ocop-btn-main" type="button" @click="retryLoad">Thử lại</button>
            <button v-else class="ocop-btn-ghost" type="button" @click="clearFilters">Xóa bộ lọc</button>
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

          <div v-else-if="products.length" class="product-grid stagger-in">
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

          <nav
            v-if="totalPages > 1"
            class="pagination-wrap"
            :class="{ 'is-loading': isLoading }"
            :aria-busy="isLoading"
            aria-label="Phân trang"
          >
            <button
              class="page-step"
              type="button"
              aria-label="Trang trước"
              :disabled="currentPage === 1"
              @click="goToPage(currentPage - 1)"
            >
              <AppIcon name="chevronLeft" :size="16" /> <span class="page-step-label">Trang trước</span>
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
              aria-label="Trang sau"
              :disabled="currentPage === totalPages"
              @click="goToPage(currentPage + 1)"
            >
              <span class="page-step-label">Trang sau</span> <AppIcon name="chevronRight" :size="16" />
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

.category-chips-wrap {
  position: relative;
}

/* Gợi ý còn chip bị che: mép mờ cùng màu nền thẻ ở phía còn nội dung cuộn được. */
.category-chips-wrap::before,
.category-chips-wrap::after {
  position: absolute;
  z-index: 1;
  top: 1px;
  bottom: 1px;
  width: var(--ocop-space-12);
  opacity: 0;
  pointer-events: none;
  content: '';
  transition: opacity var(--ocop-transition);
}

.category-chips-wrap::before {
  left: 1px;
  border-radius: calc(var(--ocop-radius-lg) - 1px) 0 0 calc(var(--ocop-radius-lg) - 1px);
  background: linear-gradient(to right, var(--ocop-card), color-mix(in srgb, var(--ocop-card) 0%, transparent));
}

.category-chips-wrap::after {
  right: 1px;
  border-radius: 0 calc(var(--ocop-radius-lg) - 1px) calc(var(--ocop-radius-lg) - 1px) 0;
  background: linear-gradient(to left, var(--ocop-card), color-mix(in srgb, var(--ocop-card) 0%, transparent));
}

.category-chips-wrap.fade-start::before,
.category-chips-wrap.fade-end::after {
  opacity: 1;
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

.filter-dialog {
  min-width: 0;
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
  max-width: 100%;
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

.filter-chip-label {
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
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
  transition: opacity var(--ocop-transition);
  margin-top: var(--ocop-space-8);
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-3);
}

.page-step,
.page-number {
  display: inline-flex;
  white-space: nowrap;
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

.pagination-wrap.is-loading {
  opacity: 0.6;
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

@media (prefers-reduced-motion: reduce) {
  .category-chips-wrap::before,
  .category-chips-wrap::after,
  .pagination-wrap {
    transition: none;
  }
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

  .banner-search-field input {
    font-size: var(--ocop-font-size-body);
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

  /* Màn hẹp: nút Trước/Sau chỉ còn mũi tên (tên vẫn có trong aria-label) để cả hàng vừa một dòng. */
  .page-step {
    padding: 0 var(--ocop-space-2);
    font-size: var(--ocop-font-size-small);
  }

  .page-step-label {
    display: none;
  }
}
</style>
