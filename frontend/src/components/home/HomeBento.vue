<script setup lang="ts">
import { ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { flowerFarmPhoto } from '@/constants/photos'

const photoFailed = ref(false)
</script>

<template>
  <!-- Bento grid: ô bản đồ lớn (slot) giữa các ô lối tắt nhỏ, cùng một lưới và một khoảng cách. -->
  <section class="home-bento" aria-label="Khám phá nhanh">
    <div class="bento-map">
      <slot name="map" />
    </div>

    <RouterLink class="bento-tile tile-stars" :to="{ name: 'products', query: { sort: 'rating' } }">
      <span class="tile-kicker">Sản phẩm OCOP</span>
      <strong class="tile-figure">3–5 <small>sao</small></strong>
      <span class="tile-copy">Hạng sao được công nhận cho sản phẩm đặc trưng của Lâm Đồng</span>
      <span class="tile-link">Xem sản phẩm <AppIcon name="chevronRight" :size="16" /></span>
    </RouterLink>

    <a class="bento-tile tile-tourism" :class="{ 'has-photo': !photoFailed }" href="#diem-du-lich">
      <img v-if="!photoFailed" class="tile-photo" :src="flowerFarmPhoto.src" alt="" loading="lazy" @error="photoFailed = true" />
      <span v-else class="tourism-mark" aria-hidden="true"><AppIcon name="leaf" :size="120" /></span>
      <span class="tile-kicker">Du lịch nông nghiệp</span>
      <strong class="tile-title">Đồi chè, vườn dâu, nông trại</strong>
      <span class="tile-link">Xem điểm du lịch <AppIcon name="chevronRight" :size="16" /></span>
    </a>

    <RouterLink class="bento-tile tile-subject" :to="{ name: 'subject-application' }">
      <span class="subject-icon" aria-hidden="true"><AppIcon name="store" :size="24" /></span>
      <span class="tile-body">
        <span class="tile-kicker">Dành cho chủ thể OCOP</span>
        <strong class="tile-title">Đưa sản phẩm của bạn lên Cổng OCOP Lâm Đồng</strong>
        <span class="tile-copy">Đăng nhập, gửi hồ sơ chủ thể và khai báo sản phẩm; nội dung được kiểm duyệt trước khi công khai.</span>
      </span>
      <span class="subject-cta">Đăng ký chủ thể <AppIcon name="chevronRight" :size="16" /></span>
    </RouterLink>
  </section>
</template>

<style scoped>
.home-bento {
  position: relative;
  z-index: 2;
  display: grid;
  margin-top: calc(var(--ocop-space-12) * -1);
  grid-template-columns: repeat(4, minmax(0, 1fr));
  grid-auto-rows: minmax(180px, auto);
  gap: var(--ocop-space-4);
}

.bento-map {
  grid-column: span 2;
  grid-row: span 2;
  min-width: 0;
}

.bento-tile {
  position: relative;
  display: flex;
  min-width: 0;
  overflow: hidden;
  flex-direction: column;
  gap: var(--ocop-space-2);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-card);
  color: var(--ocop-navy);
  text-decoration: none;
  transition: transform var(--ocop-transition), box-shadow var(--ocop-transition);
}

.bento-tile:hover {
  box-shadow: var(--ocop-shadow-overlay);
  transform: translateY(-3px);
}

.tile-kicker {
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  letter-spacing: 0.08em;
  text-transform: uppercase;
}

.tile-title {
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 750;
  line-height: 1.3;
}

.tile-copy {
  font-size: var(--ocop-font-size-small);
  line-height: 1.5;
}

.tile-link {
  display: inline-flex;
  margin-top: auto;
  align-items: center;
  gap: var(--ocop-space-1);
  font-size: var(--ocop-font-size-body);
  font-weight: 700;
}

/* Ô sao OCOP: nền xanh đêm, số lớn, sao vàng. */
.tile-stars {
  border-color: var(--ocop-mist-900);
  background: var(--ocop-mist-950);
  color: var(--ocop-white);
}

