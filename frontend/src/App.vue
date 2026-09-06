<script setup lang="ts">
import { useRoute } from 'vue-router'

import AppHeader from '@/components/AppHeader.vue'
import SiteFooter from '@/components/SiteFooter.vue'

const route = useRoute()
</script>

<template>
  <AppHeader v-if="route.meta.layout !== 'auth'" />
  <RouterView />
  <SiteFooter v-if="route.meta.layout !== 'auth'" />
</template>
