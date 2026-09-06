<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute } from 'vue-router'

import AppHeader from '@/components/AppHeader.vue'
import { authStore } from '@/stores/auth'

const route = useRoute()

onMounted(() => {
  void authStore.initialize()
})
</script>

<template>
  <AppHeader v-if="route.meta.layout !== 'auth'" />
  <RouterView />
</template>
