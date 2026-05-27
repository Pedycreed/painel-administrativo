"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { apiPut } from "@/lib/api"

interface EditarObraDialogProps {
  obra: { id: number; titulo: string; autor: string; status: string; slug: string; fonte?: string }
  onUpdated: () => void
}

export default function EditarObraDialog({ obra, onUpdated }: EditarObraDialogProps) {
  const [open, setOpen] = useState(false)
  const [titulo, setTitulo] = useState(obra.titulo)
  const [autor, setAutor] = useState(obra.autor)
  const [status, setStatus] = useState(obra.status)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!titulo || !autor) return
    setError("")
    setLoading(true)

    try {
      const novoSlug = titulo
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "")

      await apiPut(`/obras/${obra.slug || obra.id}/`, {
        titulo,
        autor,
        slug: novoSlug,
        status,
        fonte: obra.fonte || "scan"
      })
      setOpen(false)
      onUpdated()
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao atualizar obra")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={(o) => {
      if (o) {
        setTitulo(obra.titulo)
        setAutor(obra.autor)
        setStatus(obra.status)
      }
      setOpen(o)
    }}>
      <DialogTrigger>
        <Button variant="outline" className="border-border text-[oklch(0.75_0_0)] hover:bg-[oklch(0.16_0_0)] text-sm">
          Editar
        </Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border text-foreground">
        <DialogHeader>
          <DialogTitle className="text-foreground">Editar Obra</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit}>
          <div className="flex flex-col gap-4 mt-4">
            <div className="flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Título</label>
              <Input
                className="bg-[oklch(0.16_0_0)] border-border text-foreground"
                value={titulo}
                onChange={(e) => setTitulo(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Autor</label>
              <Input
                className="bg-[oklch(0.16_0_0)] border-border text-foreground"
                value={autor}
                onChange={(e) => setAutor(e.target.value)}
                required
              />
            </div>
            <div className="flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Status</label>
              <select
                className="bg-[oklch(0.16_0_0)] border border-border text-foreground rounded-md px-3 py-2 text-sm"
                value={status}
                onChange={(e) => setStatus(e.target.value)}
              >
                <option value="ongoing">Ongoing</option>
                <option value="completed">Complete</option>
              </select>
            </div>
            {error && <p className="text-red-400 text-sm">{error}</p>}
            <Button type="submit" disabled={loading} className="bg-primary hover:bg-primary/80 mt-2">
              {loading ? "Salvando..." : "Salvar"}
            </Button>
          </div>
        </form>
      </DialogContent>
    </Dialog>
  )
}