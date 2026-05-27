"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { ArrowLeft } from "lucide-react"

import { apiGet, apiPut, apiPostForm } from "@/lib/api"

interface Obra {
  titulo: string
  autor: string
  status: string
  capa_url: string | null
  sinopse: string | null
  tags: string[] | null
}

export default function EditarObraPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const [slug, setSlug] = useState("")
  const [titulo, setTitulo] = useState("")
  const [autor, setAutor] = useState("")
  const [status, setStatus] = useState("ongoing")
  const [capaUrl, setCapaUrl] = useState("")
  const [capaPreview, setCapaPreview] = useState("")
  const [uploading, setUploading] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [sinopse, setSinopse] = useState("")
  const [tagsText, setTagsText] = useState("")
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)

  function processarCapa(url: string) {
    setCapaUrl(url)
    setCapaPreview(url)
  }

  async function handleFile(file: File) {
    if (!file.type.startsWith("image/")) return
    if (!slug) {
      alert("Slug da obra ainda não carregou. Aguarde um instante.")
      return
    }
    setUploading(true)
    try {
      const formData = new FormData()
      formData.append("imagem", file)
      formData.append("slug", slug)

      const data = await apiPostForm<{ url: string }>("/upload/imagem/", formData)
      processarCapa(data.url)
    } catch (e) {
      console.error(e)
      alert(e instanceof Error ? e.message : "Erro ao fazer upload da imagem")
    } finally {
      setUploading(false)
    }
  }

  async function handleDrop(e: React.DragEvent) {
    e.preventDefault()
    setDragActive(false)
    const file = e.dataTransfer.files[0]
    if (file) handleFile(file)
  }

  function handleDragOver(e: React.DragEvent) {
    e.preventDefault()
    setDragActive(true)
  }

  function handleDragLeave(e: React.DragEvent) {
    e.preventDefault()
    setDragActive(false)
  }

  function handleFileSelect(e: React.ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0]
    if (file) handleFile(file)
  }

  function handleUrlInput(e: React.ChangeEvent<HTMLInputElement>) {
    const url = e.target.value
    if (url.startsWith("http")) processarCapa(url)
  }

  useEffect(() => {
    params.then(async (p) => {
      setSlug(p.id)
      try {
        const data = await apiGet<Obra>(`/obras/${p.id}/`)
        setTitulo(data.titulo)
        setAutor(data.autor)
        setStatus(data.status)
        setCapaUrl(data.capa_url || "")
        setCapaPreview(data.capa_url || "")
        setSinopse(data.sinopse || "")
        setTagsText(data.tags ? data.tags.join(", ") : "")
      } catch (e) {
        console.error(e)
        alert(e instanceof Error ? e.message : "Erro ao carregar obra")
      } finally {
        setLoading(false)
      }
    })
  }, [])

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    if (!titulo || !autor) return
    setSaving(true)
    try {
      const novoSlug = titulo
        .toLowerCase()
        .normalize("NFD")
        .replace(/[\u0300-\u036f]/g, "")
        .replace(/[^a-z0-9]+/g, "-")
        .replace(/^-|-$/g, "")

      const tags = tagsText
        .split(",")
        .map((t) => t.trim())
        .filter(Boolean)

      await apiPut(`/obras/${slug}/`, {
        titulo,
        autor,
        slug: novoSlug,
        status,
        capa_url: capaUrl,
        sinopse,
        tags,
      })
      router.push(`/obras/${novoSlug}`)
    } catch (err) {
      console.error(err)
      alert(err instanceof Error ? err.message : "Erro ao atualizar obra")
    } finally {
      setSaving(false)
    }
  }

  if (loading) return <div className="px-6 py-8"><p className="text-[oklch(0.55_0_0)]">Carregando...</p></div>

  return (
    <div className="px-6 py-6">
      <Link href="/" className="text-[oklch(0.55_0_0)] text-sm hover:text-foreground mb-6 inline-flex items-center gap-1">
        <ArrowLeft className="w-4 h-4" />Obras
      </Link>

      <h1 className="text-2xl font-semibold text-foreground mb-8">Edição Avançada</h1>

      <form onSubmit={handleSubmit}>
        <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg p-6 flex flex-col gap-5">
          {/* Informações básicas */}
          <div>
            <h2 className="text-foreground font-medium mb-4">Informações Básicas</h2>
            <div className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-[oklch(0.55_0_0)] text-sm">Título</label>
                <Input
                  className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
                  value={titulo}
                  onChange={(e) => setTitulo(e.target.value)}
                />
              </div>

              <div className="flex flex-col gap-1">
                <label className="text-[oklch(0.55_0_0)] text-sm">Autor</label>
                <Input
                  className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
                  value={autor}
                  onChange={(e) => setAutor(e.target.value)}
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
            </div>
          </div>

          {/* Capa */}
          <div className="border-t border-border pt-5">
            <h2 className="text-foreground font-medium mb-4">Capa da Obra</h2>

            {/* Drop zone */}
            <div
              className={`border-2 border-dashed rounded-lg flex flex-col items-center justify-center p-8 transition-colors cursor-pointer ${
                dragActive
                  ? "border-primary bg-primary/10"
                  : "border-border bg-[oklch(0.16_0_0)] hover:border-[oklch(0.3_0_0)]"
              }`}
              onDrop={handleDrop}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onClick={() => document.getElementById("capa-file")?.click()}
            >
              {capaPreview ? (
                <div className="flex flex-col items-center gap-3">
                  <img
                    src={capaPreview}
                    alt="Capa"
                    className="w-32 h-48 object-cover rounded-lg border border-border"
                  />
                  <p className="text-[oklch(0.55_0_0)] text-xs">Clique ou arraste outra imagem para trocar</p>
                </div>
              ) : uploading ? (
                <p className="text-[oklch(0.55_0_0)]">Enviando...</p>
              ) : (
                <>
                  <p className="text-foreground text-sm font-medium mb-1">Arraste uma imagem aqui</p>
                  <p className="text-[oklch(0.55_0_0)] text-xs">ou clique para selecionar</p>
                  <p className="text-[oklch(0.35_0_0)] text-xs mt-2">JPG, PNG, WebP</p>
                </>
              )}
              <input
                id="capa-file"
                type="file"
                accept="image/*"
                className="hidden"
                onChange={handleFileSelect}
              />
            </div>

            {/* URL da capa */}
            <div className="mt-4 flex flex-col gap-1">
              <label className="text-[oklch(0.55_0_0)] text-sm">Ou cole a URL da capa</label>
              <Input
                className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
                placeholder="https://..."
                value={capaUrl}
                onChange={(e) => { setCapaUrl(e.target.value); handleUrlInput({ target: e } as any) }}
              />
            </div>
          </div>

          {/* Sinopse */}
          <div className="border-t border-border pt-5">
            <h2 className="text-foreground font-medium mb-4">Sinopse</h2>
            <textarea
              className="bg-[oklch(0.16_0_0)] border border-border text-foreground rounded-md px-3 py-2 text-sm min-h-[100px] resize-y focus:outline-none focus:border-primary/50 placeholder:text-[oklch(0.55_0_0)]"
              value={sinopse}
              onChange={(e) => setSinopse(e.target.value)}
              placeholder="Breve descrição da obra..."
            />
          </div>

          {/* Tags */}
          <div className="border-t border-border pt-5">
            <h2 className="text-foreground font-medium mb-4">Tags</h2>
            <div className="flex flex-col gap-1">
              <Input
                className="bg-[oklch(0.16_0_0)] border-border text-foreground placeholder:text-[oklch(0.55_0_0)]"
                placeholder="Ação, Aventura, Fantasia"
                value={tagsText}
                onChange={(e) => setTagsText(e.target.value)}
              />
              <p className="text-[oklch(0.55_0_0)] text-xs">Separadas por vírgula</p>
            </div>
          </div>

          {/* Botões */}
          <div className="flex gap-2 border-t border-border pt-5">
            <Button type="submit" disabled={saving} className="bg-primary hover:bg-primary/80 text-primary-foreground">
              {saving ? "Salvando..." : "Salvar"}
            </Button>
            <Button
              type="button"
              onClick={() => router.back()}
              variant="outline"
              className="border-border text-[oklch(0.75_0_0)] hover:bg-[oklch(0.16_0_0)]"
            >
              Cancelar
            </Button>
          </div>
        </div>
      </form>
    </div>
  )
}
