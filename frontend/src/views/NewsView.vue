<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import NewsCard from '@/components/news/NewsCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getNews } from '@/services/news'
import type { NewsItem } from '@/types/news'

const route = useRoute()
const router = useRouter()
const pageSize = 9

const search = ref('')
const articles = ref<NewsItem[]>([])
const total = ref(0)
const currentPage = ref(1)
const isLoading = ref(false)
const errorMessage = ref('')
let latestRequestId = 0

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize)))
const pageNumbers = computed(() => {
  const start = Math.max(1, Math.min(currentPage.value - 2, totalPages.value - 4))
  const end = Math.min(totalPages.value, start + 4)
  return Array.from({ length: end - start + 1 }, (_, index) => start + index)
})

function queryText(value: unknown): string {
  return typeof value === 'string' ? value : ''
}

function hydrateFromQuery(): void {
  search.value = queryText(route.query.search)
  const requestedPage = Number(route.query.page)
  currentPage.value = Number.isInteger(requestedPage) && requestedPage > 0 ? requestedPage : 1
}

async function loadNews(): Promise<void> {
  const requestId = ++latestRequestId
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await getNews({
      page: currentPage.value,
      page_size: pageSize,
      search: search.value || undefined,
    })
    if (requestId !== latestRequestId) return
    articles.value = response.items
    total.value = response.total

    const availablePages = Math.max(1, Math.ceil(response.total / pageSize))
    if (response.total > 0 && currentPage.value > availablePages) {
      await goToPage(availablePages, true)
    }
  } catch (error) {
    if (requestId !== latestRequestId) return
    articles.value = []
    total.value = 0
    errorMessage.value = getApiErrorMessage(
      error,
      'Chưa thể tải tin tức từ nguồn OCOP. Vui lòng thử lại.',
    )
  } finally {
    if (requestId === latestRequestId) isLoading.value = false
  }
}

async function submitSearch(): Promise<void> {
  const keyword = search.value.trim()
  await router.push({ name: 'news', query: keyword ? { search: keyword } : {} })
}

async function clearSearch(): Promise<void> {
  search.value = ''
  await router.push({ name: 'news' })
}

