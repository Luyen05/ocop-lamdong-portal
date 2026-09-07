<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

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
      :src="asset('hero-agriculture.png')"
      alt="Nông nghiệp cao nguyên Lâm Đồng"
    />
    <div class="hero-overlay" />

    <div class="hero-content">
      <div class="hero-badge">
        <img :src="asset('icon-hero-badge.svg')" alt="" />
        Cổng thông tin quốc gia chương trình OCOP Lâm Đồng
      </div>

      <h1 id="home-hero-title">
        Nông Sản OCOP Đạt Sao &amp; Bản Đồ Số Du Lịch Nông Nghiệp Tỉnh Lâm Đồng
      </h1>
      <p>
        Tra cứu thông tin chính thức 185+ sản phẩm OCOP, nhà vườn công nghệ cao,
        trải nghiệm hái dâu tây, đồi chè Cầu Đất và chỉ đường thông minh trên bản đồ số GIS.
      </p>

      <form class="hero-search" role="search" @submit.prevent="submitSearch">
        <label class="search-field">
          <span class="visually-hidden">Tên sản phẩm cần tìm</span>
          <img :src="asset('icon-search.svg')" alt="" />
          <input
            v-model="search"
            type="search"
            placeholder="Nhập tên sản phẩm (Atisô, Cà phê Cầu Đất, Dâu tây...)..."
          />
        </label>
        <button type="submit">
          <img :src="asset('icon-search-white.svg')" alt="" />
          Tra Cứu Ngay
        </button>
      </form>

      <div class="hero-actions">
        <a class="map-action" href="#ban-do">
          <img :src="asset('icon-compass.svg')" alt="" />
          Khám Phá Bản Đồ Số GIS
        </a>
        <a class="tourism-action" href="#diem-du-lich">
          <img :src="asset('icon-pin.svg')" alt="" />
          Điểm Du Lịch Canh Nông
        </a>
      </div>
    </div>
  </section>
</template>

<style scoped>
.home-hero {
  position: relative;
  min-height: 598px;
  overflow: hidden;
  border-radius: var(--ocop-radius-xl);
  background: var(--ocop-navy);
  box-shadow: 0 25px 50px -12px rgb(0 0 0 / 25%);
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
  background: linear-gradient(0deg, #020618 0%, rgb(7 12 31 / 80%) 25%, rgb(15 23 43 / 60%) 50%, transparent 100%);
}

.hero-content {
  position: relative;
  z-index: 1;
  display: flex;
  width: min(100%, 1024px);
  min-height: 598px;
  margin-inline: auto;
  padding: 96px 24px;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: #fff;
  text-align: center;
}

.hero-badge {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 16px;
  border: 1px solid rgb(0 188 125 / 30%);
  border-radius: 999px;
  background: rgb(0 188 125 / 20%);
  color: #5ee9b5;
  font-size: 12px;
  font-weight: 650;
  line-height: 16px;
  text-transform: uppercase;
}

.hero-badge img {
  width: 16px;
  height: 16px;
}

h1 {
  max-width: 896px;
  margin: 24px 0 0;
  font-size: clamp(34px, 4vw, 48px);
  font-weight: 800;
  letter-spacing: -1.2px;
  line-height: 1.25;
}

.hero-content > p {
  max-width: 672px;
  margin: 24px 0 0;
  color: #cad5e2;
  font-size: 14px;
  line-height: 1.625;
}

.hero-search {
  display: grid;
  width: min(100%, 768px);
  margin-top: 24px;
  padding: 16px;
  grid-template-columns: minmax(0, 2fr) minmax(190px, 1fr);
  gap: 8px;
  border: 1px solid rgb(255 255 255 / 40%);
  border-radius: var(--ocop-radius-lg);
  background: rgb(255 255 255 / 95%);
  box-shadow: 0 20px 25px rgb(0 0 0 / 10%);
}

.search-field {
  position: relative;
  display: block;
}

.search-field img {
  position: absolute;
  top: 50%;
  left: 12px;
  width: 16px;
  height: 16px;
  transform: translateY(-50%);
}

.search-field input {
  width: 100%;
  height: 40px;
  padding: 10px 12px 10px 36px;
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-md);
  outline: 0;
  background: var(--ocop-surface-muted);
  color: var(--ocop-navy);
  font-size: 12px;
}

.search-field input:focus {
  border-color: var(--ocop-primary-500);
  box-shadow: 0 0 0 3px rgb(0 122 85 / 12%);
}

.hero-search button,
.hero-actions a {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  justify-content: center;
  gap: 8px;
  border-radius: var(--ocop-radius-md);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.hero-search button {
  border: 0;
  background: var(--ocop-primary-700);
  box-shadow: 0 4px 5px rgb(0 122 85 / 30%);
}

.hero-search button:hover {
  background: var(--ocop-primary-900);
}

.hero-search button img,
.hero-actions img {
  width: 16px;
  height: 16px;
}

.hero-actions {
  display: flex;
  margin-top: 24px;
  flex-wrap: wrap;
  justify-content: center;
  gap: 12px;
}

.hero-actions a {
  padding: 10px 20px;
  box-shadow: 0 10px 12px rgb(0 0 0 / 10%);
}

.map-action {
  border: 1px solid var(--ocop-blue);
  background: var(--ocop-blue);
}

.tourism-action {
  border: 1px solid rgb(255 255 255 / 30%);
  background: rgb(255 255 255 / 10%);
}

.hero-actions a:hover {
  filter: brightness(1.08);
}

@media (max-width: 767.98px) {
  .home-hero,
  .hero-content {
    min-height: 570px;
  }

  .home-hero {
    border-radius: var(--ocop-radius-lg);
  }

  .hero-content {
    padding: 52px 18px;
  }

  .hero-badge {
    font-size: 10px;
  }

  h1 {
    margin-top: 20px;
    font-size: clamp(30px, 9vw, 40px);
    letter-spacing: -0.8px;
  }

  .hero-content > p {
    margin-top: 18px;
    font-size: 13px;
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
