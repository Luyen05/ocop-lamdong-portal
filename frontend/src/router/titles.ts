/**
 * Tiêu đề thẻ trình duyệt theo từng trang. Trang chi tiết (sản phẩm, điểm du lịch…) tự đặt lại
 * tiêu đề có tên cụ thể sau khi tải xong dữ liệu.
 */
export const SITE_NAME = 'OCOP Lâm Đồng'

const ROUTE_TITLES: Record<string, string> = {
  login: 'Đăng nhập',
  register: 'Đăng ký tài khoản',
  'social-login-callback': 'Đăng nhập bằng Google/Facebook',
  profile: 'Tài khoản của tôi',
  'subject-application': 'Đăng ký chủ thể OCOP',
  products: 'Sản phẩm OCOP',
  'product-detail': 'Chi tiết sản phẩm',
  'product-experience': 'Điểm mua & trải nghiệm',
  locations: 'Điểm du lịch nông nghiệp',
  'location-detail': 'Điểm du lịch',
  map: 'Bản đồ số du lịch nông nghiệp',
  news: 'Tin tức OCOP',
  forbidden: 'Không có quyền truy cập',
  'not-found': 'Không tìm thấy trang',
  'subject-product-create': 'Thêm sản phẩm',
  'subject-product-edit': 'Sửa sản phẩm',
  'subject-product-request-edit': 'Sửa yêu cầu cập nhật sản phẩm',
}

export function documentTitleFor(routeName: unknown, metaTitle?: string): string {
  if (routeName === 'home') return `${SITE_NAME} | Nông sản OCOP và du lịch nông nghiệp`
  const pageTitle = (typeof routeName === 'string' && ROUTE_TITLES[routeName]) || metaTitle
  return pageTitle ? `${pageTitle} | ${SITE_NAME}` : SITE_NAME
}
