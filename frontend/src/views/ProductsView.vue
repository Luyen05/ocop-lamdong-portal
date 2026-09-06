<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import ProductCard from '@/components/products/ProductCard.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getCategories } from '@/services/categories'
import { getProducts } from '@/services/products'
import type { Category } from '@/types/category'
import type {
  ProductFilters,
  ProductListItem,
  ProductSort,
} from '@/types/product'

const route = useRoute()
const router = useRouter()

const categories = ref<Category[]>([])
const products = ref<ProductListItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const pageSize = 12
const isLoading = ref(false)
const errorMessage = ref('')

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
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await getProducts(filtersFromRoute())
    products.value = response.items
    total.value = response.total
  } catch (error) {
    products.value = []
    total.value = 0
    errorMessage.value = getApiErrorMessage(
      error,
      'Không thể tải danh sách sản phẩm. Vui lòng thử lại.',
    )
  } finally {
    isLoading.value = false
  }
}

async function loadCategories(): Promise<void> {
  try {
    categories.value = (await getCategories()).items
  } catch {
    categories.value = []
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
  await router.push({ name: 'products', query: filterQuery() })
}

async function clearFilters(): Promise<void> {
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

async function goToPage(page: number): Promise<void> {
  if (page < 1 || page > totalPages.value || page === currentPage.value) return
  await router.push({ name: 'products', query: filterQuery(page) })
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
})
</script>

<template>
  <main class="products-page">
    <section class="page-banner">
      <div class="container py-5">
        <span class="page-eyebrow">Tinh hoa sản phẩm địa phương</span>
        <h1>Sản phẩm OCOP Lâm Đồng</h1>
        <p>Tìm kiếm sản phẩm theo danh mục, hạng sao, địa phương và mức giá.</p>
      </div>
    </section>

    <div class="container py-5">
      <div class="products-layout">
        <aside>
          <form class="filter-panel" @submit.prevent="applyFilters">
            <div class="filter-heading">
              <h2>Bộ lọc</h2>
              <button class="btn-reset" type="button" @click="clearFilters">Xóa lọc</button>
            </div>

            <div>
              <label class="form-label" for="product-search">Từ khóa</label>
              <input
                id="product-search"
                v-model.trim="form.search"
                class="form-control"
                type="search"
                placeholder="Tên sản phẩm, chủ thể..."
              />
            </div>

            <div>
              <label class="form-label" for="product-category">Danh mục</label>
              <select id="product-category" v-model="form.category" class="form-select">
                <option value="">Tất cả danh mục</option>
                <option v-for="category in categories" :key="category.id" :value="category.slug">
                  {{ category.name }}
                </option>
              </select>
            </div>

            <div class="row g-2">
              <div class="col-6">
                <label class="form-label" for="product-star">Hạng sao</label>
                <select id="product-star" v-model="form.star" class="form-select">
                  <option value="">Tất cả</option>
                  <option value="3">3 sao</option>
                  <option value="4">4 sao</option>
                  <option value="5">5 sao</option>
                </select>
              </div>
              <div class="col-6">
                <label class="form-label" for="product-district">Địa bàn</label>
                <input
                  id="product-district"
                  v-model.trim="form.district"
                  class="form-control"
                  type="text"
                  placeholder="Đà Lạt"
                />
              </div>
            </div>

            <div>
              <label class="form-label">Khoảng giá</label>
              <div class="row g-2">
                <div class="col-6">
                  <input
                    v-model="form.minPrice"
                    class="form-control"
                    type="number"
                    min="0"
                    step="1000"
                    aria-label="Giá tối thiểu"
                    placeholder="Từ"
                  />
                </div>
                <div class="col-6">
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
              </div>
            </div>

            <button class="btn btn-success w-100" type="submit">Áp dụng bộ lọc</button>
          </form>
        </aside>

        <section aria-live="polite">
          <div class="result-toolbar">
            <p class="mb-0 fw-semibold">{{ resultText }}</p>
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
          </div>

          <div v-if="errorMessage" class="alert alert-danger" role="alert">
            {{ errorMessage }}
            <button class="btn btn-sm btn-outline-danger ms-2" type="button" @click="loadProducts">
              Thử lại
            </button>
          </div>

          <div v-else-if="isLoading" class="product-grid" aria-label="Đang tải sản phẩm">
            <div v-for="index in 6" :key="index" class="loading-card placeholder-glow">
              <span class="placeholder col-12 media-placeholder" />
              <span class="placeholder col-7 mt-4" />
              <span class="placeholder col-10 mt-3" />
              <span class="placeholder col-5 mt-3" />
            </div>
          </div>

          <div v-else-if="products.length" class="product-grid">
            <ProductCard v-for="product in products" :key="product.id" :product="product" />
          </div>

          <div v-else class="empty-state">
            <strong>Chưa tìm thấy sản phẩm phù hợp</strong>
            <p>Hãy thử thay đổi từ khóa hoặc xóa bớt bộ lọc.</p>
            <button class="btn btn-outline-success" type="button" @click="clearFilters">
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
      </div>
    </div>
  </main>
</template>

<style scoped>
.products-page {
  min-height: calc(100vh - 4.5rem);
  background: #f7f8f4;
}

.page-banner {
  background:
    radial-gradient(circle at 82% 25%, rgb(184 214 145 / 52%), transparent 22rem),
    #edf4e5;
}

.page-eyebrow {
  color: #2f6f3e;
  font-size: 0.76rem;
  font-weight: 750;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.page-banner h1 {
  margin: 0.7rem 0;
  color: #18351f;
  font-size: clamp(2.2rem, 5vw, 3.7rem);
  font-weight: 800;
}

.page-banner p {
  max-width: 42rem;
  margin: 0;
  color: #627066;
}

.products-layout {
  display: grid;
  gap: 2rem;
}

.filter-panel {
  display: grid;
  gap: 1.15rem;
  padding: 1.25rem;
  border: 1px solid rgb(29 72 39 / 10%);
  border-radius: 1rem;
  background: #fff;
}

.filter-heading,
.result-toolbar,
.pagination-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
}

.filter-heading h2 {
  margin: 0;
  font-size: 1.15rem;
}

.filter-panel .form-label {
  color: #4f5d52;
  font-size: 0.84rem;
  font-weight: 700;
}

.btn-reset {
  border: 0;
  background: transparent;
  color: #2f6f3e;
  font-size: 0.82rem;
  font-weight: 700;
}

.result-toolbar {
  margin-bottom: 1.25rem;
}

.sort-select {
  width: min(12rem, 48%);
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(min(100%, 15rem), 1fr));
  gap: 1.25rem;
}

.loading-card {
  min-height: 27rem;
  padding: 1rem;
  border-radius: 1rem;
  background: #fff;
}

.media-placeholder {
  display: block;
  height: 14rem;
  border-radius: 0.75rem;
}

.empty-state {
  padding: 5rem 1.5rem;
  border: 1px dashed #becbbb;
  border-radius: 1rem;
  background: #fff;
  text-align: center;
}

.empty-state strong {
  display: block;
  color: #203b27;
  font-size: 1.15rem;
}

.empty-state p {
  margin: 0.5rem 0 1.25rem;
  color: #6b756d;
}

.pagination-wrap {
  justify-content: center;
  margin-top: 2rem;
}

.pagination-wrap span {
  color: #5f6b62;
  font-size: 0.9rem;
  font-weight: 650;
}

@media (min-width: 992px) {
  .products-layout {
    grid-template-columns: 17rem minmax(0, 1fr);
    align-items: start;
  }

  .filter-panel {
    position: sticky;
    top: 5.5rem;
  }
}
</style>
