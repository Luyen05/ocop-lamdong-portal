<script setup lang="ts">
import { nextTick, onBeforeUnmount, onMounted, ref } from 'vue'

import LocationCard from '@/components/locations/LocationCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { hydrangeaPhoto, strawberryPhoto, teaPhoto } from '@/constants/photos'
import { getLocations } from '@/services/locations'
import type { LocationListItem } from '@/types/location'

// Lối tắt theo loại hình, mở danh sách điểm du lịch đã lọc sẵn. Ảnh là cảnh quan minh họa chung.
const experiences = [
  { type: 'tea_coffee_farm', label: 'Đồi chè và cà phê', photo: teaPhoto, fallback: '/assets/images/tourism-tea.svg' },
  { type: 'fruit_garden', label: 'Vườn dâu, trái cây', photo: strawberryPhoto, fallback: '/assets/images/tourism-strawberry.svg' },
  { type: 'flower_garden', label: 'Vườn hoa', photo: hydrangeaPhoto, fallback: '/assets/images/tourism-farm.svg' },
]
const failedPhotos = ref<string[]>([])

const locations = ref<LocationListItem[]>([])
const isLoading = ref(true)
const hasError = ref(false)

async function loadLocations(): Promise<void> {
  isLoading.value = true
  hasError.value = false
  try {
    locations.value = (await getLocations({ page: 1, page_size: 3, sort: 'rating' })).items
  } catch {
    locations.value = []
    hasError.value = true
  } finally {
    isLoading.value = false
  }
}

// Carousel: cuộn ngang có điểm dừng (scroll-snap), chấm chỉ vị trí và nút trước/sau.
const track = ref<HTMLElement | null>(null)
const activeIndex = ref(0)
const canScroll = ref(false)

function slides(): HTMLElement[] {
  return track.value ? (Array.from(track.value.children) as HTMLElement[]) : []
}

function updateCarousel(): void {
  const element = track.value
  if (!element) return
  canScroll.value = element.scrollWidth > element.clientWidth + 1
  const items = slides()
  if (!items.length) return
  const left = element.scrollLeft
  let nearest = 0
  items.forEach((item, index) => {
    if (Math.abs(item.offsetLeft - element.offsetLeft - left) < Math.abs(items[nearest].offsetLeft - element.offsetLeft - left)) nearest = index
  })
  const atEnd = left + element.clientWidth >= element.scrollWidth - 2
  activeIndex.value = atEnd ? items.length - 1 : nearest
}

function goTo(index: number): void {
  const element = track.value
  const item = slides()[index]
  if (!element || !item) return
  const reduceMotion = window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  element.scrollTo({ left: item.offsetLeft - element.offsetLeft, behavior: reduceMotion ? 'auto' : 'smooth' })
}

onMounted(async () => {
  window.addEventListener('resize', updateCarousel, { passive: true })
  await loadLocations()
  await nextTick()
  updateCarousel()
})

onBeforeUnmount(() => window.removeEventListener('resize', updateCarousel))
</script>

