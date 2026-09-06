<script setup lang="ts">
import FeaturedProducts from '@/components/home/FeaturedProducts.vue'
import HomeCategories from '@/components/home/HomeCategories.vue'
import HomeHero from '@/components/home/HomeHero.vue'
import HomeMapPreview from '@/components/home/HomeMapPreview.vue'
import HomeNews from '@/components/home/HomeNews.vue'
import TourismSection from '@/components/home/TourismSection.vue'
</script>

<template>
  <main class="home-page">
    <div class="site-content home-content">
      <HomeHero />
      <HomeCategories />
      <FeaturedProducts />
      <TourismSection />
      <HomeMapPreview />
      <HomeNews />
    </div>
  </main>
</template>

<style scoped>
.home-page {
  min-height: 100vh;
  padding-bottom: 48px;
  background: var(--ocop-surface);
}

.home-content {
  padding-top: 24px;
}

</style>
