<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getSocialProviders, unlinkSocialAccount } from '@/services/auth'
import { authStore } from '@/stores/auth'
import type { SocialProvider } from '@/types/auth'
import { SOCIAL_PROVIDER_LABELS, beginSocialRedirect } from '@/utils/social-login'

const props = defineProps<{
  /** Nhà cung cấp vừa liên kết xong (query `lien-ket` khi quay về từ Google/Facebook). */
  justLinked?: string | null
}>()

const user = authStore.currentUser
const enabledProviders = ref<SocialProvider[]>([])
const busyProvider = ref<SocialProvider | null>(null)
const errorMessage = ref('')
const successMessage = ref('')

const linked = computed(() => new Set(user.value?.social_providers ?? []))
/** Hiện cả nhà cung cấp đã liên kết nhưng hiện bị tắt, để người dùng vẫn bỏ liên kết được. */
const rows = computed(() => {
  const providers = new Set<SocialProvider>([...enabledProviders.value, ...linked.value])
  return (['google', 'facebook'] as const).filter((provider) => providers.has(provider))
})

function isLastMethod(provider: SocialProvider): boolean {
  return Boolean(user.value) && user.value?.has_password === false
    && linked.value.size === 1 && linked.value.has(provider)
}

onMounted(async () => {
  if (props.justLinked === 'google' || props.justLinked === 'facebook') {
    successMessage.value = `Đã liên kết ${SOCIAL_PROVIDER_LABELS[props.justLinked]}. Lần sau bạn có thể đăng nhập bằng ${SOCIAL_PROVIDER_LABELS[props.justLinked]}.`
  }
  try {
    enabledProviders.value = await getSocialProviders()
  } catch {
    enabledProviders.value = []
  }
})

async function link(provider: SocialProvider): Promise<void> {
  if (busyProvider.value) return
  busyProvider.value = provider
  errorMessage.value = ''
  successMessage.value = ''
  try {
    await beginSocialRedirect(provider, 'link')
  } catch (error) {
    errorMessage.value = getApiErrorMessage(
      error,
      `Chưa mở được trang ${SOCIAL_PROVIDER_LABELS[provider]}. Vui lòng thử lại.`,
    )
    busyProvider.value = null
  }
}

async function unlink(provider: SocialProvider): Promise<void> {
  if (busyProvider.value) return
  busyProvider.value = provider
  errorMessage.value = ''
  successMessage.value = ''
  try {
    authStore.setCurrentUser(await unlinkSocialAccount(provider))
    successMessage.value = `Đã bỏ liên kết ${SOCIAL_PROVIDER_LABELS[provider]}.`
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể bỏ liên kết. Vui lòng thử lại.')
  } finally {
    busyProvider.value = null
  }
}
</script>

<template>
  <section
    v-if="user && user.role !== 'admin' && rows.length"
    class="social-links"
    aria-labelledby="social-links-title"
    data-testid="social-links"
  >
    <h2 id="social-links-title" class="h4 mb-1">Liên kết đăng nhập</h2>
    <p class="mb-3 text-secondary">
      Liên kết để lần sau đăng nhập nhanh bằng Google hoặc Facebook. Hệ thống chỉ nhận tên và email.
    </p>

    <div v-if="errorMessage" class="alert alert-danger" role="alert">{{ errorMessage }}</div>
    <div v-if="successMessage" class="alert alert-success" role="status">{{ successMessage }}</div>

    <ul class="social-link-list">
      <li v-for="provider in rows" :key="provider" class="social-link-row">
        <AppIcon :name="provider" :size="20" />
        <span class="social-link-name">
          <strong>{{ SOCIAL_PROVIDER_LABELS[provider] }}</strong>
          <small>{{ linked.has(provider) ? 'Đã liên kết' : 'Chưa liên kết' }}</small>
        </span>
        <button
          v-if="linked.has(provider)"
          class="ocop-btn-ghost social-link-action"
          type="button"
          :disabled="busyProvider !== null || isLastMethod(provider)"
          :aria-describedby="isLastMethod(provider) ? `last-method-${provider}` : undefined"
          @click="unlink(provider)"
        >
          Bỏ liên kết
          <span class="visually-hidden">{{ SOCIAL_PROVIDER_LABELS[provider] }}</span>
        </button>
        <button
          v-else
          class="ocop-btn-ghost social-link-action"
          type="button"
          :disabled="busyProvider !== null || !enabledProviders.includes(provider)"
          @click="link(provider)"
        >
          {{ busyProvider === provider ? 'Đang chuyển trang…' : 'Liên kết' }}
          <span class="visually-hidden">{{ SOCIAL_PROVIDER_LABELS[provider] }}</span>
        </button>
        <small v-if="isLastMethod(provider)" :id="`last-method-${provider}`" class="social-link-note">
          Đây là cách đăng nhập duy nhất của tài khoản nên chưa bỏ liên kết được.
        </small>
      </li>
    </ul>
  </section>
</template>

<style scoped>
.social-link-list {
  display: grid;
  gap: var(--ocop-space-2);
  margin: 0;
  padding: 0;
  list-style: none;
}

.social-link-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  align-items: center;
  gap: var(--ocop-space-3);
  padding: var(--ocop-space-3) var(--ocop-space-4);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-card);
}

.social-link-name {
  display: grid;
}

.social-link-name small {
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-caption);
}

.social-link-action {
  min-height: var(--ocop-control-md);
  padding: 0 var(--ocop-space-4);
}

.social-link-action:disabled {
  cursor: not-allowed;
  opacity: 0.65;
}

.social-link-note {
  grid-column: 1 / -1;
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-caption);
}
</style>
