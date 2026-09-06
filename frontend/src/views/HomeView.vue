<script setup lang="ts">
import FeaturedProducts from '@/components/home/FeaturedProducts.vue'
import HomeCategories from '@/components/home/HomeCategories.vue'
import HomeHero from '@/components/home/HomeHero.vue'
import TourismSection from '@/components/home/TourismSection.vue'
</script>

<template>
  <main class="home-page">
    <div class="site-content home-content">
      <HomeHero />
      <HomeCategories />
      <FeaturedProducts />
      <TourismSection />

      <section id="ban-do" class="coming-section map-coming">
        <span>Bản đồ số GIS</span>
        <h2>Khám phá các chủ thể OCOP và điểm du lịch</h2>
      </section>
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

.coming-section {
  margin-top: 48px;
  padding: 56px 24px;
  border-radius: var(--ocop-radius-xl);
  background: var(--ocop-mint-soft);
  text-align: center;
}

.coming-section span {
  color: var(--ocop-primary-700);
  font-size: 11px;
  font-weight: 800;
  text-transform: uppercase;
}

.coming-section h2 {
  margin: 8px 0 0;
  color: var(--ocop-navy);
  font-size: clamp(24px, 4vw, 36px);
  font-weight: 800;
}

.map-coming {
  background: var(--ocop-navy);
}

.map-coming h2 {
  color: #fff;
}
</style>
