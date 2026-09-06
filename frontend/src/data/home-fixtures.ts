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
