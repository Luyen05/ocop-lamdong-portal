<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { getCategories } from '@/services/categories'
import type { Category } from '@/types/category'

interface CategoryTheme {
  icon: string
  background: string
  foreground: string
}

const themes: Record<string, CategoryTheme> = {
  'nong-san-tuoi': { icon: 'sprout', background: 'var(--ocop-mint-soft)', foreground: 'var(--ocop-primary-700)' },
  'thuc-pham': { icon: 'food', background: 'var(--ocop-accent-soft)', foreground: 'var(--ocop-warning)' },
  'do-uong': { icon: 'coffee', background: 'var(--ocop-info-soft)', foreground: 'var(--ocop-blue)' },
  'thao-duoc': { icon: 'leaf', background: 'var(--ocop-tone-leaf-soft)', foreground: 'var(--ocop-tone-leaf)' },
  'thu-cong-my-nghe': { icon: 'palette', background: 'var(--ocop-tone-clay-soft)', foreground: 'var(--ocop-tone-clay)' },
  'sinh-vat-canh': { icon: 'flower', background: 'var(--ocop-tone-rose-soft)', foreground: 'var(--ocop-tone-rose)' },
  'dich-vu-du-lich-cong-dong': { icon: 'compass', background: 'var(--ocop-info-soft)', foreground: 'var(--ocop-blue)' },
}

const fallbackTheme: CategoryTheme = {
  icon: 'package',
  background: 'var(--ocop-mint-soft)',
  foreground: 'var(--ocop-primary-700)',
}

const categories = ref<Category[]>([])
const isLoading = ref(true)
const failed = ref(false)
const visibleCategories = computed(() => categories.value.slice(0, 5))

function themeFor(slug: string): CategoryTheme {
  return themes[slug] ?? fallbackTheme
}

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
    <div class="section-heading">
      <div>
        <h2 id="category-title">Danh Mục Sản Phẩm OCOP</h2>
        <p>Phân loại sản phẩm đạt chuẩn sao OCOP theo ngành hàng</p>
      </div>
      <RouterLink to="/san-pham">Xem tất cả <AppIcon name="chevronRight" :size="14" /></RouterLink>
    </div>

    <div v-if="isLoading" class="category-grid" aria-label="Đang tải danh mục">
      <div v-for="index in 5" :key="index" class="category-skeleton placeholder-glow">
        <span class="placeholder col-3" />
        <span class="placeholder col-8 mt-3" />
        <span class="placeholder col-5 mt-2" />
      </div>
    </div>

    <div v-else-if="visibleCategories.length" class="category-grid">
      <RouterLink
        v-for="category in visibleCategories"
        :key="category.id"
        class="category-card"
        :to="{ name: 'products', query: { category: category.slug } }"
        :style="{
          '--category-bg': themeFor(category.slug).background,
          '--category-color': themeFor(category.slug).foreground,
        }"
      >
        <span class="category-icon" aria-hidden="true"><AppIcon :name="themeFor(category.slug).icon" :size="23" /></span>
        <strong>{{ category.name }}</strong>
        <small>Xem sản phẩm</small>
      </RouterLink>
    </div>

    <div v-else class="category-empty" role="status">
      <span>{{ failed ? 'Chưa thể tải danh mục.' : 'Chưa có danh mục sản phẩm.' }}</span>
      <button v-if="failed" type="button" @click="loadCategories">Thử lại</button>
    </div>
  </section>
</template>

<style scoped>
.category-section {
  padding-top: var(--ocop-space-12);
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--ocop-space-4);
}

.section-heading h2 {
  margin: 0;
  color: var(--ocop-navy);
  font-size: 22px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.section-heading p {
  margin: 0;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-small);
  font-weight: 500;
  line-height: 16px;
}

.section-heading a {
  flex: 0 0 auto;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  text-decoration: none;
}

.category-grid {
  display: grid;
  margin-top: var(--ocop-space-4);
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: var(--ocop-space-3);
}

.category-card,
.category-skeleton {
  min-height: 107px;
  padding: var(--ocop-space-4);
  border: 1px solid color-mix(in srgb, var(--ocop-neutral-200) 80%, transparent);
  border-radius: var(--ocop-radius-lg);
}

.category-card {
  display: flex;
  flex-direction: column;
  background: var(--category-bg);
  color: var(--ocop-navy);
  text-decoration: none;
  transition: transform 160ms ease, box-shadow 160ms ease;
}

.category-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 12px 22px color-mix(in srgb, var(--ocop-neutral-900) 9%, transparent);
}

.category-icon {
  display: grid;
  width: 38px;
  height: 38px;
  place-items: center;
  border-radius: 10px;
  background: color-mix(in srgb, var(--ocop-white) 62%, transparent);
  color: var(--category-color);
}

.category-card strong {
  margin-top: var(--ocop-space-2);
  font-size: var(--ocop-font-size-caption);
  line-height: 16px;
}

.category-card small {
  margin-top: 2px;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
  font-weight: 500;
  line-height: 15px;
}

.category-skeleton {
  background: var(--ocop-surface-muted);
}

.category-empty {
  display: flex;
  margin-top: var(--ocop-space-4);
  align-items: center;
  justify-content: space-between;
  padding: var(--ocop-space-4);
  border: 1px dashed var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
}

.category-empty button {
  border: 0;
  background: transparent;
  color: var(--ocop-primary-700);
  font-weight: 700;
}

@media (max-width: 991.98px) {
  .category-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 575.98px) {
  .section-heading {
    align-items: flex-start;
  }

  .category-grid {
    display: flex;
    margin-inline: -16px;
    padding-inline: var(--ocop-space-4);
    overflow-x: auto;
    scroll-snap-type: x mandatory;
  }

  .category-card,
  .category-skeleton {
    min-width: 190px;
    scroll-snap-align: start;
  }
}
</style>