async function goToPage(page: number, replace = false): Promise<void> {
  if (page < 1 || page > totalPages.value) return
  const query: Record<string, string> = {}
  if (search.value) query.search = search.value
  if (page > 1) query.page = String(page)
  await (replace ? router.replace({ name: 'news', query }) : router.push({ name: 'news', query }))
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

watch(
  () => route.query,
  () => {
    hydrateFromQuery()
    void loadNews()
  },
  { deep: true, immediate: true },
)
</script>

<template>
  <main class="news-page">
    <header class="news-hero">
      <div class="site-content hero-inner">
        <span class="eyebrow"><AppIcon name="newspaper" :size="14" /> Tin tức &amp; sự kiện</span>
        <h1>Hoạt động OCOP Lâm Đồng</h1>
        <p>Theo dõi chương trình OCOP, hoạt động xúc tiến và những thông tin mới từ cổng thông tin chính thức.</p>

        <form class="news-search" role="search" @submit.prevent="submitSearch">
          <label class="visually-hidden" for="news-search-input">Tìm kiếm tin tức</label>
          <AppIcon name="search" :size="18" />
          <input
            id="news-search-input"
            v-model="search"
            type="search"
            maxlength="150"
            placeholder="Tìm theo tiêu đề hoặc nội dung..."
          />
          <button type="submit">Tìm kiếm</button>
        </form>
      </div>
    </header>

    <section class="site-content news-content" aria-labelledby="news-list-title">
      <div class="content-heading">
        <div>
          <h2 id="news-list-title">Tin mới cập nhật</h2>
          <p v-if="!isLoading">{{ total }} bài viết từ Cổng TTĐT OCOP Lâm Đồng</p>
        </div>
        <button v-if="search" type="button" class="clear-button" @click="clearSearch">Xóa tìm kiếm</button>
      </div>

      <div v-if="isLoading" class="news-grid" aria-live="polite" aria-label="Đang tải tin tức">
        <div v-for="index in 6" :key="index" class="news-skeleton placeholder-glow">
          <span class="placeholder media-placeholder" />
          <span class="placeholder col-5" />
          <span class="placeholder col-10" />
          <span class="placeholder col-8" />
        </div>
      </div>

      <div v-else-if="errorMessage" class="state-card error-state" role="alert">
        <span class="state-icon"><AppIcon name="refresh" :size="26" /></span>
        <strong>Chưa thể tải tin tức</strong>
        <p>{{ errorMessage }}</p>
        <button type="button" @click="loadNews">Thử lại</button>
      </div>

      <div v-else-if="!articles.length" class="state-card">
        <span class="state-icon"><AppIcon name="search" :size="26" /></span>
        <strong>Không tìm thấy bài viết phù hợp</strong>
        <p>Hãy thử từ khóa ngắn hơn hoặc xóa điều kiện tìm kiếm.</p>
        <button v-if="search" type="button" @click="clearSearch">Xem tất cả tin</button>
      </div>

      <div v-else class="news-grid">
        <NewsCard v-for="article in articles" :key="article.id" :article="article" />
      </div>

      <nav v-if="!isLoading && !errorMessage && totalPages > 1" class="pagination-nav" aria-label="Phân trang tin tức">
        <button type="button" :disabled="currentPage <= 1" @click="goToPage(currentPage - 1)">
          <AppIcon name="chevronLeft" :size="14" /> Trước
        </button>
        <button
          v-for="page in pageNumbers"
          :key="page"
          type="button"
          class="page-number"
          :class="{ active: page === currentPage }"
          :aria-current="page === currentPage ? 'page' : undefined"
          @click="goToPage(page)"
        >{{ page }}</button>
        <button type="button" :disabled="currentPage >= totalPages" @click="goToPage(currentPage + 1)">
          Sau <AppIcon name="chevronRight" :size="14" />
        </button>
      </nav>

      <aside class="source-note">
        <AppIcon name="shieldCheck" :size="18" />
        <p><strong>Nguồn nội dung:</strong> Cổng TTĐT OCOP Lâm Đồng. Liên kết “Đọc tại nguồn” mở bài viết gốc trong thẻ mới.</p>
      </aside>
    </section>
  </main>
</template>

<style scoped>
.news-page { min-height: 65vh; background: var(--ocop-surface); }
.news-hero { padding: 58px 0 52px; background: linear-gradient(135deg, var(--ocop-primary-950), var(--ocop-primary-700)); color: var(--ocop-white); }
.hero-inner { max-width: 860px; }
.eyebrow { display: inline-flex; align-items: center; gap: 7px; color: var(--ocop-mint-100); font-size: var(--ocop-font-size-caption); font-weight: 800; letter-spacing: .08em; text-transform: uppercase; }
.news-hero h1 { margin: 9px 0 var(--ocop-space-2); font-size: clamp(32px, 5vw, 48px); font-weight: 800; letter-spacing: -.035em; }
.news-hero p { max-width: 700px; margin: 0; color: color-mix(in srgb, var(--ocop-white) 78%, transparent); font-size: var(--ocop-font-size-body-lg); line-height: 1.65; }
.news-search { display: flex; max-width: 700px; margin-top: 26px; padding: 6px 6px 6px var(--ocop-space-4); align-items: center; gap: 10px; border-radius: var(--ocop-radius-md); background: var(--ocop-card); color: var(--ocop-slate); box-shadow: 0 12px 32px color-mix(in srgb, var(--ocop-black) 16%, transparent); }
.news-search input { min-width: 0; padding: 9px 0; flex: 1; border: 0; outline: 0; color: var(--ocop-navy); }
.news-search button, .state-card button { padding: 10px 17px; border: 0; border-radius: var(--ocop-radius-sm); background: var(--ocop-primary-700); color: var(--ocop-white); font-weight: 700; }
.news-content { padding-top: 42px; padding-bottom: 54px; }
.content-heading { display: flex; margin-bottom: var(--ocop-space-5); align-items: flex-end; justify-content: space-between; gap: var(--ocop-space-4); }
.content-heading h2 { margin: 0; color: var(--ocop-navy); font-size: 25px; font-weight: 800; }
.content-heading p { margin: var(--ocop-space-1) 0 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-small); }
.clear-button { padding: var(--ocop-space-2) var(--ocop-space-3); border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-sm); background: var(--ocop-card); color: var(--ocop-primary-700); font-size: var(--ocop-font-size-small); font-weight: 700; }
.news-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--ocop-space-5); }
.news-skeleton { display: grid; min-height: 410px; padding: 0 18px 18px; align-content: start; gap: 14px; overflow: hidden; border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-lg); background: var(--ocop-card); }
.news-skeleton .media-placeholder { width: calc(100% + 36px); height: 205px; margin: 0 -18px var(--ocop-space-2); }
.state-card { display: grid; min-height: 280px; padding: var(--ocop-space-8); place-items: center; align-content: center; gap: var(--ocop-space-2); border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-lg); background: var(--ocop-card); text-align: center; }
.state-card p { max-width: 540px; margin: 0 0 var(--ocop-space-2); color: var(--ocop-slate); }
.state-icon { display: grid; width: 56px; height: 56px; margin-bottom: var(--ocop-space-1); place-items: center; border-radius: 50%; background: var(--ocop-mint-soft); color: var(--ocop-primary-700); }
.error-state .state-icon { background: var(--ocop-danger-soft); color: var(--ocop-danger); }
.pagination-nav { display: flex; margin-top: 30px; align-items: center; justify-content: center; gap: 6px; }
.pagination-nav button { display: inline-flex; min-width: 38px; height: 38px; padding: 0 11px; align-items: center; justify-content: center; gap: var(--ocop-space-1); border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-sm); background: var(--ocop-card); color: var(--ocop-navy); font-size: var(--ocop-font-size-small); }
.pagination-nav button.active { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: var(--ocop-white); font-weight: 700; }
.pagination-nav button:disabled { cursor: not-allowed; opacity: .45; }
.source-note { display: flex; margin-top: 34px; padding: 15px 17px; align-items: flex-start; gap: 10px; border: 1px solid var(--ocop-mint-border); border-radius: 10px; background: var(--ocop-mint-soft); color: var(--ocop-primary-950); }
.source-note p { margin: 0; font-size: var(--ocop-font-size-small); line-height: 1.55; }
@media (max-width: 991.98px) { .news-grid { grid-template-columns: repeat(2, minmax(0, 1fr)); } }
@media (max-width: 575.98px) {
  .news-hero { padding: 42px 0; }
  .news-search { align-items: stretch; flex-wrap: wrap; }
  .news-search input { width: calc(100% - 32px); }
  .news-search button { width: 100%; }
  .content-heading { align-items: flex-start; flex-direction: column; }
  .news-grid { grid-template-columns: 1fr; }
  .pagination-nav button:not(.page-number) { font-size: 0; }
}
</style>
