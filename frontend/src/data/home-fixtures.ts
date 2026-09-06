// Du lieu minh hoa tam thoi cho cac module backend chua duoc trien khai.
// Khi API tourism, map va news san sang, thay cac mang nay bang service tuong ung.

export interface TourismFixture {
  id: string
  icon: string
  type: string
  openingHours: string
  district: string
  rating: number
  name: string
  description: string
  experiences: string[]
  theme: 'tea' | 'strawberry' | 'milk'
}

export const tourismFixtures: TourismFixture[] = [
  {
    id: 'cau-dat-farm',
    icon: '🏡',
    type: 'Đồi chè & Cà phê',
    openingHours: '06:00 - 17:30 Hàng ngày',
    district: 'TP. Đà Lạt',
    rating: 4.9,
    name: 'Đồi Chè Cầu Đất & Cầu Đất Farm',
    description:
      'Đồi chè gần 100 năm tuổi với hơn 220 ha sắc xanh, nơi du khách có thể săn mây và tìm hiểu quy trình chế biến trà OCOP.',
    experiences: ['Săn mây bình minh', 'Tham quan xưởng chè cổ', 'Trải nghiệm hái chè OCOP'],
    theme: 'tea',
  },
  {
    id: 'biofresh',
    icon: '🍓',
    type: 'Trang trại dâu tây',
    openingHours: '07:30 - 17:00 Hàng ngày',
    district: 'TP. Đà Lạt',
    rating: 4.8,
    name: 'Trang Trại Dâu Tây Biofresh & Vườn Hoa Sinh Thái',
    description:
      'Trang trại dâu tây Pháp - New Zealand ứng dụng công nghệ thủy canh tại khu vực Hồ Tuyền Lâm.',
    experiences: ['Tự tay hái dâu tây', 'Tìm hiểu kỹ thuật trồng sạch', 'Thưởng thức sản phẩm tại vườn'],
    theme: 'strawberry',
  },
  {
    id: 'dalat-milk-farm',
    icon: '🐄',
    type: 'Nông trại bò sữa',
    openingHours: '07:30 - 17:00 Hàng ngày',
    district: 'Huyện Đức Trọng',
    rating: 4.9,
    name: 'Nông Trại Bò Sữa Dalat Milk Farm',
    description:
      'Không gian đồng cỏ, hồ nước và trang trại bò sữa mang đến trải nghiệm nông nghiệp đặc trưng của cao nguyên.',
    experiences: ['Tham quan đồng cỏ', 'Tìm hiểu quy trình sữa', 'Chụp ảnh cảnh quan nông trại'],
    theme: 'milk',
  },
]

export interface MapMarkerFixture {
  id: string
  label: string
  type: 'ocop-5' | 'ocop-4' | 'tourism'
  x: number
  y: number
}

export const mapMarkerFixtures: MapMarkerFixture[] = [
  { id: 'da-lat', label: 'OCOP Đà Lạt', type: 'ocop-5', x: 47, y: 34 },
  { id: 'cau-dat', label: 'Cầu Đất Farm', type: 'tourism', x: 68, y: 28 },
  { id: 'duc-trong', label: 'Đức Trọng', type: 'ocop-4', x: 52, y: 62 },
  { id: 'don-duong', label: 'Đơn Dương', type: 'ocop-4', x: 72, y: 54 },
  { id: 'bao-loc', label: 'Bảo Lộc', type: 'ocop-5', x: 25, y: 76 },
  { id: 'lac-duong', label: 'Lạc Dương', type: 'tourism', x: 43, y: 17 },
]

export interface NewsFixture {
  id: string
  category: string
  date: string
  title: string
  summary: string
  theme: 'policy' | 'tourism'
}

export const newsFixtures: NewsFixture[] = [
  {
    id: 'cong-nhan-san-pham-ocop-2024',
    category: 'Tin OCOP',
    date: '15/03/2024',
    title: 'Lâm Đồng công nhận thêm 45 sản phẩm OCOP đạt 4 sao và 5 sao năm 2024',
    summary:
      'UBND tỉnh Lâm Đồng tổ chức lễ trao giấy chứng nhận cho các sản phẩm thuộc lĩnh vực nông sản, thực phẩm chế biến và dịch vụ du lịch nông thôn.',
    theme: 'policy',
  },
  {
    id: 'du-lich-nong-nghiep-ben-vung',
    category: 'Du lịch nông nghiệp',
    date: '10/03/2024',
    title: 'Phát triển mô hình Du lịch Nông nghiệp bền vững gắn với trải nghiệm làng nghề OCOP',
    summary:
      'Mô hình kết hợp hái nông sản tại vườn và thưởng thức sản phẩm OCOP tại chỗ đang trở thành xu hướng thu hút du khách đến Lâm Đồng.',
    theme: 'tourism',
  },
]
