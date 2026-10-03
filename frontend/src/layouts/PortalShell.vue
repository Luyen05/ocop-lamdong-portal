<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import { checkApiHealth } from '@/services/system'
import { authStore } from '@/stores/auth'
import pkg from '../../package.json'

export interface PortalNavItem {
  label: string
  icon: string
  to: string
  /** Chỉ sáng khi đúng đường dẫn (mục gốc như /quan-tri). Mặc định sáng cả các trang con. */
  exact?: boolean
}

export interface PortalNotification {
  key: string
  label: string
  count: number
  to: string
}

const props = withDefaults(
  defineProps<{
    brandTitle: string
    brandSubtitle: string
    brandTo: string
    navLabel: string
    navItems: PortalNavItem[]
    roleLabel: string
    profileTo: string
    pageTitle: string
    pageSubtitle?: string
    /** null: ẩn chuông (không có dữ liệu thật để hiển thị). */
    notifications?: PortalNotification[] | null
  }>(),
  {
    pageSubtitle: '',
    notifications: null,
  },
)

const route = useRoute()
const router = useRouter()

const version = pkg.version
const isDrawerOpen = ref(false)
const isBellOpen = ref(false)
const bellRoot = ref<HTMLElement | null>(null)

const userName = computed(() => authStore.currentUser.value?.full_name ?? '')
const userInitial = computed(() => userName.value.trim().charAt(0).toUpperCase() || '?')

const pendingNotifications = computed(() => (props.notifications ?? []).filter((item) => item.count > 0))
const notificationTotal = computed(() => pendingNotifications.value.reduce((sum, item) => sum + item.count, 0))
const bellLabel = computed(() =>
  notificationTotal.value > 0
    ? `Thông báo: ${notificationTotal.value} việc cần xử lý`
    : 'Thông báo: không có việc cần xử lý',
)

function isActive(item: PortalNavItem): boolean {
  if (item.exact) return route.path === item.to
  return route.path === item.to || route.path.startsWith(`${item.to}/`)
}

// Trạng thái kết nối API lấy từ endpoint thật GET /health/database.
const apiState = ref<'checking' | 'ok' | 'down'>('checking')
let healthTimer: number | undefined

async function refreshApiState(): Promise<void> {
  apiState.value = (await checkApiHealth()) ? 'ok' : 'down'
}

function closeOverlays(): void {
  isDrawerOpen.value = false
  isBellOpen.value = false
}

function onKeydown(event: KeyboardEvent): void {
  if (event.key === 'Escape') closeOverlays()
}

function onDocumentClick(event: MouseEvent): void {
  if (isBellOpen.value && bellRoot.value && !bellRoot.value.contains(event.target as Node)) {
    isBellOpen.value = false
  }
}

async function logout(): Promise<void> {
  authStore.logout()
  await router.push('/dang-nhap')
}

watch(() => route.fullPath, closeOverlays)

onMounted(() => {
  document.addEventListener('keydown', onKeydown)
  document.addEventListener('click', onDocumentClick)
  void refreshApiState()
  healthTimer = window.setInterval(() => void refreshApiState(), 60_000)
})

onBeforeUnmount(() => {
  document.removeEventListener('keydown', onKeydown)
  document.removeEventListener('click', onDocumentClick)
  if (healthTimer !== undefined) window.clearInterval(healthTimer)
})
</script>

