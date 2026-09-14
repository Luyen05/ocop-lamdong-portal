// Du lieu minh hoa tam thoi cho cac module tourism va map chua duoc trien khai.

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
    icon: 'sprout',
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
    icon: 'store',
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
    icon: 'building',
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
