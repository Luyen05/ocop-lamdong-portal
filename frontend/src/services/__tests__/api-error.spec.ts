import { AxiosError, type AxiosResponse } from 'axios'
import { describe, expect, it } from 'vitest'

import { getApiErrorMessage, getApiFieldErrors, translateValidationMessage } from '@/services/api-error'

function apiError(status: number, data: unknown): AxiosError {
  const error = new AxiosError('Request failed')
  error.response = { status, data } as AxiosResponse
  return error
}

function validation(details: unknown[]): AxiosError {
  return apiError(422, { code: 'VALIDATION_ERROR', message: 'Dữ liệu đầu vào không hợp lệ.', details })
}

describe('getApiErrorMessage', () => {
  it('giu hanh vi cu: tra message cua API, fallback va loi mang', () => {
    expect(getApiErrorMessage(apiError(409, { code: 'X', message: 'Đã tồn tại.' }), 'Lỗi')).toBe('Đã tồn tại.')
    expect(getApiErrorMessage(apiError(500, {}), 'Lỗi chung')).toBe('Lỗi chung')
    expect(getApiErrorMessage(new Error('x'), 'Lỗi chung')).toBe('Lỗi chung')
    expect(getApiErrorMessage(new AxiosError('Network Error'), 'Lỗi chung')).toBe(
      'Không thể kết nối đến máy chủ. Vui lòng thử lại.',
    )
  })

  it('co fallback mac dinh khi khong truyen', () => {
    expect(getApiErrorMessage(new Error('x'))).toBe('Có lỗi xảy ra. Vui lòng thử lại.')
  })

  it('dich loi qua dai thanh cau co ten truong', () => {
    const error = validation([
      { loc: ['body', 'name'], msg: 'String should have at most 255 characters', type: 'string_too_long' },
    ])
    expect(getApiErrorMessage(error, 'Lỗi')).toBe('Tên sản phẩm tối đa 255 ký tự.')
  })

  it('dich tối thiểu, bắt buộc, khoảng giá trị', () => {
    expect(
      getApiErrorMessage(validation([{ loc: ['body', 'description'], msg: 'String should have at least 10 characters', type: 'string_too_short' }])),
    ).toBe('Mô tả tối thiểu 10 ký tự.')
    expect(
      getApiErrorMessage(validation([{ loc: ['body', 'email'], msg: 'Field required', type: 'missing' }])),
    ).toBe('Email là bắt buộc.')
    expect(
      getApiErrorMessage(validation([{ loc: ['body', 'price'], msg: 'Input should be greater than or equal to 0', type: 'greater_than_equal' }])),
    ).toBe('Giá phải từ 0 trở lên.')
    expect(
      getApiErrorMessage(validation([{ loc: ['body', 'star'], msg: 'Input should be less than or equal to 5', type: 'less_than_equal' }])),
    ).toBe('Hạng sao không được vượt quá 5.')
    expect(
      getApiErrorMessage(validation([{ loc: ['body', 'price'], msg: 'Input should be greater than 0', type: 'greater_than' }])),
    ).toBe('Giá phải lớn hơn 0.')
  })

  it('gop nhieu loi va rut gon khi qua dai', () => {
    const error = validation([
      { loc: ['body', 'name'], msg: 'Field required', type: 'missing' },
      { loc: ['body', 'price'], msg: 'Input should be greater than or equal to 0', type: 'greater_than_equal' },
    ])
    expect(getApiErrorMessage(error)).toBe('Cần sửa 2 mục: Tên sản phẩm là bắt buộc. Giá phải từ 0 trở lên.')

    const many = validation(
      ['name', 'price', 'unit', 'description', 'story', 'cert_code'].map((field) => ({
        loc: ['body', field],
        msg: 'Field required',
        type: 'missing',
      })),
    )
    const message = getApiErrorMessage(many)
    expect(message).toContain('Cần sửa 6 mục:')
    expect(message).toContain('Và 2 mục khác.')
  })

  it('truong la dung ten truong tho trong ngoac; loi mau tuy bien giu nguyen', () => {
    expect(
      getApiErrorMessage(validation([{ loc: ['body', 'foo_bar'], msg: 'Field required', type: 'missing' }])),
    ).toBe('(foo_bar) là bắt buộc.')
    expect(
      getApiErrorMessage(
        validation([{ loc: ['body'], msg: 'Value error, Ngày hết hạn phải sau ngày cấp chứng nhận.', type: 'value_error' }]),
      ),
    ).toBe('Ngày hết hạn phải sau ngày cấp chứng nhận.')
  })

  it('mang anh: ghi so thu tu anh', () => {
    const error = validation([
      { loc: ['body', 'images', 1, 'image_url'], msg: 'String should have at most 500 characters', type: 'string_too_long' },
    ])
    expect(getApiErrorMessage(error)).toBe('Ảnh số 2: đường dẫn ảnh tối đa 500 ký tự.')
  })

  it('details rong thi dung message cua API', () => {
    expect(getApiErrorMessage(validation([]), 'Lỗi')).toBe('Dữ liệu đầu vào không hợp lệ.')
  })
})

describe('getApiFieldErrors', () => {
  it('tra map truong -> thong diep, loi dau tien moi truong, _form cho loi chung', () => {
    const error = validation([
      { loc: ['body', 'name'], msg: 'String should have at most 255 characters', type: 'string_too_long' },
      { loc: ['body', 'name'], msg: 'Field required', type: 'missing' },
      { loc: ['body'], msg: 'Value error, Sản phẩm phải có đúng một ảnh chính.', type: 'value_error' },
    ])
    expect(getApiFieldErrors(error)).toEqual({
      name: 'Tên sản phẩm tối đa 255 ký tự.',
      _form: 'Sản phẩm phải có đúng một ảnh chính.',
    })
  })

  it('khong phai loi kiem tra du lieu thi tra object rong', () => {
    expect(getApiFieldErrors(new Error('x'))).toEqual({})
    expect(getApiFieldErrors(apiError(500, { message: 'x' }))).toEqual({})
    expect(getApiFieldErrors(new AxiosError('Network'))).toEqual({})
  })
})

describe('translateValidationMessage', () => {
  it('dich so it 1 ky tu va loai khac', () => {
    expect(translateValidationMessage({ msg: 'String should have at least 1 character' })).toBe('tối thiểu 1 ký tự')
    expect(translateValidationMessage({ msg: 'Input should be a valid integer, unable to parse string as an integer' })).toBe('chưa phải số hợp lệ')
    expect(translateValidationMessage({ msg: 'Something unknown' })).toBe('chưa hợp lệ')
  })
})
