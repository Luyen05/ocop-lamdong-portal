<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'

import LeafletMap from '@/components/map/LeafletMap.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getProductLocations } from '@/services/locations'
import type { ProductLocationItem } from '@/types/location'
import { locationKind, locationToFeature, locationTypeStyle, productRoleLabel } from '@/utils/location'

const props = defineProps<{
  /** Slug sản phẩm đang xem. */
  slug: string
  /** Chủ thể của sản phẩm: dẫn tới các điểm khác của chủ thể trên bản đồ. */
  subject: { id: number; name: string }
}>()

const items = ref<ProductLocationItem[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
let latestRequestId = 0

const features = computed(() => items.value.map(locationToFeature))
/** Nối từng nơi sản xuất với nơi bán bằng đường nét đứt (tối đa 6 cặp). */
const links = computed<Array<[string, string]>>(() => {
  const producers = items.value.filter((item) => item.role === 'produced_here')
  const sellers = items.value.filter((item) => item.role === 'sold_here')
  const pairs: Array<[string, string]> = []
  for (const producer of producers) {
    for (const seller of sellers) pairs.push([producer.slug, seller.slug])
  }
  return pairs.slice(0, 6)
})

async function load(): Promise<void> {
  const requestId = ++latestRequestId
  isLoading.value = true
  errorMessage.value = ''
  try {
    const response = await getProductLocations(props.slug)
    if (requestId !== latestRequestId) return
    items.value = response.items
  } catch (error) {
    if (requestId !== latestRequestId) return
    items.value = []
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải nơi mua sản phẩm này.')
  } finally {
    if (requestId === latestRequestId) isLoading.value = false
  }
}

watch(() => props.slug, load, { immediate: true })
onBeforeUnmount(() => {
  latestRequestId++
})
</script>

<template>
  <section
    v-if="isLoading || errorMessage || items.length"
    class="where-to-buy"
    aria-labelledby="where-to-buy-title"
    data-test="where-to-buy"
  >
    <div class="where-head">
      <div>
        <span class="where-eyebrow">Mua và tham quan</span>
        <h2 id="where-to-buy-title">Mua sản phẩm này ở đâu</h2>
      </div>
      <RouterLink
        v-if="items.length"
        class="where-cta"
        :to="{ name: 'map', query: { product: slug } }"
        data-test="where-map-link"
      >
        Xem trên bản đồ lớn
        <AppIcon name="chevronRight" :size="14" />
      </RouterLink>
    </div>

    <p v-if="isLoading" class="where-state" role="status">Đang tải nơi mua sản phẩm…</p>
    <div v-else-if="errorMessage" class="where-state" role="alert">
      {{ errorMessage }}
      <button type="button" class="where-retry" @click="load">Thử lại</button>
    </div>

    <div v-else class="where-body">
      <ul class="where-list">
        <li v-for="item in items" :key="item.id" class="where-place" data-test="where-place">
          <span
            class="where-icon"
            :class="{ 'is-shop': locationKind(item.type) === 'shop' }"
            :style="{
              '--place-color': locationTypeStyle(item.type).color,
              '--place-on': locationTypeStyle(item.type).onColor ?? 'var(--ocop-white)',
            }"
            aria-hidden="true"
          >
            <AppIcon :name="locationTypeStyle(item.type).icon" :size="20" />
          </span>
          <span class="where-text">
            <span class="where-name">
              <strong>{{ item.name }}</strong>
              <span class="where-role" data-test="where-role">{{ productRoleLabel(item.role) }}</span>
            </span>
            <small>{{ item.type_label }} · {{ item.address }}</small>
          </span>
          <span class="where-actions">
            <RouterLink :to="{ name: 'map', query: { diem: item.slug, action: 'route' } }">Chỉ đường</RouterLink>
            <RouterLink :to="{ name: 'location-detail', params: { slug: item.slug } }">Chi tiết</RouterLink>
          </span>
        </li>
      </ul>

      <div class="where-map">
        <LeafletMap
          :features="features"
          :links="links"
          :cluster="true"
          :initial-zoom="11"
          label="Bản đồ nhỏ: nơi mua và sản xuất sản phẩm"
        />
      </div>
    </div>

    <RouterLink
      v-if="items.length"
      class="where-subject"
      :to="{ name: 'map', query: { subject: String(subject.id) } }"
      data-test="where-subject-link"
    >
      <span>
        <small>Chủ thể sản xuất</small>
        <strong>{{ subject.name }}</strong>
      </span>
      <span class="where-subject-cta">
        Xem địa điểm của chủ thể trên bản đồ
        <AppIcon name="chevronRight" :size="14" />
      </span>
    </RouterLink>
    <p v-if="items.length" class="where-note">
      Thông tin điểm bán do chủ thể khai báo và đã được quản trị viên duyệt. Hãy liên hệ cửa hàng để biết còn hàng.
    </p>
  </section>
