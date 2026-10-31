<script setup lang="ts">
import { onMounted, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import { getApiErrorMessage } from '@/services/api-error'
import { getSocialProviders } from '@/services/auth'
import type { SocialProvider } from '@/types/auth'
import { SOCIAL_PROVIDER_LABELS, beginSocialRedirect } from '@/utils/social-login'

const props = withDefaults(
  defineProps<{
    /** Trang cần mở sau khi đăng nhập (query `redirect` của trang đăng nhập). */
    redirect?: unknown
    heading?: string
    note?: string
  }>(),
  {
    redirect: undefined,
    heading: 'hoặc tiếp tục với',
    note: 'Hệ thống chỉ nhận tên và email của tài khoản bạn chọn, không đăng gì lên trang cá nhân của bạn.',
  },
)

const providers = ref<SocialProvider[]>([])
const activeProvider = ref<SocialProvider | null>(null)
const errorMessage = ref('')

onMounted(async () => {
  try {
    providers.value = await getSocialProviders()
  } catch {
    // Đăng nhập mạng xã hội là tùy chọn: không tải được danh sách thì chỉ ẩn các nút.
    providers.value = []
  }
})

async function start(provider: SocialProvider): Promise<void> {
  if (activeProvider.value) return
  activeProvider.value = provider
  errorMessage.value = ''
  try {
    await beginSocialRedirect(provider, 'login', props.redirect)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(
      error,
      `Chưa mở được trang đăng nhập ${SOCIAL_PROVIDER_LABELS[provider]}. Vui lòng thử lại.`,
    )
    activeProvider.value = null
  }
}
</script>

<template>
  <div v-if="providers.length" class="social-login" data-testid="social-login">
    <p class="social-divider" aria-hidden="true"><span>{{ heading }}</span></p>
    <div v-if="errorMessage" class="alert alert-danger py-2 mb-0" role="alert">
      {{ errorMessage }}
    </div>
    <div class="social-buttons">
      <button
        v-for="provider in providers"
        :key="provider"
        class="ocop-btn-ghost social-button"
        type="button"
        :disabled="activeProvider !== null"
        :aria-busy="activeProvider === provider"
        @click="start(provider)"
      >
        <span
          v-if="activeProvider === provider"
          class="spinner-border spinner-border-sm"
          aria-hidden="true"
        />
        <AppIcon v-else :name="provider" :size="18" />
        <span>
          <template v-if="activeProvider === provider">Đang chuyển trang…</template>
          <template v-else><span class="visually-hidden">Tiếp tục với </span>{{ SOCIAL_PROVIDER_LABELS[provider] }}</template>
        </span>
      </button>
    </div>
    <p v-if="note" class="social-note">{{ note }}</p>
  </div>
</template>

<style scoped>
.social-login {
  display: grid;
  gap: var(--ocop-space-3);
}

.social-divider {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-3);
  margin: 0;
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-small);
}

.social-divider::before,
.social-divider::after {
  flex: 1;
  height: 1px;
  background: var(--ocop-border);
  content: '';
}

.social-buttons {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(9.5rem, 1fr));
  gap: var(--ocop-space-2);
}

.social-note {
  margin: 0;
  color: var(--ocop-text-secondary);
  font-size: var(--ocop-font-size-caption);
  text-align: center;
}

.social-button {
  display: inline-flex;
  width: 100%;
  min-height: var(--ocop-control-md);
  align-items: center;
  justify-content: center;
  gap: var(--ocop-space-2);
  padding: 0 var(--ocop-space-3);
  color: var(--ocop-text-primary);
}

.social-button:focus-visible {
  outline: 3px solid var(--ocop-primary-500);
  outline-offset: 2px;
}

.social-button:disabled {
  cursor: progress;
  opacity: 0.7;
}
</style>