.tile-stars .tile-kicker,
.tile-stars .tile-link {
  color: var(--ocop-daquy-300);
}

.tile-stars .tile-copy {
  color: var(--ocop-mist-200);
}

.tile-figure {
  display: flex;
  align-items: baseline;
  gap: var(--ocop-space-2);
  font-size: var(--ocop-font-size-title-lg);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1;
}

.tile-figure small {
  color: var(--ocop-daquy-300);
  font-size: var(--ocop-font-size-title-sm);
  font-weight: 700;
}

/* Ô du lịch: nền xanh lá (ý nghĩa thiên nhiên), lá lớn làm họa tiết mờ. */
.tile-tourism {
  border-color: var(--ocop-tone-leaf);
  background: var(--ocop-tone-leaf);
  color: var(--ocop-white);
}

.tile-photo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

/* Có ảnh: chữ nằm trên dải tối phía dưới để luôn đọc được. */
.tile-tourism.has-photo {
  justify-content: flex-end;
  border-color: var(--ocop-mist-900);
  background: var(--ocop-mist-950);
}

.tile-tourism.has-photo::before {
  position: absolute;
  z-index: 1;
  inset: 0;
  background: linear-gradient(180deg, color-mix(in srgb, var(--ocop-mist-950) 10%, transparent) 15%, color-mix(in srgb, var(--ocop-mist-950) 90%, transparent) 70%);
  content: '';
}

.tile-tourism.has-photo > :not(.tile-photo) {
  position: relative;
  z-index: 2;
}

.tile-tourism.has-photo .tile-link {
  margin-top: var(--ocop-space-1);
  color: var(--ocop-daquy-300);
}

.tourism-mark {
  position: absolute;
  right: calc(var(--ocop-space-4) * -1);
  bottom: calc(var(--ocop-space-4) * -1);
  color: color-mix(in srgb, var(--ocop-white) 16%, transparent);
  pointer-events: none;
}

.tile-tourism .tile-kicker,
.tile-tourism .tile-link {
  color: var(--ocop-white);
}

/* Ô chủ thể: nền vàng dã quỳ, rộng 2 cột. */
.tile-subject {
  grid-column: span 2;
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  grid-template-rows: auto auto;
  align-content: center;
  column-gap: var(--ocop-space-4);
  row-gap: var(--ocop-space-4);
  border-color: var(--ocop-daquy-300);
  background: var(--ocop-daquy-50);
}

.tile-subject .tile-body {
  display: flex;
  flex-direction: column;
  gap: var(--ocop-space-1);
}

.tile-subject .tile-kicker {
  color: var(--ocop-daquy-700);
}

.tile-subject .tile-copy {
  color: var(--ocop-mist-700);
}

.subject-icon {
  display: grid;
  width: 52px;
  height: 52px;
  place-items: center;
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-mist-950);
  color: var(--ocop-daquy-300);
}

.subject-cta {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  grid-column: 2;
  justify-self: start;
  align-items: center;
  gap: var(--ocop-space-1);
  padding: 0 var(--ocop-space-4);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-mist-950);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-body);
  font-weight: 700;
}

@media (max-width: 991.98px) {
  .home-bento {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    grid-auto-rows: minmax(180px, auto);
  }

  .bento-map {
    grid-row: auto;
  }
}

@media (max-width: 575.98px) {
  .home-bento {
    margin-top: 0;
    gap: var(--ocop-space-3);
    grid-auto-rows: minmax(170px, auto);
  }

  .bento-tile {
    padding: var(--ocop-space-4);
  }

  .tile-tourism .tile-title {
    font-size: var(--ocop-font-size-body);
  }

  .tile-subject {
    grid-template-columns: 1fr;
  }

  .subject-icon {
    display: none;
  }

  .subject-cta {
    grid-column: 1;
    margin-top: var(--ocop-space-3);
  }
}
</style>
