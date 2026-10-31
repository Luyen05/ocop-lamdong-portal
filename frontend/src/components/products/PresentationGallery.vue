<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { safeExternalUrl } from '@/utils/location'

interface Image {
  id: number
  image_url: string
  is_primary: boolean
  sort_order: number
  source_url?: string | null
  credit?: string | null
  license?: string | null
}
const props = defineProps<{ images: Image[]; primaryUrl?: string | null; name: string; landscape?: boolean }>()
const selected = ref<string | null>(null)
// Ảnh (chính hoặc nhỏ) tải lỗi: ẩn nút ảnh nhỏ đó và tự chuyển ảnh chính sang ảnh hợp lệ kế tiếp.
const failedUrls = ref<Set<string>>(new Set())
const images = computed(() => [...props.images].sort((a, b) => Number(b.is_primary) - Number(a.is_primary) || a.sort_order - b.sort_order))
const candidates = computed(() => {
  const urls = images.value.map(image => image.image_url)
  if (props.primaryUrl && !urls.includes(props.primaryUrl)) urls.push(props.primaryUrl)
  return urls.filter(value => value && !failedUrls.value.has(value))
})
const url = computed(() => {
  if (selected.value && !failedUrls.value.has(selected.value)) return selected.value
  return candidates.value[0] ?? null
})
const active = computed(() => images.value.find(image => image.image_url === url.value))
const source = computed(() => safeExternalUrl(active.value?.source_url))
watch(() => [props.images, props.primaryUrl, props.name], () => {
  selected.value = null
  failedUrls.value = new Set()
})

function markFailed(value: string): void {
  failedUrls.value = new Set(failedUrls.value).add(value)
}

function select(value: string): void {
  selected.value = value
}
</script>

<template>
  <div class="gallery" :class="{ landscape, 'without-image': !url }">
    <div class="main-image">
      <img v-if="url" :key="url" :src="url" :alt="name" @error="markFailed(url)" />
      <div v-else class="image-placeholder">
        <AppIcon :name="landscape ? 'map-pin' : 'package'" :size="24" aria-hidden="true" />
        <span>Ảnh {{ landscape ? 'điểm đến' : 'sản phẩm' }} đang cập nhật</span>
      </div>
    </div>
    <p v-if="active && (source || active.credit || active.license)" class="image-credit">
      <a v-if="source" :href="source" target="_blank" rel="noopener noreferrer">Nguồn ảnh</a>
      <span v-if="active.credit">{{ active.credit }}</span>
      <span v-if="active.license">{{ active.license }}</span>
    </p>
    <div v-if="images.length > 1" class="thumbnail-list" aria-label="Chọn ảnh">
      <button v-for="(image, index) in images" v-show="!failedUrls.has(image.image_url)" :key="image.id" type="button" class="thumbnail" :class="{ active: url === image.image_url }" :aria-label="`Xem ảnh ${index + 1} của ${name}`" :aria-pressed="url === image.image_url" @click="select(image.image_url)">
        <img :src="image.image_url" alt="" loading="lazy" @error="markFailed(image.image_url)" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.gallery { min-width: 0; }
.main-image { aspect-ratio: 4 / 3; background: var(--ocop-card); border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-lg); overflow: hidden; }
.main-image img { width: 100%; height: 100%; object-fit: contain; }
.landscape .main-image img { object-fit: cover; }
.without-image .main-image { aspect-ratio: auto; min-height: calc(var(--ocop-space-16) + var(--ocop-space-12)); }
.image-placeholder { min-height: calc(var(--ocop-space-16) + var(--ocop-space-12)); display: flex; gap: var(--ocop-space-2); align-items: center; justify-content: center; padding: var(--ocop-space-4); color: var(--ocop-text-secondary); background: var(--ocop-sage-50); font-size: var(--ocop-font-size-body); }
.image-credit { display: flex; flex-wrap: wrap; gap: var(--ocop-space-2); margin: var(--ocop-space-2) 0; font-size: var(--ocop-font-size-caption); color: var(--ocop-text-secondary); }
.image-credit a { color: var(--ocop-primary-700); }
.thumbnail-list { display: flex; gap: var(--ocop-space-2); overflow-x: auto; margin-top: var(--ocop-space-3); }
.thumbnail { flex: 0 0 var(--ocop-space-16); height: var(--ocop-space-16); padding: 2px; background: var(--ocop-card); border: 2px solid var(--ocop-border); border-radius: var(--ocop-radius-sm); }
.thumbnail.active { border-color: var(--ocop-primary-700); }
.thumbnail img { width: 100%; height: 100%; object-fit: contain; }
</style>
