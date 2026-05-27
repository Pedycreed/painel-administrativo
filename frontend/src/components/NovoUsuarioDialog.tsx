"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { apiPost } from "@/lib/api"
import { useAuth } from "@/contexts/AuthContext"

interface NovoUsuarioDialogProps {
  onCreated: () => void
}

export default function NovoUsuarioDialog({ onCreated }: NovoUsuarioDialogProps) {
  const { user: requester } = useAuth()
  const isSuper = !!requester?.is_superuser

  const [open, setOpen] = useState(false)
  const [username, setUsername] = useState("")
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  // Admin (não-super) cria sempre com o time dele — backend ignora o campo se vier diferente
  const [time, setTime] = useState<"scan" | "agregador">(
    requester?.time ?? "scan"
  )
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  function reset() {
    setUsername("")
    setEmail("")
    setPassword("")
    setTime(requester?.time ?? "scan")
    setError("")
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!username || !password) return
    setError("")
    setLoading(true)
    try {
      const payload: Record<string, unknown> = {
        username,
        email,
        password,
        time,
        is_active: true,
      }
      await apiPost("/auth/usuarios/", payload)
      reset()
      setOpen(false)
      onCreated()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao criar usuário")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => { if (!o) reset(); setOpen(o) }}>
      <DialogTrigger>
        <Button className="bg-primary hover:bg-primary/80 text-primary-foreground">+ Novo Usuário</Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border text-foreground">
        <DialogHeader>
          <DialogTitle className="text-foreground">Novo Usuário</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-4">
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Username *</label>
            <Input
              className="bg-[oklch(0.16_0_0)] border-border text-foreground"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              autoFocus
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Email</label>
            <Input
              className="bg-[oklch(0.16_0_0)] border-border text-foreground"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Senha *</label>
            <Input
              className="bg-[oklch(0.16_0_0)] border-border text-foreground"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={8}
            />
          </div>
          {isSuper ? (
            <div className="flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Time</label>
              <select
                className="bg-[oklch(0.16_0_0)] border border-border text-foreground rounded-md px-3 py-2 text-sm"
                value={time}
                onChange={(e) => setTime(e.target.value as typeof time)}
              >
                <option value="scan">Scan</option>
                <option value="agregador">Agregador</option>
              </select>
            </div>
          ) : (
            <input type="hidden" value={time} readOnly />
          )}
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <Button type="submit" disabled={loading} className="bg-primary hover:bg-primary/80 mt-2">
            {loading ? "Criando..." : "Criar"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
