import axios from 'axios'

import { expireAccessToken, getAccessToken } from '@/services/token'

/**
 * Thời gian chờ riêng cho tải file lên/xuống (ảnh tối đa 5 MB, chứng nhận tối đa 10 MB):
 * mạng di động chậm cần lâu hơn mức 10 giây mặc định của các request thường.
 */
export const UPLOAD_TIMEOUT_MS = 120_000

const http = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000/api/v1',
  timeout: 10_000,
  headers: {
    Accept: 'application/json',
  },
})

http.interceptors.request.use((config) => {
  const token = getAccessToken()
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (response) => response,
  (error: unknown) => {
    if (axios.isAxiosError(error) && getAccessToken()) {
      const status = error.response?.status
      const code = (error.response?.data as { code?: string } | undefined)?.code
      if (status === 401) {
        expireAccessToken()
      } else if (status === 403 && code === 'ACCOUNT_INACTIVE') {
        // Quản trị viên vừa khóa tài khoản: kết thúc phiên ngay, không để người dùng ở lại trang cũ.
        expireAccessToken('locked')
      }
    }
    return Promise.reject(error)
  },
)

export default http
