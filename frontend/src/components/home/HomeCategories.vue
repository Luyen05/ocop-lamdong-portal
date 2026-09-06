<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { getCategories } from '@/services/categories'
import type { Category } from '@/types/category'

interface CategoryTheme {
  emoji: string
  background: string
  foreground: string
}

const themes: Record<string, CategoryTheme> = {
  'nong-san-tuoi': { emoji: '🍓', background: '#ecfdf5', foreground: '#006045' },
  'thuc-pham': { emoji: '🍯', background: '#fffbeb', foreground: '#973c00' },
  'do-uong': { emoji: '🍷', background: '#f0f9ff', foreground: '#00598a' },
  'thao-duoc': { emoji: '🌿', background: '#faf5ff', foreground: '#6e11b0' },
  'thu-cong-my-nghe': { emoji: '🎨', background: '#fff1f2', foreground: '#a50036' },
  'sinh-vat-canh': { emoji: '🌸', background: '#fdf2f8', foreground: '#9d174d' },
  'dich-vu-du-lich-cong-dong': { emoji: '🏡', background: '#eff6ff', foreground: '#1d4ed8' },
}

const fallbackTheme: CategoryTheme = {
  emoji: '🌱',
  background: '#ecfdf5',
  foreground: '#006045',
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
      <RouterLink to="/san-pham">Xem tất cả <span aria-hidden="true">→</span></RouterLink>
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
        <span class="category-emoji" aria-hidden="true">{{ themeFor(category.slug).emoji }}</span>
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
  padding-top: 48px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.section-heading h2 {
  margin: 0;
  color: var(--ocop-navy);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.section-heading p {
  margin: 0;
  color: var(--ocop-slate);
  font-size: 12px;
  font-weight: 500;
  line-height: 16px;
}

.section-heading a {
  flex: 0 0 auto;
  color: var(--ocop-primary-700);
  font-size: 12px;
  font-weight: 700;
  text-decoration: none;
}

.category-grid {
  display: grid;
  margin-top: 16px;
  grid-template-columns: repeat(5, minmax(0, 1fr));
  gap: 12px;
}

.category-card,
.category-skeleton {
  min-height: 107px;
  padding: 16px;
  border: 1px solid rgb(226 232 240 / 80%);
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
  box-shadow: 0 12px 22px rgb(15 23 43 / 9%);
}

.category-emoji {
  color: var(--category-color);
  font-size: 24px;
  line-height: 32px;
}

.category-card strong {
  margin-top: 8px;
  font-size: 12px;
  line-height: 16px;
}

.category-card small {
  margin-top: 2px;
  color: var(--ocop-slate);
  font-size: 10px;
  font-weight: 500;
  line-height: 15px;
}

.category-skeleton {
  background: var(--ocop-surface-muted);
}

.category-empty {
  display: flex;
  margin-top: 16px;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
  border: 1px dashed var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  color: var(--ocop-slate);
  font-size: 12px;
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
    padding-inline: 16px;
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
