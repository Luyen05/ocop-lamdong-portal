// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, h, withDirectives } from 'vue'

import { vReveal } from '../reveal'

type ObserverCallback = (entries: Array<{ isIntersecting: boolean; target: Element }>) => void

function installObserver() {
  const observed: Element[] = []
  let callback: ObserverCallback = () => {}
  const disconnect = vi.fn()
  class FakeObserver {
    constructor(cb: ObserverCallback) {
      callback = cb
    }
    observe(element: Element) {
      observed.push(element)
    }
    unobserve() {}
    disconnect = disconnect
  }
  vi.stubGlobal('IntersectionObserver', FakeObserver)
  return { observed, disconnect, fire: (el: Element) => callback([{ isIntersecting: true, target: el }]) }
}

function component(modifiers: Record<string, boolean> = {}) {
  return defineComponent({
    render() {
      return withDirectives(
        h('div', { class: 'wrap' }, [h('p', { class: 'a' }, 'A'), h('p', { class: 'b' }, 'B'), h('p', { class: 'c' }, 'C')]),
        [[vReveal, undefined, '', modifiers]],
      )
    },
  })
}

afterEach(() => {
  vi.unstubAllGlobals()
})

describe('v-reveal', () => {
  it('đánh dấu phần tử và thêm reveal-in khi cuộn tới', () => {
    const observer = installObserver()
    const wrapper = mount(component())
    const el = wrapper.element as HTMLElement
    expect(el.classList.contains('reveal')).toBe(true)
    expect(el.classList.contains('reveal-in')).toBe(false)
    observer.fire(el)
    expect(el.classList.contains('reveal-in')).toBe(true)
  })

  it('stagger: mỗi con trực tiếp có độ trễ tăng dần', () => {
    installObserver()
    const wrapper = mount(component({ stagger: true }))
    const children = Array.from(wrapper.element.children) as HTMLElement[]
    expect(children.every((child) => child.classList.contains('reveal'))).toBe(true)
    expect(children.map((child) => child.style.getPropertyValue('--reveal-delay'))).toEqual(['0ms', '70ms', '140ms'])
  })

  it('không làm gì khi thiếu IntersectionObserver (nội dung vẫn hiện)', () => {
    vi.stubGlobal('IntersectionObserver', undefined)
    const wrapper = mount(component())
    expect((wrapper.element as HTMLElement).classList.contains('reveal')).toBe(false)
  })

  it('không làm gì khi người dùng chọn giảm chuyển động', () => {
    installObserver()
    vi.stubGlobal('matchMedia', () => ({ matches: true }))
    const wrapper = mount(component())
    expect((wrapper.element as HTMLElement).classList.contains('reveal')).toBe(false)
  })

  it('ngắt observer khi gỡ phần tử', () => {
    const observer = installObserver()
    const wrapper = mount(component())
    wrapper.unmount()
    expect(observer.disconnect).toHaveBeenCalled()
  })
})
