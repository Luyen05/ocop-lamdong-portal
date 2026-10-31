// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import PageSkeleton from '../PageSkeleton.vue'

describe('PageSkeleton', () => {
  it('hiển thị khung xương trang và báo trạng thái đang tải', () => {
    const wrapper = mount(PageSkeleton)
    expect(wrapper.find('[data-testid="page-skeleton"]').exists()).toBe(true)
    expect(wrapper.text()).toContain('Đang tải')
  })
})
