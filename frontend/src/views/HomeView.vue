<script setup lang="ts">
import FeaturedProducts from '@/components/home/FeaturedProducts.vue'
import HomeBento from '@/components/home/HomeBento.vue'
import HomeCategories from '@/components/home/HomeCategories.vue'
import HomeHero from '@/components/home/HomeHero.vue'
import HomeMapPreview from '@/components/home/HomeMapPreview.vue'
import HomeNews from '@/components/home/HomeNews.vue'
import TourismSection from '@/components/home/TourismSection.vue'
import { homePhotos } from '@/constants/photos'
</script>

<template>
  <main class="home-page">
    <HomeHero />

    <div class="site-content">
      <HomeBento>
        <template #map>
          <HomeMapPreview />
        </template>
      </HomeBento>
      <HomeCategories />
      <FeaturedProducts />
    </div>

    <TourismSection />

    <div class="site-content">
      <HomeNews />
      <p class="photo-credits">
        Ảnh cảnh quan minh họa chụp tại Đà Lạt, dùng theo Giấy phép Unsplash:
        <template v-for="(photo, index) in homePhotos" :key="photo.src">
          <a :href="photo.sourceUrl" target="_blank" rel="noopener noreferrer">{{ photo.author }}</a><span v-if="index < homePhotos.length - 1">, </span>
        </template>.
      </p>
    </div>
  </main>
</template>

<style scoped>
.photo-credits {
  margin: 0;
  padding-bottom: var(--ocop-space-8);
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
}

.photo-credits a {
  color: var(--ocop-primary-700);
}

.home-page {
  min-height: 100vh;
  background: var(--ocop-surface);
}
</style>
