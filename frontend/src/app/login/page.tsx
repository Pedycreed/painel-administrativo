"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"

export default function LoginPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [email, setEmail] = useState("")
  const [passwordConfirm, setPasswordConfirm] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      if (isLogin) {
        const res = await fetch(`${API_URL}/auth/login/`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ username, password }),
        })

        if (!res.ok) {
          const data = await res.json()
          throw new Error(data.error || "Falha no login")
        }

        const data = await res.json()
        localStorage.setItem("access_token", data.access)
        localStorage.setItem("refresh_token", data.refresh)
        localStorage.setItem("user", JSON.stringify(data.user))

        // Hard redirect para garantir que carrega o novo estado
        window.location.href = "/"
        return
      }

      // Registro
      if (password !== passwordConfirm) {
        throw new Error("As senhas não coincidem")
      }

      const res = await fetch(`${API_URL}/auth/register/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          username,
          email,
          password,
          password_confirm: passwordConfirm,
        }),
      })

      if (!res.ok) {
        const data = await res.json()
        throw new Error(data.error || data.username?.[0] || "Falha no registro")
      }

      const data = await res.json()
      localStorage.setItem("access_token", data.access)
      localStorage.setItem("refresh_token", data.refresh)
      localStorage.setItem("user", JSON.stringify(data.user))

      window.location.href = "/"
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro desconhecido")
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-[oklch(0.06_0_0)] flex items-center justify-center px-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center gap-2 mb-8">
          <div className="w-10 h-10 bg-primary rounded-lg flex items-center justify-center">
            <span className="text-primary-foreground font-bold text-lg">M</span>
          </div>
          <span className="text-foreground font-semibold text-2xl">MangáPanel</span>
        </div>

        {/* Card */}
        <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg p-6">
          <h1 className="text-xl font-semibold text-foreground mb-1">
            {isLogin ? "Entrar" : "Criar conta"}
          </h1>
          <p className="text-[oklch(0.55_0_0)] text-sm mb-6">
            {isLogin
              ? "Digite suas credenciais para acessar o painel"
              : "Preencha os dados para criar sua conta"}
          </p>

          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            <div className="flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Usuário</label>
              <Input
                className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
                placeholder="Usuário"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                autoFocus
              />
            </div>

            {!isLogin && (
              <div className="flex flex-col gap-1">
                <label className="text-[oklch(0.55_0_0)] text-sm">Email</label>
                <Input
                  className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
                  placeholder="email@exemplo.com"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            )}

            <div className="flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Senha</label>
              <Input
                className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
                placeholder="••••••••"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            {!isLogin && (
              <div className="flex flex-col gap-1">
                <label className="text-[oklch(0.55_0_0)] text-sm">Confirmar senha</label>
                <Input
                  className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
                  placeholder="••••••••"
                  type="password"
                  value={passwordConfirm}
                  onChange={(e) => setPasswordConfirm(e.target.value)}
                  required
                />
              </div>
            )}

            {error && (
              <p className="text-red-400 text-sm">{error}</p>
            )}

            <Button
              type="submit"
              disabled={loading}
              className="bg-primary hover:bg-primary/80 text-primary-foreground mt-2"
            >
              {loading ? "Processando..." : isLogin ? "Entrar" : "Criar conta"}
            </Button>
          </form>

          <div className="mt-4 text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin)
                setError("")
              }}
              className="text-[oklch(0.55_0_0)] text-sm hover:text-foreground transition-colors"
            >
              {isLogin ? "Não tem conta? Criar conta" : "Já tem conta? Entrar"}
            </button>
          </div>
        </div>

        {/* Demo credentials */}
        <p className="text-center text-[oklch(0.4_0_0)] text-xs mt-4">
          Demo: Entre em contato com o seu Adm
        </p>
      </div>
    </div>
  )
}