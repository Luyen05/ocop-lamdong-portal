<script setup lang="ts">
import { ref } from 'vue'

import type { SitePhoto } from '@/constants/photos'

defineProps<{
  photo: SitePhoto
}>()

// Ảnh lỗi thì banner vẫn đọc được nhờ nền màu thương hiệu bên dưới.
const photoFailed = ref(false)
</script>

<template>
  <section class="photo-banner">
    <img
      v-if="!photoFailed"
      class="banner-photo"
      :src="photo.src"
      alt=""
      :style="{ objectPosition: photo.position ?? 'center 62%' }"
      @error="photoFailed = true"
    />
    <div class="site-content banner-inner hero-stagger">
      <slot />
    </div>
  </section>
</template>

<style scoped>
/* Banner đầu trang có ảnh cảnh quan thật, lớp tối ở bên trái để chữ trắng luôn đọc rõ. */
.photo-banner {
  position: relative;
  overflow: hidden;
  background: var(--ocop-mist-800);
  color: var(--ocop-white);
}

.banner-photo {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.photo-banner::after {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, color-mix(in srgb, var(--ocop-mist-950) 88%, transparent), color-mix(in srgb, var(--ocop-mist-950) 55%, transparent) 55%, color-mix(in srgb, var(--ocop-mist-950) 22%, transparent));
  content: '';
}

.banner-inner {
  position: relative;
  z-index: 1;
  display: flex;
  padding: var(--ocop-space-12) 0;
  flex-direction: column;
  align-items: flex-start;
  gap: var(--ocop-space-3);
}

.photo-banner :slotted(h1) {
  margin: 0;
  font-size: clamp(1.875rem, 4.5vw, 3rem);
  font-weight: 800;
  letter-spacing: -0.025em;
}

.photo-banner :slotted(p) {
  max-width: 40rem;
  margin: 0;
  color: var(--ocop-mist-100);
  font-size: var(--ocop-font-size-body-lg);
  line-height: 1.65;
}

.photo-banner :slotted(.banner-eyebrow) {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  color: var(--ocop-daquy-300);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
  letter-spacing: 0.1em;
  text-transform: uppercase;
}
</style>
