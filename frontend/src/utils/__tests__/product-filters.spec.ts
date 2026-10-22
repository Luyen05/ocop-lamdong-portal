import { describe, expect, it } from 'vitest'

import {
  hasPriceConflict,
  normalizePrice,
  normalizeProductFilters,
} from '@/utils/product-filters'

describe('normalizeProductFilters', () => {
  it('chi nhan star 3/4/5 va sap xep hop le', () => {
    expect(normalizeProductFilters({ star: '4', sort: 'rating' })).toMatchObject({ star: '4', sort: 'rating' })
    for (const star of ['2', '6', '0', 'abc', '33', '', null, ['3']]) {
      expect(normalizeProductFilters({ star }).star).toBe('')
    }
    expect(normalizeProductFilters({ sort: 'bogus' }).sort).toBe('newest')
  })

  it('gia phai la so khong am', () => {
    expect(normalizePrice('1500')).toBe('1500')
    expect(normalizePrice(' 007 ')).toBe('7')
    for (const value of ['abc', '-5', '1e3', '', 'NaN', '12,5', undefined, null, '99999999999999999999']) {
      expect(normalizePrice(value)).toBe('')
    }
  })

  it('cat chuoi theo gioi han backend va bo kieu khong phai chuoi', () => {
    const result = normalizeProductFilters({ search: ` ${'a'.repeat(200)} `, district: 'd'.repeat(120), category: ['x'] })
    expect(result.search).toHaveLength(150)
    expect(result.district).toHaveLength(100)
    expect(result.category).toBe('')
  })

  it('phat hien min lon hon max', () => {
    expect(hasPriceConflict({ minPrice: '500', maxPrice: '100' })).toBe(true)
    expect(hasPriceConflict({ minPrice: '100', maxPrice: '100' })).toBe(false)
    expect(hasPriceConflict({ minPrice: '', maxPrice: '100' })).toBe(false)
  })
})
