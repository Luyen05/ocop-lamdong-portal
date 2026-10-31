import { describe, expect, it } from 'vitest'

import { useConfirmDialog } from '@/composables/useConfirmDialog'

describe('useConfirmDialog', () => {
  it('ask mo hop thoai voi noi dung va resolve true khi chap nhan', async () => {
    const confirm = useConfirmDialog()
    const answer = confirm.ask({ title: 'Xóa?', message: 'Chắc chắn?', confirmLabel: 'Xóa', tone: 'danger' })
    expect(confirm.props).toMatchObject({ open: true, title: 'Xóa?', message: 'Chắc chắn?', confirmLabel: 'Xóa', tone: 'danger' })
    confirm.accept()
    await expect(answer).resolves.toBe(true)
    expect(confirm.props.open).toBe(false)
  })

  it('dismiss resolve false va dung gia tri mac dinh', async () => {
    const confirm = useConfirmDialog()
    const answer = confirm.ask({ title: 'Hủy?' })
    expect(confirm.props).toMatchObject({ confirmLabel: 'Xác nhận', cancelLabel: 'Hủy', tone: 'primary', message: '' })
    confirm.dismiss()
    await expect(answer).resolves.toBe(false)
  })

  it('cau hoi moi huy cau hoi dang do', async () => {
    const confirm = useConfirmDialog()
    const first = confirm.ask({ title: 'A' })
    const second = confirm.ask({ title: 'B' })
    await expect(first).resolves.toBe(false)
    expect(confirm.props.title).toBe('B')
    confirm.accept()
    await expect(second).resolves.toBe(true)
  })
})
