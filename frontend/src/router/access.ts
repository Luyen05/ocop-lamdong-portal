import type { User, UserRole } from '@/types/auth'

export interface RouteAccessMeta {
  requiresAuth?: boolean
  guestOnly?: boolean
  roles?: readonly UserRole[]
}

export type RouteAccessDecision = 'allow' | 'login' | 'forbidden' | 'home'

const roleLandingPaths: Record<UserRole, string> = {
  admin: '/quan-tri',
  subject: '/tai-khoan',
  user: '/',
}

export function resolveRouteAccess(
  meta: RouteAccessMeta,
  user: User | null,
): RouteAccessDecision {
  if (meta.requiresAuth && !user) return 'login'
  if (meta.roles?.length && (!user || !meta.roles.includes(user.role))) return 'forbidden'
  if (meta.guestOnly && user) return 'home'
  return 'allow'
}

export function resolvePostLoginTarget(
  role: UserRole,
  requestedRedirect: unknown,
): string {
  if (
    typeof requestedRedirect === 'string'
    && requestedRedirect.startsWith('/')
    && !requestedRedirect.startsWith('//')
  ) {
    return requestedRedirect
  }

  return roleLandingPaths[role]
}
