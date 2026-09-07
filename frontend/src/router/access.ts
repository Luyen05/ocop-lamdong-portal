import type { User, UserRole } from '@/types/auth'

export interface RouteAccessMeta {
  requiresAuth?: boolean
  guestOnly?: boolean
  roles?: readonly UserRole[]
}

export type RouteAccessDecision = 'allow' | 'login' | 'forbidden' | 'home'

export function resolveRouteAccess(
  meta: RouteAccessMeta,
  user: User | null,
): RouteAccessDecision {
  if (meta.requiresAuth && !user) return 'login'
  if (meta.roles?.length && (!user || !meta.roles.includes(user.role))) return 'forbidden'
  if (meta.guestOnly && user) return 'home'
  return 'allow'
}
