<script setup lang="ts">
import { tourismFixtures } from '@/data/home-fixtures'
</script>

<template>
  <section id="diem-du-lich" class="tourism-section" aria-labelledby="tourism-title">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Trải Nghiệm Du Lịch Nông Nghiệp</span>
        <h2 id="tourism-title">Điểm Đến Canh Nông Tiêu Biểu</h2>
      </div>
      <span class="demo-label">Dữ liệu minh họa</span>
    </div>

    <div class="tourism-grid">
      <article v-for="place in tourismFixtures" :key="place.id" class="tourism-card">
        <div class="tourism-visual" :class="`theme-${place.theme}`">
          <span class="type-badge">{{ place.icon }} {{ place.type }}</span>
          <span class="rating-badge">★ {{ place.rating.toFixed(1) }}</span>
          <span class="visual-mark" aria-hidden="true">{{ place.icon }}</span>
        </div>

        <div class="tourism-body">
          <div class="place-meta">
            <span>◷ {{ place.openingHours }}</span>
            <span>⌖ {{ place.district }}</span>
          </div>
          <h3>{{ place.name }}</h3>
          <p>{{ place.description }}</p>
          <ul>
            <li v-for="experience in place.experiences" :key="experience">✓ {{ experience }}</li>
          </ul>
          <div class="tourism-actions">
            <button type="button" disabled title="Trang chi tiết sẽ được triển khai ở module du lịch">
              Khám Phá
            </button>
            <a href="#ban-do">⌖ Chỉ Đường</a>
          </div>
        </div>
      </article>
    </div>
  </section>
</template>

<style scoped>
.tourism-section {
  padding-top: 48px;
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
  margin: 4px 0 0;
  color: var(--ocop-navy);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.demo-label {
  padding: 5px 9px;
  border: 1px solid #fde68a;
  border-radius: 999px;
  background: #fffbeb;
  color: #92400e;
  font-size: 10px;
  font-weight: 700;
}

.tourism-grid {
  display: grid;
  margin-top: 16px;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 12px;
}

.tourism-card {
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: #fff;
  box-shadow: 0 4px 12px rgb(15 23 43 / 5%);
}

.tourism-visual {
  position: relative;
  display: grid;
  min-height: 165px;
  overflow: hidden;
  place-items: center;
}

.tourism-visual::before,
.tourism-visual::after {
  position: absolute;
  border-radius: 50%;
  content: '';
}

.tourism-visual::before {
  width: 190px;
  height: 190px;
  top: -90px;
  right: -50px;
  background: rgb(255 255 255 / 20%);
}

.tourism-visual::after {
  width: 130px;
  height: 130px;
  bottom: -75px;
  left: -25px;
  background: rgb(15 23 43 / 10%);
}

.theme-tea {
  background: linear-gradient(145deg, #b7d89b, #357a4d);
}

.theme-strawberry {
  background: linear-gradient(145deg, #f8b4b4, #bf3030);
}

.theme-milk {
  background: linear-gradient(145deg, #dce9f5, #6ca8c0);
}

.visual-mark {
  font-size: 66px;
  filter: drop-shadow(0 10px 12px rgb(15 23 43 / 20%));
}

.type-badge,
.rating-badge {
  position: absolute;
  z-index: 1;
  top: 12px;
  padding: 5px 9px;
  border-radius: var(--ocop-radius-sm);
  background: rgb(15 23 43 / 76%);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
}

.type-badge {
  left: 12px;
}

.rating-badge {
  right: 12px;
  color: #fde68a;
}

.tourism-body {
  display: flex;
  min-height: 300px;
  padding: 16px;
  flex-direction: column;
}

.place-meta {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  color: var(--ocop-slate);
  font-size: 10px;
}

.tourism-body h3 {
  min-height: 40px;
  margin: 8px 0 6px;
  color: var(--ocop-navy);
  font-size: 14px;
  font-weight: 750;
  line-height: 20px;
}

.tourism-body p {
  display: -webkit-box;
  overflow: hidden;
  margin: 0;
  color: var(--ocop-slate);
  font-size: 11px;
  line-height: 16px;
  -webkit-box-orient: vertical;
  -webkit-line-clamp: 3;
}

.tourism-body ul {
  display: grid;
  margin: 12px 0 0;
  padding: 0;
  gap: 4px;
  color: #45556c;
  font-size: 10px;
  list-style: none;
}

.tourism-body li::first-letter {
  color: var(--ocop-primary-700);
}

.tourism-actions {
  display: flex;
  margin-top: auto;
  padding-top: 14px;
  gap: 8px;
}

.tourism-actions button,
.tourism-actions a {
  display: inline-flex;
  min-height: 36px;
  flex: 1;
  align-items: center;
  justify-content: center;
  border-radius: var(--ocop-radius-md);
  font-size: 11px;
  font-weight: 700;
  text-decoration: none;
}

.tourism-actions button {
  border: 1px solid var(--ocop-primary-700);
  background: var(--ocop-primary-700);
  color: #fff;
  opacity: 0.72;
}

.tourism-actions a {
  border: 1px solid var(--ocop-border);
  background: var(--ocop-surface-muted);
  color: #45556c;
}

@media (max-width: 991.98px) {
  .tourism-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 575.98px) {
  .section-heading {
    align-items: flex-start;
  }

  .tourism-grid {
    grid-template-columns: 1fr;
  }
}
</style>
