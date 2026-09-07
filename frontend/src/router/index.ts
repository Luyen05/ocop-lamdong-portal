import { createRouter, createWebHistory } from 'vue-router'

import { AUTH_SESSION_EXPIRED_EVENT } from '@/services/token'
import { authStore } from '@/stores/auth'
import HomeView from '@/views/HomeView.vue'
import { resolveRouteAccess } from '@/router/access'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
    },
    {
      path: '/dang-nhap',
      name: 'login',
      component: () => import('@/views/LoginView.vue'),
      meta: { layout: 'auth', guestOnly: true },
    },
    {
      path: '/dang-ky',
      name: 'register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { layout: 'auth', guestOnly: true },
    },
    {
      path: '/tai-khoan',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/san-pham',
      name: 'products',
      component: () => import('@/views/ProductsView.vue'),
    },
    {
      path: '/san-pham/:slug',
      name: 'product-detail',
      component: () => import('@/views/ProductDetailView.vue'),
    },
    {
      path: '/khong-co-quyen',
      name: 'forbidden',
      component: () => import('@/views/ForbiddenView.vue'),
    },
    {
      path: '/quan-tri',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { layout: 'admin', requiresAuth: true, roles: ['admin'] },
      children: [
        {
          path: '',
          name: 'admin-dashboard',
          component: () => import('@/views/admin/AdminDashboardView.vue'),
        },
      ],
    },
  ],
  scrollBehavior: (to) =>
    to.hash ? { el: to.hash, behavior: 'smooth' } : { top: 0 },
})

router.beforeEach(async (to) => {
  await authStore.initialize()

  const decision = resolveRouteAccess(
    {
      requiresAuth: Boolean(to.meta.requiresAuth),
      guestOnly: Boolean(to.meta.guestOnly),
      roles: to.meta.roles,
    },
    authStore.currentUser.value,
  )

  if (decision === 'login') {
    return { name: 'login', query: { redirect: to.fullPath } }
  }
  if (decision === 'forbidden') {
    return { name: 'forbidden', query: { from: to.fullPath } }
  }
  if (decision === 'home') {
    return { name: 'home' }
  }
  return true
})

window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, () => {
  const currentRoute = router.currentRoute.value
  if (currentRoute.meta.requiresAuth) {
    void router.push({
      name: 'login',
      query: { redirect: currentRoute.fullPath, expired: '1' },
    })
  }
})

export default router
