<script setup lang="ts">
import { onMounted, ref } from 'vue'

import NewsCard from '@/components/news/NewsCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getNews } from '@/services/news'
import type { NewsItem } from '@/types/news'

const articles = ref<NewsItem[]>([])
const isLoading = ref(true)
const hasError = ref(false)

async function loadNews(): Promise<void> {
  isLoading.value = true
  hasError.value = false
  try {
    const response = await getNews({ page: 1, page_size: 4 })
    articles.value = response.items
  } catch {
    articles.value = []
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(() => void loadNews())
</script>

<template>
  <section id="tin-tuc" class="news-section" aria-labelledby="home-news-title">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Tin tức &amp; sự kiện OCOP</span>
        <h2 id="home-news-title">Cập nhật hoạt động OCOP Lâm Đồng</h2>
        <p class="section-copy">Thông tin mới được tổng hợp từ Cổng TTĐT OCOP Lâm Đồng.</p>
      </div>
      <RouterLink class="view-all" to="/tin-tuc">
        Xem tất cả <AppIcon name="chevronRight" :size="14" />
      </RouterLink>
    </div>

    <div v-if="isLoading" class="news-grid" aria-live="polite" aria-label="Đang tải tin tức">
      <div v-for="index in 2" :key="index" class="news-skeleton placeholder-glow">
        <span class="placeholder visual-placeholder" />
        <span class="skeleton-copy">
          <span class="placeholder col-5" />
          <span class="placeholder col-10" />
          <span class="placeholder col-8" />
        </span>
      </div>
    </div>

    <div v-else-if="hasError" class="state-card" role="alert">
      <AppIcon name="refresh" :size="24" />
      <div>
        <strong>Chưa thể tải tin tức mới</strong>
        <p>Nguồn tin đang tạm thời không phản hồi.</p>
      </div>
      <button type="button" @click="loadNews">Thử lại</button>
    </div>

    <div v-else-if="!articles.length" class="state-card">
      <AppIcon name="newspaper" :size="24" />
      <div>
        <strong>Chưa có tin mới</strong>
        <p>Các bài viết mới sẽ được cập nhật tại đây.</p>
      </div>
    </div>

    <div v-else class="news-grid">
      <NewsCard v-for="article in articles" :key="article.id" :article="article" compact />
    </div>
  </section>
</template>

<style scoped>
.news-section { padding: 48px 0; }
.section-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 16px; }
.eyebrow { color: var(--ocop-primary-700); font-size: 11px; font-weight: 800; line-height: 16px; text-transform: uppercase; }
h2 { max-width: 680px; margin: 4px 0 0; color: var(--ocop-navy); font-size: 22px; font-weight: 800; letter-spacing: -.5px; line-height: 28px; }
.section-copy { margin: 2px 0 0; color: var(--ocop-slate); font-size: 13px; }
.view-all { display: inline-flex; flex: 0 0 auto; align-items: center; gap: 4px; color: var(--ocop-primary-700); font-size: 12px; font-weight: 750; text-decoration: none; }
.view-all:hover { color: var(--ocop-primary-950); text-decoration: underline; }
.news-grid { display: grid; margin-top: 16px; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
.news-skeleton { display: grid; min-height: 230px; overflow: hidden; grid-template-columns: minmax(150px, 36%) minmax(0, 1fr); border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-lg); background: #fff; }
.visual-placeholder { width: 100%; height: 100%; border-radius: 0; }
.skeleton-copy { display: grid; padding: 24px 18px; align-content: start; gap: 15px; }
.state-card { display: flex; min-height: 130px; margin-top: 16px; padding: 24px; align-items: center; justify-content: center; gap: 13px; border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-lg); background: #fff; color: var(--ocop-primary-700); text-align: left; }
.state-card strong { color: var(--ocop-navy); }
.state-card p { margin: 2px 0 0; color: var(--ocop-slate); font-size: 13px; }
.state-card button { margin-left: 12px; padding: 8px 13px; border: 1px solid var(--ocop-primary-700); border-radius: 8px; background: #fff; color: var(--ocop-primary-700); font-size: 12px; font-weight: 700; }
@media (max-width: 991.98px) { .news-grid { grid-template-columns: 1fr; } }
@media (max-width: 575.98px) {
  .section-heading { align-items: flex-start; flex-direction: column; }
  .news-skeleton { min-height: 360px; grid-template-columns: 1fr; }
  .visual-placeholder { min-height: 170px; }
  .state-card { align-items: flex-start; flex-wrap: wrap; }
  .state-card button { width: 100%; margin-left: 0; }
}
</style>
