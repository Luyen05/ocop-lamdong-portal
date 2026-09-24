<script setup lang="ts">
import { onMounted, ref } from 'vue'

import LocationCard from '@/components/locations/LocationCard.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getLocations } from '@/services/locations'
import type { LocationListItem } from '@/types/location'

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

onMounted(() => {
  void loadLocations()
})
</script>

<template>
  <section id="diem-du-lich" class="tourism-section" aria-labelledby="tourism-title">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Trải Nghiệm Du Lịch Nông Nghiệp</span>
        <h2 id="tourism-title">Điểm Đến Canh Nông Tiêu Biểu</h2>
      </div>
      <RouterLink class="view-all" :to="{ name: 'locations' }">
        Xem tất cả <AppIcon name="chevronRight" :size="14" />
      </RouterLink>
    </div>

    <div v-if="isLoading" class="tourism-grid" aria-label="Đang tải điểm du lịch">
      <div v-for="index in 3" :key="index" class="loading-card placeholder-glow">
        <span class="placeholder col-12 media-placeholder" />
        <span class="placeholder col-8 mt-3" />
        <span class="placeholder col-10 mt-2" />
      </div>
    </div>

    <div v-else-if="locations.length" class="tourism-grid">
      <LocationCard v-for="location in locations" :key="location.id" :location="location" />
    </div>

    <div v-else class="tourism-empty" role="status">
      <p>
        {{ hasError ? 'Chưa tải được danh sách điểm du lịch.' : 'Chưa có điểm du lịch nào được công bố.' }}
      </p>
      <button v-if="hasError" class="btn btn-sm btn-outline-success" type="button" @click="loadLocations">
        Thử lại
      </button>
    </div>
  </section>
</template>

<style scoped>
.tourism-section {
  padding-top: var(--ocop-space-12);
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--ocop-space-4);
}

.eyebrow {
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
  line-height: 16px;
  text-transform: uppercase;
}

h2 {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-title-md);
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.view-all {
  display: inline-flex;
  align-items: center;
  gap: var(--ocop-space-1);
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
  text-decoration: none;
}

.tourism-grid {
  display: grid;
  margin-top: var(--ocop-space-4);
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--ocop-space-3);
}

.loading-card {
  min-height: 22rem;
  padding: 1rem;
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.media-placeholder {
  display: block;
  height: 10rem;
  border-radius: var(--ocop-radius-md);
}

.tourism-empty {
  display: flex;
  margin-top: var(--ocop-space-4);
  padding: 2rem 1rem;
  flex-direction: column;
  align-items: center;
  gap: var(--ocop-space-2);
  border: 1px dashed var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  color: var(--ocop-slate);
}

.tourism-empty p {
  margin: 0;
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
