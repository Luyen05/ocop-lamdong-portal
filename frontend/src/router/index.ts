import { createRouter, createWebHistory } from 'vue-router'

import { AUTH_SESSION_EXPIRED_EVENT } from '@/services/token'
import { authStore } from '@/stores/auth'
import { pageStatus } from '@/stores/page-status'
import HomeView from '@/views/HomeView.vue'
import { resolveRouteAccess } from '@/router/access'
import { documentTitleFor } from '@/router/titles'
import { scrollBehavior } from '@/utils/motion'
import { decideChunkRecovery, isChunkLoadError } from '@/utils/chunk-error'
import { applyPageSeo, ROUTE_DESCRIPTIONS } from '@/utils/seo'

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
      // Google/Facebook trả người dùng về đây (FRONTEND_BASE_URL/dang-nhap/mang-xa-hoi/<google|facebook>).
      path: '/dang-nhap/mang-xa-hoi/:provider(google|facebook)',
      name: 'social-login-callback',
      component: () => import('@/views/SocialLoginCallbackView.vue'),
      meta: { layout: 'auth' },
    },
    {
      path: '/tai-khoan',
      name: 'profile',
      component: () => import('@/views/ProfileView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/tai-khoan/danh-gia',
      name: 'my-reviews',
      component: () => import('@/views/MyReviewsView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/dang-ky-chu-the',
      name: 'subject-application',
      component: () => import('@/views/SubjectApplicationView.vue'),
      meta: { requiresAuth: true, roles: ['user', 'subject'] },
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
      path: '/san-pham/:slug/diem-trai-nghiem',
      name: 'product-experience',
      component: () => import('@/views/ProductExperienceView.vue'),
    },
    {
      path: '/diem-du-lich',
      name: 'locations',
      component: () => import('@/views/LocationsView.vue'),
    },
    {
      path: '/diem-du-lich/:slug',
      name: 'location-detail',
      component: () => import('@/views/LocationDetailView.vue'),
    },
    {
      path: '/ban-do',
      name: 'map',
      component: () => import('@/views/MapView.vue'),
    },
    {
      path: '/tin-tuc',
      name: 'news',
      component: () => import('@/views/NewsView.vue'),
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
          meta: { title: 'Tổng quan quản trị' },
        },
        {
          path: 'ho-so-chu-the',
          name: 'admin-subject-applications',
          component: () => import('@/views/admin/AdminSubjectApplicationsView.vue'),
          meta: { title: 'Hồ sơ chủ thể' },
        },
        {
          path: 'san-pham',
          name: 'admin-products',
          component: () => import('@/views/admin/AdminProductsView.vue'),
          meta: { title: 'Duyệt sản phẩm' },
        },
        {
          path: 'diem-du-lich',
          name: 'admin-locations',
          component: () => import('@/views/admin/AdminLocationsView.vue'),
          meta: { title: 'Duyệt điểm du lịch' },
        },
        {
          path: 'danh-gia',
          name: 'admin-reviews',
          component: () => import('@/views/admin/AdminReviewsView.vue'),
          meta: { title: 'Duyệt đánh giá' },
        },
        {
          path: 'nguoi-dung',
          name: 'admin-users',
          component: () => import('@/views/admin/AdminUsersView.vue'),
          meta: { title: 'Quản lý người dùng' },
        },
        {
          path: 'danh-muc',
          name: 'admin-categories',
          component: () => import('@/views/admin/AdminCategoriesView.vue'),
          meta: { title: 'Quản lý danh mục' },
        },
      ],
    },
    {
      path: '/chu-the',
      component: () => import('@/layouts/SubjectLayout.vue'),
      meta: { layout: 'subject', requiresAuth: true, roles: ['subject'] },
      children: [
        { path: '', redirect: '/chu-the/san-pham' },
        {
          path: 'ho-so',
          name: 'subject-profile',
          component: () => import('@/views/subject/SubjectProfileView.vue'),
          meta: { title: 'Hồ sơ chủ thể' },
        },
        {
          path: 'san-pham',
          name: 'subject-products',
          component: () => import('@/views/subject/SubjectProductsView.vue'),
          meta: { title: 'Sản phẩm của chủ thể' },
        },
        {
          path: 'san-pham/them',
          name: 'subject-product-create',
          component: () => import('@/views/subject/SubjectProductEditorView.vue'),
        },
        {
          path: 'san-pham/:id(\\d+)/chinh-sua',
          name: 'subject-product-edit',
          component: () => import('@/views/subject/SubjectProductEditorView.vue'),
        },
        {
          path: 'yeu-cau/:requestId(\\d+)/chinh-sua',
          name: 'subject-product-request-edit',
          component: () => import('@/views/subject/SubjectProductEditorView.vue'),
        },
        {
          path: 'diem-du-lich',
          name: 'subject-locations',
          component: () => import('@/views/subject/SubjectLocationsView.vue'),
          meta: { title: 'Điểm du lịch của tôi' },
        },
        {
          path: 'diem-du-lich/khai-bao',
          name: 'subject-location-create',
          component: () => import('@/views/subject/SubjectLocationEditorView.vue'),
          meta: { title: 'Khai báo điểm du lịch' },
        },
        {
          path: 'diem-du-lich/yeu-cau/:requestId(\\d+)',
          name: 'subject-location-request-edit',
          component: () => import('@/views/subject/SubjectLocationEditorView.vue'),
          meta: { title: 'Bổ sung yêu cầu cập nhật' },
        },
        {
          path: 'diem-du-lich/:id(\\d+)',
          name: 'subject-location-edit',
          component: () => import('@/views/subject/SubjectLocationEditorView.vue'),
          meta: { title: 'Hồ sơ điểm du lịch' },
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      name: 'not-found',
      component: () => import('@/views/NotFoundView.vue'),
    },
  ],
  // Quay lại trang trước thì giữ vị trí cuộn cũ; cuộn tới #neo thì mượt trừ khi người dùng giảm chuyển động.
  scrollBehavior: (to, _from, savedPosition) => {
    if (savedPosition) return savedPosition
    return to.hash ? { el: to.hash, behavior: scrollBehavior() } : { top: 0 }
  },
})

