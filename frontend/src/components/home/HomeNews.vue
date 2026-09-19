<script setup lang="ts">
import { onMounted, ref } from 'vue'

import NewsCard from '@/components/news/NewsCard.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { listNews } from '@/services/news'
import type { NewsListItem } from '@/types/news'

const news = ref<NewsListItem[]>([])
const isLoading = ref(true)
const errorMessage = ref('')

async function loadNews(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await listNews({ page: 1, page_size: 3 })
    news.value = response.items.slice(0, 3)
  } catch (error) {
    news.value = []
    errorMessage.value = getApiErrorMessage(error, 'Chưa thể tải tin tức.')
  } finally {
    isLoading.value = false
  }
}

onMounted(loadNews)
</script>

<template>
  <section id="tin-tuc" class="news-section" aria-labelledby="news-title">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Tin Tức &amp; Sự Kiện OCOP</span>
        <h2 id="news-title">Cập nhật hoạt động OCOP Lâm Đồng</h2>
        <p class="section-copy">Chính sách khuyến nông, chương trình xúc tiến và câu chuyện du lịch nông nghiệp.</p>
      </div>
      <RouterLink to="/tin-tuc">Xem tất cả tin tức <span aria-hidden="true">→</span></RouterLink>
    </div>

    <div v-if="isLoading" class="news-state" role="status">Đang tải tin tức…</div>
    <div v-else-if="errorMessage" class="news-state" role="alert">
      <strong>{{ errorMessage }}</strong>
      <button type="button" @click="loadNews">Thử lại</button>
    </div>
    <div v-else-if="news.length" class="news-grid">
      <NewsCard v-for="article in news" :key="article.id" :news="article" />
    </div>
    <div v-else class="news-state" role="status">Chưa có tin tức được xuất bản.</div>
  </section>
</template>

<style scoped>
.news-section {
  padding: 48px 0;
}
.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}
.eyebrow {
  color: var(--ocop-primary-700);
  font-size: 11px;
  font-weight: 800;
  line-height: 16px;
  text-transform: uppercase;
}
h2 {
  max-width: 680px;
  margin: 4px 0 0;
  color: var(--ocop-navy);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}
.section-copy {
  margin: 2px 0 0;
  color: var(--ocop-slate);
  font-size: 13px;
}
.section-heading > a {
  flex: 0 0 auto;
  color: var(--ocop-primary-700);
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}
.news-grid {
  display: grid;
  margin-top: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}
.news-state {
  margin-top: 16px;
  padding: 44px 20px;
  border: 1px dashed var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: #fff;
  color: var(--ocop-slate);
  text-align: center;
}
.news-state strong {
  display: block;
  color: var(--ocop-navy);
}
.news-state button {
  margin-top: 12px;
  padding: 7px 14px;
  border: 1px solid var(--ocop-primary-700);
  border-radius: var(--ocop-radius-sm);
  background: #fff;
  color: var(--ocop-primary-700);
  font-size: 12px;
  font-weight: 700;
}
@media (max-width: 991.98px) {
  .news-grid { grid-template-columns: 1fr; }
}
@media (max-width: 575.98px) {
  .section-heading { align-items: flex-start; flex-direction: column; }
}
</style>
