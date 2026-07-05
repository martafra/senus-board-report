import { getToken } from './token'

const BASE_URL = import.meta.env.VITE_API_URL

export class ApiError extends Error {
  status: number

  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const token = getToken()
  const headers = new Headers(options.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  if (options.body && !(options.body instanceof URLSearchParams) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  const response = await fetch(`${BASE_URL}${path}`, { ...options, headers })

  if (!response.ok) {
    let message = response.statusText
    try {
      const body = await response.json()
      message = body.detail ?? message
    } catch {
      // response body wasn't JSON, keep the status text
    }
    throw new ApiError(response.status, message)
  }

  return response.json() as Promise<T>
}

export function apiGet<T>(path: string): Promise<T> {
  return request<T>(path)
}

export function apiPost<T>(path: string): Promise<T> {
  return request<T>(path, { method: 'POST' })
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export function login(email: string, password: string): Promise<TokenResponse> {
  const body = new URLSearchParams({ username: email, password })
  return request<TokenResponse>('/auth/login', { method: 'POST', body })
}

export interface CurrentUser {
  email: string
  name: string
  role: string
}

export function fetchCurrentUser(): Promise<CurrentUser> {
  return apiGet<CurrentUser>('/auth/me')
}

// Mirrors app/schemas/metrics.py on the backend.
export interface MetricValue {
  value: number
  unit: 'EUR' | '%' | 'x' | 'count'
  description: string
}

export interface PeriodMetrics {
  period_label: string
  period_type: 'ANNUAL' | 'HALF_YEAR' | 'QUARTERLY' | 'MONTHLY'
  start_date: string
  end_date: string
  is_actual_reported: boolean
  metrics: Record<string, MetricValue>
}

export type MetricsSection =
  | 'growth'
  | 'profitability'
  | 'cash-liquidity'
  | 'solvency'
  | 'returns'

export function fetchMetrics(section: MetricsSection): Promise<PeriodMetrics[]> {
  return apiGet<PeriodMetrics[]>(`/metrics/${section}`)
}

// Mirrors app/schemas/insights.py on the backend.
export interface Insight {
  section_key: string
  content: string
  model: string
  generated_at: string
  prompt_version: string
}

export function fetchInsight(section: MetricsSection): Promise<Insight> {
  return apiGet<Insight>(`/insights/${section}`)
}

export function regenerateInsight(section: MetricsSection): Promise<Insight> {
  return apiPost<Insight>(`/insights/${section}/regenerate`)
}