<template>
  <div class="ps-shell">
    <a class="ps-skip" href="#ps-content">Bỏ qua điều hướng, tới nội dung chính</a>

    <button
      v-if="isDrawerOpen"
      class="ps-backdrop"
      type="button"
      aria-label="Đóng menu"
      @click="isDrawerOpen = false"
    />

    <aside id="portal-sidebar" class="ps-sidebar" :class="{ 'is-open': isDrawerOpen }">
      <RouterLink class="ps-brand" :to="brandTo">
        <span class="ps-brand__logo"><img src="/assets/figma/home/icon-brand.svg" alt="" width="20" height="20" /></span>
        <span class="ps-brand__text">
          <strong>{{ brandTitle }}</strong>
          <small>{{ brandSubtitle }}</small>
        </span>
      </RouterLink>

      <nav class="ps-nav" :aria-label="navLabel">
        <RouterLink v-for="item in navItems" :key="item.to" v-slot="{ href, navigate }" :to="item.to" custom>
          <a
            class="ps-nav__item"
            :class="{ 'is-active': isActive(item) }"
            :href="href"
            :title="item.label"
            :aria-current="isActive(item) ? 'page' : undefined"
            @click="navigate"
          >
            <span class="ps-nav__icon"><AppIcon :name="item.icon" :size="18" /></span>
            <span class="ps-nav__label">{{ item.label }}</span>
          </a>
        </RouterLink>
      </nav>

      <div class="ps-sidebar__footer">
        <RouterLink class="ps-foot-link" to="/" title="Trang công khai">
          <AppIcon name="arrowLeft" :size="16" />
          <span class="ps-foot-link__label">Trang công khai</span>
        </RouterLink>
        <button class="ps-foot-link" type="button" title="Đăng xuất" @click="logout">
          <AppIcon name="logout" :size="16" />
          <span class="ps-foot-link__label">Đăng xuất</span>
        </button>
        <p class="ps-version">
          <span class="ps-version__label">Phiên bản</span>
          <strong>{{ version }}</strong>
        </p>
      </div>
    </aside>

    <div class="ps-main">
      <header class="ps-topbar">
        <button
          class="ps-topbar__toggle"
          type="button"
          :aria-expanded="isDrawerOpen"
          aria-controls="portal-sidebar"
          aria-label="Mở hoặc đóng menu"
          @click="isDrawerOpen = !isDrawerOpen"
        >
          <AppIcon name="menu" :size="20" />
        </button>

        <div class="ps-topbar__title">
          <p class="ps-topbar__name">{{ pageTitle }}</p>
          <p v-if="pageSubtitle" class="ps-topbar__sub">{{ pageSubtitle }}</p>
        </div>

        <div class="ps-topbar__right">
          <span v-if="apiState !== 'checking'" class="ps-api" :class="`is-${apiState}`" role="status">
            <span class="ps-api__dot" aria-hidden="true" />
            <span class="ps-api__text">{{ apiState === 'ok' ? 'API kết nối' : 'Mất kết nối API' }}</span>
          </span>

          <div v-if="notifications" ref="bellRoot" class="ps-bell">
            <button
              class="ps-bell__button"
              type="button"
              :aria-expanded="isBellOpen"
              aria-controls="portal-notifications"
              :aria-label="bellLabel"
              @click="isBellOpen = !isBellOpen"
            >
              <AppIcon name="bell" :size="18" />
              <span v-if="notificationTotal > 0" class="ps-bell__badge" aria-hidden="true">
                {{ notificationTotal > 99 ? '99+' : notificationTotal }}
              </span>
            </button>
            <div v-if="isBellOpen" id="portal-notifications" class="ps-bell__panel">
              <p class="ps-bell__title">Việc cần xử lý</p>
              <ul v-if="pendingNotifications.length" class="ps-bell__list">
                <li v-for="item in pendingNotifications" :key="item.key">
                  <RouterLink :to="item.to">
                    <span>{{ item.label }}</span>
                    <strong>{{ item.count }}</strong>
                  </RouterLink>
                </li>
              </ul>
              <p v-else class="ps-bell__empty">Không có việc nào đang chờ.</p>
            </div>
          </div>

          <RouterLink class="ps-avatar" :to="profileTo">
            <span class="ps-avatar__initial" aria-hidden="true">{{ userInitial }}</span>
            <span class="ps-avatar__info">
              <strong>{{ userName }}</strong>
              <small>{{ roleLabel }}</small>
            </span>
          </RouterLink>
        </div>
      </header>

      <main id="ps-content" class="ps-content" tabindex="-1">
        <slot />
      </main>
    </div>
  </div>
