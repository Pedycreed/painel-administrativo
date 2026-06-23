"use client"

import { useState, useRef } from "react"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { apiPost, apiPostForm } from "@/lib/api"
import { UploadCloud } from "lucide-react"
import { useAuth } from "@/contexts/AuthContext"

export default function NovaObraDialog() {
  const { user } = useAuth()
  // Se o usuário tem time fixo, a fonte da nova obra já vem pré-definida.
  const fonteFixa = !user?.has_full_access ? user?.time ?? null : null

  const [titulo, setTitulo] = useState("")
  const [autor, setAutor] = useState("")
  const [status, setStatus] = useState("ongoing")
  const [fonte, setFonte] = useState<string>(fonteFixa ?? "scan")
  const [idioma, setIdioma] = useState("pt")
  const [tipoObra, setTipoObra] = useState("manga")
  const [capaFile, setCapaFile] = useState<File | null>(null)
  const [capaPreview, setCapaPreview] = useState("")
  const [uploadingCapa, setUploadingCapa] = useState(false)
  const [dragActive, setDragActive] = useState(false)

  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState("")

  const fileInputRef = useRef<HTMLInputElement>(null)

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file && file.type.startsWith("image/")) {
      setCapaFile(file)
      setCapaPreview(URL.createObjectURL(file))
    }
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    setDragActive(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault()
    setDragActive(false)
  }

  function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files[0]
    if (file && file.type.startsWith("image/")) {
      setCapaFile(file)
      setCapaPreview(URL.createObjectURL(file))
    }
  }

  async function uploadCapa(slug: string): Promise<string> {
    if (!capaFile) return ""
    setUploadingCapa(true)
    try {
      const formData = new FormData()
      formData.append("imagem", capaFile)
      formData.append("slug", slug)
      const data = await apiPostForm<{ url: string }>("/upload/imagem/", formData)
      return data.url
    } finally {
      setUploadingCapa(false)
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!titulo || !autor) return
    setError("")
    setLoading(true)

    try {
      const slug = titulo
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "")

      let capaUrl = ""
      if (capaFile) {
        capaUrl = await uploadCapa(slug)
      }

      await apiPost("/obras/", { titulo, autor, slug, status, fonte, idioma, tipo_obra: tipoObra, capa_url: capaUrl })
      setTitulo("")
      setAutor("")
      setStatus("ongoing")
      setFonte("scan")
      setIdioma("pt")
      setTipoObra("manga")
      setCapaFile(null)
      setCapaPreview("")
      setOpen(false)
      window.location.reload()
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao criar obra")
    } finally {
      setLoading(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={setOpen}>
      <DialogTrigger>
        <Button className="bg-primary hover:bg-primary/80 text-primary-foreground">+ Nova Obra</Button>
      </DialogTrigger>
      <DialogContent className="bg-card border-border text-foreground">
        <DialogHeader>
          <DialogTitle className="text-foreground">Nova Obra</DialogTitle>
        </DialogHeader>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 mt-4">
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Título *</label>
            <Input
              className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
              placeholder="Ex: Solo Leveling"
              value={titulo}
              onChange={(e) => setTitulo(e.target.value)}
              required
            />
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Autor *</label>
            <Input
              className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
              placeholder="Ex: Chugong"
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
          {fonteFixa ? (
            <input type="hidden" value={fonteFixa} readOnly />
          ) : (
            <div className="flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Fonte</label>
              <select
                className="bg-[oklch(0.16_0_0)] border border-border text-foreground rounded-md px-3 py-2 text-sm"
                value={fonte}
                onChange={(e) => setFonte(e.target.value)}
              >
                <option value="scan">Scan</option>
                <option value="agregador">Agregador</option>
              </select>
            </div>
          )}
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Idioma</label>
            <select
              className="bg-[oklch(0.16_0_0)] border border-border text-foreground rounded-md px-3 py-2 text-sm"
              value={idioma}
              onChange={(e) => setIdioma(e.target.value)}
            >
              <option value="pt">Português</option>
              <option value="en">English</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Tipo</label>
            <select
              className="bg-[oklch(0.16_0_0)] border border-border text-foreground rounded-md px-3 py-2 text-sm"
              value={tipoObra}
              onChange={(e) => setTipoObra(e.target.value)}
            >
              <option value="manga">Mangá</option>
              <option value="manhwa">Manhwa</option>
              <option value="manhua">Manhua</option>
              <option value="novel">Light Novel</option>
            </select>
          </div>
          <div className="flex flex-col gap-1">
            <label className="text-[oklch(0.55_0_0)] text-sm">Capa</label>
            <div
              className={`border-2 border-dashed rounded-lg flex flex-col items-center justify-center p-4 transition-colors cursor-pointer ${
                dragActive
                  ? "border-primary bg-primary/10"
                  : "border-border bg-[oklch(0.16_0_0)] hover:border-[oklch(0.3_0_0)]"
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => fileInputRef.current?.click()}
            >
              {capaPreview ? (
                <div className="flex flex-col items-center gap-2">
                  <img
                    src={capaPreview}
                    alt="Capa"
                    className="w-20 h-28 object-cover rounded border border-border"
                  />
                  <p className="text-[oklch(0.55_0_0)] text-xs">Clique ou arraste para trocar</p>
                </div>
              ) : (
                <>
                  <UploadCloud className="w-6 h-6 text-[oklch(0.55_0_0)] mb-1" />
                  <p className="text-xs text-[oklch(0.55_0_0)]">Arraste ou clique para selecionar</p>
                </>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>
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