<template>
  <section id="diem-du-lich" class="tourism-section" aria-labelledby="tourism-title">
    <div class="site-content">
      <div class="ocop-section-head">
        <div>
          <p class="ocop-eyebrow">Du lịch nông nghiệp</p>
          <h2 id="tourism-title" class="ocop-section-title">Điểm du lịch tiêu biểu</h2>
        </div>
        <RouterLink class="ocop-link-more" :to="{ name: 'locations' }">
          Xem tất cả điểm du lịch <AppIcon name="chevronRight" :size="16" />
        </RouterLink>
      </div>

      <ul class="experience-row" aria-label="Khám phá theo loại hình">
        <li v-for="item in experiences" :key="item.type">
          <RouterLink class="experience-card" :to="{ name: 'locations', query: { type: item.type } }">
            <img
              :src="failedPhotos.includes(item.type) ? item.fallback : item.photo.src"
              alt=""
              loading="lazy"
              :style="{ objectPosition: item.photo.position }"
              @error="failedPhotos.push(item.type)"
            />
            <span class="experience-label">
              {{ item.label }}
              <AppIcon name="chevronRight" :size="16" />
            </span>
          </RouterLink>
        </li>
      </ul>

      <div v-if="isLoading" class="tourism-grid" aria-busy="true" aria-label="Đang tải điểm du lịch">
        <div v-for="index in 3" :key="index" class="loading-card placeholder-glow">
          <span class="placeholder media-placeholder" />
          <span class="skeleton-copy">
            <span class="placeholder col-5" />
            <span class="placeholder col-9" />
            <span class="placeholder col-11" />
          </span>
        </div>
      </div>

      <div v-else-if="locations.length" class="carousel">
        <ul
          id="tourism-track"
          ref="track"
          class="tourism-track"
          aria-label="Danh sách điểm du lịch tiêu biểu"
          @scroll.passive="updateCarousel"
        >
          <li v-for="location in locations" :key="location.id" class="tourism-slide">
            <LocationCard :location="location" />
          </li>
        </ul>

        <div v-if="canScroll" class="carousel-controls">
          <button
            class="carousel-arrow"
            type="button"
            aria-controls="tourism-track"
            aria-label="Điểm du lịch trước"
            :disabled="activeIndex === 0"
            @click="goTo(activeIndex - 1)"
          >
            <AppIcon name="chevronLeft" :size="18" />
          </button>
          <div class="carousel-dots">
            <button
              v-for="(location, index) in locations"
              :key="location.id"
              class="carousel-dot"
              :class="{ active: index === activeIndex }"
              type="button"
              aria-controls="tourism-track"
              :aria-label="`Xem điểm ${index + 1}: ${location.name}`"
              :aria-current="index === activeIndex ? 'true' : undefined"
              @click="goTo(index)"
            />
          </div>
          <button
            class="carousel-arrow"
            type="button"
            aria-controls="tourism-track"
            aria-label="Điểm du lịch tiếp theo"
            :disabled="activeIndex === locations.length - 1"
            @click="goTo(activeIndex + 1)"
          >
            <AppIcon name="chevronRight" :size="18" />
          </button>
        </div>
      </div>

      <div v-else class="tourism-empty" :role="hasError ? 'alert' : 'status'">
        <span class="state-icon" aria-hidden="true"><AppIcon :name="hasError ? 'refresh' : 'map-pin'" :size="22" /></span>
        <p>
          {{ hasError ? 'Chưa tải được danh sách điểm du lịch.' : 'Chưa có điểm du lịch nào được công bố.' }}
        </p>
        <button v-if="hasError" class="ocop-btn-ghost" type="button" @click="loadLocations">
          <AppIcon name="refresh" :size="16" /> Thử lại
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.tourism-section {
  margin-top: var(--ocop-space-12);
  padding: var(--ocop-space-12) 0 var(--ocop-space-12);
  background: var(--ocop-mist-100);
}

.tourism-grid,
.tourism-track {
  display: grid;
  margin-top: var(--ocop-space-5);
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ocop-space-6);
}

.tourism-track {
  margin-bottom: 0;
  padding: 0;
  grid-auto-columns: calc((100% - 2 * var(--ocop-space-6)) / 3);
  grid-auto-flow: column;
  grid-template-columns: none;
  overflow-x: auto;
  list-style: none;
  scroll-snap-type: x mandatory;
  scrollbar-width: none;
}

.tourism-track::-webkit-scrollbar {
  display: none;
}

.tourism-slide {
  display: flex;
  min-width: 0;
  scroll-snap-align: start;
}

.tourism-slide > * {
  width: 100%;
}

.carousel-controls {
  display: flex;
  margin-top: var(--ocop-space-4);
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-3);
}

.carousel-arrow {
  display: grid;
  width: var(--ocop-control-md);
  height: var(--ocop-control-md);
  padding: 0;
  place-items: center;
  border: 1px solid var(--ocop-border);
  border-radius: 50%;
  background: var(--ocop-card);
  color: var(--ocop-navy);
}

