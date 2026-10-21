<script setup lang="ts">
import { computed } from 'vue'

import { formatAverage } from '@/utils/review'

/** Hàng 5 ngôi sao chỉ để xem; trình đọc màn hình đọc "4,5 trên 5 sao". */
const props = withDefaults(defineProps<{ rating: number; size?: 'sm' | 'md' | 'lg' }>(), { size: 'md' })

const label = computed(() => {
  const value = Number.isInteger(props.rating) ? String(props.rating) : formatAverage(props.rating)
  return `${value} trên 5 sao`
})

function iconFor(position: number): string {
  if (props.rating >= position) return 'bi-star-fill'
  if (props.rating >= position - 0.5) return 'bi-star-half'
  return 'bi-star'
}
</script>

<template>
  <span class="review-stars" :class="`is-${size}`" role="img" :aria-label="label">
    <i
      v-for="position in 5"
      :key="position"
      class="bi"
      :class="[iconFor(position), { 'is-empty': rating < position - 0.5 }]"
      aria-hidden="true"
    />
  </span>
</template>

<style scoped>
.review-stars {
  display: inline-flex;
  align-items: center;
  gap: 2px;
  color: var(--ocop-daquy-600);
  font-size: var(--ocop-font-size-small);
  line-height: 1;
}

.review-stars.is-md {
  font-size: var(--ocop-font-size-body);
}

.review-stars.is-lg {
  font-size: var(--ocop-font-size-title-sm);
}

.review-stars .is-empty {
  color: var(--ocop-mist-300);
}
</style>
