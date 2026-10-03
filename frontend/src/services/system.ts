import http from '@/services/http'

/** Kiểm tra API và cơ sở dữ liệu còn phản hồi (GET /health/database, không cần đăng nhập). */
export async function checkApiHealth(): Promise<boolean> {
  try {
    await http.get('/health/database', { timeout: 5_000 })
    return true
  } catch {
    return false
  }
}
