import 'vue-router'

import type { UserRole } from '@/types/auth'

declare module 'vue-router' {
  interface RouteMeta {
    layout?: 'auth' | 'admin' | 'subject'
    title?: string
    requiresAuth?: boolean
    guestOnly?: boolean
    roles?: readonly UserRole[]
  }
}

export {}
