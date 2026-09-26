// Màu và biểu tượng cho từng nhóm sản phẩm OCOP, dùng chung ở chip danh mục, thẻ sản phẩm và trang sản phẩm
// để cùng một nhóm luôn có cùng một màu. Bảng màu lấy từ ảnh thật (lá chè, cà phê, dã quỳ, cẩm tú cầu, trời).
export interface CategoryTheme {
  icon: string
  background: string
  foreground: string
}

const themes: Record<string, CategoryTheme> = {
  'nong-san-tuoi': { icon: 'cherry', background: 'var(--ocop-tone-berry-soft)', foreground: 'var(--ocop-tone-berry)' },
  'thuc-pham': { icon: 'food', background: 'var(--ocop-daquy-50)', foreground: 'var(--ocop-daquy-700)' },
  'do-uong': { icon: 'coffee', background: 'var(--ocop-secondary-100)', foreground: 'var(--ocop-secondary-700)' },
  'thao-duoc': { icon: 'leaf', background: 'var(--ocop-tone-leaf-soft)', foreground: 'var(--ocop-tone-leaf)' },
  'thu-cong-my-nghe': { icon: 'palette', background: 'var(--ocop-tone-clay-soft)', foreground: 'var(--ocop-tone-clay)' },
  'sinh-vat-canh': { icon: 'flower', background: 'var(--ocop-tone-hydrangea-soft)', foreground: 'var(--ocop-tone-hydrangea)' },
  'dich-vu-du-lich-cong-dong': { icon: 'compass', background: 'var(--ocop-tone-sky-soft)', foreground: 'var(--ocop-tone-sky)' },
}

const fallbackTheme: CategoryTheme = {
  icon: 'package',
  background: 'var(--ocop-mist-100)',
  foreground: 'var(--ocop-mist-700)',
}

export function categoryTheme(slug: string | null | undefined): CategoryTheme {
  return (slug && themes[slug]) || fallbackTheme
}
