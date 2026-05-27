"use client"

import { createContext, useContext, useState, useEffect, ReactNode, useCallback } from 'react'
import { useRouter, usePathname } from 'next/navigation'
import {
  User,
  login as authLogin,
  logout as authLogout,
  register as authRegister,
  getStoredUser,
  getAccessToken,
  fetchCurrentUser,
  clearTokens,
  setTokens,
  setUser as saveUser,
} from '@/lib/auth'

interface AuthContextType {
  user: User | null
  isLoading: boolean
  isAuthenticated: boolean
  login: (username: string, password: string) => Promise<void>
  register: (username: string, email: string, password: string, passwordConfirm: string) => Promise<void>
  logout: () => Promise<void>
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const router = useRouter()
  const pathname = usePathname()

  const isAuthenticated = !!user

  // Verifica se já existe sessão ao carregar
  useEffect(() => {
    async function loadUser() {
      const token = getAccessToken()

      if (!token) {
        setIsLoading(false)
        // Se não tem token e não está na página de login, redireciona
        if (pathname !== '/login') {
          router.push('/login')
        }
        return
      }

      const storedUser = getStoredUser()
      if (storedUser) {
        setUser(storedUser)
      }

      // Verifica se o token ainda é válido
      const currentUser = await fetchCurrentUser()
      if (currentUser) {
        setUser(currentUser)
      } else {
        setUser(null)
        clearTokens()
        if (pathname !== '/login') {
          router.push('/login')
        }
      }

      setIsLoading(false)
    }

    loadUser()
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const login = useCallback(async (username: string, password: string) => {
    const response = await authLogin({ username, password })
    setUser(response.user)
    // Force navigation after state is updated
    window.location.href = '/'
  }, [])

  const register = useCallback(async (
    username: string,
    email: string,
    password: string,
    passwordConfirm: string
  ) => {
    const response = await authRegister({
      username,
      email,
      password,
      password_confirm: passwordConfirm,
    })
    setUser(response.user)
    window.location.href = '/'
  }, [])

  const logout = useCallback(async () => {
    await authLogout()
    setUser(null)
    window.location.href = '/login'
  }, [])

  const refreshUser = useCallback(async () => {
    const currentUser = await fetchCurrentUser()
    if (currentUser) {
      setUser(currentUser)
    }
  }, [])

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}