</template>

<style scoped>
.ps-shell {
  display: grid;
  min-height: 100vh;
  grid-template-columns: var(--admin-sidebar-width) minmax(0, 1fr);
  background: var(--admin-bg);
  color: var(--admin-text);
  font-family: var(--admin-font);

  /* Trang bên trong khung dùng token thương hiệu cũ (--ocop-primary-*, --ocop-mint-*):
     trong khu quản trị và chủ thể chúng trỏ về màu chủ đạo sáng của khung, trang công khai không bị ảnh hưởng. */
  --ocop-primary-950: var(--admin-primary-dark);
  --ocop-primary-900: var(--admin-primary-dark);
  --ocop-primary-800: var(--admin-primary-dark);
  --ocop-primary-700: var(--admin-primary);
  --ocop-primary-500: var(--admin-primary);
  --ocop-mint-soft: var(--admin-primary-soft);
  --ocop-mint-100: var(--admin-primary-soft);
  --ocop-mint-border: var(--admin-primary-border);
  --ocop-mint-200: var(--admin-primary-border);
}

.ps-skip {
  position: absolute;
  z-index: 100;
  top: 8px;
  left: 8px;
  padding: 10px 14px;
  border-radius: var(--admin-radius-sm);
  background: var(--admin-primary);
  color: var(--admin-on-primary);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  text-decoration: none;
  transform: translateY(-200%);
}
.ps-skip:focus-visible { transform: translateY(0); }

.ps-backdrop {
  position: fixed;
  z-index: 45;
  inset: 0;
  border: 0;
  background: var(--admin-scrim);
}

/* ── Sidebar ── */
.ps-sidebar {
  position: sticky;
  z-index: 50;
  top: 0;
  display: flex;
  height: 100vh;
  flex-direction: column;
  gap: var(--admin-space-5);
  overflow-y: auto;
  padding: var(--admin-space-5) var(--admin-space-3) var(--admin-space-4);
  border-right: 1px solid var(--admin-sidebar-border);
  background: var(--admin-sidebar-bg);
}

.ps-brand {
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 10px;
  padding: 0 var(--admin-space-2);
  color: var(--admin-text);
  text-decoration: none;
}
.ps-brand__logo {
  display: grid;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  place-items: center;
  border-radius: var(--admin-radius-md);
  background: var(--admin-primary);
}
.ps-brand__text { display: grid; min-width: 0; }
.ps-brand__text strong { font-size: var(--admin-font-sm); font-weight: 800; letter-spacing: 0.02em; }
.ps-brand__text small { color: var(--admin-muted); font-size: var(--admin-font-xs); }

.ps-nav { display: grid; align-content: start; gap: 4px; }
.ps-nav__item {
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 10px;
  padding: 0 var(--admin-space-2);
  border-radius: var(--admin-radius-md);
  color: var(--admin-muted);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  text-decoration: none;
  transition: background var(--admin-transition), color var(--admin-transition);
}
.ps-nav__item:hover { background: var(--admin-sidebar-hover); color: var(--admin-text); }
.ps-nav__item.is-active { background: var(--admin-sidebar-active-bg); color: var(--admin-sidebar-active-text); font-weight: 700; }
.ps-nav__icon {
  display: grid;
  width: 32px;
  height: 32px;
  flex-shrink: 0;
  place-items: center;
  border-radius: var(--admin-radius-sm);
  background: var(--admin-bg);
}
.ps-nav__item.is-active .ps-nav__icon { background: var(--admin-card); }

