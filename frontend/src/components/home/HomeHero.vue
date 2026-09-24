<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'

const router = useRouter()
const search = ref('')

function asset(name: string): string {
  return `/assets/figma/home/${name}`
}

async function submitSearch(): Promise<void> {
  const keyword = search.value.trim()
  await router.push({ name: 'products', query: keyword ? { search: keyword } : {} })
}
</script>

<template>
  <section class="home-hero" aria-labelledby="home-hero-title">
    <img
      class="hero-image"
      :src="asset('hero-agriculture.jpg')"
      alt="Nông nghiệp cao nguyên Lâm Đồng"
    />
    <div class="hero-overlay" />

    <div class="hero-content">
      <div class="hero-badge">
        <AppIcon name="award" :size="16" />
        Cổng thông tin quảng bá OCOP Lâm Đồng
      </div>

      <h1 id="home-hero-title">
        Nông sản OCOP đạt sao &amp; Bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng
      </h1>
      <p>
        Tra cứu sản phẩm OCOP đã được phê duyệt, khám phá nhà vườn công nghệ cao,
        điểm du lịch canh nông và vị trí trên bản đồ số GIS của tỉnh Lâm Đồng.
      </p>

      <form class="hero-search" role="search" @submit.prevent="submitSearch">
        <label class="search-field">
          <span class="visually-hidden">Tên sản phẩm cần tìm</span>
          <AppIcon name="search" :size="16" />
          <input
            v-model="search"
            type="search"
            placeholder="Nhập tên sản phẩm (Atisô, Cà phê Cầu Đất, Dâu tây...)..."
          />
        </label>
        <button type="submit">
          <AppIcon name="search" :size="16" />
          Tra Cứu Ngay
        </button>
      </form>

      <div class="hero-actions">
        <a class="map-action" href="#ban-do">
          <AppIcon name="compass" :size="16" />
          Khám Phá Bản Đồ Số GIS
        </a>
        <a class="tourism-action" href="#diem-du-lich">
          <AppIcon name="map-pin" :size="16" />
          Điểm Du Lịch Canh Nông
        </a>
      </div>
    </div>
  </section>
</template>

<style scoped>
.home-hero {
  position: relative;
  min-height: 550px;
  overflow: hidden;
  border-radius: var(--ocop-radius-xl);
  background: var(--ocop-navy);
  box-shadow: 0 25px 50px -12px color-mix(in srgb, var(--ocop-black) 25%, transparent);
}

.hero-image,
.hero-overlay {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-image {
  object-fit: cover;
  opacity: 0.4;
  transform: scale(1.05);
}

.hero-overlay {
  background: linear-gradient(0deg, var(--ocop-neutral-950) 0%, color-mix(in srgb, var(--ocop-neutral-950) 80%, transparent) 25%, color-mix(in srgb, var(--ocop-neutral-900) 60%, transparent) 50%, transparent 100%);
}

.hero-content {
  position: relative;
  z-index: 1;
  display: flex;
  width: min(100%, 1024px);
  min-height: 550px;
  margin-inline: auto;
  padding: 72px var(--ocop-space-6);
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--ocop-white);
  text-align: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 6px var(--ocop-space-4);
  border: 1px solid color-mix(in srgb, var(--ocop-emerald-500) 30%, transparent);
  border-radius: var(--ocop-radius-pill);
  background: color-mix(in srgb, var(--ocop-emerald-500) 20%, transparent);
  color: var(--ocop-mint-400);
  font-size: var(--ocop-font-size-caption);
  font-weight: 650;
  line-height: 16px;
  text-transform: uppercase;
}

h1 {
  max-width: 896px;
  margin: var(--ocop-space-6) 0 0;
  font-size: clamp(34px, 3.7vw, 46px);
  font-weight: 800;
  letter-spacing: -1.2px;
  line-height: 1.25;
}

.hero-content > p {
  max-width: 672px;
  margin: var(--ocop-space-6) 0 0;
  color: var(--ocop-neutral-300);
  font-size: 14px;
  line-height: 1.625;
}

.hero-search {
  display: grid;
  width: min(100%, 768px);
  margin-top: var(--ocop-space-6);
  padding: var(--ocop-space-4);
  grid-template-columns: minmax(0, 2fr) minmax(190px, 1fr);
  gap: var(--ocop-space-2);
  border: 1px solid color-mix(in srgb, var(--ocop-white) 40%, transparent);
  border-radius: var(--ocop-radius-lg);
  background: color-mix(in srgb, var(--ocop-white) 95%, transparent);
  box-shadow: 0 20px 25px color-mix(in srgb, var(--ocop-black) 10%, transparent);
}

.search-field {
  position: relative;
  display: block;
}

.search-field .app-icon {
  position: absolute;
  top: 50%;
  left: 12px;
  transform: translateY(-50%);
  color: var(--ocop-slate);
}

.search-field input {
  width: 100%;
  height: 40px;
  padding: 10px var(--ocop-space-3) 10px 36px;
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-md);
  outline: 0;
  background: var(--ocop-surface-muted);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-caption);
}

.search-field input:focus {
  border-color: var(--ocop-primary-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ocop-success) 12%, transparent);
}

.hero-search button,
.hero-actions a {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-2);
  border-radius: var(--ocop-radius-md);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  text-decoration: none;
}

.hero-search button {
  border: 0;
  background: var(--ocop-primary-700);
  box-shadow: 0 4px 5px color-mix(in srgb, var(--ocop-success) 30%, transparent);
}

.hero-search button:hover {
  background: var(--ocop-primary-900);
}

.hero-actions {
  display: flex;
  margin-top: var(--ocop-space-6);
  flex-wrap: wrap;
  justify-content: center;
  gap: var(--ocop-space-3);
}

.hero-actions a {
  padding: 10px var(--ocop-space-5);
  box-shadow: 0 10px 12px color-mix(in srgb, var(--ocop-black) 10%, transparent);
}

.map-action {
  border: 1px solid var(--ocop-blue);
  background: var(--ocop-blue);
}

.tourism-action {
  border: 1px solid color-mix(in srgb, var(--ocop-white) 30%, transparent);
  background: color-mix(in srgb, var(--ocop-white) 10%, transparent);
}

.hero-actions a:hover {
  filter: brightness(1.08);
}

@media (max-width: 767.98px) {
  .home-hero,
  .hero-content {
    min-height: 530px;
  }

  .home-hero {
    border-radius: var(--ocop-radius-lg);
  }

  .hero-content {
    padding: 52px 18px;
  }

  .hero-badge {
    font-size: var(--ocop-font-size-2xs);
  }

  h1 {
    margin-top: var(--ocop-space-5);
    font-size: clamp(28px, 8vw, 36px);
    letter-spacing: -0.8px;
  }

  .hero-content > p {
    margin-top: 18px;
    font-size: var(--ocop-font-size-small);
  }

  .hero-search {
    padding: 10px;
    grid-template-columns: 1fr;
  }

  .hero-actions {
    width: 100%;
  }

  .hero-actions a {
    width: 100%;
  }
}
</style>
