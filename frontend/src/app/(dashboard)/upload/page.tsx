"use client"

import { useState, useEffect, useRef } from "react"
import { apiGet, apiPost, apiPostForm } from "@/lib/api"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { UploadCloud, CheckCircle2, AlertCircle } from "lucide-react"

interface Obra {
  id: number
  titulo: string
  slug: string
  fonte: string
  idioma?: string
}

export default function UploadPage() {
  const [obras, setObras] = useState<Obra[]>([])
  const [selectedObra, setSelectedObra] = useState<string>("")
  const [numero, setNumero] = useState<string>("")
  const [titulo, setTitulo] = useState<string>("")

  const [files, setFiles] = useState<File[]>([])
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadStatus, setUploadStatus] = useState<"idle" | "success" | "error">("idle")
  const [errorMessage, setErrorMessage] = useState("")
  const [dragActive, setDragActive] = useState(false)

  const fileInputRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    apiGet<Obra[] | { results: Obra[] }>("/obras/")
      .then((data) => setObras(Array.isArray(data) ? data : (data?.results ?? [])))
      .catch((err) => console.error("Erro ao carregar obras:", err))
  }, [])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const selectedFiles = Array.from(e.target.files).sort((a, b) => a.name.localeCompare(b.name))
      setFiles(selectedFiles)
    }
  }

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(true)
  }

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
  }

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault()
    setDragActive(false)
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const droppedFiles = Array.from(e.dataTransfer.files)
        .filter(f => f.type.startsWith("image/"))
        .sort((a, b) => a.name.localeCompare(b.name))
      if (droppedFiles.length > 0) {
        setFiles(droppedFiles)
      }
    }
  }

  const handleUpload = async () => {
    if (!selectedObra) return setErrorMessage("Selecione uma obra.")
    if (!numero) return setErrorMessage("Informe o número do capítulo.")
    if (files.length === 0) return setErrorMessage("Selecione as páginas.")

    setIsUploading(true)
    setUploadStatus("idle")
    setErrorMessage("")
    setUploadProgress(0)

    try {
      const obra = obras.find(o => o.id.toString() === selectedObra)
      if (!obra) throw new Error("Obra não encontrada")

      // 1. Sobe cada página direto pro R2 via backend (multipart)
      const publicUrls: string[] = []
      for (let i = 0; i < files.length; i++) {
        const file = files[i]
        const fd = new FormData()
        fd.append("imagem", file)
        fd.append("slug", obra.slug)
        fd.append("capitulo_numero", numero)
        fd.append("ordem", String(i + 1))

        const res = await apiPostForm<{ url: string }>("/upload/pagina/", fd)
        publicUrls.push(res.url)
        // Upload representa 60% do progresso
        setUploadProgress(Math.round(((i + 1) / files.length) * 60))
      }

      // 2. Cria o capítulo
      const capResponse = await apiPost<{ id: number }>("/capitulos/", {
        obra: obra.id,
        numero: parseFloat(numero),
        titulo: titulo || `Capítulo ${numero}`,
        ordem: Math.floor(parseFloat(numero)),
      })
      const capituloId = capResponse.id

      // 3. Cria as páginas vinculadas
      for (let i = 0; i < publicUrls.length; i++) {
        await apiPost("/paginas/", {
          capitulo: capituloId,
          imagem_url: publicUrls[i],
          ordem: i + 1,
          width: 0,
          height: 0,
        })
        setUploadProgress(60 + Math.round(((i + 1) / publicUrls.length) * 40))
      }

      setUploadStatus("success")
      setFiles([])
      setNumero("")
      setTitulo("")
      if (fileInputRef.current) fileInputRef.current.value = ""
    } catch (error) {
      console.error(error)
      setUploadStatus("error")
      setErrorMessage(error instanceof Error ? error.message : "Ocorreu um erro durante o upload.")
    } finally {
      setIsUploading(false)
    }
  }

  return (
    <div className="p-6 max-w-4xl mx-auto min-h-screen">
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-foreground">Upload de Capítulo</h1>
        <p className="text-[oklch(0.55_0_0)] text-sm">Faça upload de páginas diretamente para a nuvem.</p>
      </div>

      <Card className="bg-[oklch(0.12_0_0)] border-border text-foreground">
        <CardHeader>
          <CardTitle className="text-lg">Informações do Capítulo</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div className="space-y-1">
              <label className="text-sm font-medium text-[oklch(0.55_0_0)]">Obra</label>
              <select
                className="w-full bg-[oklch(0.16_0_0)] border border-border rounded-md px-3 py-2"
                value={selectedObra}
                onChange={e => setSelectedObra(e.target.value)}
                disabled={isUploading}
              >
                <option value="">Selecione uma obra...</option>
                {obras.map(o => (
                  <option key={o.id} value={o.id}>{o.titulo} ({o.fonte})</option>
                ))}
              </select>
            </div>
            <div className="space-y-1">
              <label className="text-sm font-medium text-[oklch(0.55_0_0)]">Número do Cap.</label>
              <Input
                type="number"
                step="0.1"
                placeholder="Ex: 1 ou 1.5"
                className="bg-[oklch(0.16_0_0)] border-border"
                value={numero}
                onChange={e => setNumero(e.target.value)}
                disabled={isUploading}
              />
            </div>
          </div>
          <div className="space-y-1">
            <label className="text-sm font-medium text-[oklch(0.55_0_0)]">Título (Opcional)</label>
            <Input
              placeholder="Ex: O Despertar"
              className="bg-[oklch(0.16_0_0)] border-border"
              value={titulo}
              onChange={e => setTitulo(e.target.value)}
              disabled={isUploading}
            />
          </div>

          <div className="pt-4">
            <label className="text-sm font-medium text-[oklch(0.55_0_0)] mb-2 block">Páginas</label>
            <div
              className={`border-2 border-dashed rounded-lg p-8 flex flex-col items-center justify-center transition-colors cursor-pointer ${
                dragActive
                  ? "border-primary bg-primary/10"
                  : "border-border bg-[oklch(0.16_0_0)] hover:bg-[oklch(0.18_0_0)]"
              }`}
              onClick={() => fileInputRef.current?.click()}
              onDragOver={handleDragOver}
              onDragLeave={handleDragLeave}
              onDrop={handleDrop}
            >
              <UploadCloud className="w-10 h-10 text-[oklch(0.55_0_0)] mb-3" />
              <p className="text-sm text-center">
                <span className="font-semibold text-primary">Clique para selecionar</span> ou arraste e solte
              </p>
              <p className="text-xs text-[oklch(0.55_0_0)] mt-1">Imagens (JPG, PNG, WEBP)</p>
              <input
                ref={fileInputRef}
                type="file"
                multiple
                accept="image/*"
                className="hidden"
                onChange={handleFileChange}
                disabled={isUploading}
              />
            </div>

            {files.length > 0 && (
              <div className="mt-4">
                <p className="text-sm font-medium text-[oklch(0.55_0_0)]">{files.length} páginas selecionadas.</p>
                <div className="flex flex-wrap gap-2 mt-2 max-h-32 overflow-y-auto p-2 bg-[oklch(0.14_0_0)] rounded border border-border">
                  {files.map((f, i) => (
                    <span key={i} className="text-xs bg-[oklch(0.20_0_0)] px-2 py-1 rounded truncate max-w-[150px]">
                      {f.name}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {uploadStatus === "error" && (
            <div className="bg-destructive/10 text-destructive p-3 rounded-md flex items-start gap-2 text-sm mt-4">
              <AlertCircle className="w-4 h-4 mt-0.5 shrink-0" />
              <p>{errorMessage}</p>
            </div>
          )}

          {uploadStatus === "success" && (
            <div className="bg-emerald-500/10 text-emerald-500 p-3 rounded-md flex items-start gap-2 text-sm mt-4">
              <CheckCircle2 className="w-4 h-4 mt-0.5 shrink-0" />
              <p>Upload concluído com sucesso! Capítulo salvo no banco de dados.</p>
            </div>
          )}

          {isUploading && (
            <div className="mt-4 space-y-2">
              <div className="flex justify-between text-xs text-[oklch(0.55_0_0)]">
                <span>Enviando e processando...</span>
                <span>{uploadProgress}%</span>
              </div>
              <div className="w-full bg-[oklch(0.16_0_0)] rounded-full h-2 overflow-hidden">
                <div
                  className="bg-primary h-2 rounded-full transition-all duration-300"
                  style={{ width: `${uploadProgress}%` }}
                ></div>
              </div>
            </div>
          )}

          <div className="pt-4">
            <Button
              className="w-full bg-primary hover:bg-primary/80"
              onClick={handleUpload}
              disabled={isUploading || files.length === 0 || !selectedObra || !numero}
            >
              {isUploading ? "Fazendo Upload..." : "Publicar Capítulo"}
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Upload ZIP */}
      <Card className="bg-[oklch(0.12_0_0)] border-border">
        <CardHeader>
          <CardTitle className="text-foreground">Upload via ZIP (Múltiplas Páginas)</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-[oklch(0.55_0_0)] mb-4">
            Faça upload de um arquivo ZIP contendo todas as páginas do capítulo. As imagens serão ordenadas automaticamente pelo nome.
          </p>
          <div className="flex flex-col gap-4">
            <div>
              <label className="text-sm text-[oklch(0.55_0_0)]">Obra</label>
              <select
                className="w-full bg-[oklch(0.16_0_0)] border-border text-foreground p-2 rounded"
                value={selectedObra}
                onChange={(e) => setSelectedObra(e.target.value)}
              >
                <option value="">Selecione</option>
                {obras.map((o) => (
                  <option key={o.id} value={o.slug}>{o.titulo}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="text-sm text-[oklch(0.55_0_0)]">Número do Capítulo</label>
              <Input
                placeholder="Ex: 1 ou 12.5"
                value={numero}
                onChange={(e) => setNumero(e.target.value)}
                className="bg-[oklch(0.16_0_0)]"
              />
            </div>
            <div>
              <label className="text-sm text-[oklch(0.55_0_0)]">Arquivo ZIP</label>
              <Input
                type="file"
                accept=".zip"
                onChange={(e) => {
                  if (e.target.files?.[0]) {
                    const file = e.target.files[0]
                    // Placeholder: você implementa o upload ZIP aqui
                    console.log('ZIP selecionado:', file.name)
                  }
                }}
                className="bg-[oklch(0.16_0_0)]"
              />
            </div>
            <Button className="bg-primary hover:bg-primary/80" disabled>
              Upload ZIP (em breve)
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
