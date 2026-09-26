<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { getCategories } from '@/services/categories'
import type { Category } from '@/types/category'
import { categoryTheme } from '@/utils/category'

const categories = ref<Category[]>([])
const isLoading = ref(true)
const failed = ref(false)
const visibleCategories = computed(() => categories.value)

const themeFor = categoryTheme

async function loadCategories(): Promise<void> {
  isLoading.value = true
  failed.value = false
  try {
    categories.value = (await getCategories()).items
  } catch {
    categories.value = []
    failed.value = true
  } finally {
    isLoading.value = false
  }
}

onMounted(loadCategories)
</script>

<template>
  <section class="category-section" aria-labelledby="category-title">
    <div class="category-bar">
      <h2 id="category-title" class="category-title">
        <AppIcon name="package" :size="18" />
        Tìm theo nhóm sản phẩm
      </h2>

      <div v-if="isLoading" class="chip-row" aria-busy="true" aria-label="Đang tải danh mục">
        <span v-for="index in 7" :key="index" class="chip-skeleton placeholder-glow"><span class="placeholder col-12" /></span>
      </div>

      <ul v-else-if="visibleCategories.length" class="chip-row" aria-label="Nhóm sản phẩm OCOP">
        <li v-for="category in visibleCategories" :key="category.id">
          <RouterLink
            class="category-card"
            :to="{ name: 'products', query: { category: category.slug } }"
            :style="{
              '--category-bg': themeFor(category.slug).background,
              '--category-color': themeFor(category.slug).foreground,
            }"
          >
            <span class="category-icon" aria-hidden="true"><AppIcon :name="themeFor(category.slug).icon" :size="16" /></span>
            {{ category.name }}
          </RouterLink>
        </li>
        <li>
          <RouterLink class="category-card is-all" to="/san-pham">
            Tất cả <AppIcon name="chevronRight" :size="16" />
          </RouterLink>
        </li>
      </ul>

      <div v-else class="category-empty" role="status">
        <span>{{ failed ? 'Chưa thể tải danh mục.' : 'Chưa có danh mục sản phẩm.' }}</span>
        <button v-if="failed" class="ocop-btn-ghost" type="button" @click="loadCategories">
          <AppIcon name="refresh" :size="16" /> Thử lại
        </button>
      </div>
    </div>
  </section>
</template>

<style scoped>
.category-section {
  padding-top: var(--ocop-space-8);
}

.category-bar {
  display: flex;
  flex-direction: column;
  gap: var(--ocop-space-3);
}

.category-title {
  display: inline-flex;
  margin: 0;
  flex: 0 0 auto;
  align-items: center;
  gap: var(--ocop-space-2);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-body-lg);
  font-weight: 750;
}

.category-title :deep(.app-icon) {
  color: var(--ocop-daquy-600);
}

.chip-row {
  display: flex;
  min-width: 0;
  margin: 0;
  padding: 0;
  flex: 1;
  flex-wrap: wrap;
  gap: var(--ocop-space-2);
  list-style: none;
}

/* Chip: nhãn bo tròn bấm được, dẫn tới danh sách sản phẩm đã lọc. */
.category-card {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 0 var(--ocop-space-4) 0 6px;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-card);
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-body);
  font-weight: 600;
  text-decoration: none;
  white-space: nowrap;
  transition: border-color var(--ocop-transition), background var(--ocop-transition), transform var(--ocop-transition);
}

.category-card:hover {
  border-color: var(--category-color, var(--ocop-border-strong));
  background: var(--category-bg, var(--ocop-mist-50));
  transform: translateY(-1px);
}

.category-card.is-all {
  padding-left: var(--ocop-space-4);
  border-color: transparent;
  background: transparent;
  color: var(--ocop-primary-700);
  font-weight: 700;
}

.category-icon {
  display: grid;
  width: 32px;
  height: 32px;
  place-items: center;
  border-radius: 50%;
  background: var(--category-bg);
  color: var(--category-color);
}

.chip-skeleton {
  width: 150px;
  height: var(--ocop-control-md);
  overflow: hidden;
  border-radius: var(--ocop-radius-pill);
}

.chip-skeleton .placeholder {
  display: block;
  height: 100%;
}

.category-empty {
  display: flex;
  flex: 1;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-3) var(--ocop-space-4);
  border: 1px dashed var(--ocop-border-strong);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
  color: var(--ocop-slate);
}

@media (max-width: 991.98px) {
  /* Trượt ngang, mép phải mờ dần để báo còn nội dung. */
  .chip-row {
    margin-inline: -16px;
    padding-inline: var(--ocop-space-4);
    flex-wrap: nowrap;
    overflow-x: auto;
    scroll-snap-type: x proximity;
    scrollbar-width: none;
    mask-image: linear-gradient(90deg, transparent 0, var(--ocop-black) 16px, var(--ocop-black) calc(100% - 40px), transparent);
  }

  .chip-row::-webkit-scrollbar {
    display: none;
  }

  .chip-row > * {
    scroll-snap-align: start;
  }
}
</style>
