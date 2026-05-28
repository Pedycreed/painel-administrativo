"use client"

import { useState, useEffect } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { apiPatch } from "@/lib/api"
import { useAuth } from "@/contexts/AuthContext"

export interface UsuarioGestao {
  id: number
  username: string
  email: string
  papel: "admin"
  papel_display: string
  time: "scan" | "agregador" | null
  time_display: string
  is_active: boolean
  is_superuser: boolean
}

interface EditarUsuarioDialogProps {
  usuario: UsuarioGestao
  onUpdated: () => void
}

export default function EditarUsuarioDialog({ usuario, onUpdated }: EditarUsuarioDialogProps) {
  const { user: requester } = useAuth()
  const isSuper = !!requester?.is_superuser

  const [open, setOpen] = useState(false)
  const [email, setEmail] = useState(usuario.email)
  const [time, setTime] = useState<"scan" | "agregador">(
    usuario.time ?? requester?.time ?? "scan"
  )
  const [isActive, setIsActive] = useState(usuario.is_active)
  const [password, setPassword] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  useEffect(() => {
    if (open) {
      // Reset ao reabrir
      setEmail(usuario.email)
      setTime(usuario.time ?? requester?.time ?? "scan")
      setIsActive(usuario.is_active)
      setPassword("")
      setError("")
    }
  }, [open, usuario, requester])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    setError("")
    setLoading(true)
    try {
      const payload: Record<string, unknown> = {
        email,
        is_active: isActive,
      }
      // Superuser tem time=null (acesso transversal). Não mandar time
      // pra não sobrescrever pra "scan" acidentalmente.
      if (!usuario.is_superuser) {
        payload.time = time
      }
      if (password) payload.password = password
      await apiPatch(`/auth/usuarios/${usuario.id}/`, payload)
      setOpen(false)
      onUpdated()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar usuário")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button variant="outline" className="border-border text-[oklch(0.75_0_0)] hover:bg-[oklch(0.16_0_0)] text-xs h-7 px-2">
          Editar
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border text-foreground">
        <DialogHeader>
          <DialogTitle className="text-foreground">
            Editar Usuário — {usuario.username}
          </DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-4">
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
            <label className="text-[oklch(0.55_0_0)] text-sm">
              Nova senha <span className="text-[oklch(0.4_0_0)]">(deixe vazio pra manter)</span>
            </label>
            <Input
              className="bg-[oklch(0.16_0_0)] border-border text-foreground"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
            />
          </div>
          {isSuper ? (
            <div className="flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Time</label>
              <select
                className="bg-[oklch(0.16_0_0)] border border-border text-foreground rounded-md px-3 py-2 text-sm"
                value={time}
                onChange={(e) => setTime(e.target.value as typeof time)}
                disabled={usuario.is_superuser}
              >
                <option value="scan">Scan</option>
                <option value="agregador">Agregador</option>
              </select>
            </div>
          ) : (
            <input type="hidden" value={time} readOnly />
          )}
          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id={`active-${usuario.id}`}
              checked={isActive}
              onChange={(e) => setIsActive(e.target.checked)}
              className="h-4 w-4"
            />
            <label htmlFor={`active-${usuario.id}`} className="text-foreground text-sm">
              Ativo
            </label>
          </div>
          {error && <p className="text-red-400 text-sm">{error}</p>}
          <Button type="submit" disabled={loading} className="bg-primary hover:bg-primary/80 mt-2">
            {loading ? "Salvando..." : "Salvar"}
          </Button>
        </form>
      </DialogContent>
    </Dialog>
  )
}
