import axios from 'axios'

interface ApiErrorBody {
  code?: string
  message?: string
  details?: unknown
}

export function getApiErrorMessage(error: unknown, fallback: string): string {
  if (!axios.isAxiosError<ApiErrorBody>(error)) {
    return fallback
  }

  if (!error.response) {
    return 'Không thể kết nối đến máy chủ. Vui lòng thử lại.'
  }

  return error.response.data?.message || fallback
}
