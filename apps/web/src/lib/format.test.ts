import { describe, expect, it } from 'vitest'
import { formatMetricValue, formatTooltipNumber } from './format'
import type { MetricValue } from './api'

describe('formatMetricValue', () => {
  it('formats EUR amounts as currency', () => {
    const metric: MetricValue = { value: -613313, unit: 'EUR', description: '' }
    expect(formatMetricValue(metric)).toBe('-€613,313')
  })

  it('formats percentages with one decimal place', () => {
    const metric: MetricValue = { value: 77.4732, unit: '%', description: '' }
    expect(formatMetricValue(metric)).toBe('77.5%')
  })

  it('formats ratios with an x suffix', () => {
    const metric: MetricValue = { value: 4.3678, unit: 'x', description: '' }
    expect(formatMetricValue(metric)).toBe('4.37x')
  })

  it('formats counts as plain numbers', () => {
    const metric: MetricValue = { value: 36, unit: 'count', description: '' }
    expect(formatMetricValue(metric)).toBe('36')
  })
})

describe('formatTooltipNumber', () => {
  it('formats a number with thousands separators', () => {
    expect(formatTooltipNumber(1234567)).toBe('1,234,567')
  })

  it('falls back to a plain string for non-numeric values', () => {
    expect(formatTooltipNumber('n/a')).toBe('n/a')
  })
})
