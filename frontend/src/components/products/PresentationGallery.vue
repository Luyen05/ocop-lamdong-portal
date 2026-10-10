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
const failed = ref(false)
const images = computed(() => [...props.images].sort((a, b) => Number(b.is_primary) - Number(a.is_primary) || a.sort_order - b.sort_order))
const url = computed(() => selected.value || images.value[0]?.image_url || props.primaryUrl)
const active = computed(() => images.value.find(image => image.image_url === url.value))
const source = computed(() => safeExternalUrl(active.value?.source_url))
watch(() => [props.images, props.primaryUrl, props.name], () => {
  selected.value = null
  failed.value = false
})

function select(value: string): void {
  selected.value = value
  failed.value = false
}
</script>

<template>
  <div class="gallery" :class="{ landscape, 'without-image': !url || failed }">
    <div class="main-image">
      <img v-if="url && !failed" :src="url" :alt="name" @error="failed = true" />
      <div v-else class="image-placeholder">
        <AppIcon :name="landscape ? 'map-pin' : 'package'" :size="24" aria-hidden="true" />
        <span>Ảnh {{ landscape ? 'điểm đến' : 'sản phẩm' }} đang cập nhật</span>
      </div>
    </div>
    <p v-if="!failed && active && (source || active.credit || active.license)" class="image-credit">
      <a v-if="source" :href="source" target="_blank" rel="noopener noreferrer">Nguồn ảnh</a>
      <span v-if="active.credit">{{ active.credit }}</span>
      <span v-if="active.license">{{ active.license }}</span>
    </p>
    <div v-if="images.length > 1" class="thumbnail-list" aria-label="Chọn ảnh">
      <button v-for="(image, index) in images" :key="image.id" type="button" class="thumbnail" :class="{ active: url === image.image_url }" :aria-label="`Xem ảnh ${index + 1} của ${name}`" :aria-pressed="url === image.image_url" @click="select(image.image_url)">
        <img :src="image.image_url" alt="" loading="lazy" />
      </button>
    </div>
  </div>
</template>

<style scoped>
.gallery { min-width: 0; }
.main-image { aspect-ratio: 4 / 3; background: var(--ocop-card); border: 1px solid var(--ocop-border); border-radius: 1rem; overflow: hidden; }
.main-image img { width: 100%; height: 100%; object-fit: contain; }
.landscape .main-image img { object-fit: cover; }
.without-image .main-image { aspect-ratio: auto; min-height: 7rem; }
.image-placeholder { min-height: 7rem; display: flex; gap: .6rem; align-items: center; justify-content: center; padding: 1rem; color: var(--ocop-text-secondary); background: var(--ocop-sage-50); font-size: .9rem; }
.image-credit { display: flex; flex-wrap: wrap; gap: .5rem; margin: .5rem 0; font-size: .75rem; color: var(--ocop-text-secondary); }
.image-credit a { color: var(--ocop-primary-700); }
.thumbnail-list { display: flex; gap: .5rem; overflow-x: auto; margin-top: .75rem; }
.thumbnail { flex: 0 0 4rem; height: 4rem; padding: 2px; background: var(--ocop-card); border: 2px solid var(--ocop-border); border-radius: .5rem; }
.thumbnail.active { border-color: var(--ocop-primary-700); }
.thumbnail img { width: 100%; height: 100%; object-fit: contain; }
</style>
