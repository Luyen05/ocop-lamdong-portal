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
    <div class="ocop-section-head">
      <div>
        <p class="ocop-eyebrow">Tin tức &amp; sự kiện OCOP</p>
        <h2 id="home-news-title" class="ocop-section-title">Hoạt động OCOP Lâm Đồng</h2>
        <p class="ocop-section-copy">Thông tin mới được tổng hợp từ Cổng TTĐT OCOP Lâm Đồng.</p>
      </div>
      <RouterLink class="ocop-link-more" to="/tin-tuc">
        Xem tất cả tin tức <AppIcon name="chevronRight" :size="16" />
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

    <div v-else-if="hasError" class="state-card is-info" role="alert">
      <span class="state-icon" aria-hidden="true"><AppIcon name="newspaper" :size="22" /></span>
      <div>
        <strong>Chưa thể tải tin tức mới</strong>
        <p>Nguồn tin đang tạm thời không phản hồi.</p>
      </div>
      <button class="ocop-btn-ghost" type="button" @click="loadNews"><AppIcon name="refresh" :size="16" /> Thử lại</button>
    </div>

    <div v-else-if="!articles.length" class="state-card">
      <span class="state-icon" aria-hidden="true"><AppIcon name="newspaper" :size="22" /></span>
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
.news-section { padding: var(--ocop-space-12) 0 var(--ocop-space-16); }
.news-grid { display: grid; margin-top: var(--ocop-space-5); grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ocop-space-4); }
.news-skeleton { display: grid; min-height: 230px; overflow: hidden; grid-template-columns: minmax(150px, 36%) minmax(0, 1fr); border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-lg); background: var(--ocop-card); }
.visual-placeholder { width: 100%; height: 100%; border-radius: 0; }
.skeleton-copy { display: grid; padding: var(--ocop-space-6) var(--ocop-space-5); align-content: start; gap: var(--ocop-space-4); }
.state-card { display: flex; margin-top: var(--ocop-space-5); padding: var(--ocop-space-6); align-items: center; gap: var(--ocop-space-5); border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-md); background: var(--ocop-card); text-align: left; }
.state-card.is-info { border-color: var(--ocop-info-border); background: var(--ocop-info-soft); }
.state-card > div { flex: 1; }
.state-icon { display: grid; width: 48px; height: 48px; flex: 0 0 auto; place-items: center; border-radius: 50%; background: var(--ocop-mist-100); color: var(--ocop-primary-700); }
.is-info .state-icon { background: var(--ocop-card); color: var(--ocop-info); }
.state-card strong { color: var(--ocop-navy); font-size: var(--ocop-font-size-body-lg); }
.is-info strong { color: var(--ocop-info-strong); }
.state-card p { margin: var(--ocop-space-1) 0 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-body); }
@media (max-width: 991.98px) { .news-grid { grid-template-columns: 1fr; } }
@media (max-width: 575.98px) {
  .news-section { padding: var(--ocop-space-8) 0 var(--ocop-space-12); }
  .news-skeleton { min-height: 360px; grid-template-columns: 1fr; }
  .visual-placeholder { min-height: 170px; }
  .state-card { align-items: flex-start; flex-wrap: wrap; }
  .state-card button { width: 100%; }
}
</style>
