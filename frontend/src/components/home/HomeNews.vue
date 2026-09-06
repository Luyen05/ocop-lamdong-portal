<script setup lang="ts">
import { newsFixtures } from '@/data/home-fixtures'
</script>

<template>
  <section id="tin-tuc" class="news-section" aria-labelledby="news-title">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Tin Tức &amp; Sự Kiện OCOP</span>
        <h2 id="news-title">Cập nhật chính sách khuyến nông và hoạt động quảng bá du lịch</h2>
      </div>
      <span class="demo-label">Dữ liệu minh họa</span>
    </div>

    <div class="news-grid">
      <article v-for="article in newsFixtures" :key="article.id" class="news-card">
        <div class="news-visual" :class="`theme-${article.theme}`">
          <span aria-hidden="true">{{ article.theme === 'policy' ? '🏅' : '🌿' }}</span>
        </div>
        <div class="news-body">
          <div class="news-meta">
            <span>{{ article.category }}</span>
            <time>{{ article.date }}</time>
          </div>
          <h3>{{ article.title }}</h3>
          <p>{{ article.summary }}</p>
          <button type="button" disabled title="Trang tin tức sẽ được triển khai ở module sau">
            Đọc bài viết →
          </button>
        </div>
      </article>
    </div>
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
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.demo-label {
  flex: 0 0 auto;
  padding: 5px 9px;
  border: 1px solid #fde68a;
  border-radius: 999px;
  background: #fffbeb;
  color: #92400e;
  font-size: 10px;
  font-weight: 700;
}

.news-grid {
  display: grid;
  margin-top: 16px;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.news-card {
  display: grid;
  overflow: hidden;
  grid-template-columns: minmax(160px, 38%) minmax(0, 1fr);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: #fff;
  box-shadow: 0 4px 12px rgb(15 23 43 / 5%);
}

.news-visual {
  display: grid;
  min-height: 230px;
  place-items: center;
}

.theme-policy {
  background: linear-gradient(145deg, #d4ebd0, #6da06b);
}

.theme-tourism {
  background: linear-gradient(145deg, #f7dfb5, #b67d40);
}

.news-visual span {
  font-size: 62px;
  filter: drop-shadow(0 8px 10px rgb(15 23 43 / 18%));
}

.news-body {
  display: flex;
  padding: 18px;
  flex-direction: column;
}

.news-meta {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  color: var(--ocop-slate);
  font-size: 10px;
}

.news-meta span {
  padding: 4px 8px;
  border-radius: 999px;
  background: var(--ocop-mint-soft);
  color: var(--ocop-primary-900);
  font-weight: 700;
}

.news-body h3 {
  margin: 12px 0 7px;
  color: var(--ocop-navy);
  font-size: 15px;
  font-weight: 750;
  line-height: 21px;
}

.news-body p {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--ocop-slate);
  font-size: 11px;
  line-height: 17px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.news-body button {
  width: max-content;
  margin-top: auto;
  padding: 0;
  border: 0;
  background: transparent;
  color: var(--ocop-primary-700);
  font-size: 11px;
  font-weight: 700;
  opacity: 0.72;
}

@media (max-width: 991.98px) {
  .news-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 575.98px) {
  .section-heading {
    align-items: flex-start;
  }

  .news-card {
    grid-template-columns: 1fr;
  }

  .news-visual {
    min-height: 170px;
  }

  .news-body {
    min-height: 230px;
  }
}
</style>
