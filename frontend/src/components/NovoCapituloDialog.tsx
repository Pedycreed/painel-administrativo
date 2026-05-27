"use client"

import { useState } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { apiPost } from "@/lib/api"

interface NovoCapituloDialogProps {
  obraId: number
  onCreated: () => void
}

export default function NovoCapituloDialog({ obraId, onCreated }: NovoCapituloDialogProps) {
  const [open, setOpen] = useState(false)
  const [numero, setNumero] = useState("")
  const [titulo, setTitulo] = useState("")
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!numero) return
    setError("")
    setLoading(true)

    try {
      await apiPost("/capitulos/", {
        obra: obraId,
        numero: parseFloat(numero),
        titulo,
        ordem: 0,
      })
      setNumero("")
      setTitulo("")
      setOpen(false)
      onCreated()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao criar capítulo")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button className="bg-primary hover:bg-primary/80 text-sm">+ Novo Capítulo</Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border text-foreground">
        <DialogHeader>
          <DialogTitle className="text-foreground">Novo Capítulo</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-4">
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Número *</label>
            <Input
              className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
              placeholder="Ex: 10"
              type="number"
              step="0.1"
              value={numero}
              onChange={(e) => setNumero(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Título (opcional)</label>
            <Input
              className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
              placeholder="Ex: O começo de tudo"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
            />
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