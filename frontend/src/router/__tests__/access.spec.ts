import { describe, expect, it } from 'vitest'

import { resolveRouteAccess } from '@/router/access'
import type { User, UserRole } from '@/types/auth'

function createUser(role: UserRole): User {
  return {
    id: 1,
    email: `${role}@example.com`,
    full_name: `Tai khoan ${role}`,
    phone: null,
    avatar_url: null,
    is_active: true,
    role,
    created_at: '2026-09-07T00:00:00Z',
    updated_at: '2026-09-07T00:00:00Z',
  }
}

describe('resolveRouteAccess', () => {
  it('chuyen khach chua dang nhap den trang dang nhap', () => {
    expect(resolveRouteAccess({ requiresAuth: true }, null)).toBe('login')
  })

  it('chan nguoi dung thuong khoi khu vuc quan tri', () => {
    expect(
      resolveRouteAccess(
        { requiresAuth: true, roles: ['admin'] },
        createUser('user'),
      ),
    ).toBe('forbidden')
  })

  it('cho phep admin truy cap khu vuc quan tri', () => {
    expect(
      resolveRouteAccess(
        { requiresAuth: true, roles: ['admin'] },
        createUser('admin'),
      ),
    ).toBe('allow')
  })

  it('dua tai khoan da dang nhap ra khoi trang chi danh cho khach', () => {
    expect(resolveRouteAccess({ guestOnly: true }, createUser('subject'))).toBe('home')
  })
})
