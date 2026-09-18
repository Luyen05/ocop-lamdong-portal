<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { NewsListItem } from '@/types/news'

const props = defineProps<{ news: NewsListItem }>()
const imageFailed = ref(false)
watch(() => props.news.primary_image_url, () => { imageFailed.value = false })
const publishedDate = computed(() => new Date(props.news.published_at).toLocaleDateString('vi-VN'))
</script>

<template>
  <article class="news-card">
    <RouterLink class="news-media" :to="`/tin-tuc/${news.slug}`" :aria-label="news.title">
      <img v-if="news.primary_image_url && !imageFailed" :src="news.primary_image_url"
        :alt="news.title" loading="lazy" @error="imageFailed = true" />
      <div v-else class="image-placeholder" aria-hidden="true">OCOP</div>
    </RouterLink>
    <div class="news-body">
      <span class="category-badge">{{ news.category }}</span>
      <h2><RouterLink :to="`/tin-tuc/${news.slug}`">{{ news.title }}</RouterLink></h2>
      <p>{{ news.summary }}</p>
      <time :datetime="news.published_at">{{ publishedDate }}</time>
      <RouterLink class="read-link" :to="`/tin-tuc/${news.slug}`">Đọc bài viết →</RouterLink>
    </div>
  </article>
</template>

<style scoped>
.news-card { display: flex; height: 100%; min-width: 0; overflow: hidden; flex-direction: column; border: 1px solid var(--ocop-border, #e0e7dd); border-radius: 1rem; background: #fff; box-shadow: 0 4px 12px rgb(15 23 43 / 5%); }
.news-media { display: block; aspect-ratio: 1.4 / 1; overflow: hidden; }
.news-media img, .image-placeholder { width: 100%; height: 100%; }
.news-media img { object-fit: cover; }
.image-placeholder { display: grid; place-items: center; background: linear-gradient(145deg, #edf4e5, #cbdcbc); color: #2f6f3e; font-size: 1.6rem; font-weight: 800; letter-spacing: .15em; }
.news-body { display: flex; flex: 1; flex-direction: column; align-items: start; gap: .8rem; padding: 1.25rem; }
.category-badge { padding: .3rem .65rem; border-radius: 999px; background: #e6f1de; color: #2f6f3e; font-size: .76rem; font-weight: 700; }
h2 { margin: 0; font-size: 1.2rem; line-height: 1.4; overflow-wrap: anywhere; }
h2 a { color: #18351f; text-decoration: none; }
p { margin: 0; color: #627066; line-height: 1.6; overflow-wrap: anywhere; }
time { margin-top: auto; color: #69736b; font-size: .85rem; }
.read-link { color: #2f6f3e; font-weight: 700; text-decoration: none; }
</style>