</template>

<style scoped>
.where-to-buy {
  display: grid;
  gap: var(--ocop-space-4);
  padding: var(--ocop-space-6);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-xl);
  background: var(--ocop-card);
}

.where-head {
  display: flex;
  flex-wrap: wrap;
  align-items: flex-end;
  justify-content: space-between;
  gap: var(--ocop-space-3);
}

.where-eyebrow {
  color: var(--ocop-daquy-700);
  font-size: var(--ocop-font-size-caption);
  font-weight: 800;
  letter-spacing: 0.04em;
  text-transform: uppercase;
}

.where-head h2 {
  margin: 2px 0 0;
  color: var(--ocop-navy);
  font-size: var(--ocop-font-size-title-md);
  font-weight: 800;
}

.where-cta {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  gap: 6px;
  padding: 0 var(--ocop-space-5);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
  text-decoration: none;
}

.where-state {
  margin: 0;
  color: var(--ocop-text-muted);
}

.where-retry {
  min-height: var(--ocop-control-md);
  margin-left: var(--ocop-space-2);
  padding: 0 var(--ocop-space-4);
  border: 1px solid var(--ocop-primary-700);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-card);
  color: var(--ocop-primary-700);
  font-weight: 700;
}

.where-body {
  display: grid;
  gap: var(--ocop-space-4);
}

.where-list {
  display: grid;
  align-content: start;
  gap: var(--ocop-space-3);
  margin: 0;
  padding: 0;
  list-style: none;
}

.where-place {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-3);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-surface-subtle);
}

.where-icon {
  display: grid;
  width: 44px;
  height: 44px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: var(--place-color);
  color: var(--place-on);
}

.where-icon.is-shop {
  border-radius: var(--ocop-radius-md);
}

.where-text {
  display: grid;
  min-width: 0;
  flex: 1 1 14rem;
  gap: 2px;
}

.where-name {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: var(--ocop-space-2);
}

.where-name strong {
  color: var(--ocop-navy);
  overflow-wrap: anywhere;
}

.where-role {
  padding: 2px var(--ocop-space-2);
  border-radius: var(--ocop-radius-pill);
  background: var(--ocop-daquy-100);
  color: var(--ocop-daquy-800);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
}

.where-text small {
  color: var(--ocop-text-muted);
  font-size: var(--ocop-font-size-small);
}

.where-actions {
  display: flex;
  gap: var(--ocop-space-2);
}

.where-actions a {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  padding: 0 var(--ocop-space-3);
  border: 1px solid var(--ocop-primary-700);
  border-radius: var(--ocop-radius-pill);
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
  text-decoration: none;
}

.where-map {
  position: relative;
  isolation: isolate;
  height: 300px;
  overflow: hidden;
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
}

.where-subject {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  justify-content: space-between;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-4);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-surface-subtle);
  color: var(--ocop-navy);
  text-decoration: none;
}

.where-subject small {
  display: block;
  color: var(--ocop-text-muted);
}

.where-subject-cta {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  gap: 6px;
  color: var(--ocop-primary-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 700;
}

.where-note {
  margin: 0;
  color: var(--ocop-text-muted);
  font-size: var(--ocop-font-size-small);
}

@media (min-width: 992px) {
  .where-body {
    grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  }

  .where-map {
    height: auto;
    min-height: 300px;
  }
}
</style>