.carousel-arrow:disabled {
  opacity: 0.45;
}

.carousel-dots {
  display: flex;
  gap: var(--ocop-space-1);
}

/* Chấm có vùng bấm 24px, phần nhìn thấy 8px; chấm đang xem dài hơn (không chỉ khác màu). */
.carousel-dot {
  display: grid;
  width: 24px;
  height: 24px;
  padding: 0;
  place-items: center;
  border: 0;
  background: transparent;
}

.carousel-dot::before {
  width: 8px;
  height: 8px;
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-mist-400);
  content: '';
  transition: width var(--ocop-transition), background var(--ocop-transition);
}

.carousel-dot.active::before {
  width: 22px;
  background: var(--ocop-mist-800);
}

.experience-row {
  display: grid;
  margin: var(--ocop-space-5) 0 0;
  padding: 0;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ocop-space-4);
  list-style: none;
}

.experience-card {
  position: relative;
  display: flex;
  height: 132px;
  overflow: hidden;
  align-items: flex-end;
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-mist-900);
  color: var(--ocop-white);
  text-decoration: none;
}

.experience-card img {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 300ms ease;
}

.experience-card::before {
  position: absolute;
  z-index: 1;
  inset: 0;
  background: linear-gradient(180deg, transparent 30%, color-mix(in srgb, var(--ocop-mist-950) 85%, transparent));
  content: '';
}

.experience-card:hover img {
  transform: scale(1.04);
}

.experience-label {
  position: relative;
  z-index: 2;
  display: inline-flex;
  align-items: center;
  gap: var(--ocop-space-1);
  padding: var(--ocop-space-4);
  font-size: var(--ocop-font-size-body-lg);
  font-weight: 700;
}

@media (prefers-reduced-motion: reduce) {
  .experience-card img {
    transition: none;
  }
}

.loading-card {
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.media-placeholder {
  display: block;
  width: 100%;
  aspect-ratio: 16 / 10;
}

.skeleton-copy {
  display: grid;
  padding: var(--ocop-space-4);
  gap: var(--ocop-space-3);
}

.skeleton-copy .placeholder {
  display: block;
}

.tourism-empty {
  display: flex;
  margin-top: var(--ocop-space-5);
  padding: var(--ocop-space-8) var(--ocop-space-4);
  flex-direction: column;
  align-items: center;
  gap: var(--ocop-space-3);
  border: 1px dashed var(--ocop-border-strong);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-body);
  text-align: center;
}

.tourism-empty p {
  margin: 0;
}

.state-icon {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-mist-100);
  color: var(--ocop-primary-700);
}

@media (max-width: 991.98px) {
  .tourism-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: var(--ocop-space-4);
  }

  .tourism-track {
    grid-auto-columns: calc((100% - var(--ocop-space-4)) / 2);
    gap: var(--ocop-space-4);
  }
}

@media (max-width: 575.98px) {
  .tourism-section {
    margin-top: var(--ocop-space-8);
    padding: var(--ocop-space-8) 0;
  }

  .tourism-grid {
    margin-top: var(--ocop-space-4);
    grid-template-columns: 1fr;
    gap: var(--ocop-space-3);
  }

  .experience-row {
    margin-inline: -16px;
    padding-inline: var(--ocop-space-4);
    grid-auto-columns: 62%;
    grid-auto-flow: column;
    grid-template-columns: none;
    gap: var(--ocop-space-3);
    overflow-x: auto;
    scroll-snap-type: x proximity;
    scrollbar-width: none;
  }

  .experience-row > li {
    scroll-snap-align: start;
  }

  .experience-card {
    height: 112px;
  }

  /* Điện thoại: thẻ chiếm 86% bề ngang để lộ một phần thẻ sau, báo còn nội dung để vuốt. */
  .tourism-track {
    margin-inline: -16px;
    padding-inline: var(--ocop-space-4);
    grid-auto-columns: 86%;
    gap: var(--ocop-space-3);
    scroll-padding-inline: var(--ocop-space-4);
  }
}
</style>