router.beforeEach(async (to) => {
  pageStatus.startNavigation()
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

// Trang không có nội dung cho tìm kiếm: cần đăng nhập, đăng nhập/đăng ký, lỗi.
const NOINDEX_ROUTES = new Set(['forbidden', 'not-found', 'social-login-callback'])

router.afterEach((to) => {
  pageStatus.finishNavigation()
  const name = typeof to.name === 'string' ? to.name : ''
  applyPageSeo({
    fullTitle: documentTitleFor(to.name, to.meta.title),
    description: ROUTE_DESCRIPTIONS[name],
    path: to.path,
    noindex: Boolean(to.meta.requiresAuth) || to.meta.layout === 'auth' || NOINDEX_ROUTES.has(name) || !name,
    // Trang chi tiết tự đặt lại thẻ SEO có tên cụ thể sau khi tải xong dữ liệu.
  })
})

// Không tải được mã của trang (mất mạng, hoặc vừa có bản mới nên tên tệp cũ không còn):
// có mạng thì tải lại đúng trang đích một lần; còn lại báo người dùng và cho thử lại.
router.onError((error, to) => {
  if (!isChunkLoadError(error)) {
    pageStatus.finishNavigation()
    console.error(error)
    return
  }
  if (decideChunkRecovery(pageStatus.online.value) === 'reload') {
    window.location.assign(to.fullPath)
    return
  }
  pageStatus.reportNavigationFailure(to.fullPath)
})

window.addEventListener(AUTH_SESSION_EXPIRED_EVENT, (event) => {
  const currentRoute = router.currentRoute.value
  const locked = (event as CustomEvent<string>).detail === 'locked'
  if (locked) {
    void router.push({ name: 'login', query: { locked: '1' } })
  } else if (currentRoute.meta.requiresAuth) {
    void router.push({
      name: 'login',
      query: { redirect: currentRoute.fullPath, expired: '1' },
    })
  }
})

export default router
