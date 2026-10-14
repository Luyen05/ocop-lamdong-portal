// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import StatusPanel from '@/components/ui/StatusPanel.vue'

describe('StatusPanel', () => {
  it('trạng thái lỗi có nút Thử lại phát sự kiện retry', async () => {
    const wrapper = mount(StatusPanel, { props: { kind: 'error', message: 'Máy chủ không phản hồi.' } })
    expect(wrapper.get('[role="alert"]').text()).toContain('Chưa tải được dữ liệu')
    await wrapper.get('button').trigger('click')
    expect(wrapper.emitted('retry')).toHaveLength(1)
  })

  it('đang tải báo cho trình đọc màn hình và vẽ khung xương', () => {
    const wrapper = mount(StatusPanel, { props: { kind: 'loading', rows: 2 } })
    expect(wrapper.get('[role="status"]').text()).toContain('Đang tải')
    expect(wrapper.findAll('.skeleton-row')).toHaveLength(2)
  })

  it('trạng thái rỗng không có nút Thử lại', () => {
    const wrapper = mount(StatusPanel, { props: { kind: 'empty', title: 'Chưa có sản phẩm' } })
    expect(wrapper.text()).toContain('Chưa có sản phẩm')
    expect(wrapper.find('button').exists()).toBe(false)
  })
})
