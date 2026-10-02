<script setup lang="ts">
import { computed, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { photoByIndex } from '@/constants/photos'
import type { NewsItem } from '@/types/news'

const props = defineProps<{
  article: NewsItem
  compact?: boolean
}>()

const imageFailed = ref(false)

// Bài chưa có ảnh dùng ảnh cảnh quan Đà Lạt làm nền trang trí (chọn ổn định theo mã bài), không phải ảnh của bài.
const fallbackPhoto = computed(() => {
  const seed = Array.from(props.article.id).reduce((total, char) => total + char.charCodeAt(0), 0)
  return photoByIndex(seed)
})

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
        <img class="news-placeholder-photo" :src="fallbackPhoto.src" alt="" loading="lazy" />
        <span><AppIcon name="newspaper" :size="compact ? 30 : 34" /></span>
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
  box-shadow: 0 5px 18px color-mix(in srgb, var(--ocop-navy) 6%, transparent);
  transition: transform var(--ocop-transition), box-shadow var(--ocop-transition);
}

.news-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 28px color-mix(in srgb, var(--ocop-navy) 11%, transparent);
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
  position: relative;
  display: grid;
  width: 100%;
  height: 100%;
  place-items: center;
  background: linear-gradient(145deg, var(--ocop-mint-soft), var(--ocop-text-on-dark));
  color: var(--ocop-primary-700);
}

.news-media .news-placeholder-photo {
  position: absolute;
  inset: 0;
}

.news-card:hover .news-media .news-placeholder-photo {
  transform: scale(1.05);
}

.news-placeholder span {
  position: relative;
  display: grid;
  width: 64px;
  height: 64px;
  place-items: center;
  border: 1px solid var(--ocop-white);
  border-radius: 50%;
  background: color-mix(in srgb, var(--ocop-white) 88%, transparent);
  box-shadow: var(--ocop-shadow-sm);
}

.news-body {
  display: flex;
  min-height: 220px;
  padding: var(--ocop-space-5);
  flex: 1;
  flex-direction: column;
}

.news-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
}

.news-meta span {
  padding: var(--ocop-space-1) var(--ocop-space-2);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mint-soft);
  color: var(--ocop-primary-900);
  font-weight: 700;
}

.news-body h2 {
  display: -webkit-box;
  overflow: hidden;
  margin: 14px 0 var(--ocop-space-2);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-title-sm);
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
  font-size: var(--ocop-font-size-small);
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
  font-size: var(--ocop-font-size-body-lg);
}

.news-card.compact .news-body p {
  font-size: var(--ocop-font-size-caption);
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
