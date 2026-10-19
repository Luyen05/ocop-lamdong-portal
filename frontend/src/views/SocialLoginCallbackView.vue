<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AuthLayout from '@/components/auth/AuthLayout.vue'
import { resolvePostLoginTarget } from '@/router/access'
import { getApiErrorMessage } from '@/services/api-error'
import { completeSocialLogin, linkSocialAccount } from '@/services/auth'
import { authStore } from '@/stores/auth'
import {
  SOCIAL_PROVIDER_LABELS,
  clearPendingSocialLogin,
  isSocialProvider,
  readPendingSocialLogin,
  type SocialLoginMode,
} from '@/utils/social-login'

const route = useRoute()
const router = useRouter()

const provider = isSocialProvider(route.params.provider) ? route.params.provider : null
const providerLabel = provider ? SOCIAL_PROVIDER_LABELS[provider] : 'mạng xã hội'
// Mã chỉ dùng được một lần: đọc xong thì xóa phiên chờ ngay để tải lại trang không gửi lại.
const pending = readPendingSocialLogin()
clearPendingSocialLogin()
const mode = ref<SocialLoginMode>(pending?.mode ?? 'login')
const errorMessage = ref('')
const retryRedirect = ref<string | null>(pending?.redirect ?? null)

const title = computed(() =>
  mode.value === 'link' ? `Liên kết ${providerLabel}` : `Đăng nhập bằng ${providerLabel}`,
)
const retryLink = computed(() => {
  if (mode.value === 'link') return '/tai-khoan'
  return retryRedirect.value ? { path: '/dang-nhap', query: { redirect: retryRedirect.value } } : '/dang-nhap'
})

function queryText(name: string): string | null {
  const value = route.query[name]
  return typeof value === 'string' && value ? value : null
}

onMounted(async () => {
  const code = queryText('code')
  const state = queryText('state')
  const providerError = queryText('error')
  if (code || state || providerError) {
    // Bỏ mã khỏi thanh địa chỉ và lịch sử trình duyệt.
    await router.replace({ path: route.path, query: {} })
  }

  if (!provider) {
    errorMessage.value = 'Đường dẫn đăng nhập không hợp lệ.'
    return
  }
  if (providerError) {
    errorMessage.value = `Bạn đã hủy hoặc chưa cho phép ${mode.value === 'link' ? 'liên kết' : 'đăng nhập bằng'} ${providerLabel}.`
    return
  }
  if (!code || !state || !pending || pending.provider !== provider || pending.state !== state) {
    errorMessage.value = 'Phiên đăng nhập không hợp lệ hoặc đã hết hạn (quá 10 phút). Vui lòng thử lại.'
    return
  }
  const payload = { code, ...(pending.codeVerifier ? { code_verifier: pending.codeVerifier } : {}) }

  if (pending.mode === 'link') {
    if (!authStore.isAuthenticated.value) {
      errorMessage.value = `Bạn cần đăng nhập trước khi liên kết ${providerLabel}.`
      return
    }
    try {
      authStore.setCurrentUser(await linkSocialAccount(provider, payload))
      await router.replace({ path: '/tai-khoan', query: { 'lien-ket': provider } })
    } catch (error) {
      errorMessage.value = getApiErrorMessage(error, `Không thể liên kết ${providerLabel}. Vui lòng thử lại.`)
    }
    return
  }

  try {
    const result = await completeSocialLogin(provider, payload)
    const user = await authStore.loginWithToken(result.access_token)
    await router.replace(resolvePostLoginTarget(user.role, pending.redirect))
  } catch (error) {
    errorMessage.value = getApiErrorMessage(
      error,
      `Không thể đăng nhập bằng ${providerLabel}. Vui lòng thử lại.`,
    )
  }
})
</script>

<template>
  <AuthLayout :title="title" subtitle="Hoàn tất với tài khoản OCOP Lâm Đồng.">
    <div v-if="errorMessage" class="d-grid gap-3">
      <div class="alert alert-danger mb-0" role="alert">{{ errorMessage }}</div>
      <RouterLink class="btn btn-success btn-lg" :to="retryLink">
        {{ mode === 'link' ? 'Về trang tài khoản' : 'Thử lại' }}
      </RouterLink>
      <RouterLink class="ocop-btn-ghost callback-home" to="/">Về trang chủ</RouterLink>
    </div>
    <p v-else class="callback-loading" role="status">
      <span class="spinner-border spinner-border-sm" aria-hidden="true" />
      Đang hoàn tất với {{ providerLabel }}…
    </p>
  </AuthLayout>
</template>

<style scoped>
.callback-loading {
  display: flex;
  align-items: center;
  gap: var(--ocop-space-2);
  margin: 0;
  color: var(--ocop-text-secondary);
}

.callback-home {
  min-height: var(--ocop-control-lg);
}
</style>
