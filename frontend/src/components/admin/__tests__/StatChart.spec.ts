// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

const chartInstances: { config: { type: string; data: { labels: string[]; datasets: { data: number[] }[] }; options: { indexAxis: string } }; destroy: ReturnType<typeof vi.fn> }[] = []

vi.mock('chart.js', () => {
  class Chart {
    static register = vi.fn()
    config: unknown
    destroy = vi.fn()
    constructor(_canvas: unknown, config: unknown) {
      this.config = config
      chartInstances.push(this as never)
    }
  }
  return { Chart, BarController: {}, BarElement: {}, CategoryScale: {}, LinearScale: {}, Tooltip: {} }
})

import StatChart from '@/components/admin/StatChart.vue'

const items = [
  { label: '3 sao', value: 46, color: 'var(--ocop-daquy-600)' },
  { label: '4 sao', value: 26, color: 'var(--ocop-daquy-700)' },
]

describe('StatChart', () => {
  beforeEach(() => {
    chartInstances.length = 0
  })

  it('vẽ biểu đồ cột với nhãn và số liệu, có mô tả cho trình đọc màn hình', () => {
    const wrapper = mount(StatChart, { props: { title: 'Hạng sao', items, summary: '3 sao: 46; 4 sao: 26' } })

    expect(chartInstances).toHaveLength(1)
    const config = chartInstances[0]!.config
    expect(config.type).toBe('bar')
    expect(config.options.indexAxis).toBe('x')
    expect(config.data.labels).toEqual(['3 sao', '4 sao'])
    expect(config.data.datasets[0]!.data).toEqual([46, 26])
    expect(wrapper.get('canvas').attributes('aria-label')).toBe('3 sao: 46; 4 sao: 26')
  })

  it('thanh ngang dùng trục y làm trục nhãn', () => {
    mount(StatChart, { props: { title: 'Nhóm', kind: 'bar', items, summary: 'x' } })

    expect(chartInstances[0]!.config.options.indexAxis).toBe('y')
  })

  it('thanh chia tỉ lệ tạo mỗi nhóm một dataset', () => {
    mount(StatChart, { props: { title: 'Trạng thái', kind: 'stacked', items, summary: 'x' } })

    expect(chartInstances[0]!.config.data.datasets.map((dataset) => dataset.data)).toEqual([[46], [26]])
  })

  it('nút Bảng số liệu chuyển sang bảng có đủ số liệu', async () => {
    const wrapper = mount(StatChart, { props: { title: 'Hạng sao', items, summary: 'x' } })
    const toggle = wrapper.get('button')

    expect(toggle.attributes('aria-pressed')).toBe('false')
    await toggle.trigger('click')

    expect(toggle.attributes('aria-pressed')).toBe('true')
    expect(toggle.text()).toContain('Xem biểu đồ')
    const rows = wrapper.findAll('tbody tr').map((row) => row.text())
    expect(rows).toEqual(['3 sao46', '4 sao26'])
  })

  it('huỷ biểu đồ khi gỡ component', () => {
    const wrapper = mount(StatChart, { props: { title: 'Hạng sao', items, summary: 'x' } })
    wrapper.unmount()

    expect(chartInstances[0]!.destroy).toHaveBeenCalled()
  })
})
