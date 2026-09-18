<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import NewsCard from '@/components/news/NewsCard.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { listNews } from '@/services/news'
import type { NewsListItem } from '@/types/news'

const items = ref<NewsListItem[]>([])
const searchInput = ref('')
const submittedSearch = ref('')
const currentPage = ref(1)
const pageSize = ref(12)
const total = ref(0)
const isLoading = ref(true)
const errorMessage = ref('')
const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))
let requestId = 0

async function loadNews(page = currentPage.value): Promise<void> {
  const id = ++requestId
  currentPage.value = page
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await listNews({ page, page_size: pageSize.value, search: submittedSearch.value || undefined })
    if (id !== requestId) return
    items.value = response.items
    currentPage.value = response.page
    pageSize.value = response.page_size
    total.value = response.total
  } catch (error) {
    if (id !== requestId) return
    items.value = []
    total.value = 0
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải danh sách tin tức. Vui lòng thử lại.')
  } finally {
    if (id === requestId) isLoading.value = false
  }
}
function submitSearch(): void {
  submittedSearch.value = searchInput.value.trim()
  void loadNews(1)
}
function goToPage(page: number): void {
  if (page < 1 || page > totalPages.value || isLoading.value) return
  void loadNews(page)
}
onMounted(() => { void loadNews() })
onUnmounted(() => { requestId++ })
</script>

<template>
  <main class="news-page">
    <section class="page-banner">
      <div class="container py-5">
        <span class="page-eyebrow">Tin tức &amp; sự kiện OCOP</span>
        <h1>Tin tức OCOP Lâm Đồng</h1>
        <p>Cập nhật hoạt động, chính sách và câu chuyện OCOP Lâm Đồng.</p>
      </div>
    </section>
    <div class="container py-5">
      <form class="search-panel mb-4" @submit.prevent="submitSearch">
        <label class="form-label fw-semibold" for="news-search">Tìm kiếm tin tức</label>
        <div class="search-controls">
          <input id="news-search" v-model="searchInput" class="form-control" type="search" placeholder="Nhập từ khóa..." />
          <button class="btn btn-success" type="submit">Tìm kiếm</button>
        </div>
      </form>
      <section aria-live="polite" :aria-busy="isLoading">
        <div v-if="isLoading" class="loading-state" role="status">Đang tải tin tức...</div>
        <div v-else-if="errorMessage" class="alert alert-danger" role="alert">
          <p>{{ errorMessage }}</p>
          <button class="btn btn-outline-danger" type="button" @click="loadNews()">Thử lại</button>
        </div>
        <template v-else>
          <p class="fw-semibold">{{ total }} bài viết phù hợp</p>
          <div v-if="items.length" class="news-grid">
            <NewsCard v-for="news in items" :key="news.id" :news="news" />
          </div>
          <div v-else class="empty-state">
            <strong>Chưa tìm thấy bài viết phù hợp</strong>
            <p>Hãy thử thay đổi từ khóa tìm kiếm.</p>
          </div>
          <nav v-if="totalPages > 1" class="pagination-wrap" aria-label="Phân trang tin tức">
            <button class="btn btn-outline-success" type="button" :disabled="currentPage === 1" @click="goToPage(currentPage - 1)">Trang trước</button>
            <span>Trang {{ currentPage }} / {{ totalPages }}</span>
            <button class="btn btn-outline-success" type="button" :disabled="currentPage === totalPages" @click="goToPage(currentPage + 1)">Trang sau</button>
          </nav>
        </template>
      </section>
    </div>
  </main>
</template>

<style scoped>
.news-page { min-height: calc(100vh - 4.5rem); background: #f7f8f4; }
.page-banner { background: radial-gradient(circle at 82% 25%, rgb(184 214 145 / 52%), transparent 22rem), #edf4e5; }
.page-eyebrow { color: #2f6f3e; font-size: .76rem; font-weight: 750; letter-spacing: .11em; text-transform: uppercase; }
h1 { margin: .7rem 0; color: #18351f; font-size: clamp(2.2rem, 5vw, 3.7rem); font-weight: 800; }
.page-banner p { max-width: 42rem; margin: 0; color: #627066; }
.search-panel { padding: 1.25rem; border: 1px solid rgb(29 72 39 / 10%); border-radius: 1rem; background: #fff; }
.search-controls { display: flex; gap: .75rem; }
.search-controls button { flex-shrink: 0; }
.news-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(min(100%, 19rem), 1fr)); gap: 1.25rem; }
.empty-state, .loading-state { padding: 5rem 1.5rem; border: 1px dashed #becbbb; border-radius: 1rem; background: #fff; text-align: center; color: #627066; }
.empty-state strong { color: #203b27; font-size: 1.15rem; }
.empty-state p { margin: .5rem 0 0; }
.pagination-wrap { display: flex; flex-wrap: wrap; align-items: center; justify-content: center; gap: 1rem; margin-top: 2rem; }
@media (max-width: 575px) { .search-controls { flex-direction: column; } }
</style>