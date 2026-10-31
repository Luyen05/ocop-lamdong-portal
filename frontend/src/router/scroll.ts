import type { RouteLocationNormalized, RouterScrollBehavior } from 'vue-router'

import { scrollBehavior as motionBehavior } from '@/utils/motion'

/**
 * Quy tắc cuộn khi đổi route:
 * - Nút Back/Forward: khôi phục vị trí cũ.
 * - Có #neo: cuộn tới neo (mượt trừ khi giảm chuyển động).
 * - Trang bản đồ chỉ đổi query (chọn điểm, lọc): giữ nguyên vị trí cuộn để bản đồ không bị đẩy đi.
 * - Còn lại: lên đầu trang. Các trang khác (sản phẩm, tin tức…) vẫn lên đầu khi đổi bộ lọc.
 */
export const resolveScroll: RouterScrollBehavior = (
  to: RouteLocationNormalized,
  from: RouteLocationNormalized,
  savedPosition,
) => {
  if (savedPosition) return savedPosition
  if (to.hash) return { el: to.hash, behavior: motionBehavior() }
  if (to.name === 'map' && from.name === 'map' && to.path === from.path) return false
  return { top: 0 }
}
