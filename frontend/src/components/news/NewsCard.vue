<script setup lang="ts">
import { ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import type { NewsItem } from '@/types/news'

defineProps<{
  article: NewsItem
  compact?: boolean
}>()

const imageFailed = ref(false)

function formatDate(value: string | null): string {
  if (!value) return 'Chưa rõ ngày đăng'
  const date = new Date(value)
  if (Number.isNaN(date.getTime())) return 'Chưa rõ ngày đăng'
  return new Intl.DateTimeFormat('vi-VN', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
  }).format(date)
}
</script>

<template>
  <article class="news-card" :class="{ compact }">
    <div class="news-media">
      <img
        v-if="article.image_url && !imageFailed"
        :src="article.image_url"
        :alt="`Ảnh minh họa: ${article.title}`"
        loading="lazy"
        referrerpolicy="no-referrer"
        @error="imageFailed = true"
      />
      <div v-else class="news-placeholder" aria-hidden="true">
        <span><AppIcon name="newspaper" :size="compact ? 42 : 50" /></span>
      </div>
    </div>

    <div class="news-body">
      <div class="news-meta">
        <span>{{ article.category }}</span>
        <time :datetime="article.published_at || undefined">{{ formatDate(article.published_at) }}</time>
      </div>
      <h2>{{ article.title }}</h2>
      <p>{{ article.summary || 'Xem nội dung chi tiết tại nguồn tin chính thức.' }}</p>
      <a :href="article.source_url" target="_blank" rel="noopener noreferrer">
        Đọc tại nguồn
        <AppIcon name="chevronRight" :size="14" />
        <span class="visually-hidden">: {{ article.title }} (mở trong thẻ mới)</span>
      </a>
    </div>
  </article>
</template>

<style scoped>
.news-card {
  display: flex;
  min-width: 0;
  overflow: hidden;
  flex-direction: column;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  box-shadow: 0 5px 18px rgb(24 37 31 / 6%);
  transition: transform 180ms ease, box-shadow 180ms ease;
}

.news-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px rgb(24 37 31 / 11%);
}

.news-media {
  overflow: hidden;
  aspect-ratio: 16 / 9;
  background: var(--ocop-mint-soft);
}

.news-media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 240ms ease;
}

.news-card:hover .news-media img {
  transform: scale(1.025);
}

.news-placeholder {
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  background: linear-gradient(145deg, var(--ocop-mint-soft), #dceee4);
  color: var(--ocop-primary-700);
}

.news-placeholder span {
  display: grid;
  width: 86px;
  height: 86px;
  place-items: center;
  border: 1px solid var(--ocop-mint-border);
  border-radius: 50%;
  background: rgb(255 255 255 / 66%);
}

.news-body {
  display: flex;
  min-height: 220px;
  padding: 20px;
  flex: 1;
  flex-direction: column;
}

.news-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--ocop-slate);
  font-size: 12px;
}

.news-meta span {
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--ocop-mint-soft);
  color: var(--ocop-primary-900);
  font-weight: 700;
}

.news-body h2 {
  display: -webkit-box;
  overflow: hidden;
  margin: 14px 0 8px;
  color: var(--ocop-navy);
  font-size: 18px;
  font-weight: 750;
  line-height: 1.4;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 2;
}

.news-body p {
  display: -webkit-box;
  overflow: hidden;
  margin: 0 0 18px;
  color: var(--ocop-slate);
  font-size: 14px;
  line-height: 1.65;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.news-body a {
  display: inline-flex;
  width: fit-content;
  margin-top: auto;
  align-items: center;
  gap: 5px;
  color: var(--ocop-primary-700);
  font-size: 13px;
  font-weight: 750;
  text-decoration: none;
}

.news-body a:hover {
  color: var(--ocop-primary-950);
  text-decoration: underline;
}

.news-card.compact {
  display: grid;
  grid-template-columns: minmax(150px, 36%) minmax(0, 1fr);
}

.news-card.compact .news-media {
  height: 100%;
  min-height: 230px;
  aspect-ratio: auto;
}

.news-card.compact .news-body {
  min-height: 230px;
  padding: 18px;
}

.news-card.compact .news-body h2 {
  font-size: 16px;
}

.news-card.compact .news-body p {
  font-size: 12px;
  line-height: 1.55;
}

@media (max-width: 575.98px) {
  .news-card.compact {
    display: flex;
  }

  .news-card.compact .news-media {
    min-height: 0;
    aspect-ratio: 16 / 9;
  }
}

@media (prefers-reduced-motion: reduce) {
  .news-card,
  .news-media img {
    transition: none;
  }
}
</style>