.ps-sidebar__footer { display: grid; gap: var(--admin-space-1); margin-top: auto; }
.ps-foot-link {
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 10px;
  padding: 0 var(--admin-space-3);
  border: 0;
  border-radius: var(--admin-radius-md);
  background: transparent;
  color: var(--admin-muted);
  font: inherit;
  font-size: var(--admin-font-sm);
  font-weight: 600;
  text-align: left;
  text-decoration: none;
  cursor: pointer;
}
.ps-foot-link:hover { background: var(--admin-sidebar-hover); color: var(--admin-text); }
.ps-version {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--admin-space-2);
  margin: var(--admin-space-2) 0 0;
  padding: var(--admin-space-3);
  border-radius: var(--admin-radius-md);
  background: var(--admin-bg);
  color: var(--admin-muted);
  font-size: var(--admin-font-xs);
}
.ps-version strong { color: var(--admin-text); font-weight: 700; }

/* ── Topbar ── */
.ps-main { min-width: 0; }
.ps-topbar {
  position: sticky;
  z-index: 30;
  top: 0;
  display: flex;
  min-height: var(--admin-topbar-height);
  align-items: center;
  gap: var(--admin-space-3);
  padding: 0 var(--admin-space-6);
  border-bottom: 1px solid var(--admin-border);
  background: var(--admin-topbar-bg);
}
.ps-topbar__toggle {
  display: none;
  width: 44px;
  height: 44px;
  flex-shrink: 0;
  place-items: center;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-md);
  background: var(--admin-card);
  color: var(--admin-text);
  cursor: pointer;
}
.ps-topbar__title { min-width: 0; }
.ps-topbar__title p { margin: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ps-topbar__name { font-size: var(--admin-font-lg); font-weight: 800; }
.ps-topbar__sub { color: var(--admin-muted); font-size: var(--admin-font-xs); }
.ps-topbar__right { display: flex; align-items: center; gap: var(--admin-space-3); margin-left: auto; }

.ps-api {
  display: inline-flex;
  min-height: 32px;
  align-items: center;
  gap: 6px;
  padding: 0 var(--admin-space-3);
  border-radius: var(--admin-radius-pill);
  font-size: var(--admin-font-xs);
  font-weight: 700;
}
.ps-api.is-ok { background: var(--admin-badge-approved-bg); color: var(--admin-badge-approved-text); }
.ps-api.is-down { background: var(--admin-badge-rejected-bg); color: var(--admin-badge-rejected-text); }
.ps-api__dot { width: 8px; height: 8px; border-radius: 50%; background: currentColor; }

.ps-bell { position: relative; }
.ps-bell__button {
  position: relative;
  display: grid;
  width: 44px;
  height: 44px;
  place-items: center;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-md);
  background: var(--admin-card);
  color: var(--admin-text);
  cursor: pointer;
}
.ps-bell__button:hover { background: var(--admin-primary-soft); }
.ps-bell__badge {
  position: absolute;
  top: -6px;
  right: -6px;
  min-width: 20px;
  padding: 1px 5px;
  border-radius: var(--admin-radius-pill);
  background: var(--admin-danger);
  color: var(--admin-on-primary);
  font-size: var(--admin-font-xs);
  font-weight: 800;
  line-height: 1.4;
  text-align: center;
}
.ps-bell__panel {
  position: absolute;
  z-index: 60;
  top: calc(100% + 8px);
  right: 0;
  width: min(320px, calc(100vw - 32px));
  padding: var(--admin-space-3);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-modal);
}
.ps-bell__title {
  margin: 0 0 var(--admin-space-2);
  padding: 0 var(--admin-space-2);
  color: var(--admin-muted);
  font-size: var(--admin-font-xs);
  font-weight: 800;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}
.ps-bell__list { display: grid; gap: 2px; margin: 0; padding: 0; list-style: none; }
.ps-bell__list a {
  display: flex;
  min-height: 44px;
  align-items: center;
  justify-content: space-between;
  gap: var(--admin-space-3);
  padding: 0 var(--admin-space-2);
  border-radius: var(--admin-radius-sm);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  text-decoration: none;
}
.ps-bell__list a:hover { background: var(--admin-primary-soft); }
.ps-bell__list strong {
  min-width: 28px;
  padding: 2px 8px;
  border-radius: var(--admin-radius-pill);
  background: var(--admin-badge-pending-bg);
  color: var(--admin-badge-pending-text);
  font-size: var(--admin-font-xs);
  text-align: center;
}
.ps-bell__empty { margin: 0; padding: var(--admin-space-2); color: var(--admin-muted); font-size: var(--admin-font-sm); }

