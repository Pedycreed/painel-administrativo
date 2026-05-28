"use client"

import { useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { Badge } from "@/components/ui/badge"
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import Link from "next/link"
import { ArrowLeft, Trash2 } from "lucide-react"
import NovoCapituloDialog from "@/components/NovoCapituloDialog"
import EditarObraDialog from "@/components/EditarObraDialog"
import { apiGet, apiDelete } from "@/lib/api"

interface Obra {
  id: number
  titulo: string
  autor: string
  slug: string
  status: string
  fonte: string
  capa_url: string | null
  sinopse: string
  tags: string[]
  capitulos: Capitulo[]
}

interface Capitulo {
  id: number
  numero: number
  titulo: string
  paginas: any[]
}

export default function ObraPage({ params }: { params: Promise<{ id: string }> }) {
  const router = useRouter()
  const [obra, setObra] = useState<Obra | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState("")
  const [deleting, setDeleting] = useState(false)

  async function fetchObra(slug: string) {
    try {
      const data = await apiGet<Obra>(`/obras/${slug}/`)
      setObra(data)
    } catch (e) {
      setError(e instanceof Error ? e.message : "Erro ao carregar obra")
    } finally {
      setLoading(false)
    }
  }

  async function deleteCapitulo(capituloId: number) {
    if (!confirm("Tem certeza que deseja deletar este capítulo e todas as suas páginas?")) return
    try {
      await apiDelete(`/capitulos/${capituloId}/`)
      if (obra) fetchObra(obra.slug)
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao deletar capítulo")
    }
  }

  async function deleteObra() {
    if (!obra) return
    const msg = `Tem certeza que deseja EXCLUIR a obra "${obra.titulo}"?\n\nIsso vai deletar TODOS os capítulos e páginas dela. Essa ação NÃO pode ser desfeita.`
    if (!confirm(msg)) return
    // Confirmação dupla — digitar o título pra evitar acidente
    const confirmTitulo = prompt(`Pra confirmar, digite o título exato da obra:\n\n${obra.titulo}`)
    if (confirmTitulo !== obra.titulo) {
      if (confirmTitulo !== null) alert("Título não confere. Exclusão cancelada.")
      return
    }
    setDeleting(true)
    try {
      await apiDelete(`/obras/${obra.slug}/`)
      // Volta pra lista do time da obra
      router.push(obra.fonte === "agregador" ? "/agregador" : "/scan")
    } catch (e) {
      alert(e instanceof Error ? e.message : "Erro ao excluir obra")
      setDeleting(false)
    }
  }

  useEffect(() => {
    params.then(p => fetchObra(p.id))
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (loading) {
    return <div className="px-6 py-8"><p className="text-[oklch(0.55_0_0)]">Carregando...</p></div>
  }

  if (error || !obra) {
    return (
      <div className="px-6 py-8">
        <Link href="/" className="text-[oklch(0.55_0_0)] text-sm hover:text-foreground mb-6 inline-block">
          <ArrowLeft className="w-4 h-4 inline mr-1" />Obras
        </Link>
        <p className="text-red-400">{error || "Obra não encontrada."}</p>
      </div>
    )
  }

  return (
    <div className="px-6 py-6">
      <Link href="/" className="text-[oklch(0.55_0_0)] text-sm hover:text-foreground mb-6 inline-flex items-center gap-1">
        <ArrowLeft className="w-4 h-4" />Obras
      </Link>

      {/* Header da obra */}
      <div className="flex items-start gap-6 mb-8">
        <div className="w-48 h-72 bg-[oklch(0.12_0_0)] border border-border rounded-lg overflow-hidden shrink-0">
          {obra.capa_url ? (
            <img src={obra.capa_url} alt={obra.titulo} className="w-full h-full object-cover" />
          ) : (
            <div className="w-full h-full flex items-center justify-center">
              <span className="text-5xl font-bold text-[oklch(0.25_0_0)]">
                {obra.titulo?.charAt(0).toUpperCase()}
              </span>
            </div>
          )}
        </div>

        <div className="flex-1 pt-2">
          <div className="flex items-center justify-between mb-2">
            <h1 className="text-2xl font-semibold text-foreground">{obra.titulo}</h1>
            <div className="flex gap-2">
              <EditarObraDialog obra={obra} onUpdated={() => fetchObra(obra.slug)} />
              <Link
                href={`/obras/${obra.slug}/editar`}
                className="text-[oklch(0.55_0_0)] hover:text-foreground text-sm px-3 py-2 rounded-md hover:bg-[oklch(0.16_0_0)] transition-colors"
              >
                Edição Avançada →
              </Link>
              <button
                onClick={deleteObra}
                disabled={deleting}
                className="text-destructive hover:bg-destructive/10 text-sm px-3 py-2 rounded-md transition-colors inline-flex items-center gap-1.5 disabled:opacity-50 disabled:cursor-not-allowed"
                title="Excluir obra"
              >
                <Trash2 className="w-4 h-4" />
                {deleting ? "Excluindo..." : "Excluir"}
              </button>
            </div>
          </div>

          <p className="text-[oklch(0.55_0_0)] mb-4">{obra.autor}</p>

          <div className="flex gap-2 mb-4">
            <Badge className={obra.status === "ongoing" ? "bg-primary/20 text-primary" : "bg-[oklch(0.2_0_0)] text-[oklch(0.55_0_0)]"}>
              {obra.status === "ongoing" ? "Ongoing" : "Complete"}
            </Badge>
            <Badge className="bg-[oklch(0.16_0_0)] text-[oklch(0.55_0_0)]">
              {obra.fonte === "scan" ? "Scan" : "Agregador"}
            </Badge>
          </div>

          {obra.sinopse && (
            <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg p-4 mb-4">
              <h2 className="text-[oklch(0.55_0_0)] text-sm font-medium mb-2">Sinopse</h2>
              <p className="text-[oklch(0.75_0_0)] text-sm leading-relaxed">{obra.sinopse}</p>
            </div>
          )}

          {obra.tags && obra.tags.length > 0 && (
            <div className="flex gap-2 flex-wrap">
              {obra.tags.map((tag, i) => (
                <span key={i} className="bg-[oklch(0.16_0_0)] text-[oklch(0.55_0_0)] text-xs px-2.5 py-1 rounded-full">
                  {tag}
                </span>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Capítulos */}
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-lg font-semibold text-foreground">Capítulos ({obra.capitulos?.length || 0})</h2>
        <NovoCapituloDialog obraId={obra.id} onCreated={() => fetchObra(obra.slug)} />
      </div>

      {obra.capitulos && obra.capitulos.length > 0 ? (
        <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg overflow-hidden">
          <Table>
            <TableHeader>
              <TableRow className="border-border">
                <TableHead className="text-[oklch(0.55_0_0)] font-medium">Capítulo</TableHead>
                <TableHead className="text-[oklch(0.55_0_0)] font-medium">Título</TableHead>
                <TableHead className="text-[oklch(0.55_0_0)] font-medium text-right">Páginas</TableHead>
                <TableHead className="text-[oklch(0.55_0_0)] font-medium text-right">Ações</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {obra.capitulos.map((cap) => (
                <TableRow key={cap.id} className="border-border">
                  <TableCell className="text-primary font-medium">#{cap.numero}</TableCell>
                  <TableCell className="text-foreground">{cap.titulo || "Sem título"}</TableCell>
                  <TableCell className="text-[oklch(0.55_0_0)] text-right">{cap.paginas?.length || 0}</TableCell>
                  <TableCell className="text-right">
                    <button
                      onClick={() => deleteCapitulo(cap.id)}
                      className="text-[oklch(0.55_0_0)] hover:text-destructive transition-colors p-1"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      ) : (
        <div className="bg-[oklch(0.12_0_0)] border border-border rounded-lg py-12 text-center">
          <p className="text-[oklch(0.55_0_0)]">Nenhum capítulo cadastrado ainda.</p>
        </div>
      )}
    </div>
  )
}