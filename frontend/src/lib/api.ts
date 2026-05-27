const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

// Traduções de mensagens comuns do Django/DRF pro PT-BR
const ERROR_TRANSLATIONS: Record<string, string> = {
  "This password is too common.": "Senha muito comum. Escolha uma mais difícil.",
  "This password is too short. It must contain at least 8 characters.": "Senha muito curta (mínimo 8 caracteres).",
  "This password is entirely numeric.": "Senha não pode ser só números.",
  "The password is too similar to the username.": "Senha muito parecida com o username.",
  "A user with that username already exists.": "Já existe um usuário com esse username.",
  "user with this email address already exists.": "Já existe um usuário com esse email.",
  "Enter a valid email address.": "Email inválido.",
  "This field may not be blank.": "Campo obrigatório.",
  "This field is required.": "Campo obrigatório.",
}

function translate(msg: string): string {
  return ERROR_TRANSLATIONS[msg] || msg
}

/**
 * Formata erro de resposta da API. Suporta:
 * - { detail: "..." } → mensagem genérica DRF
 * - { error: "..." } → mensagem custom das views
 * - { campo: ["msg1", "msg2"], outroCampo: [...] } → erros de validação por campo
 * - { non_field_errors: [...] } → erros globais do serializer
 */
export function formatApiError(data: unknown, status: number): string {
  if (!data || typeof data !== "object") return `Erro ${status}`

  const obj = data as Record<string, unknown>

  if (typeof obj.detail === "string") return translate(obj.detail)
  if (typeof obj.error === "string") return translate(obj.error)

  // Erros de validação por campo
  const fieldErrors: string[] = []
  for (const [field, value] of Object.entries(obj)) {
    if (field === "detail" || field === "error") continue
    const msgs = Array.isArray(value) ? value : [value]
    for (const m of msgs) {
      if (typeof m === "string") {
        const translated = translate(m)
        if (field === "non_field_errors") {
          fieldErrors.push(translated)
        } else {
          fieldErrors.push(`${field}: ${translated}`)
        }
      }
    }
  }
  if (fieldErrors.length > 0) return fieldErrors.join(" | ")
  return `Erro ${status}`
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

export async function refreshAccessToken(): Promise<string | null> {
  const refresh = getRefreshToken()
  if (!refresh) return null

  try {
    const res = await fetch(`${API_URL.replace('/api', '')}/api/token/refresh/`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh }),
    })

    if (!res.ok) return null

    const data = await res.json()
    if (typeof window !== 'undefined') {
      localStorage.setItem('access_token', data.access)
      if (data.refresh) {
        localStorage.setItem('refresh_token', data.refresh)
      }
    }
    return data.access
  } catch {
    return null
  }
}

export async function apiFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`
  const token = getAccessToken()

  const headers: HeadersInit = {
    'Content-Type': 'application/json',
    ...options.headers,
  }

  if (token) {
    headers['Authorization'] = `Bearer ${token}`
  }

  let res = await fetch(url, {
    ...options,
    headers,
  })

  // Token expirado - tenta refresh
  if (res.status === 401) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`
      res = await fetch(url, {
        ...options,
        headers,
      })
    } else {
      // Refresh falhou - limpa tokens e redireciona
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      throw new Error('Sessão expirada')
    }
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(formatApiError(errorData, res.status))
  }

  // Delete pode retornar vazio
  if (res.status === 204) {
    return {} as T
  }

  return res.json()
}

// Funções de conveniência
export async function apiGet<T>(endpoint: string): Promise<T> {
  return apiFetch<T>(endpoint)
}

export async function apiPost<T>(endpoint: string, data: unknown): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'POST',
    body: JSON.stringify(data),
  })
}

export async function apiPut<T>(endpoint: string, data: unknown): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'PUT',
    body: JSON.stringify(data),
  })
}

export async function apiPatch<T>(endpoint: string, data: unknown): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'PATCH',
    body: JSON.stringify(data),
  })
}

export async function apiDelete<T>(endpoint: string): Promise<T> {
  return apiFetch<T>(endpoint, {
    method: 'DELETE',
  })
}

/**
 * POST multipart/form-data. Diferente do apiPost, NÃO seta Content-Type
 * (o browser precisa setar com boundary). Mantém o Authorization JWT.
 */
export async function apiPostForm<T>(endpoint: string, formData: FormData): Promise<T> {
  const url = endpoint.startsWith('http') ? endpoint : `${API_URL}${endpoint}`
  const token = getAccessToken()

  const headers: HeadersInit = {}
  if (token) headers['Authorization'] = `Bearer ${token}`

  let res = await fetch(url, { method: 'POST', headers, body: formData })

  if (res.status === 401) {
    const newToken = await refreshAccessToken()
    if (newToken) {
      headers['Authorization'] = `Bearer ${newToken}`
      res = await fetch(url, { method: 'POST', headers, body: formData })
    } else {
      if (typeof window !== 'undefined') {
        localStorage.removeItem('access_token')
        localStorage.removeItem('refresh_token')
        localStorage.removeItem('user')
        window.location.href = '/login'
      }
      throw new Error('Sessão expirada')
    }
  }

  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}))
    throw new Error(formatApiError(errorData, res.status))
  }

  if (res.status === 204) return {} as T
  return res.json()
}