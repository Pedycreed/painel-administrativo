"use client"

import { useEffect, useState } from "react"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
// papel column removed — every panel user is admin now
import { Trash2, ShieldCheck } from "lucide-react"
import { apiGet, apiDelete } from "@/lib/api"
import { useAuth } from "@/contexts/AuthContext"
import { useRequireManagerRole } from "@/lib/teamGuard"
import NovoUsuarioDialog from "@/components/NovoUsuarioDialog"
import EditarUsuarioDialog, { UsuarioGestao } from "@/components/EditarUsuarioDialog"

export default function UsuariosPage() {
  const allowed = useRequireManagerRole()
  const { user: requester } = useAuth()
  const [usuarios, setUsuarios] = useState<UsuarioGestao[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")

  async function loadUsuarios() {
    setError("")
    try {
      const data = await apiGet<UsuarioGestao[] | { results: UsuarioGestao[] }>("/auth/usuarios/")
      // Suporta resposta paginada ou não
      const lista = Array.isArray(data) ? data : (data?.results ?? [])
      setUsuarios(lista)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar usuários")
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!allowed) return
    loadUsuarios()
  }, [allowed])

  async function handleDelete(u: UsuarioGestao) {
    if (u.id === requester?.id) return
    if (!confirm(`Deletar o usuário "${u.username}"? Essa ação não pode ser desfeita.`)) return
    try {
      await apiDelete(`/auth/usuarios/${u.id}/`)
      loadUsuarios()
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao deletar usuário")
    }
  }

  if (!allowed) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p className="text-[oklch(0.55_0_0)]">Verificando acesso...</p>
      </div>
    )
  }

  return (
    <div className="min-h-screen">
      <div className="px-4 sm:px-6 py-4 sm:py-6 max-w-6xl mx-auto">
        {/* Header */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
          <div>
            <h1 className="text-xl sm:text-2xl font-semibold text-foreground">Usuários</h1>
            <p className="text-[oklch(0.55_0_0)] text-sm mt-1">
              {requester?.is_superuser
                ? "Gestão completa: você pode criar e editar usuários de qualquer time."
                : `Gestão de usuários do time ${requester?.time_display ?? ""}.`}
            </p>
          </div>
          <NovoUsuarioDialog onCreated={loadUsuarios} />
        </div>

        {/* Tabela */}
        {loading ? (
          <p className="text-[oklch(0.55_0_0)] text-center py-10">Carregando...</p>
        ) : error ? (
          <p className="text-red-400 text-center py-10">{error}</p>
        ) : usuarios.length === 0 ? (
          <p className="text-[oklch(0.55_0_0)] text-center py-10">Nenhum usuário cadastrado.</p>
        ) : (
          <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="border-border">
                  <TableHead className="text-[oklch(0.55_0_0)] font-medium">Usuário</TableHead>
                  <TableHead className="text-[oklch(0.55_0_0)] font-medium">Email</TableHead>
                  <TableHead className="text-[oklch(0.55_0_0)] font-medium">Time</TableHead>
                  <TableHead className="text-[oklch(0.55_0_0)] font-medium">Status</TableHead>
                  <TableHead className="text-[oklch(0.55_0_0)] font-medium text-right">Ações</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {usuarios.map((u) => {
                  const isSelf = u.id === requester?.id
                  return (
                    <TableRow key={u.id} className="border-border">
                      <TableCell className="text-foreground font-medium">
                        <div className="flex items-center gap-2">
                          {u.is_superuser && (
                            <ShieldCheck className="w-3.5 h-3.5 text-primary" aria-label="Superuser" />
                          )}
                          {u.username}
                          {isSelf && (
                            <span className="text-[oklch(0.4_0_0)] text-xs">(você)</span>
                          )}
                        </div>
                      </TableCell>
                      <TableCell className="text-[oklch(0.75_0_0)] text-sm">{u.email || "—"}</TableCell>
                      <TableCell className="text-[oklch(0.75_0_0)] text-sm">
                        {u.time_display || "—"}
                      </TableCell>
                      <TableCell>
                        {u.is_active ? (
                          <Badge className="bg-emerald-500/10 text-emerald-500 text-xs">Ativo</Badge>
                        ) : (
                          <Badge className="bg-[oklch(0.2_0_0)] text-[oklch(0.55_0_0)] text-xs">Inativo</Badge>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-2">
                          {!u.is_superuser || requester?.is_superuser ? (
                            <EditarUsuarioDialog usuario={u} onUpdated={loadUsuarios} />
                          ) : null}
                          {!isSelf && !u.is_superuser && (
                            <button
                              onClick={() => handleDelete(u)}
                              className="text-[oklch(0.55_0_0)] hover:text-destructive transition-colors p-1"
                              aria-label="Deletar"
                              title="Deletar"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </div>
  )
}