.ps-avatar {
  display: flex;
  min-height: 44px;
  align-items: center;
  gap: 10px;
  padding: 0 var(--admin-space-2);
  border-radius: var(--admin-radius-md);
  color: var(--admin-text);
  text-decoration: none;
}
.ps-avatar:hover { background: var(--admin-primary-soft); }
.ps-avatar__initial {
  display: grid;
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  place-items: center;
  border-radius: 50%;
  background: var(--admin-primary);
  color: var(--admin-on-primary);
  font-size: var(--admin-font-sm);
  font-weight: 800;
}
.ps-avatar__info { display: grid; min-width: 0; }
.ps-avatar__info strong {
  max-width: 160px;
  overflow: hidden;
  font-size: var(--admin-font-sm);
  text-overflow: ellipsis;
  white-space: nowrap;
}
.ps-avatar__info small { color: var(--admin-muted); font-size: var(--admin-font-xs); }

.ps-content {
  width: min(100%, 1280px);
  margin-inline: auto;
  padding: var(--admin-space-6);
  outline: none;
}

:where(.ps-nav__item, .ps-foot-link, .ps-bell__button, .ps-bell__list a, .ps-avatar, .ps-topbar__toggle, .ps-brand):focus-visible {
  outline: 3px solid var(--admin-primary);
  outline-offset: 2px;
}

/* ── Máy tính bảng: sidebar thu thành cột icon ── */
@media (min-width: 768px) and (max-width: 1023.98px) {
  .ps-shell { grid-template-columns: var(--admin-sidebar-rail-width) minmax(0, 1fr); }
  .ps-sidebar { align-items: center; padding-inline: var(--admin-space-2); }
  .ps-brand { padding: 0; }
  .ps-brand__text,
  .ps-nav__label,
  .ps-foot-link__label,
  .ps-version__label {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
  .ps-nav,
  .ps-sidebar__footer { width: 100%; }
  .ps-nav__item,
  .ps-foot-link { justify-content: center; padding: 0; }
  .ps-version { justify-content: center; padding: var(--admin-space-2) 0; }
  .ps-avatar__info {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
  .ps-topbar { padding-inline: var(--admin-space-5); }
}

/* ── Điện thoại: sidebar thành ngăn kéo ── */
@media (max-width: 767.98px) {
  .ps-shell { grid-template-columns: minmax(0, 1fr); }
  .ps-sidebar {
    position: fixed;
    top: 0;
    left: 0;
    width: min(var(--admin-sidebar-width), 85vw);
    box-shadow: var(--admin-shadow-modal);
    transform: translateX(-110%);
    visibility: hidden;
    transition: transform 220ms ease, visibility 0s linear 220ms;
  }
  .ps-sidebar.is-open {
    transform: translateX(0);
    visibility: visible;
    transition: transform 220ms ease, visibility 0s;
  }
  .ps-topbar { padding-inline: var(--admin-space-4); }
  .ps-topbar__toggle { display: grid; }
  .ps-topbar__sub { display: none; }
  .ps-avatar__info {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
  .ps-api { padding: 0; }
  .ps-api__text {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip-path: inset(50%);
    white-space: nowrap;
  }
  .ps-api__dot { width: 12px; height: 12px; margin: 10px; }
  .ps-content { padding: var(--admin-space-5) var(--admin-space-4); }
}

/* Mỗi lần đổi trang, nội dung hiện dần nhẹ (các khối bên trong tự xuất hiện lần lượt bằng .stagger-in). */
:slotted(*) { animation: ocop-fade-in 260ms ease-out both; }

@media (prefers-reduced-motion: reduce) {
  :slotted(*) { animation: none; }
  .ps-sidebar,
  .ps-sidebar.is-open,
  .ps-nav__item { transition: none; }
}
</style>
