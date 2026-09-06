<script setup lang="ts">
import { onMounted } from 'vue'

import { authStore } from '@/stores/auth'

onMounted(() => {
  void authStore.initialize()
})
</script>

<template>
  <RouterView />
</template>
