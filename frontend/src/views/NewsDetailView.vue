<script setup lang="ts">
import axios from 'axios'
import { computed, onUnmounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { getApiErrorMessage } from '@/services/api-error'
import { getNewsBySlug } from '@/services/news'
import type { NewsDetail } from '@/types/news'

const route = useRoute()
const news = ref<NewsDetail | null>(null)
const isLoading = ref(true)
const errorMessage = ref('')
const isNotFound = ref(false)
const imageFailed = ref(false)
const publishedDate = computed(() => news.value ? new Date(news.value.published_at).toLocaleDateString('vi-VN') : '')
let requestId = 0

async function loadNews(slug: string): Promise<void> {
  const id = ++requestId
  isLoading.value = true
  errorMessage.value = ''
  isNotFound.value = false
  imageFailed.value = false
  news.value = null
  try {
    const response = await getNewsBySlug(slug)
    if (id !== requestId) return
    news.value = response
    document.title = `${response.title} | OCOP Lâm Đồng`
  } catch (error) {
    if (id !== requestId) return
    isNotFound.value = axios.isAxiosError(error) && error.response?.status === 404
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải bài viết. Vui lòng thử lại.')
  } finally {
    if (id === requestId) isLoading.value = false
  }
}
function retryNews(): void {
  if (typeof route.params.slug === 'string') void loadNews(route.params.slug)
}
watch(() => route.params.slug, (slug) => {
  if (typeof slug === 'string') void loadNews(slug)
}, { immediate: true })
onUnmounted(() => {
  requestId++
  document.title = 'OCOP Lâm Đồng'
})
</script>

<template>
  <main class="detail-page">
    <div class="container py-4 py-lg-5">
      <RouterLink class="back-link" to="/tin-tuc">← Quay lại danh sách tin tức</RouterLink>
      <div v-if="isLoading" class="loading-state" role="status">Đang tải bài viết...</div>
      <section v-else-if="errorMessage" class="error-state" role="alert">
        <h1>{{ isNotFound ? 'Không tìm thấy bài viết' : 'Không thể tải bài viết' }}</h1>
        <p>{{ errorMessage }}</p>
        <button v-if="!isNotFound" class="btn btn-outline-success" type="button" @click="retryNews">Thử lại</button>
      </section>
      <article v-else-if="news" class="news-detail">
        <span class="category-badge">{{ news.category }}</span>
        <h1>{{ news.title }}</h1>
        <div class="news-meta">
          <time :datetime="news.published_at">{{ publishedDate }}</time>
          <span>{{ news.views }} lượt xem</span>
        </div>
        <div class="primary-image">
          <img v-if="news.primary_image_url && !imageFailed" :src="news.primary_image_url" :alt="news.title" @error="imageFailed = true" />
          <div v-else class="image-placeholder" aria-hidden="true">OCOP</div>
        </div>
        <p class="summary">{{ news.summary }}</p>
        <div class="news-content">{{ news.content }}</div>
      </article>
    </div>
  </main>
</template>

<style scoped>
.detail-page { min-height: calc(100vh - 4.5rem); background: #f7f8f4; }
.back-link { color: #3f724a; text-decoration: none; }
.news-detail { max-width: 56rem; margin: 2rem auto 0; padding: clamp(1.25rem, 4vw, 2.5rem); border: 1px solid rgb(29 72 39 / 10%); border-radius: 1.1rem; background: #fff; overflow-wrap: anywhere; }
.category-badge { display: inline-block; padding: .4rem .7rem; border-radius: 999px; background: #e6f1de; color: #2f6f3e; font-size: .76rem; font-weight: 750; }
h1 { margin: 1rem 0; color: #172d1d; font-size: clamp(2rem, 5vw, 3.3rem); font-weight: 800; }
.news-meta { display: flex; flex-wrap: wrap; gap: 1rem; color: #69736b; font-size: .9rem; }
.primary-image { overflow: hidden; margin-top: 1.5rem; aspect-ratio: 16 / 9; border-radius: 1rem; }
.primary-image img, .image-placeholder { width: 100%; height: 100%; }
.primary-image img { object-fit: cover; }
.image-placeholder { display: grid; place-items: center; background: linear-gradient(145deg, #edf4e5, #cbdcbc); color: #2f6f3e; font-size: 1.6rem; font-weight: 800; letter-spacing: .15em; }
.summary { margin: 1.5rem 0; color: #3f5545; font-size: 1.1rem; font-weight: 600; line-height: 1.8; white-space: pre-line; }
.news-content { color: #626f65; line-height: 1.8; white-space: pre-line; }
.loading-state, .error-state { padding: 5rem 1rem; text-align: center; }
.error-state p { color: #69736b; }
</style>