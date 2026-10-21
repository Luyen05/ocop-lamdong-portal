export type PasswordTone = 'muted' | 'danger' | 'warning' | 'success'

export interface PasswordStrength {
  label: string
  tone: PasswordTone
}

/** Điểm 0–4: đủ 8 ký tự, có chữ hoa và chữ thường, có số, có ký tự đặc biệt. */
export function getPasswordScore(password: string): number {
  let score = 0
  if (password.length >= 8) score += 1
  if (/[a-z]/.test(password) && /[A-Z]/.test(password)) score += 1
  if (/\d/.test(password)) score += 1
  if (/[^A-Za-z0-9]/.test(password)) score += 1
  return score
}

export function getPasswordStrength(password: string): PasswordStrength {
  if (!password) return { label: 'Chưa nhập', tone: 'muted' }
  const score = getPasswordScore(password)
  if (score <= 1) return { label: 'Yếu', tone: 'danger' }
  if (score <= 2) return { label: 'Trung bình', tone: 'warning' }
  return { label: 'Tốt', tone: 'success' }
}

export const PASSWORD_MIN_LENGTH = 8
export const PASSWORD_MAX_LENGTH = 128
