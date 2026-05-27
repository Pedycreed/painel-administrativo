const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export type Time = 'scan' | 'agregador'

export interface User {
  id: number
  username: string
  email: string
  papel: 'admin'
  papel_display: string
  time: Time | null
  time_display: string
  avatar_url: string | null
  can_edit: boolean
  has_full_access: boolean
  can_manage_users: boolean
  is_superuser: boolean
  first_name: string
  last_name: string
}

export interface AuthResponse {
  user: User
  access: string
  refresh: string
}

export interface LoginCredentials {
  username: string
  password: string
}

export interface RegisterData {
  username: string
  email: string
  password: string
  password_confirm: string
  first_name?: string
  last_name?: string
}

// Armazena tokens
export function setTokens(access: string, refresh: string) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }
}

export function getAccessToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('access_token')
  }
  return null
}

export function getRefreshToken(): string | null {
  if (typeof window !== 'undefined') {
    return localStorage.getItem('refresh_token')
  }
  return null
}

export function clearTokens() {
  if (typeof window !== 'undefined') {
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
  }
}

export function setUser(user: User) {
  if (typeof window !== 'undefined') {
    localStorage.setItem('user', JSON.stringify(user))
  }
}

export function getStoredUser(): User | null {
  if (typeof window !== 'undefined') {
    const user = localStorage.getItem('user')
    return user ? JSON.parse(user) : null
  }
  return null
}

// Login
export async function login(credentials: LoginCredentials): Promise<AuthResponse> {
  const res = await fetch(`${API_URL}/auth/login/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(credentials),
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.error || 'Falha no login')
  }

  const data: AuthResponse = await res.json()
  setTokens(data.access, data.refresh)
  setUser(data.user)
  return data
}

// Registro
export async function register(data: RegisterData): Promise<AuthResponse> {
  const res = await fetch(`${API_URL}/auth/register/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  })

  if (!res.ok) {
    const error = await res.json()
    throw new Error(error.error || 'Falha no registro')
  }

  const response: AuthResponse = await res.json()
  setTokens(response.access, response.refresh)
  setUser(response.user)
  return response
}

// Logout
export async function logout() {
  const refresh = getRefreshToken()

  try {
    await fetch(`${API_URL}/auth/logout/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${getAccessToken()}`,
      },
      body: JSON.stringify({ refresh }),
    })
  } catch {
    // Ignora erros de logout
  }

  clearTokens()
}

// Fetch com autenticação
export async function authFetch<T>(url: string, options: RequestInit = {}): Promise<T> {
  const token = getAccessToken()

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
    ...(options.headers as Record<string, string> | undefined),
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  const res = await fetch(url, {
    ...options,
    headers,
  })

  if (res.status === 401) {
    // Token expirado, tenta refresh
    const newToken = await refreshToken()
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`
      const retryRes = await fetch(url, { ...options, headers })
      return retryRes.json()
    } else {
      clearTokens()
      window.location.href = '/login'
      throw new Error('Sessão expirada')
    }
  }

  if (!res.ok) {
    const error = await res.json().catch(() => ({ detail: 'Erro desconhecido' }))
    throw new Error(error.detail || error.error || 'Erro na requisição')
  }

  return res.json()
}

// Refresh token
export async function refreshToken(): Promise<string | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null

  try {
    const res = await fetch(`${API_URL}/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })

    if (!res.ok) return null

    const data = await res.json()
    setTokens(data.access, data.refresh || refresh)
    return data.access
  } catch {
    return null
  }
}

// Buscar usuário atual
export async function fetchCurrentUser(): Promise<User | null> {
  try {
    const user = await authFetch<User>(`${API_URL}/auth/me/`)
    setUser(user)
    return user
  } catch {
    return null
  }
}